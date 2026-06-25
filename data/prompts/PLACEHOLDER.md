# 占位符清单

`general_agent/` 下的模板文件中的 `{{占位符}}` 由 `PromptLoader.get()` 在运行时替换。
以下占位符全部由各 Agent 实现时分别定义。

## 01_role.md

| 占位符 | 用途 |
|--------|------|
| `{{AGENT_NAME}}` | Agent 名称 |
| `{{AGENT_DESCRIPTION}}` | Agent 职责简述 |
| `{{RESPONSIBILITIES}}` | Agent 具体职责范围 |

## 02_mission.md

| 占位符 | 用途 |
|--------|------|
| `{{PRIMARY_GOAL}}` | 首要目标 |
| `{{SUCCESS_CRITERIONS}}` | 成功标准 |
| `{{PRIORITIES}}` | 优先级规则 |

## 03_constraint.md

| 占位符 | 用途 |
|--------|------|
| `{{HARD_CONSTRAINTS}}` | 硬约束（不可违反） |
| `{{SOFT_CONSTRAINTS}}` | 软约束（尽量遵守） |

## 04_tools.md

| 占位符 | 用途 |
|--------|------|
| `{{ADDITION_TOOLS}}` | 各 Agent 专属工具的 XML 定义，插入在 `ask_user`/`finish` 之后 |

## 05_communtion_style.md

| 占位符 | 用途 |
|--------|------|
| `{{TONE}}` | 语气 |
| `{{VERBOSITY}}` | 详细程度 |
| `{{EXPLANATION_STYLE}}` | 解释风格 |
| `{{STYLE_RULES}}` | 偏好行为 |
| `{{STYLE_AVOIDS}}` | 应避免的行为 |

## 06_output_format.md

无占位符（固定内容，所有 Agent 统一）。

## 07_reserved.md

无占位符（固定内容）。

---

共 14 个占位符，全部 per-Agent 定义。
