<!--
阅读指南：本文件可能较长。请先阅读目录，然后跳转到相关章节。
每次读取 100 行，直到该章节读完。除非文件很短，否则不要一次性加载整个文件。
-->

# 设计文档

设计遵循 **Plan → Execute → Result Validation → Replan** 循环。验证结果可能推翻原有设计假设，需要及时调整。

- **直接删除：** 不适用的架构决策、模块设计、项目结构直接删除，不保留划掉或标记
- **直接追加：** 新模块、新接口、新设计决策追加到对应章节末尾
- **版本控制：** 所有删除和修改的历史由 Git 追溯，本文档不保留废弃内容

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 架构设计](#2-架构设计)
- [3. 项目结构](#3-项目结构)
- [4. 模块设计](#4-模块设计)
  - [4.0 Handler 协议](#40-handler-协议)
  - [4.1 提示词模块](#41-提示词模块)
  - [4.2 配置模块](#42-配置模块)
  - [4.3 LLM 调用模块](#43-llm-调用模块)
  - [4.4 RAG 模块](#44-rag-模块)
  - [4.5 记忆模块](#45-记忆模块)
  - [4.6 主 Agent（编排器）](#46-主-agent编排器)
  - [4.7 简历 Agent](#47-简历-agent)
  - [4.8 学习 Agent](#48-学习-agent)
  - [4.9 面试 Agent](#49-面试-agent)
  - [4.10 岗位搜索 Agent](#410-岗位搜索-agent)
  - [4.11 日志模块](#411-日志模块)
  - [4.12 Message 模块](#412-message-模块)
  - [4.13 Tool 系统](#413-tool-系统)
  - [4.14 面试问答 Agent](#414-面试问答-agent)
  - [4.15 Lifecycle 模块](#415-lifecycle-模块)
  - [4.16 会话状态管理模块](#416-会话状态管理模块)
- [5. 参考资料与约定](#5-参考资料与约定)

---

## 1. 项目概述

**get-me-in** 是一个面向程序员的 AI 求职助手。它通过多个专业化 Agent 协作，覆盖求职全流程：简历优化、技能学习、模拟面试、岗位搜索。用户通过 CLI 与主 Agent 对话，主 Agent 根据意图调度子 Agent，所有 Agent 通过共享的记忆模块交换上下文。

**目标用户：** 正在求职或准备求职的程序员。

**核心价值：** 将分散的求职工具（简历修改、刷题、模拟面试、岗位搜索）整合为一个有记忆、有上下文的统一体验。

## 2. 架构设计

### 2.1 架构模式：Hub-and-Spoke

```
                         ┌─────────────┐
                         │  记忆模块    │
                         │ (共享状态)   │
                         └──────┬──────┘
                    ┌───────────┼───────────┐
                    │ 读/写     │ 读/写      │ 读/写
              ┌─────┴─────┐ ┌──┴──────┐ ┌──┴──────┐
              │ 简历 Agent │ │学习 Agent│ │面试 Agent│ ...
              └─────┬─────┘ └──┬──────┘ └──┬──────┘
                    │           │           │
                    └───────────┼───────────┘
                                │ 仅主 Agent 可调用
                          ┌─────┴─────┐
                          │  主 Agent  │
                          │ (编排器)   │
                          └─────┬─────┘
                                │ CLI 交互
                          ┌─────┴─────┐
                          │   用户     │
                          └───────────┘
```

**核心规则：**
- **主 Agent 是唯一入口**：用户只和主 Agent 对话
- **子 Agent 之间不直接通信**：Agent 之间不允许互相调用
- **主 Agent 唯一特权是调度子 Agent**：所有 Agent 共享相同的基础能力（对话循环、意图识别、工具调用、记忆读写），主 Agent 额外持有 `AgentRegistry`；子 Agent 不允许持有或调度其他 Agent
- **记忆模块是唯一共享通道**：所有 Agent 通过记忆模块读写上下文

### 2.2 技术栈

| 层 | 选型 | 理由 |
|----|------|------|
| 语言 | Python 3.14 | pyproject.toml 已设定 |
| Agent 框架 | 自研轻量 | 最大控制力，最小依赖，匹配 Hub-and-Spoke 模式 |
| LLM 接入 | OpenAI SDK（`openai`） | 双 tier（pro / flash），base_url 通过环境变量注入，兼容所有 OpenAI-compatible 后端 |
| CLI 交互 | `input()` + `$EDITOR` 临时文件 + `rich` 渲染 | 日常对话用 `input()`；长文本（JD、简历、回答）弹出编辑器编辑临时文件；Markdown 输出用 `rich` 美化 |
| 向量存储 | Chroma（内存模式 / 持久化模式通过 `CHROMA_PERSIST_DIR` 切换） | 开发阶段零配置，设置环境变量即可持久化到 `data/chroma/` |
| 向量化 & 重排 | `sentence_transformers` | bi-encoder 做召回，cross-encoder 做重排 |
| 记忆存储 | 文件系统（Markdown） | 人机可读，Git 可追踪，无需数据库 |

### 2.3 数据流

```
用户输入 → CLI → 主 Agent（意图识别）
                      │
                      ├─ 需要子 Agent？─→ 调用子 Agent
                      │                      │
                      │                      ├→ 子 Agent 自行从记忆模块读取上下文
                      │                      ├→ 子 Agent 执行任务
                      │                      ├← 子 Agent 返回结果
                      │                      └→ 子 Agent 将关键信息写入记忆模块
                      │
                      └─ 不需要子 Agent？─→ 主 Agent 直接回复
                      
主 Agent → CLI → 用户
```

### 2.4 提示词组合约定

所有 Agent 调用 LLM 时，`PromptLoader` 强制在 Agent 专用提示词前面拼接 `general_agent_prompt`，Agent 自身无法跳过或修改此行为。

`general_agent_prompt` 由 `data/prompts/general_agent/` 目录下的多个 `.md` 文件拼接而成，按类型拆分（如安全策略、工具列表、输出格式），各文件独立维护。`PromptLoader` 加载时自动收集该目录下所有文件并拼接。

仅作用于 Agent（主 Agent 及各子 Agent），记忆压缩、RAG 等基础设施模块不适用。

## 3. 项目结构

```
get-me-in/
├── src/
│   ├── config.py            # 环境变量集中管理（启动加载 + 校验）
│   ├── message.py           # 通用消息/事件数据类（横跨 CLI/Agent/LLM/Memory）
│   ├── request.py           # App → Agent 输入协议（对称 Response，不进对话历史）
│   ├── response.py          # Agent → CLI 输出协议（不进对话历史）
│   ├── main_agent/          # 主 Agent 入口 & 编排逻辑
│   │   ├── __init__.py
│   │   └── orchestrator.py  # 意图识别、Agent 调度（纯 LLM 驱动，无独立 Router）
│   ├── agents/              # 子 Agent 实现
│   │   ├── __init__.py
│   │   ├── base.py          # Agent 基类（对话循环、意图识别、工具调用、记忆读写）
│   │   ├── resume/          # 简历 Agent
│   │   ├── learning/        # 学习 Agent
│   │   ├── interview/       # 面试 Agent
│   │   └── job_search/      # 岗位搜索 Agent (TBD)
│   ├── memory/              # 记忆模块
│   │   ├── __init__.py       # Facade：build_memories() + sync/async
│   │   ├── store.py          # 文件系统写入 + 事件发射（同步）
│   │   ├── indexer.py        # MemoryIndexer：监听事件 → RAG 索引
│   │   ├── retriever.py      # MemoryRetriever：语义检索
│   │   ├── builder.py        # MemoryBuilder：LLM 从对话构建记忆
│   │   └── schemas.py        # Memory 数据结构
│   ├── utils/               # 通用工具
│   │   ├── chunker.py        # 通用文本切分（front-matter + --- 分隔）
│   │   ├── formatters.py     # 通用格式化（时间戳文件名 + front-matter 拼装）
│   │   ├── file_reader.py    # 文件读取底层（read_text / list_directory / search_text / read_pdf / read_docx）
│   │   └── dumper.py         # 对话历史 dump（调试上下文丢失问题）
│   ├── logger.py             # 日志模块（横切基础设施）
│   ├── lifecycle.py          # 进程生命周期管理（统一退出清理入口）
│   ├── llm/                 # LLM 调用封装
│   │   ├── __init__.py
│   │   └── client.py         # 双 tier（pro / flash）统一调用
│   ├── rag/                 # RAG 模块（Embedder + Store + Loader + Reranker）
│   │   ├── __init__.py
│   │   ├── embedder.py      # 向量化（sentence_transformers）
│   │   ├── store.py         # Chroma 封装（collection 增删查）
│   │   ├── loader.py        # 启动加载 + 增量加载（threading 后台）
│   │   └── reranker.py      # 重排
│   ├── tools/               # Tool 系统
│   │   ├── __init__.py
│   │   ├── exceptions.py    # ToolCallException（工具异常 + 修复建议）
│   │   ├── registry.py      # Tool dataclass + @tool 装饰器 + ToolRegistry
│   │   ├── system_tool.py   # 系统工具（get_current_datetime / get_working_dir）
│   │   ├── web_tool.py      # web_search 工具
│   │   ├── switch_tools.py  # Agent 切换工具
│   │   ├── plan_tools.py    # Plan 机制工具
│   │   ├── workspace_tools.py # 工作区工具（10 个：read/list/grep/search_file/replace/write/delete/move/edit/open）
│   │   ├── customer_file_tool.py # 外部文件读取（read_customer_file）
│   │   ├── rag_tools.py     # RAG 查询工具（query_memory / query_reference_data）
│   │   └── resume_tools.py  # 简历工具（copy_template / build_pdf）
│   ├── prompts/             # 提示词加载器
│   │   ├── __init__.py
│   │   └── loader.py        # 模板加载 & 变量替换
│   └── cli/                 # CLI 交互层
│       ├── __init__.py
│       ├── app.py           # 终端交互入口
│       └── handler.py       # Handler 抽象基类 + LLMHandler（M1 验证管线，M4 由 Orchestrator 替换，M5-Review 删除 LLMHandler）
├── data/                    # 持久化存储（文件系统）
│   ├── profile/
│   │   └── profile.md       # 用户画像（free-form section，记录技能、经历、偏好等）
│   ├── reference/           # 参考数据（RAG 检索源）
│   │   ├── interview_questions/   # 面试题库
│   │   ├── company_info/          # 面经 / 公司情报
│   │   ├── knowledge_base/        # 知识库（已验证的正确答案）
│   │   ├── resume_examples/       # 简历范例
│   │   ├── recommended_materials/ # 推荐资料
│   │   └── job_descriptions/      # 岗位描述
│   ├── memories/
│   │   ├── main/            # 按 Agent 分目录，每个文件一条记忆
│   │   ├── resume/
│   │   ├── learning/
│   │   ├── interview/
│   │   └── job_search/
│   └── prompts/             # 提示词模板（按用途组织，不按 Agent 划分）
│       ├── general_agent/   # 所有 Agent 强制拼接的公共前缀（按文件名排序拼接）
│       │   ├── 01_role.md
│       │   ├── 02_mission.md
│       │   ├── 03_constraint.md
│       │   ├── 04_tools.md
│       │   ├── 05_sub_agents.md
│       │   ├── 06_communtion_style.md
│       │   ├── 07_output_format.md
│       │   ├── 08_input_format.md
│       │   └── 09_reserved.md
│       ├── PLACEHOLDER.md    # 占位符清单（15 个占位符，不参与拼接）
│       ├── memory/
│       │   └── builder.md    # MemoryBuilder 系统提示词
│       ├── resume_analysis.md
│       └── ...
├── tests/
├── docs/
│   ├── current.md
│   ├── design.md
│   ├── plan.md
│   ├── task.md
│   └── decision.md
├── main.py                  # 程序入口
└── pyproject.toml
```

## 4. 模块设计

### 4.0 Handler 协议 & App 交互循环

**用途：** 定义 CLI 层与业务逻辑层之间的桥接接口。CLI 不直接调用 LLM 或 Agent，而是调用注入的 `Handler`，由 Handler 负责具体的输入处理逻辑。M1 用 `LLMHandler` 验证端到端管线，M4 由 `BaseAgent` 实现同一协议（M5-Review 删除 LLMHandler）。

**职责：**
- 定义 `process(input: Request) -> Response` 抽象方法
- CLI 层不关心处理细节，只根据 `Response.type` 做不同渲染

**`Request` 数据类（`src/request.py`，对称 `Response`）：**
- `type: RequestType` — `USER_INPUT` / `CONTINUE` / `CONFIRM_APPROVED`
- `message: str = ""` — 用户输入文本，仅 `USER_INPUT` 时填写
- `Request` 是 App → Agent 协议层，不进对话历史

**`Response` 数据类（`src/response.py`）：**
- `type: ResponseType` — `FINISH` / `SELECT` / `CONFIRM` / `PROGRESS`
- `message: str` — 展示文本（markdown）
- `choices: list[str] | None` — `SELECT` 时用，最后一项固定"🔧 自定义输入..."
- `thinking: str | None` — LLM 推理过程，由 `SHOW_THINKING` 环境变量控制是否渲染
- `sub_type: str = ""` — 对应 `Message.event_type`，用于 App 判断继续/终止逻辑

| type | 触发 | App 行为 | 返回给 Agent |
|------|------|---------|-------------|
| `FINISH` | LLM 返回 `event_type="finish"` | 渲染 markdown，退出内层循环 | 无（等用户下一轮输入） |
| `PROGRESS` | LLM 返回 TOOL_CALL，工具无需审批 | 渲染进度消息，立即构造 `Request(CONTINUE)` | `Request(CONTINUE)` → 执行工具 |
| `CONFIRM` | LLM 返回 TOOL_CALL，工具需审批 | `questionary.confirm` | y → `Request(CONFIRM_APPROVED)`；n → 退出内层循环 |
| `SELECT` | LLM 调 `provide_choices` | `questionary.select` | 用户选择 → `Request(USER_INPUT)` |

**App 双循环结构：**

```
外层 while input():                    ← 等用户输入（正常 CLI 交互）
    request = Request(USER_INPUT, text)
    内层 while True:                   ← agent loop（阻塞用户输入）
        response = handler.process(request)
        FINISH   → render, break
        PROGRESS → render, request = CONTINUE
        CONFIRM  → questionary.confirm
                    confirmed? → request = CONFIRM_APPROVED
                    rejected?  → break（不等用户说话）
```

**关键接口：**
- `Handler.process(input: Request) -> Response` —— 处理用户输入，返回 CLI 指令
- `Handler._parse_llm_reply(reply: str) -> Message` —— 静态方法，将 LLM 返回的 JSON（`06_output_format.md` schema）反序列化为 `Message`。子类可复用或覆盖

**CLI 等待动效：**
- `App._process_with_spinner(request)` 将 `handler.process()` 放入后台线程，主线程以 `\r` 单行覆盖展示 `.` / `..` / `...` + 计时（`{dots:<3} 处理中 N.Ns`），LLM 返回后擦除

**位置：** `src/cli/handler.py` + `src/response.py` + `src/request.py`

**设计决策：**
- `Request` 和 `Response` 对称：都是 App ↔ Agent 协议层，都不进对话历史
- `Response` 是 CLI 指令层 —— 与 `Message` 语义分离
- Agent loop 上移至 App 内层 while —— `process()` 单步执行，每次只做一步（处理输入 → LLM → 分发 → 返回），工具暂停时返回 PROGRESS/CONFIRM
- `_pending_tool` 断点恢复 —— `process()` 跨调用保存 (tool_name, payload, tool_call_id)，CONTINUE/CONFIRM_APPROVED 时恢复执行
- 用户拒绝审批 → 退出内层循环，不调 `process()`，等用户主动输入
- 交互库选择 `questionary`（`select` + `confirm`）
- M1 用 `LLMHandler`，M4 由 `BaseAgent` 替换（M5-Review 删除 LLMHandler）—— `Handler` 协议是稳定的桥接点

### 4.1 提示词模块

**用途：** 集中管理所有提示词模板，提供加载和变量替换能力。提示词按用途组织，不绑定特定 Agent —— 同一个提示词可以被多个模块使用。

**职责：**
- 从 `data/prompts/` 加载提示词模板
- 为 Agent 加载提示词时，强制将 `general_agent/` 目录下所有文件拼接后放在最前面
- 支持变量替换（`{user_name}`、`{skills}` 等占位符）
- 按名称获取提示词，调用方不关心文件路径

**关键接口 / 公开 API：**
- `PromptLoader.get(**variables) -> str` —— 拼接 `general_agent/` 下所有文件 + 替换占位符，返回完整 Agent 提示词。所有 Agent 通过此方法获取提示词，区别仅在于传入的变量值不同
- `PromptLoader.list() -> list[str]` —— 列出 `general_agent/` 下所有文件
- `PromptLoader.get_raw(name: str, **variables) -> str` —— 加载 `data/prompts/` 下指定模板文件并替换变量，不拼接公共前缀（供记忆压缩等非 Agent 模块使用）

**内部结构：**
- `loader.py`：`get()` 读取 `general_agent/` 下所有 `.md` 文件，按文件名排序拼接后替换占位符；`get_raw()` 加载 `data/prompts/` 下指定文件，跳过公共前缀。不再使用名称→模板映射——Agent 差异完全由占位符值体现
- `PLACEHOLDER.md`：记录 `general_agent/` 中所有 `{{占位符}}` 的完整清单，供 Agent 实现时参考，不参与拼接

**占位符系统：**

`general_agent/` 下的模板文件使用 `{{占位符}}` 语法标记可变内容，共 14 个占位符，全部由各 Agent 实现时分别定义。`PromptLoader.get()` 在加载时用 Agent 提供的变量字典替换占位符。

| 文件 | 占位符 | 类型 |
|------|--------|------|
| `01_role.md` | `{{AGENT_NAME}}`, `{{AGENT_DESCRIPTION}}`, `{{RESPONSIBILITIES}}` | Agent 身份 |
| `02_mission.md` | `{{PRIMARY_GOAL}}`, `{{SUCCESS_CRITERIONS}}`, `{{PRIORITIES}}` | 任务目标 |
| `03_constraint.md` | `{{HARD_CONSTRAINTS}}`, `{{SOFT_CONSTRAINTS}}` | 约束规则 |
| `04_tools.md` | `{{ADDITION_TOOLS}}` | 专属工具 |
| `05_sub_agents.md` | `{{SUB_AGENTS_LIST}}` | 可切换子 Agent 列表 |
| `06_communtion_style.md` | `{{TONE}}`, `{{VERBOSITY}}`, `{{EXPLANATION_STYLE}}`, `{{STYLE_RULES}}`, `{{STYLE_AVOIDS}}` | 沟通风格 |
| `07_output_format.md` | 无 | 固定 |
| `08_input_format.md` | 无 | 固定 |
| `09_reserved.md` | 无 | 固定 |

完整清单及各占位符说明见 `data/prompts/PLACEHOLDER.md`。

**设计决策：**
- Agent 无专属模板文件 —— 所有 Agent 共用 `general_agent/` 下的同一套模板，差异仅由占位符填充值体现
- Markdown + XML 混合格式 —— Markdown 人可读，XML 标签便于 LLM 解析语义块
- 提示词与代码分离 —— 调整提示词不需要改代码，降低迭代成本
- `PromptLoader` 无状态 —— 每次 `get()` 都重新读文件，修改提示词后无需重启
- 占位符由 Agent 定义值 —— 固定提示词模板 + 可变占位符，同一套模板适配所有 Agent

### 4.2 配置模块

**用途：** 集中管理所有环境变量，在应用启动时加载 `.env` 文件并校验必填变量，避免各模块散落 `os.environ` 调用带来的遗漏和拼写错误。

**职责：**
- 应用启动时调用 `python-dotenv` 加载 `.env`
- 检查所有必填环境变量是否存在，缺失时打印清晰的错误信息并退出
- 将配置值挂在模块属性上，其他模块通过 `from src.config import config` 获取

**环境变量：**

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `OPENAI_BASE_URL` | API 地址 | 无（必填） |
| `OPENAI_API_KEY` | API 密钥 | 无（必填） |
| `LLM_PRO_MODEL` | pro tier 模型名 | 无（必填） |
| `LLM_FLASH_MODEL` | flash tier 模型名 | 无（必填） |
| `BI_ENCODER_MODEL` | RAG 召回（bi-encoder） | `BAAI/bge-base-zh-v1.5` |
| `CROSS_ENCODER_MODEL` | RAG 重排（cross-encoder） | `BAAI/bge-reranker-v2-m3` |
| `EMBED_BATCH_SIZE` | Embedding 批处理大小 | `32` |
| `CHROMA_PERSIST_DIR` | Chroma 持久化目录（留空 = 内存模式） | 无（内存模式） |
| `RETRIEVAL_TOP_K` | Chroma 召回返回数量 | `10` |
| `RERANK_BATCH_SIZE` | Reranker 批处理大小 | `32` |
| `RERANK_TOP_K` | Reranker 重排后保留数量 | `5` |
| `HF_ENDPOINT` | HuggingFace 镜像（国内用户建议 `https://hf-mirror.com`） | 无（缺失时走官方站 huggingface.co） |
| `LOG_LEVEL` | 日志级别（DEBUG / INFO / WARNING / ERROR） | `INFO` |
| `LOG_DIR` | 日志文件目录 | `data/logs/` |
| `MEMORIES_BASE_DIR` | 记忆存储根目录（按 Agent 分子目录，一文件一条记忆） | `data/memories/` |
| `SHOW_THINKING` | 是否展示 LLM 推理过程（`"true"` / `"false"`） | `false` |
| `AGENT_MAX_ROUNDS` | Agent 最大工具调用轮数 | `10` |
| `TOOL_CONFIRM_ENABLED` | 工具审批全局开关（`"true"` / `"false"`） | `true` |
| `WORKING_DIR` | Agent 工作目录（临时文件） | `data/temp/` |
| `LLM_THINKING_ENABLED` | LLM 思考模式开关（`"true"` / `"false"`） | `true` |

有默认值的环境变量缺失时不报错，自动使用默认值。无默认值的必填变量（如 `OPENAI_API_KEY`）缺失时列出所有缺失项并 `sys.exit(1)`。

`_VAR_SPECS` 第 4 列 `is_bool`：设为 `True` 时，取值自动转为 `bool`（`"true"`/`"1"` → `True`，其余 → `False`）。`SimpleNamespace` 接受弱类型，``config.SHOW_THINKING``、``config.TOOL_CONFIRM_ENABLED`` 和 ``config.LLM_THINKING_ENABLED`` 为 ``bool``，其他变量为 ``str``。

**关键接口 / 公开 API：**

- `config.OPENAI_BASE_URL: str` —— API 地址
- `config.OPENAI_API_KEY: str` —— API 密钥
- `config.LLM_PRO_MODEL: str` —— pro tier 模型名
- `config.LLM_FLASH_MODEL: str` —— flash tier 模型名

`config` 是模块级单例，模块加载时即完成校验，导入即可直接使用属性，无需额外初始化。

**内部结构：**
- `config.py`：`load_dotenv()` → 遍历必填列表 → 缺失则 `print` + `sys.exit(1)` → 将值挂到模块属性

**设计决策：**
- 集中式而非分散式 —— 启动时一次性校验，运行时不会因环境变量缺失而中途崩溃
- 模块级单例 —— `import` 即加载，不需要显式调用 `init()`，零侵入
- 其他模块禁止直接使用 `os.environ` —— 所有环境变量通过 `config` 模块访问，换变量名只改一处
- `.env` 不在代码中提交 —— 每台机器/每个开发者各自维护自己的 `.env`，`.env.example` 提交到仓库作为模板

### 4.3 LLM 调用模块

**用途：** 封装 LLM 调用，提供两种能力等级（pro / flash），供 Agent 基类复用。Agent 不感知具体 model 名称，只需选择调用等级。

**职责：**
- 从 `src.config` 模块读取 API 配置
- 初始化 OpenAI 客户端（base_url、api_key 由 config 注入）
- 提供 `chat_pro()` 和 `chat_flash()` 两个入口
- 错误直接抛出，不做 fallback

**环境变量来源：** 由 `src/config.py` 统一加载和校验（见 §4.2），`LLMClient` 不直接读取 `os.environ`。

**关键接口 / 公开 API：**
- `LLMClient.chat_pro(messages: list[dict], **kwargs) -> str` —— 调用 pro tier 模型（model 名取自 `config.LLM_PRO_MODEL`），返回回复文本。`**kwargs` 透传给 `chat.completions.create`（如 `temperature`、`top_p`、`response_format`），`LLMClient` 不做预设或拦截
- `LLMClient.chat_flash(messages: list[dict], **kwargs) -> str` —— 调用 flash tier 模型（model 名取自 `config.LLM_FLASH_MODEL`），返回回复文本。`**kwargs` 同上透传
- `LLMClient.client` —— 暴露底层 `openai.OpenAI` 实例，用于需要精细化控制（如自定义 model、流式）的场景，绕过便捷封装

**内部结构：**
- `client.py`：`LLMClient` 类，构造函数从 `config.OPENAI_BASE_URL` 和 `config.OPENAI_API_KEY` 读取配置，实例化 `openai.OpenAI`；两个 `chat_*` 方法内部调用 `self.client.chat.completions.create(model=..., messages=...)` 并返回 `choice.message.content`，model 名分别来自 `config.LLM_PRO_MODEL` 和 `config.LLM_FLASH_MODEL`

**Agent 基类中的封装（`src/agents/base.py`）：**

Agent 基类持有 `LLMClient` 引用，通过类属性 `_pro_params` / `_flash_params` 声明默认参数，子类按需覆盖。暴露两个便利方法，内部合并默认值 + 调用时覆盖参数：

```python
class BaseAgent:
    _pro_params: dict = {"response_format": {"type": "json_object"}}   # 子类按需覆盖
    _flash_params: dict = {"response_format": {"type": "json_object"}} # 子类按需覆盖

    def __init__(self, llm_client: LLMClient, ...):
        self._llm = llm_client

    def _llm_pro(self, messages: list[dict], **kwargs) -> str:
        """高能力调用 — 用于需要深度推理的任务"""
        params = {**self._pro_params, **kwargs}
        return self._llm.chat_pro(messages, **params)

    def _llm_flash(self, messages: list[dict], **kwargs) -> str:
        """快速调用 — 用于简单分类、格式化等轻量任务"""
        params = {**self._flash_params, **kwargs}
        return self._llm.chat_flash(messages, **params)
```

参数优先级：调用时 `**kwargs` > 子类 `_pro_params/_flash_params` > LLMClient 默认（model 名）。

子 Agent 调用 `self._llm_pro(messages)` 或 `self._llm_flash(messages)`，不传 model 名。需要临时覆盖参数时传 `self._llm_pro(messages, temperature=0.9)`。

**设计决策：**
- 双 tier 而非单一接口 —— 不同任务对模型能力/延迟需求不同，pro 做深度推理（简历分析、面试评估），flash 做轻量任务（意图分类、格式化输出）
- model 名不暴露给 Agent —— 由运维/部署层面决定具体模型，Agent 只关心能力等级
- 不做 fallback —— 保持简单，调用失败直接抛出错误到 CLI 层展示
- 配置由 `src/config.py` 集中管理 —— LLMClient 不直接读 `os.environ`，换变量名只改 config 一处
- 使用 OpenAI SDK 而非自建 HTTP 调用 —— 生态兼容性好（任何 OpenAI-compatible 后端均可），且 SDK 内建重试、流式等能力
- LLM 参数分层管理 —— `LLMClient` 保持薄管道角色，仅透传 `**kwargs` 不做预设；temperature / top_p 等参数默认值由 `BaseAgent._pro_params` / `_flash_params` 类属性声明，子 Agent 按需覆盖，调用时 `**kwargs` 可临时覆盖；需要原生 SDK 控制时通过 `LLMClient.client` 直接操作
- 暴露底层 client —— `LLMClient.client` 公开 `openai.OpenAI` 实例，高级场景（自定义 model、流式）可直接使用，不被便捷封装限制

### 4.4 RAG 模块

**用途：** 共享基础设施层，为各模块提供语义检索能力。使用 `sentence_transformers` 做向量化和重排，`Chroma` 作为向量存储。向量存储先使用内存模式，后续可切换为本地持久化。

**职责：**
- 将文本向量化（Embedder）
- 将文档按分隔符切分为逻辑块（Chunker）—— 统一使用 Markdown 水平线 `---` 作为条目边界，记忆和参考数据共用同一套切分规则
- 向量存储与检索（ChromaStore）—— 内部持有 Embedder，统一提供 add/query/remove
- 重排（Reranker）—— cross-encoder 精排，分数存 metadata

**关键接口 / 公开 API：**
- `Embedder.embed(texts: list[str]) -> list[list[float]]` —— 将文本转换为向量
- `Chunker.chunk(text: str, separator: str, metadata: dict) -> list[Chunk]` —— 按分隔符切分文本为逻辑块，每个块携带 metadata
- `ChromaStore.add(chunks: list[Chunk], collection: str) -> None` —— 将块向量化后存入指定 collection
- `ChromaStore.query(query_text: str, collection: str, filter: dict | None, top_k: int) -> list[Chunk]` —— 内部向量化后检索，返回 Chunk 列表
- `Reranker.rerank(query: str, candidates: list[Chunk], top_k: int | None = None) -> list[Chunk]` —— 重排（top_k 默认值由 `RERANK_TOP_K` 配置，分数注入 `metadata["rerank_score"]`，异常直接抛出）

**处理流程：**

```
写入:
  MD 文本 → Chunker.chunk(text, separator, metadata) → 逻辑块列表
              │
              └→ ChromaStore.add(chunks, collection)
                      │
                      └→ Embedder.embed() → Chroma collection

检索:
  查询文本 → ChromaStore.query(query_text, collection, filter, top_k=20)
              │
              └→ Reranker.rerank(query, candidates, top_k=5)
                      │
                      └→ 最终结果
```

**内部结构：**
- `Embedder`：封装 `sentence_transformers` 的 bi-encoder 模型（默认 `BAAI/bge-base-zh-v1.5`，由 `BI_ENCODER_MODEL` 配置），将文本转为归一化向量；`embed()` 支持 `batch_size` 参数（默认值由 `EMBED_BATCH_SIZE` 环境变量配置）
- `Chunker`：通用切分器，按传入的 `separator` 切分文本为逻辑块，附加 `metadata`（agent、date、chunk_id、category 等）—— 不关心内容语义，只按分隔符切
- `ChromaStore`：封装 Chroma 客户端，内部持有 `Embedder` 完成向量化，统一提供 `add()` / `query()` / `remove()` 接口。默认内存模式（设置 `CHROMA_PERSIST_DIR` 环境变量则切换为 `PersistentClient` 持久化到 `data/chroma/`）。`add()` 使用 Chroma `documents` 字段存储原始文本，`query()` 接受文本直接检索并返回 `list[Chunk]`。不预建 collection（首次 `add()` 自动创建），不校验 collection 名
- `Reranker`：独立加载 `sentence_transformers` 的 CrossEncoder 模型（默认 `BAAI/bge-reranker-v2-m3`，由 `CROSS_ENCODER_MODEL` 配置），`__init__` 时预热；`rerank()` 批处理大小和 top-k 由 `RERANK_BATCH_SIZE` / `RERANK_TOP_K` 环境变量控制；分数注入 `Chunk.metadata["rerank_score"]`，结果从高到低排序；异常直接抛出，由调用方降级

**Collection 设计：**

两个 collection，不按 Agent 划分：

| Collection | 用途 | 数据来源 | category 自动标注 |
|------------|------|----------|-------------------|
| `references` | 所有参考数据 | `data/reference/<category>/*.md`，按 `---` 切分 | 子目录名即 category 值，Chunker 自动打 metadata |
| `memories` | 所有 Agent 的记忆条目 | MemoryStore 写入 `data/memories/<agent>/<timestamp>.md`，每个文件一条记忆，front-matter 含 `id`/`agent`/`time` | 按 agent 过滤 |

检索时默认跨所有 chunk 搜索，Reranker 自然排序。调用方可传 `filter={"agent": "resume"}` 限定范围。

**Chunk 数据结构：**

```python
@dataclass
class Chunk:
    id: str          # uuid4，Chroma 主键
    content: str     # 条目原始文本（不含分隔符）
    metadata: dict   # 因 collection 而异（见下表）
```

| 字段 | references | memories | 写入方 | 用途 |
|------|-----------|----------|--------|------|
| `category` | ✅ 必填 | — | Loader | 子目录名，限定检索范围 |
| `source_file` | ✅ | ✅ | Loader | 来源文件路径，便于追溯和增量更新时删除旧 chunk |
| `agent` | — | ✅ 必填 | Loader | 写入方 Agent 名，跨 Agent 检索过滤 |
| `date` | — | ✅ | Loader | 写入日期，时间范围过滤 |
| `id` | — | ✅ | Chunker (front-matter) | Memory uuid，精确标识一条记忆 |
| `time` | — | ✅ | Chunker (front-matter) | Memory 时间戳 |
| `rerank_score` | ✅ | ✅ | Reranker | cross-encoder 重排分数（float），仅排序后结果携带 |

Chunk 本身不校验 metadata 结构，规范由写入方遵守。

**RagLoader 模块：**

`loader.py` 负责读取磁盘文件 → 调 Chunker（从 `src/utils/chunker.py` 导入）→ 写入 ChromaStore，是 RAG 模块的唯一数据入口。Store 和 Reranker 通过构造函数注入（单例由 `src/rag/__init__.py` 模块级懒加载管理）。

**状态机：** `LoaderState` 枚举（IDLE → LOADING → READY / ERROR）。调用方通过 `state` / `error` 属性查询，据此决策降级或重试。

| 方法 | 说明 |
|------|------|
| `__init__(store, reranker)` | Store/Reranker 注入，Chunker 内部创建，初始 state=IDLE |
| `auto_load()` | 同步 + `threading.Lock`，LOADING 状态下拒绝；内存模式全量加载；持久化模式读取 `.last_update` 时间戳仅加载变更文件；异常写 state=ERROR 不抛出；完成后写时间戳 + state=READY |
| `load_file(path)` | 同步 + 同锁，增量更新：remove(source_file) → chunk → add |
| `state` (property) | 返回 `LoaderState` |
| `error` (property) | 返回 `str | None`（仅 ERROR 时有值） |

加载逻辑：遍历目录时，子目录名自动提取为 category（仅 `references`）或 agent（仅 `memories`），传入 Chunker 作为 metadata。memories 目录为空时不创建 collection。

**设计决策：**
- 统一分隔符 `---` —— 所有数据（参考数据、记忆）以 Markdown 水平线作为条目边界，写入方负责保证每条之间是自包含的语义单元
- category 自动标注 —— 参考数据的 category 由子目录名自动提取（`data/reference/<category>/` → `{"category": "<category>"}`），不维护独立配置文件
- 全库搜索 + 可选过滤 —— 默认不传 filter 全库检索，Reranker 自然排序；调用方可传 `{"category": "knowledge_base"}` 限定范围
- Chroma 内存模式先行 —— 开发阶段零配置，后续切换持久化只需改 Chroma 初始化参数
- 两个 collection —— `references`（参考数据）和 `memories`（记忆），不按 Agent 或数据类型拆分
- Store 召回 + Reranker 重排 —— ChromaStore.query() 用 bi-encoder 粗筛，Reranker 用 cross-encoder 精排，两阶段分离
- RAG 是基础设施，不是 Agent —— 不参与 Agent 调度，由需要检索能力的模块直接调用

**模块入口 API（`src/rag/__init__.py`）：**

外部调用方不直接接触 `ChromaStore` / `Reranker` / `RagLoader`，仅通过以下函数使用 RAG：

| 函数 | 说明 |
|------|------|
| `search(query_text, collection="references", filter=None, top_k=None) -> list[Chunk]` | 检索 + 重排，内部串联 `store.query()` → `reranker.rerank()`。`filter` 透传 Chroma `where` 限定检索范围。LOADING/ERROR 状态时抛出 `RuntimeError` |
| `load(target=None) -> str` | 加载/重载。`load()` 全量重载；`load("pattern")` 按子串匹配文件路径重载，返回结果描述 |
| `delete(where, collection="memories") -> int` | 按 metadata 过滤删除，返回删除条数。空 `where={}` 抛 `ValueError` |
| `is_ready() -> bool` | RAG 是否就绪（`loader.state == READY`），供外部轮询 |

内部单例管理：`_ensure_init()` 双检锁懒加载 `ChromaStore` / `Reranker` / `RagLoader`，首次 import 时启动 daemon 线程执行 `auto_load()`。Store 和 Reranker 对外不可见。

**Chunker 归属：** `Chunker` / `Chunk` 已抽出到 `src/utils/chunker.py`，作为通用文本切分工具被 RAG 和记忆模块共用。

### 4.5 记忆模块

**用途：** 系统的持久化上下文层。存储 LLM 构建的记忆条目。所有 Agent 通过此模块获取上下文。记忆按 Agent 隔离存储，各 Agent 写入自己的子目录。

**职责：**
- 记忆的写入和删除（按 Agent 隔离，一文件一条记忆）
- 对话构建记忆：调用 LLM 从对话中提取关键信息，构建结构化记忆条目
- 为各 Agent 提供语义检索接口（跨 Agent / 单 Agent）

**架构：MemoryStore 与 RAG 解耦**

MemoryStore **不直接持有 RAG**，通过观察者模式解耦：

```
写入方向:
  MemoryStore (只管文件系统)
    │ 发射事件 (同步 callback)
    ├── MemoryWritten ──→ MemoryIndexer ──→ RAG (写入)
    └── MemoryDeleted ──→ MemoryIndexer ──→ RAG (删除)

读取方向:
  MemoryRetriever ←── RAG (search)

Store 与 RAG 完全隔离。
```

**公开 API：**

| 接口 | 位置 | 说明 |
|------|------|------|
| `init()` | `memory/__init__.py` | 懒加载单例 Store + Indexer + Retriever（可选，首次调用自动初始化） |
| `build_memories(conversation, agent, llm, sync_mode=True) -> list[Memory] \| None` | `memory/__init__.py` | Facade，构建记忆 + 保存 + 索引。`sync_mode=True` 同步返回 Memory 列表；`False` 后台线程执行，返回 `None` |
| `search_memories(query, agent=None, top_k=5) -> list[Memory]` | `memory/__init__.py` | 语义检索。`agent=None` 跨 Agent 全量检索 |
| `delete_memory(agent, file_path) -> bool` | `memory/__init__.py` | 删文件 + 移除 RAG 索引。成功返回 `True` |

**内部结构：**

| 文件 | 职责 |
|------|------|
| `schemas.py` | `Memory(id: uuid, agent: str, time: datetime, content: str, category: str)` 及 `MemoryWrittenEvent`、`MemoryDeletedEvent`、`chunk_to_memory()` |
| `store.py` | 同步文件系统读写。`write_memory()`：生成时间戳文件名 → front-matter 格式化 → 写文件 → 发射事件。`delete_memory()`：删文件 → 发射事件。不提供读方法，不持队列/线程 |
| `indexer.py` | `MemoryIndexer`：监听 Store 事件，`_on_write` → `rag.load(file_path)`，`_on_delete` → `rag.delete(where={"source_file": file_path})`。构造即绑定，无公开方法 |
| `retriever.py` | `MemoryRetriever`：封装 `rag.search(filter={"agent": ...})`，`Chunk` → `Memory` 转换后返回 |
| `builder.py` | `MemoryBuilder`：加载 `data/prompts/memory/builder.md` 系统提示词 → 对话序列化为 JSON → `chat_flash(response_format=json_object)` 强制 JSON → `json.loads()` 解析 `{"facts": "...", "preferences": "..."}` → 按 `\n` 拆分行，每行一条 Memory → 注入 `id`/`time`/`agent`/`category` → `list[Memory]` |
| `__init__.py` | Facade：`init()` + `build_memories()` + `search_memories()` + `delete_memory()` 四大公开函数，内部双检锁懒加载单例 Store/Indexer/Retriever |

**文件组织：**

一条 Memory 一个文件：`data/memories/<agent>/<yyyyMMddHHmmss.fff>.<category>.md`（category 在文件名中避免 facts/preferences 同时间戳冲突）

文件格式为 front-matter (简单 KV，`---` 包裹) + 正文（多条事实/偏好以 `\n\n---\n\n` 分隔，Chunker 按 `---` 切分为独立 chunk）：

```
---
id: abc123
agent: resume
category: fact
time: 2026-06-30T14:30:00
---

用户的目标岗位是后端工程师，技能栈为 Python/Go...
```

- `file_path` 可从 `memory.time` 推导，Memory 不存储文件路径
- MemoryStore 写文件前创建目录；RagLoader 扫描时目录不存在则跳过

**Chunk ↔ Memory 转换：**

`chunk_to_memory(chunk) -> Memory`：从 Chunk metadata 取 `id`/`agent`/`time`/`category`，content 取 Chunk.content。MemoryRetriever 和 MemoryBuilder 共用。

**设计决策：**
- 记忆按 Agent 分目录 —— 每个 Agent 独立管理自己的记忆；跨 Agent 检索走 `MemoryRetriever.search(agent=None)`
- 文件系统而非数据库 —— 人机可读、Git 可追踪、免运维
- 一文件一条记忆 —— 时间戳文件名天然有序，精确标识，无需再切分
- 观察者模式解耦 —— MemoryStore 不持有 RAG，通过事件 + Indexer/Retriever 桥接
- 不提供更新 —— 每次调用创建新文件；删除由用户驱动
- 记忆构建由 LLM 完成 —— 从对话中提取关键信息，非简单压缩
- 异步由 Builder facade 控制 —— MemoryStore 本身纯同步
- Profile / Preferences 暂缓 —— `data/profile/profile.md`，free-form section，LLM 辅助生成画像，后续详细讨论

### 4.6 主 Agent（编排器）

**用途：** 系统的入口 Agent。与所有 Agent 共享相同的基础能力（对话循环、工具调用、记忆读写），唯一区别是主 Agent 持有 `AgentRegistry`，可以调度子 Agent。子 Agent 不允许持有或调度其他 Agent。

**所有 Agent 的通用能力（由 `base.py` 定义）：**
- 维护对话循环（LLM JSON → 工具调度 → 结果喂回 → 循环，单步执行，由 App 层驱动循环）
- 工具调用（`ToolRegistry.get_for(name)` 拉取工具集，7b 未知工具附列表 / 7c 审批门禁 / 7d 自动执行）
- `_pending_tool` 断点恢复：跨 `process()` 调用保存挂起的工具调用
- `_round_counter` + `_max_rounds` 安全阀
- `process(input: Request) -> Response` 统一接口

**主 Agent 额外特权：**
- 通过 `AgentRegistry` 全局单例获取子 Agent 列表，根据意图调度子 Agent
- `switch_to_subagent(sub_agent, context)` 工具（仅 MainAgent 可见）：LLM 通过标准 tool_call 携带目标 Agent 名和上下文 → tool handler 返回 switch 标记 → BaseAgent 返回 FINISH + switch → App 切换 handler
- `switch_to_mainagent(summary)` 工具（所有子 Agent 自动注入）：子 Agent 退出并带回总结 → App 切回主 Agent → 向主 Agent `_history` 注入 `tool_call_result` 完成异步调用闭环
- 子 Agent 会话不进主 Agent 历史（仅 tool_call → ... → tool_call_result），主 Agent 持有全部上下文，子 Agent 无状态
- `provide_choices` 工具：LLM 向用户列出选项（如子 Agent 列表）
- `/exit_sub` CLI 命令：App 层拦截，主 Agent 前台时报错，子 Agent 时等价 `switch_to_mainagent("用户主动退出")`
- 意图路由纯 LLM 驱动，不做独立 `Router`

**`AgentRegistry`（`src/agents/registry.py`，全局单例）：**
```python
class AgentRegistry:
    _descriptors: dict[str, SubAgentDescriptor] = {}
    _agents: dict[str, BaseAgent] = {}
    def register(self, name, agent): ...        # 存入 + 构建 SubAgentDescriptor
    def get(self, name) -> BaseAgent: ...       # App.switch_agent() 用
    def list(self) -> list[str]: ...            # tool schema 的 choices 用
    def list_agents_prompt(self) -> str: ...    # → {{SUB_AGENTS_LIST}}
```

**`SubAgentDescriptor`：**
```python
@dataclass
class SubAgentDescriptor:
    name: str              # registry key
    display_name: str      # _get_agent_name()
    description: str       # _get_agent_description()
    responsibilities: str  # _get_responsibilities()
    hard_constraints: str  # _get_hard_constraints()
    # 不含 tone/verbosity/style —— 路由决策不需要沟通风格
```

与 `ToolRegistry` 对称：ToolRegistry 用 `@tool` 装饰器 + `to_xml()` → `{{ADDITION_TOOLS}}`，AgentRegistry 用 `register()` + `to_xml()` → `{{SUB_AGENTS_LIST}}`。

**Agent 切换流程：**
1. 主 Agent LLM 输出 `tool_call: switch_to_subagent(learning, "...")` → handler 返回 `_SwitchTarget` 标记
2. `BaseAgent._execute_tool()` 检测标记 → 不包装 `tool_call_result`，设 `_pending_switch`
3. `process()` 返回 `Response(type="finish", switch_agent="learning", switch_context="...")`
4. App 内层循环检测 `FINISH + switch_agent` → `switch_agent(name, context)` → `continue`
5. 子 Agent 接管，从头开始自己的 `_history`
6. 子 Agent 调 `switch_to_mainagent(summary)` → 同样流程切回
7. 主 Agent `_history` 注入 `tool_call_result(summary)`，`process(CONTINUE)` 继续

**关键接口 / 公开 API：**
- `BaseAgent.process(input: Request) -> Response` —— 统一入口（单步执行）
- `App.switch_agent(name, pre_prompt)` —— Agent 切换（待实现）
- `get_agent_registry()` —— 获取 AgentRegistry 全局单例
- `Response.switch_agent` / `Response.switch_context` —— FINISH + switch 表示切换

**位置：** `src/agents/main_agent.py` + `src/agents/registry.py` + `src/agents/base.py`

**设计决策：**
- 所有 Agent 共享相同的基础能力 —— 每个 Agent 独立管理自己的对话和工具调用
- Agent loop 上移至 App 层 —— `process()` 单步执行，每次只做一步（处理输入 → LLM → 分发 → 返回），工具暂停返回 PROGRESS/CONFIRM，由 App 内层 while 驱动循环
- 主 Agent 的唯一特权是 Agent 调度 + `AgentRegistry` —— 约束通过 `switch_to_subagent` tool 的 `agent=["main"]` 可见性实现，子 Agent 不允许持有或调度其他 Agent，保持两级结构
- 意图路由纯 LLM 驱动 —— 调度 = 工具，不做独立 Router（`src/main_agent/router.py` 不需要）
- `AgentRegistry` 全局单例（`get_agent_registry()`，双检锁），与 `ToolRegistry` 对称；子 Agent 通过 `SubAgentDescriptor` 抽取元数据，`list_agents_prompt()` 生成 prompt → `{{SUB_AGENTS_LIST}}` 占位符注入
- Agent 切换建模为异步工具调用 —— tool_call（switch_to_subagent）→ 子 Agent 多轮会话 → tool_call_result（switch_to_mainagent 的 summary），主 Agent 持有全部上下文，子 Agent 无状态
- 不新增 `ResponseType` —— 切换通过 `Response(type="finish", switch_agent=..., switch_context=...)` 表示
- `/exit_sub` CLI 命令在 App 层拦截，主 Agent 前台时报错
- `write_memory()` 作为 BaseAgent 便利方法，封装 `build_memories()`，默认异步（daemon 线程）；`query_cross_agent()` 后续封装为 tool；`get_recent_memories()` 废弃不做

#### UIBridge — 工具 handler 直连 CLI 交互

`ConfirmMode` 审批体系已被 UIBridge 取代。工具 handler 通过跨线程通信桥直接在后台线程中调用 CLI 前端交互，不再依赖 `process()` 返回特殊 ResponseType。

**UIBridge 接口（`src/cli/uibridge.py`）：**
```python
class UIBridge:
    # Tool Handler 端（后台线程，阻塞调用）
    def select(self, question: str, choices: list[str]) -> str: ...
    def confirm(self, message: str) -> bool: ...

    # App 端（主线程，轮询）
    has_request: bool        # 是否有待处理的 UI 请求
    action: str              # "select" / "confirm"
    question: str            # 提示文本
    choices: list[str]       # 选项（仅 select）
    def respond(self, result: str | bool) -> None: ...
```

**注入机制：** 模块级 `_current_bridge` + `get_bridge()`。App 在后台线程中调用 `_set_bridge(bridge)` → handler 通过 `get_bridge()` 获取 → handler 完成后 `_set_bridge(None)` 清理。Bridge 粒度为每次用户输入。

**线程模型：**
```
App.run() [主线程]                          BaseAgent.process() [后台线程]
  _process_with_spinner():                    process() → _execute_tool()
    while not done:                             handler(**payload)
      show spinner                                ui = get_bridge()
      if bridge.has_request:                      choice = ui.select(q, opts)  [BLOCK]
        render questionary              ←──→     return {"selected": choice}
        bridge.respond(result)                  ← TOOL_CALL_RESULT
```

**对现有流程的影响：**
- `_should_confirm()` 已恢复，在 `_execute_tool()` 中、handler 执行前统一检查 `ConfirmMode`，需审批时通过 UIBridge 弹窗
- `ConfirmMode` 恢复参与调度：`NEVER` 跳过、`ALWAYS` 强制审批、`CONFIG` 跟随 `TOOL_CONFIRM_ENABLED`
- `ResponseType.CONFIRM` 不再由 `process()` 返回，`App.run()` 中对应分支已移除
- 审批拒绝由框架统一处理：`_execute_tool()` 返回 `__reject__` TOOL_CALL_RESULT，`process()` 检测 `_pending_reject` → FINISH

**UIBridge 的两个使用层次：**

| 层次 | 调用方 | 方式 | 示例 |
|------|--------|------|------|
| 框架层 | `_execute_tool()` | `get_bridge().confirm()` 根据 `ConfirmMode` 自动审批 | web_search(CONFIG)、switch_to_subagent(ALWAYS) |
| 工具层 | 工具 handler | 自行调用 `get_bridge().select()`/`confirm()` 做非审批交互 | provide_choices 调 `select()` 列出选项 |

**`__reject__` sentinel：** 审批被拒时，`_execute_tool()` 追加 `{"__reject__": True}` 的 TOOL_CALL_RESULT 关闭调用链 + 设 `_pending_reject` → `process()` 返回 FINISH → App 回外层循环等用户输入。

### 4.7 简历 Agent

**用途：** 帮助用户创建、优化、定制 LaTeX 简历。通过 workspace 工具直接操作模板文件，支持从模板创建、按 JD 修改、编译 PDF 和预览。

**职责：**
- 复制 LaTeX 模板到工作区（`copy_template`）
- 用 workspace 工具（read / edit / replace / grep）填充占位符和修改内容
- 编译 LaTeX 为 PDF（`build_pdf`）
- 用系统默认工具打开 PDF 预览（`workspace_open`）

**工作流：**
```
copy_template(chn/en/all, prefix)  →  复制模板 + README.md
  ↓
workspace_read + README.md         →  LLM 理解模板结构和填充约束
  ↓
workspace_replace / workspace_edit  →  逐项填充占位符
  ↓
build_pdf                          →  编译 PDF
  ↓
workspace_open                     →  预览
```

**专属工具（`src/tools/resume_tools.py`）：**

| 工具 | 审批 | 用途 |
|------|------|------|
| `copy_template` | CONFIG | 复制 LaTeX 模板到工作区 |
| `build_pdf` | NEVER | `pdflatex -synctex=1 -interaction=nonstopmode` 编译，60s timeout |

**数据模型：** 原 `src/agents/resume/schemas.py` 已删除（M5-Review）。Schema-based 填充模式未启用（决策 114），LLM 直接用 workspace 工具编辑 LaTeX，无需维护数据模型。

**ResumeAgent（`src/agents/resume/agent.py`）：** 继承 `BaseAgent`，14 占位符实现，`_get_agent_key()` 返回 `RESUME_AGENT_KEY`。workspace 工具（agent=[RESUME_AGENT_KEY]）和 `query_reference_data`（agent=[\"*\"]) 自动可见。

**设计决策：**
- LLM 直接操作 LaTeX 文件而非 schema 填充（决策 114）—— 模板已有占位符，用 workspace_replace 替换即可
- `copy_template` 前 LLM 与用户确认语言 + 文件名前缀（决策 113）
- `build_pdf` 找不到 pdflatex 时抛 ToolCallException，LLM 告知用户安装
- `README.md` 始终跟随模板复制，作为 LLM 的模板操作手册

### 4.8 学习 Agent

**用途：** 根据用户技能差距（由简历 Agent 和岗位搜索 Agent 的输出推导）制定学习计划，追踪学习进度。

**职责：**
- 分析技能差距（目标岗位要求 vs 用户当前技能）
- 生成结构化学习计划
- 追踪学习进度
- 推荐学习资源

**关键接口 / 公开 API：**
- `LearningAgent.assess_gap(profile: Profile, target_jobs: list[Job]) -> SkillGap` —— 评估技能差距
- `LearningAgent.create_plan(skill_gap: SkillGap) -> StudyPlan` —— 生成学习计划
- `LearningAgent.check_progress() -> Progress` —— 查询学习进度

**内部结构：**
- 差距分析器：对比用户技能和目标岗位要求
- 计划生成器：调用 LLM 生成学习路线
- 进度追踪器：记录已完成的学习任务

**设计决策：**
- 学习计划和学习进度都存储在记忆模块中

### 4.9 面试 Agent

**用途：** 模拟技术面试，提供反馈。覆盖行为面试、技术问答、系统设计、代码实战等面试类型。

**职责：**
- 根据目标岗位和用户技能栈生成面试题
- 进行交互式模拟面试
- 评估回答质量并给出反馈
- 追踪面试准备进度

**关键接口 / 公开 API：**
- `InterviewAgent.start_session(type: InterviewType, focus: list[str]) -> Session` —— 开始模拟面试
- `InterviewAgent.answer(answer: str) -> Feedback` —— 提交回答并获取反馈
- `InterviewAgent.end_session() -> SessionReport` —— 结束面试并生成报告

**内部结构：**
- 题库生成器：根据岗位和技能生成针对性面试题
- 面试引擎：管理面试会话流程
- 评估器：调用 LLM 评估回答质量

**设计决策：**
- 面试会话结束后，关键反馈写入记忆模块

### 4.10 岗位搜索 Agent

**用途：** （待定 —— 具体实施方案尚未确定）

**备选方向：**
- 爬取招聘网站（拉勾、Boss 直聘、LinkedIn 等）
- 接入招聘平台 API
- 用户手动输入 JD，Agent 仅做分析和匹配

**待明确：**
- 数据源的选择
- 自动化程度（全自动搜索 vs 用户驱动）
- 合规性考量

### 4.11 日志模块

**用途：** 横切基础设施，为所有模块提供统一的日志记录能力。封装 Python 标准库 `logging`，零额外依赖。

**职责：**
- 提供 `get_logger(name: str) -> logging.Logger` 单一入口，获取命名 logger
- 懒加载初始化 —— 首次调用 `get_logger()` 时自动配置 handler 和格式，无需显式 `init()`
- 日志写入 `data/logs/app.log`，按文件大小轮转（`RotatingFileHandler`，10MB × 5 备份）
- `ERROR` 及以上级别同步输出到 stderr，不干扰 `rich` 的 stdout

**关键接口 / 公开 API：**
- `get_logger(name: str) -> logging.Logger` —— 获取命名 logger，首次调用自动初始化日志系统

**日志格式：**
```
2026-07-01 14:30:00 | INFO     | memory.store | 写入记忆成功
```

**内部结构：**
- `logger.py`：`get_logger()` 公开函数 + `_setup()` 内部初始化（读 config → 创建 `RotatingFileHandler` + `StreamHandler(stderr)` → 绑定到 root logger）

**设计决策：**
- 标准库即可，零额外依赖 —— `logging` + `RotatingFileHandler` 覆盖所有需求
- 懒加载 —— 不强制在 `main.py` 中显式初始化，任意模块 `get_logger(__name__)` 即可
- stderr 而非 stdout —— 不污染 `rich` 的终端渲染输出
- 按大小轮转而非按天 —— CLI 应用使用频率不均，按大小更可预测

### 4.12 Message 模块

**用途：** 通用消息 / 事件数据类，统一覆盖用户输入、系统指令、工具调用、工具结果和 LLM 回复。所有模块（CLI、Agent、LLM、Memory）共用此数据结构，是整个系统的数据总线。

**职责：**
- 定义 `Message` 数据类，作为对话历史和事件流的统一载体
- 不包含业务逻辑、持久化或网络操作 —— 纯粹的数据结构

**数据结构（`src/message.py`）：**

```
@dataclass
class Message:
    event_type: EventType      # EventType(StrEnum)，唯一 required 字段
    message: str = ""          # 展示文本（终端显示），默认空字符串
    id: str                    # uuid4 hex，唯一标识（auto）
    role: str = "user"         # 发送者角色：user / assistant / system
    timestamp: datetime        # 消息时间戳（auto）
    tool: str | None = None    # 工具名，仅 tool_call / tool_call_result 时填写
    tool_call_id: str | None   # 关联 tool_call 消息的 id，仅 tool_call_result 时填写
    event_payload: dict|None   # 结构化载荷（工具参数或调用结果）
    thinking: str|None = None  # LLM 内部推理；role="user" 时恒为 None
```

**事件类型枚举：**

```
class EventType(StrEnum):
    USER_INPUT = "user_input"            # 用户输入（输入侧）
    TOOL_CALL = "tool_call"              # 工具调用（输出侧）
    TOOL_CALL_RESULT = "tool_call_result" # 工具调用结果（输入侧）
    FINISH = "finish"                     # 对话结束（输出侧）
    SYSTEM_MESSAGE = "system_message"     # 系统提示/错误恢复（输入侧）
```

**字段语义：**

| 字段 | 含义 | 示例 |
|------|------|------|
| `event_type` | 事件类型，`EventType` 枚举值 | `EventType.USER_INPUT`、`EventType.TOOL_CALL` |
| `message` | 终端展示文本，默认 `""` | `tool_call_result` 时通常为空 |
| `role` | "谁发的"——消息来源控制 | user 下既有 `user_input` 也有 `tool_call_result` |
| `tool` | 工具名，串联调用链 | `"get_current_datetime"` |
| `tool_call_id` | 对应 `tool_call` 消息的 `id` | `"550e8400-e29b-41d4-a716-446655440000"` |
| `event_payload` | `dict | None`：`tool_call` 时为参数，`tool_call_result` 时为结果 | `{"datetime": "2026-07-06 19:30:00 +0800"}` |
| `thinking` | LLM 推理过程，对齐 `06_output_format.md` | user 消息恒为 `None` |

**与 prompt 的映射：**

- **输出侧（`06_output_format.md`）**：LLM 输出扁平 JSON → `Message.from_llm_reply()` 反序列化。`role` 固定 `"assistant"`，`event_type∈{tool_call, finish}`。
- **输入侧（`07_input_format.md`）**：对话历史经 `Message.to_json()` 序列化 → 注入 `{"role": "user", "content": ...}`。`role` 固定 `"user"`，`event_type∈{user_input, tool_call_result, system_message}`。

**序列化/反序列化：**

- `Message.to_json()` — `dataclasses.asdict()` + `json.dumps(default=str)`，处理 datetime 等非 JSON 类型
- `Message.from_llm_reply(reply)` — 静态方法，按扁平 JSON schema 解析；required 字段 `[]` 取值，optional 字段 `.get()` 默认 `None`

**设计决策：**
- **模块级独立** — 放在 `src/message.py`，与 config/logger 同为项目级基础设施
- **`EventType(StrEnum)` 枚举化** — `StrEnum` 继承 `str`，JSON 序列化后为字符串，与 LLM 交互无摩擦；代码中禁用裸字符串
- **`message` 默认 `""`** — `event_type` 是唯一 required 字段，`tool_call_result` 场景无需强制填 message
- **`tool` / `tool_call_id` 一级字段** — 比嵌套在 `event_payload` 内部更易于检索和追踪
- **输入/输出分文件** — `06_output_format.md`（输出 schema）+ `07_input_format.md`（输入 schema），字段互不越界，LLM 清楚区分
- **role 保留** — `event_type` 不能替代 `role`：role 回答"谁发的"，event_type 回答"什么类型"
- **thinking 独立字段** — 不混入 `message`，由 `SHOW_THINKING` flag 控制是否展示
- **event_payload 用 dict** — 足够灵活承载任意结构化载荷

### 4.13 Tool 系统

**用途：** 定义 Agent 可用的工具。工具注册、LLM 描述生成、可见性控制、调用调度统一管理。

**职责：**
- 提供 `@tool` 装饰器注册工具
- `Tool` dataclass 持有元数据并渲染 `04_tools.md` 格式的 XML
- `ToolRegistry` 全局管理，按 Agent 过滤

**`Tool` dataclass（`src/tools/registry.py`）：**
```python
@dataclass
class Tool:
    name: str              # fn.__name__
    purpose: str
    use_when: str
    do_not_use_when: str
    arguments_schema: str  # input_schema 自动补全后的 JSON
    expected_output: str
    handler: Callable      # 原函数
    agent: list[str] | None  # None = 通用

    def to_xml(self) -> str:  # 渲染为 04_tools.md 格式
```

**`@tool` 装饰器：**
- `input_schema` 扁平化：`{参数名: {description, default}}`，只写 LLM 需要的
- 装饰器阶段自动补齐：`type`（从 type hint）、`required`（从默认值有无）
- 构建 `Tool` → `ToolRegistry.register(tool)`

```python
@tool(
    purpose="读取文件指定行范围",
    use_when="需要查看文件内容时",
    do_not_use_when="文件不存在或路径无效时",
    expected_output="返回指定行范围的文本内容",
    input_schema={
        "path": {"description": "文件路径"},
        "line_from": {"description": "起始行号", "default": 1},
    },
    agent=["main"],  # 可选，None = 所有 Agent 可用
)
def read_content(path: str, line_from: int = 1) -> Message: ...
```

**`ToolRegistry`：**
```python
class ToolRegistry:
    _tools: dict[str, Tool] = {}
    @classmethod
    def register(cls, tool): ...        # @tool 装饰器调用
    @classmethod
    def get_for(cls, agent_name): ...   # 按 agent 过滤，返回可用工具
```

**调用流程：**
1. `BaseAgent.__init__` 调 `ToolRegistry.get_for(self.name)` → `self._tools`
2. 构建 system prompt 时过滤后的 tool 调用 `to_xml()` → 注入 `{{ADDITION_TOOLS}}`
3. Agent Loop 中 LLM 返回扁平 JSON（`tool` + `event_payload`）→ `tool.handler(**event_payload)` 返回纯数据 → 调用方包装为 `tool_call_result` Message（含 tool/tool_call_id/event_payload）
4. 调用前门禁检查：当前 Agent 是否在白名单

**设计决策：**
- `input_schema` 不写 `type` 和 `required` —— 从 type hint 自动推断，消除冗余和一致性风险
- 全局注册 + agent 过滤 —— 加载和发现解耦
- `to_xml()` 对齐 `04_tools.md` 模板 —— LLM 看到标准 XML 格式
- `extra_tools` 参数不进全局 Registry —— 实例级工具注入
- 工具错误自修复：未知工具 → system_message 附完整可用工具列表；执行失败 → error payload 附带 `arguments_schema` + `expected_output`，LLM 对照检查参数 → 自修复

**`ToolCallException`（`src/tools/exceptions.py`）：**
- `message: str` — 面向 LLM 的业务错误描述
- `suggestion: str | None` — 修复建议
- handler 只抛业务语义，`_execute_tool()` 框架层从 Tool 对象填充 `arguments_schema` + `expected_output`
- 普通 Exception 仍然走 `{error, error_code, arguments_schema, expected_output}`

**工具模块清单：**

| 模块 | 工具 | 数量 |
|------|------|------|
| `system_tool.py` | `get_current_datetime`, `get_working_dir` | 2 |
| `web_tool.py` | `web_search` | 1 |
| `switch_tools.py` | `switch_to_subagent`, `switch_to_mainagent` | 2 |
| `plan_tools.py` | `create_plan`, `update_plan_status`, `cancel_all_plans` | 3 |
| `workspace_tools.py` | `workspace_read`, `workspace_list`, `workspace_grep`, `workspace_search_file`, `workspace_replace`, `workspace_write`, `workspace_delete`, `workspace_move`, `workspace_edit`, `workspace_open` | 10 |
| `customer_file_tool.py` | `read_customer_file` | 1 |
| `rag_tools.py` | `query_memory`, `query_reference_data` | 2 |
| `resume_tools.py` | `copy_template`, `build_pdf` | 2 |
| **总计** | | **23** |

**位置：** `src/tools/`

### 4.14 面试问答 Agent

**用途：** M4 的验证性子 Agent。从 RAG 检索面试题，与用户进行问→答→评价的交互循环，验证 tool 注册 + agent loop + dispatch + return 全链路。

**职责：**
- 从 `data/reference/interview_questions/` 检索题目
- 提问 → 用户回答 → LLM 评价 → 下一题循环
- `return` 退回主 Agent

**关键接口 / 公开 API：**
- 继承 `BaseAgent`，实现 `process(Request) -> Response`
- `@tool search_questions(query)` — RAG 检索工具

**内部结构：**
- `InterviewAgent(BaseAgent)`：持有 RAG search 工具
- Loop：检索题目 → 展示 → 接收回答 → 评价 → 下一题或 `return`

**位置：** `src/agents/interview/`

**设计决策：**
- 作为 M4 唯一的真实子 Agent，复杂度最低 —— 只需要一个 RAG 工具
- 简历、学习等 Agent 在 M5+ 实现

### 4.15 Lifecycle 模块

**用途：** 进程生命周期管理，提供统一的退出清理入口。各模块通过 `register_shutdown()` 注册清理 hook，`shutdown()` 在进程退出前按注册逆序执行所有 hook。

**职责：**
- 提供 `register_shutdown(hook, *, name)` — 注册一个无参清理函数，同一 name 可重复注册
- 提供 `shutdown()` — 逆序执行所有已注册 hook，单个 hook 异常被捕获并记日志，不影响后续 hook 执行
- 与具体模块解耦 —— lifecycle 不感知 hook 内部逻辑

**当前注册的 hook：**

| name | 注册方 | 职责 |
|------|--------|------|
| `memory` | `src/memory/__init__.py` `_ensure_init()` | 等待所有 async `build_memories` daemon 线程完成 |

**调用方：** `main.py` 在 `app.run()` 返回后调用 `lifecycle.shutdown()`，不感知各模块内部清理细节。

**关键接口 / 公开 API：**
- `register_shutdown(hook, *, name="") -> None` — 注册退出清理 hook
- `shutdown() -> None` — 执行所有 hook，应在进程退出前调用一次

**位置：** `src/lifecycle.py`

**设计决策：**
- 松耦合 —— main.py 只调 `lifecycle.shutdown()`，不感知各模块清理细节；新模块只需一行 `register_shutdown()` 即可加入清理流程
- 逆序执行 —— 后注册的先清理，符合依赖关系（如 memory 依赖 RAG，RAG 先注册，memory 后注册，清理时 memory 先退出）
- 防御性 —— 单个 hook 异常不阻止其他 hook 执行，日志记录异常详情
- daemon 线程保持 —— `shutdown()` 提供优雅退出路径，不改变线程性质，强制杀进程不会被卡住

### 4.16 会话状态管理模块

**用途：** 自动持久化和恢复 Agent 对话状态，支持崩溃恢复和未来回滚。每次 LLM FINISH 时全量保存当前 handler 的对话历史 + plan 状态到文件系统。

**职责：**
- Auto-save：每次 FINISH 自动保存到 `data/save/{session_id}/` 目录
- Restore：`/restore` 命令从存档恢复 `_history` + `_plan`
- Plan 持久化：`session.json` 中按 agent 分字段存储 PlanItem 列表
- 延迟子 Agent 清理：sub→main 后等 main 成功保存再删 sub 存档

**存储结构：**

```
data/save/{session_id}/
├── session.json    # 元数据 + {agent_key}_plan
├── main.json       # 主 Agent 消息列表
└── resume.json     # 子 Agent 消息列表（仅在子 Agent 活跃时）
```

**关键接口 / 公开 API（`src/utils/saver.py`）：**

| 函数 / 类 | 说明 |
|-----------|------|
| `save_messages(filepath, history) -> bool` | 序列化 Message 列表为 JSON，写入文件 |
| `load_messages(filepath) -> list[Message] \| None` | 读取 JSON 文件，重建 Message 列表 |
| `save_session_meta(session_dir, session_id, current_agent, plan, plan_keys_to_remove)` | 写入 session.json，保留其他 agent 的 plan |
| `list_sessions(save_dir) -> list[dict]` | 扫描存档目录，按 mtime 倒序返回会话列表 |
| `SaveManager` | 高层封装类 — 管理 session_id、延迟清理、`save(agent_key, history, plan)`、`load_main()`、`load_sub()`、`find_sub_agent()`、`load_plans()`、`list_sessions()` |

**SaveManager 类（供 App 使用）：**

```python
class SaveManager:
    session_id: str               # 当前会话 ID（yyyyMMddHHmmss），可读写
    def save(agent_key, history, plan=None) -> None      # 保存 + 延迟清理
    def schedule_sub_cleanup(agent_key) -> None          # 标记 sub 存档待清理
    def load_main(session_id) -> list[Message] | None    # 读取主 Agent 历史
    def load_sub(session_id, agent_key) -> list[Message] | None  # 读取子 Agent 历史
    def find_sub_agent(session_id) -> str | None         # 找到子 Agent key
    def load_plans(session_id) -> dict[str, list]        # 读取所有 agent 的 plan
    def list_sessions() -> list[dict]                    # 列出所有存档会话
```

**序列化：**
- `Message.from_dict(d)` — 从 `dataclasses.asdict()` 输出重建 Message，含 `plan_status`（调用 `PlanStatusInfo.from_dict()`）
- `PlanStatusInfo.from_dict(d)` — 递归重建 PlanItem 列表
- 写入时用 `dataclasses.asdict()` + `json.dumps(default=str)`，无双层编码

**App 集成（`src/cli/app.py`）：**
- `_save_mgr = SaveManager(Path(config.SAVE_DIR))` — `__init__` 中创建
- `_auto_save()` → `_save_mgr.save(agent_key, history, plan=self._handler._plan)` — FINISH 时调用
- `/restore` → `_restore_interactive()` / `_do_restore(id)` — 用 `questionary.select` 或直接恢复

**位置：** `src/utils/saver.py` + `src/cli/app.py`（薄调用层）

**设计决策：**
- 独立于 BaseAgent —— Agent 不感知文件系统，状态管理在 App 层
- 延迟清理 —— sub→main 时不立即删 sub 存档，等 main 下次 FINISH 保存成功后再删，避免崩溃丢数据
- 全量覆盖写入 —— 每次 save 覆盖对应 JSON 文件，为后续 rollback 预留（每条 FINISH 一个完整快照）
- Plan 随 session.json 持久化 —— save 时写入当前 agent 的 plan 并保留其他 agent 的 plan，restore 时全部装载
- Session ID 由 App 生成 —— `yyyyMMddHHmmss` 格式，人类可读、自然有序
- 后续扩展 —— rollback 到上一句话（回退到前一条 FINISH 对应的 save），可通过 CLI 命令触发

## 5. 参考资料与约定

**参考资料：**
- [待补充] —— [涵盖内容]

**约定：**
- Python 3.14+，代码风格遵循 PEP 8
- 所有 Agent 实现 `src/agents/base.py` 定义的基类接口
- Agent 之间禁止直接调用，必须通过主 Agent 编排
- Agent 之间禁止共享内存引用，必须通过记忆模块读写
- 对话压缩由 LLM 完成，不引入额外 NLP 依赖
- 编写代码时不同步编写测试文件，除非用户显式要求
