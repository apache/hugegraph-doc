---
title: "FAQ"
linkTitle: "FAQ"
weight: 6
---

## Deployment and startup {#deployment}

### Choose RocksDB or HStore {#choose-backend}

Start with Server + RocksDB for development or a standalone deployment. Use an HStore cluster with PD, Store, and Server when you need multiple nodes
and replicas. Capacity and performance depend on graph structure, queries, and hardware; test with your own data before choosing a deployment.

Version 1.7.0 supports RocksDB, HStore, HBase, and Memory. Legacy backends such as Cassandra, ScyllaDB, MySQL, and PostgreSQL require a version earlier than 1.7.0.
See the [Server quick start](/docs/quickstart/hugegraph/hugegraph-server/) for deployment steps.

### Investigate a core dump at startup {#core-dump}

Check `java -version` first. HugeGraph 1.8.0 uses Java 17, and 1.7.0 uses Java 11.
Then inspect the Server logs and the JVM's `hs_err_pid*.log` for the crash location, system architecture, and native-library versions.
A core dump can also involve native libraries or memory, so the message alone does not identify the cause.

### Which backends need init-store {#initialize-backend}

Run `bin/init-store.sh` before using RocksDB or HBase for the first time. Memory and HStore do not use this script; PD and Store manage HStore storage.
The `backend` and `serializer` settings must match. RocksDB, for example, uses `binary`.

If Server starts but reports that the backend is not connected, check initialization results, backend configuration, and connectivity.

### Resolve a missing GLIBCXX version during init-store {#native-library}

This error means the system's `libstdc++` lacks a symbol required by the RocksDB native library.

```text
java.lang.UnsatisfiedLinkError: .../librocksdbjni....so:
.../libstdc++.so.6: version `GLIBCXX_3.4.10' not found
```

Check the release's supported platform, system architecture, and the `libstdc++` actually loaded.
Use a compatible runtime or the official container image for that release. When updating the C++ runtime, check the missing symbol and compatibility;
a single GCC version number does not establish compatibility for every release.

### Which Server startup script should I use {#start-script}

Current distributions use `bin/start-hugegraph.sh`. GremlinServer and the REST Server run in the same process.
The `start-restserver.sh` and `start-gremlinserver.sh` commands in older guides do not apply to current distributions.

### Which graphs does the startup script load {#load-graphs}

The script name does not select a graph. Server loads local graph configurations from `conf/graphs` by default;
change that directory with `graphs` in `conf/rest-server.properties`. Give each local graph its own configuration file and restart Server after changes.

`graph.load_from_local_config` defaults to `false` and controls constructor preloading. It cannot disable startup loading of local graphs.
See the [Server configuration guide](/docs/config/config-guide/).

## Connections and queries {#queries}

### Read compressed responses with curl {#compressed-response}

The batch vertex and edge APIs return gzip-compressed responses. Let curl decode them according to the response headers.

```bash
curl --compressed \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices?limit=10'
```

Supply credentials when authentication is enabled. If the content is still unexpected, check the HTTP status, `Content-Type`, and `Content-Encoding`.
Do not pipe a JSON error response directly to `gunzip`.

### A vertex exists, but lookup by ID cannot find it {#vertex-id}

Copy the `id` from an existing query result and preserve its type. String IDs need JSON double quotes; numeric IDs do not.
For example, the JSON representation of the string ID `1:marko` is `"1:marko"`.

URL-encode that entire JSON ID before putting it in the URL path. Adding quotes alone does not handle reserved characters in an ID.

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

Start with a small `limit` to check the filter and returned data. Use pagination or narrower filters for large labels.
For property filters, check the required indexes instead of requesting every element with that label.

### REST works, but Gremlin returns HTTP 500 {#gremlin-connection}

Read the error response and Server logs first. Check `host` and `port` in `gremlin-server.yaml` against `gremlinserver.url` in `rest-server.properties`.
They must identify the same reachable Gremlin service. Restart Server after changing the configuration.

A reachable REST endpoint proves that the HTTP entrypoint works. Query errors, permissions, and the Gremlin connection still need separate checks.

### REST returns HTTP 415 {#content-type}

For a JSON request body, set `Content-Type: application/json` and check that the body contains valid JSON.

## Import and data maintenance {#data-management}

### Loader reports Socket Timeout {#loader-timeout}

Check Server load, logs, and the network. If import concurrency is too high, reduce the batch size or request concurrency,
then adjust timeout and retry settings to the observed request duration.
Error tolerance controls whether processing continues after bad records; investigate the failure before increasing it.
See the [Loader guide](/docs/quickstart/toolchain/hugegraph-loader/) for parameters.

### Clear all data from a graph {#clear-graph}

An administrator can call the following endpoint. It deletes the graph's schema, vertices, edges, and indexes, so confirm the target graph and backup first.

```text
DELETE /graphspaces/{graphspace}/graphs/{graph}/clear
```

Supply the URL-encoded `confirm_message` query parameter with the exact value `I'm sure to delete all data`.
See the [Graph API](/docs/clients/restful-api/graphs/) for the complete request.

### Schema still exists after clearing the backend {#schema-cache}

A running Server caches graph and schema state. Clearing the underlying storage directly leaves that cache out of sync and requires a Server restart.
Prefer supported graph-management APIs. Stop the affected services and back up the data before any direct backend maintenance.

## Modeling and IDs {#modeling}

### A vertex or edge ID exceeds the length limit {#id-length}

Current binary storage allows vertex IDs up to 16384 bytes and edge IDs up to 65536 bytes. The limit applies to encoded bytes.
Use shorter business identifiers as primary keys instead of combining large text fields into an ID.

Index IDs longer than 32 bytes use hash storage. This is handled separately from oversized vertex and edge IDs.

### Are nested properties supported {#nested-properties}

Nested properties are not supported. Model a nested object as a vertex and connect it with an edge when its relationships need to be retained.

### Can one edge label connect several vertex-label pairs {#edge-links}

Yes. Call `link(sourceLabel, targetLabel)` once for each pair when creating the `EdgeLabel`.
For example, one `investment` label can connect both `individual → enterprise` and `enterprise → enterprise`.
The deprecated `sourceLabel()` and `targetLabel()` builder methods describe only one pair.

Search the [Server issues](https://github.com/apache/hugegraph/issues) or
[Toolchain issues](https://github.com/apache/hugegraph-toolchain/issues) for other questions.
