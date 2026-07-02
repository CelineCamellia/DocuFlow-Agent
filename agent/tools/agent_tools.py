import csv
import os
import re
from datetime import datetime

from langchain_core.tools import tool

from rag.rag_service import RagSummarizeService
from utils.config_handler import agent_conf
from utils.logger_handler import logger
from utils.path_tool import get_abs_path
from services.report_service import export_markdown_to_word


rag = RagSummarizeService()
case_data_cache: dict[str, dict[str, str]] = {}


def refresh_rag_service() -> None:
    """刷新全局 RAG 服务，确保上传/重建知识库后 retriever 读取最新向量库。"""
    global rag
    rag = RagSummarizeService()



def run_rag_summarize(query: str) -> str:
    """普通函数版本，供前端/路由兜底直接调用 RAG，避免 Agent 未调用工具。"""
    return rag.rag_summarize(query)


@tool(description="检索企业内部知识库，并基于检索片段回答制度、会议、项目、风险、报告模板等问题；返回回答和检索来源")
def rag_summarize(query: str) -> str:
    return run_rag_summarize(query)


def get_last_retrieval_sources() -> list[dict[str, str | int]]:
    """Return citation chunks from the latest RAG tool call for Streamlit display."""
    return rag.last_sources


@tool(description="从企业文档文本中抽取主题、时间、负责人、任务、风险、结论和待办事项，返回结构化要点")
def extract_doc_info(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    joined = "\n".join(lines)

    def find_first(patterns: list[str]) -> str:
        for pattern in patterns:
            match = re.search(pattern, joined)
            if match:
                return match.group(1).strip(" ：:，,。")
        return "未明确"

    owner = find_first([r"负责人[:：]\s*([^\n,，。]+)", r"责任人[:：]\s*([^\n,，。]+)"])
    deadline = find_first([r"截止时间[:：]\s*([^\n,，。]+)", r"计划于\s*([^\n,，。]+?)\s*完成"])
    risk = find_first([r"风险[:：]\s*([^\n。]+)", r"当前风险是\s*([^\n。]+)"])

    tasks = [line for line in lines if any(key in line for key in ["任务", "待办", "计划", "完成", "推进"])]
    conclusions = [line for line in lines if any(key in line for key in ["结论", "决定", "通过", "确认"])]

    return "\n".join(
        [
            "【文档结构化抽取结果】",
            f"主题：{lines[0][:80] if lines else '未明确'}",
            f"负责人：{owner}",
            f"截止时间：{deadline}",
            f"风险点：{risk}",
            "关键任务：" + ("；".join(tasks[:5]) if tasks else "未明确"),
            "会议/文档结论：" + ("；".join(conclusions[:5]) if conclusions else "未明确"),
        ]
    )


@tool(description="对比两段企业文档，提取新增内容、删除内容、共同内容和可能风险")
def compare_documents(doc_a: str, doc_b: str) -> str:
    a_lines = {line.strip() for line in doc_a.splitlines() if line.strip()}
    b_lines = {line.strip() for line in doc_b.splitlines() if line.strip()}

    added = list(b_lines - a_lines)[:8]
    removed = list(a_lines - b_lines)[:8]
    common = list(a_lines & b_lines)[:8]

    return "\n".join(
        [
            "【多文档差异对比】",
            "新增内容：" + ("；".join(added) if added else "未发现明显新增"),
            "删除内容：" + ("；".join(removed) if removed else "未发现明显删除"),
            "共同内容：" + ("；".join(common) if common else "共同内容较少"),
            "风险提示：请重点核对新增的时间、负责人、验收口径、费用规则和风险描述是否影响后续执行。",
        ]
    )


def _load_case_data() -> None:
    if case_data_cache:
        return

    data_path = get_abs_path(agent_conf["external_data_path"])
    if not os.path.exists(data_path):
        logger.warning(f"[get_case_info]外部工况数据不存在：{data_path}")
        return

    with open(data_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row.get("case_id", "").strip()
            if case_id:
                case_data_cache[case_id] = row


@tool(description="按工况编号查询企业项目样例数据，包括项目名称、负责人、进度、风险和报告状态")
def get_case_info(case_id: str) -> str:
    _load_case_data()
    row = case_data_cache.get(case_id.strip())
    if not row:
        return f"未查询到工况编号 {case_id} 的记录"

    return "\n".join(
        [
            f"工况编号：{row.get('case_id', '')}",
            f"项目名称：{row.get('project_name', '')}",
            f"负责人：{row.get('owner', '')}",
            f"当前进度：{row.get('progress', '')}",
            f"风险等级：{row.get('risk_level', '')}",
            f"风险说明：{row.get('risk_desc', '')}",
            f"报告状态：{row.get('report_status', '')}",
        ]
    )


@tool(description="识别企业文档中的项目风险、交付风险、数据风险、合规风险和报告可信度风险")
def identify_risks(text: str) -> str:
    risk_keywords = {
        "进度风险": ["延期", "逾期", "截止", "进度", "里程碑"],
        "质量风险": ["质量", "验收", "不稳定", "错误", "缺陷"],
        "数据风险": ["数据", "来源", "扫描", "抽取", "版本"],
        "合规风险": ["制度", "审批", "发票", "合规", "权限"],
        "交付风险": ["交付", "客户", "报告", "下载", "上线"],
    }
    hits = []
    for risk_type, keywords in risk_keywords.items():
        matched = [word for word in keywords if word in text]
        if matched:
            hits.append(f"- {risk_type}：命中关键词 {', '.join(matched)}，建议补充责任人、影响范围和处理期限。")

    if not hits:
        hits.append("- 暂未发现明显风险关键词；建议继续结合项目进度、质量、数据来源和交付节点人工复核。")

    return "【风险识别结果】\n" + "\n".join(hits)


@tool(description="为周报、会议纪要、项目进展、风险分析等企业文档生成结构化报告大纲")
def generate_report_outline(topic: str) -> str:
    return "\n".join(
        [
            f"# {topic}报告大纲",
            "一、背景与目标",
            "二、输入资料与检索依据",
            "三、当前进展与关键结论",
            "四、问题清单与风险分析",
            "五、处理建议与责任分工",
            "六、后续计划与验收标准",
        ]
    )


def _safe_filename(title: str) -> str:
    filename = re.sub(r"[\\/:*?\"<>|]+", "_", title).strip()
    return filename[:60] or "docuflow_report"


@tool(description="将报告正文导出为 Word 文档，返回本地文件路径；适合用户明确要求生成报告文件时调用")
def export_word_report(content: str, title: str = "DocuFlow企业文档分析报告") -> str:
    filepath = export_markdown_to_word(content=content, title=title)
    return f"Word报告已生成：{filepath}"


@tool(description="无入参；当用户明确要求生成正式报告时调用，用于触发报告生成提示词")
def fill_context_for_report():
    return "报告生成模式已开启"
