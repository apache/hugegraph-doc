---
title: "Cypher 兼容性"
linkTitle: "Cypher 兼容性"
weight: 3
---

### 范围

本页记录当前 Cypher 开发改动实际验证过的用例，不代表完整支持 openCypher 或 Neo4j，也不代表所有已发布
版本的 HugeGraph 都具备相同行为。测试代码基于
[`hugegraph/hugegraph@27a7c9b`](https://github.com/hugegraph/hugegraph/commit/27a7c9b42274d6d4f95eabed6d2051d393ae0eaf)，
使用 Java `17.0.20.1`、TinkerPop `3.8.1`、`org.opencypher.gremlin:translation:1.0.4` 和 RocksDB。

接口路径为 `/graphspaces/{graphspace}/graphs/{graph}/cypher`。一般用法见
[HugeGraph Cypher 指南](/cn/docs/language/hugegraph-cypher/)。

### 请求形式与参数

| 请求 | 已验证行为 | 测试方法 |
|---|---|---|
| `GET ?cypher=<URL 编码的语句>` | 保留原有查询参数形式 | `testGet` |
| `POST application/json`，请求体为原始 Cypher 文本 | 保留旧的原始文本请求形式 | `testPost` |
| `POST text/plain`，请求体为原始 Cypher 文本 | 支持纯文本请求 | `testPlainTextPost` |
| `POST application/json`，请求体为 JSON 对象 | 查询语句与参数分开传入 | `testParameters` |

```json
{
  "cypher": "MATCH (n:cypher_person) WHERE n.name = $name RETURN n.name",
  "parameters": {"name": "marko"}
}
```

JSON 对象中的 `cypher` 必须是非空字符串；`parameters` 若提供，必须是对象。省略 `parameters` 表示空参数表。
语句引用了未提供的参数时会报执行错误；显式传入 `null` 是有效值。测试覆盖字符串、数字、布尔值、引号和换行，
参数名 `id` 与 `label`，以及默认最多 16 个参数。参数值会作为绑定值传递，不会改写查询文本。

同时检查 HTTP 状态和响应体的 `status.code`：执行错误可能仍返回 HTTP 200，但 `status.code` 为 400，结果数据为 null。

### 已验证行为

API 测试夹具使用强类型 Schema，并为 `city` 建立 `SECONDARY` 索引、为 `age` 建立 `RANGE` 索引。验收结论仅限于下列用例：

| 范围 | 测试用例 | 测试方法 |
|---|---|---|
| 查询 | 标签扫描、相等和范围条件、布尔组合、有向一跳和两跳关系、空结果 | `testGet`、`testExactReadsAndPredicates`、`testRelationQuery` |
| 结果 | 别名、标量和节点值、嵌套值、关系 ID、路径结构、null 与缺失属性 | `testReturnNodeIdAsPrimitiveValue`、`testReturnNodeDoesNotLeakInternalIdTypes`、`testReturnNestedIdDoesNotLeakInternalIdTypes`、`testReturnRelationIdDoesNotLeakInternalIdTypes`、`testReturnPathShape`、`testNullAndMissingProperty` |
| 聚合和分页 | `DISTINCT`、`count`/`sum`/`min`/`max`/`avg`、`ORDER BY`、`SKIP`、`LIMIT` | `testDuplicatesDistinctAndPagination`、`testAggregates` |
| 写入 | 创建顶点和边、修改属性、删除边和顶点；通过原生 REST 读取检查状态 | `testCreate`、`testCreateSetAndDeleteWithNativeReadback` |
| 失败写入 | 拒绝双顶点 `CREATE` 后，连续 32 次查询和原生读取均未发现残留 | `testFailedWriteDoesNotLeakIntoLaterRequests` |
| 错误与路由 | 非法语法和请求结构、参数键、Schema 值、认证及图路由 | `testInvalidRequests`、`testRejectInvalidQuery`、`testRejectInvalidBindingShapeAndKeys`、`testAuthenticationAndGraphRouting`、`testSpecifiedGraphRouting` |

`CypherApiTest` 通过 20/20，`CypherClientTest` 通过 7/7，`CypherOpProcessorTest` 通过 4/4，均无跳过。
相关 Gremlin 测试通过 10 项，另有一项 `testClearAndInit` 因后端不共享而不适用；Login 测试通过 3/3。
EditorConfig 格式检查和仓库根目录 clean compile 均通过。代码改动位于
[PR #238](https://github.com/hugegraph/hugegraph/pull/238)。固定测试提交
[`c3b2f3e`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/docs/cypher-compatibility.md)
中的兼容性说明包含逐方法测试映射和验证记录。该提交的测试源码：
[`CypherApiTest`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/api/CypherApiTest.java)、
[`CypherClientTest`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/api/cypher/CypherClientTest.java)
和
[`CypherOpProcessorTest`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/opencypher/CypherOpProcessorTest.java)。

### 基线故障与当前修复

在上述固定基线提交中，失败的双顶点 `CREATE` 在两次观察中都留下了延迟可见的残留。第一次运行中，即时原生读取未发现前缀，
但后续聚合/排序查询暴露了前缀，原生全量列表也确认了它。第二次复现时，即时原生读取和之后 7 次 count/原生读取均未见前缀；
第 8 次 count 后才出现。原始基线证据保留在
[基线报告](https://github.com/apache/hugegraph-doc/pull/499#issuecomment-5826172378)。

当前开发改动通过了 `testFailedWriteDoesNotLeakIntoLaterRequests`：针对该夹具，原生读取和后续 32 轮查询/原生读取均确认无残留。
这只验证了已报告的失败场景及当前测试栈，不能据此推断所有回滚路径、跨请求事务语义、所有语句或后端的写原子性。

### 本次未验证

本次测试范围之外的高级语法和行为仍未验证，包括 `MERGE`、`OPTIONAL MATCH`、`WITH`、`UNWIND`、`UNION`、变长路径、
广泛的函数覆盖、过程调用、Cypher Schema DDL、`EXPLAIN`/`PROFILE`、HStore、Bolt、跨请求事务和性能。
