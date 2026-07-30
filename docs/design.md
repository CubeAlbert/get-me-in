# 系统设计文档

> 适用分支：`refactor`
>
> 本文是当前 v2 架构与剩余迁移边界的唯一设计来源。历史 v1 设计由 Git 保留，不再维护并行的重构设计文件。

## 1. 重构结论与当前落地状态

R0 重构启动时，legacy 项目已经完成一个可运行的 CLI 多 Agent 骨架，并打通了主 Agent 路由、简历 Agent、工具调用、RAG、记忆、Plan、会话恢复和基础中断等关键链路。问题不在于“功能完全不可用”，而在于所有能力逐步堆叠到了少数核心对象和模块级全局状态上：

- `BaseAgent` 同时承担提示词组装、对话状态、LLM 调用、回复解析、工具执行、审批、切换、Plan、记忆和取消处理。
- `App` 同时承担输入组件、命令路由、渲染、后台线程、UIBridge、Agent 编排、会话恢复、自动保存、记忆触发和输入历史。
- Agent、Tool、LLM、RAG、Memory、UIBridge、Plan context 与 Session ID 均存在不同形式的全局注册或模块级状态。
- CLI 通过 `_history`、`_plan`、`_get_agent_key()` 等私有成员直接修改 Agent，协议边界名义上存在，实际上没有形成封装。
- Tool 使用 `__switch__`、`__reject__`、`__cancelled__` 魔法字典传递控制流，Request/Response 枚举仍保留已废弃分支。
- 新增 Agent 需要重复实现约 14 个 `_get_*()` 方法；三个现有 Agent 的大部分代码都是提示词元数据样板。

因此本分支采用 **受控重写（controlled rewrite）**：在新的 `src/get_me_in/` 包中构建 v2，通过纵向切片逐步获得功能等价；不在原有 `BaseAgent` 和 `App` 上继续做大规模就地拆分。

当前 v2 已完成 R0～R8。根 `main.py` 已在 R8-E 切换到 `src.get_me_in.cli.main.main()`，R8-O 完整 smoke 与用户审查已经通过；R8-D 由提交 `7514af3` 删除 51 个 legacy production 文件，并由 `c13d455` checkpoint；R8-G 文档归一化与完整 G8 已完成，最终用户审查由决策 240 收口。当前停在 R9 独立授权门禁前，不检查、设计或实施 R9。

## 2. R0 legacy 能力盘点

本节保留重构启动时的行为基线，用于解释迁移决策；它不表示当前生产架构。当前 v2 事实以第 5～6 节和 `docs/current.md` 为准。

### 2.1 R0 已实现并作为迁移基线的能力

| 能力 | R0 状态 | legacy 实现 | v2 迁移要求 |
|------|----------|----------|----------|
| CLI 对话 | ✅ | `src/cli/app.py`，questionary + Rich | 保持基本交互和 Markdown 渲染 |
| 长文本输入 | ✅ | `/edit` 调系统编辑器 | 迁移为独立 CLI command |
| 命令补全与输入历史 | ✅ | questionary + prompt_toolkit | 从 `App` 提取为输入组件 |
| LLM 双 tier | ✅ | `LLMClient.chat_pro/chat_flash` | 抽象为 `LLMPort` + model profile |
| Web Search | ⚠️ | 由 LLM provider 的工具调用模拟 | 保留接口，明确 provider 能力与失败语义 |
| Prompt 拼装 | ✅ | `PromptLoader` 拼接公共模板并替换占位符 | Agent 元数据改为声明式 `AgentSpec` |
| 主 Agent 路由 | ✅ | MainAgent + AgentRegistry + switch tools | 改为 typed handoff，不再使用魔法字典 |
| ResumeAgent | ✅ | workspace 工具直接修改 LaTeX | 作为 v2 第一个完整纵向切片 |
| JobSearchAgent | ⚠️ | 测试用壳，依赖 web_search | 不视为完整岗位搜索产品能力 |
| 工具注册与可见性 | ✅ | `@tool` + 全局 ToolRegistry | 显式 ToolCatalog + capability 绑定 |
| 工具审批 | ✅ | ConfirmMode + UIBridge | 改为 RuntimeEvent/RuntimeCommand 往返 |
| 工作区文件工具 | ✅ | 10 个 workspace 工具 | 底层统一为 Workspace service，工具保持薄层 |
| 简历模板与 PDF 编译 | ✅ | copy_template + build_pdf | 迁移为 Resume capability adapter |
| Plan | ✅ | BaseAgent 内部状态 + 4 个工具 | 提取为独立 PlanService/PlanState |
| RAG | ✅ | Chroma + bi-encoder + reranker | 显式生命周期，索引 manifest 替代时间戳推断 |
| Memory | ✅ | Builder + Store + Indexer + Retriever | 应用服务显式编排，不依赖全局 Facade/观察者副作用 |
| 会话保存与恢复 | ✅ | SaveManager + JSON | 迁移为 versioned SessionSnapshot repository |
| `/rewind` | ✅ | 截断当前 Agent 内存 history | 升级为 Session aggregate 的受控 rewind |
| `/dump` | ✅ | 导出 history | 迁移为诊断 command |
| Esc 中断检查点 | ✅/受限 | 非阻塞阶段可取消，LLM 调用中需等待 | v2 将 cancellation 作为 LLM port 一等能力 |
| 生命周期清理 | ✅ | 模块级 shutdown hooks | 改为显式 Application.close() 逆序清理 |

### 2.2 R0 尚未实现或明确暂缓的能力

| 能力 | 原因分类 | 说明 | 重构后的处理 |
|------|----------|------|----------------|
| InterviewAgent | 路线图未完成 | 设计存在，代码目录不存在 | v2 稳定后新增，不作为首轮迁移阻塞项 |
| LearningAgent | 路线图未完成 | 仅有设计，没有实现 | v2 稳定后新增 |
| 完整 Job Search | 产品方案未定 | 数据源、自动化、合规边界未明确 | 先保留 JD 分析能力，搜索数据源另立决策 |
| LLM 调用即时取消 | 当前架构限制 | LLMClient 不暴露请求/transport 生命周期，单例不可安全重建 | 在 LLMPort 和 request-scoped call handle 中设计 |
| Sticky Plan | UI 架构限制 | questionary 与 Rich Live 的终端控制冲突 | CLI renderer 独占输出后再实现 |
| Schema-based 简历填充 | 已放弃方案 | Schema 复杂且限制灵活性，改为直接编辑 LaTeX | 不恢复旧方案；可在 Workspace/Artifact API 稳定后重新评估 |
| 简历版本写入/历史检索 | 已取消 | 通用 query_memory 被认为已覆盖个人信息检索 | v2 需区分“用户记忆”和“产物版本”，后者归 ArtifactRepository |
| 多会话并行或多前端 | 当前架构限制 | 全局 bridge/cancel/plan agent/registry/client 只支持单活动上下文 | v2 依赖实例化 ApplicationContext，不共享可变全局状态 |

### 2.3 R0 文档与代码漂移

当前文档列出 23 个工具，但代码实际存在 25 个 `@tool`：Plan 已从 3 个增加到 4 个，switch 模块还包含 `provide_choices`。`RequestType.CONFIRM_APPROVED`、`ResponseType.SELECT`、`ResponseType.CONFIRM` 仍在协议中，但主循环已经不再使用。这类漂移说明当前架构缺少单一事实来源，重构后工具目录、Agent 目录和协议枚举必须由同一声明生成或可直接枚举验证。

### 2.4 历史基线材料收敛

R0～R5 曾使用五份辅助文档冻结 legacy 行为和迁移输入。决策 228 确认其有效内容已收敛，完整原文继续由 Git 保存：

| 历史材料 | 已收敛内容 | 当前事实来源 |
|---|---|---|
| v1 capability parity matrix | legacy 可观察能力、25 个工具迁移基线、允许废止的全局 Registry／UIBridge／魔法字段 | 本节、第 6 节、`docs/task.md` 和相关决策；当前 Catalog 必须从运行时导出 |
| G0 audit | R-D1～R-D6、G0 通过与进入 R1 的门禁 | 第 9 节、`docs/plan.md` R0、`docs/task.md` R0 和 `docs/decision.md` |
| legacy CLI smoke checklist | 启动、命令、审批、handoff、Session、Knowledge／Memory、Resume 的人工观察维度 | `docs/task.md` R8-O、`docs/current.md` 和决策 225 的实际完成证据 |
| legacy entry baseline | 旧入口源码基线 `f5ee3765cc055622029d8ce34c1a8f611202c434` 与旧启动链路 | 第 6.11 节、决策 190～192；删除前入口回退点为 R8-E `9fbeabc` |
| v2 static asset boundary | 只复用 reference／prompts／resume templates，禁止迁移旧运行数据 | 第 7.1 节、R-D6、`docs/task.md` R8-D 和 AGENTS.md |

这些辅助文档中的空白 smoke 记录和阶段性措辞不是当前待办，不得覆盖 `docs/current.md`、实际 Catalog 或已完成的 R8-O 证据。

## 3. 架构问题与重复代码根因

### 3.1 巨型对象与职责聚合

| 模块 | 当前规模（约） | 混合职责 | 结果 |
|------|----------------|----------|------|
| `src/agents/base.py` | 708 行 | Prompt、LLM、解析、状态机、工具、审批、Plan、Memory、Cancel | 任一基础能力变更都影响所有 Agent |
| `src/cli/app.py` | 700+ 行 | 输入、命令、渲染、线程、交互桥、编排、存档、恢复 | 无法替换 CLI 或独立验证编排逻辑 |
| `src/tools/workspace_tools.py` | 460+ 行 | 路径安全、读写状态、文件操作、工具描述 | 文件能力无法被非 Resume 场景复用 |
| `src/utils/saver.py` | 340+ 行 | JSON codec、文件 repository、session aggregate、清理策略 | schema 演进与业务流程耦合 |

核心问题不是文件行数本身，而是每个模块包含多个变化原因。

### 3.2 Agent 声明样板重复

MainAgent、ResumeAgent 和 JobSearchAgent 都重复实现 `_get_agent_name()`、`_get_agent_description()`、`_get_responsibilities()`、`_get_primary_goal()`、`_get_success_criterions()`、约束和风格等方法。它们没有行为差异，只是在 Python 方法里返回字符串。新增 InterviewAgent 或 LearningAgent 会继续复制相同结构。

目标：使用一个不可变 `AgentSpec` 声明 key、展示信息、prompt 片段、model profile 和 capability；只有真正存在领域行为时才创建 Agent 类。

### 3.3 全局状态与隐式装配重复

当前存在多套相似模式：

- `get_client()`：双检锁 LLM 单例。
- `get_agent_registry()`：双检锁 AgentRegistry 单例。
- `src/rag/__init__.py`：Store/Reranker/Loader 单例与后台线程。
- `src/memory/__init__.py`：Store/Indexer/Retriever 单例与后台线程。
- `UIBridge._current_bridge`、`plan_tools._plan_agent`、`session._session_id`：模块级当前上下文。
- `main.py` 通过导入八个 tool 模块触发注册副作用。

这些代码块表面不同，根因相同：依赖没有在 composition root 中显式创建并传递。它们让初始化顺序成为隐藏协议，也让并行会话、隔离验证和资源释放变得困难。

### 3.4 控制流使用魔法字段

工具普通返回值和框架控制信号共用 dict：`__switch__`、`__reject__`、`__cancelled__`。BaseAgent 需要依次探测这些键并设置 `_pending_switch`、`_pending_reject`、`_pending_tool`。App 又需要解释 Response 上的 switch 字段并补写 tool result。

目标：Tool 只返回显式 `ToolOutcome`；Runtime 只产生显式 `RuntimeEvent`。Handoff、Approval、Selection、Cancelled 和 Failed 都是类型，不再藏在业务数据中。

### 3.5 抽象泄漏和跨层私有访问

`App` 直接读取或覆盖 Handler 的 `_history`、`_plan`，直接调用 `_get_agent_key()`、`dump_history()`、`write_memory()`；AgentRegistry 也通过 `_get_*()` 私有方法抽取描述。这意味着 `Handler.process()` 并不是实际边界，换一个 Handler 实现仍需伪造 BaseAgent 私有结构。

目标：一个 `Application` 对应一个活动 `ApplicationSession`，Session aggregate 是会话状态唯一所有者；CLI 只调用公开的 Application API。`AgentRuntime` 接收一个 Agent 的规范状态并返回状态转换结果，不再持有第二份长期可变状态，也不增加进程内 `AgentStateRepository`。

