# LaTeX 简历模板操作手册

本模板通过 `{-XXX-}` 占位符管理简历内容。Agent 的任务是：用真实信息替换所有占位符，保持 LaTeX 结构不动，最终编译为 PDF。

---

## 一、模板章节结构

| 章节 | 中文标题 | English Title | 内容说明 |
|------|----------|---------------|----------|
| Title | — | — | 姓名，居中大号显示 |
| Header | — | — | 性别 / 年龄 / 邮箱 / 电话 / GitHub |
| 个人简介 | 个人简介 | Professional Summary | 最少 3 条、最多 5 条 bullet，概述核心能力 |
| 教育背景 | 教育背景 | Education | 支持多条教育经历（同一组占位符复用），时间倒排 |
| 专业技能 | 专业技能 | Technical Skills | 编程语言 / 数据库（各分熟练/不熟练）/ 框架 / AI / 工具，可增删技能行 |
| 工作经历 | 工作经历 | Work Experience | 公司 / 职位 / 部门 / 时间 + 5 条描述 |
| 项目经验 | 项目经验 | Project Experience | 项目名 / 角色 / 时间 / 概述 / 技术栈 + 6 职责 + 4 成果 |
| 其他信息 | 其他信息 | Additional Information | 灵活章节：证书、语言水平、兴趣爱好等，可增删类型 |

> **注意：** 中文模板和英文模板章节结构完全一致，仅标题语言不同。Agent 操作时不要修改 `\sectitle{...}` 中的章节标题。

---

## 二、占位符清单

| 占位符 | 中文说明 | English |
|--------|----------|---------|
| `{-NAME-}` | 姓名 | Full Name |
| `{-GENDER-}` | 性别 | Gender |
| `{-AGE-}` | 年龄 | Age |
| `{-EMAIL-}` | 邮箱 | Email Address |
| `{-PHONE-}` | 电话 | Phone Number |
| `{-GITHUB-}` | GitHub 用户名 | GitHub Username |
| `{-SUMMARY-1-}` 至 `{-SUMMARY-5-}` | 个人简介各条目（最少填充 3 条） | Professional Summary Bullet Points |
| `{-UNIVERSITY-}` | 大学名称（多条教育经历时复用） | University Name |
| `{-EDU-DATE-}` | 教育时间（多条教育经历时复用） | Education Period |
| `{-MAJOR-}` | 专业（多条教育经历时复用） | Major |
| `{-DEGREE-}` | 学位（多条教育经历时复用） | Degree |
| `{-SKILL-LANG-PRO-}` | 编程语言（熟练），`\emph{}` 包裹，逗号分隔 | Programming Languages (Proficient) |
| `{-SKILL-LANG-OTHER-}` | 编程语言（不熟练），以 `, ` 开头，逗号分隔；无则不填 | Programming Languages (Familiar) |
| `{-SKILL-DB-PRO-}` | 数据库与中间件（熟练），`\emph{}` 包裹，逗号分隔 | Databases & Middleware (Proficient) |
| `{-SKILL-DB-OTHER-}` | 数据库与中间件（不熟练），以 `, ` 开头，逗号分隔；无则不填 | Databases & Middleware (Familiar) |
| `{-SKILL-FRAMEWORK-}` | 框架，逗号分隔 | Frameworks |
| `{-SKILL-AI-}` | AI 工程技能，逗号分隔 | AI Engineering Skills |
| `{-SKILL-TOOLS-}` | 开发工具，逗号分隔 | Development Tools |
| `{-JOB-TITLE-}` | 职位 | Job Title |
| `{-JOB-COMPANY-}` | 公司 | Company Name |
| `{-JOB-DEPT-}` | 部门 | Department |
| `{-JOB-DATE-}` | 工作时间 | Employment Period |
| `{-JOB-DESC-1-}` 至 `{-JOB-DESC-7-}` | 工作描述条目（最少填充 3 条） | Job Description Bullet Points |
| `{-PROJECT-NAME-}` | 项目名称 | Project Name |
| `{-PROJECT-ROLE-}` | 项目角色 | Project Role |
| `{-PROJECT-DATE-}` | 项目时间 | Project Period |
| `{-PROJECT-DESC-}` | 项目描述 | Project Description |
| `{-PROJECT-TECH-}` | 技术栈 | Tech Stack |
| `{-PROJECT-RESP-1-}` 至 `{-PROJECT-RESP-7-}` | 职责条目（最少填充 3 条） | Responsibilities |
| `{-PROJECT-RESULT-1-}` 至 `{-PROJECT-RESULT-7-}` | 关键成果条目（最少填充 3 条） | Key Achievements |
| `{-OTHER-TYPE-1-}` | 其他信息类型（如证书、语言水平、兴趣爱好等） | Category (e.g., Certifications, Languages) |
| `{-OTHER-1-}` 至 `{-OTHER-2-}` | 该类型下的条目；多条可追加 `\item{-OTHER-N-}` | Items under the category |

