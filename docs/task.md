# 任务列表

工作流遵循 **Plan → Execute → Result Validation → Replan** 循环。工作按三个层级组织：**阶段 → 任务 → 子任务**。阶段是顺序执行的 —— 完成一个阶段后再开始下一个。LLM 在创建时规划顺序，更新时必须保持该顺序。

| 符号 | 状态 | 含义 |
|------|------|------|
| ⬜ | 待开始 | 尚未开始 |
| 🔄 | 进行中 | 正在执行 |
| ✅ | 已完成 | 已完成 |
| ⏸️ | 阻塞 | 被阻塞 —— 在标记后注明原因 |
| ⛔ | 终止 | 任务被终止，由新任务替代 |
| 📌 | 暂缓 | 已记录，留待后续阶段处理 |

状态标记设置在子任务上。任务和阶段的状态由子任务推导：若任一子任务为 🔄，其所属任务即为进行中；若所有子任务均为 ✅，则任务为已完成。

**终止规则：**
- 当某个任务不再适用或方向需要调整时，将当前未完成的子任务标记为 ⛔
- 在终止任务下方以 `>> 替代：[新任务名称]` 的格式追加替代任务
- 替代任务沿用子任务列表格式，从 ⬜ 开始
- 原终止任务保留在文档中，不做删除 —— 作为决策轨迹留存

---

## 阶段 1 —— M1: 项目骨架 & 基础设施

### 1. 项目配置 & 依赖

- ✅ 完善 `pyproject.toml`：添加 `sentence_transformers`、`chromadb`、`rich`、`openai`、`python-dotenv` 等依赖
- ✅ `uv sync` 安装所有依赖并验证

### 2. 配置模块 (`src/config.py`)

- ✅ 实现 `config.py`：启动时调用 `load_dotenv()`、校验 4 个必填环境变量（缺失则打印清单并 `sys.exit(1)`）、将变量挂到模块属性上
- ⬜ 其他模块（LLM 等）统一 `from src.config import config` 获取配置，不再直接调用 `os.environ`

### 3. LLM 适配层 (`src/llm/`)

- ✅ 实现 `client.py`：`LLMClient` 双 tier 调用（`chat_pro()` / `chat_flash()`），从环境变量读取 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`LLM_PRO_MODEL`、`LLM_FLASH_MODEL`
- ✅ 创建 `.env.example` 模板文件（含 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`LLM_PRO_MODEL`、`LLM_FLASH_MODEL` 四项）

### 4. CLI 交互层 (`src/cli/`)

- ✅ 实现 `handler.py`：抽象基类 `Handler`（`process(user_input: str) -> str`）+ `DemoHandler`（输入 1→纯文本、2→markdown、3→选项列表），仅用于测试 I/O 管线
- ✅ 实现 `app.py`：`App` 类，依赖注入 `Handler`，对话循环 `while True: input() → handler.process() → rich`，不直接调 LLM
- ✅ 实现 `$EDITOR` 临时文件长文本输入（用户输入特殊命令时弹出编辑器）
- ✅ `rich` 渲染 Markdown 输出（代码块、表格、列表等）

### 5. 提示词模块 (`src/prompts/`)

- ✅ 实现 `loader.py`：`get(**kwargs)` 读取 `general_agent/` 下所有 `.md`（按文件名排序拼接）并替换占位符；`get_raw(name, **kwargs)` 加载 `data/prompts/<name>.md` 跳过拼接
- ✅ 创建 `data/prompts/general_agent/` 下 7 个模板文件（`01_role.md` ~ `07_reserved.md`）
- ✅ 创建 `data/prompts/PLACEHOLDER.md`（14 个 per-Agent 占位符清单）
- ⛔ 创建 `data/prompts/memory_compressor.md` —— memory_compressor.md 已删除，替代为 `data/prompts/memory/builder.md`
>> 替代：M3-6 实现 MemoryBuilder 提示词模板
- 编排不再使用独立提示词 —— 调度子 Agent 定义为工具，通过 `{{ADDITION_TOOLS}}` 注入

### 6. 入口集成

- ✅ 更新 `main.py`：初始化 LLM Client → PromptLoader → CLI App，串联完整对话流程
- ✅ 端到端验证：启动程序 → 输入一句话 → LLM 返回 → rich 渲染输出
- 📌 `06_output_format.md` 已定义结构化 JSON 输出，`LLMHandler` 当前透传原始回复不做解析 —— JSON 解析留待 M4 主 Agent 实现

