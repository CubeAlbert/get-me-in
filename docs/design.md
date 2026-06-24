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
  - [4.1 提示词模块](#41-提示词模块)
  - [4.2 LLM 调用模块](#42-llm-调用模块)
  - [4.3 RAG 模块](#43-rag-模块)
  - [4.4 记忆模块](#44-记忆模块)
  - [4.5 主 Agent（编排器）](#45-主-agent编排器)
  - [4.6 简历 Agent](#46-简历-agent)
  - [4.7 学习 Agent](#47-学习-agent)
  - [4.8 面试 Agent](#48-面试-agent)
  - [4.9 岗位搜索 Agent](#49-岗位搜索-agent)
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
| 向量存储 | Chroma（内存模式） | 开发阶段零配置，后续可切换本地持久化 |
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
│   │   ├── __init__.py
│   │   ├── store.py         # 记忆读写接口
│   │   ├── compressor.py    # LLM 对话压缩成记忆
│   │   └── schemas.py       # 记忆数据结构定义
│   ├── llm/                 # LLM 调用封装
│   │   ├── __init__.py
│   │   └── client.py         # 双 tier（pro / flash）统一调用
│   ├── rag/                 # RAG 模块（Chroma + 召回 + 重排）
│   │   ├── __init__.py
│   │   ├── embedder.py      # 向量化（sentence_transformers）
│   │   ├── chunker.py       # 按分隔符切分文本为逻辑块
│   │   ├── store.py         # Chroma 封装（collection 增删查）
│   │   ├── retriever.py     # 召回
│   │   └── reranker.py      # 重排
│   ├── prompts/             # 提示词加载器
│   │   ├── __init__.py
│   │   └── loader.py        # 模板加载 & 变量替换
│   └── cli/                 # CLI 交互层
│       ├── __init__.py
│       └── app.py           # 终端交互入口
├── data/                    # 持久化存储（文件系统）
│   ├── profile/
│   │   └── profile.md       # 用户档案（技能、经历、教育）
│   ├── preferences/
│   │   └── preferences.md   # 用户偏好（目标岗位、薪资、地点等）
│   ├── memories/
│   │   ├── main/            # 按 Agent 分目录，各自按日期分文件
│   │   │   └── 2026-06-24.md
│   │   ├── resume/
│   │   ├── learning/
│   │   ├── interview/
│   │   └── job_search/
│   └── prompts/             # 提示词模板（按用途组织，不按 Agent 划分）
│       ├── general_agent/   # 所有 Agent 强制拼接的公共前缀（多文件拼接）
│       │   ├── safety.md
│       │   ├── tools.md
│       │   └── output_format.md
│       ├── orchestrator.md
│       ├── memory_compressor.md
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

### 4.1 提示词模块

**用途：** 集中管理所有提示词模板，提供加载和变量替换能力。提示词按用途组织，不绑定特定 Agent —— 同一个提示词可以被多个模块使用。

**职责：**
- 从 `data/prompts/` 加载提示词模板
- 为 Agent 加载提示词时，强制将 `general_agent/` 目录下所有文件拼接后放在最前面
- 支持变量替换（`{user_name}`、`{skills}` 等占位符）
- 按名称获取提示词，调用方不关心文件路径

**关键接口 / 公开 API：**
- `PromptLoader.get(name: str, **variables) -> str` —— 按名称加载提示词并替换变量；若调用方是 Agent，自动在前面拼接 `general_agent/` 内容
- `PromptLoader.list() -> list[str]` —— 列出所有可用提示词名称
- `PromptLoader.get_raw(name: str, **variables) -> str` —— 仅加载指定提示词，不拼接公共前缀（供记忆压缩等非 Agent 模块使用）

**内部结构：**
- `loader.py`：扫描 `data/prompts/` 下的所有模板文件，构建名称→模板的映射；`get()` 对 Agent 调用方强制拼接 `general_agent/` 目录下所有 `.md` 文件；`get_raw()` 跳过拼接

**设计决策：**
- 按用途而非按 Agent 命名 —— 提示词可能被多个模块复用（例如 `skill_gap.md` 可能被简历 Agent 和学习 Agent 同时使用）
- Markdown 格式 —— 人可读，支持 Markdown 语法，LLM 提示词天然适合
- 提示词与代码分离 —— 调整提示词不需要改代码，降低迭代成本
- `PromptLoader` 无状态 —— 每次 `get()` 都重新读文件，修改提示词后无需重启

### 4.2 LLM 调用模块

**用途：** 封装 LLM 调用，提供两种能力等级（pro / flash），供 Agent 基类复用。Agent 不感知具体 model 名称，只需选择调用等级。

**职责：**
- 初始化 OpenAI 客户端（base_url、api_key 从环境变量注入）
- 提供 `chat_pro()` 和 `chat_flash()` 两个入口
- 错误直接抛出，不做 fallback

**环境变量：**

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `OPENAI_BASE_URL` | API 地址 | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | API 密钥 | 无（必填） |
| `LLM_PRO_MODEL` | pro tier 模型名 | `gpt-4o` |
| `LLM_FLASH_MODEL` | flash tier 模型名 | `gpt-4o-mini` |

`.env` 文件通过 `python-dotenv` 在应用启动时加载。

**关键接口 / 公开 API：**
- `LLMClient.chat_pro(messages: list[dict], **kwargs) -> str` —— 调用 pro tier 模型，返回回复文本
- `LLMClient.chat_flash(messages: list[dict], **kwargs) -> str` —— 调用 flash tier 模型，返回回复文本

**内部结构：**
- `client.py`：`LLMClient` 类，构造函数从 `os.environ` 读取配置，实例化 `openai.OpenAI`；两个 `chat_*` 方法内部调用 `self.client.chat.completions.create(model=..., messages=...)` 并返回 `choice.message.content`

**Agent 基类中的封装（`src/agents/base.py`）：**

Agent 基类持有 `LLMClient` 引用，暴露两个便利方法供子类调用：

```python
class BaseAgent:
    def __init__(self, llm_client: LLMClient, ...):
        self._llm = llm_client

    def _llm_pro(self, messages: list[dict], **kwargs) -> str:
        """高能力调用 — 用于需要深度推理的任务"""
        return self._llm.chat_pro(messages, **kwargs)

    def _llm_flash(self, messages: list[dict], **kwargs) -> str:
        """快速调用 — 用于简单分类、格式化等轻量任务"""
        return self._llm.chat_flash(messages, **kwargs)
```

子 Agent 调用 `self._llm_pro(messages)` 或 `self._llm_flash(messages)`，不传 model 名。

**设计决策：**
- 双 tier 而非单一接口 —— 不同任务对模型能力/延迟需求不同，pro 做深度推理（简历分析、面试评估），flash 做轻量任务（意图分类、格式化输出）
- model 名不暴露给 Agent —— 由运维/部署层面决定具体模型，Agent 只关心能力等级
- 不做 fallback —— 保持简单，调用失败直接抛出错误到 CLI 层展示
- 环境变量注入 —— 切换后端只需改 `.env`，不修改代码
- 使用 OpenAI SDK 而非自建 HTTP 调用 —— 生态兼容性好（任何 OpenAI-compatible 后端均可），且 SDK 内建重试、流式等能力

### 4.3 RAG 模块

**用途：** 共享基础设施层，为各模块提供语义检索能力。使用 `sentence_transformers` 做向量化和重排，`Chroma` 作为向量存储。向量存储先使用内存模式，后续可切换为本地持久化。

**职责：**
- 将文本向量化（Embedder）
- 将文档按分隔符切分为逻辑块（Chunker）—— 分隔符由写入方定义
- 向量存储与检索（ChromaStore）
- 召回（Retriever）与重排（Reranker）

**关键接口 / 公开 API：**
- `Embedder.embed(texts: list[str]) -> list[list[float]]` —— 将文本转换为向量
- `Chunker.chunk(text: str, separator: str, metadata: dict) -> list[Chunk]` —— 按分隔符切分文本为逻辑块，每个块携带 metadata
- `ChromaStore.add(chunks: list[Chunk], collection: str) -> None` —— 将块向量化后存入指定 collection
- `ChromaStore.query(query_vector: list[float], collection: str, filter: dict | None, top_k: int) -> list[Chunk]` —— 在指定 collection 中检索
- `Retriever.retrieve(query: str, collection: str, filter: dict | None, top_k: int = 20) -> list[RetrievalResult]` —— 召回
- `Reranker.rerank(query: str, candidates: list[RetrievalResult], top_k: int = 5) -> list[RetrievalResult]` —— 重排

**处理流程：**

```
写入:
  MD 文本 → Chunker.chunk(text, separator, metadata) → 逻辑块列表
              │
              └→ Embedder.embed(chunks) → 向量
                      │
                      └→ ChromaStore.add(vectors, metadata, collection)

检索:
  查询 → Embedder.embed(query) → 查询向量
          │
          ├→ ChromaStore.query(vector, collection, filter, top_k=20)
          │      │
          │      └→ Reranker.rerank(query, candidates, top_k=5)
          │             │
          └─────────────┘
                 最终结果
```

**内部结构：**
- `Embedder`：封装 `sentence_transformers` 模型加载和推理
- `Chunker`：通用切分器，按传入的 `separator` 切分文本为逻辑块，附加 `metadata`（agent、date、chunk_id 等）—— 不关心内容语义，只按分隔符切
- `ChromaStore`：封装 Chroma 客户端，管理 collection 的创建、写入、查询。默认内存模式
- `Retriever`：组合 `Embedder` + `ChromaStore`，完成召回流程
- `Reranker`：使用 `sentence_transformers` 的 CrossEncoder 对粗排结果精排

**Collection 设计：**

Chroma 按模块/用途划分 collection，不按 Agent 划分：

| Collection | 用途 | 数据来源 |
|------------|------|----------|
| `memories` | 所有 Agent 的记忆条目 | Agent 通过记忆模块写入 |
| `interview_questions` | 面试题库 | 项目初始化时导入 |
| `job_descriptions` | 岗位描述库 | 用户输入或爬取 |

**设计决策：**
- 切分策略由写入方定义 —— Agent 在固化记忆时按约定分隔符组织输出，Chunker 只负责按分隔符切，不感知内容语义
- Chroma 内存模式先行 —— 开发阶段零配置，后续切换持久化只需改 Chroma 初始化参数
- Collection 按模块划分 —— 不同数据的检索场景和使用频率不同，独立 collection 便于管理
- 召回和重排分离 —— 召回用 bi-encoder（快，粗筛），重排用 cross-encoder（慢但准，精排）
- RAG 是基础设施，不是 Agent —— 不参与 Agent 调度，由需要检索能力的模块直接调用

### 4.4 记忆模块

**用途：** 系统的持久化上下文层。存储用户档案、偏好，以及经过 LLM 压缩的对话记忆。所有 Agent 通过此模块获取上下文。记忆按 Agent 隔离存储，各 Agent 写入自己的子目录。

**职责：**
- 结构化数据（档案、偏好）的 CRUD
- 对话记忆的写入和检索（按 Agent 隔离）
- 对话压缩：调用 LLM 将原始对话压缩为结构化记忆条目
- 为各 Agent 提供上下文查询接口

**关键接口 / 公开 API：**
- `MemoryStore.get_profile() -> Profile` —— 获取用户档案
- `MemoryStore.get_preferences() -> Preferences` —— 获取用户偏好
- `MemoryStore.write_memory(agent: str, memory: Memory) -> None` —— 写入一条记忆到指定 Agent 的子目录
- `MemoryStore.get_recent_memories(agent: str, limit: int, related_to: str | None) -> list[Memory]` —— 获取指定 Agent 最近的记忆条目
- `MemoryStore.query_cross_agent(query: str, agents: list[str] | None, limit: int) -> list[Memory]` —— 跨 Agent 检索记忆（通过 RAG 模块），agents 为 None 时查询全部
- `MemoryCompressor.compress(conversation: list[Message]) -> list[Memory]` —— 将对话压缩为记忆

**内部结构：**
- `MemoryStore`：文件系统读写封装，按 Agent 路由到 `data/memories/<agent>/` 子目录，按日期分文件
- `MemoryCompressor`：调用 LLM 完成对话压缩，提取关键信息和决策
- `schemas.py`：定义 `Profile`、`Preferences`、`Memory` 等数据结构

**Memory ↔ RAG 接口：**

记忆模块持有 RAG 模块的 `Chunker`、`ChromaStore`、`Retriever`、`Reranker` 引用，在写入和跨 Agent 检索时调用：

```
write_memory(agent, memory)
  ├─ 1. 格式化: memory.to_markdown() → 带分隔符的 Markdown 文本
  │       分隔符由 Agent 定义，固化在记忆输出中
  ├─ 2. 写入文件: data/memories/<agent>/<date>.md
  └─ 3. 切分入库: Chunker.chunk(md_text, separator, {agent, date})
           └─ Embedder.embed(chunks) → ChromaStore.add(chunks, collection="memories")

query_cross_agent(query, agents, limit)
  ├─ 1. Retriever.retrieve(query, collection="memories", filter={agent: in(agents)}, top_k=20)
  ├─ 2. Reranker.rerank(query, candidates, top_k=limit)
  └─ 3. 返回 Memory 对象列表
```

**设计决策：**
- 记忆按 Agent 分目录 —— 每个 Agent 独立管理自己的记忆，避免互相干扰；跨 Agent 检索通过 RAG 模块的语义搜索实现
- 文件系统而非数据库 —— 人机可读、Git 可追踪、免运维
- 记忆按日期分文件 —— 便于检索和人工翻阅，单文件不会过大
- 对话压缩由 LLM 完成 —— 压缩质量是关键，规则压缩会丢失语义

### 4.5 主 Agent（编排器）

**用途：** 系统的入口 Agent。与所有 Agent 共享相同的基础能力（对话循环、意图识别、工具调用、记忆读写），唯一区别是主 Agent 持有 `AgentRegistry`，可以调度子 Agent。子 Agent 不允许持有或调度其他 Agent。

**所有 Agent 的通用能力（由 `base.py` 定义）：**
- 维护对话循环
- 意图识别与分发
- 工具调用（RAG、记忆读写、其他工具）
- 记忆读写便利方法：`self.write_memory(memory)` / `self.get_recent_memories(limit)` / `self.query_cross_agent(query, agents, limit)`，内部自动传入 `self.name`
- 任务完成后将结果写入记忆模块

**主 Agent 额外特权：**
- 持有 `AgentRegistry`，根据意图调度子 Agent

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

### 4.6 简历 Agent

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

### 4.7 学习 Agent

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

### 4.8 面试 Agent

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

### 4.9 岗位搜索 Agent

**用途：** （待定 —— 具体实施方案尚未确定）

**备选方向：**
- 爬取招聘网站（拉勾、Boss 直聘、LinkedIn 等）
- 接入招聘平台 API
- 用户手动输入 JD，Agent 仅做分析和匹配

**待明确：**
- 数据源的选择
- 自动化程度（全自动搜索 vs 用户驱动）
- 合规性考量

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
