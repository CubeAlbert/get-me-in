# v1 能力等价矩阵

> 基线范围：`refactor` 分支上的旧实现。本文记录可观察行为，而非 v2 设计。它是后续迁移的验收依据；仅当保留本文说明的调用方可见契约，或已有明确的 R-D 决策将其废止时，v2 才可改变内部实现机制。

## 状态与阅读规则

- **源基线：**提交 `5e6e892`（`docs(refactor): add v2 rewrite plan`）。
- **范围内：**`main.py` 与 `src/` 中当前已实现的行为。
- **R-D6 已排除／废止：**旧 Session、Memory、Chroma 索引、`data/temp/`、输入历史、Plan、handoff 状态和 dump/log 状态的迁移。
- **错误约定：**工具 handler 对可修复的调用方错误抛出 `ToolCallException`；`BaseAgent` 将它和未预期异常转换为供模型使用的结构化工具调用结果。审批拒绝和取消以旧版哨兵载荷表示。
- **等价规则：**“能力相同”不要求保留 v1 的全局注册表、魔法字典、私有字段访问或 import-time 副作用；这些机制会被 v2 架构显式替换。

## 应用与交互基线

| 能力 | 输入 | 输出 | 副作用 | 失败／边界行为 | v2 处置 |
|---|---|---|---|---|---|
| CLI 对话 | 用户文本；内部依次使用 `Request(USER_INPUT)` 与 `CONTINUE` | 渲染后的最终 Markdown 或进度更新 | 保留每个 Agent 的历史；在 `FINISH` 时自动保存；可选启动记忆提取 | EOF/Ctrl+C 退出外层循环；格式错误的模型输出获得一次修复尝试 | 迁移 |
| 主 Agent → 子 Agent handoff | 主模型调用 `switch_to_subagent(agent_name, context)` | 主 Agent 暂停，指定子 Agent 成为活跃 Agent | 保存切换调用 id；之后将摘要注入为匹配的工具结果 | 必须获得用户审批；未知 registry key 渲染为错误 | 以强类型 handoff 替换 |
| 子 Agent → 主 Agent 返回 | 子模型调用 `switch_to_mainagent(summary)`，或用户输入 `/exit_sub` | 主 Agent 携带摘要上下文继续执行 | 保存主 Agent 状态，并计划清理子 Agent 存档 | 主 Agent 活跃时 `/exit_sub` 无效 | 以强类型 handoff 替换 |
| 用户选择 | `provide_choices(question, choices)` | 工具结果中的已选文本或自定义文本 | CLI 渲染 questionary UI 时，worker 通过 `UIBridge` 阻塞 | 依赖 UI 的可用性和取消结果 | 以强类型选择事件替换 |
| 工具审批 | 工具元数据与 `TOOL_CONFIRM_ENABLED` | 已批准执行或已拒绝结果 | CLI/UIBridge 阻塞等待确认 | 支持 `NEVER`、`ALWAYS`、`CONFIG`；拒绝会闭合旧工具调用 | 迁移策略，替换 UI bridge |
| 取消 | Agent loop 执行期间按 Esc | 已取消的工具结果／已取消的 loop 状态 | 模块级取消事件被设置，并在新请求开始时清除 | 在 LLM 前、LLM 后和工具前检查；后续请求仍应可用 | 迁移行为，替换全局事件 |
| 帮助与命令 | `/help`、`/edit`、`/dump`、`/restore [id]`、`/rewind`、`/ragreload [target]`、`/build-memory`、`/exit_sub`、`/auto-approve-switch`、`/exit` | 渲染的命令结果或下一请求 | 编辑器打开临时文件；restore 改写 handler 状态；reload 触发 RAG 加载 | 缺少编辑器返回空输入；无效 restore 会报告；`/exit` 结束 CLI | 迁移 |
| Session 保存／恢复／回退 | Agent 历史、Plan、session id；可选的回退目标 | JSON 存档数据、恢复的活跃对话、预填输入 | 写入 `data/save/{session_id}`；恢复主／子历史与 Plan | 保存失败写日志；缺失／损坏的 session 会报告；回退会在重新提交前截断历史 | 迁移为新的 v2 schema；不迁移 v1 数据 |
| 对话 dump | 当前 Agent 历史 | dump 路径或失败提示 | 在 `data/logs/` 写入带时间戳的消息 dump | 失败时返回 false 并写日志 | 迁移 |