## 阶段 2 —— M2: RAG 模块

### 1. 参考数据目录

- ✅ 创建 `data/reference/` 及 6 个子目录（`interview_questions/`、`company_info/`、`knowledge_base/`、`resume_examples/`、`recommended_materials/`、`job_descriptions/`）
- ✅ 每种子目录下创建示例 `.md` 文件，按 `---` 分隔条目，供开发调试使用

### 2. Embedder (`src/rag/embedder.py`)

- ✅ 加载 bi-encoder 模型（模型名由环境变量 `BI_ENCODER_MODEL` 配置）
- ✅ 实现 `embed(texts: list[str], batch_size: int) -> list[list[float]]`，将文本列表转为归一化向量列表，`batch_size` 默认值由环境变量 `EMBED_BATCH_SIZE` 配置

### 3. Chunker (`src/rag/chunker.py`)

- ✅ 定义 `Chunk` 数据类（`id: str`、`content: str`、`metadata: dict`）
- ✅ 实现 `chunk(text: str, separator: str = "\n---\n", metadata: dict = {}) -> list[Chunk]`，按 `---` 切分文本，每个片段生成 uuid4 并附加 metadata；自动过滤仅含空白字符的片段

### 4. ChromaStore (`src/rag/store.py`)

- ✅ 封装 Chroma 客户端：内部持有 `Embedder`；通过 `CHROMA_PERSIST_DIR` 环境变量切换内存/持久化模式；不预建 collection，不校验 collection 名
- ✅ 实现 `add(chunks: list[Chunk], collection: str) -> None`：内部调 `Embedder.embed()` 向量化，将原始文本存入 Chroma `documents` 字段，metadata 透传
- ✅ 实现 `query(query_text: str, collection: str, filter: dict | None = None, top_k: int | None = None) -> list[Chunk]`：接受文本内部向量化（top_k 默认由 `RETRIEVAL_TOP_K` 配置），透传 where filter，结果还原为 Chunk 对象（含 content）
- ✅ 实现 `remove(source_file: str, collection: str) -> None`：按 `source_file` metadata 过滤删除（供增量更新使用）

### 5. Retriever (`src/rag/retriever.py`)

- ⛔ 已废弃 — Store.query() 改为接受文本、内部向量化后，Retriever 职责退化为一层透传，无存在必要
- >> 替代：直接使用 ChromaStore.query() 做检索

### 6. Reranker (`src/rag/reranker.py`)

- ✅ 独立加载 cross-encoder 模型（模型名由 `CROSS_ENCODER_MODEL` 配置），`__init__` 时用假数据跑一次 `predict()` 预热
- ✅ 实现 `rerank(query: str, candidates: list[Chunk], top_k: int | None = None) -> list[Chunk]`：对 (query, candidate.content) 逐对评分（batch_size 由 `RERANK_BATCH_SIZE` 配置），分数写入 `Chunk.metadata["rerank_score"]`，按分数降序返回 top_k 条（默认值由 `RERANK_TOP_K` 配置）；异常直接抛出

### 7. RagLoader (`src/rag/loader.py`)

- ✅ 构造函数注入 `ChromaStore` + `Reranker`，内部创建 `Chunker`；定义 `LoaderState` 枚举（IDLE / LOADING / READY / ERROR）
- ✅ 实现 `auto_load()`：同步 + `threading.Lock`（LOADING 时拒绝）；内存模式全量 / 持久化模式 `.last_update` 增量；异常写 `state=ERROR` + `error_msg` 不抛出；完成后写时间戳 + `state=READY`
- ✅ 实现 `load_file(path: Path) -> None`：同步 + 同锁，`remove(source_file)` → chunk → add；异常写 state 不抛出
- ✅ 暴露 `state: LoaderState` 和 `error: str | None` 属性
- ✅ `src/rag/__init__.py` 模块入口：双检锁懒加载单例 + `start()` 后台初始化 + 环境变量静默进度条；公共 API：`start()` / `search()` / `load()` / `is_ready()`
- ✅ `/ragreload` 命令：CLI 命令 `/ragreload [关键词]`，调 `load()` 完成重载；`_reload_full()` 返回文件计数；`_reload_matched()` 逐文件 try/except 防崩

