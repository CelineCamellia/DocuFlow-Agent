# DocuFlow-Agent

**企业级 RAG + Agent 智能文档处理与报告生成系统。**

本项目面向企业内部制度、会议纪要、项目周报、风险规范、工况记录和报告模板等文档场景，构建一条从“文档输入 → 文档解析 → Chunk 切分 → Embedding 向量化 → Chroma 检索 → Agent 工具调用 → 结构化分析 → Word 报告导出”的轻量工程闭环。

它不是普通 PDF 问答系统，而是将 RAG 封装为 Agent 工具，并扩展信息抽取、风险识别、文档对比、工况查询、报告大纲生成和 Word 导出能力的企业文档处理工作流。

## 1. 当前版本能力

### P0 已补强能力

- 支持 `txt / md / pdf / docx` 多格式企业文档上传。
- 支持直接粘贴会议纪要、项目周报、制度条款等文本并保存入库。
- 基于 `RecursiveCharacterTextSplitter` 进行 chunk 切分。
- 基于 DashScope Embedding + Chroma 构建本地持久化向量库。
- 基于 MD5 记录已处理文件，避免重复入库。
- Agent 可调用 RAG、信息抽取、风险识别、文档对比、工况查询、报告大纲、Word 导出等工具。
- RAG 回答会返回检索来源，Streamlit 页面可展开查看命中文档片段。
- 支持将最近一次助手回复导出为 Word，并通过页面下载。
- 提供 `eval/qa_eval_set.json` 和 `rag/retrieval_eval.py`，用于简单检索命中率与响应时延评测。

### 暂未实现能力

- 未实现 FastAPI 后端接口。
- 未实现复杂 rerank 模型。
- 未实现多路召回融合。
- 未实现登录、权限、多用户管理。
- 未实现 LoRA 微调；本项目定位是大模型应用系统，不做模型训练。

## 2. 技术栈

- Python
- Streamlit
- LangChain / LangGraph runtime
- Chroma
- DashScope Embedding / Qwen Chat Model
- RAG
- Agent / Tool Calling
- Prompt Engineering
- python-docx
- YAML 配置管理
- Logging 日志工具

## 3. 项目结构

```text
app.py                          # Streamlit 页面入口：上传、入库、问答、来源展示、报告下载
agent/react_agent.py            # Agent 创建与流式执行
agent/tools/agent_tools.py      # 企业文档处理工具函数
agent/tools/middleware.py       # 工具监控、模型调用日志、动态 Prompt 切换
rag/vector_store.py             # 文档加载、切分、MD5 去重、Chroma 入库
rag/rag_service.py              # RAG 检索、上下文拼接、来源整理、模型总结
rag/retrieval_eval.py           # 检索评测脚本
services/report_service.py      # Word 报告导出服务
utils/                          # 配置、路径、日志、文件加载工具
config/                         # 模型、向量库、Prompt、外部数据路径配置
prompts/                        # main_prompt / rag_summarize / report_prompt
data/docuflow/                  # 企业文档样例
data/external/case_records.csv  # 工况样例数据
eval/qa_eval_set.json           # RAG 检索评测问题集
outputs/reports/                # 报告导出目录
```

## 4. 快速启动

### 4.1 安装依赖

```bash
pip install -r requirements.txt
```

### 4.2 配置模型环境

本项目默认使用 DashScope 兼容模型配置。请在本地环境变量中配置 API Key。

```bash
# Windows PowerShell 示例
setx DASHSCOPE_API_KEY "你的API_KEY"
```

也可以根据自己环境调整 `config/rag.yml` 中的模型名称。

### 4.3 启动页面

```bash
streamlit run app.py
```

### 4.4 构建知识库

启动后在侧边栏点击：

```text
保存文档并更新知识库
```

系统会读取 `data/docuflow` 下的样例资料和用户上传资料，完成文档解析、chunk 切分、Embedding 向量化和 Chroma 入库。

## 5. 演示问题

```text
总结项目周报中的进展、风险和下周计划，并给出处理建议。
```

```text
企业报销制度中，差旅费用报销需要哪些材料？
```

```text
会议纪要中有哪些待办事项、负责人和截止时间？
```

```text
根据 CASE-001 查询工况信息，并生成风险分析。
```

```text
基于知识库生成一份项目进展报告，并导出 Word。
```

## 6. 检索来源展示

每次 Agent 调用 RAG 工具后，页面会在助手回复下方提供“查看本轮 RAG 检索来源”折叠区，展示：

- 参考资料编号；
- 来源文件名；
- 页码/位置；
- 命中文档片段。

这个功能用于证明模型回答不是纯生成，而是基于企业知识库检索结果。

## 7. 检索评测

先构建知识库，再运行：

```bash
python rag/retrieval_eval.py
```

脚本会读取 `eval/qa_eval_set.json`，统计：

- 评测问题数量；
- 检索命中数；
- hit_rate；
- 平均检索时延 avg_latency_ms；
- 每个问题命中的 top_sources。

注意：当前评测是轻量检索评测，不是完整答案准确率评测。简历中不要写虚假的“准确率提升 xx%”，应该基于该脚本跑出的真实结果填写。

## 8. 简历表达方向

推荐表达：

> 独立开发 DocuFlow-Agent 企业级 RAG + Agent 智能文档处理系统，面向企业制度、会议纪要、项目周报和风险材料等内部文档场景，实现多格式文档解析入库、Chroma 向量检索、Agent 工具调用、结构化信息抽取、风险识别、引用来源展示和 Word 报告导出。

可写技术点：

- 基于 Chroma + Embedding 构建企业文档向量库，支持多格式文档入库、MD5 去重、chunk 切分和 top_k 检索。
- 将 RAG 封装为 Agent 工具，结合 LangChain create_agent 注册文档检索、信息抽取、风险识别、文档对比、工况查询和报告导出工具。
- 通过 middleware 实现工具调用日志和普通问答 / 报告生成模式的动态 Prompt 切换。
- 使用 Streamlit 实现文档上传、知识库更新、流式问答、检索来源展示和 Word 报告下载。
- 构建轻量评测集，用于统计检索命中率和平均检索时延。

## 9. 后续优化方向

P1：RAG 工程化增强

- query rewrite；
- BM25 关键词检索 + 向量检索多路召回；
- rerank；
- chunk 策略对比；
- 更完整的答案准确率评测。

P2：Agent 工作流增强

- 复杂任务拆解；
- 风险识别结果与报告生成联动；
- 更规范的 JSON 信息抽取；
- 轻量 FastAPI 接口。

## v1.2 P0 Bugfix 说明

本版本修复了“页面显示已上传/已更新知识库，但问答时模型仍提示无法读取 docx 文件”的问题：

1. 增强 `docx_loader`：同时读取 Word 正文段落、表格单元格、页眉和页脚，避免表格型题单/目录解析为空。
2. `load_document()` 返回真实入库统计：新增入库文件数、chunk 数、跳过数和失败原因，不再只显示保存文件数量。
3. 上传/重建知识库后刷新 RAG 服务，避免继续使用旧 retriever。
4. 对“知识库、刚上传、docx、目录、题目、检索”等明显文档问题，增加强制 RAG 兜底路由，避免 Agent 未调用检索工具。
5. 新增“强制重建知识库”按钮：如果旧版本已经错误入库或 MD5 已记录，点击该按钮可清空旧向量库和 MD5 记录后重新解析入库。

如果你更新代码后仍然检索不到旧上传文件，请在页面左侧点击 **强制重建知识库（修复解析后点这个）**，然后再提问。
