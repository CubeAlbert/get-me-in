<!--
阅读指南：请先阅读目录找到相关决策，然后直接跳转到该章节。无需加载整个文件。
-->

# 决策记录

[按时间顺序记录重要的项目决策。每个条目分配一个递增编号。最近的决策应摘要在 `current.md` 的"重要决策"中。]

## 目录

- [决策 230 — 确认 R8-G 详细清单但不授权本会话实施](#决策-230--确认-r8-g-详细清单但不授权本会话实施)
- [决策 231 — 授权新会话实施 R8-G 并保持 G8 分流边界](#决策-231--授权新会话实施-r8-g-并保持-g8-分流边界)
- [决策 229 — R8-D 前置生命周期修复与遗留删除完成](#决策-229--r8-d-前置生命周期修复与遗留删除完成)
- [决策 228 — 辅助文档完成收敛并删除](#决策-228--辅助文档完成收敛并删除)
- [决策 227 — 授权新会话执行 R8-D 并收敛活跃文档](#决策-227--授权新会话执行-r8-d-并收敛活跃文档)
- [决策 226 — R8-D 执行清单细化并保持授权门禁](#决策-226--r8-d-执行清单细化并保持授权门禁)
- [决策 225 — R8-O 完整通过并停在 R8-D 授权门禁前](#决策-225--r8-o-完整通过并停在-r8-d-授权门禁前)
- [决策 219 — finish thinking 恢复为可选摘要](#决策-219--finish-thinking-恢复为可选摘要)
- [决策 224 — provide_choices 取消后暂停当前 Agent](#决策-224--provide_choices-取消后暂停当前-agent)
- [决策 223 — Esc 取消当前 SubAgent run 但保留 handoff](#决策-223--esc-取消当前-subagent-run-但保留-handoff)
- [决策 222 — `/exit_sub` 默认总结，false 允许直接退出](#决策-222--exit_sub-默认总结false-允许直接退出)
- [决策 217 — SessionSnapshot 持久化 agent turn_id 并兼容旧 handoff 快照](#决策-217--sessionsnapshot-持久化-agent-turn_id-并兼容旧-handoff-快照)
- [决策 216 — 模型回复解析失败暂停当前 SubAgent，由用户继续](#决策-216--模型回复解析失败暂停当前-subagent-由用户继续)
- [决策 215 — 模型调用上限默认调整为 100 且 Main／Resume 计数独立](#决策-215--模型调用上限默认调整为-100-且-mainresume-计数独立)
- [决策 214 — 工具调用未知参数沿用 v1 静默忽略语义](#决策-214--工具调用未知参数沿用-v1-静默忽略语义)
- [决策 213 — system prompt 顺序只由模板文件名决定](#决策-213--system-prompt-顺序只由模板文件名决定)
- [决策 212 — finish thinking 必须是非空用户可见摘要](#决策-212--finish-thinking-必须是非空用户可见摘要)
- [决策 211 — uv 唯一默认镜像切换为 TUNA 并拆分依赖添加与同步](#决策-211--uv-唯一默认镜像切换为-tuna-并拆分依赖添加与同步)
- [决策 210 — 新增 Resume-only PDF 合并工具并纳入 Artifact aggregate](#决策-210--新增-resume-only-pdf-合并工具并纳入-artifact-aggregate)
- [决策 209 — 选择交互取消不得提升为 Agent 或 handoff 取消](#决策-209--选择交互取消不得提升为-agent-或-handoff-取消)
- [决策 208 — RAG 启动后台预热全部查询模型且不泄漏权重输出](#决策-208--rag-启动后台预热全部查询模型且不泄漏权重输出)
- [决策 207 — targeted Knowledge reload 只比较目标范围](#决策-207--targeted-knowledge-reload-只比较目标范围)
- [决策 206 — 空 Memory collection 返回空结果并以显式迁移准备真实测试](#决策-206--空-memory-collection-返回空结果并以显式迁移准备真实测试)
- [决策 205 — Main 的业务能力只由当前 SubAgent 穷尽定义](#决策-205--main-的业务能力只由当前-subagent-穷尽定义)
- [决策 204 — 在单次模型修复前增加本地 JSON repair](#决策-204--在单次模型修复前增加本地-json-repair)
- [决策 203 — 恢复 v2 provider JSON mode](#决策-203--恢复-v2-provider-json-mode)
- [决策 202 — 多余模型字段采用允许列表投影而非格式修复](#决策-202--多余模型字段采用允许列表投影而非格式修复)
- [决策 201 — 收敛模型输出协议并由 Runtime 填充内部事件字段](#决策-201--收敛模型输出协议并由-runtime-填充内部事件字段)
- [决策 200 — 恢复 Main／Resume 剩余 Agent prompt 元数据](#决策-200--恢复-mainresume-剩余-agent-prompt-元数据)
- [决策 199 — 恢复 Main／Resume 完整 CommunicationStyle](#决策-199--恢复-mainresume-完整-communicationstyle)
- [决策 198 — 恢复 SubAgent XML prompt 并限定路由可见性](#决策-198--恢复-subagent-xml-prompt-并限定路由可见性)
- [决策 197 — 恢复 legacy XML Tool prompt 结构与固定语义顺序](#决策-197--恢复-legacy-xml-tool-prompt-结构与固定语义顺序)
- [决策 196 — 恢复 25 个 Tool 的完整 LLM-facing 语义](#决策-196--恢复-25-个-tool-的完整-llm-facing-语义)
- [决策 195 — Tool 提示词语义缺失阻断 R8-O](#决策-195--tool-提示词语义缺失阻断-r8-o)
- [决策 194 — 恢复固定欢迎 banner 并暂缓主题客制化](#决策-194--恢复固定欢迎-banner-并暂缓主题客制化)
- [决策 193 — R8-O 前置审查修复入口诊断与关闭边界](#决策-193--r8-o-前置审查修复入口诊断与关闭边界)
- [决策 192 — R8-E 已完成并建立入口回退点](#决策-192--r8-e-已完成并建立入口回退点)
- [决策 191 — 授权 R8 实施并完成 R8-P](#决策-191--授权-r8-实施并完成-r8-p)
- [决策 190 — R8 设计审查收紧入口错误、回退配置与验收证据](#决策-190--r8-设计审查收紧入口错误回退配置与验收证据)
- [决策 189 — R7-T2 修复完成并再次恢复 G7](#决策-189--r7-t2-修复完成并再次恢复-g7)
- [决策 188 — R7-T2 审查再次撤回 G7 并细化 R8](#决策-188--r7-t2-审查再次撤回-g7-并细化-r8)
- [决策 187 — R7-T 修复完成并重新通过 G7](#决策-187--r7-t-修复完成并重新通过-g7)
- [决策 186 — 撤回 G7 完成结论并记录 R7-T 审查问题](#决策-186--撤回-g7-完成结论并记录-r7-t-审查问题)
- [决策 185 — 批准原始字节 content_hash 并完成 R7/G7](#决策-185--批准原始字节-content_hash-并完成-r7g7)
- [决策 184 — R7-P6 production composition 完成](#决策-184--r7-p6-production-composition-完成)
- [决策 183 — R7-P5 ArtifactService 完成](#决策-183--r7-p5-artifactservice-完成)
- [决策 182 — Artifact 使用 operation aggregate 持久化](#决策-182--artifact-使用-operation-aggregate-持久化)
- [决策 181 — Resume 双 Runtime composition 完成](#决策-181--resume-双-runtime-composition-完成)
- [决策 180 — R7-P 动态 session identity 完成](#决策-180--r7-p-动态-session-identity-完成)
- [决策 179 — R7-P0 temperature 契约完成并继续 R7](#决策-179--r7-p0-temperature-契约完成并继续-r7)
- [决策 178 — 确认 R7 具体清单与 temperature/log 补充](#决策-178--确认-r7-具体清单与-temperaturelog-补充)
- [决策 177 — 确认 R7 总体边界并提交具体清单审查](#决策-177--确认-r7-总体边界并提交具体清单审查)
- [决策 176 — R6-F 完成并重新通过 G6](#决策-176--r6-f-完成并重新通过-g6)
- [决策 175 — 撤销 G6 通过结论并授权 R6-F 审查修复](#决策-175--撤销-g6-通过结论并授权-r6-f-审查修复)
- [决策 174 — G6 通过并停在 R6-T 审查门禁](#决策-174--g6-通过并停在-r6-t-审查门禁)
- [决策 173 — v2 显式装配日志并固定环境变量所有权](#决策-173--v2-显式装配日志并固定环境变量所有权)
- [决策 172 — R5-F follow-up 统一格式修复的唯一契约与重试边界](#决策-172--r5-f-follow-up-统一格式修复的唯一契约与重试边界)
- [决策 171 — R6 前增加独立 thinking 契约修复门禁](#决策-171--r6-前增加独立-thinking-契约修复门禁)
- [决策 170 — R6 清单获确认并固定新会话实施入口](#决策-170--r6-清单获确认并固定新会话实施入口)
- [决策 169 — R6 重设一致性边界并增加强制终止门禁](#决策-169--r6-重设一致性边界并增加强制终止门禁)
- [决策 168 — R5 审查修复命令事件闭合与错误边界](#决策-168--r5-审查修复命令事件闭合与错误边界)
- [决策 167 — G5 已通过且 R6 暂停](#决策-167--g5-已通过且-r6-暂停)
- [决策 166 — /restore 与 /rewind 的选择菜单提供取消项](#决策-166---restore-与-rewind-的选择菜单提供取消项)
- [决策 165 — /rewind 在回退前捕获预填文本](#决策-165---rewind-在回退前捕获预填文本)
- [决策 164 — 审批交互使用明确选项而非 y/N](#决策-164--审批交互使用明确选项而非-yn)
- [决策 163 — 用户拒绝审批立即结束当前 Agent 回合](#决策-163--用户拒绝审批立即结束当前-agent-回合)
- [决策 162 — R5 工具可见性使用强类型事件投影](#决策-162--r5-工具可见性使用强类型事件投影)
- [决策 161 — 恢复 DeepSeek Web Search 的旧版请求契约并拒绝未执行调用](#决策-161--恢复-deepseek-web-search-的旧版请求契约并拒绝未执行调用)
- [决策 160 — 不保留 /auto-approve-switch 向前兼容](#决策-160--不保留-auto-approve-switch-向前兼容)
- [决策 159 — 帮助从真实命令注册表排序并列出 alias](#决策-159--帮助从真实命令注册表排序并列出-alias)
- [决策 158 — /restore 选择显示会话预览而非内部 session_id](#决策-158---restore-选择显示会话预览而非内部-session_id)
- [决策 157 — /rewind 选择显示用户输入预览而非内部 turn_id](#决策-157---rewind-选择显示用户输入预览而非内部-turn_id)
- [决策 156 — InputController 通过 CompletionProvider 获取动态命令补全](#决策-156--inputcontroller-通过-completionprovider-获取动态命令补全)
- [决策 155 — R5 第一切片已审查并保持交互职责后置](#决策-155--r5-第一切片已审查并保持交互职责后置)
- [决策 154 — R5 清单获确认并固定新会话实施入口](#决策-154--r5-清单获确认并固定新会话实施入口)
- [决策 153 — R5 使用薄 CLI、单 WorkerRunner 与可替换命令注册](#决策-153--r5-使用薄-cli单-workerrunner-与可替换命令注册)
- [决策 152 — R4 复审补齐 handoff 启动、失败闭合与 frontend 回合投影](#决策-152--r4-复审补齐-handoff-启动失败闭合与-frontend-回合投影)
- [决策 151 — R4/G4 完成后先进入 R5 前复审](#决策-151--r4g4-完成后先进入-r5-前复审)
- [决策 150 — G4 后强制重新 Review R5 至 R8](#决策-150--g4-后强制重新-review-r5-至-r8)
- [决策 149 — 后续设计按当前 Runtime 重新校准](#决策-149--后续设计按当前-runtime-重新校准)
- [决策 148 — G2/G3 修复完成并恢复门禁结论](#决策-148--g2g3-修复完成并恢复门禁结论)
- [决策 147 — 架构复审撤销 G2/G3 完成结论并暂停 R4](#决策-147--架构复审撤销-g2g3-完成结论并暂停-r4)
- [决策 146 — R3 简历工具使用临时 ResumeArtifactPort](#决策-146--r3-简历工具使用临时-resumeartifactport)
- [决策 145 — R3 检索工具只依赖临时 RetrievalPort](#决策-145--r3-检索工具只依赖临时-retrievalport)
- [决策 144 — 文件预览经 FrontendPort 处理](#决策-144--文件预览经-frontendport-处理)
- [决策 143 — Runtime 直接执行显式 Catalog 工具，应用独立装配 Workspace](#决策-143--runtime-直接执行显式-catalog-工具应用独立装配-workspace)
- [决策 142 — system tools 通过显式 Clock 与 WorkspacePort 注入实现](#决策-142--system-tools-通过显式-clock-与-workspaceport-注入实现)
- [决策 141 — 保留静态 prompt 的 JSON 在应用边界归一化](#决策-141--保留静态-prompt-的-json-在应用边界归一化)
- [决策 140 — R2 用 ToolResult 闭合暂停的工具回合](#决策-140--r2-用-toolresult-闭合暂停的工具回合)
- [决策 139 — R1 临时无工具对话仅用于 G1 验证](#决策-139--r1-临时无工具对话仅用于-g1-验证)
- [决策 138 — R1 骨架清单获确认后开始编码](#决策-138--r1-骨架清单获确认后开始编码)
- [决策 137 — refactor 分支采用独立 v2 受控重写](#决策-137--refactor-分支采用独立-v2-受控重写)
- [决策 136 — 不暴露 LLM 原生 reasoning_content](#决策-136--不暴露-llm-原生-reasoning_content)
- [决策 135 — 发送 LLM 消息剥离 thinking + 修正 input format role](#决策-135--发送-llm-消息剥离-thinking--修正-input-format-role)
- [决策 134 — SessionId 统一：SaveManager & dumper 共享会话 ID](#决策-134--sessionid-统一savemanager--dumper-共享会话-id)
- [决策 133 — Spinner 计时排除 UIBridge 等待时长](#决策-133--spinner-计时排除-uibridge-等待时长)
- [决策 132 — LLM 调用超时 + 异常处理](#决策-132--llm-调用超时--异常处理)
- [决策 131 — 记忆集成基础设施](#决策-131--记忆集成基础设施)
- [决策 130 — Esc 中断 Agent 处理（基础完成，即时中止暂缓）](#决策-130--esc-中断-agent-处理基础完成即时中止暂缓)
- [决策 129 — /rewind 命令（内存级回退 + ↑↓ 输入历史）](#决策-129--rewind-命令内存级回退--输入历史)
- [决策 128 — replan 工具（保留已完成项）](#决策-128--replan-工具保留已完成项)
- [决策 127 — plan_status 简化 schema](#决策-127--plan_status-简化-schema)
- [决策 126 — Restore 恢复上下文预览](#决策-126--restore-恢复上下文预览)
- [决策 125 — plan_status 落地到 Message 对象](#决策-125--plan_status-落地到-message-对象)
- [决策 124 — RAG 模型加载本地缓存优先（local_files_only 回退策略）](#决策-124--rag-模型加载本地缓存优先local_files_only-回退策略)
- [决策 123 — 会话状态管理模块（auto-save / restore / rollback）](#决策-123--会话状态管理模块auto-save--restore--rollback)
- [决策 122 — CLI 命令注册改用 _COMMAND_HELP dict + /help 命令](#决策-122--cli-命令注册改用-_command_help-dict--help-命令)
- [决策 121 — workspace_delete 批量删除](#决策-121--workspace_delete-批量删除)
- [决策 120 — workspace_edit 读后编辑守卫](#决策-120--workspace_edit-读后编辑守卫)
- [决策 119 — plan_status 每轮注入替代一次性 PLAN 消息](#决策-119--plan_status-每轮注入替代一次性-plan-消息)
- [决策 118 — 删除 LLMHandler](#决策-118--删除-llmhandler)
- [决策 117 — Agent temperature 分层设置](#决策-117--agent-temperature-分层设置)
- [决策 116 — PLACEHOLDER.txt 升级为 README.md](#决策-116--placeholder.txt-升级为-readmemd)
- [决策 115 — /dump 命令导出对话历史用于调试](#决策-115--dump-命令导出对话历史用于调试)
- [决策 114 — 简历构建改为 workspace 工具直接编辑 LaTeX](#决策-114--简历构建改为-workspace-工具直接编辑-latex)
- [决策 113 — copy_template 用户交互前置到 LLM](#决策-113--copy_template-用户交互前置到-llm)
- [决策 112 — workspace_edit 简化为纯 replace 模式](#决策-112--workspace_edit-简化为纯-replace-模式)
- [决策 111 — RAG 查询工具用 StrEnum 校验 filter](#决策-111--rag-查询工具用-strenum-校验-filter)
- [决策 110 — workspace_replace 全文字符串替换](#决策-110--workspace_replace-全文字符串替换)
- [决策 109 — workspace_list 单层不递归](#决策-109--workspace_list-单层不递归)
- [决策 108 — workspace 工具限定 ResumeAgent](#决策-108--workspace-工具限定-resumeagent)
- [决策 107 — Agent key 常量统一管理](#决策-107--agent-key-常量统一管理)
- [决策 106 — ToolCallException 统一工具异常](#决策-106--toolcallexception-统一工具异常)
- [决策 105 — read_customer_file 绝对路径 + 统一输出格式](#决策-105--read_customer_file-绝对路径--统一输出格式)
- [决策 104 — workspace_edit 批量编辑 + 倒序处理 + old_content 校验](#决策-104--workspace_edit-批量编辑--倒序处理--old_content-校验)
- [决策 103 — workspace_read 结构化输出：行号 + 内容数组](#决策-103--workspace_read-结构化输出行号--内容数组)
- [决策 102 — workspace_search 拆分为 grep + search_file](#决策-102--workspace_search-拆分为-grep--search_file)
- [决策 101 — workspace_fs 拆分为三个独立工具](#决策-101--workspace_fs-拆分为三个独立工具)
- [决策 100 — Sticky plan 阻塞：questionary + Live 终端冲突](#决策-100--sticky-plan-阻塞questionary--live-终端冲突)
- [决策 99 — message=None 走 retry 而非静默兜底](#决策-99--messagenone-走-retry-而非静默兜底)
- [决策 98 — list[str] schema 自动生成 items 类型](#决策-98--liststr-schema-自动生成-items-类型)
- [决策 97 — SYSTEM_MESSAGE role 分类](#决策-97--system_message-role-分类)
- [决策 96 — Role 枚举化](#决策-96--role-枚举化)
- [决策 95 — Plan 工具标准模式：context variable 访问 Agent](#决策-95--plan-工具标准模式context-variable-访问-agent)
- [决策 94 — 结构化问题模板：collect_info.md + start_resume_building](#决策-94--结构化问题模板collect_infomd--start_resume_building)
- [决策 93 — 简历输入三路径 + LLM 判断](#决策-93--简历输入三路径--llm-判断)
- [决策 92 — RAG 查询拆分为 query_memory 和 query_reference_data](#决策-92--rag-查询拆分为-query_memory-和-query_reference_data)
- [决策 91 — 工作区工具按权限边界拆分](#决策-91--工作区工具按权限边界拆分)
- [决策 90 — 简历 Agent Plan → Execute 处理模式](#决策-90--简历-agent-plan--execute-处理模式)
- [决策 89 — 简历数据模型：结构化 Resume](#决策-89--简历数据模型结构化-resume)
- [决策 88 — Plan 机制作为通用基础设施](#决策-88--plan-机制作为通用基础设施)
- [决策 87 — 工具调用参数兼容性：忽略未知参数 + 校验必填](#决策-87--工具调用参数兼容性忽略未知参数--校验必填)
- [决策 86 — `MAIN_AGENT_KEY` 常量替换 magic string "main"](#决策-86--main_agent_key-常量替换-magic-string-main)
- [决策 85 — `__reject__` sentinel：switch 被拒后终止 agent loop](#决策-85--__reject__-sentinelswitch-被拒后终止-agent-loop)
- [决策 84 — UIBridge：工具 handler 通过跨线程通信桥直连 CLI 交互](#决策-84--uibridge工具-handler-通过跨线程通信桥直连-cli-交互)
- [决策 83 — switch tool 必须声明 input_schema](#决策-83--switch-tool-必须声明-input_schema)
- [决策 82 — CONFIRM 拒绝 → 下次 USER_INPUT 携带拒绝信息](#决策-82--confirm-拒绝--下次-user_input-携带拒绝信息)
- [决策 81 — Agent 稳定标识 _get_agent_key() + ToolRegistry "*" sentinel](#决策-81--agent-稳定标识-_get_agent_key--toolregistry--sentinel)
- [决策 80 — 子 Agent 列表 prompt 注入：{{SUB_AGENTS_LIST}} 占位符 + 模板重排](#决策-80--子-agent-列表-prompt-注入sub_agents_list-占位符--模板重排)
- [决策 79 — /exit_sub 主 Agent 前台时报错](#决策-79--exit_sub-主-agent-前台时报错)
- [决策 78 — Agent 切换机制：Tool-based 异步工具调用模型](#决策-78--agent-切换机制tool-based-异步工具调用模型)
- [决策 77 — JSON 解析增强：json-repair + 换行转义 + 提示注入节制](#决策-77--json-解析增强json-repair--换行转义--提示注入节制)
- [决策 76 — LLM Thinking 可配置开关](#决策-76--llm-thinking-可配置开关)
- [决策 75 — BaseAgent LLM 调用默认强制 JSON 输出](#决策-75--baseagent-llm-调用默认强制-json-输出)
- [决策 74 — 退出清理统一入口：Lifecycle 模块](#决策-74--退出清理统一入口lifecycle-模块)
- [决策 73 — LLMClient 线程安全单例](#决策-73--llmclient-线程安全单例)
- [决策 72 — MainAgent 重新定位为路由 Agent](#决策-72--mainagent-重新定位为路由-agent)
- [决策 71 — WORKING_DIR 环境变量 + get_working_dir() 工具](#决策-71--working_dir-环境变量--get_working_dir-工具)
- [决策 70 — LLMClient.web_search() 两轮 native function calling](#决策-70--llmclientweb_search-两轮-native-function-calling)
- [决策 69 — 审批 UI：questionary.select + ConfirmChoice 枚举](#决策-69--审批-uiquestionaryselect--confirmchoice-枚举)
- [决策 68 — MainAgent 位置：src/agents/main_agent.py](#决策-68--mainagent-位置srcagentsmain_agentpy)
- [决策 67 — 工具错误上下文增强：工具列表 + 参数 schema](#决策-67--工具错误上下文增强工具列表--参数-schema)
- [决策 66 — 用户拒绝审批 → 退出内层循环，不调 process()](#决策-66--用户拒绝审批--退出内层循环不调-process)
- [决策 65 — Request 类型（对称 Response）作为 App → Agent 输入协议](#决策-65--request-类型对称-response-作为-app--agent-输入协议)
- [决策 64 — Agent Loop 上移至 App 层 + process() 单步执行](#决策-64--agent-loop-上移至-app-层--process-单步执行)
- [决策 63 — message 默认 "" + event_type 唯一 required](#决策-63--message-默认--event_type-唯一-required)
- [决策 62 — 移除 04_tools.md 硬编码预定义工具](#决策-62--移除-04_toolsmd-硬编码预定义工具)
- [决策 61 — Message.to_json() / from_llm_reply() 统一序列化](#决策-61--messageto_json--from_llm_reply-统一序列化)
- [决策 60 — 06_output / 07_input prompt 分工](#决策-60--06_output--07_input-prompt-分工)
- [决策 59 — System prompt 隔离](#决策-59--system-prompt-隔离)
- [决策 58 — 工具 handler 返回纯数据](#决策-58--工具-handler-返回纯数据)
- [决策 57 — Message 新增 tool / tool_call_id 一级字段](#决策-57--message-新增-tool--tool_call_id-一级字段)
- [决策 56 — Message.event_type 枚举化：EventType(StrEnum)](#决策-56--messageeventtype-枚举化eventtypestrenum)
- [决策 55 — Agent Loop 中间进度回传：Response(type="progress")](#决策-55--agent-loop-中间进度回传responsetypeprogress)
- [决策 54 — 工具审批模式：ConfirmMode 枚举](#决策-54--工具审批模式confirmmode-枚举)
- [决策 53 — AgentRegistry 设计](#决策-53--agentregistry-设计)
- [决策 52 — M4 子 Agent 实现：面试问答 Agent](#决策-52--m4-子-agent-实现面试问答-agent)
- [决策 51 — Agent 切换机制：App.switch_agent()](#决策-51--agent-切换机制appswitch_agent)
- [决策 50 — CLI 交互库选型：questionary](#决策-50--cli-交互库选型questionary)
- [决策 49 — 意图路由：纯 LLM 驱动](#决策-49--意图路由纯-llm-驱动)
- [决策 48 — process() 接口：Message → Response](#决策-48--process-接口message--response)
- [决策 47 — ToolRegistry 全局注册表](#决策-47--toolregistry-全局注册表)
- [决策 46 — 工具错误处理](#决策-46--工具错误处理)
- [决策 45 — 工具可见性控制](#决策-45--工具可见性控制)
- [决策 44 — event_payload → 函数入参映射](#决策-44--event_payload--函数入参映射)
- [决策 43 — Tool 装饰器 + input_schema 设计](#决策-43--tool-装饰器--input_schema-设计)
- [决策 42 — Agent Loop 终止条件](#决策-42--agent-loop-终止条件)
- [决策 41 — 工具结果注入方式](#决策-41--工具结果注入方式)
- [决策 40 — Agent Loop 对话历史管理](#决策-40--agent-loop-对话历史管理)
- [决策 39 — Chroma in-memory delete(where=) 不可靠：delete_collection 替代方案](#决策-39--chroma-in-memory-deletewhere-不可靠delete_collection-替代方案)
- [决策 38 — 记忆模块统一入口 + 文件名 category + --- 分隔符](#决策-38--记忆模块统一入口--文件名-category----分隔符)
- [决策 37 — MemoryBuilder JSON 强制模式 + 换行拆分](#决策-37--memorybuilder-json-强制模式--换行拆分)
- [决策 36 — Memory 类别重构：fact/preference 两分类 + builder 严格 JSON 输出](#决策-36--memory-类别重构factpreference-两分类--builder-严格-json-输出)
- [决策 35 — MemoryStore 格式化逻辑抽出到 utils/formatters.py](#决策-35--memorystore-格式化逻辑抽出到-utilsformatterspy)
- [决策 34 — Message 通用消息模型：7 字段 + 模块分离](#决策-34--message-通用消息模型7-字段--模块分离)
- [决策 33 — 日志系统：标准库 logging + 按大小轮转](#决策-33--日志系统标准库-logging--按大小轮转)
- [决策 32 — MemoryBuilder 替代 Compressor（对话构建而非压缩）](#决策-32--memorybuilder-替代-compressor对话构建而非压缩)
- [决策 31 — Chunker 通用化 + front-matter 解析](#决策-31--chunker-通用化--front-matter-解析)
- [决策 30 — 一文件一条记忆 + front-matter KV 格式](#决策-30--一文件一条记忆--front-matter-kv-格式)
- [决策 29 — MemoryStore 与 RAG 解耦（观察者模式）](#决策-29--memorystore-与-rag-解耦观察者模式)
- [决策 28 — RAG 公共 API 极简化](#决策-28--rag-公共-api-极简化)
- [决策 27 — RagLoader 设计决策](#决策-27--ragloader-设计决策)
- [决策 26 — ChromaStore 统一检索入口（移除 Retriever）](#决策-26--chromastore-统一检索入口移除-retriever)
- [决策 25 — Reranker 设计决策](#决策-25--reranker-设计决策)
- [决策 24 — RAG 增量加载与文件同步策略](#决策-24--rag-增量加载与文件同步策略)
- [决策 23 — ChromaStore 内部设计决策](#决策-23--chromastore-内部设计决策)
- [决策 22 — /ragreload 手动重载命令](#决策-22--ragreload-手动重载命令)
- [决策 21 — HF_ENDPOINT 镜像配置](#决策-21--hf_endpoint-镜像配置)
- [决策 20 — Embedder/Reranker 模型分离 + batch_size 环境变量化](#决策-20--embedderreranker-模型分离--batch_size-环境变量化)
- [决策 19 — RagLoader 后台加载与降级](#决策-19--ragloader-后台加载与降级)
- [决策 18 — RAG 模型选型](#决策-18--rag-模型选型)
- [决策 17 — RAG 双 Collection + 统一分隔符](#决策-17--rag-双-collection--统一分隔符)
- [决策 16 — JSON 输出解析留待 M4](#决策-16--json-输出解析留待-m4)
- [决策 15 — 编排工具化而非提示词化](#决策-15--编排工具化而非提示词化)
- [决策 14 — Agent 无专属模板文件](#决策-14--agent-无专属模板文件)
- [决策 13 — LLM 参数分层管理](#决策-13--llm-参数分层管理)
- [决策 12 — 集中式环境变量管理](#决策-12--集中式环境变量管理configpy-模块)
- [决策 11 — Jupyter 交互式调试工作流](#决策-11--jupyter-交互式调试工作流)
- [决策 10 — LLM 后端：OpenAI SDK + 双 tier 封装](#决策-10--llm-后端openai-sdk--双-tier-封装)
- [决策 9 — 包管理：uv + SJTU 镜像](#决策-9--包管理uv--sjtu-镜像)
- [决策 8 — CLI 方案：input() + $EDITOR + rich](#决策-8--cli-方案input--editor--rich)
- [决策 7 — 编码时不写测试](#决策-7--编码时不写测试)
- [决策 6 — 工作流：Plan → Execute → Result Validation → Replan](#决策-6--工作流plan--execute--result-validation--replan)
- [决策 5 — 提示词管理：强制拼接 + 按用途组织](#决策-5--提示词管理强制拼接--按用途组织)
- [决策 4 — 记忆存储与分块策略](#决策-4--记忆存储与分块策略)
- [决策 3 — RAG 技术选型：Chroma + sentence_transformers](#决策-3--rag-技术选型chroma--sentence_transformers)
- [决策 2 — 同步代码，不使用 asyncio](#决策-2--同步代码不使用-asyncio)
- [决策 1 — 架构模式：Hub-and-Spoke + 自研轻量 Agent 框架](#决策-1--架构模式hub-and-spoke--自研轻量-agent-框架)
---

### 决策 1 — 架构模式：Hub-and-Spoke + 自研轻量 Agent 框架

**背景：** 项目包含多个专业化 Agent（简历、学习、面试、岗位搜索），需要确定 Agent 之间的通信模式和框架选型。

**决策：** 采用 Hub-and-Spoke 架构，主 Agent 是唯一调度中心，子 Agent 之间不允许直接通信。Agent 框架自研，不使用 LangChain / CrewAI / AutoGen 等现成框架。

**理由：**
- Hub-and-Spoke 匹配项目规模（< 10 个 Agent），不需要 Mesh 的对等通信复杂度
- 自研框架最大控制力，学习成本为零，依赖最小化
- 现成框架引入不必要的抽象层和几十个依赖包，项目只需几百行编排代码

**曾考虑的替代方案：**
- CrewAI / AutoGen —— 功能过剩，学习成本高，引入大量依赖，调试困难
- LangGraph —— StateGraph 抽象对 Hub-and-Spoke 模式过度设计
- Mesh 架构（Agent 对等通信）—— 当前 Agent 数量不需要，增加复杂度

---

### 决策 2 — 同步代码，不使用 asyncio

**背景：** 技术栈讨论时提到 asyncio 适合 Agent 调用场景，需要决定是否引入异步编程。

**决策：** 全部使用同步代码，不引入 asyncio 或任何异步框架。

**理由：** Agent 调用链在当前规模下同步执行即可，异步增加开发和调试成本，收益不明显。

**曾考虑的替代方案：**
- asyncio —— Python 标准库，但增加心智负担，当前规模不需要

---

### 决策 3 — RAG 技术选型：Chroma + sentence_transformers

**背景：** 需要语义检索能力支持记忆检索、面试题库、JD 匹配等场景，需要选择向量存储和模型方案。

**决策：** 使用 Chroma 作为向量存储（内存模式先行，后续可切本地持久化），sentence_transformers 提供 bi-encoder（召回）和 cross-encoder（重排）。

**理由：**
- Chroma 内存模式零配置启动，开发阶段免运维，后续改一行参数即可切换持久化
- sentence_transformers 一个库同时覆盖召回和重排两种模型，不引入额外依赖
- 召回+重排两阶段是 RAG 成熟模式：bi-encoder 快但粗，cross-encoder 慢但准

**曾考虑的替代方案：**
- FAISS —— 功能强大但偏底层，Chroma 更轻量且有 collection 管理
- 本地 JSON 文件存向量 —— 查询效率低，不支持近似搜索
- OpenAI Embeddings API —— 需要网络、有成本、不可离线

---

### 决策 4 — 记忆存储与分块策略

**背景：** 记忆需要持久化存储和语义检索，需要确定存储格式、目录组织、以及如何将记忆切分为可检索的单元。

**决策：**
- 记忆按 Agent 分目录（`data/memories/<agent>/`），每个 Agent 下按日期分文件
- 存储格式为 Markdown，文件系统而非数据库
- Agent 固化记忆时写入约定分隔符，Chunker 按分隔符切分为逻辑块后向量化入库
- Chroma collection 按模块划分（`memories`、`interview_questions`、`job_descriptions`），不按 Agent 划分

**理由：**
- 按 Agent 隔离避免互相干扰，跨 Agent 检索通过 RAG 语义搜索
- Markdown + 文件系统人机可读，Git 可追踪，免运维，项目规模下无性能瓶颈
- 分隔符切分策略由写入方（Agent）定义，Chunker 保持通用，不耦合业务语义
- Collection 按模块划分便于管理不同数据的检索场景

**曾考虑的替代方案：**
- SQLite / PostgreSQL —— 过度设计，失去人机可读性
- 按整篇 MD 文件入库 —— 粒度过粗，检索精度差
- 按 Agent 分 collection —— 记忆统一检索时需跨 collection 查询

---

### 决策 5 — 提示词管理：强制拼接 + 按用途组织

**背景：** 每个 Agent 需要各自独立的提示词，同时所有 Agent 需要共享安全策略、工具列表、输出格式等公共约束。

**决策：**
- `data/prompts/general_agent/` 目录下多个 `.md` 文件定义公共前缀（安全策略、工具列表、输出格式）
- `PromptLoader` 对 Agent 调用方强制拼接公共前缀，Agent 无法跳过
- 非 Agent 模块（记忆压缩等）使用 `get_raw()` 跳过拼接
- 提示词按用途命名，不按 Agent 划分

**理由：**
- 强制拼接确保所有 Agent 遵守统一的安全和格式约束
- 按用途组织允许同一提示词被多个模块复用
- 提示词与代码分离，调整提示词改文件即可，降低迭代成本

**曾考虑的替代方案：**
- 每个 Agent 各自管理完整提示词 —— 公共约束变更时需改多处，容易遗漏
- 公共提示词放在代码中硬编码 —— 调整需要改代码

---

### 决策 6 — 工作流：Plan → Execute → Result Validation → Replan

**背景：** 项目采用 AI 辅助开发，需要一套适合迭代的工作流，而非传统瀑布式开发。

**决策：** 采用 Plan → Execute → Result Validation → Replan 循环。设计/计划文件不适用的内容直接删除（Git 追溯），任务被废弃时标 ⛔ 并追加替代任务。

**理由：**
- 验证结果可能推翻原有假设，计划需要随时调整
- 直接删除保持文档干净，Git 负责历史
- 任务标 ⛔ 而非删除，保留决策轨迹

**曾考虑的替代方案：**
- 传统瀑布（先完整设计再开发）—— 不适合 AI 辅助的快速迭代
- 全部保留废弃内容（划线标记）—— 文档越来越臃肿

---

### 决策 7 — 编码时不写测试

**背景：** 项目处于早期快速迭代阶段，需求和设计频繁变化。

**决策：** 编写代码时不同步编写测试文件，除非用户显式要求。

**理由：** 早期阶段设计频繁变化，测试维护成本高。待接口和设计稳定后再考虑测试。

**曾考虑的替代方案：**
- TDD（测试驱动开发）—— 早期阶段不适合，需求变化导致测试反复重写
- 每个模块写完补测试 —— 拖慢迭代速度

---

### 决策 8 — CLI 方案：input() + $EDITOR + rich

**背景：** 需要选择 CLI 交互方案，项目是对话式 AI 助手，非命令行工具。

**决策：** 日常对话使用 `input()`，长文本输入（JD、简历、面试回答）弹出 `$EDITOR` 编辑临时文件，Markdown 输出用 `rich` 渲染。

**理由：**
- 对话式交互不需要 click 的命令行参数解析
- `$EDITOR` 临时文件解决 `input()` 不支持多行输入的问题
- `rich` 仅用于输出美化，轻量且够用

**曾考虑的替代方案：**
- `click` —— 适合命令行多子命令工具，对话式 AI 用不上
- `prompt_toolkit` —— 提供输入历史和自动补全，但对当前需求过度

---

### 决策 9 — 包管理：uv + SJTU 镜像

**背景：** 需要选择 Python 项目的包管理和虚拟环境方案。

**决策：** 使用 `uv` 管理依赖和运行（`uv add` / `uv remove` / `uv sync` / `uv run`），PyPI 镜像配置在上海交大 SJTUG 镜像站（`https://mirrors.sjtug.sjtu.edu.cn/pypi/web/simple`），在 `pyproject.toml` 中通过 `[[tool.uv.index]]` 持久化配置。

**理由：**
- `uv` 是当前最快的 Python 包管理器（Rust 实现），下载和解析速度远超 pip/Poetry
- `uv run` 统一了"在项目 venv 中执行命令"的入口，避免激活虚拟环境的混乱
- 国内镜像大幅提升下载速度（从 550KB/s → 25MB/s）
- `pyproject.toml` 持久化镜像配置，团队共享无需各自配置

**曾考虑的替代方案：**
- Poetry —— 功能完善但比 uv 慢一个数量级，且 `poetry run` 不如 `uv run` 简洁
- pip + venv —— 需要手动管理虚拟环境，`uv` 自动处理
- 清华 TUNA 镜像 / 中科大镜像 —— 均可替代，速度接近

---

### 决策 10 — LLM 后端：OpenAI SDK + 双 tier 封装

**背景：** 项目需要 LLM 调用能力，需要选择 SDK 和封装方式。

**决策：**
- 使用 `openai` 包（OpenAI SDK），兼容所有 OpenAI-compatible 后端（如 vLLM、Ollama、DeepSeek 等）
- 封装为双 tier：`chat_pro()`（高能力，默认 `gpt-4o`）和 `chat_flash()`（快速，默认 `gpt-4o-mini`）
- 通过 4 个环境变量注入配置：`OPENAI_BASE_URL`、`OPENAI_API_KEY`、`LLM_PRO_MODEL`、`LLM_FLASH_MODEL`
- `python-dotenv` 在应用启动时加载 `.env`
- 调用逻辑封装在 `src/agents/base.py` 中，子 Agent 调用 `self._llm_pro()` / `self._llm_flash()`，不传 model 名

**理由：**
- OpenAI SDK 是事实标准，生态兼容性最广，换后端只改环境变量不动代码
- 双 tier 覆盖两种场景：深度推理（简历分析、面试评估）用 pro，轻量任务（意图分类、格式化）用 flash
- model 名不暴露给 Agent —— 具体模型由运维决定，Agent 只关心能力等级
- 不做 fallback —— 保持简单，错误直接抛出到 CLI 前端

**曾考虑的替代方案：**
- 直接使用 Anthropic SDK —— 仅支持 Claude，不如 OpenAI-compatible 生态广
- 多 provider 适配层 —— 过度设计，OpenAI-compatible 协议已足够通用
- 硬编码 model 名 —— 换模型需要改代码

---

### 决策 11 — Jupyter 交互式调试工作流

**背景：** 开发阶段需要快速验证局部函数（如 RAG embedding、Chunker 逻辑），直接跑完整 CLI 链路太重。

**决策：** 使用 `uv run --with jupyter jupyter lab` 启动 Jupyter Notebook 做交互式验证，`jupyter` 不写入项目依赖。

**理由：**
- `uv run` 确保 notebook 在项目 venv 中运行，能 import 项目代码
- `--with jupyter` 临时注入不污染 `pyproject.toml`
- 交互式环境适合调试局部逻辑，改一行跑一行，不需要每次从头启动 CLI

**曾考虑的替代方案：**
- 单元测试 —— early阶段接口不稳定，测试维护成本高（决策 7 已有约束）
- `python -i` 交互式解释器 —— 功能弱，不支持富文本和代码块

---

### 决策 12 — 集中式环境变量管理（config.py 模块）

**背景：** 各模块各自调用 `os.environ` 读取环境变量，散落各处不利于维护和启动校验。

**决策：** 新增 `src/config.py` 模块集中管理所有环境变量。启动时调用 `load_dotenv()` 加载 `.env`，逐一校验必填变量，缺失时打印清单并 `sys.exit(1)`。其他模块（LLM、CLI 等）通过 `from src.config import config` 获取配置值，禁止直接调用 `os.environ`。

**理由：**
- 启动时一次性校验，不会因环境变量缺失而在运行时中途崩溃
- 换变量名只改 `config.py` 一处，风险远低于全局 grep 替换
- 模块级单例，`import` 即加载，零侵入
- 缺失时打印清晰清单，用户一眼知道缺什么

**曾考虑的替代方案：**
- 各模块各自校验 —— 校验逻辑散落，可能遗漏，错误信息不一致
- 使用 `pydantic-settings` —— 功能完善但引入额外依赖，当前 4 个变量不需要

---

### 决策 13 — LLM 参数分层管理

**背景：** LLM 调用需要支持 temperature、top_p、response_format 等参数，不同 Agent 需要不同的默认值，同时调用方需要能临时覆盖。

**决策：**
- `LLMClient.chat_pro()` / `chat_flash()` 通过 `**kwargs` 透传所有额外参数给 OpenAI SDK，不预设也不拦截任何参数
- `BaseAgent` 提供 `_pro_params` / `_flash_params` 类属性（dict），子 Agent 按需覆盖声明自己的默认值
- `BaseAgent._llm_pro()` / `_llm_flash()` 合并类默认值 + 调用时覆盖：`{**self._pro_params, **kwargs}`
- 需要精细控制时，直接通过 `LLMClient.client`（暴露底层 `openai.OpenAI` 实例）走原生 SDK

**理由：**
- `LLMClient` 保持薄管道角色，不关心调用方是谁、传了什么参数
- 参数默认值声明在子 Agent 类定义处，一目了然，不用翻调用代码
- 分层清晰：`LLMClient` 管 API 连接，`BaseAgent` 管参数合并，子 Agent 管具体值
- 暴露底层 client 让高级用户不被封装限制

**曾考虑的替代方案：**
- 在 `LLMClient` 中硬编码 temperature 等参数 —— 不同 Agent 需求不同，耦合
- 每个子 Agent 各自拼 `**kwargs` 传参 —— 参数散落各处，缺乏统一入口

---

### 决策 14 — Agent 无专属模板文件

**背景：** 提示词模块设计初期讨论了两种组织方式：每个 Agent 各有一组专属模板文件，还是所有 Agent 共用一套模板文件、差异由占位符值体现。

**决策：**
- 所有 Agent 共用 `general_agent/` 下 7 个模板文件，不允许 Agent 拥有自己的模板文件
- Agent 之间的差异完全由 14 个 per-Agent 占位符填充值体现（清单见 `data/prompts/PLACEHOLDER.md`）
- `PromptLoader.get(**variables)` 加载时拼接通用模板 + 替换占位符，`**variables` 的键值对由各 Agent 提供

**理由：**
- 共用模板确保所有 Agent 遵守统一的角色框架、安全约束和输出格式，不会因各自编写而出现遗漏或不一致
- 占位符系统提供了足够的差异化空间（身份、目标、约束、工具、风格五个维度）
- 模板文件数量可控（固定 7 个），新增 Agent 不需要新增模板文件

**曾考虑的替代方案：**
- 每个 Agent 各自管理完整提示词 —— 公共约束变更时需要改 N 处，容易遗漏
- Agent 专属模板文件覆盖公共模板 —— 复杂度高，Agent 可能绕过核心安全策略

---

### 决策 15 — 编排工具化而非提示词化

**背景：** 主 Agent 调度子 Agent 的方式有两种选择：在提示词中描述调度规则，或将调度定义为工具调用。

**决策：**
- 不在提示词中写"当用户说 X 时调用 Y Agent"
- 调度子 Agent 定义为工具（如 `dispatch_resume`、`dispatch_interview`），通过 `{{ADDITION_TOOLS}}` 占位符注入主 Agent 的工具列表
- LLM 通过标准工具选择流程（`04_tools.md` + `06_output_format.md`）完成意图识别和调度

**理由：**
- 工具化调度利用 LLM 原生的 function calling 能力，无需在提示词中维护调度规则
- 新增或移除子 Agent 只需增删工具定义，不改提示词
- 与输出格式（JSON + action.tool）一致，LLM 的工具选择和调度是同一套流程

**曾考虑的替代方案：**
- 在提示词中枚举调度规则 —— 调度逻辑耦合在文本中，变更需要改提示词，且长提示词降低 LLM 遵从度
- 独立的意图路由模块（规则匹配 / 分类器）—— 增加维护成本，且不如 LLM 灵活

---

### 决策 16 — JSON 输出解析留待 M4

**背景：** `06_output_format.md` 已定义结构化 JSON 输出 schema（`thinking` + `action`），M1 阶段的 `LLMHandler` 面临选择：立即实现 JSON 解析，还是透传原始回复。

**决策：**
- M1 阶段不做 JSON 解析，`LLMHandler` 将 LLM 原始回复直接返回给 CLI
- JSON 解析（`json.loads` → 提取 `action.message` → 识别 `action.tool` → agent loop）留到 M4 由 Orchestrator 实现
- M1 裸 JSON 输出不影响端到端验证目的

**理由：**
- JSON 解析逻辑属于 Agent 编排层（Orchestrator），不属于 M1 基础设施验证范畴
- 提前实现需要在 `LLMHandler` 中引入 Agent loop 逻辑（工具分发、多轮对话状态机），跨到了 M4 的边界
- M1 目标是验证 config → LLM → prompts → CLI 管线，裸 JSON 输出已足够验证

**曾考虑的替代方案：**
- 在 M1 立即解析 JSON —— 需要在 Handler 中实现半个 agent loop，边界模糊，且 M4 时会被 Orchestrator 替换，额外工作量无积累价值
- 临时移除 `06_output_format.md` 中的 JSON 约束 —— 不需要，LLM 输出裸 JSON 不影响测试目的

---

### 决策 17 — RAG 双 Collection + 统一分隔符

**背景：** M2 阶段设计 RAG 数据存储方案，需要确定 collection 划分策略、分隔符约定、以及参考数据的组织方式。

**决策：**
- 两个 collection：`references`（参考数据）+ `memories`（记忆），不按数据类型拆细
- 统一使用 Markdown 水平线 `---` 作为条目边界，记忆和参考数据共用同一套切分规则
- 参考数据的 category 由子目录名自动提取（`data/reference/<category>/` → `{"category": "<category>"}`），不维护独立配置文件
- 默认全库检索，Reranker 自然排序；调用方可传 `filter={"category": "knowledge_base"}` 限定范围
- 不需要 index.md 或 router 做前置分类

**理由：**
- 两个 collection 足够覆盖所有场景，更多 collection 增加跨 collection 合并排序的复杂度，收益有限
- `---` 是 Markdown 原生语法，人和 LLM 写起来自然
- 子目录名即 category，零维护，新增数据类型只需新建目录
- 全库检索 + Reranker 排序已经够准，前置路由是过度设计

**曾考虑的替代方案：**
- 每种参考数据一个 collection —— 跨 collection 检索需要合并排序
- 维护 index.md 做两级检索 —— 增加维护负担且不必要
- `<!-- chunk -->` 做分隔符 —— 语义明确但输入繁琐

---

### 决策 18 — RAG 模型选型

**背景：** RAG 模块需要 bi-encoder（召回）和 cross-encoder（重排），需选定具体模型并做成可配置。

**决策：**
- Bi-encoder：`BAAI/bge-base-zh-v1.5`（中文优化，召回速度快）
- Cross-encoder：`BAAI/bge-reranker-v2-m3`（精排准确率高）
- 模型名通过环境变量 `BI_ENCODER_MODEL` / `CROSS_ENCODER_MODEL` 配置，带默认值
- 若 cross-encoder 性能不足可降级为 `BAAI/bge-reranker-base`（仅记录备选，不做在代码中）

**理由：**
- BGE 系列是国内中文语义检索事实标准，社区验证充分
- 环境变量配置支持不同环境灵活切换
- `bge-reranker-v2-m3` 是 v2 系列最强模型，本地推理慢时可降级 base

**曾考虑的替代方案：**
- `all-MiniLM-L6-v2` —— 英文优化，中文效果差
- OpenAI Embeddings API —— 需网络、有成本、不可离线

---

### 决策 19 — RagLoader 后台加载与降级

**背景：** 参考数据和记忆的文件数量可能较多，启动时同步加载会阻塞 CLI。需要设计加载机制。

**决策：**
- 新增 `src/rag/loader.py`（RagLoader），负责遍历磁盘 → Chunker → ChromaStore
- `auto_load()` 使用 `threading.Thread` 后台执行，不阻塞主线程
- 暴露 `is_ready()` 供调用方判断；RAG 未就绪时对话走纯 LLM 降级
- `load_file(path)` 支持增量加载：按 `source_file` 删旧 chunk 后重新入库
- Collection 不预建，ChromaStore 首次 `add()` 时自动创建

**理由：**
- `threading` 而非 `asyncio`，与项目同步代码约定一致（决策 2）
- 后台加载保证 CLI 秒级可交互
- `is_ready()` 降级机制简单可靠
- 增量加载支持热更新（新增面试题、Agent 写入记忆后即时入库）

**曾考虑的替代方案：**
- 同步加载 —— 启动慢，数据量大时不可接受
- 启动时预建 collection —— Chroma 首次写入自动创建，预建无额外收益
- 全量重载 —— 改一个文件就要全部重新加载

---

### 决策 20 — Embedder/Reranker 模型分离 + batch_size 环境变量化

**背景：** 设计初期将 bi-encoder 和 cross-encoder 都放在 Embedder 中，由 Reranker 复用 Embedder 的 cross-encoder 模型。实现阶段发现两个模型职责不同、调用方不同，耦合不必要。

**决策：**
- Embedder 只持有 bi-encoder（`SentenceTransformer`），只提供 `embed(texts)` 向量化方法
- Reranker 独立加载 cross-encoder（`CrossEncoder`），不依赖 Embedder
- `batch_size` 通过环境变量 `EMBED_BATCH_SIZE` 配置（默认 32），`embed()` 作为可选参数

**理由：**
- 单一职责：Embedder 就是文本 → 向量，不关心评分逻辑
- 独立加载避免模块间不必要的耦合
- 环境变量配置支持不同硬件灵活调整，无需改代码

**曾考虑的替代方案：**
- Embedder 同时持有两个模型 → 职责冗余
- batch_size 硬编码 → GPU/CPU 差异大

---

### 决策 21 — HF_ENDPOINT 镜像配置

**背景：** 国内访问 HuggingFace Hub 经常超时，`sentence_transformers` 首次加载需下载数百 MB 权重文件。

**决策：**
- 新增 `HF_ENDPOINT` 环境变量，默认值 `https://hf-mirror.com`（国内镜像）
- `load_dotenv()` 自动注入 `os.environ`，`sentence_transformers` 底层自动读取，零代码改动

**理由：**
- 国内用户开箱即用，海外用户可覆盖为官方地址
- 不侵入代码，完全由环境变量控制

**曾考虑的替代方案：**
- 不做处理 —— 国内用户首次加载必然失败

---

### 决策 22 — /ragreload 手动重载命令（📌 暂缓，未实现）

**背景：** RAG 后台加载可能因模型下载失败而无法就绪，用户需要在不重启程序的情况下重新触发加载。

**决策：**
- 新增 CLI 命令 `/ragreload`，手动重新触发 `auto_load()`
- 当前阶段不实现（标记为 📌 暂缓），M2 末尾或 M3 再做
- RagLoader 内部 catch 异常，加载失败时 `_ready` 保持 False，对话自动降级纯 LLM

**理由：**
- 模型下载成功后一条命令恢复 RAG，无需退出程序
- 与 `is_ready()` 降级机制互补

**曾考虑的替代方案：**
- 自动重试 —— 可能反复失败浪费资源
- 要求重启程序 —— 体验差

---

### 决策 23 — ChromaStore 内部设计决策

**背景：** ChromaStore 作为 Chroma 的封装层，需要确定 Embedder 依赖方式、数据存储格式、线程安全策略、距离度量、collection 校验、持久化切换等内部设计。

**决策：**

- **Embedder 内部创建**：Store 在 `__init__` 直接 `Embedder()`，不接受构造函数注入。未来切换 API 后端时在 Embedder 内部通过环境变量控制，Store 不动
- **原始文本存入 Chroma**：`add()` 时使用 Chroma 的 `documents` 参数存储原文，`query()` 返回 `list[Chunk]`（直接从 Chroma 结果还原 content）
- **filter 直接透传**：`query()` 的 where filter dict 透传给 Chroma，不做封装（Chroma 语法是 MongoDB 子集）
- **不加锁**：`auto_load()` 期间 `is_ready()` 为 False，查询走纯 LLM 降级；`load_file()` 增量更新为单文件操作，耗时极短
- **距离度量用默认 L2**：Embedder 已输出归一化向量，L2 与 cosine 排序结果数学上等价，无需显式设置 `hnsw:space`
- **不校验 collection 名**：信任调用方传对 `"references"` 或 `"memories"`
- **持久化通过环境变量切换**：设置 `CHROMA_PERSIST_DIR` → `PersistentClient(path)`，不设置 → `Client()`（内存模式）。持久化目录 `data/chroma/` 加入 `.gitignore`

**理由：**

- 内部创建 Embedder 保持调用方零配置，同时 Embedder 接口 `embed(texts) -> list[list[float]]` 足够通用，后端切换不影响 Store
- `documents` 字段是 Chroma 原生能力，存原文避免 query 后回源读文件
- filter 透传零学习成本，Chroma 语法与 MongoDB 一致
- 线程安全简化：运行时自然隔离，无需引入锁复杂度
- L2 等价性由数学保证，无需额外配置
- collection 校验收益为零（调用方只有 Loader 和 MemoryStore，均编写时已知）

**曾考虑的替代方案：**

- 构造函数注入 Embedder —— 当前只有一个使用方，注入无收益
- content 塞入 metadata —— 污染 metadata，Chroma 原生 `documents` 字段更合适
- filter 封装一层 —— 增加学习成本，Chrom 语法已标准
- 加锁 —— 当前访问模式天然隔离，加锁是过度设计
- 显式设置 `hnsw:space=cosine` —— 归一化向量下与 L2 等价

---

### 决策 24 — RAG 增量加载与文件同步策略

**背景：** 持久化模式下，重启后需要判断哪些文件已变更，避免对未变化的文件重复做 embedding。同时，运行时文件的增删需要与 Chroma 保持同步。

**决策：**

- **时间戳增量加载**：持久化模式下，`auto_load()` 读取 `data/chroma/.last_update` 时间戳（不存在 → epoch 0），扫描 `data/reference/` 和 `data/memories/`，收集 mtime > 时间戳的文件，对每个变化的文件执行 `remove(source_file)` → `chunk` → `add`，最后写入当前时间戳
- **用户手动删除磁盘文件**：不管，不清理 Chroma 中的孤儿 chunk
- **Agent 程序化操作**：删除文件时统一封装，同步清理 Chroma 对应数据；写入记忆时走统一路径（写文件 → Chunker → ChromaStore.add()），确保文件与 Chroma 一致
- 封装逻辑在 Memory 模块实现时处理，Store 只提供 `add()` / `remove()` / `query()` 基础接口

**理由：**

- 时间戳比对 O(n) 扫描足够简单，无需维护文件 hash 或变更日志
- 用户手动删除属于外部操作，清理孤儿 chunk 需要全量比对（拿 Chroma 所有 source_file 去磁盘检查），成本高收益低
- Agent 程序化操作统一封装，避免各处重复 delete+add 逻辑
- 职责分层：Store 提供原子操作，Memory 模块负责一致性封装

**曾考虑的替代方案：**

- 全量删重建 —— 每次都重新 embedding，持久化优势浪费
- 文件 hash 比对 —— 精准但复杂度高，当前文件数量少时无必要
- 在 Store 中实现文件操作封装 —— Store 只管 Chroma，文件操作不是其职责
- 监听文件系统事件（watchdog）—— 引入额外依赖，过度设计

---

### 决策 25 — Reranker 设计决策

**背景：** Reranker 独立加载 cross-encoder 对召回结果精排，需确定分数传递方式、批处理配置、预热策略和异常处理。

**决策：**

- **分数存入 `metadata["rerank_score"]`**：Reranker 不修改 Chunk 结构，在现有 `metadata: dict` 中注入浮点数分数，结果按分数从高到低排列
- **批处理大小环境变量化**：新增 `RERANK_BATCH_SIZE` 环境变量（默认值 32），控制 `CrossEncoder.predict()` 每次传入多少对 (query, document)
- **Top-K 环境变量化**：新增 `RERANK_TOP_K` 环境变量（默认值 5），控制重排后保留条数
- **`__init__` 时预热**：加载模型后用一对假数据 `[("预热", "预热")]` 跑一次 `predict()`，避免首次真实调用卡顿
- **异常直接抛出**：模型加载失败或 predict 异常不吞，抛给调用方。调用方（检索链路）try/except 后降级，用 ChromaStore 原始召回结果

**理由：**

- dict 注入分数改 metadata 不动 Chunk 字段，最小侵入
- 批处理和 top-k 环境变量化延续 Embedder 风格（决策 20），不同硬件灵活调整
- 预热收益明显（首次调用从 2-3s 降至 100ms），一行代码换取流畅用户体验
- Reranker 不做降级逻辑：降级是调用方（检索链路）的调度职责，Reranker 只管评分

**曾考虑的替代方案：**

- 在 Chunk 上加 `score` 字段 —— 改动数据结构，只有 Reranker 使用，放入 metadata 更合适
- top-k 硬编码 5 —— 不同场景（面试题 vs JD 匹配）可能需要不同数量
- 不预热 —— 每次启动后第一次检索体验差
- Reranker 内部 try/except 返回原结果 —— 调用方不知道重排失败了，反而被当作正常结果使用

---

### 决策 26 — ChromaStore 统一检索入口（移除 Retriever）

**背景：** 为实现阶段发现 `ChromaStore.__init__` 和 `Retriever.__init__` 各自创建 `Embedder` 实例，导致 bi-encoder 模型被加载两次（内存翻倍 + 加载时间翻倍）。追溯设计发现一旦 `ChromaStore.query()` 改为接受文本、内部向量化，`Retriever` 的职责退化为一层透传调用：`retrieve(query) { return store.query(query) }`。

**决策：**
- 移除 `src/rag/retriever.py`（不创建该文件）
- `ChromaStore.query()` 改为接受查询文本（`query_text: str`），内部调 `self._embedder.embed()` 向量化后检索
- 检索流程从 `Embedder.embed() → Retriever → Store.query()` 简化为 `Store.query(query_text)`
- Reranker 仍独立存在，在 Store 召回后做精排

**理由：**
- 消除双 Embedder 实例，bi-encoder 模型只加载一次（ChromaStore 内部持有）
- Retriever 成为纯粹的透传层，无独立存在价值
- 调用方更简洁：`store.query("排序算法")` 而非先创建 Embedder 再传向量
- RAG 模块从 6 个文件减为 5 个，职责边界更清晰

**曾考虑的替代方案：**
- Embedder 做成单例 —— 治标，Retriever 本身仍是透传层
- ChromaStore 暴露 embedder —— 增加耦合，不如内部消化

---

### 决策 27 — RagLoader 设计决策

**背景：** Loader 是 RAG 数据的唯一入口，需要管理加载状态以支持降级机制。Store 和 Reranker 需保持单例，Loader 如何获取这些实例影响整体耦合。

**决策：**

- **Store/Reranker 构造函数注入，不做内部创建**：`RagLoader(store: ChromaStore, reranker: Reranker)`。单例由 `src/rag/__init__.py` 模块级懒加载管理
- **Chunker 内部创建**：无状态，不需要注入
- **状态机管理加载状态**：`LoaderState` 枚举（IDLE / LOADING / READY / ERROR），通过 `state` 属性和 `error` 属性暴露
- **同步 + 锁保证串行**：`auto_load()` 和 `load_file()` 均为同步方法，用 `threading.Lock` 保护。LOADING 状态下拒绝新请求
- **异常不抛出，写入状态**：加载失败时 `state = ERROR` + `error_msg = str(e)`，由用户/调用方根据状态决策重试或降级
- **内存模式全量，持久化模式增量**：内存每次全量加载；持久化通过 `.last_update` 时间戳比对 mtime 做增量
- **memories 目录为空不处理**：不创建空 collection，等记忆模块实际写入后 `load_file()` 增量入库

**理由：**

- 注入优于内部创建：避免在 Loader 内部重复构建 Store/Reranker 实例，既保持单例又符合依赖反转原则
- 状态机替代简单的 `is_ready() bool`：调用方需要区分 "还在加载" vs "加载失败"，前者需等待后者需用户介入
- Loader 本身不开线程：同步 + 锁，调用方如需异步自己开 thread，保持职责单一
- 异常写入状态而非抛出：LOADER 被多处调用，抛异常意味着每个调用方都要处理，状态机统一管理

**曾考虑的替代方案：**

- Loader 内部创建 Store/Reranker —— 多实例问题
- `auto_load_async()` 内部开线程 —— 增加 Loader 复杂度，异步包装应是调用方职责
- `is_ready() + is_error()` 两个方法 —— 不如单一 state 枚举清晰
- 异常直接抛给调用方 —— 每个调用点都要 try/except，不如状态统一

---

### 决策 28 — RAG 公共 API 极简化

**背景：** `src/rag/__init__.py` 最初暴露了 `get_store()`、`get_reranker()`、`get_loader()` 三个 getter，调用方需要手动拼接 `store.query()` → `reranker.rerank()` 流程。外部只需两件事：检索和重载。

**决策：**

- `src/rag/__init__.py` 仅暴露三个公共函数：`search(query_text, collection, top_k)`、`load(target)`、`is_ready()`
- `search()` 内部串联 `store.query()` → `reranker.rerank()`，LOADING/ERROR 状态时抛出 `RuntimeError`
- `load(target=None)` 透传 `loader.reload(target)`：None 全量重载，非空匹配路径重载
- `is_ready()` 返回 `loader.state == LoaderState.READY`，供外部轮询
- `ChromaStore` 和 `Reranker` 完全隐藏在模块内部，外部不可见

**理由：**

- 外部调用方不需要知道 Store/Reranker 的存在，只需"给我结果"
- `search()` 在 LOADING/ERROR 时抛异常，语义清晰，调用方自然选择 try/except 或 `is_ready()` 轮询
- 2+1 个函数构成完整公共 API，学习成本为零
- 内部单例管理、双检锁、daemon 线程等复杂度对外透明

**曾考虑的替代方案：**

- 暴露 `get_store()` + `get_reranker()` —— 调用方需理解内部 pipeline，增加使用成本
- `search()` 在 LOADING 时阻塞等待而非抛异常 —— 阻塞时长不可控，不如让调用方决定何时重试

---

### 决策 29 — MemoryStore 与 RAG 解耦（观察者模式）

**背景：** 原设计 MemoryStore 直接持有 RAG 内部组件（Chunker、ChromaStore、Reranker）的引用，`write_memory()` 和 `query_cross_agent()` 内部直接调 RAG。这导致 Memory 模块与 RAG 内部实现细节强耦合，换 RAG 底层就得改 MemoryStore。

**决策：**
- MemoryStore 只管文件系统读写，不持有任何 RAG 引用
- 解耦方式为观察者模式：Store 写文件后发射 `MemoryWritten` / `MemoryDeleted` 事件
- `MemoryIndexer` 监听事件→调用 RAG 公共 API（`rag.load()` / `rag.delete()`）
- `MemoryRetriever` 封装 RAG `search()`，返回 Memory 对象
- Store 通过 `on_write(callback)` / `on_delete(callback)` 注册监听器，callback 同步执行

**理由：**
- Store 不再知道 RAG 的存在，换 RAG 实现只需改 Indexer
- 事件驱动解耦，写入路径（Store→Indexer→RAG）和读取路径（Retriever→RAG）完全独立
- 不需要引入消息队列或异步框架，Python 原生 callback 足够

**曾考虑的替代方案：**
- Store 依赖 RAG 公共 API 而非内部组件 —— 耦合方向反了，RAG 是基础设施，Memory 是上层
- 全异步消息队列 —— 过度设计，当前规模不需要

---

### 决策 30 — 一文件一条记忆 + front-matter KV 格式

**背景：** 原设计 `data/memories/<agent>/<date>.md` 一个文件包含多条记忆，Chunker 按 `---` 切分为多个 Chunk。这导致记忆之间边界模糊，增删改单条记忆需要操作整文件，且 metadata（id、agent、time）无法持久化到文件中。

**决策：**
- **一条 Memory 一个文件：** `data/memories/<agent>/<yyyyMMddHHmmss.fff>.md`，文件名即时间戳，天然有序
- **Front-matter KV 格式：** 文件以 `---` 包裹的 KV 开头（`id`、`agent`、`time`），后接正文 content
- **所有文件统一格式：** reference 文件同样加 front-matter（`category`），Chunker 自动解析注入 metadata
- **`file_path` 可从 `memory.time` 推导：** 不存储在 Memory 对象中

**理由：**
- 一文件一条：`source_file` 天然是单条记忆标识，增删精确到文件级别
- Front-matter 持久化 metadata：`/ragreload` 全量重载时不丢
- 时间戳文件名：天然有序，浏览记忆时一目了然
- 所有文件统一格式：一套 Chunker 处理 reference 和 memory

**曾考虑的替代方案：**
- 按日期文件存多条记忆 —— 增删需要改整文件，Chunk 粒度与文件粒度不一致
- JSON 文件 —— 不如 Markdown 人机可读
- 文件名用 uuid —— 排序混乱，人工无法浏览

---

### 决策 31 — Chunker 通用化 + front-matter 解析

**背景：** Chunker 原是 RAG 模块专属（`src/rag/chunker.py`），仅做 `---` 机械切分。M3 的 MemoryBuilder 也需要用 Chunker 解析 LLM 输出的 Markdown，同时所有文件需要 front-matter 支持以持久化 metadata。

**决策：**
- Chunker 从 `src/rag/` 移至 `src/utils/chunker.py`，成为通用工具
- `chunk()` 新增 front-matter 解析：文件开头第一对 `---` 提取 KV → metadata 注入所有 Chunk → 剥离 front-matter → 后续 `---` 正常切分
- metadata 优先级：front-matter KV < chunk() 的 metadata 参数（调用方可覆盖）
- `source_file` 仍由 RagLoader 自动注入，不写在 front-matter 中
- 解析用简单 `key: value` 格式，不用 YAML（避免额外依赖）

**理由：**
- 移至 utils 消除 memory→rag 的依赖方向问题
- front-matter 解析让 metadata 持久化在文件中，与程序注入互补
- 简单 KV 解析零依赖，足够覆盖 Memory（id/agent/time）和 Reference（category）的场景
- 调用方覆盖优先级保证灵活性

**曾考虑的替代方案：**
- Chunker 留在 RAG —— MemoryBuilder 需要依赖 RAG，耦合方向不合理
- 用 YAML front-matter —— 需要 `pyyaml` 依赖，当前需求不必要
- 不改 Chunker，由 RagLoader/MemoryStore 各自解析 front-matter —— 重复逻辑

**实施细化（2026-07-01）：**
- `chunk()` 返回值从空列表变为 front-matter 强制要求：无 front-matter 的输入返回 `[]`，在调用处留 TODO 桩供未来扩展（如纯文本自动注入默认 metadata）
- 实现方式：编译正则 `_FM_RE` 匹配 `^---...---`，解析失败 → 返回 `[]`；成功 → `{**fm_meta, **caller_meta}` 合并（caller 覆盖）

---

### 决策 32 — MemoryBuilder 替代 Compressor（对话构建而非压缩）

**背景：** 原设计 `MemoryCompressor.compress(conversation) -> list[Memory]` 定义为"LLM 对话压缩成记忆"，但这个名字暗示只是压缩/摘要，而不是主动从对话中提取关键信息构建记忆。

**决策：**
- 重命名为 `MemoryBuilder`，职责定义为"从对话中提取/构建记忆条目"
- 系统提示词放在 `data/prompts/memory/builder.md`（替代已删除的 `memory_compressor.md`）
- LLM 输出 Markdown 格式（`---` 分隔 + front-matter），Builder 注入 `id`/`time`/`agent` 后复用 Chunker 解析
- `memory/__init__.py` 提供 Facade：`build_memories(conversation, agent, llm, store, sync_mode=False)`
- `sync_mode=True` 同步返回 `list[Memory]`；`False` 后台线程执行，立即返回 `None`
- 异步控制在 Builder Facade，MemoryStore 本身纯同步

**理由：**
- "构建"比"压缩"更准确 —— LLM 主动判断什么值得记住并组织为 Memory，而非机械压缩
- LLM 输出与 memory 文件同格式，一套 Chunker 两端复用
- 异步由上层控制，Store 保持简单同步

**曾考虑的替代方案：**
- 保持 Compressor 名字 —— 名不副实，压缩暗示降维/摘要而非提取
- LLM 输出 JSON —— Markdown 更自然，且与文件格式统一
- MemoryStore 内部做异步队列 —— 职责混淆，Builder 是更好的异步控制点

---

### 决策 33 — 日志系统：标准库 logging + 按大小轮转

**背景：** 项目当前没有任何日志系统，调试依赖 `print()` 或异常堆栈。M3 记忆模块即将开始实现，MemoryStore 任务清单中已写明"失败仅记日志，不抛异常"，需要一个统一的日志基础设施。

**决策：**
- 使用 Python 标准库 `logging`，零额外依赖
- 提供 `get_logger(name: str) -> logging.Logger` 单一入口，懒加载初始化（首次调用自动配置 handler）
- 文件输出使用 `RotatingFileHandler`，按大小轮转（10MB × 5 备份），写入 `data/logs/app.log`
- 控制台输出使用 `StreamHandler(stderr, ERROR+)`，不干扰 `rich` 的 stdout 渲染
- 2 个环境变量：`LOG_LEVEL`（默认 `INFO`）、`LOG_DIR`（默认 `data/logs/`）
- 日志格式：`2026-07-01 14:30:00 | INFO     | memory.store | 写入记忆成功`

**理由：**
- 标准库足够 —— 项目是命令行工具，不是分布式系统，不需要 ELK/Sentry 等外部日志平台
- 按大小轮转比按天轮转更适合 CLI 应用 —— 使用频率不均，按天可能在某次密集使用中产生超大文件
- stderr 而非 stdout —— `rich` 接管 stdout 做 Markdown 渲染，日志写 stdout 会破坏终端输出
- 懒加载 —— 不强制在 `main.py` 显式初始化，任意模块 `get_logger(__name__)` 即开即用
- 环境变量控制级别和路径 —— 开发期设 `DEBUG` 看详细日志，正式使用设 `WARNING` 减少噪音

**曾考虑的替代方案：**
- `print()` 到 stderr —— 无级别过滤、无轮转、无时间戳，不可维护
- `loguru` —— 功能强大但引入额外依赖，当前需求标准库完全覆盖
- `TimedRotatingFileHandler` 按天轮转 —— CLI 应用使用频率不均，按大小更可预测
- 仅在 `main.py` 初始化 root logger —— 强依赖启动顺序，`get_logger()` 调用在 import 阶段就会执行，此时 root 可能尚未配置

---

### 决策 34 — Message 通用消息模型：7 字段 + 模块分离

**背景：** M3 任务 2 最初规格 Message 仅有 3 个字段（`role`/`content`/`timestamp`）。讨论后发现 Message 需要承载更多语义：用户输入、系统指令、工具调用、工具结果、LLM 回复，以及 LLM 内部推理过程。同时 `06_output_format.md` 的 JSON Schema（`thinking` + `action`）需要映射到统一的消息模型。

**决策：**

- **Message 7 字段：** `id`（uuid hex）、`timestamp`（datetime）、`role`（user/assistant/system）、`message`（展示文本）、`event_type`（事件类型标识）、`event_payload`（dict | None）、`thinking`（str | None）
- **`event_type` 区分消息语义：** 候选值包括 `user_input`、`system_input`、`tool_call`、`tool_call_result`、`finish` 等，后续随工具扩展追加
- **`role` 保留：** `event_type` 不能替代 `role` 做消息来源控制。例如 `tool_call_result` 和 `system_input` 都是 `role="system"`，需靠 `event_type` 区分语义
- **`message` 为展示文本：** 始终是终端显示内容，与 `action.message` 语义一致
- **`thinking` 为 LLM 推理：** 对齐 `06_output_format.md` Schema 顶层 `"thinking"`；user 消息恒为 `None`；未来由 `SHOW_THINKING` flag 控制展示（当前不做）
- **模块位置：** Message 抽出为 `src/message.py`，作为项目级通用基础设施，而非放在 `src/memory/schemas.py` 中

**理由：**

- Message 是整个系统的数据总线（CLI → Agent → LLM → Memory），放在 memory 下会造成其他模块反向依赖 memory
- `role` + `event_type` 双层语义：role 回答"谁发的"，event_type 回答"这是什么类型的消息"，职责不重叠
- `thinking` 独立字段避免推理过程混入 `message` 污染展示
- `event_payload` 用 dict 足够灵活，不需要为每种工具定义具体 TypedDict

**曾考虑的替代方案：**

- Message 放在 `src/memory/schemas.py` —— CLI/LLM/Agent 都需要 import memory 模块，耦合方向不合理
- 用 `event_type` 替代 `role` —— 无法区分"系统指令"和"工具结果"的消息来源，消息路由时需额外判断
- `thinking` 混在 `message` 中 —— 展示时需要额外解析剥离，不干净
- `event_payload` 用具体 TypedDict 类型 —— 工具类型不断扩展，维护成本高

---

### 决策 35 — MemoryStore 格式化逻辑抽出到 utils/formatters.py

**背景：** 实现 `MemoryStore` 时，`write_memory()` 内部需要两个 pure 函数：将 `datetime` 转为 `yyyyMMddHHmmss.fff.md` 文件名、将 `Memory` 对象拼装为 front-matter Markdown。最初计划将这两个函数作为 `MemoryStore` 的 `@staticmethod`，但 static method 内聚性差，且这两个函数是通用工具，未来可能被 MemoryBuilder 或 Chunker 复用。

**决策：**
- 创建 `src/utils/formatters.py`，包含两个函数：`timestamp_to_filename(time: datetime) -> str` 和 `memory_to_markdown(agent: str, memory: Memory) -> str`
- `MemoryStore` 不持有格式化逻辑，直接 `from src.utils.formatters import ...` 调用
- 函数保持纯函数风格（无状态、无副作用），职责范围限定为格式化

**理由：**
- 格式化逻辑是通用工具，不属于 Store 的职责范围，抽出后 `src/utils/` 下 `chunker.py` + `formatters.py` 形成工具集
- Store 类更轻量，只关心文件读写和事件发射
- 纯函数天然可复用，MemoryBuilder 后续也可能用到

**曾考虑的替代方案：**
- 保留在 Store 作为 `@staticmethod` —— 不解决复用问题，且 static method 暴露为公共 API 容易误导调用方
- 内联写在 `write_memory()` 中 —— 方法过长，SRP 违规

### 决策 36 — Memory 类别重构：fact/preference 两分类 + builder 严格 JSON 输出

**背景：** 最初设计 Memory 输出为 `---` 分隔的自由 Markdown，Memory 无类别字段。用户重写 `data/prompts/memory/builder.md` 后，决定用结构化 JSON 输出替代自由 Markdown，并为 Memory 引入 `category` 分类。

**决策：**
- Memory 新增 `category: str` 字段，取值 `"fact"` 或 `"preference"`，默认 `"fact"`
- `builder.md` 输出严格 JSON：`{"facts": "<string>", "preferences": "<string>"}`，两个字段均为必填，无内容填空字符串
- 废弃原 4 分类设计（facts/preferences/entities/events），entities 和 events 合并入 facts
- LLM 每次调用最多产出 2 条 Memory（每字段非空生成一条）
- `memory_to_markdown()` front-matter 新增 `category`，`chunk_to_memory()` 从 metadata 提取（缺失默认 `"fact"`）
- Builder 不依赖 Chunker —— 直接 `json.loads()` 解析后构造 Memory 列表

**理由：**
- 两分类覆盖所有记忆场景：事实（客观、长期）和偏好（主观、程度）
- 严格 JSON 输出可控、可解析，比自由 Markdown + Chunker 更可靠
- 每次最多 2 条记忆，输出精简，LLM 不会过度提取
- front-matter 带 category 后，RAG 检索可按类别过滤 (`filter={"category": "preference"}`)

**曾考虑的替代方案：**
- 4 分类（facts/preferences/entities/events）—— entities 和 events 与 facts 边界模糊，增加 LLM 分类负担
- 数组输出 `{"facts": [], "preferences": []}` —— 不可控，LLM 可能生成过多条目
- 保留 `---` 分隔的自由 Markdown —— 解析脆弱，需依赖 Chunker，且无法区分类别

### 决策 37 — MemoryBuilder JSON 强制模式 + 换行拆分

**背景：** 实现了 `MemoryBuilder` 后，用户要求 LLM 输出强制 JSON 以确保格式可靠，同时要求每条简短陈述独立成为一条 Memory（而非整个 facts/preferences 字符串作为一条）。

**决策：**
- `build()` 调用 `chat_flash()` 时传入 `response_format={"type": "json_object"}`，OpenAI SDK 强制模型输出合法 JSON
- `json.loads()` 解析后，`facts` 和 `preferences` 字符串按 `\n` 拆分为多行，每行一条 Memory（过滤空行）
- Builder 不再依赖 Chunker —— 文本拆分逻辑内聚在 `build()` 中
- 每条 Memory 独立存储，独立检索

**理由：**
- `response_format` 比仅依赖提示词更可靠，消除非法 JSON 的风险
- 换行拆分符合新版 `builder.md` 的语义（每条一个简短陈述），`\n\n---\n\n` 拼接后由 Chunker 切分，每条独立 RAG 可检索
- flash tier 足够处理结构化提取，不需 pro tier

**曾考虑的替代方案：**
- 仅提示词约束 JSON 格式 —— 偶发非法 JSON，解析脆弱
- 整段 content 存为一条 Memory —— 粒度太粗，检索时无法精准定位单条事实/偏好
- 每行存为独立文件 —— 同时间戳文件名冲突，需 `category` 字段区分

### 决策 38 — 记忆模块统一入口 + 文件名 category + --- 分隔符

**背景：** 实现了 MemoryBuilder、MemoryIndexer、MemoryRetriever 后，需要统一的对外接口。同时发现同一 LLM 调用产出的 facts 和 preferences 共享时间戳导致文件名冲突，且每行独立存文件粒度太细。

**决策：**
- `src/memory/__init__.py` 作为唯一公开入口，暴露 `init()`、`build_memories()`、`search_memories()`、`delete_memory()` 四个函数
- 内部双检锁懒加载单例 MemoryStore / MemoryIndexer / MemoryRetriever（类 RAG 模块的 `_ensure_init` 模式）
- 文件名格式改为 `yyyyMMddHHmmss.fff.<category>.md`，不同 category 不冲突
- Builder 内部：LLM 返回的多行文本按 `\n` 拆分后，用 `\n\n---\n\n` 拼接为一个 content，一 category 一个文件
- Chunker 解析文件时剥离 front-matter 后按 `---` 切分，每条事实/偏好独立成为 RAG chunk

**理由：**
- 统一入口降低调用方认知负担，不需要 import 子模块
- filename 加 category 解决同时间戳冲突，不需要错开时间戳（更干净）
- `---` 分隔符复用现有 Chunker，不用单独写拆分逻辑，且一条一 chunk 检索粒度最细
- 外部 API 与 RAG 模块风格一致（`init`/`search`/`delete`）

**曾考虑的替代方案：**
- 暴露子模块让调用方自己组装 —— 耦合度高，调用方需了解内部模块关系
- 每行独立文件 —— 同时间戳文件名冲突，需错开时间戳（脆弱）
- 整段存一条不拆分 —— RAG 检索粒度太粗

---

### 决策 39 — Chroma in-memory `delete(where=)` 不可靠：`delete_collection` 替代方案

**背景：** 测试发现 ChromaDB v1.5.9 in-memory 模式下 `col.delete(where={"source_file": "..."})` 间歇性不匹配（返回成功但实际 0 条删除），导致 `/ragreload` 全量重载后偶发重复条目。经检索确认这是 Chroma 自身已知问题（[#4275](https://github.com/chroma-core/chroma/issues/4275) 删除后查询结果异常 v1.0.0+；[#5367](https://github.com/chroma-core/chroma/issues/5367) `query()` where filter 不匹配但 `get()` 正常）。项目路径规范化（`Path.resolve()` + `str().replace("\\", "/")`）两端一致，排除自身 bug。

**决策：**
- 全量 `/ragreload`（无参数）：先调 `ChromaStore.delete_collection()` 原子删除整个 collection，再遍历所有 `.md` 文件重新入库。彻底绕过 `delete(where=...)` 的 metadata 匹配问题
- 单文件 `/ragreload <keyword>`：保留现有 `_load_one()` 逻辑（`remove` + `add`），接受间歇性不匹配——单文件场景影响范围极小，不值得引入 collection 重建
- `ChromaStore.delete_collection(name)` 封装 `self._client.delete_collection(name)`，try/except 静默处理 collection 不存在的情况

**理由：**
- `delete_collection` 是 Chroma 的原子操作，不依赖 metadata filter，可靠性远高于 `delete(where=...)`
- 全量重载本身就遍历所有文件，drop 后重建的总工作量与逐文件 `remove` + `add` 相当
- 单文件重载走 `delete_collection` 会清掉所有其他文件的数据，不可行；但单文件场景下 `where` 漏删只影响一个文件，且下次全量重载会自动修正
- 这是 Chroma 上游 bug，等待修复不现实（#4275 从 v1.0.0 到 v1.5.9 未修）

**曾考虑的替代方案：**
- 等待 Chroma 官方修复 —— #4275 跨越 5+ 个大版本未修，不可依赖
- 切换到持久化模式 —— 持久化模式同样用 DuckDB，bug 可能存在；且内存模式是设计决策 3 的约定
- 用 `col.get(where=...)` + `col.delete(ids=[...])` 替代 —— `get(where=...)` 同样有 metadata 匹配问题（#5367）
- 全量和单文件统一用 `delete_collection` —— 单文件场景 drop 整个 collection 代价不可接受

---

### 决策 40 — Agent Loop 对话历史管理

**背景：** M4 需要设计 Agent Loop 的对话历史结构。当前 `LLMHandler` 用 `list[dict]`（OpenAI 原生格式），但 M3 已定义了 `Message` 数据类（7 字段，覆盖所有消息类型）。需要在裸 dict 和自定义类型之间选择。

**决策：** Agent Loop 内部用 `list[Message]` 管理对话历史。调 LLM 时转换：`[{"role": m.role, "content": json.dumps(dataclasses.asdict(m))} for m in messages]`。完整序列化，不裁剪，不因 event_type 改变结构。

**理由：**
- `Message` 已在所有模块（CLI/Agent/LLM/Memory）共用，保持一致
- 完整序列化不变形 → LLM 供应商的缓存命中策略能正常工作
- 比 `ConversationContext` 轻量，比裸 dict 类型安全

**曾考虑的替代方案：**
- 裸 `list[dict]` —— 简单但失去类型安全，`event_payload`/`thinking` 等字段无处存放
- `ConversationContext` 封装类 —— 过度抽象，当前只有一个 LLM 后端
- 裁剪序列化（按 event_type 过滤字段）—— 破坏缓存命中率

---

### 决策 41 — 工具结果注入方式

**背景：** Agent Loop 中 LLM 选工具 → 执行 → 结果需喂回 LLM 继续推理。项目使用自定义 JSON 输出格式（非 OpenAI 原生 function calling），`role: "tool"` 需要配套 `tool_call_id` 配对，增加不必要复杂度。

**决策：** 工具结果以 `role: "user"` 注入对话历史，`event_type: "tool_call_result"` 区分语义。不引入 OpenAI 原生 tool_call_id 配对。

**理由：**
- 我们没有用 OpenAI 的 native function calling（`tool_choice` 参数），LLM 是纯文本推理选工具
- `role` 只管消息来源控制，`event_type` 负责语义区分，各司其职
- 简单，兼容任意 OpenAI-compatible 后端

**曾考虑的替代方案：**
- `role: "tool"` + `tool_call_id` —— 需按 OpenAI tool call 协议维护配对，额外复杂度无实际收益

---

### 决策 42 — Agent Loop 终止条件

**背景：** Agent Loop 需要明确的终止/挂起条件，防止无限循环。

**决策：** 三个终止条件：
- `finish` — LLM 自主判断任务完成，正常退出
- `ask_user` — LLM 需要用户输入，挂起等 CLI `input()`
- `max_rounds` — 安全阀，由 `AGENT_MAX_ROUNDS` 环境变量控制，默认值后续定

**理由：**
- `finish`/`ask_user` 是 LLM 自主决策，逻辑由系统提示词控制，代码层只需 > 0 的硬上限
- 环境变量化避免硬编码，部署时可调整

**曾考虑的替代方案：**
- 不加 max_rounds —— 网络异常或 LLM 幻觉可能导致死循环
- 更多终止条件（错误终止、超时终止）—— 当前阶段不需要，后续按需添加

---

### 决策 43 — Tool 装饰器 + input_schema 设计

**背景：** M4 需要工具注册机制。MCP 协议使用完整 JSON Schema（含 type/required），但 Python 的 type hints 已包含类型信息，手写 type 是冗余，且给了一致性出错窗口。

**决策：** 用 `@tool` 装饰器注册工具。`input_schema` 只写 LLM 真正需要的 —— 参数描述和默认值：
```python
@tool(
    purpose="...", use_when="...", do_not_use_when="...",
    expected_output="...",
    input_schema={"path": {"description": "文件路径"}, "line_from": {"description": "起始行号", "default": 1}},
)
def read_content(path: str, line_from: int = 1, line_to: int | None = None) -> Message: ...
```
`type` 从 type hint 自动推断，`required` 从是否有默认值自动推断，均在装饰器阶段（`inspect.signature`）完成。

**理由：**
- 比 MCP 的完整 JSON Schema 少写一半，不手写 type 和 required，消除冗余和一致性风险
- `input_schema` 是 LLM 看到的 ground truth，type hint 只是代码层的类型检查
- 装饰器阶段一次性完成推断，运行时无需重复计算

**曾考虑的替代方案：**
- 完整 JSON Schema（MCP 方案）—— type/required 冗余，手写和 type hint 存在一致性风险
- `Annotated[str, "文件路径"]` —— 每个参数都包一层，签名变长，未选择

---

### 决策 44 — event_payload → 函数入参映射

**背景：** LLM 返回 JSON `action.args` → 解析为 `event_payload: dict` → 需要映射到 Python 函数调用的入参。

**决策：** 直接 `**kwargs` 解包，不做额外映射层。
```python
tool = self._tools[action["tool"]]
result = tool.handler(**action["args"])  # read_content(path="/...", line_from=1)
```
`event_payload` = `action.args`，key 名由 `input_schema` 的 key 保证与函数参数名一致。

**理由：** Python 原生能力足够，不需要参数名转换层。

**曾考虑的替代方案：** 无。

---

### 决策 45 — 工具可见性控制

**背景：** 不同 Agent 需要不同的工具集。主 Agent 有 `dispatch_*` 工具，子 Agent 不应看到这些。

**决策：** `@tool` 加 `agent` 参数：
- `agent=None`（默认）→ 所有 Agent 可用
- `agent=["main", "resume"]` → 仅指定 Agent 可用

全局加载所有 tool（`ToolRegistry`），Agent 构建 system prompt 时只收集有权限的 tool（`to_xml()` 过滤），调用时再加一道门禁检查。

**理由：** 加载和过滤分离 —— 全局注册避免分散管理，过滤在提示词生成时集中处理，门禁是最后防线。

**曾考虑的替代方案：**
- 每个 Agent 声明自己要加载的工具模块 —— 分散，改动时多处更新

---

### 决策 46 — 工具错误处理

**背景：** 工具执行可能失败（LLM 参数理解错误、文件不存在等），错误信息需要让 LLM 有能力自我纠正。

**决策：** 工具抛异常 → Agent Loop 捕获 → 构造 `Message(event_type="tool_call_result", message="[Error] ...")` → 喂回 LLM。错误消息需携带足够上下文（如 LLM 参数错误时附带 `arguments_schema`）。原则：**给够上下文让 LLM 有能力自修复**。具体包装策略后续迭代。

**理由：** LLM 看到错误 + 工具定义后可以重试或改方式，比简单抛异常终止 loop 更鲁棒。

**曾考虑的替代方案：**
- 直接抛异常终止 loop —— 过于粗暴，LLM 长上下文下偶尔参数偏差是正常现象

---

### 决策 47 — ToolRegistry 全局注册表

**背景：** 工具注册后需要被 Agent 发现。`BaseAgent` 遍历 `dir(self)` 太重，且职责不应在 Agent 上。

**决策：** `ToolRegistry` 全局注册表：
- `@tool` 装饰器构建 Tool → `ToolRegistry.register(tool)`
- `BaseAgent.__init__` 调 `ToolRegistry.get_for(agent_name)` 按 agent 过滤拉取
- `extra_tools` 参数额外注入，不进全局 Registry

**理由：** 注册和发现解耦，`BaseAgent` 不关心工具来源。

**曾考虑的替代方案：**
- `BaseAgent` 遍历 `dir(self)` 扫描标记方法 —— 太重，职责混乱
- 每个 Agent 手动注册工具列表 —— 容易遗漏

---

### 决策 48 — process() 接口：Message → Response

**背景：** M1 的 `Handler.process(str) -> str` 只返回文本。引入 questionary 后，handler 需要告诉 App 渲染选项列表、等待审批确认、正常回复。`str` 不够用。

**决策：** `process(input: Message) -> Response`。`Response` 是 CLI 指令层，不进对话历史：
- `finish` — 渲染 markdown，本轮结束
- `select` — 渲染 questionary.select（最后一项固定"自定义输入"），用户选择 → Message → agent loop 继续
- `confirm` — 渲染 questionary.confirm，y → 执行工具，n → 跳过

**理由：** `Response` 语义独立于 `Message`，CLI 指令和对话数据分层清晰。`select` 绑定"返回给 LLM 什么"，`confirm` 绑定"操作是否执行"。

**曾考虑的替代方案：**
- 复用 `Message` 作为 CLI 指令 —— 语义混淆，CLI 指令不应出现在对话历史中

---

### 决策 49 — 意图路由：纯 LLM 驱动

**背景：** 设计文档提到 `Router.classify()`，但决策 15 已定调度 = 工具。需要确认是否还需要独立 Router。

**决策：** 纯 LLM 驱动，不做独立 Router。主 Agent 的 LLM 通过 `dispatch_*` 工具选择调度。`src/main_agent/router.py` 不需要。

**理由：** LLM 原生能力足够做意图识别，独立 Router 增加维护成本且边界情况弱。

**曾考虑的替代方案：**
- 独立 Router（关键词/规则）—— 快但边界弱，需要持续维护
- 混合方案 —— 复杂度高，V1 不必要

---

### 决策 50 — CLI 交互库选型：questionary

**背景：** M4 需要 CLI 提供选项列表和审批确认能力。选项包括 `questionary`、`InquirerPy`、rich 自带 Prompt。

**决策：** 使用 `questionary`。`select` 覆盖选项列表（最后一项"🔧 自定义输入..."），`confirm` 覆盖工具审批。

**理由：**
- API 最简洁（`select()` + `confirm()` 两个函数覆盖所有场景）
- 基于 prompt_toolkit，生态成熟，Windows 兼容性好
- 一个依赖，`uv add questionary` 一句话

**曾考虑的替代方案：**
- `InquirerPy` — 功能更全但更重
- Rich 自带 `Prompt.ask()` — 只有文本输入，无选择菜单
- 自绘 —— 重复造轮子

---

### 决策 51 — Agent 切换机制：Tool-based 异步调用模型

**背景：** 主 Agent dispatch 子 Agent 后，CLI 的 handler 需要切换。原设计用 `Response(type="switch_agent")`，但切换不应是 CLI 指令而应是 App 层操作。

**决策（更新于 M4 实现阶段）：**
- 切换封装为 `@tool`：`switch_to_subagent`（agent=["main"]）+ `switch_to_mainagent`（agent=["*"]），均 `confirm_mode=ALWAYS`
- 子 Agent 会话建模为异步 tool_call：tool_call → 子 Agent 多轮 → tool_call_result(summary)
- 切换信号流：tool handler 返回 `{"__switch__": True, "target": "...", "context": "..."}` → `BaseAgent._execute_tool()` 检测 → 返回 `None` 不包装 tool_call_result → `process()` 设 `_pending_switch` → 返回 `Response(FINISH, switch_agent=..., switch_context=..., switch_tool_call_id=...)`
- App FINISH 分支检测 `switch_agent`：main→sub 时保存 `_switch_tool_call_id`；sub→main 时向主 Agent `_history` 注入 TOOL_CALL_RESULT 完成闭环
- 主 Agent `_history` 中 TOOL_CALL 保留（作为待完成的异步调用），子 Agent 会话不可见
- `/exit_sub` 在 App 层拦截：向子 Agent 注入 system_message 让 LLM 整理上下文 → 调用 switch_to_mainagent
- 子 Agent 无状态，不持有任何持久上下文
- 子 Agent 之间不允许互调（`switch_to_subagent` 仅 main 可见）

**理由：** Tool-based 复用 LLM 已掌握的 function calling 路径；不新增 ResponseType（FINISH + switch 字段）；异步调用模型保证主 Agent 持有全部上下文。

**曾考虑的替代方案：**
- `Response(type="switch_agent")` — 混淆了 CLI 指令和 handler 切换
- 新增 EventType `SWITCH_SUB` — 需要修改 4 处，EventType 承担双重职责
- `App.switch_agent()` 作为独立方法 — 虽然后续封装为 `_get_handler()` + FINISH 分支，而非独立公开方法

---

### 决策 52 — M4 测试子 Agent 实现：JobSearchAgent

**背景：** 计划要求"初期子 Agent 可为桩实现"，但桩无法验证 agent loop + tool + dispatch + return 全链路。原定面试问答 Agent，但切换机制实现后需要一个快速可用的子 Agent 验证全链路。

**决策：** 实现 **JobSearchAgent**（`src/agents/job_search/agent.py`）作为测试用子 Agent：
- 14 个占位符填充职位搜索分析场景
- 可复用现有 `web_search` 工具搜索岗位信息
- 自动获得 `switch_to_mainagent` 工具（agent=["*"] 可见）
- 验证流程：main → switch_to_subagent → JobSearchAgent 对话 → switch_to_mainagent → main 收到总结
- 面试问答 Agent（原 milestone 7）后续按需实现

**理由：** 职位搜索分析场景简单（理解需求 → 搜索 → 分析），无需额外工具即可验证全链路。优先验证切换机制，专业子 Agent 后续按里程碑顺序实现。

**曾考虑的替代方案：**
- 桩实现（返回固定文本）—— 只验证 dispatch 管线，agent loop 和 tool 系统未覆盖
- 面试问答 Agent 先行 —— 需要 RAG 工具，而切换机制尚未验证，应先验证管线再填充功能

---

### 决策 53 — AgentRegistry 设计

**背景：** 主 Agent 需要持有子 Agent 注册表以完成 dispatch。设计文档提到但未细化。

**决策：**
- `AgentRegistry` 放在 `src/agents/registry.py`，**全局单例**（`get_agent_registry()` 双检锁），与 ToolRegistry 对称
- `register(name, agent)` 存入实例的同时，从 `agent._get_*()` 抽取元数据构建 `SubAgentDescriptor`
- `SubAgentDescriptor` 字段：`name` / `display_name` / `description` / `responsibilities` / `hard_constraints`（聚焦路由决策）
- `list_agents_prompt()` 遍历 descriptor，生成格式化列表，通过 `{{SUB_AGENTS_LIST}}` 占位符注入主 Agent system prompt
- "仅 MainAgent 使用"的约束不在数据结构层 → 通过 `switch_to_subagent` tool 的 `agent=["main"]` 可见性控制
- 新子 Agent 注册一步到位：`register("resume", ResumeAgent(...))` → prompt + tool schema 自动更新

**理由：** 与 ToolRegistry 设计理念一致，全局单例降低耦合，SubAgentDescriptor 分离元数据与实例利于 prompt 生成。

**曾考虑的替代方案：** 仅 dict 包装（`register/get/list`）—— 够用但不支持 prompt 自动生成和 tool schema 枚举值动态更新。

---

### 决策 54 — 工具审批模式：ConfirmMode 枚举

**背景：** BaseAgent 的工具调度需要审批门禁（`Response(type="confirm")`），但不是所有工具都需要审批 —— 像 `get_current_datetime` 这类无副作用只读操作不应阻塞用户。需要一个按工具粒度控制审批的机制。

**决策：**
- 新增 `ConfirmMode(StrEnum)` 枚举，三个值：
  - `NEVER` — 无论全局开关，都不审批（如只读查询）
  - `ALWAYS` — 无论全局开关，一律审批（如删除操作）
  - `CONFIG`（默认）— 跟随全局 `TOOL_CONFIRM_ENABLED` 环境变量
- `Tool` dataclass 新增 `confirm_mode: ConfirmMode` 字段，默认 `CONFIG`
- `@tool` 装饰器新增 `confirm_mode` 参数
- `confirm_mode` 不进入 `to_xml()`，对 LLM 完全透明

**理由：**
- 枚举提供类型安全，比裸字符串 `"never"`/`"always"`/`"config"` 更可靠
- `StrEnum` 继承 `str`，序列化/比较自然，repr 可读
- 不进 XML 保证了 LLM 不会知道审批策略，无法通过构造特定输出来绕过审批
- 三级粒度覆盖所有场景：只读无条件免审、危险操作强制审批、常规操作跟随全局策略

**曾考虑的替代方案：**
- `bool` 字段（`needs_confirm: bool`）—— 只有两态，无法表达"跟随全局"语义
- 全局白名单/黑名单 —— 配置分散，不如工具自描述
- 暴露给 LLM —— 安全风险，LLM 可能尝试说服用户绕过审批

---

### 决策 55 — Agent Loop 中间进度回传：Response(type="progress")

**背景：** Agent loop 内部可能执行多轮工具调用，每轮可能耗时数秒。如果 `process()` 只在最终 `finish` 时返回，用户会看到长时间无反馈的黑屏，不知道后台在做什么。

当前 `process()` 是同步阻塞的一次性调用（`input → loop → finish`），无法在中间步骤向 App 报告进度。

**决策：**
- `Response` 新增 `type="progress"`，表示 agent loop 有中间步骤已完成、等待继续
- `Message` 新增静态工厂 `internal_continue()`，生成 `event_type="internal_continue"` 的消息
- `BaseAgent.process()` 拆分为"追加用户输入"和"继续 loop"两种模式：
  - `event_type != "internal_continue"` → 追加用户输入到 history → 从 round 0 开始
  - `event_type == "internal_continue"` → 不追加、从上次 `_round_idx + 1` 继续
- `_round_idx` 提为实例属性，跨 `process()` 调用持久化
- 工具执行后不 `continue` 下一轮，而是 `return Response(type="progress")`；App 渲染后立即调 `handler.process(Message.internal_continue())` 推进
- `finish` / 审批 `confirm` 正常 `return`，App 停在等待用户输入

**理由：**
- 不改变 `Handler.process()` 的单入口协议，App 无需感知 agent loop 内部状态
- `internal_continue` 作为事件类型让 `process()` 区分"新用户输入"和"继续推进"
- 把 `_round_idx` 持久化到实例级别，天然支持跨 `process()` 调用恢复

**曾考虑的替代方案：**
- stderr 直接输出进度 —— 格式不可控，与 rich 渲染冲突，且无法利用 `thinking` 面板
- `process()` 改为 generator（`yield Response`）—— 改变协议签名为 async，违反决策 2（同步代码）
- 让 App 在另一个线程轮询 —— 过度复杂，单线程同步 loop 更可控
- 暴露给 LLM —— 安全风险，LLM 可能尝试说服用户绕过审批

---

### 决策 56 — Message.event_type 枚举化：EventType(StrEnum)

**背景：** `Message.event_type` 此前为 `str` 类型，代码中散布裸字符串（如 `"user_input"`、`"tool_call_result"` 等），拼写错误只能在运行时暴露，且各模块各自理解 event_type 语义，缺乏统一约束。

**决策：** 定义 `EventType(StrEnum)` 枚举，包含 5 个值：
- `USER_INPUT` — 用户输入
- `TOOL_CALL` — 工具调用（LLM 输出）
- `TOOL_CALL_RESULT` — 工具调用结果
- `FINISH` — 对话结束
- `SYSTEM_MESSAGE` — 系统提示/错误恢复

`Message.event_type` 类型改为 `EventType`。所有模块代码中使用 `EventType.USER_INPUT` 等枚举值，不再使用裸字符串。

**理由：**
- `StrEnum` 继承 `str`，`EventType.FINISH == "finish"` 为 `True`，JSON 序列化后为 `"finish"` 字符串，与 LLM 交互无摩擦
- IDE 自动补全 + 静态类型检查，拼写错误在编写阶段暴露
- 集中管理事件类型语义，新增/废弃类型有统一入口

**曾考虑的替代方案：**
- 保持 `str` 类型 + 常量 —— 同样解决拼写问题，但无类型约束
- 使用 `Enum`（非 `StrEnum`）—— `json.dumps()` 输出 `"EventType.FINISH"` 而非 `"finish"`，需额外序列化逻辑

---

### 决策 57 — Message 新增 tool / tool_call_id 一级字段

**背景：** 此前 `Message` 字段不含工具名和工具调用关联信息。`tool_call_result` 的场景下，工具名放在 `event_payload` 内部，工具调用关联 ID 不存在（仅通过对话顺序隐式关联）。随着 `EventType` 枚举明确化，`event_type` 不再承担"这是哪个工具"的语义，需要独立字段承载。

**决策：**
- `Message` 新增 `tool: str | None = None` — 工具名，仅 `tool_call` 和 `tool_call_result` 时填写
- `Message` 新增 `tool_call_id: str | None = None` — 关联的 `tool_call` 消息的 `id`，仅 `tool_call_result` 时填写
- `event_payload` 不再嵌套 `tool` / `tool_call_id`，仅承载纯载荷数据（`tool_call` 时为工具参数，`tool_call_result` 时为调用结果）

**理由：**
- 一级字段比嵌套字典更易于检索和序列化
- `tool_call_id` 显式关联使链式追踪成为可能（tool_call → tool_call_result 的因果链）
- 分离关注点：`tool` 回答"哪个工具"，`event_payload` 回答"什么数据"

**曾考虑的替代方案：**
- 放在 `event_payload` 内部 —— 增加嵌套层级，查询不便
- 不设 `tool_call_id`，靠 `id` 顺序匹配 —— 并发或复杂对话时不可靠

---

### 决策 58 — 工具 handler 返回纯数据

**背景：** 此前 `@tool` 装饰的工具 handler（如 `get_current_datetime()`）直接返回 `Message` 对象，handler 内部自行包装 `event_type`、`role` 等字段。这导致 handler 感知了协议层细节，且不同 handler 的包装方式可能不一致。

**决策：** Handler 返回纯数据（`str` / `dict`），由调用方（`BaseAgent._execute_tool()` / `LLMHandler.process()`）统一包装为 `Message(event_type="tool_call_result", tool=..., tool_call_id=..., event_payload=...)`。

**理由：**
- Handler 只关心业务逻辑，不关心协议格式
- 统一包装点确保所有工具结果格式一致
- 测试 handler 时只需验证返回值数据，无需构造完整 Message

**曾考虑的替代方案：**
- Handler 返回 `Message`（旧方案）—— handler 需感知 Message 结构，跨 handler 格式不一致风险高
- Handler 返回 `tuple[str, dict]` —— 多返回值增加调用复杂度，不如统一 `dict`

---

### 决策 59 — System prompt 隔离

**背景：** 此前 `BaseAgent._history` 第一条是 `Message(role="system", message=system_prompt, event_type="system_prompt")`，将 system prompt 作为 Message 存储。但 system prompt 的结构与其他 Message 不同：它是纯文本注入 OpenAI `{"role": "system", "content": "..."}`，不走 Message JSON 序列化。且 `event_type="system_prompt"` 不在 `EventType` 枚举中。

**决策：**
- System prompt 作为独立字符串 `self._system_prompt` 存储，不混入 `_history`
- `_to_openai()` 构建 messages 数组时，先放入 `{"role": "system", "content": self._system_prompt}`，再追加 `_history` 中各 Message 的 `to_json()`
- `_history` 只存对话消息（user/assistant 角色）

**理由：**
- 语义清晰：system prompt 是静态配置，不是动态消息
- 序列化一致：Message JSON 格式只在对话消息中使用，system prompt 保持原生
- 避免 `event_type` 枚举污染

**曾考虑的替代方案：**
- 新增 `EventType.SYSTEM_PROMPT` —— 增加了枚举值但 system prompt 仍不需要 `id`/`timestamp`/`tool` 等字段
- System prompt 也用 Message JSON 包装 —— LLM 收到的是两层嵌套 JSON，不必要

---

### 决策 60 — 06_output / 07_input prompt 分工

**背景：** 此前 prompt 中只有 `06_output_format.md` 定义 LLM 输出格式，输入侧没有对应的格式说明。LLM 不明确知道自己收到的消息是什么结构，可能影响理解 `tool_call_result` 的正确解析方式。

**决策：**
- `06_output_format.md`：定义 LLM 输出 JSON schema，`role="assistant"`，`event_type∈{tool_call, finish}`，含 `tool`/`event_payload`
- `07_input_format.md`（新建）：定义 LLM 收到的消息 JSON schema，`role="user"`，`event_type∈{user_input, tool_call_result, system_message}`，不含 `tool`/`thinking`
- 原 `07_reserved.md` 顺延为 `08_reserved.md`

**理由：**
- 输入/输出泾渭分明，LLM 清楚区分"自己产出的"和"别人喂给它的"
- 帮助 LLM 正确解析 `tool_call_result` 的结构（`tool_call_id` 链回自己的 `tool_call`）
- 两个 schema 的字段互不越界，设计自文档化

**曾考虑的替代方案：**
- 仅在 06 中描述输入结构 —— LLM 不知道 `system_message` 等类型的语义
- 合并为一个文件 —— 输入/输出混在一起，LLM 容易混淆

---

### 决策 61 — Message.to_json() / from_llm_reply() 统一序列化

**背景：** `BaseAgent._to_openai()` 和 `LLMHandler` 各自用 `json.dumps(dataclasses.asdict(m))` 序列化 Message；`Handler._parse_llm_reply()` 手动解析旧嵌套 schema。多处重复且解析逻辑分散。

**决策：**
- `Message.to_json()` — 实例方法，`dataclasses.asdict()` + `json.dumps(default=str)` 统一序列化
- `Message.from_llm_reply(reply: str)` — 静态方法，按扁平 JSON schema 反序列化，required 字段用 `[]`（缺失即 crash），optional 字段用 `.get()`（默认 `None`）
- `Handler._parse_llm_reply()` 简化为一行委托 `Message.from_llm_reply()`
- `BaseAgent._to_openai()` 改用 `Message.to_json()`

**理由：**
- 序列化/反序列化是 Message 的固有行为，放在类内部最合理
- 未来 schema 变更只需改一处
- `default=str` 处理 `datetime` 等非 JSON 原生类型

**曾考虑的替代方案：**
- 保留 `Handler._parse_llm_reply()` 独立实现 —— 代码重复，BaseAgent 和 LLMHandler 都需各自维护解析逻辑
- 用 `dataclasses.asdict()` 的 `dict_factory` 参数定制序列化 —— 与 `default=str` 等价但更隐晦

---

### 决策 62 — 移除 04_tools.md 硬编码预定义工具

**背景：** `04_tools.md` 此前硬编码了 `ask_user`、`finish`、`return` 三个预定义工具，独立于 `ToolRegistry`。随着 `event_type` 枚举化，`finish` 不再是工具调用而是事件类型（LLM 通过 `event_type="finish"` 结束对话），`ask_user` 和 `return` 也不再作为独立工具存在。硬编码工具与 `{{ADDITION_TOOLS}}` 注入的真实工具并存，LLM 可能混淆。

**决策：** 移除 `04_tools.md` 中所有硬编码的 `<Tool>` 定义，仅保留 `<Tools>{{ADDITION_TOOLS}}</Tools>` 空壳。所有可用工具由 `ToolRegistry` 通过 `{{ADDITION_TOOLS}}` 占位符动态注入。

**理由：**
- `finish` 已改为 `event_type` 枚举值，不再作为工具
- `ask_user` 和 `return` 设计上已废弃（agent loop 通过 `finish` + message 即可覆盖交互和退出场景）
- 单一工具来源（`ToolRegistry`）避免 LLM 看到两套工具列表不一致

**曾考虑的替代方案：**
- 保留 `ask_user` 和 `return` 为注册工具 —— 与 `finish` 语义重叠，增加 LLM 选择负担

---

### 决策 63 — message 默认 "" + event_type 唯一 required

**背景：** `Message` 此前有两个 required 字段 `message` 和 `event_type`。在实际使用中，`tool_call_result` 消息的 `message` 通常为空（工具 stdout 可选），强制填写增加了不必要的样板代码。

**决策：**
- `message` 默认值改为 `""`（空字符串）
- `event_type` 保持为唯一 required 字段
- 字段顺序调整为 `event_type` 在前（required）→ `message` 在后（有默认值），符合 dataclass 规范

**理由：**
- `Message(event_type=EventType.USER_INPUT)` 即可构造最小消息，减少样板
- `tool_call_result` 场景天然无需 message，默认 `""` 语义合理
- 仍然可以在需要时显式传 `message="..."` 覆盖

**曾考虑的替代方案：**
- 保持 `message` required —— `tool_call_result` 每处构造都需手动 `message=""`，增加样板

---

### 决策 64 — Agent Loop 上移至 App 层 + process() 单步执行

**背景：** 原 `BaseAgent.process()` 内部 `for` 循环一次性跑到底，LLM 的每次 TOOL_CALL 对用户不可见。用户需要看到工具调用的中间进度，且审批门禁需要暂停循环等待用户确认。

**决策：**
- `process()` 从内部 `for` 循环改为单步执行：每次调用只做一步（处理输入 → LLM → 分发 → 返回）
- Agent loop 循环由 `App.run()` 内层 `while True` 驱动
- 工具执行暂停时返回 `Response(PROGRESS)` 或 `Response(CONFIRM)`，App 渲染后喂回 `Request(CONTINUE)` 或 `Request(CONFIRM_APPROVED)` 恢复
- 新增实例状态 `_pending_tool: tuple[tool_name, payload, tool_call_id]` 跨 `process()` 调用保存断点
- 内层 `while self._round_counter < self._max_rounds` 仅用于错误恢复（JSON 解析失败、未知工具），正常路径一次退出

**理由：**
- App 层可见工具调用的中间过程（PROGRESS 渲染工具名 + message），不再黑屏等待
- 审批暂停时 App 弹 `questionary.confirm`，用户确认/拒绝后继续或退出
- 保持 `process()` 同步单入口，App 无需感知 Agent 内部状态机
- `_pending_tool` 断点简单直接，不需要 generator/coroutine

**曾考虑的替代方案：**
- `process()` 改为 generator（`yield Response`）—— 改变协议为异步，违反决策 2
- 保留内部循环 + stderr 输出进度 —— 格式不可控，与 rich 渲染冲突
- `process()` 内部回调 App —— 反向依赖，破坏 Handler 协议

---

### 决策 65 — Request 类型（对称 Response）作为 App → Agent 输入协议

**背景：** 原 `Handler.process()` 入参为 `Message`，但 Agent loop 上移后需要区分三种不同的调用场景：用户新输入、PROGRESS 后自动继续、审批通过后恢复执行。复用 `Message` 会导致语义混淆（CONTINUE 不是真正的"消息"）。

**决策：**
- 新增 `src/request.py`，定义 `Request` dataclass + `RequestType(StrEnum)`
- `RequestType` 三个值：`USER_INPUT`（用户输入了文本）、`CONTINUE`（自动继续执行）、`CONFIRM_APPROVED`（用户确认了工具执行）
- `Handler.process()` 签名从 `process(Message) -> Response` 改为 `process(Request) -> Response`
- `Request` 和 `Response` 对称：都是 App ↔ Agent 协议层，都不进对话历史

**理由：**
- `Request` 语义独立于 `Message`，不会把"继续执行"这种控制信号混入对话
- 对称设计：App 用 `Request` 告诉 Agent 做什么，Agent 用 `Response` 告诉 App 渲染什么
- 没有 `CONFIRM_REJECTED`：用户拒绝时 App 不调 `process()`，直接退出内层循环等用户主动输入

**曾考虑的替代方案：**
- 复用 `Message` 作为入参，新增 `event_type="internal_continue"` —— 混淆了对话数据和协议控制，且需要新增 EventType
- 用多个方法（`process_input` / `process_continue` / `process_confirm`）—— 增加 Handler 接口复杂度

---

### 决策 66 — 用户拒绝审批 → 退出内层循环，不调 process()

**背景：** 工具需要审批时，`process()` 返回 `Response(CONFIRM)`，App 弹 `questionary.confirm`。用户拒绝后有两种选择：构造一个"拒绝"结果喂回 LLM，或直接退出等待用户重新输入。

**决策：** 用户拒绝审批 → App 直接 `break` 退出内层循环，不调用 `process()`。下一次用户主动输入时，`process(USER_INPUT)` 检测 `_pending_tool` 是否仍存在 → 存在则说明上次被拒绝 → 在 USER_INPUT Message 的 `event_payload` 中注入拒绝信息（`{"tool": ..., "tool_call_id": ..., "reason": "用户取消了此操作"}`），一条消息同时携带用户文本和拒绝信息。

**理由：**
- LLM 在分析用户意图时同时得知上次调用被拒，可以决定重新尝试或调整方向
- TOOL_CALL 保留在 history 中形成完整调用链：TOOL_CALL → (放弃) → USER_INPUT(拒绝信息)
- 不新增独立消息，保持对话紧凑
- App 层逻辑不变，仅在 BaseAgent 收 USER_INPUT 时做守卫

**更新（M4 实现阶段）：** 原决策认为"LLM 不需要知道审批被拒绝"，实现 switch_to_subagent 后发现 LLM 缺少被拒信息时会误以为工具已执行、等待 result。因此增加拒绝信息注入机制。

**曾考虑的替代方案：**
- 构造 `Request(CONFIRM_REJECTED)` → process() 注入 system_message → LLM 继续 —— 多余，用户拒绝后 LLM 无上下文继续
- `process()` 内部处理审批（阻塞等 stdin）—— 破坏依赖注入，App 层失去对 I/O 的控制
- 直接删除 TOOL_CALL —— 丢失上下文，LLM 不知道刚才发生了什么

---

### 决策 67 — 工具错误上下文增强：工具列表 + 参数 schema

**背景：** 原工具调度在遇到未知工具或执行失败时，给 LLM 的错误信息较简略（仅 `"未知工具：xxx"` 或 `{"error": "..."}`），LLM 缺少足够信息自修正。

**决策：**
- 未知工具 → system_message 附带完整可用工具名列表：`"未知工具：xxx。可用工具：tool_a, tool_b, ..."`
- 工具执行失败 → error payload 附带 `arguments_schema` + `expected_output`，让 LLM 对照检查参数是否正确
- 原则延续决策 46：**给够上下文让 LLM 有能力自修复**

**理由：**
- 工具列表让 LLM 一眼看到正确选项，不需要从 system prompt 里翻
- `arguments_schema` 是工具的真实参数定义，LLM 可以对照找出哪里不对（拼写、缺失 required、类型错误）
- 与决策 46 一脉相承：错误恢复靠信息量，不靠复杂逻辑

**曾考虑的替代方案：**
- 仅告知"未知工具"不列可用工具 —— LLM 需重新解析 system prompt 中的工具列表，浪费一轮
- 仅返回 error string —— LLM 不知道参数哪里错了，只能猜

---

### 决策 68 — MainAgent 位置：`src/agents/main_agent.py`

**背景：** 设计文档原计划 `src/main_agent/` 独立目录放置主 Agent。实现时用户指出 Agent 应统一放在 `src/agents/` 下。

**决策：** `MainAgent` 放在 `src/agents/main_agent.py`，与 `BaseAgent` 同目录。`src/main_agent/` 目录不创建。

**理由：**
- 所有 Agent 统一管理，简化项目结构
- `BaseAgent` 和 `MainAgent` 在同一目录，import 路径更短
- 未来子 Agent 也放在 `src/agents/` 下（如 `interview/`），一致的目录约定

**曾考虑的替代方案：**
- 独立 `src/main_agent/` 目录 —— 增加目录层级，与其他 Agent 位置不一致

---

### 决策 69 — 审批 UI：questionary.select + ConfirmChoice 枚举

**背景：** 审批确认使用 `questionary.confirm`，在某些终端渲染为 `??` 而非正常的 `? (y/N)`，用户体验差。

**决策：** 替换为 `questionary.select` + `ConfirmChoice(StrEnum)` 枚举：
- `ConfirmChoice.APPROVE = "✅ 执行"` / `ConfirmChoice.REJECT = "❌ 取消"`
- App 中比较用枚举值而非裸字符串

**理由：**
- `select` 比 `confirm` 渲染更稳定，在不同终端一致
- 枚举保证选项字符串不写错，类型安全
- emoji 提升视觉辨识度

**曾考虑的替代方案：**
- 保持 `questionary.confirm` 换终端 —— 治标不治本
- 裸字符串比较 `"✅ 执行"` —— 拼写错误风险

---

### 决策 70 — LLMClient.web_search() 两轮 native function calling

**背景：** 需要为 Agent 提供网络搜索能力。DeepSeek API 支持内置 `web_search` 工具，通过 OpenAI 兼容的 function calling 协议调用。

**决策：** `LLMClient.web_search(query)` 实现为两轮对话：
- Round 1：发 system prompt + user query + `web_search` 工具定义 + `tool_choice` 强制选 `web_search`，模型返回 `tool_calls`
- Round 2：喂回 assistant 的 `tool_calls` + `role: "tool"` 结果（`"Provide the result"`），模型整理后返回答案
- 两轮均 `extra_body={"thinking": {"type": "disabled"}}` 关闭推理
- System prompt 将模型定位为"纯搜索工具"而非"拥有工具能力的助手"

**理由：**
- 复用 OpenAI SDK 原生 `tools` / `tool_choice` 参数，无需额外 HTTP 调用
- 两轮协议是 DeepSeek web_search 的标准调用方式
- 关闭 thinking 节省 token、加快响应

**曾考虑的替代方案：**
- 用 `WebSearch` / `WebFetch` 工具做真实 HTTP 请求 —— 需要额外的搜索 API key 和服务
- 一轮调用直接返回搜索结果 —— DeepSeek 需要两轮 tool_call 协议

---

### 决策 71 — WORKING_DIR 环境变量 + get_working_dir() 工具

**背景：** Agent 可能需要在磁盘上读写临时文件，需要一个统一的工作目录。

**决策：**
- 新增 `WORKING_DIR` 环境变量，默认 `data/temp/`，通过 `config.py` 管理
- `get_working_dir()` 工具：`Path.resolve()` 返回绝对路径，自动 `mkdir(parents=True, exist_ok=True)`
- `data/temp/` 加入 `.gitignore`

**理由：**
- 统一工作目录避免文件散落各处
- 默认值开箱即用，环境变量支持部署时自定义
- 自动创建目录避免 LLM 因目录不存在而调用失败

**曾考虑的替代方案：**
- 硬编码 `data/temp/` —— 不够灵活
- 让 LLM 自行选择路径 —— 可能写出项目外的文件

### 决策 72 — MainAgent 重新定位为路由 Agent

**背景：** MainAgent 最初定位为通用"求职助手"，既回答问题又调度子 Agent。随着架构细化，需要明确职责边界，避免路由 Agent 越界执行子 Agent 的专业任务。

**决策：**
- MainAgent 重新定位为"程序员求职助手路由Agent"
- 唯一职责：识别意图 → 分类 → 选择子Agent → 切换入口
- 硬约束明确禁止：不生成简历内容、不提供学习方案、不执行面试模拟、不搜索或分析职位
- 如果用户请求属于子Agent能力范围，必须切换Agent
- 如果无法判断用户需求，必须向用户提问，而不是猜测

**理由：**
- Hub-and-Spoke 架构要求主 Agent 作为纯调度中心，不应与子 Agent 职责重叠
- 明确的职责边界让 LLM 行为可预测，减少"万能型"Agent 的幻觉风险
- 专业化分工：路由归主 Agent，执行归子 Agent

**曾考虑的替代方案：**
- 主 Agent 既路由又执行 —— 职责模糊，容易跳过子 Agent 直接回答，破坏架构
- 主 Agent 完全透明路由（不告知用户切换）—— 用户体验差，不理解为什么要"换人"

### 决策 73 — LLMClient 线程安全单例

**背景：** `LLMClient` 在 5 处被独立实例化（`main.py`、`src/memory/__init__.py`、`src/memory/builder.py`、`src/tools/web_tool.py`），重复创建 OpenAI client 实例浪费连接池资源，且多个实例之间无共享状态。

**决策：**
- `src/llm/__init__.py` 提供 `get_client()` 函数，双检锁（DCL）懒加载单例
- 所有调用方统一使用 `from src.llm import get_client` + `get_client()`
- 线程安全：`threading.Lock` 保护初始化临界区
- `LLMClient` 类本身保持不变，单例仅体现在 `__init__.py` 层面

**理由：**
- 项目使用 `threading` 做后台加载（RAG 初始化、Memory async 模式），需要线程安全
- 双检锁模式与项目现有 RAG/Memory 模块单例风格一致
- OpenAI client 内部管理 HTTP 连接池，单一实例更高效
- 调用方代码更简洁：`get_client()` vs `LLMClient()`

**曾考虑的替代方案：**
- 每个调用方独立实例化 —— 当前做法，浪费连接池资源
- `LLMClient` 自身做 `__new__` 单例 —— 侵入类自身，测试不友好，且与项目模块级单例惯例不一致
- 通过依赖注入传递 —— M4 阶段尚未建立全局 DI 容器，过度设计

---

### 决策 74 — 退出清理统一入口：Lifecycle 模块

**背景：**
- M4 阶段实现了 `build_memories(async_mode)` 后台记忆固化，使用 daemon 线程
- daemon 线程在进程退出时被直接杀死，中间产生的记忆永久丢失
- 需要进程退出前显式等待后台线程完成
- 未来其他模块（RAG、临时文件清理等）也需要退出清理钩子
- 各模块自行管理退出逻辑会导致 main.py 感知过多内部细节

**决策：**
- 新建 `src/lifecycle.py` 作为进程生命周期管理模块
- `register_shutdown(hook, *, name)` — 各模块在初始化时注册无参清理函数
- `shutdown()` — 进程退出前调用，按注册逆序执行所有 hook
- 单个 hook 异常被捕获并记日志，不影响后续 hook 执行
- memory 模块在 `_ensure_init()` 中自动注册 `_shutdown_wait_pending`

**理由：**
- 松耦合：main.py 只调 `lifecycle.shutdown()`，不感知各模块内部清理细节
- 可扩展：以后任何模块需要退出清理，一行 `register_shutdown()` 即可
- 防御性：单个 hook 异常不会阻止其他 hook 执行
- daemon 线程保持不变，`shutdown()` 只提供优雅退出路径，强制杀进程不会被卡住

**曾考虑的替代方案：**
- 各模块暴露独立 `shutdown_*()` 让 main.py 逐个调用 — main.py 与各模块强耦合
- 线程改为非 daemon — 进程会卡住直到所有线程完成，用户体验差
- 仅 memory 模块内建 `shutdown()` — 单点方案，不可扩展

---

### 决策 75 — BaseAgent LLM 调用默认强制 JSON 输出

**背景：**
- Agent LLM 输出格式由 `general_agent/06_output_format.md` 定义为 flat JSON schema
- `process()` 中通过 `_parse_llm_reply()` 解析 JSON，失败时注入 output_format 让 LLM 自修复
- 不强制 JSON 模式时 LLM 可能输出 markdown 包裹的 JSON，增加解析失败概率
- MemoryBuilder 已固定使用 `response_format={"type": "json_object"}`

**决策：**
- `BaseAgent._pro_params` 默认值 `{"response_format": {"type": "json_object"}}`
- `BaseAgent._flash_params` 同样设置，供子类 flash tier 调用使用
- 通过 `**self._pro_params` 注入 `chat_pro()` 调用，无需每个调用点手动传参
- 子类可通过覆盖类变量自定义参数

**理由：**
- 输出格式已明确定义为 JSON，强制模式消除 LLM 擅自包裹 markdown 的可能性
- 减少 JSON 解析失败 → system_message 注入 → 重试的浪费
- 类变量 + `**kwargs` 透传模式与项目现有设计一致（决策 12）
- 子类如需调整（如某些 LLM 不支持）只需覆盖类变量

**曾考虑的替代方案：**
- 每个调用点手动传 `response_format` — 重复代码，容易遗漏
- 不强制 JSON，依赖 LLM 自觉遵守 prompt — 实践表明不可靠，增加重试成本
- 仅在 `chat_pro` 中 hardcode — 剥夺子类自定义能力

---

### 决策 76 — LLM Thinking 可配置开关

**背景：**
- commit `21205f2` 引入了 `LLM_THINKING_ENABLED` 环境变量和对应的 `extra_body` 注入逻辑
- 某些 LLM API provider（如 DeepSeek）在 `chat.completions` 响应中包含 `thinking`/`reasoning_content` 字段
- 这些推理内容在上游被计入 output tokens 计费，但本项目自身通过 `SHOW_THINKING` flag 控制是否展示给用户
- 需要一种方式让用户完全关闭 provider 端的 thinking，以节省 token 消耗和响应延迟
- `web_search()` 场景不需要推理能力，应固定关闭

**决策：**
- 新增 `LLM_THINKING_ENABLED` 环境变量（bool 类型，`is_bool=True`，默认 `"true"`）
- `LLMClient` 新增静态方法 `_thinking_extra_body()`，根据配置返回 `extra_body` dict：
  - `False` → `{"thinking": {"type": "disabled"}}`
  - `True`（默认）→ `{}`（走 provider 默认行为，不做任何干预）
- `chat_pro()` 和 `chat_flash()` 通过 `kwargs.setdefault("extra_body", self._thinking_extra_body())` 注入，调用方可覆盖
- `web_search()` 两轮调用均固定设置 `extra_body={"thinking": {"type": "disabled"}}`，不受全局开关影响
- Agent 层无感知 — thinking 控制完全在 `LLMClient` 管道层完成

**理由：**
- `extra_body` 是 OpenAI SDK 的扩展入口（`chat.completions.create(extra_body=...)`），兼容不同 provider 的 thinking 控制语法（DeepSeek、OpenAI o-series 等）
- 默认启用（`true`）保持 provider 原生体验，用户可按需关闭以节省 token 和延迟
- `web_search()` 固定关闭：搜索场景只需结果整理，不需要深度推理，额外的 thinking tokens 是纯粹浪费
- 环境变量 + config 模块统一管理，与项目现有配置风格一致（决策 12）
- 调用方可传 `extra_body` 覆盖默认值（`setdefault` 不覆盖已存在的 key）

**曾考虑的替代方案：**
- 硬编码禁用 — 剥夺用户选择权，且某些 provider 可能不支持该指令
- 在 Agent 层（`BaseAgent`）控制 — 违背参数分层管理原则（决策 13），thinking 是 LLM API 管道层的事，Agent 不应关心
- 仅控制 `chat_pro` — flash tier 同样可能因 thinking 增加延迟
- `web_search()` 跟随全局开关 — 搜索场景 thinking 无价值，不如固定关闭

---

### 决策 77 — JSON 解析增强：json-repair + 换行转义 + 提示注入节制

**背景：**
- LLM 输出中包含多行文本时，`message` 字段内的物理换行未被转义为 `\n`，导致 `json.loads()` 解析失败（报错后 LLM 重试浪费 token 和轮数）
- 原方案自研了一个状态机 `_repair_newlines()` 修复 JSON 字符串内的裸换行，但只能处理换行问题，无法覆盖其他 LLM 常见 JSON 错误（尾部逗号、引号等）
- `thinking` 字段使用 `parsed["thinking"]` 强制取值，某些 LLM 不输出 `thinking` 时导致 `KeyError`，而 JSON schema 中 `thinking` 本应为可选
- JSON 解析失败时每轮都注入 `output_format` 提示，LLM 连续失败时 history 被同一段提示反复填充

**决策：**
- 引入 `json-repair` 库（PyPI: `json-repair==0.61.2`，零依赖），替换自研 `_repair_newlines()` 状态机
- `Message.from_llm_reply()` 直接使用 `json_repair.loads(reply)`，一次调用覆盖未转义换行、尾部逗号、单引号、缺失引号等 LLM 常见 JSON 错误
- `06_output_format.md` `<Requirements>` 新增约束：JSON 字符串内不得包含物理换行，必须转义为 `\n`
- `thinking` 字段从 `parsed["thinking"]`（强制）改为 `parsed.get("thinking")`（容错）
- `BaseAgent.process()` 新增 `_format_injected` 标记：每次 `process()` 调用的错误恢复循环中仅首次 parse 失败注入 `output_format` 提示，后续失败只 `continue` 重试
- parse 失败时 `logger.debug` 打印原始 LLM 回复，便于定位

**理由：**
- `json-repair` 专为 LLM 畸形 JSON 设计，覆盖场景远超自研状态机，且持续维护（GitHub 1k+ stars）
- 单个 `json_repair.loads()` 替代 try/except + 修复 + 重试三段逻辑，代码量减少
- `06_output_format.md` 约束从源头减少换行问题，`json_repair` 作为容错兜底，双重保障
- `thinking` 可选化匹配实际 LLM 行为（部分模型不输出此字段），与 `tool`/`event_payload` 处理一致
- 提示注入节制避免 history 膨胀：同一轮 `process()` 中 LLM 连续 parse 失败时，重复注入 output_format 无益

**曾考虑的替代方案：**
- 仅强化 prompt 约束，不做代码容错 — LLM 不能 100% 遵守，生产环境需要防御性解析
- 仅自研状态机（`_repair_newlines`）— 只覆盖换行问题，尾部逗号、引号等仍需额外处理
- `demjson3` / `json5` — 侧重非标准 JSON 语法（注释、尾部逗号），不是专门的 LLM 修复方案
- parse 失败每次注入更短提示而非跳过 — 用户明确要求"只提示一次，不要一直塞入提示"

---

### 决策 78 — Agent 切换机制：Tool-based 异步工具调用模型

**背景：** 主 Agent 需要调度子 Agent 执行专业任务（如面试模拟），并在子任务完成后收回控制权。切换时需要携带上下文（用户目标、历史背景等），子 Agent 完成工作后需要将总结带回主 Agent，使主 Agent 能继续决策。需要设计一个保证主 Agent 上下文完整性、子 Agent 无状态的切换机制。

**决策：**
- 切换封装为 `@tool`，LLM 通过标准 tool_call 携带 `sub_agent` + `context`
- 整个子 Agent 会话建模为一次"异步工具调用"：
  - 主 Agent `_history` 中保留 `tool_call: switch_to_subagent(...)` （待完成）
  - 子 Agent 多轮交互不进主 Agent 历史
  - 子 Agent 退出时，向主 Agent `_history` 注入 `tool_call_result(summary)` 完成闭环
- 两个 switch tool：
  - `switch_to_subagent(sub_agent, context)` — 仅 MainAgent 可见
  - `switch_to_mainagent(summary)` — 所有子 Agent 自动注入
- 子 Agent 之间不允许互调
- `/exit_sub` CLI 命令在 App 层拦截：主 Agent 前台时报错，子 Agent 时等价 `switch_to_mainagent("用户主动退出")`
- 不新增 `EventType` 或 `ResponseType`：切换通过 `Response(type="finish", switch_agent=..., switch_context=...)` 表示
- 切换信号流：tool handler 返回 `_SwitchTarget` → `BaseAgent._execute_tool()` 检测 → `BaseAgent.process()` 返回 FINISH + switch → App 内层循环检测 → `App.switch_agent()`
- `AgentRegistry` 放在 `src/agents/registry.py`，仅 MainAgent 持有，App 通过它做 handler 切换

**理由：**
- Tool-based 复用了 LLM 已熟练掌握的 function calling 路径，有 `input_schema` 描述参数、有 `use_when` 约束条件，LLM 不需要学习新输出格式
- 异步调用模型保证主 Agent 始终持有完整上下文（含子 Agent 的总结），子 Agent 无持久状态
- 不新增 EventType 避免了枚举承载"控制流"和"对话事件"两种职责
- 子 Agent 无状态设计简化了实现和调试

**曾考虑的替代方案：**
- Option B（新增 `SWITCH_SUB` EventType）— 需要修改 LLM 输出 schema、Message 解析、BaseAgent 分发、App 循环四个地方，且让 EventType 枚举承担双重职责
- 在主 Agent 中注入子 Agent 全部对话 — 历史膨胀严重，cache miss，LLM 可能混淆两段对话

---

### 决策 79 — `/exit_sub` 主 Agent 前台时报错

**背景：** `/exit_sub` 仅在子 Agent 会话中有意义。在主 Agent 前台时用户误输入，需要明确的错误反馈。后续可考虑动态隐藏命令，但当前阶段以简单明确为优先。

**决策：** 主 Agent 前台时 `/exit_sub` 直接报错 `"当前已是主Agent，/exit_sub 仅在子Agent会话中可用"`，不做隐藏处理。实现用 `isinstance(handler, MainAgent)` 判断，无需修改其他地方。

**理由：**
- `isinstance` 单行判断，实现代价极低
- 错误消息明确告知用户当前状态
- 后续如需动态显示/隐藏可以在此基础上迭代

**曾考虑的替代方案：**
- 动态过滤 help 命令列表 — 当前阶段过度设计，改了 App help 渲染逻辑
- 静默忽略 — 用户不知道命令为什么没生效

---

### 决策 80 — 子 Agent 列表 prompt 注入：{{SUB_AGENTS_LIST}} 占位符 + 模板重排

**背景：** 主 Agent 的 system prompt 需要动态注入子 Agent 列表（名称、描述、职责、约束），让 LLM 知道有哪些子 Agent 可用、何时该切换。此内容对子 Agent 无意义（子 Agent 不能调度其他 Agent）。

**决策：**
- 新增 `{{SUB_AGENTS_LIST}}` 占位符，与 `{{ADDITION_TOOLS}}` 同模式：`PromptLoader.get(**placeholders)` 替换
- `BaseAgent._get_sub_agents_list()` 默认返回 `""`（子 Agent 不感知）
- `MainAgent` 覆盖为 `get_agent_registry().list_agents_prompt()`
- 模板文件重排序：新文件 `05_sub_agents.md`（仅含 `{{SUB_AGENTS_LIST}}`），原 05~08 顺延为 06~09

```
04_tools.md               — 工具定义（含 switch_to_subagent）
05_sub_agents.md          — 可切换子 Agent 列表（新增）
06_communtion_style.md    — 沟通风格（原 05）
07_output_format.md       — 输出格式（原 06）
08_input_format.md        — 输入格式（原 07）
09_reserved.md            — 保留（原 08）
```

**理由：**
- 04（工具）定义"你可以切换"，05（子 Agent 列表）定义"可以切到谁"，逻辑顺序自然
- 占位符模式与 `{{ADDITION_TOOLS}}` 一致，不引入新机制
- `BaseAgent` 默认 `""` 确保子 Agent prompt 中无冗余内容
- 扩展只需 `register()` 一步，prompt 自动更新

**曾考虑的替代方案：**
- 放在 09 末尾 — 与工具定义距离太远，LLM 看到 switch_to_subagent 时尚不知道有哪些目标
- 放入 `01_role.md` 作为 `{{RESPONSIBILITIES}}` 的一部分 — 职责描述和子 Agent 清单混在一起，维护困难

---

### 决策 81 — Agent 稳定标识 `_get_agent_key()` 与 ToolRegistry `agent_key` 参数

**背景：** `switch_to_subagent` 需要 `agent=["main"]` 仅对主 Agent 可见，但 `ToolRegistry.get_for()` 使用 `_get_agent_name()`（展示名"程序员求职助手路由Agent"）做匹配，无法用稳定的短标识过滤。同时 `switch_to_mainagent` 需要对所有子 Agent 可见但对 MainAgent 不可见，需要"非 main"语义。

**决策：**
- `BaseAgent` 新增 `_get_agent_key()` 方法（非抽象），默认返回 `_get_agent_name()`；MainAgent 覆盖为 `"main"`
- `ToolRegistry.get_for()` 新增 `agent_key` 参数，同时匹配 `agent_name` 和 `agent_key`
- `"*"` sentinel 别名：`"*" in tool.agent` → 匹配所有 `agent_key != "main"` 的 Agent

**理由：**
- `agent_key` 与 `agent_name` 职责分离：展示名可随时调整（中英文），key 是稳定的编程标识
- `"*"` 支持"所有非 main"语义而无需枚举子 Agent 名，扩展时无需改 tool 定义

**曾考虑的替代方案：**
- `isinstance(handler, MainAgent)` 判断 — ToolRegistry 不应依赖 Agent 具体类型
- 列出所有子 Agent 名（`agent=["interview", "learning"]`）— 每加一个 Agent 都要更新，容易遗漏

---

### 决策 82 — CONFIRM 拒绝 → 下次 USER_INPUT 携带拒绝信息

**背景：** 用户拒绝工具审批（如拒绝 switch_to_subagent）后，TOOL_CALL 已写入 `_history` 但无 TOOL_CALL_RESULT 闭环。直接删除 TOOL_CALL 会丢失上下文。需要在用户下次输入时告知 LLM 上一条工具调用被拒绝了。

**决策：** 在 `BaseAgent.process()` 的 `USER_INPUT` 分支开头检测 `_pending_tool` 是否仍然存在：
- 存在 → 用户拒绝了上次 CONFIRM → 在 USER_INPUT Message 的 `event_payload` 中注入 `{"tool": ..., "tool_call_id": ..., "reason": "用户取消了此操作"}`
- 不存在 → 正常处理，`event_payload` 为 `None`

一条消息同时携带用户文本和拒绝信息，不新增独立消息。

**理由：**
- LLM 在分析用户意图时同时得知上次调用被拒，可以决定重新尝试或调整方向
- 不修改 App 层逻辑，仅在 BaseAgent 收 USER_INPUT 时做守卫
- TOOL_CALL 保留在 history 中形成完整调用链：TOOL_CALL → (放弃) → USER_INPUT(拒绝信息)

**曾考虑的替代方案：**
- 直接删除 TOOL_CALL — 丢失上下文，LLM 不知道刚才发生了什么
- 注入独立 TOOL_CALL_RESULT 消息 — 消息数膨胀，且"结果"语义与"被拒绝"不符
- App 层处理 — App 不应感知 agent history 结构

---

### 决策 83 — switch tool 必须声明 input_schema

**背景：** `@tool` 装饰器通过 `input_schema` 参数声明工具参数，`inspect.signature` 仅用于填充 `type`/`required`。初次实现 `switch_to_subagent` 时未传 `input_schema`，导致 `arguments_schema` 为空 `{}`，LLM 无法得知参数定义。

**决策：** 所有 `@tool` 装饰的工具必须显式提供 `input_schema`，`inspect.signature` 从函数签名补充类型和默认值信息。

**理由：**
- `input_schema` 是 LLM 了解工具参数的唯一途径，缺失时 LLM 只能猜测参数名
- `@tool` 设计的本意就是 `input_schema` 声明参数 + 函数签名补充类型，不是自动从签名生成 schema

---

### 决策 84 — UIBridge：工具 handler 通过跨线程通信桥直连 CLI 交互

**背景：** M4 工具审批原通过 `ConfirmMode` 枚举 + `_should_confirm()` 机制：`process()` 检测需审批的工具 → 返回 `Response(type="CONFIRM")` → App 渲染 questionary → 用户选择 → `Request(CONFIRM_APPROVED)` → `process()` 执行 handler。每增加一种交互类型（如 select），需要改 `process()`、`App.run()`、`RequestType` 三处，耦合度高。

**决策：**
- 新增 `src/cli/uibridge.py`：`UIBridge` 类作为工具 handler（后台线程）与 CLI 前端（主线程）的跨线程通信桥
- `UIBridge.select(question, choices) -> str` 和 `UIBridge.confirm(message) -> bool` 两个交互方法，handler 直接调用，阻塞等待用户响应
- 模块级 `get_bridge()` 供 handler 获取当前 bridge；`_set_bridge()` 由 App 在后台线程中设置/清除
- Bridge 粒度为每次用户输入（创建在 App 内层循环前），同一次输入内的多个 tool call 共享同一个 bridge
- App `_process_with_spinner()` 在 spinner 循环中轮询 `bridge.has_request`，检测到请求时暂停 spinner、渲染 questionary、传回结果
- `ConfirmMode` 恢复参与调度：`_should_confirm()` 在 `_execute_tool()` 中、handler 执行前调用；需审批时由框架通过 UIBridge 弹窗，拒绝则返回 `__reject__` TOOL_CALL_RESULT
- `ResponseType.CONFIRM` 分支从 `App.run()` 移除；审批由框架层统一处理，不再由各 handler 自行调用 `get_bridge().confirm()`

**理由：**
- 交互逻辑集中在 tool handler 内，代码自包含，可读性高
- 加新交互类型（如文件选择、进度条、文本输入）只需 `UIBridge` 加方法，不改 `process()`/`App.run()`/`RequestType`
- 消除 `ConfirmMode` 在框架层的调度复杂度，工具自行决定是否需要用户交互
- 跨线程 Event 同步机制简单可靠，无队列/锁开销

**曾考虑的替代方案：**
- `RequestType.SELECT_RESPONSE` — 每加交互类型需改三处，扩展性差
- `ConfirmMode.SELECT` — ConfirmMode 职责膨胀，审批和选择是不同概念
- 在 `_execute_tool()` 内直接调用 questionary — questionary 必须在主线程运行，后台线程调用会崩溃

---

### 决策 85 — `__reject__` sentinel：switch 被拒后终止 agent loop

**背景：** `_should_confirm()` 恢复后，审批由 `_execute_tool()` 在 handler 执行前通过 UIBridge 统一处理。用户拒绝审批时需终止 agent loop 等用户输入，而非让 LLM 继续循环。

**决策：**
- `_execute_tool()` 审批被拒时返回 `__reject__` TOOL_CALL_RESULT：`event_payload={"__reject__": True, "reason": "用户取消了此操作"}`
- 同步设 `_pending_reject = True` → `process()` 检测 → 返回 FINISH → App 回外层循环
- `process()` CONTINUE 分支：append TOOL_CALL_RESULT → 检测 `_pending_reject` → 清标记 → 返回 `Response(FINISH, message="")` 
- App FINISH 分支：无 switch_agent → 渲染空消息 → break 内层循环 → 回外层等用户输入
- 下次 USER_INPUT 时 LLM 看到完整 TOOL_CALL + TOOL_CALL_RESULT(rejected) 链，正常继续

**理由：**
- 语义清晰：`__switch__` = 切换 handler，`__reject__` = 终止 loop
- TOOL_CALL 正常关闭（有 TOOL_CALL_RESULT），不留下悬空 tool_call 污染下次对话
- 与旧 CONFIRM 拒绝行为一致（取消 → 停止 → 等用户），用户体验不退化
- 实现最小化：只用 1 个 bool 标记 + 现有 FINISH 路径

**曾考虑的替代方案：**
- `{"rejected": True}` 作为普通 tool result（无终止）— LLM 可能重试 switch 或执行意外操作
- 不追加 TOOL_CALL_RESULT，直接 FINISH — 下次 LLM 看到悬空 TOOL_CALL，可能困惑
- 新增 `ResponseType.REJECTED` — 需改 App 分支，增加复杂度，FINISH 足够表达"本轮结束"

---

### 决策 86 — `MAIN_AGENT_KEY` 常量替换 magic string "main"

**背景：** 字符串 `"main"` 作为主 Agent 标识符分散在 4 个文件 6 处控制流中：`MainAgent._get_agent_key()`、`ToolRegistry._visible()`、`switch_tools` 的 agent/target、`App._get_handler()` 和 FINISH 分支。拼写错误或语义不一致会导致工具不可见或切换失败。

**决策：**
- 在 `src/agents/registry.py` 定义 `MAIN_AGENT_KEY = "main"`，作为唯一真实来源
- `MainAgent._get_agent_key()` → `return MAIN_AGENT_KEY`
- `switch_to_subagent` → `agent=[MAIN_AGENT_KEY]`
- `switch_to_mainagent` → `target=MAIN_AGENT_KEY`
- `App._get_handler()` → `name == MAIN_AGENT_KEY`
- `App.run()` FINISH 分支 → `response.switch_agent != MAIN_AGENT_KEY`
- `BaseAgent.__init__` → 调用 `ToolRegistry.get_for(..., main_key=MAIN_AGENT_KEY)` 传入
- **`tools/registry.py` 不直接 import `MAIN_AGENT_KEY`** — 通过 `get_for(..., main_key: str = "main")` 参数接收，保持 infrastructure 层不依赖 agents 层

**理由：**
- 单一真实来源，修改只需改一处
- `tools/registry.py` 通过参数接收（而非 import）保持依赖方向正确：agents → tools，不是 tools → agents
- 拼写错误在 IDE/类型检查阶段暴露，不会出现 `"main"` vs `"Main"` vs `"MAIN"` 的不一致

**曾考虑的替代方案：**
- 直接用 `"main"` 字面量 — magic string，分散，拼写风险
- 定义在 `tools/registry.py` — 语义上不属于 tool 系统
- `tools/registry.py` import `MAIN_AGENT_KEY` — 依赖方向反转，基础设施层不应依赖 Agent 层

---

### 决策 87 — 工具调用参数兼容性：忽略未知参数 + 校验必填

**背景：** LLM 偶尔在 tool_call 的 `event_payload` 中传入多余的参数（幻觉），之前 `**payload` 直接解包会导致 `TypeError: unexpected keyword argument`，工具执行失败。同时缺失必填参数时也应提前拦截，避免 handler 内部报错。

**决策：**
- `_execute_tool()` 在调用 handler 前通过 `inspect.signature(tool.handler)` 提取合法参数名
- 过滤掉 LLM 传入的未知参数（记 debug 日志），只传合法参数给 handler
- 校验必填参数（无默认值的参数），缺失时返回带 `arguments_schema` 的 error TOOL_CALL_RESULT，让 LLM 自修复
- `07_output_format.md` 的 `event_payload` 描述同步更新："仅需提供已声明的参数，多余参数会被忽略，但必填参数不得缺失"

**理由：**
- 防御性编程：LLM 的 tool_call 参数不能完全信任，框架层过滤比每个 handler 各自处理更可靠
- 多余参数静默忽略 + 必填参数显式报错，两端兼顾
- `inspect.signature` 是 Python 标准库，零依赖，handler 签名即参数定义 source of truth
- 错误附带 `arguments_schema` 让 LLM 有能力自修复（延续决策 46/67 原则）

**曾考虑的替代方案：**
- 不做过滤（`**payload` 直接解包）— LLM 偶尔传多余参数导致 TypeError 崩溃
- 每个 handler 内部做 `**kwargs` 捕获 — 散落各处，一致性差
- 在 `@tool` 装饰器阶段存储参数名列表 — 增加 Tool 字段，不如 inspect 直接读签名

---

### 决策 88 — Plan 机制作为通用基础设施

**背景：** M5 简历 Agent 需要多步骤执行（Parse → Plan → Execute → Generate），且学习 Agent、面试 Agent 后续也会有类似的多步骤任务需求。需要一套通用的计划/任务管理能力。

**决策：**
- Plan 放在 `BaseAgent` 层，3 个工具：
  - `create_plan(items: list[str])` — 创建有序 PlanItem 列表，第一条自动 IN_PROGRESS
  - `update_plan_status(id, status)` — 标记完成/取消，IN_PROGRESS → COMPLETED/CANCELLED 时自动激活下一条
  - `cancel_all_plans()` — 所有 PENDING + IN_PROGRESS → CANCELLED
- 全部免审批（内部操作，非关键路径）
- LLM 上下文通过 `system_message` 动态注入当前 IN_PROGRESS 的 plan item
- 生命周期：MainAgent plan 全程存活（dispatch 子 Agent 再切回不丢），子 Agent plan 随 return 丢弃
- PlanStatus 枚举：`PENDING / IN_PROGRESS / COMPLETED / CANCELLED`
- 用户干预：LLM 可单项取消（`update_plan_status(id, "cancelled")`）或全量重建（`cancel_all_plans` → `create_plan`）
- `tool_call_result` 自带当前状态（当前 item、下一项、是否全部完成），无需额外通知 LLM

**理由：**
- 通用基础设施避免每个子 Agent 各自实现计划管理
- system_message 动态注入比占位符更灵活，不破坏 LLM 缓存
- 两种干预粒度覆盖"跳过单项"和"推翻重来"两种场景
- 子 Agent plan 随 return 丢弃保持子 Agent 无状态原则

**曾考虑的替代方案：**
- 占位符 `{{ACTIVE_PLAN}}` 注入 — 每次 plan 变化都重建 system prompt，破坏 LLM 缓存
- `create_plan` 需用户审批 — 内部操作，审批打断 agent loop 不合理
- 全量重建作为唯一干预方式 — 过于粗暴，"跳过第 3 步"不应要求重建整个计划

---

### 决策 89 — 简历数据模型：结构化 Resume

**背景：** 简历 Agent 需要内部表示来表达简历内容，而非在纯文本上操作。

**决策：**
- 顶层 `Resume` → `BasicInfo` / `TechStack` / `WorkExperience` / `ProjectExperience` / `OtherInfo`
- `BasicInfo`：姓名、性别（男/女）、英文名（可选）、出生日期（年龄 property 反推）、电话、邮箱、GitHub（可选）、教育经历 `list[Education]`、自我评价 `list[str]`（≥3 条）
- `Education`：学位（本科/研究生/博士生）、学校、专业、起止时间（允许"至今"）
- `TechStack`：`dict[str, set[str]]`，动态扩展。预定义 4 个枚举 key（编程语言/数据库/开发工具/AI工具），仅编程语言必填
- `WorkExperience`：公司、起止时间（允许"至今"）、部门、职位、职责 `list[str]`（≥3 条）
- `ProjectExperience`：项目名、角色、起止时间、概述、技术栈、职责、成果
- `OtherInfo`：证书/语言能力/爱好，全可选，允许动态扩展
- LaTeX 模板（`CHN_Template.tex`/`EN_Template.tex`）不下沉为占位符替换，而是作为**样式参考**（preamble、字体、颜色、section 格式）。简历生成时根据数据模型动态构建 LaTeX
- 模板的固定数量占位符（如 `{-SUMMARY-1-}`~`{-SUMMARY-5-}`）不适合动态数据，改为数据驱动的循环生成

**理由：**
- 结构化表示能精确操作每个字段（如"修改技能栈"而非"修改简历第 3 段"）
- 动态 dict 支持用户自定义技能类别（如"框架""中间件"），不限于 4 个预定义 key
- 模板作为样式参考 + 数据驱动构建，比固定占位符替换更灵活，能处理多段教育/工作/项目
- 中文模板和英文模板语言不同但占位符结构相同，数据模型通用

**曾考虑的替代方案：**
- 纯文本操作 — 无法精确定位修改，LLM 容易遗漏或误改
- 固定占位符替换 — 不支持可变数量的教育/工作/项目经历
- 模板完全程控生成 — 丢失样式一致性，不如从参考模板提取样式

---

### 决策 90 — 简历 Agent Plan → Execute 处理模式

**背景：** 简历 Agent 的任务复杂度高于简单的问答 —— 需要解析简历、分析差距、逐步修改、最终生成输出。一次 LLM 调用无法完成。

**决策：** 四阶段流程：
1. **Parse** — 判断输入类型（文件路径 / 直接内容 / 空）→ 读文件或触发对话式构建 → 提取文本 → 结构化解析
2. **Plan** — `plan_resume_edits` 工具：分析简历 + JD → LLM 生成修改计划 → UIBridge 展示 → 用户确认 → `create_plan(items)`
3. **Execute** — Agent loop 按 plan 逐项推进，缺失信息时通过 UIBridge 询问用户
4. **Generate & Output** — 组装 LaTeX → `build_pdf` 编译 → 展示 PDF → 写入记忆模块

- ResumeAgent 内部循环：只要在处理简历就不退回 MainAgent
- 需要用户输入时通过 UIBridge（非退出 loop 的 ask_user）

**理由：**
- Plan → Execute 将"决定做什么"和"实际去做"分离，Plan 阶段可展示确认
- 内部循环保证多轮交互的连贯性（如连续修改多个 section）
- 复用 Plan 通用基础设施推进执行进度

**曾考虑的替代方案：**
- 一次性生成 — 复杂简历修改不可能一次 LLM 调用完成
- 每步退 MainAgent 等用户下一轮输入 — 打断连续性，用户需反复 dispatch

---

### 决策 91 — 工作区工具按权限边界拆分

**背景：** M5 需要文件系统操作工具（读/写/删/编辑/搜索）。需要决定工具粒度：拆分为独立工具还是合并。

**决策：**
- `workspace_read` — 读文件，免审批
- `workspace_search` — grep 搜索，免审批
- `workspace_fs` — write / delete / move（含重命名），默认审批
- `workspace_edit` — 字符串精确替换，默认审批
- `read_customer_file` — 读取外部用户文件（txt/md/docx/pdf），内部按扩展名分派解析器，`agent=["*"]` 排除 MainAgent
- 按权限边界拆分（读/搜索 免审批，写/删/编辑 需审批），而非按操作类型合并

**理由：**
- 权限边界决定工具边界 —— 同权限的合并，不同权限的拆分
- `workspace_fs` 合并 write/delete/move：都是文件系统变更操作，审批策略一致
- `workspace_edit` 独立：语义不同（替换 vs 全量写入），LLM 用例也不同
- `read_customer_file` 与 `workspace_read` 区分：前者读用户文件（支持 docx/pdf 解析），后者读工作区 Agent 生成的文件

**曾考虑的替代方案：**
- 全合为一个 `workspace` + action 参数 — schema 臃肿，LLM 选择困难
- 全部拆分（6 个独立工具）— 太碎，workspace_write/delete/move 无必要分开

---

### 决策 92 — RAG 查询拆分为 query_memory 和 query_reference_data

**背景：** 原有单一的 RAG 查询工具。记忆和参考数据访问权限应不同：MainAgent 可以查记忆但不应直接查参考数据。

**决策：**
- `query_memory` — 语义检索记忆，MainAgent + 所有子 Agent 可用
- `query_reference_data` — 语义检索参考数据，仅子 Agent 可用，MainAgent 不可用
- 两个工具均免审批

**理由：**
- MainAgent 是路由 Agent（决策 72），不应干预子 Agent 的领域任务（如从参考数据检索面试题）
- 权限分离让工具可见性矩阵更精细

**曾考虑的替代方案：**
- 单一 `query_rag` 工具 — 无法区分记忆和参考数据的访问权限
- MainAgent 也可查参考数据 — 违背路由 Agent 定位

---

### 决策 93 — 简历输入三路径 + LLM 判断

**背景：** 用户可能以多种方式提供简历：给文件路径、粘贴内容、或者没有现成简历需要从零构建。

**决策：**
- 路径输入 — `read_customer_file` 读文件
- 内容输入 — dispatch context 携带简历正文
- 对话式构建 — `start_resume_building` 工具：加载 `data/prompts/resume/collect_info.md` → `create_plan` → agent loop 逐项收集
- 初期由 LLM 自动判断输入类型，后期演进为 `@path` 语法
- 从记忆读取简历本次不做，预留规划

**理由：**
- LLM 判断简单灵活，三种路径差异明显（路径 vs 正文 vs 空），不易误判
- `@path` 语法对齐 Claude Code 的用户习惯，但初期先跑通 LLM 判断再优化
- 对话式构建由 Plan 机制保证顺序 + 模板保证内容完整，不由 LLM 自由发挥

**曾考虑的替代方案：**
- 独立 Router 判断输入类型 — 过度设计，LLM 原生能力足够
- 对话式构建纯 LLM 自由发挥 — 可能漏问必填字段，用户体验不一致

---

### 决策 94 — 结构化问题模板：collect_info.md + start_resume_building

**背景：** 对话式构建简历时，用户没有现成简历文件，需要 Agent 逐步询问收集信息（基本信息、技术栈、工作经历、项目经历、其他）。如果让 LLM 自由发挥，可能遗漏必填字段、询问顺序混乱、每次体验不一致。

**决策：**
- 将问题模板抽为独立文件 `data/prompts/resume/collect_info.md`，定义 5 个 section 各字段的必填/可选状态和提问措辞
- `start_resume_building` 工具（ResumeAgent 专属）：加载 `collect_info.md` → `create_plan` 创建 5 个有序 plan item → agent loop 逐项推进
- 每个 plan item IN_PROGRESS 时，system_message 注入对应 section 名，LLM 按模板中预定义的问题逐项询问
- Plan 机制保证顺序（基本信息 → 技术栈 → 工作经历 → 项目经历 → 其他），模板保证内容完整（必填字段全覆盖）

**理由：**
- 模板文件与代码分离，调整问题措辞不需要改代码
- Plan 机制保证执行顺序，不会出现"先问项目经历再问基本信息"的情况
- 必填/可选标注让 LLM 知道哪些可以跳过，减少不必要的追问
- 一致的询问体验，不管用户什么时候开始对话式构建

**曾考虑的替代方案：**
- LLM 自由发挥询问 — 可能遗漏必填字段（如教育经历），每次体验不一致
- 问题模板硬编码在 Python 代码中 — 调整措辞需改代码，与提示词分离原则相悖
- `collect_info.md` 放在 `general_agent/` 下 — 这是 ResumeAgent 专属的，不是通用 Agent 提示词

---

### 决策 95 — Plan 工具标准模式：context variable 访问 Agent

**背景：** Plan 工具最初实现在 `BaseAgent._build_plan_tools()` 中，通过闭包捕获 `self` 来访问 Agent 的 `_plan`。这与项目规范（所有工具放在 `src/tools/` 下、通过 `@tool` 装饰器注册）不一致。

**决策：**
- Plan 工具移至 `src/tools/plan_tools.py`，使用 `@tool` 装饰器注册（与其他工具一致）
- 通过模块级 context variable `_set_plan_agent()` / `_get_plan_agent()` 让工具 handler 访问当前 Agent 实例
- `BaseAgent._execute_tool()` 在调用 handler 前设置 context variable，finally 中清理
- 模式与 UIBridge 的 `_set_bridge()` / `get_bridge()` 完全一致

**理由：**
- 工具统一管理在 `src/tools/`，不破坏既有架构约定
- Context variable 是项目已验证的模式（UIBridge），无需引入新机制
- 闭包方案把工具逻辑耦合在 BaseAgent 中，不符合关注点分离

**曾考虑的替代方案：**
- 闭包捕获 `self` —— 工具在 BaseAgent 内部，无法被 ToolRegistry 全局管理，违反架构规范

---

### 决策 96 — Role 枚举化

**背景：** `Message.role` 字段此前为 `str` 类型，代码中散布 `role="user"`、`role="system"`、`role="assistant"` 裸字符串。

**决策：** 在 `src/message.py` 新增 `Role(StrEnum)`：`USER = "user"` / `SYSTEM = "system"` / `ASSISTANT = "assistant"`。`Message.role` 类型改为 `Role`，默认 `Role.USER`。所有文件中裸字符串替换为枚举值。

**理由：**
- `StrEnum` 继承 `str`，JSON 序列化后仍为 `"user"` 等字符串，与 LLM 交互无摩擦
- IDE 自动补全 + 静态类型检查，拼写错误在编写阶段暴露
- 与 `EventType(StrEnum)`（决策 56）风格一致

**曾考虑的替代方案：**
- 保持 `str` + 常量 —— 无类型约束，枚举更安全

---

### 决策 97 — SYSTEM_MESSAGE role 分类

**背景：** 此前所有 `event_type=SYSTEM_MESSAGE` 的消息统一使用 `role="user"`。但系统提示有两类：纠错类（JSON 格式错误、未知工具）和正常上下文类（plan 进度、退出提示）。纠错类应以 system role 发送，让 LLM 明确区分"框架指令"和"用户内容"。

**决策：**
- 纠错类 SYSTEM_MESSAGE → `Role.SYSTEM`：output_format 格式注入、message=None 修复提示、未知工具列表
- 正常上下文 SYSTEM_MESSAGE → `Role.USER`：plan 进度注入、`/exit_sub` 退出提示
- 外层 OpenAI API 消息格式跟随 `Message.role`：`{"role": "system", "content": "..."}`

**理由：**
- 纠错信息是框架层面的，不应伪装为 user 消息
- System role 使 LLM 天然区分框架指令和用户输入，降低混淆
- Plan 上下文和退出提示是业务流程的一部分，保持 user role 更自然

**曾考虑的替代方案：**
- 所有 SYSTEM_MESSAGE 都改为 `Role.SYSTEM` —— 过度，plan 进度和退出提示不属于框架纠错

---

### 决策 98 — list[str] schema 自动生成 items 类型

**背景：** `_build_arguments_schema()` 对 `list[str]` 类型参数只输出 `"type": "array"`，不包含元素类型信息。LLM 不知道数组元素是 string 还是 object，容易猜错（如将 `["a", "b"]` 误构为 `{"description": ["a", "b"]}`）。

**决策：** `_build_arguments_schema()` 对 `list[X]` 类型（通过 `get_origin` / `get_args` 解析）自动生成 `"items": {"type": "X"}`。仅处理一层（`list[str]` → `items: {type: string}`），不递归处理嵌套泛型。

**理由：**
- LLM 需要明确知道数组元素类型才能正确构造参数
- 一层处理覆盖所有当前用例（create_plan 的 `list[str]`）
- `plan_tools.py` 移除 `from __future__ import annotations` 以确保类型标注在运行时是可解析对象而非字符串

**曾考虑的替代方案：**
- 在 `input_schema` 中手写 `items` —— 冗余，应自动推断
- 递归处理嵌套泛型 —— 当前无使用场景，过度设计

---

### 决策 99 — message=None 走 retry 而非静默兜底

**背景：** LLM 偶尔返回 `{"event_type": "finish", "message": null}`，导致 `Markdown(None)` crash。最初考虑在 `from_llm_reply()` 中静默替换为 `""`，但 `message` 是 required 字段，静默兜底掩盖了 LLM 的格式遵从问题。

**决策：** `process()` 中解析成功后检查 `llm_msg.message is None` → 注入 `output_format` 提示 → `continue`（retry）。不修改 `from_llm_reply()` 的逻辑。

**理由：**
- `message` 是 required 字段，null 视为格式错误
- 走与 JSON 解析失败相同的 retry 路径，保持错误处理一致性
- LLM 自修复能力已验证（JSON parse error retry），复用到 message=None 场景
- App 层加 `response.message or ""` 防御作为安全网

**曾考虑的替代方案：**
- 在 `from_llm_reply()` 静默替换为 `""` —— 掩盖 LLM 输出质量问题

---

### 决策 100 — Sticky plan 阻塞：questionary + Live 终端冲突

**背景：** 希望实现常显的 plan 面板（Phase 3），使用 `rich.Live` + `Layout` 将终端分为固定 plan 区域和滚动对话区。但 `questionary` 底层使用 `prompt_toolkit` 接管终端输入，与 `rich.Live` 争抢终端控制权。

**决策：** Phase 3 暂缓。保持 Phase 2 方案：在每次 FINISH、PROGRESS 和 questionary 输入前静态重打印 plan 面板。面板在所有项完成后自动隐藏。等后续有充分时间再评估替代方案（如换用 `prompt_toolkit` 原生 layout 或 `textual`）。

**理由：**
- `rich.Live` 和 `prompt_toolkit` 都直接操作终端 buffer，无法和平共存
- 频繁重打印在当前使用频率下视觉上可接受
- 这是 UI 优化，不是功能阻塞，不应拖慢 M5 核心功能

**曾考虑的替代方案：**
- 换用 `rich.prompt.Prompt` —— 失去 autocomplete 和 `/` 命令补全
- 换用 `textual` TUI 框架 —— 引入重依赖 + 大量重构
- 直接用 ANSI escape 手动管理 scroll region —— 脆弱、跨平台兼容性差

---

### 决策 101 — workspace_fs 拆分为三个独立工具

**背景：** 决策 91 将 write/delete/move 合并为 `workspace_fs` + action 参数。在详细设计中重新评估后，三者参数差异太大（write 需要 content、delete 不需要、move 需要 src+dst），合并会导致 schema 臃肿。

**决策：** 拆分为 `workspace_write` / `workspace_delete` / `workspace_move` 三个独立工具。三者均为 `ConfirmMode.CONFIG`（默认审批），所有 Agent 可见。

**理由：**
- write 入参 `path + content`，delete 入参 `path`，move 入参 `src + dst` — 合并后 LLM 需理解哪些参数在哪个 action 下有效
- 独立工具 schema 清晰，LLM 选择准确
- 三者在审批策略上一致，但在语义上足够不同，值得分开

**曾考虑的替代方案：**
- 保持合并（决策 91） — schema 臃肿，LLM 选择困难

---

### 决策 102 — workspace_search 拆分为 grep + search_file

**背景：** 决策 91 定义的 `workspace_search` 同时承担内容搜索和文件查找两个职责。两者目的不同：一个搜文件内容，一个按文件名找文件。

**决策：** 拆分为 `workspace_grep`（内容搜索，结构化输出对齐 workspace_read）和 `workspace_search_file`（文件名 glob 匹配，返回路径列表）。两者均为 `ConfirmMode.NEVER`。

**理由：**
- 内容搜索返回 `{files: [{path, matches: [[num, str]]}]}`，文件名搜索返回 `{files: [str]}` — 结构天然不同
- 分离后 LLM 使用路径更清晰：先 `search_file` 定位文件，再 `grep` 搜索内容，再 `read` 获取上下文

---

### 决策 103 — workspace_read 结构化输出：行号 + 内容数组

**背景：** `workspace_read` 需要为 `workspace_edit` 提供精确的行号和内容用于校验替换。

**决策：**
- 返回 `lines: [[int, str]]`（JSON array-of-arrays），行号 1-indexed，保持原始行号不受 offset 影响
- `offset` 起始行号，`limit` 默认 100 行，`truncated` 标记未读完
- 编码检测使用 `charset-normalizer`

**理由：**
- `[[num, str]]` 比 `[{n, c}]` 紧凑，减少 token 消耗
- 行号不变使 edit 可直接复用
- `truncated` 引导 LLM 分段读取大文件

---

### 决策 104 — workspace_edit 批量编辑 + 倒序处理 + old_content 校验

**背景：** 对已有文件的修改需要防止 LLM 幻觉导致文件损坏。

**决策：**
- `replace`（替换当行）和 `insert_after`（行后插入）合并为一个工具
- 每条 edit 必须提供 `line` + `old_content`（原始行内容），行号 + 内容双重匹配才执行
- `line=0` 仅限 `insert_after`（插入文件开头），此时不校验 `old_content`
- 支持批量 edits，所有 edit 引用编辑前的原始行号，系统内部按行号降序处理
- 任何一条校验失败全量回滚，文件不做任何修改（原子性）

**理由：**
- old_content 校验防止 LLM 幻觉（行号漂移、内容混淆）
- 倒序处理避免行号漂移，LLM 不需要自己算偏移
- 原子性保证文件不被部分破坏

---

### 决策 105 — read_customer_file 绝对路径 + 统一输出格式

**背景：** 用户简历文件可能在系统任意位置，且格式多样（txt/md/pdf/docx）。

**决策：**
- 必须绝对路径（跨平台适配），无沙箱校验
- 所有格式统一输出 `{path, format, total_lines, offset, limit, truncated, lines: [[num, str]]}`
- PDF 用 pdfplumber 提取文本后按 `\n` 拆分为行，DOCX 用 python-docx 同理
- 仅支持 `.docx`，不支持旧版 `.doc`（二进制 OLE 无纯 Python 方案）
- 不做 OCR

**理由：**
- 绝对路径避免 Agent 工作目录不确定性
- 统一输出让 LLM 无需根据格式猜测返回结构
- `.doc` 需 LibreOffice 系统依赖，太重

---

### 决策 106 — ToolCallException 统一工具异常

**背景：** 当前工具 handler 直接抛出 `ValueError`/`FileNotFoundError` 等裸异常，LLM 收到的错误信息缺乏结构化的上下文和修复建议。

**决策：** 引入 `src/tools/exceptions.py`，定义 `ToolCallException(Exception)`，包含 `message`（面向 LLM 的错误描述）和 `suggestion`（可选修复建议）。`BaseAgent._execute_tool()` 统一捕获并包装为 tool_call_result 喂回 LLM。所有 workspace 工具和 `read_customer_file` 使用此异常替代原始异常。

**理由：**
- 给 LLM 足够的上下文自修复（当前架构依赖此机制，见决策 46）
- 统一的异常类型便于 `_execute_tool()` 区分"预期内的工具错误"和"框架 bug"
- suggestion 字段给 LLM 明确的修复方向

---

### 决策 107 — Agent key 常量统一管理

**背景：** Agent 标识符散落在 main.py、workspace_tools.py 等多处作为裸字符串，修改时容易遗漏。

**决策：** 在 `src/agents/registry.py` 统一管理所有 Agent key 常量：`MAIN_AGENT_KEY = "main"`、`RESUME_AGENT_KEY = "resume"`、`JOB_SEARCH_AGENT_KEY = "job_search"`、`INTERVIEW_AGENT_KEY = "interview"`。所有代码引用常量而非裸字符串。

**理由：**
- IDE 自动补全 + 静态检查，拼写错误在编译期暴露
- 新增 Agent 时只需改 registry.py
- 与 `MAIN_AGENT_KEY`（决策 86）风格一致

---

### 决策 108 — workspace 工具限定 ResumeAgent

**背景：** 工作区文件操作是简历定制的专属能力，不应暴露给路由 Agent（MainAgent）或其他子 Agent。

**决策：** 所有 workspace 工具 `agent=[RESUME_AGENT_KEY]`，仅 ResumeAgent 可见。JobSearchAgent 等其他子 Agent 不可用工作区工具。

**理由：**
- MainAgent 是路由 Agent（决策 72），不应操作文件
- 职位搜索 Agent 只需要搜索结果展示，不需文件系统
- 未来如需给其他 Agent 开放，改 `agent` 列表即可

---

### 决策 109 — workspace_list 单层不递归

**背景：** 设计阶段没有 list 工具。Agent 需要了解工作区结构。

**决策：** 新增 `workspace_list`（免审批，ResumeAgent 专属），单层目录列表不递归。底层 `file_reader.list_directory()`。

**理由：**
- 递归输出过大，Agent 应当逐层探索而非一次拿到全部
- 与 `ls` 默认行为一致，直觉

---

### 决策 110 — workspace_replace 全文字符串替换

**背景：** `workspace_edit` 行级精确校验门槛高，LLM 做简单全局替换（如"Python" → "Python 3"）不需要 reads + 逐行 edits。

**决策：** 新增 `workspace_replace`（`ConfirmMode.CONFIG`），全文件匹配字符串并全部替换，返回替换次数。`old_str` 不存在时不报错返回 0。

**理由：**
- 简单替换场景用 replace 即可，不必走 search → read → edit 完整流程
- 降低 LLM 使用门槛，减少 tool call 次数

---

### 决策 111 — RAG 查询工具用 StrEnum 校验 filter

**背景：** `query_memory` 和 `query_reference_data` 接受 LLM 传入的 filter 参数，需要确保值与 Chroma metadata 约定一致。

**决策：**
- 定义 `MemoryType(StrEnum)`（FACT / PREFERENCE）和 `ReferenceCategory(StrEnum)`（6 个子目录名）
- 枚举值标注依赖文件（`MemoryType` → `builder.md` + `schemas.py`；`ReferenceCategory` → `data/reference/` 子目录）
- LLM 传入无效值时 `ToolCallException` 附带可选值列表

**理由：**
- 枚举保证 LLM 传入值和 metadata 约定同步
- 修改枚举时提醒同步更新相关文件
- 无效值直接反馈给 LLM 让 GAI 自修复

---

### 决策 112 — workspace_edit 简化为纯 replace 模式

**背景：** 原 workspace_edit 有 replace 和 insert_after 两个 action，LLM 需理解 action 字段语义，且同 line 的 replace+insert_after 有排序问题。

**决策：** 简化为纯 replace：每 edit 仅 {line, old_content, content}。content 可含 `\n` 实现多行（行前插入 = content="new\nold"，行后插入 = content="old\nnew"，删除 = content=""）。系统按行号降序处理。

**理由：**
- LLM 不需要学习 action 字段
- 用 `\n` 控制插入语义更自然
- 避免同行 replace+insert_after 排序问题

---

### 决策 113 — copy_template 用户交互前置到 LLM

**背景：** copy_template 需要确认语言、文件名前缀、是否覆盖已有文件。

**决策：** 这些确认由 LLM 在调用工具前完成，工具本身只做参数校验和复制。LLM 应先确认语言和文件名前缀、检查已有文件、确认删除，再调用 copy_template。

**理由：**
- 工具职责单一（复制文件）
- 用户交互由 LLM 灵活处理
- 工具抛 ToolCallException 时 LLM 能自行处理

---

### 决策 114 — 简历构建改为 workspace 工具直接编辑 LaTeX

**背景：** 原计划用 schema-based 工具（`set_basic_info` / `set_education` 等）结构化填充 Resume 对象再生成 LaTeX。实现后发现 schema 定义复杂、LLM 易填错、灵活度不够。

**决策：** 放弃 schema 模式，改为 LLM 用 workspace 工具（read / edit / replace）直接操作 LaTeX 模板文件。ResumeAgent 提示词中说明模板占位符，LLM 逐项替换。

**理由：**
- LaTeX 模板已有占位符（如 {-NAME-}），直接用 workspace_replace 替换即可
- LLM 对大段文本编辑的能力足以胜任
- 避免重复维护 schema 和 LaTeX 两套映射

---

### 决策 115 — `/dump` 命令导出对话历史用于调试

**背景：** 对话中出现上下文丢失问题，需要分析历史消息。

**决策：** `src/utils/dumper.py` + `BaseAgent.dump_history()` + CLI `/dump` 命令。将当前 Agent 的 `_history` 序列化为 JSON 写入 `data/logs/<agent>_<datetime>_message.dump`。

**理由：**
- 导出完整对话历史可离线分析
- CLI 命令用户可随时触发
- JSON 格式便于脚本处理

---

### 决策 116 — PLACEHOLDER.txt 升级为 README.md

**背景：** copy_template 伴随复制的 `PLACEHOLDER.txt` 仅包含占位符对照表，不足以指导 LLM 正确填充模板。随着模板结构复杂度增加（教育多条目、技能 PRO/OTHER 拆分、各节条数约束、日期格式规范等），需要一份完整的操作手册。

**决策：** 将 `PLACEHOLDER.txt` 升级为 `README.md`，包含三部分：(1) 模板章节结构概览；(2) 完整占位符清单与说明；(3) 填充约束与边界处理指南。`copy_template` 函数常量 `_PLACEHOLDER_FILE` → `_README_FILE`，工具描述同步更新。

**理由：**
- LLM 在复制模板后立即 `workspace_read(README.md)` 即可获得完整操作指引
- 约束集中管理，修改模板后只需更新 README.md 无需改 Agent prompt
- README.md 作为独立文件可被用户直接阅读和编辑

---

### 决策 117 — Agent temperature 分层设置

**背景：** 项目所有 LLM 调用均未设置 `temperature`，依赖 provider 默认值。不同 Agent 对确定性的需求不同（路由 vs 内容生成 vs 记忆提取）。

**决策：**
- MainAgent（路由/调度）：`temperature=0.1`，`response_format=json_object`
- JobSearchAgent（搜索分析）：`temperature=0.2`，`response_format=json_object`
- ResumeAgent（简历定制）：`temperature=0.2`，`response_format=json_object`
- MemoryBuilder（记忆提取）：`temperature=0`，`response_format=json_object`

**理由：**
- 路由 Agent 需要最高确定性，避免错误调度
- 内容生成 Agent 需要少量创造性（0.2），但保持可控
- 记忆提取是纯信息抽取任务，需要完全确定性
- 通过 `_pro_params` 类变量设置，`kwargs` 仍可覆盖

---

### 决策 118 — 删除 LLMHandler

**背景：** `LLMHandler` 是 M1 阶段的 demo handler，在 M4 引入 `MainAgent` 后已被完全替代（见 task.md 阶段 4 任务 1）。代码保留在 `src/cli/handler.py` 中，占 ~100 行，依赖 `LLMClient`、`PromptLoader`、`EventType`、`Role` 等模块。

**决策：** 删除 `LLMHandler` 类及 `src/cli/__init__.py` 中的导出。保留 `Handler` 抽象基类和 `_parse_llm_reply()` 静态方法（仍被 `BaseAgent` 使用）。

**理由：**
- 消除死代码，降低维护负担
- 减少不必要的模块依赖
- `MainAgent` 已稳定运行，无回退需求

---

### 决策 119 — plan_status 每轮注入替代一次性 PLAN 消息

**背景：** 原 plan 注入为一次性 `[PLAN] 当前任务 [1/3]: ...` 消息，仅在新任务激活时注入一次，LLM 容易在多轮对话后遗忘计划上下文。

**决策：** 新增 `PlanStatusInfo` 数据结构（current/completed/remaining），`_to_openai()` 每轮将序列化后的 plan_status JSON 注入 system prompt 末尾。移除 `_last_injected_plan_id` 标记机制。

**理由：**
- 每轮注入确保 LLM 始终可见计划全貌而非仅当前任务
- system prompt 注入比 _history 消息更可靠（不会被压缩或遗忘）
- 简化注入逻辑，减少状态管理

---

### 决策 120 — workspace_edit 读后编辑守卫

**背景：** LLM 可能凭历史上下文中的文件内容进行编辑，导致 old_content 校验失败或编辑错行。

**决策：** 模块级 `_read_files: set[str]` 集合。`workspace_read` 后将文件绝对路径加入集合；`workspace_edit` 前检查集合是否存在，未命中则抛 `ToolCallException` 提示先 read；edit 成功后从集合中移除（一次 read 对应一次 edit）。

**理由：**
- 强制 LLM 编辑前获取最新文件内容
- 消费机制确保每次 edit 后需重新 read，避免连续编辑导致行号漂移
- 代码层面兜底，不依赖 prompt 约束

---

### 决策 121 — workspace_delete 批量删除

**背景：** 原 `workspace_delete` 每次只能删除一个路径，删除多个文件（如编译产物 .aux/.log/.out）需要多次调用。

**决策：** 入参从 `path: str` 改为 `paths: list[str]`，返回 `{"deleted": [...], "errors": [...]}`，单个路径失败不中断其他路径。

**理由：**
- 减少 tool call 次数
- 错误不中断批量操作，LLM 可从 errors 字段了解失败原因

---

### 决策 122 — CLI 命令注册改用 `_COMMAND_HELP` dict + `/help` 命令

**背景：** CLI 命令原先以 flat list `_COMMANDS` 注册，欢迎信息中逐一手写命令说明，新增命令需同步改三处（list、dispatch 分支、欢迎信息），且命令说明散落在欢迎字符串中。

**决策：**
- 用 `_COMMAND_HELP: dict[str, str]` 替代 flat `_COMMANDS` list，命令名 → 描述集中管理
- `_COMMANDS` 由 `list(_COMMAND_HELP.keys())` 自动生成
- 新增 `/help` 命令，遍历 `_COMMAND_HELP` 打印所有命令说明
- 新增 `/auto-approve-switch [on|off]` 命令，运行时修改 `config.TOOL_CONFIRM_ENABLED`（`SimpleNamespace` 可变，`_should_confirm()` 每次读取即时生效）
- 欢迎信息从一长串简化为 `输入 /help 查看所有命令`

**理由：**
- 单一数据源：加命令只需加一条 dict entry，自动获得 tab 补全 + help 文档
- `/help` 自文档化，无需在欢迎信息中堆砌所有命令
- `/auto-approve-switch` 利用 config `SimpleNamespace` 运行时可变特性，无需重启

**曾考虑的替代方案：**
- 保持 flat list + 手写欢迎信息 —— 新增命令改多处，容易遗漏
- 单独维护 help 文本 —— 与命令列表不同步的风险

---

### 决策 123 — 会话状态管理模块（auto-save / restore / rollback）

**背景：** `/dump` 命令只能手动导出对话历史用于调试，缺乏自动持久化和恢复能力。用户希望在每次 LLM FINISH 后自动保存会话状态，支持崩溃恢复和跨会话回滚。

**决策：**

- **模块位置**：新建 `src/utils/saver.py`，包含底层函数（`save_messages` / `load_messages` / `save_session_meta` / `list_sessions`）和高层 `SaveManager` 类
- **存储结构**：`data/save/{session_id}/` 目录，`main.json` + `{agent_key}.json` + `session.json`（元数据 + plan 状态）
- **Session ID**：`App.__init__` 时生成 `yyyyMMddHHmmss` 格式 ID，由 `SaveManager` 管理
- **Auto-save 时机**：每次 LLM FINISH 时自动保存（`App._auto_save()` → `SaveManager.save()`）
- **延迟子 Agent 清理**：sub→main 时不立即删除 sub 存档，而是设 `pending_sub_cleanup` 标记；等 main 下次 FINISH 成功保存后再删除 sub 存档和对应 plan，避免崩溃丢数据
- **`/restore` 命令**：无参数时 `questionary.select` 按 mtime 倒序列出存档；带 session_id 直接恢复。恢复时重建 `_history` + `_plan`，如有 sub 存档则切换 handler
- **Plan 持久化**：`session.json` 中按 `{agent_key}_plan` 分字段存储 `PlanItem` 列表，save 时写入当前 agent 的 plan 并保留其他 agent 的 plan，restore 时装载回 `_plan`
- **Message 序列化**：`Message.from_dict()` 支持从 `dataclasses.asdict()` 输出重建，含 `plan_status`；`PlanStatusInfo.from_dict()` 递归重建
- **全量覆盖写入**：每次 save 覆盖对应 JSON 文件，为后续 rollback 功能预留（每条 FINISH 一个快照）
- **后续扩展**：rollback 到上一句话（上一条 FINISH 对应的 save）

**理由：**
- 状态管理独立模块，不耦合到 App 或 BaseAgent
- 目录结构清晰，一个 session 一个目录，人可浏览
- 延迟清理保证 sub→main 切换窗口期不丢数据
- Plan 随对话历史一起持久化，restore 后 LLM 继续执行原有计划

**曾考虑的替代方案：**
- 在 `BaseAgent` 中实现 save/restore —— App 层耦合，Agent 不应感知文件系统
- 每次 FINISH 保留 diff 而非全量覆盖 —— 复杂度高，rollback 时需 apply 一系列 diff，出错概率大
- sub 存档立即删除 —— 崩溃窗口风险，已拒绝

---

### 决策 124 — RAG 模型加载本地缓存优先（local_files_only 回退策略）

**背景：** `SentenceTransformer` / `CrossEncoder` 默认每次实例化都向 HF Hub 发 HEAD 请求校验缓存元数据（`adapter_config.json` 等），镜像站（hf-mirror.com）偶发 504 时触发 5 轮指数退避重试，严重拖慢 RAG 启动甚至失败。

**决策：**
- `src/rag/embedder.py` 和 `src/rag/reranker.py` 加载模型时先传 `local_files_only=True`（纯读本地缓存，零 HTTP 请求）
- 抛异常（缓存未命中）时 try/except 回退为默认联网下载
- 首次运行仍可自动下载模型；之后每次启动零网络依赖

**理由：**
- 常态路径（模型已缓存）完全离线，504 问题消失，加载耗时从数次 HEAD 请求等待降至 Embedder 0.3s / Reranker 2.1s
- 回退分支保证首次运行和换模型场景不受影响
- 防御性编程：不依赖网络可用性假设

**曾考虑的替代方案：**
- 全局 `HF_HUB_OFFLINE=1` 环境变量 —— 首次运行（或换模型后）直接失败，无自动回退，已拒绝
- 调小 `HF_HUB_ETAG_TIMEOUT` —— 仍然发请求，只是快速失败，治标不治本

---

### 决策 125 — plan_status 落地到 Message 对象

**背景：** `plan_status` 原本只在 `_to_openai()` 中拼接 JSON 到 system prompt 末尾，从未写入 `Message.plan_status` 字段。导致保存的 `main.json` 中每条消息的 `plan_status` 全是 null，restore 后丢失每轮对话的 plan 上下文。

**决策：**
- 移除 `_to_openai()` 中 system prompt 末尾的 `[PLAN_STATUS]` JSON 拼接
- 新增 `BaseAgent._stamp_plan_status(msg)` 方法，在 `process()` 每次 `_history.append()` 前调用 `_build_plan_status_info()` 写入 `Message.plan_status`
- Stamping 点：USER_INPUT、TOOL_CALL_RESULT、LLM reply（TOOL_CALL / FINISH）
- `Message.to_json()` 通过 `dataclasses.asdict()` 自动序列化 `plan_status`，落盘后每条消息带有对应时刻的 plan 快照
- 全部 plan 项 cancelled/completed 时 `_auto_save()` 传 `None`，同时从 `session.json` 清除 `{agent_key}_plan`

**理由：**
- 语义正确：每条消息携带当时 plan 状态，restore 后 LLM 能看到历史 plan 轨迹
- 解耦 system prompt：plan 信息不再混在文本中，由 Message 对象化承载
- 保存后 `main.json` 完整自描述，不依赖外部上下文

**曾考虑的替代方案：**
- 仅在 save 时批量回填 plan_status —— 时序不准，每轮 plan 状态可能不同
- 保留 system prompt 拼接 + 同时写 Message —— 冗余，LLM 收到两份 plan 信息

---

### 决策 126 — Restore 恢复上下文预览

**背景：** `/restore` 选择时用户看不到存档对应的对话内容，恢复后也没有任何上文提示。

**决策：**
- **preview 字段**：`SaveManager.save()` 从 history 提取首条 `USER_INPUT` 消息（截断 60 字符），写入 `session.json` 的 `preview` 字段；`list_sessions()` 透传
- **choice title 渲染**：`_restore_interactive()` 在每条 choice 中追加 `"{preview}"`
- **上下文面板**：`_do_restore()` 恢复后调用 `_render_context_recap()`，倒取最后 5 条非 `SYSTEM_MESSAGE` 消息，除最后一条外截断 80 字符，纯文本输出（不用 Panel，避免 rich 换行破坏布局）
- **最后一条不截断**：确保最近的对话内容完整展示
- **分隔线**：最后一条前加 `──` 视觉分隔

**理由：**
- 用户选择存档前能看到对话概要（preview），恢复后能看到上文，不需要盲选
- 纯文本渲染避免 Panel 宽度限制导致长消息换行破坏 `>` 前缀布局
- `rich.text.Text` + `escape()` 比 inline markup 更可靠

**曾考虑的替代方案：**
- Panel 渲染 —— 长消息换行后 `>` 孤零零悬挂，视觉效果差
- 显示全部消息不截断 —— 终端被占满

---

### 决策 127 — plan_status 简化 schema

**背景：** `Message.plan_status` 原本存完整 `PlanStatusInfo` 对象（含 `PlanItem` 的 `id`/`description`/`status`/`order`），每条消息的 JSON 臃肿，LLM 阅读效率低，多轮 tool_call 中难以持续关注 plan 状态。

**决策：**
- 新增 `plan_to_simple(plan_items) -> dict | None`：将 `PlanItem` 列表转为 `{current: "序号|任务名" | null, completed: ["序号|任务名"], remaining: ["序号|任务名"]}` 字符串格式
- `Message.plan_status` 类型从 `PlanStatusInfo | None` 改为 `dict | None`
- 删除 `PlanStatusInfo.from_dict()`，`Message.from_dict()` 直接透传 dict
- 删除 `_build_plan_status_info()`，`_stamp_plan_status()` 改为调用 `plan_to_simple()`
- 同步更新 `08_input_format.md` 中 `plan_status` 的 schema 描述
- `session.json` 中 plan 恢复不受影响（仍用 `PlanItem` 列表）

**理由：**
- 简化格式大幅减少 token 消耗，LLM 更容易关注 plan 状态
- 纯 dict 无需 dataclass 重建，序列化/反序列化更简单
- 序号+任务名字符串已足够 LLM 理解 plan 全貌，不需要 `id`/`status` 等详细字段

**曾考虑的替代方案：**
- 保持 `PlanStatusInfo` 并只改序列化 —— 类型系统和 LLM 视角不一致，维护两份 schema
- plan_status 注入 system prompt —— 导致每次 prompt 变化、缓存不命中，已拒绝
- 过滤 tool_call 消息 —— 丢失工具调用上下文，已改为只过滤 SYSTEM_MESSAGE

---

### 决策 128 — replan 工具（保留已完成项）

**背景：** LLM 在执行计划过程中可能发现剩余步骤不再适用，需要修订。`cancel_all` + `create_plan` 组合会丢掉已完成步骤且需两次工具调用。

**决策：**
- 新增 `replan` 工具（`plan_tools.py` 第 4 个）：接收新步骤列表，保留 `COMPLETED` 项，替换未完成项
- 新增 `BaseAgent._replan(items)`：保留已完成项（含原 id/description/status/order），取消其余，新项序号接续，首项自动 `IN_PROGRESS`
- `update_plan_status` 的 `use_when` 强化：任何计划状态变化必须先更新再继续

**理由：**
- 一次工具调用完成修订，比 cancel_all + create 少一轮 LLM 往返
- 保留已完成项维护执行轨迹，后续决策有据可查
- 语义明确：replan 修订剩余计划 vs cancel_all 彻底放弃

**曾考虑的替代方案：**
- LLM 手动 cancel_all + create —— 多一轮工具调用，且丢失已完成历史

---

### 决策 129 — /rewind 命令（内存级回退 + ↑↓ 输入历史）

**背景：** 原 rollback 设计（决策 123）规划为"每次 FINISH 全量快照，通过 CLI 命令回退到前一次 FINISH"，依赖文件存储的多版本管理。实际实现时发现方案过重——用户真正需要的是"回到某个输入点重来"，而非文件级版本回溯。

**决策：**

- **`/rewind` 命令**：纯内存操作，通过 CLI 命令触发，列出当前 Agent `_history` 中所有 `USER_INPUT` 消息供用户选择；选中后预填文本到 CLI（`_pending_prefill`），用户可编辑或直接回车确认后才截断 `_history` 到选中位置之前
- **预填机制（`_pending_prefill`）**：App 级状态字段，输入循环顶部检测并传入 `questionary.text(default=)`，回车后清除；可复用于 ↑↓ 输入历史和 `/rewind`
- **↑↓ 输入历史导航**：通过 `prompt_toolkit.KeyBindings` 注入到 questionary prompt，`~has_completions` filter 确保 autocomplete 下拉可见时 ↑↓ 导航菜单、不可见时导航输入历史，互斥
- **不涉及文件存储**：重新设计后 `/rewind` 完全在内存中操作 `_history` 截断，不碰 `data/save/`
- **取消路径**：select 阶段末尾有 `── 取消 ──` 选项 + Ctrl+C；预填编辑阶段 Ctrl+C / 空回车均可取消，history 不截断
- **Restore 集成**：`/restore` 恢复会话后调用 `_populate_input_history()`，从恢复的 `_history` 提取 USER_INPUT 填充 `_input_history`

**理由：**
- 用户需求是 CLIG 级别的"回到某句话重来"，不是 VCS 级别的文件快照回退
- 纯内存操作零 IO 开销，实现简单（仅 `app.py` 改动）
- 预填 + 确认的两段式流程给用户安全网：select 可取消、编辑阶段也可取消
- `_pending_prefill` 机制通用化，后续 ↑↓ 输入历史可直接复用

**曾考虑的替代方案：**
- 基于文件快照的 rollback（原设计）—— 需要多版本文件管理，复杂度高，用户实际不需要
- `/rewind` 仅在子 Agent 可用 —— 用户实际使用中发现主 Agent 也有回退需求，已取消限制
- 在 select 后直接截断 history 再预填 —— 用户反馈无法取消，改为先预填确认再截断

---

### 决策 130 — Esc 中断 Agent 处理（基础完成，即时中止暂缓）

**背景：** 当工具不需要审批或用户切换审批模式后，Agent 自动连续执行工具，用户无法中断。需要按 Esc 键让 Agent 立即停下返回输入提示符。

**决策：**

- **Cancel 标志用 `threading.Event`** — 放在 `src/cli/uibridge.py` 模块级，与 `_current_bridge` 同模式：`_cancel_event` + `_set_cancel()` / `_clear_cancel()` / `is_cancelled()`。`threading.Event` 是内核级同步原语，`set()` 后跨线程立即可见，不需要额外锁
- **Esc 检测在主线程 spinner loop 中** — 非阻塞轮询（Windows `msvcrt.kbhit()` / Unix `select`+`tty.setraw`），只在无 bridge request 时检测（避免与确认弹窗的 questionary 冲突）
- **三个 Cancel 检查点** — 在 `BaseAgent.process()` 中：
  1. while 循环开始 — `_pending_tool` 已清除，历史一致
  2. LLM 调用返回后 — LLM 回复未写入 history，丢弃无副作用
  3. **工具执行前（关键）** — 注入合成 TOOL_CALL_RESULT（`__cancelled__: True`）告知 LLM 工具未执行。因为上轮 LLM 返回的 TOOL_CALL 已在 history 中，必须闭环
- **即时中止（关闭 httpx transport）暂缓** — 按 Esc 时若 daemon 线程正阻塞在 `chat_pro()` 的 httpx socket read 中，需等 API 返回（10-30s）。理想方案：主线程调 `OpenAI.close()` 关闭底层 httpx transport → socket 断开 → 异常在 ~50ms 内传播到 `process()` → 返回 FINISH。**但这需要 LLMClient 从设计之初就暴露 abort 作为一等公民 API**，当前 `LLMClient` 的 `OpenAI` SDK 是内部黑盒，事后打洞关闭 transport 属于侵入式修改。详见 `docs/design.md#417-agent-中断机制`

**理由：**
- `threading.Event` 模式已在 UIBridge 验证，跨线程通信零学习成本
- 三个检查点覆盖了 agent loop 中所有可安全中断的位置，数据一致性由检查点位置保证（非 LLM 调用阶段都能 ≤0.1s 响应）
- 即时中止暂缓是务实的工程决策 —— 当前架构的 `LLMClient` 未将 HTTP transport 生命周期暴露给外部，硬改风险高（需要同时处理 OpenAI SDK 重试、单例重建、异常类型匹配）。重构 LLMClient 时应将 abort 作为一等需求纳入设计

**曾考虑的替代方案：**
- 只设一个检查点（工具执行前）—— LLM retry 循环中取消无法生效
- 不注入合成 TOOL_CALL_RESULT（检查点 #3 直接 return）—— history 中有 TOOL_CALL 无结果，LLM 下次产生歧义
- 用 `signal` 或 `KeyboardInterrupt` 实现 —— Windows 信号支持不完整，且与 questionary 的 Ctrl+C 处理冲突
- 从 spinner loop 调 `OpenAI.close()` 强行 abort —— 侵入 LLMClient 内部实现，与当前架构边界冲突，暂缓

---

### 决策 131 — 记忆集成基础设施

**背景：** M5-5 记忆集成一直处于暂缓状态，需要在 Agent 生命周期中接入记忆模块。此前 `write_memory()` 只在 `BaseAgent` 中定义但无调用入口，且目录名使用了中文显示名（`_get_agent_name()`）而非标识符（`_get_agent_key()`），导致记忆保存到 `data/memories/程序员求职助手路由Agent/` 等路径。

**决策：**

- **`AUTO_MEMORY_ON_EXIT` 配置项** — 新增 `config.AUTO_MEMORY_ON_EXIT`（bool，默认 `false`），在 Agent FINISH 时自动调用 `write_memory(sync_mode=False)` 将当前对话异步固化为长期记忆。同时作用于 MainAgent 正常退出和子 Agent→MainAgent 切换退出。
- **`/build-memory` CLI 命令** — 新增手动触发命令，调 `self._handler.write_memory(sync_mode=False)` 后立即返回（异步守护线程），控制台打印 `"记忆构建已启动（后台异步处理）"`。
- **目录名修正** — `BaseAgent.write_memory()` 中 `agent = self._get_agent_name()` → `agent = self._get_agent_key()`，记忆保存到 `data/memories/main/`、`resume/`、`job_search/`。
- **异步写入** — 两路径均使用 `sync_mode=False`（守护线程后台执行），`src/memory/__init__.py` 的 lifecycle shutdown hook（10s timeout）已覆盖线程等待。
- **钩子位置** — 自动记忆写入放在 `App.run()` FINISH 分支的 `_auto_save()` 之后、switch 分支之前，覆盖所有三种 FINISH 场景（正常退出 / main→sub / sub→main）。
- **线程安全** — FINISH 时 agent loop 已退出，`_history` 无并发修改；守护线程只读 conversation 副本；记忆目录（`data/memories/`）与存档目录（`data/save/`）完全隔离。

**理由：**

- 需求明确为通用基础设施（非 resume 专属），配置项 + CLI 命令覆盖自动和手动两种场景
- 异步写入不阻塞 agent loop 和 CLI 响应，用户无感知延迟
- `agent_key` 作为目录名与已有 `data/memories/main/`、`interview/` 目录风格一致
- 复用已有 `write_memory()` 和 `build_memories(sync_mode=False)` 基础设施，新增代码仅 ~15 行

**曾考虑的替代方案：**

- 同步写入（`sync_mode=True`）—— 用户需等待 LLM 记忆提取完成（数秒），影响体验，已拒绝
- 在 `BaseAgent.process()` 中写记忆 —— App 层钩子更合适，Agent 不应感知 I/O 生命周期
- 保持 `_get_agent_name()` 作为目录名 —— 中文路径不便于脚本处理和跨平台兼容

---

### 决策 132 — LLM 调用超时 + 异常处理

**背景：** OpenAI SDK 默认超时为 `httpx.Timeout(timeout=600.0, connect=10.0)`（读取超时 600 秒），用户反馈 LLM 调用无响应时程序卡死在 spinner 动效。此前 `LLMClient` 构造时未传 `timeout` 参数，`BaseAgent.process()` 中 `chat_pro()` 调用无 try/except，`App._process_with_spinner()` 中 daemon 线程异常未捕获导致 `done` 事件永远不触发（spinner 死循环）。此外 `.env` 文件缺失 10 个已有默认值的配置项。

**决策：**

- **`LLM_TIMEOUT` 配置项** — 新增 `config.LLM_TIMEOUT`（可选，默认 `"60"` 秒），在 `OpenAI()` 构造函数中 `timeout=float(config.LLM_TIMEOUT)` 全局应用于 `chat_pro` / `chat_flash` / `web_search` 三个方法。`.env.example` 和 `.env` 同步追加。
- **`BaseAgent.process()` 异常捕获** — `chat_pro()` 调用包裹 `try/except Exception`，超时/网络错误时 `logger.warning`（单行，无 traceback）+ 返回 `Response(FINISH, message="❌ LLM 调用失败（超时阈值 {timeout}s）: {e}")`，控制权交还 CLI。
- **未消费 USER_INPUT 回滚** — 仅首轮 LLM 失败（`_round_counter == 1` 且 `_history[-1].event_type == USER_INPUT`）时 `_history.pop()` 移除未消费的用户消息，保持 history 干净。多轮后（已有 tool 交互）不回滚。
- **`_process_with_spinner` 兜底** — `_run()` 中 `process()` 调用包裹 `try/except Exception`，任意未预期异常捕获后构造 `Response(FINISH, error_msg)` 并正常 `done.set()`，确保 spinner 永不死循环。
- **`.env` 补全** — 追加 10 个缺失配置项（`EMBED_BATCH_SIZE`、`RETRIEVAL_TOP_K`、`RERANK_BATCH_SIZE`、`RERANK_TOP_K`、`CHROMA_PERSIST_DIR`、`MEMORIES_BASE_DIR`、`LOG_DIR`、`SAVE_DIR`、`AUTO_MEMORY_ON_EXIT`、`LLM_TIMEOUT`），值与 `_VAR_SPECS` 默认值一致。

**理由：**

- 超时客户端级设置一次覆盖所有 API 调用，改动最小（3 个调用点共享 1 行配置）
- 异常捕获两层分工：`base.py` 精准处理 LLM 层失败（有意义错误信息 + 回滚），`app.py` 兜底处理所有未知异常（保证 spinner 不死）
- `_round_counter == 1` 精确识别"用户刚发消息、LLM 从未处理"场景，多轮 tool 交互后的失败不回滚（tool 结果已有效）
- 用户看到简洁错误信息 + 重试建议，不再面对满屏 traceback

**曾考虑的替代方案：**

- 超时设在逐调用层（`chat.completions.create(timeout=...)`）—— 需改 3 个方法各加参数，无额外收益
- `logger.exception()` 完整 traceback —— 对 CLI 用户过于噪音，改为单行 `logger.warning` / `logger.error`
- 不 pop 未消费 USER_INPUT —— history 残留会导致下次输入时 LLM 看到重复消息
- 只修 `base.py` 不修 `app.py` —— 未来新的未预期异常仍会导致 spinner 死循环

---

### 决策 133 — Spinner 计时排除 UIBridge 等待时长

**背景：** `_process_with_spinner` 中的 spinner 计时器 `elapsed = time.time() - start` 从处理开始一直计时，当 LLM 返回 `provide_choices` 或工具审批弹窗等待用户输入时（`_handle_bridge_request` 阻塞在 `questionary.select().ask()`），计时器也在跑，给用户造成"系统还在处理中"的错觉。

**决策：** 新增 `paused_duration` 变量累计 UIBridge 交互期间的暂停时长。进入 `_handle_bridge_request` 前记录 `pause_start`，退出后累加 `time.time() - pause_start` 到 `paused_duration`。elapsed 计算改为 `time.time() - start - paused_duration`。3 行改动，不改 `_process_with_spinner` 的 while 循环结构。

**理由：**
- 最小改动：只加一个累加器变量和两次计时，不重构循环结构
- 累积模式天然支持多次 UI 交互（如 confirm + select 先后触发），每次都正确扣除
- 用户看到的秒数只反映实际 LLM 处理耗时，消除"系统卡死"的错觉

**曾考虑的替代方案：**
- 在 `_handle_bridge_request` 内部暂停/恢复计时器 —— 耦合到 UI 渲染函数，不干净
- 用单独的 `time.monotonic()` 计时器分段记录 —— 过度设计，当前场景一个累加器足够

---

### 决策 134 — SessionId 统一：SaveManager & dumper 共享会话 ID

**背景：** `SaveManager.__init__` 在构造时生成 `session_id`（`datetime.now().strftime("%Y%m%d%H%M%S")`），而 `dumper.dump_history()` 每次 `/dump` 都重新生成独立时间戳（`datetime.now().strftime("%Y%m%d_%H%M%S")`，格式也不同）。两者互不感知——存档用 ID "A"，dump 文件名用时间戳 "B"，无法通过文件名关联到同一次会话。用户希望 dumper 同 session 多次 dump 直接覆盖旧文件，而非每次生成新文件。

**决策：**
- 新建 `src/utils/session.py` — 模块级单例，暴露 `init_session_id(session_id=None)` 和 `get_session_id()` 两个函数。`init` 在启动时由 `main.py` 调用生成新 ID；传入参数时用于 `/restore` 切换会话。
- `SaveManager.__init__` 改用 `get_session_id()` 替代独立的 `datetime.now()`。
- `SaveManager.session_id` setter 内追加 `init_session_id(value)`，确保 `/restore` 后 dumper 也使用恢复后的旧 ID。
- `dumper.py` 移除 `from datetime import datetime`，改用 `get_session_id()`；文件名从 `{agent}_{ts}_message.dump` 改为 `{agent}_{session_id}_message.dump`，同一 session 多次 `/dump` 自然覆盖。
- saver.py 的 `datetime` import 保留——`save_session_meta()` 仍用 `datetime.now(timezone.utc).isoformat()`。

**理由：**
- 单一真相源：整个进程只有一个会话 ID，存档目录名和 dump 文件名天然一致
- 零配置：`main.py` 一行 `init_session_id()` 即完成初始化，后续模块 `get_session_id()` 即取即用
- Restore 兼容：SaveManager setter 是唯一修改会话 ID 的入口，同步共享模块零额外调用点
- 文件名覆盖：确定性文件名（同一 session = 同一文件名），`/dump` 两次自然覆盖，无需额外删除逻辑

**曾考虑的替代方案：**
- 让 dumper 接收 SaveManager 实例作为参数 —— 耦合 dumper 到 SaveManager，且 dumper 在 base.py 中通过局部 import 调用，传参链路长
- 把 session_id 挂到 config 上 —— config 是静态配置，session_id 是运行时状态，语义不匹配

---

### 决策 135 — 发送 LLM 消息剥离 thinking + 修正 input format role

**背景：** 两个独立但相关的问题：

1. `BaseAgent._to_openai()` 将 `_history` 中每条 `Message` 通过 `to_json()` 完整序列化后发给 LLM，包括 `thinking` 字段。前几轮 LLM 回复中的推理过程被原样送回模型，浪费 token 且可能干扰当前推理。

2. `08_input_format.md` 的 schema 中 `role` 写死为 `"const": "user"`，与实际不符——`_to_openai()` 使用 `m.role` 透传，LLM 实际收到 `user`（用户输入/工具结果）、`assistant`（LLM 自身历史回复）、`system`（系统纠错消息）三种 role；`event_type` 也缺少 `tool_call` 和 `finish`（assistant 历史消息的类型）。

**决策：**

1. **代码侧** — `_to_openai()` 中每条消息序列化前用 `dataclasses.replace(m, thinking=None)` 剥离 `thinking` 字段。`to_json()` 保持不变（dump 时仍需完整序列化）。

2. **提示词侧** — `08_input_format.md` 的 `role` 从 `"const": "user"` 改为 `enum: ["user", "assistant", "system"]`，`event_type` enum 扩展 `"tool_call"` 和 `"finish"`，`<EventTypes>` 新增对应条目并标明 **不含 `thinking` 字段**。

**理由：**

- **Token 节省**：`thinking` 是 LLM 的内部推理过程，不应对后续轮次可见，剥离后减少无意义 token 消耗
- **推理质量**：前轮推理内容可能包含错误路径或过时上下文，混入历史可能误导模型
- **格式一致**：input format 应与实际发送的数据一致，`role` 写死 `"user"` 会让 LLM 对 `assistant` 和 `system` 消息产生困惑
- **最小改动**：仅改 `_to_openai()` 一行 + prompt 一处，不影响 dump/save/restore 流程

**曾考虑的替代方案：**

- 修改 `to_json()` 加 `exclude_thinking` 参数 —— 增加方法签名复杂度，且 `to_json()` 在两处调用（LLM 发送 + dump）需求不同，调用方控制更清晰
- 在 LLMClient 层过滤 —— 职责越界，LLMClient 不应理解 Message 内部结构

---

### 决策 136 — 不暴露 LLM 原生 reasoning_content

**背景：** DeepSeek API 在 `chat.completions` 响应中提供 `reasoning_content` 字段（原生推理内容），比当前 LLM 在 JSON 中手写 `thinking` 字段更准确且省 token。考虑过让 `LLMClient` 捕获 `reasoning_content` 并替换 `Message.thinking`。

**决策：** **不做。** 保持当前方案——LLM 推理过程仅在 `Message.thinking` 中存储（由 `07_output_format.md` 的 JSON `thinking` 字段承载），`_to_openai()` 发送前剥离。`LLMClient` 层不捕获 `reasoning_content`。

**理由：**

- **安全风险**：`reasoning_content` 是模型的原生推理过程，可能包含系统提示词（system prompt）的片段或推导。将其暴露给用户（通过 `SHOW_THINKING` Panel 渲染或 dump 导出）会泄露系统设计细节和约束，存在 prompt injection 风险。
- **省 token 不如此重要**：JSON `thinking` 字段占用 token 但可控（`_to_openai()` 已剥离，不会累积到上下文窗口）。与安全风险相比，这点 token 开销可接受。
- **JSON thinking 更可控**：LLM 在 JSON 中手写的 `thinking` 是面向用户的摘要，不会包含敏感的系统提示词推导过程。

**曾考虑的替代方案：**

- `LLMClient` 新增 `chat_pro_thinking()` 返回 `ChatResult(content, reasoning)`，`BaseAgent` 用 `reasoning_content` 填充 `Message.thinking`，同时从 `07_output_format.md` 删除 `thinking` 字段 —— 实施后回滚，理由如上。

---

### 决策 137 — refactor 分支采用独立 v2 受控重写

**背景：** 当前项目已经具备可运行的 CLI、Agent、Tool、Plan、Session、RAG、Memory 和 Resume 链路，但核心能力集中在 `BaseAgent`、`App` 与多套模块级全局状态中。继续在旧结构上增加 Agent 会扩大样板代码、跨层私有访问、导入副作用和控制流耦合。`refactor` 是独立分支，用户不要求保护旧内部接口或旧运行状态。

**决策：**

- 在新的 `src/get_me_in/` 包内受控重写 v2，旧 `src/*` 只作为行为基线，达到门禁后切换入口并删除遗留实现。
- v2 禁止可变全局运行时单例、import-time 注册、CLI 直接访问 Agent 私有状态和 `__switch__`/`__reject__`/`__cancelled__` 等魔法控制 dict；依赖由 composition root 显式装配，Runtime 使用强类型 Command/Event 协议。
- 不迁移旧 Session、Memory、Chroma、`data/temp/`、Plan、handoff、input history 或其他运行状态。只保留 `data/reference/`、`data/prompts/`、`data/resume/template/` 三类静态资产，新索引和新会话由 v2 重建。
- 用户明确授权 `refactor` 分支编写核心自动化测试，优先覆盖 domain/runtime/session/tool codec/workspace；真实 adapter 和交互链路使用集成测试、Notebook 或 smoke checklist。
- 当前会话只更新设计、计划、状态和技能规则，不创建 v2 项目代码。进入每个实现阶段前仍需先提交新文件、类和公开方法清单供用户确认。

**理由：**

- 独立包让 v2 可以建立单向依赖和明确边界，不必兼容已被判定为重构根因的旧内部协议。
- 放弃低价值旧运行数据 migration，显著减少 Session/Memory 兼容层和迁移验证工作。
- 保留 reference、prompts 和 resume templates 能延续真正有价值的项目知识与静态资产。
- 自动化测试为状态机、handoff、持久化和路径安全提供必要回归保护，适合大规模重写。

**曾考虑的替代方案：**

- 原地拆分旧 BaseAgent/App —— 需要长期维护兼容层，容易把旧耦合带入新模块，已拒绝。
- 迁移全部 v1 Session/Memory/Workspace 数据 —— 成本高且用户明确不需要，已拒绝。
- 继续禁止测试文件，只用 Notebook/人工验证 —— 对状态机与持久化重写的回归保护不足，已拒绝。

---

### 决策 138 — R1 骨架清单获确认后开始编码

**背景：** R0 的能力基线、静态资产边界、旧入口基线和 G0 审查均已完成。用户已确认 R1 的新文件、类和公开方法清单，并要求后续会话可以进入编码阶段，不再因旧约束停留在文档准备阶段。

**决策：**

- 在 `src/get_me_in/` 创建 v2 的 `domain`、`application`、`ports`、`adapters` 分层骨架；项目源码目录保持既有布局，因此包导入统一使用 `src.get_me_in`。
- 首批实现仅覆盖 Settings、基础 ports、声明式 Agent/Prompt、实例级 CancellationToken、Application 与 `build_application(settings)` composition root；不提前实现 R2 Runtime、真实 LLM adapter 或 Session 持久化。
- 为上述纯逻辑增加核心自动化测试。R1 的开发期 import guard、最小无工具 LLM 对话和 G1 验收尚未完成，任务状态保持进行中。
- 更新 `AGENTS.md`：R1 清单获得用户确认后允许创建骨架代码；后续阶段仍须先提交对应清单供用户确认。

**理由：**

- 分层骨架先把 v2 的依赖方向和实例隔离落实到可执行代码，后续 Runtime 与工具迁移可在此基础上增量完成。
- 先只实现无副作用的核心模型和装配点，避免在 R1 过早复制旧 `BaseAgent`/`App` 的控制流耦合。
- 自动化测试能在后续重构中持续验证 Settings、Agent catalog、Prompt 渲染和 composition root 的基本行为。

**曾考虑的替代方案：**

- 继续只更新文档，等待全部里程碑细节确认 —— 用户已明确确认 R1 清单并要求进入 coding phase，会无必要地延迟重构。
- 在 R1 直接实现完整 Runtime 与真实 LLM 调用 —— 会跨越 R2 的协议和状态机设计门禁，增加返工风险。

---

### 决策 139 — R1 临时无工具对话仅用于 G1 验证

**背景：** G1 需要验证 v2 可以完成一轮无工具 LLM 对话，但正式的 RuntimeCommand/RuntimeEvent、AgentRuntime 和真实 LLM adapter 被安排在 R2，尚未进入确认后的实现范围。用户确认允许增加临时方案，同时要求明确记录后续移除责任。

**决策：**

- 在 `Application` 增加 `complete_text(text) -> str`，仅渲染 main Agent prompt 并调用显式注入的 `LLMPort`。
- 该方法以 `TEMP-R1` 标记；不保存 history、不支持工具、审批、handoff、session、重试或真实 adapter 的默认装配。
- 未注入 `LLMPort` 的 application 必须明确失败，不能隐式创建 client 或读取全局状态。
- R2 正式 AgentRuntime 成为唯一模型调用入口后，必须删除 `complete_text()` 及其测试；不得将临时接口扩展为正式 Runtime。

**理由：**

- 用最小同步链路验证 Settings、PromptRenderer、AgentCatalog、CancellationToken 和 port 注入可以共同工作，同时不跳过 R2 的强类型协议门禁。
- 显式注入使单元测试可使用 fake LLM，避免在 R1 引入 provider 网络调用、可变单例或 import-time client。
- 明确的移除条件避免临时 API 在后续阶段成为兼容负担。

**曾考虑的替代方案：**

- R1 直接实现 OpenAI adapter 和完整 Runtime —— 越过 R2 的模型请求、事件和取消设计，已拒绝。
- 不提供任何对话链路，等 R2 完成后再验证 G1 —— 无法在 R1 发现 prompt 与 composition root 的集成问题，已拒绝。

---

### 决策 140 — R2 用 ToolResult 闭合暂停的工具回合

**背景：** R2 的 Runtime 需要实现 `tool call → pause → tool result → LLM`，但原先确认的 RuntimeCommand 清单没有能承载工具执行结果的命令。用户明确允许新增该命令；真实 ToolCatalog 与 handler 执行仍属于 R3。

**决策：**

- 新增 `ToolResult(call_id, output)` RuntimeCommand。
- Runtime 对已声明的工具调用发出 `ToolStarted` 并进入 `WAITING_FOR_TOOL`；只接受相同 `call_id` 的 ToolResult，先发出 `ToolFinished`，再将结果作为 `Role.TOOL` 的 ConversationEvent 继续请求 LLM。
- call id 不匹配或非等待状态收到结果时返回确定的 Failed event；未声明工具仍返回 `unknown_tool`。
- R2 的 `available_tools` 仅为回合协议测试的过渡集合；R3 必须以显式 ToolCatalog 替换，不能形成全局 Registry。

**理由：**

- 工具回合的状态与闭合关系成为强类型协议，不再依赖魔法 dict 或 CLI 补写历史。
- 先完成 Runtime 的暂停/恢复语义，R3 可以独立注入真正的工具发现、审批与执行能力。

**曾考虑的替代方案：**

- 将工具结果塞进 Continue 命令 —— 无法携带 call id 与结果，无法验证闭合对应关系，已拒绝。
- 等到 R3 再定义完整回合 —— R2 无法满足既定 Runtime 状态机门禁，已拒绝。

---

### 决策 141 — 保留静态 prompt 的 JSON 在应用边界归一化

**背景：** v2 继续复用 `data/prompts/general_agent/` 静态资产。该 prompt 的输出格式使用 `message/event_type/tool/event_payload`，而 R2 的内部 ModelReply 采用更窄的 `content/tool_call` 形状。首次真实 provider smoke 因此在 parser 边界失败。

**决策：**

- ModelReplyParser 同时接受 v2 JSON 形状和保留静态 prompt 的 JSON 形状，并统一归一化为 v2 ModelReply。
- 兼容仅存在于 application 层 parser；domain、RuntimeEvent 和 LLMPort 不引入旧 Message、旧 Request/Response 或魔法控制字段。
- 保留 prompt 输出发生 tool_call 时，将 `tool/event_payload` 映射为 `tool_name/tool_arguments`。

**理由：**

- 保留经确认可复用的 prompt 静态资产，同时保持 v2 内部协议单一且强类型。
- 转换集中在 provider 文本进入 Runtime 的唯一边界，后续替换 prompt 时不影响 domain 或 adapter。

**曾考虑的替代方案：**

- 立即重写全部 general_agent prompt 为 v2 格式 —— 静态资产迁移范围过大，且会干扰旧 CLI 的行为基线，已拒绝。
- 让 Runtime 直接识别旧 Message/event_type 字段 —— 扩散旧协议并破坏 v2 边界，已拒绝。

---

### 决策 142 — system tools 通过显式 Clock 与 WorkspacePort 注入实现

**背景：** 旧 `get_current_datetime` 和 `get_working_dir` 直接依赖全局 config 与装饰器注册。R3 已建立显式 ToolCatalog/ToolExecutor，需要迁移这两项基础工具，同时不得引入可变运行时单例或 import-time 副作用。

**决策：**

- `build_system_tools(clock)` 显式接收 Clock，时间工具只读取该依赖。
- 工作目录工具从 ToolContext 的 WorkspacePort 解析 `Path(".")`，返回受限工作区的绝对根目录；未配置工作区时返回结构化 `workspace_unavailable` 失败。
- 工具定义由工厂返回，待 composition root 汇总，不使用装饰器或全局 Registry。

**理由：**

- 时间和工作区边界可由测试替身替换，且每个 Application 实例保持隔离。
- 工作目录的语义与 WorkspacePort 的路径边界一致，不再让工具绕过受限文件系统。
- 失败通过 ToolOutcome 表达，Runtime 可以按统一 typed event 协议处理。

**曾考虑的替代方案：**

- 保留对旧 config.WORKING_DIR 的读取 —— 会把 v1 全局配置依赖带入 v2，已拒绝。
- 在工具模块 import 时注册到全局 ToolRegistry —— 违反 R-D2，已拒绝。

---

### 决策 143 — Runtime 直接执行显式 Catalog 工具，应用独立装配 Workspace

**背景：** R2 的 `available_tools` 只验证“暂停后由外部提交 ToolResult”的过渡协议，无法提供真实工具发现、capability 校验或 handler 执行。旧工具同时依赖全局 `WORKING_DIR=data/temp/` 和模块级 Plan context，违反 v2 实例隔离原则。

**决策：**

- AgentRuntime 通过显式 ToolExecutor 执行 ToolCatalog 中的工具，并以 AgentSpec capabilities 强制校验可见性。
- 需要审批的工具先产生 ApprovalRequested；Approve/Reject 用同一 call_id 重新闭合执行。业务失败序列化为 ToolFinished 结果后继续交给模型修复，不把它误作 Runtime 致命失败。
- composition root 为每个 Application 创建 LocalWorkspace、PlanService 和 ToolContext；新增 WORKSPACE_DIR，默认 `data/workspace/` 并忽略运行内容，不读取旧 `data/temp/`。

**理由：**

- 工具目录、审批与执行的事实来源统一在显式对象中，消除 R2 过渡集合和全局注册。
- 每个 Application 的工作区与计划状态可独立测试，后续 R4 Session 只需接管这些实例状态。
- 业务工具失败仍可让模型调整参数或策略，避免过早终止用户任务。

**曾考虑的替代方案：**

- 保留 R2 的外部 ToolResult 作为正式执行入口 —— CLI 仍需理解工具私有状态，已拒绝。
- 继续使用旧 WORKING_DIR/data/temp —— 会迁移被 R-D6 排除的运行状态边界，已拒绝。

---

### 决策 144 — 文件预览经 FrontendPort 处理

**背景：** 旧 `workspace_open` 在工具 handler 内按操作系统分支直接启动 GUI。该副作用既无法由测试替身替换，也让 tool/domain 层掌握操作系统细节。

**决策：**

- 定义 FrontendPort.open_file(path)，workspace_open 仅检查受限工作区内的文件并调用该 port。
- OSFrontend 在 adapter 层按 Windows/macOS/Linux 调用默认打开器；composition root 显式装配它。
- workspace_open 保持 ALWAYS 审批，frontend 缺失或打开失败返回结构化 ToolFailure。

**理由：**

- 工具逻辑可用 fake FrontendPort 测试，而不在自动化测试中打开用户程序。
- 操作系统副作用集中在 adapter，符合 v2 的依赖方向和可替换性。

**曾考虑的替代方案：**

- 在 workspace tool 内直接使用 os.startfile/subprocess —— 耦合操作系统并难以测试，已拒绝。

---

### 决策 145 — R3 检索工具只依赖临时 RetrievalPort

**背景：** R3 需要把 `query_memory` 与 `query_reference_data` 纳入 v2 的显式 ToolCatalog，但 v2 的 KnowledgeService、索引状态与 Chroma 装配被排在 R6。直接调用旧 `src.rag` 会重新引入模块级全局状态和旧运行时边界。

**决策：**

- 定义 `RetrievalPort` 和可序列化的 `RetrievalResult`，查询工具仅通过该端口读取 `memories` 或 `references` collection。
- R3 的 composition root 注入 `DeferredRetrievalAdapter`；在 R6 实现真实检索前，它返回明确的 `retrieval_unavailable` 失败，不伪造查询结果。
- 保留 `memory_type`、`category`、`top_k` 的校验与结果去除 `rerank_score` 的输出契约；R6 以真实 KnowledgeService 适配器替换临时适配器。

**理由：**

- 工具目录、参数校验和 Runtime 闭合路径可在 R3 完成并得到自动化测试保护。
- 临时不可用状态是显式、可观测且可删除的，不会把旧 RAG 单例或 Chroma 生命周期带入 v2。
- R6 只需替换 composition root 中的适配器，无需重写调用该工具的 Runtime 或 Agent。

**曾考虑的替代方案：**

- 从 v2 直接 import 旧 `src.rag` —— 违反 v2 依赖边界和无全局运行时状态约束，已拒绝。
- 返回固定的测试结果 —— 会掩盖真实检索尚未可用的事实，已拒绝。

---

### 决策 146 — R3 简历工具使用临时 ResumeArtifactPort

**背景：** `copy_template` 和 `build_pdf` 是既有的简历工作流入口，但 Artifact、版本与编译记录的持久化模型属于 R7。R3 仍须把这两个工具纳入统一的 ToolCatalog，并消除它们对旧 config、工作区和 `subprocess` 的直接依赖。

**决策：**

- 定义 `ResumeArtifactPort`，使工具只通过端口执行模板复制和 PDF 构建；模板复制仍使用 `WorkspacePort` 约束目标路径，PDF 构建仍使用注入的 `ProcessRunner` 支持超时和取消。
- R3 使用 `LocalResumeArtifacts` 适配静态 `data/resume/template/` 资产和本机 `pdflatex`；两个工具均要求显式审批。
- R7 新建 ArtifactService 后替换该适配器，负责 artifact、版本、编译日志和 PDF 引用持久化；不修改已建立的 ToolOutcome/Runtime 闭合协议。

**理由：**

- 现在即可保留模板复制和编译的可观察行为，并以 fake port 覆盖审批、取消和结果序列化。
- 静态模板读取、进程调用和工作区写入各自位于端口边界，避免工具 handler 直接访问配置或操作系统。
- R7 的持久化设计不会反向扩大 R3 的实现范围。

**曾考虑的替代方案：**

- 等到 R7 再迁移两个工具 —— 会使 R3 的 25 工具目录不完整，已拒绝。
- 在工具 handler 内直接读取模板和调用 `subprocess.run` —— 破坏依赖注入和自动化测试隔离，已拒绝。

---

### 决策 147 — 架构复审撤销 G2/G3 完成结论并暂停 R4

**背景：** R1～R3 实现完成后进行架构复审。现有 80 个自动化测试全部通过，但静态检查与只读诊断发现：真实 Prompt 未注入 ToolCatalog/AgentCatalog；Main Agent 实际可见全部 25 个工具；ConversationEvent 与 Handoff 缺少可持久化的 call-id 关联；等待工具期间取消或接收新用户消息会遗留孤立 TOOL_CALL；Workspace revision 只是可跨 Session 复用的内容 hash；OpenAI 与 ProcessRunner 只在阻塞调用前后检查取消；默认两轮上限无法支持连续多工具任务；Settings 中的 LLM timeout 未进入 Runtime。

**决策：**

- 撤销 `docs/task.md` 中 G2、G3 的完成结论，将上述缺口恢复为待修复任务；已经满足且有测试证据的细分任务保持完成。
- R4 Session Aggregate 与编排暂不启动。先提交 G2/G3 修复所需的新文件、类、公开方法与既有接口调整清单，获得用户确认后再编码。
- 重新验收必须覆盖真实 Prompt 目录注入、provider-neutral message/call-id codec、pending call 的所有闭合路径、真实阻塞 adapter 取消、完整 capability 绑定、session-scoped revision、连续多工具回合及 Settings timeout 生效。
- 单元测试继续保留，但 Fake LLM/Fake ProcessRunner 不能单独作为真实 adapter 取消或端到端工具发现的验收证据。

**理由：**

- 门禁的意义是保护下一阶段依赖的协议，而不是只证明局部类型和 handler 可以运行；带缺口进入 R4 会把错误的消息关联、状态所有权和权限边界固化进 Session schema。
- 先修复 R2/R3 边界，可以避免 R4 同时承担会话建模和底层 Runtime 返工，降低 snapshot、rewind 与 handoff 闭环的设计风险。
- 保留已通过的细分成果，同时只撤销不真实的门禁状态，比整体回滚 R1～R3 更准确。

**曾考虑的替代方案：**

- 保持 G2/G3 完成，在 R4 顺便修复 —— 会混合门禁责任，并使 Session model 建立在尚未稳定的 call-id、pending state 和 revision 语义上，已拒绝。
- 只增加测试、不调整任务状态 —— 文档仍会指示新会话直接进入 R4，无法真实反映当前风险，已拒绝。

---

### 决策 148 — G2/G3 修复完成并恢复门禁结论

**背景：** 决策 147 识别的 Runtime、消息关联、取消、权限和 Workspace 授权缺口已经按用户确认的推荐方案修复。核心自动化测试增至 86 项并全部通过；临时 `scripts/v2_runtime_smoke.py` 已提供真实终端交互链路，用户确认当前状态可用。

**决策：**

- 恢复 G2 与 G3 的完成结论；R2/R3 不再保留已知门禁缺口。
- Runtime 采用 pull-driven 单事件状态机，由强类型 `RuntimeCommand` 驱动；conversation codec 显式保存 tool name、arguments、call id 与结果关联，handoff 保留原 call id。
- Prompt 仅注入当前 Agent 可见的 ToolCatalog/AgentCatalog 描述；生产工具必须声明 capability，Main Agent 不获得 workspace、resume 等领域权限。
- OpenAI adapter 与 ProcessRunner 的活动调用可由 CancellationToken 中断；工作区 read-before-edit 授权绑定 session/path/revision，禁止跨 Session 复用。
- `scripts/v2_runtime_smoke.py` 仅作为 R2/R3 人工 smoke Runner；它不替代 R5 正式 CLI，遇到 handoff 只展示并关闭当前回合，不提前实现 R4 编排。
- R4 仍须先提交新文件、类、公开方法和职责边界清单供用户确认；本次恢复门禁不构成进入 R4 编码的授权。

**理由：**

- 86 项自动化测试覆盖 Prompt 目录注入、消息与 call-id 关联、pending 状态闭合、连续多工具回合、配置化 timeout、capability 隔离、跨 Session revision 隔离以及 adapter/子进程取消。
- 临时 Runner 补充了真实终端交互证据，同时明确隔离于后续 Session、handoff 编排和正式 CLI，避免验证设施演变为新的生产架构入口。
- R2/R3 协议已稳定到足以支撑 R4 设计，但继续保留 R4 的独立确认门禁，可以防止未经审查地固化 Session 状态所有权。

**曾考虑的替代方案：**

- 保持 G2/G3 为未完成直到 R5 正式 CLI 落地 —— 会把 Runtime/Tool 门禁与 CLI 迁移门禁混为一谈，已拒绝。
- 将临时 Runner 直接演进为正式 CLI —— 会越过 R4 Session 与 R5 CLI 拆分设计，已拒绝。

---

### 决策 149 — 后续设计按当前 Runtime 重新校准

**背景：** G2/G3 修复后，Runtime 已采用 pull-driven 单事件状态机，并由 `RuntimeState` 持有 history、phase、pending tool 和单次运行控制状态。原 R4 设计仍要求 SessionState 另行持有 AgentState、pending action 与 plan，同时提出 `AgentStateRepository` 和 `handle(session_id, command)`；直接实现会产生双重状态源，并与当前一个 Application 持有一个 Runtime 的结构冲突。复审同时发现 handoff 缺少成功/失败完成命令、rewind 缺少用户回合关联、R5/R6 命令依赖倒置，以及 R6/R7 部分任务已经在 R3 提前建立端口或工具契约。

**决策：**

- 一个 `Application` 同时只管理一个活动 `ApplicationSession`，对外保留 `handle(command)`；单个 Application 内多会话并行继续留在 R9。
- `SessionState` 是唯一规范状态所有者；`AgentSessionState` 承接当前 RuntimeState 与 Plan。`AgentRuntime.advance(state, command)` 返回内部 `RuntimeTransition`，不再保存第二份长期状态，也不增加进程内 `AgentStateRepository`。
- 增加 `CompleteHandoff` 与 `FailHandoff`，由 Orchestrator 按原 call id 闭合 WAITING_FOR_HANDOFF；HandoffFrame 同时记录 turn id 与 call id。
- ConversationRecord 增加 turn id，rewind 只允许用户回合边界。Snapshot 只保存稳定状态，不自动重放活动 LLM/Process 或 TOOL_READY；restore/rewind 清除 WorkspaceAccessState。
- CLI input history 归 R5 InputController，可单独持久化但不进入 domain SessionState；Artifact/ArtifactRef schema 推迟到 R7。
- G4 使用测试专用 sub Agent 验证 main→sub→main，真实 Resume AgentSpec 保留在 R7。
- R5 先注册 `/ragreload` 与 `/build-memory` 的 unavailable handler，R6 再接真实服务；现有 RetrievalPort 保持 tool-facing 契约，不在 R6 重复定义。
- R7 保留 R3 已迁移的 Resume 工具签名，以 ArtifactService-backed adapter 替换临时实现；R6 与 R7 可在 G5 后并行，最终 G7 仅对实际使用 knowledge/memory 的路径依赖 G6。

**理由：**

- 单一规范状态能避免 Session、Runtime 和 PlanService 各自持有可漂移副本，并让 snapshot/restore/rewind 在一个 aggregate 中校验。
- 专用 handoff completion command 将 active agent、handoff stack 与源 tool call closure 收敛为原子编排操作。
- turn id 和稳定 snapshot phase 可以防止 rewind 切断多工具回合、恢复重复执行有副作用工具。
- 把 CLI 状态、Artifact schema 和 Knowledge 实现留在各自里程碑，可以缩小 R4 范围并保持依赖方向清晰。

**曾考虑的替代方案：**

- 保留 Runtime 内部状态，再由 Session 复制一份用于持久化 —— 会形成双重事实来源，已拒绝。
- 让 AgentRuntime 直接读写 AgentStateRepository —— 增加不必要的进程内 repository，并隐藏状态转换，已拒绝。
- 一个 Application 同时管理多个活动 Session —— 超出当前 CLI 和 R4 需求，与 R9 暂缓范围冲突，已拒绝。
- 允许 restore 自动继续 TOOL_READY —— 可能重复文件写入、编译或外部调用，已拒绝。

---

### 决策 150 — G4 后强制重新 Review R5 至 R8

**背景：** 对 R5～R8 进行基于 `docs/plan.md` 的快速风险扫描后，未发现需要立即推翻总体路线的问题，但这些阶段都依赖 R4 最终落地的 Application、SessionView、ApplicationCommand/RuntimeCommand、RuntimeEvent、handoff 和 cancellation 边界。当前仅有修订后的设计，尚不能用来确认 CLI worker、Knowledge 命令接入、R6/R7 并行验收和 R8 删除清单的最终形状。

**决策：**

- G4 完成并执行 checkpoint 后、提交 R5 新文件/类/公开方法清单前，强制重新 Review R5～R8。
- 复审至少检查四项：R5 CLI/WorkerRunner 是否保持薄层；R6 `/ragreload`、`/build-memory` 与资源清理是否匹配 R5；R6/R7 并行和 G7 最终依赖是否仍成立；R8 删除范围、临时 Runner 删除时点和回退步骤是否完整。
- 复审结论必须同步到活跃 refactor design/plan/task/decision，并获得 R5 清单确认；未完成前不得开始 R5 coding。
- 当前不深入细化 R5～R8，不因预判未来接口而扩大 R4 范围。

**理由：**

- R4 会重塑 Application 与 Session 的公开边界，提前锁定 R5 worker 和命令协议容易重复本次状态所有权漂移。
- R6/R7 的并行是优化而非硬约束，应依据 G4/G5 后真实集成边界决定。
- 在删除旧入口前重新核对真实依赖，比现在维护一份推测性的 R8 删除清单更可靠。

**曾考虑的替代方案：**

- 现在深入设计 R5～R8 —— 缺少 R4 落地证据，容易产生推测性接口，已拒绝。
- 保持现有计划且不增加复审门禁 —— 新会话可能在 G4 后直接进入 R5 coding，无法防止设计再次漂移，已拒绝。

---

### 决策 151 — R4/G4 完成后先进入 R5 前复审

**背景：** R4 已按确认清单完成 Session aggregate、Runtime 状态迁移、handoff 编排与 v2 snapshot；核心自动化测试增至 98 项。R5～R8 的接口和依赖仍必须以实际落地边界为准。

**决策：**

- 将 R4 和 G4 标记为完成，并在 `docs/current.md` 将当前工作切换到 R5 启动前复审门禁。
- 不在本次 checkpoint 改写 `docs/design.md` 或 `docs/plan.md`；R5 新文件、类和公开方法清单仍须经过复审并获用户确认。

**理由：**

- R4 的实际 `Application`、`SessionService`、`Orchestrator`、ApplicationCommand/RuntimeCommand、RuntimeEvent 与 cancellation 边界已经可作为复审事实基础。
- 保持 R5 编码门禁，避免 CLI、Knowledge、Resume 和旧代码删除在未经重新校准的条件下扩张范围。

**曾考虑的替代方案：**

- 直接开始 R5 CLI 编码 —— 违反决策 150 的强制复审门禁，已拒绝。

---

### 决策 152 — R4 复审补齐 handoff 启动、失败闭合与 frontend 回合投影

**背景：** R5 前强制复审发现，R4 虽已让 Orchestrator 切换 active agent，但没有用 handoff context 启动目标 Runtime；正式 CLI 在 `HandoffRequested` 后发送 `Continue` 时，目标 Runtime 仍处于 `READY`。同时，子 Agent 在活动 handoff 中取消或失败时，源 Agent 的原始 call id 未闭合；`SessionView` 也没有提供 `/rewind` 选择所需的安全 turn 投影。原有 98 项测试未覆盖这些真实边界。

**决策：**

- Orchestrator 在 main→sub 切换时立即以 `UserMessage(context)` 推进目标 Runtime，保存其新状态后再向 CLI 返回原 `HandoffRequested`；CLI 不负责构造子 Agent 私有上下文。
- 活动子 Agent 返回 `Cancelled` 或 `Failed` 时，Orchestrator 必须以 `FailHandoff` 闭合源 Agent 的原 call id、弹出 frame 并恢复源 Agent。
- Snapshot codec 拒绝 nested frame，以及 active agent、源 phase、pending call id、turn id 与 frame 不一致的数据；restore 在替换当前 Session 前拒绝当前 Application 未装配的 Agent。
- 增加只读 `SessionTurnView`，由 `SessionView.rewind_points` 公开主 Agent 用户回合；CLI input navigation history 仍由 R5 `InputController` 独立管理。
- 补齐 handoff 启动/取消/嵌套、复杂 rewind、workspace grant 清理、损坏 snapshot 和公开 rewind projection 测试；104 项核心自动化测试通过后恢复 G4 完成结论。

**理由：**

- Handoff 编排必须在 application 层形成可直接继续驱动的状态，不能把子 Runtime 启动细节泄漏给 CLI。
- 任何 handoff 终止路径都需要闭合原 call id，避免主 Agent 永久停留在 `WAITING_FOR_HANDOFF`。
- Frontend 需要 rewind 选择数据，但不应因此读取完整 snapshot 或 Agent 私有 history。

**曾考虑的替代方案：**

- 由 CLI 在收到 `HandoffRequested` 后向子 Agent 发送 `UserMessage(context)` —— 会让 CLI 吸收业务编排，已拒绝。
- 让 CLI 从 `SessionSnapshot` 扫描 user record —— 暴露持久化内部结构并耦合 codec，已拒绝。

---

### 决策 153 — R5 使用薄 CLI、单 WorkerRunner 与可替换命令注册

**背景：** R4 复验后，Application 已提供 typed command/event、`request_cancel()`、SessionView rewind projection 和公开 Session API。R5 必须迁移旧 App 的输入、命令、渲染、线程、审批与自动保存能力，同时不能重新吸收 Agent 编排、完整 Session 状态或后续 Knowledge/Resume service。R8 前旧 `main.py` 仍需保持可运行，因此删除临时 Runner 前还需要正式 v2 CLI 的独立入口。

**决策：**

- R5 新建 `src/get_me_in/cli/`，只包含 `CliApp`、`CommandRegistry`、`InputController`、`Renderer`、`WorkerRunner` 与模块入口；具体文件、对象和公开方法以 `docs/design.md#67-cli` 的清单为唯一编码边界。
- CliApp 负责 RuntimeEvent → RuntimeCommand 推进；HandoffRequested 只渲染并 Continue，不在 CLI 构造子 Agent context。WorkerRunner 使用单 worker 串行调用 Application，跨线程取消只调用 `Application.request_cancel()`。
- CommandRegistry 公开 `register/replace/dispatch/help_entries/completions`；R5 注册 `/ragreload` 与 `/build-memory` unavailable spec，R6 以 replace 接入真实 handler，不修改 CliApp 主循环。
- InputController 只维护进程内导航历史；restore 后由 `SessionView.rewind_points` 重建，不增加 CLI snapshot schema。终态由 CliApp 调用 `Application.snapshot()` 自动保存，失败单独渲染。
- 审批命令使用 `/approval prompt|auto`，保留 `/auto-approve-switch` alias；审批模式是 CLI 偏好，不修改 ToolDefinition 或 Runtime。
- R5 提供 `python -m src.get_me_in.cli`；G5 通过后删除临时 Runner。R6/R7 可在 G5 后并行，但 R8 必须等待 G6、G7 均完成，并将入口切换与遗留删除拆为两个独立提交。

**理由：**

- 单线程串行推进符合 Application 当前“一个活动 Session、一个活动 command”的状态边界，并把唯一安全的跨线程动作限制为取消。
- 可替换 command spec 让 R6 服务接入不需要修改 CLI 主循环，也不需要 Application 知道 CLI 命令名。
- 复用 SessionView 投影可以完成 restore/rewind 与 context recap，同时避免建立第二套 history 持久化和暴露 snapshot 内部结构。
- 独立模块入口使 G5 能验证正式 CLI，又不提前切换 R8 生产入口。

**曾考虑的替代方案：**

- 直接把临时 `scripts/v2_runtime_smoke.py` 演进为正式 CLI —— 缺少命令、输入、渲染与 worker 边界，已拒绝。
- 让 CommandRegistry handler 直接修改 Agent/Runtime 或读取 SessionSnapshot —— 重新制造跨层耦合，已拒绝。
- 在 R5 新增独立 CLI history snapshot —— 当前 SessionView 已提供 rewind projection，没有足够收益支撑第二套 schema，已拒绝。

---

### 决策 154 — R5 清单获确认并固定新会话实施入口

**背景：** 用户已确认 R5 新文件、类与公开方法清单，但明确要求当前会话不编码，并检查新会话经 project-bootstrap 恢复后是否具备无歧义的实施信息。冷启动审查发现确认状态尚未写入 `current.md`，原清单也缺少构造依赖、返回类型、CommandResult 语义与实施顺序。

**决策：**

- 正式确认 `docs/design.md#67-cli` 的 R5 文件、对象、构造依赖和公开方法清单；新会话允许按该清单创建 `src/get_me_in/cli/` 与三个对应测试文件。
- 固定 CommandResult/CommandSpec 语义和五步实施顺序；每一步独立验证、独立提交，不跨入 R6/R7。
- 第一实施切片是 `commands.py` 与 `test_cli_commands.py`；完成后再迁移 InputController/Renderer，不一次创建全部 R5 文件。
- 当前会话只更新状态与设计文档，不创建 R5 代码；新会话必须先执行 project-bootstrap，以 `docs/current.md` 路由到活跃 refactor design/plan/task/decision。

**理由：**

- 把确认事实和第一个可执行切片写入唯一状态快照，避免新会话重复请求确认或一次性铺开全部 CLI。
- 明确类型语义和依赖能减少实现时临时发明控制 dict、跨层依赖或额外持久化 schema 的风险。

**曾考虑的替代方案：**

- 只在本次对话中确认、不更新 current.md —— 新会话无法可靠恢复授权状态，已拒绝。
- 新会话直接创建全部 R5 文件 —— 违反小步验证和独立提交约定，已拒绝。

---

### 决策 155 — R5 第一切片已审查并保持交互职责后置

**背景：** R5 第一切片已创建 `commands.py` 与 `test_cli_commands.py`，以 `CommandRegistry` 固定强类型 command spec/result、解析、alias、replace 和核心 command handlers，并通过 110 项 v2 核心自动化测试。用户审查认为当前实现可接受，但要求同步项目文档，避免后续把已登记 handler 误认为完整 CLI 交互。

**决策：**

- 将第一实施切片标记完成，提交为 `151b04a refactor: add CLI command registry`。
- `/help`、`/edit`、`/dump`、`/restore`、`/rewind`、R6 unavailable commands、`/exit_sub`、审批模式与 `/exit` 已在注册表中登记为核心 handler，但命令迁移任务保持进行中。
- 第二切片仍必须实现 `InputController` 与 `Renderer`；无参数 restore/rewind 的选择、编辑器、帮助和通知的真实终端交互不得遗漏或提前塞入 CommandRegistry。
- 后续仍严格按既定五步顺序实施，不创建 WorkerRunner、CliApp 或模块入口，直到相应切片开始。

**理由：**

- 注册层只负责解析与强类型结果；终端 I/O 和渲染属于后续明确的职责边界。
- 将命令迁移保留为进行中，可使任务文档同时反映已验证的协议基础和未落地的真实交互，避免后续阶段遗漏。

**曾考虑的替代方案：**

- 将所有已登记命令直接标记完成 —— 会掩盖 InputController、Renderer 与 CliApp 尚未实现的交互和集成任务，已拒绝。
- 在第一切片补齐所有输入和渲染逻辑 —— 违反已确认的小步实施顺序，已拒绝。

---

### 决策 156 — InputController 通过 CompletionProvider 获取动态命令补全

**背景：** 已确认的 R5 `InputController` 负责 autocomplete，但原始公开方法清单没有接收 `CommandRegistry` 或命令补全列表的边界。静态注入列表会使后续 R6 的 `register()`/`replace()` 无法自动反映在输入补全中；让 InputController 直接依赖 CommandRegistry 则会破坏 CLI 组件的职责隔离。

**决策：**

- 新增 `CompletionProvider = Callable[[], tuple[str, ...]]` 和 `InputController.set_completions(provider) -> None`。
- CLI 装配时调用 `input_controller.set_completions(command_registry.completions)`；`read()` 每次显示输入框时调用 provider 获取最新命令。
- 未注入 provider 时使用空元组，支持独立构造和测试；InputController 不直接依赖或持有 CommandRegistry。

**理由：**

- provider 保持命令注册表的动态性，R6 替换 handler 或后续新增命令不需要刷新一份静态列表。
- 单向的 callable 注入保留 InputController 对终端 I/O 的专注边界。

**曾考虑的替代方案：**

- 严格保持原公开清单并推迟 autocomplete —— 会使已确认职责无法闭合，已拒绝。
- 注入静态命令列表 —— register()/replace() 后会产生过期补全，已拒绝。
- 让 InputController import CommandRegistry —— 引入不必要的组件耦合，已拒绝。

---

### 决策 157 — /rewind 选择显示用户输入预览而非内部 turn_id

**背景：** R5 首次人工 smoke 发现 `/rewind` 的选择项直接显示 `SessionTurnView.turn_id` UUID。虽然该值可准确驱动 `RewindSession`，但用户无法从 UUID 判断要回退到哪条输入，交互不可用。

**决策：**

- 无参数 `/rewind` 的选项显示为“序号 + 清理后的用户输入预览”，预览最长 80 个字符。
- CommandRegistry 在内部保存显示 label 到 `turn_id` 的映射；选择后仍将精确 `turn_id` 传入 `RewindSession`。
- 不扩展 InputController 的 `select()` 类型或暴露 Session 内部结构。

**理由：**

- 前端选择应使用用户可理解的文本，内部标识仅用于协议闭合。
- 局部映射保持既有 InputController 字符串选择边界，避免为单一命令引入新 UI DTO。

**曾考虑的替代方案：**

- 继续展示 UUID —— 人工 smoke 已证明不可用，已拒绝。
- 将 UUID 与预览同时展示 —— 会造成冗长噪声，且不改善用户选择，已拒绝。

---

### 决策 158 — /restore 选择显示会话预览而非内部 session_id

**背景：** `/restore` 的会话列表同样只显示 `session_id` UUID，无法说明各存档会话的内容。与 `/rewind` 不同，CLI 不能读取持久化 snapshot 或私有 history，因此现有 `SessionPreview` 投影缺少所需信息。

**决策：**

- `SessionPreview` 增加 `preview`，由 session repository 从 snapshot 中最新主 Agent 用户输入派生，最长 80 个字符。
- 无参数 `/restore` 显示“序号 + preview + 保存时间”，在 CommandRegistry 内部映射选项到精确 `session_id`。
- preview 仅为公开 projection，不写入或修改 snapshot schema；不存在用户输入的会话显示明确占位文本。

**理由：**

- 用户可依据自己的请求文本识别会话，同时保持 CLI 不读取 SessionSnapshot 的分层边界。
- 运行时派生避免引入新的持久化字段与 schema migration。

**曾考虑的替代方案：**

- 继续仅显示 session_id —— 人工 smoke 已证明不可用，已拒绝。
- 在 CLI 直接读取 snapshot 文件 —— 会破坏 application/session 与 frontend 的公开边界，已拒绝。

---

### 决策 159 — 帮助从真实命令注册表排序并列出 alias

**背景：** 人工 smoke 发现 `/help` 按注册顺序显示主命令，未展示 `/auto-approve-switch` 等可实际补全的 alias，也未明确 `/approval` 的参数；帮助内容与可用命令不一致。

**决策：**

- `help_entries()` 和 `completions()` 都从当前 CommandRegistry 派生并按命令名排序。
- 帮助逐项显示 alias，alias 指向主命令的参数说明；主命令描述包含必要参数。
- `/approval` 接受 `prompt|auto`，同时兼容旧 `/auto-approve-switch on|off` 语义。

**理由：**

- 注册表是命令可用性的唯一事实来源，帮助和补全必须与其保持一致。
- 明确参数可避免用户输入无参数命令时只能得到不透明错误。

**曾考虑的替代方案：**

- 维护独立 help dict —— 会再次产生漂移，已拒绝。
- 删除兼容 alias —— 违反已确认的 R5 兼容要求，已拒绝。

---

### 决策 160 — 不保留 /auto-approve-switch 向前兼容

**背景：** 用户指出 `/auto-approve-switch` 的命名语义应当是无参数切换；要求它携带 `prompt|auto` 或 `on|off` 参数会造成命令名与实际行为矛盾。维护 alias 也让帮助和补全承担不必要的旧行为说明。

**决策：**

- 删除 `/auto-approve-switch`，不做向前兼容。
- `/approval` 无参数时在 `prompt` 与 `auto` 间切换；携带 `prompt` 或 `auto` 时显式设置。
- 审批模式继续仅为 CliApp 进程内偏好，不写入 ToolDefinition、Runtime 或 snapshot。

**理由：**

- 单一命令同时提供符合名称的快捷切换和可预测的显式设置。
- 移除 alias 可让帮助、补全和实际行为保持一一对应。

**曾考虑的替代方案：**

- 保留 alias 并让其无参数切换 —— 仍保留无价值的旧入口，已拒绝。
- 保留 alias 并要求参数 —— 与 switch 语义矛盾，已拒绝。

---

### 决策 161 — 恢复 DeepSeek Web Search 的旧版请求契约并拒绝未执行调用

**背景：** v2 `OpenAIWebSearchAdapter` 将旧版 `LLMClient.web_search()` 的两轮请求简化为新的 system/user 文本，并移除了两轮调用的 `max_tokens=4096`。真实 provider 随后返回 `<｜｜DSML｜｜tool_calls>`，该文本是未执行的 `web_search` 调用，却被 adapter 当作成功结果写入 session，导致后续模型在无真实搜索内容的条件下作答。

**决策：**

- 恢复旧版的精确 DeepSeek 请求契约：system prompt、`Perform a web search for the query: {query}` 用户消息、`max_tokens=4096`、`web_search` function schema 和第二轮的 `Provide the result` tool result。
- 保持 `WebSearchPort`、`ToolContext` 和 `ToolSuccess/ToolFailure` 边界不变；这是既有 adapter 的 provider 协议修复，不新增搜索服务或公共接口。
- 如果 provider 仍以 `<｜｜DSML｜｜tool_calls>` 返回未执行调用，adapter 必须抛出错误，由工具层转为 `web_search_failed`，不得写成 `ToolSuccess`。
- 增加 adapter 契约测试，并执行一次最小真实 DeepSeek provider smoke，确认恢复契约后返回正常的搜索摘要。

**理由：**

- 该搜索能力由 DeepSeek 在 OpenAI 兼容调用链中提供；旧协议已在项目中实际运行，迁移时不应以通用化提示词替换 provider 专用 wire contract。
- 对未执行调用 fail closed，可防止 session 和后续回答把控制标记误作事实性搜索结果。

**曾考虑的替代方案：**

- 接入第三方搜索供应商 —— 当前没有必要；会改变既有 provider 边界、配置和计费方式。
- 接受 DSML 文本并让后续模型继续处理 —— 已被真实 session 证明会产生无依据回答。

---

### 决策 162 — R5 工具可见性使用强类型事件投影

**背景：** 当前 CLI 仅显示 `正在执行工具：<name>` 与 `工具完成：<name>`。`ToolStarted` 未携带参数，`ToolFinished.output` 未被 Renderer 显示；Plan 工具虽更新了领域状态，但用户看不到具体计划项和进度。复杂任务的执行过程因此不可审阅。

**决策：**

- `ToolStarted` 新增只读 arguments 映射，Renderer 负责按敏感字段脱敏、按长度截断后显示摘要。
- `ToolFinished` 新增可选只读 `Plan` 投影。只有成功的 Plan 工具调用携带该投影，Renderer 直接渲染计划项、状态和当前项，不反解析字符串化的工具结果。
- 普通工具完成时展示截断结果预览；完整内容仍留在 session dump，避免终端被大结果淹没。
- 不新增 RuntimeEvent 种类、不让 CLI 读取 Session 或 PlanService。持续驻留的 Sticky Plan 继续暂缓，基础 Plan 表格不再暂缓。

**理由：**

- 参数、结果与计划进度是用户审阅工具行为的最小证据；强类型投影既保持 CLI 薄层，也避免 JSON 字符串协议漂移。
- 统一在 Renderer 做脱敏和截断，避免各工具自行拼装面向终端的展示文本。

**曾考虑的替代方案：**

- Renderer 解析 `ToolFinished.output` 中的 JSON — 耦合工具 payload，且失败/格式变化会破坏展示。
- 每次工具完成都输出完整原始结果 — 对搜索、文件和长文本工具会造成终端噪声并可能暴露敏感内容。

---

### 决策 163 —— 用户拒绝审批立即结束当前 Agent 回合

**背景：** 用户在 CLI 中对 `ApprovalRequested` 选择 No 后，Runtime 曾将其统一编码为普通 `ToolFailure("rejected")`，随后发出 `ToolFinished`。CliApp 按一般工具完成事件继续发送 `Continue`，模型收到拒绝结果后可能再次请求同一工具，用户无法立即取回输入控制权。

**决定：**

- `Reject` 表示用户对当前 pending tool call 的明确否决，不属于可由模型自行修复的工具执行失败。
- Runtime 仍须生成带 `code: "rejected"` 的 `ToolResultRecord`，以闭合 call 并保持 session codec 与 snapshot 的完整性；随后清除 pending call、进入 `CANCELLED` 并返回 `Cancelled`。
- CliApp 收到该终态后执行既有 snapshot 逻辑并退出内层 Agent loop，立即显示下一次输入框；不发送 `Continue`，不把拒绝结果交回模型。
- 网络、provider、参数或业务层面的实际工具失败继续维持 `ToolFinished` → `Continue`，让模型获得错误上下文并尝试自修复。

**理由：**

- 用户的明确拒绝是交互边界上的终止意图，不能被模型重试覆盖。
- 保留结构化 tool result 可维护每个已发起 call 都有闭合记录的 Runtime 与持久化不变量。
- 将“拒绝”和“执行失败”分开后，既保证用户可控，也不牺牲模型对技术失败的修复能力。

**曾考虑的替代方案：**

- 继续把拒绝作为普通 `ToolFailure`，仅由提示词要求模型不重试 —— 无法保证行为，且 CLI 仍不能立刻归还输入。
- 不记录 tool result 直接取消 —— 会留下未闭合的已声明调用，破坏会话记录与 snapshot 的一致性。

---

### 决策 164 —— 审批交互使用明确选项而非 `y/N`

**背景：** v2 `InputController.confirm()` 使用 `questionary.confirm()`，终端会显示 `y/N` 文本确认。用户要求恢复 v1 审批界面的明确选项交互，以便直接看见“执行”与“取消”。

**决定：**

- `InputController.confirm()` 改用 `questionary.select()`，固定显示“✅ 执行”和“❌ 取消”两个选项。
- 选中“✅ 执行”返回 `True`，其余选择与输入取消保持拒绝语义；`CliApp` 继续将布尔结果映射为既有 `Approve/Reject` command。
- 不引入 v1 的 `ConfirmChoice` 类型，也不让 v2 依赖旧模块；选项仅是 InputController 内部展示细节。

**理由：**

- 选项列表在终端中更易识别，且与 v1 已验证的审批体验保持一致。
- 保持 `confirm() -> bool | None` 公开契约不变，不影响 Runtime、CliApp 和自动审批模式。

**曾考虑的替代方案：**

- 继续使用 `questionary.confirm()` 并调整提示文本 —— 仍会保留 `y/N` 交互，不符合目标。
- 复用旧 `ConfirmChoice` —— 会让 v2 CLI 反向依赖 legacy 代码，违反受控重构边界。

---

### 决策 165 —— `/rewind` 在回退前捕获预填文本

**背景：** `/rewind` 的 handler 在执行 `RewindSession(turn_id)` 后，才从返回的 `SessionView.rewind_points` 查找目标回合并生成 `PREFILL`。回退会截断目标回合及其之后的记录，目标文本因此常常不在新投影中，导致 CLI 无法预填。

**决定：**

- CommandRegistry 在发送 `RewindSession(turn_id)` 前，从当前公开 `SessionView.rewind_points` 找到目标 `turn_id` 对应的用户文本。
- 回退成功后用已捕获的文本返回 `CommandResult(CommandAction.PREFILL, text)`；CliApp 将其传给下一次 `InputController.read(prefill)`。
- 回退后的 `SessionView` 仅用于刷新输入历史和渲染会话摘要，不用于反查已截断的目标文本。

**理由：**

- 预填文本是用户选择回退目标时已公开的稳定数据，无需访问私有 history 或 snapshot。
- 保持 CLI 薄层职责：CommandRegistry 只编排公开 Application API，InputController 只负责展示预填。

**曾考虑的替代方案：**

- 让 Application 在 rewind 返回值中新增 target text —— 当前 `SessionView` 已能在操作前提供所需投影，扩展 application 协议没有必要。
- 从 Session 私有 history 或磁盘 snapshot 读取目标文本 —— 破坏既定的 CLI/Application 边界。

---

### 决策 166 —— `/restore` 与 `/rewind` 的选择菜单提供取消项

**背景：** `/restore` 和 `/rewind` 使用 questionary 选择列表时，用户只能通过 Ctrl+C 中断选择。该操作会以终端中断的方式返回，缺少明确、可发现的正常取消路径。

**决定：**

- 两个命令的无参数选择列表末尾固定追加“❌ 取消”。
- 选择该项时 CommandRegistry 返回 `HANDLED`，不发送 `RestoreSession` 或 `RewindSession`，CliApp 自然进入下一次输入。
- `InputController.select()` 的通用取消（EOF、KeyboardInterrupt）继续保留；显式取消项只用于这两个会话管理命令。

**理由：**

- 用户无需记忆 Ctrl+C，即可安全地退出会话选择。
- 在 CommandRegistry 消化取消意图，不会让 Application 或 Session 层感知 CLI 展示选项。

**曾考虑的替代方案：**

- 为所有 `InputController.select()` 自动加入取消项 —— 会改变工具选择等其他交互的选项契约，范围过大。
- 仅提示用户使用 Ctrl+C —— 交互不可发现，且不满足正常返回 CLI 的需求。

---

### 决策 167 —— G5 已通过且 R6 暂停

**背景：** 用户已确认 R5 的 V50–V56 人工 smoke 可接受，独立 v2 CLI 的 G5 门禁满足。R5 的临时 `scripts/v2_runtime_smoke.py` 已完成其过渡验证职责，应按既定计划删除。

**决定：**

- 通过 G5，删除 `scripts/v2_runtime_smoke.py`，保留 `python -m src.get_me_in.cli` 作为 R8 切换前唯一的 v2 CLI 入口。
- R5 任务标记完成，当前状态保存为“R6 尚未启动”。
- 按用户明确指示，不提交 R6 新文件、类和公开方法清单，也不开始 R6 编码；未来恢复时仍需先经过该确认门禁。

**理由：**

- G5 的人工 smoke 与核心自动化回归均已有明确验收证据，保留临时 Runner 只会形成第二条验证入口。
- 停在已完成的 R5 可保留清晰、可恢复的项目状态，同时尊重用户对后续阶段的节奏控制。

**曾考虑的替代方案：**

- 删除 Runner 后立即开始 R6 —— 超出用户授权，且绕过 R6 清单确认门禁。
- 保留 Runner 以备后续使用 —— 与 R5/R8 的单一 v2 CLI 入口约定冲突。

---

### 决策 168 —— R5 审查修复命令事件闭合与错误边界

**背景：** G5 通过后的代码复审发现，`/exit_sub` handler 直接渲染 `ExitSubAgent` 返回的 RuntimeEvent，却没有交回 CliApp 继续驱动。主 Agent 下调用会抛出 `ValueError` 并终止 CLI；活动 handoff 下调用会留下处于待继续阶段的源 Runtime。相同的命令异常边界也会让无效 restore/rewind 参数直接退出 CLI。既有测试只验证 handler 调用了 Application，没有贯通 CommandRegistry、CliApp 和后续 Continue。

**决定：**

- `CommandAction` 增加 `DRIVE`，`CommandResult` 增加可选 RuntimeEvent；会产生运行事件的 CLI 命令必须把事件交回 CliApp 的统一事件循环。
- `/exit_sub` 不再在 handler 内自行渲染事件；CliApp 收到 `DRIVE` 后按现有 RuntimeEvent 规则继续推进并在终态 snapshot。
- CliApp 在命令 dispatch 边界捕获预期异常，调用 Renderer 显示错误后返回输入循环；不捕获 `KeyboardInterrupt` 之外的进程控制异常。
- 增加命令事件继续驱动和命令失败后继续输入的跨组件测试；完整核心回归增至 134 项。
- 修正 R5 设计文档中“不修改 RuntimeEvent/Session 投影”的过期描述，明确实际扩展及对应决策；不借修复进入 R6 编码。

**理由：**

- RuntimeEvent 的下一步只能由 CliApp 决定，handler 渲染后丢弃会破坏 pull-driven 状态机。
- 用户输入的无效命令或参数属于可恢复 CLI 错误，不应形成进程级失败。
- 以强类型 `DRIVE` 表达事件转交，继续避免魔法 dict，同时保持 CommandRegistry 不复制 RuntimeEvent 分支逻辑。

**曾考虑的替代方案：**

- 在 `/exit_sub` handler 内循环调用 Continue —— 会复制 CliApp 的审批、选择、终态与 snapshot 规则，已拒绝。
- 只为 `/exit_sub` 捕获 `ValueError` —— 无法覆盖 restore/rewind 等同类用户可控错误，已拒绝。
- 提前建立 R6 通用 ApplicationCommand worker 协议 —— 超出本次 R5 修复范围，留待 R6 设计整理，已拒绝。

---

### 决策 169 —— R6 重设一致性边界并增加强制终止门禁

**背景：** R5 修复完成后复审 R6，发现原设计只有 KnowledgeService/MemoryService 的方向，没有固定长时间 CLI command 如何经过 WorkerRunner、Memory 如何合法取得会话输入、后台任务和前台取消如何隔离、manifest 如何区分 observed/indexed 状态，也没有资源唯一 owner 和阶段终止门禁。原任务还重复提出 SearchQuery/SearchResult，并允许 R6/R7 并行，容易在 Knowledge/Memory 未稳定时提前进入 Resume。

**决定：**

- 保留现有 RetrievalPort/RetrievalResult；删除重复 SearchQuery/SearchResult、MemoryService.search 和 v1 RagLoader Facade 形状。
- R6 新增 `CommandAction.RUN`、typed ApplicationCommand/ApplicationResult 和 WorkerRunner 执行路径；`/ragreload` 前台串行且可取消，`/build-memory` 复制会话输入后排入单非 daemon worker。
- `SessionService.memory_source()` 只返回复制后的 provider-neutral ConversationRecord；CLI、MemoryExtractor 和后台任务不得读取 SessionState/private history。
- manifest 同时记录 observed/indexed hash、pending operation、chunk ids、status/error；index/repository 部分成功必须可见且可重试，不得误报全部成功。
- v2 Chroma、manifest 和 Memory 使用 `data/v2/` 全新 schema-versioned 路径；不读取旧 Chroma、旧 Markdown Memory 或 `.last_update`。
- JsonMemoryRepository 同时实现 MemoryRepository 与只读 KnowledgeSourceRepository；KnowledgeService 启动和全量 reload 显式扫描 reference 与 v2 memory repositories，不依赖写入回调恢复 memory index。
- Application 通过 ResourceStack 管理顶层 owner；close 逆序、幂等、失败隔离并返回 timeout/error report。前台 reload、活动 Runtime 与后台 Memory 使用不同 cancellation 所有权。
- `Application.finalize_turn()` 负责终态 snapshot 与可选 auto-memory 排队，保持 CLI 不接触 history，且 Memory 失败不覆盖原终态。
- R6/R7 不再并行。增加 R6-T 强制终止门禁：G6 后只允许 checkpoint、提交证据并停止，未经用户后续明确授权不得进入 R7 或 R8。
- R6 文件、对象、构造依赖与公开方法以 `docs/design.md#69-knowledge-与-memory` 为待确认清单；当前会话只更新文档，不创建或修改 R6 代码。

**理由：**

- 长时间 reload 与非阻塞 memory build 是两种不同执行语义，必须在 application/worker 边界显式建模，不能继续由 command handler 直接阻塞或自行开 daemon thread。
- observed/indexed 双状态和 pending operation 可以表达文件已变但旧 index 仍有效、删除中断和失败重试，单一 hash/status 无法可靠恢复。
- 单一资源 owner 与独立 cancellation 避免 close 双调用、后台 Memory 被 Esc 误取消或前台 reload 无法停止。
- 终止门禁让 R6 的真实模型、Chroma、后台关闭和一致性证据先接受用户审查，再决定是否承担 R7 的 Resume/Artifact 复杂度。

**曾考虑的替代方案：**

- 直接迁移 v1 RagLoader、Memory Facade 和 observer callbacks —— 会恢复全局状态、延迟 import 和不可恢复的隐式索引，已拒绝。
- 让 `/ragreload` 和 `/build-memory` 在 CommandRegistry handler 中直接调用 service —— 会绕过 WorkerRunner、spinner/cancel 和强类型 ApplicationResult，已拒绝。
- 让 CLI 读取 SessionSnapshot/history 构造 Memory —— 违反 R4/R5 的只读投影与私有状态边界，已拒绝。
- 继续并行 R6/R7 —— 会绕过用户要求的 R6 完成后停顿，也会让 Resume 验收依赖尚未稳定的 Knowledge/Memory，已拒绝。

---

### 决策 170 —— R6 清单获确认并固定新会话实施入口

**背景：** R6 设计复审已固定新增、删除、修改范围以及文件、对象、构造依赖和公开方法清单。用户确认该清单，同时明确当前会话不写 R6 代码，需要通过文档 checkpoint 让后续新会话 bootstrap 后获得完整实施边界。

**决定：**

- 用户确认 `docs/design.md#69-knowledge-与-memory` 的 R6 清单；R6 coding 门禁已解除，但本次确认不授权在当前会话编写代码。
- 当前会话只更新 `docs/current.md`、活跃 refactor 文档与本决策记录，并创建独立 docs checkpoint 提交；不得创建或修改 R6 代码。
- 后续新会话必须先执行 `/project-bootstrap`，以 `docs/current.md` 路由到活跃文档；第一切片仅创建 `domain/knowledge.py`、`domain/memories.py`、`ports/knowledge.py`、`ports/memories.py` 与 `test_knowledge_service.py`，只实现 domain/ports/manifest diff 纯逻辑。
- 第一切片须独立验证、独立提交，之后才按 6.9.4 的固定顺序继续 R6；清单确认不允许一次性创建其余文件，也不扩大 R6 修改范围。
- R6-T 仍是强制终止门禁：G6 后只允许整理验收证据和 `/project-checkpoint`，状态必须保存为“R6 完成、R7 未启动、等待用户审查”，随后停止。未经用户后续明确授权不得进入 R7 或 R8。

**理由：**

- 把授权状态、第一切片和禁止越界项写入 `docs/current.md` 及活跃文档，可让新会话只依赖标准 bootstrap 流程恢复，不依赖本次聊天记录。
- 将第一切片限制为 domain/ports/manifest diff，能先稳定纯逻辑与协议，再引入资源、线程、模型和 Chroma 等副作用边界。
- 保留 R6-T 可以确保 R6 完成后的审查不会被“清单已确认”误解为继续推进 R7 的长期授权。

**曾考虑的替代方案：**

- 当前会话直接开始 R6 coding —— 与用户明确要求冲突，已拒绝。
- 只修改 `current.md`，不更新 task/design/plan/decision —— 新会话可能读到相互矛盾的“待确认”状态，已拒绝。
- 清单确认后一次性创建全部 R6 文件 —— 破坏逐切片验证与独立提交要求，已拒绝。

---

### 决策 171 —— R6 前增加独立 `thinking` 契约修复门禁

**背景：** R6 coding 启动前复核系统提示词与模型回复，发现静态 `07_output_format.md` 仍要求 finish 输出 JSON `thinking`，`ModelReplyParser` 也会解析该字段，但 v2 AgentRuntime 只把 content 写入 MessageRecord，导致 thinking 在解析后被丢弃，无法展示、dump 或随 snapshot 恢复。现有测试只保护了“不回放给下一轮 LLM”，没有保护“当前回复仍须保留”。这偏离决策 135/136 和 v1 可观察行为。

**决定：**

- 在 R5 与 R6 之间增加独立 R5-F 和验收门禁 G5-F；当前会话只更新文档，不修复代码，也不创建 R6 文件。
- finish 的 JSON thinking 为必需 string，tool_call thinking 可选；决策 171 仅取代决策 77 对 finish thinking 的可选化，保留 tool_call 容错。这是模型生成的用户可见摘要，不是 provider 原生 reasoning_content。继续禁止捕获或暴露原生 reasoning_content。
- assistant MessageRecord 与 ToolCallRecord 保存可选 thinking；RuntimeEvent、Session snapshot 和 Renderer 保留该投影。v2 新增独立 `show_thinking` setting 读取 `SHOW_THINKING`，与控制 provider 模式的 `llm_thinking_enabled` 分离。
- ConversationCodec 发往下一轮 LLM 时始终剥离 thinking；“不回放”不能再通过“解析后永久丢弃”实现。
- R6 的总体设计、文件清单和第一切片不变，但新增 G5-F 前置依赖。`SessionService.memory_source()` 必须把复制记录中的 thinking 规范化为 `None`，防止 MemoryExtractor 将展示摘要当成会话事实。
- G5-F 通过、独立提交并 checkpoint 前不得开始 R6；R6 完成后的 R6-T 终止门禁不变。

**理由：**

- thinking 属于一次模型回复的可观察数据；是否展示和是否回放是两个不同决策，不能用丢数据代替上下文过滤。
- 原生 reasoning_content 可能泄漏系统提示词与内部推导，而 JSON thinking 是受项目输出协议约束的用户可见摘要，两者必须保持类型和设置隔离。
- 在 MemoryBuildSource 复制边界剥离 thinking，可同时保留 snapshot/诊断能力并避免 R6 Memory 提取增加噪声或敏感输入。

**曾考虑的替代方案：**

- 把修复并入 R6 —— 会混合通用 Runtime/Session/CLI 契约和 Knowledge/Memory 副作用，扩大 G6 定位范围，已拒绝。
- 保持 parser 接收后丢弃 —— 继续浪费输出 token，并违反已确认的可展示/可 dump 行为，已拒绝。
- 将 provider reasoning_content 用作 thinking —— 决策 136 已因安全和 prompt injection 风险拒绝，继续不采用。
- 让 MemoryExtractor 自行忽略 thinking —— 会把展示数据泄漏到后台 LLM 输入，边界过晚，已拒绝。

---

### 决策 172 —— R5-F follow-up 统一格式修复的唯一契约与重试边界

**背景：** G5-F 首次 checkpoint 后运行真实 v2 CLI，模型在工具结果后的回复连续两次解析失败。会话 snapshot 只能看到旧 Runtime 注入了 `Return exactly one JSON object with a string content field.`，既没有完整 output format，也没有保存具体解析错误或原始失败回复。该提示与 G5-F 新增的 finish `thinking` 约束冲突：模型即使按提示只返回 content，仍会再次失败。

**决定：**

- finish 必须出现 string `thinking` 字段，但允许值为 `""`；tool_call 可省略 `thinking`，也允许值为 `""`。
- `07_output_format.md` 使用条件 schema 表达 finish 的字段要求；`PromptRenderer.render_output_format()` 是 repair 规则的唯一读取入口，Runtime 不再维护简化副本。
- 首次 `ModelReplyParseError` 将“具体解析错误 + 完整 canonical output format”作为 `Role.SYSTEM` 消息注入；不把无效原始回复写回会话历史。
- 每个用户回合最多进行一次格式修复。修复后的回复仍无效时立即返回 `invalid_model_reply`；整个回合还受 `AGENT_MAX_MODEL_CALLS` 总上限约束，不允许无限重试。
- 完整原始回复只进入 DEBUG 日志，正常日志和 system repair message 只保留必要诊断信息。

**理由：**

- 条件字段要求与 parser、prompt、repair message 使用同一契约，避免“提示模型修成另一种仍非法的格式”。
- 具体错误可让模型定向修复，完整规则避免遗漏 `thinking`、event_type 或工具字段。
- 单次 repair 在容错和成本可控之间保持明确边界，也防止格式错误形成无限模型循环。
- 不回放无效原文可避免污染会话；DEBUG 日志仍为人工诊断保留完整证据。

**曾考虑的替代方案：**

- 继续注入只要求 content 的简化提示 —— 与 finish 契约冲突，已拒绝。
- 将无效原始回复和错误一起注入模型 —— 会扩大上下文污染和敏感信息暴露，当前没有必要。
- 持续重试直到解析成功 —— 成本和终止时间不可控，已拒绝。

---

### 决策 173 —— v2 显式装配日志并固定环境变量所有权

**背景：** 独立入口 `python -m src.get_me_in.cli` 没有导入旧 `src.logger`，因此旧 `data/logs/app.log` 在 v2 运行期间不会更新。格式修复失败时 Runtime 又丢弃 `ModelReplyParseError` 细节和原始回复，CLI 只能显示通用 `invalid_model_reply`。同时 `.env` 同时保留 legacy 与 v2 配置，容易误以为 `AGENT_MAX_ROUNDS`、`WORKING_DIR` 或旧 RAG/Memory 路径已经控制 v2。

**决定：**

- 新增 v2 `logging_setup.configure_logging(log_dir, level)`，由 CLI composition 阶段显式调用；只配置 `src.get_me_in` logger 命名空间，不接管 root logger 或第三方 SDK 日志。
- 使用 `RotatingFileHandler` 写入 `LOG_DIR/app.log`，10MB × 5；stderr 只显示 ERROR+。INFO 记录 CLI 生命周期，WARNING 记录 provider/timeout/格式错误及最多 500 字符预览，DEBUG 记录完整模型原始回复。
- v2 Settings 显式读取并校验 `LOG_LEVEL`、`LOG_DIR`。当前 `.env` 的 `LOG_LEVEL=DEBUG` 会记录完整模型回复，日常使用可改回 INFO。
- v2 只消费 `Settings.from_env()` 声明的变量。legacy `AGENT_MAX_ROUNDS` 不控制 v2；v2 使用 `AGENT_MAX_MODEL_CALLS`，未配置时默认 12。`WORKSPACE_DIR`、`SESSIONS_DIR` 未配置时分别使用 `data/workspace/`、`data/v2/sessions/`。
- legacy RAG/Memory、`WORKING_DIR` 与 `SAVE_DIR` 配置在对应 v2 阶段正式迁移前不生效；后续阶段新增 typed Settings 时必须同步 `.env.example` 与 checkpoint 说明。

**理由：**

- 显式 CLI 装配符合 v2 禁止 import-time 全局副作用的边界，也能保证真实入口一定启用诊断。
- 仅捕获 v2 namespace 避免 DEBUG 模式重新引入 httpx/OpenAI 等第三方噪声。
- 把“环境中存在”与“v2 当前消费”明确分开，可防止调错无效变量并误判运行限制或数据路径。

**曾考虑的替代方案：**

- 直接复用 legacy `src.logger` —— 会让独立 v2 反向依赖旧基础设施，已拒绝。
- 配置 root logger —— 会收集大量第三方 DEBUG 日志并降低可读性，已拒绝。
- 只在 CLI 显示更多错误而不落盘 —— 无法保留模型原始回复和跨运行诊断证据，已拒绝。

---

### 决策 174 —— G6 通过并停在 R6-T 审查门禁

**背景：** R6 的六个固定切片已完成，需要把完成事实、验证证据与下一阶段的停止边界写入受控状态，避免将“R6 完成”误解为自动授权 R7。

**决定：**

- 认定 G6 通过：`IndexManifest.diff()`、资源生命周期、KnowledgeService、local/Chroma adapters、MemoryService 以及 Settings/bootstrap/CLI 接入均已完成；真实 `KnowledgeService` 已替换并删除 `DeferredRetrievalAdapter`。
- 验收证据为 171 项核心自动化测试、`compileall` 与真实 Chroma/embedder/reranker 临时目录 smoke 均通过。
- 执行 checkpoint，将状态固定为“R6 完成、R7 未启动、等待用户审查”；不得创建或修改 R7 文件、切换入口或执行 R8 清理。

**理由：**

- R6 已形成可审查的独立边界；先审查 Knowledge/Memory 的一致性和资源关闭，再决定是否授权 Resume/Artifact 的下一阶段。

---

### 决策 175 —— 撤销 G6 通过结论并授权 R6-F 审查修复

**背景：** R6-T 代码审查确认原 171 项测试虽然断言通过，但测试进程因非 daemon worker 泄漏不能正常退出；同时发现 Knowledge 未启动、reload cancellation 未接通、search 未与 mutation 串行、Chroma replace/delete 可误报一致、Memory partial failure 不可观察以及 worker timeout 后可能关闭仍在使用的依赖。决策 174 的 G6 通过结论缺少这些交叉契约证据。

**决定：**

- 撤销决策 174 中“G6 已通过”的结论，保留 R6-T 对 R7/R8 的禁止；当前阶段改为 R6-F，用户已明确授权修复代码。
- BackgroundWorker task 接收独立 `CancellationSignal`，新增 `BackgroundJobState`、`BackgroundJobResult` 与 `result(job_id)`；`/build-memory` 继续立即返回 receipt，本轮不增加 CLI 查询命令。
- `KnowledgeService.delete_source()` 增加可选 repository finalize callback，按 manifest intent、index delete、repository finalize、manifest commit 协调 Memory 删除。
- 启动加载、前台 reload cancellation、search/mutation 串行、Chroma 可恢复 replace/delete、Memory typed partial failure、timeout-safe close、静态 memory prompt 与测试 cleanup 统一纳入 R6-F。
- R6-F 只修改既有 R6 文件、对应测试和文档；不创建 service/module 文件，不修改 R7、旧 `main.py`、RuntimeCommand/RuntimeEvent 或 snapshot schema。

**理由：**

- 这些问题影响 G6 明确要求的一致性、取消、资源所有权和可验证性，必须在进入 R7 前闭合。
- typed job result 与 finalize callback 是异步结果和跨 repository/index 删除事务所需的最小公开扩展；继续依赖异常吞噬或无结果 receipt 无法证明 partial failure。
- 保持四个独立切片可使每组修复分别验证、提交和回滚。

**曾考虑的替代方案：**

- 保留 G6 通过并把问题延后到 R8 —— 会让错误的一致性与关闭契约成为后续迁移基础，已拒绝。
- 让 MemoryBuildReceipt 持有 Future —— 会把运行时同步对象放入 immutable domain DTO，已拒绝。
- Memory 删除先移除 repository 再尽力删除 index —— 无法满足 manifest delete intent 与可恢复重试约束，已拒绝。

---

### 决策 176 —— R6-F 完成并重新通过 G6

**背景：** 决策 175 撤销了原 G6 结论，并授权四个独立修复切片。修复需要证明启动、取消、索引与 Memory 部分失败、关闭顺序和真实 adapter 链路均已闭合，且测试进程能够正常退出。

**决定：**

- 认定 R6-F 完成并重新通过 G6；再次进入 R6-T 强制终止门禁，R7/R8 仍未授权。
- 四个修复切片分别提交为 `05c4956`、`73a1c79`、`79c0601`、`38708e2`，保持可独立审查与回滚。
- 验收证据为 `uv run python -m unittest discover -s tests/get_me_in -t .` 正常退出并通过 187 项测试、`compileall` 通过，以及 `uv run python -m scripts.r6_knowledge_smoke` 输出 `R6_SMOKE_OK hits=1 score=0.961208`。
- 真实 smoke 暴露的 Chroma query embedding 容器类型、Windows client 关闭和模型默认值漂移已纳入切片 4；Settings 恢复 BAAI 模型基线并兼容旧环境变量名。

**理由：**

- 自动化测试正常退出证明非 daemon worker 泄漏已闭合；真实 adapter smoke 证明查询、rerank、删除和资源释放在实际依赖上可运行。
- typed background result、delete finalize 和 timeout-safe close 使 partial failure 与资源所有权能够被应用层观察并安全重试。
- R6-T 继续隔离后续迁移风险；R6 验收不构成进入 R7 或清理旧实现的授权。

---

### 决策 177 —— 确认 R7 总体边界并提交具体清单审查

**背景：** R6-F 已重新通过 G6 并停在 R6-T。R7 启动前对实际 v2 composition、Resume 工具和 restore 边界复核后，确认生产 Application 仍只装配 Main Runtime，Artifact schema/repository 尚未建立；同时发现 `ToolContext.session_id` 在 bootstrap 时捕获初始值，连续 restore 后可能使 workspace revision grant 与 artifact provenance 使用错误 scope。原 R7 任务没有固定双 Runtime 的资源所有权、Artifact build-attempt schema 或 metadata partial failure 的恢复语义。

**决定：**

- R7 第一切片固定为 R7-P dynamic session identity：`SessionState` 继续是唯一长期 session id 来源，由 Orchestrator 在每次 `AgentRuntime.advance(..., session_id=...)` 时传入当前值；禁止新增全局或可变 session-id 镜像。
- Resume 保留除 `route` 外的 v1 capability parity：`system`、`plan`、`interaction`、`web.search`、`external_file.read`、`return_to_main`、`workspace.read/write/open`、`resume.artifact` 与 `knowledge.query`。
- Main/Resume 分别拥有 Runtime、CancellationToken、PlanService、ToolContext 与 LLM；共享 adapter 只由一个顶层 owner 关闭，跨线程取消继续只经过 `Application.request_cancel()`。
- Artifact 使用全新 `data/v2/artifacts/` versioned repository，独立于 Memory 与 SessionSnapshot；save/restore/rewind 不删除、覆盖或回滚工作区文件和 Artifact 记录。
- ArtifactService 是 tool-facing `ResumeArtifactPort` 的正式实现，并借用 `LocalResumeArtifacts` backend 处理静态模板和 `pdflatex`。现有工具名称、LLM 参数 schema 与 Runtime/ToolOutcome 闭合协议不变。
- Artifact operation 使用 deterministic key 和 pending → side effect → commit；记录所有 build attempt，只有 `exit_code == 0` 且 PDF 存在时创建可用 PDF Artifact。文件成功但 metadata 提交失败时返回 typed partial failure，并允许 retry reconcile。
- 将 R7 新文件、对象、构造依赖、公开方法、允许修改文件和六个实施切片写入 `docs/design.md#6104-r7-新文件对象与公开边界清单待确认`。该具体清单尚待用户最终确认；本 checkpoint 不授权创建 R7 文件或修改代码。
- G7 通过后仍须 checkpoint 并停止；R8 的旧 `main.py` 入口切换和遗留删除继续需要后续独立授权。

**理由：**

- 动态传入 session id 能保持 SessionState 的单一事实来源，并让 workspace 授权与 Artifact provenance 使用同一 scope。
- 独立 Runtime/LLM ownership 避免两个 Agent 共享 mutable cancellation 或重复关闭同一 LLM，同时保持 Hub-and-Spoke 编排不变。
- 独立 Artifact repository 能保存产物版本和失败编译记录，而不污染只保存 fact/preference 的 Memory，也不把外部文件副作用伪装成可 rewind 的 Session 状态。
- 两阶段 operation 和 typed partial failure 使“文件已改变、metadata 未提交”可观察、可恢复，不会把局部完成误报成完整成功。
- 先提交具体清单再请求最终确认，符合新模块先讨论设计、列文件/类/公开方法后再编码的受控重写门禁。

**曾考虑的替代方案：**

- 继续使用 bootstrap 时固定的 `ToolContext.session_id` —— 连续 restore 后可能跨 session 复用 revision grant，已拒绝。
- Main/Resume 共用同一 LLM 或 CancellationToken —— 所有权和关闭边界不清，取消也可能污染非活动 Agent，已拒绝。
- 把 ArtifactRef 写入 SessionSnapshot 并随 rewind 回滚文件 —— 文件系统副作用不可由对话 snapshot 原子撤销，已拒绝。
- 只在 PDF 成功时记录、忽略失败 attempt —— 会丢失编译诊断与重试证据，已拒绝。
- metadata 保存失败仍返回工具成功 —— 会误报 artifact/version 已持久化，已拒绝。

---

### 决策 178 —— 确认 R7 具体清单与 temperature/log 补充

**背景：** 决策 177 已确认 R7 五项总体边界，但具体文件、对象、构造依赖、公开方法与实施切片仍处于最终确认门禁。补充审查发现 v2 `LLMRequest` 和 OpenAI adapter 没有表达旧决策 117 中 Main `0.1`、Resume `0.2`、MemoryBuilder `0` 的显式 temperature 行为；Artifact build attempt 若无限保存 stdout/stderr 或写入 workspace 绝对路径，也会形成持久化膨胀与路径泄露风险。

**决定：**

- 用户确认 `docs/design.md#6105-r7-新文件对象与公开边界清单已确认` 中的新文件、对象、构造依赖、公开方法、允许修改文件和七个实施切片；R7 的 coding 清单门禁解除。
- 新增独立前置切片 R7-P0：`AgentSpec.temperature: float` 固定 Main `0.1`、Resume `0.2`；`LLMRequest.temperature: float | None = None`；MemoryExtractor 显式传入 `0.0`。OpenAI adapter 只透传非 `None` 值，并校验其为 `[0, 2]` 内的有限数。
- Artifact 使用 `schema_version=1`；Artifact 保存 `content_hash`，模板来源只保存 `template_name`，operation key 使用 canonical JSON 的 SHA-256。
- 每次 build attempt 的 stdout/stderr 各自最多持久化 65536 bytes。保存前将 workspace 绝对根替换为 `<workspace>/`，再按 UTF-8 安全的 head/tail 截断，默认各保留 32768 bytes；同时保存原始字节数与 truncated 标记。
- `ArtifactPartialFailure` 保留 typed code、changed_paths、message，并映射到既有 `ToolFailure`，不扩展 ToolOutcome。pending operation 只在后续相同 operation key 调用时惰性 reconcile；R7 不新增 daemon、CLI 查询命令或 pruning/retention policy。
- R7 按七个切片实施：R7-P0 temperature → R7-P dynamic session identity → Resume composition → Artifact domain/repository → ArtifactService/copy/build/log → Settings/bootstrap/resource ownership → 真实 Resume smoke/G7。每个切片独立验证、提交并停止。
- 用户明确要求当前会话仍不 coding，只同步活跃设计、计划、任务、current 和本决策并创建文档 checkpoint。后续新会话执行 `/project-bootstrap` 后，只能从 R7-P0 开始；G7 通过后仍须 checkpoint 并等待 R8 的独立授权。

**理由：**

- 显式 temperature 保留已验证的角色差异，避免 provider 默认值变化悄然改变 Main、Resume 或 Memory 提取行为；独立 R7-P0 可在引入 Artifact 副作用前验证该横切契约。
- 固定日志上限与路径脱敏能保留编译首尾诊断，同时避免巨大或敏感的本机输出进入长期 repository；原始长度和截断标记使诊断方明确知道记录不完整。
- schema version、content hash 与 deterministic operation key 为幂等重试和未来迁移提供稳定依据；惰性 reconcile 足以闭合当前 tool 调用，不需要提前引入后台协调器。
- 维持既有 ToolOutcome 和 SessionSnapshot 边界，可把 R7 变更限制在已确认的 Resume/Artifact 纵向切片内。

**曾考虑的替代方案：**

- 继续依赖 provider 默认 temperature —— 行为随 adapter 或 provider 漂移，且无法表达 MemoryExtractor 的确定性偏好，已拒绝。
- 为所有 LLM 请求强制一个全局 temperature —— 会抹平 Main、Resume 与 MemoryExtractor 的职责差异，已拒绝。
- 完整保存 build stdout/stderr —— 可能无限膨胀 repository 并泄露绝对路径，已拒绝。
- 只保存固定前缀或仅保留失败摘要 —— 容易丢失编译器末尾的最终错误和上下文，已拒绝。
- 在 R7 增加后台 reconcile、日志清理命令或自动 retention —— 超出当前纵向切片且引入额外生命周期，延后到有真实容量证据后再决策。

---

### 决策 179 —— R7-P0 temperature 契约完成并继续 R7

**背景：** R7 已确认的第一切片需要恢复 Main、Resume 和 MemoryExtractor 的显式 temperature 契约，避免依赖 provider 默认值。当前生产 composition 尚未创建 Resume AgentSpec，该工厂属于后续已确认的 Resume composition 切片。

**决定：**

- `AgentSpec.temperature` 成为必填且受 `[0, 2]` 有限值校验的声明；当前 Main 固定为 `0.1`，后续 `build_resume_spec()` 必须固定为 `0.2`。
- `LLMRequest.temperature` 采用可选字段；AgentRuntime 透传 AgentSpec 值，MemoryExtractor 显式传入 `0.0`，OpenAI adapter 仅对非 `None` 的有效值传给 provider。
- 针对性自动化测试通过 27 项；R7-P0 完成。用户已明确授权在无新增决策时继续 R7-P 及其后的已确认切片，仍不得切换旧 `main.py` 或进入 R8。

**理由：**

- 显式请求值稳定了角色差异，同时让不指定 temperature 的调用保持 adapter 无隐藏默认值的语义。
- Resume 工厂尚未获准在 P0 之外提前创建；将 `0.2` 固定在该工厂的实施切片，可维持已确认的按切片范围控制。

**曾考虑的替代方案：**

- 在 P0 预先创建 Resume AgentSpec 工厂 —— 跨越已确认的切片边界，已拒绝。
- 由 OpenAI adapter 为未指定请求填入全局默认值 —— 会隐藏调用方契约并造成 provider 行为漂移，已拒绝。

---

### 决策 180 —— R7-P 动态 session identity 完成

**背景：** composition root 创建 ToolContext 时会捕获初始 session id，而 restore 可替换 SessionState。若工具继续读取固定值，workspace revision grant 与后续 Artifact provenance 会脱离唯一的 SessionState。

**决定：**

- `AgentRuntime.advance()` 显式接收当前 `session_id`；Orchestrator 从传入的 SessionState 在每次调用时提供它。
- Runtime 只在该次 `advance()` 的工具执行中，用 session id 替换 immutable ToolContext 模板中的 scope；调用返回后清除该临时值。
- SessionService 保持 restore 清理离开和进入 session scope、rewind 清理当前 scope 的行为；连续 restore 与 main→resume→main handoff 已加入回归。

**理由：**

- 这使 SessionState 保持唯一长期事实来源，不需要全局变量、CLI 私有读取或第二份可变 session-id 状态。
- 后续 ArtifactService 可以直接使用动态 ToolContext 的 session id 与 agent key 记录 provenance。

**曾考虑的替代方案：**

- 在 ToolContext 或 composition root 保存可变 session id —— 会形成第二份长期状态并在 restore 后漂移，已拒绝。

---

### 决策 181 —— Resume 双 Runtime composition 完成

**背景：** R7 需要以声明式 Resume Agent 替换旧 14 个元数据方法，并保证 Main 与 Resume 的运行、取消和 LLM 生命周期互不污染。

**决定：**

- 新增 `build_resume_spec()`，固定 Resume `temperature=0.2` 和已确认的非路由 capability 集合。
- `build_application()` 接受覆盖 Main/Resume 且实例互异的 `runtime_llms` 映射；生产装配为两个独立 adapter。
- Application 不再公开单一 runtime 或 cancellation；SessionService/Orchestrator 管理双 Runtime，取消只送往 active agent。

**理由：**

- 声明式 spec 保留 Resume 行为约束而不重新创建无状态价值的旧 Agent 类。
- 独立所有权防止 Resume 取消或 close 影响 Main 的正在进行或未来请求。

---

### 决策 182 —— Artifact 使用 operation aggregate 持久化

**背景：** 已确认的 ArtifactRepository 只有 `save_operation()` 一个写入口，但 R7 仍需原子保存 Artifact 与 build-attempt。

**决定：**

- `ArtifactOperation` 增加不可变 `artifacts` 与 `build_attempts` 元组；repository 以逐 operation JSON 单次原子 replace 保存整个 aggregate。
- 副作用前保存无结果的 PENDING；副作用后保存携带全部结果的 COMMITTED。COMMITTED 表示本次尝试记录已完整持久化，业务成功仍由 process 结果表达。
- `list_artifacts()` 与 `list_build_attempts()` 从 operation records 展开；不增加独立保存接口或扩大 R7 责任范围。

**理由：**

- metadata 提交失败时原 PENDING 仍在，后续相同 key 调用可安全 reconcile；成功时状态和结果同时可见。

---

### 决策 183 —— R7-P5 ArtifactService 完成

**背景：** Artifact aggregate repository 已完成，但 Resume 工具仍需在不改变 ToolOutcome 的前提下协调 PENDING、文件副作用、COMMITTED 结果和失败重试。

**决定：**

- ArtifactService 直接实现 ResumeArtifactPort；copy/build 均先持久化 PENDING，再经 LocalResumeArtifacts backend 执行副作用，并以一次 aggregate replace 提交结果。
- 同 key 的 COMMITTED 调用返回已持久化结果；PENDING 的模板复制以相同内容预检避免重复写入，已有 PDF 的 PENDING 生成 reconcile attempt 并补提交 artifact。
- 非零、超时、取消和 backend 异常都形成 build-attempt；只有成功且 PDF 存在时记录 PDF Artifact。metadata 提交失败继续映射为 `ArtifactPartialFailure`。
- stdout/stderr 在 workspace 根替换与 UTF-8 安全截断后，保证持久化字节总量不超过配置上限。

**理由：**

- operation aggregate 保证 operation 状态与其结果对 repository 读取者原子可见；保留 PENDING 则使局部完成具备可恢复证据。
- 将模板读取和进程调用保留在 backend，使 application service 不越过已确认的分层边界。

---

### 决策 184 —— R7-P6 production composition 完成

**背景：** P5 已具备 ArtifactService，但 production composition 仍没有将 repository、日志上限和实际 pdflatex timeout 作为 Settings 管理的依赖。

**决定：**

- Settings 增加 `artifacts_dir`、`pdf_build_timeout_seconds`、`artifact_log_max_bytes`，默认分别为 `data/v2/artifacts/`、60 秒和 65536 bytes；环境变量为 `PDF_BUILD_TIMEOUT_SECONDS` 与 `ARTIFACT_LOG_MAX_BYTES`，均拒绝非正值。
- bootstrap 以 LocalResumeArtifacts 作为低层 backend，构造唯一的 JsonArtifactRepository 与 ArtifactService，并将同一个 service 注入 Main/Resume ToolContext。
- ResourceStack 只登记 ArtifactService 的 `close()`，由它关闭 repository；不改变 ToolOutcome、SessionSnapshot 或旧 `main.py`。

**理由：**

- 配置化使生产 timeout 与日志边界可显式审计、可测试；单一资源 owner 避免共享 repository 的重复关闭。

---

### 决策 185 —— 批准原始字节 content_hash 并完成 R7/G7

**背景：** 真实双语 PDF smoke 表明 `WorkspacePort.read()` 是文本接口，不能读取二进制 PDF；以文本解码内容计算 Artifact hash 会破坏原始字节语义。

**决定：**

- WorkspacePort 增加 `content_hash(path) -> str`，固定为受限工作区内文件原始字节的 64 位小写 SHA-256；LocalWorkspace 先经 `resolve()` 限制路径，再以流式二进制读取计算摘要。
- `read()` 与 FileSnapshot.revision 保持文本语义；ArtifactService 对所有 Artifact 类型统一使用 `workspace.content_hash()`，不直接读取文件系统、不增加通用二进制读取接口、Tool、Capability 或 CLI。
- 真实中文、英文、双语模板在隔离工作区完成复制、README 读取与 pdflatex 编译，生成四份 PDF；全量 205 项自动化测试和 `compileall` 通过。R7/G7 至此完成，必须停在 R8 独立授权门禁前。

**理由：**

- 原始字节摘要才稳定表达 PDF 与文本产物的实际内容，且不改变 workspace 的文本编辑／revision 边界。
- 将 hash 保留在 WorkspacePort 避免 ArtifactService 越过端口边界，也不混淆编译 backend 与内容查询职责。

---

### 决策 186 —— 撤回 G7 完成结论并记录 R7-T 审查问题

**背景：** 决策 185 记录了 R7 七个代码切片、真实 Resume smoke、205 项自动化测试与 `compileall` 通过，并据此认定 G7 完成。后续 R7-T 审查在当前环境重新确认 205 项测试、`compileall` 与 `git diff --check` 通过，但发现现有测试没有覆盖四类关键缺口：PENDING build 可能把旧 PDF 误判为当前构建成功；文件副作用后的 metadata preparation 与 ToolFailure 映射没有完整保留 typed partial failure／`changed_paths`；结构合法但字段损坏的 Artifact JSON 会泄漏 `KeyError`／`ValueError` 等非 typed 异常；`task.md` 仍有直接属于 G7 的 temperature、已有简历修改、capability、审批、取消、restore／rewind 与 handoff 端到端验收项未完成。本轮没有重新执行真实 `pdflatex` smoke。

**决定：**

- 撤回决策 185 中“R7/G7 已完成”的门禁结论；R7 七个切片已经编码、205 项测试与既有 smoke 的事实记录继续保留，但不能等同于 G7 已通过。
- 将当前状态设为“R7-T 审查修复待授权”；在四类审查问题修复、未完成 G7 端到端项补齐并重新 checkpoint 前，不得进入 R8。
- 在 `docs/task.md` 记录旧 PDF reconcile、typed partial failure、损坏 JSON typed failure 与完整 G7 复验四组待办；本 checkpoint 只记录问题，不授权或实施任何代码修复。
- 后续若获用户授权，必须先确认修复切片与验证范围；修复后运行针对性测试、完整自动化测试、`compileall`、`git diff --check` 与真实 Resume smoke，并同步 `current.md`、`task.md`、`decision.md` 后再决定是否恢复 G7。

**理由：**

- 自动化测试全绿只能证明已覆盖行为没有回归，不能证明 PENDING 副作用归属、partial failure 可观察性和损坏持久化记录边界正确。
- G7 是进入 R8 的强制依赖；任务文件仍存在直接对应 G7 的未完成项时，继续维持完成结论会使入口切换与遗留删除失去可靠门禁。
- 保留已完成代码和验证事实、仅撤回验收结论，可以准确区分“实现已存在”与“阶段已验收”，也符合受控重写在审查点停止的要求。

**曾考虑的替代方案：**

- 保留 G7 完成结论，把问题延后到 R8 或 R9 —— 会允许在 Artifact 一致性和端到端证据不完整时切换入口，已拒绝。
- 本 checkpoint 直接实施修复 —— 用户明确要求先只记录问题，未授权代码修改，已拒绝。

---

### 决策 187 —— R7-T 修复完成并重新通过 G7

**背景：** 用户在决策 186 的问题 checkpoint 提交后授权开始修复。三个已知 Artifact 问题分别涉及 PENDING PDF 归属、文件副作用后的 partial failure 可观察性，以及损坏 JSON 的 typed decode/aggregate validation。补齐 G7 已有简历 edit/replace smoke 时又发现 Windows 文本模式会把模板中已有 CRLF 再次转换，插入空行并导致精确 edit 行号漂移。

**决定：**

- PENDING PDF operation 重试时重新执行受 cancellation／timeout 控制的构建，不再仅凭同名 PDF 已存在就合成成功；只有本次实际构建返回 exit code 0 且 PDF 存在时登记可用产物。
- 文件副作用完成后的 Artifact DTO 构造、`content_hash()`、`next_version()` 与 repository commit 统一纳入 `ArtifactPartialFailure("metadata_commit_failed", changed_paths, message)`；Resume tool 通过既有 ToolFailure message／suggestion 暴露内部 code 与可能已改变的路径，不扩展 ToolOutcome schema。
- JsonArtifactRepository 将 JSON object、顶层／nested schema、必填字段、枚举、时间以及 PENDING/result ownership 不变量的失败统一转换为 `ArtifactRepositoryError`；save 与 load 使用相同 aggregate 校验。
- `LocalWorkspace.write()` 禁用平台换行转换，保证写入字节、返回 revision 与后续 read 的文本一致；已有 CRLF 不再变成 CRCRLF。
- 新增 production composition 回归覆盖 Main→Resume→Main、审批拒绝、Main／Resume temperature、Resume capability/prompt 与 handoff 后 snapshot/rewind/restore；结合既有 MemoryExtractor、workspace、CLI Esc 与 session 测试完成 G7 验收矩阵。
- 最终 212 项自动化测试、`compileall` 与 `git diff --check` 通过。真实 ArtifactService 在隔离工作区生成中文、英文、双语共 4 份 PDF；另完成已有英文简历 replace、workspace grant 清理后拒绝旧 revision、重新读取、精确 edit 与真实 PDF 编译。恢复 G7 完成结论，继续停在 R8 独立授权门禁前。

**理由：**

- 重新构建比根据无法证明归属的旧 PDF 猜测副作用已完成更安全，并继续保持 operation key 的幂等结果边界。
- partial failure 必须让调用方知道文件可能已改变；复用 ToolFailure 的现有字段可以保留可观察性而不扩大 Runtime 协议。
- repository typed failure 必须覆盖结构和 aggregate 语义，而不只是 JSON 语法，否则损坏持久化数据仍会泄漏实现异常。
- workspace revision 必须描述实际可再次读取的文本；禁止隐式换行转换可以同时保护 LaTeX 行号、hash 与 read-before-edit 契约。

**曾考虑的替代方案：**

- 为 PENDING operation 增加新的副作用阶段或 PDF baseline hash 字段 —— 会修改已确认的 schema/public boundary；当前重新构建已能安全闭合问题，未采用。
- 将 `changed_paths` 加入 ToolFailure 公共 schema —— 会扩大 R7 Runtime 协议；既有 suggestion 足以表达，未采用。
- 仅调整 smoke 脚本行号以绕过 CRLF 问题 —— 会掩盖真实用户编辑时的行号漂移，已拒绝。

---

### 决策 188 —— R7-T2 审查再次撤回 G7 并细化 R8

**背景：** 用户要求在 R7 coding 完成后开始审查，并更新 R8 任务细节。当前环境重新运行 212 项自动化测试、`compileall` 与 `git diff --check` 均通过；但静态审查和两个临时目录最小复现发现，决策 187 所述 Artifact retry 与 aggregate typed failure 仍有未覆盖路径。R8 当前粗粒度任务也没有给出切换观察门禁、精确删除集合、配置迁移和旧数据保护方法。

**决定：**

- 暂时撤回决策 187 的 G7 完成结论，但保留其五个修复提交、212 项测试和真实 Resume smoke 的历史事实；R7-T2 修复与完整复验前不得进入 R8。
- R7-T2 分为三个不扩展公开 API 的候选修复切片：
  1. `JsonArtifactRepository` 的 save/load 共用校验补齐字段类型、deterministic operation key 与 kind/status/result shape；损坏记录统一为 `ArtifactRepositoryError`。
  2. `ArtifactService.build_pdf()` 与 Resume tool 统一首次和重放的 backend exception／无结果状态，禁止相同 committed attempt 从 `ToolFailure` 漂移为 `ToolSuccess`。
  3. `build_application()` 对 ResourceStack 建立前后的构造失败统一逆序关闭已创建 owner，覆盖 injected LLM validation、Memory prompt 读取和 knowledge start 失败。
- R8 候选实施顺序固定为 R8-P 准备 → R8-E 根入口切换 → R8-O 强制观察与用户审查 → R8-D 精确遗留删除 → R8-G 文档与 G8。R8-E 和 R8-D 必须是独立提交；R8-O 未通过时使用 `git revert <R8-E commit>` 回退。
- R8 不新增 runtime class、service、port、schema 或公开方法。根入口只允许委托现有 `src.get_me_in.cli.main.main()`；遗留删除范围和保留范围以 `docs/design.md` 第 6.11 节为准。
- 旧 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 是不迁移的历史用户数据；R8 只验证 v2 不访问，禁止自动删除。`.ipynb_checkpoints` 必须按精确路径复核后单独清理。
- 本轮只更新审查结论和 R8 任务细节，不授权或实施 R7-T2／R8 coding。

**证据：**

- 全量测试输出为 `Ran 212 tests ... OK`；`compileall` 与 `git diff --check` 正常结束。
- 一个合法 JSON 形状但 `COMMITTED + BUILD_PDF + build_attempts=()` 的 operation 可被 repository 保存和读取；随后 `ArtifactService.build_pdf()` 在 `existing.build_attempts[-1]` 抛出 `IndexError`。
- backend 首次抛出 `RuntimeError("compiler unavailable")` 后，service 保存 COMMITTED attempt 并向调用方抛错；第二次同 key 调用返回 `ProcessResult(exit_code=None, timed_out=False, cancelled=False)`，而当前 Resume tool 仅对 cancelled／timed_out 映射失败，其余结果返回 `ToolSuccess`。
- `build_application()` 在 worker／Knowledge／Artifact owner 创建后才校验 injected Runtime LLM，并在全部 owner 创建后才建立 ResourceStack；中途异常没有统一 cleanup 边界。

**理由：**

- 绿色测试不能替代未覆盖的持久化 corruption 与 retry 语义；同一 operation 的首次和重放结果必须稳定，损坏记录必须在 repository 边界转换为 typed failure。
- 入口切换会把当前 composition root 变为默认生产路径；构造失败清理、`.env.example` 与 Settings 一致性必须在切换前闭合。
- 入口切换、观察和删除拆分后，失败可以通过单独 revert 恢复旧入口，同时保留旧代码和旧用户数据供诊断。

**曾考虑的替代方案：**

- 保持 G7 完成并把问题并入 R8 —— 会在已知 Artifact retry 误报与 corruption 泄漏存在时切换默认入口，已拒绝。
- R8-E 与 R8-D 同一提交 —— 会失去可观察、可回退的旧实现缓冲期，已拒绝。
- R8 自动删除旧运行数据 —— 与 R-D6 的“不迁移”不等于“授权删除”相冲突，已拒绝。

---

### 决策 189 —— R7-T2 修复完成并再次恢复 G7

**背景：** 用户确认修复决策 188 记录的三个 R7-T2 问题。修复继续遵守不改变 Artifact schema/version、operation key 算法、ToolOutcome schema、public repository/service 方法与全局生命周期的边界，并按三个独立切片实施。

**决定：**

- `JsonArtifactRepository` 的 save/load 使用同一 aggregate validator，验证顶层和 nested 字段类型、deterministic operation key、PENDING/COMMITTED 与 COPY_TEMPLATE/BUILD_PDF 的 result shape；损坏记录统一抛出 `ArtifactRepositoryError`。提交：`e963b11`。
- `ArtifactService.build_pdf()` 将 backend exception 规范化为持久化的 `ProcessResult(exit_code=None)`，首次和同 key replay 返回相同结果；Resume tool 将无 exit code、非 timeout、非 cancelled 的结果稳定映射为 `ToolFailure("build_pdf_failed", ...)`。提交：`e0e2041`。
- `build_application()` 使用临时 `ExitStack` 持有部分 composition 资源；成功后把所有权交给现有 Application/ResourceStack，任一步失败则关闭已构造 owner。runtime LLM mapping 在资源创建前校验，并覆盖 Memory prompt 读取和 Knowledge start 失败。提交：`6af22a3`。
- 最终 216 项自动化测试、`compileall` 与 `git diff --check` 通过。真实临时工作区成功复制中文／英文模板并编译两份 PDF，两个 build exit code 均为 0，repository 记录 5 个 artifacts 与 2 个 build attempts。
- 再次恢复 G7 完成结论。继续停在 R8 独立授权门禁前；决策 188 细化的 R8 五切片仍只是候选清单，未经用户确认不得 coding。

**理由：**

- Aggregate 在 repository 边界被完整验证后，service 不再需要防御无法成立的 committed shape，也不会泄漏 `IndexError`。
- 将 backend exception 归一为可持久化结果，使首次执行和 replay 具有相同的工具语义，同时保留原始诊断文本。
- 临时 construction ownership 与稳定运行期 ResourceStack 分离，既覆盖部分构造失败，又不改变正常关闭顺序和唯一 owner。

**曾考虑的替代方案：**

- 为 backend exception 新增 Artifact schema 字段或异常类型 —— 会扩大已确认公共边界，现有 `exit_code=None` 与 stderr 已足够表达，未采用。
- 只提前校验已知失败点而不建立统一 cleanup —— 仍会遗漏未来新增构造步骤，已拒绝。

---

### 决策 190 —— R8 设计审查收紧入口错误、回退配置与验收证据

**背景：** G7 恢复后对 R8 候选清单与实际 v2 composition、Settings、Catalog、CLI 文档和仓库状态进行只读复核。五切片顺序仍然成立，但发现四个会削弱切换门禁的问题：`cli.main.main()` 只处理 Settings 校验错误，composition／启动异常仍会向根入口泄漏 traceback；R8-P 原计划在切换前删除 v1-only `.env.example` 项，导致单独 revert R8-E 后旧入口可能缺少回退配置；目录 mtime／hash 不能证明 v2 没有读取旧数据；Catalog 验收只写“数量一致”而没有固定当前实际数量。另确认 README 当前为空，capability／legacy smoke 文档仍含历史 `/auto-approve-switch`，本地有三个未跟踪 `.ipynb_checkpoints` 目录。

**决定：**

- 保留 R8-P → R8-E → R8-O → R8-D → R8-G 的顺序和 R8-O 用户审查门禁。R8-P 只建立过渡态配置／README：补齐 v2 设置，但把 v1-only 变量保留在“legacy rollback only”段；R8-D 完成后才由 R8-G 删除。
- R8-E 允许在既有 `src/get_me_in/cli/main.py` 内增加最小启动异常映射：`SettingsValidationError` 返回 `2`，composition／CLI 构造或启动的 `Exception` 记录诊断、渲染简短错误并返回 `1`，正常关闭返回 `0`；不得吞掉 `KeyboardInterrupt`／`SystemExit`，不得增加公开 API。
- R8-E 允许新建纯测试文件 `tests/get_me_in/test_cli_main.py`，与既有 import/settings/CLI/bootstrap 测试共同覆盖根入口委托、三个退出码、无 traceback 与资源关闭。R8 不新增生产文件、class、service、port、schema、公开方法或 `[project.scripts]`。
- 固定 R8 验收基线为 2 个 Agent（Main／Resume）、25 个 ToolDefinition、10 个 CLI 命令；名称和数量分别从 `AgentCatalog`、`ToolCatalog.export_descriptors()`、`CommandRegistry.help_entries()`／`completions()` 取证。
- “旧数据未访问”必须由静态禁用路径／legacy 环境变量扫描、sentinel project root 的 Settings 路径断言、拒绝访问旧目录的启动／smoke 边界共同证明；mtime／hash 前后对比只证明未改写。`data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 始终保留，不迁移、不删除。
- `.ipynb_checkpoints/`、`src/.ipynb_checkpoints/`、`src/llm/.ipynb_checkpoints/` 当前均未被 Git 跟踪；R8-D 执行前再次按精确路径复核，作为本地清理证据，不伪装成提交内容。
- R8-D 前回退只 revert R8-E；R8-D 后的紧急回退按逆序先 revert R8-D、再 revert R8-E。capability／smoke 旧表保留时必须明确标为历史 baseline，不能把旧 `/auto-approve-switch` 冒充当前 `/approval`。
- 本决策只更新 R8 候选设计、计划和任务，不构成 R8 coding 授权；根 `main.py`、`.env.example`、README 和生产代码本轮均不修改。

**理由：**

- 根入口成为默认生产路径后，用户可读的启动失败和稳定退出码属于入口契约，而不是可推迟到真实 smoke 才发现的实现细节。
- 入口提交只有在旧源码和必要旧配置同时保留时才真正可以单独回退；提前清理配置会让 Git 上的“可 revert”失去运行层面的意义。
- 文件元数据只能观察写副作用，无法证明没有读；把静态、配置和拒绝访问边界组合起来，才能覆盖“未读取”和“未改写”两个不同命题。
- 固定 Catalog 数量与派生来源可以防止最终文档只做模糊的自洽检查，也避免另建一份运行时注册事实。

**曾考虑的替代方案：**

- 保持 `cli.main.main()` 不变，仅在 smoke 接受 traceback —— 不满足当前 R8-O 已写明的用户可读启动错误门禁，已拒绝。
- R8-P 直接删除所有 v1-only 配置 —— 会破坏观察期单提交回退，延后到 R8-G。
- 只比较旧数据目录 hash／mtime —— 只能证明未写，不能证明未读，未采用。
- 在 R8 增加 console script —— 当前根入口与模块诊断入口已经足够，会扩大待确认生产入口面，未采用。

---

### 决策 191 —— 授权 R8 实施并完成 R8-P

**背景：** 用户明确要求先通过 project-bootstrap 恢复状态，然后在 R8 已完成设计范围内自动实施；每个阶段完成后使用 checkpoint 保存状态，只有遇到需要用户决策的事项才暂停。R8-O 原有的用户审查门禁保持有效。

**决定：**

- R8 由 R8-P 开始实施，不新增生产 class、service、port、schema 或公开方法。
- R8-P 已完成并独立提交 `d91e37c`：`.env.example` 与 `Settings.from_env()` 的 v2 变量、默认值和兼容别名对齐；仅供回退旧入口的变量保留在明确的 `legacy rollback only` 段；README 记录观察期入口、静态输入、新旧运行数据与回退边界。
- 导入边界扫描扩展至全部待删除 legacy production modules；Settings sentinel 断言证明 legacy 环境变量不会改变 v2 的 workspace、sessions、knowledge、memories 或 artifacts 路径。Catalog 实测为 2 个 Agent、25 个 ToolDefinition、10 个 CLI 命令；三个静态资产目录均可用。
- R8-P 验证通过：完整 unittest 218 项、`compileall`、`git diff --check`。R8-O 仍需执行拒绝访问旧目录的启动／smoke 边界，并在完成后强制等待用户审查，未通过不得进入 R8-D。

**理由：**

- 将回退配置保留至观察完成，可以让 R8-E 保持真正可单独 revert 的运行时回退点。
- 静态导入扫描与 typed Settings 路径断言在入口切换前就关闭 v2 回接 legacy 模块和旧数据路径的风险；运行期拒绝访问边界留给 R8-O 的真实观察矩阵。

**曾考虑的替代方案：**

- 跳过 R8-O 用户审查并连续删除 legacy —— 与已确认的强制观察门禁冲突，未采用。

---

### 决策 192 —— R8-E 已完成并建立入口回退点

**背景：** R8-P 已完成过渡配置、README、导入边界和 Settings 数据路径审计。根 `main.py` 仍运行 legacy composition，R8-E 需要在不新增生产 API 的边界内把唯一生产入口委托给既有 v2 CLI，并保证启动失败不会向用户泄漏 traceback。

**决定：**

- 根 `main.py` 现在只导入 `src.get_me_in.cli.main.main`，并以 `raise SystemExit(main())` 传递其退出码；legacy composition 和 import-time registration 不再由根入口加载。
- v2 CLI 对 `SettingsValidationError` 保持用户可读错误和退出码 `2`；对 composition、CLI 构造、启动或运行的 `Exception` 将完整 traceback 写入日志、只显示简短错误并返回 `1`。`KeyboardInterrupt` 与 `SystemExit` 不被捕获；正常关闭返回 `0` 并关闭 Worker 与 Application。
- 新增 `tests/get_me_in/test_cli_main.py` 覆盖根入口依赖、三个退出码、无 traceback 及关闭路径。完整自动化 222 项、`compileall`、`git diff --check` 通过。
- R8-E 独立提交 `9fbeabc`。R8-D 前的回退仅可执行 `git revert 9fbeabc`；R8-O 必须先完成并经用户审查，才允许删除 legacy。

**理由：**

- 入口切换独立于删除提交，才能在观察期间保留可验证、可恢复的 legacy 实现。
- 运行日志保留完整诊断，同时把终端错误限制为可操作的简短消息，满足生产入口的稳定性与可读性契约。

**曾考虑的替代方案：**

- 让 `logger.exception()` 直接输出 traceback 到 stderr —— 会违反入口错误不向用户显示 traceback 的观察门禁，未采用。

---

### 决策 193 —— R8-O 前置审查修复入口诊断与关闭边界

**背景：** R8-E checkpoint 后进入 R8-O 前置审查。审查与真实根入口复现发现：启动异常使用 `INFO` 记录，`LOG_LEVEL` 为 `WARNING`／`ERROR`／`CRITICAL` 时完整诊断不会写入文件；`Application.close()` 返回的 `CloseReport.issues` 被入口忽略，关闭失败或超时仍可能返回 `0`；README 仍把 v2 模块入口描述为切换前预览，`.env.example` 又把 v2 实际支持的三个 RAG 兼容别名放入“v2 不读取”的 legacy-only 段。

**决定：**

- 提交 `8e43bd7` 在既有日志配置中增加内部 file-only record 标记。启动／运行异常以 `CRITICAL` 写入文件并由 stderr handler 过滤；因此所有允许的 `LOG_LEVEL` 都保留完整 traceback，终端仍只显示简短错误。日志配置本身失败时不尝试向未配置 logger 写 traceback。
- 同一提交让入口分别隔离 Worker 与 Application 的关闭异常，始终尝试关闭两者；`CloseReport.issues` 的失败／超时会写入 file-only 诊断、向用户显示资源名称和原因，并将进程退出码改为 `1`。无关闭问题的正常 `/exit` 保持 `0`。
- 提交 `45b5152` 将 README 更新为“根 `main.py` 是唯一 v2 生产入口、模块入口仅用于诊断”，并把 `BI_ENCODER_MODEL`、`CROSS_ENCODER_MODEL`、`EMBED_BATCH_SIZE` 移到 v2 兼容别名段；真正仅供旧入口回退的变量继续保留在 legacy-only 段。
- 验证结果为 225 项自动化测试、`compileall`、`git diff --check` 和 import scan 通过。真实根入口缺失／非法配置均返回 `2`；`LOG_LEVEL=ERROR` 下的真实启动异常返回 `1`，终端无 traceback、临时文件日志含完整 traceback；交互式 `/exit` 返回 `0`。
- R8-O 只完成入口契约、`/help`、`/approval`、`/exit`、正常关闭和全量回归；其余 CLI、真实 Agent／Knowledge／Memory／Resume 及旧数据拒绝访问边界仍待执行。不得据此进入 R8-D，R8-O 完成后仍必须等待用户审查。

**理由：**

- 启动失败提示用户检查日志时，诊断不能因用户选择更高日志阈值而消失；file-only 高优先级记录同时满足文件完整、终端简洁两个契约。
- `CloseReport` 是关闭失败和超时的强类型事实，入口忽略它会把异常关闭误报为成功；返回 `1` 能区分正常与异常关闭，同时保留失败隔离和逆序资源策略。
- 观察期文档必须描述当前入口和实际 Settings 行为，才能保证单提交回退说明可执行且不会把兼容别名误认为 v2 禁用变量。

**曾考虑的替代方案：**

- 继续以 `INFO` 记录异常并要求生产环境使用 `LOG_LEVEL=INFO` —— 会让受支持的高日志阈值失去诊断，已拒绝。
- 以普通 `ERROR`／`CRITICAL` 同时写文件和 stderr —— 会重新向终端输出 traceback，违反入口契约，已拒绝。
- 只调用 `Application.close()` 而不解释 `CloseReport` —— 会继续把 typed failure 静默丢弃，已拒绝。
- 将针对性修复视为 R8-O 已完成 —— 仍缺真实链路和旧数据拒绝访问证据，已拒绝。

---

### 决策 194 —— 恢复固定欢迎 banner 并暂缓主题客制化

**背景：** R8-E 将根 `main.py` 切换到 v2 CLI 后，真实启动观察发现旧版在首次输入前显示的 `get-me-in — AI 求职助手` 欢迎 banner 没有迁移。根入口、Rich 终端和输入链路均正常，缺失原因是 v2 `CliApp.run()` 直接读取输入，而 `Renderer` 没有对应的欢迎展示方法。该问题会降低入口切换后的产品识别和 `/help` 可发现性。

**决定：**

- 将 banner 丢失认定为 R8-O 观察期回归，并对决策 190／191 的“R8 不新增公开方法”边界作一次用户明确批准的最小例外：只新增 `Renderer.render_welcome() -> None`，不新增生产文件、class、service、port 或 schema。
- `CliApp.run()` 在首次读取输入前调用 `render_welcome()` 一次；默认内容恢复为固定产品标识 `get-me-in — AI 求职助手` 和提示 `输入 /help 查看所有命令`，展示职责继续由 CLI Renderer 独占。
- 本次不修改 `Settings`、`.env.example` 或 Runtime/Application，不增加 banner 依赖或外部资产。
- 将显示开关、标题、副标题与样式客制化记录为 R9 增强任务。后续配置文本按普通文本安全渲染，不得默认解释为 Rich markup；实施前仍需提交 Settings／公开方法清单。
- 验证结果为 29 项 CLI 针对性测试和完整 227 项自动化测试通过，`compileall`、`git diff --check` 与 import scan 通过；真实 `uv run python main.py` 在首次输入提示前显示 banner，`/exit` 正常返回退出码 `0`。

**理由：**

- banner 是入口展示行为，放在 Renderer 并由薄 CliApp 触发符合现有职责边界，也避免根 `main.py` 重新承担终端表现。
- 固定内容足以闭合当前回归；把用户配置同时加入 R8 会扩大 Settings、示例配置和安全渲染范围，不利于观察期保持最小改动。
- 明确测试“首次输入前且只显示一次”可以防止 restore、rewind 或多回合循环重复输出欢迎信息。

**曾考虑的替代方案：**

- 在根 `main.py` 直接打印 Rich Panel —— 会污染唯一生产入口的委托职责，未采用。
- 复用 `render_notice()` 输出纯文本 —— 无法恢复旧版 Panel 产品标识，也会混淆普通通知和启动展示语义，未采用。
- 本次直接加入 `.env` 主题配置 —— 会扩大 R8 已确认配置契约并引入 Rich markup 安全边界，延后到 R9。

---

### 决策 195 —— Tool 提示词语义缺失阻断 R8-O

**背景：** 使用生产 `build_application()`、真实 `AgentCatalog`／`ToolCatalog` 和 `PromptRenderer` 导出 Main／Resume system prompt 后，确认当前工具目录实际只包含 `name`、简短 `description`、参数类型和 required 列表。旧版 Tool 的 `purpose`、`use_when`、`do_not_use_when`、`expected_output`、参数描述与默认值没有进入 v2 `ToolDefinition`／`ToolSchema`，也没有被 PromptRenderer 输出；因此这不是 Notebook 导出遗漏，而是全部 25 个生产 Tool 的 LLM-facing 语义退化。现有 capability、confirmation、typed handler validation 只能控制可见性、审批和执行边界，不能替代工具选择、相似工具消歧、参数构造和结果理解所需的提示信息。

**决定：**

- 用户明确要求该问题必须修复，不接受维持现状。立即将其设为 R8-O/G8 阻断项；修复、完整自动化和真实 Main／Resume prompt／行为复验完成前，不得通过 R8-O、执行用户审查或进入 R8-D。
- 本 checkpoint 只记录问题，不修改生产代码。下一步必须先提交 `ToolDefinition`／`ToolSchema` 强类型字段、PromptRenderer 输出、25 个工具逐项迁移映射、兼容边界和独立测试切片清单供用户确认。
- 修复至少恢复 purpose、use_when、do_not_use_when、expected_output、参数 description/default，并对适用参数表达 allowed values/items；保留现有 type/required、Capability、confirmation、handler 和 ToolOutcome 运行时边界。
- 当前 `src/tools/` 下 9 个 legacy Tool 定义文件仍保留完整元数据，Git 历史显示它们未在 v2 重构期间被修改，可作为迁移基线。逐项审计若发现某个工具缺失、描述已发生历史改写或无法确认原意，再由用户提供对应原始定义；当前无需用户额外提供。
- 验收必须直接检查真实 Main／Resume system prompt，而不只检查 Tool 名称和数量；同时覆盖 capability 隔离、相似工具选择边界、参数说明／默认值／允许值和 expected output。既有 25 Tool 数量基线不因本修复改变。

**理由：**

- Runtime 拒绝非法参数只能让模型在失败后自修复，不能弥补调用前缺少使用时机、禁用条件和参数语义；继续切换会降低工具选择准确率并增加无效重试。
- R8-D 计划删除 legacy `src/tools/`，必须在删除前完成语义迁移和逐项对照，避免唯一可直接审查的历史定义退出工作树。
- 先确认强类型字段与迁移清单，可以避免简单复制旧 XML 字符串、重新引入全局 Registry，或把 LLM 提示语义错误塞入 ToolPolicy。

**曾考虑的替代方案：**

- 维持精简 `description`，依赖模型自行推断或 handler 报错 —— 用户明确拒绝，且无法满足行为对齐。
- 把旧字段全部拼接进单个 `description` —— 会丢失结构、难以测试和演进，也无法可靠表达参数默认值／允许值，未采用。
- 将 use/do-not-use 规则写入通用静态 prompt —— 会让 Agent 看见不可用工具规则，并产生 ToolCatalog 与 prompt 的双重事实源，未采用。
- 先执行 R8-D，之后从 Git 历史恢复旧定义 —— 会人为移除当前最直接的逐项迁移基线，已拒绝。

---

### 决策 196 —— 恢复 25 个 Tool 的完整 LLM-facing 语义

**背景：** 决策 195 将 Tool 提示词语义缺失设为 R8-O 阻断项。实施前逐项盘点确认 v2 的 25 个 Tool 均能在 9 个 legacy Tool 文件中找到同名原始定义，不需要用户补充；但 `workspace_edit.revision`、capability、审批和 typed outcome 等属于 v2 已确认的新边界，不能用旧 Registry 或旧 handler 覆盖。

**决定：**

- `ToolDefinition` 使用显式 `purpose`、`use_when`、`do_not_use_when`、`expected_output`，不再用单个精简 description 承载全部 LLM-facing 语义。
- 新增 immutable `ToolParameter`，与 `ToolSchema.required` 共同表达参数 value type、description、default、list items、allowed values 和 nullable。构造时拒绝未声明 required、required+default、required+nullable、类型错误的 default／allowed value，以及非 list 参数的 items。
- PromptRenderer 为每个当前 Agent 可见 Tool 输出结构化 JSON：name、四类工具指导字段、properties、required 和 expected output；参数类型使用 JSON Schema 名称，nullable 输出类型联合。`ToolPolicy` 继续只控制 capability 可见性和审批，不注入为工具选择语义。
- ToolExecutor 改为从 `ToolParameter.value_type/nullable` 执行既有参数边界校验；handler、ToolOutcome、RuntimeCommand/RuntimeEvent、25 个 Tool 名称与 capability 数量均不改变。
- 25 个定义以 legacy 文本为语义基线迁移；对 v2 已改变的真实行为做准确适配，例如 `workspace_edit` 保留 revision 参数和原子校验，Main 只见路由能力，Resume 不见 `switch_to_subagent`。全部定义均找到，无需用户提供原始版本。
- 验证结果：56 项 Tool/Prompt/Runtime/bootstrap 针对性测试、完整 234 项自动化测试、`compileall` 与 `git diff --check` 通过。真实 production composition 直接渲染 Main／Resume system prompt并输出 `PROMPT_SMOKE_OK main_chars=10899 resume_chars=18085 tools=25`；完整字段、参数元数据和 capability 隔离断言通过，资源正常关闭。
- 决策 195 的 Tool 阻断解除；R8-O 仍有剩余 CLI、真实 Agent／Knowledge／Memory／Resume 和旧数据拒绝访问 smoke，不因此视为整体完成，也不得提前进入 R8-D。

**理由：**

- 独立强类型字段恢复了旧版经过实践验证的工具选择和参数指导，同时保留 v2 显式 Catalog、capability 和 typed execution 的架构收益。
- 将参数描述、默认值和列表／枚举约束放在同一个 `ToolParameter` 中，可以防止多个平行映射漂移，并让 Runtime 校验与 Prompt 序列化引用同一份定义。
- 真实 composition prompt 验收直接覆盖模型实际看到的内容，避免再次出现“Catalog 名称和数量正确，但提示词语义缺失”的假阳性。

**曾考虑的替代方案：**

- 恢复旧 `Tool` dataclass、XML 与 import-time Registry —— 会重新引入已删除的全局注册和 agent 特判，已拒绝。
- 仅扩展 PromptRenderer、继续从其他位置拼接说明 —— 会形成第二份工具元数据事实源，已拒绝。
- 用 legacy 定义覆盖 `workspace_edit` 等 v2 接口 —— 会破坏 revision-aware edit 和已确认运行时边界，已拒绝。

---

### 决策 197 —— 恢复 legacy XML Tool prompt 结构与固定语义顺序

**背景：** 决策 196 首次实现将每个 Tool 序列化为单行 JSON，并使用 `sort_keys=True`。这会按字母顺序把 `do_not_use_when` 放到最前，破坏工具说明原有的阅读顺序；同时静态模板 `04_tools.md` 已使用 `<Tools>` 外层，最终形成 XML 外壳包裹 JSON Tool 的混合结构。legacy `Tool.to_xml()` 已提供经过使用验证的语义顺序，因此没有必要继续保留这一混合格式。

**决定：**

- PromptRenderer 恢复 `<Tool name="...">` 结构，内部顺序固定为 `Purpose`、`UseWhen`、`DoNotUseWhen`、`Arguments`、`ExpectedOutput`。
- `Arguments` 内保留 JSON，直接以参数名为 key；每个参数的字段顺序固定为 `description`、`type`、`required`，随后按适用性输出 `items`、`default`、`enum`。nullable 类型沿用 legacy 的 `type|null` 表达。
- Arguments 继续完全由 v2 immutable `ToolParameter`／`ToolSchema` 生成，Tool 元数据仍只有一个事实源；不恢复 legacy `Tool` dataclass、decorator 注册、import-time Registry、handler 或 agent 特判。
- 本变更只调整 LLM-facing prompt 序列化，不改变 ToolCatalog、Capability、审批、ToolExecutor、ToolOutcome、25 个 Tool 名称及任何公开运行时协议。
- 决策 196 中“输出结构化 JSON”的格式部分由本决策替代；其强类型元数据、执行校验、逐项迁移和 capability 边界继续有效。
- 验证结果：39 项 Prompt/bootstrap/ToolCatalog 针对性回归、完整 234 项自动化测试与 `compileall` 通过；真实 production composition 输出 `PROMPT_XML_SMOKE_OK main_chars=11722 resume_chars=19857 tools=25`，中文元数据、XML 顺序和 Main/Resume capability 隔离断言均通过。

**理由：**

- 固定的语义顺序先告诉模型工具用途和使用边界，再提供参数和预期输出，比按字母排序更符合工具选择与参数构造流程。
- `<Tools>`／`<Tool>` 层级保持一致，避免 XML 外壳与单行 JSON Tool 混用，同时 Arguments 中的 JSON 仍便于稳定生成和精确测试。
- 序列化格式与 Registry 架构是两个独立问题；恢复 XML 不需要、也不应恢复可变全局注册机制。

**曾考虑的替代方案：**

- 只移除 `sort_keys=True`、继续输出 Tool JSON —— 可以修复顺序，但仍保留 `<Tools>` 包裹 JSON 的混合结构，未采用。
- 把 Arguments 也改为逐字段 XML —— 会增加冗长程度和转义负担，且参数对象用 JSON 已足够清晰，未采用。
- 恢复完整 legacy Tool／Registry 实现 —— 会破坏 v2 显式 composition root 与强类型执行边界，继续拒绝。

---

### 决策 198 —— 恢复 SubAgent XML prompt 并限定路由可见性

**背景：** v2 PromptRenderer 将 AgentDescriptor 序列化为按字母排序的单行 JSON，只输出 key、name、description，遗漏 legacy SubAgentDescriptor 中用于路由判断的 responsibilities 与 hard constraints。它还简单排除“当前 Agent”后输出其余全部 Agent，导致 Resume prompt 把 Main 错列为可切换子 Agent。用户要求 SubAgent 与 Tool 使用一致的 XML 风格，并询问为何 production prompt 只有 Resume、没有 Job Search。

**决定：**

- SubAgent 恢复 `<SubAgent name="key">` XML，字段顺序固定为 `Name`、`Description`、`Responsibilities`、`HardConstraints`；多个 SubAgent 块使用一个空行分隔。
- 所有内容仍从 immutable AgentDescriptor／AgentSpec 生成，不恢复 legacy AgentRegistry、import-time 注册或 Agent 私有方法读取。
- 只有声明 `Capability.ROUTE` 的 Agent 才注入 SubAgent 列表；当前 Main 看见 Resume，Resume 的 `<SubAgents>` 内容为空。
- production Catalog 继续只装配 Main 与 Resume。legacy JobSearchAgent 明确标记为测试壳，完整 Job Search 在 R0～R8 冻结并列入后续产品能力；保留 `AgentKey.JOB_SEARCH` 和通用 orchestration 测试，不将其误报为当前可用 Agent。
- 本变更仅修复模型可见的路由描述与可见性，不改变 AgentCatalog、Orchestrator、handoff protocol 或 Tool capability。
- 验证结果：30 项 Prompt/bootstrap/Catalog/orchestration 回归、完整 235 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 composition 输出 `SUBAGENT_XML_SMOKE_OK main_chars=11930 resume_chars=19809 agents=2 tools=25`，并验证字段顺序、完整中文元数据、Main-only 可见性和 JobSearch 未装配。

**理由：**

- responsibilities 与 hard constraints 是 Main 判断是否路由、是否越权所需的核心信息，不能压缩为 display name 和 description。
- XML 层级与 `<SubAgents>` 静态模板、Tool prompt 结构及 legacy 行为保持一致，减少混合格式和模型解析歧义。
- 用 Route capability 表达可见性比按具体 AgentKey 特判更符合 v2 capability 架构，也防止专业子 Agent 把 Main 或其他 Agent 当作可直接调度目标。

**曾考虑的替代方案：**

- 只把现有三字段 JSON 改为 XML —— 仍会遗漏路由边界并保留 Resume 反向看见 Main 的错误，未采用。
- 立即把 legacy JobSearchAgent 加入 production composition —— 该实现只是测试壳，且违反 R0～R8 冻结完整 Job Search 的已确认范围，未采用。
- 恢复 legacy AgentRegistry —— 会重新引入全局可变注册与 Agent 私有状态读取，继续拒绝。

---

### 决策 199 —— 恢复 Main／Resume 完整 CommunicationStyle

**背景：** 对真实 system prompt 的复核确认，v2 `AgentStyle` 类型虽然已经支持 tone、verbosity、explanation_style、rules、avoids，但 production Main／Resume spec 只填入三条概括性文案，且 rules／avoids 使用默认空 tuple。这导致 `<StyleRules>`、`<StyleAvoids>` 为空，前三个区块也与 legacy 原始定义不一致；不是 Notebook 或 PromptRenderer 导出遗漏。

**决定：**

- Main 的 Tone、Verbosity、ExplanationStyle、4 条 StyleRules 与 6 条 StyleAvoids 全部按 legacy `MainAgent` 原文恢复。
- Resume 的 Tone、Verbosity、ExplanationStyle、6 条 StyleRules 与 4 条 StyleAvoids 全部按 legacy `ResumeAgent` 原文恢复。
- 原始文本直接进入现有 immutable `AgentStyle`，继续由 PromptRenderer 填充 `06_communtion_style.md` 的五个既有区块；不复制为第二套 prompt 拼接逻辑，不修改模板或公开接口。
- 完整对象相等测试锁定两套 AgentStyle，并通过真实 Main／Resume production composition prompt 直接验证五个区块，防止只恢复部分关键词或再次退化为空。
- 本次只恢复当前 production Main／Resume；冻结的 legacy JobSearchAgent 不因此进入 v2 composition。
- 验证结果：26 项 bootstrap/Prompt/Catalog 回归、完整 236 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 composition 输出 `COMMUNICATION_STYLE_SMOKE_OK main_chars=12111 resume_chars=20104 agents=2 tools=25`。

**理由：**

- CommunicationStyle 是 Agent 行为契约的一部分；概括改写会丢失首次交互、澄清、编辑前读取、结束条件和禁止暴露内部实现等具体行为指导。
- `AgentStyle` 已经是合适且唯一的强类型事实源，问题在 production spec 数据未完整迁移，不需要改变 PromptRenderer 或模板。
- 完整对象断言加真实 prompt smoke 同时覆盖“定义正确”和“模型实际可见”，避免再次出现类型存在但字段未填充的假阳性。

**曾考虑的替代方案：**

- 只补 StyleRules／StyleAvoids，保留前三项概括文案 —— 仍与用户原始定义不一致，未采用。
- 将缺失内容直接写死到 `06_communtion_style.md` —— 会让所有 Agent 共享错误规则并形成第二事实源，未采用。
- 同时迁移 JobSearch CommunicationStyle 并装配 Agent —— 超出当前冻结范围，未采用。

---

### 决策 200 —— 恢复 Main／Resume 剩余 Agent prompt 元数据

**背景：** 在排除 Tool、SubAgent、InputFormat、OutputFormat 后继续对照 legacy system prompt，确认 9 个静态模板、Role／Constraints 的固定 Must、Reserved 以及决策 199 已修复的 CommunicationStyle 均未发生变化。剩余差异全部来自 production Main／Resume `AgentSpec`：Name、Description、Responsibilities、PrimaryGoal、SuccessCriteria、Priorities、HardConstraints、SoftConstraints 被缩写、改写并失去项目符号／数字优先级，造成关键职责和约束缺失。

**决定：**

- Main 的 8 类动态元数据按 legacy `MainAgent` 原始语义完整恢复，包括 7 条 Responsibilities、5 条 SuccessCriteria、5 条数字 Priorities、10 条 HardConstraints 和 4 条 SoftConstraints；其中已不存在的 `switch_agent` 适配为当前真实工具名 `switch_to_subagent`。
- Resume 的 8 类动态元数据按 legacy `ResumeAgent` 原始文本完整恢复，包括 5 条 Responsibilities、4 条 SuccessCriteria、5 条数字 Priorities、7 条 legacy HardConstraints 和 4 条 SoftConstraints。
- Resume 在 legacy 基线上保留两项有独立价值的 v2 强化硬约束：“不得编造或夸大用户经历、技能等信息”和“不得路由或调度其他子 Agent；需要其他能力时应退回主 Agent”，最终共 9 条硬约束。
- 列表前缀作为 AgentSpec 字段内容保留，使 PromptRenderer 继续只负责按换行拼接；不增加按字段猜测 bullet／number 的全局渲染规则。
- 不修改静态 prompt 模板、PromptRenderer、AgentSpec 类型、Capability、AgentCatalog、Orchestrator、Tool 或 handoff 协议；完整 Job Search 继续冻结。
- 新增完整 Agent metadata 对象契约测试，并通过真实 production composition prompt 验证模型实际可见内容。
- 验证结果：32 项 bootstrap/Prompt/Catalog/orchestration 回归、完整 237 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 composition 输出 `AGENT_METADATA_SMOKE_OK main_chars=13159 resume_chars=20806 agents=2 tools=25`，并确认未重新引入旧 `switch_agent` 标识符。

**理由：**

- Main 丢失的领域限制、强制路由和澄清规则会直接改变系统边界；Resume 丢失的工作区限制、真实状态优先、编辑前重读、编译诊断与最小修改规则会直接影响工具行为。
- 恢复原始列表结构可保留优先级和规则边界，避免模型把多个独立要求理解为一段弱提示。
- 只修正 immutable AgentSpec 数据即可闭合问题，不需要破坏 v2 声明式架构；追加两项 v2 硬约束可避免“恢复 legacy”反而撤销重构期间确认的安全强化。

**曾考虑的替代方案：**

- 仅恢复最严重的 HardConstraints —— Responsibilities、SuccessCriteria 和 Priorities 仍会缺失，无法完整恢复行为契约，未采用。
- 在 PromptRenderer 中自动为 tuple 添加 bullet —— 无法区分普通列表和数字优先级，也会影响所有测试 spec，未采用。
- 逐字恢复 legacy 并删除全部 v2 新约束 —— 会撤销真实性和子 Agent 调度边界强化，未采用。

---

### 决策 201 —— 收敛模型输出协议并由 Runtime 填充内部事件字段

**背景：** R8-O 真实对话偶发出现 `Invalid model reply ... finish requires a string thinking field`。原始回复是合法 JSON，但完整复制了 InputFormat 的历史消息 envelope：包含 `id/role/timestamp/tool_call_id/plan_status`，同时像历史 assistant 消息一样不含 `thinking`。当前模板按文件名排序，OutputFormat 后仍有 InputFormat 和 Reserved；ConversationCodec 也持续向模型展示无 thinking 的 assistant 历史。解析器同时兼容 `content + nested tool_call` 与 `message/event_type/tool/event_payload` 两套形状，并未验证 prompt 声明的多个字段，进一步造成公开契约与内部行为不一致。检查同时发现 tool_call 历史错误地把 `call_id` 写入 `id`，并把 `tool_call_id` 留为 null；所有 record 的 `plan_status` 也始终为 null，与源设计的系统注入语义不符。

**决定：**

- 模型输出只保留业务字段 `event_type`、`message`、`thinking`、`tool`、`event_payload`。`id`、`role`、`timestamp`、`tool_call_id`、`plan_status` 由 Runtime／ConversationCodec 内部生成，模型提供这些字段时视为格式错误并进入既有一次修复流程。
- 唯一输出协议只有两种条件形状：finish 必须提供 string `message` 与 string `thinking`，并不得提供非 null 的 tool 数据；tool_call 必须提供 string `message`、非空 string `tool` 与 object `event_payload`，thinking 可省略但存在时必须是 string。
- `ModelReplyParser` 删除决策 141 中 `content + nested tool_call` 过渡形状兼容，只接受新的最小事件协议；拒绝未知 event type、未知／内部字段、缺失字段、错误类型和非法 finish/tool_call 字段组合。决策 141 的双协议兼容部分由本决策替代。
- `PromptRenderer` 保持其他模板稳定排序，但显式将 `07_output_format.md` 放在完整 system prompt 最后，不再让关键输出契约的位置依赖后续文件名。OutputFormat 增加 Input/Output 区别、两种完整示例和禁止复制内部字段的明确说明。
- Runtime 继续以注入的 IdGenerator 与 Clock 生成记录字段；每条 tool call 同时生成独立 `event_id` 和调用链 `call_id`。ConversationCodec 对历史 tool call 输出 `id=event_id`、`tool_call_id=call_id`，对应 tool result 使用自身 event id 并复用相同 tool_call_id。
- MessageRecord、ToolCallRecord、ToolResultRecord 以可选 Plan 保存生成记录时的系统状态；ConversationCodec 只投影 legacy `{current, completed, remaining}` 摘要且继续剥离 thinking。SessionSnapshotCodec 对 record plan 做可选持久化，旧 schema_version=2 快照缺少该字段时仍按 null 读取，不要求数据迁移。
- 本修复不改变 LLM provider、ToolDefinition、ToolExecutor、Capability、审批、ToolOutcome、handoff 或 production Agent/Tool Catalog。
- 验证结果：61 项 Parser/Prompt/Conversation/Session/Runtime/bootstrap 定向测试、完整 239 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 production composition 输出 `OUTPUT_CONTRACT_SMOKE_OK chars=12794 tools=25`，确认 OutputFormat 位于末尾、Input/Output 区分可见且 Catalog 数量未变。

**理由：**

- 模型只应表达业务决定，UUID、角色、时间与计划属于可信运行时状态；删除重复字段既缩短回复，也消除模型模仿输入 envelope 的主要诱因。
- 将 OutputFormat 固定在最后并直接展示正反边界，比依靠 repair warning 或继续增加弱提示更稳定；一次 repair 仍保留为异常兜底。
- 分离 event id 与 tool call correlation id 可保证一条调用及其结果既有各自事件身份，又能通过稳定 call id 精确闭合。
- record 级 Plan 快照恢复源设计的“系统在消息生成时盖章”语义，避免用当前最终计划倒灌覆盖历史状态；可选字段保持现有快照向后兼容。

**曾考虑的替代方案：**

- 只把 OutputFormat 移到最后 —— 可以降低误仿概率，但继续保留冗余模型字段、双解析协议和错误 UUID 映射，未采用。
- 将 finish 的 thinking 改为可选或吞掉 warning —— 会破坏已确认的思考摘要展示契约并隐藏格式漂移，未采用。
- 接受并忽略模型生成的内部字段 —— 无法及时识别模型复制 InputFormat，也容易让未来代码误用不可信 UUID、时间或计划状态，未采用。
- 为 record plan 提升 snapshot schema version —— 新字段完全可选且旧数据可无损解释为 null，强制迁移没有收益，未采用。

---

### 决策 202 —— 多余模型字段采用允许列表投影而非格式修复

**背景：** 决策 201 的首版实现把所有未声明顶层字段视为格式错误，包括模型模仿 InputFormat 生成的 `id/role/timestamp/tool_call_id/plan_status`。用户复审指出这些字段本就会由系统重新生成；仅为删除不可信字段额外调用一次模型没有收益，而且历史输入继续包含系统生成的完整 envelope，模型偶尔复制这些字段是可安全兜底的偏差。

**决定：**

- `ModelReplyParser` 只读取 `event_type/message/thinking/tool/event_payload`，其余内部字段和任意未知顶层字段直接忽略，不触发 repair，也不进入 ModelReply 或 conversation record。
- Runtime 始终使用注入的 IdGenerator、Clock、固定 assistant role、当前调用链和 Plan 快照生成 `id/role/timestamp/tool_call_id/plan_status`；同名模型值即使存在也无法覆盖内部值。
- repair 只用于无法安全解释业务意图的错误：非法／缺失 event_type、缺失或错误类型的 message/thinking/tool/event_payload，以及 finish 携带非 null tool 数据等条件冲突。
- OutputFormat 将“不得输出，否则报错”改为“无需输出；即使出现也会忽略并重新生成”，并明确其他未消费顶层字段同样忽略。
- 决策 201 中“模型提供内部／未知字段时视为格式错误”和“拒绝未知／内部字段”的部分由本决策替代；最小业务协议、OutputFormat 末尾顺序、双协议移除、业务字段严格验证、内部字段生成、UUID correlation 与 Plan 快照决定继续有效。
- 增加 Runtime 回归，证明包含伪造内部字段及未知字段的合法 finish 只调用模型一次，最终事件 id 不采用模型值。验证结果为 62 项定向测试、完整 240 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 composition 输出 `OUTPUT_PROJECTION_SMOKE_OK chars=12825 tools=25`，确认末尾 OutputFormat 与忽略／重建规则可见。

**理由：**

- 忽略不消费的数据等价于在应用边界做允许列表投影，可以把模型输出降为最小业务 DTO，同时不信任任何模型生成的系统状态。
- 多余字段不改变 event_type 或必需业务字段的含义，确定性丢弃比请求模型重写更快、更省调用，也更能容忍模型模仿历史 envelope。
- 对语义冲突继续 repair，可避免把同时声称 finish 和工具调用的回复武断解释为某一种意图。

**曾考虑的替代方案：**

- 保持所有多余字段触发 repair —— 安全性没有额外收益，却增加延迟和模型调用，用户明确否决。
- 只忽略已知内部字段、拒绝其他未知字段 —— 会让无害的 provider／模型扩展字段再次触发无意义 repair；统一允许列表投影更简单。
- 接受模型字段并在缺失时才由 Runtime 补齐 —— 会让不可信 UUID、角色、时间和计划状态进入领域边界，继续拒绝。

---

### 决策 203 —— 恢复 v2 provider JSON mode

**背景：** R8-O 真实 Resume 链路在 `workspace_list` 返回空目录后，第三次模型调用输出了 249 字符纯 Markdown 而非 JSON。Runtime 正确记录 `Model response is not valid JSON`，注入 canonical OutputFormat，并在第四次调用恢复合法 finish；但额外调用耗时约 45 秒。审查确认旧 BaseAgent 的 `_pro_params/_flash_params` 默认包含 `response_format={"type":"json_object"}`，v2 OpenAILLMAdapter 只传 model/messages/timeout/temperature/thinking，遗漏 provider 层 JSON mode，导致系统目前完全依赖 prompt 约束。

**决定：**

- OpenAILLMAdapter 的每次 `chat.completions.create()` 固定携带 `response_format={"type":"json_object"}`，恢复 legacy 已使用的 provider 约束。
- 不扩展 LLMRequest 公开协议：当前 OpenAILLMAdapter 的生产调用方只有 AgentRuntime 与 MemoryExtractor，二者 canonical 输出都要求 JSON object；Web Search 使用独立 OpenAIWebSearchAdapter 和 function-call 协议，不经过本 adapter。
- Prompt 末尾 OutputFormat、ModelReplyParser／MemoryExtractor 的内部解析，以及 Runtime 的一次格式 repair 全部保留。provider JSON mode 减少格式漂移，不能替代业务字段和条件校验。
- `LLM_THINKING_ENABLED` 行为不变；json_object 与既有 thinking extra_body、temperature、timeout、request-scoped client 和 cancellation 同时传递。
- 用户确认 Resume 可以通过 `read_customer_file` 读取用户明确指定的工作区外文件，因此本次不把修复后回复中的外部路径提示认定为问题，也不收紧 Resume 的外部文件读取能力。
- 增加 adapter 请求契约断言，确认 provider 实际收到 json_object。49 项 OpenAI adapter/Runtime/Memory/bootstrap 定向测试、完整 240 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 Pro 模型输出 `PROVIDER_JSON_MODE_SMOKE_OK keys=['ok']`，确认当前 provider 接受 json_object 并返回可解析对象。

**理由：**

- 结构化输出应同时由 provider、prompt 与内部 parser 三层保护；只靠提示词无法阻止模型在工具结果后偶发回到自然语言模式。
- 当前 adapter 的所有生产消费者都声明 JSON object 输出，固定参数比为 LLMRequest 增加当前没有调用方差异的可选字段更小、更明确。
- repair 仍有必要处理 provider 不支持／未遵循 JSON mode、截断或业务 schema 不合法等异常情况。

**曾考虑的替代方案：**

- 将纯文本自动包装为 finish —— 无法可靠判断模型原本是否意图调用工具，也无法生成可信 thinking，未采用。
- 仅加强 OutputFormat 文案 —— 本次真实 prompt 已把 OutputFormat 放在最后，仍出现纯文本，证据表明 prompt-only 不足。
- 给 LLMRequest 增加 response mode 字段 —— 当前没有非 JSON 的 OpenAILLMAdapter 调用方，会扩大公开协议和全部构造点，暂不采用；未来出现普通文本消费者时再显式拆分。

---

### 决策 204 —— 在单次模型修复前增加本地 JSON repair

**背景：** 决策 203 恢复 provider JSON mode 后，继续审查 v2 格式恢复链路发现 ModelReplyParser 只使用标准库 `json.loads`。项目仍声明 `json-repair` 依赖，但只有 legacy `src/message.py` 调用；v2 对尾逗号、JSON 字符串中的物理换行等可确定修复的语法瑕疵也会注入 OutputFormat 并额外调用一次模型。实测 json_repair 0.61.2 能把尾逗号和物理换行修复为 dict，但对普通自然语言返回空字符串。

**决定：**

- ModelReplyParser 先调用 `json.loads`；仅在 JSON 语法失败时调用 `json_repair.loads`。修复结果仍必须是 JSON object，并进入同一业务字段、类型和 finish/tool_call 条件校验；json_repair 只处理语法，不替代语义验证。
- 尾逗号、JSON string 内物理换行等可确定修复的语法瑕疵在本地恢复并继续执行，不增加模型调用。成功恢复只记录 INFO `Model reply normalized locally`，历史中仅写入 Runtime 生成的标准 MessageRecord／ToolCallRecord。
- 普通纯文本、合法 JSON string／array、缺少 event_type/message、finish 缺少 string thinking、非法 tool_call 字段或 finish/tool 数据冲突均视为解析失败；不得把纯文本包装为 finish，不得为缺失 thinking 自动补空字符串，也不得猜测或执行工具。
- 本地 json_repair 无法产生合规回复，或标准／修复后的 JSON 未通过语义校验时，AgentRuntime 沿用既有格式修复流程：注入具体错误与完整 canonical OutputFormat，设置 `repair_attempted=true`，并允许模型自修一次；第二次仍失败才返回 typed `invalid_model_reply`。
- 原始畸形回复不进入 conversation history；模型自修时只增加 Runtime 生成的 system repair message。`AgentSessionState.repair_attempted` 与 snapshot 字段继续承担运行时重试边界和 schema_version=2 持久化职责。
- 本决策不替代决策 172/203 的一次模型 repair，而是在其前增加本地语法修复层；provider json_object、末尾 OutputFormat、允许列表投影、内部字段生成和严格业务校验继续有效。
- 验证结果：61 项 Parser/Runtime/provider/bootstrap/snapshot 定向测试与完整 244 项自动化测试通过；`compileall` 与 `git diff --check` 通过。

**理由：**

- 确定性的语法修复应在本地完成，避免不必要的延迟、费用和模型调用；标准 parser 优先可避免 json_repair 对本来合法回复做不必要改写。
- finish 的 thinking 是已确认的用户可见摘要契约，不能由 Runtime 无依据地生成空值；纯文本也无法证明模型选择了 finish 而不是 tool_call。
- 一次模型自修保留了严格协议和可恢复性之间的平衡：本地层不猜业务意图，模型有一次机会按 canonical OutputFormat 重新表达，失败后再稳定退出。

**曾考虑的替代方案：**

- 本地 repair 失败后立即返回 invalid_model_reply —— 放弃了既有且已验证的一次模型自修能力，未采用。
- 将纯文本或 JSON string 自动包装为 finish —— 无法生成可信 thinking，也无法确认模型没有工具调用意图，未采用。
- finish 缺少 thinking 时自动补空字符串 —— 会绕过已确认的输出契约并制造并非由模型生成的展示数据，未采用。
- 从纯文本中推断工具名和参数 —— 可能误执行副作用，违反 typed tool boundary，明确拒绝。
- 立即删除 repair_attempted 与升级 snapshot schema —— 会扩大本次修复并破坏旧 schema v2 快照兼容，暂不采用。

---

### 决策 205 —— Main 的业务能力只由当前 SubAgent 穷尽定义

**背景：** R8-O 真实 Main 对话中，用户问候后模型主动声称可以“准备面试、推荐学习资料”；随后面对 Java 学习资料请求，模型虽然识别到没有匹配 SubAgent，仍推荐 Coursera、Udemy、Stack Overflow 等替代资源。当前 production Catalog 只有 Main 与 Resume，但 Main 的 Role／Mission 使用“对应的专业子Agent”等非穷尽表述，`05_sub_agents.md` 只输出列表而未声明其权威性；同时 Main 持有 `SYSTEM`、`WEB_SEARCH`、`KNOWLEDGE_QUERY` 等宽 capability，其中 `query_reference_data` 的使用说明明确包含技术知识、面试题和推荐资料。模型因此同时看到“纯路由”“未来领域名称”和可执行领域工具，无法稳定区分辅助工具与当前对外业务能力。

**决定：**

- Main 是纯路由入口，自身不提供任何领域业务能力。Main 面向用户可声明、路由和承诺的业务能力完全由当前 `<SubAgents>` 提供；该列表是当前会话唯一、权威且穷尽的能力来源，不是示例或未来规划。
- Main 不得根据产品名称、工具列表、历史消息、模型已有知识、用户请求或未来扩展推测能力；不得宣传、暗示、承诺或自行执行 `<SubAgents>` 列表外能力。
- 无匹配 SubAgent 时，Main 只说明当前不支持该请求，不提供搜索平台、学习资料、操作步骤或其他替代建议。问候或用户询问能力时可以主动介绍服务，但只能将当前 SubAgent 的真实职责转换为用户可读表述，不暴露 Agent、Tool、Capability 或路由机制。
- Main 的工具白名单固定为：四个 Plan 工具、`get_current_datetime`、`provide_choices`、`read_customer_file`、`query_memory`、`switch_to_subagent`。这些工具只能用于意图识别、必要上下文收集、计划路由过程和执行 handoff，不构成对外业务能力，也不得用于自行完成领域任务。其余工具对 Main 全部不可见。
- 为精确表达白名单，在现有 `Capability` 枚举增加 `CURRENT_DATETIME` 与 `MEMORY_QUERY`；`get_current_datetime` 使用前者，`query_memory` 使用后者。`get_working_dir` 改由已有 `WORKSPACE_READ` 控制，`query_reference_data` 继续使用 `KNOWLEDGE_QUERY`。Main 移除 `SYSTEM`、`WEB_SEARCH`、`KNOWLEDGE_QUERY`，保留 `PLAN`、`CURRENT_DATETIME`、`INTERACTION`、`EXTERNAL_FILE_READ`、`MEMORY_QUERY`、`ROUTE`。Resume 继续拥有完成其既有职责所需的 capability。
- `04_tools.md` 增加“工具是执行辅助而非业务能力来源”的权威规则；`05_sub_agents.md` 增加穷尽列表、禁止能力推测、无匹配处理和用户可见能力介绍规则；Main `AgentSpec` 的 Role／Mission／Constraints／CommunicationStyle 同步强化相同边界。
- 本次不新增模块、class、service、port、schema 或公开方法；只增加两个 capability 枚举成员并调整现有声明、模板与测试。R8-O 必须以真实 production composition 验证 Main 精确工具集合、Resume 不回退、Main 只见 Resume、权威规则进入最终 prompt，并以真实对话复验问候和无匹配请求。
- 实施同时修复两个由共享 ToolDefinition 引起的名称泄漏：`query_memory` 不再在 Main prompt 中指向不可见的 `query_reference_data`，`read_customer_file` 不再指向不可见的 `workspace_read`；Resume 的非简历请求约束也不再暗示 Main 必然具备其他领域能力。
- 验证结果：49 项 capability／Prompt／bootstrap／Tool 定向测试、完整 244 项自动化测试、`compileall` 与 `git diff --check` 通过。真实 `uv run python main.py` 对话中，问候只介绍简历定制／优化；Java 学习资料请求只说明当前不支持且未提供替代建议；`/exit` 返回 0。决策 205 的 R8-O 阻断解除。

**理由：**

- 只有运行时实际装配的 SubAgent 才能代表当前可交付业务能力；将列表设为穷尽来源，可以避免模型用常识补全尚未实现的 Learning／Interview／Job Search。
- capability 必须与单个工具边界对齐。继续复用 `SYSTEM` 和 `KNOWLEDGE_QUERY` 会让 Main 在获得当前时间／记忆查询的同时被动获得工作目录／公共参考检索，提示词禁止无法替代运行时不可见性。
- 将辅助工具与业务能力分开，可以保留 Main 收集路由上下文所需的最小能力，同时维持决策 72 的纯路由职责。

**曾考虑的替代方案：**

- 只修改问候文案 —— 无法约束后续任意请求，也不解决 Tool 与 SubAgent 的权威性冲突，未采用。
- 保留宽 capability，仅要求模型不要调用多余工具 —— 工具仍会出现在 prompt 中并被视为可用能力，运行时边界也没有收紧，未采用。
- 无匹配项时提供通用替代建议 —— 会继续让 Main 实际执行未装配领域能力，用户明确拒绝。
- 问候时完全不介绍能力 —— 可以降低误报，但牺牲可发现性；用户确认允许基于真实 SubAgent 主动介绍，因此未采用。

---

### 决策 206 —— 空 Memory collection 返回空结果并以显式迁移准备真实测试

**背景：** R8-O 真实 Main 对话调用 `query_memory` 时返回 `{"code": "retrieval_unavailable", "message": "Collection  does not exist"}`。只读诊断确认 production v2 Chroma 已正常加载，`references` collection 有 34 条记录；但 `data/v2/memories/` 尚不存在，manifest 也只有 reference entries，因此没有创建 `memories` collection。当前 `ChromaKnowledgeIndex.replace_source()` 写入时使用 `get_or_create_collection()`，查询时却直接调用 `get_collection()`；合法的“尚无任何 v2 记忆”因此被误判为检索基础设施不可用。仓库同时保留 `data/memories/resume/` 下两份 legacy Markdown 记忆，但根据 R-D6／R6 边界，production v2 不读取或自动迁移旧运行数据。`AUTO_MEMORY_ON_EXIT` 当前保持默认关闭。

**决定：**

- `ChromaKnowledgeIndex.search()` 遇到明确的 Chroma collection-not-found 时返回空 tuple，使 `query_memory` 按正常零命中处理；不预创建空 collection，也不把合法空库状态包装为 `retrieval_unavailable`。
- 只归一化明确的 collection-not-found。Chroma 连接、持久化、查询、embedding、rerank、取消及其他异常继续上抛，由现有 Tool 边界映射为 typed failure，不得用宽泛异常捕获掩盖真实故障。
- 增加 adapter 与 retrieval Tool 回归：覆盖 `memories` collection 不存在时返回空结果；覆盖其他 `get_collection()`／query 异常仍可观察；保持已有 references 查询与结果字段契约不变。
- 后续真实 Memory smoke 前，先对当前 `data/memories/resume/` 下两份 legacy Markdown 文件执行一次性、显式、可审计的测试迁移，将其内容转换为现有 schema 的 v2 `MemoryRecord` JSON，并通过既有 KnowledgeService 建立 `memories` collection／manifest entries。
- 迁移仅是 R8-O 测试准备，不成为 production 启动逻辑或长期兼容层。原 legacy 文件不得修改或删除；v2 Settings、JsonMemoryRepository 和 KnowledgeService 不增加 legacy 路径扫描。迁移前后记录源文件 hash／mtime、输出记录数、v2 repository／manifest／collection 数量与真实 `query_memory` 命中证据。
- 本轮只记录决策和任务状态，不实施 adapter 修复、测试或数据迁移；完成实现与验证前，该问题作为 R8-O 阻断项，仍不得进入 R8-D。

**理由：**

- “collection 不存在”在尚无任何记忆时等价于空集合，而不是服务故障；返回零命中符合检索接口语义，也避免模型错误地告诉用户整个记忆库不可用。
- 将 missing collection 与其他异常精确区分，可以在改善首次使用体验的同时保留真实故障可观察性。
- 使用显式一次性迁移能够复用当前用户已有记忆完成真实命中测试，又不破坏 v2 不读取 legacy runtime data 的架构边界。
- 保留原文件及迁移证据，使测试数据准备可审计、可重跑，并避免把“不迁移”误解为允许删除旧数据。

**曾考虑的替代方案：**

- 启动时无条件创建 `references`／`memories` 空 collection —— 引入不必要的持久化副作用，且不能替代 search 对缺失 collection 的健壮语义，未采用。
- 捕获所有 Chroma 查询异常并返回空结果 —— 会把数据库损坏、连接错误或 embedding／rerank 故障伪装成零命中，明确拒绝。
- 让 production v2 直接扫描 `data/memories/` —— 违反旧运行数据隔离与不迁移决策，也会形成长期双格式兼容负担，明确拒绝。
- 测试时重新手工编造记忆而不迁移现有文件 —— 无法验证当前用户真实 legacy 数据向 v2 schema／索引的准备路径，用户要求先迁移当前记忆文件，因此未采用。

---

### 决策 207 —— targeted Knowledge reload 只比较目标范围

**背景：** 决策 206 的真实 Memory smoke 在两条 legacy 记忆迁移并由启动加载建立 v2 索引后执行 `/ragreload memories`。首次请求因后台启动加载仍持有串行锁而正确返回 `busy=True`；加载完成后的第二次请求却把 manifest 中 6 条 `references/*` entries 全部报告为 deleted。原因是各 source repository 使用 target 过滤 observed sources，但 `KnowledgeService.reload(target)` 仍让完整 manifest 与过滤后的 observed tuple 做 diff，于是所有非目标 entries 都被误判为删除。reference 源文件未受影响，本轮立即执行无 target 的完整 reload，已从静态文件恢复全部 reference manifest entries 与 Chroma chunks。

**决定：**

- `KnowledgeService.reload(target)` 在 target 非空时，同时把 observed sources 和用于 `IndexManifest.diff()` 的 manifest entries 限制为 `target in source_key`；target 为空时继续使用完整 manifest 和全部 observed sources。
- service 边界再次过滤 repository 返回值，不依赖每个 repository 都正确实现 target；实际 mutation 仍作用于完整 manifest，以保留所有非目标 entries。
- 不改变 `ReloadKnowledge`、`ReloadReport`、`KnowledgeSourceRepository.scan(target)`、CLI 命令或其他公开协议；target 继续采用既有 source-key substring 语义。
- 增加跨 collection 回归：target 为 `memories` 时只报告 memory entry unchanged，并确认 reference entry 仍存在且没有进入 deleted。
- 修复后真实 `/ragreload memories` 返回 `deleted=()`、两条 memory source 为 unchanged；只读检查确认 Chroma `memories=36` chunks、`references=34` chunks，manifest 同时保留 2 条 memory 与 6 条 reference source，全部为 `ready`。

**理由：**

- targeted reload 的作用域必须在“观察”和“比较”两侧一致，否则过滤本身会被解释为删除信号。
- 在 service 再次执行 target 过滤，可以把语义固定在应用边界，避免 adapter 实现差异扩大删除范围。
- 保留完整 manifest 作为 mutation owner，可继续复用现有 pending／ready／error 状态机，而无需增加合并 API 或新的 manifest schema。

**曾考虑的替代方案：**

- targeted reload 完全忽略 deleted —— 会导致目标范围内真实删除无法从索引和 manifest 收敛，未采用。
- 为 `memories`／`references` collection 写特殊分支 —— target 当前是通用 source-key substring，不应硬编码 collection 名称，未采用。
- 修改每个 repository 并信任其过滤结果 —— 仍无法阻止未来 adapter 返回非目标 source 后污染 diff；service 必须守住最终作用域。
- 取消 `/ragreload [target]` 参数 —— 会缩减既有 CLI 能力且不是修复根因，未采用。

---

### 决策 208 —— RAG 启动后台预热全部查询模型且不泄漏权重输出

**背景：** 用户复核决策 19 的旧版体验后指出，RAG 应在服务启动时后台自动加载，模型权重加载信息不得泄漏到 CLI。当前 v2 `KnowledgeService.start()` 确实将 startup reload 提交给 application-owned `BackgroundWorker`，但 `SentenceTransformerEmbedder` 与 `CrossEncoderReranker` 都在首次使用时才构造模型。manifest 无变化时 startup reload 不执行 embedding，因此 embedding 权重留到首次查询；reranker 在索引同步中从不使用，必然留到首次有候选结果的查询。v2 只为 encode／predict 设置 `show_progress_bar=False`，没有恢复旧 RAG 在第三方库首次 import 前设置的 Hugging Face／tqdm／transformers 静默边界。因此“后台同步索引”已经成立，但“后台预热完整查询模型且 CLI 静默”没有完整迁移。

**决定：**

- `KnowledgeIndexPort` 增加最小生命周期方法 `prepare(cancellation) -> None`。该方法只加载查询所需模型，不扫描 source、不读写 manifest 或 Chroma collection、不执行查询。
- `ChromaKnowledgeIndex.prepare()` 按 embedding、reranker 顺序调用各自幂等 `prepare()`；模型已加载时不重复构造，并在每次可能阻塞的模型构造前后检查 cancellation。
- `KnowledgeService.reload()` 在现有串行锁和 `LOADING` 状态内先执行 `index.prepare()`，再执行 manifest diff 与 mutation。startup background load、手动 `/ragreload` 和失败后的重试使用同一路径；即使 manifest 全部 unchanged 也必须预热模型。
- 只有预热及 reload 均完成后才能进入 `READY/DEGRADED`。预热异常进入 `ERROR` 并返回 failure；search 继续返回 `retrieval_unavailable`，后续显式 reload 可重新执行 prepare 并恢复。
- 生产 CLI 在 `build_application()` 前固定设置 `HF_HUB_DISABLE_PROGRESS_BARS=1`、`TQDM_DISABLE=1`、`TRANSFORMERS_VERBOSITY=error`，并将 `huggingface_hub`、`transformers`、`sentence_transformers` logger 级别限制为 ERROR。现有 encode／predict `show_progress_bar=False` 保留；不得通过跨线程 `redirect_stdout/redirect_stderr` 静默，因为它们是进程级重定向，可能吞掉并发 CLI 输出。
- 增加回归覆盖：manifest unchanged 仍 prepare；prepare 失败保持不可查询且 reload 可重试；adapter 同时预热两套模型但不访问 collection；CLI 进程设置完整静默环境。
- 验证结果：41 项 Knowledge/Adapter/Retrieval/CLI 定向测试与完整 253 项自动化测试通过，`compileall`、`git diff --check` 通过。真实 `uv run python main.py` 先显示欢迎界面，后台等待 20 秒期间无 Hugging Face、transformers、tqdm 或权重加载输出；随后首次 `query_memory` 约 2 秒完成真实命中且无模型延迟加载输出，`/exit` 返回 0。

**理由：**

- `READY` 必须代表一次真实查询所依赖的全部本地模型和索引均已就绪；只同步 manifest／Chroma 而把模型构造留给首次查询，会造成状态语义失真和不可预测延迟。
- 将 prepare 放入 reload 的既有后台、取消、串行和失败状态边界，可避免再创建线程、全局 singleton 或第二套加载状态机。
- 精确的库级环境与 logger 配置不会接管进程 stdout/stderr，既能恢复旧版静默体验，也不会破坏 Rich／questionary 的并发终端输出。

**曾考虑的替代方案：**

- 只在首次 search 内懒加载 —— 继续阻塞用户请求并可能泄漏权重输出，正是本次需要修复的问题。
- 通过一次伪查询预热 —— 会访问 collection、执行 embedding／query／rerank 并混淆模型生命周期与业务检索，未采用。
- 只预热 embedding，不预热 reranker —— reranker 仍会在首次有候选结果时前台加载，不能满足完整就绪语义。
- 在后台线程使用 `redirect_stdout/redirect_stderr` —— Python 重定向影响整个进程，可能吞掉 CLI 提示或用户交互输出，明确拒绝。

---

### 决策 209 —— 选择交互取消不得提升为 Agent 或 handoff 取消

**背景：** R8-O 真实 Main→Resume 对话中，Resume 调用 `provide_choices`，用户进入“自定义输入”后按 Ctrl+C。`InputController.select()` 正确返回 `None`，但 `CliApp` 将该值映射为全局 `Cancel("Selection cancelled by user")`。Runtime 先把 `provide_choices` 写成 cancelled tool result，再进入 `CANCELLED_NOTICE → CANCELLED`；Orchestrator 看到活动 SubAgent 返回 `Cancelled` 后按既有规则关闭 Main→Resume frame，并把 `switch_to_subagent` 闭合为 `subagent_cancelled`。因此用户只取消一个文本框，却连同 Resume run 和 handoff 一起退出，Main 最终回答“已经取消了切换”。

**决定：**

- 新增 typed Runtime command `CancelSelection(request_id, reason="Selection cancelled by user")`，专门闭合 `WAITING_FOR_SELECTION`；`request_id` 必须匹配当前 pending `provide_choices` call。
- Runtime 收到 `CancelSelection` 后通过既有 `_finish_tool()` 写入 `{"code":"cancelled","message": reason}`，产生 `ToolFinished` 并进入 `MODEL_QUEUED`；不得设置 cancellation token、不得进入 `CANCELLED_NOTICE/CANCELLED`。
- `CliApp` 对 `SelectionRequested` 的有效字符串继续发送 `SubmitSelection`；`InputController.select()` 因选择界面或自定义文本中的 Ctrl+C／EOF 返回 `None` 时发送 `CancelSelection`，不再发送全局 `Cancel`。
- Orchestrator 无需增加例外：局部取消产生 `ToolFinished`，自然保留当前 active SubAgent 与 handoff stack；真正的 `Cancel` 仍产生 `Cancelled` 并按既有 `FailHandoff(subagent_cancelled)` 路径安全关闭原 call id。
- 不修改 `InputController.select() -> str | None`、`SelectionRequested`、`ToolInteraction`、SessionSnapshot schema 或 `provide_choices` ToolDefinition；不把空字符串解释为取消。
- 增加三层回归：Runtime 验证 cancelled tool result 后继续完成；CliApp 验证 `None → CancelSelection → Continue`；Orchestrator 验证局部取消保持 Resume active 和 handoff frame，同时保留真正 `Cancel` 退出 handoff 的既有测试。
- 验证结果：48 项 Runtime/CLI/Orchestrator/Session 定向测试与完整 256 项自动化测试通过，`compileall`、`git diff --check` 通过。真实 questionary 进入自定义输入后发送 Ctrl+C，终端输出 `Cancelled by user` 且函数返回 `SELECTION_RESULT None`；应用回归确认该 `None` 只映射为 `CancelSelection`。

**理由：**

- 取消一次交互和取消整个 Agent run 是不同作用域；只有后者才应触发 handoff unwind。
- 独立 command 保留 request-id 校验、typed 状态转换和明确审计语义，也避免 Orchestrator 猜测某个 `Cancelled` 是否“其实只是 UI 取消”。
- 复用 `_finish_tool()` 可以让当前 Agent看见用户取消并自行决定重问、换方案或主动返回 Main，同时保持 conversation call closure 完整。

**曾考虑的替代方案：**

- 将 `None` 作为 `SubmitSelection` 的值 —— 会把取消伪装成合法选择，且破坏 `value: str` 契约，未采用。
- 将空字符串作为选择结果 —— 无法区分用户确实输入空白和取消，也没有 typed cancelled code，未采用。
- 修改 Orchestrator 忽略所有 SubAgent `Cancelled` —— 会遗留真正取消、失败或 Esc 中断的活动 handoff，破坏原 call-id 闭合，明确拒绝。
- 在 Runtime 的全局 `_cancel()` 中针对 `WAITING_FOR_SELECTION` 特判并继续 —— 会让真正的 Esc run cancellation 在选择阶段也无法退出 SubAgent，作用域仍然混淆，未采用。

---

### 决策 210 —— 新增 Resume-only PDF 合并工具并纳入 Artifact aggregate

**背景：** 用户提供 legacy `merge_pdfs(first, second, output)` 实现，要求新增给 Resume Agent 使用并适配当前 v2 设计。legacy handler 直接 import `pypdf`、读取全局 `config.working_dir`、调用 `_validate_path()` 并以 `open(..., "wb")` 写文件；这会绕过 v2 的显式依赖、Workspace confinement、Artifact operation 和 typed outcome 边界。当前 production Catalog 在历史 R3/R7/R8-E 阶段固定为 25 个工具，本次是用户明确授权的新能力，不是迁移遗漏。

**决定：**

- 新增 Resume-only `merge_pdfs` ToolDefinition，参数为必填字符串 `first/second/output`，均是工作区相对路径且 `.pdf` 后缀可省略；按 first → second 拼接全部页面，输出 `{output, first, second, total_pages}`。
- 工具要求 `RESUME_ARTIFACT + WORKSPACE_READ + WORKSPACE_WRITE`，采用现有 `ConfirmationMode.ALWAYS`，因此 Main capability 不可见且调用前进入当前统一审批策略。当前 ToolCatalog 验收值从历史 25 调整为 26。
- 新增 immutable `PdfMergeResult`，并在既有 `ResumeArtifactPort`、`ResumeArtifactBackend` 和 `ArtifactService` 上增加同名窄方法；不新增文件、模块、service、capability、CLI 命令或 ToolOutcome 字段。
- `LocalResumeArtifacts` 是唯一 import `pypdf` 和执行 PDF 二进制 I/O 的层。所有路径先经 `WorkspacePort.resolve()` 约束；两个源必须存在且不同，输出不得等于任一源。输出先写同目录临时文件，再用 `os.replace()` 原子提交，失败清理临时文件。
- 不扩展 `WorkspacePort.read()` 的文本契约，也不增加通用 binary read/write API。ArtifactService 使用既有 `content_hash()` 获取两个源 PDF 的原始字节 hash，形成 deterministic `MERGE_PDFS` operation key。
- 成功输出作为 PDF Artifact 保存 hash、version 和新增的可选 `page_count`；repository 强制 committed merge 只能包含一个路径匹配、带非负 page count 的 PDF Artifact且不能包含 build attempt。相同 committed operation replay 直接返回持久化结果，不重复写文件；metadata commit 失败继续使用 `ArtifactPartialFailure` 报告已变化的输出路径。
- `pyproject.toml` 显式增加 `pypdf>=6.0.0`，项目镜像锁定 `pypdf 6.14.2`。R3/R7 的 25-tool 历史证据保留，不倒写为 26。
- 验证结果：58 项 Resume Tool／Artifact／Catalog／bootstrap 定向测试和完整 261 项自动化测试通过；真实适配器 smoke 创建 1 页与 2 页不同尺寸 PDF，合并结果为 3 页且尺寸顺序证明 first → second。`compileall`、`git diff --check` 与 v2 import boundary 通过。

**理由：**

- PDF 合并是 Resume 产物能力，应复用现有 artifact transaction 与 provenance，而不是让 Tool handler 直接操作文件系统。
- `WorkspacePort.read()` 明确是文本读取；PDF 所需二进制能力已经可由受限路径 adapter 和 `content_hash()` 满足，没有理由扩张公共 Workspace API。
- 原子替换避免无效／损坏输入或写入异常留下半份输出；禁止输出覆盖源文件可避免 pypdf 惰性读取与目标截断造成源简历损坏。
- 持久化 page count 让 committed replay 保持与首次调用相同的结构化输出，不需要再次解析或重写 PDF。

**曾考虑的替代方案：**

- 直接迁移 legacy handler —— 会重新引入全局 config、handler 文件 I/O 和未记录副作用，拒绝。
- 给 WorkspacePort 增加通用二进制 read/write —— 扩大所有工具的文件访问面，且当前只有 Resume artifact adapter 需要，未采用。
- 合并成功但不进入 ArtifactService —— 会使 PDF 产物缺少 operation、hash、version 和 partial-failure 语义，与 R7 已确认边界冲突。
- committed replay 时重新执行合并或重新读取输出计算页数 —— 前者产生重复副作用，后者需要增加额外 backend 查询契约；持久化 `page_count` 更窄且确定。

---

### 决策 211 —— uv 唯一默认镜像切换为 TUNA 并拆分依赖添加与同步

**背景：** 增加 `pypdf` 时，SJTUG 对大量 wheel 元数据返回不可用 304 或不支持 range request，普通 `uv lock` 用时 5 分 42 秒；临时使用官方 PyPI 虽在约 11 秒完成，却会把整个 lock registry 改成官方源，不符合项目镜像策略。用户确认采用清华 TUNA，并要求继续保留 Windows、Ubuntu/Linux 的跨平台解析能力；此前出现的用户级 `sdists-v9\.git: Access denied` 是独立问题，本次不修改 cache。

**决定：**

- `pyproject.toml` 只保留一个 `[[tool.uv.index]]`：`name = "tuna"`、`url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"`、`default = true`。
- 不添加 `[tool.uv].environments`，不限制为 Windows；继续生成同时覆盖 Windows 与 Ubuntu/Linux wheel 的 universal lock。
- 不使用官方 PyPI 作为默认源，不配置多个普通 PyPI 镜像，不引入 PyTorch CPU 专用源。
- 普通锁定／部署流程为 `uv lock` → `uv sync --locked`；不得使用 `--upgrade`。执行 `uv lock` 或 `uv add` 前先检查是否已有同类 uv 进程，禁止并发锁定，并允许解析阶段长时间无输出。
- 后续新增依赖固定拆分为 `uv add <package> --no-sync` → `uv sync`。前者慢表示依赖解析或镜像元数据问题，后者慢表示 wheel 下载或安装问题。
- 本次普通 `uv lock` 约 9 秒完成，`uv sync --locked` 约 2 秒完成。同步清理了临时 Jupyter 环境留下的 21 个非项目包，不改变 lock 中项目依赖。
- lock 前后均包含 133 个 package，name/version 集合完全一致；`pypdf 6.14.2` 保留。所有 registry 与 artifact URL 已切换为 TUNA，无 `pypi.org`、`sjtug` 或 `mirror.sjtu` 残留。
- TUNA 同步后重新通过 58 项 PDF 合并相关定向测试、完整 261 项自动化测试、`compileall`、`git diff --check` 与 v2 import boundary。

**理由：**

- 单一默认镜像让解析和安装来源明确，避免多个普通索引产生优先级、供应链和复现歧义。
- 不增加 environments 过滤可继续锁定项目已支持的 Windows 与 Ubuntu/Linux 平台，而不是用本机 Windows 状态缩窄部署范围。
- 将解析与同步拆开后，耗时可准确归因到 metadata resolver 或 wheel 下载／安装阶段，避免把两个问题混为一次 `uv add`。
- 普通 `uv lock` 在不升级依赖的情况下完成 registry 重写，包版本集合可直接与切换前比较。

**曾考虑的替代方案：**

- 继续使用 SJTUG 并单纯延长等待 —— 可以完成但 metadata 行为持续造成数分钟延迟，不再采用。
- 使用官方 PyPI —— 临时验证较快，但违反用户确认的国内默认镜像约束，且会把 lock 全量切换到 `pypi.org`，拒绝。
- 配置 TUNA 与其他普通镜像并存 —— 增加来源优先级与复现复杂度，未采用。
- 通过 `[tool.uv].environments` 只锁 Windows 或引入 PyTorch CPU 专源 —— 会破坏 Ubuntu/Linux universal lock 或扩张本次范围，明确拒绝。
- 同时处理 `UV_CACHE_DIR` —— cache 权限错误与镜像是独立问题；只有 TUNA 后再次出现 Access denied 时才另立任务处理。

---

### 决策 212 —— finish thinking 必须是非空用户可见摘要

**背景：** R8-O 真实 Main 对话返回了结构合法但 `thinking=""` 的 finish JSON。现有决策 172、OutputFormat、Parser 和回归测试明确允许空字符串，因此回复不会产生 warning；Renderer 又只展示 truthy thinking，最终用户看不到“思考摘要”。这与 thinking 是模型生成、供用户查看的摘要这一产品语义不一致。

**决定：**

- `finish.thinking` 必须是非空且不能只包含空白的字符串；`""`、空格、制表符或换行组成的值均不合法。
- `ModelReplyParser` 对空或纯空白 finish thinking 抛出 `ModelReplyParseError`，由 AgentRuntime 注入具体错误与 canonical OutputFormat，并沿用每回合最多一次模型 repair。
- Runtime 不自动生成、补齐或替换 thinking，避免伪造模型未提供的摘要。
- `tool_call.thinking` 保持既有可选契约；省略、空字符串或合法字符串仍可接受。
- 本决策仅取代决策 172 中“finish thinking 允许空字符串”的部分，其余格式修复、日志和重试边界不变。
- Parser／Runtime／Prompt 定向回归、完整 263 项自动化测试、`compileall` 与 `git diff --check` 均通过。

**理由：**

- 必填但允许空值只满足结构，不满足用户可见摘要的业务语义，并会被 Renderer 自然跳过。
- 将语义约束放在 Parser 可保证首次回复与 repair 回复使用同一规则，且不会把无效值写入会话记录。
- 非空校验只针对 finish，不会强迫每次工具调用都生成无价值摘要。

**曾考虑的替代方案：**

- Renderer 为 `""` 显示空面板 —— 没有用户价值，且掩盖模型未履行输出契约。
- Runtime 为 `""` 自动生成默认摘要 —— 不是模型真实输出，违反 thinking 数据来源边界。
- 仅修改 prompt、不修改 Parser —— 模型仍可能输出空值并静默通过，无法形成可靠契约。

---

### 决策 213 —— system prompt 顺序只由模板文件名决定

**背景：** 决策 201 为降低模型复制 InputFormat envelope 的概率，在 PromptRenderer 中增加了特殊重排：先按文件名排序，再把 `07_output_format.md` 强制移动到所有模板之后。真实最终顺序因此变成 `01～06 → 08_input_format → 09_reserved → 07_output_format`，目录文件名不再能够解释 system prompt，测试还把这一隐藏规则固定下来。

**决定：**

- PromptRenderer 只执行 `sorted(general_agent/*.md)` 并按该顺序拼接，不得在代码中为任何模板设置位置特例。
- 将 `08_input_format.md` 重命名为 `07_input_format.md`，将 `07_output_format.md` 重命名为 `08_output_format.md`；`09_reserved.md` 保持不变。
- 最终静态区块顺序为 `01_role → 02_mission → 03_constraint → 04_tools → 05_sub_agents → 06_communtion_style → 07_input_format → 08_output_format → 09_reserved`。
- v2 `render_output_format()` 从目录中发现且要求唯一的 `*_output_format.md`，不绑定数字前缀；legacy rollback BaseAgent 同步读取当前 `08_output_format.md`，格式修复契约不变。
- 决策 201 中“OutputFormat 固定为 system prompt 最后一节”的排序策略被本决策取代；决策 201 的最小业务字段、内部字段生成与解析校验仍然有效。
- PromptRenderer／Runtime／bootstrap 定向 47 项和完整 264 项自动化测试通过；production 模板顺序回归与 legacy OutputFormat 读取 smoke 通过。

**理由：**

- 数字文件名前缀应当是模板顺序的唯一事实来源，目录检查、运行时行为和测试预期必须一致。
- 删除二次重排可避免未来新增模板时产生无法从文件名发现的顺序变化。
- InputFormat 先于 OutputFormat，模型先理解收到的历史结构，再读取自身输出契约；Reserved 继续作为最终保留约束。

**曾考虑的替代方案：**

- 保留文件名并继续在代码中移动 OutputFormat —— 顺序规则隐藏在实现中，明确拒绝。
- 只修改测试期待但保留重排 —— 不能改变真实运行行为，拒绝。
- 将 OutputFormat 改为 `99_output_format.md` 继续保持最后 —— 用户明确要求调整 07/08，且 `09_reserved.md` 应继续承担最终保留约束，未采用。

---

### 决策 214 —— 工具调用未知参数沿用 v1 静默忽略语义

**背景：** R8-O 真实交互中，`provide_choices` 的工具参数除了 `question` 和 `choices` 外还出现了 `thinking`，v2 `ToolExecutor` 将该字段判定为 `unexpected_argument`，导致工具没有进入选择交互。对照 v1 `BaseAgent._execute_tool()` 可知，旧实现会按 handler 签名过滤未知参数，仅对过滤后的参数执行必填校验并调用 handler；因此这是 v2 的兼容性回归。

**决定：**

- `ToolExecutor` 在参数校验前只保留 `ToolSchema.properties` 中声明的字段。
- 未知字段（包括误混入 `event_payload` 的 `thinking`）静默忽略，不返回 `unexpected_argument`，也不传入工具 handler。
- 过滤后的已知字段继续执行必填参数和类型校验；未知工具、能力限制、审批、取消及 handler 异常语义不变。
- 顶层 `tool_call.thinking` 仍作为可选模型元数据保留；即使模型错误地将它嵌入 `event_payload`，工具边界也按 v1 兼容规则安全处理。
- 增加 ToolExecutor 级和 Runtime 级回归，分别覆盖未知参数被过滤及 `provide_choices` 正常产生 `SelectionRequested`。

**理由：**

- 保持 v1 已验证的模型容错行为，避免模型把回复元数据混入工具载荷时中断用户流程。
- 将兼容处理放在统一工具执行边界，所有工具一致生效，不需要为 `thinking` 或单个工具增加特判。
- 仍对声明的业务参数严格校验，未知字段不会扩大 handler 的输入面。

**曾考虑的替代方案：**

- 只在 Parser 中特判并删除 `thinking` —— 无法覆盖其他未知字段，且不能保持 v1 的通用兼容语义，未采用。
- 为 `provide_choices` 单独增加 `thinking` schema 字段 —— 会把模型元数据错误地伪装成业务参数，扩大工具契约，未采用。
- 继续返回 `unexpected_argument` 并要求模型 repair —— 与 v1 行为不一致，会让可安全忽略的附加字段阻断交互，未采用。

**验证：**

- `git diff --check` 通过。

- 已增加 `tests/get_me_in/test_tool_catalog.py` 和 `tests/get_me_in/test_runtime.py` 回归覆盖；本次 checkpoint 未重新执行完整自动化测试。

---

### 决策 215 —— 模型调用上限默认调整为 100 且 Main／Resume 计数独立

**背景：** R8-O 真实 Main→Resume 交互中出现 `Runtime exceeded 12 model calls`。当前配置参数是 `AGENT_MAX_MODEL_CALLS`，默认值为 12；该限制统计模型 completion 次数，包含格式修复调用，不是工具 handler 执行次数。检查发现 Main 与 Resume 使用同一个配置值，但各自拥有独立的 `AgentRuntime`、`CancellationToken` 和 `AgentSessionState.model_calls`。

**决定：**

- 将 `AGENT_MAX_MODEL_CALLS` 的默认值从 12 调整为 100，并同步更新 `Settings`、`AgentRuntime` 默认值和 `.env.example`。
- 保留显式环境变量覆盖能力；如果用户设置 `AGENT_MAX_MODEL_CALLS`，仍以该值为准。
- Main 与 Resume 继续共享同一个上限配置，但不共享调用计数；计数分别存储在 `SessionState.agents[AgentKey.MAIN].model_calls` 与 `SessionState.agents[AgentKey.RESUME].model_calls`。
- 新的 `UserMessage` 会为当前 Agent 开始新的 run 计数；Main 在 handoff 返回后继续自己的 run，Resume 在被启动时使用自己的 run 计数。
- 工具执行本身不增加 `model_calls`；每次模型 completion（包括 repair）增加一次。
- 增加 Settings 默认值回归，以及真实 Main→Resume→Main 的计数隔离回归。

**理由：**

- 100 次模型调用足以覆盖真实简历收集、工具调用、审批、handoff 和必要 repair 的组合流程，避免默认 12 次过早终止。
- 保持共享配置可以维持统一运行策略，同时用 AgentSessionState 隔离计数，避免 SubAgent 消耗或污染 Main 的预算。
- 继续保留显式环境变量覆盖，方便真实 smoke 或资源受限部署临时收紧上限。

**曾考虑的替代方案：**

- 只修改 `.env.example` —— 无法覆盖未设置环境变量时的 Settings fallback 和直接构造 Runtime，未采用。
- Main 与 Resume 共享一个全局总预算 —— 会让 handoff 顺序影响另一 Agent 的可用额度，违反当前 Session agent-local state 边界，未采用。
- 为 Main 与 Resume 增加两套独立环境变量 —— 当前没有差异化预算需求，会扩大配置面，未采用。

**验证：**

- `git diff --check` 通过。
- 新增 Settings 默认值断言；Main→Resume→Main 回归确认 Main 使用 2 次模型调用、Resume 使用 1 次且两个状态对象独立。

---

### 决策 216 —— 模型回复解析失败暂停当前 SubAgent，由用户继续

**背景：** R8-O 真实 Resume 对话中，模型第一次回复未满足 `finish.thinking` 契约，Runtime 注入一次 repair 后，第二次回复仍然无法解析。此前 Runtime 返回 `Failed("invalid_model_reply", ...)`，Orchestrator 将所有活动 SubAgent 的 `Failed` 都包装为 `subagent_failed` 并闭合 handoff，导致解析错误被误判为 SubAgent 业务失败。用户明确要求解析失败停在断点，由用户输入继续当前会话。

**决定：**

- 最终一次模型 repair 仍失败时，Runtime 返回独立的 `Paused(code="invalid_model_reply", ...)` 事件，并将当前 Agent 状态置为 `RuntimePhase.WAITING_FOR_USER`；解析失败不再使用 `Failed`。
- Orchestrator 对 `Paused` 不执行 `FailHandoff`，保留当前 active SubAgent、原 handoff frame、Main 的等待状态和双方会话历史；CLI 将该事件视为当前回合终点并重新读取用户输入。
- `UserMessage` 在 `WAITING_FOR_USER` 阶段合法，下一条用户消息继续发送给原 active SubAgent，保留当前 Session/handoff 上下文并重新开始该 Agent 的模型 run。
- provider failure、timeout、取消和其他运行／业务失败仍使用 `Failed`；活动 handoff 下这些失败才闭合原始 call 并返回 Main。
- `WAITING_FOR_USER` 纳入 session snapshot codec 与 restore safe phase；Renderer 明确提示当前 Agent 已暂停以及下一条用户消息的继续语义。
- `invalid_model_reply` 的完整原始模型回复继续以 warning 写入 `data/logs/app.log`，不再截断为 preview。

**理由：**

- 模型输出不符合协议是当前回合的可恢复格式问题，不足以证明 SubAgent 业务执行失败；保留 handoff 才能让用户补充消息后继续原任务。
- 通过显式 `Paused` 与 `WAITING_FOR_USER` 区分暂停和失败，避免 Orchestrator 依赖错误码特判，也避免把恢复路径混入 fatal failure closure。
- 保留一次 repair 机制，但把第二次失败后的控制权交还用户，既不自动重试模型，也不丢弃当前 Agent 上下文。

**曾考虑的替代方案：**

- 继续把 `invalid_model_reply` 当作 `Failed` 并回 Main —— 会把格式问题错误升级为 SubAgent 失败，拒绝。
- 解析失败后自动再次调用当前 SubAgent —— 会绕过用户控制并可能消耗模型调用预算，拒绝。
- 只在 Orchestrator 对 `Failed.code` 做 `invalid_model_reply` 特判 —— 状态仍会显示为 failed，持久化语义不准确，未采用。

**验证：**

- Runtime、Orchestrator、CLI、Renderer、Session codec 相关 68 项测试通过。
- production bootstrap 相关 20 项测试通过；`git diff --check` 通过。
- 真实 CLI／完整 R8-O smoke 尚未完成，仍需用户后续观察。

---

### 决策 217 —— SessionSnapshot 持久化 agent turn_id 并兼容旧 handoff 快照

**背景：** R8-O 真实 Resume 会话执行 `/restore` 时，合法的 handoff 快照报错 `Handoff frame must match the source turn`。检查发现 `SessionSnapshotCodec` 保存 handoff frame 的 `turn_id`，却没有保存 `AgentSessionState.turn_id`；恢复后 source agent 的 turn_id 默认为空字符串，严格一致性校验因此误判快照损坏。此前已经生成的 schema v2 快照同样缺少该字段。

**决定：**

- `SessionSnapshotCodec` 在每个 agent payload 中持久化并恢复 `turn_id`。
- 对缺少 agent `turn_id` 的旧 schema v2 handoff 快照，仅在 source state 为空且 handoff frame 存在时使用 frame 的 source turn 补齐；补齐后仍执行完整 session 校验。
- 如果快照已经包含 `turn_id` 但与 handoff frame 不一致，继续拒绝恢复，不放宽真实一致性约束。
- 增加 agent turn_id round-trip 测试和缺字段旧 handoff 快照兼容测试。

**理由：**

- `turn_id` 是 handoff source 状态与 frame 的必要关联字段，必须和 pending call、phase 一样进入快照。
- 只对可确定的历史缺字段情况做最小兼容修复，避免把真实损坏或篡改的 turn_id 静默接受。
- `/restore` 仍只恢复稳定状态，不重放已完成的工具副作用。

**曾考虑的替代方案：**

- 删除 handoff frame 的 turn 校验 —— 会失去 source turn 一致性保护，拒绝。
- 所有恢复快照都以 frame turn 覆盖 source turn —— 会掩盖包含错误字段的新快照，拒绝。
- 提升 schema version 并强制用户删除旧存档 —— 会使现有合法 session 不可恢复，未采用。

**验证：**

- Session codec、SessionService、bootstrap 定向回归共 31 项测试通过。
- `git diff --check` 通过。

---

### 决策 218 —— MemoryExtractor 使用数组契约并隔离后台异常详情

**背景：** R8-O 真实 `/build-memory` 失败时，v2 `MemoryExtractor` 按数组遍历模型结果并读取 `category/content`，但生产加载的旧记忆 prompt 要求模型返回 `facts/preferences` 对象；同时 `MemoryService` 的 `logger.exception` 通过 ERROR stderr handler 将完整 traceback 输出到前台，暴露内部实现细节。

**决定：**

- 将 `data/prompts/memory/builder.md` 改为适配当前 `MemoryExtractor` 的输入输出契约：输入为拼接后的对话文本，输出为只包含 `category`（`fact`／`preference`）和 `content` 的 JSON 数组。
- Memory 构建异常继续使用 `logger.exception` 保存完整 traceback，但标记为仅文件日志；前台和后台 job result 只保留 `Error: memory build failed; details were written to app.log`，真实终端中的 ERROR 提示显示为红色。
- 保留既有 Memory partial failure 的 typed report 语义，不改变后台构建仍立即返回 receipt 的异步边界。

**理由：**

- Prompt、模型 JSON mode 和 extractor parser 必须共享同一业务 schema，避免合法的 v1 对象被 v2 当作数组遍历而触发 `TypeError`。
- 用户界面不应显示后台实现 traceback，但日志仍需保留完整证据以便诊断。

**曾考虑的替代方案：**

- 在 `MemoryExtractor` 中兼容旧 `facts/preferences` 对象 —— 会继续保留 prompt 与实现不一致的双契约，未采用。
- 删除异常 traceback —— 会损失排查所需的完整日志证据，拒绝。

**验证：**

- Memory、logging、CLI 定向回归 17 项通过。
- 全量 unittest 275 项通过，`git diff --check` 通过。

---

### 决策 219 —— finish thinking 恢复为可选摘要

**背景：** 决策 212 将 `finish.thinking` 收紧为非空、非纯空白字符串，但真实运行中并非每次最终回复都需要向用户展示思考摘要。该强制要求会把本可正常完成的 finish 回复送入额外 repair，增加模型调用和延迟。用户明确要求推翻该约束。

**决定：**

- `finish` 可以省略 `thinking` 字段。
- `finish.thinking` 可以省略、使用 `null`、空字符串或空白字符串；这些情况均表示没有摘要并允许正常完成。
- `finish.thinking` 如果提供其他非空值，必须是字符串；`null` 不再视为类型错误。
- `finish.message` 仍必须是非空字符串；finish 的 `tool` 和 `event_payload` 约束不变；tool_call 的 thinking 规则不变。
- 决策 219 取代决策 212 对 finish thinking 非空的要求，并同步更新 OutputFormat、Parser、Runtime 回归和 R8 文档契约。

**理由：**

- 思考摘要是可选的展示信息，不应阻断业务上已经完整的最终回复。
- 保留非空非字符串值的类型校验，可以避免把任意结构静默写入会话消息；`null` 明确作为无摘要值处理。
- 取消不必要的 repair 调用，降低真实对话延迟和模型调用次数。

**曾考虑的替代方案：**

- 继续要求模型始终生成非空摘要 —— 会把可选展示字段错误升级为必需业务字段，拒绝。
- 缺少 thinking 时由 Runtime 自动补充默认摘要 —— 会制造并非模型生成的展示内容，拒绝。
- 拒绝 `thinking: null` —— 会把明确表示“无摘要”的值错误升级为格式错误，未采用。

**验证：**

- Parser 回归覆盖 finish 缺少 thinking、`null`、空字符串、空白字符串和非字符串类型。
- Runtime 回归确认无摘要 finish 不触发 repair；全量 unittest 276 项通过，`git diff --check` 通过。

---

### 决策 220 —— RAG startup 提交不得持有 KnowledgeService 锁

**背景：** R8-O 真实检索持续返回 `retrieval_unavailable`，日志显示 startup background job 已开始并结束，但 KnowledgeService 仍停留在 `LOADING`。检查发现 `KnowledgeService.start()` 在持有 `_lock` 时调用 `BackgroundWorker.submit()`；后台线程可能立即执行 `reload()`，非阻塞获取同一把锁失败并返回 `ReloadReport(busy=True)`。BackgroundWorker 只检查 `error/failures`，因此把该结果记录为成功，而 service 状态没有从 `LOADING` 收敛。

**决定：**

- `start()` 只在锁内完成 `IDLE → LOADING` 状态转换，释放锁后再提交 startup reload；提交失败时重新取得锁并将状态置为 `ERROR`。
- 保持既有单 worker、非阻塞串行边界和 `READY/DEGRADED/ERROR` 状态语义，不新增线程、公开 API 或第二套加载状态机。
- 为 startup reload、index prepare、embedding／reranker 模型准备、source scan、reload 完成／失败增加阶段日志；异常完整 traceback 使用 file-only 记录写入 `app.log`，前台继续只显示简短的 `retrieval_unavailable` 错误。
- 增加 worker 立即执行 startup reload 的竞态回归，确保服务不会因提交时序永久停在 `LOADING`。

**理由：**

- 释放提交前的服务锁消除后台线程与启动调用之间的确定性竞态，同时保留所有 reload 操作的串行保护。
- 阶段日志可以区分模型构造、索引准备、manifest 扫描和 mutation 的耗时或失败位置，避免把状态症状误判为检索根因。
- 详细诊断必须可追溯，但不应把内部 stacktrace 泄漏到 CLI 前台。

**曾考虑的替代方案：**

- 让 startup `reload()` 在拿不到锁时等待 —— 会改变现有非阻塞串行契约并可能阻塞检索／关闭路径，未采用。
- 只增加 `retrieval_unavailable` 日志 —— 只能记录结果症状，无法修复 `LOADING` 永久停留，未采用。
- 增加独立 RAG watchdog 或第二个 worker —— 会扩大生命周期与并发边界，当前没有必要，未采用。

**验证：**

- 新增立即执行 worker 的 startup lock 回归测试；Knowledge／adapter／retrieval 定向测试 35 项通过。
- 全量 unittest 278 项通过，`git diff --check` 通过。

---

### 决策 221 —— 审批拒绝暂停当前 Agent，下一条用户消息再继续

**背景：** R8-O 审批拒绝场景中，Runtime 将 `Reject` 返回为 `Cancelled`。当拒绝发生在活动 Resume 子 Agent 时，Orchestrator 按取消语义关闭 handoff，向 Main 写入拒绝结果并返回 `ToolFinished`；CLI 随后自动发送 `Continue()`，导致 Main 在没有下一条用户消息的情况下再次调用 LLM。v1 的行为是拒绝后结束当前 agent loop，将拒绝结果保留在历史中，等待下一条用户消息后再一起发送给当前 Agent 的 LLM。

**决定：**

- `Reject` 将待处理 tool call 的拒绝结果写入 `ToolResultRecord`，把当前 Agent 状态置为 `WAITING_FOR_USER`，并返回既有 `Paused("approval_rejected", reason)` 事件。
- 审批拒绝不再使用 `Cancelled` 语义，不触发 Orchestrator 的 handoff closure，也不自动调度下一次模型调用。
- 下一条 `UserMessage` 可从 `WAITING_FOR_USER` 开始新的模型 run；ConversationCodec 按历史顺序把拒绝的 `tool_call_result` 和新的用户消息一起编码给当前 Agent。
- 不新增 RuntimeEvent 或公开 API；真实取消、provider failure 和其他 terminal failure 的既有 `Cancelled/Failed` handoff 语义保持不变。

**理由：**

- 审批拒绝表示用户结束当前工具尝试并准备提供后续指示，不等同于取消整个子 Agent 会话。
- 保留活动 handoff 可以让用户继续当前 Resume 任务，也避免 Main 在缺少新用户意图时自行推理下一步。
- 复用 `Paused` 和 `WAITING_FOR_USER` 可保持既有解析失败暂停、CLI 输入边界和 session snapshot 安全状态。

**曾考虑的替代方案：**

- 继续返回 `Cancelled`，但在 CLI 中特殊阻止 `Continue()` —— 只能修复一个前端入口，Orchestrator 仍会关闭活动 handoff，未采用。
- 返回 `ToolFinished` 并让模型自行决定是否继续 —— 会违反 v1 的拒绝后停顿语义，未采用。
- 新增独立 `ApprovalRejected` 事件 —— 当前 `Paused` 已能表达等待用户继续，增加事件会扩大公开协议，未采用。

**验证：**

- Runtime、CLI、Orchestrator 和真实 bootstrap 的审批拒绝定向回归 65 项通过；覆盖 Resume 子 Agent 拒绝后 handoff 保留、无额外 LLM 调用及下一条用户消息继续。
- 全量 unittest 279 项通过，`git diff --check` 通过。

---

### 决策 222 —— `/exit_sub` 默认总结，false 允许直接退出

**背景：** 当前 `/exit_sub` 直接通过 `FailHandoff` 关闭原始 handoff，没有让 SubAgent 先整理上下文；同时用户需要在不调用 LLM 的情况下主动退出。已有 `switch_to_mainagent(summary)` 工具可以承载正常的 SubAgent 总结返回。

**决定：**

- `ExitSubAgent` 增加 `summarize: bool = True` 参数；`/exit_sub` 和 `/exit_sub true` 向当前 SubAgent 发送退出总结指令，要求其整理执行内容并调用 `switch_to_mainagent(summary)`。
- `/exit_sub false` 直接闭合原始 handoff，向 Main 写入 `code: "subagent_exited"`、`message: "用户主动退出"` 的结果，不伪造 summary。
- CLI 对参数仅接受 `true`／`false`，默认 `true`；帮助文本必须说明默认行为和直接退出模式。

**理由：**

- 默认保留 SubAgent 总结，可以让 Main 获得真实的执行结论和后续事项。
- `false` 为用户提供明确的快速退出路径，且消息语义不再误称为“SubAgent 未完成退出”。
- 复用既有 `switch_to_mainagent` 和 handoff closure，避免新增第二套总结协议。

**曾考虑的替代方案：**

- `/exit_sub` 始终直接退出并生成固定 summary —— 会丢失 SubAgent 的真实上下文，未采用。
- 新增独立的总结事件 —— 会扩大 Runtime 公共协议，已有 handoff 工具足够，未采用。

**验证：**

- CLI 回归覆盖默认、`true`、`false` 和非法参数；Orchestrator 回归确认总结路径先调用 SubAgent，再由 `switch_to_mainagent` 闭合原始 call。

---

### 决策 223 —— Esc 取消当前 SubAgent run 但保留 handoff

**背景：** WorkerRunner 检测 Esc 后调用 `Application.request_cancel()`；活动 Resume 返回 `Cancelled` 时，Orchestrator 原先按全局取消语义执行 `FailHandoff`，导致用户只是想停止当前模型／工具执行，却被自动退回 Main。

**决定：**

- 活动 handoff 下收到 SubAgent 的 `Cancelled` 时，保留当前 active SubAgent、handoff frame 和 Main 的 `WAITING_FOR_HANDOFF` 状态，不自动闭合源 tool call。
- CLI 仍将 `Cancelled` 作为本轮终点并恢复用户输入；下一条 `UserMessage` 继续发送给原 SubAgent。
- `Failed` 仍按业务／provider 失败路径执行 `FailHandoff` 并退回 Main；选择交互继续使用独立的 `CancelSelection` 语义。

**理由：**

- Esc 的用户意图是取消当前阻塞执行，不是放弃当前 SubAgent 任务。
- 保留 handoff 可以让用户在中断后补充指令继续 Resume，而不会让 Main 在没有新用户意图时自行接管。
- 将取消与失败分开处理，维持失败 call closure，同时避免扩大 RuntimeEvent 或新增取消事件。

**曾考虑的替代方案：**

- 继续由 Orchestrator 自动关闭 handoff —— 会复现 Esc 误退回 Main 的问题，未采用。
- 在 CLI 中拦截所有 `Cancelled` —— 会让编排层无法保持 session/handoff 一致性，未采用。
- 将 Esc 映射为 `Paused` —— 会混淆用户主动取消与模型解析失败暂停，未采用。

**验证：**

- Orchestrator 回归确认 Esc 后 active agent 仍为 Resume、handoff frame 保留、Main 仍等待 handoff，下一条用户消息继续进入 Resume。
- 定向测试 59 项通过，全量 unittest 283 项通过，`git diff --check` 通过。

---

### 决策 224 —— provide_choices 取消后暂停当前 Agent

**背景：** 决策 209 为 `provide_choices` 的 Ctrl+C／EOF 增加了 typed `CancelSelection`，但实现将取消结果写入历史后进入 `MODEL_QUEUED`，CLI 自动发送 `Continue()`，导致模型在用户取消选择后立即再次调用 LLM。用户要求取消工具后先把控制权交还 CLI，下一条用户消息再继续当前会话。

**决定：**

- `CancelSelection` 仍校验当前 `request_id` 并写入 `ToolResultRecord`，结果为 `{"code":"cancelled","message": reason}`。
- 当前 Agent 状态改为 `WAITING_FOR_USER`，返回 `Paused("selection_cancelled", reason)`；不设置全局 cancellation token，不进入 `MODEL_QUEUED`，不自动触发下一次 LLM 调用。
- CLI 将该 `Paused` 作为当前回合终点，恢复用户输入；下一条 `UserMessage` 与取消结果按历史顺序一起发送给当前 Agent，活动 SubAgent handoff 保持不变。
- 本决定取代决策 209 中“取消后产生 `ToolFinished`、进入 `MODEL_QUEUED` 并继续模型循环”的部分；`CancelSelection` 与真正的全局 `Cancel` 仍保持不同作用域。

**理由：**

- 用户取消的是一次选择交互，不是授权 LLM 自行决定下一步；继续调用模型会绕过用户输入边界。
- `Paused/WAITING_FOR_USER` 与审批拒绝、模型解析失败保持一致，能保留工具取消结果并等待明确的新指令。
- 保留 typed `CancelSelection` 和 request-id 校验，不把 UI 取消重新混入全局 `Cancel` 或 handoff unwind。

**曾考虑的替代方案：**

- 保持 `ToolFinished` 并让 CLI 继续 `Continue()` —— 会复现用户取消后自动调用 LLM 的问题，未采用。
- 直接丢弃取消结果 —— 会丢失当前工具 call 的审计和后续上下文，未采用。
- 将选择取消映射为全局 `Cancel` —— 会再次触发 SubAgent／handoff 取消，未采用。

**验证：**

- Runtime、CLI、Orchestrator 定向测试 46 项通过，覆盖无额外 LLM 调用、回到 CLI、下一条用户消息继续及活动 handoff 保留。
- 全量测试复跑时出现既有 KnowledgeService 锁释放时序波动；相关单测单独重跑通过，`git diff --check` 通过。

---

### 决策 225 —— R8-O 完整通过并停在 R8-D 授权门禁前

**背景：** R8-O 剩余人工 smoke 已由用户逐项完成并确认无问题。工程侧重新执行完整回归时，`test_prepare_failure_keeps_service_unavailable_and_can_be_retried` 复现了状态读取竞态：`reload()` 异常路径已把 `_state` 设为 `ERROR`，但尚未释放服务锁；无锁的公开 `state` 属性可提前暴露 `ERROR`，调用方紧接着搜索会得到 `retrieval_busy` 而不是稳定的 `retrieval_unavailable`。

**决定：**

- `KnowledgeService.state` 使用既有服务锁同步读取，确保调用方观察到的状态与该次 reload/search 临界区完成保持一致；不新增 API，不改变 reload/search 业务协议。
- 提交 `9da3242` 作为独立 R8-O 修复提交。
- 用户确认的完整 CLI／交互、Main→Resume→Main、Plan、Knowledge／Memory、Resume、关闭和数据边界人工 smoke，以及工程侧完整验证，共同构成 R8-O 通过证据。
- R8-O 用户审查完成后仍停在 R8-D 授权门禁；本决定不授权删除 legacy production modules、`.ipynb_checkpoints` 或任何旧运行数据。

**理由：**

- 状态属性是调用方判断服务可用性的公开观察面，不能暴露尚未完成锁内转换的中间状态。
- 单独等待测试线程或放宽为接受 `retrieval_busy` 会掩盖真实的观察一致性缺口。
- R8-D 是不可与观察期混合的独立删除切片，必须保留明确的用户授权与回退边界。

**曾考虑的替代方案：**

- 仅在测试中等待锁释放 —— 只能隐藏竞态，不能保证生产调用方观察一致状态，未采用。
- 将 `retrieval_busy` 视为失败启动后的合法永久结果 —— 会破坏既有 `retrieval_unavailable` 契约及显式 reload 重试语义，未采用。
- R8-O 通过后自动开始 R8-D —— 违反强制用户审查及独立授权门禁，未采用。

**验证：**

- KnowledgeService 定向 20 项测试通过。
- `uv run python -m unittest discover -s tests/get_me_in -t .`：283 项测试通过。
- `compileall`、`git diff --check`、import boundary 与实际 Catalog 验证通过；Catalog 为 2 Agent、26 ToolDefinition、10 CLI command。
- 真实 Memory delete smoke：删除前命中 1 条，删除后 repository、manifest 与 Chroma 查询均为空。
- legacy refusal smoke：4 个旧数据目录的常见文件访问被设置为访问即失败，隔离 v2 production composition 完成 Knowledge 启动、一轮 Runtime 与无 issue 关闭。

---

### 决策 226 —— R8-D 执行清单细化并保持授权门禁

**背景：** 用户确认 R8-D 之前的任务和检查均已完成，并要求开始分析、更新 R8-D 任务列表。原清单已给出删除目录和顶层文件，但缺少执行前精确盘点、意外非跟踪内容保护、staged allowlist、删除敏感验证以及提交前后的明确停止条件，不足以直接支持一次安全、可审计的删除。

**决定：**

- R8-D 任务拆分为清单分析与授权、删除前安全快照、精确删除、删除后验证、提交与回退五组；本次只完成只读盘点与文档更新，不执行删除。
- 当前 Git 跟踪删除白名单固定为 8 个 legacy package 中 45 个文件和 6 个顶层 legacy module，共 51 个文件。执行前必须重新生成清单；如目录内出现意外非跟踪内容或 symlink／reparse point，立即停止，不按目录整体删除。
- 三个本地 `.ipynb_checkpoints` 目录继续作为独立 literal-path 清理项；当前共 5 个文件，均被 Git 忽略且未发现 reparse link。禁止使用 `git clean`、通配符或从工作区根递归搜索删除。
- `pyproject.toml` 的 11 个直接依赖当前均有 v2 使用证据，R8-D 预计保持 `pyproject.toml`／`uv.lock` 不变；删除后必须复核，不凭 legacy 文件消失猜测性删除依赖。
- R8-D 提交只包含 51 个 tracked legacy 源文件删除。提交前必须通过 staged allowlist、完整自动化、`compileall`、`git diff --check`、Catalog、根入口和 legacy-data refusal 验证；最终完整真实 adapter／业务 smoke 仍由 R8-G/G8 执行。
- 本清单更新不构成 R8-D 执行授权。只有用户审查并明确授权后，才可从删除前安全快照开始；旧 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 始终不在删除范围内。

**理由：**

- 删除整个目录前先锁定 tracked、untracked、ignored 与 reparse 状态，可以防止精确源码白名单意外扩大到用户文件或链接目标。
- staged allowlist 把“计划删除 51 个文件”转化为提交前可核验事实，避免最终文档、v2 源码、测试或数据变更混入不可逆切片。
- 当前直接依赖全部仍有 v2 消费者；保留无变化的依赖文件比基于旧目录名称推测清理更安全，也避免无必要的锁文件重解析。
- R8-D 与 R8-G 分层验证：前者证明删除本身没有破坏生产入口和边界，后者完成文档归一化与最终全矩阵验收。

**曾考虑的替代方案：**

- 直接按 8 个目录执行递归删除 —— 无法保护执行前新增的非跟踪内容或 reparse target，未采用。
- 使用 `git clean` 一次清除所有 ignored checkpoint／cache —— 作用域会扩大到未列入 R8-D 的其他本地文件，明确拒绝。
- legacy 删除后顺手移除看似旧版专用的依赖 —— 静态检查证明 11 个直接依赖均仍被 v2 使用，且猜测性修改会扩大 R8-D 风险，拒绝。
- 把删除、最终文档和完整 G8 smoke 混成一个提交 —— 会破坏 R8-D 独立回退点并降低问题定位能力，未采用。

**验证：**

- 当前分支为 `refactor`，工作区在分析前干净，历史包含 R8-E `9fbeabc`、R8-O 修复 `9da3242` 与 checkpoint `f504427`。
- `git ls-files` 只读盘点得到 51 个 tracked legacy 源文件；白名单内未发现额外非忽略文件。
- 三个 checkpoint 目录当前共 5 个文件，均未被 Git 跟踪；路径属性检查未发现 reparse link。
- 对 `src/get_me_in/` 与 `tests/get_me_in/` 的直接依赖扫描确认 11 个项目依赖均仍有使用点。

---

### 决策 227 —— 授权新会话执行 R8-D 并收敛活跃文档

**背景：** R8-D 精确删除清单已经完成分析并由提交 `0b2cda7` checkpoint。用户明确表示本会话不执行删除，将在新会话执行 R8-D；同时要求把重构期间并行维护的设计、计划和任务内容收敛到原始四份项目文档，并更新 AGENTS.md，使新会话能够恢复正确状态并直接执行已授权的 R8-D。

**决定：**

- 用户对 `docs/task.md` R8-D 4.1～4.5 清单的审查和执行授权已经完成；本会话只迁移文档，不删除 legacy 源码、checkpoint 或旧运行数据。
- `docs/refactor-design.md`、`docs/refactor-plan.md`、`docs/refactor-task.md` 的完整 v2 内容分别收敛到 `docs/design.md`、`docs/plan.md`、`docs/task.md`，三份并行文档删除；历史 v1 内容只由 Git 保存。
- `docs/current.md` 的活跃路由改为 `docs/design.md`、`docs/plan.md`、`docs/task.md`、`docs/decision.md`；AGENTS.md 只描述当前 v2 事实、R8-D 执行边界和新会话恢复顺序，不再把 legacy 架构写成生产事实。
- 新会话必须先执行 `/project-bootstrap`，然后从 `docs/task.md` 4.2 删除前安全快照开始，依次完成精确删除、删除后验证和独立 R8-D 提交。
- R8-D 授权不包含 R8-G 或 R9。完成 R8-D 独立提交与 checkpoint 后必须停止，等待用户审查和后续授权。

**理由：**

- 单一 design／plan／task 路径消除“原始文档是 v1、refactor 文档是 v2”的双重事实源，新会话不再需要根据分支猜测应该读取哪一套。
- `current.md` 继续承担唯一阶段快照，四份项目文档分别承担设计、计划、任务和决策；AGENTS.md 只提供稳定工作约定和当前门禁，不复制完整状态。
- 将授权、执行起点和终止门禁写入 current/task/decision/AGENTS 四处，可以让新会话在不依赖聊天历史的情况下正确执行 R8-D，同时避免误入 R8-G。

**曾考虑的替代方案：**

- 保留三份 `refactor-*` 文档并只修改 AGENTS.md —— 仍保留两套事实源，无法完成用户要求的文档收敛，未采用。
- 删除历史 v1 内容而不保留追溯 —— Git 已完整保存旧版本，没有必要继续在工作树维护重复文档。
- 在本会话顺带执行 R8-D —— 用户明确要求只更新文档并在新会话执行，拒绝越过会话边界。
- 把 R8-G 一并授权 —— 本次授权仅针对 R8-D；R8-G 包含最终文档、README、配置和完整 G8 验收，仍需独立执行和审查。

**验证：**

- 收敛后活跃文件固定为 `docs/design.md`、`docs/plan.md`、`docs/task.md`、`docs/decision.md`，`docs/current.md` 只引用这四份文件。
- `docs/task.md` 将 R8-D 授权项标记完成，并把新会话起点固定为 4.2；R8-D 其余执行项保持待办。
- 本次变更仅涉及 Markdown 项目文档与 AGENTS.md，不包含任何 legacy 源码、checkpoint 或 `data/` 变更。

---

### 决策 228 —— 辅助文档完成收敛并删除

**背景：** 决策 227 已将活跃重构内容收敛到 design／plan／task／decision，但 `docs/` 仍保留五份 R0～R5 阶段的辅助 baseline、audit、matrix 和 smoke 文档。用户要求判断这些文件是否仍有保留必要；若内容已经整合，则用独立提交删除额外文档。

**决定：**

- 保留 `docs/current.md`。它是 `/project-bootstrap` 的唯一状态入口，不属于四份主文档，但新会话恢复依赖它。
- `docs/capability-parity-matrix.md` 的 legacy 能力、25-tool 基线和非等价机制已收敛到 `docs/design.md` 第 2／6 节、`docs/task.md` 与相关历史决策；当前 26-tool 事实必须从实际 Catalog 派生。
- `docs/g0-audit.md` 的 G0 结论和 R-D1～R-D6 门禁已收敛到 `docs/plan.md` R0、`docs/task.md` R0、`docs/design.md` 第 9 节与决策记录。
- `docs/legacy-cli-smoke-checklist.md` 的观察维度已由 `docs/task.md` R8-O、`docs/current.md` 和决策 225 的实际完成证据取代；旧清单中的空白结果与 `/auto-approve-switch` 不再是当前待办或命令事实。
- `docs/legacy-entry-baseline.md` 的旧入口源码基线 `f5ee3765cc055622029d8ce34c1a8f611202c434` 已记录到 `docs/design.md`；当前删除前回退点继续是 R8-E `9fbeabc`。
- `docs/v2-static-asset-boundary.md` 的三类静态输入和四类禁止旧运行数据边界已收敛到 `docs/design.md` 第 7.1 节、R-D6、`docs/task.md` R8-D 与 AGENTS.md。
- 删除上述五份辅助文档。完整原文由 Git 历史保留；工作树中的 `docs/` 只保留 `current.md` 与 design／plan／task／decision 四份主文档。

**理由：**

- 五份文件均无代码或测试依赖，内容是已完成阶段的冻结材料；继续保留会制造空白 smoke、旧命令和阶段性数量与当前事实并列的歧义。
- 将必要的 provenance 和映射写入主文档与本决策后，删除辅助副本不会损失新会话执行 R8-D 所需信息。
- `current.md` 与四份主文档形成清晰的五文件恢复集合，符合 `/project-bootstrap` 路由，同时保留 Git 作为完整历史来源。

**曾考虑的替代方案：**

- 连同 `docs/current.md` 一起删除，只保留四份主文档 —— 会破坏项目约定和 `/project-bootstrap` 的状态入口，明确拒绝。
- 保留五份文件并标为 archive —— 仍会让搜索结果混入旧命令、空白 smoke 和过期阶段状态，未采用。
- 建立 `docs/archive/` 保存副本 —— Git 已提供完整追溯，无需在工作树维护第二份历史，未采用。

**验证：**

- 删除前确认五份文件只被文档互相引用，没有代码、测试、README 或运行配置依赖。
- `docs/design.md` 新增历史材料收敛映射和旧入口源码基线；plan／task／current／AGENTS 已移除对辅助文件的活跃依赖。
- 本提交不修改 `src/`、`data/`、`main.py`、测试、依赖、README 或 `.env.example`，不执行 R8-D。

---

### 决策 229 —— R8-D 前置生命周期修复与遗留删除完成

**背景：** R8-D 删除后的默认 5 秒配置无法稳定等待 Knowledge 后台模型预热完成，根入口 `/exit` 连续 smoke 返回关闭超时；用户授权插入一个独立的前置修复提交，但要求保持 worker、ResourceStack、typed timeout 和 non-daemon 生命周期语义不变。

**决定：**

- 独立提交 `b74af9e` 将 `Settings` 产品默认值、`Settings.from_env()` fallback 和 `.env.example` 的 `SHUTDOWN_TIMEOUT_SECONDS` 从 5 秒调整为 60 秒，并增加默认值回归断言。
- 未修改 `BackgroundWorker`、`ResourceStack`、关闭错误处理、typed timeout 或 non-daemon worker 语义；修复提交不包含任何 legacy 删除。
- 默认配置连续 3 次冷启动立即 `/exit` 均返回 0，耗时约 38.603s、37.284s、36.941s；每次结束后匹配进程数为 0。
- 删除提交 `7514af3` 仅包含精确复核的 51 个 tracked legacy 源文件；3 个 checkpoint 目录仅作本地清理证据，不进入提交。
- R8-D 完成后只 checkpoint 并停止；不得自动进入 R8-G 或 R9。

**理由：**

- 60 秒是已观察到的实际模型预热与资源关闭所需产品边界，能够保留有界关闭和失败可见性，同时避免用 daemon 化或忽略关闭错误掩盖生命周期问题。
- 修复与删除分成两个可独立回退的提交，便于区分生命周期配置变化与 legacy 源码删除。
- 三次默认配置冷启动、完整自动化、静态边界、Catalog、production composition、legacy refusal 与旧数据指纹复核共同构成 R8-D 验收证据。

**曾考虑的替代方案：**

- 临时进程设置 60 秒后直接提交删除 —— 只能证明当前运行可停止，不能改变产品默认配置，未采用。
- 修改 BackgroundWorker、ResourceStack 或 daemonize worker —— 会扩大生命周期协议范围并掩盖关闭错误，明确禁止。
- 在删除提交中混入 README、R8-G 文档或依赖清理 —— 会破坏 R8-D 独立回退点，未采用。

**验证：**

- `b74af9e` 仅修改 `.env.example`、`src/get_me_in/application/settings.py` 和 `tests/get_me_in/test_settings.py`；`7514af3` 仅删除 51 个白名单文件。
- `uv run python -m unittest discover -s tests/get_me_in -t .` 运行 283 项并通过；`compileall`、`git diff --check`、import scan、11 项依赖使用、Catalog、composition 和拒绝访问 smoke 均通过。
- `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 的只读指纹与 mtime 和删除前一致；工作区 checkpoint 清理未进入 Git 提交。

---

### 决策 230 —— 确认 R8-G 详细清单但不授权本会话实施

**背景：** R8-D 已由 `7514af3` 精确删除 51 个 legacy 源文件并由 `c13d455` checkpoint。用户要求先审查完成情况，再判断 R8-G 清单是否需要调整。审查确认 R8-D 提交范围、保留路径和工作区状态正确，本轮独立复验 283 项 unittest、`compileall`、`git diff --check` 与生产 legacy import／动态 import 扫描均通过；同时发现原 R8-G 四条待办过于粗，未明确文件白名单、真实 smoke 明细、失败分流、decision append-only 规则和 R8-G 提交后的完整回退顺序。

**决定：**

- 用户接受细化建议；本会话只更新文档和 AGENTS.md，不修改代码，不删除 README／`.env.example` 的过渡段，不执行真实 adapter／业务 smoke，也不创建 R8-G 实施提交。
- R8-G 清单拆为六组：5.1 清单确认与实施门禁、5.2 过渡配置与 README、5.3 活跃文档与 AGENTS.md、5.4 自动化／静态／Catalog、5.5 根入口／真实 adapter／数据边界、5.6 提交／回退／停止门禁。
- R8-G 获得单独授权后只允许修改 `.env.example`、`README.md`、`AGENTS.md`、`docs/current.md`、`docs/design.md`、`docs/plan.md`、`docs/task.md` 与 `docs/decision.md`。不得修改生产代码、测试、脚本、数据、依赖或锁文件。
- 若 G8 发现代码、测试、依赖、公开协议或数据迁移缺陷，立即停止 R8-G，保留证据并另行提交最小修复清单；不得把修复混入文档／配置提交。
- `docs/decision.md` 继续 append-only；历史决策不因最终文档归一化而改写。当前态文档必须清除“legacy 源码仍存在／R8-O 未通过／R8-D 待执行”等过渡事实，历史章节保留时须明确其历史属性。
- G8 必须覆盖完整 unittest、`compileall`、`git diff --check`、import boundary、2 Agent／26 Tool／10 command Catalog、真实根入口与 CLI／handoff／审批／取消、Chroma／Knowledge／Memory、中文／英文／双语 Resume 与 PDF merge、legacy-data 非访问组合证据、写入边界和资源关闭。
- 当前 R8-D 后、R8-G 前的紧急回退为 `git revert 7514af3` 后 `git revert 9fbeabc`。未来 R8-G 提交后必须按逆提交顺序先 revert R8-G 提交，再 revert `7514af3`，最后 revert `9fbeabc`；legacy 源码恢复前不得实际启用 legacy-only 配置，任何回退不得触碰旧运行数据。
- R8-G/G8 完成并 checkpoint 后必须停止等待用户审查，不得自动进入 R9。

### 决策 231 —— 授权新会话实施 R8-G 并保持 G8 分流边界

**背景：** R8-D 已完成并通过用户审查，R8-G 5.1～5.6 清单已确认；本会话已完成 bootstrap、分支／工作区／历史核验，用户明确要求开始实施并为每个子任务建立 checkpoint。

**决定：** 授权本会话从 R8-G 5.2 开始自动执行至 R8-G 完成。实施只能修改 `.env.example`、`README.md`、`AGENTS.md`、`docs/current.md`、`docs/design.md`、`docs/plan.md`、`docs/task.md` 与 `docs/decision.md`；每个子任务独立验证并 checkpoint。若 G8 发现生产代码、测试、依赖、公开协议或数据迁移缺陷，立即停止并提交独立修复清单，不得混入 R8-G 文档／配置提交；完成 G8 与 checkpoint 后停止，不进入 R9。

**理由：** 用户已补齐决策 230 要求的单独明确授权；独立子任务提交和失败分流保持 R8-D 回退点可审查，并防止文档归一化掩盖产品缺陷。

**替代方案：** 继续等待授权——不再适用；将代码修复混入 R8-G——拒绝；自动进入 R9——拒绝。

**理由：**

- 文件白名单把最终文档归一化与产品修复分开，使 R8-G 可以独立审查、提交和回退。
- 显式 smoke matrix 避免辅助 matrix 文档删除后只剩“完整验证”这一不可执行描述，也确保 unit tests 不被误当作真实 adapter、CLI 生命周期或数据边界证据。
- 将失败分流写入门禁，可防止最终文档阶段顺手修改代码、依赖或测试而破坏 R8-D／R8-G 的独立提交边界。
- 区分 R8-G 前后的两种回退序列，才能在 legacy-only 示例被删除后仍保留完整、可审计的恢复路径。

**曾考虑的替代方案：**

- 直接使用原四条 R8-G 待办 —— 缺少文件范围、验证明细和失败处理，无法支持新会话安全执行，未采用。
- 本会话顺带删除 README／`.env.example` 过渡内容并执行 G8 —— 用户明确要求本会话不修改代码且只调整清单；R8-G 实施仍需单独授权，未采用。
- G8 发现缺陷时直接在同一提交修复 —— 会混合文档归一化与产品行为变化，破坏独立审查和回退，明确禁止。
- 重写决策 225～229 为最终状态 —— 会破坏历史证据；采用追加决策与更新当前态文档。

**验证与交接：**

- 新会话必须先执行 `/project-bootstrap`，以 `docs/current.md` 路由到四份活跃文档，读取本决策和 `docs/task.md` 5.1～5.6。
- 未取得 R8-G 单独明确授权前，只能审查清单和工作区状态，不得修改 README／`.env.example` 或执行 R8-G/G8。
