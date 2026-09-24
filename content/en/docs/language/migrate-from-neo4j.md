---
title: "Migrating from Neo4j"
linkTitle: "Migrating from Neo4j"
weight: 4
---

### Who this page is for

Neo4j users evaluating HugeGraph. HugeGraph's Cypher coverage is defined by
the [`cypher-for-gremlin`](https://github.com/opencypher/cypher-for-gremlin)
translator and is not 1:1 with Neo4j — see the
[Cypher compatibility matrix](/docs/language/cypher-compatibility/) for the
feature-level differences and
[HugeGraph Cypher](/docs/language/hugegraph-cypher/) for usage.

### What carries over directly

| Neo4j concept | HugeGraph equivalent |
|---|---|
| Property graph model (nodes / relationships / properties) | Same — vertex labels / edge labels / properties |
| Core Cypher: `MATCH`/`WHERE`/`RETURN`/`CREATE`/`SET`/`DELETE` | Works as-is (REST `/cypher` endpoint or Java client `CypherManager`) |
| Simple aggregations (`count`/`sum`/`min`/`max`/`avg`) | Works as-is |
| Traversal-heavy queries | Gremlin traversals or the [traverser REST APIs](/docs/clients/restful-api/traverser/) (k-out, shortest path, personalrank, ...) |

### Habits you need to change

| In Neo4j | In HugeGraph |
|---|---|
| `CREATE INDEX` / `CREATE CONSTRAINT` | Create indexes/constraints through the [schema REST APIs](/docs/clients/restful-api/schema/); Cypher carries no DDL |
| Implicit schema (add properties freely) | **Strong schema**: define VertexLabel / EdgeLabel / PropertyKey before writing data |
| Parameterized queries `$param` | Not supported — escape/validate values client-side and interpolate literals |
| `CALL dbms.*` / `CALL algo.*` procedures | Equivalent capabilities live in the [traverser](/docs/clients/restful-api/traverser/), [task](/docs/clients/restful-api/task/), and other REST APIs |
| Driver: Neo4j Bolt driver | [hugegraph-client](/docs/clients/hugegraph-client/) (`CypherManager`) or any HTTP client |
| Transaction boundaries inside a Cypher statement | One statement per request; bulk writes use the [Loader](/docs/guides/toolchain/) or bulkport |

### Suggested migration path

1. **Inventory your queries**: classify the Cypher in your application against
   the [compatibility matrix](/docs/language/cypher-compatibility/) into
   "works as-is / rewrite as Gremlin / switch to a REST API".
2. **Create the schema first**: define VertexLabel / EdgeLabel / PropertyKey
   and indexes through the schema API — HugeGraph requires the schema to
   exist before data is written.
3. **Import data**: REST for small datasets; the
   [HugeGraph Loader](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-loader)
   for bulk loads.
4. **Switch incrementally**: keep the queries Cypher can express, and rewrite
   translator-unsupported constructs as Gremlin — the
   [equivalents table](/docs/language/hugegraph-cypher/#gremlin-equivalents)
   shows the mapping.

### Known limitations at a glance

- Cypher statements support neither parameter binding, multi-statement
  scripts, nor `CALL` procedures.
- The translator's last release is 2019-11 (1.0.4); its own TCK self-report is
  879 pass / 79 fail (~91.7%) — uncovered syntax fails at translation time.
- Anything unsupported can always be expressed as an equivalent Gremlin
  traversal — see the
  [equivalents table](/docs/language/hugegraph-cypher/#gremlin-equivalents).
