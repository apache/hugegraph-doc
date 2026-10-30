---
title: "Migrating from Neo4j"
linkTitle: "Migrating from Neo4j"
weight: 4
---

### Who this page is for

Neo4j users evaluating HugeGraph. HugeGraph's Cypher coverage is defined by
the [`cypher-for-gremlin`](https://github.com/opencypher/cypher-for-gremlin)
translator and is not 1:1 with Neo4j — see
[Known limitations](/docs/language/hugegraph-cypher/#known-limitations) for what
released HugeGraph versions do, and the
[Cypher compatibility notes](/docs/language/cypher-compatibility/) for the
development-tree verification record and
[HugeGraph Cypher](/docs/language/hugegraph-cypher/) for usage.

### What carries over directly

| Neo4j concept | HugeGraph equivalent |
|---|---|
| Property graph model (nodes / relationships / properties) | Same — vertex labels / edge labels / properties |
| Core Cypher: `MATCH`/`WHERE`/`RETURN`/`CREATE`/`SET`/`DELETE` | Works as-is (REST `/cypher` endpoint or Java client `CypherManager`), subject to the schema and index rules below |
| Simple aggregations (`count`/`sum`/`min`/`max`/`avg`) | Works as-is |
| Traversal-heavy queries | Gremlin traversals or the [traverser REST APIs](/docs/clients/restful-api/traverser/) (k-out, shortest path, personalrank, ...) |

### Habits you need to change

| In Neo4j | In HugeGraph |
|---|---|
| `CREATE INDEX` / `CREATE CONSTRAINT` | Create property indexes through the [IndexLabel REST API](/docs/clients/restful-api/indexlabel/); uniqueness constraints map to `UNIQUE` IndexLabels; node keys map to non-nullable keys plus a composite `UNIQUE` index; property existence constraints map to non-nullable keys on [VertexLabels](/docs/clients/restful-api/vertexlabel/) or [EdgeLabels](/docs/clients/restful-api/edgelabel/). Note that `primary_keys` defines vertex identity, not a uniqueness constraint — a duplicate `CREATE` overwrites the existing vertex instead of failing |
| Implicit schema (add properties freely) | **Strong schema**: define VertexLabel / EdgeLabel / PropertyKey before writing data |
| Property predicates in `WHERE` need no index | The starting vertex lookup in `WHERE` needs a covering index unless it is an equality on every primary key of the label. Use `RANGE` for `>` / `<` comparisons. Without a covering index the request returns HTTP 400 with a "not indexed" error |
| Parameterized queries `$param` | Released versions send the raw statement only; a missing binding is inlined as `null` (a predicate on it matches no rows, `SET` removes the property, `CREATE` can store the marker string `"  cypher.null"` or fail). Validate values client-side. JSON-bound parameters are supported from 1.8.0, limited to 16 top-level bindings |
| `CALL dbms.*` / `CALL algo.*` procedures | Equivalent capabilities are in the [traverser](/docs/clients/restful-api/traverser/), [task](/docs/clients/restful-api/task/), and other REST APIs |
| Driver: Neo4j Bolt driver | [hugegraph-client](/docs/clients/hugegraph-client/) (`CypherManager`) or any HTTP client |
| Transaction boundaries inside a Cypher statement | One statement per request; graph-to-graph migration uses [Apache SeaTunnel 3.0.0](https://seatunnel.apache.org/download/) (preferred, see below), file-based bulk loads use the [HugeGraph Loader](/docs/quickstart/toolchain/hugegraph-loader/) |
{.wide}

On `PRIMARY_KEY` labels, a `UNIQUE` index cannot include all primary-key fields (the server rejects it). To keep duplicate-rejection behavior, use a `CUSTOMIZE_STRING` label keyed on the Neo4j node id and add a `UNIQUE` index on the business key.

The latest published release is 1.7.0 as of 2026-10-09; the merged JSON-bound request form is a
`master` feature, not a promise about that release. See the compatibility notes for its validated contract.

### Suggested migration path

1. **Inventory your queries**: classify the Cypher in your application against
   the [Known limitations](/docs/language/hugegraph-cypher/#known-limitations)
   (which describe released behaviour) into
   "works as-is / rewrite as Gremlin / switch to a REST API"; the
   [compatibility notes](/docs/language/cypher-compatibility/) record only the
   development-tree contract.
2. **Create the schema first**: define VertexLabel / EdgeLabel / PropertyKey
   and indexes through the schema API — HugeGraph requires the schema to
   exist before data is written.
3. **Import data**: the preferred path is
   [Apache SeaTunnel 3.0.0](https://seatunnel.apache.org/download/) (released
   2026-09-29) running **Neo4j Source → HugeGraph Sink** directly — no
   intermediate file export. REST remains fine for small datasets; the
   [HugeGraph Loader](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-loader)
   stays an alternative for file-based imports. HugeGraph-side setup
   (environment, `mappings`, vertex/edge import examples) is covered in the
   [Import Graph Data with SeaTunnel Sink guide](/docs/quickstart/toolchain/import/hugegraph-seatunnel-connector/).

   The [SeaTunnel 3.0.0 connector docs](https://seatunnel.apache.org/docs/3.0.0/introduction/about/) document
   what to rely on:
   - [Neo4j Source](https://seatunnel.apache.org/docs/3.0.0/connectors/source/Neo4j/) reads Cypher
     query results with explicit field schemas; 3.0.0 adds multi-table reads via `tables_configs`.
   - [HugeGraph Sink](https://seatunnel.apache.org/docs/3.0.0/connectors/sink/HugeGraph/) is
     refactored in 3.0.0 with multi-mapping support — use the recommended `mappings` configuration
    for vertices/edges and follow its schema-creation behavior. By default, the Sink fails fast on
    errors (`batch_failure_fallback=false` and `max_insert_errors=0`). Record skipping is opt-in via
    `batch_failure_fallback=true`; if enabled, capture and reconcile skipped records and compare row counts before cutover.
   - [HugeGraph Source](https://seatunnel.apache.org/docs/3.0.0/connectors/source/HugeGraph/) is
     new in 3.0.0 (schema auto-discovery, multi-label/parallel reads), enabling HugeGraph export
     and migration workflows.

   Map Neo4j properties to HugeGraph PropertyKeys and pick the vertex ID strategy
   before importing. The Sink requires `idFields` for every vertex strategy other than
   `AUTOMATIC`, and edge mappings need separate `sourceConfig.idFields` and
   `targetConfig.idFields`, so the Neo4j query must return the field that carries the ID:
   - `idStrategy = "PRIMARY_KEY"`: put a Neo4j business key in `idFields` and express edge
     endpoints through those same key fields.
   - `idStrategy = "CUSTOMIZE_STRING"`: this alone does not keep the Neo4j node id. Make the
     Neo4j query return the id you want to keep as its own column (aliased, for example `AS node_id`),
     declare that field in the Source `schema.fields` (it must match the fields the query
     returns), set the vertex `idFields` to it, and map the matching edge endpoint fields
     in `sourceConfig.idFields` and `targetConfig.idFields`.

   Labels you pre-created in step 2 must use that same strategy — automatic creation does not
   convert an existing `PRIMARY_KEY` label into `CUSTOMIZE_STRING`. The Sink `mappings`
   configuration can create the missing PropertyKey, VertexLabel and EdgeLabel definitions, so
   those three parts of step 2 are optional when you use it; it does not create IndexLabels, so
   create any index your queries rely on (see the habits table above) separately. Load vertices
   before edges. These capabilities are
   documented, but a complete Neo4j → HugeGraph migration has not been run end-to-end here —
   validate examples against your own data before treating them as tested.
4. **Switch incrementally**: keep the queries Cypher can express, and rewrite
   translator-unsupported constructs as Gremlin — the
   [equivalents table](/docs/language/hugegraph-cypher/#gremlin-equivalents)
   shows the mapping.

### Known limitations at a glance

- Released versions support neither parameter binding (a missing binding
  is inlined as `null` — see the habits table), multi-statement
  scripts, nor `CALL` procedures.
- The translator's last release is 2019-11 (1.0.4); its own TCK self-report is
  879 pass / 79 fail (~91.8%) — uncovered syntax fails at translation time.
- Unsupported query constructs can typically be rewritten as Gremlin
  traversals — see the
  [equivalents table](/docs/language/hugegraph-cypher/#gremlin-equivalents);
  schema DDL and `CALL` procedures map to REST APIs instead.

The translator’s historical TCK percentage is not a HugeGraph end-to-end compatibility rate; no measured overall HugeGraph Cypher percentage is established
here.
