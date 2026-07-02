import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from agent.react_agent import ReactAgent
from rag.vector_store import VectorStoreService
from utils.config_handler import chroma_conf
from services.report_service import export_markdown_to_word, extract_report_path
from utils.path_tool import get_abs_path


st.set_page_config(page_title="DocuFlow-Agent", layout="wide")
st.title("DocuFlow-Agent 企业级 RAG + Agent 智能文档处理系统")
st.caption("企业内部文档输入 → 文档解析 → 向量检索 → Agent 工具调用 → 结构化分析 / Word 报告生成")
st.divider()


EXAMPLE_QUESTIONS = [
    "总结项目周报中的进展、风险和下周计划，并给出处理建议。",
    "根据 CASE-001 查询工况信息，并生成风险分析。",
    "基于知识库生成一份项目进展报告，并导出 Word。",
    "企业报销制度中，差旅费用报销需要哪些材料？",
    "会议纪要中有哪些待办事项、负责人和截止时间？",
]


def init_agent(force_refresh: bool = False):
    if force_refresh or "agent" not in st.session_state:
        st.session_state["agent"] = ReactAgent()


def save_uploaded_files(uploaded_files):
    upload_dir = get_abs_path("data/docuflow")
    os.makedirs(upload_dir, exist_ok=True)
    saved_files = []
    for uploaded_file in uploaded_files:
        save_path = os.path.join(upload_dir, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_files.append(save_path)
    return saved_files


def save_text_document(text: str):
    upload_dir = get_abs_path("data/docuflow")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"manual_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    save_path = os.path.join(upload_dir, filename)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)
    return save_path


def get_last_assistant_content() -> str:
    for message in reversed(st.session_state.get("message", [])):
        if message.get("role") == "assistant" and message.get("content"):
            return message["content"]
    return ""


def render_sources(sources: list[dict]):
    if not sources:
        return
    with st.expander("查看本轮 RAG 检索来源", expanded=False):
        for item in sources:
            st.markdown(f"**参考资料 {item.get('index', '-')}：{item.get('source', '未知来源')}**")
            st.caption(f"页码/位置：{item.get('page', '-')}")
            st.write(item.get("snippet", ""))
            st.divider()


def render_report_download(path: str | None, label: str = "下载生成的 Word 报告"):
    if not path:
        return
    report_path = Path(path)
    if not report_path.exists() or not report_path.is_file():
        st.warning(f"报告路径不存在或无法访问：{path}")
        return
    with open(report_path, "rb") as f:
        st.download_button(
            label=label,
            data=f.read(),
            file_name=report_path.name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


init_agent()

if "message" not in st.session_state:
    st.session_state["message"] = []
if "last_report_path" not in st.session_state:
    st.session_state["last_report_path"] = None
if "pending_prompt" not in st.session_state:
    st.session_state["pending_prompt"] = ""

with st.sidebar:
    st.header("知识库管理")
    uploaded_files = st.file_uploader(
        "上传企业文档",
        type=["txt", "md", "pdf", "docx"],
        accept_multiple_files=True,
    )
    manual_text = st.text_area(
        "或直接粘贴文档内容",
        height=180,
        placeholder="粘贴会议纪要、项目周报、制度条款、风险说明等",
    )

    if st.button("保存文档并更新知识库", type="primary"):
        saved = []
        if uploaded_files:
            saved.extend(save_uploaded_files(uploaded_files))
        if manual_text.strip():
            saved.append(save_text_document(manual_text.strip()))

        if not saved:
            st.warning("请先上传文件或粘贴文本。")
        else:
            with st.spinner("正在解析文档、切分文本并写入向量库..."):
                load_result = VectorStoreService().load_document()
                init_agent(force_refresh=True)

            st.success(
                f"知识库更新完成：新增入库 {load_result['success_files']} 个文件，"
                f"新增 {load_result['total_chunks']} 个 chunk，跳过 {load_result['skipped_files']} 个，失败 {load_result['failed_files']} 个。"
            )
            if load_result.get("success"):
                with st.expander("查看成功入库文件", expanded=True):
                    for item in load_result["success"]:
                        st.write(f"✅ {item['file']}：{item['chunks']} 个 chunk")
            if load_result.get("failed"):
                with st.expander("查看解析失败文件", expanded=True):
                    for item in load_result["failed"]:
                        st.write(f"❌ {item['file']}：{item['reason']}")
            if load_result.get("skipped"):
                with st.expander("查看已跳过文件", expanded=False):
                    for item in load_result["skipped"]:
                        st.write(f"⏭️ {item['file']}：{item['reason']}")

    if st.button("强制重建知识库（修复解析后点这个）"):
        with st.spinner("正在清空旧向量库和 MD5 记录，并重新入库..."):
            chroma_dir = get_abs_path(chroma_conf["persist_directory"])
            md5_path = get_abs_path(chroma_conf["md5_hex_store"])
            if os.path.exists(chroma_dir):
                shutil.rmtree(chroma_dir, ignore_errors=True)
            if os.path.exists(md5_path):
                os.remove(md5_path)
            load_result = VectorStoreService().load_document()
            init_agent(force_refresh=True)
        st.success(
            f"知识库已强制重建：入库 {load_result['success_files']} 个文件，"
            f"生成 {load_result['total_chunks']} 个 chunk，失败 {load_result['failed_files']} 个。"
        )
        if load_result.get("success"):
            with st.expander("查看本次入库文件", expanded=True):
                for item in load_result["success"]:
                    st.write(f"✅ {item['file']}：{item['chunks']} 个 chunk")
        if load_result.get("failed"):
            with st.expander("查看解析失败文件", expanded=True):
                for item in load_result["failed"]:
                    st.write(f"❌ {item['file']}：{item['reason']}")

    st.divider()
    st.subheader("演示问题")
    for idx, question in enumerate(EXAMPLE_QUESTIONS, start=1):
        if st.button(question, key=f"example_{idx}"):
            st.session_state["pending_prompt"] = question
            st.rerun()

    st.divider()
    st.subheader("报告导出")
    if st.button("将最近一次助手回复导出为 Word"):
        content = get_last_assistant_content()
        if not content:
            st.warning("暂无可导出的助手回复。")
        else:
            path = export_markdown_to_word(content, title="DocuFlow最近分析结果")
            st.session_state["last_report_path"] = path
            st.success(f"已导出：{path}")

    render_report_download(st.session_state.get("last_report_path"), label="下载最近导出的 Word 报告")

for message in st.session_state["message"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources", []))
            render_report_download(message.get("report_path"), label="下载本条回复生成的 Word 报告")

prompt_from_input = st.chat_input("请输入文档分析、知识库问答、信息抽取或报告生成需求")
prompt = st.session_state.pop("pending_prompt", "") or prompt_from_input

if prompt:
    # 1. 显示用户输入
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    response_chunks = []

    # 2. 调用 Agent，但不再使用 write_stream，避免 Streamlit 前端 removeChild 报错
    with st.spinner("DocuFlow-Agent 正在分析文档与选择工具..."):
        res_stream = st.session_state["agent"].execute_stream(prompt)

        for chunk in res_stream:
            if chunk:
                response_chunks.append(str(chunk))

    # 3. 拼接最终回答
    final_response = "".join(response_chunks).strip()

    if not final_response:
        final_response = "未生成有效回答，请重试，或检查知识库是否已成功入库。"

    # 4. 获取本轮 RAG 检索来源
    sources = st.session_state["agent"].get_last_retrieval_sources()

    # 5. 提取报告路径
    report_path = extract_report_path(final_response)
    if report_path:
        st.session_state["last_report_path"] = report_path

    # 6. 保存助手回复
    assistant_message = {
        "role": "assistant",
        "content": final_response,
        "sources": sources,
        "report_path": report_path,
    }

    st.session_state["message"].append(assistant_message)

    # 7. 直接在当前页面显示，不再 st.rerun()
    with st.chat_message("assistant"):
        st.markdown(final_response)
        render_sources(sources)
        render_report_download(report_path, label="下载本条回复生成的 Word 报告")
