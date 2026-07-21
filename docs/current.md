# 当前状态

**当前阶段：** R1: v2 骨架与 Composition Root

**当前任务：** 建立无全局可变状态的最小 v2 应用骨架

**当前子任务：** v2 import 规则与开发期依赖检查（🔄）——落实分层依赖并自动阻止 v2 反向导入旧 `BaseAgent`、`App`、`UIBridge` 或全局 Registry

**当前阻塞：** 无；旧 CLI 的真实终端 smoke C01/C05 仍待人工验证，但不阻塞 R1

**下一步：** 完成 v2 import 依赖检查与最小无工具 LLM 对话链路，验证两个 Application 实例的完整隔离并通过 G1

**已暂缓：** InterviewAgent、LearningAgent、完整 Job Search、Sticky Plan 等新功能统一放到 R9；R0～R8 只做 v2 重构

**参考文档：** `docs/refactor-design.md`（活跃设计）／`docs/refactor-plan.md`（活跃计划）／`docs/refactor-task.md`（活跃任务）／`docs/decision.md`（决策记录）

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1-136: 见 decision.md
137. **`refactor` 分支采用独立 v2 受控重写** — 在 `src/get_me_in/` 建立 v2，显式装配依赖并使用强类型 Runtime 协议；不迁移旧 Session、Memory、Chroma、temp 等运行数据，只保留 `data/reference/`、`data/prompts/`、`data/resume/template/`；已授权核心自动化测试
138. **R1 骨架清单获确认后开始编码** — v2 采用 `src.get_me_in` 导入路径；首批实现 Settings、基础 ports、声明式 Agent/Prompt、CancellationToken、Application 与 composition root，并为纯逻辑建立自动化测试；R1 尚未完成 import guard 和 G1
