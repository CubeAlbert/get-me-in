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

Runtime event 保持：`Progress`、`ApprovalRequested`、`SelectionRequested`、`ToolStarted`、`ToolFinished`、`HandoffRequested`、`Completed`、`Failed`、`Cancelled`。

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

CLI input history 属于 R5 `InputController`，不进入 domain SessionState。R5 复审决定只保留进程内导航状态，并从 `SessionView.rewind_points` 重建 restore 后的历史，不增加独立 CLI snapshot schema。Artifact 由 R7 `ArtifactRepository` 管理，R4 的 SessionSnapshot 不提前定义 Artifact/ArtifactRef schema。

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

`SessionView` 通过只读 `SessionTurnView` 投影公开主 Agent 用户回合的 `turn_id`、文本和时间，用于 R5 context recap 与 `/rewind` 选择；CLI 不读取完整 `SessionSnapshot` 或私有 history。CLI 自己的输入导航历史仍归 `InputController`，不进入 domain Session。

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

### 6.7 CLI

CLI 只依赖 `Application` 的公开命令、事件与 Session view，不接触 AgentRuntime、PlanService、CancellationToken 实例、完整 SessionSnapshot 或任何私有 history。拆分职责如下：

- `CliApp`：唯一外层输入循环；把普通文本转换为 `UserMessage`，驱动 RuntimeEvent → 下一条 RuntimeCommand，并在终态触发 session snapshot。
- `CommandRegistry`：命令解析、帮助文本、alias 与 handler 映射；R6 可替换已注册的 unavailable handler，无需修改 CliApp。
- `InputController`：autocomplete、进程内输入导航历史、prefill、editor、confirm/select；不增加独立 CLI 持久化 schema。restore 后可从 `SessionView.rewind_points` 重建导航历史。
- `Renderer`：Markdown、Plan、spinner、错误、命令结果和 `SessionView` context recap；不决定下一条业务 command。
- `WorkerRunner`：使用单 worker 串行执行一个 `Application.handle(RuntimeCommand)`，轮询 Esc/Ctrl+C 并只通过 `Application.request_cancel()` 跨线程取消；不得并发执行 snapshot/restore/另一条 command。

事件推进由 `CliApp` 明确处理：`Progress`、`ToolStarted`、`ToolFinished`、`HandoffRequested` 转为 `Continue`；`ApprovalRequested` 转为 `Approve/Reject`；`SelectionRequested` 转为 `SubmitSelection/Cancel`；`Completed/Failed/Cancelled` 结束内层循环。终态后调用 `Application.snapshot()` 保留旧 CLI 自动保存能力，保存失败单独渲染，不覆盖原终态。

审批策略属于 CLI 偏好：正式命令使用 `/approval prompt|auto`，并保留 `/auto-approve-switch` 兼容 alias；该策略只决定 `ApprovalRequested` 是否自动发送 `Approve`，不修改 ToolDefinition 或 Runtime 状态。Sticky Plan 只有在 Renderer 独占终端生命周期后再加入。

`/ragreload` 与 `/build-memory` 在 R5 只进入 CommandRegistry 并明确报告 R6 尚不可用；R6 通过 `CommandRegistry.replace()` 接入真实 handler。R5 提供 `python -m src.get_me_in.cli` 独立入口；正式 CLI 通过 G5 后删除临时 `scripts/v2_runtime_smoke.py`，因此 R8 切换 `main.py` 前仍有唯一可验证的 v2 CLI 入口。

R5 新文件、对象与公开边界清单如下，已由用户在决策 154 中确认；编码只允许创建或调整清单明确列出的 R5 范围：

