---
title: "Cypher 兼容性"
linkTitle: "Cypher 兼容性"
weight: 3
---

### 本页范围

HugeGraph 通过 [`cypher-for-gremlin`](https://github.com/opencypher/cypher-for-gremlin)
转译器（`org.opencypher.gremlin:translation:1.0.4`，发布于 2019-11-05）把 Cypher
翻译成 Gremlin 执行。因此 HugeGraph 的 Cypher 覆盖面等于该转译器实现的
openCypher 9 子集 —— 用法见 [HugeGraph Cypher](/cn/docs/language/hugegraph-cypher/)，
简版限制见[已知限制](/cn/docs/language/hugegraph-cypher/#已知限制)。

转译器 1.0.4 自报的 conformance 数据为 **879 通过 / 79 失败（约 91.7%）**。
下表按现有证据对特性分级；它不能替代对你的真实负载做测试。

### 特性矩阵

| openCypher 特性 | 状态 | 证据层级 | 说明 / Gremlin 替代 |
|---|---|---|---|
| `MATCH` + `WHERE` + `RETURN`（节点模式） | ✅ 可用 | 文档示例 | [语言指南](/cn/docs/language/hugegraph-cypher/) |
| 关系模式 `(a)-[:KNOWS]->(b)` | ✅ 可用 | 文档示例 | — |
| `ORDER BY` / `LIMIT` / `SKIP` | ✅ 可用 | 文档示例 | — |
| `CREATE` 点/边、`SET` / `REMOVE`、`DELETE` / `DETACH DELETE` | ✅ 可用 | 文档示例 | — |
| 聚合（`count`、`sum`、`min`、`max`、`avg`） | ✅ 可用 | 文档示例 | — |
| `MERGE`（基础） | ⚠️ 部分 | 转译器报告 | `MERGE ... ON CREATE SET` / `ON MATCH SET` 不支持 → 用 Gremlin 先查后建 |
| 变长路径 `(a)-[:KNOWS*1..3]->(b)` | ⚠️ 未验证 | — | 优先用 [traverser REST API](/cn/docs/clients/restful-api/traverser/) 或 Gremlin `repeat()` |
| `OPTIONAL MATCH`、`WITH`、`UNWIND` | ⚠️ 未验证 | — | 使用前先测试；可回退 Gremlin |
| 字符串 / 数学函数 | ⚠️ 部分 | 转译器报告 | 只覆盖 openCypher 9 函数子集；不支持的在翻译期报错 |
| `date()` / `datetime()` 函数 | ❌ 不支持 | Issue 记录 | 在客户端算好时间戳后以字面量传入 |
| 正则 `=~` 与 `NOT (... IN ...)` | ❌ 不支持 | Issue 记录 | 客户端过滤，或用 Gremlin 谓词（`TextP.regex`） |
| Map projection `n { .name, .age }` | ❌ 不支持 | Issue 记录 | 返回节点本身或显式属性 |
| 查询参数（`$param`） | ❌ 不支持 | API 面（`CypherAPI` 只接受语句字符串） | 在客户端转义/校验后拼接字面量 |
| `CALL` 过程（图算法） | ❌ 不支持 | API 面 | 使用 [traverser REST API](/cn/docs/clients/restful-api/traverser/) 或 Gremlin |
| 多语句脚本 | ❌ 不支持 | API 面 | 每次请求一条语句 |
| Cypher 里的 DDL（`CREATE INDEX`、约束） | ❌ 不支持 | 架构 | 通过 [schema REST API](/cn/docs/clients/restful-api/schema/) 建索引/约束 |
| `EXPLAIN` / `PROFILE` | ❌ 不支持 | API 面 | 在 Gremlin 遍历上使用 `profile()` |

图例：✅ 已在文档路径验证 · ⚠️ 部分支持或未在 HugeGraph 验证 —— 先测试 ·
❌ Cypher API 不可达。

### 开发分支实测

在
[`hugegraph/hugegraph@27a7c9b42274d6d4f95eabed6d2051d393ae0eaf`](https://github.com/hugegraph/hugegraph/commit/27a7c9b42274d6d4f95eab6d2051d393ae0eaf)
上，使用 Java `17.0.20.1`、TinkerPop `3.8.1`、RocksDB 和 `translation-1.0.4`，
对实际 Cypher 路径进行了 9 条 Cypher 请求的样例验证。legacy GET 和纯文本 POST、
基础节点与边的 `CREATE`、`SET`、`DELETE` 请求以及 native REST 回读通过。

本次单语句写原子性检查未通过。第一轮中，失败的双节点 `CREATE` 后即时
native 回读未见前缀；后续聚合/排序读暴露了前缀，native 全量列表也予以
确认。第二轮复现中，即时 native 回读和之后 7 次成功的只读 count/native
回读均未见前缀；第 8 次 count 后，native 全量列表首次显示
`baseline_repro_prefix_v2`。两轮都观察到残留；触发条件仍在调查，尚无修复
验证。本样例不能证明完整写事务或 openCypher 兼容性。详见[本 PR 的基线
结果](https://github.com/apache/hugegraph-doc/pull/499#issuecomment-5826172378)。

### 失败行为

不支持的写法在翻译期报错，响应 `status.message` 携带转译器错误。无法表达的
语句始终有等价 Gremlin 写法 —— 见
[对照表](/cn/docs/language/hugegraph-cypher/#等价的-gremlin-写法)。

### 持续完善

随着 conformance 证据增加，本矩阵会持续更新。针对真实 HugeGraph 服务运行
openCypher TCK 并公布通过/失败矩阵，是把 ⚠️ 行变成确定答案的既定后续工作。
