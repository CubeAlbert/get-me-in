# 当前状态

**当前阶段：** R2: Agent Runtime 与事件协议

**当前任务：** 完成 LLM adapter 配置与 G2 验收

**当前子任务：** OpenAI sync adapter 的 provider-thinking 配置（🔄）——R2 的强类型 Runtime、ToolResult 暂停/恢复、取消与关闭生命周期已完成；仍需集中 provider-thinking 配置并进行可选真实 provider smoke

**当前阻塞：** 无；旧 CLI 的真实终端 smoke C01/C05 仍待人工验证。真实 provider smoke 会发起外部 API 调用，待核心自动化验收后按需执行

**下一步：** 为 OpenAI adapter 集中 model tier 与 provider-thinking 配置，补充 adapter contract 测试；完成后执行 G2 审查

**已暂缓：** InterviewAgent、LearningAgent、完整 Job Search、Sticky Plan 等新功能统一放到 R9；R0～R8 只做 v2 重构

**参考文档：** `docs/refactor-design.md`（活跃设计）／`docs/refactor-plan.md`（活跃计划）／`docs/refactor-task.md`（活跃任务）／`docs/decision.md`（决策记录）

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1-136: 见 decision.md
137. **`refactor` 分支采用独立 v2 受控重写** — 在 `src/get_me_in/` 建立 v2，显式装配依赖并使用强类型 Runtime 协议；不迁移旧 Session、Memory、Chroma、temp 等运行数据，只保留 `data/reference/`、`data/prompts/`、`data/resume/template/`；已授权核心自动化测试
138. **R1 骨架清单获确认后开始编码** — v2 采用 `src.get_me_in` 导入路径；首批实现 Settings、基础 ports、声明式 Agent/Prompt、CancellationToken、Application 与 composition root，并为纯逻辑建立自动化测试；R1 尚未完成 import guard 和 G1
139. **R1 临时无工具对话仅用于 G1 验证** — `Application.complete_text()` 必须显式注入 `LLMPort`，不保存 history、不支持工具或 handoff，并用 `TEMP-R1` 标注；R2 正式 AgentRuntime 落地时必须删除，不能作为正式 Runtime 演进
140. **R2 用 ToolResult 闭合暂停的工具回合** — Runtime 对已声明工具发出 `ToolStarted` 后暂停，只接受匹配 `call_id` 的 `ToolResult` 并产生 `ToolFinished` 后继续 LLM；R3 的 ToolCatalog 将替代 R2 过渡期的可用工具集合
