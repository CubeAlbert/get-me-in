# 重构设计文档

> 适用分支：`refactor`
>
> 本文是重构期间的目标架构来源。`docs/design.md` 记录当前实现及历史设计，二者并存；在 v2 完成切换前，不把旧文档改写成尚未落地的状态。

## 1. 结论

当前项目已经完成一个可运行的 CLI 多 Agent 骨架，并打通了主 Agent 路由、简历 Agent、工具调用、RAG、记忆、Plan、会话恢复和基础中断等关键链路。问题不在于“功能完全不可用”，而在于所有能力逐步堆叠到了少数核心对象和模块级全局状态上：

- `BaseAgent` 同时承担提示词组装、对话状态、LLM 调用、回复解析、工具执行、审批、切换、Plan、记忆和取消处理。
- `App` 同时承担输入组件、命令路由、渲染、后台线程、UIBridge、Agent 编排、会话恢复、自动保存、记忆触发和输入历史。
- Agent、Tool、LLM、RAG、Memory、UIBridge、Plan context 与 Session ID 均存在不同形式的全局注册或模块级状态。
- CLI 通过 `_history`、`_plan`、`_get_agent_key()` 等私有成员直接修改 Agent，协议边界名义上存在，实际上没有形成封装。
- Tool 使用 `__switch__`、`__reject__`、`__cancelled__` 魔法字典传递控制流，Request/Response 枚举仍保留已废弃分支。
- 新增 Agent 需要重复实现约 14 个 `_get_*()` 方法；三个现有 Agent 的大部分代码都是提示词元数据样板。

因此本分支推荐进行一次 **受控重写（controlled rewrite）**：在新的 `src/get_me_in/` 包中构建 v2，通过纵向切片逐步获得功能等价；旧实现仅作为行为基线，直到新入口通过验收后再删除。不要在原有 `BaseAgent` 和 `App` 上继续做大规模就地拆分。

## 2. 当前能力盘点

### 2.1 已实现并可作为重构基线的能力

| 能力 | 当前状态 | 当前实现 | 重构要求 |
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

### 2.2 尚未实现或明确暂缓的能力

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

### 2.3 文档与代码漂移

当前文档列出 23 个工具，但代码实际存在 25 个 `@tool`：Plan 已从 3 个增加到 4 个，switch 模块还包含 `provide_choices`。`RequestType.CONFIRM_APPROVED`、`ResponseType.SELECT`、`ResponseType.CONFIRM` 仍在协议中，但主循环已经不再使用。这类漂移说明当前架构缺少单一事实来源，重构后工具目录、Agent 目录和协议枚举必须由同一声明生成或可直接枚举验证。

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

## 5. 目标架构

### 5.1 分层与依赖方向