### 3.6 UI 与执行线程互相侵入

当前 App 启后台线程执行 Agent，工具再通过全局 UIBridge 阻塞回主线程做 confirm/select；取消标志也放在 UI 模块。这虽然解决了单 CLI 场景，却使工具依赖 CLI，实现其他前端时必须复刻桥接协议。

目标：Runtime 遇到审批或选择时返回事件并暂停；前端把用户结果作为 command 送回。后台线程只用于运行阻塞步骤和显示 spinner，不承载业务协议。

### 3.7 文件访问和路径安全散落

workspace、customer file、resume tools 和 file_reader 各自处理 Path、exists、suffix、编码和错误转换。`_validate_path()` 使用字符串前缀判断是否越界，语义上不如 `Path.is_relative_to()` 可靠；读取后编辑状态 `_read_files` 又是进程级集合，会跨会话污染。

目标：建立实例化 `Workspace`，集中处理 root、路径解析、编码、原子写入和 read revision；工具只负责参数适配与结果展示。

### 3.8 序列化与 schema 演进分散

Message、MemoryBuilder、Saver 都直接使用 `dataclasses.asdict()` + `json.dumps()`；恢复逻辑手工重建枚举和 datetime。存档没有 `schema_version`，模型字段变化会直接影响旧存档。

目标：使用 versioned DTO + codec + migration；Domain 对象不直接决定磁盘格式。

### 3.9 RAG 与 Memory 生命周期耦合

MemoryStore 通过回调触发 MemoryIndexer，Indexer 再延迟 import RAG Facade。RAG 自身又有单例状态和后台加载线程。`.last_update` 只按时间戳判断增量，无法完整表达删除、重命名或内容 hash。

目标：KnowledgeService 显式协调 repository 与 index；manifest 记录 source、collection、hash、mtime 和 chunk ids；启动、重载、关闭均为公开生命周期。

## 4. 重构目标与非目标

### 4.1 目标

1. 每个模块只有一个主要变化原因，核心对象控制在可审查范围内。
2. 所有运行时依赖由 composition root 显式创建；禁止依赖导入副作用完成装配。
3. 单个进程可创建多个相互隔离的 Application；每个 Application 同时只管理一个活动 ApplicationSession。单个 Application 内的多会话并行留到 R9。
4. CLI 不读取 Agent 私有字段，Agent 不导入 CLI。
5. Agent 元数据声明式，新增普通 Agent 不再复制 14 个方法。
6. 工具控制结果强类型化，工具上下文显式注入。
7. Session、Message、Plan、Artifact 使用版本化持久化 schema。
8. 取消令牌贯穿 Runtime、LLM、Tool 和 ProcessRunner。
9. 保持同步编程模型；允许受控 worker thread，不引入 asyncio。
10. 在切换入口前达到当前已实现功能的可验证等价。

### 4.2 非目标

- 本轮重构不同时开发 InterviewAgent、LearningAgent 或完整招聘平台抓取。
- 不引入 LangChain、CrewAI、AutoGen 等 Agent 框架。
- 不因重构恢复已放弃的 schema-based 简历方案。
- 不在 v2 骨架未稳定前增加新的 CLI 功能。
- 不把记忆模块当作跨 Agent 业务对象数据库；简历 PDF 等产物由 ArtifactRepository 管理。

## 5. v2 目标与已落地架构

### 5.1 分层与依赖方向

```text
cli ──────────────────┐
                      v
                application
               /           \
              v             v
           domain          ports
                             ^
                             |
                         adapters

bootstrap/composition root 负责创建 adapters 并注入 application。
domain 和 application 不允许反向 import CLI、OpenAI、Chroma、questionary 或具体文件系统实现。
```

### 5.2 当前目录

```text
src/get_me_in/
├── domain/
│   ├── agents.py          # AgentSpec / AgentKey / Capability
│   ├── artifacts.py       # Artifact / ArtifactOperation
│   ├── knowledge.py       # Knowledge state / manifest
│   ├── memories.py        # Memory record / build result
│   ├── messages.py        # ConversationRecord / Role
│   ├── plans.py           # Plan / PlanItem / PlanStatus
│   ├── sessions.py        # SessionState / AgentSessionState / HandoffFrame
│   └── tools.py           # ToolDefinition / ToolOutcome
├── application/
│   ├── application.py     # Application 公开边界
│   ├── runtime.py         # AgentRuntime 状态机
│   ├── orchestration.py   # Hub-and-Spoke handoff
│   ├── commands.py        # RuntimeCommand
│   ├── app_commands.py    # ApplicationCommand
│   ├── events.py          # RuntimeEvent
│   ├── session_service.py / session_codec.py
│   ├── plan_service.py / tool_executor.py
│   ├── knowledge_service.py / memory_service.py
│   └── artifact_service.py / resources.py
├── ports/
│   ├── llm.py / web_search.py
│   ├── sessions.py / retrieval.py
│   ├── knowledge.py / memories.py
│   ├── workspace.py / external_files.py
│   ├── artifacts.py / resume_artifacts.py
│   └── clock.py / ids.py / process.py / frontend.py
├── adapters/
│   ├── openai_llm.py / openai_web_search.py
│   ├── json_session_repository.py
│   ├── json_manifest_repository.py
│   ├── json_memory_repository.py
│   ├── json_artifact_repository.py
│   ├── chroma_knowledge_index.py
│   ├── local_workspace.py
│   └── local_resume_artifacts.py
├── tools/
│   ├── system.py / plan.py / switch.py
│   ├── retrieval.py / customer_file.py / web.py
│   └── workspace.py / resume.py
├── agents/
│   └── resume.py          # Resume AgentSpec factory
├── cli/
│   ├── app.py
│   ├── commands.py
│   ├── input.py
│   ├── renderer.py
│   ├── worker.py
│   ├── main.py
│   └── __main__.py
├── logging_setup.py
└── bootstrap.py           # 唯一 production composition root；同时声明 Main AgentSpec
```

上表只列稳定层级和主要模块，完整文件集合以仓库实际目录为准。R8-D 已删除 legacy production 源码；当前生产代码只有根 `main.py` 与 `src/get_me_in/` v2，不存在供 production 反向 import 的旧 `BaseAgent`、`App`、全局 Registry 或 UIBridge。

## 6. 核心模型与公开边界

### 6.1 AgentSpec 替代 14 个占位符方法

建议模型：

```python
@dataclass(frozen=True)
class AgentSpec:
    key: AgentKey
    display_name: str
    description: str
    responsibilities: tuple[str, ...]
    primary_goal: str
    success_criteria: tuple[str, ...]
    hard_constraints: tuple[str, ...]
    soft_constraints: tuple[str, ...]
    style: AgentStyle
    model_profile: str
    capabilities: frozenset[Capability]
```

PromptRenderer 接收 AgentSpec、ToolCatalog 和 AgentCatalog，统一生成 system prompt。AgentCatalog 提供公开 descriptor，不再调用 Agent 私有方法。真正需要领域状态机的 Agent 才增加实现类。

### 6.2 RuntimeCommand 与 RuntimeEvent

Runtime command 保持：`UserMessage`、`Continue`、`Approve`、`Reject`、`SubmitSelection`、`ToolResult`、`Cancel`；R4 增加 `CompleteHandoff(call_id, summary)` 与 `FailHandoff(call_id, code, message)`，专门闭合 `WAITING_FOR_HANDOFF`。R8-O 增加 `CancelSelection(request_id, reason)`，只将 `provide_choices` 的取消作为 tool result 交回当前 Agent，不产生 Agent `Cancelled`，不得关闭活动 handoff；真正的运行取消继续使用 `Cancel`。

Runtime event 保持：`Progress`、`ApprovalRequested`、`SelectionRequested`、`ToolStarted`、`ToolFinished`、`HandoffRequested`、`Completed`、`Failed`、`Paused`、`Cancelled`。`Paused` 表示当前 Agent 已进入 `WAITING_FOR_USER`，活动 handoff 不闭合，CLI 必须等待下一条 `UserMessage`；当前用于模型回复解析失败、审批拒绝和选择取消。`ToolStarted` 携带只读 arguments 映射，`ToolFinished` 可携带 Plan 投影；二者均不要求 CLI 读取 Session 或反解析工具输出字符串。

一个 Application 只暴露一个活动 Session，公开边界调整为：

```python
def handle(
    command: RuntimeCommand | ApplicationCommand,
) -> RuntimeEvent | SessionView | Path | ApplicationResult
def view() -> SessionView
def snapshot() -> SessionSnapshot
def restore(session_id: str) -> SessionView
def rewind(turn_id: str) -> SessionView
def list_sessions() -> tuple[SessionPreview, ...]
def dump() -> Path
def exit_subagent(summarize: bool = True) -> RuntimeEvent
def request_cancel(reason: str = "Cancelled by user") -> None
def finalize_turn() -> TurnFinalizationResult
def close() -> CloseReport
```

`RestoreSession`、`RewindSession`、`ExitSubAgent`、`DumpSession` 等属于 `ApplicationCommand`，不混入模型回合使用的 `RuntimeCommand`。CLI 可以通过统一分发入口调用两类 command，但 Runtime 永远不解释 CLI/Session 命令。

该协议取代旧 Request/Response、UIBridge action 和 switch magic dict。Runtime 每次只推进一个明确状态，不使用多个松散 `_pending_*` 标志表达组合状态。内部 `AgentRuntime.advance(state, command, *, session_id)` 返回 `RuntimeTransition(state, event)`；`RuntimeTransition` 只在 application 层使用。Application 对 RuntimeCommand 返回一个 RuntimeEvent，对 ApplicationCommand 返回对应的只读 view、Path 或强类型 ApplicationResult。

### 6.3 ToolCatalog、ToolContext 与 ToolOutcome

Tool 不再在 import 时注册。每个 tool module 暴露 `build_*_tools(dependencies) -> list[ToolDefinition]`，由 bootstrap 汇总：

```python
@dataclass(frozen=True)
class ToolContext:
    session_id: str
    agent_key: AgentKey
    plan: PlanService
    workspace: WorkspacePort
    cancellation: CancellationToken

class ToolOutcome: ...
class ToolSuccess(ToolOutcome): ...
class ToolFailure(ToolOutcome): ...
class ToolHandoff(ToolOutcome): ...
class ToolInteraction(ToolOutcome): ...
```

Agent 可见工具由已经落地的通用 capability 决定，例如 `workspace.read`、`workspace.write`、`workspace.open` 与 `resume.artifact`，不再使用 `agent=["*"]` 和主 Agent 特判。若后续确有最小权限需要，再拆分 `resume.template.copy` 与 `resume.pdf.build`，R4 不提前扩展枚举。

### 6.4 Session aggregate 与编排

`SessionState` 是 active agent、所有 `AgentSessionState`、handoff stack 和会话时间信息的唯一规范所有者。`AgentSessionState` 直接承接当前 `RuntimeState` 的 history、phase、pending tool、model call/repair 状态，并持有该 Agent 的 Plan；不得在 Session 与 Runtime 中复制同一组字段。长期存活的 `PlanService` 不再独立拥有另一份 plan，执行工具时从 AgentSessionState 恢复，转换完成后立即写回。

CLI input history 属于 R5 `InputController`，不进入 domain SessionState。R5 复审决定只保留进程内导航状态，并从 `SessionView.rewind_points` 重建 restore 后的历史，不增加独立 CLI snapshot schema。`/restore` 与 `/rewind` 的交互选择列表末尾必须提供“❌ 取消”；选择取消只返回 CLI，不调用 Application。`/rewind` 必须在发出 `RewindSession(turn_id)` 前从当前只读 rewind point 保存目标用户文本，并通过 `CommandAction.PREFILL` 传回 CliApp 的下一次输入框；不得在回退后的投影中反查，因为目标回合可能已被截断。Artifact 由 R7 `ArtifactRepository` 管理，R4 的 SessionSnapshot 不提前定义 Artifact/ArtifactRef schema。

Hub-and-Spoke 规则保留：只有 Orchestrator 能进行 handoff。Main Runtime 只接收可路由的 Agent descriptor；子 Agent Runtime 不持有完整 `AgentCatalog`，也不直接调用其他子 Agent。

