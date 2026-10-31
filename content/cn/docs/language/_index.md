---
title: "图查询语言"
linkTitle: "图查询语言"
weight: 7
---

HugeGraph 支持两种主流图查询语言：**Gremlin**（命令式遍历语言）与 **Cypher**（声明式模式匹配语言）。

- **Gremlin**：Apache TinkerPop 的核心图遍历语言，语法灵活、表达力强，适合复杂拓扑路径探索与精细遍历控制。
- **Cypher**：openCypher 标准化的声明式语言，类似 SQL 的直观模式匹配（`MATCH ... WHERE ... RETURN`），易读性强且便于 Neo4j 迁移。

## 语言指南与参考

- [HugeGraph-Gremlin](/cn/docs/language/hugegraph-gremlin/)

  Gremlin 遍历基础、CRUD 语法示例、TinkerPop 规范支持情况及 1.8 升级变化。
- [Cypher 查询语言](/cn/docs/language/hugegraph-cypher/)

  基于 cypher-for-gremlin 的 Cypher 语法支持、读取与写入示例、执行机制与常见限制。
- [Cypher 兼容性与限制](/cn/docs/language/cypher-compatibility/)

  Cypher 子句与函数的覆盖矩阵、已知差异及未实现特性的规避方案。
- [从 Neo4j 迁移到 HugeGraph](/cn/docs/language/migrate-from-neo4j/)

  Neo4j 与 HugeGraph 在图模型、ID 策略、多标签及查询语法上的核心差异对照与迁移步骤。
- [经典示例数据](/cn/docs/language/hugegraph-example/)

  TinkerPop 经典的 6 顶点 6 边人际与软件关系图示例，供编写查询时对照参考。
{.cards}

## 周边工具与相关入口

在不同场景下执行图查询的快捷入口：

- **命令行交互**：通过 [Gremlin Console](/cn/docs/clients/gremlin-console/) 可以在终端中离线调试或连接 Server 提交脚本。
- **Web 可视化探索**：在 [HugeGraph-Hubble](/cn/docs/quickstart/toolchain/hugegraph-hubble/) 中在线执行 Gremlin / Cypher，进行图谱可视化与 Text2GQL 探索。
- **HTTP REST 接口**：直接通过 HTTP 请求提交查询，见 [Gremlin REST API](/cn/docs/clients/restful-api/gremlin/) 与 [Cypher REST API](/cn/docs/clients/restful-api/cypher/)。
- **版本升级参考**：从旧版本升级至 1.8.0 时，请查阅 [1.8 Gremlin 与 TinkerPop 迁移指南](/cn/docs/guides/gremlin-migration-3.8/)，排查语法废弃与行为变化。
