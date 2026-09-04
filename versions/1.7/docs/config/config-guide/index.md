# Server Startup Guide

LLMS index: [llms.txt](/versions/1.7/llms.txt)

---

### 1 Overview

The directory for the configuration files is `hugegraph-release/conf`, and all the configurations related to the service and the graph itself are located in this directory.

The main configuration files include `gremlin-server.yaml`, `rest-server.properties`, and `hugegraph.properties`.

The `HugeGraphServer` integrates the `GremlinServer` and `RestServer` internally, and `gremlin-server.yaml` and `rest-server.properties` are used to configure these two servers.

- [GremlinServer](https://tinkerpop.apache.org/docs/3.5.1/reference/#gremlin-server): GremlinServer accepts Gremlin requests and invokes the graph engine.
- RestServer: It provides a RESTful API that, based on different HTTP requests, calls the corresponding Core API. If the user's request body is a Gremlin statement, it will be forwarded to GremlinServer to perform operations on the graph data.

Now let's introduce these three configuration files one by one.

### 2. gremlin-server.yaml

The main structure of `gremlin-server.yaml` is shown below. Some imports are omitted from this example; refer to the file included in the release package for the complete content.

```yaml
# host and port of gremlin server, need to be consistent with host and port in rest-server.properties
#host: 127.0.0.1
#port: 8182

# timeout in ms of gremlin query
evaluationTimeout: 30000

channelizer: org.apache.tinkerpop.gremlin.server.channel.WsAndHttpChannelizer
# don't set graph at here, this happens after support for dynamically adding graph
graphs: {
}
scriptEngines: {
  gremlin-groovy: {
    staticImports: [
      org.opencypher.gremlin.process.traversal.CustomPredicates.*',
      org.opencypher.gremlin.traversal.CustomFunctions.*
    ],
    plugins: {
      org.apache.hugegraph.plugin.HugeGraphGremlinPlugin: {},
      org.apache.tinkerpop.gremlin.server.jsr223.GremlinServerGremlinPlugin: {},
      org.apache.tinkerpop.gremlin.jsr223.ImportGremlinPlugin: {
        classImports: [
          java.lang.Math,
          org.apache.hugegraph.backend.id.IdGenerator,
          org.apache.hugegraph.type.define.Directions,
          org.apache.hugegraph.type.define.NodeRole,
          org.apache.hugegraph.traversal.algorithm.CollectionPathsTraverser,
          org.apache.hugegraph.traversal.algorithm.CountTraverser,
          org.apache.hugegraph.traversal.algorithm.CustomizedCrosspointsTraverser,
          org.apache.hugegraph.traversal.algorithm.CustomizePathsTraverser,
          org.apache.hugegraph.traversal.algorithm.FusiformSimilarityTraverser,
          org.apache.hugegraph.traversal.algorithm.HugeTraverser,
          org.apache.hugegraph.traversal.algorithm.JaccardSimilarTraverser,
          org.apache.hugegraph.traversal.algorithm.KneighborTraverser,
          org.apache.hugegraph.traversal.algorithm.KoutTraverser,
          org.apache.hugegraph.traversal.algorithm.MultiNodeShortestPathTraverser,
          org.apache.hugegraph.traversal.algorithm.NeighborRankTraverser,
          org.apache.hugegraph.traversal.algorithm.PathsTraverser,
          org.apache.hugegraph.traversal.algorithm.PersonalRankTraverser,
          org.apache.hugegraph.traversal.algorithm.SameNeighborTraverser,
          org.apache.hugegraph.traversal.algorithm.ShortestPathTraverser,
          org.apache.hugegraph.traversal.algorithm.SingleSourceShortestPathTraverser,
          org.apache.hugegraph.traversal.algorithm.SubGraphTraverser,
          org.apache.hugegraph.traversal.algorithm.TemplatePathsTraverser,
          org.apache.hugegraph.traversal.algorithm.steps.EdgeStep,
          org.apache.hugegraph.traversal.algorithm.steps.RepeatEdgeStep,
          org.apache.hugegraph.traversal.algorithm.steps.WeightedEdgeStep,
          org.apache.hugegraph.traversal.optimize.ConditionP,
          org.apache.hugegraph.traversal.optimize.Text,
          org.apache.hugegraph.traversal.optimize.TraversalUtil,
          org.apache.hugegraph.util.DateUtil,
          org.opencypher.gremlin.traversal.CustomFunctions,
          org.opencypher.gremlin.traversal.CustomPredicate
        ],
        methodImports: [
          java.lang.Math#*,
          org.opencypher.gremlin.traversal.CustomPredicate#*,
          org.opencypher.gremlin.traversal.CustomFunctions#*
        ]
      },
      org.apache.tinkerpop.gremlin.jsr223.ScriptFileGremlinPlugin: {
        files: [scripts/empty-sample.groovy]
      }
    }
  }
}
serializers:
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphBinaryMessageSerializerV1,
      config: {
        serializeResultToString: false,
        ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]
      }
  }
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphSONMessageSerializerV1d0,
      config: {
        serializeResultToString: false,
        ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]
      }
  }
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphSONMessageSerializerV2d0,
      config: {
        serializeResultToString: false,
        ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]
      }
  }
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphSONMessageSerializerV3d0,
      config: {
        serializeResultToString: false,
        ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]
      }
  }
metrics: {
  consoleReporter: {enabled: false, interval: 180000},
  csvReporter: {enabled: false, interval: 180000, fileName: ./metrics/gremlin-server-metrics.csv},
  jmxReporter: {enabled: false},
  slf4jReporter: {enabled: false, interval: 180000},
  gangliaReporter: {enabled: false, interval: 180000, addressingMode: MULTICAST},
  graphiteReporter: {enabled: false, interval: 180000}
}
maxInitialLineLength: 4096
maxHeaderSize: 8192
maxChunkSize: 8192
maxContentLength: 65536
maxAccumulationBufferComponents: 1024
resultIterationBatchSize: 64
writeBufferLowWaterMark: 32768
writeBufferHighWaterMark: 65536
ssl: {
  enabled: false
}
```

In most cases, you only need to pay attention to `channelizer`, `host`, and `port`. Graphs are not loaded from the Gremlin Server `graphs` section. Whether local graph configurations are loaded is controlled by `graph.load_from_local_config` in `rest-server.properties`.

- `channelizer`: The default `WsAndHttpChannelizer` supports both WebSocket and HTTP. Gremlin Console uses WebSocket, while HugeGraph Client, Loader, and Hubble use HTTP.

By default, the GremlinServer serves at `localhost:8182`. If you need to modify it, configure the `host` and `port` settings.

- `host`: The hostname or IP address of the machine where the GremlinServer is deployed. Currently, HugeGraphServer does not support distributed deployment, and GremlinServer is not directly exposed to users.
- `port`: The port number of the machine where the GremlinServer is deployed.

Additionally, you need to add the corresponding configuration `gremlinserver.url=http://host:port` in `rest-server.properties`.

### 3. rest-server.properties

The following is an example of the available `rest-server.properties` options. The current upstream release template does not include `graph.load_from_local_config`, whose source-code default is `false`; set it explicitly to `true` when using local graph configurations under `conf/graphs`.

```properties
# bind url
# could use '0.0.0.0' or specified (real)IP to expose external network access
restserver.url=http://127.0.0.1:8080
#restserver.enable_graphspaces_filter=false
# gremlin server url, need to be consistent with host and port in gremlin-server.yaml
#gremlinserver.url=http://127.0.0.1:8182

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

- `restserver.url`: The URL at which the RestServer provides its services. Modify it according to the actual environment. If you can't connet to server from other IP address, try to modify it as specific IP; or modify it as `http://0.0.0.0` to listen all network interfaces as a convenient solution, but need to take care of the network area that might access.
- `graphs`: The directory containing graph configuration files. The default is `./conf/graphs`. `init-store` scans this directory; the Server loads its properties files only when `graph.load_from_local_config=true`.
- `graph.load_from_local_config`: Whether the Server reads local graph configurations at startup. Its default value in the source code is `false`.

> The current upstream template still uses `arthas.telnet_port`, `arthas.http_port`, and `arthas.disabled_commands`, but `ServerOptions` reads the camelCase names shown in the example above. Custom configurations should use `arthas.telnetPort`, `arthas.httpPort`, and `arthas.disabledCommands`.

> The `gremlinserver.url` configuration option is the URL at which the GremlinServer provides services to the RestServer. By default, it is set to `http://localhost:8182`. If you need to modify it, it should match the `host` and `port` settings in `gremlin-server.yaml`.

### 4. hugegraph.properties

`hugegraph.properties` is a type of file. If the system has multiple graphs, there will be multiple similar files. This file is used to configure parameters related to graph storage and querying. The default content of the file is as follows:

```properties
# gremlin entrence to create graph
gremlin.graph=org.apache.hugegraph.HugeFactory

# cache config
#schema.cache_capacity=100000
# vertex-cache default is 1000w, 10min expired
#vertex.cache_capacity=10000000
#vertex.cache_expire=600
# edge-cache default is 100w, 10min expired
#edge.cache_capacity=1000000
#edge.cache_expire=600

# schema illegal name template
#schema.illegal_name_regex=\s+|~.*

# NOTE: since 1.7.0, only hstore, rocksdb, hbase, memory are supported for backend.
# if you want to use Cassandra/MySql/PG... as backend, please use version < 1.7.0
backend=rocksdb
serializer=binary

store=hugegraph

# pd config
#pd.peers=127.0.0.1:8686

# task config
task.schedule_period=10
task.retry=0
task.wait_timeout=10

# if use 'ikanalyzer', need download jar from 'https://github.com/apache/hugegraph-doc/raw/ik_binary/dist/server/ikanalyzer-2012_u6.jar' to lib directory
search.text_analyzer=jieba
search.text_analyzer_mode=INDEX

# rocksdb backend config
#rocksdb.data_path=/path/to/disk
#rocksdb.wal_path=/path/to/disk

# hbase backend config
#hbase.hosts=localhost
#hbase.port=2181
#hbase.znode_parent=/hbase
#hbase.threads_max=64
```

Pay attention to the following uncommented items:

- `gremlin.graph`: The entry point for GremlinServer startup. Users should not modify this item.
- `backend`: The storage backend. Version 1.7.0 supports `memory`, `rocksdb`, `hstore`, and `hbase`.
- `serializer`: The serializer used when writing schemas, vertices, and edges to the backend. RocksDB uses `binary`.
- `store`: The storage name used by the graph in the backend.
- `rocksdb.data_path`: This item is only meaningful when the backend is set to `rocksdb`. It specifies the data directory for RocksDB.
- `rocksdb.wal_path`: This item is only meaningful when the backend is set to `rocksdb`. It specifies the log directory for RocksDB.

### 5. Multi-Graph Configuration

A Server can load multiple graphs, with a separate properties file for each graph. The following example creates a RocksDB graph named `hugegraph_rocksdb` and an in-memory graph named `hugegraph_memory`.

**[Optional]: Modify `rest-server.properties`**

You can modify the graph profile directory in the `graphs` option of `rest-server.properties`. The default configuration is `graphs=./conf/graphs`, if you want to change it to another directory then adjust the `graphs` option, e.g. adjust it to `graphs=/etc/hugegraph/graphs`, example is as follows:

```properties
graphs=./conf/graphs
graph.load_from_local_config=true
```

Under `conf/graphs`, create `hugegraph_memory.properties` and `hugegraph_rocksdb.properties` based on `hugegraph.properties`.

Configure `hugegraph_memory.properties` as follows:

```properties
backend=memory
serializer=text
store=hugegraph_memory
```

Configure `hugegraph_rocksdb.properties` as follows:

```properties
backend=rocksdb
serializer=binary

store=hugegraph_rocksdb
```

**Stop the server, execute `init-store.sh` (to create a new database for the new graph), and restart the server.**

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

Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphspaces/DEFAULT/graphs)...OK
Started [pid 21614]
```

Check out created graphs:

```bash
curl http://127.0.0.1:8080/graphspaces/DEFAULT/graphs

{"graphs":["hugegraph_rocksdb","hugegraph_memory"]}
```

Get details of a graph:

```bash
curl http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph_memory

{"name":"hugegraph_memory","backend":"memory"}
```

```bash
curl http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph_rocksdb

{"name":"hugegraph_rocksdb","backend":"rocksdb"}
```
