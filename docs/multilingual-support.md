# 多语言 UI 与模型回复语言专项计划

## 1. 状态与授权边界

- **专项状态：** L1～L6 已完成；代码／测试 checkpoint 为 `02c9c5d`，文档已完成收口。本文件按用户要求保留，作为专项范围、白名单和验证矩阵的历史参考。
- **实施入口：** 本专项已收口；后续变更须从核心文档重新建立授权，不从本文件自动进入 R9。
- **首版语言：** `zh-CN`、`en-US`。
- **配置方式：** 进程启动时确定语言；不增加 `/language`，不在运行中自动检测或切换语言。
- **R9 边界：** 本专项是当前基线维护，独立于 R9；实施和完成均不构成 R9 授权。
- **数据边界：** 不读取、改写、迁移或删除四个 legacy 数据目录；不修改现有 `data/runtime/` Memory 内容或 Chroma 索引。

## 2. 已确认产品决策

1. UI 文案由专用 locale loader 从语言资源加载，通过稳定 key 和命名占位符格式化；不得对最终输出做全局字符串替换。
2. Rich 的 Panel、Markdown、颜色、转义和敏感参数脱敏继续由 Renderer 代码控制；语言资源只保存普通文本。
3. 模型交互只新增一段独立 ResponseLanguage system prompt，运行时注入目标语言；不为每种语言复制整套 system prompt。
4. `08_input_format.md`、`09_output_format.md`、JSON key、event type、Tool 名称／参数、AgentKey、Capability、命令名和 HandoffContext 标签均保持 canonical，不翻译。
5. 模型回复语言覆盖 `finish.message`、`tool_call.message`、可见 `thinking`、模型生成的问题／选项和 Plan 描述；代码、路径、命令、标识符、专有名词、引用原文保持原样。
6. 简历中文／英文／双语是 artifact language，独立于 UI locale 和对话回复语言。
7. 首版不增加运行时语言切换，因此不修改 `SessionState`、`SessionSnapshotCodec` 或 snapshot schema；恢复会话时使用当前进程配置的 UI／回复语言，历史消息原文不翻译。
8. Memory build 不做多语言改造。用户正常情况下不频繁切换语言，Memory 内容保持现有原文；本专项不修改 MemoryExtractor prompt、repository 或 build lifecycle。
9. 当前生产 Memory 检索已用真实 Chroma、现有 embedding 和 reranker 验证英文查询中文事实：技术栈与年龄两组英文查询均正确 Top-1；本专项不更换 embedding／reranker，也不重建索引。
10. 语言正确性是 provider 行为门禁，不进入 `ModelMessageCodec` 的 JSON／字段校验和有界 format repair；自动化只能证明 prompt 注入，真实 provider smoke 才能证明模型遵从。

## 3. 目标架构

```text
.env / Settings
  ├── UI_LOCALE=zh-CN|en-US
  └── MODEL_RESPONSE_LANGUAGE=ui|zh-CN|en-US
          │
          ├── UI_LOCALE
          │     → LocaleLoader
          │     → Translator.text(key, **values)
          │     → Renderer / InputController / CommandRegistry / CliApp
          │
          └── resolved response locale
                → PromptRenderer
                → 07_response_language.md
                → 08_input_format.md
                → 09_output_format.md
                → 10_reserved.md
                → Main Runtime + Resume Runtime
```

语言只从 Settings／composition root 注入。Domain、Application service、Tool handler 和 adapter 不得读取环境变量或直接加载语言文件。

## 4. 新增类型与公开边界

### 4.1 `src/get_me_in/application/localization.py`

新增以下最小类型：

- `Locale(StrEnum)`：仅声明 `ZH_CN = "zh-CN"`、`EN_US = "en-US"`。
- `parse_locale(value: str, *, setting_name: str) -> Locale`：执行精确、fail-fast 的配置解析；不接受隐式别名。
- `resolve_response_locale(value: str, ui_locale: Locale) -> Locale`：`ui` 解析为当前 `ui_locale`，其余值交给 `parse_locale()`。
- `prompt_language_name(locale: Locale) -> str`：返回供 system prompt 使用的确定性名称，例如 `简体中文（zh-CN）`、`English (en-US)`；它不是 UI 翻译资源。

该模块不读取文件、不依赖 CLI、不持有可变全局状态。

### 4.2 `src/get_me_in/cli/localization.py`

新增：