### 8. 端到端验证

- ✅ 示例参考数据就绪（`cs_fundamentals.md` 含 19 条条目）
- ✅ `search("快速排序")` → 经 `store.query()` 召回 → `Reranker.rerank()` 精排 → 返回结果正确（快速排序 0.973，归并排序 0.311，分数区分度良好）

## 阶段 3 —— M3: 记忆模块 + RAG 收尾

### 0. M2 收尾 — Chunker 抽出 + RAG 接口扩充 + 文件改造

- ✅ Chunker/Chunk 从 `src/rag/chunker.py` 移至 `src/utils/chunker.py`，更新 `src/rag/` 下所有 import
- ✅ Chunker.chunk() 新增 front-matter 解析：正则匹配 `^---` KV 块 → 注入所有 Chunk；无 front-matter 返回 []，留 TODO 桩
- ✅ RAG `search()` 加 `filter: dict | None` 参数，透传 Chroma `where`
- ✅ RAG 新增 `delete(where: dict, collection="memories") -> int`，空 `{}` 抛 `ValueError`
- ✅ 现有 `data/reference/` 下所有 `.md` 文件加 front-matter（`category: <子目录名>`）
- ✅ `RagLoader` 改为从 `src.utils.chunker` 导入 Chunker

### 1. 日志模块 (`src/logger.py`)

- ✅ `_setup()` 内部初始化：读 `config.LOG_LEVEL` / `config.LOG_DIR` → 创建 `RotatingFileHandler`（10MB × 5）+ `StreamHandler(stderr, ERROR+)` → 绑定 root logger
- ✅ `get_logger(name: str) -> logging.Logger`：首次调用触发 `_setup()`，返回 `logging.getLogger(name)`
- ✅ `src/config.py` 追加 `LOG_LEVEL`（默认 `INFO`）、`LOG_DIR`（默认 `data/logs/`）
- ✅ 创建 `data/logs/` 目录（`.gitkeep` 占位，确保目录被 Git 追踪）

### 2. 记忆数据结构 (`src/memory/schemas.py`)

- ✅ `Memory` 数据类：`id: str` (uuid) + `agent: str` + `time: datetime` + `content: str` + `category: str` ("fact"/"preference") — 实现在 `src/memory/schemas.py`
- ✅ `Message` 数据类：7 字段（id/timestamp/role/message/event_type/event_payload/thinking）— 抽出为通用基础设施 `src/message.py`
- ✅ 事件数据类：`MemoryWrittenEvent(agent, memory, file_path)`、`MemoryDeletedEvent(agent, file_path)` — 实现在 `src/memory/schemas.py`
- ✅ `chunk_to_memory(chunk: Chunk) -> Memory` 转换函数 — 实现在 `src/memory/schemas.py`

### 3. MemoryStore 文件读写 + 事件 (`src/memory/store.py`) + 格式化工具 (`src/utils/formatters.py`)

- ✅ `write_memory(agent, memory) -> str | None`：取 `memory.time` 生成时间戳文件名 → 格式化 front-matter + 正文 → 创建目录 → 写文件 → 发射 `MemoryWritten`
- ✅ `delete_memory(agent, file_path) -> bool`：删文件 → 发射 `MemoryDeleted`
- ✅ `on_write(callback)` / `on_delete(callback)` 事件注册 + `_emit_write` / `_emit_delete` 发射
- ✅ 失败仅记日志，不抛异常
- ✅ 格式化工具 `src/utils/formatters.py`（`timestamp_to_filename` + `memory_to_markdown`）从 Store 抽出

### 4. MemoryIndexer (`src/memory/indexer.py`)

- ✅ `__init__(store)`：注册 `on_write` / `on_delete` 回调
- ✅ `_on_write(event)` → `rag.load_file(file_path)` 增量索引
- ✅ `_on_delete(event)` → `rag.delete(where={"source_file": file_path})` 移除索引
- ✅ RAG facade 新增 `load_file()` 公开函数

### 5. MemoryRetriever (`src/memory/retriever.py`)

- ✅ `search(query, agent=None, top_k=5) -> list[Memory]`：内部调 `rag.search(filter={"agent": agent})` → `chunk_to_memory()`
- ✅ RAG 未就绪时 `is_ready()` 前置检查，抛出 `RuntimeError`
- ✅ 单 Agent 检索 + 跨 Agent 全量检索 验证通过

