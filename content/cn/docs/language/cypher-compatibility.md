---
title: "Cypher 兼容性"
linkTitle: "Cypher 兼容性"
weight: 3
---

### 范围

**下文验证结果描述的是 `master`，不能直接套用于已发布版本。** 已发布版本在
`/graphspaces/{graphspace}/graphs/{graph}/cypher` 上只提供两种请求形式：`GET ?cypher=<URL 编码的语句>`
和 `POST application/json`（请求体为原始 Cypher 文本）。已发布版本不接受绑定参数，引用 `$param` 的语句
不会报错，而是返回空结果——参见[已知限制](/cn/docs/language/hugegraph-cypher/#已知限制)。

本页记录当前 Cypher 开发改动实际验证过的用例，不代表完整支持 openCypher 或 Neo4j，也不代表所有已发布
版本的 HugeGraph 都具备相同行为。测试代码基于当前 Apache `master` 的
[`af3c686`](https://github.com/apache/hugegraph/commit/af3c6867f4bfa3f95e63ad472c12a88c63529c1b)，
该基线声明 HugeGraph `1.8.0`，使用 Java 17 和 TinkerPop `3.8.1`。Cypher 改动独立建立在该基线上。运行栈使用 Java `17.0.20.1`、
TinkerPop `3.8.1`、`org.opencypher.gremlin:translation:1.0.4` 和 RocksDB。

接口路径为 `/graphspaces/{graphspace}/graphs/{graph}/cypher`。一般用法见
[HugeGraph Cypher 指南](/cn/docs/language/hugegraph-cypher/)。

### 请求形式与参数

| 请求 | 是否存在于已发布版本 | 测试栈上已验证行为 | 测试方法 |
|---|---|---|---|
| `GET ?cypher=<URL 编码的语句>` | 是 | 保留原有查询参数形式 | `testGet` |
| `POST application/json`，请求体为原始 Cypher 文本 | 是 | 保留旧的原始文本请求形式 | `testPost` |
| `POST text/plain`，任意请求体 | 否 | 返回 HTTP 415 | `testRejectPlainTextPost` |
| `POST application/json`，请求体为 JSON 对象 | 否 — 由 [#3289](https://github.com/apache/hugegraph/pull/3289) 引入 | 查询语句与参数分开传入 | `testParameters` |

因此下面的 JSON 对象形式**在任何已发布的 HugeGraph 版本中都不可用**，它描述已合入 `master`（1.8.0 开发线）的改动。
在已发布版本上，引用 `$param` 的语句会把该参数绑定为 `null` 并返回空结果——参见
[已知限制](/cn/docs/language/hugegraph-cypher/#已知限制)。

```json
{
  "cypher": "MATCH (n:cypher_person) WHERE n.name = $name RETURN n.name",
  "parameters": {"name": "marko"}
}
```

JSON 数组、字符串、数字、布尔值或 null 请求体会返回 HTTP 400。
格式错误的 JSON 对象和尾随内容也会产生请求错误，不会回退为原始 Cypher 文本。

JSON 对象中的 `cypher` 必须是非空字符串；`parameters` 若提供，必须是对象。省略 `parameters` 表示空参数表。
语句引用了未提供的参数时会报执行错误；显式传入 `null` 是有效值。测试覆盖字符串、数字、布尔值、引号和换行，
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

独立代码改动位于 [ASF PR #3289](https://github.com/apache/hugegraph/pull/3289)，该 PR 已于 2026-10-08 合入 Apache `master`，合入提交为
[`5039e5b`](https://github.com/apache/hugegraph/commit/5039e5b67d26ea305b8509d3a414877749baaebb)。上述固定基线仍对应合入前的实际验证。
原始开发改动仍关联 [PR #238](https://github.com/hugegraph/hugegraph/pull/238)。
在固定源码提交
[`8d06ad3`](https://github.com/apache/hugegraph/blob/8d06ad3b18fbd18807cf545184d07e6fec0c55b4/docs/cypher-compatibility.md) 上，`CypherApiTest` 通过 23/23，
`CypherClientTest` 通过 7/7，`CypherOpProcessorTest` 通过 8/8，均无跳过。新增的谓词、执行上下文和请求资源所有权
回归测试均通过；`AbstractRestClientTest` 的九项测试也全部通过，包括 ASCII 请求体、UTF-16 Map 请求体及 gzip。
Login 测试通过 3/3；相关 Gremlin 测试通过 10 项，保留一项因后端不共享而不适用的 `testClearAndInit` 跳过。
EditorConfig 格式检查、仓库根目录 clean compile 和完整 install 均通过。在实际服务测试前，分发包内的 API JAR 与编译目标 JAR 一致。

该固定提交中的兼容性说明包含验证记录和逐方法映射。测试源码：
[`CypherApiTest`](https://github.com/apache/hugegraph/blob/8d06ad3b18fbd18807cf545184d07e6fec0c55b4/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/api/CypherApiTest.java)、
[`CypherClientTest`](https://github.com/apache/hugegraph/blob/8d06ad3b18fbd18807cf545184d07e6fec0c55b4/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/api/cypher/CypherClientTest.java)
和
[`CypherOpProcessorTest`](https://github.com/apache/hugegraph/blob/8d06ad3b18fbd18807cf545184d07e6fec0c55b4/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/opencypher/CypherOpProcessorTest.java)。
此前在
[`e62c961`](https://github.com/apache/hugegraph/commit/e62c961e00221569d4f955abbadf60faee45b283)
基线上的验证仍保留在
[`fd8f4a6`](https://github.com/apache/hugegraph/blob/fd8f4a626b9e899663d3114035e2967e421b3e55/docs/cypher-compatibility.md)。
此前变基前的验证记录仍保留在
[`c3b2f3e`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/docs/cypher-compatibility.md)。

### 基线故障与当前修复

在此前的基线
[`27a7c9b`](https://github.com/apache/hugegraph/commit/27a7c9b42274d6d4f95eabed6d2051d393ae0eaf)
中，失败的双顶点 `CREATE` 在两次观察中都留下了延迟可见的残留。第一次运行中，即时原生读取未发现前缀，
但后续聚合/排序查询暴露了前缀，原生全量列表也确认了它。第二次复现时，即时原生读取和之后 7 次 count/原生读取均未见前缀；
第 8 次 count 后才出现。原始基线证据保留在
[基线报告](https://github.com/apache/hugegraph-doc/pull/499#issuecomment-5826172378)。

当前开发改动通过了 `testFailedWriteDoesNotLeakIntoLaterRequests`：针对该夹具，原生读取和后续 32 轮查询/原生读取均确认无残留。
这只验证了已报告的失败场景及当前测试栈，不能据此推断所有回滚路径、跨请求事务语义、所有语句或后端的写原子性。

### 本次未验证

本次测试范围之外的高级语法和行为仍未验证，包括 `MERGE`、`OPTIONAL MATCH`、`WITH`、`UNWIND`、`UNION`、变长路径、
广泛的函数覆盖、过程调用、Cypher Schema DDL、`EXPLAIN`/`PROFILE`、HStore、Bolt、跨请求事务和性能。
