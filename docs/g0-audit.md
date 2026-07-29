# G0 审查记录：R0 基线冻结与决策门禁

> 审查日期：2026-07-21。适用分支：`refactor`。本审查只判断是否具备进入 R1 设计清单确认的条件；它不授权创建 v2 代码模块。

## 审查结论

**通过（附带人工 smoke 待办）**。R0 的架构、行为和输入边界材料已经完备，且没有创建 `src/get_me_in/` 或其他 v2 代码。可以进入 R1 的“新文件、类和公开方法清单”设计审查；在你确认该清单前，仍不得创建 v2 代码。

真实终端下的 CLI smoke C01（抵达输入提示）和 C05（`/exit`）尚未执行。它们是旧入口完整人工可运行性的待验证项，不改变本次架构门禁结论；必须保留到后续人工 smoke 记录中，不能标记为已通过。

## G0 核对表

| 门禁要求 | 证据 | 结果 |
|---|---|---|
| 目标架构、迁移策略、功能冻结与验证策略已由用户确认 | `docs/design.md` 的 R-D1～R-D6；`docs/plan.md` | 通过 |
| 已明确哪些旧行为必须有等价实现，哪些机制可废止 | [capability-parity-matrix.md](capability-parity-matrix.md) | 通过 |
| 25 个现有工具均有迁移处置 | capability matrix 的工具目录基线 | 通过 |
| 静态资产复用范围和旧状态排除范围已固定 | [v2-static-asset-boundary.md](v2-static-asset-boundary.md) | 通过 |
| CLI 可观察行为的人工验证方法已具备 | [legacy-cli-smoke-checklist.md](legacy-cli-smoke-checklist.md)，共 30 项 | 通过 |
| 旧入口的源码回退点已记录 | [legacy-entry-baseline.md](legacy-entry-baseline.md)，源码提交 `f5ee376` | 通过 |
| v2 代码尚未创建 | `src/get_me_in/` 不存在；当前 R0 提交均为文档 | 通过 |
| 旧入口完整交互 smoke 已实际执行 | C01、C05 尚未在真实用户终端执行 | 待人工验证 |

## 发现与迁移约束

1. 旧 `main.py` 在 CLI 输入循环前启动 RAG 模型／索引加载；本地模型未缓存或网络受限时会延迟可交互性。R5/R6 必须将 CLI 可用性与 Knowledge 生命周期解耦，并定义 loading、error、retry 的强类型可见事件。
2. v2 只读取 `data/reference/`、`data/prompts/`、`data/resume/template/` 三类静态资产。`data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 和旧进程内状态均禁止作为 v2 输入。
3. v1 的全局 Registry、UIBridge、Plan Agent 全局变量、workspace read cache、import-time 注册与魔法控制字典不属于等价要求；其可观察结果须由 v2 的显式装配、service 和强类型协议表达。
4. 本审查不修改 `docs/current.md`、`docs/task.md` 或项目状态快照；按项目约定，待你审查并明确要求 checkpoint 后再更新。

## 进入 R1 前的强制步骤

向用户提交 R1 的全部新文件、类和公开方法清单，至少说明：目录分层、每个类型的职责、构造依赖、公开 API、测试边界，以及 `build_application(settings)` 的装配关系。**只有用户明确确认该清单后，才允许创建 v2 文件。**
