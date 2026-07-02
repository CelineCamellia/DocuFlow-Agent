import os

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from utils.config_handler import rag_conf


dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")

if not dashscope_api_key:
    raise RuntimeError("未检测到 DASHSCOPE_API_KEY，请先配置环境变量。")


chat_model = ChatOpenAI(
    api_key=dashscope_api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model=rag_conf["chat_model_name"],
    temperature=0.2,
    streaming=True,
)


embed_model = DashScopeEmbeddings(
    model=rag_conf["embedding_model_name"]
)