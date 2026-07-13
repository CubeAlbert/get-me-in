<!--
阅读指南：请先阅读目录找到相关决策，然后直接跳转到该章节。无需加载整个文件。
-->

# 决策记录

[按时间顺序记录重要的项目决策。每个条目分配一个递增编号。最近的决策应摘要在 `current.md` 的"重要决策"中。]

## 目录

- [决策 1 — 架构模式：Hub-and-Spoke + 自研轻量 Agent 框架](#决策-1--架构模式hub-and-spoke--自研轻量-agent-框架)
- [决策 2 — 同步代码，不使用 asyncio](#决策-2--同步代码不使用-asyncio)
- [决策 3 — RAG 技术选型：Chroma + sentence_transformers](#决策-3--rag-技术选型chroma--sentence_transformers)
- [决策 4 — 记忆存储与分块策略](#决策-4--记忆存储与分块策略)
- [决策 5 — 提示词管理：强制拼接 + 按用途组织](#决策-5--提示词管理强制拼接--按用途组织)
- [决策 6 — 工作流：Plan → Execute → Result Validation → Replan](#决策-6--工作流plan--execute--result-validation--replan)
- [决策 7 — 编码时不写测试](#决策-7--编码时不写测试)
- [决策 8 — CLI 方案：input() + $EDITOR + rich](#决策-8--cli-方案input--editor--rich)
- [决策 9 — 包管理：uv + SJTU 镜像](#决策-9--包管理uv--sjtu-镜像)
- [决策 10 — LLM 后端：OpenAI SDK + 双 tier 封装](#决策-10--llm-后端openai-sdk--双-tier-封装)
- [决策 11 — Jupyter 交互式调试工作流](#决策-11--jupyter-交互式调试工作流)
- [决策 12 — 集中式环境变量管理](#决策-12--集中式环境变量管理configpy-模块)
- [决策 13 — LLM 参数分层管理](#决策-13--llm-参数分层管理)
- [决策 14 — Agent 无专属模板文件](#决策-14--agent-无专属模板文件)
- [决策 15 — 编排工具化而非提示词化](#决策-15--编排工具化而非提示词化)
- [决策 16 — JSON 输出解析留待 M4](#决策-16--json-输出解析留待-m4)
- [决策 17 — RAG 双 Collection + 统一分隔符](#决策-17--rag-双-collection--统一分隔符)
- [决策 18 — RAG 模型选型](#决策-18--rag-模型选型)
- [决策 19 — RagLoader 后台加载与降级](#决策-19--ragloader-后台加载与降级)
- [决策 20 — Embedder/Reranker 模型分离 + batch_size 环境变量化](#决策-20--embedderreranker-模型分离--batch_size-环境变量化)
- [决策 21 — HF_ENDPOINT 镜像配置](#决策-21--hf_endpoint-镜像配置)
- [决策 22 — /ragreload 手动重载命令](#决策-22--ragreload-手动重载命令)
- [决策 23 — ChromaStore 内部设计决策](#决策-23--chromastore-内部设计决策)
- [决策 24 — RAG 增量加载与文件同步策略](#决策-24--rag-增量加载与文件同步策略)
- [决策 25 — Reranker 设计决策](#决策-25--reranker-设计决策)
- [决策 26 — ChromaStore 统一检索入口（移除 Retriever）](#决策-26--chromastore-统一检索入口移除-retriever)
- [决策 27 — RagLoader 设计决策](#决策-27--ragloader-设计决策)
- [决策 28 — RAG 公共 API 极简化](#决策-28--rag-公共-api-极简化)
- [决策 29 — MemoryStore 与 RAG 解耦（观察者模式）](#决策-29--memorystore-与-rag-解耦观察者模式)
- [决策 30 — 一文件一条记忆 + front-matter KV 格式](#决策-30--一文件一条记忆--front-matter-kv-格式)
- [决策 31 — Chunker 通用化 + front-matter 解析](#决策-31--chunker-通用化--front-matter-解析)
- [决策 32 — MemoryBuilder 替代 Compressor（对话构建而非压缩）](#决策-32--memorybuilder-替代-compressor对话构建而非压缩)
- [决策 33 — 日志系统：标准库 logging + 按大小轮转](#决策-33--日志系统标准库-logging--按大小轮转)
- [决策 34 — Message 通用消息模型：7 字段 + 模块分离](#决策-34--message-通用消息模型7-字段--模块分离)
- [决策 35 — MemoryStore 格式化逻辑抽出到 utils/formatters.py](#决策-35--memorystore-格式化逻辑抽出到-utilsformatterspy)
- [决策 36 — Memory 类别重构：fact/preference 两分类 + builder 严格 JSON 输出](#决策-36--memory-类别重构factpreference-两分类--builder-严格-json-输出)
- [决策 37 — MemoryBuilder JSON 强制模式 + 换行拆分](#决策-37--memorybuilder-json-强制模式--换行拆分)
- [决策 38 — 记忆模块统一入口 + 文件名 category + --- 分隔符](#决策-38--记忆模块统一入口--文件名-category----分隔符)
- [决策 39 — Chroma in-memory delete(where=) 不可靠：delete_collection 替代方案](#决策-39--chroma-in-memory-deletewhere-不可靠delete_collection-替代方案)
- [决策 40 — Agent Loop 对话历史管理](#决策-40--agent-loop-对话历史管理)
- [决策 41 — 工具结果注入方式](#决策-41--工具结果注入方式)
- [决策 42 — Agent Loop 终止条件](#决策-42--agent-loop-终止条件)
- [决策 43 — Tool 装饰器 + input_schema 设计](#决策-43--tool-装饰器--input_schema-设计)
- [决策 44 — event_payload → 函数入参映射](#决策-44--event_payload--函数入参映射)
- [决策 45 — 工具可见性控制](#决策-45--工具可见性控制)
- [决策 46 — 工具错误处理](#决策-46--工具错误处理)
- [决策 47 — ToolRegistry 全局注册表](#决策-47--toolregistry-全局注册表)
- [决策 48 — process() 接口：Message → Response](#决策-48--process-接口message--response)
- [决策 49 — 意图路由：纯 LLM 驱动](#决策-49--意图路由纯-llm-驱动)
- [决策 50 — CLI 交互库选型：questionary](#决策-50--cli-交互库选型questionary)
- [决策 51 — Agent 切换机制：App.switch_agent()](#决策-51--agent-切换机制appswitch_agent)
- [决策 52 — M4 子 Agent 实现：面试问答 Agent](#决策-52--m4-子-agent-实现面试问答-agent)
- [决策 53 — AgentRegistry 设计](#决策-53--agentregistry-设计)
- [决策 54 — 工具审批模式：ConfirmMode 枚举](#决策-54--工具审批模式confirmmode-枚举)
- [决策 55 — Agent Loop 中间进度回传：Response(type="progress")](#决策-55--agent-loop-中间进度回传responsetypeprogress)
- [决策 56 — Message.event_type 枚举化：EventType(StrEnum)](#决策-56--messageeventtype-枚举化eventtypestrenum)
- [决策 57 — Message 新增 tool / tool_call_id 一级字段](#决策-57--message-新增-tool--tool_call_id-一级字段)
- [决策 58 — 工具 handler 返回纯数据](#决策-58--工具-handler-返回纯数据)
- [决策 59 — System prompt 隔离](#决策-59--system-prompt-隔离)
- [决策 60 — 06_output / 07_input prompt 分工](#决策-60--06_output--07_input-prompt-分工)
- [决策 61 — Message.to_json() / from_llm_reply() 统一序列化](#决策-61--messageto_json--from_llm_reply-统一序列化)
- [决策 62 — 移除 04_tools.md 硬编码预定义工具](#决策-62--移除-04_toolsmd-硬编码预定义工具)
- [决策 63 — message 默认 "" + event_type 唯一 required](#决策-63--message-默认--event_type-唯一-required)
- [决策 64 — Agent Loop 上移至 App 层 + process() 单步执行](#决策-64--agent-loop-上移至-app-层--process-单步执行)
- [决策 65 — Request 类型（对称 Response）作为 App → Agent 输入协议](#决策-65--request-类型对称-response-作为-app--agent-输入协议)
- [决策 66 — 用户拒绝审批 → 退出内层循环，不调 process()](#决策-66--用户拒绝审批--退出内层循环不调-process)
- [决策 67 — 工具错误上下文增强：工具列表 + 参数 schema](#决策-67--工具错误上下文增强工具列表--参数-schema)
- [决策 68 — MainAgent 位置：src/agents/main_agent.py](#决策-68--mainagent-位置srcagentsmain_agentpy)
- [决策 69 — 审批 UI：questionary.select + ConfirmChoice 枚举](#决策-69--审批-uiquestionaryselect--confirmchoice-枚举)
- [决策 70 — LLMClient.web_search() 两轮 native function calling](#决策-70--llmclientweb_search-两轮-native-function-calling)
- [决策 71 — WORKING_DIR 环境变量 + get_working_dir() 工具](#决策-71--working_dir-环境变量--get_working_dir-工具)
- [决策 72 — MainAgent 重新定位为路由 Agent](#决策-72--mainagent-重新定位为路由-agent)
- [决策 73 — LLMClient 线程安全单例](#决策-73--llmclient-线程安全单例)
- [决策 74 — 退出清理统一入口：Lifecycle 模块](#决策-74--退出清理统一入口lifecycle-模块)
- [决策 75 — BaseAgent LLM 调用默认强制 JSON 输出](#决策-75--baseagent-llm-调用默认强制-json-输出)
- [决策 76 — LLM Thinking 可配置开关](#决策-76--llm-thinking-可配置开关)
- [决策 77 — JSON 解析增强：json-repair + 换行转义 + 提示注入节制](#决策-77--json-解析增强json-repair--换行转义--提示注入节制)
- [决策 78 — Agent 切换机制：Tool-based 异步工具调用模型](#决策-78--agent-切换机制tool-based-异步工具调用模型)
- [决策 79 — /exit_sub 主 Agent 前台时报错](#决策-79--exit_sub-主-agent-前台时报错)
- [决策 80 — 子 Agent 列表 prompt 注入：{{SUB_AGENTS_LIST}} 占位符 + 模板重排](#决策-80--子-agent-列表-prompt-注入sub_agents_list-占位符--模板重排)
- [决策 81 — Agent 稳定标识 _get_agent_key() + ToolRegistry "*" sentinel](#决策-81--agent-稳定标识-_get_agent_key--toolregistry--sentinel)
- [决策 82 — CONFIRM 拒绝 → 下次 USER_INPUT 携带拒绝信息](#决策-82--confirm-拒绝--下次-user_input-携带拒绝信息)
- [决策 83 — switch tool 必须声明 input_schema](#决策-83--switch-tool-必须声明-input_schema)
- [决策 84 — UIBridge：工具 handler 通过跨线程通信桥直连 CLI 交互](#决策-84--uibridge工具-handler-通过跨线程通信桥直连-cli-交互)
- [决策 85 — `__reject__` sentinel：switch 被拒后终止 agent loop](#决策-85--__reject__-sentinelswitch-被拒后终止-agent-loop)
- [决策 86 — `MAIN_AGENT_KEY` 常量替换 magic string "main"](#决策-86--main_agent_key-常量替换-magic-string-main)

---

### 决策 1 — 架构模式：Hub-and-Spoke + 自研轻量 Agent 框架

**背景：** 项目包含多个专业化 Agent（简历、学习、面试、岗位搜索），需要确定 Agent 之间的通信模式和框架选型。

**决策：** 采用 Hub-and-Spoke 架构，主 Agent 是唯一调度中心，子 Agent 之间不允许直接通信。Agent 框架自研，不使用 LangChain / CrewAI / AutoGen 等现成框架。

**理由：**
- Hub-and-Spoke 匹配项目规模（< 10 个 Agent），不需要 Mesh 的对等通信复杂度
- 自研框架最大控制力，学习成本为零，依赖最小化
- 现成框架引入不必要的抽象层和几十个依赖包，项目只需几百行编排代码

**曾考虑的替代方案：**
- CrewAI / AutoGen —— 功能过剩，学习成本高，引入大量依赖，调试困难
- LangGraph —— StateGraph 抽象对 Hub-and-Spoke 模式过度设计
- Mesh 架构（Agent 对等通信）—— 当前 Agent 数量不需要，增加复杂度

---

### 决策 2 — 同步代码，不使用 asyncio

**背景：** 技术栈讨论时提到 asyncio 适合 Agent 调用场景，需要决定是否引入异步编程。

**决策：** 全部使用同步代码，不引入 asyncio 或任何异步框架。

**理由：** Agent 调用链在当前规模下同步执行即可，异步增加开发和调试成本，收益不明显。

**曾考虑的替代方案：**
- asyncio —— Python 标准库，但增加心智负担，当前规模不需要

---

### 决策 3 — RAG 技术选型：Chroma + sentence_transformers

**背景：** 需要语义检索能力支持记忆检索、面试题库、JD 匹配等场景，需要选择向量存储和模型方案。

**决策：** 使用 Chroma 作为向量存储（内存模式先行，后续可切本地持久化），sentence_transformers 提供 bi-encoder（召回）和 cross-encoder（重排）。

**理由：**
- Chroma 内存模式零配置启动，开发阶段免运维，后续改一行参数即可切换持久化
- sentence_transformers 一个库同时覆盖召回和重排两种模型，不引入额外依赖
- 召回+重排两阶段是 RAG 成熟模式：bi-encoder 快但粗，cross-encoder 慢但准

**曾考虑的替代方案：**
- FAISS —— 功能强大但偏底层，Chroma 更轻量且有 collection 管理
- 本地 JSON 文件存向量 —— 查询效率低，不支持近似搜索
- OpenAI Embeddings API —— 需要网络、有成本、不可离线

---

### 决策 4 — 记忆存储与分块策略

**背景：** 记忆需要持久化存储和语义检索，需要确定存储格式、目录组织、以及如何将记忆切分为可检索的单元。

**决策：**
- 记忆按 Agent 分目录（`data/memories/<agent>/`），每个 Agent 下按日期分文件
- 存储格式为 Markdown，文件系统而非数据库
- Agent 固化记忆时写入约定分隔符，Chunker 按分隔符切分为逻辑块后向量化入库
- Chroma collection 按模块划分（`memories`、`interview_questions`、`job_descriptions`），不按 Agent 划分

**理由：**
- 按 Agent 隔离避免互相干扰，跨 Agent 检索通过 RAG 语义搜索
- Markdown + 文件系统人机可读，Git 可追踪，免运维，项目规模下无性能瓶颈
- 分隔符切分策略由写入方（Agent）定义，Chunker 保持通用，不耦合业务语义
- Collection 按模块划分便于管理不同数据的检索场景

**曾考虑的替代方案：**
- SQLite / PostgreSQL —— 过度设计，失去人机可读性
- 按整篇 MD 文件入库 —— 粒度过粗，检索精度差
- 按 Agent 分 collection —— 记忆统一检索时需跨 collection 查询

---

### 决策 5 — 提示词管理：强制拼接 + 按用途组织

**背景：** 每个 Agent 需要各自独立的提示词，同时所有 Agent 需要共享安全策略、工具列表、输出格式等公共约束。

**决策：**
- `data/prompts/general_agent/` 目录下多个 `.md` 文件定义公共前缀（安全策略、工具列表、输出格式）
- `PromptLoader` 对 Agent 调用方强制拼接公共前缀，Agent 无法跳过
- 非 Agent 模块（记忆压缩等）使用 `get_raw()` 跳过拼接
- 提示词按用途命名，不按 Agent 划分

**理由：**
- 强制拼接确保所有 Agent 遵守统一的安全和格式约束
- 按用途组织允许同一提示词被多个模块复用
- 提示词与代码分离，调整提示词改文件即可，降低迭代成本

**曾考虑的替代方案：**
- 每个 Agent 各自管理完整提示词 —— 公共约束变更时需改多处，容易遗漏
- 公共提示词放在代码中硬编码 —— 调整需要改代码

---

### 决策 6 — 工作流：Plan → Execute → Result Validation → Replan

**背景：** 项目采用 AI 辅助开发，需要一套适合迭代的工作流，而非传统瀑布式开发。

**决策：** 采用 Plan → Execute → Result Validation → Replan 循环。设计/计划文件不适用的内容直接删除（Git 追溯），任务被废弃时标 ⛔ 并追加替代任务。

**理由：**
- 验证结果可能推翻原有假设，计划需要随时调整
- 直接删除保持文档干净，Git 负责历史
- 任务标 ⛔ 而非删除，保留决策轨迹

**曾考虑的替代方案：**
- 传统瀑布（先完整设计再开发）—— 不适合 AI 辅助的快速迭代
- 全部保留废弃内容（划线标记）—— 文档越来越臃肿

---

### 决策 7 — 编码时不写测试

**背景：** 项目处于早期快速迭代阶段，需求和设计频繁变化。

**决策：** 编写代码时不同步编写测试文件，除非用户显式要求。

**理由：** 早期阶段设计频繁变化，测试维护成本高。待接口和设计稳定后再考虑测试。

**曾考虑的替代方案：**
- TDD（测试驱动开发）—— 早期阶段不适合，需求变化导致测试反复重写
- 每个模块写完补测试 —— 拖慢迭代速度

---

### 决策 8 — CLI 方案：input() + $EDITOR + rich

**背景：** 需要选择 CLI 交互方案，项目是对话式 AI 助手，非命令行工具。

**决策：** 日常对话使用 `input()`，长文本输入（JD、简历、面试回答）弹出 `$EDITOR` 编辑临时文件，Markdown 输出用 `rich` 渲染。

**理由：**
- 对话式交互不需要 click 的命令行参数解析
- `$EDITOR` 临时文件解决 `input()` 不支持多行输入的问题
- `rich` 仅用于输出美化，轻量且够用

**曾考虑的替代方案：**
- `click` —— 适合命令行多子命令工具，对话式 AI 用不上
- `prompt_toolkit` —— 提供输入历史和自动补全，但对当前需求过度

---

### 决策 9 — 包管理：uv + SJTU 镜像

**背景：** 需要选择 Python 项目的包管理和虚拟环境方案。

**决策：** 使用 `uv` 管理依赖和运行（`uv add` / `uv remove` / `uv sync` / `uv run`），PyPI 镜像配置在上海交大 SJTUG 镜像站（`https://mirrors.sjtug.sjtu.edu.cn/pypi/web/simple`），在 `pyproject.toml` 中通过 `[[tool.uv.index]]` 持久化配置。

**理由：**
- `uv` 是当前最快的 Python 包管理器（Rust 实现），下载和解析速度远超 pip/Poetry
- `uv run` 统一了"在项目 venv 中执行命令"的入口，避免激活虚拟环境的混乱
- 国内镜像大幅提升下载速度（从 550KB/s → 25MB/s）
- `pyproject.toml` 持久化镜像配置，团队共享无需各自配置

**曾考虑的替代方案：**
- Poetry —— 功能完善但比 uv 慢一个数量级，且 `poetry run` 不如 `uv run` 简洁
- pip + venv —— 需要手动管理虚拟环境，`uv` 自动处理
- 清华 TUNA 镜像 / 中科大镜像 —— 均可替代，速度接近

---

### 决策 10 — LLM 后端：OpenAI SDK + 双 tier 封装

**背景：** 项目需要 LLM 调用能力，需要选择 SDK 和封装方式。

**决策：**
- 使用 `openai` 包（OpenAI SDK），兼容所有 OpenAI-compatible 后端（如 vLLM、Ollama、DeepSeek 等）
- 封装为双 tier：`chat_pro()`（高能力，默认 `gpt-4o`）和 `chat_flash()`（快速，默认 `gpt-4o-mini`）
- 通过 4 个环境变量注入配置：`OPENAI_BASE_URL`、`OPENAI_API_KEY`、`LLM_PRO_MODEL`、`LLM_FLASH_MODEL`
- `python-dotenv` 在应用启动时加载 `.env`
- 调用逻辑封装在 `src/agents/base.py` 中，子 Agent 调用 `self._llm_pro()` / `self._llm_flash()`，不传 model 名

**理由：**
- OpenAI SDK 是事实标准，生态兼容性最广，换后端只改环境变量不动代码
- 双 tier 覆盖两种场景：深度推理（简历分析、面试评估）用 pro，轻量任务（意图分类、格式化）用 flash
- model 名不暴露给 Agent —— 具体模型由运维决定，Agent 只关心能力等级
- 不做 fallback —— 保持简单，错误直接抛出到 CLI 前端

**曾考虑的替代方案：**
- 直接使用 Anthropic SDK —— 仅支持 Claude，不如 OpenAI-compatible 生态广
- 多 provider 适配层 —— 过度设计，OpenAI-compatible 协议已足够通用
- 硬编码 model 名 —— 换模型需要改代码

---

### 决策 11 — Jupyter 交互式调试工作流

**背景：** 开发阶段需要快速验证局部函数（如 RAG embedding、Chunker 逻辑），直接跑完整 CLI 链路太重。

**决策：** 使用 `uv run --with jupyter jupyter lab` 启动 Jupyter Notebook 做交互式验证，`jupyter` 不写入项目依赖。

**理由：**
- `uv run` 确保 notebook 在项目 venv 中运行，能 import 项目代码
- `--with jupyter` 临时注入不污染 `pyproject.toml`
- 交互式环境适合调试局部逻辑，改一行跑一行，不需要每次从头启动 CLI

**曾考虑的替代方案：**
- 单元测试 —— early阶段接口不稳定，测试维护成本高（决策 7 已有约束）
- `python -i` 交互式解释器 —— 功能弱，不支持富文本和代码块

---

### 决策 12 — 集中式环境变量管理（config.py 模块）

**背景：** 各模块各自调用 `os.environ` 读取环境变量，散落各处不利于维护和启动校验。

**决策：** 新增 `src/config.py` 模块集中管理所有环境变量。启动时调用 `load_dotenv()` 加载 `.env`，逐一校验必填变量，缺失时打印清单并 `sys.exit(1)`。其他模块（LLM、CLI 等）通过 `from src.config import config` 获取配置值，禁止直接调用 `os.environ`。

**理由：**
- 启动时一次性校验，不会因环境变量缺失而在运行时中途崩溃
- 换变量名只改 `config.py` 一处，风险远低于全局 grep 替换
- 模块级单例，`import` 即加载，零侵入
- 缺失时打印清晰清单，用户一眼知道缺什么

**曾考虑的替代方案：**
- 各模块各自校验 —— 校验逻辑散落，可能遗漏，错误信息不一致
- 使用 `pydantic-settings` —— 功能完善但引入额外依赖，当前 4 个变量不需要

---

### 决策 13 — LLM 参数分层管理

**背景：** LLM 调用需要支持 temperature、top_p、response_format 等参数，不同 Agent 需要不同的默认值，同时调用方需要能临时覆盖。

**决策：**
- `LLMClient.chat_pro()` / `chat_flash()` 通过 `**kwargs` 透传所有额外参数给 OpenAI SDK，不预设也不拦截任何参数
- `BaseAgent` 提供 `_pro_params` / `_flash_params` 类属性（dict），子 Agent 按需覆盖声明自己的默认值
- `BaseAgent._llm_pro()` / `_llm_flash()` 合并类默认值 + 调用时覆盖：`{**self._pro_params, **kwargs}`
- 需要精细控制时，直接通过 `LLMClient.client`（暴露底层 `openai.OpenAI` 实例）走原生 SDK

**理由：**
- `LLMClient` 保持薄管道角色，不关心调用方是谁、传了什么参数
- 参数默认值声明在子 Agent 类定义处，一目了然，不用翻调用代码
- 分层清晰：`LLMClient` 管 API 连接，`BaseAgent` 管参数合并，子 Agent 管具体值
- 暴露底层 client 让高级用户不被封装限制

**曾考虑的替代方案：**
- 在 `LLMClient` 中硬编码 temperature 等参数 —— 不同 Agent 需求不同，耦合
- 每个子 Agent 各自拼 `**kwargs` 传参 —— 参数散落各处，缺乏统一入口

---

### 决策 14 — Agent 无专属模板文件

**背景：** 提示词模块设计初期讨论了两种组织方式：每个 Agent 各有一组专属模板文件，还是所有 Agent 共用一套模板文件、差异由占位符值体现。

**决策：**
- 所有 Agent 共用 `general_agent/` 下 7 个模板文件，不允许 Agent 拥有自己的模板文件
- Agent 之间的差异完全由 14 个 per-Agent 占位符填充值体现（清单见 `data/prompts/PLACEHOLDER.md`）
- `PromptLoader.get(**variables)` 加载时拼接通用模板 + 替换占位符，`**variables` 的键值对由各 Agent 提供

**理由：**
- 共用模板确保所有 Agent 遵守统一的角色框架、安全约束和输出格式，不会因各自编写而出现遗漏或不一致
- 占位符系统提供了足够的差异化空间（身份、目标、约束、工具、风格五个维度）
- 模板文件数量可控（固定 7 个），新增 Agent 不需要新增模板文件

**曾考虑的替代方案：**
- 每个 Agent 各自管理完整提示词 —— 公共约束变更时需要改 N 处，容易遗漏
- Agent 专属模板文件覆盖公共模板 —— 复杂度高，Agent 可能绕过核心安全策略

---

### 决策 15 — 编排工具化而非提示词化

**背景：** 主 Agent 调度子 Agent 的方式有两种选择：在提示词中描述调度规则，或将调度定义为工具调用。

**决策：**
- 不在提示词中写"当用户说 X 时调用 Y Agent"
- 调度子 Agent 定义为工具（如 `dispatch_resume`、`dispatch_interview`），通过 `{{ADDITION_TOOLS}}` 占位符注入主 Agent 的工具列表
- LLM 通过标准工具选择流程（`04_tools.md` + `06_output_format.md`）完成意图识别和调度

**理由：**
- 工具化调度利用 LLM 原生的 function calling 能力，无需在提示词中维护调度规则
- 新增或移除子 Agent 只需增删工具定义，不改提示词
- 与输出格式（JSON + action.tool）一致，LLM 的工具选择和调度是同一套流程

**曾考虑的替代方案：**
- 在提示词中枚举调度规则 —— 调度逻辑耦合在文本中，变更需要改提示词，且长提示词降低 LLM 遵从度
- 独立的意图路由模块（规则匹配 / 分类器）—— 增加维护成本，且不如 LLM 灵活

---

### 决策 16 — JSON 输出解析留待 M4

**背景：** `06_output_format.md` 已定义结构化 JSON 输出 schema（`thinking` + `action`），M1 阶段的 `LLMHandler` 面临选择：立即实现 JSON 解析，还是透传原始回复。

**决策：**
- M1 阶段不做 JSON 解析，`LLMHandler` 将 LLM 原始回复直接返回给 CLI
- JSON 解析（`json.loads` → 提取 `action.message` → 识别 `action.tool` → agent loop）留到 M4 由 Orchestrator 实现
- M1 裸 JSON 输出不影响端到端验证目的

**理由：**
- JSON 解析逻辑属于 Agent 编排层（Orchestrator），不属于 M1 基础设施验证范畴
- 提前实现需要在 `LLMHandler` 中引入 Agent loop 逻辑（工具分发、多轮对话状态机），跨到了 M4 的边界
- M1 目标是验证 config → LLM → prompts → CLI 管线，裸 JSON 输出已足够验证

**曾考虑的替代方案：**
- 在 M1 立即解析 JSON —— 需要在 Handler 中实现半个 agent loop，边界模糊，且 M4 时会被 Orchestrator 替换，额外工作量无积累价值
- 临时移除 `06_output_format.md` 中的 JSON 约束 —— 不需要，LLM 输出裸 JSON 不影响测试目的

---

### 决策 17 — RAG 双 Collection + 统一分隔符

**背景：** M2 阶段设计 RAG 数据存储方案，需要确定 collection 划分策略、分隔符约定、以及参考数据的组织方式。

**决策：**
- 两个 collection：`references`（参考数据）+ `memories`（记忆），不按数据类型拆细
- 统一使用 Markdown 水平线 `---` 作为条目边界，记忆和参考数据共用同一套切分规则
- 参考数据的 category 由子目录名自动提取（`data/reference/<category>/` → `{"category": "<category>"}`），不维护独立配置文件
- 默认全库检索，Reranker 自然排序；调用方可传 `filter={"category": "knowledge_base"}` 限定范围
- 不需要 index.md 或 router 做前置分类

**理由：**
- 两个 collection 足够覆盖所有场景，更多 collection 增加跨 collection 合并排序的复杂度，收益有限
- `---` 是 Markdown 原生语法，人和 LLM 写起来自然
- 子目录名即 category，零维护，新增数据类型只需新建目录
- 全库检索 + Reranker 排序已经够准，前置路由是过度设计

**曾考虑的替代方案：**
- 每种参考数据一个 collection —— 跨 collection 检索需要合并排序
- 维护 index.md 做两级检索 —— 增加维护负担且不必要
- `<!-- chunk -->` 做分隔符 —— 语义明确但输入繁琐

---

### 决策 18 — RAG 模型选型

**背景：** RAG 模块需要 bi-encoder（召回）和 cross-encoder（重排），需选定具体模型并做成可配置。

**决策：**
- Bi-encoder：`BAAI/bge-base-zh-v1.5`（中文优化，召回速度快）
- Cross-encoder：`BAAI/bge-reranker-v2-m3`（精排准确率高）
- 模型名通过环境变量 `BI_ENCODER_MODEL` / `CROSS_ENCODER_MODEL` 配置，带默认值
- 若 cross-encoder 性能不足可降级为 `BAAI/bge-reranker-base`（仅记录备选，不做在代码中）

**理由：**
- BGE 系列是国内中文语义检索事实标准，社区验证充分
- 环境变量配置支持不同环境灵活切换
- `bge-reranker-v2-m3` 是 v2 系列最强模型，本地推理慢时可降级 base

**曾考虑的替代方案：**
- `all-MiniLM-L6-v2` —— 英文优化，中文效果差
- OpenAI Embeddings API —— 需网络、有成本、不可离线

---

### 决策 19 — RagLoader 后台加载与降级

**背景：** 参考数据和记忆的文件数量可能较多，启动时同步加载会阻塞 CLI。需要设计加载机制。

**决策：**
- 新增 `src/rag/loader.py`（RagLoader），负责遍历磁盘 → Chunker → ChromaStore
- `auto_load()` 使用 `threading.Thread` 后台执行，不阻塞主线程
- 暴露 `is_ready()` 供调用方判断；RAG 未就绪时对话走纯 LLM 降级
- `load_file(path)` 支持增量加载：按 `source_file` 删旧 chunk 后重新入库
- Collection 不预建，ChromaStore 首次 `add()` 时自动创建

**理由：**
- `threading` 而非 `asyncio`，与项目同步代码约定一致（决策 2）
- 后台加载保证 CLI 秒级可交互
- `is_ready()` 降级机制简单可靠
- 增量加载支持热更新（新增面试题、Agent 写入记忆后即时入库）

**曾考虑的替代方案：**
- 同步加载 —— 启动慢，数据量大时不可接受
- 启动时预建 collection —— Chroma 首次写入自动创建，预建无额外收益
- 全量重载 —— 改一个文件就要全部重新加载

---

### 决策 20 — Embedder/Reranker 模型分离 + batch_size 环境变量化

**背景：** 设计初期将 bi-encoder 和 cross-encoder 都放在 Embedder 中，由 Reranker 复用 Embedder 的 cross-encoder 模型。实现阶段发现两个模型职责不同、调用方不同，耦合不必要。

**决策：**
- Embedder 只持有 bi-encoder（`SentenceTransformer`），只提供 `embed(texts)` 向量化方法
- Reranker 独立加载 cross-encoder（`CrossEncoder`），不依赖 Embedder
- `batch_size` 通过环境变量 `EMBED_BATCH_SIZE` 配置（默认 32），`embed()` 作为可选参数

**理由：**
- 单一职责：Embedder 就是文本 → 向量，不关心评分逻辑
- 独立加载避免模块间不必要的耦合
- 环境变量配置支持不同硬件灵活调整，无需改代码

**曾考虑的替代方案：**
- Embedder 同时持有两个模型 → 职责冗余
- batch_size 硬编码 → GPU/CPU 差异大

---

### 决策 21 — HF_ENDPOINT 镜像配置

**背景：** 国内访问 HuggingFace Hub 经常超时，`sentence_transformers` 首次加载需下载数百 MB 权重文件。

**决策：**
- 新增 `HF_ENDPOINT` 环境变量，默认值 `https://hf-mirror.com`（国内镜像）
- `load_dotenv()` 自动注入 `os.environ`，`sentence_transformers` 底层自动读取，零代码改动

**理由：**
- 国内用户开箱即用，海外用户可覆盖为官方地址
- 不侵入代码，完全由环境变量控制

**曾考虑的替代方案：**
- 不做处理 —— 国内用户首次加载必然失败

---

### 决策 22 — /ragreload 手动重载命令（📌 暂缓，未实现）

**背景：** RAG 后台加载可能因模型下载失败而无法就绪，用户需要在不重启程序的情况下重新触发加载。

**决策：**
- 新增 CLI 命令 `/ragreload`，手动重新触发 `auto_load()`
- 当前阶段不实现（标记为 📌 暂缓），M2 末尾或 M3 再做
- RagLoader 内部 catch 异常，加载失败时 `_ready` 保持 False，对话自动降级纯 LLM

**理由：**
- 模型下载成功后一条命令恢复 RAG，无需退出程序
- 与 `is_ready()` 降级机制互补

**曾考虑的替代方案：**
- 自动重试 —— 可能反复失败浪费资源
- 要求重启程序 —— 体验差

---

### 决策 23 — ChromaStore 内部设计决策

**背景：** ChromaStore 作为 Chroma 的封装层，需要确定 Embedder 依赖方式、数据存储格式、线程安全策略、距离度量、collection 校验、持久化切换等内部设计。

**决策：**

- **Embedder 内部创建**：Store 在 `__init__` 直接 `Embedder()`，不接受构造函数注入。未来切换 API 后端时在 Embedder 内部通过环境变量控制，Store 不动
- **原始文本存入 Chroma**：`add()` 时使用 Chroma 的 `documents` 参数存储原文，`query()` 返回 `list[Chunk]`（直接从 Chroma 结果还原 content）
- **filter 直接透传**：`query()` 的 where filter dict 透传给 Chroma，不做封装（Chroma 语法是 MongoDB 子集）
- **不加锁**：`auto_load()` 期间 `is_ready()` 为 False，查询走纯 LLM 降级；`load_file()` 增量更新为单文件操作，耗时极短
- **距离度量用默认 L2**：Embedder 已输出归一化向量，L2 与 cosine 排序结果数学上等价，无需显式设置 `hnsw:space`
- **不校验 collection 名**：信任调用方传对 `"references"` 或 `"memories"`
- **持久化通过环境变量切换**：设置 `CHROMA_PERSIST_DIR` → `PersistentClient(path)`，不设置 → `Client()`（内存模式）。持久化目录 `data/chroma/` 加入 `.gitignore`

**理由：**

- 内部创建 Embedder 保持调用方零配置，同时 Embedder 接口 `embed(texts) -> list[list[float]]` 足够通用，后端切换不影响 Store
- `documents` 字段是 Chroma 原生能力，存原文避免 query 后回源读文件
- filter 透传零学习成本，Chroma 语法与 MongoDB 一致
- 线程安全简化：运行时自然隔离，无需引入锁复杂度
- L2 等价性由数学保证，无需额外配置
- collection 校验收益为零（调用方只有 Loader 和 MemoryStore，均编写时已知）

**曾考虑的替代方案：**

- 构造函数注入 Embedder —— 当前只有一个使用方，注入无收益
- content 塞入 metadata —— 污染 metadata，Chroma 原生 `documents` 字段更合适
- filter 封装一层 —— 增加学习成本，Chrom 语法已标准
- 加锁 —— 当前访问模式天然隔离，加锁是过度设计
- 显式设置 `hnsw:space=cosine` —— 归一化向量下与 L2 等价

---

### 决策 24 — RAG 增量加载与文件同步策略

**背景：** 持久化模式下，重启后需要判断哪些文件已变更，避免对未变化的文件重复做 embedding。同时，运行时文件的增删需要与 Chroma 保持同步。

**决策：**

- **时间戳增量加载**：持久化模式下，`auto_load()` 读取 `data/chroma/.last_update` 时间戳（不存在 → epoch 0），扫描 `data/reference/` 和 `data/memories/`，收集 mtime > 时间戳的文件，对每个变化的文件执行 `remove(source_file)` → `chunk` → `add`，最后写入当前时间戳
- **用户手动删除磁盘文件**：不管，不清理 Chroma 中的孤儿 chunk
- **Agent 程序化操作**：删除文件时统一封装，同步清理 Chroma 对应数据；写入记忆时走统一路径（写文件 → Chunker → ChromaStore.add()），确保文件与 Chroma 一致
- 封装逻辑在 Memory 模块实现时处理，Store 只提供 `add()` / `remove()` / `query()` 基础接口

**理由：**

- 时间戳比对 O(n) 扫描足够简单，无需维护文件 hash 或变更日志
- 用户手动删除属于外部操作，清理孤儿 chunk 需要全量比对（拿 Chroma 所有 source_file 去磁盘检查），成本高收益低
- Agent 程序化操作统一封装，避免各处重复 delete+add 逻辑
- 职责分层：Store 提供原子操作，Memory 模块负责一致性封装

**曾考虑的替代方案：**

- 全量删重建 —— 每次都重新 embedding，持久化优势浪费
- 文件 hash 比对 —— 精准但复杂度高，当前文件数量少时无必要
- 在 Store 中实现文件操作封装 —— Store 只管 Chroma，文件操作不是其职责
- 监听文件系统事件（watchdog）—— 引入额外依赖，过度设计

---

### 决策 25 — Reranker 设计决策

**背景：** Reranker 独立加载 cross-encoder 对召回结果精排，需确定分数传递方式、批处理配置、预热策略和异常处理。

**决策：**

- **分数存入 `metadata["rerank_score"]`**：Reranker 不修改 Chunk 结构，在现有 `metadata: dict` 中注入浮点数分数，结果按分数从高到低排列
- **批处理大小环境变量化**：新增 `RERANK_BATCH_SIZE` 环境变量（默认值 32），控制 `CrossEncoder.predict()` 每次传入多少对 (query, document)
- **Top-K 环境变量化**：新增 `RERANK_TOP_K` 环境变量（默认值 5），控制重排后保留条数
- **`__init__` 时预热**：加载模型后用一对假数据 `[("预热", "预热")]` 跑一次 `predict()`，避免首次真实调用卡顿
- **异常直接抛出**：模型加载失败或 predict 异常不吞，抛给调用方。调用方（检索链路）try/except 后降级，用 ChromaStore 原始召回结果

**理由：**

- dict 注入分数改 metadata 不动 Chunk 字段，最小侵入
- 批处理和 top-k 环境变量化延续 Embedder 风格（决策 20），不同硬件灵活调整
- 预热收益明显（首次调用从 2-3s 降至 100ms），一行代码换取流畅用户体验
- Reranker 不做降级逻辑：降级是调用方（检索链路）的调度职责，Reranker 只管评分

**曾考虑的替代方案：**

- 在 Chunk 上加 `score` 字段 —— 改动数据结构，只有 Reranker 使用，放入 metadata 更合适
- top-k 硬编码 5 —— 不同场景（面试题 vs JD 匹配）可能需要不同数量
- 不预热 —— 每次启动后第一次检索体验差
- Reranker 内部 try/except 返回原结果 —— 调用方不知道重排失败了，反而被当作正常结果使用

---

### 决策 26 — ChromaStore 统一检索入口（移除 Retriever）

**背景：** 为实现阶段发现 `ChromaStore.__init__` 和 `Retriever.__init__` 各自创建 `Embedder` 实例，导致 bi-encoder 模型被加载两次（内存翻倍 + 加载时间翻倍）。追溯设计发现一旦 `ChromaStore.query()` 改为接受文本、内部向量化，`Retriever` 的职责退化为一层透传调用：`retrieve(query) { return store.query(query) }`。

**决策：**
- 移除 `src/rag/retriever.py`（不创建该文件）
- `ChromaStore.query()` 改为接受查询文本（`query_text: str`），内部调 `self._embedder.embed()` 向量化后检索
- 检索流程从 `Embedder.embed() → Retriever → Store.query()` 简化为 `Store.query(query_text)`
- Reranker 仍独立存在，在 Store 召回后做精排

**理由：**
- 消除双 Embedder 实例，bi-encoder 模型只加载一次（ChromaStore 内部持有）
- Retriever 成为纯粹的透传层，无独立存在价值
- 调用方更简洁：`store.query("排序算法")` 而非先创建 Embedder 再传向量
- RAG 模块从 6 个文件减为 5 个，职责边界更清晰

**曾考虑的替代方案：**
- Embedder 做成单例 —— 治标，Retriever 本身仍是透传层
- ChromaStore 暴露 embedder —— 增加耦合，不如内部消化

---

### 决策 27 — RagLoader 设计决策

**背景：** Loader 是 RAG 数据的唯一入口，需要管理加载状态以支持降级机制。Store 和 Reranker 需保持单例，Loader 如何获取这些实例影响整体耦合。

**决策：**

- **Store/Reranker 构造函数注入，不做内部创建**：`RagLoader(store: ChromaStore, reranker: Reranker)`。单例由 `src/rag/__init__.py` 模块级懒加载管理
- **Chunker 内部创建**：无状态，不需要注入
- **状态机管理加载状态**：`LoaderState` 枚举（IDLE / LOADING / READY / ERROR），通过 `state` 属性和 `error` 属性暴露
- **同步 + 锁保证串行**：`auto_load()` 和 `load_file()` 均为同步方法，用 `threading.Lock` 保护。LOADING 状态下拒绝新请求
- **异常不抛出，写入状态**：加载失败时 `state = ERROR` + `error_msg = str(e)`，由用户/调用方根据状态决策重试或降级
- **内存模式全量，持久化模式增量**：内存每次全量加载；持久化通过 `.last_update` 时间戳比对 mtime 做增量
- **memories 目录为空不处理**：不创建空 collection，等记忆模块实际写入后 `load_file()` 增量入库

**理由：**

- 注入优于内部创建：避免在 Loader 内部重复构建 Store/Reranker 实例，既保持单例又符合依赖反转原则
- 状态机替代简单的 `is_ready() bool`：调用方需要区分 "还在加载" vs "加载失败"，前者需等待后者需用户介入
- Loader 本身不开线程：同步 + 锁，调用方如需异步自己开 thread，保持职责单一
- 异常写入状态而非抛出：LOADER 被多处调用，抛异常意味着每个调用方都要处理，状态机统一管理

**曾考虑的替代方案：**

- Loader 内部创建 Store/Reranker —— 多实例问题
- `auto_load_async()` 内部开线程 —— 增加 Loader 复杂度，异步包装应是调用方职责
- `is_ready() + is_error()` 两个方法 —— 不如单一 state 枚举清晰
- 异常直接抛给调用方 —— 每个调用点都要 try/except，不如状态统一

---

### 决策 28 — RAG 公共 API 极简化

**背景：** `src/rag/__init__.py` 最初暴露了 `get_store()`、`get_reranker()`、`get_loader()` 三个 getter，调用方需要手动拼接 `store.query()` → `reranker.rerank()` 流程。外部只需两件事：检索和重载。

**决策：**

- `src/rag/__init__.py` 仅暴露三个公共函数：`search(query_text, collection, top_k)`、`load(target)`、`is_ready()`
- `search()` 内部串联 `store.query()` → `reranker.rerank()`，LOADING/ERROR 状态时抛出 `RuntimeError`
- `load(target=None)` 透传 `loader.reload(target)`：None 全量重载，非空匹配路径重载
- `is_ready()` 返回 `loader.state == LoaderState.READY`，供外部轮询
- `ChromaStore` 和 `Reranker` 完全隐藏在模块内部，外部不可见

**理由：**

- 外部调用方不需要知道 Store/Reranker 的存在，只需"给我结果"
- `search()` 在 LOADING/ERROR 时抛异常，语义清晰，调用方自然选择 try/except 或 `is_ready()` 轮询
- 2+1 个函数构成完整公共 API，学习成本为零
- 内部单例管理、双检锁、daemon 线程等复杂度对外透明

**曾考虑的替代方案：**

- 暴露 `get_store()` + `get_reranker()` —— 调用方需理解内部 pipeline，增加使用成本
- `search()` 在 LOADING 时阻塞等待而非抛异常 —— 阻塞时长不可控，不如让调用方决定何时重试

---

### 决策 29 — MemoryStore 与 RAG 解耦（观察者模式）

**背景：** 原设计 MemoryStore 直接持有 RAG 内部组件（Chunker、ChromaStore、Reranker）的引用，`write_memory()` 和 `query_cross_agent()` 内部直接调 RAG。这导致 Memory 模块与 RAG 内部实现细节强耦合，换 RAG 底层就得改 MemoryStore。

**决策：**
- MemoryStore 只管文件系统读写，不持有任何 RAG 引用
- 解耦方式为观察者模式：Store 写文件后发射 `MemoryWritten` / `MemoryDeleted` 事件
- `MemoryIndexer` 监听事件→调用 RAG 公共 API（`rag.load()` / `rag.delete()`）
- `MemoryRetriever` 封装 RAG `search()`，返回 Memory 对象
- Store 通过 `on_write(callback)` / `on_delete(callback)` 注册监听器，callback 同步执行

**理由：**
- Store 不再知道 RAG 的存在，换 RAG 实现只需改 Indexer
- 事件驱动解耦，写入路径（Store→Indexer→RAG）和读取路径（Retriever→RAG）完全独立
- 不需要引入消息队列或异步框架，Python 原生 callback 足够

**曾考虑的替代方案：**
- Store 依赖 RAG 公共 API 而非内部组件 —— 耦合方向反了，RAG 是基础设施，Memory 是上层
- 全异步消息队列 —— 过度设计，当前规模不需要

---

### 决策 30 — 一文件一条记忆 + front-matter KV 格式

**背景：** 原设计 `data/memories/<agent>/<date>.md` 一个文件包含多条记忆，Chunker 按 `---` 切分为多个 Chunk。这导致记忆之间边界模糊，增删改单条记忆需要操作整文件，且 metadata（id、agent、time）无法持久化到文件中。

**决策：**
- **一条 Memory 一个文件：** `data/memories/<agent>/<yyyyMMddHHmmss.fff>.md`，文件名即时间戳，天然有序
- **Front-matter KV 格式：** 文件以 `---` 包裹的 KV 开头（`id`、`agent`、`time`），后接正文 content
- **所有文件统一格式：** reference 文件同样加 front-matter（`category`），Chunker 自动解析注入 metadata
- **`file_path` 可从 `memory.time` 推导：** 不存储在 Memory 对象中

**理由：**
- 一文件一条：`source_file` 天然是单条记忆标识，增删精确到文件级别
- Front-matter 持久化 metadata：`/ragreload` 全量重载时不丢
- 时间戳文件名：天然有序，浏览记忆时一目了然
- 所有文件统一格式：一套 Chunker 处理 reference 和 memory

**曾考虑的替代方案：**
- 按日期文件存多条记忆 —— 增删需要改整文件，Chunk 粒度与文件粒度不一致
- JSON 文件 —— 不如 Markdown 人机可读
- 文件名用 uuid —— 排序混乱，人工无法浏览

---

### 决策 31 — Chunker 通用化 + front-matter 解析

**背景：** Chunker 原是 RAG 模块专属（`src/rag/chunker.py`），仅做 `---` 机械切分。M3 的 MemoryBuilder 也需要用 Chunker 解析 LLM 输出的 Markdown，同时所有文件需要 front-matter 支持以持久化 metadata。

**决策：**
- Chunker 从 `src/rag/` 移至 `src/utils/chunker.py`，成为通用工具
- `chunk()` 新增 front-matter 解析：文件开头第一对 `---` 提取 KV → metadata 注入所有 Chunk → 剥离 front-matter → 后续 `---` 正常切分
- metadata 优先级：front-matter KV < chunk() 的 metadata 参数（调用方可覆盖）
- `source_file` 仍由 RagLoader 自动注入，不写在 front-matter 中
- 解析用简单 `key: value` 格式，不用 YAML（避免额外依赖）

**理由：**
- 移至 utils 消除 memory→rag 的依赖方向问题
- front-matter 解析让 metadata 持久化在文件中，与程序注入互补
- 简单 KV 解析零依赖，足够覆盖 Memory（id/agent/time）和 Reference（category）的场景
- 调用方覆盖优先级保证灵活性

**曾考虑的替代方案：**
- Chunker 留在 RAG —— MemoryBuilder 需要依赖 RAG，耦合方向不合理
- 用 YAML front-matter —— 需要 `pyyaml` 依赖，当前需求不必要
- 不改 Chunker，由 RagLoader/MemoryStore 各自解析 front-matter —— 重复逻辑

**实施细化（2026-07-01）：**
- `chunk()` 返回值从空列表变为 front-matter 强制要求：无 front-matter 的输入返回 `[]`，在调用处留 TODO 桩供未来扩展（如纯文本自动注入默认 metadata）
- 实现方式：编译正则 `_FM_RE` 匹配 `^---...---`，解析失败 → 返回 `[]`；成功 → `{**fm_meta, **caller_meta}` 合并（caller 覆盖）

---

### 决策 32 — MemoryBuilder 替代 Compressor（对话构建而非压缩）

**背景：** 原设计 `MemoryCompressor.compress(conversation) -> list[Memory]` 定义为"LLM 对话压缩成记忆"，但这个名字暗示只是压缩/摘要，而不是主动从对话中提取关键信息构建记忆。

**决策：**
- 重命名为 `MemoryBuilder`，职责定义为"从对话中提取/构建记忆条目"
- 系统提示词放在 `data/prompts/memory/builder.md`（替代已删除的 `memory_compressor.md`）
- LLM 输出 Markdown 格式（`---` 分隔 + front-matter），Builder 注入 `id`/`time`/`agent` 后复用 Chunker 解析
- `memory/__init__.py` 提供 Facade：`build_memories(conversation, agent, llm, store, sync_mode=False)`
- `sync_mode=True` 同步返回 `list[Memory]`；`False` 后台线程执行，立即返回 `None`
- 异步控制在 Builder Facade，MemoryStore 本身纯同步

**理由：**
- "构建"比"压缩"更准确 —— LLM 主动判断什么值得记住并组织为 Memory，而非机械压缩
- LLM 输出与 memory 文件同格式，一套 Chunker 两端复用
- 异步由上层控制，Store 保持简单同步

**曾考虑的替代方案：**
- 保持 Compressor 名字 —— 名不副实，压缩暗示降维/摘要而非提取
- LLM 输出 JSON —— Markdown 更自然，且与文件格式统一
- MemoryStore 内部做异步队列 —— 职责混淆，Builder 是更好的异步控制点

---

### 决策 33 — 日志系统：标准库 logging + 按大小轮转

**背景：** 项目当前没有任何日志系统，调试依赖 `print()` 或异常堆栈。M3 记忆模块即将开始实现，MemoryStore 任务清单中已写明"失败仅记日志，不抛异常"，需要一个统一的日志基础设施。

**决策：**
- 使用 Python 标准库 `logging`，零额外依赖
- 提供 `get_logger(name: str) -> logging.Logger` 单一入口，懒加载初始化（首次调用自动配置 handler）
- 文件输出使用 `RotatingFileHandler`，按大小轮转（10MB × 5 备份），写入 `data/logs/app.log`
- 控制台输出使用 `StreamHandler(stderr, ERROR+)`，不干扰 `rich` 的 stdout 渲染
- 2 个环境变量：`LOG_LEVEL`（默认 `INFO`）、`LOG_DIR`（默认 `data/logs/`）
- 日志格式：`2026-07-01 14:30:00 | INFO     | memory.store | 写入记忆成功`

**理由：**
- 标准库足够 —— 项目是命令行工具，不是分布式系统，不需要 ELK/Sentry 等外部日志平台
- 按大小轮转比按天轮转更适合 CLI 应用 —— 使用频率不均，按天可能在某次密集使用中产生超大文件
- stderr 而非 stdout —— `rich` 接管 stdout 做 Markdown 渲染，日志写 stdout 会破坏终端输出
- 懒加载 —— 不强制在 `main.py` 显式初始化，任意模块 `get_logger(__name__)` 即开即用
- 环境变量控制级别和路径 —— 开发期设 `DEBUG` 看详细日志，正式使用设 `WARNING` 减少噪音

**曾考虑的替代方案：**
- `print()` 到 stderr —— 无级别过滤、无轮转、无时间戳，不可维护
- `loguru` —— 功能强大但引入额外依赖，当前需求标准库完全覆盖
- `TimedRotatingFileHandler` 按天轮转 —— CLI 应用使用频率不均，按大小更可预测
- 仅在 `main.py` 初始化 root logger —— 强依赖启动顺序，`get_logger()` 调用在 import 阶段就会执行，此时 root 可能尚未配置

---

### 决策 34 — Message 通用消息模型：7 字段 + 模块分离

**背景：** M3 任务 2 最初规格 Message 仅有 3 个字段（`role`/`content`/`timestamp`）。讨论后发现 Message 需要承载更多语义：用户输入、系统指令、工具调用、工具结果、LLM 回复，以及 LLM 内部推理过程。同时 `06_output_format.md` 的 JSON Schema（`thinking` + `action`）需要映射到统一的消息模型。

**决策：**

- **Message 7 字段：** `id`（uuid hex）、`timestamp`（datetime）、`role`（user/assistant/system）、`message`（展示文本）、`event_type`（事件类型标识）、`event_payload`（dict | None）、`thinking`（str | None）
- **`event_type` 区分消息语义：** 候选值包括 `user_input`、`system_input`、`tool_call`、`tool_call_result`、`finish` 等，后续随工具扩展追加
- **`role` 保留：** `event_type` 不能替代 `role` 做消息来源控制。例如 `tool_call_result` 和 `system_input` 都是 `role="system"`，需靠 `event_type` 区分语义
- **`message` 为展示文本：** 始终是终端显示内容，与 `action.message` 语义一致
- **`thinking` 为 LLM 推理：** 对齐 `06_output_format.md` Schema 顶层 `"thinking"`；user 消息恒为 `None`；未来由 `SHOW_THINKING` flag 控制展示（当前不做）
- **模块位置：** Message 抽出为 `src/message.py`，作为项目级通用基础设施，而非放在 `src/memory/schemas.py` 中

**理由：**

- Message 是整个系统的数据总线（CLI → Agent → LLM → Memory），放在 memory 下会造成其他模块反向依赖 memory
- `role` + `event_type` 双层语义：role 回答"谁发的"，event_type 回答"这是什么类型的消息"，职责不重叠
- `thinking` 独立字段避免推理过程混入 `message` 污染展示
- `event_payload` 用 dict 足够灵活，不需要为每种工具定义具体 TypedDict

**曾考虑的替代方案：**

- Message 放在 `src/memory/schemas.py` —— CLI/LLM/Agent 都需要 import memory 模块，耦合方向不合理
- 用 `event_type` 替代 `role` —— 无法区分"系统指令"和"工具结果"的消息来源，消息路由时需额外判断
- `thinking` 混在 `message` 中 —— 展示时需要额外解析剥离，不干净
- `event_payload` 用具体 TypedDict 类型 —— 工具类型不断扩展，维护成本高

---

### 决策 35 — MemoryStore 格式化逻辑抽出到 utils/formatters.py

**背景：** 实现 `MemoryStore` 时，`write_memory()` 内部需要两个 pure 函数：将 `datetime` 转为 `yyyyMMddHHmmss.fff.md` 文件名、将 `Memory` 对象拼装为 front-matter Markdown。最初计划将这两个函数作为 `MemoryStore` 的 `@staticmethod`，但 static method 内聚性差，且这两个函数是通用工具，未来可能被 MemoryBuilder 或 Chunker 复用。

**决策：**
- 创建 `src/utils/formatters.py`，包含两个函数：`timestamp_to_filename(time: datetime) -> str` 和 `memory_to_markdown(agent: str, memory: Memory) -> str`
- `MemoryStore` 不持有格式化逻辑，直接 `from src.utils.formatters import ...` 调用
- 函数保持纯函数风格（无状态、无副作用），职责范围限定为格式化

**理由：**
- 格式化逻辑是通用工具，不属于 Store 的职责范围，抽出后 `src/utils/` 下 `chunker.py` + `formatters.py` 形成工具集
- Store 类更轻量，只关心文件读写和事件发射
- 纯函数天然可复用，MemoryBuilder 后续也可能用到

**曾考虑的替代方案：**
- 保留在 Store 作为 `@staticmethod` —— 不解决复用问题，且 static method 暴露为公共 API 容易误导调用方
- 内联写在 `write_memory()` 中 —— 方法过长，SRP 违规

### 决策 36 — Memory 类别重构：fact/preference 两分类 + builder 严格 JSON 输出

**背景：** 最初设计 Memory 输出为 `---` 分隔的自由 Markdown，Memory 无类别字段。用户重写 `data/prompts/memory/builder.md` 后，决定用结构化 JSON 输出替代自由 Markdown，并为 Memory 引入 `category` 分类。

**决策：**
- Memory 新增 `category: str` 字段，取值 `"fact"` 或 `"preference"`，默认 `"fact"`
- `builder.md` 输出严格 JSON：`{"facts": "<string>", "preferences": "<string>"}`，两个字段均为必填，无内容填空字符串
- 废弃原 4 分类设计（facts/preferences/entities/events），entities 和 events 合并入 facts
- LLM 每次调用最多产出 2 条 Memory（每字段非空生成一条）
- `memory_to_markdown()` front-matter 新增 `category`，`chunk_to_memory()` 从 metadata 提取（缺失默认 `"fact"`）
- Builder 不依赖 Chunker —— 直接 `json.loads()` 解析后构造 Memory 列表

**理由：**
- 两分类覆盖所有记忆场景：事实（客观、长期）和偏好（主观、程度）
- 严格 JSON 输出可控、可解析，比自由 Markdown + Chunker 更可靠
- 每次最多 2 条记忆，输出精简，LLM 不会过度提取
- front-matter 带 category 后，RAG 检索可按类别过滤 (`filter={"category": "preference"}`)

**曾考虑的替代方案：**
- 4 分类（facts/preferences/entities/events）—— entities 和 events 与 facts 边界模糊，增加 LLM 分类负担
- 数组输出 `{"facts": [], "preferences": []}` —— 不可控，LLM 可能生成过多条目
- 保留 `---` 分隔的自由 Markdown —— 解析脆弱，需依赖 Chunker，且无法区分类别

### 决策 37 — MemoryBuilder JSON 强制模式 + 换行拆分

**背景：** 实现了 `MemoryBuilder` 后，用户要求 LLM 输出强制 JSON 以确保格式可靠，同时要求每条简短陈述独立成为一条 Memory（而非整个 facts/preferences 字符串作为一条）。

**决策：**
- `build()` 调用 `chat_flash()` 时传入 `response_format={"type": "json_object"}`，OpenAI SDK 强制模型输出合法 JSON
- `json.loads()` 解析后，`facts` 和 `preferences` 字符串按 `\n` 拆分为多行，每行一条 Memory（过滤空行）
- Builder 不再依赖 Chunker —— 文本拆分逻辑内聚在 `build()` 中
- 每条 Memory 独立存储，独立检索

**理由：**
- `response_format` 比仅依赖提示词更可靠，消除非法 JSON 的风险
- 换行拆分符合新版 `builder.md` 的语义（每条一个简短陈述），`\n\n---\n\n` 拼接后由 Chunker 切分，每条独立 RAG 可检索
- flash tier 足够处理结构化提取，不需 pro tier

**曾考虑的替代方案：**
- 仅提示词约束 JSON 格式 —— 偶发非法 JSON，解析脆弱
- 整段 content 存为一条 Memory —— 粒度太粗，检索时无法精准定位单条事实/偏好
- 每行存为独立文件 —— 同时间戳文件名冲突，需 `category` 字段区分

### 决策 38 — 记忆模块统一入口 + 文件名 category + --- 分隔符

**背景：** 实现了 MemoryBuilder、MemoryIndexer、MemoryRetriever 后，需要统一的对外接口。同时发现同一 LLM 调用产出的 facts 和 preferences 共享时间戳导致文件名冲突，且每行独立存文件粒度太细。

**决策：**
- `src/memory/__init__.py` 作为唯一公开入口，暴露 `init()`、`build_memories()`、`search_memories()`、`delete_memory()` 四个函数
- 内部双检锁懒加载单例 MemoryStore / MemoryIndexer / MemoryRetriever（类 RAG 模块的 `_ensure_init` 模式）
- 文件名格式改为 `yyyyMMddHHmmss.fff.<category>.md`，不同 category 不冲突
- Builder 内部：LLM 返回的多行文本按 `\n` 拆分后，用 `\n\n---\n\n` 拼接为一个 content，一 category 一个文件
- Chunker 解析文件时剥离 front-matter 后按 `---` 切分，每条事实/偏好独立成为 RAG chunk

**理由：**
- 统一入口降低调用方认知负担，不需要 import 子模块
- filename 加 category 解决同时间戳冲突，不需要错开时间戳（更干净）
- `---` 分隔符复用现有 Chunker，不用单独写拆分逻辑，且一条一 chunk 检索粒度最细
- 外部 API 与 RAG 模块风格一致（`init`/`search`/`delete`）

**曾考虑的替代方案：**
- 暴露子模块让调用方自己组装 —— 耦合度高，调用方需了解内部模块关系
- 每行独立文件 —— 同时间戳文件名冲突，需错开时间戳（脆弱）
- 整段存一条不拆分 —— RAG 检索粒度太粗

---

### 决策 39 — Chroma in-memory `delete(where=)` 不可靠：`delete_collection` 替代方案

**背景：** 测试发现 ChromaDB v1.5.9 in-memory 模式下 `col.delete(where={"source_file": "..."})` 间歇性不匹配（返回成功但实际 0 条删除），导致 `/ragreload` 全量重载后偶发重复条目。经检索确认这是 Chroma 自身已知问题（[#4275](https://github.com/chroma-core/chroma/issues/4275) 删除后查询结果异常 v1.0.0+；[#5367](https://github.com/chroma-core/chroma/issues/5367) `query()` where filter 不匹配但 `get()` 正常）。项目路径规范化（`Path.resolve()` + `str().replace("\\", "/")`）两端一致，排除自身 bug。

**决策：**
- 全量 `/ragreload`（无参数）：先调 `ChromaStore.delete_collection()` 原子删除整个 collection，再遍历所有 `.md` 文件重新入库。彻底绕过 `delete(where=...)` 的 metadata 匹配问题
- 单文件 `/ragreload <keyword>`：保留现有 `_load_one()` 逻辑（`remove` + `add`），接受间歇性不匹配——单文件场景影响范围极小，不值得引入 collection 重建
- `ChromaStore.delete_collection(name)` 封装 `self._client.delete_collection(name)`，try/except 静默处理 collection 不存在的情况

**理由：**
- `delete_collection` 是 Chroma 的原子操作，不依赖 metadata filter，可靠性远高于 `delete(where=...)`
- 全量重载本身就遍历所有文件，drop 后重建的总工作量与逐文件 `remove` + `add` 相当
- 单文件重载走 `delete_collection` 会清掉所有其他文件的数据，不可行；但单文件场景下 `where` 漏删只影响一个文件，且下次全量重载会自动修正
- 这是 Chroma 上游 bug，等待修复不现实（#4275 从 v1.0.0 到 v1.5.9 未修）

**曾考虑的替代方案：**
- 等待 Chroma 官方修复 —— #4275 跨越 5+ 个大版本未修，不可依赖
- 切换到持久化模式 —— 持久化模式同样用 DuckDB，bug 可能存在；且内存模式是设计决策 3 的约定
- 用 `col.get(where=...)` + `col.delete(ids=[...])` 替代 —— `get(where=...)` 同样有 metadata 匹配问题（#5367）
- 全量和单文件统一用 `delete_collection` —— 单文件场景 drop 整个 collection 代价不可接受

---

### 决策 40 — Agent Loop 对话历史管理

**背景：** M4 需要设计 Agent Loop 的对话历史结构。当前 `LLMHandler` 用 `list[dict]`（OpenAI 原生格式），但 M3 已定义了 `Message` 数据类（7 字段，覆盖所有消息类型）。需要在裸 dict 和自定义类型之间选择。

**决策：** Agent Loop 内部用 `list[Message]` 管理对话历史。调 LLM 时转换：`[{"role": m.role, "content": json.dumps(dataclasses.asdict(m))} for m in messages]`。完整序列化，不裁剪，不因 event_type 改变结构。

**理由：**
- `Message` 已在所有模块（CLI/Agent/LLM/Memory）共用，保持一致
- 完整序列化不变形 → LLM 供应商的缓存命中策略能正常工作
- 比 `ConversationContext` 轻量，比裸 dict 类型安全

**曾考虑的替代方案：**
- 裸 `list[dict]` —— 简单但失去类型安全，`event_payload`/`thinking` 等字段无处存放
- `ConversationContext` 封装类 —— 过度抽象，当前只有一个 LLM 后端
- 裁剪序列化（按 event_type 过滤字段）—— 破坏缓存命中率

---

### 决策 41 — 工具结果注入方式

**背景：** Agent Loop 中 LLM 选工具 → 执行 → 结果需喂回 LLM 继续推理。项目使用自定义 JSON 输出格式（非 OpenAI 原生 function calling），`role: "tool"` 需要配套 `tool_call_id` 配对，增加不必要复杂度。

**决策：** 工具结果以 `role: "user"` 注入对话历史，`event_type: "tool_call_result"` 区分语义。不引入 OpenAI 原生 tool_call_id 配对。

**理由：**
- 我们没有用 OpenAI 的 native function calling（`tool_choice` 参数），LLM 是纯文本推理选工具
- `role` 只管消息来源控制，`event_type` 负责语义区分，各司其职
- 简单，兼容任意 OpenAI-compatible 后端

**曾考虑的替代方案：**
- `role: "tool"` + `tool_call_id` —— 需按 OpenAI tool call 协议维护配对，额外复杂度无实际收益

---

### 决策 42 — Agent Loop 终止条件

**背景：** Agent Loop 需要明确的终止/挂起条件，防止无限循环。

**决策：** 三个终止条件：
- `finish` — LLM 自主判断任务完成，正常退出
- `ask_user` — LLM 需要用户输入，挂起等 CLI `input()`
- `max_rounds` — 安全阀，由 `AGENT_MAX_ROUNDS` 环境变量控制，默认值后续定

**理由：**
- `finish`/`ask_user` 是 LLM 自主决策，逻辑由系统提示词控制，代码层只需 > 0 的硬上限
- 环境变量化避免硬编码，部署时可调整

**曾考虑的替代方案：**
- 不加 max_rounds —— 网络异常或 LLM 幻觉可能导致死循环
- 更多终止条件（错误终止、超时终止）—— 当前阶段不需要，后续按需添加

---

### 决策 43 — Tool 装饰器 + input_schema 设计

**背景：** M4 需要工具注册机制。MCP 协议使用完整 JSON Schema（含 type/required），但 Python 的 type hints 已包含类型信息，手写 type 是冗余，且给了一致性出错窗口。

**决策：** 用 `@tool` 装饰器注册工具。`input_schema` 只写 LLM 真正需要的 —— 参数描述和默认值：
```python
@tool(
    purpose="...", use_when="...", do_not_use_when="...",
    expected_output="...",
    input_schema={"path": {"description": "文件路径"}, "line_from": {"description": "起始行号", "default": 1}},
)
def read_content(path: str, line_from: int = 1, line_to: int | None = None) -> Message: ...
```
`type` 从 type hint 自动推断，`required` 从是否有默认值自动推断，均在装饰器阶段（`inspect.signature`）完成。

**理由：**
- 比 MCP 的完整 JSON Schema 少写一半，不手写 type 和 required，消除冗余和一致性风险
- `input_schema` 是 LLM 看到的 ground truth，type hint 只是代码层的类型检查
- 装饰器阶段一次性完成推断，运行时无需重复计算

**曾考虑的替代方案：**
- 完整 JSON Schema（MCP 方案）—— type/required 冗余，手写和 type hint 存在一致性风险
- `Annotated[str, "文件路径"]` —— 每个参数都包一层，签名变长，未选择

---

### 决策 44 — event_payload → 函数入参映射

**背景：** LLM 返回 JSON `action.args` → 解析为 `event_payload: dict` → 需要映射到 Python 函数调用的入参。

**决策：** 直接 `**kwargs` 解包，不做额外映射层。
```python
tool = self._tools[action["tool"]]
result = tool.handler(**action["args"])  # read_content(path="/...", line_from=1)
```
`event_payload` = `action.args`，key 名由 `input_schema` 的 key 保证与函数参数名一致。

**理由：** Python 原生能力足够，不需要参数名转换层。

**曾考虑的替代方案：** 无。

---

### 决策 45 — 工具可见性控制

**背景：** 不同 Agent 需要不同的工具集。主 Agent 有 `dispatch_*` 工具，子 Agent 不应看到这些。

**决策：** `@tool` 加 `agent` 参数：
- `agent=None`（默认）→ 所有 Agent 可用
- `agent=["main", "resume"]` → 仅指定 Agent 可用

全局加载所有 tool（`ToolRegistry`），Agent 构建 system prompt 时只收集有权限的 tool（`to_xml()` 过滤），调用时再加一道门禁检查。

**理由：** 加载和过滤分离 —— 全局注册避免分散管理，过滤在提示词生成时集中处理，门禁是最后防线。

**曾考虑的替代方案：**
- 每个 Agent 声明自己要加载的工具模块 —— 分散，改动时多处更新

---

### 决策 46 — 工具错误处理

**背景：** 工具执行可能失败（LLM 参数理解错误、文件不存在等），错误信息需要让 LLM 有能力自我纠正。

**决策：** 工具抛异常 → Agent Loop 捕获 → 构造 `Message(event_type="tool_call_result", message="[Error] ...")` → 喂回 LLM。错误消息需携带足够上下文（如 LLM 参数错误时附带 `arguments_schema`）。原则：**给够上下文让 LLM 有能力自修复**。具体包装策略后续迭代。

**理由：** LLM 看到错误 + 工具定义后可以重试或改方式，比简单抛异常终止 loop 更鲁棒。

**曾考虑的替代方案：**
- 直接抛异常终止 loop —— 过于粗暴，LLM 长上下文下偶尔参数偏差是正常现象

---

### 决策 47 — ToolRegistry 全局注册表

**背景：** 工具注册后需要被 Agent 发现。`BaseAgent` 遍历 `dir(self)` 太重，且职责不应在 Agent 上。

**决策：** `ToolRegistry` 全局注册表：
- `@tool` 装饰器构建 Tool → `ToolRegistry.register(tool)`
- `BaseAgent.__init__` 调 `ToolRegistry.get_for(agent_name)` 按 agent 过滤拉取
- `extra_tools` 参数额外注入，不进全局 Registry

**理由：** 注册和发现解耦，`BaseAgent` 不关心工具来源。

**曾考虑的替代方案：**
- `BaseAgent` 遍历 `dir(self)` 扫描标记方法 —— 太重，职责混乱
- 每个 Agent 手动注册工具列表 —— 容易遗漏

---

### 决策 48 — process() 接口：Message → Response

**背景：** M1 的 `Handler.process(str) -> str` 只返回文本。引入 questionary 后，handler 需要告诉 App 渲染选项列表、等待审批确认、正常回复。`str` 不够用。

**决策：** `process(input: Message) -> Response`。`Response` 是 CLI 指令层，不进对话历史：
- `finish` — 渲染 markdown，本轮结束
- `select` — 渲染 questionary.select（最后一项固定"自定义输入"），用户选择 → Message → agent loop 继续
- `confirm` — 渲染 questionary.confirm，y → 执行工具，n → 跳过

**理由：** `Response` 语义独立于 `Message`，CLI 指令和对话数据分层清晰。`select` 绑定"返回给 LLM 什么"，`confirm` 绑定"操作是否执行"。

**曾考虑的替代方案：**
- 复用 `Message` 作为 CLI 指令 —— 语义混淆，CLI 指令不应出现在对话历史中

---

### 决策 49 — 意图路由：纯 LLM 驱动

**背景：** 设计文档提到 `Router.classify()`，但决策 15 已定调度 = 工具。需要确认是否还需要独立 Router。

**决策：** 纯 LLM 驱动，不做独立 Router。主 Agent 的 LLM 通过 `dispatch_*` 工具选择调度。`src/main_agent/router.py` 不需要。

**理由：** LLM 原生能力足够做意图识别，独立 Router 增加维护成本且边界情况弱。

**曾考虑的替代方案：**
- 独立 Router（关键词/规则）—— 快但边界弱，需要持续维护
- 混合方案 —— 复杂度高，V1 不必要

---

### 决策 50 — CLI 交互库选型：questionary

**背景：** M4 需要 CLI 提供选项列表和审批确认能力。选项包括 `questionary`、`InquirerPy`、rich 自带 Prompt。

**决策：** 使用 `questionary`。`select` 覆盖选项列表（最后一项"🔧 自定义输入..."），`confirm` 覆盖工具审批。

**理由：**
- API 最简洁（`select()` + `confirm()` 两个函数覆盖所有场景）
- 基于 prompt_toolkit，生态成熟，Windows 兼容性好
- 一个依赖，`uv add questionary` 一句话

**曾考虑的替代方案：**
- `InquirerPy` — 功能更全但更重
- Rich 自带 `Prompt.ask()` — 只有文本输入，无选择菜单
- 自绘 —— 重复造轮子

---

### 决策 51 — Agent 切换机制：Tool-based 异步调用模型

**背景：** 主 Agent dispatch 子 Agent 后，CLI 的 handler 需要切换。原设计用 `Response(type="switch_agent")`，但切换不应是 CLI 指令而应是 App 层操作。

**决策（更新于 M4 实现阶段）：**
- 切换封装为 `@tool`：`switch_to_subagent`（agent=["main"]）+ `switch_to_mainagent`（agent=["*"]），均 `confirm_mode=ALWAYS`
- 子 Agent 会话建模为异步 tool_call：tool_call → 子 Agent 多轮 → tool_call_result(summary)
- 切换信号流：tool handler 返回 `{"__switch__": True, "target": "...", "context": "..."}` → `BaseAgent._execute_tool()` 检测 → 返回 `None` 不包装 tool_call_result → `process()` 设 `_pending_switch` → 返回 `Response(FINISH, switch_agent=..., switch_context=..., switch_tool_call_id=...)`
- App FINISH 分支检测 `switch_agent`：main→sub 时保存 `_switch_tool_call_id`；sub→main 时向主 Agent `_history` 注入 TOOL_CALL_RESULT 完成闭环
- 主 Agent `_history` 中 TOOL_CALL 保留（作为待完成的异步调用），子 Agent 会话不可见
- `/exit_sub` 在 App 层拦截：向子 Agent 注入 system_message 让 LLM 整理上下文 → 调用 switch_to_mainagent
- 子 Agent 无状态，不持有任何持久上下文
- 子 Agent 之间不允许互调（`switch_to_subagent` 仅 main 可见）

**理由：** Tool-based 复用 LLM 已掌握的 function calling 路径；不新增 ResponseType（FINISH + switch 字段）；异步调用模型保证主 Agent 持有全部上下文。

**曾考虑的替代方案：**
- `Response(type="switch_agent")` — 混淆了 CLI 指令和 handler 切换
- 新增 EventType `SWITCH_SUB` — 需要修改 4 处，EventType 承担双重职责
- `App.switch_agent()` 作为独立方法 — 虽然后续封装为 `_get_handler()` + FINISH 分支，而非独立公开方法

---

### 决策 52 — M4 测试子 Agent 实现：JobSearchAgent

**背景：** 计划要求"初期子 Agent 可为桩实现"，但桩无法验证 agent loop + tool + dispatch + return 全链路。原定面试问答 Agent，但切换机制实现后需要一个快速可用的子 Agent 验证全链路。

**决策：** 实现 **JobSearchAgent**（`src/agents/job_search/agent.py`）作为测试用子 Agent：
- 14 个占位符填充职位搜索分析场景
- 可复用现有 `web_search` 工具搜索岗位信息
- 自动获得 `switch_to_mainagent` 工具（agent=["*"] 可见）
- 验证流程：main → switch_to_subagent → JobSearchAgent 对话 → switch_to_mainagent → main 收到总结
- 面试问答 Agent（原 milestone 7）后续按需实现

**理由：** 职位搜索分析场景简单（理解需求 → 搜索 → 分析），无需额外工具即可验证全链路。优先验证切换机制，专业子 Agent 后续按里程碑顺序实现。

**曾考虑的替代方案：**
- 桩实现（返回固定文本）—— 只验证 dispatch 管线，agent loop 和 tool 系统未覆盖
- 面试问答 Agent 先行 —— 需要 RAG 工具，而切换机制尚未验证，应先验证管线再填充功能

---

### 决策 53 — AgentRegistry 设计

**背景：** 主 Agent 需要持有子 Agent 注册表以完成 dispatch。设计文档提到但未细化。

**决策：**
- `AgentRegistry` 放在 `src/agents/registry.py`，**全局单例**（`get_agent_registry()` 双检锁），与 ToolRegistry 对称
- `register(name, agent)` 存入实例的同时，从 `agent._get_*()` 抽取元数据构建 `SubAgentDescriptor`
- `SubAgentDescriptor` 字段：`name` / `display_name` / `description` / `responsibilities` / `hard_constraints`（聚焦路由决策）
- `list_agents_prompt()` 遍历 descriptor，生成格式化列表，通过 `{{SUB_AGENTS_LIST}}` 占位符注入主 Agent system prompt
- "仅 MainAgent 使用"的约束不在数据结构层 → 通过 `switch_to_subagent` tool 的 `agent=["main"]` 可见性控制
- 新子 Agent 注册一步到位：`register("resume", ResumeAgent(...))` → prompt + tool schema 自动更新

**理由：** 与 ToolRegistry 设计理念一致，全局单例降低耦合，SubAgentDescriptor 分离元数据与实例利于 prompt 生成。

**曾考虑的替代方案：** 仅 dict 包装（`register/get/list`）—— 够用但不支持 prompt 自动生成和 tool schema 枚举值动态更新。

---

### 决策 54 — 工具审批模式：ConfirmMode 枚举

**背景：** BaseAgent 的工具调度需要审批门禁（`Response(type="confirm")`），但不是所有工具都需要审批 —— 像 `get_current_datetime` 这类无副作用只读操作不应阻塞用户。需要一个按工具粒度控制审批的机制。

**决策：**
- 新增 `ConfirmMode(StrEnum)` 枚举，三个值：
  - `NEVER` — 无论全局开关，都不审批（如只读查询）
  - `ALWAYS` — 无论全局开关，一律审批（如删除操作）
  - `CONFIG`（默认）— 跟随全局 `TOOL_CONFIRM_ENABLED` 环境变量
- `Tool` dataclass 新增 `confirm_mode: ConfirmMode` 字段，默认 `CONFIG`
- `@tool` 装饰器新增 `confirm_mode` 参数
- `confirm_mode` 不进入 `to_xml()`，对 LLM 完全透明

**理由：**
- 枚举提供类型安全，比裸字符串 `"never"`/`"always"`/`"config"` 更可靠
- `StrEnum` 继承 `str`，序列化/比较自然，repr 可读
- 不进 XML 保证了 LLM 不会知道审批策略，无法通过构造特定输出来绕过审批
- 三级粒度覆盖所有场景：只读无条件免审、危险操作强制审批、常规操作跟随全局策略

**曾考虑的替代方案：**
- `bool` 字段（`needs_confirm: bool`）—— 只有两态，无法表达"跟随全局"语义
- 全局白名单/黑名单 —— 配置分散，不如工具自描述
- 暴露给 LLM —— 安全风险，LLM 可能尝试说服用户绕过审批

---

### 决策 55 — Agent Loop 中间进度回传：Response(type="progress")

**背景：** Agent loop 内部可能执行多轮工具调用，每轮可能耗时数秒。如果 `process()` 只在最终 `finish` 时返回，用户会看到长时间无反馈的黑屏，不知道后台在做什么。

当前 `process()` 是同步阻塞的一次性调用（`input → loop → finish`），无法在中间步骤向 App 报告进度。

**决策：**
- `Response` 新增 `type="progress"`，表示 agent loop 有中间步骤已完成、等待继续
- `Message` 新增静态工厂 `internal_continue()`，生成 `event_type="internal_continue"` 的消息
- `BaseAgent.process()` 拆分为"追加用户输入"和"继续 loop"两种模式：
  - `event_type != "internal_continue"` → 追加用户输入到 history → 从 round 0 开始
  - `event_type == "internal_continue"` → 不追加、从上次 `_round_idx + 1` 继续
- `_round_idx` 提为实例属性，跨 `process()` 调用持久化
- 工具执行后不 `continue` 下一轮，而是 `return Response(type="progress")`；App 渲染后立即调 `handler.process(Message.internal_continue())` 推进
- `finish` / 审批 `confirm` 正常 `return`，App 停在等待用户输入

**理由：**
- 不改变 `Handler.process()` 的单入口协议，App 无需感知 agent loop 内部状态
- `internal_continue` 作为事件类型让 `process()` 区分"新用户输入"和"继续推进"
- 把 `_round_idx` 持久化到实例级别，天然支持跨 `process()` 调用恢复

**曾考虑的替代方案：**
- stderr 直接输出进度 —— 格式不可控，与 rich 渲染冲突，且无法利用 `thinking` 面板
- `process()` 改为 generator（`yield Response`）—— 改变协议签名为 async，违反决策 2（同步代码）
- 让 App 在另一个线程轮询 —— 过度复杂，单线程同步 loop 更可控
- 暴露给 LLM —— 安全风险，LLM 可能尝试说服用户绕过审批

---

### 决策 56 — Message.event_type 枚举化：EventType(StrEnum)

**背景：** `Message.event_type` 此前为 `str` 类型，代码中散布裸字符串（如 `"user_input"`、`"tool_call_result"` 等），拼写错误只能在运行时暴露，且各模块各自理解 event_type 语义，缺乏统一约束。

**决策：** 定义 `EventType(StrEnum)` 枚举，包含 5 个值：
- `USER_INPUT` — 用户输入
- `TOOL_CALL` — 工具调用（LLM 输出）
- `TOOL_CALL_RESULT` — 工具调用结果
- `FINISH` — 对话结束
- `SYSTEM_MESSAGE` — 系统提示/错误恢复

`Message.event_type` 类型改为 `EventType`。所有模块代码中使用 `EventType.USER_INPUT` 等枚举值，不再使用裸字符串。

**理由：**
- `StrEnum` 继承 `str`，`EventType.FINISH == "finish"` 为 `True`，JSON 序列化后为 `"finish"` 字符串，与 LLM 交互无摩擦
- IDE 自动补全 + 静态类型检查，拼写错误在编写阶段暴露
- 集中管理事件类型语义，新增/废弃类型有统一入口

**曾考虑的替代方案：**
- 保持 `str` 类型 + 常量 —— 同样解决拼写问题，但无类型约束
- 使用 `Enum`（非 `StrEnum`）—— `json.dumps()` 输出 `"EventType.FINISH"` 而非 `"finish"`，需额外序列化逻辑

---

### 决策 57 — Message 新增 tool / tool_call_id 一级字段

**背景：** 此前 `Message` 字段不含工具名和工具调用关联信息。`tool_call_result` 的场景下，工具名放在 `event_payload` 内部，工具调用关联 ID 不存在（仅通过对话顺序隐式关联）。随着 `EventType` 枚举明确化，`event_type` 不再承担"这是哪个工具"的语义，需要独立字段承载。

**决策：**
- `Message` 新增 `tool: str | None = None` — 工具名，仅 `tool_call` 和 `tool_call_result` 时填写
- `Message` 新增 `tool_call_id: str | None = None` — 关联的 `tool_call` 消息的 `id`，仅 `tool_call_result` 时填写
- `event_payload` 不再嵌套 `tool` / `tool_call_id`，仅承载纯载荷数据（`tool_call` 时为工具参数，`tool_call_result` 时为调用结果）

**理由：**
- 一级字段比嵌套字典更易于检索和序列化
- `tool_call_id` 显式关联使链式追踪成为可能（tool_call → tool_call_result 的因果链）
- 分离关注点：`tool` 回答"哪个工具"，`event_payload` 回答"什么数据"

**曾考虑的替代方案：**
- 放在 `event_payload` 内部 —— 增加嵌套层级，查询不便
- 不设 `tool_call_id`，靠 `id` 顺序匹配 —— 并发或复杂对话时不可靠

---

### 决策 58 — 工具 handler 返回纯数据

**背景：** 此前 `@tool` 装饰的工具 handler（如 `get_current_datetime()`）直接返回 `Message` 对象，handler 内部自行包装 `event_type`、`role` 等字段。这导致 handler 感知了协议层细节，且不同 handler 的包装方式可能不一致。

**决策：** Handler 返回纯数据（`str` / `dict`），由调用方（`BaseAgent._execute_tool()` / `LLMHandler.process()`）统一包装为 `Message(event_type="tool_call_result", tool=..., tool_call_id=..., event_payload=...)`。

**理由：**
- Handler 只关心业务逻辑，不关心协议格式
- 统一包装点确保所有工具结果格式一致
- 测试 handler 时只需验证返回值数据，无需构造完整 Message

**曾考虑的替代方案：**
- Handler 返回 `Message`（旧方案）—— handler 需感知 Message 结构，跨 handler 格式不一致风险高
- Handler 返回 `tuple[str, dict]` —— 多返回值增加调用复杂度，不如统一 `dict`

---

### 决策 59 — System prompt 隔离

**背景：** 此前 `BaseAgent._history` 第一条是 `Message(role="system", message=system_prompt, event_type="system_prompt")`，将 system prompt 作为 Message 存储。但 system prompt 的结构与其他 Message 不同：它是纯文本注入 OpenAI `{"role": "system", "content": "..."}`，不走 Message JSON 序列化。且 `event_type="system_prompt"` 不在 `EventType` 枚举中。

**决策：**
- System prompt 作为独立字符串 `self._system_prompt` 存储，不混入 `_history`
- `_to_openai()` 构建 messages 数组时，先放入 `{"role": "system", "content": self._system_prompt}`，再追加 `_history` 中各 Message 的 `to_json()`
- `_history` 只存对话消息（user/assistant 角色）

**理由：**
- 语义清晰：system prompt 是静态配置，不是动态消息
- 序列化一致：Message JSON 格式只在对话消息中使用，system prompt 保持原生
- 避免 `event_type` 枚举污染

**曾考虑的替代方案：**
- 新增 `EventType.SYSTEM_PROMPT` —— 增加了枚举值但 system prompt 仍不需要 `id`/`timestamp`/`tool` 等字段
- System prompt 也用 Message JSON 包装 —— LLM 收到的是两层嵌套 JSON，不必要

---

### 决策 60 — 06_output / 07_input prompt 分工

**背景：** 此前 prompt 中只有 `06_output_format.md` 定义 LLM 输出格式，输入侧没有对应的格式说明。LLM 不明确知道自己收到的消息是什么结构，可能影响理解 `tool_call_result` 的正确解析方式。

**决策：**
- `06_output_format.md`：定义 LLM 输出 JSON schema，`role="assistant"`，`event_type∈{tool_call, finish}`，含 `tool`/`event_payload`
- `07_input_format.md`（新建）：定义 LLM 收到的消息 JSON schema，`role="user"`，`event_type∈{user_input, tool_call_result, system_message}`，不含 `tool`/`thinking`
- 原 `07_reserved.md` 顺延为 `08_reserved.md`

**理由：**
- 输入/输出泾渭分明，LLM 清楚区分"自己产出的"和"别人喂给它的"
- 帮助 LLM 正确解析 `tool_call_result` 的结构（`tool_call_id` 链回自己的 `tool_call`）
- 两个 schema 的字段互不越界，设计自文档化

**曾考虑的替代方案：**
- 仅在 06 中描述输入结构 —— LLM 不知道 `system_message` 等类型的语义
- 合并为一个文件 —— 输入/输出混在一起，LLM 容易混淆

---

### 决策 61 — Message.to_json() / from_llm_reply() 统一序列化

**背景：** `BaseAgent._to_openai()` 和 `LLMHandler` 各自用 `json.dumps(dataclasses.asdict(m))` 序列化 Message；`Handler._parse_llm_reply()` 手动解析旧嵌套 schema。多处重复且解析逻辑分散。

**决策：**
- `Message.to_json()` — 实例方法，`dataclasses.asdict()` + `json.dumps(default=str)` 统一序列化
- `Message.from_llm_reply(reply: str)` — 静态方法，按扁平 JSON schema 反序列化，required 字段用 `[]`（缺失即 crash），optional 字段用 `.get()`（默认 `None`）
- `Handler._parse_llm_reply()` 简化为一行委托 `Message.from_llm_reply()`
- `BaseAgent._to_openai()` 改用 `Message.to_json()`

**理由：**
- 序列化/反序列化是 Message 的固有行为，放在类内部最合理
- 未来 schema 变更只需改一处
- `default=str` 处理 `datetime` 等非 JSON 原生类型

**曾考虑的替代方案：**
- 保留 `Handler._parse_llm_reply()` 独立实现 —— 代码重复，BaseAgent 和 LLMHandler 都需各自维护解析逻辑
- 用 `dataclasses.asdict()` 的 `dict_factory` 参数定制序列化 —— 与 `default=str` 等价但更隐晦

---

### 决策 62 — 移除 04_tools.md 硬编码预定义工具

**背景：** `04_tools.md` 此前硬编码了 `ask_user`、`finish`、`return` 三个预定义工具，独立于 `ToolRegistry`。随着 `event_type` 枚举化，`finish` 不再是工具调用而是事件类型（LLM 通过 `event_type="finish"` 结束对话），`ask_user` 和 `return` 也不再作为独立工具存在。硬编码工具与 `{{ADDITION_TOOLS}}` 注入的真实工具并存，LLM 可能混淆。

**决策：** 移除 `04_tools.md` 中所有硬编码的 `<Tool>` 定义，仅保留 `<Tools>{{ADDITION_TOOLS}}</Tools>` 空壳。所有可用工具由 `ToolRegistry` 通过 `{{ADDITION_TOOLS}}` 占位符动态注入。

**理由：**
- `finish` 已改为 `event_type` 枚举值，不再作为工具
- `ask_user` 和 `return` 设计上已废弃（agent loop 通过 `finish` + message 即可覆盖交互和退出场景）
- 单一工具来源（`ToolRegistry`）避免 LLM 看到两套工具列表不一致

**曾考虑的替代方案：**
- 保留 `ask_user` 和 `return` 为注册工具 —— 与 `finish` 语义重叠，增加 LLM 选择负担

---

### 决策 63 — message 默认 "" + event_type 唯一 required

**背景：** `Message` 此前有两个 required 字段 `message` 和 `event_type`。在实际使用中，`tool_call_result` 消息的 `message` 通常为空（工具 stdout 可选），强制填写增加了不必要的样板代码。

**决策：**
- `message` 默认值改为 `""`（空字符串）
- `event_type` 保持为唯一 required 字段
- 字段顺序调整为 `event_type` 在前（required）→ `message` 在后（有默认值），符合 dataclass 规范

**理由：**
- `Message(event_type=EventType.USER_INPUT)` 即可构造最小消息，减少样板
- `tool_call_result` 场景天然无需 message，默认 `""` 语义合理
- 仍然可以在需要时显式传 `message="..."` 覆盖

**曾考虑的替代方案：**
- 保持 `message` required —— `tool_call_result` 每处构造都需手动 `message=""`，增加样板

---

### 决策 64 — Agent Loop 上移至 App 层 + process() 单步执行

**背景：** 原 `BaseAgent.process()` 内部 `for` 循环一次性跑到底，LLM 的每次 TOOL_CALL 对用户不可见。用户需要看到工具调用的中间进度，且审批门禁需要暂停循环等待用户确认。

**决策：**
- `process()` 从内部 `for` 循环改为单步执行：每次调用只做一步（处理输入 → LLM → 分发 → 返回）
- Agent loop 循环由 `App.run()` 内层 `while True` 驱动
- 工具执行暂停时返回 `Response(PROGRESS)` 或 `Response(CONFIRM)`，App 渲染后喂回 `Request(CONTINUE)` 或 `Request(CONFIRM_APPROVED)` 恢复
- 新增实例状态 `_pending_tool: tuple[tool_name, payload, tool_call_id]` 跨 `process()` 调用保存断点
- 内层 `while self._round_counter < self._max_rounds` 仅用于错误恢复（JSON 解析失败、未知工具），正常路径一次退出

**理由：**
- App 层可见工具调用的中间过程（PROGRESS 渲染工具名 + message），不再黑屏等待
- 审批暂停时 App 弹 `questionary.confirm`，用户确认/拒绝后继续或退出
- 保持 `process()` 同步单入口，App 无需感知 Agent 内部状态机
- `_pending_tool` 断点简单直接，不需要 generator/coroutine

**曾考虑的替代方案：**
- `process()` 改为 generator（`yield Response`）—— 改变协议为异步，违反决策 2
- 保留内部循环 + stderr 输出进度 —— 格式不可控，与 rich 渲染冲突
- `process()` 内部回调 App —— 反向依赖，破坏 Handler 协议

---

### 决策 65 — Request 类型（对称 Response）作为 App → Agent 输入协议

**背景：** 原 `Handler.process()` 入参为 `Message`，但 Agent loop 上移后需要区分三种不同的调用场景：用户新输入、PROGRESS 后自动继续、审批通过后恢复执行。复用 `Message` 会导致语义混淆（CONTINUE 不是真正的"消息"）。

**决策：**
- 新增 `src/request.py`，定义 `Request` dataclass + `RequestType(StrEnum)`
- `RequestType` 三个值：`USER_INPUT`（用户输入了文本）、`CONTINUE`（自动继续执行）、`CONFIRM_APPROVED`（用户确认了工具执行）
- `Handler.process()` 签名从 `process(Message) -> Response` 改为 `process(Request) -> Response`
- `Request` 和 `Response` 对称：都是 App ↔ Agent 协议层，都不进对话历史

**理由：**
- `Request` 语义独立于 `Message`，不会把"继续执行"这种控制信号混入对话
- 对称设计：App 用 `Request` 告诉 Agent 做什么，Agent 用 `Response` 告诉 App 渲染什么
- 没有 `CONFIRM_REJECTED`：用户拒绝时 App 不调 `process()`，直接退出内层循环等用户主动输入

**曾考虑的替代方案：**
- 复用 `Message` 作为入参，新增 `event_type="internal_continue"` —— 混淆了对话数据和协议控制，且需要新增 EventType
- 用多个方法（`process_input` / `process_continue` / `process_confirm`）—— 增加 Handler 接口复杂度

---

### 决策 66 — 用户拒绝审批 → 退出内层循环，不调 process()

**背景：** 工具需要审批时，`process()` 返回 `Response(CONFIRM)`，App 弹 `questionary.confirm`。用户拒绝后有两种选择：构造一个"拒绝"结果喂回 LLM，或直接退出等待用户重新输入。

**决策：** 用户拒绝审批 → App 直接 `break` 退出内层循环，不调用 `process()`。下一次用户主动输入时，`process(USER_INPUT)` 检测 `_pending_tool` 是否仍存在 → 存在则说明上次被拒绝 → 在 USER_INPUT Message 的 `event_payload` 中注入拒绝信息（`{"tool": ..., "tool_call_id": ..., "reason": "用户取消了此操作"}`），一条消息同时携带用户文本和拒绝信息。

**理由：**
- LLM 在分析用户意图时同时得知上次调用被拒，可以决定重新尝试或调整方向
- TOOL_CALL 保留在 history 中形成完整调用链：TOOL_CALL → (放弃) → USER_INPUT(拒绝信息)
- 不新增独立消息，保持对话紧凑
- App 层逻辑不变，仅在 BaseAgent 收 USER_INPUT 时做守卫

**更新（M4 实现阶段）：** 原决策认为"LLM 不需要知道审批被拒绝"，实现 switch_to_subagent 后发现 LLM 缺少被拒信息时会误以为工具已执行、等待 result。因此增加拒绝信息注入机制。

**曾考虑的替代方案：**
- 构造 `Request(CONFIRM_REJECTED)` → process() 注入 system_message → LLM 继续 —— 多余，用户拒绝后 LLM 无上下文继续
- `process()` 内部处理审批（阻塞等 stdin）—— 破坏依赖注入，App 层失去对 I/O 的控制
- 直接删除 TOOL_CALL —— 丢失上下文，LLM 不知道刚才发生了什么

---

### 决策 67 — 工具错误上下文增强：工具列表 + 参数 schema

**背景：** 原工具调度在遇到未知工具或执行失败时，给 LLM 的错误信息较简略（仅 `"未知工具：xxx"` 或 `{"error": "..."}`），LLM 缺少足够信息自修正。

**决策：**
- 未知工具 → system_message 附带完整可用工具名列表：`"未知工具：xxx。可用工具：tool_a, tool_b, ..."`
- 工具执行失败 → error payload 附带 `arguments_schema` + `expected_output`，让 LLM 对照检查参数是否正确
- 原则延续决策 46：**给够上下文让 LLM 有能力自修复**

**理由：**
- 工具列表让 LLM 一眼看到正确选项，不需要从 system prompt 里翻
- `arguments_schema` 是工具的真实参数定义，LLM 可以对照找出哪里不对（拼写、缺失 required、类型错误）
- 与决策 46 一脉相承：错误恢复靠信息量，不靠复杂逻辑

**曾考虑的替代方案：**
- 仅告知"未知工具"不列可用工具 —— LLM 需重新解析 system prompt 中的工具列表，浪费一轮
- 仅返回 error string —— LLM 不知道参数哪里错了，只能猜

---

### 决策 68 — MainAgent 位置：`src/agents/main_agent.py`

**背景：** 设计文档原计划 `src/main_agent/` 独立目录放置主 Agent。实现时用户指出 Agent 应统一放在 `src/agents/` 下。

**决策：** `MainAgent` 放在 `src/agents/main_agent.py`，与 `BaseAgent` 同目录。`src/main_agent/` 目录不创建。

**理由：**
- 所有 Agent 统一管理，简化项目结构
- `BaseAgent` 和 `MainAgent` 在同一目录，import 路径更短
- 未来子 Agent 也放在 `src/agents/` 下（如 `interview/`），一致的目录约定

**曾考虑的替代方案：**
- 独立 `src/main_agent/` 目录 —— 增加目录层级，与其他 Agent 位置不一致

---

### 决策 69 — 审批 UI：questionary.select + ConfirmChoice 枚举

**背景：** 审批确认使用 `questionary.confirm`，在某些终端渲染为 `??` 而非正常的 `? (y/N)`，用户体验差。

**决策：** 替换为 `questionary.select` + `ConfirmChoice(StrEnum)` 枚举：
- `ConfirmChoice.APPROVE = "✅ 执行"` / `ConfirmChoice.REJECT = "❌ 取消"`
- App 中比较用枚举值而非裸字符串

**理由：**
- `select` 比 `confirm` 渲染更稳定，在不同终端一致
- 枚举保证选项字符串不写错，类型安全
- emoji 提升视觉辨识度

**曾考虑的替代方案：**
- 保持 `questionary.confirm` 换终端 —— 治标不治本
- 裸字符串比较 `"✅ 执行"` —— 拼写错误风险

---

### 决策 70 — LLMClient.web_search() 两轮 native function calling

**背景：** 需要为 Agent 提供网络搜索能力。DeepSeek API 支持内置 `web_search` 工具，通过 OpenAI 兼容的 function calling 协议调用。

**决策：** `LLMClient.web_search(query)` 实现为两轮对话：
- Round 1：发 system prompt + user query + `web_search` 工具定义 + `tool_choice` 强制选 `web_search`，模型返回 `tool_calls`
- Round 2：喂回 assistant 的 `tool_calls` + `role: "tool"` 结果（`"Provide the result"`），模型整理后返回答案
- 两轮均 `extra_body={"thinking": {"type": "disabled"}}` 关闭推理
- System prompt 将模型定位为"纯搜索工具"而非"拥有工具能力的助手"

**理由：**
- 复用 OpenAI SDK 原生 `tools` / `tool_choice` 参数，无需额外 HTTP 调用
- 两轮协议是 DeepSeek web_search 的标准调用方式
- 关闭 thinking 节省 token、加快响应

**曾考虑的替代方案：**
- 用 `WebSearch` / `WebFetch` 工具做真实 HTTP 请求 —— 需要额外的搜索 API key 和服务
- 一轮调用直接返回搜索结果 —— DeepSeek 需要两轮 tool_call 协议

---

### 决策 71 — WORKING_DIR 环境变量 + get_working_dir() 工具

**背景：** Agent 可能需要在磁盘上读写临时文件，需要一个统一的工作目录。

**决策：**
- 新增 `WORKING_DIR` 环境变量，默认 `data/temp/`，通过 `config.py` 管理
- `get_working_dir()` 工具：`Path.resolve()` 返回绝对路径，自动 `mkdir(parents=True, exist_ok=True)`
- `data/temp/` 加入 `.gitignore`

**理由：**
- 统一工作目录避免文件散落各处
- 默认值开箱即用，环境变量支持部署时自定义
- 自动创建目录避免 LLM 因目录不存在而调用失败

**曾考虑的替代方案：**
- 硬编码 `data/temp/` —— 不够灵活
- 让 LLM 自行选择路径 —— 可能写出项目外的文件

### 决策 72 — MainAgent 重新定位为路由 Agent

**背景：** MainAgent 最初定位为通用"求职助手"，既回答问题又调度子 Agent。随着架构细化，需要明确职责边界，避免路由 Agent 越界执行子 Agent 的专业任务。

**决策：**
- MainAgent 重新定位为"程序员求职助手路由Agent"
- 唯一职责：识别意图 → 分类 → 选择子Agent → 切换入口
- 硬约束明确禁止：不生成简历内容、不提供学习方案、不执行面试模拟、不搜索或分析职位
- 如果用户请求属于子Agent能力范围，必须切换Agent
- 如果无法判断用户需求，必须向用户提问，而不是猜测

**理由：**
- Hub-and-Spoke 架构要求主 Agent 作为纯调度中心，不应与子 Agent 职责重叠
- 明确的职责边界让 LLM 行为可预测，减少"万能型"Agent 的幻觉风险
- 专业化分工：路由归主 Agent，执行归子 Agent

**曾考虑的替代方案：**
- 主 Agent 既路由又执行 —— 职责模糊，容易跳过子 Agent 直接回答，破坏架构
- 主 Agent 完全透明路由（不告知用户切换）—— 用户体验差，不理解为什么要"换人"

### 决策 73 — LLMClient 线程安全单例

**背景：** `LLMClient` 在 5 处被独立实例化（`main.py`、`src/memory/__init__.py`、`src/memory/builder.py`、`src/tools/web_tool.py`），重复创建 OpenAI client 实例浪费连接池资源，且多个实例之间无共享状态。

**决策：**
- `src/llm/__init__.py` 提供 `get_client()` 函数，双检锁（DCL）懒加载单例
- 所有调用方统一使用 `from src.llm import get_client` + `get_client()`
- 线程安全：`threading.Lock` 保护初始化临界区
- `LLMClient` 类本身保持不变，单例仅体现在 `__init__.py` 层面

**理由：**
- 项目使用 `threading` 做后台加载（RAG 初始化、Memory async 模式），需要线程安全
- 双检锁模式与项目现有 RAG/Memory 模块单例风格一致
- OpenAI client 内部管理 HTTP 连接池，单一实例更高效
- 调用方代码更简洁：`get_client()` vs `LLMClient()`

**曾考虑的替代方案：**
- 每个调用方独立实例化 —— 当前做法，浪费连接池资源
- `LLMClient` 自身做 `__new__` 单例 —— 侵入类自身，测试不友好，且与项目模块级单例惯例不一致
- 通过依赖注入传递 —— M4 阶段尚未建立全局 DI 容器，过度设计

---

## 决策 74 — 退出清理统一入口：Lifecycle 模块

**背景：**
- M4 阶段实现了 `build_memories(async_mode)` 后台记忆固化，使用 daemon 线程
- daemon 线程在进程退出时被直接杀死，中间产生的记忆永久丢失
- 需要进程退出前显式等待后台线程完成
- 未来其他模块（RAG、临时文件清理等）也需要退出清理钩子
- 各模块自行管理退出逻辑会导致 main.py 感知过多内部细节

**决策：**
- 新建 `src/lifecycle.py` 作为进程生命周期管理模块
- `register_shutdown(hook, *, name)` — 各模块在初始化时注册无参清理函数
- `shutdown()` — 进程退出前调用，按注册逆序执行所有 hook
- 单个 hook 异常被捕获并记日志，不影响后续 hook 执行
- memory 模块在 `_ensure_init()` 中自动注册 `_shutdown_wait_pending`

**理由：**
- 松耦合：main.py 只调 `lifecycle.shutdown()`，不感知各模块内部清理细节
- 可扩展：以后任何模块需要退出清理，一行 `register_shutdown()` 即可
- 防御性：单个 hook 异常不会阻止其他 hook 执行
- daemon 线程保持不变，`shutdown()` 只提供优雅退出路径，强制杀进程不会被卡住

**曾考虑的替代方案：**
- 各模块暴露独立 `shutdown_*()` 让 main.py 逐个调用 — main.py 与各模块强耦合
- 线程改为非 daemon — 进程会卡住直到所有线程完成，用户体验差
- 仅 memory 模块内建 `shutdown()` — 单点方案，不可扩展

---

## 决策 75 — BaseAgent LLM 调用默认强制 JSON 输出

**背景：**
- Agent LLM 输出格式由 `general_agent/06_output_format.md` 定义为 flat JSON schema
- `process()` 中通过 `_parse_llm_reply()` 解析 JSON，失败时注入 output_format 让 LLM 自修复
- 不强制 JSON 模式时 LLM 可能输出 markdown 包裹的 JSON，增加解析失败概率
- MemoryBuilder 已固定使用 `response_format={"type": "json_object"}`

**决策：**
- `BaseAgent._pro_params` 默认值 `{"response_format": {"type": "json_object"}}`
- `BaseAgent._flash_params` 同样设置，供子类 flash tier 调用使用
- 通过 `**self._pro_params` 注入 `chat_pro()` 调用，无需每个调用点手动传参
- 子类可通过覆盖类变量自定义参数

**理由：**
- 输出格式已明确定义为 JSON，强制模式消除 LLM 擅自包裹 markdown 的可能性
- 减少 JSON 解析失败 → system_message 注入 → 重试的浪费
- 类变量 + `**kwargs` 透传模式与项目现有设计一致（决策 12）
- 子类如需调整（如某些 LLM 不支持）只需覆盖类变量

**曾考虑的替代方案：**
- 每个调用点手动传 `response_format` — 重复代码，容易遗漏
- 不强制 JSON，依赖 LLM 自觉遵守 prompt — 实践表明不可靠，增加重试成本
- 仅在 `chat_pro` 中 hardcode — 剥夺子类自定义能力

---

## 决策 76 — LLM Thinking 可配置开关

**背景：**
- commit `21205f2` 引入了 `LLM_THINKING_ENABLED` 环境变量和对应的 `extra_body` 注入逻辑
- 某些 LLM API provider（如 DeepSeek）在 `chat.completions` 响应中包含 `thinking`/`reasoning_content` 字段
- 这些推理内容在上游被计入 output tokens 计费，但本项目自身通过 `SHOW_THINKING` flag 控制是否展示给用户
- 需要一种方式让用户完全关闭 provider 端的 thinking，以节省 token 消耗和响应延迟
- `web_search()` 场景不需要推理能力，应固定关闭

**决策：**
- 新增 `LLM_THINKING_ENABLED` 环境变量（bool 类型，`is_bool=True`，默认 `"true"`）
- `LLMClient` 新增静态方法 `_thinking_extra_body()`，根据配置返回 `extra_body` dict：
  - `False` → `{"thinking": {"type": "disabled"}}`
  - `True`（默认）→ `{}`（走 provider 默认行为，不做任何干预）
- `chat_pro()` 和 `chat_flash()` 通过 `kwargs.setdefault("extra_body", self._thinking_extra_body())` 注入，调用方可覆盖
- `web_search()` 两轮调用均固定设置 `extra_body={"thinking": {"type": "disabled"}}`，不受全局开关影响
- Agent 层无感知 — thinking 控制完全在 `LLMClient` 管道层完成

**理由：**
- `extra_body` 是 OpenAI SDK 的扩展入口（`chat.completions.create(extra_body=...)`），兼容不同 provider 的 thinking 控制语法（DeepSeek、OpenAI o-series 等）
- 默认启用（`true`）保持 provider 原生体验，用户可按需关闭以节省 token 和延迟
- `web_search()` 固定关闭：搜索场景只需结果整理，不需要深度推理，额外的 thinking tokens 是纯粹浪费
- 环境变量 + config 模块统一管理，与项目现有配置风格一致（决策 12）
- 调用方可传 `extra_body` 覆盖默认值（`setdefault` 不覆盖已存在的 key）

**曾考虑的替代方案：**
- 硬编码禁用 — 剥夺用户选择权，且某些 provider 可能不支持该指令
- 在 Agent 层（`BaseAgent`）控制 — 违背参数分层管理原则（决策 13），thinking 是 LLM API 管道层的事，Agent 不应关心
- 仅控制 `chat_pro` — flash tier 同样可能因 thinking 增加延迟
- `web_search()` 跟随全局开关 — 搜索场景 thinking 无价值，不如固定关闭

---

## 决策 77 — JSON 解析增强：json-repair + 换行转义 + 提示注入节制

**背景：**
- LLM 输出中包含多行文本时，`message` 字段内的物理换行未被转义为 `\n`，导致 `json.loads()` 解析失败（报错后 LLM 重试浪费 token 和轮数）
- 原方案自研了一个状态机 `_repair_newlines()` 修复 JSON 字符串内的裸换行，但只能处理换行问题，无法覆盖其他 LLM 常见 JSON 错误（尾部逗号、引号等）
- `thinking` 字段使用 `parsed["thinking"]` 强制取值，某些 LLM 不输出 `thinking` 时导致 `KeyError`，而 JSON schema 中 `thinking` 本应为可选
- JSON 解析失败时每轮都注入 `output_format` 提示，LLM 连续失败时 history 被同一段提示反复填充

**决策：**
- 引入 `json-repair` 库（PyPI: `json-repair==0.61.2`，零依赖），替换自研 `_repair_newlines()` 状态机
- `Message.from_llm_reply()` 直接使用 `json_repair.loads(reply)`，一次调用覆盖未转义换行、尾部逗号、单引号、缺失引号等 LLM 常见 JSON 错误
- `06_output_format.md` `<Requirements>` 新增约束：JSON 字符串内不得包含物理换行，必须转义为 `\n`
- `thinking` 字段从 `parsed["thinking"]`（强制）改为 `parsed.get("thinking")`（容错）
- `BaseAgent.process()` 新增 `_format_injected` 标记：每次 `process()` 调用的错误恢复循环中仅首次 parse 失败注入 `output_format` 提示，后续失败只 `continue` 重试
- parse 失败时 `logger.debug` 打印原始 LLM 回复，便于定位

**理由：**
- `json-repair` 专为 LLM 畸形 JSON 设计，覆盖场景远超自研状态机，且持续维护（GitHub 1k+ stars）
- 单个 `json_repair.loads()` 替代 try/except + 修复 + 重试三段逻辑，代码量减少
- `06_output_format.md` 约束从源头减少换行问题，`json_repair` 作为容错兜底，双重保障
- `thinking` 可选化匹配实际 LLM 行为（部分模型不输出此字段），与 `tool`/`event_payload` 处理一致
- 提示注入节制避免 history 膨胀：同一轮 `process()` 中 LLM 连续 parse 失败时，重复注入 output_format 无益

**曾考虑的替代方案：**
- 仅强化 prompt 约束，不做代码容错 — LLM 不能 100% 遵守，生产环境需要防御性解析
- 仅自研状态机（`_repair_newlines`）— 只覆盖换行问题，尾部逗号、引号等仍需额外处理
- `demjson3` / `json5` — 侧重非标准 JSON 语法（注释、尾部逗号），不是专门的 LLM 修复方案
- parse 失败每次注入更短提示而非跳过 — 用户明确要求"只提示一次，不要一直塞入提示"

---

## 决策 78 — Agent 切换机制：Tool-based 异步工具调用模型

**背景：** 主 Agent 需要调度子 Agent 执行专业任务（如面试模拟），并在子任务完成后收回控制权。切换时需要携带上下文（用户目标、历史背景等），子 Agent 完成工作后需要将总结带回主 Agent，使主 Agent 能继续决策。需要设计一个保证主 Agent 上下文完整性、子 Agent 无状态的切换机制。

**决策：**
- 切换封装为 `@tool`，LLM 通过标准 tool_call 携带 `sub_agent` + `context`
- 整个子 Agent 会话建模为一次"异步工具调用"：
  - 主 Agent `_history` 中保留 `tool_call: switch_to_subagent(...)` （待完成）
  - 子 Agent 多轮交互不进主 Agent 历史
  - 子 Agent 退出时，向主 Agent `_history` 注入 `tool_call_result(summary)` 完成闭环
- 两个 switch tool：
  - `switch_to_subagent(sub_agent, context)` — 仅 MainAgent 可见
  - `switch_to_mainagent(summary)` — 所有子 Agent 自动注入
- 子 Agent 之间不允许互调
- `/exit_sub` CLI 命令在 App 层拦截：主 Agent 前台时报错，子 Agent 时等价 `switch_to_mainagent("用户主动退出")`
- 不新增 `EventType` 或 `ResponseType`：切换通过 `Response(type="finish", switch_agent=..., switch_context=...)` 表示
- 切换信号流：tool handler 返回 `_SwitchTarget` → `BaseAgent._execute_tool()` 检测 → `BaseAgent.process()` 返回 FINISH + switch → App 内层循环检测 → `App.switch_agent()`
- `AgentRegistry` 放在 `src/agents/registry.py`，仅 MainAgent 持有，App 通过它做 handler 切换

**理由：**
- Tool-based 复用了 LLM 已熟练掌握的 function calling 路径，有 `input_schema` 描述参数、有 `use_when` 约束条件，LLM 不需要学习新输出格式
- 异步调用模型保证主 Agent 始终持有完整上下文（含子 Agent 的总结），子 Agent 无持久状态
- 不新增 EventType 避免了枚举承载"控制流"和"对话事件"两种职责
- 子 Agent 无状态设计简化了实现和调试

**曾考虑的替代方案：**
- Option B（新增 `SWITCH_SUB` EventType）— 需要修改 LLM 输出 schema、Message 解析、BaseAgent 分发、App 循环四个地方，且让 EventType 枚举承担双重职责
- 在主 Agent 中注入子 Agent 全部对话 — 历史膨胀严重，cache miss，LLM 可能混淆两段对话

---

## 决策 79 — `/exit_sub` 主 Agent 前台时报错

**背景：** `/exit_sub` 仅在子 Agent 会话中有意义。在主 Agent 前台时用户误输入，需要明确的错误反馈。后续可考虑动态隐藏命令，但当前阶段以简单明确为优先。

**决策：** 主 Agent 前台时 `/exit_sub` 直接报错 `"当前已是主Agent，/exit_sub 仅在子Agent会话中可用"`，不做隐藏处理。实现用 `isinstance(handler, MainAgent)` 判断，无需修改其他地方。

**理由：**
- `isinstance` 单行判断，实现代价极低
- 错误消息明确告知用户当前状态
- 后续如需动态显示/隐藏可以在此基础上迭代

**曾考虑的替代方案：**
- 动态过滤 help 命令列表 — 当前阶段过度设计，改了 App help 渲染逻辑
- 静默忽略 — 用户不知道命令为什么没生效

---

## 决策 80 — 子 Agent 列表 prompt 注入：{{SUB_AGENTS_LIST}} 占位符 + 模板重排

**背景：** 主 Agent 的 system prompt 需要动态注入子 Agent 列表（名称、描述、职责、约束），让 LLM 知道有哪些子 Agent 可用、何时该切换。此内容对子 Agent 无意义（子 Agent 不能调度其他 Agent）。

**决策：**
- 新增 `{{SUB_AGENTS_LIST}}` 占位符，与 `{{ADDITION_TOOLS}}` 同模式：`PromptLoader.get(**placeholders)` 替换
- `BaseAgent._get_sub_agents_list()` 默认返回 `""`（子 Agent 不感知）
- `MainAgent` 覆盖为 `get_agent_registry().list_agents_prompt()`
- 模板文件重排序：新文件 `05_sub_agents.md`（仅含 `{{SUB_AGENTS_LIST}}`），原 05~08 顺延为 06~09

```
04_tools.md               — 工具定义（含 switch_to_subagent）
05_sub_agents.md          — 可切换子 Agent 列表（新增）
06_communtion_style.md    — 沟通风格（原 05）
07_output_format.md       — 输出格式（原 06）
08_input_format.md        — 输入格式（原 07）
09_reserved.md            — 保留（原 08）
```

**理由：**
- 04（工具）定义"你可以切换"，05（子 Agent 列表）定义"可以切到谁"，逻辑顺序自然
- 占位符模式与 `{{ADDITION_TOOLS}}` 一致，不引入新机制
- `BaseAgent` 默认 `""` 确保子 Agent prompt 中无冗余内容
- 扩展只需 `register()` 一步，prompt 自动更新

**曾考虑的替代方案：**
- 放在 09 末尾 — 与工具定义距离太远，LLM 看到 switch_to_subagent 时尚不知道有哪些目标
- 放入 `01_role.md` 作为 `{{RESPONSIBILITIES}}` 的一部分 — 职责描述和子 Agent 清单混在一起，维护困难

---

## 决策 81 — Agent 稳定标识 `_get_agent_key()` 与 ToolRegistry `agent_key` 参数

**背景：** `switch_to_subagent` 需要 `agent=["main"]` 仅对主 Agent 可见，但 `ToolRegistry.get_for()` 使用 `_get_agent_name()`（展示名"程序员求职助手路由Agent"）做匹配，无法用稳定的短标识过滤。同时 `switch_to_mainagent` 需要对所有子 Agent 可见但对 MainAgent 不可见，需要"非 main"语义。

**决策：**
- `BaseAgent` 新增 `_get_agent_key()` 方法（非抽象），默认返回 `_get_agent_name()`；MainAgent 覆盖为 `"main"`
- `ToolRegistry.get_for()` 新增 `agent_key` 参数，同时匹配 `agent_name` 和 `agent_key`
- `"*"` sentinel 别名：`"*" in tool.agent` → 匹配所有 `agent_key != "main"` 的 Agent

**理由：**
- `agent_key` 与 `agent_name` 职责分离：展示名可随时调整（中英文），key 是稳定的编程标识
- `"*"` 支持"所有非 main"语义而无需枚举子 Agent 名，扩展时无需改 tool 定义

**曾考虑的替代方案：**
- `isinstance(handler, MainAgent)` 判断 — ToolRegistry 不应依赖 Agent 具体类型
- 列出所有子 Agent 名（`agent=["interview", "learning"]`）— 每加一个 Agent 都要更新，容易遗漏

---

## 决策 82 — CONFIRM 拒绝 → 下次 USER_INPUT 携带拒绝信息

**背景：** 用户拒绝工具审批（如拒绝 switch_to_subagent）后，TOOL_CALL 已写入 `_history` 但无 TOOL_CALL_RESULT 闭环。直接删除 TOOL_CALL 会丢失上下文。需要在用户下次输入时告知 LLM 上一条工具调用被拒绝了。

**决策：** 在 `BaseAgent.process()` 的 `USER_INPUT` 分支开头检测 `_pending_tool` 是否仍然存在：
- 存在 → 用户拒绝了上次 CONFIRM → 在 USER_INPUT Message 的 `event_payload` 中注入 `{"tool": ..., "tool_call_id": ..., "reason": "用户取消了此操作"}`
- 不存在 → 正常处理，`event_payload` 为 `None`

一条消息同时携带用户文本和拒绝信息，不新增独立消息。

**理由：**
- LLM 在分析用户意图时同时得知上次调用被拒，可以决定重新尝试或调整方向
- 不修改 App 层逻辑，仅在 BaseAgent 收 USER_INPUT 时做守卫
- TOOL_CALL 保留在 history 中形成完整调用链：TOOL_CALL → (放弃) → USER_INPUT(拒绝信息)

**曾考虑的替代方案：**
- 直接删除 TOOL_CALL — 丢失上下文，LLM 不知道刚才发生了什么
- 注入独立 TOOL_CALL_RESULT 消息 — 消息数膨胀，且"结果"语义与"被拒绝"不符
- App 层处理 — App 不应感知 agent history 结构

---

## 决策 83 — switch tool 必须声明 input_schema

**背景：** `@tool` 装饰器通过 `input_schema` 参数声明工具参数，`inspect.signature` 仅用于填充 `type`/`required`。初次实现 `switch_to_subagent` 时未传 `input_schema`，导致 `arguments_schema` 为空 `{}`，LLM 无法得知参数定义。

**决策：** 所有 `@tool` 装饰的工具必须显式提供 `input_schema`，`inspect.signature` 从函数签名补充类型和默认值信息。

**理由：**
- `input_schema` 是 LLM 了解工具参数的唯一途径，缺失时 LLM 只能猜测参数名
- `@tool` 设计的本意就是 `input_schema` 声明参数 + 函数签名补充类型，不是自动从签名生成 schema

---

### 决策 84 — UIBridge：工具 handler 通过跨线程通信桥直连 CLI 交互

**背景：** M4 工具审批原通过 `ConfirmMode` 枚举 + `_should_confirm()` 机制：`process()` 检测需审批的工具 → 返回 `Response(type="CONFIRM")` → App 渲染 questionary → 用户选择 → `Request(CONFIRM_APPROVED)` → `process()` 执行 handler。每增加一种交互类型（如 select），需要改 `process()`、`App.run()`、`RequestType` 三处，耦合度高。

**决策：**
- 新增 `src/cli/uibridge.py`：`UIBridge` 类作为工具 handler（后台线程）与 CLI 前端（主线程）的跨线程通信桥
- `UIBridge.select(question, choices) -> str` 和 `UIBridge.confirm(message) -> bool` 两个交互方法，handler 直接调用，阻塞等待用户响应
- 模块级 `get_bridge()` 供 handler 获取当前 bridge；`_set_bridge()` 由 App 在后台线程中设置/清除
- Bridge 粒度为每次用户输入（创建在 App 内层循环前），同一次输入内的多个 tool call 共享同一个 bridge
- App `_process_with_spinner()` 在 spinner 循环中轮询 `bridge.has_request`，检测到请求时暂停 spinner、渲染 questionary、传回结果
- `ConfirmMode` 不再参与框架调度逻辑；`_should_confirm()` 移除；所有工具统一走 PROGRESS→CONTINUE 路径
- `ResponseType.CONFIRM` 分支从 `App.run()` 移除；工具审批由 handler 内部 `get_bridge().confirm()` 完成

**理由：**
- 交互逻辑集中在 tool handler 内，代码自包含，可读性高
- 加新交互类型（如文件选择、进度条、文本输入）只需 `UIBridge` 加方法，不改 `process()`/`App.run()`/`RequestType`
- 消除 `ConfirmMode` 在框架层的调度复杂度，工具自行决定是否需要用户交互
- 跨线程 Event 同步机制简单可靠，无队列/锁开销

**曾考虑的替代方案：**
- `RequestType.SELECT_RESPONSE` — 每加交互类型需改三处，扩展性差
- `ConfirmMode.SELECT` — ConfirmMode 职责膨胀，审批和选择是不同概念
- 在 `_execute_tool()` 内直接调用 questionary — questionary 必须在主线程运行，后台线程调用会崩溃

---

### 决策 85 — `__reject__` sentinel：switch 被拒后终止 agent loop

**背景：** switch 工具（`switch_to_subagent`、`switch_to_mainagent`）改用 UIBridge 后，handler 内部调 `get_bridge().confirm()`，用户拒绝时原实现返回 `{"rejected": True}` 作为 TOOL_CALL_RESULT。这导致 LLM 收到 tool 结果后继续 agent loop，可能重试 switch 或执行其他动作，与旧 CONFIRM 拒绝行为（→ 退出内层循环等用户输入）不一致。

**决策：**
- 新增 `__reject__` sentinel，与 `__switch__` 对称：handler 返回 `{"__reject__": True, "reason": "..."}`
- `_execute_tool()` 检测 `__reject__` → 设 `_pending_reject = True` → 正常返回 TOOL_CALL_RESULT Message（关闭 TOOL_CALL 调用链）
- `process()` CONTINUE 分支：append TOOL_CALL_RESULT → 检测 `_pending_reject` → 清标记 → 返回 `Response(FINISH, message="")` 
- App FINISH 分支：无 switch_agent → 渲染空消息 → break 内层循环 → 回外层等用户输入
- 下次 USER_INPUT 时 LLM 看到完整 TOOL_CALL + TOOL_CALL_RESULT(rejected) 链，正常继续

**理由：**
- 语义清晰：`__switch__` = 切换 handler，`__reject__` = 终止 loop
- TOOL_CALL 正常关闭（有 TOOL_CALL_RESULT），不留下悬空 tool_call 污染下次对话
- 与旧 CONFIRM 拒绝行为一致（取消 → 停止 → 等用户），用户体验不退化
- 实现最小化：只用 1 个 bool 标记 + 现有 FINISH 路径

**曾考虑的替代方案：**
- `{"rejected": True}` 作为普通 tool result（无终止）— LLM 可能重试 switch 或执行意外操作
- 不追加 TOOL_CALL_RESULT，直接 FINISH — 下次 LLM 看到悬空 TOOL_CALL，可能困惑
- 新增 `ResponseType.REJECTED` — 需改 App 分支，增加复杂度，FINISH 足够表达"本轮结束"

---

### 决策 86 — `MAIN_AGENT_KEY` 常量替换 magic string "main"

**背景：** 字符串 `"main"` 作为主 Agent 标识符分散在 4 个文件 6 处控制流中：`MainAgent._get_agent_key()`、`ToolRegistry._visible()`、`switch_tools` 的 agent/target、`App._get_handler()` 和 FINISH 分支。拼写错误或语义不一致会导致工具不可见或切换失败。

**决策：**
- 在 `src/agents/registry.py` 定义 `MAIN_AGENT_KEY = "main"`，作为唯一真实来源
- `MainAgent._get_agent_key()` → `return MAIN_AGENT_KEY`
- `switch_to_subagent` → `agent=[MAIN_AGENT_KEY]`
- `switch_to_mainagent` → `target=MAIN_AGENT_KEY`
- `App._get_handler()` → `name == MAIN_AGENT_KEY`
- `App.run()` FINISH 分支 → `response.switch_agent != MAIN_AGENT_KEY`
- `BaseAgent.__init__` → 调用 `ToolRegistry.get_for(..., main_key=MAIN_AGENT_KEY)` 传入
- **`tools/registry.py` 不直接 import `MAIN_AGENT_KEY`** — 通过 `get_for(..., main_key: str = "main")` 参数接收，保持 infrastructure 层不依赖 agents 层

**理由：**
- 单一真实来源，修改只需改一处
- `tools/registry.py` 通过参数接收（而非 import）保持依赖方向正确：agents → tools，不是 tools → agents
- 拼写错误在 IDE/类型检查阶段暴露，不会出现 `"main"` vs `"Main"` vs `"MAIN"` 的不一致

**曾考虑的替代方案：**
- 直接用 `"main"` 字面量 — magic string，分散，拼写风险
- 定义在 `tools/registry.py` — 语义上不属于 tool 系统
- `tools/registry.py` import `MAIN_AGENT_KEY` — 依赖方向反转，基础设施层不应依赖 Agent 层