Handoff 使用 `HandoffFrame(source, target, call_id, turn_id, context)`。Orchestrator 切换到子 Agent 时保留源 Agent 的 `WAITING_FOR_HANDOFF` pending call，并立即以 `UserMessage(context)` 启动目标 Runtime，使 CLI 在收到 `HandoffRequested` 后只需继续驱动新的 active agent。子 Agent 返回 summary 后，Orchestrator 向源 Runtime 发送 `CompleteHandoff`，原子地写入 tool result、弹出 frame 并恢复 active agent。未知 Agent、目标启动失败、嵌套切换和子 Agent `Failed` 通过 `FailHandoff` 闭合原 call id；`/exit_sub` 默认要求 SubAgent 总结并正常 `CompleteHandoff`，显式 `false` 才直接 `FailHandoff`。活动 SubAgent 的 `Cancelled` 只结束当前 run，保留 active agent、handoff frame 与 Main 的 `WAITING_FOR_HANDOFF`，等待下一条用户消息；CLI 不补写 conversation record。

R4 以测试专用 sub Agent 完成 G4 编排门禁；真实 Resume AgentSpec 与领域能力仍在 R7 落地，避免 R4 反向依赖 R7。

### 6.5 持久化

SessionSnapshot 至少包含：

```json
{
  "schema_version": 2,
  "session_id": "...",
  "active_agent": "main",
  "agents": {"main": {}},
  "handoff_stack": [],
  "created_at": "...",
  "saved_at": "..."
}
```

每条 `ConversationRecord` 增加同一用户回合共享的 `turn_id`；tool call/result 继续额外使用 `call_id`。Rewind 只接受 `turn_id`，默认回退到用户回合边界，并同步修正 Agent state、Plan、pending action 与 handoff stack，不能截断在 tool call/result 中间。

Repository 必须原子写入临时文件后 replace，磁盘 `SessionSnapshotCodec` 与 provider-facing `ConversationCodec` 分离。v2 从全新 `schema_version=2` 会话开始，不读取或迁移旧 Session。

Snapshot 只记录可恢复的稳定状态。正在执行的 LLM/Process 调用先归一化为 interrupted/cancelled；`TOOL_READY` 不允许作为可自动重放状态持久化，避免恢复后重复副作用。等待 approval、selection 或 handoff 的状态可以保存，但 handoff frame 必须与 active agent、源 Agent 的 `WAITING_FOR_HANDOFF`、pending call id 和 turn id 一致。restore 必须先确认 snapshot 中的 Agent 均已由当前 Application 装配，再替换活动 Session；restore/rewind 必须清除 `WorkspaceAccessState`，编辑前重新读取文件。

`SessionView` 通过只读 `SessionTurnView` 投影公开主 Agent 用户回合的 `turn_id`、文本和时间，用于 R5 context recap 与 `/rewind` 选择；`SessionPreview` 同时提供从最新主 Agent 用户输入派生的短 `preview`，用于 `/restore` 会话选择。CLI 不读取完整 `SessionSnapshot` 或私有 history。CLI 自己的输入导航历史仍归 `InputController`，不进入 domain Session。

R4 新增文件、类和公开方法清单如下，编码前仍需用户确认：

| 文件 | 新增/调整对象 | 公开边界 |
|------|---------------|----------|
| `domain/sessions.py` | `RuntimePhase`、`PendingToolCall`、`AgentSessionState`、`SessionState`、`HandoffFrame`、`SessionTurnView`、`SessionView`、`SessionPreview` | 不提供副作用方法；承接现有 runtime state 类型并只保存不可变规范状态，禁止 domain 反向 import application；`SessionTurnView` 仅为 frontend 提供安全回合投影 |
| `application/runtime.py` | 调整 `RuntimeState` 所有权；新增 `RuntimeTransition` | `advance(state, command) -> RuntimeTransition`；移除长期内部状态副本 |
| `application/commands.py` | `CompleteHandoff`、`FailHandoff` | 强类型字段按 call id 闭合 handoff |
| `application/app_commands.py` | `ApplicationCommand`、`RestoreSession`、`RewindSession`、`ExitSubAgent`、`DumpSession` | 仅供 Application/CLI，不进入 AgentRuntime |
| `application/orchestration.py` | `Orchestrator`、`SessionTransition` | `handle(session, command) -> SessionTransition` |
| `application/session_service.py` | `SessionService` | 持有一个活动 SessionState，公开 `view/snapshot/restore/rewind/list_sessions/dump`；不再增加同义状态容器类 |
| `application/session_codec.py` | `SessionSnapshot`、`SessionSnapshotCodec` | `encode/decode`，校验 `schema_version=2` 与 record/pending 对应关系 |
| `ports/sessions.py` | 扩展 `SessionRepository` | `save/load/list/close`；不暴露 JSON 细节 |
| `adapters/json_session_repository.py` | `JsonSessionRepository` | 原子 save 与只读 load/list；不迁移 v1 |
| `application/application.py` | 调整现有 `Application` | 保留 `handle/request_cancel/close`，增加上述 Session 公共 API |
| `tests/get_me_in/test_sessions.py` | Session domain/service tests | 覆盖唯一状态源、turn rewind、Plan/pending/handoff 同步与 revision grant 清理 |
| `tests/get_me_in/test_orchestration.py` | Orchestrator tests | 覆盖 main→测试 sub→main、Complete/FailHandoff、未知/嵌套/取消路径 |
| `tests/get_me_in/test_session_codec.py` | Snapshot codec tests | 覆盖 tagged records、schema version、稳定 phase 与损坏数据拒绝 |
| `tests/get_me_in/test_json_session_repository.py` | Repository contract tests | 覆盖原子 save、load/list、失败不破坏旧 snapshot 与 v1 隔离 |

`domain/messages.py`、`application/plan_service.py`、`application/tool_executor.py`、`application/settings.py`、`bootstrap.py` 属于既有文件调整：分别增加 `turn_id`、消除长期独立 Plan 副本、按 session/agent 生成 ToolContext、增加 `sessions_dir`（默认全新 `data/v2/sessions/`）、为每个 Application 创建真实 session id 与资源清理顺序；不新增第二套 Message、Plan 或 ToolContext 类型。

### 6.6 LLM 与取消

`LLMPort.complete(request, cancellation)` 返回标准 `LLMResult`。OpenAI adapter 负责模型名、provider thinking、timeout、retry 与原始 SDK 数据转换。每个活动调用产生可取消 handle；取消后该 handle 失效，但 Application 和下一次调用仍可继续。不要通过外部访问 OpenAI SDK 私有字段。

如果 OpenAI SDK 无法稳定中止同步调用，adapter 可以使用 request-scoped client/transport，由 worker 持有并在取消时关闭；该细节不得泄漏到 Runtime。

#### 6.6.1 JSON `thinking` 契约（R6 前置修复）

R8-F-C 完成后，静态 `07_message_format.md` 中的 `thinking` 是模型生成、允许向用户展示的推理摘要，与 provider 原生 `reasoning_content` 和 `LLM_THINKING_ENABLED` 完全分离。finish 回复可以省略 thinking；如果提供 `null`、空字符串或空白字符串表示没有摘要，其他非空值必须是 string。tool_call 的 thinking 仍可省略但如果提供必须是 string。该规则由决策 219 取代决策 212 对 finish thinking 非空的要求，并恢复 finish thinking 的可选语义。v2 继续执行决策 136，不读取、保存或展示 provider 原生 reasoning_content。

`MessageRecord` 和 `ToolCallRecord` 保存可选 thinking；Runtime 必须把 `ModelReplyParser` 的结果投影到 Completed/ToolStarted，使 Renderer 可在独立 `SHOW_THINKING` setting 开启时显示“思考摘要”。Session snapshot 对 assistant message/tool call 的 thinking 做可选 round-trip，缺失字段兼容为 `None`。thinking 不参与业务状态转换、tool closure、handoff、rewind 边界或 Plan。

“保留”不等于“回放”。R8-F-C 完成后由 `ModelMessageCodec` 编码下一轮 LLMRequest，并必须对所有历史记录剥离 thinking；R6 的 `SessionService.memory_source()` 同样必须复制出 thinking 为 `None` 的 provider-neutral 记录，MemoryExtractor 不得接收展示摘要。这样修复只为 R6 增加 G5-F 前置依赖和一条 MemoryBuildSource 投影约束，不改变 R6 的总体架构、已确认文件清单或第一切片。

#### 6.6.2 单一模型消息 Entity 与有界格式修复（R8-F-C，已确认）

决策 242 的首轮实现只收敛了模型输出：`ModelReplyParser` 接受 `message/thinking/tool_call`，但 `ConversationCodec` 仍把历史记录手写为另一套 flat JSON；`07_input_format.md` 与 `08_output_format.md` 又把两套字段语言一起拼入 system prompt。两个 mapper、两个 Prompt schema 和两个不同的中间对象各自有测试，因而 287 项自动化可以全绿，却没有实现 Input／Output 共用一个 Entity 的核心目标。决策 248 撤回该实现的 smoke 入口。

修正后的唯一 LLM-facing 顶层对象是 immutable `ModelMessageEntity`。它表达 provider role、`message`、可选 `thinking`、可选 `tool_call`、可选的系统注入 `tool_result`、可选 `context` 与仅供本地诊断的 normalization 标记；嵌套值使用经过 codec 校验的 immutable mapping，不再创建第二个 reply entity。role 只映射 provider `LLMMessage.role`，其余模型可见字段使用同一个 JSON envelope：

```json
{
  "message": "文本",
  "thinking": null,
  "tool_call": null,
  "tool_result": null,
  "context": null
}
```

同一个 `ModelMessageCodec` 是唯一字段映射与验证所有者：

- 历史输入：`MessageRecord | ToolCallRecord | ToolResultRecord` → `ModelMessageEntity` → `LLMMessage`。assistant 历史的 thinking 继续剥离；Tool call 映射到 `tool_call`；Tool result 映射到 `tool_result={"name": ..., "value": ...}`；Plan 映射到 `context={"plan": ...}`。内部 event id、timestamp、turn id 与 tool call correlation id 不进入模型可见 JSON。
- 模型输出：原始 JSON → `ModelMessageEntity(role=assistant, ...)` → Runtime 的 `Completed`／`ToolStarted` 与既有 domain record。模型只可填 `message`、`thinking`、`tool_call`；`tool_result` 与 `context` 是 Runtime-owned，模型返回非空值时拒绝。`tool_call=null` 表示 finish，object 表示工具调用；finish message 必须非空。`arguments` 缺失／null 可归一化为 `{}` 后交给 ToolExecutor 做既有校验。
- `ModelReply`／`ModelReplyParser` 与当前手写 flat `ConversationCodec` 不再作为独立协议所有者；迁移测试与 import 后删除这两个旧模块，由 `AgentRuntime` 只依赖注入的 `ModelMessageCodec`，不得在 Runtime、PromptRenderer 或测试 fixture 中再次手写同一字段转换。
- `ConversationRecord` union 继续是 Session/domain 的 canonical history，不因 LLM 边界合并而替换；RuntimeCommand、RuntimeEvent、ToolDefinition、ToolExecutor、Capability、审批、handoff、CLI、provider `json_object` 和 snapshot conversation schema 均保持不变。

首条完整 system prompt 继续作为 provider 外层 `Role.SYSTEM` 控制消息，不伪装成 conversation JSON；其后的 history record 与模型 reply 才统一经过 `ModelMessageEntity`。Prompt 模板只保留一个按文件名排序的 `07_message_format.md`，删除 `07_input_format.md` 与 `08_output_format.md`。该文件展示上面的唯一 envelope，并用“history-owned／assistant-owned”说明字段所有权；不得出现旧 InputFormat 的字段列表，也不得为了说“禁止旧格式”而再次把旧字段名写入 system prompt。`PromptRenderer.render_message_format()` 从这一文件读取格式修复内容，完整 system prompt 与 repair 注入因而使用同一来源；决策 213 的“顺序只由文件名决定”继续有效，但其中 InputFormat／OutputFormat 两文件命名被决策 248 取代。

首轮实现中已经落地的有界 repair 计数继续保留：本地 `json_repair` 成功不计数；每个 Agent 用户 turn 最多安排 3 次模型格式 repair；合法回复和工具执行不清零；第四次失败进入 `Paused("invalid_model_reply")`／`WAITING_FOR_USER` 并保留 handoff；下一条 `UserMessage` 清零。`format_repairs_used` 与 snapshot 对旧 bool 的 0／1 兼容不回退。

