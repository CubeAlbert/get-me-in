# Chroma 内存模式订正计划

> 适用分支：`refactor`
>
> 本计划只恢复 R8 完成态中遗漏的 Chroma 内存索引模式，不进入 R9，不读取、迁移、改写或删除 legacy 运行数据。

## 1. 问题与目标

v1 的 `ChromaStore` 根据 `CHROMA_PERSIST_DIR` 在内存 client 与 `PersistentClient` 之间切换；内存模式每次启动全量建立索引，持久化模式复用磁盘索引。v2 重构后，`Settings` 固定 `data/v2/knowledge/chroma/`，composition root 无条件创建 `PersistentClient`，该模式选择能力未迁移。

本次恢复目标：

- 默认继续使用当前 persistent 模式，现有用户行为与磁盘数据不变。
- 显式选择 memory 模式时，Chroma 向量索引与 index manifest 仅存在于当前进程。
- memory 模式每次启动从 `data/reference/` 与 `data/v2/memories/` 全量重建索引。
- memory 模式不得创建、读取或改写 persistent Chroma 目录与 JSON manifest。
- 两种模式继续复用同一 `KnowledgeService`、取消、串行、失败重试和资源关闭契约。

## 2. 已确认设计

### 2.1 配置

- 增加 typed `KnowledgeIndexMode`：`persistent`／`memory`。
- 增加 `KNOWLEDGE_INDEX_MODE`，默认 `persistent`；非法值由 `Settings.from_env()` 拒绝。
- `knowledge_chroma_dir` 与 `knowledge_manifest_path` 继续固定在全新 v2 路径，只在 persistent 模式使用。
- 旧 `CHROMA_PERSIST_DIR` 继续不生效；不得借恢复模式重新接入 `data/chroma/`。
- 本轮不增加自定义 Chroma 持久化路径，避免把模式恢复与路径授权混为一项。

### 2.2 成对存储

| 模式 | Chroma client | Manifest repository | 启动语义 |
|---|---|---|---|
| `persistent` | `PersistentClient` | `JsonManifestRepository` | 根据持久化 manifest 增量同步 |
| `memory` | `EphemeralClient` | `InMemoryManifestRepository` | 空 manifest 驱动全量重建 |

不得让 `EphemeralClient` 读取磁盘 manifest。否则新进程中的空 Chroma 会把磁盘 manifest 的全部 source 判定为 `unchanged`，错误进入 `READY` 且没有可查询 collection。

`data/v2/memories/` 中的 Memory JSON 仍是业务源数据，不随 Chroma memory 模式改为易失；本次只切换向量索引和 index manifest。

### 2.3 生命周期

- 当前 Chroma 1.5.9 提供 `EphemeralClient()`，并支持幂等 `close()`。
- 同一进程内的 ephemeral clients 共享 Chroma system；最后一个 client 关闭后 system 才停止并清空。
- production 继续遵守一进程一个 `Application` 的现有边界；自动化不得重叠持有多个 memory-mode application。
- memory 模式退出时不得删除或改写已有 persistent Chroma／manifest；切回 persistent 后由现有 source hash diff 追平 Memory JSON 或 reference 变化。
- 两种模式都只使用嵌入式本地 client；禁止引入 Chroma Server、`HttpClient` 或网络 API。

## 3. 实施白名单

### 3.1 生产代码

- `src/get_me_in/application/settings.py`
- `src/get_me_in/adapters/in_memory_manifest_repository.py`（新增）
- `src/get_me_in/bootstrap.py`

不修改 `KnowledgeService`、Knowledge port/domain、Memory schema、CLI command、Tool、Runtime、Session 或公开检索协议。

### 3.2 自动化

- `tests/get_me_in/test_settings.py`
- `tests/get_me_in/test_knowledge_adapters.py`
- `tests/get_me_in/test_knowledge_service.py`
- `tests/get_me_in/test_bootstrap.py`

只有在现有测试无法覆盖明确契约时才使用上述完整白名单；不得顺手迁移无关 fixture。

### 3.3 配置与文档

- `.env.example`
- `README.md`
- `AGENTS.md`
- `docs/current.md`
- `docs/design.md`
- `docs/task.md`
- `docs/decision.md`
- `docs/pre-r9-quality-hardening.md`
- `docs/chroma-memory-mode-restoration.md`

## 4. 执行切片

### C1 —— 配置与 adapter

- [ ] 增加 `KnowledgeIndexMode` 与 `knowledge_index_mode`，默认 persistent。
- [ ] 严格解析 `KNOWLEDGE_INDEX_MODE`；保持旧 runtime data path sentinel。
- [ ] 新增 process-local `InMemoryManifestRepository`，初始 `IndexManifest(1)`，`save()` 只更新内存状态。
- [ ] 增加 Settings／manifest adapter 定向测试。

### C2 —— Composition 与生命周期

- [ ] 在唯一 composition root 中按 mode 成对选择 Chroma client 与 manifest repository。
- [ ] 保持当前 `ExitStack` ownership、构造失败清理、Knowledge close 顺序和后台 worker 关闭契约。
- [ ] 增加默认 persistent、显式 memory、非法配置、错误 client 未构造、构造失败无泄漏测试。

### C3 —— 一致性与隔离

- [ ] 覆盖“磁盘 manifest 全 READY + 空 ephemeral store”仍全量建立索引。
- [ ] 覆盖 memory 模式不创建／不修改 Chroma 目录与 JSON manifest。
- [ ] 覆盖 persistent → memory → persistent 切换后由 source diff 追平新增、修改和删除。
- [ ] 覆盖最后一个 ephemeral client 关闭后重新创建为空；测试显式提供 embeddings，不调用 Chroma 默认 embedding function。
- [ ] 继续证明四个 legacy 数据目录不会被访问。

### C4 —— 验证与收口

- [ ] 运行 Settings、Knowledge adapter/service、Bootstrap 定向测试。
- [ ] 运行完整 unittest、`compileall`、`git diff --check`。
- [ ] 运行真实 Chroma 双模式 smoke：persistent 重启保留、memory 重启清空；索引写入只经项目 Embedder 的显式 embeddings 路径。
- [ ] 静态确认没有 `HttpClient`／Server composition，没有 legacy data path 读取。
- [ ] 更新配置和当前事实文档；`docs/decision.md` 只追加新决策并同步 TOC。
- [ ] 分离代码／测试 checkpoint 与最终文档 checkpoint；R9 继续保持未授权。

## 5. 停止门禁

出现以下任一情况必须停止并报告最小证据，不得扩大实现：

- 需要修改 `KnowledgeService` 或现有 port/domain 公开协议才能完成模式切换。
- memory 模式必须借助临时磁盘 manifest、删除 persistent 数据或访问 legacy 路径才能工作。
- Chroma 真实 client 不能在现有 `close()` ownership 下可靠释放。
- 模式切换无法通过现有 source hash／manifest diff 恢复 persistent 索引一致性。
- 需要新增远程 Chroma、异步框架、依赖或 R9 对象。
