#代码作用：
# 把 config文件夹里的多个 .yml 配置文件读取出来，转换成 Python 字典，然后保存成全局变量，供项目中其他代码直接使用。

"""
yaml
k: v
"""
import yaml  # 读取 yaml 格式配置文件
from utils.path_tool import get_abs_path  # 将相对路径转换为项目内的绝对路径

#下面每一个def作用：读取一个对应的 yml 文件，并通过 yaml.load 将其解析成 Python 字典。

# 加载 RAG 配置文件
def load_rag_config(config_path: str=get_abs_path("config/rag.yml"), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:  # 以只读方式打开 rag.yml 配置文件
        return yaml.load(f, Loader=yaml.FullLoader)  # 将 yaml 内容解析成 Python 字典


# 加载 Chroma 向量库配置
def load_chroma_config(config_path: str=get_abs_path("config/chroma.yml"), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:  # 以只读方式打开 chroma.yml 配置文件
        return yaml.load(f, Loader=yaml.FullLoader)  # 将 yaml 内容解析成 Python 字典


# 加载提示词配置
def load_prompts_config(config_path: str=get_abs_path("config/prompts.yml"), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:  # 以只读方式打开 prompts.yml 配置文件
        return yaml.load(f, Loader=yaml.FullLoader)  # 将 yaml 内容解析成 Python 字典


# 加载 Agent 配置
def load_agent_config(config_path: str=get_abs_path("config/agent.yml"), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:  # 以只读方式打开 agent.yml 配置文件
        return yaml.load(f, Loader=yaml.FullLoader)  # 将 yaml 内容解析成 Python 字典


# 调用上面的加载函数，将配置文件内容读取到全局变量中
rag_conf = load_rag_config()              # 保存 RAG 相关配置
chroma_conf = load_chroma_config()        # 保存 Chroma 向量库相关配置
prompts_conf = load_prompts_config()      # 保存提示词相关配置
agent_conf = load_agent_config()          # 保存 Agent 相关配置

#一个测试demo，看看能不能用
if __name__ == '__main__':
    print(rag_conf["chat_model_name"])  # 输出 RAG 配置中的聊天模型名称