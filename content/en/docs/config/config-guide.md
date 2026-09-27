---
title: "Server Startup Guide"
linkTitle: "Server Startup Guide"
weight: 1
search_keywords: [HugeGraph configuration, server config, configuration guide]
search_boost: 1.6
---

### 1 Overview

Default configuration lives under `conf/` in the extracted distribution. External HBase, Kerberos, and HTTPS files can use other paths; see the corresponding backend, authentication, and HTTPS guides.

The main files are `gremlin-server.yaml`, `rest-server.properties`, and `hugegraph.properties`.

`HugeGraphServer` integrates GremlinServer and RestServer, configured by `gremlin-server.yaml` and `rest-server.properties` respectively.

- [GremlinServer](https://tinkerpop.apache.org/docs/3.5.1/reference/#gremlin-server): Accepts Gremlin requests and invokes the graph engine.
- RestServer: Provides REST APIs that invoke Core APIs. A Gremlin request body is forwarded to GremlinServer to operate on graph data.

The following sections describe these files.

> [!WARNING]
> **Production requires Server authentication and network access controls**
>
> The authentication settings on this page apply to HugeGraph Server. In production, enable [authentication and authorization](/docs/config/config-authentication/), maintain an IP allowlist, grant minimum permissions, and retain and protect Server `audit-*.log` files. Commented authentication settings in the examples indicate that authentication is disabled by default.

The distribution copies default files from the Server repository into the installation directory's `conf/` folder. Options absent from these files use source-code defaults; explicit file settings override those defaults.
The file-loading behavior on this page was checked against Server master commit `2f827d6`. Use the configuration files and entry scripts that correspond to your installed release.

| File | Source and purpose | Loading behavior |
|------|------------|----------|
| `conf/gremlin-server.yaml` | Shipped with the distribution; configures Gremlin Server. | Passed to Server by `start-hugegraph.sh`. |
| `conf/rest-server.properties` | Shipped when building the checked Server master; configures REST Server, PD, authentication, and related settings. | Read by startup scripts and Server; the corresponding container entrypoint also updates supported settings before startup. |
| `conf/graphs/hugegraph.properties` | Shipped default graph configuration, using RocksDB. | Scanned by both `init-store.sh` and application initialization, which attempts to load local graphs. `graph.load_from_local_config` defaults to `false` and controls only constructor preloading and rescanning on `reload()`. |
| `conf/graphs/hstore.properties.template` | Shipped HStore template; users create other graph configurations as needed. | The HStore image renames it to `hugegraph.properties` during its build; distribution users can copy and customize it. |

Complete defaults are in Server master: [gremlin-server.yaml](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/conf/gremlin-server.yaml), [rest-server.properties](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/conf/rest-server.properties), [hugegraph.properties](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/conf/graphs/hugegraph.properties), and [hstore.properties.template](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/conf/graphs/hstore.properties.template).

The following Docker environment-variable behavior applies only to images built from `master`; arbitrary variable names are not converted into configuration options. Before initialization and startup, this entrypoint processes `HG_SERVER_BACKEND`, `HG_SERVER_PD_PEERS`, `HG_SERVER_USE_PD`, `HG_SERVER_CLUSTER`, `HG_SERVER_REST_URL`, `HG_SERVER_MIN_FREE_MEMORY`, `HG_SERVER_AUTH_TOKEN_SECRET`, `HG_SERVER_INIT_STORE_ENABLED`, and `PASSWORD`. Check the tagged entrypoint for historical release images. See [Docker entrypoint](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/docker/docker-entrypoint.sh).

### 2 gremlin-server.yaml

This example shows commonly adjusted startup options. Use the source links above for the complete serializer and plugin configuration.

The shipped `host` and `port` lines are commented out. Without explicit values, the address is `127.0.0.1:8182`. Uncomment and set these options to change the listener:

```yaml {filename="conf/gremlin-server.yaml"}
#host: 127.0.0.1
#port: 8182
evaluationTimeout: 30000
channelizer: org.apache.tinkerpop.gremlin.server.channel.WsAndHttpChannelizer
graphs: {}
ssl: { enabled: false }
```

Usually, focus on `channelizer`, `host`, and `port`. Graphs are not loaded from the Gremlin Server `graphs` section. During application initialization, the REST-side manager scans the `graphs` directory and attempts to load local graph configurations. `graph.load_from_local_config` controls only constructor preloading and rescanning on `reload()`; its default `false` does not disable local loading during application initialization.

- `channelizer`: The default `WsAndHttpChannelizer` supports WebSocket and HTTP. Gremlin Console uses WebSocket; HugeGraph Client, Loader, and Hubble use HTTP.

GremlinServer listens at `127.0.0.1:8182` by default. Set `host` and `port` to change this address.

- `host`: The hostname or IP of the GremlinServer host. RestServer forwards Gremlin requests; GremlinServer is not directly exposed to users.
- `port`: The GremlinServer listener port.

Set the matching `gremlinserver.url=http://host:port` in `rest-server.properties`.

### 3 rest-server.properties

The following example lists `rest-server.properties` options. The master template omits `graph.load_from_local_config`, whose source-code default is `false`. Setting it to `true` is optional: it enables constructor preloading and rescanning on `reload()`. Application initialization still scans and attempts to load local graph configurations.

```properties
# bind url
# could use '0.0.0.0' or specified (real)IP to expose external network access
restserver.url=http://127.0.0.1:8080
#restserver.enable_graphspaces_filter=false
# gremlin server url, need to be consistent with host and port in gremlin-server.yaml
#gremlinserver.url=127.0.0.1:8182

graphs=./conf/graphs
graph.load_from_local_config=true

# The maximum thread ratio for batch writing, only take effect if the batch.max_write_threads is 0
batch.max_write_ratio=80
batch.max_write_threads=0

# configuration of arthas
arthas.telnetPort=8562
arthas.httpPort=8561
arthas.ip=127.0.0.1
arthas.disabledCommands=jad

# authentication configs
#auth.authenticator=org.apache.hugegraph.auth.StandardAuthenticator
# for admin password, By default, it is pa and takes effect upon the first startup
#auth.admin_pa=pa
#auth.graph_store=hugegraph

# use pd
# usePD=true

# slow query log
log.slow_query_threshold=1000
# bytes of request body recorded as-is (may contain sensitive literals), 0 to disable
log.slow_query_body_limit=512

# jvm(in-heap) memory usage monitor, set 1 to disable it
memory_monitor.threshold=0.85
memory_monitor.period=2000
```

- `restserver.url`: The REST listener URL. Use a specific address for remote access, or `http://0.0.0.0` to listen on every interface while restricting the accessible network.
- `graphs`: The graph configuration directory, defaulting to `./conf/graphs`. Both `init-store.sh` and application initialization scan it; initialization attempts to load its properties files.
- `graph.load_from_local_config`: Controls constructor preloading and rescanning on `reload()`, with source-code default `false`. It does not block local loading during application initialization and is not a security isolation switch.

> The upstream template still uses `arthas.telnet_port`, `arthas.http_port`, and `arthas.disabled_commands`, but `ServerOptions` reads the camelCase names in the example. Use `arthas.telnetPort`, `arthas.httpPort`, and `arthas.disabledCommands` in custom configurations.

> `gremlinserver.url` is the GremlinServer address used by RestServer, defaulting to `http://127.0.0.1:8182`. It must match `host` and `port` in `gremlin-server.yaml`. Like the template, it can omit the scheme; missing schemes receive an `http://` prefix.

### 4 hugegraph.properties

`hugegraph.properties` is the default shipped graph configuration. Each additional graph needs its own properties file under `conf/graphs`. This example shows the key settings for the default RocksDB backend; see the source links above for the complete file.

```properties
gremlin.graph=org.apache.hugegraph.HugeFactory
backend=rocksdb
serializer=binary
store=hugegraph
```

The main uncommented options are:

- `gremlin.graph`: The graph entry point used by GremlinServer. Leave it unchanged unless enabling authentication, which uses `org.apache.hugegraph.auth.HugeFactoryAuthProxy`.
- `vertex.cache_type` / `edge.cache_type`: Cache implementation, either `l1` or `l2`, defaulting to `l2`.
- `backend`: The storage backend. Version 1.7.0 supports memory, rocksdb, hstore, and hbase.
- `serializer`: Serialization of schemas, vertices, and edges. RocksDB uses binary.
- `store`: The graph's backend store name.
- `task.schedule_period`, `task.retry`, `task.wait_timeout`: Task scheduling period in seconds, retry count, and wait timeout in seconds. HStore uses a distributed scheduler; other backends use a local scheduler. The old `task.scheduler_type` key is ignored.
- `search.text_analyzer` / `search.text_analyzer_mode`: Full-text analyzer and mode. Supported analyzers include `ansj`, `hanlp`, `smartcn`, `jieba`, `jcseg`, `mmseg4j`, and `ikanalyzer`, each with its own mode values.
- `rocksdb.data_path`: RocksDB data directory, defaulting to `rocksdb-data/data`; applies only when `backend=rocksdb`.
- `rocksdb.wal_path`: RocksDB WAL directory, defaulting to `rocksdb-data/wal`; applies only when `backend=rocksdb`.

### 5 Multi-Graph Configuration

A Server can load multiple graphs, each with its own properties file. This example creates a RocksDB graph `hugegraph_rocksdb` and an in-memory graph `hugegraph_memory`.

**[Optional]: Modify rest-server.properties**

Set the graph configuration directory with `graphs` in `rest-server.properties`, defaulting to `graphs=./conf/graphs`. Adjust it for another directory. The example optionally enables constructor preloading and rescanning on `reload()` with `graph.load_from_local_config=true`; application initialization still reads local graph configurations from this directory:

```properties
graphs=./conf/graphs
graph.load_from_local_config=true
```

Under `conf/graphs`, create `hugegraph_memory.properties` and `hugegraph_rocksdb.properties` based on `hugegraph.properties`.

Modify `hugegraph_memory.properties` as follows:

```properties
backend=memory
serializer=text
store=hugegraph_memory
```

Modify `hugegraph_rocksdb.properties` as follows:

```properties
backend=rocksdb
serializer=binary

store=hugegraph_rocksdb
```

**Stop Server, run init-store.sh to initialize the new graphs, then restart Server.**

```bash
$ ./bin/stop-hugegraph.sh
```

```bash
$ ./bin/init-store.sh

Initializing HugeGraph Store...
2023-06-11 14:16:14 [main] [INFO] o.a.h.u.ConfigUtil - Scanning option 'graphs' directory './conf/graphs'
2023-06-11 14:16:14 [main] [INFO] o.a.h.c.InitStore - Init graph with config file: ./conf/graphs/hugegraph_rocksdb.properties
...
2023-06-11 14:16:15 [main] [INFO] o.a.h.StandardHugeGraph - Graph 'hugegraph_rocksdb' has been initialized
2023-06-11 14:16:15 [main] [INFO] o.a.h.c.InitStore - Init graph with config file: ./conf/graphs/hugegraph_memory.properties
...
2023-06-11 14:16:16 [main] [INFO] o.a.h.StandardHugeGraph - Graph 'hugegraph_memory' has been initialized
2023-06-11 14:16:16 [main] [INFO] o.a.h.StandardHugeGraph - Close graph standardhugegraph[hugegraph_rocksdb]
...
2023-06-11 14:16:16 [main] [INFO] o.a.h.HugeFactory - HugeFactory shutdown
2023-06-11 14:16:16 [hugegraph-shutdown] [INFO] o.a.h.HugeFactory - HugeGraph is shutting down
Initialization finished.
```

```bash
$ ./bin/start-hugegraph.sh

Starting HugeGraphServer in daemon mode...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)...OK
Started [pid 21614]
```

List the created graphs:

```bash
curl http://127.0.0.1:8080/graphspaces/DEFAULT/graphs

{"graphs":["hugegraph_rocksdb","hugegraph_memory"]}
```

Inspect a graph:

```bash
curl http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph_memory

{"name":"hugegraph_memory","backend":"memory"}
```

```bash
curl http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph_rocksdb

{"name":"hugegraph_rocksdb","backend":"rocksdb"}
```