回归测试必须证明：所有 history record 与 reply 都经过同一个 Entity／codec；system prompt 和 repair prompt 只含一个 MessageFormat 且不含旧 InputFormat 字段约定；message、tool call、tool result、system repair、Plan context 的映射与方向所有权；thinking 不回放；非法输出不触发猜测或副作用；三次 repair、第四次暂停和 snapshot 兼容保持有效。完整自动化和独立代码 checkpoint 通过后，才交由用户执行真实 Main finish、Main 工具链、Main→Resume→工具→finish smoke。本修正不进入、检查或设计 R9。

### 6.7 CLI

CLI 只依赖 `Application` 的公开命令、事件与 Session view，不接触 AgentRuntime、PlanService、CancellationToken 实例、完整 SessionSnapshot 或任何私有 history。拆分职责如下：

- `CliApp`：唯一外层输入循环；把普通文本转换为 `UserMessage`，驱动 RuntimeEvent → 下一条 RuntimeCommand，并在终态触发 session snapshot；命令 handler 的预期异常统一渲染为错误并返回输入循环，不允许用户可控的命令参数终止 CLI。
- `CommandRegistry`：命令解析、帮助文本、alias 与 handler 映射；R6 可替换已注册的 unavailable handler，无需修改 CliApp。
- `InputController`：autocomplete、进程内输入导航历史、prefill、editor、confirm/select；其中 `confirm()` 使用 questionary 选项列表呈现“✅ 执行 / ❌ 取消”，不使用 `y/N` 确认框；不增加独立 CLI 持久化 schema。restore 后可从 `SessionView.rewind_points` 重建导航历史。
- `Renderer`：Markdown、Plan、spinner、错误、命令结果和 `SessionView` context recap；工具开始时以脱敏、截断后的 arguments 摘要展示调用，工具结束时显示截断结果预览；Plan 工具结束时直接渲染只读 Plan 表格，不解析输出字符串；不决定下一条业务 command。
- `WorkerRunner`：使用单 worker 串行执行 RuntimeCommand 或需要 worker 的 ApplicationCommand，并只接受 `RuntimeEvent | ApplicationResult`；轮询 Esc/Ctrl+C 时仅通过 `Application.request_cancel()` 跨线程取消，不得并发执行 snapshot/restore/另一条 command。

事件推进由 `CliApp` 明确处理：`Progress`、`ToolStarted`、`ToolFinished`、`HandoffRequested` 转为 `Continue`；`ApprovalRequested` 转为 `Approve/Reject`；`SelectionRequested` 的有效值转为 `SubmitSelection`，选择界面或自定义输入中的 Ctrl+C／EOF 转为 `CancelSelection`；`Completed/Failed/Paused/Cancelled` 结束当前内层循环并把控制权交还输入层。`Reject` 与 `CancelSelection` 都先写入对应 tool result，再进入 `WAITING_FOR_USER` 并返回 `Paused`；不得自动 `Continue` 或再次调用模型，下一条 `UserMessage` 才携带已记录结果继续当前 Agent。真正的运行取消使用全局 `Cancel` 并返回 `Cancelled`；活动 SubAgent 下仍保留 handoff。会返回 RuntimeEvent 的 CLI 命令（当前为 `/exit_sub`）使用 `CommandAction.DRIVE` 将事件交回 `CliApp`，不得只在 handler 内渲染后丢弃；这样直接退出产生的 `ToolFinished` 仍会继续驱动源 Agent。只有实际工具执行的技术／业务失败才以 `ToolFinished` 交回模型自修复。回合终点后调用 `Application.finalize_turn()`，独立尝试 snapshot 与可选 auto-memory；任一持久化失败都不覆盖原 RuntimeEvent。

审批策略属于 CLI 偏好：`/approval` 无参数时在 `prompt` 与 `auto` 间切换，使用 `/approval prompt|auto` 可显式设置；该策略只决定 `ApprovalRequested` 是否自动发送 `Approve`，不修改 ToolDefinition 或 Runtime 状态。`/auto-approve-switch` 不向前兼容。基础 Plan 表格在每次 Plan 工具变更后显示；持续驻留的 Sticky Plan 只有在 Renderer 独占终端生命周期后再加入。

`/ragreload` 与 `/build-memory` 在 R5 只进入 CommandRegistry 并明确报告 R6 尚不可用；R6 通过 `CommandRegistry.replace()` 接入真实 handler。R5 提供 `python -m src.get_me_in.cli` 独立入口；正式 CLI 通过 G5 后删除临时 `scripts/v2_runtime_smoke.py`，因此 R8 切换 `main.py` 前仍有唯一可验证的 v2 CLI 入口。

R5 新文件、对象与公开边界清单如下，已由用户在决策 154 中确认；编码只允许创建或调整清单明确列出的 R5 范围：

| 文件 | 新增对象 | 公开边界 |
|------|----------|----------|
| `src/get_me_in/cli/__init__.py` | v2 CLI package | 不导出可变全局实例 |
| `src/get_me_in/cli/app.py` | `CliApp` | `__init__(application, commands, input_controller, renderer, worker)`、`run() -> int`；内部持有审批模式并驱动 command/event，不暴露业务状态 |
| `src/get_me_in/cli/commands.py` | `ApprovalMode`、`CommandAction`、`CommandResult`、`CommandSpec`、`CommandRegistry` | `CommandRegistry(specs=())`、`register(spec) -> None`、`replace(spec) -> None`、`dispatch(text) -> CommandResult | None`、`help_entries() -> tuple[tuple[str, str], ...]`、`completions() -> tuple[str, ...]`、`build_command_registry(application, input_controller, renderer) -> CommandRegistry`；结果使用强类型 action，不返回魔法 dict |
| `src/get_me_in/cli/input.py` | `CompletionProvider`、`InputController` | `__init__(editor=None)`、`set_completions(provider: CompletionProvider) -> None`、`read(prefill=None) -> str | None`、`edit() -> str | None`、`confirm(prompt) -> bool | None`、`select(prompt, choices, allow_custom=False) -> str | None`、`remember(text) -> None`、`replace_history(entries) -> None` |
| `src/get_me_in/cli/renderer.py` | `Renderer` | `__init__(console=None)`、`render_event(event) -> None`、`render_session(view) -> None`、`render_help(entries) -> None`、`render_error(message) -> None`、`render_notice(message) -> None`、`status(message)`；不返回下一条 command |
| `src/get_me_in/cli/worker.py` | `WorkerRunner` | `__init__(application, renderer, poll_interval_seconds=0.1)`、`run(command: RuntimeCommand | ApplicationCommand) -> RuntimeEvent | ApplicationResult`、`close() -> None`；只管理单 worker、轮询和取消 |
| `src/get_me_in/cli/main.py` | CLI composition function | `main() -> int`；构造 Application 与 CLI 组件，按 worker → application 顺序关闭 |
| `src/get_me_in/cli/__main__.py` | 模块入口 | 只调用 `main()`，不含业务逻辑 |
| `tests/get_me_in/test_cli_app.py` | CliApp protocol tests | 覆盖事件推进、handoff continue、终态自动保存与保存失败 |
| `tests/get_me_in/test_cli_commands.py` | CommandRegistry tests | 覆盖 parse/help/alias/replace、restore/rewind、unavailable handler 与审批策略 |
| `tests/get_me_in/test_cli_worker.py` | WorkerRunner tests | 覆盖单 worker、取消、关闭与禁止并发 |

其中 `ApprovalMode` 只包含 `PROMPT/AUTO`；`CommandAction` 包含 `HANDLED/EXIT/SUBMIT/PREFILL/SET_APPROVAL/DRIVE`。`CommandResult` 由 `action`、可选 `text`、可选 `approval_mode` 和可选 `event` 组成：`SUBMIT` 用于 `/edit` 产生普通用户输入，`PREFILL` 用于 `/rewind` 回退后预填，`SET_APPROVAL` 只修改 CliApp 的进程内审批偏好，`DRIVE` 必须携带 RuntimeEvent 并交给 CliApp 的既有事件循环。`CommandSpec` 包含 `name/description/handler/aliases`，handler 接收命令参数文本并返回 `CommandResult`；非命令输入时 `dispatch()` 返回 `None`。`help_entries()` 与 `completions()` 都从当前注册表派生并按命令名排序；帮助单列 alias，避免显示与实际可补全命令不一致。`CompletionProvider = Callable[[], tuple[str, ...]]` 由 `InputController.set_completions()` 注入；CliApp 在装配时传入 `CommandRegistry.completions`，`read()` 每次打开输入框时读取 provider 的最新结果。InputController 不持有或依赖 CommandRegistry；未注入 provider 时使用空补全列表。

R5 复用既有 `build_application()`，不改变 `bootstrap.py` 的 Runtime/Session 装配边界；`cli/main.py` 负责 Settings 加载和 CLI 组件装配。R5 没有修改 RuntimeCommand、Session snapshot schema、ToolDefinition 或 R6/R7 service；为满足真实 CLI 展示与交互闭合，已显式扩展 `ToolStarted.arguments`、`ToolFinished.plan`、`SessionPreview.preview` 和 Reject 的终止语义，这些投影与转换分别由决策 158、162、163 约束。真实 questionary/Rich、Windows UTF-8、Esc、Ctrl+C、EOF 与 editor-not-found 仍使用人工 smoke 验证。

推荐实施顺序固定为：

1. `commands.py` 与 `test_cli_commands.py`：先固定强类型 command spec/result、解析、alias、replace 和核心 command handlers。
2. `input.py`、`renderer.py`：迁移纯终端输入/输出职责，不接 Application 私有状态。
3. `worker.py` 与 `test_cli_worker.py`：完成单 worker、轮询取消和关闭。
4. `app.py` 与 `test_cli_app.py`：完成 command/event 驱动、handoff continue、交互和终态自动 snapshot。
5. `main.py`、`__main__.py`：装配正式入口，执行自动化测试与人工 smoke；G5 通过后删除临时 Runner 并单独提交。

上述每一步独立验证并使用现有提交风格提交；不得在同一提交提前实现 R6 Knowledge handler 或 R7 Resume Agent。

### 6.8 Workspace 与 Artifact

WorkspacePort 提供 `resolve/read/list/search/write/edit/delete/move`；LocalWorkspace 统一：

- 使用 `Path.resolve()` + `Path.is_relative_to(root)` 校验边界。
- 使用 session-scoped revision 代替进程级 `_read_files`。
- revision grant 是运行期安全状态，不写入 SessionSnapshot；restore/rewind 后必须清除。
- 写入使用原子替换，错误统一为 domain error。
- 编码检测集中处理，不在每个 tool 重复。

Resume 的模板复制、LaTeX 编译和 PDF 产物记录属于 ArtifactService。用户记忆只保存事实/偏好，不承担简历文件版本管理。

### 6.9 Knowledge 与 Memory

本节保留 R6 当时已经确认并最终落地的设计边界，用于解释现有 Knowledge/Memory 实现；其中“本次会话”“后续新会话”和实施切片均为历史实施记录，不代表当前待办或授权状态。R6 复审结论是保留 Knowledge/Memory 的总体方向，但重新设计命令执行、会话输入、manifest 一致性和资源所有权。R6 只迁移当时已有的 Reference RAG、Memory 构建/查询/删除、`/ragreload`、`/build-memory` 与可配置的终态自动 Memory；未引入 R7 Resume Agent、Artifact schema 或其他新功能。

#### 6.9.1 新增、删除与修改

**新增：**

