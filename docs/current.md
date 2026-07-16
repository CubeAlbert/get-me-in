# 当前状态

**当前阶段：** M5-Review: 工具与提示词审查优化

**当前任务：** Review 当前所有工具及 Agent 提示词，优化质量

**当前子任务：** workspace / resume 工具及 ResumeAgent 提示词 review 已完成；剩余 RAG 工具

**当前阻塞：** 无

**下一步：** Review RAG 工具（`query_memory` / `query_reference_data`）

**已暂缓：** schema-based 填充工具、记忆集成

**参考文档：** `docs/file-reader-design.md` — workspace 工具组完整设计；`data/resume/template/README.md` — 模板操作手册

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1-100: 见 decision.md
101-115: 见 decision.md
116. **PLACEHOLDER.txt → README.md** — 升级为模板操作手册，copy_template 始终跟随复制
117. **Agent temperature 分层设置** — MainAgent 0.1, ResumeAgent/JobSearchAgent 0.2, MemoryBuilder 0
118. **删除 LLMHandler** — M4 已被 MainAgent 替代
119. **plan_status 每轮注入** — PlanStatusInfo 替代一次性 PLAN 注入，LLM 始终可见计划全貌
120. **workspace_edit 读后编辑守卫** — read 后写 _read_files，edit 前校验+消费，每次 edit 后需重新 read
121. **workspace_delete 批量删除** — 入参从 str 改为 list[str]，部分失败不中断
