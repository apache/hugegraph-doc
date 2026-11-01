---
title: "HugeGraph Cypher"
linkTitle: "Cypher 查询语言"
weight: 2
---

### 概述

HugeGraph 支持 [Cypher](https://opencypher.org/) —— 最初由 Neo4j 创建、并由 [openCypher](https://github.com/opencypher/openCypher) 标准化的声明式图查询语言。Gremlin 是命令式的遍历语言，而 Cypher
只需描述想要的图模式（`MATCH`、`WHERE`、`RETURN`），由引擎决定如何执行。

HugeGraph 实现了对 [openCypher 9](https://opencypher.org/) 语法子集的支持，查询语句在服务端解析并无缝对接底层 TinkerPop 图遍历引擎。因此开发者可以使用直观的模式匹配语法，快速完成图数据的检索与写入。完整支持矩阵与限制参见 [Cypher 兼容性](/cn/docs/language/cypher-compatibility/)。

### 何时用 Cypher、何时用 Gremlin

| 适合用 Cypher | 适合用 Gremlin |
|---|---|
| 正在从 Neo4j 迁移，或已熟悉 Cypher | 需要 HugeGraph 的完整功能面 |
| 需要声明式模式匹配（`MATCH (a)-[:KNOWS]->(b)`） | 需要精细的遍历控制、自定义步骤或 lambda |
| 查询以读模式和投影为主 | 需要图算法、OLAP 或 Cypher 未暴露的功能 |
{.wide}

凡是 Cypher 表达不了的，等价的 [Gremlin 查询](/cn/docs/language/hugegraph-gremlin/) 总是可用 —— 下文示例同时给出两种写法。

### 调用 Cypher API

Cypher 语句通过 HugeGraph Server 的 REST 端点提交：

```http
GET  /graphspaces/{graphspace}/graphs/{graph}/cypher?cypher={statement}
POST /graphspaces/{graphspace}/graphs/{graph}/cypher
```

在服务端未开启认证时无需携带认证头；开启认证后支持 `Authorization: Basic ...`（标准 RFC 4648 Base64 编码，如 `curl -u`）或 `Authorization: Bearer <token>`。
完整请求/响应格式见 [Cypher REST API 参考](/cn/docs/clients/restful-api/cypher/)。

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

以下示例基于包含 `person`（属性 `name`、`age`、`city`）和 `knows` 边的图模型。
执行前请注意：
- 属性过滤谓词（如 `WHERE n.age > 30`）通常需要对应的索引覆盖（如在 `person.age` 上建立 `RANGE` 索引）。
- 若顶点标签采用 `PRIMARY_KEY` 策略或定义了非空属性，创建数据时需为必填属性和主键赋值；建议先分别创建顶点再建立关联边。

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
{.wide}

提示：可使用 `EXPLAIN MATCH (n:person) RETURN n` 查看对应的底层 Gremlin 遍历语句（位于返回结果的 `translation` 字段中），方便对照编写等价写法。`PROFILE` 暂不受支持。

### 使用限制

- **参数化查询规则**：支持通过 JSON 请求体传递参数（`{"cypher": "...", "parameters": {...}}`，最多支持 16 个顶层参数；
  更多属性可放入 Map 对象并显式引用）。引用了未声明的 `$param` 时会直接抛出执行错误；显式传入 `null` 是允许的。
- **高级语法覆盖边界**：部分高级 openCypher 语法（如 map projection、部分复杂函数）当前暂不支持，未支持的结构会在解析校验阶段报错。
- **过程调用**：HugeGraph 的图分析算法（最短路径、k-out、PersonalRank 等）通过独立的 [Traverser REST API](/cn/docs/clients/restful-api/traverser/) 或 Gremlin 提供，未暴露为 Cypher `CALL` 过程。
- **单请求单语句**：每次请求仅支持执行一条 Cypher 语句，不支持多语句复合脚本。

执行或校验失败时，服务端会在响应的 `status.attributes.errors` 中返回包含 `code`、`message` 与 `hint` 的结构化错误详情。遇到功能缺口时，等价的 Gremlin 写法是官方推荐的替代方案。

### 延伸阅读

- [Cypher REST API 参考](/cn/docs/clients/restful-api/cypher/)
- [Cypher 兼容性说明](/cn/docs/language/cypher-compatibility/)
- [Gremlin 查询语言](/cn/docs/language/hugegraph-gremlin/)
- [openCypher 官方规范](https://opencypher.org/)

