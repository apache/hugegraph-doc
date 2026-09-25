---
title: "HugeGraph Cypher"
linkTitle: "Cypher Query Language"
weight: 2
---

### Overview

HugeGraph supports [Cypher](https://opencypher.org/), the declarative graph query language originally created by Neo4j and standardized as [openCypher](https://github.com/opencypher/openCypher). While Gremlin is an imperative traversal language, Cypher lets you describe the graph pattern you want (`MATCH`, `WHERE`, `RETURN`) and lets the engine decide how to execute it.

HugeGraph executes Cypher by translating the statement to Gremlin through the [cypher-for-gremlin](https://github.com/opencypher/cypher-for-gremlin) transpiler, then running the resulting traversal on the TinkerPop stack. This means Cypher support in HugeGraph covers the openCypher 9 surface that the transpiler implements — see [Known limitations](#known-limitations) below.

### When to use Cypher vs Gremlin

| Use Cypher when | Use Gremlin when |
|---|---|
| You are migrating from Neo4j or already know Cypher | You need the full HugeGraph feature surface |
| You want declarative pattern matching (`MATCH (a)-[:KNOWS]->(b)`) | You need fine-grained traversal control, custom steps, or lambdas |
| Your queries are read-mostly patterns and projections | You need graph algorithms, OLAP, or features Cypher does not expose |

For anything Cypher cannot express, the equivalent Gremlin query always works — examples below show both.

### Calling the Cypher API

Cypher statements are submitted to the HugeGraph Server through the REST endpoint:

```http
GET  /graphspaces/{graphspace}/graphs/{graph}/cypher?cypher={statement}
POST /graphspaces/{graphspace}/graphs/{graph}/cypher
```

The endpoint always requires an `Authorization` header (`Basic` or `Bearer`), even when server authentication is disabled — the credentials are forwarded to the Gremlin Server. See the [Cypher REST API reference](/docs/clients/restful-api/cypher/) for the full request/response format.

Example:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/cypher?cypher=MATCH%20(n:person)%20RETURN%20n.name%20LIMIT%2010"
```

From the Java client, use `CypherManager` (see [hugegraph-client](/docs/clients/hugegraph-client/)):

```java
ResultSet resultSet = hugeClient.cypher().execute("MATCH (n:person) RETURN n.name LIMIT 10");
```

### Basic examples

The examples below assume a graph with `person` vertices (`name`, `age`, `city` properties) and `knows` edges.

#### Read — MATCH / WHERE / RETURN

```cypher
// All persons named "marko"
MATCH (n:person) WHERE n.name = 'marko' RETURN n

// Projection with ordering and limit
MATCH (n:person)
WHERE n.age > 30
RETURN n.name AS name, n.age AS age
ORDER BY age DESC
LIMIT 10

// Relationship pattern
MATCH (a:person)-[:knows]->(b:person)
WHERE a.name = 'marko'
RETURN b.name AS friend
```

#### Create — CREATE

```cypher
// Create a vertex
CREATE (n:person {name: 'josh', age: 32, city: 'beijing'})

// Create two vertices and an edge between them
CREATE (a:person {name: 'peter'})-[:knows]->(b:person {name: 'lop'})
```

#### Update — SET / REMOVE

```cypher
MATCH (n:person) WHERE n.name = 'josh'
SET n.age = 33
REMOVE n.city
```

#### Delete — DELETE / DETACH DELETE

```cypher
// Delete an edge
MATCH (a:person)-[r:knows]->(b:person)
WHERE a.name = 'peter' AND b.name = 'lop'
DELETE r

// Delete a vertex and all its edges
MATCH (n:person) WHERE n.name = 'josh'
DETACH DELETE n
```

#### Aggregation

```cypher
MATCH (n:person) RETURN count(n) AS total
MATCH (n:person) RETURN n.city AS city, count(*) AS cnt ORDER BY cnt DESC
```

### Gremlin equivalents

Every Cypher statement is translated to Gremlin internally. When a Cypher feature is unsupported, write the traversal directly:

| Cypher | Gremlin equivalent |
|---|---|
| `MATCH (n:person) WHERE n.name='marko' RETURN n` | `g.V().hasLabel('person').has('name','marko')` |
| `MATCH (a)-[:knows]->(b) RETURN b` | `g.V().out('knows')` |
| `CREATE (n:person {name:'x'})` | `g.addV('person').property('name','x')` |
| `MATCH (n) DETACH DELETE n` | `g.V().drop()` |
| `MATCH (n:person) RETURN count(n)` | `g.V().hasLabel('person').count()` |

Tip: `EXPLAIN MATCH (n:person) RETURN n` is accepted and returns the translated Gremlin in `result.data[0].translation` — the fastest way to obtain the equivalent traversal for the table above. `PROFILE` is not supported.

### Known limitations

Cypher support in HugeGraph is bounded by the transpiler layer, which is based on openCypher 9 era tooling. Known gaps:

- **No parameterized queries in released versions** — the API accepts a raw statement string only. A statement using `$param` still runs: a missing binding evaluates to `null`, so the query returns no rows (or writes null values) rather than failing. Sanitize/escape values on the client side before interpolating them into the statement. JSON-bound parameters (`{"cypher": ..., "parameters": {...}}`) are on the way in [PR #238](https://github.com/hugegraph/hugegraph/pull/238).
- **Partial clause coverage** — some openCypher constructs are not translated (for example map projections and certain `datetime()` functions). Unsupported constructs fail at translation time with an error from the transpiler. Constructs such as `MERGE ... ON CREATE SET`, `=~` regex predicates, and `NOT ... IN` do translate, but they are not verified end-to-end on HugeGraph — see the [compatibility notes](/docs/language/cypher-compatibility/).
- **No `CALL` procedures** — HugeGraph graph algorithms (shortest path, k-out, personalrank, etc.) are not exposed as Cypher procedures; use the [traverser REST APIs](/docs/clients/restful-api/traverser/) or Gremlin instead.
- **Single statement per request** — multi-statement scripts are not supported; send one statement per call.

When a statement fails translation, the response `status.message` contains the transpiler error. If you hit a gap, the Gremlin equivalent is the supported fallback.

### Further reading

- [Cypher REST API reference](/docs/clients/restful-api/cypher/)
- [Gremlin Query Language](/docs/language/hugegraph-gremlin/)
- [openCypher project](https://opencypher.org/) — language specification and resources
