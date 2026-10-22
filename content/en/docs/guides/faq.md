---
title: "FAQ"
linkTitle: "FAQ"
weight: 6
---

## Deployment and startup {#deployment}

### Choose RocksDB or HStore {#choose-backend}

For development, testing, or small-to-medium standalone deployments, **Server + RocksDB** is recommended for its simplicity and high
performance. When data volume is large (TB to PB scale) or requires horizontal scalability and multi-replica high availability, deploy an
**HStore distributed cluster** (PD + Store + Server).

Version 1.7.0 supports RocksDB, HStore, HBase, and Memory. Legacy backends such as Cassandra, ScyllaDB, MySQL, and PostgreSQL require a
version earlier than 1.7.0. See the [Server quick start](/docs/quickstart/hugegraph/hugegraph-server/) for deployment steps.

### Investigate a core dump at startup {#core-dump}

First, run `java -version` to confirm your JDK version: **HugeGraph master (1.8 baseline) requires Java 17**, and **1.7.0 requires Java 11** (Java 8 is no longer supported). If the JDK version is correct, inspect the Server logs and the JVM crash log (`hs_err_pid*.log`) to check for
architecture mismatches, missing native libraries (such as RocksDB JNI), or insufficient system memory.

### Which backends need init-store {#initialize-backend}

When using local persistent backends like RocksDB or HBase, **you must run `bin/init-store.sh` before the first startup**. Memory (in-memory
backend) and HStore (distributed backend) do not use this script; HStore storage is managed directly by PD and Store.

Note: The `backend` and `serializer` settings must match (for example, RocksDB requires `binary`). If the service starts but reports that
the backend is disconnected, verify initialization and backend connection settings first.

### Resolve a missing GLIBCXX version during init-store {#native-library}

The following error indicates that the host system's `libstdc++` version is too old and lacks symbols required by the RocksDB JNI native library:

```text
java.lang.UnsatisfiedLinkError: .../librocksdbjni....so:
.../libstdc++.so.6: version `GLIBCXX_3.4.10' not found
```

To resolve: Upgrade the system's `libstdc++` (or install a newer GCC runtime), or run HugeGraph using the official Docker image.

### Which Server startup script should I use {#start-script}

Current releases uniformly use `bin/start-hugegraph.sh`. Both GremlinServer and the REST Server start in the same process. The
`start-restserver.sh` and `start-gremlinserver.sh` scripts from older documentation are deprecated.

### Which graphs does the startup script load {#load-graphs}

The script name has no relation to the graph name. Server scans and loads all graph configurations in `conf/graphs` by default (this
directory can be customized via `graphs` in `conf/rest-server.properties`). Each local graph uses an independent configuration file; restart
Server after editing configurations.

Note: `graph.load_from_local_config` defaults to `false` (controlling constructor preloading) and cannot prevent local graph loading at
startup. See the [Server configuration guide](/docs/config/config-guide/).

## Connections and queries {#queries}

### Read compressed responses with curl {#compressed-response}

Batch vertex and edge endpoints return gzip-compressed data by default. Add the `--compressed` flag to curl to decompress automatically:

```bash
curl --compressed \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices?limit=10'
```

If authentication is enabled, supply credentials. If output remains unexpected, check HTTP status codes, `Content-Type`, and
`Content-Encoding`. Do not pipe JSON error responses directly into `gunzip`.

### A vertex exists, but lookup by ID cannot find it {#vertex-id}

Check the exact format and type of `id` in existing query results: **string IDs require JSON double quotes, while numeric IDs do not**. For
example, the string ID `1:marko` is written in JSON as `"1:marko"`.

When embedding this JSON ID into a URL path, URL-encode the entire string including double quotes. If the ID contains special characters,
encoding the whole quoted string is required:

| Character | URL encoding |
| --- | --- |
| `+` | `%2B` |
| Space | `%20` |
| `/` | `%2F` |
| `?` | `%3F` |
| `%` | `%25` |
| `#` | `%23` |
| `&` | `%26` |
| `=` | `%3D` |
| `"` | `%22` |

### Queries by label time out {#label-timeout}

When a label contains a large volume of data, scanning all records will exhaust resources and time out. Recommended solutions:
1. Append `.limit(n)` to restrict the number of returned records;
2. Use pagination to fetch results incrementally;
3. Filter by specific properties and ensure the relevant properties are indexed to prevent full scans.

### REST works, but Gremlin returns HTTP 500 {#gremlin-connection}

A working REST endpoint only confirms HTTP reachability. HTTP 500 from Gremlin typically stems from:
1. **Gremlin Server connection failure**: Verify that `gremlinserver.url` in `conf/rest-server.properties` points to a reachable Gremlin
port (default `8182`, configured in `conf/gremlin-server.yaml`);
2. **Query syntax or logic error**: Such as unindexed property filtering triggering scan limits;
3. **Missing or expired credentials**.

Check `logs/hugegraph-server.log` for the detailed exception stack trace.

### REST returns HTTP 415 {#content-type}

When sending POST/PUT requests with a JSON body, set the header `Content-Type: application/json` and ensure the payload is valid JSON.

## Import and data maintenance {#data-management}

### Loader reports Socket Timeout {#loader-timeout}

Import timeouts usually occur when batch sizes are too large or write concurrency is too high for the Server. Recommended actions:
1. Decrease `--batch-size` (e.g., from 500 down to 200);
2. Reduce the number of concurrent insert threads;
3. Increase `--timeout` and configure retry settings. See the [Loader guide](/docs/quickstart/toolchain/hugegraph-loader/) for parameter details.

### Clear all data from a graph {#clear-graph}

Administrators can call the following endpoint to wipe schema, vertices, edges, and indexes from a graph (verify target graph and backups beforehand):

```text
DELETE /graphspaces/{graphspace}/graphs/{graph}/clear
```

The request requires the `confirm_message` query parameter, strictly matching `I'm sure to delete all data` (URL-encoded). See the [Graph
API](/docs/clients/restful-api/graphs/) for complete reference.

### Schema still exists after clearing the backend {#schema-cache}

Server caches metadata in memory. Bypassing Server to clear underlying storage directly (such as wiping RocksDB directories or HBase tables)
causes cache inconsistency. If storage was manually deleted, **restart Server** to clear the cache. For normal cleanup, use the official
[Clear Graph API](/docs/clients/restful-api/graphs/#clear-graph).

## Modeling and IDs {#modeling}

### A vertex or edge ID exceeds the length limit {#id-length}

To maintain storage and indexing performance, HugeGraph enforces maximum ID length limits (calculated by encoded byte count):
- **Vertex ID**: Maximum 16384 bytes (16 KB);
- **Edge ID**: Maximum 65536 bytes (64 KB).

Use concise business identifiers as primary keys rather than concatenating large text blocks. Note: Property index values exceeding 32 bytes
are automatically hashed for storage and will not trigger length errors.

### Are nested properties supported {#nested-properties}

Nested properties (complex nested maps or objects) are not currently supported. To represent multi-level relations, model the nested object
as an independent vertex and link it to the parent vertex with an edge.

### Can one edge label connect several vertex-label pairs {#edge-links}

Yes. When creating an `EdgeLabel`, invoke `link(sourceLabel, targetLabel)` once for each source-target pair.
For example, an `investment` edge label can link both `individual → enterprise` and `enterprise → enterprise`. The deprecated
`sourceLabel()` and `targetLabel()` methods only supported a single pair and should no longer be used.

For other questions, search the [Server issues](https://github.com/apache/hugegraph/issues) or [Toolchain
issues](https://github.com/apache/hugegraph-toolchain/issues).