## Agent、提示词与模型基线

| 能力 | 输入 | 输出 | 副作用 | 失败／边界行为 | v2 处置 |
|---|---|---|---|---|---|
| 主 Agent 路由 | 用户请求与已注册子 Agent 描述符 | 主 Agent 回答或 handoff 工具调用 | 读取全局 `AgentRegistry` 的提示词数据 | 设计上不直接执行领域工作；未知目标由 App 拒绝 | 迁移为声明式 spec |
| 简历专长 | 简历／JD 请求与 workspace 工具 | 简历建议、文件／工具调用或返回摘要 | 仅通过工具操作；读取 LaTeX 模板提示词数据 | 精确编辑前必须读取；工具／编译错误回馈给模型 | 在 R7 迁移 |
| 求职搜索专长 | 求职搜索请求 | 模型回复／工具使用 | 启动时注册 | 当前仅为测试／切片 Agent；完整产品能力被冻结 | 保留基线，延后产品扩展 |
| 提示词渲染 | 提示词名称和 14 个 Agent 变量 | 拼接的通用 Agent 与专用 Agent 提示词 | 读取 `data/prompts/` | 缺少提示词、未解析变量或缺失变量时加载／渲染失败 | 迁移渲染器并保留静态资产 |
| LLM 对话 | OpenAI 兼容消息、工具 XML、tier 参数 | 解析后的 JSON 模型回复和可选 thinking | 惰性、线程安全的客户端单例；provider thinking 配置 | provider／解析／格式错误进入 Agent 修复或失败路径；thinking 在下轮模型输入前剥离 | 迁移 adapter 行为 |
| Web 搜索 | 自然语言查询 | 基于搜索的文本 | 使用 LLM 客户端的 web-search 方法 | provider 失败成为工具失败 | 迁移／重新定义 adapter |

## legacy 工具目录基线（25 个工具）

当前工具可见性由隐式规则控制：通用工具对所有 Agent 可见，`agent=["main"]` 仅主 Agent 可见，`agent=["*"]` 表示子 Agent，resume workspace 工具仅 ResumeAgent 可见。`N` 表示从不审批，`A` 表示始终审批，`C` 表示跟随配置。

