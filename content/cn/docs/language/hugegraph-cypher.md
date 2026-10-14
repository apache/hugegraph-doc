---
title: "HugeGraph Cypher"
linkTitle: "Cypher 查询语言"
weight: 2
---

### 概述

HugeGraph 支持 [Cypher](https://opencypher.org/) —— 最初由 Neo4j 创建、并由 [openCypher](https://github.com/opencypher/openCypher) 标准化的声明式图查询语言。Gremlin 是命令式的遍历语言，而 Cypher
只需描述想要的图模式（`MATCH`、`WHERE`、`RETURN`），由引擎决定如何执行。

HugeGraph 通过 [cypher-for-gremlin](https://github.com/opencypher/cypher-for-gremlin) 转译器将 Cypher 语句翻译为 Gremlin，再在 TinkerPop 技术栈上执行。因此 HugeGraph 的 Cypher
能力覆盖转译器所实现的 openCypher 9 语法面 —— 详见下文[已知限制](#已知限制)。

### 何时用 Cypher、何时用 Gremlin

| 适合用 Cypher | 适合用 Gremlin |
|---|---|
| 正在从 Neo4j 迁移，或已熟悉 Cypher | 需要 HugeGraph 的完整功能面 |
| 需要声明式模式匹配（`MATCH (a)-[:KNOWS]->(b)`） | 需要精细的遍历控制、自定义步骤或 lambda |
| 查询以读模式和投影为主 | 需要图算法、OLAP 或 Cypher 未暴露的功能 |

凡是 Cypher 表达不了的，等价的 Gremlin 查询总是可用 —— 下文示例同时给出两种写法。

### 调用 Cypher API

Cypher 语句通过 HugeGraph Server 的 REST 端点提交：

```http
GET  /graphspaces/{graphspace}/graphs/{graph}/cypher?cypher={statement}
POST /graphspaces/{graphspace}/graphs/{graph}/cypher
```

该端点始终要求 `Authorization` 头（`Basic` 或 `Bearer`），即使服务端未开启认证 —— 凭据会被转发给 Gremlin Server。`Basic` 凭据必须使用 URL 安全的 Base64 编码（用 `-` 和 `_` 代替 `+` 和 `/`），且密码不能包含 `:`；
无法满足这两个条件的账号请改用 `Bearer`。完整的请求/响应格式见 [Cypher REST API 参考](/cn/docs/clients/restful-api/cypher/)。

示例：

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/cypher?cypher=MATCH%20(n:person)%20RETURN%20n.name%20LIMIT%2010"
```

Java 客户端使用 `CypherManager`（见 [hugegraph-client](/cn/docs/clients/hugegraph-client/)）：

```java
ResultSet resultSet = hugeClient.cypher().execute("MATCH (n:person) RETURN n.name LIMIT 10");
```

### 基础示例

以下示例假设图中存在 `person` 顶点（`name`、`age`、`city` 属性）和 `knows` 边，并假设标签
声明了 `person` 上的 `nullableKeys("age", "city")` 以及 `knows` 上的可空属性，并且 `person.age` 上有 `RANGE` 索引——例如在
`scripts/example.groovy` 的 Schema 上补充这些可空键，再加上
`schema.indexLabel("personByAge").onV("person").by("age").range().ifNotExist().create()`。`WHERE` 中的属性谓词必须有索引覆盖：
`scripts/example.groovy` 只为 `person.city` 以及 `(age, city)` 建了 `SECONDARY` 索引，因此在 `RANGE` 索引存在之前，
`n.age > 30` 这类范围比较会被拒绝并报“未建索引”错误。
若先加载 `scripts/example.groovy`，请注意它已经预置了 `person` 顶点 `marko`、`vadas`、`josh` 和 `peter`；
由于 `person` 标签使用 `PRIMARY_KEY` id 策略，用这些名字执行 `CREATE` 会替换预置顶点，
因此下面的创建、更新和删除示例使用示例数据中不存在的名字（`alice`、`bob`、`carol`），或请在空图上执行。若 Schema 未声明可空键（已发布的默认 Schema 把
`person` 的 `age`、`city` 标记为非空），下面的创建与更新示例会触发非空属性校验失败：请在每条语句中
为所有非空属性赋值，或先以 `nullableKeys` 声明标签。若 `person` 标签使用 `PRIMARY_KEY` id 策略（`scripts/example.groovy` 即如此），双顶点简写
`CREATE (a)-[:knows]->(b)` 会被拒绝并返回执行错误（提示必须设置主键；在已合入
[#3289](https://github.com/apache/hugegraph/pull/3289) 的 `master` 上验证），因此下面的边示例先分别创建顶点再匹配它们；
该简写在 `AUTOMATIC` id 策略下可用。

#### 查询 — MATCH / WHERE / RETURN

```cypher
// 所有名为 "marko" 的 person
MATCH (n:person) WHERE n.name = 'marko' RETURN n
```

```cypher
// 投影 + 排序 + 限制条数
MATCH (n:person)
WHERE n.age > 30
RETURN n.name AS name, n.age AS age
ORDER BY age DESC
LIMIT 10
```

```cypher
// 关系模式
MATCH (a:person)-[:knows]->(b:person)
WHERE a.name = 'marko'
RETURN b.name AS friend
```

#### 创建 — CREATE

```cypher
// 创建顶点
CREATE (n:person {name: 'alice', age: 32, city: 'beijing'})
```

```cypher
// 先创建两个顶点，再创建它们之间的边（每条语句单独作为一次请求发送）
CREATE (:person {name: 'bob'})
CREATE (:person {name: 'carol'})
MATCH (a:person), (b:person)
WHERE a.name = 'bob' AND b.name = 'carol'
CREATE (a)-[:knows]->(b)
```

#### 更新 — SET / REMOVE

```cypher
MATCH (n:person) WHERE n.name = 'alice'
SET n.age = 33
REMOVE n.city
```

#### 删除 — DELETE / DETACH DELETE

```cypher
// 删除边
MATCH (a:person)-[r:knows]->(b:person)
WHERE a.name = 'bob' AND b.name = 'carol'
DELETE r
```

```cypher
// 删除顶点及其所有边
MATCH (n:person) WHERE n.name = 'alice'
DETACH DELETE n
```

#### 聚合

```cypher
// 总数
MATCH (n:person) RETURN count(n) AS total
```

```cypher
// 按城市分组计数
MATCH (n:person) RETURN n.city AS city, count(*) AS cnt ORDER BY cnt DESC
```

### 等价的 Gremlin 写法

每条 Cypher 语句在内部都会被翻译为 Gremlin。当某个 Cypher 特性不受支持时，可直接编写遍历：

| Cypher | 等价 Gremlin |
|---|---|
| `MATCH (n:person) WHERE n.name='marko' RETURN n` | `g.V().hasLabel('person').has('name','marko')` |
| `MATCH (a)-[:knows]->(b) RETURN b` | `g.V().out('knows')` |
| `CREATE (n:person {name:'x'})` | `g.addV('person').property('name','x')` |
| `MATCH (n) DETACH DELETE n` | `g.V().drop()` |
| `MATCH (n:person) RETURN count(n)` | `g.V().hasLabel('person').count()` |

提示：`EXPLAIN MATCH (n:person) RETURN n` 会以 `EXPLAIN` 选项解析，翻译后的 Gremlin 预期出现在 `result.data[0].translation` 中 —— 这是转译层行为，尚未在服务器上端到端验证（见
[兼容性说明](/cn/docs/language/cypher-compatibility/)）。它仍是起草上表等价写法的最快方式。`PROFILE` 不受支持。

### 已知限制

HugeGraph 的 Cypher 能力受转译层约束，该层基于 openCypher 9 时代的工具链。已知缺口：

- **已发布版本不支持参数化查询** —— API 只接受原始语句字符串。使用 `$param` 的语句不会报错：缺失的绑定会被内联为 `null`，结果取决于表达式：`WHERE n.name = $name` 这类谓词匹配不到行，`RETURN $value AS value` 仍会返回一行 `null`。
  缺失绑定的写入并不能可靠地存入 null 值：视语句而定，`SET n.prop = $missing` 会移除已有属性，`CREATE (n:label {prop: $missing})` 会在文本属性中存入转译库的 null 标记字符串 `"  cypher.null"`，而对非文本属性执行同样的
  `CREATE`，或对非空属性执行 `SET`，则会报错。请在客户端先对值做转义/净化再拼接到语句中。在合入 [#3289](https://github.com/apache/hugegraph/pull/3289) 后的
测试栈上情况改变：缺失的绑定对所有请求形式都是执行错误，包括 `GET ?cypher=` 与原始文本
`POST`——服务器总是附带参数表并拒绝未解析的 `$param` 引用。JSON 绑定参数（`{"cypher": ..., "parameters": {...}}`）已通过合入 `master` 的
[ASF PR #3289](https://github.com/apache/hugegraph/pull/3289) 引入，承接原 [PR #238](https://github.com/hugegraph/hugegraph/pull/238)；已验证的请求契约见
[开发版兼容性记录](/cn/docs/language/cypher-compatibility/)。
- **子句覆盖不完整** —— 部分 openCypher 结构无法翻译（例如 map projection、部分 `datetime()` 函数）。不支持的结构会在翻译阶段报错。`MERGE ... ON CREATE SET`、`NOT ... IN` 等结构可以翻译，但尚未在 HugeGraph 上端到端验证。
  开发改动验证了计算字符串上的两个 `=~` 全字符串匹配用例，更广泛的正则覆盖仍未验证 —— 见[兼容性说明](/cn/docs/language/cypher-compatibility/)。
- **不支持 `CALL` 过程** —— HugeGraph 的图算法（最短路径、k-out、personalrank 等）未暴露为 Cypher 过程；请改用 [traverser REST API](/cn/docs/clients/restful-api/traverser/) 或 Gremlin。
- **每次请求仅一条语句** —— 不支持多语句脚本，请每次调用发送一条语句。

当语句翻译失败时，响应的 `status.message` 会包含转译器错误信息。遇到缺口时，等价的 Gremlin 写法是受支持的回退方案。

### 延伸阅读

- [Cypher REST API 参考](/cn/docs/clients/restful-api/cypher/)
- [Gremlin 查询语言](/cn/docs/language/hugegraph-gremlin/)
- [openCypher 项目](https://opencypher.org/) —— 语言规范与资源

转译库历史 TCK 通过比例不等于 HugeGraph 端到端兼容率；本页没有给出经测量的 HugeGraph Cypher 总体兼容百分比。