- `LocaleCatalogError(ValueError)`：目录、JSON shape、key、占位符或格式化错误。
- immutable `Translator`：持有已验证的当前语言文本；公开 `text(key: str, **values: object) -> str`。
- `load_translator(locales_dir: Path, locale: Locale) -> Translator`：读取 base `zh-CN` 与目标 catalog，验证后返回 Translator。

loader 契约：

- catalog 顶层必须是 JSON object，全部 value 必须是 string。
- `zh-CN.json` 是 key 基线；`en-US.json` 的 key set 必须与其完全一致。
- 相同 key 在不同语言中的命名占位符集合必须完全一致。
- 未知 key、缺失／多余格式参数、非法 format string 均抛 `LocaleCatalogError`，不得静默显示 key 或半翻译文本。
- 只允许 Python `str.format` 风格命名占位符，例如 `{tool_name}`；禁止位置参数和嵌套属性访问。
- 正常 production 不做静默 fallback。启动阶段若请求 locale 无法解析，使用能够成功加载的 base catalog 显示配置错误并退出 2；若 base catalog 本身损坏，使用一个不依赖 catalog 的最小英文诊断并退出 1。

### 4.3 locale 资源

新增：

- `data/locales/zh-CN.json`
- `data/locales/en-US.json`

资源至少覆盖：

- welcome、help hint、处理中状态。
- Tool started／finished／result、thinking、handoff、approval、selection、pause、cancel、error。
- Session recap、Plan 表头和 PlanStatus label。
- CLI command 描述、alias 说明、unknown command、usage、restore／rewind／approval 提示。
- 输入确认、取消、自定义输入、空白预览。
- application result、startup／shutdown／snapshot／memory scheduling 错误的 presentation wrapper。
- agent、phase、job state 等已知枚举的展示标签；未知技术值使用本地化 wrapper 加 escaped 原值。

资源不得包含 Rich markup；动态值继续在 Renderer 中使用 `Text`／`escape`，模型的 `message` 继续单独使用 Markdown。

## 5. 配置与启动顺序

### 5.1 新增配置

`.env.example` 与 `Settings` 新增：

```dotenv
UI_LOCALE=zh-CN
MODEL_RESPONSE_LANGUAGE=ui
LOCALES_DIR=data/locales
```

- `UI_LOCALE` 可选，缺失时默认为 `zh-CN`；显式值只接受 `zh-CN|en-US`。
- `MODEL_RESPONSE_LANGUAGE` 可选，缺失时默认为 `ui`，在中文默认 UI 下实际解析为 `zh-CN`；显式值只接受 `ui|zh-CN|en-US`，Settings 中保存 resolved `Locale`，避免下游重复解析。
- `LOCALES_DIR` 可选，缺失时默认为 `data/locales`；显式值使用现有 project-relative path 解析与 legacy-path refusal，production 只从该目录读取 locale 静态资源。
- 三个值进入 `.env.example` canonical key／shape 测试；`.env.example` 注释列出全部可用选项与默认值。

### 5.2 Settings 之前的诊断 Renderer

当前 `cli.main` 在 `Settings.from_env()` 前先创建 Renderer。实施时按以下顺序调整：

1. 确定 `project_root`、加载 `.env`。
2. 从 raw env 读取 `UI_LOCALE` 与 `LOCALES_DIR`，只用于 bootstrap translator；缺失／非法值先使用 base catalog。
3. 用 bootstrap translator 构造初始 Renderer。
4. 执行完整 `Settings.from_env()`；配置错误由初始 Renderer 本地化包装并返回 2。
5. Settings 成功后，用 validated `settings.locales_dir`、`settings.ui_locale` 严格重载 Translator，并显式注入所有 CLI 组件。

bootstrap fallback 只用于报告配置错误，不得成为有效 production 配置的隐式默认。

## 6. UI 本地化实施细节

### 6.1 CLI-owned 文案

- `Renderer` 接收 `Translator`；新增 `render_error_key()`／`render_notice_key()` 等最小 helper，但保留 raw technical detail 的安全展示入口。
- `InputController` 接收同一 Translator，翻译执行／取消、自定义输入和输入提示。
- `build_command_registry()` 接收 Translator；`CommandSpec.name`／aliases 保持 canonical，description 和 handler presentation text 由 key 生成。
- `CliApp` 不自行拼接中文；已知通知／错误通过 Renderer key API 展示。
- `WorkerRunner` 的“处理中”由 Renderer／Translator 提供；worker 不读取 locale 文件。
- restore／rewind 的 timestamp 先保持当前稳定 `YYYY-MM-DD HH:mm`，本专项不引入 locale-aware 日期库或时区格式变化。

