#RAG 项目向量库服务模块
# 作用：读取知识库文件 -> 文本切分 -> 存入 Chroma 向量库 -> 提供检索器

from langchain_chroma import Chroma  # 导入 Chroma 向量数据库
from langchain_core.documents import Document  # LangChain 文档对象类型
from utils.config_handler import chroma_conf  # Chroma 配置
#配置信息在06 Agent项目\config\chroma.yml中
from model.factory import embed_model  # 导入嵌入模型，用于向量化
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 文本切分器
from utils.path_tool import get_abs_path  # 将相对路径转换为绝对路径
from utils.file_handler import docx_loader, pdf_loader, txt_loader, listdir_with_allowed_type, get_file_md5_hex  # 文件处理工具
from utils.logger_handler import logger  # 日志器
import os  # 文件路径处理

# VectorStoreService 类
# 作用：封装 Chroma 向量库对象、文本切分器和文档加载方法
class VectorStoreService:

    # 创建向量库对象和文本切分器
    def __init__(self):
        # 创建 Chroma 向量库对象
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],  # 向量库名称
            embedding_function=embed_model,  # 嵌入模型
            #关于模型，需要配置一个模型工厂，方便切换模型，路径:06 Agent项目\model\factory.py
            persist_directory=chroma_conf["persist_directory"],  # 本地持久化存储目录
        )

        # 创建文本切分器
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],  # 分片大小
            chunk_overlap=chroma_conf["chunk_overlap"],  # 重叠长度
            separators=chroma_conf["separators"],  # 切分符
            length_function=len,  # 长度计算函数
        )

    # 获取向量检索器
    # 作用：提供给 RAG 链用于检索相关文档
    def get_retriever(self):
        # 将当前 Chroma 向量库对象转换成 retriever 检索器，k 控制返回的相关文档数量
        #.as_retriever(...)：调用 Chroma 提供的一个方法，把向量库转换成检索器对象。
        #search_kwargs 是方法 as_retriever() 的参数，用来传递检索相关的配置。
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]}) #就是k:v的意思

    # 加载知识库文件并存入向量库
    # 作用：处理 data 文件夹内的 txt/md/pdf/docx 文件 -> 切分 -> 添加到向量库，并返回真实入库统计
    def load_document(self) -> dict:
        """加载知识库目录中的文件，并返回真实处理结果。

        旧版本页面只显示“已更新知识库：N 个文档”，但这个 N 只是保存文件数量，
        不代表真正完成了解析、切分、Embedding、写入 Chroma。这里返回成功/跳过/
        失败/chunk 数，便于页面给出可信提示。
        """
        def check_md5_hex(md5_for_check: str):
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding="utf-8").close()
                return False

            with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding="utf-8") as f:
                for line in f.readlines():
                    if line.strip() == md5_for_check:
                        return True
                return False

        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
                f.write(md5_for_check + "\n")

        def get_file_documents(read_path: str):
            lower_path = read_path.lower()
            if lower_path.endswith(("txt", "md")):
                return txt_loader(read_path)
            if lower_path.endswith("pdf"):
                return pdf_loader(read_path)
            if lower_path.endswith("docx"):
                return docx_loader(read_path)
            return []

        result = {
            "total_files": 0,
            "success_files": 0,
            "skipped_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "success": [],
            "skipped": [],
            "failed": [],
        }

        allowed_files_path: list[str] = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"]),
        )
        result["total_files"] = len(allowed_files_path)

        for path in allowed_files_path:
            filename = os.path.basename(path)
            md5_hex = get_file_md5_hex(path)
            if not md5_hex:
                result["failed_files"] += 1
                result["failed"].append({"file": filename, "reason": "MD5计算失败"})
                logger.warning(f"[加载知识库]{path} MD5计算失败，跳过")
                continue

            if check_md5_hex(md5_hex):
                result["skipped_files"] += 1
                result["skipped"].append({"file": filename, "reason": "内容已入库，跳过"})
                logger.info(f"[加载知识库]{path} 内容已经存在知识库内，跳过")
                continue

            try:
                documents: list[Document] = get_file_documents(path)
                if not documents:
                    result["failed_files"] += 1
                    result["failed"].append({"file": filename, "reason": "未解析到有效文本，可能是扫描版/图片版文档"})
                    logger.warning(f"[加载知识库]{path} 未解析到有效文本，跳过")
                    continue

                for document in documents:
                    document.metadata["source"] = filename
                    document.metadata["file_path"] = path
                    document.metadata["file_type"] = os.path.splitext(filename)[1].lstrip(".").lower()

                split_document: list[Document] = self.spliter.split_documents(documents)
                if not split_document:
                    result["failed_files"] += 1
                    result["failed"].append({"file": filename, "reason": "切分后无有效文本"})
                    logger.warning(f"[加载知识库]{path} 分片后没有有效文本内容，跳过")
                    continue

                for idx, document in enumerate(split_document, start=1):
                    document.metadata["chunk_id"] = idx

                self.vector_store.add_documents(split_document)
                save_md5_hex(md5_hex)

                result["success_files"] += 1
                result["total_chunks"] += len(split_document)
                result["success"].append({"file": filename, "chunks": len(split_document)})
                logger.info(f"[加载知识库]{path} 内容加载成功，chunks={len(split_document)}")

            except Exception as e:
                result["failed_files"] += 1
                result["failed"].append({"file": filename, "reason": str(e)})
                logger.error(f"[加载知识库]{path} 加载失败：{str(e)}", exc_info=True)
                continue

        return result

#测试demo
if __name__ == '__main__':
    vs = VectorStoreService()  # 创建向量库服务对象

    vs.load_document()  # 加载知识库文件

    retriever = vs.get_retriever()  # 获取向量检索器

    # 测试检索，返回 Document 列表
    res = retriever.invoke("项目周报风险")
    for r in res:  # 输出每条文档片段
        print(r.page_content)
        print("-"*20)
