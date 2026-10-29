---
title: "Cypher 兼容性"
linkTitle: "Cypher 兼容性"
weight: 3
---

### 范围

**下文验证结果描述的是 `master`，不能直接套用于已发布版本。** HugeGraph 1.7.0 在
`/graphspaces/{graphspace}/graphs/{graph}/cypher` 上只提供两种请求形式：`GET ?cypher=<URL 编码的语句>`
和 `POST application/json`（请求体为原始 Cypher 文本）。1.7.0 之前的版本在 `/graphs/{graph}/cypher` 下
提供同样的两种形式。已发布版本不接受绑定参数，引用 `$param` 的语句
不会报错，缺失的绑定会被内联为 `null`（基于它的谓词匹配不到行，而 `RETURN $value AS value` 仍会返回一行）——参见[已知限制](/cn/docs/language/hugegraph-cypher/#已知限制)。

本页记录 Cypher 语法的实际验证用例与行为边界，不代表完整支持 openCypher 或 Neo4j，也不代表所有已发布
版本的 HugeGraph 都具备相同行为。Cypher 参数绑定与语法增强自 1.8.0（基于 Java 17 与 TinkerPop 3.8.1）起合入。

接口路径为 `/graphspaces/{graphspace}/graphs/{graph}/cypher`。一般用法见
[HugeGraph Cypher 指南](/cn/docs/language/hugegraph-cypher/)。

### 请求形式与参数

| 请求 | 是否存在于已发布版本 | 测试栈上已验证行为 | 测试方法 |
|---|---|---|---|
| `GET ?cypher=<URL 编码的语句>` | 是 | 保留原有查询参数形式 | `testGet` |
| `POST application/json`，请求体为原始 Cypher 文本 | 是 | 保留旧的原始文本请求形式 | `testPost` |
| `POST text/plain`，任意请求体 | 否 | 返回 HTTP 415 | `testRejectPlainTextPost` |
| `POST application/json`，请求体为 JSON 对象 | 否 — 自 1.8.0 起支持 | 查询语句与参数分开传入 | `testParameters` |

因此下面的 JSON 对象形式**在 1.7.0 及更早版本中不可用**，它描述 1.8.0 起支持的功能。
在已发布版本上，引用 `$param` 的语句会把缺失的绑定内联为 `null`，是否返回行取决于表达式（`WHERE n.name = $name` 匹配不到行，`RETURN $value AS value` 会返回一行 `null`）——参见
[已知限制](/cn/docs/language/hugegraph-cypher/#已知限制)。

```json
{
  "cypher": "MATCH (n:cypher_person) WHERE n.name = $name RETURN n.name",
  "parameters": {"name": "marko"}
}
```

JSON 数组、字符串、数字、布尔值或 null 请求体会返回 HTTP 400。
格式错误的 JSON 对象和尾随内容也会产生请求错误，不会回退为原始 Cypher 文本。

JSON 对象中的 `cypher` 必须是非空白字符串；`parameters` 若提供，必须是对象。省略 `parameters` 表示空参数表。
语句引用了未提供的参数时会报执行错误；显式传入 `null` 是有效值。在测试栈上，该执行错误适用于所有请求形式，
包括 `GET ?cypher=` 和原始文本 `POST`：自 1.8.0 起总是附带
参数表并拒绝未解析的 `$param` 引用，取代了上文描述的已发布版本“缺失绑定按 `null` 处理”行为。测试覆盖字符串、数字、布尔值、引号和换行，
参数名 `id` 与 `label`。当前实现的 `parameters` 最多接受 16 个顶层条目，该上限固定。
该上限只统计顶层 `parameters` 对象中的键。Cypher 不支持在 Gremlin Server 的处理器配置中设置
`maxParameters`。参数值会作为绑定值传递，不会改写查询文本。

一个 Map 只计为一个顶层参数。可以将相关值放入一个 Map，并显式引用各字段；顶点标签和必需属性必须匹配图中已有的 Schema：

```json
{
  "cypher": "CREATE (n:cypher_person {name:$props.name, age:$props.age, city:$props.city}) RETURN n.name",
  "parameters": {"props": {"name": "new-person", "age": 20, "city": "Beijing"}}
}
```

实际 REST 验证确认，一个包含 17 个条目的 Map 可以通过显式属性引用完成写入，并通过原生 REST 核对全部 17 个持久化值。
返回包含 17 个条目的 Map 也成功，而 17 个顶层绑定参数会产生执行错误。请使用上述显式属性引用；
固定版本的转译库不会通过 CREATE 的简写形式赋予绑定 Map 中的属性。

转译库将精确字符串 `"  cypher.null"`（开头有两个空格）保留为 null 标记，因此绑定值会拒绝该字符串，
包括列表和嵌套 Map 中的值。显式 null 仍受支持。语句字面量及存储属性等于该字符串的情况仍受转译库限制，
本次改动未验证这些值能够保真。

同时检查 HTTP 状态和响应体的 `status.code`：执行错误可能仍返回 HTTP 200，但 `status.code` 为 400，结果数据为 null。

### 已验证行为

API 测试夹具使用强类型 Schema，并为 `city` 建立 `SECONDARY` 索引、为 `age` 建立 `RANGE` 索引。验收结论仅限于下列用例：

| 范围 | 测试用例 | 测试方法 |
|---|---|---|
| 查询 | 标签扫描、相等和范围条件、布尔组合、有向一跳和两跳关系、空结果、计算字符串的正则全字符串匹配 | `testGet`、`testExactReadsAndPredicates`、`testRelationQuery`、`testComputedRegexExecutesExtensionPredicate`、`testComputedRegexRequiresWholeStringMatch` |
| 结果 | 别名、标量和节点值、嵌套值、关系 ID、路径结构、null 与缺失属性 | `testReturnNodeIdAsPrimitiveValue`、`testReturnNodeDoesNotLeakInternalIdTypes`、`testReturnNestedIdDoesNotLeakInternalIdTypes`、`testReturnRelationIdDoesNotLeakInternalIdTypes`、`testReturnPathShape`、`testNullAndMissingProperty` |
| 聚合和分页 | `DISTINCT`、`count`/`sum`/`min`/`max`/`avg`、`ORDER BY`、`SKIP`、`LIMIT` | `testDuplicatesDistinctAndPagination`、`testAggregates` |
| 写入 | 创建顶点和边、修改属性、删除边和顶点；通过原生 REST 读取检查状态 | `testCreate`、`testCreateSetAndDeleteWithNativeReadback` |
| 失败写入 | 拒绝双顶点 `CREATE` 后，连续 32 次查询和原生读取均未发现残留 | `testFailedWriteDoesNotLeakIntoLaterRequests` |
| 错误与路由 | 非法语法和请求结构、内容类型、参数键与保留的 null 标记、Schema 值、认证及图路由 | `testInvalidRequests`、`testRejectPlainTextPost`、`testRejectInvalidQuery`、`testRejectInvalidBindingShapeAndKeys`、`testRejectTranslatorNullMarker`、`testRejectTranslatorNullSentinelInBindings`、`testAuthenticationAndGraphRouting`、`testSpecifiedGraphRouting` |

合入后在 `5039e5b` 上的补充 REST 验证对全新 RocksDB 图重新执行了文档示例：查询、带排序和 LIMIT 的投影、聚合、
单顶点 `CREATE`、`SET`/`REMOVE`、边 `DELETE`、`DETACH DELETE`，以及上表全部请求形式约定均与文档一致，
包括三种请求形式下缺失绑定的执行错误。双顶点简写 `CREATE (a)-[:knows]->(b)` 在同一运行中于 `person` 标签使用
`AUTOMATIC` id 策略的图上验证通过；在 `PRIMARY_KEY` 标签上，同一语句会被拒绝并返回执行错误（提示必须设置主键），
而同一标签上的单顶点 `CREATE` 成功。在 `PRIMARY_KEY` Schema 上，请将两条 `CREATE` 语句分开执行，或对该形式使用
`AUTOMATIC` id 策略。

指南中有两个示例依赖 Schema。范围谓词查询（`WHERE n.age > 30`）需要上文夹具 Schema 中声明的 `age` 上的 `RANGE` 索引；
`scripts/example.groovy` 的 Schema 只为 `person` 建了 `SECONDARY` 索引（`city`，以及 `age` 与 `city` 的组合），
因此在那里对 `age` 做范围比较会被拒绝并报“未建索引”错误，直到建立 `RANGE` 索引。创建、更新和删除示例随后改名为
`alice`、`bob` 和 `carol`，因为 `scripts/example.groovy` 已预置 `marko`、`vadas`、`josh` 和 `peter`，而在 `PRIMARY_KEY` 标签上
用预置名字执行 `CREATE` 会替换该顶点；改名只改动数据取值，没有作为单独的验证重新运行。

### 测试与实现边界

相关单元测试与集成测试覆盖 `CypherApiTest`、`CypherClientTest` 与 `CypherOpProcessorTest`。
在 `PRIMARY_KEY` 策略的 Schema 下，双顶点简写 `CREATE (a)-[:knows]->(b)` 会因缺少主键而被拒绝；而在 `AUTOMATIC` 策略下支持该简写。对于 `PRIMARY_KEY` Schema，建议将两条创建语句分开执行。

### 未验证范围

以下高级语法和特性当前尚未在 HugeGraph 上完成端到端验证，生产环境使用时请予以注意：
- 复杂语法与子句：`MERGE`、`OPTIONAL MATCH`、`WITH`、`UNWIND`、`UNION`、变长路径匹配；
- 扩展能力：过程调用（Procedures）、Cypher Schema DDL、`EXPLAIN` / `PROFILE`；
- 协议与驱动：Bolt 协议驱动、跨请求事务。
