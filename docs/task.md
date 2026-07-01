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

### 1. 记忆数据结构 (`src/memory/schemas.py`)

- ⬜ `Memory` 数据类：`id: str` (uuid) + `agent: str` + `time: datetime` + `content: str`
- ⬜ `Message` 数据类：`role: str` + `content: str` + `timestamp: datetime`
- ⬜ 事件数据类：`MemoryWrittenEvent(agent, memory, file_path)`、`MemoryDeletedEvent(agent, file_path)`
- ⬜ `chunk_to_memory(chunk: Chunk) -> Memory` 转换函数

### 2. MemoryStore 文件读写 + 事件 (`src/memory/store.py`)

- ⬜ `write_memory(agent, memory) -> None`：取 `memory.time` 生成时间戳文件名 → 格式化 front-matter + 正文 → 创建目录 → 写文件 → 发射 `MemoryWritten`
- ⬜ `delete_memory(agent, file_path) -> None`：删文件 → 发射 `MemoryDeleted`
- ⬜ `on_write(callback)` / `on_delete(callback)` 事件注册 + `_emit(event)` 发射
- ⬜ 失败仅记日志，不抛异常

### 3. MemoryIndexer (`src/memory/indexer.py`)

- ⬜ `__init__(store)`：注册 `on_write` / `on_delete` 回调
- ⬜ `_on_write(event)` → `rag.load(file_path)`
- ⬜ `_on_delete(event)` → `rag.delete(where={"source_file": file_path})`

### 4. MemoryRetriever (`src/memory/retriever.py`)

- ⬜ `search(query, agent=None, top_k=5) -> list[Memory]`：内部调 `rag.search(filter={"agent": agent})` → `chunk_to_memory()`
- ⬜ RAG 未就绪时抛出 `RuntimeError`

### 5. 目录 + 文件准备

- ⬜ 创建 `data/memories/` 及 5 个 Agent 子目录（`main/`、`resume/`、`learning/`、`interview/`、`job_search/`）

### 6. MemoryBuilder + 提示词 (`src/memory/builder.py`)

- ⬜ 完善 `data/prompts/memory/builder.md` 系统提示词（输入格式 + 输出格式 + 构建规则）
- ⬜ `MemoryBuilder.__init__(llm: LLMClient)`：加载 `builder.md` 提示词
- ⬜ `build(conversation: list[Message], agent: str) -> list[Memory]`：对话 → Markdown → LLM → `---` 分隔输出 → Chunker 切分 → 注入 `id`/`time`/`agent` → 返回 Memory 列表

### 7. Facade (`src/memory/__init__.py`)

- ⬜ `build_memories(conversation, agent, llm, store, sync_mode=False) -> list[Memory] | None`：sync 模式调 `builder.build()` → `store.write_memory()` 返回列表；async 模式开 daemon 线程执行后返回 `None`

### 8. 端到端验证

- ⬜ sync 模式：对话 → 构建 → 写入 → 检索 全链路验证
- ⬜ async 模式：对话 → 构建（后台）→ 等待 → 检索验证
- ⬜ 删除：写入 → 检索确认存在 → 删除文件 → 检索确认不存在
- ⬜ `/ragreload` 全量重载后检索验证（metadata 持久化确认）
