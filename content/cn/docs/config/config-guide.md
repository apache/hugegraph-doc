---
title: "Server 启动指南"
linkTitle: "Server 启动指南"
weight: 1
---

### 1 概述

配置文件的目录为 hugegraph-release/conf，所有关于服务和图本身的配置都在此目录下。

主要的配置文件包括：gremlin-server.yaml、rest-server.properties 和 hugegraph.properties

HugeGraphServer 内部集成了 GremlinServer 和 RestServer，而 gremlin-server.yaml 和 rest-server.properties 就是用来配置这两个 Server 的。

- [GremlinServer](https://tinkerpop.apache.org/docs/3.5.1/reference/#gremlin-server)：GremlinServer 接收 Gremlin 请求并调用图引擎。
- RestServer：提供 RESTful API，根据不同的 HTTP 请求，调用对应的 Core API，如果用户请求体是 gremlin 语句，则会转发给 GremlinServer，实现对图数据的操作。

下面对这三个配置文件逐一介绍。

### 2 gremlin-server.yaml

`gremlin-server.yaml` 的主要结构如下。示例省略了部分导入项；完整内容以发布包中的文件为准。

```yaml
# host and port of gremlin server, need to be consistent with host and port in rest-server.properties
#host: 127.0.0.1
#port: 8182

# Gremlin 查询中的超时时间（以毫秒为单位）
evaluationTimeout: 30000

channelizer: org.apache.tinkerpop.gremlin.server.channel.WsAndHttpChannelizer
# 不要在此处设置图形，此功能将在支持动态添加图形后再进行处理
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

通常只需关注 `channelizer`、`host` 和 `port`。图不在 Gremlin Server 的 `graphs` 段加载；是否读取本地图配置由 `rest-server.properties` 中的 `graph.load_from_local_config` 控制。

- channelizer：默认的 `WsAndHttpChannelizer` 同时支持 WebSocket 和 HTTP。Gremlin-Console 使用 WebSocket，HugeGraph-Client、Loader 和 Hubble 使用 HTTP；

默认 GremlinServer 是服务在 localhost:8182，如果需要修改，配置 host、port 即可

- host：部署 GremlinServer 机器的机器名或 IP，目前 HugeGraphServer 不支持分布式部署，且 GremlinServer 不直接暴露给用户;
- port：部署 GremlinServer 机器的端口；

同时需要在 rest-server.properties 中增加对应的配置项 gremlinserver.url=http://host:port

### 3 rest-server.properties

下面是可用的 `rest-server.properties` 示例。当前上游发布模板没有写出 `graph.load_from_local_config`，而源码默认值为 `false`；使用 `conf/graphs` 中的本地图配置时必须显式设为 `true`。

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

- restserver.url：RestServer 提供服务的 url，根据实际环境修改。如果其他 IP 地址无法访问，可以尝试修改为特定的地址；或修改为 `http://0.0.0.0` 来监听来自任何 IP 地址的请求，这种方案较为便捷，但需要留意服务可被访问的网络范围；
- graphs：图配置文件所在目录，默认值是 `./conf/graphs`。`init-store` 会扫描该目录；Server 仅在 `graph.load_from_local_config=true` 时加载其中的 properties 文件；
- graph.load_from_local_config：是否在 Server 启动时读取本地图配置，源码默认值为 `false`；

> 当前上游模板中的 Arthas 键仍写作 `arthas.telnet_port`、`arthas.http_port` 和 `arthas.disabled_commands`，但 `ServerOptions` 读取的是下方示例中的 camelCase 名称。自定义配置应使用 `arthas.telnetPort`、`arthas.httpPort` 和 `arthas.disabledCommands`。

> 配置项 gremlinserver.url 是 GremlinServer 为 RestServer 提供服务的 url，该配置项默认为 http://localhost:8182，如需修改，需要和 gremlin-server.yaml 中的 host 和 port 相匹配；

### 4 hugegraph.properties

hugegraph.properties 是一类文件，因为如果系统存在多个图，则会有多个相似的文件。该文件用来配置与图存储和查询相关的参数，文件的默认内容如下：

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

重点关注未注释的几项：

- gremlin.graph：GremlinServer 的启动入口，用户不要修改此项；
- backend：使用的后端存储。1.7.0 支持 memory、rocksdb、hstore 和 hbase；
- serializer：schema、vertex 和 edge 写入后端时使用的序列化器。RocksDB 使用 binary；
- store：图在后端使用的存储名称；
- rocksdb.data_path：backend 为 rocksdb 时此项才有意义，rocksdb 的数据目录
- rocksdb.wal_path：backend 为 rocksdb 时此项才有意义，rocksdb 的日志目录

### 5 多图配置

一个 Server 可以加载多个图，每个图使用单独的 properties 文件。下面创建 RocksDB 图 `hugegraph_rocksdb` 和内存图 `hugegraph_memory`。

**[可选]：修改 rest-server.properties**

通过修改 `rest-server.properties` 中的 `graphs` 配置项来设置图的配置文件目录。默认配置为 `graphs=./conf/graphs`，如果想要修改为其它目录则调整 `graphs` 配置项，比如调整为 `graphs=/etc/hugegraph/graphs`，示例如下：

```properties
graphs=./conf/graphs
graph.load_from_local_config=true
```

在 `conf/graphs` 路径下基于 `hugegraph.properties` 创建 `hugegraph_memory.properties` 和 `hugegraph_rocksdb.properties`。

`hugegraph_memory.properties` 修改如下：

```properties
backend=memory
serializer=text
store=hugegraph_memory
```

`hugegraph_rocksdb.properties` 修改如下：

```properties
backend=rocksdb
serializer=binary

store=hugegraph_rocksdb
```

**停止 Server，初始化执行 init-store.sh（为新的图创建数据库），重新启动 Server**

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

查看创建的图：

```bash
curl http://127.0.0.1:8080/graphspaces/DEFAULT/graphs

{"graphs":["hugegraph_rocksdb","hugegraph_memory"]}
```

查看某个图的信息：

```bash
curl http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph_memory

{"name":"hugegraph_memory","backend":"memory"}
```

```bash
curl http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph_rocksdb

{"name":"hugegraph_rocksdb","backend":"rocksdb"}
```
