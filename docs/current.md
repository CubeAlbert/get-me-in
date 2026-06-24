# 当前状态

**当前阶段：** 阶段 1 — M1: 项目骨架 & 基础设施

**当前任务：** 1. 项目配置 & 依赖

**当前子任务：** ⬜ 完善 `pyproject.toml`：添加 `sentence_transformers`、`chromadb`、`rich`、LLM SDK 等依赖

**当前阻塞：** 无

**下一步：** 确定 LLM 后端选型（Claude API / OpenAI），完善 `pyproject.toml` 添加所需依赖，创建虚拟环境并安装

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1. 架构采用 Hub-and-Spoke 模式，自研轻量 Agent 框架，不用 LangChain/CrewAI/AutoGen
2. 同步代码，不使用 asyncio
3. RAG 使用 Chroma（内存模式先行）+ sentence_transformers（bi-encoder 召回 + cross-encoder 重排）
4. 记忆按 Agent 分目录存储，Agent 固化记忆时带分隔符，由 Chunker 切分后入库
5. 所有 Agent 的 LLM 调用由 PromptLoader 强制拼接 general_agent_prompt（安全策略+工具+输出格式）
6. 工作流遵循 Plan → Execute → Result Validation → Replan
7. 编码时不写测试，除非用户显式要求
