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