---

## 三、填充约束与指南

### 3.1 核心原则

- **只替换占位符，不修改模板结构。** 不要增删 `\section`、不要改变 LaTeX 命令、不要调整格式参数（字体/颜色/间距）。你的工作是用 `workspace_replace` 精确替换 `{-XXX-}`，保留 `{-XXX-}` 前后的 LaTeX 代码不动。
- **所有修改用 workspace 工具完成。** 首选 `workspace_replace`（全局文本替换），需要精确行级操作时用 `workspace_edit`（必须先 `workspace_read` 获取准确行号和内容）。
- **保持 LaTeX 语法正确。** 替换内容中的 `&`、`%`、`$`、`#`、`_`、`{`、`}`、`~`、`^`、`\` 需要转义。
- **禁止过度联想，只填写事实。** 用户给了什么就填什么，不要主动帮用户"设计"内容。除非用户明确提出"帮我想想这部分该怎么写"、"帮我设计一下可能的职责"、"帮我写一下可能的成果"等请求，否则只使用用户已提供的信息。用户没说到的占位符保留不动。

### 3.2 语言约束

| 模板 | 填写语言 |
|------|----------|
| `CHN_Template.tex` | 全中文填写（技能名、技术术语可保留英文） |
| `EN_Template.tex` | 全英文填写 |

### 3.3 全局日期格式

| 模板 | 已完成时间段 | 至今（进行中） |
|------|-------------|---------------|
| 中文 | `2014年9月-2018年6月` | `2026年2月至今` |
| 英文 | `Sept. 2014 – June 2018` | `Oct. 2021 - Present` |

### 3.4 各章节约束

**个人简介（SUMMARY）：**
- **最少 3 条，最多 5 条。** 不足 5 条时删除多余的 `\item{-SUMMARY-N-}` 行
- 每条 1-2 句话，具体不空洞。反例："熟悉 Python" → 正例："5 年以上 Python 后端开发经验（FastAPI/Django），主导日活百万级 API 网关"
- 覆盖维度：核心技术栈 / 领域经验年限 / 关键成果 / 软技能 / 行业背景

**教育背景（EDUCATION）：**
- **时间倒排** — 最近的在前面，最远的在最后
- **最后一条不加 `\\` 和 `\hdashrule`** — 分割线只用于分隔多条教育经历
- 模板默认提供 2 组教育经历占位符（同一组占位符名），若教育经历在同一所学校则 `workspace_replace` 替换即可；若不同学校，需用 `workspace_edit` 精确编辑第二组
- 增减教育条目时通过复制/删除 `{-UNIVERSITY-} ... \hdashrule` 块实现

**专业技能（TECHNICAL SKILLS）：**
- **LANG / DB 分熟练和不熟练两部分：**
  - `PRO`（熟练）在 `\emph{}` 内，逗号分隔，无尾逗号
  - `OTHER`（不熟练）跟在 `\emph{}` 后面，以 `, ` 开头，无则不填
  - 示例：`\emph{Python, Go, Java}, Rust, SQL`
- **FRAMEWORK / AI / TOOLS** 用 `{-SKILL-XXX-}` 单一占位符，逗号分隔，无尾逗号
- **可增删技能行** — 用户可要求删除某类技能或新增类型；增减时保持 LaTeX 结构一致
- **最后一行不加 `\\`** — 同教育背景规则

**工作经历（WORK EXPERIENCE）：**
- **JOB-DESC 最少 3 条，最多 7 条** — 模板默认提供 7 条占位符，不足时删除多余 `\item` 行
- **JOB-DATE 遵循全局日期格式**（见 3.3）
- **多条经历时复制整块** — 从 `\textBF{-JOB-TITLE-}` 到 `\hdashrule` 整体复制，追加到下方
- **时间倒排** — 最近的工作经历在最前面
- **最后一条经历删除 `\hdashrule` 分隔符** — 同教育背景规则

**工作描述（JOB-DESC）：**
- 用 STAR 法则（情境 → 任务 → 行动 → 结果）
- 每条包含具体技术、行动、量化结果
- 反例："负责后端开发" → 正例："设计并实现分布式消息调度系统，支撑日均 500 万任务分派，延迟从 3s 降至 200ms"

**项目经验（PROJECT）：**
- **PROJECT-DATE 遵循全局日期格式**（见 3.3）
- **RESP（职责）最少 3 条，最多 7 条** — 模板默认提供 7 条占位符，不足时删除多余 `\item` 行
- **RESULT（成果）最少 3 条，最多 7 条** — 数量尽量与 RESP 对齐（软约束），同样不足时删多余行
- RESP 和 RESULT 必须具体、可量化（数字/百分比/指标）
- PROJECT-DESC：1 句话概括项目背景和价值
- PROJECT-TECH：逗号分隔技术栈，按核心程度排列
- **多条项目时复制整块** — 从 `\textBF{-PROJECT-NAME-}` 到 `\hdashrule` 整体复制，追加到下方
- **时间倒排** — 最近的项目在最前面
- **最后一条项目删除 `\hdashrule` 分隔符**

**其他信息（OTHER）：**
- **灵活章节** — 用于填写上述章节未覆盖的内容：证书、语言水平、兴趣爱好、开源贡献等
- **类型可变** — `\textBF{{-OTHER-TYPE-1-}}` 填写类型名（如"证书"、"语言水平"），可改为实际需要的类型
- **条目可扩展** — 默认 2 条 `\item`，按需增减
- **多个类型时复制整块** — 从 `\textBF{...}` 到 `\vspace{0.5ex}` 整体复制，LLM 用 `workspace_edit` 追加到下方

### 3.5 边界处理

| 场景 | 处理方式 |
|------|----------|
| 用户未提供某项信息 | **保留占位符不动**，不要编造、不要猜测。后续提示用户手动填写 |
| 个人简介不足 5 条 | 填已有的，删除多余 `\item` 行（最少保留 3 条） |
| 其他信息需多个类型 | 复制 `\textBF{{-OTHER-TYPE-N-}}` 到 `\vspace{0.5ex}` 整块，LLM 用 `workspace_edit` 追加 |
| 其他信息无需填写 | 保留占位符或删除整个 section（需用户确认） |
| 教育经历多于 2 条 | 仿照现有结构追加 `{-UNIVERSITY-} ... \hdashrule` 块，最后一条不加分隔线 |
| 教育经历仅 1 条 | 删除第二组占位符块及其前面的 `\hdashrule` |
| 工作经历多条 | 复制 `\textBF{-JOB-TITLE-}` 到 `\hdashrule` 整块，时间倒排，最后一条删 `\hdashrule` |
| 工作经历仅 1 条 | 保留单块，删除末尾 `\hdashrule` |
| JOB-DESC 不足 7 条 | 删除多余 `\item` 行（最少保留 3 条） |
| 项目多条 | 复制 `\textBF{-PROJECT-NAME-}` 到 `\hdashrule` 整块，时间倒排，最后一条删 `\hdashrule` |
| 项目仅 1 条 | 保留单块，删除末尾 `\hdashrule` |
| RESP/RESULT 不足 7 条 | 删除多余 `\item` 行（最少保留 3 条） |
| 技能行需删除/新增 | 删除整行 LaTeX 或仿照现有格式新增行，最后一行不加 `\\` |
| 不确定某字段该填什么 | 先 `workspace_read` 查看上下文，再用 `provide_choices` 让用户选择 |
| 模板中 `{-XXX-}` 未在本文档列出 | 视为普通占位符，按上下文合理填充；若不确定含义，保留并询问用户 |

### 3.6 编译与预览

1. 所有占位符填充完成后，**务必**调用 `build_pdf` 编译
2. 若 `exit_code != 0`：阅读 stderr，定位错误行号 → `workspace_read` 查看 → `workspace_edit` 修复 → 重新 `build_pdf`
3. 编译成功后，调用 `workspace_open` 打开 PDF 供用户预览
4. 常见 LaTeX 错误：特殊字符未转义、`\` 和中文紧贴导致 CJK 错误、`{` `}` 不匹配

### 3.7 工作流检查清单

- [ ] 确认用户意图：新建还是修改？中文还是英文？文件名前缀？
- [ ] `copy_template` → `workspace_read(README.md)` 阅读本手册
- [ ] 逐个替换占位符，编辑前 `workspace_read` 确认
- [ ] 遵循各章节约束（条数限制、日期格式、末尾 `\\` 规则等）
- [ ] 全部填充完成后 `build_pdf` 编译
- [ ] `workspace_open` 预览 PDF
- [ ] 编译失败则根据 stderr 修复 → 重新编译
