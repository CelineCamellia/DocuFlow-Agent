# DocuFlow-Agent：企业级 RAG + Agent 智能文档处理系统

DocuFlow-Agent 是一个面向企业内部文档处理场景的大模型应用项目，基于 RAG + Agent + Tool Calling 构建智能文档处理流程，支持企业制度、会议纪要、项目周报、风险材料等文档的解析入库、语义检索、信息抽取、风险分析与 Word 报告生成。

本项目重点体现大模型应用开发中的文档解析、向量检索、Agent 工具调用、Prompt Engineering、检索来源追踪和结构化报告生成能力。

---

## 1. 项目定位

在企业内部知识管理场景中，会议纪要、项目周报、制度文件、风险说明等资料通常分散在不同文档中，人工查找和整理成本较高。DocuFlow-Agent 希望通过大模型应用能力，将企业文档处理流程自动化。

系统核心流程：

```text
企业文档输入
→ 文档解析
→ chunk 切分
→ Embedding 向量化
→ Chroma 向量库存储
→ RAG 检索
→ Agent 工具调用
→ 结构化分析
→ Word 报告生成
```

本项目不是普通 PDF 问答系统，而是将 RAG 检索能力封装为 Agent 工具，并扩展信息抽取、文档对比、风险识别、工况查询、报告大纲生成和 Word 导出等能力，形成面向企业文档处理的轻量工作流。

---

## 2. 技术栈

| 方向        | 技术                       |
| --------- | ------------------------ |
| 开发语言      | Python                   |
| 前端展示      | Streamlit                |
| 大模型调用     | Qwen / DashScope         |
| Embedding | DashScope Embedding      |
| Agent 框架  | LangChain Agent          |
| RAG 检索    | LangChain Retriever      |
| 向量数据库     | Chroma                   |
| 文档解析      | txt / md / pdf / docx    |
| 报告生成      | python-docx              |
| 工程化能力     | 配置管理、日志记录、Prompt 模板、检索评测 |

---

## 3. 已实现功能

### 3.1 多格式企业文档输入

系统支持上传或录入企业内部文档，包括：

* txt 文本文档；
* md Markdown 文档；
* pdf 文档；
* docx Word 文档；
* 页面直接粘贴的文本内容。

上传后的文档会保存到本地知识库目录，并进入后续解析、切分和向量化流程。

---

### 3.2 文档解析与知识库构建

系统会对文档进行统一处理：

* 解析文档正文内容；
* 对 docx 文档读取正文段落、表格单元格、页眉和页脚；
* 使用 chunk 策略对长文本进行切分；
* 使用 Embedding 模型生成文本向量；
* 使用 Chroma 持久化存储向量；
* 使用 MD5 去重，避免同一文档重复入库；
* 支持知识库强制重建，方便重新解析文档。

---

### 3.3 RAG 检索增强问答

用户提出问题后，系统会基于知识库进行语义检索，召回与问题相关的文档片段，并将片段作为上下文传入大模型生成回答。

系统支持展示本轮 RAG 检索来源，包括：

* 命中文档名称；
* 文档页码或位置；
* 命中文本片段；
* 参考资料编号。

该功能用于提升回答结果的可追溯性，避免模型脱离资料直接生成。

---

### 3.4 Agent 工具调用

系统将不同文档处理能力封装为 Agent 工具，支持根据用户任务调用不同能力。

已注册工具包括：

| 工具                      | 作用                    |
| ----------------------- | --------------------- |
| rag_summarize           | 基于知识库检索并总结回答          |
| extract_doc_info        | 抽取文档中的负责人、任务、风险、时间等信息 |
| compare_documents       | 对比两段文档内容差异            |
| identify_risks          | 识别项目文档中的风险点           |
| get_case_info           | 查询模拟项目工况信息            |
| generate_report_outline | 生成项目报告大纲              |
| export_word_report      | 将分析结果导出为 Word 报告      |
| fill_context_for_report | 触发报告生成场景              |

---

### 3.5 Prompt 分层设计

项目中将提示词拆分为三类：

| Prompt        | 作用                  |
| ------------- | ------------------- |
| main_prompt   | 控制 Agent 主任务判断与工具选择 |
| rag_prompt    | 控制基于检索资料的回答生成       |
| report_prompt | 控制结构化报告生成格式         |

通过不同 Prompt 的拆分，系统可以区分普通问答、知识库检索和报告生成任务，提升输出稳定性。

---

### 3.6 Word 报告生成

系统支持将分析结果整理为 Word 文档，用于模拟企业内部汇报材料、项目进展报告和风险分析报告的生成流程。

报告生成能力包括：

* 结构化分析结果整理；
* Markdown 内容转 Word；
* 页面下载 Word 文件；
* 支持最近一次助手回复导出为 Word。

---

### 3.7 检索评测脚本

项目提供轻量检索评测脚本，用于测试知识库检索效果。

评测内容包括：

* 检索问题数量；
* top-k 命中文档情况；
* 命中文档来源；
* 平均检索耗时。

该部分用于后续对 chunk 参数、top_k 配置和检索策略进行优化。

---

## 4. 项目结构

