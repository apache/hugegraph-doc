---
title: "Cypher Compatibility"
linkTitle: "Cypher Compatibility"
weight: 3
---

### Scope

**The verification results below describe `master`, not a released HugeGraph version.** HugeGraph 1.7.0 exposes exactly two
request forms on `/graphspaces/{graphspace}/graphs/{graph}/cypher`: `GET ?cypher=<URL-encoded statement>`
and `POST application/json` with a raw Cypher body. Releases before 1.7.0 expose the same two forms under
`/graphs/{graph}/cypher`. Released versions accept no bound parameters, and a
statement that references `$param` runs with the missing binding inlined as `null` rather than failing (a predicate on it matches no rows,
while `RETURN $value AS value` still returns a row) — see
[Known limitations](/docs/language/hugegraph-cypher/#known-limitations).

This page documents the verified use cases and behavioral boundaries of the Cypher implementation. It does not imply complete coverage of openCypher or Neo4j. Cypher parameter binding and enhancements are merged starting from 1.8.0 (Java 17, TinkerPop 3.8.1).

The endpoint is `/graphspaces/{graphspace}/graphs/{graph}/cypher`. General usage is covered in the
[HugeGraph Cypher guide](/docs/language/hugegraph-cypher/).

### Request forms and parameters

| Request | In a released version | Verified contract on the tested tree | Test method |
|---|---|---|---|
| `GET ?cypher=<URL-encoded statement>` | Yes | Existing query-string form | `testGet` |
| `POST application/json` with raw Cypher text | Yes | Legacy raw-body form remains available | `testPost` |
| `POST text/plain` with any body | No | Rejected with HTTP 415 | `testRejectPlainTextPost` |
| `POST application/json` with a JSON object | No — supported starting in 1.8.0 | Query and bindings are sent separately | `testParameters` |

The JSON object form below is therefore **not available in 1.7.0 and earlier**; it describes functionality supported starting from 1.8.0.
On released versions a statement using `$param` runs with the missing binding inlined as `null`; whether it returns rows
depends on the expression (`WHERE n.name = $name` matches nothing, `RETURN $value AS value` returns a row holding `null`) —
see [Known limitations](/docs/language/hugegraph-cypher/#known-limitations).

```json
{
  "cypher": "MATCH (n:cypher_person) WHERE n.name = $name RETURN n.name",
  "parameters": {"name": "marko"}
}
```

POST bodies containing JSON arrays, strings, numbers, booleans, or null are rejected with HTTP 400.
Malformed JSON objects and trailing tokens also produce request errors; they do not fall back to raw Cypher.

For the JSON-object form, `cypher` must be a nonblank string and `parameters`, if present, must be an object.
Omitting `parameters` means an empty map. A referenced but missing binding is an execution error; an explicit
null value is valid. On the tested tree this execution error applies to every request form, including
`GET ?cypher=` and raw-body `POST`: starting in 1.8.0, the server always attaches the
parameters map and rejects unresolved `$param` references, replacing the released null-binding behaviour
described above. Tests cover string, number, and boolean values, quotes and newlines, the binding names
`id` and `label`. The current implementation accepts at most 16 top-level entries in `parameters`; this
limit is fixed. Only keys in the top-level `parameters` object count toward it. Cypher does not support a
`maxParameters` setting in Gremlin Server's processor configuration. Values remain bindings and do not
alter query text.

A Map counts as one top-level parameter. Group related values into one Map and reference its fields
explicitly; the vertex label and required properties must match the graph's existing schema:

```json
{
  "cypher": "CREATE (n:cypher_person {name:$props.name, age:$props.age, city:$props.city}) RETURN n.name",
  "parameters": {"props": {"name": "new-person", "age": 20, "city": "Beijing"}}
}
```

Live REST verification confirmed that one Map containing 17 entries works with explicit property
references, with all 17 persisted values checked through native REST. A 17-entry returned Map also
succeeds, while 17 top-level bindings produce an execution error. Use the explicit property references
shown above; the pinned translator does not assign a bound Map's fields through the shorthand CREATE form.

The translator reserves the exact string `"  cypher.null"` (two leading spaces) as its null marker. That
string is rejected as a binding value, including inside lists and nested maps. Explicit null remains
supported. Literal query values and stored properties equal to that string remain a translator limitation;
this change does not establish value preservation for those cases.

Check both the HTTP status and the response body's `status.code`: an execution failure can retain HTTP 200
while returning `status.code` 400 and null result data.

### Verified behavior

The API fixture uses a strong schema, with a `SECONDARY` index on `city` and a `RANGE` index on `age`.
Acceptance results are limited to these test cases:

| Area | Tested cases | Test methods |
|---|---|---|
| Reads | Label scans; equality and range predicates; boolean combinations; directed one- and two-hop patterns; empty results; whole-string regex matching on computed strings | `testGet`, `testExactReadsAndPredicates`, `testRelationQuery`, `testComputedRegexExecutesExtensionPredicate`, `testComputedRegexRequiresWholeStringMatch` |
| Results | Aliases, scalar and node values, nested values, relationship ids, path shape, null and missing properties | `testReturnNodeIdAsPrimitiveValue`, `testReturnNodeDoesNotLeakInternalIdTypes`, `testReturnNestedIdDoesNotLeakInternalIdTypes`, `testReturnRelationIdDoesNotLeakInternalIdTypes`, `testReturnPathShape`, `testNullAndMissingProperty` |
| Aggregation and pagination | `DISTINCT`, `count`/`sum`/`min`/`max`/`avg`, `ORDER BY`, `SKIP`, and `LIMIT` | `testDuplicatesDistinctAndPagination`, `testAggregates` |
| Writes | Vertex and edge `CREATE`, property `SET`, edge and vertex `DELETE`; state checked through native REST reads | `testCreate`, `testCreateSetAndDeleteWithNativeReadback` |
| Failed write | A rejected two-vertex `CREATE` left no residue during 32 subsequent query and native-read checks | `testFailedWriteDoesNotLeakIntoLaterRequests` |
| Errors and routing | Invalid syntax and request shape, content type, binding keys and the reserved null marker, schema values, authentication, and graph routing | `testInvalidRequests`, `testRejectPlainTextPost`, `testRejectInvalidQuery`, `testRejectInvalidBindingShapeAndKeys`, `testRejectTranslatorNullMarker`, `testRejectTranslatorNullSentinelInBindings`, `testAuthenticationAndGraphRouting`, `testSpecifiedGraphRouting` |

An additional post-merge REST run on `5039e5b` re-executed the documented guide examples against a fresh RocksDB graph:
reads, projection with ordering and limit, aggregation, single-vertex `CREATE`, `SET`/`REMOVE`, edge `DELETE`,
`DETACH DELETE`, and every request-form contract above held, including the missing-binding execution error on all
three forms. The two-vertex shorthand `CREATE (a)-[:knows]->(b)` fails on schemas requiring vertex properties: on a `PRIMARY_KEY` label the statement is rejected with an execution error reporting that primary keys must be set; on vertex labels with non-nullable properties, even under `AUTOMATIC` id strategy, it fails the graph transaction non-null check (`checkNonnullProperty`) because required attributes are omitted. On schemas with mandatory properties or explicit primary keys, do not rely on property-less vertex shortcuts; create vertices with complete properties separately before creating connecting edges.

Two guide examples depend on the schema. The range-predicate read (`WHERE n.age > 30`) needs the `RANGE` index on `age`
declared in the fixture schema above; the `scripts/example.groovy` schema has only `SECONDARY` indexes on `person`
(`city`, and `age` with `city`), so a range comparison on `age` there is rejected with a "not indexed" error until a
`RANGE` index exists. The create, update and delete examples were renamed afterwards to `alice`, `bob` and `carol` because
`scripts/example.groovy` already seeds `marko`, `vadas`, `josh` and `peter`, and on a `PRIMARY_KEY` label a `CREATE` with a seeded
name replaces that vertex; the rename changes only data values and was not run as a separate verification.

### Test and Implementation Boundaries

Unit and integration test suites cover `CypherApiTest`, `CypherClientTest`, and `CypherOpProcessorTest`.
On schemas with non-nullable properties or `PRIMARY_KEY` strategy, the shorthand `CREATE (a)-[:knows]->(b)` is rejected due to non-null property checks (`checkNonnullProperty`) or missing primary keys. Create vertices with complete properties separately before creating connecting edges.

### Not verified by this change

Advanced constructs and behaviors outside the verified set above remain unverified:
- Complex clauses: `MERGE`, `OPTIONAL MATCH`, `WITH`, `UNWIND`, `UNION`, variable-length path patterns;
- Extended features: Procedures, Cypher Schema DDL, `EXPLAIN` / `PROFILE`;
- Protocols & drivers: Bolt protocol drivers, cross-request transactions.