| 工具 | 输入 → 输出 | 副作用 | 失败／约束 | 审批 | v2 处置 |
|---|---|---|---|---|---|
| `get_current_datetime` | 无 → 含时区偏移的本地时间戳 | 无 | 仅依赖系统时钟 | N | 迁移 |
| `get_working_dir` | 无 → 工作区绝对路径 | 缺失时创建配置的工作目录 | 文件系统错误向上传播 | N | 迁移 |
| `web_search` | 查询 → 搜索文本 | 远程模型／搜索请求 | provider 失败 | C | 重新定义 adapter |
| `switch_to_subagent` | 目标 key、上下文 → 切换哨兵 | 请求 handoff | 仅主 Agent；目标随后必须可解析 | A | 替换 |
| `switch_to_mainagent` | 摘要 → 切换哨兵 | 请求返回 handoff | 仅子 Agent | A | 替换 |
| `provide_choices` | 问题、选项 → 已选文本 | 阻塞于 `UIBridge.select()` | UI 取消／不可用 | N | 替换 |
| `create_plan` | 事项描述 → 完整 Plan 状态 | 替换当前 Plan；首项变为进行中 | 依赖当前 Agent 全局上下文 | N | 迁移至服务 |
| `update_plan_status` | 事项 id、状态 → 完整 Plan 状态 | 更新事项；可能激活下一项 | 合法状态：pending/in_progress/completed/cancelled | N | 迁移至服务 |
| `cancel_all_plans` | 无 → 空／已完成 Plan 结果 | 取消未完成事项 | 依赖当前 Agent 全局上下文 | N | 迁移至服务 |
| `replan` | 替换后的未完成事项 → 完整 Plan 状态 | 保留已完成工作，替换剩余事项 | 依赖当前 Agent 全局上下文 | N | 迁移至服务 |
| `workspace_read` | 相对路径、offset、limit → 带行号文本 | 在进程缓存中标记文件已读 | 仅工作区内；文件必须是可读文本 | N | 迁移 |
| `workspace_list` | 相对目录 → entries | 无 | 仅工作区内；路径必须是目录 | N | 迁移 |
| `workspace_grep` | pattern、path、glob、regex、limit → matches | 无 | 仅工作区内；模式／编码错误 | N | 迁移 |
| `workspace_search_file` | 文件名 glob、path、limit → 路径 | 无 | 仅工作区内；结果到上限时设置 `truncated` | N | 迁移 |
| `workspace_replace` | 文件、旧文本、新文本 → 替换数 | 以 UTF-8 重写文件 | 仅文件；实现本身不强制文档要求的事前读取规则 | C | 迁移并加强原子性 |
| `workspace_write` | 新相对路径、内容 → written 标记 | 创建父目录和文件 | 拒绝覆盖；仅工作区内 | C | 迁移为原子写入 |
| `workspace_delete` | 相对路径列表 → 已删除路径和逐路径错误 | 删除文件或空目录 | 允许部分成功；拒绝删除非空目录 | C | 迁移 |
| `workspace_move` | 源路径、目标路径 → moved 标记 | 移动／重命名并创建父目录 | 源必须存在；目标不得存在 | C | 迁移 |
| `workspace_edit` | 文件和行号／旧内容 edits → 已应用结果 | 重写文件 | 必须先 `workspace_read`；任一行不匹配／错误会在写入前中止 | C | 迁移为 session-scoped revision |
| `workspace_open` | 现有文件 → opened 标记 | 启动操作系统默认打开器 | 文件缺失或操作系统启动失败 | C | 通过 frontend adapter 迁移 |
| `read_customer_file` | 外部路径、offset、limit → 带行号文本／PDF／DOCX 内容 | 读取工作区外的用户提供文件 | 必须存在且格式受支持／可读 | C | 以显式授权边界迁移 |
| `query_memory` | 查询、可选 `fact`／`preference`、top-k → chunks | 查询 Chroma memory collection | RAG 必须就绪；无效类型抛出 `ToolCallException` | N | 至 R6 前使用 port adapter |
| `query_reference_data` | 查询、可选参考分类、top-k → chunks | 查询 Chroma reference collection | RAG 必须就绪；无效分类抛出 `ToolCallException` | N | 至 R6 前使用 port adapter |
| `copy_template` | 模板、前缀、可选目标目录 → 已复制 artifact 路径 | 复制 LaTeX 模板文件与 README | 模板／名称／路径无效，或目标发生冲突 | C | 在 R7 迁移 |
| `build_pdf` | 相对 `.tex` 路径 → 编译结果／PDF 路径 | 运行 `pdflatex`，生成辅助文件和 PDF | 缺少源文件／编译器，非零退出，超时或编译错误 | C | 通过 process／artifact service 迁移 |

### R3 实际工具迁移矩阵（25/25）

> 本表以 `build_application(settings).tool_catalog.export_descriptors()` 为唯一目录来源；自动化测试断言其名称集合与数量均为 25。`已迁移`表示 R3 已具备显式定义、参数校验、审批策略和 Runtime 闭合；后续里程碑仅替换对应端口实现或补齐编排能力。

