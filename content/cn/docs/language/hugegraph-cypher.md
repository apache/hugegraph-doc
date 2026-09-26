---
title: "HugeGraph Cypher"
linkTitle: "Cypher 查询语言"
weight: 2
---

### 概述

HugeGraph 支持 [Cypher](https://opencypher.org/) —— 最初由 Neo4j 创建、并由 [openCypher](https://github.com/opencypher/openCypher) 标准化的声明式图查询语言。Gremlin 是命令式的遍历语言，而 Cypher 只需描述想要的图模式（`MATCH`、`WHERE`、`RETURN`），由引擎决定如何执行。

HugeGraph 通过 [cypher-for-gremlin](https://github.com/opencypher/cypher-for-gremlin) 转译器将 Cypher 语句翻译为 Gremlin，再在 TinkerPop 技术栈上执行。因此 HugeGraph 的 Cypher 能力覆盖转译器所实现的 openCypher 9 语法面 —— 详见下文[已知限制](#已知限制)。

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

该端点始终要求 `Authorization` 头（`Basic` 或 `Bearer`），即使服务端未开启认证 —— 凭据会被转发给 Gremlin Server。完整的请求/响应格式见 [Cypher REST API 参考](/cn/docs/clients/restful-api/cypher/)。

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

以下示例假设图中存在 `person` 顶点（`name`、`age`、`city` 属性）和 `knows` 边。

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
CREATE (n:person {name: 'josh', age: 32, city: 'beijing'})
```

```cypher
// 创建两个顶点及它们之间的边
CREATE (a:person {name: 'peter'})-[:knows]->(b:person {name: 'lop'})
```

#### 更新 — SET / REMOVE

```cypher
MATCH (n:person) WHERE n.name = 'josh'
SET n.age = 33
REMOVE n.city
```

#### 删除 — DELETE / DETACH DELETE

```cypher
// 删除边
MATCH (a:person)-[r:knows]->(b:person)
WHERE a.name = 'peter' AND b.name = 'lop'
DELETE r
```

```cypher
// 删除顶点及其所有边
MATCH (n:person) WHERE n.name = 'josh'
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

提示：`EXPLAIN MATCH (n:person) RETURN n` 会以 `EXPLAIN` 选项解析，翻译后的 Gremlin 预期出现在 `result.data[0].translation` 中 —— 这是转译层行为，尚未在服务器上端到端验证（见[兼容性说明](/cn/docs/language/cypher-compatibility/)）。它仍是起草上表等价写法的最快方式。`PROFILE` 不受支持。

### 已知限制

HugeGraph 的 Cypher 能力受转译层约束，该层基于 openCypher 9 时代的工具链。已知缺口：

- **已发布版本不支持参数化查询** —— API 只接受原始语句字符串。使用 `$param` 的语句不会报错：缺失的绑定会被求值为 `null`，查询返回空结果（或写入 null 值）。请在客户端先对值做转义/净化再拼接到语句中。JSON 绑定参数（`{"cypher": ..., "parameters": {...}}`）将随 [PR #238](https://github.com/hugegraph/hugegraph/pull/238) 落地。
- **子句覆盖不完整** —— 部分 openCypher 结构无法翻译（例如 map projection、部分 `datetime()` 函数）。不支持的结构会在翻译阶段报错。`MERGE ... ON CREATE SET`、`=~` 正则谓词、`NOT ... IN` 等结构可以翻译，但尚未在 HugeGraph 上端到端验证 —— 见[兼容性说明](/cn/docs/language/cypher-compatibility/)。
- **不支持 `CALL` 过程** —— HugeGraph 的图算法（最短路径、k-out、personalrank 等）未暴露为 Cypher 过程；请改用 [traverser REST API](/cn/docs/clients/restful-api/traverser/) 或 Gremlin。
- **每次请求仅一条语句** —— 不支持多语句脚本，请每次调用发送一条语句。

当语句翻译失败时，响应的 `status.message` 会包含转译器错误信息。遇到缺口时，等价的 Gremlin 写法是受支持的回退方案。

### 延伸阅读

- [Cypher REST API 参考](/cn/docs/clients/restful-api/cypher/)
- [Gremlin 查询语言](/cn/docs/language/hugegraph-gremlin/)
- [openCypher 项目](https://opencypher.org/) —— 语言规范与资源
