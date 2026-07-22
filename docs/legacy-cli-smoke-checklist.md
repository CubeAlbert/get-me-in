# 旧 CLI Smoke Checklist

> 适用分支：`refactor`。本清单用于冻结 v1 CLI 的可见行为，作为 R0/G0 基线和 R5 迁移验收参照。它是人工 smoke，不替代核心 domain/application 自动化测试。

## 1. 执行前提

- 在项目根目录执行 `uv run python main.py`。
- 已配置 v1 运行所需环境变量和可用 LLM provider；需要验证 RAG 时，模型与 Chroma 依赖可用。
- 记录本次执行的时间、操作系统、Python 版本、provider 和实际 session id；测试产生的运行时数据不属于 v2 迁移输入。
- 对有外部副作用的工具，使用专用测试工作目录和可删除的测试文件；不得修改 `data/reference/`、`data/prompts/` 或 `data/resume/template/` 源资产。

通过标准：每项获得“预期可见结果”，且未出现无响应、未闭合的工具调用、意外退出或无法继续下一次用户请求。因外部依赖不可用而不能完成的项，记录为“环境阻塞”，不伪造通过。

## 2. 启动、基础对话和退出

| 编号 | 操作 | 预期可见结果 | 结果 |
|---|---|---|---|
| C01 | 启动 `uv run python main.py` | 出现欢迎信息和输入提示；RAG 在后台启动，不阻塞 CLI 输入 | [ ] |
| C02 | 输入简单问候或无需工具的问题 | 输出最终 Markdown 回复；返回下一次输入提示 | [ ] |
| C03 | 请求需要多轮执行的简单任务 | 显示进度后继续执行，最终输出回复；对话未卡死 | [ ] |
| C04 | 在输入提示按 Ctrl+C 或发送 EOF | 友好退出，不显示 traceback | [ ] |
| C05 | 输入 `/exit` | 输出退出提示并正常结束进程 | [ ] |

## 3. 命令与输入行为

| 编号 | 操作 | 预期可见结果 | 结果 |
|---|---|---|---|
| C10 | 输入 `/help` | 列出 `/edit`、`/ragreload`、`/dump`、`/restore`、`/rewind`、`/build-memory`、`/exit_sub`、`/auto-approve-switch`、`/exit` | [ ] |
| C11 | 输入空白文本 | 不调用 Agent，继续显示输入提示 | [ ] |
| C12 | 输入 `/edit`，在编辑器中写入一段文本后退出 | 编辑器内容作为一次用户请求提交 | [ ] |
| C13 | 配置不可用编辑器后输入 `/edit` | 显示编辑器不可用或取消提示，CLI 仍可继续使用 | [ ] |
| C14 | 输入一条普通文本后按 ↑／↓ | 可在非补全状态下浏览输入历史 | [ ] |
| C15 | 输入 `/auto-approve-switch on`、`off` 和无参数形式 | 审批开关按命令更新并显示当前状态 | [ ] |

## 4. Plan、工具审批、选择与取消

| 编号 | 操作 | 预期可见结果 | 结果 |
|---|---|---|---|
| C20 | 请求 Agent 创建并推进一个多步骤 Plan | 进度面板显示唯一的进行中事项；完成后不再显示活跃 Plan | [ ] |
| C21 | 触发一个需审批的写操作并选择拒绝 | 写操作未执行；工具调用被闭合；Agent 能继续说明或接受下一请求 | [ ] |
| C22 | 触发一个需审批的写操作并选择确认 | 操作执行并将结果返回给 Agent | [ ] |
| C23 | 请求需要 `provide_choices` 的澄清 | 显示选项及自定义输入入口；选择结果回到 Agent | [ ] |
| C24 | 在模型等待或工具执行期间按 Esc | 当前 loop 取消；随后提交新请求仍可正常完成 | [ ] |

## 5. Agent handoff

| 编号 | 操作 | 预期可见结果 | 结果 |
|---|---|---|---|
| C30 | 请求简历相关任务，使主 Agent 调用 `switch_to_subagent` | 显示审批；确认后切换至 ResumeAgent | [ ] |
| C31 | 在 ResumeAgent 会话中完成任务并返回主 Agent | 主 Agent 获得子 Agent 摘要，原 handoff 工具调用被闭合 | [ ] |
| C32 | 在主 Agent 输入 `/exit_sub` | 显示“当前已是主 Agent”的错误；CLI 保持可用 | [ ] |
| C33 | 在子 Agent 输入 `/exit_sub` | 子 Agent 被要求整理摘要并返回主 Agent | [ ] |
| C34 | 触发未知子 Agent 目标 | 显示未知 Agent 错误，进程和后续请求保持可用 | [ ] |

## 6. 存档、恢复、回退和 dump