```text
DocuFlow-Agent/
├── app.py                         # Streamlit 页面入口
├── agent/
│   ├── react_agent.py             # Agent 装配与执行逻辑
│   └── tools/
│       ├── agent_tools.py         # 工具函数定义
│       └── middleware.py          # 工具调用监控与 Prompt 切换
├── rag/
│   ├── vector_store.py            # 文档解析、切分、向量库入库
│   ├── rag_service.py             # RAG 检索与总结回答
│   └── retrieval_eval.py          # 检索评测脚本
├── services/
│   └── report_service.py          # Word 报告生成服务
├── model/
│   └── factory.py                 # 模型与 Embedding 工厂
├── utils/
│   ├── config_handler.py          # 配置读取
│   ├── file_handler.py            # 文件解析与 MD5 工具
│   ├── logger_handler.py          # 日志工具
│   ├── path_tool.py               # 路径处理
│   └── prompt_loader.py           # Prompt 加载工具
├── config/
│   ├── agent.yml                  # Agent 配置
│   ├── chroma.yml                 # 向量库配置
│   ├── prompts.yml                # Prompt 路径配置
│   └── rag.yml                    # 模型与 RAG 配置
├── prompts/
│   ├── main_prompt.txt            # Agent 主提示词
│   ├── rag_summarize.txt          # RAG 总结提示词
│   └── report_prompt.txt          # 报告生成提示词
├── data/
│   ├── docuflow/                  # 企业文档知识库目录
│   └── external/                  # 模拟外部业务数据
├── eval/
│   └── qa_eval_set.json           # 检索评测样例
├── outputs/                       # Word 报告输出目录
├── requirements.txt
└── README.md
```

---

## 5. 快速启动

### 5.1 安装依赖

```bash
pip install -r requirements.txt
```

如需解析 Word 文档，请确保安装：

```bash
pip install python-docx
```

### 5.2 配置 API Key

项目通过环境变量读取 DashScope API Key，请勿将 API Key 写入代码或上传到 GitHub。

Windows PowerShell：

```powershell
setx DASHSCOPE_API_KEY "你的真实API_KEY"
```

配置完成后，关闭当前终端并重新打开。

验证方式：

```powershell
echo $env:DASHSCOPE_API_KEY
```

### 5.3 配置模型

在 `config/rag.yml` 中配置模型：

```yaml
chat_model_name: qwen-plus
embedding_model_name: text-embedding-v4
```

### 5.4 启动项目

```bash
streamlit run app.py
```

启动后浏览器访问：

```text
http://localhost:8501
```

---

## 6. 使用流程

1. 打开 Streamlit 页面；
2. 在左侧上传企业文档，或直接粘贴文档内容；
3. 点击“保存文档并更新知识库”；
4. 等待系统完成文档解析、切分、Embedding 和向量库入库；
5. 在聊天框输入问题；
6. 系统基于知识库检索相关片段并生成回答；
7. 展开“查看本轮 RAG 检索来源”查看命中文档；
8. 如需报告，点击“将最近一次助手回复导出为 Word”。

---

## 7. 演示问题

可以使用以下问题进行项目演示：

```text
请基于知识库中已上传的《企业项目周报.docx》，总结项目进展、主要风险和下周计划，并给出处理建议。
```

```text
请从《企业项目周报.docx》中提取负责人、待办事项、风险项和截止时间。
```

```text
请分析这份项目周报中的主要风险，并给出处理建议。
```

```text
请根据这份项目周报生成一份结构化项目进展报告。
```

```text
企业报销制度中，差旅费用报销需要哪些材料？
```

```text
会议纪要中有哪些待办事项、负责人和截止时间？
```

---

## 8. 项目亮点

### 8.1 从普通问答升级为文档处理工作流

项目不仅支持知识库问答，还扩展了信息抽取、风险识别、文档对比和报告生成能力，更贴近企业内部文档处理场景。

### 8.2 RAG 检索结果可追溯

系统在回答后展示本轮检索来源，用户可以看到模型回答所依据的文档片段，降低无依据生成风险。

### 8.3 Agent 工具化设计

将 RAG 检索、信息抽取、风险分析、报告生成等能力封装为工具，使系统能够根据任务类型调用不同能力。

### 8.4 Prompt 分层与报告生成

通过 main_prompt、rag_prompt、report_prompt 分层设计，让普通问答和报告生成拥有不同输出约束，提升结构化输出质量。

### 8.5 支持 Word 文档交付

系统支持将分析结果导出为 Word 报告，模拟企业办公场景下的项目汇报和风险分析交付方式。

---

## 9. 当前边界

当前版本主要用于本地演示和校招项目展示，已实现企业文档 RAG + Agent 的核心闭环，但仍有进一步优化空间。

当前未包含：

* 多用户权限系统；
* 生产级数据库后台；
* Docker / K8s 部署；
* 复杂多路召回；
* rerank 模型；
* LoRA 微调；
* 多模态解析；
* 完整企业级权限与审计系统。

---

## 10. 后续优化方向

后续可以继续增强以下能力：

* 增加 query rewrite，提升复杂问题检索效果；
* 引入 BM25 + 向量检索的多路召回策略；
* 增加 rerank，对召回片段进行二次排序；
* 对比不同 chunk_size、chunk_overlap 和 top_k 参数下的检索效果；
* 增加更规范的 JSON 信息抽取；
* 增加轻量 FastAPI 接口，方便前后端分离或服务化调用；
* 扩展评测集，统计回答准确性、引用覆盖率和无依据拒答能力。

