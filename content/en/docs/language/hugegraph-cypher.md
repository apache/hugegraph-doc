---
title: "HugeGraph Cypher"
linkTitle: "Cypher Query Language"
weight: 2
---

### Overview

HugeGraph supports [Cypher](https://opencypher.org/), the declarative graph query language originally created by Neo4j and standardized as
[openCypher](https://github.com/opencypher/openCypher). While Gremlin is an imperative traversal language, Cypher lets you describe the graph pattern you want
(`MATCH`, `WHERE`, `RETURN`) and lets the engine decide how to execute it.

HugeGraph executes Cypher by translating the statement to Gremlin through the [cypher-for-gremlin](https://github.com/opencypher/cypher-for-gremlin) transpiler,
then running the resulting traversal on the TinkerPop stack. This means Cypher support in HugeGraph covers the openCypher 9 surface that the transpiler
implements — see [Known limitations](#known-limitations) below.

### When to use Cypher vs Gremlin

| Use Cypher when | Use Gremlin when |
|---|---|
| You are migrating from Neo4j or already know Cypher | You need the full HugeGraph feature surface |
| You want declarative pattern matching (`MATCH (a)-[:KNOWS]->(b)`) | You need fine-grained traversal control, custom steps, or lambdas |
| Your queries are read-mostly patterns and projections | You need graph algorithms, OLAP, or features Cypher does not expose |
{.wide}

For anything Cypher cannot express, the equivalent [Gremlin query](/docs/language/hugegraph-gremlin/) always works — examples below show both.

### Calling the Cypher API

Cypher statements are submitted to the HugeGraph Server through the REST endpoint:

```http
GET  /graphspaces/{graphspace}/graphs/{graph}/cypher?cypher={statement}
POST /graphspaces/{graphspace}/graphs/{graph}/cypher
```

When server authentication is disabled, no `Authorization` header is required; when authentication is enabled,
standard `Basic` (RFC 4648 Base64, e.g. `curl -u`) or `Bearer <token>` credentials are supported.
See the [Cypher REST API reference](/docs/clients/restful-api/cypher/) for the full request and response format.

Example:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/cypher?cypher=MATCH%20(n:person)%20RETURN%20n.name%20LIMIT%2010"
```

From the Java client, use `CypherManager` (see [hugegraph-client](/docs/clients/client/hugegraph-client/)):

```java
ResultSet resultSet = hugeClient.cypher().execute("MATCH (n:person) RETURN n.name LIMIT 10");
```

### Basic examples

The examples below assume a graph with `person` vertices (`name`, `age`, `city` properties) and `knows` edges.
Before running them, note:
- Property predicates in `WHERE` (such as `WHERE n.age > 30`) require covering indexes (e.g. a `RANGE` index on `person.age`).
- On schemas with non-nullable properties or `PRIMARY_KEY` strategy, create statements must provide required attributes and primary keys;
  create vertices with complete properties separately before creating connecting edges.

#### Read — MATCH / WHERE / RETURN

```cypher
// All persons named "marko"
MATCH (n:person) WHERE n.name = 'marko' RETURN n
```

```cypher
// Projection with ordering and limit
MATCH (n:person)
WHERE n.age > 30
RETURN n.name AS name, n.age AS age
ORDER BY age DESC
LIMIT 10
```

```cypher
// Relationship pattern
MATCH (a:person)-[:knows]->(b:person)
WHERE a.name = 'marko'
RETURN b.name AS friend
```

#### Create — CREATE

```cypher
// Create a vertex
CREATE (n:person {name: 'alice', age: 32, city: 'beijing'})
```

```cypher
// Create two vertices, then an edge between them (send each statement as its own request)
CREATE (:person {name: 'bob'})
CREATE (:person {name: 'carol'})
MATCH (a:person), (b:person)
WHERE a.name = 'bob' AND b.name = 'carol'
CREATE (a)-[:knows]->(b)
```

#### Update — SET / REMOVE

```cypher
MATCH (n:person) WHERE n.name = 'alice'
SET n.age = 33
REMOVE n.city
```

#### Delete — DELETE / DETACH DELETE

```cypher
// Delete an edge
MATCH (a:person)-[r:knows]->(b:person)
WHERE a.name = 'bob' AND b.name = 'carol'
DELETE r
```

```cypher
// Delete a vertex and all its edges
MATCH (n:person) WHERE n.name = 'alice'
DETACH DELETE n
```

#### Aggregation

```cypher
// Total count
MATCH (n:person) RETURN count(n) AS total
```

```cypher
// Grouped count
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
{.wide}

Tip: You can inspect translated Gremlin traversals via `EXPLAIN MATCH (n:person) RETURN n` (in the `translation` field of the response) to draft
equivalent traversals. `PROFILE` is not supported.

### Known limitations

Cypher support in HugeGraph is bounded by the transpiler layer, which is based on openCypher 9 era tooling. Known gaps:

- **Parameterized query rules** — Parameter bindings are supported via JSON request bodies (`{"cypher": "...", "parameters": {...}}`, up to 16 top-level
  parameters; group additional properties into a Map and reference fields explicitly). Referencing an undeclared `$param` results in an execution error;
  explicit `null` is supported.
- **Partial clause coverage** — Some openCypher constructs cannot be translated (e.g. map projections and certain `datetime()` functions).
  Unsupported constructs fail during translation.
- **No `CALL` procedures** — HugeGraph graph algorithms (shortest path, k-out, personalrank, etc.) are not exposed as Cypher procedures; use the
  [traverser REST APIs](/docs/clients/restful-api/traverser/) or Gremlin instead.
- **Single statement per request** — Multi-statement scripts are not supported; send one statement per call.

When a statement fails translation or execution, the server returns structured error details under `status.attributes.errors` with `code`, `message`, and
`hint`. If you hit a gap, the Gremlin equivalent is the supported fallback.

### Further reading

- [Cypher REST API reference](/docs/clients/restful-api/cypher/)
- [Cypher compatibility notes](/docs/language/cypher-compatibility/)
- [Gremlin Query Language](/docs/language/hugegraph-gremlin/)
- [openCypher project](https://opencypher.org/) — language specification and resources

Note: The transpiler's historical TCK pass rate does not represent end-to-end compatibility in HugeGraph; test with your actual business queries.
