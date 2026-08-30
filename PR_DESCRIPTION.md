# Add SeaTunnel Connector Integration Guide (CN only)

## Purpose

- 新增 Apache SeaTunnel Connector 集成快速上手文档，作为 HugeGraph 工具链的生态入口之一
- 帮助新用户理解 SeaTunnel 与 Loader / Tools 的选型边界，并给出 JDBC / Kafka / graph2graph 三类常见用法

## Changes

- **New**: `content/cn/docs/quickstart/toolchain/hugegraph-seatunnel-connector.md` — CN 快速上手：
  - 发布版（2.3.13，`schema_config`）与 dev（Source + `mappings`）分开讲解，示例按上游 commit 钉住核对
  - sql2graph（JDBC 顶点/边写入）、kafka2graph（流式写入）、graph2graph（图迁移，dev）三个场景，含完整 HOCON 配置与验证命令
  - dev 示例与上游最新状态对齐（2026-08）：HugeGraph Source 与 `mappings` 多映射已随 PR apache/seatunnel#11413 合入 dev（2026-08-05），将随 SeaTunnel **3.0.0** 发布；2.3.13 内置 Client 1.5.0，dev 已升 1.7.0
  - 补充 dev Source 要点：省略 `label` 读全量（多表输出、不可配 `schema`/`filter`）、`parallelism > 1` 分片并行要求可扫描后端（RocksDB / HBase / Cassandra）且与 `filter` 互斥、`~id`/`~source_id`/`~target_id` 保留列克隆
  - 常用配置表区分 `schema_config`（2.3.13）与 `mappings`（dev），并列出 dev 新增选项（`schema_save_mode`、`data_save_mode`、`check_vertex`、失败回退、重试、`updateStrategies`、`listFormat`、`unfold*` 等）
  - 参考文档补齐官网版本化链接（2.3.13 Sink）与上游追踪链接（apache/seatunnel#10001 / #10002 / #11413 / #11329）
- **New images**: `content/cn/docs/images/seatunnel/*.png`（总览 / sql2graph / kafka2graph / graph2graph 示意图）
- **Modified**: `content/cn/docs/introduction/_index.md` — 工具链表新增 SeaTunnel-connector 条目（Sink 2.3.13+；Source 已合入 dev，随 3.0.0 发布）；新增全栈生态全景图

## Notes for reviewers

- 按 review 意见先出纯 CN 版本，EN 版本通过后再补
- dev 示例按上游 commit `f1a1a0a` 核对（含 #11413 合入后的 Source / Sink 文档），`dev` 会继续变化，文档已注明需重新核对
- Source 尚未随正式 Release 发布（已合入 dev，随 SeaTunnel 3.0.0 发布）；3.0.0 发版后可将 dev 示例链接切换为官网版本化地址

## Related

- 功能请求：apache/seatunnel#10001
- Sink Connector（已随 SeaTunnel 2.3.13 发布）：apache/seatunnel#10002
- Source Connector + 多映射重构（2026-08-05 合入 dev，随 3.0.0 发布）：apache/seatunnel#11413
- 文档改进：apache/seatunnel#11329
