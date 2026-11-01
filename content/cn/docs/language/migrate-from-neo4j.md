---
title: "从 Neo4j 迁移"
linkTitle: "从 Neo4j 迁移"
weight: 4
---

### 概述

面向从 Neo4j 迁移或评估 HugeGraph 的开发者。HugeGraph 原生支持 openCypher 声明式查询语法，
但在图模型、Schema 规范、参数绑定和索引机制上与 Neo4j 存在差异。
具体语法与兼容性请参考 [HugeGraph Cypher](/cn/docs/language/hugegraph-cypher/) 与 [Cypher 兼容性说明](/cn/docs/language/cypher-compatibility/)。

### 可以直接带过来的部分

| Neo4j 概念 | HugeGraph 对应 |
|---|---|
| 属性图模型（节点/关系/属性） | 相同 —— 顶点标签 / 边标签 / 属性 |
| 基础 Cypher：`MATCH`/`WHERE`/`RETURN`/`CREATE`/`SET`/`DELETE` | 直接可用（REST `/cypher` 端点或 Java 客户端 `CypherManager`），但须遵守下文的 Schema 与索引规则 |
| 简单聚合（`count`/`sum`/`min`/`max`/`avg`） | 直接可用 |
| 依赖图遍历的查询需求 | Gremlin 遍历或 [traverser REST API](/cn/docs/clients/restful-api/traverser/)（k-out、最短路、personalrank 等） |
{.wide}

### 需要改变习惯的部分