### 6.2 RuntimeEvent 中的固定展示文本

为避免 Application 依赖 CLI Translator，固定展示语义使用 typed code，前端再翻译：

- 新增 `ProgressKind(StrEnum)`：`CALLING_MODEL`、`REPAIRING_MODEL_RESPONSE`、`WAITING_FOR_TOOL_RESULT`。
- `Progress` 从自由 `message` 改为 `kind: ProgressKind`；不得用英文原文作为翻译 key。
- `ToolApproval` 与 `ApprovalRequested` 改为携带 canonical `tool_name`，审批问题由 InputController／Renderer 生成；当前只有 ToolExecutor 产生 ToolApproval，迁移全部构造点与测试。
- `Failed.code`、`Paused.code` 继续作为稳定映射依据；原始 `message` 保留日志／诊断用途。已知 code 显示本地化文案，未知 code 显示本地化 wrapper、escaped code 和 bounded detail。
- `Cancelled.reason` 与 snapshot 现有字符串契约保持不变；已知 `Cancelled by user`／CLI closing 由 Renderer 映射，本专项不修改 Session 持久化。
- `SelectionRequested.prompt`／choices、`ToolStarted.message`／thinking、Plan description 和 `Completed.message` 属于模型生成内容，不经 UI translator 二次翻译。
- `ApplicationResult` 不再依赖 dataclass `str(result)` 作为最终 UI；Renderer 按具体 result 类型输出本地化标题与字段，业务值保持原样。

### 6.3 不翻译的值

- slash command、Tool 名称、参数名、路径、session／turn／call id。
- JSON key、error code、RuntimePhase／PlanStatus 的持久化值。
- provider／adapter 原始错误 detail、stdout／stderr、Tool result 数据和用户输入；UI 只翻译其标题／wrapper。
- assistant Markdown 内容不进入 UI catalog，也不做机器翻译。

## 7. 模型回复语言 Prompt

新增 `data/prompts/general_agent/07_response_language.md`。保留 filename-driven lexicographic renderer；新文件位于 CommunicationStyle 后、InputFormat 前，`render_output_format()` 仍只读取唯一 `*_output_format.md`。

新增唯一 placeholder：`{{RESPONSE_LANGUAGE}}`。`PromptRenderer` 的允许变量、构造参数／render values 和测试同步更新。

Prompt 必须表达：

```xml
<ResponseLanguage>
- 所有面向用户的 finish.message、tool_call.message、可见 thinking、问题、选项和 Plan 描述必须使用 {{RESPONSE_LANGUAGE}}。
- 代码、路径、命令、Tool 名称、JSON key、标识符、专有名词和引用原文保持原样。
- artifact 的目标语言独立于对话语言；制作英文简历不表示切换 UI 或对话语言。
- HandoffContext、历史消息或工具结果出现其他语言时，不得自行改变目标回复语言。
</ResponseLanguage>
```

- PromptRenderer 由 bootstrap 注入 resolved response locale；Main 和 Resume 使用同一个值。
- 不修改 Main／Resume AgentSpec 和 ToolDefinition 的 canonical 中文元数据；先用真实 provider smoke 验证中文 system instruction 驱动英文回复的稳定性。
- 不修改 `08_input_format.md`、`09_output_format.md`、`ModelMessageEntity`、`ModelMessageCodec`、repair budget 或 provider JSON mode。
- format repair 时完整 system prompt 仍在 request 中，因此 ResponseLanguage 自动保持；repair message 不重复一份语言协议。

## 8. 分阶段实施与 checkpoint

### L0 —— 文档计划（本会话）

- 只更新专项计划与五份核心文档，追加决策。
- 不修改代码、测试、配置或数据。

### L1 —— Locale 类型、catalog loader 与 Settings

**生产白名单：**

- 新增 `src/get_me_in/application/localization.py`。
- 新增 `src/get_me_in/cli/localization.py`。
- 新增 `data/locales/zh-CN.json`、`data/locales/en-US.json`。
- 修改 `.env.example`、`src/get_me_in/application/settings.py`、`src/get_me_in/cli/main.py`。

**测试白名单：**

- 新增 `tests/get_me_in/test_localization.py`。
- 修改 `tests/get_me_in/test_settings.py`、`tests/get_me_in/test_cli_main.py`。