| 编号 | 操作 | 预期可见结果 | 结果 |
|---|---|---|---|
| C40 | 完成一轮普通对话 | 在 `data/save/{session_id}/` 生成自动存档 | [ ] |
| C41 | 输入 `/dump` | 生成 `data/logs/<agent>_<datetime>_message.dump`，或显示失败提示且不中断 CLI | [ ] |
| C42 | 输入 `/restore` 并在列表中选择有效 session | 恢复主／子 Agent、Plan 和输入历史；显示上下文回顾 | [ ] |
| C43 | 输入 `/restore <不存在的 id>` | 报告读取失败；CLI 保持可用 | [ ] |
| C44 | 输入 `/rewind` 并选择历史用户输入后确认提交 | 输入被预填；确认后历史从选中消息前截断并重新执行 | [ ] |
| C45 | 在 `/rewind` 的预填编辑中取消或提交空文本 | 回退取消，历史不被截断 | [ ] |

## 7. RAG、Memory 与 Resume 纵向链路

| 编号 | 操作 | 预期可见结果 | 结果 |
|---|---|---|---|
| C50 | 输入 `/ragreload` | 重建／重载 RAG，显示成功或明确失败信息 | [ ] |
| C51 | 输入 `/ragreload <可匹配关键词>` | 仅重载匹配 Markdown，显示匹配数或未匹配提示 | [ ] |
| C52 | 通过工具查询 reference 或 memory | RAG 未就绪时给出可修复错误；就绪时返回结构化结果 | [ ] |
| C53 | 输入 `/build-memory` | 显示后台记忆构建已启动；CLI 不阻塞 | [ ] |
| C54 | 新建简历：确认语言与前缀，调用模板复制 | 复制 `*_CHN.tex`／`*_EN.tex` 和 README；冲突时不覆盖 | [ ] |
| C55 | 读取后对 LaTeX 做精确编辑 | 未读取时 edit 被拒绝；内容或行号不匹配时不写入文件 | [ ] |
| C56 | 调用 `build_pdf` | 返回 stdout、stderr、exit code；缺少 `pdflatex`、超时或编译失败给出明确错误 | [ ] |
| C57 | 编译成功后调用 `workspace_open` | 操作系统使用默认程序打开 PDF；失败提示可手动打开 | [ ] |

## 8. 记录模板

```text
执行日期：
执行者：
操作系统／Python：
LLM provider：
测试 session id：

通过：
失败：
环境阻塞：
异常日志／dump 路径：
结论：
```

## 9. R0 判定范围

本清单仅记录 v1 的可观察能力，供后续 R2–R8 使用。它不要求 v2 保留 `UIBridge`、全局 Registry、私有字段访问、旧存档格式或任何魔法控制字典；这些实现机制将在 v2 中由强类型协议和显式装配替代。

## 10. R5 v2 CLI 增量 Smoke

> 在旧入口仍保留期间，使用 `uv run python -m src.get_me_in.cli` 运行本节；不要用本节结果替代上方 v1 基线。R5 尚未接入真实 Knowledge/Memory 服务，因此 `/ragreload` 与 `/build-memory` 预期明确报告 R6 前不可用。

| 编号 | 操作 | 预期可见结果 | 结果 |
|---|---|---|---|
| V50 | 启动 `uv run python -m src.get_me_in.cli` | 出现 v2 输入提示；缺少必填配置时以可读错误退出，不显示 traceback | [ ] |
| V51 | 输入 `/help`，再输入未知命令 | 帮助来自 CommandRegistry；未知命令作为提示显示，CLI 保持可用 | [ ] |
| V52 | 输入普通文本，触发 Progress、工具、handoff 或终态 | CliApp 以 typed event 驱动 Continue；handoff 后目标 Runtime 可继续；终态后生成 v2 snapshot | [ ] |
| V53 | 触发审批并使用 `/approval prompt`、`/approval auto` | prompt 模式询问确认；auto 模式自动发送 Approve；均不修改 ToolDefinition | [ ] |
| V54 | 触发 SelectionRequested，分别选择预置项、自定义输入和取消 | 分别发送 SubmitSelection 或 Cancel；后续请求仍可运行 | [ ] |
| V55 | 输入 `/restore`、`/rewind` | 使用公开 SessionView/list API 选择；`/restore` 显示序号、最近用户输入预览与保存时间而非 session_id；`/rewind` 显示序号与用户输入预览而非 turn_id；恢复后输入历史重建；回退预填文本 | [ ] |
| V56 | 运行期间按 Esc/Ctrl+C | WorkerRunner 仅调用 Application.request_cancel()；取消后可再次输入 | [ ] |

本节的 Windows UTF-8、EOF、编辑器不存在与真实 provider 结果需要人工记录；自动化测试仅覆盖 CLI 的 typed protocol 和隔离边界。
