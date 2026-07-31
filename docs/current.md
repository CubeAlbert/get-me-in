# 当前状态

**当前阶段：** R8 已完成并通过最终用户审查；Resume 跨平台编译回归修复及 Windows/Linux 真实 smoke 已完成，不进入 R9；R9 仍未授权

**当前任务：** Resume 模板与编译适配器统一使用 XeLaTeX，代码、测试、文档记录及 Windows/Linux 真实 PDF smoke 均已完成

**当前子任务：** 中文模板固定 `fontset=fandol`、英文模板移除中文包、`LocalResumeArtifacts` 使用 `xelatex`，定向验证和跨平台真实 smoke 均已完成。

**当前阻塞：** 无；用户已确认 Windows 和 Linux 均完成中文/英文 XeLaTeX 真实 PDF smoke。R9 独立授权门禁仍保持关闭。

**会话交接说明：** 决策 254 建立 `docs/pre-r9-quality-hardening.md`，作为后续唯一质量加固执行清单；Q1～Q7、HandoffContext、R8-F-C、query_memory provider smoke 以及 Windows/Linux Resume XeLaTeX 真实 smoke 均已完成。Resume 编译器统一为 XeLaTeX 的决策为 265，跨平台 smoke 完成更正为 266。R8-P～R8-G/G8 完成态不变；任何工作不得读取、迁移、改写或删除旧运行数据。新会话必须继续遵守 R9 独立授权门禁。

**下一步：** 等待用户明确授权 R9；在此之前不得检查、设计或实施 R9。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

266. **确认 Windows/Linux Resume XeLaTeX 真实 smoke 已完成** — 用户确认已在 Windows 和 Linux 分别完成中文与英文模板的真实 XeLaTeX PDF 编译验证；此前本机 MiKTeX 诊断不代表项目验证状态，现无阻塞。R9 仍未授权。
265. **统一 Resume 跨平台编译引擎为 XeLaTeX** — 中文模板固定 `fontset=fandol`，英文模板移除中文环境包；适配器使用 `xelatex`，保留 shell 限制、cwd、超时、取消、stdout/stderr 捕获和日志边界。
264. **完成 R9 前质量加固 Q7 与文档状态收口** — Q1～Q6 coding、完整验证、Q7 用户 smoke 和最终文档状态均完成；R9 仍需独立授权。
263. **记录 Q7 用户 smoke 1～6 全部完成** — 用户确认 Main/Resume handoff、R8-F-C、query_memory、Q7 业务边界及 Ubuntu/Linux lock/install smoke 均无问题。
262. **记录 Q7 用户 smoke 1～5 完成并暂停第 6 项** — 第 6 项 Linux lock/install smoke 当时待用户处理；本条为历史状态，后由决策 263 更正。
261. **完成 R9 前质量加固 Q6** — 完成依赖升级后的最小测试迁移，完整 unittest 293/293、compileall 和 diff-check 通过。
260. **Q6 依赖升级子任务完成但完整验证阻塞** — 依赖升级完成，但旧 retrieval 测试断言造成范围外失败，等待授权迁移。
259. **完成 R9 前质量加固 Q5** — session dump 独立目录和 CLI Rich 输出安全修复完成，定向测试 60/60 通过。
258. **完成 R9 前质量加固 Q4** — Workspace no-replace、单次 snapshot 读取和有限文件搜索完成，定向测试 40/40 通过。
257. **完成 R9 前质量加固 Q3** — Tool Schema 的 allowed-values 和 list items 外层校验完成，定向测试 67/67 通过。
