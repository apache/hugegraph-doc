---
title: "从 Neo4j 迁移"
linkTitle: "从 Neo4j 迁移"
weight: 4
---

### 本页面向谁

正在评估 HugeGraph 的 Neo4j 用户。HugeGraph 的 Cypher 覆盖面由
[cypher-for-gremlin](https://github.com/opencypher/cypher-for-gremlin) 转译器决定，
与 Neo4j 并非 1:1 等价 —— 逐项差异见
[Cypher 兼容性矩阵](/cn/docs/language/cypher-compatibility/)，
用法见 [HugeGraph Cypher](/cn/docs/language/hugegraph-cypher/)。

### 可以直接带过来的部分

| Neo4j 概念 | HugeGraph 对应 |
|---|---|
| 属性图模型（节点/关系/属性） | 相同 —— 顶点标签 / 边标签 / 属性 |
| 基础 Cypher：`MATCH`/`WHERE`/`RETURN`/`CREATE`/`SET`/`DELETE` | 直接可用（REST `/cypher` 端点或 Java 客户端 `CypherManager`） |
| 简单聚合（`count`/`sum`/`min`/`max`/`avg`） | 直接可用 |
| 依赖图遍历的查询需求 | Gremlin 遍历或 [traverser REST API](/cn/docs/clients/restful-api/traverser/)（k-out、最短路、personalrank 等） |

### 需要改变习惯的部分

| 在 Neo4j 里 | 在 HugeGraph 里 |
|---|---|
| `CREATE INDEX` / `CREATE CONSTRAINT` | 通过 [schema REST API](/cn/docs/clients/restful-api/schema/) 建索引/约束；Cypher 不承载 DDL |
| 隐式 schema（属性随意添加） | **强 schema**：先定义 VertexLabel/EdgeLabel/PropertyKey，再写数据 |
| 参数化查询 `$param` | 暂不支持 —— 在客户端转义/校验后拼接字面量 |
| `CALL dbms.*` / `CALL algo.*` 过程 | 对应功能分散在 [traverser](/cn/docs/clients/restful-api/traverser/)、[task](/cn/docs/clients/restful-api/task/) 等 REST API |
| 驱动：Neo4j Bolt driver | [hugegraph-client](/cn/docs/clients/hugegraph-client/)（`CypherManager`）或任意 HTTP 客户端 |
| 事务边界在 Cypher 语句内 | 每次请求一个语句；批量写入用 [Loader](/cn/docs/guides/toolchain/) 或 bulkport |

### 建议的迁移路径

1. **盘点查询**：把应用里的 Cypher 按
   [兼容性矩阵](/cn/docs/language/cypher-compatibility/) 分成
   "直接可用 / 需改写为 Gremlin / 需换 REST API" 三类。
2. **先建 schema**：用 schema API 建好 VertexLabel/EdgeLabel/PropertyKey 和索引 ——
   HugeGraph 在写入前要求 schema 存在。
3. **导入数据**：小数据集用 REST；大批量用
   [HugeGraph Loader](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-loader)。
4. **灰度切换**：Cypher 能表达的查询保持不动， translator 不支持的改写为
   Gremlin（等价写法见 [对照表](/cn/docs/language/hugegraph-cypher/#等价的-gremlin-写法)）。

### 已知限制速查

- Cypher 语句不支持参数绑定、多语句脚本与 `CALL` 过程。
- 转译器最后一次发布是 2019-11（1.0.4），其自身 TCK 报告为
  879 通过 / 79 失败（约 91.7%）—— 未覆盖的语法会在翻译期报错。
- 不支持的写法始终可以用等价 Gremlin 表达 —— 见
  [HugeGraph Cypher 的对照表](/cn/docs/language/hugegraph-cypher/#等价的-gremlin-写法)。
