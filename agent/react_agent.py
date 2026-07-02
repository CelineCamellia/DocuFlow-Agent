from langchain.agents import create_agent

from agent.tools.agent_tools import (
    compare_documents,
    export_word_report,
    extract_doc_info,
    fill_context_for_report,
    generate_report_outline,
    get_case_info,
    identify_risks,
    rag_summarize,
    run_rag_summarize,
    refresh_rag_service,
    get_last_retrieval_sources,
)
from agent.tools.middleware import (
    log_before_model,
    monitor_tool,
    report_prompt_switch,
)
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts


class ReactAgent:
    def __init__(self):
        # 每次重新创建 Agent 时同步刷新 RAG 服务，避免上传新文档后仍使用旧 retriever。
        refresh_rag_service()
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[
                rag_summarize,
                extract_doc_info,
                compare_documents,
                get_case_info,
                identify_risks,
                generate_report_outline,
                export_word_report,
                fill_context_for_report,
            ],
            middleware=[
                monitor_tool,
                log_before_model,
                report_prompt_switch,
            ],
        )

    def get_last_retrieval_sources(self) -> list[dict[str, str | int]]:
        return get_last_retrieval_sources()

    @staticmethod
    def _should_force_rag(query: str) -> bool:
        """对明显的知识库/上传文档问题，绕过 Agent 自由决策，强制走 RAG。

        旧版本完全依赖大模型自己判断是否调用 rag_summarize，遇到
        “我刚上传的 docx 里有什么”这类问题时，模型可能直接回答
        “无法访问文件”。这里做一个工程兜底：只要问题明显指向知识库
        或刚上传文档，就直接执行 RAG 检索。
        """
        keywords = [
            "知识库", "刚上传", "上传的", "上传文件", "文档", "文件",
            "docx", "pdf", "txt", "md", "目录", "题单", "题目",
            "几道题", "多少题", "模块", "检索", "基于",
        ]
        return any(keyword.lower() in query.lower() for keyword in keywords)

    def execute_stream(self, query: str):
        # 稳定兜底：明显要求检索上传文档/知识库时，直接调用 RAG，
        # 避免 Agent 未触发工具导致“无法读取文件”的错误回答。
        if self._should_force_rag(query):
            yield run_rag_summarize(query) + "\n"
            return

        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        last_yielded = None
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            message_type = type(latest_message).__name__

            # Only stream AI-facing content. ToolMessage content is used by the
            # Agent internally and by the citation panel, but should not be
            # shown as raw intermediate output in the chat window.
            if message_type == "AIMessage" and latest_message.content:
                content = latest_message.content.strip()
                if content and content != last_yielded:
                    last_yielded = content
                    yield content + "\n"


if __name__ == "__main__":
    agent = ReactAgent()
    for chunk in agent.execute_stream("根据项目周报生成一份风险分析报告，并导出Word"):
        print(chunk, end="", flush=True)
