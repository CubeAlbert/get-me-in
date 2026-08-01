# 当前状态

**当前阶段：** R8 已完成并通过最终用户审查；tool call message 非空契约与 CLI 展示修正及真实 provider smoke 已完成，不进入 R9；R9 仍未授权

**当前任务：** tool call message 非空契约与 CLI Markdown／thinking 展示修正已全部完成

**当前子任务：** 无；Prompt、parser、ToolStarted、Renderer、自动化、production-component smoke 与两组真实 provider／TTY smoke 均已完成。

**当前阻塞：** 无；定向测试 65/65、84/84，完整 unittest 296/296、compileall、diff-check、production-component smoke 与真实 provider smoke 均通过。R9 独立授权门禁仍保持关闭。

**会话交接说明：** 决策 270 记录两组真实 provider／TTY smoke 完成：tool-call message 在 `SHOW_THINKING=false`／`true` 下均显示；关闭时无思考摘要，开启时 provider 未返回可选 tool-call thinking，但 finish thinking 以纯文本 Panel 位于最终 Markdown message 上方，符合当前契约。设计、代码与工程状态 checkpoint 分别为 `b190a06`、`0694c2b`、`5a43fda`、`40229f5`。R8-P～R8-G/G8 完成态不变；不得读取、迁移、改写或删除旧运行数据，不得进入 R9。

**下一步：** 等待用户明确授权 R9；在此之前不得检查、设计或实施 R9。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

270. **完成 tool call message 修正的真实 provider／TTY smoke 与最终收口** — `SHOW_THINKING=false`／`true` 两组工具调用均显示 message；关闭时无摘要，开启时 finish thinking 以纯文本 Panel 位于最终 Markdown message 上方；本修正全部完成，R9 仍未授权。
269. **完成 tool call message 修正的工程实现与自动化门禁** — `b190a06`、`0694c2b`、`5a43fda` 已提交；定向 65/65、84/84，完整 unittest 296/296、compileall、diff-check、InputFormat blob 与 production-component smoke 通过；等待真实 provider／TTY smoke，R9 仍未授权。
268. **确认 tool call message 非空契约与 CLI Markdown 展示修正** — 所有模型输出 message 由 parser 强制非空；finish thinking 仅在 Prompt 中必填且为纯文本；`ToolStarted` 携带 message/thinking，CLI 按 thinking Panel → Markdown message → 工具状态展示；范围与分片 checkpoint 已确认，R9 仍未授权。
267. **修复 workspace_edit 多行修改后的 read-before-edit 行号漂移回归** — 成功 edit 消费当前 read 授权；下一次 edit 必须重新 workspace_read，返回 revision 不再直接授权下一次编辑；定向 54/54、完整 unittest 295/295、compileall 和 diff-check 通过。R9 仍未授权。
266. **确认 Windows/Linux Resume XeLaTeX 真实 smoke 已完成** — 用户确认已在 Windows 和 Linux 分别完成中文与英文模板的真实 XeLaTeX PDF 编译验证；此前本机 MiKTeX 诊断不代表项目验证状态，现无阻塞。R9 仍未授权。
265. **统一 Resume 跨平台编译引擎为 XeLaTeX** — 中文模板固定 `fontset=fandol`，英文模板移除中文环境包；适配器使用 `xelatex`，保留 shell 限制、cwd、超时、取消、stdout/stderr 捕获和日志边界。
264. **完成 R9 前质量加固 Q7 与文档状态收口** — Q1～Q6 coding、完整验证、Q7 用户 smoke 和最终文档状态均完成；R9 仍需独立授权。
263. **记录 Q7 用户 smoke 1～6 全部完成** — 用户确认 Main/Resume handoff、R8-F-C、query_memory、Q7 业务边界及 Ubuntu/Linux lock/install smoke 均无问题。
262. **记录 Q7 用户 smoke 1～5 完成并暂停第 6 项** — 第 6 项 Linux lock/install smoke 当时待用户处理；本条为历史状态，后由决策 263 更正。
261. **完成 R9 前质量加固 Q6** — 完成依赖升级后的最小测试迁移，完整 unittest 293/293、compileall 和 diff-check 通过。