| 文件 | 新增对象 | 公开边界 |
|------|----------|----------|
| `src/get_me_in/cli/__init__.py` | v2 CLI package | 不导出可变全局实例 |
| `src/get_me_in/cli/app.py` | `CliApp` | `__init__(application, commands, input_controller, renderer, worker)`、`run() -> int`；内部持有审批模式并驱动 command/event，不暴露业务状态 |
| `src/get_me_in/cli/commands.py` | `ApprovalMode`、`CommandAction`、`CommandResult`、`CommandSpec`、`CommandRegistry` | `CommandRegistry(specs=())`、`register(spec) -> None`、`replace(spec) -> None`、`dispatch(text) -> CommandResult | None`、`help_entries() -> tuple[tuple[str, str], ...]`、`completions() -> tuple[str, ...]`、`build_command_registry(application, input_controller, renderer) -> CommandRegistry`；结果使用强类型 action，不返回魔法 dict |
| `src/get_me_in/cli/input.py` | `InputController` | `__init__(editor=None)`、`read(prefill=None) -> str | None`、`edit() -> str | None`、`confirm(prompt) -> bool | None`、`select(prompt, choices, allow_custom=False) -> str | None`、`remember(text) -> None`、`replace_history(entries) -> None` |
| `src/get_me_in/cli/renderer.py` | `Renderer` | `__init__(console=None)`、`render_event(event) -> None`、`render_session(view) -> None`、`render_help(entries) -> None`、`render_error(message) -> None`、`render_notice(message) -> None`、`status(message)`；不返回下一条 command |
| `src/get_me_in/cli/worker.py` | `WorkerRunner` | `__init__(application, renderer, poll_interval_seconds=0.1)`、`run(command: RuntimeCommand) -> RuntimeEvent`、`close() -> None`；只管理单 worker、轮询和取消 |
| `src/get_me_in/cli/main.py` | CLI composition function | `main() -> int`；构造 Application 与 CLI 组件，按 worker → application 顺序关闭 |
| `src/get_me_in/cli/__main__.py` | 模块入口 | 只调用 `main()`，不含业务逻辑 |
| `tests/get_me_in/test_cli_app.py` | CliApp protocol tests | 覆盖事件推进、handoff continue、终态自动保存与保存失败 |
| `tests/get_me_in/test_cli_commands.py` | CommandRegistry tests | 覆盖 parse/help/alias/replace、restore/rewind、unavailable handler 与审批策略 |
| `tests/get_me_in/test_cli_worker.py` | WorkerRunner tests | 覆盖单 worker、取消、关闭与禁止并发 |

其中 `ApprovalMode` 只包含 `PROMPT/AUTO`；`CommandAction` 只包含 `HANDLED/EXIT/SUBMIT/PREFILL/SET_APPROVAL`。`CommandResult` 由 `action`、可选 `text` 和可选 `approval_mode` 组成：`SUBMIT` 用于 `/edit` 产生普通用户输入，`PREFILL` 用于 `/rewind` 回退后预填，`SET_APPROVAL` 只修改 CliApp 的进程内审批偏好。`CommandSpec` 包含 `name/description/handler/aliases`，handler 接收命令参数文本并返回 `CommandResult`；非命令输入时 `dispatch()` 返回 `None`。

R5 复用既有 `build_application()`，不改变 `bootstrap.py` 的 Runtime/Session 装配边界；`cli/main.py` 负责 Settings 加载和 CLI 组件装配。R5 只调整 `docs/legacy-cli-smoke-checklist.md`，不修改 RuntimeCommand/RuntimeEvent、Session snapshot schema、ToolDefinition 或 R6/R7 service。真实 questionary/Rich、Windows UTF-8、Esc、Ctrl+C、EOF 与 editor-not-found 仍使用人工 smoke 验证。

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

现有 `RetrievalPort` 作为 tool-facing 查询端口保留，不在 R6 重复定义。`KnowledgeService` 实现或适配该端口，并管理 source ingestion、query、reload、manifest 和生命周期；内部写入边界拆为 source repository、index adapter 与 manifest repository，避免用含义模糊的单一 `KnowledgeRepository` 包揽三类职责。`MemoryService` 负责从会话提取 Memory、写 repository，再调用 KnowledgeService 建索引。两者通过 port 连接，不使用 observer callback 和延迟 import。

索引 manifest 使用内容 hash 检测新增、修改、删除和重命名。索引失败时文件写入不能被报告为“全部成功”；应记录 pending/error 状态供重试。

Application 使用统一的逆序资源清理栈管理 LLM、Web Search、Knowledge loader/index 和其他可关闭 adapter；`Application.close()` 不按模块逐项硬编码。R6 与 R7 可在 G5 后并行实现；只有 Resume 验收中实际使用 knowledge/memory 的路径依赖 G6。

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

R-D1～R-D6 已由用户确认。当前会话仍只完成文档与技能调整，不创建 v2 代码模块；进入 R1 前仍需按项目约定提交新文件、类和公开方法清单。
