# v2 静态资产输入边界

> 适用分支：`refactor`。本文落实 R-D6：v2 只能复用项目中的静态资产，不读取、迁移或兼容 v1 的运行时状态。本文件是 R0/G0 的输入边界基线，不创建 v2 代码或运行目录。

## 1. 允许复用的静态资产

| 资产根目录 | 当前内容 | v1 当前读取方 | v2 可用方式 | 不变量 |
|---|---|---|---|---|
| `data/reference/` | 6 个分类目录、6 个 Markdown 参考文件 | `RagLoader` 递归加载 `.md`，目录名写入 `category` metadata | 作为知识库的原始输入，由 v2 `KnowledgeService` 建立全新索引 | 保留原路径、目录分类和 UTF-8 Markdown 内容；不复用旧 Chroma collection 或时间戳 |
| `data/prompts/` | `general_agent/` 9 个公共模板、`resume/collect_info.md`、`memory/builder.md`、`PLACEHOLDER.md` | `PromptLoader`；MemoryBuilder 直接读取 memory prompt | 作为 prompt renderer 的只读模板输入 | 保留相对路径、文件排序语义和 `{{NAME}}` 占位符语法；v2 不使用 14 个抽象方法来提供变量 |
| `data/resume/template/` | `CHN_Template.tex`、`EN_Template.tex`、`README.md` | `copy_template` 复制文件；ResumeAgent 按 README 约束编辑 | 作为 ArtifactService 的模板源文件 | 保留文件名、占位符、LaTeX 结构与 README 约束；产物复制到 v2 workspace，不在模板目录内编辑 |

### `data/reference/` 分类清单

| 分类目录 | 当前文件 | v1 metadata `category` | v2 约束 |
|---|---|---|---|
| `company_info/` | `examples.md` | `company_info` | 分类名是稳定的检索过滤值 |
| `interview_questions/` | `basics.md` | `interview_questions` | 分类名是稳定的检索过滤值 |
| `job_descriptions/` | `examples.md` | `job_descriptions` | 分类名是稳定的检索过滤值 |
| `knowledge_base/` | `cs_fundamentals.md` | `knowledge_base` | 分类名是稳定的检索过滤值 |
| `recommended_materials/` | `system_design.md` | `recommended_materials` | 分类名是稳定的检索过滤值 |
| `resume_examples/` | `project_experience.md` | `resume_examples` | 分类名是稳定的检索过滤值 |

v2 在 R6 前可为查询能力提供薄 port adapter，但不得让 adapter 读取旧 `data/chroma/`，也不得把旧索引视为 v2 的初始状态。

## 2. 明确禁止作为 v2 输入的状态

| 路径／状态 | v1 用途 | v2 处置 |
|---|---|---|
| `data/save/` | Session 存档、历史、Plan | 不读取、不迁移；v2 从新的 session schema 开始 |
| `data/memories/` | 每 Agent Markdown memory | 不读取、不迁移；R6 创建新的 repository |
| `data/chroma/` | 持久化 Chroma collection 与 `.last_update` | 不读取、不迁移；R6 由允许的 reference 资产重建索引 |
| `data/temp/` | 旧运行时临时文件 | 不读取、不迁移 |
| `data/logs/` | 应用日志与对话 dump | 不作为产品输入；v2 可在自身生命周期内写新日志 |
| 旧进程内状态 | Agent history、registry、UIBridge、workspace read cache、取消事件、输入历史 | 不共享；每个 v2 Application 由 composition root 独立构造 |

## 3. v2 装配和写入边界

1. composition root 接收静态资产根路径或由 typed Settings 提供它们；domain/application 不直接依赖相对工作目录或 `Path.cwd()`。
2. v2 对上述三个目录只读。索引、session、memory、workspace 和 artifact 的输出必须写入新的 v2 管理边界，不能反写模板、prompt 或 reference 源文件。
3. v2 的启动不得通过扫描 `data/save/`、`data/memories/`、`data/chroma/` 或 `data/temp/` 恢复状态；可用静态资产缺失时，必须报告对应的配置／加载错误，而不能回退到旧运行状态。
4. `data/reference/` 增删改后的索引策略由 R6 的 manifest 决定；v1 `.last_update` 不参与任何 v2 决策。
5. Resume 模板复制、LaTeX 编译与 PDF 预览属于 R7 的 ArtifactService；它们不得使用旧 `src.tools.resume_tools` 作为 v2 依赖。

## 4. G0 核对结论

- 三类允许复用的静态资产均存在且可枚举。
- reference 分类目录与当前 `ReferenceCategory` 枚举值一一对应。
- prompt 公共模板的排序依赖文件名，`01_role.md` 至 `09_reserved.md` 的前缀必须保留。
- 简历模板源、使用手册和中文／英文模板文件名均已固定，可作为 R7 的产品等价输入。
- 旧运行时数据目录与允许复用的静态资产路径明确分离；R-D6 无迁移约束可被后续自动化测试和 smoke checklist 验证。
