# 当前状态

**当前阶段：** M5-Review: 工具与提示词审查优化

**当前任务：** Review 当前所有工具及 Agent 提示词，优化质量

**当前子任务：** Review workspace 工具（10 个）— 审查 schema / prompt / 异常处理

**当前阻塞：** 无

**下一步：** 逐一审查 workspace_read → workspace_list → ... → workspace_open

**已暂缓：** schema-based 填充工具、记忆集成

**参考文档：** `docs/file-reader-design.md` — workspace 工具组完整设计

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1-100: 见 decision.md
101. **workspace_fs 拆分为三个独立工具**（write/delete/move）— 参数差异大，拆分后 schema 更清晰
102. **workspace_search 拆分为 grep + search_file** — 内容搜索与文件发现是不同操作
103. **workspace_read 结构化输出** — `lines: [[int, str]]`，行号保持原始行号
104. **workspace_edit 批量编辑 + 倒序处理 + old_content 校验**
105. **read_customer_file 绝对路径 + 统一输出格式** — txt/md/pdf/docx 统一 `lines` 结构
106. **ToolCallException 统一工具异常** — message + suggestion + 框架填充 arguments_schema
107. **Agent key 常量统一管理** — `MAIN_AGENT_KEY` / `RESUME_AGENT_KEY` 等
108. **workspace 工具限定 ResumeAgent** — `agent=[RESUME_AGENT_KEY]`
109. **workspace_list 单层不递归** — Agent 逐层探索工作区
110. **workspace_replace 全文字符串替换** — 简单替换不走 search→read→edit
111. **RAG 查询工具用 StrEnum 校验 filter** — `MemoryType` / `ReferenceCategory`
112. **workspace_edit 简化为纯 replace** — LLM 用 `\n` 自行控制插入/替换/删除，无需 action 字段
113. **copy_template 用户交互前置** — LLM 先确认语言+文件名前缀，再调用工具
114. **构建 resume 改为 workspace 工具直接编辑 LaTeX** — 放弃 schema-based 填充，LLM 直接操作模板
115. **`/dump` 命令导出对话历史** — `BaseAgent.dump_history()` + CLI `/dump`