- 增加通用的前台 `ApplicationCommand` 执行路径。`CommandAction.RUN` 携带 application command，`WorkerRunner` 串行执行并返回强类型 `ApplicationResult`；`CliApp` 只负责调用 Renderer，不识别 Knowledge/Memory 私有状态。`/ragreload` 在 worker 中同步执行、可通过 `Application.request_cancel()` 取消；`/build-memory` 只排入受控后台队列并立即返回 receipt。
- 增加 `MemoryBuildSource`。`SessionService` 在 application 层复制当前 Agent 的 provider-neutral `ConversationRecord`，并把 assistant message/tool call 的 thinking 规范化为 `None`；CLI 和 Memory 后台任务均不得持有 `SessionState`、读取私有 history 或把展示摘要交给 MemoryExtractor。
- 增加 schema-versioned `IndexManifest` 和全新 v2 Memory repository。默认路径分别位于 `data/v2/knowledge/manifest.json`、`data/v2/knowledge/chroma/` 与 `data/v2/memories/`；不得读取旧 `data/chroma/` 或 `data/memories/`。
- 增加一个 Application-owned、非 daemon 的 `BackgroundWorker`，串行处理启动加载和 Memory 构建。KnowledgeService/MemoryService 只借用该 worker，不拥有或关闭它；后台任务使用自己的 cancellation，不与前台 Runtime command 共用可变 token。ResourceStack 必须先关闭 worker、等待或取消任务，再关闭 MemoryService/KnowledgeService 持有的 repository/index/model。
- 增加逆序、幂等、失败隔离的 `ResourceStack`。只注册顶层 owner，嵌套资源只由其直接 owner 关闭，禁止 LLM/index/repository 被重复注册和重复关闭。
- 增加 `Application.finalize_turn()`：终态依次尝试 snapshot 和按 `AUTO_MEMORY_ON_EXIT` 的 v2 typed setting 可选排入 Memory 构建；两项结果独立记录，snapshot 失败仍按旧行为继续尝试 auto-memory，任一失败都不得覆盖另一项结果或原 RuntimeEvent。

**删除／不再创建：**

- 删除原任务中的通用 `SearchQuery`／`SearchResult`；tool-facing 查询继续使用已经稳定的 `RetrievalPort`／`RetrievalResult`，index 内部只使用 `IndexHit`，避免两套公开搜索 DTO。
- 不迁移 v1 `RagLoader`、`start/is_ready/load/load_file/delete` Facade 形状，不创建第二个 Loader service；启动、查询、重载、单 source upsert/delete 均收敛到 `KnowledgeService`。
- 不创建 `MemoryService.search()`；`query_memory` 仍通过 `RetrievalPort` 查询 `memories` collection，MemoryService 只负责 build/delete 与 repository→index 一致性。
- 不保留 observer callback、延迟 import、模块级 singleton、daemon thread、`.last_update` 时间戳增量和 v1 Markdown Memory 兼容读取。
- R6 完成后删除临时 `DeferredRetrievalAdapter`；删除动作只能与真实 `KnowledgeService` 装配及 retrieval contract tests 同一切片完成，不能提前制造无 adapter 状态。

**修改：**

- `KnowledgeService` 直接实现 `RetrievalPort.search()`，并显式依赖一组 source repositories、document chunker、index port、manifest repository 与 cancellation；启动/全量 reload 同时扫描只读 reference repository 和全新 v2 memory repository。ToolDefinition、RetrievalPort 签名和 Runtime tool closure 不变。
- `MemoryExtractor` 使用专用 `LLMPort` 和静态 memory prompt；不创建旧 PromptLoader/LLMClient，不与活动 AgentRuntime 共享 cancellation。MemoryService 显式执行 `extract → repository.write → KnowledgeService.index_document`。
- `Application.close()` 改为只关闭 `ResourceStack` 并返回 `CloseReport`；CLI 在退出时显示 close error/timeout，但所有资源仍必须继续逆序关闭。
- `Settings` 增加 v2 index/memory 路径、embedding/rerank batch/top-k、shutdown timeout 与 auto-memory typed 配置；禁止 adapter 读取旧全局 config 或自行读取环境变量。
- 决策 149/153 中允许 R6/R7 并行的部分由决策 169 取代。R6 coding、G6、文档 checkpoint 全部完成后强制终止，不得创建、修改或确认任何 R7 文件、类、公开方法或代码。

#### 6.9.2 状态与一致性

`KnowledgeState` 使用 `IDLE/LOADING/READY/DEGRADED/ERROR/CLOSING/CLOSED`。首次启动尚无可用 index 时，`IDLE/LOADING/ERROR` 查询返回明确 `retrieval_unavailable`；`READY` 可查询；部分 source 失败时进入 `DEGRADED`，保留已提交 index 可查询并在 reload report 中列出失败项。`READY/DEGRADED` 还表示 embedding 与 reranker 权重均已由后台 startup reload 完成预热；manifest 无变化也不得跳过预热，首次用户查询不得承担模型构造。预热失败进入 `ERROR`，后续显式 reload 通过同一 `prepare → diff → mutation` 路径重试。并发 reload 不排队、不重入，返回 typed busy failure；search 与 index mutation 由 KnowledgeService 串行边界保护，不直接依赖 Chroma 的隐含线程安全。

Manifest 以规范化的 `collection + project-relative source path` 作为 source key，记录 `schema_version/source_key/collection/observed_hash/indexed_hash/mtime/chunk_ids/status/pending_operation/error`。内容 hash 是变化判定依据，mtime 仅作扫描优化。写入或删除前先原子保存 `PENDING`；index 成功后保存 `READY` 或移除已删除 entry；失败保存 `ERROR`，保留上一次 `indexed_hash/chunk_ids` 以支持幂等重试。重命名通过“旧路径消失 + 同 collection 同 hash 新路径出现”报告，但实际按可重试的 delete+upsert 执行，不依赖 Chroma 原子 rename。

Memory repository 每条记录使用独立、versioned JSON 文件。repository 写成功但 index 失败时，build report 必须返回 partial failure，manifest 保留 pending/error；不得报告“全部成功”。删除先写入 manifest delete intent，再删除 index，最后删除 repository 文件；中途失败保留可重试状态。MemoryExtractor 的输出只能包含 `fact/preference`，空白、未知 category 或无效 JSON 作为 typed extraction failure，不写 repository。

#### 6.9.3 R6 文件、对象与公开边界清单（已确认）

下表是 R6 唯一允许创建的新代码范围，已获用户明确确认。本次会话仍只更新文档并 checkpoint，不创建这些文件；后续新会话必须先执行 `/project-bootstrap`，再按实施切片逐步编码。

| 文件 | 新增对象 | 构造依赖与公开方法 |
|------|----------|--------------------|
| `src/get_me_in/domain/knowledge.py` | `KnowledgeCollection`、`KnowledgeState`、`ManifestStatus`、`PendingIndexOperation`、`KnowledgeSource`、`KnowledgeDocument`、`IndexChunk`、`IndexHit`、`ManifestEntry`、`IndexManifest`、`ReloadReport` | immutable DTO/StrEnum；无 I/O 方法 |
| `src/get_me_in/domain/memories.py` | `MemoryCategory`、`MemoryRecord`、`MemoryBuildSource`、`MemoryBuildReceipt`、`MemoryBuildReport` | versioned immutable DTO；`MemoryBuildSource` 只持有复制且 thinking 已规范化为 `None` 的 ConversationRecord |
| `src/get_me_in/application/app_results.py` | `ApplicationResult`、`BackgroundJobReceipt`、`KnowledgeReloaded`、`MemoryBuildScheduled`、`TurnFinalizationResult`、`CloseIssue`、`CloseReport` | strong typed result；不返回控制 dict |
| `src/get_me_in/application/background_worker.py` | `BackgroundWorker` | `__init__(name, shutdown_timeout_seconds)`、`submit(task_name, task) -> BackgroundJobReceipt`、`close() -> CloseReport`；单非 daemon worker，timeout 构造注入 |
| `src/get_me_in/application/resources.py` | `ResourceStack` | `register(name, close: Callable[[], CloseReport | None]) -> None`、`close() -> CloseReport`；显式注册唯一 owner 的 close callback，逆序、幂等、失败隔离 |
| `src/get_me_in/application/knowledge_service.py` | `KnowledgeService` | `__init__(sources: tuple[KnowledgeSourceRepository, ...], chunker, index, manifests, worker)`、`start() -> None`、`state`、现有 `RetrievalPort.search(...)`、`reload(target=None) -> ReloadReport`、`index_document(document) -> ReloadReport`、`delete_source(source_key) -> ReloadReport`、`request_cancel(reason) -> None`、`close() -> CloseReport`；worker 为 borrowed dependency，close 不关闭 worker |
| `src/get_me_in/application/memory_extractor.py` | `MemoryExtractor` | `__init__(llm, prompt, clock, id_generator, timeout_seconds)`、`extract(source, cancellation) -> tuple[MemoryRecord, ...]` |
| `src/get_me_in/application/memory_service.py` | `MemoryService` | `__init__(repository, extractor, knowledge, worker)`、`build_async(source) -> MemoryBuildReceipt`、`delete(memory_id) -> MemoryBuildReport`、`close() -> CloseReport`；KnowledgeService/worker 均为 borrowed dependency，close 只关闭自有 repository/extractor |
| `src/get_me_in/ports/knowledge.py` | `KnowledgeSourceRepository`、`DocumentChunker`、`KnowledgeIndexPort`、`ManifestRepository` | `scan/read`、`chunk`、`prepare/replace_source/delete_source/search/close`、`load/save/close`；`prepare(cancellation)` 只加载查询必需模型，不读写 index；全部为 Protocol |
| `src/get_me_in/ports/memories.py` | `MemoryRepository` | `write(record) -> KnowledgeDocument`、`get(memory_id)`、`list(agent=None)`、`delete(memory_id)`、`close()`；具体 adapter 还需实现 KnowledgeSourceRepository 供重启重建 index |
| `src/get_me_in/adapters/local_knowledge_sources.py` | `LocalKnowledgeSourceRepository` | `__init__(reference_root)`、`scan(target=None)`、`read(source)`；只允许 reference_root 下 Markdown |
| `src/get_me_in/adapters/markdown_chunker.py` | `MarkdownChunker` | `chunk(document) -> tuple[IndexChunk, ...]`；chunk id 对 source key、content hash 和序号确定性生成 |
| `src/get_me_in/adapters/json_manifest_repository.py` | `JsonManifestRepository` | `__init__(path)`、`load()`、`save(manifest)`、`close()`；schema 校验与原子替换 |
| `src/get_me_in/adapters/chroma_knowledge_index.py` | `SentenceTransformerEmbedder`、`CrossEncoderReranker`、`ChromaKnowledgeIndex` | 模型名、batch/top-k、persist path 全部构造注入；`prepare()` 幂等预热 embedding 与 reranker；index 实现 KnowledgeIndexPort，不读取全局 config |
| `src/get_me_in/adapters/json_memory_repository.py` | `JsonMemoryRepository` | `__init__(root, clock)`，同时实现 MemoryRepository 与 KnowledgeSourceRepository 的 `scan/read`；只读写全新 v2 JSON，使应用重启或 index 重建时可显式恢复 memories collection |
| `tests/get_me_in/test_knowledge_service.py` | Knowledge service contract tests | manifest diff、busy/state、增删改名、失败重试、取消与 close |
| `tests/get_me_in/test_memory_service.py` | Memory service contract tests | immutable source、extract/write/index、partial failure、delete retry、后台关闭 |
| `tests/get_me_in/test_resources.py` | Resource lifecycle tests | 逆序、幂等、异常隔离、timeout report |
| `tests/get_me_in/test_knowledge_adapters.py` | adapter contract tests | JSON schema/atomicity、path boundary、deterministic chunk ids；真实模型/Chroma 仍走 integration smoke |

允许修改的既有文件仅为 `application/settings.py`、`application/app_commands.py`、`application/application.py`、`application/session_service.py`、`bootstrap.py`、`cli/app.py`、`cli/commands.py`、`cli/worker.py`、`cli/renderer.py`、`cli/main.py`、`tools/retrieval.py`、对应既有测试和 R6 文档。`RuntimeCommand`、`RuntimeEvent`、AgentRuntime、Session snapshot schema、ToolDefinition、R7 文件和旧 `main.py` 均不在 R6 修改范围。

#### 6.9.4 实施与终止门禁

R6 固定按以下切片实施，每个切片独立验证、独立提交：domain/ports/manifest diff → ResourceStack 与 application command worker path → KnowledgeService fake-index contract → 本地 source/manifest/chunker/Chroma adapters → MemoryExtractor/MemoryService/background worker → Settings/bootstrap/CLI 接入与 DeferredRetrievalAdapter 删除 → G6 integration/smoke。

新会话的第一切片范围固定为 `src/get_me_in/domain/knowledge.py`、`src/get_me_in/domain/memories.py`、`src/get_me_in/ports/knowledge.py`、`src/get_me_in/ports/memories.py` 与 `tests/get_me_in/test_knowledge_service.py`，只实现 domain/ports/manifest diff 纯逻辑。该切片验证并独立提交前，不得创建清单中的其他 R6 文件；不得借 R6 授权修改 R7 文件或旧 `main.py`。

