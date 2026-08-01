# 当前状态

**当前阶段：** R8 完成态后的独立质量修正；tool call message 非空契约与 CLI 展示工程实现已完成，等待真实 provider smoke；R9 仍未授权

**当前任务：** 真实 provider／TTY 验收 tool-call message Markdown 与 thinking 纯文本展示

**当前子任务：** 分别在 `SHOW_THINKING=false` 与 `true` 下触发真实工具调用，确认 message 始终显示、thinking 仅在开启时显示且位于 message 上方。

**当前阻塞：** 需要用户的真实 provider 凭据、交互式 TTY 与主观终端展示确认；自动化 296/296、compileall、diff-check 和 production-component smoke 已通过。R9 独立授权门禁仍保持关闭。

**会话交接说明：** 决策 269 记录设计 checkpoint `b190a06`、Prompt/codec checkpoint `0694c2b` 与 RuntimeEvent/CLI checkpoint `5a43fda`。定向测试 65/65、84/84，完整 unittest 296/296、compileall、diff-check、InputFormat blob 与 production-component smoke 均通过；真实 provider smoke 不得由 fake/unit 结果替代。R8-P～R8-G/G8 完成态不变；不得读取、迁移、改写或删除旧运行数据，不得进入 R9。

**下一步：** 用户完成两种 `SHOW_THINKING` 设置下的真实工具调用 smoke；通过后同步最终完成态文档并 checkpoint。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

269. **完成 tool call message 修正的工程实现与自动化门禁** — `b190a06`、`0694c2b`、`5a43fda` 已提交；定向 65/65、84/84，完整 unittest 296/296、compileall、diff-check、InputFormat blob 与 production-component smoke 通过；等待真实 provider／TTY smoke，R9 仍未授权。
268. **确认 tool call message 非空契约与 CLI Markdown 展示修正** — 所有模型输出 message 由 parser 强制非空；finish thinking 仅在 Prompt 中必填且为纯文本；`ToolStarted` 携带 message/thinking，CLI 按 thinking Panel → Markdown message → 工具状态展示；范围与分片 checkpoint 已确认，R9 仍未授权。
267. **修复 workspace_edit 多行修改后的 read-before-edit 行号漂移回归** — 成功 edit 消费当前 read 授权；下一次 edit 必须重新 workspace_read，返回 revision 不再直接授权下一次编辑；定向 54/54、完整 unittest 295/295、compileall 和 diff-check 通过。R9 仍未授权。
266. **确认 Windows/Linux Resume XeLaTeX 真实 smoke 已完成** — 用户确认已在 Windows 和 Linux 分别完成中文与英文模板的真实 XeLaTeX PDF 编译验证；此前本机 MiKTeX 诊断不代表项目验证状态，现无阻塞。R9 仍未授权。
265. **统一 Resume 跨平台编译引擎为 XeLaTeX** — 中文模板固定 `fontset=fandol`，英文模板移除中文环境包；适配器使用 `xelatex`，保留 shell 限制、cwd、超时、取消、stdout/stderr 捕获和日志边界。
264. **完成 R9 前质量加固 Q7 与文档状态收口** — Q1～Q6 coding、完整验证、Q7 用户 smoke 和最终文档状态均完成；R9 仍需独立授权。
263. **记录 Q7 用户 smoke 1～6 全部完成** — 用户确认 Main/Resume handoff、R8-F-C、query_memory、Q7 业务边界及 Ubuntu/Linux lock/install smoke 均无问题。
262. **记录 Q7 用户 smoke 1～5 完成并暂停第 6 项** — 第 6 项 Linux lock/install smoke 当时待用户处理；本条为历史状态，后由决策 263 更正。
261. **完成 R9 前质量加固 Q6** — 完成依赖升级后的最小测试迁移，完整 unittest 293/293、compileall 和 diff-check 通过。
260. **Q6 依赖升级子任务完成但完整验证阻塞** — 依赖升级完成，但旧 retrieval 测试断言造成范围外失败，等待授权迁移。
