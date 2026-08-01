# 当前状态

**当前阶段：** R8 已完成并通过最终用户审查；旧 RAG 环境变量兼容别名清理已完成，不进入 R9；R9 仍未授权

**当前任务：** 移除 `BI_ENCODER_MODEL`、`CROSS_ENCODER_MODEL`、`EMBED_BATCH_SIZE` 兼容别名已完成

**当前子任务：** 无；`.env.example`、Settings 解析、回归测试与当前事实文档已同步收口。

**当前阻塞：** 无；Settings 15/15、Bootstrap 25/25、完整 unittest 306/306、compileall、diff-check 与静态扫描均通过。R9 独立授权门禁仍保持关闭。

**会话交接说明：** 决策 273 记录旧 RAG 配置别名移除，代码／测试 checkpoint 为 `df01327`：当前只读取 `EMBEDDING_MODEL`、`RERANKER_MODEL`、`EMBEDDING_BATCH_SIZE`；旧名称按未知环境变量忽略，既有默认模型与 batch size 不变。Chroma memory／persistent 订正保持完成态，旧运行数据继续隔离，不得进入 R9。

**下一步：** 等待用户审查本次配置清理；审查完成后仍停在 R9 独立授权门禁前。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

273. **移除旧 RAG 环境变量兼容别名** — 代码／测试 `df01327` 已 checkpoint；`.env.example` 与 Settings 不再支持 `BI_ENCODER_MODEL`、`CROSS_ENCODER_MODEL`、`EMBED_BATCH_SIZE`，正式变量和既有默认值保持不变，完整 unittest 306/306 通过，R9 仍未授权。
272. **完成 Chroma memory／persistent 模式订正** — 计划 `e23aa4a`、代码／测试 `a5df705` 已 checkpoint；定向 72/72、完整 305/305、compileall、diff-check、真实双模式 smoke 与数据边界门禁通过，R9 仍未授权。
271. **确认并授权 Chroma memory／persistent 模式订正** — 默认保持 persistent；memory 使用 `EphemeralClient` 与 process-local manifest 成对装配并每次启动全量重建；旧 Chroma 路径继续隔离，按专项计划执行，不进入 R9。
270. **完成 tool call message 修正的真实 provider／TTY smoke 与最终收口** — `SHOW_THINKING=false`／`true` 两组工具调用均显示 message；关闭时无摘要，开启时 finish thinking 以纯文本 Panel 位于最终 Markdown message 上方；本修正全部完成，R9 仍未授权。
269. **完成 tool call message 修正的工程实现与自动化门禁** — `b190a06`、`0694c2b`、`5a43fda` 已提交；定向 65/65、84/84，完整 unittest 296/296、compileall、diff-check、InputFormat blob 与 production-component smoke 通过；等待真实 provider／TTY smoke，R9 仍未授权。
268. **确认 tool call message 非空契约与 CLI Markdown 展示修正** — 所有模型输出 message 由 parser 强制非空；finish thinking 仅在 Prompt 中必填且为纯文本；`ToolStarted` 携带 message/thinking，CLI 按 thinking Panel → Markdown message → 工具状态展示；范围与分片 checkpoint 已确认，R9 仍未授权。
267. **修复 workspace_edit 多行修改后的 read-before-edit 行号漂移回归** — 成功 edit 消费当前 read 授权；下一次 edit 必须重新 workspace_read，返回 revision 不再直接授权下一次编辑；定向 54/54、完整 unittest 295/295、compileall 和 diff-check 通过。R9 仍未授权。
266. **确认 Windows/Linux Resume XeLaTeX 真实 smoke 已完成** — 用户确认已在 Windows 和 Linux 分别完成中文与英文模板的真实 XeLaTeX PDF 编译验证；此前本机 MiKTeX 诊断不代表项目验证状态，现无阻塞。R9 仍未授权。
265. **统一 Resume 跨平台编译引擎为 XeLaTeX** — 中文模板固定 `fontset=fandol`，英文模板移除中文环境包；适配器使用 `xelatex`，保留 shell 限制、cwd、超时、取消、stdout/stderr 捕获和日志边界。
264. **完成 R9 前质量加固 Q7 与文档状态收口** — Q1～Q6 coding、完整验证、Q7 用户 smoke 和最终文档状态均完成；R9 仍需独立授权。