```text
interfaces/cli ───────┐
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

### 5.2 建议目录

```text
src/get_me_in/
├── domain/
│   ├── agents.py          # AgentSpec / AgentKey / Capability
│   ├── messages.py        # ConversationRecord / Role
│   ├── plans.py           # Plan / PlanItem / PlanStatus
│   ├── sessions.py        # SessionState / AgentSessionState / HandoffFrame
│   └── tools.py           # ToolDefinition / ToolOutcome
├── application/
│   ├── runtime.py         # AgentRuntime 状态机
│   ├── orchestration.py   # Hub-and-Spoke handoff
│   ├── commands.py        # RuntimeCommand
│   ├── app_commands.py    # ApplicationCommand
│   ├── events.py          # RuntimeEvent
│   ├── session_service.py
│   ├── session_codec.py
│   ├── memory_service.py
│   └── knowledge_service.py
├── ports/
│   ├── llm.py
│   ├── interaction.py
│   ├── sessions.py
│   ├── retrieval.py
│   ├── workspace.py
│   └── clock.py
├── adapters/
│   ├── llm/openai.py
│   ├── json_session_repository.py
│   ├── retrieval/chroma.py
│   ├── workspace/local.py
│   └── resume/latex.py
├── tools/
│   ├── catalog.py
│   ├── common.py
│   ├── plan.py
│   ├── workspace.py
│   └── resume.py
├── agents/
│   ├── catalog.py
│   ├── main.py
│   ├── resume.py
│   └── job_search.py
├── interfaces/cli/
│   ├── app.py
│   ├── commands.py
│   ├── input.py
│   ├── renderer.py
│   └── worker.py
└── bootstrap.py           # 唯一 composition root
```

旧 `src/*` 在迁移期间保留。禁止新 v2 模块反向 import 旧 `BaseAgent`、`App`、全局 Registry 或 UIBridge；必要兼容通过最外层 adapter 完成。

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

Runtime command 保持：`UserMessage`、`Continue`、`Approve`、`Reject`、`SubmitSelection`、`ToolResult`、`Cancel`；R4 增加 `CompleteHandoff(call_id, summary)` 与 `FailHandoff(call_id, code, message)`，专门闭合 `WAITING_FOR_HANDOFF`。

Runtime event 保持：`Progress`、`ApprovalRequested`、`SelectionRequested`、`ToolStarted`、`ToolFinished`、`HandoffRequested`、`Completed`、`Failed`、`Cancelled`。`ToolStarted` 携带只读 arguments 映射，`ToolFinished` 可携带 Plan 投影；二者均不要求 CLI 读取 Session 或反解析工具输出字符串。

一个 Application 只暴露一个活动 Session，公开边界调整为：

```python
def handle(command: RuntimeCommand) -> RuntimeEvent
def view() -> SessionView
def snapshot() -> SessionSnapshot
def restore(session_id: str) -> SessionView
def rewind(turn_id: str) -> SessionView
def list_sessions() -> tuple[SessionPreview, ...]
def dump() -> Path
def request_cancel(reason: str = "Cancelled by user") -> None
def close() -> None
```

`RestoreSession`、`RewindSession`、`ExitSubAgent`、`DumpSession` 等属于 `ApplicationCommand`，不混入模型回合使用的 `RuntimeCommand`。CLI 可以通过统一分发入口调用两类 command，但 Runtime 永远不解释 CLI/Session 命令。

该协议取代当前 Request/Response、UIBridge action 和 switch magic dict。Runtime 每次只推进一个明确状态，不使用多个松散 `_pending_*` 标志表达组合状态。内部 `AgentRuntime.advance(state, command)` 返回 `RuntimeTransition(state, event)`；`RuntimeTransition` 只在 application 层使用，Application 对外仍一次返回一个 `RuntimeEvent`。

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

Handoff 使用 `HandoffFrame(source, target, call_id, turn_id, context)`。Orchestrator 切换到子 Agent 时保留源 Agent 的 `WAITING_FOR_HANDOFF` pending call，并立即以 `UserMessage(context)` 启动目标 Runtime，使 CLI 在收到 `HandoffRequested` 后只需继续驱动新的 active agent。子 Agent 返回 summary 后，Orchestrator 向源 Runtime 发送 `CompleteHandoff`，原子地写入 tool result、弹出 frame 并恢复 active agent。未知 Agent、目标启动失败、嵌套切换、子 Agent 失败或取消以及 `/exit_sub` 均必须通过 `FailHandoff` 或 `CompleteHandoff` 闭合原 call id；CLI 不补写 conversation record。

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

静态 `07_output_format.md` 中的 `thinking` 是模型生成、允许向用户展示的推理摘要，与 provider 原生 `reasoning_content` 和 `LLM_THINKING_ENABLED` 完全分离。finish 回复必须包含 string thinking；tool_call 可省略。该规则由决策 171 取代决策 77 对 finish thinking 的可选化，保留 tool_call 的容错。v2 继续执行决策 136，不读取、保存或展示 provider 原生 reasoning_content。

`MessageRecord` 和 `ToolCallRecord` 保存可选 thinking；Runtime 必须把 `ModelReplyParser` 的结果投影到 Completed/ToolStarted，使 Renderer 可在独立 `SHOW_THINKING` setting 开启时显示“思考摘要”。Session snapshot 对 assistant message/tool call 的 thinking 做可选 round-trip，缺失字段兼容为 `None`。thinking 不参与业务状态转换、tool closure、handoff、rewind 边界或 Plan。

“保留”不等于“回放”。`ConversationCodec` 编码下一轮 LLMRequest 时必须对所有历史记录剥离 thinking；R6 的 `SessionService.memory_source()` 同样必须复制出 thinking 为 `None` 的 provider-neutral 记录，MemoryExtractor 不得接收展示摘要。这样修复只为 R6 增加 G5-F 前置依赖和一条 MemoryBuildSource 投影约束，不改变 R6 的总体架构、已确认文件清单或第一切片。

### 6.7 CLI

CLI 只依赖 `Application` 的公开命令、事件与 Session view，不接触 AgentRuntime、PlanService、CancellationToken 实例、完整 SessionSnapshot 或任何私有 history。拆分职责如下：

- `CliApp`：唯一外层输入循环；把普通文本转换为 `UserMessage`，驱动 RuntimeEvent → 下一条 RuntimeCommand，并在终态触发 session snapshot；命令 handler 的预期异常统一渲染为错误并返回输入循环，不允许用户可控的命令参数终止 CLI。
- `CommandRegistry`：命令解析、帮助文本、alias 与 handler 映射；R6 可替换已注册的 unavailable handler，无需修改 CliApp。
- `InputController`：autocomplete、进程内输入导航历史、prefill、editor、confirm/select；其中 `confirm()` 使用 questionary 选项列表呈现“✅ 执行 / ❌ 取消”，不使用 `y/N` 确认框；不增加独立 CLI 持久化 schema。restore 后可从 `SessionView.rewind_points` 重建导航历史。
- `Renderer`：Markdown、Plan、spinner、错误、命令结果和 `SessionView` context recap；工具开始时以脱敏、截断后的 arguments 摘要展示调用，工具结束时显示截断结果预览；Plan 工具结束时直接渲染只读 Plan 表格，不解析输出字符串；不决定下一条业务 command。
- `WorkerRunner`：使用单 worker 串行执行一个 `Application.handle(RuntimeCommand)`，轮询 Esc/Ctrl+C 并只通过 `Application.request_cancel()` 跨线程取消；不得并发执行 snapshot/restore/另一条 command。

事件推进由 `CliApp` 明确处理：`Progress`、`ToolStarted`、`ToolFinished`、`HandoffRequested` 转为 `Continue`；`ApprovalRequested` 转为 `Approve/Reject`；`SelectionRequested` 转为 `SubmitSelection/Cancel`；`Completed/Failed/Cancelled` 结束内层循环。会返回 RuntimeEvent 的 CLI 命令（当前为 `/exit_sub`）使用 `CommandAction.DRIVE` 将事件交回 `CliApp`，不得只在 handler 内渲染后丢弃；这样 `FailHandoff` 产生的 `ToolFinished` 仍会继续驱动源 Agent。`Reject` 是用户对该次审批的明确否决：Runtime 必须写入已拒绝的 tool result 闭合 pending call，再直接返回 `Cancelled`，不得自动 `Continue` 或把拒绝结果交回模型重试；只有实际工具执行的技术/业务失败才以 `ToolFinished` 交回模型自修复。终态后调用 `Application.snapshot()` 保留旧 CLI 自动保存能力，保存失败单独渲染，不覆盖原终态。

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
| `src/get_me_in/cli/worker.py` | `WorkerRunner` | `__init__(application, renderer, poll_interval_seconds=0.1)`、`run(command: RuntimeCommand) -> RuntimeEvent`、`close() -> None`；只管理单 worker、轮询和取消 |
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

R6 复审结论是保留 Knowledge/Memory 的总体方向，但重新设计命令执行、会话输入、manifest 一致性和资源所有权。R6 只迁移当前 Reference RAG、Memory 构建/查询/删除、`/ragreload`、`/build-memory` 与可配置的终态自动 Memory；不引入 R7 Resume Agent、Artifact schema 或其他新功能。

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

`KnowledgeState` 使用 `IDLE/LOADING/READY/DEGRADED/ERROR/CLOSING/CLOSED`。首次启动尚无可用 index 时，`IDLE/LOADING/ERROR` 查询返回明确 `retrieval_unavailable`；`READY` 可查询；部分 source 失败时进入 `DEGRADED`，保留已提交 index 可查询并在 reload report 中列出失败项。并发 reload 不排队、不重入，返回 typed busy failure；search 与 index mutation 由 KnowledgeService 串行边界保护，不直接依赖 Chroma 的隐含线程安全。

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
| `src/get_me_in/ports/knowledge.py` | `KnowledgeSourceRepository`、`DocumentChunker`、`KnowledgeIndexPort`、`ManifestRepository` | `scan/read`、`chunk`、`replace_source/delete_source/search/close`、`load/save/close`；全部为 Protocol |
| `src/get_me_in/ports/memories.py` | `MemoryRepository` | `write(record) -> KnowledgeDocument`、`get(memory_id)`、`list(agent=None)`、`delete(memory_id)`、`close()`；具体 adapter 还需实现 KnowledgeSourceRepository 供重启重建 index |
| `src/get_me_in/adapters/local_knowledge_sources.py` | `LocalKnowledgeSourceRepository` | `__init__(reference_root)`、`scan(target=None)`、`read(source)`；只允许 reference_root 下 Markdown |
| `src/get_me_in/adapters/markdown_chunker.py` | `MarkdownChunker` | `chunk(document) -> tuple[IndexChunk, ...]`；chunk id 对 source key、content hash 和序号确定性生成 |
| `src/get_me_in/adapters/json_manifest_repository.py` | `JsonManifestRepository` | `__init__(path)`、`load()`、`save(manifest)`、`close()`；schema 校验与原子替换 |
| `src/get_me_in/adapters/chroma_knowledge_index.py` | `SentenceTransformerEmbedder`、`CrossEncoderReranker`、`ChromaKnowledgeIndex` | 模型名、batch/top-k、persist path 全部构造注入；index 实现 KnowledgeIndexPort，不读取全局 config |
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

R7 启动前 Review 已确认总体边界，但下述新文件、对象和公开方法清单仍须由用户再次确认后才能编码。本 checkpoint 只固化设计、计划、任务和决策，不创建 R7 代码文件，不切换旧 `main.py`，也不进入 R8。

#### 6.10.1 R7-P：动态 session identity

当前 composition root 在创建 `ToolContext` 时捕获初始 `session_id`，但 `SessionService.restore()` 会替换规范 `SessionState`。连续恢复多个 snapshot 后，固定 id 可能使 Workspace read-before-edit grant 仍写入旧 scope，也无法为 Artifact 提供可信的当前会话 provenance。

R7 coding 的第一切片必须先修复此边界：

- `SessionState` 继续是 session id 的唯一长期事实来源；禁止新增可变全局变量、CLI 私有读取或第二份长期 session-id 镜像。
- `AgentRuntime.advance(state, command, *, session_id)` 在单次转换期间接收当前 session id；`Orchestrator` 从传入的 `SessionState` 提供该值。
- Runtime 执行工具时以当前 session id 替换其 immutable `ToolContext` 模板中的 scope；该临时值不跨 `advance()` 保存。
- `restore`／`rewind` 清除离开的真实 session scope；连续恢复不同 snapshot 后，旧 revision grant 不得授权当前 Session 的 edit。
- Resume Artifact 操作从同一动态 `ToolContext` 取得 `session_id` 与 `AgentKey.RESUME`，使 workspace 授权和 artifact provenance 使用同一规范身份。

#### 6.10.2 Resume Agent 与资源所有权

Resume 使用 immutable `AgentSpec`，不创建只用于复刻旧 14 个 `_get_*()` 方法的 stateful Agent 类。为达到当前 ResumeAgent 行为等价，capability 固定为：

`system`、`plan`、`interaction`、`web.search`、`external_file.read`、`return_to_main`、`workspace.read`、`workspace.write`、`workspace.open`、`resume.artifact`、`knowledge.query`。

Resume 不获得 `route`，不能调度其他子 Agent。Main 仍只通过 `AgentCatalog` 的公开 descriptor 发现 Resume，Hub-and-Spoke、handoff call-id 闭合与 `/exit_sub` 协议不变。

Main/Resume 分别拥有 `AgentRuntime`、`CancellationToken`、`PlanService` 和 agent-scoped `ToolContext`。生产 composition root 为两个 Runtime 创建不同的 `LLMPort` 实例；测试注入也必须按 `AgentKey` 提供互不相同的实例。每个 Runtime 只关闭自己的 LLM，共享的 Workspace、Frontend、WebSearch、Knowledge 和 Artifact service 只由 `ResourceStack` 中的唯一 owner 关闭。

Session 初始化时同时创建 Main/Resume 两份 `AgentSessionState` 与 PlanService；restore 继续拒绝当前 Application 未装配的 Agent。R7 不改变 RuntimeCommand、RuntimeEvent、HandoffFrame 或 SessionSnapshot schema。

#### 6.10.3 Artifact schema 与一致性

Artifact 使用全新 `data/v2/artifacts/` versioned repository，不读取旧 Session、Memory、Chroma 或 `data/temp/`。Artifact 只记录工作区产物和编译尝试，不写入 Memory；默认不向 SessionSnapshot 增加 ArtifactRef。save/restore/rewind 只恢复对话与 Agent 状态，不删除、覆盖或回滚工作区文件和 Artifact 记录。

ArtifactService 是工具侧 `ResumeArtifactPort` 的正式实现，并借用低层 `ResumeArtifactBackend` 完成静态模板读取和 `pdflatex` 调用；这样 application service 不直接 import `shutil`、文件系统 adapter 或 subprocess。现有 `copy_template`／`build_pdf` 的 LLM 参数 schema 和 ToolOutcome/Runtime 闭合协议保持不变。

Artifact repository 使用 deterministic operation key 和两阶段记录：

1. 在文件副作用前原子保存 `PENDING` operation；key 至少包含 session、Agent、operation kind、规范化路径和输入 revision/hash。
2. 文件操作完成后原子提交 artifact/build-attempt 结果；若最终 metadata 提交失败，原 `PENDING` 仍可用于下一次调用 reconcile。

`copy_template` 先预检模板、目标 LaTeX 与 README。`.tex` 继续拒绝覆盖不同内容；README 保留 v1 的跟随复制和可覆盖行为并产生新版本。若前次 partial operation 已写入与模板完全一致的目标文件，retry 可以依据 pending intent 补齐记录，不把它误判为普通覆盖。

`build_pdf` 记录成功、非零退出、超时、取消和异常尝试。只有 `exit_code == 0` 且 workspace 中目标 PDF 确实存在时才创建可用 PDF Artifact；stdout/stderr 属于 typed build-attempt record。文件已经写入或 PDF 已生成但 metadata 未提交时，工具返回明确的 typed partial failure 和已改变路径，不得报告全部成功。

#### 6.10.4 R7 新文件、对象与公开边界清单（待确认）

下表是建议的 R7 新代码范围。用户确认前不得创建这些文件。

| 文件 | 新增对象 | 构造依赖与公开方法 |
|------|----------|--------------------|
| `src/get_me_in/agents/__init__.py` | package marker | 不导出运行时单例，不执行注册 |
| `src/get_me_in/agents/resume.py` | Resume AgentSpec factory | `build_resume_spec() -> AgentSpec` |
| `src/get_me_in/domain/artifacts.py` | `ArtifactKind`、`ArtifactOperationKind`、`ArtifactOperationStatus`、`Artifact`、`ArtifactBuildAttempt`、`ArtifactOperation` | versioned immutable DTO/StrEnum；路径只保存 workspace-relative 形式，不含 I/O 方法或开放 metadata dict |
| `src/get_me_in/ports/artifacts.py` | `ArtifactRepository` | `get_operation(operation_key)`、`save_operation(operation)`、`next_version(path)`、`list_artifacts(path=None)`、`list_build_attempts(source_path=None)`、`close()` |
| `src/get_me_in/application/artifact_service.py` | `ArtifactService`、`ArtifactPartialFailure` | `__init__(backend, repository, clock, id_generator)`、`copy_template(..., session_id, agent_key, workspace) -> TemplateCopyResult`、`build_pdf(..., session_id, agent_key, workspace, cancellation) -> ProcessResult`、`close()`；直接实现 `ResumeArtifactPort` |
| `src/get_me_in/adapters/json_artifact_repository.py` | `JsonArtifactRepository` | `__init__(root)`；实现 ArtifactRepository，逐 operation versioned JSON、schema 校验、原子 replace、损坏记录 typed failure |
| `tests/get_me_in/test_resume_agent.py` | Resume spec/composition contract tests | capability、Prompt 可见性、双 Runtime/LLM ownership、main→resume→main、取消/失败/restore |
| `tests/get_me_in/test_artifact_service.py` | Artifact service contract tests | copy/build、version、pending reconcile、partial failure、非零退出/超时/取消、PDF existence |
| `tests/get_me_in/test_artifact_repository.py` | JSON repository contract tests | schema、atomicity、operation key、list/filter、损坏记录与幂等 close |

`src/get_me_in/ports/resume_artifacts.py` 增加低层 `ResumeArtifactBackend`，并为 tool-facing `ResumeArtifactPort.copy_template()`／`build_pdf()` 增加 keyword-only `session_id` 与 `agent_key` provenance；`LocalResumeArtifacts` 改为实现 backend，继续封装静态模板、`shutil.which()` 与 ProcessRunner，不负责持久化。

允许修改的既有文件仅为：

- `src/get_me_in/application/runtime.py`、`application/orchestration.py`、`application/tool_executor.py`、`application/application.py`、`application/session_service.py`、`application/settings.py`
- `src/get_me_in/ports/resume_artifacts.py`、`adapters/local_resume_artifacts.py`、`tools/resume.py`、`bootstrap.py`、`.env.example`
- 对应既有测试与 R7 文档

公开签名调整固定为：

- `AgentRuntime.advance(state, command, *, session_id: str) -> RuntimeTransition`
- `build_application(settings, *, runtime_llms: Mapping[AgentKey, LLMPort] | None = None) -> Application`；提供映射时必须覆盖 Main/Resume 且实例互不相同
- `Application.__init__()` 删除只代表 Main 的 `runtime`／`cancellation` 参数和公开 `cancellation` 属性；跨线程取消继续只允许 `request_cancel()`
- `Settings` 增加 `artifacts_dir` 与 `pdf_build_timeout_seconds`，分别默认 `data/v2/artifacts/` 与 60 秒
- `LocalResumeArtifacts.__init__(template_dir, process_runner, build_timeout_seconds)`

R7 不新增 CLI 命令，不改变 25 个 ToolDefinition 名称或参数 schema，不新增 Artifact 查询工具，不修改 SessionSnapshot schema，不迁移旧运行数据。

#### 6.10.5 实施与终止门禁

R7 固定按六个切片实施，每个切片独立验证、独立提交：

1. R7-P dynamic session identity 与跨 restore 隔离测试。
2. Resume AgentSpec、capability、双 Runtime composition 与 handoff contract tests。
3. Artifact domain／port／JSON repository 与 schema/atomicity tests。
4. ArtifactService、ResumeArtifactPort 替换、copy/build partial-failure tests。
5. Settings/bootstrap/resource ownership 接入与完整自动化回归。
6. 中文、英文、双语真实 Resume smoke 与 G7 checkpoint。

只有 6.10.4 清单获得用户确认后，新会话才能从切片 1 开始 coding。G7 通过后仍须 checkpoint 并停下；未经用户后续确认，不得切换旧 `main.py` 或进入 R8 遗留删除。

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

R-D1～R-D6 已由用户确认。R0～R6、G5-F 与 R6-F 均已完成；R7 五项总体边界已由决策 177 确认，并已提交 6.10.4 的具体新文件、对象、构造依赖、公开方法与实施切片清单供用户最终确认。该清单确认前不得开始 R7 coding；G7 通过后仍须 checkpoint 并等待进入 R8 的独立授权。
