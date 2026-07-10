<!--
阅读指南：本文件可能较长。请先阅读目录，然后跳转到相关章节。
每次读取 100 行，直到该章节读完。
-->

# 实施计划

工作流遵循 **Plan → Execute → Result Validation → Replan** 循环。计划是动态的 —— 执行结果验证后可能推翻原有计划，此时直接删除不适用的内容并写入新计划。历史版本由 Git 负责，本文档始终只保留当前有效的计划。

## 目录

- [1. 里程碑](#1-里程碑)
- [2. 关键依赖](#2-关键依赖)

---

## 1. 里程碑

### 里程碑 1 —— 项目骨架 & 基础设施 ✅ 已完成

- **预期产出：** 可运行的项目骨架，LLM 能调用，CLI 能对话
- **验收标准：**
  - `pyproject.toml` 包含所需依赖
  - `src/config.py` 完成环境变量集中管理（启动加载 .env + 校验必填变量）
  - `src/llm/` 完成适配层封装，至少支持一个后端（Claude API 或 OpenAI）
  - `src/cli/app.py` 实现基本对话循环（`input()` + `rich` 渲染 Markdown 输出 + `$EDITOR` 长文本输入）
  - `src/prompts/loader.py` 完成：`get(**kwargs)` 拼接 `general_agent/` + 替换占位符；`get_raw(name, **kwargs)` 加载指定文件跳过拼接
  - `data/prompts/` 下 `general_agent/` 已创建 9 个模板文件（`01_role.md` ~ `09_reserved.md`），`memory/builder.md` 已创建 MemoryBuilder 系统提示词
  - `main.py` 能启动并完成一轮对话
- **前置依赖：** 无

### 里程碑 2 —— RAG 模块 ✅ 已完成

- **预期产出：** 可用的语义检索能力，支持写入和查询
- **验收标准：**
  - `src/rag/embedder.py` ✅ — 封装 `sentence_transformers` bi-encoder（`BAAI/bge-base-zh-v1.5`），模型名由环境变量配置
  - `src/rag/chunker.py` ✅ — 按 `---` 切分文本为逻辑块，附加 metadata，过滤空白片段
  - `src/rag/store.py` ✅ — 封装 Chroma（内存/持久化），内部持有 Embedder；`add()` / `query(query_text)` / `remove(source_file)`
  - `src/rag/loader.py` ✅ — 遍历 `data/reference/` + `data/memories/`，状态机（IDLE/LOADING/READY/ERROR），`auto_load()` daemon 后台加载，持久化模式 `.last_update` 增量，`reload(target)` 手动重载
  - `src/rag/reranker.py` ✅ — CrossEncoder 精排，分数注入 `metadata["rerank_score"]`，`__init__` 预热
  - `src/rag/__init__.py` ✅ — 公共入口：`search()` / `load()` / `is_ready()` 三个函数，内部双检锁懒加载单例
  - 端到端验证通过 ✅ — `search("快速排序")` 经召回→重排返回正确结果

### 里程碑 3 —— 记忆模块 ✅ 已完成

- **预期产出：** 完整的记忆写入、删除、语义检索、LLM 构建能力；RAG 公开接口扩充；日志基础设施
- **验收标准：**
  - `src/logger.py` 日志模块就绪（`get_logger()` + `RotatingFileHandler` + stderr 输出）
  - Chunker 抽出到 `src/utils/chunker.py`，新增 front-matter 解析（`---` KV → metadata）
  - RAG `search()` 加 `filter` 参数；`delete(where)` 按 metadata 删除
  - 现有 reference 文件添加 front-matter（`category`）
  - `src/memory/schemas.py` 定义 Memory、Message、事件等数据结构
  - `src/memory/store.py` 同步文件系统读写 + 事件机制（`on_write` / `on_delete`）
  - `src/memory/indexer.py` MemoryIndexer 监听事件 → RAG 索引
  - `src/memory/retriever.py` MemoryRetriever 语义检索（`rag.search(filter=...)`）
  - `src/memory/builder.py` MemoryBuilder：对话 JSON → `chat_flash(response_format=json_object)` → `\n` 拆分 → `\n\n---\n\n` 拼接，Chunker 按 `---` 切分独立索引
  - `src/memory/__init__.py` Facade：`init()` + `build_memories()` + `search_memories()` + `delete_memory()` 四大公开函数，类 RAG 统一入口
  - 一文件一条记忆（`yyyyMMddHHmmss.fff.<category>.md`），category 在文件名避免冲突，目录由 `write_memory()` 自动创建
  - 端到端：构建记忆 → 写入 → 索引 → 检索 链路验证通过
- **前置依赖：** 里程碑 1（LLM）+ 里程碑 2（RAG）

### 里程碑 4 —— BaseAgent & 主 Agent

- **预期产出：** Agent 基类、Tool 系统、Request/Response 协议、主 Agent、面试问答子 Agent
- **进度：** M4-1（CLI + Response 升级）✅；M4-2（Tool 系统）✅；M4-3（BaseAgent）✅；M4-4（主 Agent）🔄（AgentRegistry + switch 机制已实现，待端到端验证）；M4-5（入口集成）🔄（MainAgent + JobSearchAgent 已注入 App）
- **验收标准：**
  - `src/response.py` — ✅ `Response` dataclass + `switch_agent`/`switch_context`/`switch_tool_call_id`
  - `src/request.py` — ✅ `Request` dataclass + `RequestType`（`USER_INPUT` / `CONTINUE` / `CONFIRM_APPROVED`）
  - `src/tools/registry.py` — ✅ `Tool` dataclass + `@tool` 装饰器 + `ToolRegistry` + `agent_key` + `"*"` sentinel
  - `src/tools/switch_tools.py` — ✅ `switch_to_subagent` + `switch_to_mainagent`
  - `src/cli/app.py` — ✅ 双循环 + questionary + FINISH 分支 switch 检测 + `/exit_sub`
  - `src/agents/base.py` — ✅ Agent Loop + `_pending_switch` + `_get_agent_key()` + `_get_sub_agents_list()` + CONFIRM 拒绝处理
  - `src/agents/main_agent.py` — ✅ `MainAgent(BaseAgent)`：14 个占位符值 + `_get_agent_key()` → `"main"` + `_get_sub_agents_list()` 覆盖
  - `src/agents/registry.py` — ✅ `AgentRegistry` 全局单例 + `SubAgentDescriptor` + `list_agents_prompt()`
  - `src/agents/base.py` — ✅ Agent Loop（单步执行 + `_pending_tool` 断点恢复 + `_round_counter` 安全阀）；✅ `list[Message]` 对话历史；✅ 事件分发（FINISH/TOOL_CALL）；✅ 工具调度 7b-7d（未知工具/审批门禁/自动执行）；✅ `process(Request) -> Response`；✅ `_get_sub_agents_list()` → `{{SUB_AGENTS_LIST}}` 占位符
  - `src/agents/main_agent.py` — 🔄 `MainAgent(BaseAgent)`：✅ 14 个占位符值 + ✅ `_get_sub_agents_list()` 覆盖；⬜ Agent 切换机制（switch tool + Response + App.switch_agent）
  - `src/agents/registry.py` — ✅ `AgentRegistry` 全局单例（`get_agent_registry()`）+ `SubAgentDescriptor` + `list_agents_prompt()`
  - `src/agents/interview/` — ⬜ `InterviewAgent(BaseAgent)`：RAG search 工具 + 问→答→评价 loop + `return` 退回
  - `main.py` — ⬜ 组装全链路（`MainAgent` + `InterviewAgent` + `AgentRegistry` + `ToolRegistry` → `App`）
  - `AGENT_MAX_ROUNDS` 环境变量 — ✅
  - `uv add questionary` — ✅
  - 端到端验证：主 Agent dispatch → 面试 Agent 接管 → 问答交互 → `return` 退回主 Agent — ⬜
- **前置依赖：** 里程碑 1（提示词 + LLM）+ 里程碑 2（RAG）+ 里程碑 3（记忆 + config）

### 里程碑 5 —— 简历 Agent

- **预期产出：** 可用的简历分析和定制功能
- **验收标准：**
  - 解析用户简历（Markdown 输入），提取结构化信息
  - 根据 JD 定制简历，输出优化建议和修改后的简历
  - 分析结果和定制后的简历写入记忆模块
- **前置依赖：** 里程碑 4（BaseAgent）

### 里程碑 6 —— 学习 Agent

- **预期产出：** 技能差距分析和学习计划生成
- **验收标准：**
  - 读取用户档案和岗位要求，评估技能差距
  - 生成结构化学习计划并写入记忆模块
  - 支持进度查询和更新
- **前置依赖：** 里程碑 4（BaseAgent）

### 里程碑 7 —— 面试 Agent

- **预期产出：** 交互式模拟面试
- **验收标准：**
  - 根据岗位和技能生成针对性面试题
  - 支持交互式面试会话（开始→回答→反馈→结束）
  - 面试结束后生成报告并写入记忆模块
- **前置依赖：** 里程碑 4（BaseAgent）

### 里程碑 8 —— 岗位搜索 Agent

- **预期产出：** （待定 —— 方案确定后细化）
- **验收标准：** [待明确]
- **前置依赖：** 里程碑 4（BaseAgent）

## 2. 关键依赖

### 外部依赖

- `sentence_transformers` 模型下载 —— 首次加载需联网下载 bi-encoder 和 cross-encoder 模型文件
- LLM API（Claude API / OpenAI）—— 需要有效的 API Key 和网络访问

### 跨领域依赖

- BaseAgent（里程碑 4）是后续所有子 Agent 的前置条件 —— 简历/学习/面试三个 Agent 可并行开发，但均依赖 BaseAgent 就绪
- RAG 模块（里程碑 2）虽独立开发，但记忆模块（里程碑 3）强依赖它 —— RAG 的接口必须在里程碑 2 完成后稳定
- 提示词模块（里程碑 1）需在 Agent 开发前就绪 —— 所有 Agent 的 LLM 调用都走 PromptLoader

---

## 计划更新规则

- **直接删除：** 不适用的里程碑、验收标准或依赖项直接删除，不保留划掉或标记
- **直接追加：** 新里程碑追加到已有里程碑之后
- **版本控制：** 所有删除和修改的历史由 Git 追溯，本文档不保留废弃内容
