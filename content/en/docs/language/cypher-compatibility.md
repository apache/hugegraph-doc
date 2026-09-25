---
title: "Cypher Compatibility"
linkTitle: "Cypher Compatibility"
weight: 3
---

### Scope of this page

HugeGraph executes Cypher by translating statements to Gremlin through the
[`cypher-for-gremlin`](https://github.com/opencypher/cypher-for-gremlin)
transpiler (`org.opencypher.gremlin:translation:1.0.4`, released 2019-11-05).
Cypher coverage in HugeGraph therefore equals what that translator implements
of openCypher 9 — see [HugeGraph Cypher](/docs/language/hugegraph-cypher/) for
usage and [Known limitations](/docs/language/hugegraph-cypher/#known-limitations)
for the short list.

The transpiler's own conformance self-report for 1.0.4 is **879 pass / 79 fail
(~91.7%)** of the openCypher TCK scenario set it targets. The matrix below
classifies features by the best available evidence; rows are not a substitute
for testing your own workload.

### Feature matrix

| openCypher feature | Status | Evidence tier | Notes / Gremlin workaround |
|---|---|---|---|
| `MATCH` + `WHERE` + `RETURN` (node patterns) | ✅ Works | Documented examples | [Language guide](/docs/language/hugegraph-cypher/) |
| Relationship patterns `(a)-[:KNOWS]->(b)` | ✅ Works | Documented examples | — |
| `ORDER BY` / `LIMIT` / `SKIP` | ✅ Works | Documented examples | — |
| `CREATE` vertex / edge, `SET` / `REMOVE`, `DELETE` / `DETACH DELETE` | ✅ Works | Documented examples | — |
| Aggregations (`count`, `sum`, `min`, `max`, `avg`) | ✅ Works | Documented examples | — |
| `MERGE` (basic) | ⚠️ Partial | Transpiler report | `MERGE ... ON CREATE SET` / `ON MATCH SET` not translated → check-then-create pattern via Gremlin |
| Variable-length paths `(a)-[:KNOWS*1..3]->(b)` | ⚠️ Untested | — | Prefer `traverser` REST APIs (k-out, paths) or Gremlin `repeat()` |
| `OPTIONAL MATCH`, `WITH`, `UNWIND` | ⚠️ Untested | — | Test before relying on them; fall back to Gremlin |
| String / math functions | ⚠️ Partial | Transpiler report | Subset of openCypher 9 functions; unsupported ones fail at translation time |
| `date()` / `datetime()` functions | ❌ Not supported | Issue reports | Compute timestamps client-side and pass as literal values |
| Regex `=~` and `NOT (... IN ...)` forms | ❌ Not supported | Issue reports | Filter client-side or via Gremlin predicates (`TextP.regex`) |
| Map projection `n { .name, .age }` | ❌ Not supported | Issue reports | Return the node or explicit properties |
| Query parameters (`$param`) | ❌ Not supported | API surface (`CypherAPI` accepts statement string only) | Escape/sanitize values client-side before interpolating |
| `CALL` procedures (graph algorithms) | ❌ Not supported | API surface | Use [traverser REST APIs](/docs/clients/restful-api/traverser/) or Gremlin |
| Multi-statement scripts | ❌ Not supported | API surface | One statement per request |
| Schema DDL in Cypher (`CREATE INDEX`, constraints) | ❌ Not supported | Architecture | Create schema via the [schema REST APIs](/docs/clients/restful-api/schema/) |
| `EXPLAIN` / `PROFILE` | ❌ Not supported | API surface | Use Gremlin `profile()` on the traversal API |

Legend: ✅ verified on the documented path · ⚠️ partial or not verified on
HugeGraph — test first · ❌ not reachable through the Cypher API.

### Development-branch runtime check

A sample of nine Cypher requests was run at
[`hugegraph/hugegraph@27a7c9b42274d6d4f95eabed6d2051d393ae0eaf`](https://github.com/hugegraph/hugegraph/commit/27a7c9b42274d6d4f95eabed6d2051d393ae0eaf)
with Java `17.0.20.1`, TinkerPop `3.8.1`, RocksDB, and `translation-1.0.4`. The
legacy GET and raw-text POST paths, basic node and edge `CREATE`, `SET`, and
`DELETE` requests, and native REST readback passed.

The tested single-statement write-atomicity check failed. After a failed
two-node `CREATE`, the first run's immediate native readback did not show the
prefix; later aggregate/sort reads exposed it, and a full native listing
confirmed it. In a second reproduction, neither the immediate native read nor
seven subsequent successful read-only count/native reads showed the prefix. It
appeared on the eighth count and in the following full native listing as
`baseline_repro_prefix_v2`. The residue appeared in both runs. Its trigger is
under investigation and no fix is verified. This sample does not establish
full write-transaction or openCypher compatibility. See [the baseline results
on this PR](https://github.com/apache/hugegraph-doc/pull/499#issuecomment-5826172378).

### Failure behaviour

Unsupported constructs fail at translation time; the response
`status.message` carries the transpiler error. When a statement cannot be
expressed, the equivalent Gremlin traversal always works — see the
[equivalents table](/docs/language/hugegraph-cypher/#gremlin-equivalents).

### Improving this page

This matrix is enriched as conformance evidence improves. Running the
openCypher TCK against a live HugeGraph server (and publishing the pass/fail
matrix) is the tracked follow-up that converts ⚠️ rows into definitive
answers.
