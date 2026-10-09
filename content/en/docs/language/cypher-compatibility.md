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
statement that references `$param` returns no rows rather than failing — see
[Known limitations](/docs/language/hugegraph-cypher/#known-limitations).

This page records the cases verified for the current Cypher development change. It does not claim full
openCypher or Neo4j compatibility, or compatibility across every released HugeGraph version. The tested
working tree is based on current Apache `master` at
[`af3c686`](https://github.com/apache/hugegraph/commit/af3c6867f4bfa3f95e63ad472c12a88c63529c1b),
which declares HugeGraph `1.8.0`, Java 17, and TinkerPop `3.8.1`. This is a standalone Cypher change on that
baseline. The runtime uses Java `17.0.20.1`, TinkerPop `3.8.1`, `org.opencypher.gremlin:translation:1.0.4`, and RocksDB.

The endpoint is `/graphspaces/{graphspace}/graphs/{graph}/cypher`. General usage is covered in the
[HugeGraph Cypher guide](/docs/language/hugegraph-cypher/).

### Request forms and parameters

| Request | In a released version | Verified contract on the tested tree | Test method |
|---|---|---|---|
| `GET ?cypher=<URL-encoded statement>` | Yes | Existing query-string form | `testGet` |
| `POST application/json` with raw Cypher text | Yes | Legacy raw-body form remains available | `testPost` |
| `POST text/plain` with any body | No | Rejected with HTTP 415 | `testRejectPlainTextPost` |
| `POST application/json` with a JSON object | No — introduced by [#3289](https://github.com/apache/hugegraph/pull/3289) | Query and bindings are sent separately | `testParameters` |

The JSON object form below is therefore **not available in any released HugeGraph version**; it describes the merged change on `master` (the 1.8.0 development line). On released versions a statement using `$param` runs with that binding bound to `null` and
returns no rows — see [Known limitations](/docs/language/hugegraph-cypher/#known-limitations).

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
`GET ?cypher=` and raw-body `POST`: [#3289](https://github.com/apache/hugegraph/pull/3289) always attaches the
parameters map and rejects unresolved `$param` references, replacing the released null-and-no-rows behaviour
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

The standalone code change is in [ASF PR #3289](https://github.com/apache/hugegraph/pull/3289),
which was merged into Apache `master` on 2026-10-08 as
[`5039e5b`](https://github.com/apache/hugegraph/commit/5039e5b67d26ea305b8509d3a414877749baaebb).
The verified pre-merge baseline remains pinned above. The original development
change remains linked in [PR #238](https://github.com/hugegraph/hugegraph/pull/238). At source commit
[`8d06ad3`](https://github.com/apache/hugegraph/blob/8d06ad3b18fbd18807cf545184d07e6fec0c55b4/docs/cypher-compatibility.md), `CypherApiTest` passed 23/23,
`CypherClientTest` 7/7, and `CypherOpProcessorTest` 8/8, with no skips. The additional predicate,
execution-context, and request-ownership regressions passed, as did all nine `AbstractRestClientTest`
cases, including ASCII and UTF-16 map bodies with gzip. Login tests passed 3/3; related Gremlin tests
passed 10 cases with one existing, inapplicable `testClearAndInit` skip for a non-shared backend.
EditorConfig formatting, the repository-root clean compile, and the full install passed. The packaged
API JAR matched the compiled target JAR before the live test run.

The compatibility note at that fixed commit contains the verification record and method-level mapping.
Test sources:
[`CypherApiTest`](https://github.com/apache/hugegraph/blob/8d06ad3b18fbd18807cf545184d07e6fec0c55b4/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/api/CypherApiTest.java),
[`CypherClientTest`](https://github.com/apache/hugegraph/blob/8d06ad3b18fbd18807cf545184d07e6fec0c55b4/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/api/cypher/CypherClientTest.java),
and [`CypherOpProcessorTest`](https://github.com/apache/hugegraph/blob/8d06ad3b18fbd18807cf545184d07e6fec0c55b4/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/opencypher/CypherOpProcessorTest.java).
The earlier verification on
[`e62c961`](https://github.com/apache/hugegraph/commit/e62c961e00221569d4f955abbadf60faee45b283)
remains at
[`fd8f4a6`](https://github.com/apache/hugegraph/blob/fd8f4a626b9e899663d3114035e2967e421b3e55/docs/cypher-compatibility.md).
The earlier, pre-rebase verification remains at
[`c3b2f3e`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/docs/cypher-compatibility.md).

### Baseline failure and current fix

At the earlier baseline
[`27a7c9b`](https://github.com/apache/hugegraph/commit/27a7c9b42274d6d4f95eabed6d2051d393ae0eaf),
a failed two-vertex `CREATE` left delayed residue in two observations.
In the first run, an immediate native read missed the prefix, but later aggregate/sort reads exposed it and
a full native listing confirmed it. In the second reproduction, immediate native reads and seven later
count/native-read checks showed no prefix; it appeared after the eighth count. The original baseline evidence remains in
[the baseline report](https://github.com/apache/hugegraph-doc/pull/499#issuecomment-5826172378).

The current development change passes `testFailedWriteDoesNotLeakIntoLaterRequests`: native reads and 32
later query/native-read checks confirm that this fixture leaves no residue. This verifies the reported
failure case on the tested stack; it does not establish every rollback path, cross-request transaction
semantics, or full write atomicity for all statements and backends.

### Not verified by this change

Advanced constructs and behaviors outside the test cases above remain unverified. This includes `MERGE`,
`OPTIONAL MATCH`, `WITH`, `UNWIND`, `UNION`, variable-length paths, broad function coverage, procedures,
Cypher schema DDL, `EXPLAIN`/`PROFILE`, HStore, Bolt, cross-request transactions, and performance.
