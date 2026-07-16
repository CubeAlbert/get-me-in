# 当前状态

**当前阶段：** M5-Review: 工具与提示词审查优化

**当前任务：** Review 当前所有工具及 Agent 提示词，优化质量

**当前子任务：** Review resume 工具 `copy_template` 已完成；继续 Review workspace 工具（10 个）

**当前阻塞：** 无

**下一步：** 逐一审查 workspace_read → workspace_list → ... → workspace_open

**已暂缓：** schema-based 填充工具、记忆集成

**参考文档：** `docs/file-reader-design.md` — workspace 工具组完整设计；`data/resume/template/README.md` — 模板操作手册

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1-100: 见 decision.md
101-115: 见 decision.md
116. **PLACEHOLDER.txt → README.md** — 升级为模板操作手册（章节结构 + 占位符清单 + 填充约束），copy_template 始终跟随复制
117. **Agent temperature 分层设置** — MainAgent 0.1, JobSearchAgent/ResumeAgent 0.2, MemoryBuilder 0（确定性提取）
118. **删除 LLMHandler** — M4 已被 MainAgent 替代，无保留价值，连带清理 `src/cli/__init__.py` 导出
