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
│   ├── main_agent/          # 主 Agent 入口 & 编排逻辑
│   │   ├── __init__.py
│   │   ├── orchestrator.py  # 意图识别、Agent 调度
│   │   └── router.py        # 意图 → Agent 映射
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
│   │   └── formatters.py     # 通用格式化（时间戳文件名 + front-matter 拼装）
│   ├── logger.py             # 日志模块（横切基础设施）
│   ├── llm/                 # LLM 调用封装
│   │   ├── __init__.py
│   │   └── client.py         # 双 tier（pro / flash）统一调用
│   ├── rag/                 # RAG 模块（Embedder + Store + Loader + Reranker）
│   │   ├── __init__.py
│   │   ├── embedder.py      # 向量化（sentence_transformers）
│   │   ├── store.py         # Chroma 封装（collection 增删查）
│   │   ├── loader.py        # 启动加载 + 增量加载（threading 后台）
│   │   └── reranker.py      # 重排
│   ├── prompts/             # 提示词加载器
│   │   ├── __init__.py
│   │   └── loader.py        # 模板加载 & 变量替换
│   └── cli/                 # CLI 交互层
│       ├── __init__.py
│       ├── app.py           # 终端交互入口
│       └── handler.py       # Handler 抽象基类 + LLMHandler（M1 验证管线，M4 由 Orchestrator 替换）
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
│       │   ├── 05_communtion_style.md
│       │   ├── 06_output_format.md
│       │   └── 07_reserved.md
│       ├── PLACEHOLDER.md    # 占位符清单（14 个 per-Agent 占位符，不参与拼接）
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

### 4.0 Handler 协议

**用途：** 定义 CLI 层与业务逻辑层之间的桥接接口。CLI 不直接调用 LLM 或 Agent，而是调用注入的 `Handler`，由 Handler 负责具体的输入处理逻辑。这是一个抽象协议，初期用桩实现（`DemoHandler`）验证 I/O 管线，后续主 Agent 实现同一协议后无缝替换。

**职责：**
- 定义 `process(user_input: str) -> str` 抽象方法
- 提供 `DemoHandler` 桩实现用于测试渲染（输入 1→纯文本、2→markdown、3→选项列表）

**关键接口：**
- `Handler.process(user_input: str) -> str` —— 处理用户输入，返回响应文本

**位置：** `src/cli/handler.py`

**设计决策：**
- Handler 作为抽象协议而不是写死在 CLI 中 —— CLI 不关心谁在处理输入，后续主 Agent 只需实现 `process()` 接口即可接入
- M1 阶段用 `DemoHandler` 桩 —— 此时 Agent 层尚未构建，桩实现足够验证 I/O 管线
- 返回值是纯文本 —— 渲染由 CLI 层的 `rich` 负责

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
| `05_communtion_style.md` | `{{TONE}}`, `{{VERBOSITY}}`, `{{EXPLANATION_STYLE}}`, `{{STYLE_RULES}}`, `{{STYLE_AVOIDS}}` | 沟通风格 |
| `06_output_format.md` | 无 | 固定 |
| `07_reserved.md` | 无 | 固定 |

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

**必填变量：**

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `OPENAI_BASE_URL` | API 地址 | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | API 密钥 | 无（必填） |
| `LLM_PRO_MODEL` | pro tier 模型名 | `gpt-4o` |
| `LLM_FLASH_MODEL` | flash tier 模型名 | `gpt-4o-mini` |
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