### 6. 目录 + 文件准备

- ⛔ 创建 `data/memories/` 及 5 个 Agent 子目录 — `write_memory()` 自动 `mkdir(parents=True)`，`RagLoader` 目录不存在直接返回 0，无需预建

### 7. MemoryBuilder + 提示词 (`src/memory/builder.py`)

- ✅ 完善 `data/prompts/memory/builder.md` 系统提示词（facts/preferences 两分类，换行分隔，严格 JSON 输出）
- ✅ `MemoryBuilder.__init__(llm: LLMClient)`：加载 `builder.md` 提示词
- ✅ `build(conversation, agent) -> list[Memory]`：对话 → JSON 序列化 → flash LLM (`response_format=json_object`) → `json.loads()` → `\n` 拆分 → `\n\n---\n\n` 拼接 → 注入 `id`/`time`/`agent`/`category` → Memory 列表
- ✅ 添加 `time.time()` 耗时 debug 日志
- ✅ `timestamp_to_filename()` 加 `category` 参数避免同时间戳冲突

### 8. Facade (`src/memory/__init__.py`)

- ✅ `init()`：懒加载单例 Store + Indexer + Retriever（类 RAG `_ensure_init` 模式）
- ✅ `build_memories(conversation, agent, llm, sync_mode)`：sync 模式调 builder → store.write_memory() 返回列表；async 开 daemon 线程返回 None
- ✅ `search_memories(query, agent, top_k)`：包装 MemoryRetriever.search()
- ✅ `delete_memory(agent, file_path)`：包装 Store.delete_memory()

### 9. 端到端验证

- ✅ sync 模式：对话 → 构建 → 写入 → 检索 全链路验证
- ✅ async 模式：对话 → 构建（后台）→ 等待 → 检索验证
- ✅ 删除：写入 → 检索确认存在 → 删除文件 → Chroma 行数 -1
- ✅ `/ragreload` 全量重载后检索验证（metadata 持久化确认）
- ✅ Chroma in-memory `delete(where=)` 漏删已修复：全量 `/ragreload` 用 `delete_collection` 原子删除后重建；单文件重载保留 `remove` + `add`（接受间歇性不匹配，见决策 39）

## 阶段 4 —— M4: BaseAgent & 主 Agent

### 1. CLI + Response 升级 (`src/cli/` + `src/response.py`)

- ✅ `Response` dataclass：`type`（`finish` / `select` / `confirm`）+ `message` + `choices` + `thinking`
- ✅ `Handler` 协议升级：`process(Message) -> Response` + `_parse_llm_reply()` 静态方法
- ✅ `App` 升级：`Message` 包装输入 + `Response` 解包渲染 + `thinking` 展示
- ⛔ 删除 `LLMHandler` — LLMHandler 改为临时桩适配新协议，待 MainAgent 就绪后替换
- ✅ `uv add questionary`
- ✅ `config.py` 环境变量支持 bool 类型（`_VAR_SPECS` 第 4 列 `is_bool`，循环内自动转换）
- ✅ CLI 等待动效：LLM 请求期间展示 `.`/`..`/`...` + 计时（`\r` 单行覆盖）

### 2. Tool 系统 (`src/tools/registry.py`)

- ✅ `Tool` dataclass：name / purpose / use_when / do_not_use_when / arguments_schema / expected_output / handler / agent + `to_xml()`
- ✅ `@tool` 装饰器：`input_schema` 扁平化 → `inspect.signature` 自动补齐 type/required → 构建 Tool → 注册至 `ToolRegistry`
- ✅ `ToolRegistry`：全局注册表，`get_for(agent_name)` 按 agent 过滤

### 3. BaseAgent (`src/agents/base.py`)