**R6-T 强制终止门禁：** G6 通过后，只允许整理验收证据并执行 `/project-checkpoint`，把 `docs/current.md` 保存为“R6 完成、R7 未启动、等待用户审查”。随后必须停止；未经用户在后续指令中明确确认，不得提交 R7 设计清单、创建 R7 文件、修改 R7 代码、切换入口或执行 R8 清理。

#### 6.9.5 R6-F 审查修复边界（已确认）

R6-T 代码审查发现启动、取消、索引一致性、后台失败可见性和资源关闭尚未闭合，因此撤销决策 174 中“G6 已通过”的结论，R7 继续保持未授权。用户已确认 R6-F 只修复 R6 既有边界，不创建或修改 R7 文件、不切换旧 `main.py`、不执行 R8 清理。

- `KnowledgeService.start()` 由 Application-owned `BackgroundWorker` 排入启动加载；加载完成前查询明确返回 `retrieval_unavailable`。`Application.request_cancel()` 可取消当前前台 reload，Runtime cancellation 与后台 Memory cancellation 彼此独立。
- `KnowledgeService.search()`、`reload()`、`index_document()` 与 `delete_source()` 共用显式串行边界；search 遇到正在执行的 mutation 时快速返回 busy/unavailable，不依赖 Chroma 的隐含线程安全。
- Chroma replace 必须先完成 embedding，再写入新 chunk；失败时清理本次新 chunk 并保留旧 chunk，成功后才删除旧 chunk id。删除只忽略明确的 collection-not-found，其他异常必须上抛并保留 manifest retry 状态。
- `BackgroundWorker` 的 task callback 改为接收独立 `CancellationSignal`，并保存 typed job result。新增 `BackgroundJobState`、`BackgroundJobResult` 与 `result(job_id) -> BackgroundJobResult | None`；`/build-memory` 仍立即返回 receipt，本轮不增加新的 CLI 查询命令。
- `MemoryService` 后台 build 返回 `MemoryBuildReport`，不得忽略 repository 成功、index 失败或 busy。`KnowledgeService.delete_source(..., finalize=...)` 先写 manifest delete intent，再删除 index，调用 Memory repository finalize，最后提交 manifest；任一步失败均保留可重试状态。
- `BackgroundWorker.close()` 必须拒绝新任务、取消排队及当前任务并有界等待；若任务仍未停止，ResourceStack 不得继续关闭其仍在使用的 Knowledge/Memory 依赖，只返回 typed timeout issue。MemoryService/KnowledgeService 内部资源关闭同样失败隔离。
- MemoryExtractor 使用静态 memory prompt，不在 composition root 硬编码 prompt 文本；优先复用 `data/prompts/` 既有资产，若缺失则只新增对应静态 prompt 文件。
- 所有创建 Application 的自动化测试必须注册 close cleanup；新增启动加载、reload 取消、search/mutation 竞争、Chroma replace rollback、delete error、Memory partial failure/delete retry、worker timeout 与测试进程正常退出覆盖。

R6-F 允许修改 R6 已确认文件及其对应测试，并允许在 `application/app_results.py` 增加上述两个 typed job result DTO；不新增 service/module 文件。修复按“启动／取消／串行边界 → Chroma 可恢复写入 → BackgroundWorker 与 Memory 一致性 → bootstrap/cleanup/完整回归与真实 smoke”四个独立切片提交。全部通过后重新执行 G6 和 checkpoint，仍须停在 R6-T 等待用户审查。

**实现结论：** 上述边界已按四个切片落地并通过 187 项自动化测试、`compileall` 与真实 Chroma/embedder/reranker smoke。worker 改为首次提交时延迟启动；若关闭超时，ResourceStack 停止关闭仍可能被后台任务使用的下游依赖。Settings 默认模型恢复为项目既有 BAAI 基线，同时通过 typed Settings 兼容旧环境变量名。G6 已重新通过并曾停在 R6-T；决策 177 已在后续会话授权 R7 总体边界 Review。

### 6.10 Resume 与 Artifact（R7）

本节保留 R7 当时已经确认并最终落地的设计边界，用于解释现有 Resume/Artifact 实现；其中“当前 composition root”“本次会话”“后续新会话”和实施切片均按 R7 当时状态阅读，不代表当前待办或授权状态。R7 启动前 Review 的总体边界与新文件、对象、公开方法清单均已获用户确认；后续补充 Review 又确认恢复旧决策 117 的 temperature 行为，并固定 Artifact build log 的有界持久化策略。

#### 6.10.1 R7-P0：LLM temperature 契约修复

旧决策 117 固定 Main `temperature=0.1`、Resume `temperature=0.2`、MemoryBuilder `temperature=0`，但当前 v2 `AgentSpec`／`LLMRequest` 没有 temperature，OpenAI adapter 实际依赖 provider 默认值。R7 引入真实 Resume Runtime 前必须先恢复该行为等价：

- `AgentSpec` 增加显式 `temperature: float`；Main 固定 0.1，Resume 固定 0.2。
- `LLMRequest` 增加 `temperature: float | None = None`；AgentRuntime 从 AgentSpec 传入，MemoryExtractor 显式传入 0.0。
- OpenAI adapter 仅在 request temperature 非 `None` 时传给 provider，不在 adapter 层设置隐藏默认值。
- temperature 必须是有限数且位于 `[0, 2]`；非法值在 domain/application 边界拒绝，不发 provider 请求。
- 不恢复开放 `**kwargs` 或 provider-specific options dict；本切片只修复 temperature 一个已确认契约。

该修复独立验证、独立提交，完成前不得开始 dynamic session identity 或创建 R7 新文件。

#### 6.10.2 R7-P：动态 session identity

当前 composition root 在创建 `ToolContext` 时捕获初始 `session_id`，但 `SessionService.restore()` 会替换规范 `SessionState`。连续恢复多个 snapshot 后，固定 id 可能使 Workspace read-before-edit grant 仍写入旧 scope，也无法为 Artifact 提供可信的当前会话 provenance。

R7 coding 的第一切片必须先修复此边界：

- `SessionState` 继续是 session id 的唯一长期事实来源；禁止新增可变全局变量、CLI 私有读取或第二份长期 session-id 镜像。
- `AgentRuntime.advance(state, command, *, session_id)` 在单次转换期间接收当前 session id；`Orchestrator` 从传入的 `SessionState` 提供该值。
- Runtime 执行工具时以当前 session id 替换其 immutable `ToolContext` 模板中的 scope；该临时值不跨 `advance()` 保存。
- `restore`／`rewind` 清除离开的真实 session scope；连续恢复不同 snapshot 后，旧 revision grant 不得授权当前 Session 的 edit。
- Resume Artifact 操作从同一动态 `ToolContext` 取得 `session_id` 与 `AgentKey.RESUME`，使 workspace 授权和 artifact provenance 使用同一规范身份。

#### 6.10.3 Resume Agent 与资源所有权

Resume 使用 immutable `AgentSpec`，不创建只用于复刻旧 14 个 `_get_*()` 方法的 stateful Agent 类。为达到当前 ResumeAgent 行为等价，capability 固定为：

`system`、`plan`、`interaction`、`web.search`、`external_file.read`、`return_to_main`、`workspace.read`、`workspace.write`、`workspace.open`、`resume.artifact`、`knowledge.query`。

Resume 不获得 `route`，不能调度其他子 Agent。Main 仍只通过 `AgentCatalog` 的公开 descriptor 发现 Resume，Hub-and-Spoke、handoff call-id 闭合与 `/exit_sub` 协议不变。

Main/Resume 分别拥有 `AgentRuntime`、`CancellationToken`、`PlanService` 和 agent-scoped `ToolContext`。生产 composition root 为两个 Runtime 创建不同的 `LLMPort` 实例；测试注入也必须按 `AgentKey` 提供互不相同的实例。每个 Runtime 只关闭自己的 LLM，共享的 Workspace、Frontend、WebSearch、Knowledge 和 Artifact service 只由 `ResourceStack` 中的唯一 owner 关闭。

Session 初始化时同时创建 Main/Resume 两份 `AgentSessionState` 与 PlanService；restore 继续拒绝当前 Application 未装配的 Agent。R7 不改变 RuntimeCommand、RuntimeEvent、HandoffFrame 或 SessionSnapshot schema。

#### 6.10.4 Artifact schema 与一致性

Artifact 使用全新 `data/v2/artifacts/` versioned repository，不读取旧 Session、Memory、Chroma 或 `data/temp/`。Artifact 只记录工作区产物和编译尝试，不写入 Memory；默认不向 SessionSnapshot 增加 ArtifactRef。save/restore/rewind 只恢复对话与 Agent 状态，不删除、覆盖或回滚工作区文件和 Artifact 记录。

ArtifactService 是工具侧 `ResumeArtifactPort` 的正式实现，并借用低层 `ResumeArtifactBackend` 完成静态模板读取、`pdflatex` 调用和 PDF 合并；这样 application service 不直接 import `shutil`、`pypdf`、文件系统 adapter 或 subprocess。`copy_template`／`build_pdf` 的 LLM 参数 schema 和 ToolOutcome/Runtime 闭合协议保持不变；决策 210 另行增加 Resume-only `merge_pdfs`。

Artifact repository 使用 deterministic operation key 和两阶段记录：

1. 在文件副作用前原子保存 `PENDING` operation；key 至少包含 session、Agent、operation kind、规范化路径和输入 revision/hash。
2. 文件操作完成后原子提交 artifact/build-attempt 结果；若最终 metadata 提交失败，原 `PENDING` 仍可用于下一次调用 reconcile。

`copy_template` 先预检模板、目标 LaTeX 与 README。`.tex` 继续拒绝覆盖不同内容；README 保留 v1 的跟随复制和可覆盖行为并产生新版本。若前次 partial operation 已写入与模板完全一致的目标文件，retry 可以依据 pending intent 补齐记录，不把它误判为普通覆盖。

`build_pdf` 记录成功、非零退出、超时、取消和异常尝试。只有 `exit_code == 0` 且 workspace 中目标 PDF 确实存在时才创建可用 PDF Artifact；stdout/stderr 属于 typed build-attempt record。文件已经写入或 PDF 已生成但 metadata 未提交时，工具返回明确的 typed partial failure 和已改变路径，不得报告全部成功。

`merge_pdfs(first, second, output)` 接受工作区相对路径并允许省略 `.pdf` 后缀，按 first → second 顺序拼接全部页面。低层 `LocalResumeArtifacts` 通过 `WorkspacePort.resolve()` 取得受限绝对路径，验证两个源文件存在、互不相同且输出不覆盖源文件，再以同目录临时文件和 `os.replace()` 原子提交；handler 和 ArtifactService 不直接读写二进制文件。operation key 包含两个源 PDF 的路径与原始字节 hash，输出 PDF Artifact 记录 `content_hash`、version 与 `page_count`，COMMITTED replay 不重复写文件。文件已生成但 metadata 提交失败时继续返回 `ArtifactPartialFailure` 和输出路径。

Artifact schema 从 `schema_version=1` 开始。工作区产物保存 `content_hash`；静态模板来源使用 `template_name`，不得保存工作区外绝对路径。operation key 是 canonical JSON 的 SHA-256，输入固定包含 schema version、session id、AgentKey、operation kind、规范化参数、workspace-relative path 与输入 revision/hash。

build attempt 的 stdout/stderr 在替换 workspace 绝对根路径为 `<workspace>/` 后按 UTF-8 bytes 分别限制为 `artifact_log_max_bytes`，默认 65536。发生截断时各保留头尾两段（默认各 32768 bytes，并在 UTF-8 字符边界解码），同时记录 original bytes 与 truncated flag；不能因日志截断改变 process exit/cancel/timeout 语义。

`ArtifactPartialFailure` 保留 typed `code/changed_paths/message`，由 resume tool 映射为既有 `ToolFailure("artifact_partial_failure", ...)`；不扩展 ToolOutcome schema。pending operation 只在匹配的后续调用中 lazy reconcile，不增加启动 daemon、Artifact CLI 命令或自动扫描。R7 不提供 Artifact 清理／保留期；全部 operation 继续保留，统一留到 R9 评估。

#### 6.10.5 R7 新文件、对象与公开边界清单（已确认）

下表是 R7 唯一允许创建的新代码范围，已获用户确认。

