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

For anything Cypher cannot express, the equivalent Gremlin query always works — examples below show both.

### Calling the Cypher API

Cypher statements are submitted to the HugeGraph Server through the REST endpoint:

```http
GET  /graphspaces/{graphspace}/graphs/{graph}/cypher?cypher={statement}
POST /graphspaces/{graphspace}/graphs/{graph}/cypher
```

On 1.2.0 to 1.7.0, the endpoint always requires an `Authorization` header (`Basic` or `Bearer`), even when server authentication is disabled —
the credentials are forwarded to the Gremlin Server. On those versions `Basic` credentials must be encoded with URL-safe Base64 (`-` and `_` instead
of `+` and `/`), and the password must not contain `:`. On `master` (1.8.0+), authentication is optional when server auth is disabled
([#3366](https://github.com/apache/hugegraph/pull/3366)), `Basic` credentials use standard RFC 4648 Base64 (as sent by `curl -u`,
[#3290](https://github.com/apache/hugegraph/pull/3290)), and `:` in passwords is supported.
See the [Cypher REST API reference](/docs/clients/restful-api/cypher/) for the full request/response format.

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
They assume the labels declare `nullableKeys("age", "city")` on `person` and nullable properties on `knows`, and that
`person.age` has a `RANGE` index — for example the schema in `scripts/example.groovy` modified with those nullable keys
plus `schema.indexLabel("personByAge").onV("person").by("age").range().ifNotExist().create()`. A property predicate
in `WHERE` on the starting vertex needs a covering index unless it is an equality on every primary key of the label:
`scripts/example.groovy` indexes `person.city` and `(age, city)` with `SECONDARY` indexes only, so a range comparison such
as `n.age > 30` is rejected with a "not indexed" error until the `RANGE` index exists.
If you load `scripts/example.groovy` first, note that it already seeds the `person` vertices `marko`, `vadas`, `josh` and `peter`;
because the `person` label uses the `PRIMARY_KEY` id strategy, a `CREATE` with one of those names replaces the seeded vertex,
so the create, update and delete examples below use names that the sample data does not contain (`alice`, `bob`, `carol`),
or run them on an empty graph. On a schema without the nullable keys
(the released default marks `age` and `city` non-null on `person`), the create and update examples below fail
the non-null property check: set every non-null property in each statement, or declare the labels with
`nullableKeys` first. If the `person` label uses the `PRIMARY_KEY` id strategy (as it does in `scripts/example.groovy`), the two-vertex
shorthand `CREATE (a)-[:knows]->(b)` is rejected with an execution error reporting that the primary keys must be set
(verified on `master` with [#3289](https://github.com/apache/hugegraph/pull/3289) merged), so the edge example below creates the vertices
first and then matches them. The shorthand works with the `AUTOMATIC` id strategy only when the label defines no required (non-null) properties; under the assumed schema, `name` remains non-null, so the shorthand is rejected because each created vertex must supply all non-null properties.

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

Tip: `EXPLAIN MATCH (n:person) RETURN n` is parsed with the `EXPLAIN` option, and the translated Gremlin is expected in `result.data[0].translation` —
translator-level behavior, not yet verified end-to-end on a server (see the [compatibility notes](/docs/language/cypher-compatibility/)). It remains the
quickest way to draft the equivalent traversal for the table above. `PROFILE` is not supported.

### Known limitations

Cypher support in HugeGraph is bounded by the transpiler layer, which is based on openCypher 9 era tooling. Known gaps:

- **No parameterized queries in released versions** — the API accepts a raw statement string only. A statement using `$param` still runs: a missing binding is
  inlined as `null` rather than failing, and the result depends on the expression: a predicate such as `WHERE n.name = $name` matches no rows,
  `RETURN $value AS value` still returns a row holding `null`. A write with a missing binding does not reliably store a null value: depending on the statement,
  `SET n.prop = $missing` removes the existing property, `CREATE (n:label {prop: $missing})` stores the translator's null marker string `"  cypher.null"` in a
  text property, and the same `CREATE` on a non-text property, or `SET` on a non-nullable property, fails with an error. Sanitize/escape values on the client
  side before interpolating them into the statement. On the tested tree with [#3289](https://github.com/apache/hugegraph/pull/3289) merged, this changes: a
  missing binding is an execution error for every request form, including `GET ?cypher=` and raw-body `POST` — the server always attaches a parameters map and
  rejects unresolved `$param` references. JSON-bound parameters (`{"cypher": ..., "parameters": {...}}`) are available on `master` after the merged
  [ASF PR #3289](https://github.com/apache/hugegraph/pull/3289), carried over from [PR #238](https://github.com/hugegraph/hugegraph/pull/238); see the
  [development compatibility record](/docs/language/cypher-compatibility/) for the tested request contract.
- **Partial clause coverage** — some openCypher constructs are not translated (for example map projections and certain `datetime()` functions). Unsupported
  constructs fail at translation time with an error from the transpiler. Constructs such as `MERGE ... ON CREATE SET` and `NOT ... IN` do translate, but they
  are not verified end-to-end on HugeGraph. The development change verifies two whole-string `=~` matching cases on computed strings; broader regex coverage
  remains unverified — see the [compatibility notes](/docs/language/cypher-compatibility/).
- **No `CALL` procedures** — HugeGraph graph algorithms (shortest path, k-out, personalrank, etc.) are not exposed as Cypher procedures; use the
  [traverser REST APIs](/docs/clients/restful-api/traverser/) or Gremlin instead.
- **Single statement per request** — multi-statement scripts are not supported; send one statement per call.

When a statement fails translation, the response `status.message` contains the transpiler error. If you hit a gap, the Gremlin equivalent is the supported
fallback.

### Further reading

- [Cypher REST API reference](/docs/clients/restful-api/cypher/)
- [Gremlin Query Language](/docs/language/hugegraph-gremlin/)
- [openCypher project](https://opencypher.org/) — language specification and resources

The translator’s historical TCK percentage is not a HugeGraph end-to-end compatibility rate; no measured overall HugeGraph Cypher percentage is established
here.
