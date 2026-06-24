# 当前状态

**当前阶段：** 阶段 1 — M1: 项目骨架 & 基础设施

**当前任务：** 3. LLM 适配层 (`src/llm/`)

**当前子任务：** ⬜ 实现 `client.py`：`LLMClient` 双 tier 调用（`chat_pro()` / `chat_flash()`），通过 `config` 模块读取环境变量

**当前阻塞：** 无

**下一步：** 实现 `src/llm/client.py`，从 `config` 取值实例化 `openai.OpenAI`，暴露 `chat_pro()` / `chat_flash()`

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
