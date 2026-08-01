# 当前状态

**当前阶段：** R8 完成态后的独立质量修正；正在修复 tool call message 非空契约与 CLI 展示，不进入 R9；R9 仍未授权

**当前任务：** 收紧所有模型输出的非空 message 契约，并把 tool-call message/thinking 通过 typed event 一致展示到 CLI

**当前子任务：** 先完成 OutputFormat／`ModelMessageCodec` 的非空 message 契约与定向回归，再独立 checkpoint。

**当前阻塞：** 无；设计、白名单和验收门禁已经用户确认。R9 独立授权门禁仍保持关闭。

**会话交接说明：** 决策 268 确认本修正同时处理 parser 允许空 `tool_call.message` 与 CLI 不展示 message 两个缺口。OutputFormat 删除 `<InputOutputDistinction>`，所有事件 message 由代码强制非空；finish thinking 只在 Prompt 中要求，parser 保持宽容；finish/tool-call message 均使用 Markdown，thinking 继续通过 `Panel(Text(...))` 受 `SHOW_THINKING` 控制并显示在 message 上方。Prompt/codec 与 RuntimeEvent/CLI 分片 checkpoint，最终完整验证和文档收口单独提交。R8-P～R8-G/G8 完成态不变；不得读取、迁移、改写或删除旧运行数据，不得进入 R9。

**下一步：** 修改 `08_output_format.md`、`ModelMessageCodec` 及对应测试，运行定向验证并建立第一个代码 checkpoint。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

268. **确认 tool call message 非空契约与 CLI Markdown 展示修正** — 所有模型输出 message 由 parser 强制非空；finish thinking 仅在 Prompt 中必填且为纯文本；`ToolStarted` 携带 message/thinking，CLI 按 thinking Panel → Markdown message → 工具状态展示；范围与分片 checkpoint 已确认，R9 仍未授权。
267. **修复 workspace_edit 多行修改后的 read-before-edit 行号漂移回归** — 成功 edit 消费当前 read 授权；下一次 edit 必须重新 workspace_read，返回 revision 不再直接授权下一次编辑；定向 54/54、完整 unittest 295/295、compileall 和 diff-check 通过。R9 仍未授权。
266. **确认 Windows/Linux Resume XeLaTeX 真实 smoke 已完成** — 用户确认已在 Windows 和 Linux 分别完成中文与英文模板的真实 XeLaTeX PDF 编译验证；此前本机 MiKTeX 诊断不代表项目验证状态，现无阻塞。R9 仍未授权。
265. **统一 Resume 跨平台编译引擎为 XeLaTeX** — 中文模板固定 `fontset=fandol`，英文模板移除中文环境包；适配器使用 `xelatex`，保留 shell 限制、cwd、超时、取消、stdout/stderr 捕获和日志边界。
264. **完成 R9 前质量加固 Q7 与文档状态收口** — Q1～Q6 coding、完整验证、Q7 用户 smoke 和最终文档状态均完成；R9 仍需独立授权。
263. **记录 Q7 用户 smoke 1～6 全部完成** — 用户确认 Main/Resume handoff、R8-F-C、query_memory、Q7 业务边界及 Ubuntu/Linux lock/install smoke 均无问题。
262. **记录 Q7 用户 smoke 1～5 完成并暂停第 6 项** — 第 6 项 Linux lock/install smoke 当时待用户处理；本条为历史状态，后由决策 263 更正。
261. **完成 R9 前质量加固 Q6** — 完成依赖升级后的最小测试迁移，完整 unittest 293/293、compileall 和 diff-check 通过。
260. **Q6 依赖升级子任务完成但完整验证阻塞** — 依赖升级完成，但旧 retrieval 测试断言造成范围外失败，等待授权迁移。
259. **完成 R9 前质量加固 Q5** — session dump 独立目录和 CLI Rich 输出安全修复完成，定向测试 60/60 通过。