**验收：** Locale 解析、`ui` resolve、JSON shape、key parity、placeholder parity、缺失／多余参数、bootstrap fallback、正常严格加载、Settings 缺失／非法退出码 2。L1 形成独立代码／测试 checkpoint。

### L2 —— CLI-owned UI 全量本地化

**生产白名单：**

- `src/get_me_in/cli/renderer.py`
- `src/get_me_in/cli/input.py`
- `src/get_me_in/cli/commands.py`
- `src/get_me_in/cli/app.py`
- `src/get_me_in/cli/worker.py`
- `src/get_me_in/cli/main.py`
- 两份 locale catalog

**测试白名单：**

- `tests/get_me_in/test_cli_commands.py`
- `tests/get_me_in/test_cli_app.py`
- `tests/get_me_in/test_cli_worker.py`
- `tests/get_me_in/test_cli_main.py`
- `tests/get_me_in/test_localization.py`

**验收：** 两种 locale 覆盖 welcome/help/commands/input/session/plan/thinking/tool/handoff/error/application result；Rich escape、Markdown、thinking Panel、参数脱敏保持现有契约。L2 独立 checkpoint。

### L3 —— Typed 固定事件文案与审批

**生产白名单：**

- `src/get_me_in/application/events.py`
- `src/get_me_in/application/runtime.py`
- `src/get_me_in/application/tool_executor.py`
- `src/get_me_in/domain/tools.py`
- `src/get_me_in/cli/renderer.py`
- `src/get_me_in/cli/input.py`
- 两份 locale catalog

**测试白名单：**

- `tests/get_me_in/test_runtime.py`
- `tests/get_me_in/test_cli_commands.py`
- `tests/get_me_in/test_cli_app.py`
- `tests/get_me_in/test_cli_worker.py`
- `tests/get_me_in/test_bootstrap.py`
- 直接断言 ToolApproval／ToolExecutor 的既有测试文件

**验收：** 所有 production `Progress`／`ToolApproval`／`ApprovalRequested` 构造点迁移；Application／domain 不 import CLI localization；snapshot schema、取消 reason、Tool policy 和审批状态转换不变。L3 独立 checkpoint。

### L4 —— ResponseLanguage Prompt 注入

**生产／Prompt 白名单：**

- 新增 `data/prompts/general_agent/07_response_language.md`。
- `src/get_me_in/application/prompt_renderer.py`
- `src/get_me_in/bootstrap.py`
- 必要时只使用 L1 已新增的 `application/localization.py` 映射 prompt language name。

**测试白名单：**

- `tests/get_me_in/test_prompt_renderer.py`
- `tests/get_me_in/test_bootstrap.py`
- `tests/get_me_in/test_runtime.py` 仅在构造参数 fixture 必须迁移时修改。

**验收：** zh-CN／en-US 均只出现一个 ResponseLanguage 区块；Main／Resume 使用同一 resolved locale；Prompt filename order 保持；InputFormat 与 OutputFormat 均存在且各自 blob／内容不变；`render_output_format()` 仍只返回 OutputFormat。L4 独立 checkpoint。

### L5 —— 完整工程验证与真实 smoke（已完成）

1. 定向测试按 L1～L4 分组通过。
2. `uv run python -m unittest discover -s tests/get_me_in -t .`。
3. `uv run python -m compileall src/get_me_in main.py`。
4. `git diff --check`、locale key／placeholder parity、Prompt section count/order、全部构造点静态扫描。
5. zh-CN／en-US 根入口配置错误、welcome、help、unknown command、restore／rewind 空状态、approval、cancel、shutdown component smoke。
6. fake LLM production composition smoke：Main／Resume 两份 system prompt 均含正确 ResponseLanguage；finish／tool call 事件投影不变。
7. 真实 provider／TTY smoke：
   - zh-CN：普通 finish、tool call message、可见 thinking、selection、approval、Main→Resume→Main。
   - en-US：同一矩阵，确认 UI chrome 与模型生成内容均为英文，代码／路径／Tool 名保持 canonical。
   - en-US 明确请求查询已保存的编程语言或年龄，确认模型实际调用一次 `query_memory` 并正确用英文回答；不触发 Memory build。
8. Windows 为主真实 TTY；Linux 至少执行自动化和 headless component smoke。不得把 fake/unit 结果表述为真实 provider 或物理 TTY 证据。

L5 不应修改 production；若验证发现白名单外缺陷，立即停止，记录证据并提交最小扩展清单，不得顺手修复。

