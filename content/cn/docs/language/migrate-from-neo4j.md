---
title: "从 Neo4j 迁移"
linkTitle: "从 Neo4j 迁移"
weight: 4
---

### 本页面向谁

正在评估 HugeGraph 的 Neo4j 用户。HugeGraph 的 Cypher 覆盖面由
[cypher-for-gremlin](https://github.com/opencypher/cypher-for-gremlin) 转译器决定，
与 Neo4j 并非 1:1 等价 —— 已验证与未验证范围见
[Cypher 兼容性说明](/cn/docs/language/cypher-compatibility/)，
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
| 参数化查询 `$param` | 已发布版本仅发送原始语句 —— 缺失的绑定会被求值为 `null`（空结果），请在客户端校验取值；JSON 绑定参数随 [PR #238](https://github.com/hugegraph/hugegraph/pull/238) 落地 |
| `CALL dbms.*` / `CALL algo.*` 过程 | 对应功能分散在 [traverser](/cn/docs/clients/restful-api/traverser/)、[task](/cn/docs/clients/restful-api/task/) 等 REST API |
| 驱动：Neo4j Bolt driver | [hugegraph-client](/cn/docs/clients/hugegraph-client/)（`CypherManager`）或任意 HTTP 客户端 |
| 事务边界在 Cypher 语句内 | 每次请求一个语句；图到图的数据迁移使用 [Apache SeaTunnel 3.0.0](https://seatunnel.apache.org/download/)（首选 —— 见下文），基于文件的批量导入使用 [HugeGraph Loader](/cn/docs/quickstart/toolchain/hugegraph-loader/) |

### 建议的迁移路径

1. **盘点查询**：把应用里的 Cypher 按
   [兼容性说明](/cn/docs/language/cypher-compatibility/) 分成
   "直接可用 / 需改写为 Gremlin / 需换 REST API" 三类。
2. **先建 schema**：用 schema API 建好 VertexLabel/EdgeLabel/PropertyKey 和索引 ——
   HugeGraph 在写入前要求 schema 存在。
3. **导入数据**：首选路径是 [Apache SeaTunnel 3.0.0](https://seatunnel.apache.org/download/)
   （2026-09-29 发布），直接运行 **Neo4j Source → HugeGraph Sink** —— 无需中间文件导出。
   小数据集用 REST 也没问题；基于文件的大批量导入仍可使用
   [HugeGraph Loader](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-loader)。
   HugeGraph 侧的环境准备、`mappings` 配置与顶点/边导入示例见
   [通过 SeaTunnel Sink 导入图数据](/cn/docs/quickstart/toolchain/import/hugegraph-seatunnel-connector/)。

   [SeaTunnel 3.0.0 连接器文档](https://seatunnel.apache.org/docs/3.0.0/about/) 说明了可依赖的能力：
   - [Neo4j Source](https://seatunnel.apache.org/docs/3.0.0/connectors/source/Neo4j/) 以显式字段
     schema 读取 Cypher 查询结果；3.0.0 新增通过 `tables_configs` 的多表读取。
   - [HugeGraph Sink](https://seatunnel.apache.org/docs/3.0.0/connectors/sink/HugeGraph/) 在 3.0.0
     中重构，支持多映射 —— 顶点/边请使用推荐的 `mappings` 配置，并遵循其 schema 创建行为。
   - [HugeGraph Source](https://seatunnel.apache.org/docs/3.0.0/connectors/source/HugeGraph/) 为
     3.0.0 新增（schema 自动发现、多标签/并行读取），使 HugeGraph 的导出与迁移工作流成为可能。

   将 Neo4j 属性映射为 HugeGraph PropertyKey，保持稳定顶点 ID 不变，把边的端点映射到已存在的
   顶点 ID，并先导入顶点、后导入边。以上能力均有文档记载，但这里没有完整跑通一次 Neo4j →
   HugeGraph 迁移 —— 在把示例当作已验证之前，请先用你自己的数据验证。
4. **灰度切换**：Cypher 能表达的查询保持不动， translator 不支持的改写为
   Gremlin（等价写法见 [对照表](/cn/docs/language/hugegraph-cypher/#等价的-gremlin-写法)）。

### 已知限制速查

- 已发布版本不支持参数绑定（缺失的绑定会被求值为 `null`，见上表）、
  多语句脚本与 `CALL` 过程。
- 转译器最后一次发布是 2019-11（1.0.4），其自身 TCK 报告为
  879 通过 / 79 失败（约 91.7%）—— 未覆盖的语法会在翻译期报错。
- 不受支持的查询结构通常可以改写为等价的 Gremlin 遍历 —— 见
  [HugeGraph Cypher 的对照表](/cn/docs/language/hugegraph-cypher/#等价的-gremlin-写法)；
  schema DDL 与 `CALL` 过程请改用 REST API。