| 文件 | 新增对象 | 构造依赖与公开方法 |
|------|----------|--------------------|
| `src/get_me_in/agents/__init__.py` | package marker | 不导出运行时单例，不执行注册 |
| `src/get_me_in/agents/resume.py` | Resume AgentSpec factory | `build_resume_spec() -> AgentSpec` |
| `src/get_me_in/domain/artifacts.py` | `ArtifactKind`、`ArtifactOperationKind`、`ArtifactOperationStatus`、`Artifact`、`ArtifactBuildAttempt`、`ArtifactOperation` | `schema_version=1` immutable DTO/StrEnum；Artifact 显式保存 `content_hash`／`template_name`，build attempt 保存有界日志、原始 bytes 与 truncated flags；路径只保存 workspace-relative 形式，不含 I/O 方法或开放 metadata dict |
| `src/get_me_in/ports/artifacts.py` | `ArtifactRepository` | `get_operation(operation_key)`、`save_operation(operation)`、`next_version(path)`、`list_artifacts(path=None)`、`list_build_attempts(source_path=None)`、`close()` |
| `src/get_me_in/application/artifact_service.py` | `ArtifactService`、`ArtifactPartialFailure` | `__init__(backend, repository, clock, id_generator, log_max_bytes)`、`copy_template(..., session_id, agent_key, workspace) -> TemplateCopyResult`、`build_pdf(..., session_id, agent_key, workspace, cancellation) -> ProcessResult`、`close()`；直接实现 `ResumeArtifactPort` |
| `src/get_me_in/adapters/json_artifact_repository.py` | `JsonArtifactRepository` | `__init__(root)`；实现 ArtifactRepository，逐 operation versioned JSON、schema 校验、原子 replace、损坏记录 typed failure |
| `tests/get_me_in/test_resume_agent.py` | Resume spec/composition contract tests | capability、Prompt 可见性、双 Runtime/LLM ownership、main→resume→main、取消/失败/restore |
| `tests/get_me_in/test_artifact_service.py` | Artifact service contract tests | copy/build、version、pending reconcile、partial failure、非零退出/超时/取消、PDF existence |
| `tests/get_me_in/test_artifact_repository.py` | JSON repository contract tests | schema、atomicity、operation key、list/filter、损坏记录与幂等 close |

`src/get_me_in/ports/resume_artifacts.py` 增加低层 `ResumeArtifactBackend`，并为 tool-facing `ResumeArtifactPort.copy_template()`／`build_pdf()` 增加 keyword-only `session_id` 与 `agent_key` provenance；`LocalResumeArtifacts` 改为实现 backend，继续封装静态模板、`shutil.which()` 与 ProcessRunner，不负责持久化。

决策 210 是用户在 R8-O 观察期明确授权的窄扩展：在上述既有文件中增加 immutable `PdfMergeResult`、`ResumeArtifactPort.merge_pdfs()`、`ResumeArtifactBackend.merge_pdfs()`、`ArtifactService.merge_pdfs()` 与 `ArtifactOperationKind.MERGE_PDFS`，并为 `Artifact` 增加可选 `page_count`。不新增模块、CLI 命令、capability、通用二进制 Workspace API 或 Main 工具权限。

允许修改的既有文件仅为：

- `src/get_me_in/domain/agents.py`、`ports/llm.py`、`adapters/openai_llm.py`、`application/memory_extractor.py`
- `src/get_me_in/application/runtime.py`、`application/orchestration.py`、`application/tool_executor.py`、`application/application.py`、`application/session_service.py`、`application/settings.py`
- `src/get_me_in/ports/resume_artifacts.py`、`adapters/local_resume_artifacts.py`、`tools/resume.py`、`bootstrap.py`、`.env.example`
- 对应既有测试与 R7 文档

公开签名调整固定为：

- `AgentSpec` 增加 `temperature: float`
- `LLMRequest` 增加 `temperature: float | None = None`
- `AgentRuntime.advance(state, command, *, session_id: str) -> RuntimeTransition`
- `build_application(settings, *, runtime_llms: Mapping[AgentKey, LLMPort] | None = None) -> Application`；提供映射时必须覆盖 Main/Resume 且实例互不相同
- `Application.__init__()` 删除只代表 Main 的 `runtime`／`cancellation` 参数和公开 `cancellation` 属性；跨线程取消继续只允许 `request_cancel()`
- `Settings` 增加 `artifacts_dir`、`pdf_build_timeout_seconds` 与 `artifact_log_max_bytes`，分别默认 `data/v2/artifacts/`、60 秒与 65536 bytes；环境变量为 `PDF_BUILD_TIMEOUT_SECONDS`／`ARTIFACT_LOG_MAX_BYTES`
- `LocalResumeArtifacts.__init__(template_dir, process_runner, build_timeout_seconds)`

R7 不新增 CLI 命令，不改变 25 个 ToolDefinition 名称或参数 schema，不新增 Artifact 查询工具，不修改 SessionSnapshot schema，不迁移旧运行数据。

#### 6.10.6 实施与终止门禁

R7 固定按七个切片实施，每个切片独立验证、独立提交：

1. R7-P0 temperature contract：AgentSpec／LLMRequest／OpenAI adapter／MemoryExtractor 与对应测试。
2. R7-P dynamic session identity 与跨 restore 隔离测试。
3. Resume AgentSpec、capability、双 Runtime composition 与 handoff contract tests。
4. Artifact domain／port／JSON repository 与 schema/atomicity tests。
5. ArtifactService、ResumeArtifactPort 替换、copy/build partial-failure/log-bound tests。
6. Settings/bootstrap/resource ownership 接入与完整自动化回归。
7. 中文、英文、双语真实 Resume smoke 与 G7 checkpoint。

6.10.5 清单及后续 temperature/log 补充均已获得用户确认。当前会话按用户要求只执行文档 checkpoint，不编码；后续新会话执行 `/project-bootstrap` 后只能从切片 1 R7-P0 开始。G7 通过后仍须 checkpoint 并停下；未经用户后续确认，不得切换旧 `main.py` 或进入 R8 遗留删除。

### 6.11 入口切换、观察、遗留删除与文档归一化（R8，已完成）

R8 没有新增未授权业务能力，其公开协议调整仅来自 R8-O 真实 smoke 中经独立授权的最小修复。R8-P、R8-E、R8-O、R8-D、R8-G、完整 G8 与最终用户审查均已完成；决策 239 记录 G8 完成证据，决策 240 记录最终审查，决策 241 收口本轮文档一致性修复。当前继续停在 R9 独立授权门禁前。

#### 6.11.1 强制前置门禁

- R7-T2 必须先闭合 exception retry 一致性、Artifact aggregate 完整校验与 composition root 构造失败清理；重新运行完整自动化测试、`compileall`、`git diff --check` 和针对性 Artifact／composition smoke，并恢复 G7。
- 入口切换前重新确认 G6、G7 均有效，工作区干净，`main.py` 仍是唯一生产入口；不得把 `python -m src.get_me_in.cli` 当作已经完成生产切换。
- R8 不迁移、不覆盖也不删除 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 等旧用户运行数据。只验证 v2 不读取这些目录，并在文档中说明它们属于未迁移的历史数据。

#### 6.11.2 文件、对象与公开边界

入口切换切片允许修改：

- `main.py`：唯一行为改动是委托 `src.get_me_in.cli.main.main()` 并以其整数返回值作为进程退出码；删除全部 legacy import、import-time tool registration 与旧 composition。
- `src/get_me_in/cli/main.py`：修正已经过时的“未改变 legacy entry point”说明，并在 `Settings` 已加载、composition／CLI 构造或启动失败时记录完整诊断、向用户渲染简短错误并返回退出码 `1`；只捕获 `Exception`，不得吞掉 `KeyboardInterrupt`／`SystemExit`。既有 `SettingsValidationError` 继续返回 `2`，正常关闭继续返回 `0`；不增加第二套入口或公开 API。
- `.env.example`：R8-G 已删除观察期与 legacy-only 示例，保留 `Settings.from_env()` 的 v2 正式变量、默认值和仍支持的 Knowledge 兼容别名。
- `README.md`：R8-G 已将过渡说明归一化为已落地 v2 事实，记录唯一生产入口、诊断入口、当前能力、命令、配置、数据边界和回退顺序。
- `tests/get_me_in/test_import_boundaries.py`、`tests/get_me_in/test_settings.py`、既有 CLI/bootstrap 测试及新测试文件 `tests/get_me_in/test_cli_main.py`：覆盖根入口只依赖 v2、示例配置与 Settings 对齐、Settings 错误 `2`、composition／启动错误 `1` 且不输出 traceback、正常关闭 `0` 与资源关闭路径。新测试文件只测试既有入口函数；原则上不新增生产文件、类或公开方法。
- `pyproject.toml` 不新增 `[project.scripts]` 或其他生产入口；R8 继续以根 `main.py` 为唯一生产入口，以 `python -m src.get_me_in.cli` 为诊断／预览入口。

遗留删除切片的精确生产源码范围：

- 删除 `src/agents/`、`src/cli/`、`src/llm/`、`src/memory/`、`src/prompts/`、`src/rag/`、`src/tools/`、`src/utils/`。
- 删除 `src/config.py`、`src/lifecycle.py`、`src/logger.py`、`src/message.py`、`src/request.py`、`src/response.py`。
- 保留 `src/__init__.py` 与完整 `src/get_me_in/`；不得把 v2 CLI、adapter、port 或 tests 误归为 legacy。
- 删除仓库中的 `.ipynb_checkpoints` 目录，但必须先用精确路径复核；不得借此递归清理工作区或任何 `data/` 目录。
- R8-D 执行前复核的本地路径为 `.ipynb_checkpoints/`、`src/.ipynb_checkpoints/`、`src/llm/.ipynb_checkpoints/`，均未被 Git 跟踪；现已按精确 literal path 清理，并只作为本地证据记录，没有伪装成版本提交内容。
- `pyproject.toml`／`uv.lock` 只删除经 import 与真实 smoke 证明不再使用的依赖，不凭旧模块删除猜测依赖；若无可删项则保持不变。

R8 不新建 runtime class、service、port、schema 或公开方法。若实现中发现必须增加上述对象，必须停止并重新提交清单。

#### 6.11.3 五个独立切片与回退点

1. **R8-P 准备：** 完成静态资产、配置、capability、命令、Agent/tool 数量、v2→legacy import 和 legacy data 非访问审计；只更新过渡态 `.env.example`、README 与验证证据，不切入口、不删除 legacy rollback 配置。
2. **R8-E 入口切换：** 切换根 `main.py`，补齐 `cli.main` 启动异常映射和入口 contract tests，形成独立 commit。该 commit 是删除前的明确回退点。
3. **R8-O 观察门禁：** 从 `uv run python main.py` 执行完整 smoke matrix，验证启动错误无 traceback、基础对话、命令、审批／取消、Main→Resume→Main、save/restore/rewind、Knowledge/Memory、Resume copy/edit/build/open 与关闭。未通过时用 `git revert <R8-E commit>` 回退，不使用破坏性 reset；R8-P 保留的 legacy rollback 配置使旧入口仍可启动。
4. **R8-D 遗留删除：** R8-O 经用户审查通过后，由 `7514af3` 精确删除 legacy 源码，3 个 checkpoint 目录作为本地清理证据；import/dependency、Catalog、入口和 legacy-data refusal 验证均已完成，旧运行数据未删除。
5. **R8-G 文档与 G8：** `.env.example`／README 的 legacy rollback 段已删除，活跃文档与 AGENTS.md 已同步为已落地 v2 事实；完整 G8、独立缺陷分流、最终 checkpoint 和用户审查均已完成。历史 smoke/capability 内容已由决策 228 收敛到四份主文档并通过 Git 保留，旧 `/auto-approve-switch` 没有被改写成当前命令。

#### 6.11.4 R8-O／G8 证据要求