有默认值的环境变量缺失时不报错，自动使用默认值。无默认值的必填变量（如 `OPENAI_API_KEY`）缺失时列出所有缺失项并 `sys.exit(1)`。

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
    _pro_params: dict = {}    # 子类按需覆盖，如 {"temperature": 0.3, "top_p": 0.9}
    _flash_params: dict = {}  # 子类按需覆盖，如 {"temperature": 0.0}

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
| `build_memories(conversation, agent, llm, store, sync_mode=False) -> list[Memory] \| None` | `memory/__init__.py` | Facade，构建记忆 + 保存。`sync_mode=True` 同步返回 Memory 列表；`False` 后台线程执行，返回 `None` |
| `MemoryStore.write_memory(agent, memory) -> str \| None` | `store.py` | 写文件（同步），发 `MemoryWritten` 事件。返回文件路径；失败返回 `None` 并记日志 |
| `MemoryStore.delete_memory(agent, file_path) -> bool` | `store.py` | 删文件（同步），发 `MemoryDeleted` 事件。成功返回 `True`；文件不存在或异常返回 `False` 并记日志。删除由用户驱动，不提供更新 |
| `MemoryRetriever.search(query, agent=None, top_k=5) -> list[Memory]` | `retriever.py` | 语义检索。`agent=None` 跨 Agent 全量检索 |
| `MemoryStore.on_write(callback)` / `on_delete(callback)` | `store.py` | 注册事件监听器 |

**内部结构：**

| 文件 | 职责 |
|------|------|
| `schemas.py` | `Memory(id: uuid, agent: str, time: datetime, content: str, category: str)` 及 `MemoryWrittenEvent`、`MemoryDeletedEvent`、`chunk_to_memory()` |
| `store.py` | 同步文件系统读写。`write_memory()`：生成时间戳文件名 → front-matter 格式化 → 写文件 → 发射事件。`delete_memory()`：删文件 → 发射事件。不提供读方法，不持队列/线程 |
| `indexer.py` | `MemoryIndexer`：监听 Store 事件，`_on_write` → `rag.load(file_path)`，`_on_delete` → `rag.delete(where={"source_file": file_path})`。构造即绑定，无公开方法 |
| `retriever.py` | `MemoryRetriever`：封装 `rag.search(filter={"agent": ...})`，`Chunk` → `Memory` 转换后返回 |
| `builder.py` | `MemoryBuilder`：加载 `data/prompts/memory/builder.md` 系统提示词 → 对话作为用户消息 → LLM 输出 `{"facts": "<string>", "preferences": "<string>"}` 严格 JSON → `json.loads()` 解析 → 注入 `id`/`time`/`agent`/`category` → `list[Memory]` |
| `__init__.py` | Facade：`build_memories()` 统一入口，支持 sync/async 模式 |

**文件组织：**

一条 Memory 一个文件：`data/memories/<agent>/<yyyyMMddHHmmss.fff>.md`

文件格式为 front-matter (简单 KV，`---` 包裹) + 正文：

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

**用途：** 系统的入口 Agent。与所有 Agent 共享相同的基础能力（对话循环、意图识别、工具调用、记忆读写），唯一区别是主 Agent 持有 `AgentRegistry`，可以调度子 Agent。子 Agent 不允许持有或调度其他 Agent。

**所有 Agent 的通用能力（由 `base.py` 定义）：**
- 维护对话循环
- 意图识别与分发
- 工具调用（RAG、记忆读写、其他工具）
- 记忆读写便利方法：`self.write_memory(memory)` / `self.get_recent_memories(limit)` / `self.query_cross_agent(query, agents, limit)`，内部自动传入 `self.name`
- 任务完成后将结果写入记忆模块

**主 Agent 额外特权：**
- 持有 `AgentRegistry`，根据意图调度子 Agent
- 调度子 Agent 不依赖独立提示词，而是定义为工具（如 `dispatch_resume`），通过 `{{ADDITION_TOOLS}}` 注入主 Agent 的工具列表。LLM 通过标准工具选择流程（`04_tools.md` + `06_output_format.md`）完成意图识别和调度

**关键接口 / 公开 API：**
- `Orchestrator.run(user_input: str) -> str` —— 主循环入口，接收用户输入，返回 Agent 响应
- `Orchestrator.dispatch(intent: Intent) -> AgentResult` —— 根据意图调度子 Agent
- `Router.classify(user_input: str) -> Intent` —— 意图分类

