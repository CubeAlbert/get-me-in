# 当前状态

**当前阶段：** 阶段 3 — M3: 记忆模块 + RAG 收尾

**当前任务：** 任务 1 — 日志模块 (`src/logger.py`)

**当前子任务：** 实现 `get_logger()` + `_setup()` 内部初始化，`src/config.py` 追加 `LOG_LEVEL`/`LOG_DIR`

**当前阻塞：** 无

**下一步：** 创建 `src/logger.py`，封装 `logging` 标准库（RotatingFileHandler + stderr），然后继续 M3 任务 2（schemas.py）

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1. 架构采用 Hub-and-Spoke 模式，自研轻量 Agent 框架，不用 LangChain/CrewAI/AutoGen
2. 同步代码，不使用 asyncio
3. RAG 使用 Chroma（内存模式先行）+ sentence_transformers（bi-encoder 召回 + cross-encoder 重排）
4. 记忆按 Agent 分目录存储，Agent 固化记忆时带分隔符，由 Chunker 切分后入库
5. 所有 Agent 的 LLM 调用由 PromptLoader 强制拼接 general_agent_prompt（安全策略+工具+输出格式）
6. 工作流遵循 Plan → Execute → Result Validation → Replan
7. 编码时不写测试，除非用户显式要求
8. 使用 `uv` 管理依赖和运行（`uv add`/`uv sync`/`uv run`），PyPI 镜像使用上交 SJTUG
9. LLM 后端使用 OpenAI SDK，双 tier（pro / flash），base_url 和 api_key 通过环境变量注入，不设 fallback
10. Jupyter 交互式调试用 `uv run --with jupyter jupyter lab`，jupyter 不写入项目依赖
11. 环境变量由 `src/config.py` 集中管理，启动时校验，其他模块禁止直接使用 `os.environ`
12. LLM 参数分层管理：`LLMClient` 只管透传 `**kwargs`，不关心调用方；`BaseAgent` 提供 `_pro_params` / `_flash_params` 类属性设置默认值，子 Agent 按需覆盖；调用时 `**kwargs` 可覆盖默认值
13. CLI 通过 `Handler` 抽象协议与业务逻辑解耦：`App` 依赖注入 `Handler`，不直接调 LLM；M1 阶段用 `DemoHandler` 桩验证 I/O 管线，后续主 Agent 实现同一 `process()` 接口后无缝替换
14. Agent 无专属模板文件 —— 所有 Agent 共用 `general_agent/` 下 7 个模板，差异由 14 个 per-Agent 占位符填充值体现（清单见 `data/prompts/PLACEHOLDER.md`）
15. 编排不依赖独立提示词 —— 调度子 Agent 定义为工具（如 `dispatch_resume`），通过 `{{ADDITION_TOOLS}}` 注入主 Agent 的工具列表
16. JSON 输出解析留待 M4 — `06_output_format.md` 已定义结构化 JSON schema，`LLMHandler` 不做解析直接透传，M4 由 Orchestrator 解析 JSON → 分发工具 → agent loop
17. RAG 双 collection（`references` + `memories`），统一 `---` 分隔符，category 由子目录名自动标注，全库搜索 + 可选 filter，不需要 index.md 或 router
18. RAG 模型选型：bi-encoder = `BAAI/bge-base-zh-v1.5`，cross-encoder = `BAAI/bge-reranker-v2-m3`（性能不足降级 `bge-reranker-base`），均通过环境变量配置
19. RagLoader 后台加载（`threading.Thread`），`is_ready()` 标记就绪状态，未就绪时对话降级为纯 LLM；`load_file()` 支持增量热更新
20. Embedder/Reranker 分离 — Embedder 只持 bi-encoder（`embed()`），Reranker 独立加载 cross-encoder；`EMBED_BATCH_SIZE` 环境变量化
21. `HF_ENDPOINT` 默认 `https://hf-mirror.com`，国内用户开箱即用
22. `/ragreload` 命令，手动重载 RAG（`/ragreload` 全量，`/ragreload <关键词>` 匹配），已实现
23. ChromaStore 内部创建 Embedder（不注入），原文存 `documents` 字段，filter 透传，不加锁，L2 距离，不校验 collection 名，持久化通过 `CHROMA_PERSIST_DIR` 环境变量切换
24. 增量加载：`.last_update` 时间戳比对 mtime；用户手动删文件不管；Agent 程序化操作统一封装同步 Chroma
25. Reranker：分数存 `metadata["rerank_score"]`，`RERANK_BATCH_SIZE` + `RERANK_TOP_K` 环境变量控制，`__init__` 预热，异常直接抛出由调用方降级
26. Store.query() 接受文本内部向量化，移除 Retriever —— 消除双 Embedder 实例，检索流程简化为 Store.query() → Reranker.rerank()
27. RagLoader：Store/Reranker 注入（单例由 `rag/__init__.py` 懒加载），Chunker 内部创建；`LoaderState` 状态机（IDLE/LOADING/READY/ERROR）；同步+锁，异常写状态不抛出；内存全量/持久化增量
28. RAG 公共 API 极简化：仅暴露 `start()` / `search()` / `load()` / `is_ready()` 四个函数，Store 和 Reranker 完全隐藏在模块内部；3 个环境变量在 import 前静默模型加载进度条
29. MemoryStore 与 RAG 解耦：观察者模式，Store 只写文件+发事件，MemoryIndexer 监听→RAG 索引，MemoryRetriever 封装 RAG 检索
30. 一文件一条记忆：`data/memories/<agent>/<yyyyMMddHHmmss.fff>.md`，front-matter KV 格式持久化 metadata（id/agent/time）
31. Chunker 通用化：移至 `src/utils/chunker.py`，新增 front-matter 解析，所有文件统一格式
32. MemoryBuilder 替代 Compressor：从对话构建记忆而非简单压缩，async/sync 由 Builder Facade 控制，Store 纯同步
33. Chunker 强制 front-matter：所有输入文本必须以 `---` KV 块开头，无 front-matter 返回空列表并留 TODO 桩；caller metadata 覆盖 front-matter 同名字段
34. 日志使用 Python 标准库 `logging`：`RotatingFileHandler`（10MB × 5）写入 `data/logs/app.log`，`StreamHandler(stderr)` 输出 WARNING+；懒加载初始化（`get_logger()` 首次调用自动配置）；`LOG_LEVEL`（默认 INFO）和 `LOG_DIR`（默认 `data/logs/`）通过环境变量配置