| 在 Neo4j 里 | 在 HugeGraph 里 |
|---|---|
| `CREATE INDEX` / `CREATE CONSTRAINT` | 通过 [IndexLabel REST API](/cn/docs/clients/restful-api/indexlabel/) 创建属性索引；唯一性约束对应 `UNIQUE` 索引；节点键对应非可空属性加复合 `UNIQUE` 索引；属性存在约束对应 [VertexLabel](/cn/docs/clients/restful-api/vertexlabel/) / [EdgeLabel](/cn/docs/clients/restful-api/edgelabel/) 上的非可空属性。注意 `primary_keys` 决定顶点标识，不是约束机制，重复 `CREATE` 直接覆盖旧记录 |
| 隐式 schema（属性随意添加） | **强 schema**：先定义 VertexLabel/EdgeLabel/PropertyKey，再写数据 |
| `WHERE` 中的属性谓词无需索引 | 起始顶点查找需要索引覆盖（除非对该标签全部主键做等值匹配）：`>` / `<` 等范围比较需要 `RANGE` 类型的 IndexLabel。缺少覆盖索引时返回 HTTP 200（响应体 `status.code` 400 "未建索引"错误） |
| 参数化查询 `$param` | 支持 JSON 格式参数化请求（最多支持 16 个顶层参数，更多属性可通过嵌套 Map 传递）；未声明的参数会报错 |
| `CALL dbms.*` / `CALL algo.*` 过程 | 对应功能分散在 [traverser](/cn/docs/clients/restful-api/traverser/)、[task](/cn/docs/clients/restful-api/task/) 等 REST API |
| 驱动：Neo4j Bolt driver | [hugegraph-client](/cn/docs/clients/client/hugegraph-client/)（`CypherManager`）或任意 HTTP 客户端 |
| 事务边界在 Cypher 语句内 | 每次请求一个语句；图到图的数据迁移使用 [Apache SeaTunnel 3.0.0](https://seatunnel.apache.org/download/)（首选，见下文），基于文件的批量导入使用 [HugeGraph Loader](/cn/docs/quickstart/toolchain/hugegraph-loader/) |
{.wide}

`PRIMARY_KEY` 标签上 `UNIQUE` 索引不能包含该标签的全部主键（服务端会拒绝）。若需保留唯一性约束，请改用 `CUSTOMIZE_STRING` id 策略，以 Neo4j 节点 id 为键，再在业务键上建 `UNIQUE` 索引。

### 建议的迁移路径

1. **盘点查询**：对照 [Cypher 兼容性说明](/cn/docs/language/cypher-compatibility/) 与
   [使用限制](/cn/docs/language/hugegraph-cypher/#使用限制)，梳理应用中的 Cypher 语句，
   确认直接可用、需改写为 Gremlin 或需调用 REST API 的部分。
2. **先建 schema**：用 schema API 建好 VertexLabel/EdgeLabel/PropertyKey 和索引 ——
   HugeGraph 在写入前要求 schema 存在。
3. **导入数据**：首选路径是 [Apache SeaTunnel](https://seatunnel.apache.org/download/)
   的 `Neo4j` Connector（Source）与 `HugeGraph` Connector（Sink），直接运行 **Neo4j Source → HugeGraph Sink** —— 无需中间文件导出。
   小数据集用 REST 也没问题；基于文件的大批量导入仍可使用
   [HugeGraph Loader](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-loader)。
   HugeGraph 侧的环境准备、`mappings` 配置与顶点/边导入示例见
   [通过 SeaTunnel Sink 导入图数据](/cn/docs/quickstart/toolchain/import/hugegraph-seatunnel-connector/)。

   [SeaTunnel 连接器文档](https://seatunnel.apache.org/docs/3.0.0/introduction/about/) 说明了可依赖的能力：
   - [Neo4j Source](https://seatunnel.apache.org/docs/3.0.0/connectors/source/Neo4j/) 以显式字段
     schema 读取 Cypher 查询结果，支持通过 `tables_configs` 的多表读取。
   - [HugeGraph Sink](https://seatunnel.apache.org/docs/3.0.0/connectors/sink/HugeGraph/)
    支持多映射 —— 顶点/边请使用推荐的 `mappings` 配置，并遵循其 schema 创建行为。该 Sink 默认
    遇到错误快速失败（`batch_failure_fallback=false` 与 `max_insert_errors=0`）。跳过失败记录为
    可选配置（`batch_failure_fallback=true`）；若开启，请在正式切换前捕获并核对跳过行，并比对数据总条数。
   - [HugeGraph Source](https://seatunnel.apache.org/docs/3.0.0/connectors/source/HugeGraph/)
     支持 schema 自动发现与多标签并行读取，使 HugeGraph 的导出与迁移工作流成为可能。

   将 Neo4j 属性映射为 HugeGraph PropertyKey，并在导入前先定好顶点 ID 策略。Sink 对除 `AUTOMATIC`
   之外的每种顶点策略都要求 `idFields`，边映射还需要分别设置 `sourceConfig.idFields` 与
   `targetConfig.idFields`，因此 Neo4j 查询必须返回承载 ID 的字段：
   - `idStrategy = "PRIMARY_KEY"`：在 `idFields` 中放入 Neo4j 业务键，边的端点也通过这些键字段表达。
   - `idStrategy = "CUSTOMIZE_STRING"`：仅选择它并不能保留 Neo4j 节点 id。请让 Neo4j 查询把要保留的 id
     作为单独一列返回（用 `AS node_id` 等别名），在 Source 的 `schema.fields` 中声明该字段（必须与查询返回的字段一致），
     把顶点的 `idFields` 设为该字段，并在 `sourceConfig.idFields` 与 `targetConfig.idFields` 中映射对应的边端点字段。

   第 2 步预创建的标签必须使用同一策略——自动创建不会把已有的 `PRIMARY_KEY` 标签改为 `CUSTOMIZE_STRING`。
   Sink 的 `mappings` 配置可以创建缺失的 PropertyKey、VertexLabel 和 EdgeLabel 定义，因此使用它时第 2 步中的这三类
   定义可省略；但它不会创建 IndexLabel，查询所依赖的索引仍须单独创建（见上文“需要改变习惯的部分”表）。
   若未显式指定 `frequency`，自动创建 EdgeLabel 时默认采用 `SINGLE`，相同类型且端点相同的多条平行关系（Parallel Relationships）会被覆盖合并为一条边。
   若需保留 Neo4j 中的平行边，必须在边映射中显式指定 `frequency = "MULTIPLE"`，并配置稳定的业务区分字段作为 `sortKeys`（HugeGraph 依赖 sortKeys 生成重边的唯一边 ID）。
   先导入顶点、后导入边。建议在正式切换前，先在测试环境中使用业务数据样本完整验证导入流程。
4. **灰度切换**：Cypher 能表达的查询保持不动，暂不支持的改写为
   Gremlin（等价写法见 [对照表](/cn/docs/language/hugegraph-cypher/#等价的-gremlin-写法)）。

### 使用限制速查

- **语句与参数**：不支持多语句脚本与 `CALL` 过程；参数绑定最多支持 16 个顶层参数（更多属性可通过嵌套 Map 传递）。
- **未覆盖语法**：兼容性矩阵中未涉及的高级 openCypher 结构属于未验证范围，可能在解析校验期报错；明确不支持的限制见前文说明。
- **回退方案**：不受支持的查询结构通常可以改写为等价的 Gremlin 遍历 —— 详见
  [HugeGraph Cypher 对照表](/cn/docs/language/hugegraph-cypher/#等价的-gremlin-写法)；
  Schema DDL 与存储过程请改用对应 REST API。