**内部结构：**
- `Orchestrator` 持有 `Router`（意图识别）、`MemoryStore`（记忆读写）和 `AgentRegistry`（子 Agent 注册表）
- 子 Agent 实例通过 `AgentRegistry` 获取
- 每次对话轮次结束后，将本轮交互写入记忆模块

**设计决策：**
- 所有 Agent 共享相同的基础能力，而非只有主 Agent 拥有编排逻辑 —— 每个 Agent 独立管理自己的对话和工具调用
- 主 Agent 的唯一特权是 Agent 调度 —— 子 Agent 不允许再持有子 Agent，保持两级结构
- 意图路由在主 Agent 内完成 —— 主 Agent 拥有全局上下文，适合做调度决策

### 4.7 简历 Agent

**用途：** 帮助用户创建、优化、定制简历。根据目标岗位 JD 调整简历内容，提供修改建议。

**职责：**
- 解析用户现有简历
- 根据 JD 匹配并优化简历内容
- 生成简历修改建议
- 输出优化后的简历（Markdown / LaTeX / PDF）

**关键接口 / 公开 API：**
- `ResumeAgent.analyze(resume: str) -> ResumeAnalysis` —— 分析简历结构
- `ResumeAgent.tailor(resume: str, jd: str) -> TailoredResume` —— 根据 JD 定制简历
- `ResumeAgent.suggest(resume: str) -> list[Suggestion]` —— 通用优化建议

**内部结构：**
- 简历解析器：从 Markdown/PDF/纯文本中提取结构化信息
- JD 匹配引擎：对比简历和 JD，找出差距
- 优化生成器：调用 LLM 生成修改后的简历内容

**设计决策：**
- 简历 Agent 不直接存储简历 —— 简历内容作为记忆存储在记忆模块中，便于其他 Agent 引用

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
    message: str              # 展示文本（终端显示）
    event_type: str           # 事件类型：user_input / system_input / tool_call / tool_call_result / finish / ...
    role: str = "user"        # 发送者角色：user / assistant / system
    timestamp: datetime       # 消息时间戳
    id: str                   # uuid4 hex，唯一标识
    event_payload: dict|None  # 结构化载荷（工具名、参数、结果等）
    thinking: str|None        # LLM 内部推理；user 消息恒为 None
```

**字段语义：**

| 字段 | 含义 | 示例 |
|------|------|------|
| `message` | 始终是终端展示文本，与 `action.message` 语义一致 | "正在搜索相关面试题..." |
| `event_type` | 区分消息语义，非穷举列表，随工具扩展追加 | `user_input`、`tool_call`、`finish` |
| `role` | "谁发的"——消息来源控制，不可被 event_type 替代 | system 角色下既有 `system_input` 也有 `tool_call_result` |
| `thinking` | LLM 推理过程，对齐 `06_output_format.md` 顶层 `"thinking"` | user 消息恒为 `None` |
| `event_payload` | `dict | None`，承载工具调用、参数、结果等结构化数据 | `{"tool": "search", "args": {...}}` |

**与 `06_output_format.md` Schema 的映射：**

```
Schema:  { "thinking": "...", "action": { "id": "...", "tool": "...", "message": "...", "args": {} } }
           ─────────────        ─────────────────────────────────────────────────────────
           → Message.thinking    → Message.id    → Message.event_type  → Message.message  → Message.event_payload
```

**设计决策：**
- **模块级独立** — 放在 `src/message.py`，与 config/logger 同为项目级基础设施。放在 memory 下会导致 CLI/Agent/LLM 反向依赖 memory 模块
- **role 保留** — `event_type` 不能替代 `role` 做消息来源控制，二者职责不同：role 回答"谁发的"，event_type 回答"什么类型"
- **thinking 独立字段** — 不混入 `message`，避免污染展示文本；未来由 `SHOW_THINKING` flag 控制是否展示（当前不做）
- **event_payload 用 dict** — 足够灵活承载任意结构化载荷，不需要为每种工具定义具体 TypedDict
- **event_type 非穷举** — 当前候选值为 `user_input`、`system_input`、`tool_call`、`tool_call_result`、`finish`，后续随工具扩展追加新类型

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