- 自动化：完整 unittest、`compileall`、`git diff --check`、根入口 import boundary；当前固定验收 Catalog 为 2 个 Agent（Main／Resume）、26 个 ToolDefinition、10 个 CLI 命令（`/help`、`/edit`、`/dump`、`/restore`、`/rewind`、`/ragreload`、`/build-memory`、`/exit_sub`、`/approval`、`/exit`）。数量与名称分别从 `AgentCatalog`、`ToolCatalog.export_descriptors()`、`CommandRegistry.help_entries()`／`completions()` 派生，不手工维护第二份运行时注册表。25-tool 是 R3/R7/R8-E 的历史验收值；决策 210 后当前值为 26。
- 真实 adapter：Chroma/embedder/reranker reload/query、Memory build/query/delete、中文／英文／双语 Resume copy/edit/build/open，且进程结束后后台 worker 与资源正常关闭。
- 数据边界：只复用 `data/reference/`、`data/prompts/`、`data/resume/template/`；v2 写入仅落在显式的 `data/workspace/` 与 `data/v2/` 边界。旧运行数据只保留，当前及未来 production、测试和 smoke 均不得读取其内容、迁移、改写或删除。决策 206 的一次性测试迁移是已经结束的历史特例，不构成持续权限，也不得重做。当前证明 production “未访问”只组合使用 v2 源码／Settings 静态扫描、sentinel project root 路径断言和拒绝访问旧目录的测试边界；不得通过重新读取旧文件内容或计算内容 hash 建立新证据。
- 删除后：`main.py` 与 `src/get_me_in/` 不得 import legacy；仓库不再包含列出的 legacy production modules 或 `.ipynb_checkpoints`；文档中的 Agent、tool、command 和配置数量必须与实际 Catalog／Settings 一致。
- 回退：当前 R8 完成态若需回退，先按逆提交顺序 revert R8-G 及其后续文档 checkpoint，再 revert `7514af3`，最后 revert `9fbeabc`。只有 legacy 源码恢复后才允许实际启用 legacy-only 配置；任何回退都不得读取、迁移、改写或删除旧 `data/` 运行数据。

#### 6.11.5 R8-G 已完成边界与失败分流记录

- **授权与结果：** 决策 230 确认清单，决策 231 授权实施；R8-G、G8、最终 checkpoint 和用户审查现均已完成。
- **文件白名单：** R8-G 文档／配置提交只修改了 `.env.example`、`README.md`、`AGENTS.md`、`docs/current.md`、`docs/design.md`、`docs/plan.md`、`docs/task.md` 与 `docs/decision.md`。G8 发现的测试与 production adapter 缺陷均先停止，经独立授权、修复和提交后才恢复验证，没有混入 R8-G 文档提交。
- **配置与文档：** 已删除仅供旧入口回退的示例变量和观察期说明，保留 v2 正式变量及其兼容别名；README 和活跃文档以实际 Catalog、Registry、Settings 与数据目录为准。`docs/decision.md` 只追加完成决策，不改写历史。
- **G8：** 完整自动化、静态边界、2 Agent／26 Tool／10 command Catalog、根入口 CLI／handoff／审批／取消、真实 Chroma／Knowledge／Memory、中文／英文／双语 Resume 与 PDF merge、legacy-data 拒绝访问、写入边界和资源关闭验证均已完成。
- **失败分流：** Settings 测试断言和 Windows SubprocessRunner 缺陷分别按决策 234～237 停止、授权、独立修复并提交；该流程继续作为未来文档验收发现产品缺陷时的稳定边界。
- **提交与停止：** 决策 239 完成 R8-G/G8，决策 240 完成最终用户审查；当前仍不得自动进入 R9。

### 6.12 InterviewAgent Workflow 前置备忘（R9，非确认清单）

本节只记录 R9 未来设计时不得遗忘的兼容性结论、阻塞点和优化方向，不构成 InterviewAgent 的实现授权，也不构成新文件、类或公开方法清单。R9 启动时仍须基于 R8 后的实际代码重新 Review，并由用户确认具体边界。

#### 6.12.1 与现有架构的兼容性结论

Workflow 与当前项目的 Hub-and-Spoke 架构并不冲突。Hub-and-Spoke 约束的是 Agent 间拓扑：Main 是唯一调度中心，子 Agent 不直接调用其他子 Agent；ReAct 或 Workflow 属于单个 Agent 内部的执行策略。InterviewAgent 可以作为一个 spoke 使用确定性 Workflow，只要继续遵守：

- 由 Orchestrator 统一开始和闭合 main → interview → main handoff；
- `SessionState` 继续是全部长期运行状态的唯一规范所有者；
- 对 CLI 继续使用强类型 command/event，不恢复 Request/Response、UIBridge 或魔法控制 dict；
- 工具与外部能力继续经过 capability、port 和 service，不由 workflow node 直接访问 CLI、SDK、文件系统或全局对象；
- workflow 内部的 question generation、answer evaluation 等步骤不是可互相 handoff 的“子 Agent”。若确实需要其他 Agent，必须先返回 Main，再由 Main 发起新的路由。

推荐采用“确定性 Workflow 外壳 + 节点内 LLM”：由代码固定阶段、分支、循环、终止和恢复规则；LLM 只承担生成问题、评估回答、生成追问与总结等开放任务。不要为了实现 Workflow 引入第二套 Application、Session、CLI loop 或通用 Agent 网络。

#### 6.12.2 R9 已知阻塞点

1. **Executor 具体类型耦合：** 当前 Orchestrator 的 runtime map 直接声明为 `Mapping[AgentKey, AgentRuntime]`，composition root 也默认所有 Agent 使用同一种 ReAct `AgentRuntime`；Workflow executor 尚不能作为正式可替换实现注入。
2. **状态形状偏向 ReAct：** 当前 `RuntimeTransition` 固定返回 `AgentSessionState`，后者直接包含 `RuntimePhase`、history、model call、pending tool、repair 与 Plan。Interview workflow 还需要 workflow version、稳定 step id、当前问题、收集的回答、评分进度和等待原因，不能塞入开放 metadata dict、Plan 或 runtime 私有字段。
3. **Snapshot schema 单一：** 当前 `SessionSnapshotCodec` 只编码一种 `AgentSessionState`。Workflow 若要支持 save/restore/rewind，必须有 tagged、versioned、可校验的持久化形状，并明确旧 ReAct snapshot 的兼容或迁移策略。
4. **“等待下一次用户输入”语义未定：** 当前 `Completed` 结束 CLI 内层循环并触发 finalize/snapshot。面试每问一答可能需要“本轮结束但 workflow 未结束”；R9 必须决定复用 `Completed` 的 turn-terminal 语义，还是增加显式 `AwaitingUserInput` 一类事件，不能用提示文本或 phase 字符串猜测。
5. **取消与副作用恢复未定义：** 需要区分取消当前 LLM/node、暂停整场面试和结束面试；restore/rewind 不得自动重放已完成的评分、报告写入或其他外部副作用。
6. **结果归属未定义：** 面试进度属于 Session；最终报告、逐题评分和原始回答是否进入 Artifact repository、专用 repository 或仅保留在 Session 尚待决定。Memory 仍只保存经确认的 fact/preference，不能默认成为面试记录数据库。
7. **隐私与保留期未定义：** 原始回答、评分与反馈可能包含敏感求职信息；R9 必须明确持久化范围、日志脱敏、删除入口和 retention，再决定是否长期保存。
8. **外部 Workflow 框架边界：** “Workflow”是控制流设计，不等于必须采用 LangGraph/LangChain 等框架。当前自研轻量框架决策仍有效；若未来希望引入外部 workflow engine，必须单独重开依赖与架构决策。

#### 6.12.3 推荐调整与优化方向

- 把 Orchestrator 依赖从具体 `AgentRuntime` 收敛为最小 typed executor protocol；候选能力为单步 `advance(...) -> RuntimeTransition`、跨线程 `request_cancel()` 与幂等 `close()`。最终命名和签名须在 R9 清单确认时固定。
- 为 Session 中的 agent-local state 设计 tagged union 或 typed envelope，例如 ReAct state 与 Interview workflow state；共同字段只保留真正共享的 history、turn/provenance，禁止复制第二份长期状态。
- Workflow definition 使用稳定 `workflow_version` 与 `step_id`，纯 transition 决定下一步；LLM、工具、时钟、ID 和持久化均通过显式依赖执行，使分支和恢复逻辑可做纯逻辑测试。
- 每个可能产生副作用的 node 使用幂等 operation key 或明确的 pending → effect → commit 语义；snapshot 只保存可安全恢复的稳定点。
- 复用现有 RuntimeCommand/RuntimeEvent、handoff closure、capability、ToolOutcome、CancellationToken 与 ResourceStack；只有现有协议确实不能表达“等待用户回答”等语义时才增加最小新类型。
- Interview workflow 优先建立有限状态与有界循环：面试准备 → 出题 → 等待回答 → 评估 → 追问或下一题 → 汇总 → 返回 Main；显式限制题数、追问数、模型调用数和失败重试。
- 将问题库／评价 rubric 视为 versioned Knowledge/reference 输入，将最终可交付报告视为候选 Artifact；不要把 prompt、workflow 定义和用户运行数据混在同一存储边界。
- 建立两层验证：纯 workflow transition/property tests 覆盖分支、循环、取消和恢复；真实 LLM smoke 覆盖中文／英文问答、追问质量、评分稳定性与完整 main → interview → main 链路。

#### 6.12.4 R9 启动前必须重新确认

- InterviewAgent 的职责、非目标、面试模式与完成条件；
- executor protocol 是否需要抽取，以及 ReAct/Workflow state 的具体 tagged schema；
- 每问一答的 CLI command/event 语义；
- save/restore/rewind、暂停、取消、退出和 handoff closure 规则；
- 原始回答、评分、报告、Memory 与 Artifact 的所有权、隐私和 retention；
- 问题库、rubric、模型调用、工具 capability 与外部依赖清单；
- 新文件、类、构造依赖、公开方法、snapshot migration 和独立实施切片。

## 7. 迁移策略

采用 Strangler Fig/纵向切片迁移：

1. 冻结当前功能基线，不再向旧 BaseAgent/App 添加新能力；旧运行时数据不作为兼容目标。
2. 建立 v2 domain、ports、composition root 和最小 CLI 对话。
3. 迁移工具执行与 Plan，验证无全局 Registry/UIBridge。
4. 迁移 Session/Handoff/Save/Restore/Rewind。
5. 迁移 CLI 命令与取消。
6. 迁移 RAG/Memory。
7. 以 ResumeAgent 完成第一个端到端功能等价。
8. 切换 `main.py` 到 v2，保留一次可回退提交点。
9. 删除旧实现和兼容层，再开发 Interview/Learning 等新功能。

每个阶段都必须可运行；不允许同时改写全部模块后才做首次集成。

### 7.1 数据保留边界（已确认）

v2 只复用以下静态项目资产：

- `data/reference/`
- `data/prompts/`
- `data/resume/template/`

不迁移旧会话和运行时资料，包括 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 以及旧 Plan、handoff、input history、dump/log 状态。新索引从保留的 reference 数据重建；用户工作区和 Resume 产物由 v2 使用新的持久化边界管理。

## 8. 验证策略

用户已明确授权在 `refactor` 分支为核心 domain/runtime/session/tool codec/workspace 编写自动化 characterization、unit 和 contract tests。Adapter、CLI、真实 LLM、Chroma 与 LaTeX 仍通过集成测试、Notebook 或人工 smoke checklist 验证。

每个迁移门禁至少验证：基础对话、工具成功/失败/拒绝、主→子→主 handoff、Plan、save/restore/rewind、Esc cancel、RAG query、Memory write/query、Resume template/edit/build。自动化测试应优先覆盖纯 domain/application 逻辑和失败路径，不用 mock 掩盖真实 adapter 集成问题。

## 9. 需要用户确认的架构决策

| 编号 | 已确认决定 | 影响 |
|------|------------|------|
| R-D1 | 采用新 `src/get_me_in/` 包受控重写，而非原地拆旧代码 | 最大化边界清晰度，迁移期存在双实现 |
| R-D2 | v2 禁止可变全局单例和 import-time 注册 | 所有依赖改由 bootstrap 显式装配 |
| R-D3 | 用 RuntimeCommand/RuntimeEvent 替换 Request/Response/UIBridge 控制协议 | CLI 与 Runtime 解耦，迁移工作量较大 |
| R-D4 | Resume 继续直接操作 LaTeX，但通过 Workspace/Artifact service | 保留现有产品行为，消除工具层重复 |
| R-D5 | 授权重构核心自动化测试 | 以自动化测试保护 domain/application 迁移门禁 |
| R-D6 | 不迁移旧运行时数据，仅保留 reference/prompts/resume templates | 删除 v1 migration 工作，v2 使用全新会话和索引 |

R-D1～R-D6 已由用户确认。R0～R8、G5-F、R6-F、R7-T2 与完整 G8 均已完成；R8-D 提交为 `7514af3`，决策 239／240 记录 G8 和最终用户审查，决策 241 记录完成态文档契约收口。当前停在 R9 独立授权门禁前。
