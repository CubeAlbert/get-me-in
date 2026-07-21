# 当前状态

**当前阶段：** R0: 基线冻结与决策门禁

**当前任务：** 确认 v2 重构边界并建立迁移基线

**当前子任务：** capability parity matrix（🔄）——逐项记录当前已实现能力的输入、输出、副作用和失败行为，作为 v2 验收基线

**当前阻塞：** 无

**下一步：** 当前会话不写项目代码；下次先完成 capability parity matrix、静态资产输入边界和 CLI smoke checklist，再提交 R1 的新文件、类与公开方法清单供用户确认

**已暂缓：** InterviewAgent、LearningAgent、完整 Job Search、Sticky Plan 等新功能统一放到 R9；R0～R8 只做 v2 重构

**参考文档：** `docs/refactor-design.md`（活跃设计）／`docs/refactor-plan.md`（活跃计划）／`docs/refactor-task.md`（活跃任务）／`docs/decision.md`（决策记录）

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1-136: 见 decision.md
137. **`refactor` 分支采用独立 v2 受控重写** — 在 `src/get_me_in/` 建立 v2，显式装配依赖并使用强类型 Runtime 协议；不迁移旧 Session、Memory、Chroma、temp 等运行数据，只保留 `data/reference/`、`data/prompts/`、`data/resume/template/`；已授权核心自动化测试