- ✅ Agent loop：解析 LLM JSON（扁平 schema）→ 调工具 → 结果包装为 `tool_call_result` Message 喂回 LLM → 循环
- ✅ 对话历史管理：`list[Message]` → `Message.to_json()` 序列化，system prompt 独立存储不混入 history
- ✅ 终止条件：`event_type="finish"` / `max_rounds`（`AGENT_MAX_ROUNDS` 环境变量，默认 10）
- ✅ 工具调度：7b 未知工具（附工具列表）/ 7c 审批门禁（CONFIRM）/ 7d 自动执行（PROGRESS）；流程由 App 层内循环驱动
- ✅ `process(Request) -> Response` 接口：单步执行 + `_pending_tool` 断点恢复，`_round_counter` 安全阀
- ✅ `write_memory()` 便利方法
- ✅ LLM JSON 解析：`Message.from_llm_reply()` 静态方法统一反序列化，解析失败注入 `system_message` 让 LLM 自修复
- ✅ 工具错误处理：执行失败时附带 `arguments_schema` + `expected_output` 让 LLM 自修复调用参数

### 4. 主 Agent (`src/agents/main_agent.py`)

- ✅ `MainAgent(BaseAgent)`：14 个占位符值实现，继承 BaseAgent 全能力，已替换 LLMHandler 作为 main.py 入口
- ✅ 审批 gate：`BaseAgent._should_confirm()` + `ConfirmChoice` 枚举 + `questionary.select` 渲染
- ✅ 模板文件重排序 — `05_communtion_style.md` → `06`，`06_output_format.md` → `07`，`07_input_format.md` → `08`，`08_reserved.md` → `09`
- ✅ 新增 `data/prompts/general_agent/05_sub_agents.md` — XML 包裹 `<SubAgents>{{SUB_AGENTS_LIST}}</SubAgents>`
- ✅ `data/prompts/PLACEHOLDER.md` 新增 `{{SUB_AGENTS_LIST}}` 条目
- ✅ `docs/design.md` 目录树 + 模板表格同步更新
- ⬜ `AgentRegistry`（`src/agents/registry.py`）— 全局单例（`get_agent_registry()`），SubAgentDescriptor + register/get/list/list_agents_prompt
- ⬜ `BaseAgent` 新增 `_get_sub_agents_list()` 方法（默认 `""`），placeholders 加 `SUB_AGENTS_LIST`
- ⬜ `MainAgent._get_sub_agents_list()` 覆盖 — 调用 `get_agent_registry().list_agents_prompt()`
- ⬜ `Response` 新增 `switch_agent` / `switch_context` 字段 — FINISH + switch 表示切换
- ⬜ `switch_to_subagent` tool — 仅 MainAgent 可见，handler 返回 `_SwitchTarget` 标记
- ⬜ `switch_to_mainagent` tool — 所有子 Agent 自动注入，handler 返回 `_SwitchTarget` 标记
- ⬜ `BaseAgent._execute_tool()` 检测 switch 标记 — 不包装 tool_call_result，设 `_pending_switch`
- ⬜ `BaseAgent.process()` 检测 `_pending_switch` — 返回 `Response(FINISH, switch_agent=..., switch_context=...)`
- ⬜ `App.switch_agent(name, pre_prompt)` — 切 handler + 注入上下文 + 启动新 agent loop
- ⬜ App 内层循环检测 `FINISH + switch_agent` — 调 `switch_agent()` 后 `continue`，不退出循环
- ⬜ `/exit_sub` CLI 命令 — App 层拦截，主 Agent 前台时报错，子 Agent 时等价 `switch_to_mainagent("用户主动退出")`
- ⬜ `provide_choices` → `Response(type="select")`

### 5. 入口集成 (`main.py` + `src/config.py`)

- ✅ 组装 `MainAgent` 注入 `App`（`MainAgent(llm, prompts)` 替换 `LLMHandler`）
- ✅ `AGENT_MAX_ROUNDS` 环境变量
- ✅ 工具注册导入：`system_tool`（`get_current_datetime` + `get_working_dir`）+ `web_tool`（`web_search`）
- ✅ `WORKING_DIR` 环境变量（默认 `data/temp/`）

### 6. 面试问答 Agent (`src/agents/interview/`)

- ⬜ `InterviewAgent(BaseAgent)`：问 → 答 → 评价 → 下一题 loop
- ⬜ RAG search 工具：`@tool search_questions(query)` → 检索 `data/reference/interview_questions/`
- ⬜ `return` 退回主 Agent（通过 `App.switch_agent("main", result_prompt)`）

### 7. 端到端验证

- ⬜ 主 Agent dispatch → 面试 Agent 接管 → 问答交互 → `return` 退回主 Agent 全链路