**完成状态：** 定向验证 `151/151`、完整 unittest `346/346`、compileall、diff-check、catalog／Prompt 静态 contract、fake/headless component smoke 已通过；用户已确认双语言真实 provider／Windows TTY 体验无大问题。

### L6 —— 用户审查与文档收口（已完成）

- 用户已复核 zh-CN／en-US 的 UI、工具调用步骤、thinking、handoff 和最终回复体验。
- 已更新 README 的语言配置说明以及五份核心文档的完成事实。
- 已追加完成决策；专项文档按用户要求保留，核心文档和 Git／decision 均保存收口事实。
- 文档 checkpoint 与代码／测试 checkpoint 分离；完成不自动进入 R9。

## 9. 完整文件清单

### 9.1 允许新增

- `src/get_me_in/application/localization.py`
- `src/get_me_in/cli/localization.py`
- `data/locales/zh-CN.json`
- `data/locales/en-US.json`
- `data/prompts/general_agent/07_response_language.md`
- `tests/get_me_in/test_localization.py`

### 9.2 允许按切片修改

- `.env.example`
- `README.md`（仅 L6）
- `src/get_me_in/application/settings.py`
- `src/get_me_in/application/prompt_renderer.py`
- `src/get_me_in/application/events.py`
- `src/get_me_in/application/runtime.py`
- `src/get_me_in/application/tool_executor.py`
- `src/get_me_in/domain/tools.py`
- `src/get_me_in/bootstrap.py`
- `src/get_me_in/cli/main.py`
- `src/get_me_in/cli/renderer.py`
- `src/get_me_in/cli/input.py`
- `src/get_me_in/cli/commands.py`
- `src/get_me_in/cli/app.py`
- `src/get_me_in/cli/worker.py`
- L1～L4 明确列出的既有测试。
- 五份核心文档和本专项文档。

### 9.3 明确禁止修改

- `data/prompts/general_agent/08_input_format.md`
- `data/prompts/general_agent/09_output_format.md`
- `src/get_me_in/application/model_message.py`
- `src/get_me_in/domain/sessions.py`
- `src/get_me_in/application/session_codec.py`
- MemoryExtractor／MemoryService／Memory repository／Memory builder prompt。
- Chroma、embedding、reranker、Knowledge lifecycle、manifest 和当前索引数据。
- Tool 名称、Tool 参数名、command 名称、AgentKey、Capability 和持久化枚举值。
- 依赖、lockfile、数据目录和 R9 设计／代码。

扩展禁止清单或新增 production public API 前必须停止并获得用户确认。

## 10. 风险与控制

| 风险 | 控制 |
|---|---|
| catalog 漏 key 或占位符漂移 | loader strict validation + key／placeholder parity tests |
| Rich markup 注入或 Markdown 能力退化 | catalog 仅普通文本；代码控制 Text／escape；assistant message 继续 Markdown |
| Application 依赖 CLI 翻译 | 固定语义用 typed code；Translator 只在 CLI composition |
| Settings 前无法本地化错误 | base catalog bootstrap translator；完整 Settings 后严格重载 |
| system prompt 多语言副本漂移 | 单一 ResponseLanguage 片段；Input／Output schema 不复制 |
| Main／Resume 或 handoff 后语言漂移 | resolved response locale 由 composition 同时注入两个 Runtime；真实 handoff smoke |
| 误把英文 Memory 查询成功扩大为全部语言保证 | 只记录本次两组证据；首版仅承诺 zh-CN／en-US，并保留 provider smoke |
| 自动语言检测被代码／JD 干扰 | 首版不自动检测、不运行时切换 |
| 技术错误被翻译后无法诊断 | 本地化标题／wrapper，保留 bounded raw detail 和 file-only 日志 |
| 实施越界到持久化、RAG 或 R9 | 固定禁止清单；白名单外发现立即停止 |

## 11. 新会话启动清单

1. 执行 `/project-bootstrap`。
2. 确认 `docs/current.md` 路由到本文件，并读取本文件全部内容。
3. 运行 `git status --short`，保留用户已有变更；确认没有并发 uv／Git 操作。
4. 重读 L1 文件白名单及当前代码，不从本计划假设 checkout 未变化。
5. 只实施 L1；完成定向测试、完整必要验证和独立 checkpoint 后再进入 L2。
6. 每个切片遵循 Plan → Execute → Result Validation → Replan；白名单扩展、协议变化或真实数据访问需求出现时停止。
7. 到达 L5 真实 provider／TTY 门禁时等待用户复核；没有用户证据不得标记 L6 完成。
