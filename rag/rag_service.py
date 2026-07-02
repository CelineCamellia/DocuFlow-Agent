"""RAG retrieval and summarization service for DocuFlow-Agent.

The service is used both as an Agent tool backend and as a UI diagnostics
provider.  It keeps the retrieval chain independent from the Agent decision
logic so retrieval, citation formatting and evaluation can be tested alone.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from model.factory import chat_model
from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompts


@dataclass
class SourceChunk:
    """A lightweight citation item shown in the UI and evaluation logs."""

    index: int
    source: str
    page: str
    snippet: str


def print_prompt(prompt):
    print("=" * 20)
    print(prompt.to_string())
    print("=" * 20)
    return prompt


class RagSummarizeService:
    """Retrieve enterprise document chunks and generate grounded answers."""

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_prompts()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()
        self.last_sources: list[dict[str, str | int]] = []

    def _init_chain(self):
        return self.prompt_template | print_prompt | self.model | StrOutputParser()

    def retriever_docs(self, query: str) -> list[Document]:
        """Return top-k related document chunks for a user query."""
        return self.retriever.invoke(query)

    @staticmethod
    def _shorten(text: str, max_chars: int = 900) -> str:
        text = " ".join((text or "").split())
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rstrip() + "..."

    @classmethod
    def build_source_chunks(cls, docs: list[Document]) -> list[SourceChunk]:
        """Convert LangChain Documents to source items suitable for display."""
        sources: list[SourceChunk] = []
        for idx, doc in enumerate(docs, start=1):
            metadata = doc.metadata or {}
            raw_source = str(metadata.get("source", "未知来源"))
            source = os.path.basename(raw_source) or raw_source
            page = metadata.get("page", metadata.get("page_number", "-"))
            sources.append(
                SourceChunk(
                    index=idx,
                    source=source,
                    page=str(page),
                    snippet=cls._shorten(doc.page_content),
                )
            )
        return sources

    @staticmethod
    def sources_to_context(sources: list[SourceChunk]) -> str:
        if not sources:
            return "未检索到相关参考资料。"
        return "\n".join(
            [
                f"【参考资料{item.index}】来源：{item.source}；页码：{item.page}；内容：{item.snippet}"
                for item in sources
            ]
        )

    @staticmethod
    def sources_to_markdown(sources: list[dict[str, str | int]]) -> str:
        if not sources:
            return "【检索来源】未检索到相关片段。"
        lines = ["【检索来源】"]
        for item in sources:
            lines.append(
                f"- 参考资料{item['index']}：{item['source']}，页码/位置：{item['page']}，片段：{item['snippet']}"
            )
        return "\n".join(lines)

    def get_retrieval_sources(self, query: str) -> list[dict[str, str | int]]:
        """Retrieve and return source chunks without calling the LLM."""
        docs = self.retriever_docs(query)
        sources = self.build_source_chunks(docs)
        self.last_sources = [asdict(item) for item in sources]
        return self.last_sources

    def rag_summarize_with_sources(self, query: str) -> tuple[str, list[dict[str, str | int]]]:
        docs = self.retriever_docs(query)
        sources = self.build_source_chunks(docs)
        self.last_sources = [asdict(item) for item in sources]
        context = self.sources_to_context(sources)
        answer = self.chain.invoke({"input": query, "context": context})
        return answer, self.last_sources

    def rag_summarize(self, query: str) -> str:
        """Retrieve sources, call LLM, and append citation information."""
        answer, sources = self.rag_summarize_with_sources(query)
        return f"{answer}\n\n{self.sources_to_markdown(sources)}"


if __name__ == "__main__":
    rag = RagSummarizeService()
    print(rag.rag_summarize("项目周报中有哪些风险需要跟进"))