| 工具 | v2 builder | R3 状态 | 后续替换／补齐 |
|---|---|---|---|
| `get_current_datetime` | `build_system_tools` | 已迁移 | 无 |
| `get_working_dir` | `build_system_tools` | 已迁移 | 无 |
| `web_search` | `build_web_tools` | 已迁移 | R5 真实 CLI smoke |
| `switch_to_subagent` | `build_switch_tools` | 已迁移为 `ToolHandoff` | R4 执行 handoff frame |
| `switch_to_mainagent` | `build_switch_tools` | 已迁移为 `ToolHandoff` | R4 执行 handoff frame |
| `provide_choices` | `build_switch_tools` | 已迁移为 `ToolInteraction` | R5 CLI 交互渲染 |
| `create_plan` | `build_plan_tools` | 已迁移 | R4 将计划纳入 Session |
| `update_plan_status` | `build_plan_tools` | 已迁移 | R4 将计划纳入 Session |
| `cancel_all_plans` | `build_plan_tools` | 已迁移 | R4 将计划纳入 Session |
| `replan` | `build_plan_tools` | 已迁移 | R4 将计划纳入 Session |
| `workspace_read` | `build_workspace_tools` | 已迁移 | R7 capability 绑定 |
| `workspace_list` | `build_workspace_tools` | 已迁移 | R7 capability 绑定 |
| `workspace_grep` | `build_workspace_tools` | 已迁移 | R7 capability 绑定 |
| `workspace_search_file` | `build_workspace_tools` | 已迁移 | R7 capability 绑定 |
| `workspace_replace` | `build_workspace_tools` | 已迁移 | R7 capability 绑定 |
| `workspace_write` | `build_workspace_tools` | 已迁移 | R7 capability 绑定 |
| `workspace_delete` | `build_workspace_tools` | 已迁移 | R7 capability 绑定 |
| `workspace_move` | `build_workspace_tools` | 已迁移 | R7 capability 绑定 |
| `workspace_edit` | `build_workspace_tools` | 已迁移 | R7 capability 绑定 |
| `workspace_open` | `build_workspace_tools` | 已迁移 | R5/R7 真实前端 smoke |
| `read_customer_file` | `build_customer_file_tools` | 已迁移 | R5 附件授权入口 |
| `query_memory` | `build_retrieval_tools` | 已迁移，临时不可用 | R6 `KnowledgeService` 适配器 |
| `query_reference_data` | `build_retrieval_tools` | 已迁移，临时不可用 | R6 `KnowledgeService` 适配器 |
| `copy_template` | `build_resume_tools` | 已迁移 | R7 `ArtifactService` 记录版本 |
| `build_pdf` | `build_resume_tools` | 已迁移 | R7 `ArtifactService` 记录产物 |

### R8-O 当前工具扩展（26 个工具）

> R3 的 25/25 迁移结论与 R7 的 25-tool 验收证据是历史事实，不回写。决策 210 经用户明确授权新增第 26 个工具；production `ToolCatalog` 当前以 26 为验收值。

| 工具 | v2 builder | 当前状态 | 边界 |
|---|---|---|---|
| `merge_pdfs` | `build_resume_tools` | 已实现 | 仅 Resume 可见；按 first → second 合并工作区 PDF；需审批；`ArtifactService` 记录输出 hash、version 与 page count |

## 数据与生命周期基线

| 能力 | 输入 | 输出 | 副作用 | 失败／边界行为 | v2 处置 |
|---|---|---|---|---|---|
| Reference RAG | `data/reference/` 文件、可选 reload 目标 | 可搜索的参考 chunks | 在后台线程启动模型／索引加载；写入 Chroma 索引 | `is_ready()` 守卫查询工具；加载错误被记录／报告 | 在 R6 迁移 |
| Memory | Agent 对话和 memory-builder 提示词 | Markdown 的事实／偏好及检索结果 | 在 `data/memories/` 下按 Agent 写入文件；异步索引 | 索引失败写日志；关闭时等待待处理工作 | 仅新 repository；不迁移数据 |
| 静态资产 | 提示词文件、参考文件、简历模板 | 应用使用的输入 | 只读项目资产 | 缺少／损坏资产导致对应加载／工具失败 | 作为 v2 输入保留 |
| 日志／生命周期 | 日志调用和已注册关闭钩子 | 轮转应用日志和有序清理 | 写入 `data/logs/app.log`；关闭时逆序运行钩子 | 防御性失败写日志而不终止清理 | 迁移 |

## 非等价要求的显式旧机制

以下实现细节被明确排除在 v2 等价要求之外：可变模块级 `ToolRegistry`、`AgentRegistry`、当前 `UIBridge`、当前 Plan Agent 全局变量、workspace 读取缓存、惰性模块 facade、import-time 工具注册、CLI 对 Agent 私有字段的读写，以及 `__switch__`、`__reject__`、`__cancelled__` 等魔法字典。它们对调用方可见的结果已在本文其他位置覆盖，v2 必须以显式 composition、service 和强类型 runtime event 表达这些结果。
