# 当前状态

**当前阶段：** 阶段 4 — M4: BaseAgent & 主 Agent

**当前任务：** 3. BaseAgent

**当前子任务：** ⬜ BaseAgent — `write_memory()` 便利方法

**当前阻塞：** 无

**下一步：** 在 BaseAgent 中实现 `write_memory()`，封装记忆模块的 `build_memories()` 调用，让 Agent 能便捷地将对话上下文固化为记忆

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
31. Chunker 通用化：移至 `src/utils/chunker.py`，新增 front-matter 解析；强制 front-matter（无 `---` KV 块返回空列表并留 TODO 桩）；caller metadata 覆盖 front-matter 同名字段；所有文件统一格式
32. MemoryBuilder 替代 Compressor：从对话构建记忆而非简单压缩，async/sync 由 Builder Facade 控制，Store 纯同步
33. 日志使用 Python 标准库 `logging`：`RotatingFileHandler`（10MB × 5）写入 `data/logs/app.log`，`StreamHandler(stderr)` 输出 ERROR+；懒加载初始化（`get_logger()` 首次调用自动配置）；`LOG_LEVEL`（默认 INFO）和 `LOG_DIR`（默认 `data/logs/`）通过环境变量配置
34. Message 为通用基础设施（`src/message.py`）：7 字段（id/timestamp/role/message/event_type/event_payload/thinking），统一覆盖用户输入、系统指令、工具调用、工具结果和 LLM 回复；role 保留用于消息来源控制，event_type 区分消息语义，thinking 未来由 SHOW_THINKING flag 控制展示
35. MemoryStore 格式化工具抽出到 `src/utils/formatters.py`：`timestamp_to_filename(time)` + `memory_to_markdown(agent, memory)` 作为公共函数，Store 不持有格式化逻辑
36. Memory 类别重构：`category` 字段（"fact" / "preference"），builder.md 输出 `{"facts": "<string>", "preferences": "<string>"}` 严格 JSON，废弃 entities/events 合并入 facts
37. MemoryBuilder：`response_format={"type": "json_object"}` 强制 JSON，LLM 输出按 `\n` 拆分 → `\n\n---\n\n` 拼接 → Chunker 切分独立索引
38. 记忆模块统一入口：`src/memory/__init__.py` 四大公开函数（`init`/`build_memories`/`search_memories`/`delete_memory`），类 RAG 单例懒加载；文件名加 `category` 防冲突；`---` 分隔符实现一文件多条独立检索
39. Chroma in-memory `delete(where=...)` 不可靠（社区已知 bug：#4275/#5367）：全量 `/ragreload` 改用 `delete_collection` 原子删除后重建，单文件重载保留 `remove` + `add`（接受间歇性）
40. Agent Loop 用 `list[Message]` 管理对话历史，调 LLM 时完整序列化不裁剪（保证 LLM 缓存命中率）
41. 工具结果用 `role: "user"` 注入，`event_type: "tool_call_result"` 区分语义，不引入 OpenAI 原生 tool_call_id
42. Agent Loop 终止条件：`finish` / `ask_user` / `max_rounds`（`AGENT_MAX_ROUNDS` 环境变量）
43. 工具用 `@tool` 装饰器注册，`input_schema` 扁平化（只写 description/default），type/required 自动推断
44. 工具 handler 返回 `Message`，`event_payload` → `**kwargs` 直接映射到函数入参
45. `Tool.agent` 字段控制可见性：None=通用，list=指定 Agent；全局加载 + 提示词过滤 + 调用门禁
46. 工具错误带上下文喂回 LLM 让其自修复（如附带 `arguments_schema`），原则：给够上下文让 LLM 有能力自修复
47. `ToolRegistry` 全局管理工具，`BaseAgent` 不扫描 `dir(self)`，直接从 Registry 按 agent 过滤拉取
48. `process(input: Message) -> Response`；Response 是 CLI 指令层，不进对话历史；三种 type：`finish` / `select` / `confirm`
49. 意图路由纯 LLM 驱动，不做独立 Router；`provide_choices` 工具动态列出能力 + 用户选择
50. CLI 交互用 `questionary`，`select` 绑定"返回给 LLM"，`confirm` 绑定"操作审批"
51. Agent 切换由 `App.switch_agent(name, pre_prompt)` 封装：切 handler + 喂 prompt + 立即跑一轮；子 Agent `return` 退回主 Agent；子 Agent 不允许切到其他子 Agent
52. M4 做一个真实子 Agent（面试问答），验证 tool 注册 + agent loop + dispatch + return 全链路
53. `AgentRegistry` 主 Agent 特权持有，App 通过它做 handler 切换
54. `ConfirmMode` 枚举（NEVER/ALWAYS/CONFIG）控制工具审批行为，不暴露给 LLM；全局 `TOOL_CONFIRM_ENABLED` 环境变量留后
55. Agent loop 中途吐 progress 给 CLI：`Response(type="progress")` + `Message.internal_continue()` 推进，App 层循环渲染不等待用户输入
56. `Message.event_type` 使用 `EventType(StrEnum)` 枚举，5 种值（user_input/tool_call/tool_call_result/finish/system_message），代码中禁用裸字符串
57. `Message` 新增 `tool`（工具名）和 `tool_call_id`（关联 tool_call 的 id）一级字段，`event_type=tool_call_result` 时填写
58. 工具 handler 返回纯数据（str/dict），由调用方包装为 `tool_call_result` Message（含 tool/tool_call_id/event_payload），不再由 handler 自行包装
59. System prompt 不走 Message 结构，以纯文本 `{"role": "system", "content": "..."}` 注入 OpenAI messages，`_history` 只存对话消息
60. 06_output / 07_input prompt 分工：06 定义 LLM 输出 schema（flat JSON，role=assistant，event_type∈{tool_call,finish}），07 定义输入 schema（role=user，event_type∈{user_input,tool_call_result,system_message}），字段互不越界
61. `Message.to_json()` / `Message.from_llm_reply()` 统一序列化/反序列化入口，消除多处重复的 `dataclasses.asdict()` + `json.dumps()` 调用
62. 移除 `04_tools.md` 中硬编码的预定义工具（`ask_user`/`finish`/`return`），所有工具由 `ToolRegistry` 通过 `{{ADDITION_TOOLS}}` 注入
63. `Message.event_type` 为唯一 required 字段，`message` 默认 `""`，构造最小消息只需 `Message(event_type=EventType.USER_INPUT)`
64. Agent loop 上移至 App 层：`BaseAgent.process()` 从内部 `for` 循环改为单步执行，循环由 `App.run()` 内层 while 驱动；`process()` 每次调用只做一步（LLM → 分发 → 返回），工具执行暂停时返回 PROGRESS/CONFIRM
65. 新增 `Request` 类型（对称 `Response`）：`RequestType(USER_INPUT/CONTINUE/CONFIRM_APPROVED)` 作为 App→Agent 输入协议；`Handler.process()` 签名从 `Message → Response` 改为 `Request → Response`
66. 用户拒绝工具审批 → App 直接退出内层循环，不调用 `process()`，等待用户下一次主动输入
67. 工具错误处理增强：未知工具时 system_message 附完整可用工具列表；工具执行失败时 error payload 附带 `arguments_schema` + `expected_output`，让 LLM 有足够上下文自修复调用参数
