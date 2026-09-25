---
title: "Cypher Compatibility"
linkTitle: "Cypher Compatibility"
weight: 3
---

### Scope

This page records the cases verified for the current Cypher development change. It does not claim full
openCypher or Neo4j compatibility, or compatibility across every released HugeGraph version. The tested
working tree is based on [`hugegraph/hugegraph@27a7c9b`](https://github.com/hugegraph/hugegraph/commit/27a7c9b42274d6d4f95eabed6d2051d393ae0eaf)
and uses Java `17.0.20.1`, TinkerPop `3.8.1`, `org.opencypher.gremlin:translation:1.0.4`, and RocksDB.

The endpoint is `/graphspaces/{graphspace}/graphs/{graph}/cypher`. General usage is covered in the
[HugeGraph Cypher guide](/docs/language/hugegraph-cypher/).

### Request forms and parameters

| Request | Verified contract | Test method |
|---|---|---|
| `GET ?cypher=<URL-encoded statement>` | Existing query-string form | `testGet` |
| `POST application/json` with raw Cypher text | Legacy raw-body form remains available | `testPost` |
| `POST text/plain` with raw Cypher text | Plain-text form | `testPlainTextPost` |
| `POST application/json` with a JSON object | Query and bindings are sent separately | `testParameters` |

```json
{
  "cypher": "MATCH (n:cypher_person) WHERE n.name = $name RETURN n.name",
  "parameters": {"name": "marko"}
}
```

For the JSON-object form, `cypher` must be a nonblank string and `parameters`, if present, must be an object.
Omitting `parameters` means an empty map. A referenced but missing binding is an execution error; an explicit
null value is valid. Tests cover string, number, and boolean values, quotes and newlines, the binding names
`id` and `label`, and the default limit of 16 parameters. Values remain bindings and do not alter query text.

Check both the HTTP status and the response body's `status.code`: an execution failure can retain HTTP 200
while returning `status.code` 400 and null result data.

### Verified behavior

The API fixture uses a strong schema, with a `SECONDARY` index on `city` and a `RANGE` index on `age`.
Acceptance results are limited to these test cases:

| Area | Tested cases | Test methods |
|---|---|---|
| Reads | Label scans; equality and range predicates; boolean combinations; directed one- and two-hop patterns; empty results | `testGet`, `testExactReadsAndPredicates`, `testRelationQuery` |
| Results | Aliases, scalar and node values, nested values, relationship ids, path shape, null and missing properties | `testReturnNodeIdAsPrimitiveValue`, `testReturnNodeDoesNotLeakInternalIdTypes`, `testReturnNestedIdDoesNotLeakInternalIdTypes`, `testReturnRelationIdDoesNotLeakInternalIdTypes`, `testReturnPathShape`, `testNullAndMissingProperty` |
| Aggregation and pagination | `DISTINCT`, `count`/`sum`/`min`/`max`/`avg`, `ORDER BY`, `SKIP`, and `LIMIT` | `testDuplicatesDistinctAndPagination`, `testAggregates` |
| Writes | Vertex and edge `CREATE`, property `SET`, edge and vertex `DELETE`; state checked through native REST reads | `testCreate`, `testCreateSetAndDeleteWithNativeReadback` |
| Failed write | A rejected two-vertex `CREATE` left no residue during 32 subsequent query and native-read checks | `testFailedWriteDoesNotLeakIntoLaterRequests` |
| Errors and routing | Invalid syntax and request shape, binding keys, schema values, authentication, and graph routing | `testInvalidRequests`, `testRejectInvalidQuery`, `testRejectInvalidBindingShapeAndKeys`, `testAuthenticationAndGraphRouting`, `testSpecifiedGraphRouting` |

`CypherApiTest` passed 20/20, `CypherClientTest` 7/7, and `CypherOpProcessorTest` 4/4, with no skips.
Related Gremlin tests passed 10 cases with one inapplicable `testClearAndInit` skip for a non-shared backend;
Login tests passed 3/3. EditorConfig formatting and the repository-root clean compile passed.
The code change is in [draft PR #238](https://github.com/hugegraph/hugegraph/pull/238). The compatibility
note at tested source commit [`c3b2f3e`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/docs/cypher-compatibility.md)
contains the method-level mapping and verification record. Test sources at that commit:
[`CypherApiTest`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/api/CypherApiTest.java),
[`CypherClientTest`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/api/cypher/CypherClientTest.java),
and [`CypherOpProcessorTest`](https://github.com/hugegraph/hugegraph/blob/c3b2f3e3b9ff1de0495260d6eec0b16816d7f095/hugegraph-server/hugegraph-test/src/main/java/org/apache/hugegraph/opencypher/CypherOpProcessorTest.java).

### Baseline failure and current fix

At the pinned baseline commit above, a failed two-vertex `CREATE` left delayed residue in two observations.
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
