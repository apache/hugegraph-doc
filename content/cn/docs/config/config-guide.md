---
title: "Server 启动指南"
linkTitle: "Server 启动指南"
weight: 1
---

### 1 概述

配置文件的目录为 hugegraph-release/conf，所有关于服务和图本身的配置都在此目录下。

主要的配置文件包括：gremlin-server.yaml、rest-server.properties 和 hugegraph.properties

HugeGraphServer 内部集成了 GremlinServer 和 RestServer，而 gremlin-server.yaml 和 rest-server.properties 就是用来配置这两个 Server 的。

- [GremlinServer](http://tinkerpop.apache.org/docs/3.2.3/reference/#gremlin-server)：GremlinServer 接受用户的 gremlin 语句，解析后转而调用 Core 的代码。
- RestServer：提供 RESTful API，根据不同的 HTTP 请求，调用对应的 Core API，如果用户请求体是 gremlin 语句，则会转发给 GremlinServer，实现对图数据的操作。

下面对这三个配置文件逐一介绍。

### 2 gremlin-server.yaml

gremlin-server.yaml 文件默认的内容如下：

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

上面的配置项很多，但目前只需要关注如下几个配置项：channelizer 和 graphs。

- graphs：GremlinServer 启动时需要打开的图，该项是一个 map 结构，key 是图的名字，value 是该图的配置文件路径；
- channelizer：GremlinServer 与客户端有两种通信方式，分别是 WebSocket 和 HTTP（默认）。如果选择 WebSocket，
用户可以通过 [Gremlin-Console](../clients/gremlin-console) 快速体验 HugeGraph 的特性，但是不支持大规模数据导入，
推荐使用 HTTP 的通信方式，HugeGraph 的外围组件都是基于 HTTP 实现的；

默认 GremlinServer 是服务在 localhost:8182，如果需要修改，配置 host、port 即可

- host：部署 GremlinServer 机器的机器名或 IP，目前 HugeGraphServer 不支持分布式部署，且 GremlinServer 不直接暴露给用户;
- port：部署 GremlinServer 机器的端口；

同时需要在 rest-server.properties 中增加对应的配置项 gremlinserver.url=http://host:port

### 3 rest-server.properties

rest-server.properties 文件的默认内容如下：

```properties
# bind url
# could use '0.0.0.0' or specified (real)IP to expose external network access
restserver.url=http://127.0.0.1:8080
#restserver.enable_graphspaces_filter=false
# gremlin server url, need to be consistent with host and port in gremlin-server.yaml
#gremlinserver.url=http://127.0.0.1:8182

graphs=./conf/graphs

# The maximum thread ratio for batch writing, only take effect if the batch.max_write_threads is 0
batch.max_write_ratio=80
batch.max_write_threads=0

# configuration of arthas
arthas.telnet_port=8562
arthas.http_port=8561
arthas.ip=127.0.0.1
arthas.disabled_commands=jad

# authentication configs
# choose 'org.apache.hugegraph.auth.StandardAuthenticator' or a custom implementation
#auth.authenticator=

# for StandardAuthenticator mode
#auth.graph_store=hugegraph
# auth client config
#auth.remote_url=127.0.0.1:8899,127.0.0.1:8898,127.0.0.1:8897

# TODO: Deprecated & removed later (useless from version 1.5.0)
# rpc server configs for multi graph-servers or raft-servers
#rpc.server_host=127.0.0.1
#rpc.server_port=8091
#rpc.server_timeout=30

# rpc client configs (like enable to keep cache consistency)
#rpc.remote_url=127.0.0.1:8091,127.0.0.1:8092,127.0.0.1:8093
#rpc.client_connect_timeout=20
#rpc.client_reconnect_period=10
#rpc.client_read_timeout=40
#rpc.client_retries=3
#rpc.client_load_balancer=consistentHash

# raft group initial peers
#raft.group_peers=127.0.0.1:8091,127.0.0.1:8092,127.0.0.1:8093

# lightweight load balancing (beta)
server.id=server-1
server.role=master

# slow query log
log.slow_query_threshold=1000

# jvm(in-heap) memory usage monitor, set 1 to disable it
memory_monitor.threshold=0.85
memory_monitor.period=2000
```

- restserver.url：RestServer 提供服务的 url，根据实际环境修改。如果其他 IP 地址无法访问，可以尝试修改为特定的地址；或修改为 `http://0.0.0.0` 来监听来自任何 IP 地址的请求，这种方案较为便捷，但需要留意服务可被访问的网络范围；
- graphs：RestServer 启动时也需要打开图，该项为 map 结构，key 是图的名字，value 是该图的配置文件路径；

> 注意：gremlin-server.yaml 和 rest-server.properties 都包含 graphs 配置项，而 `init-store` 命令是根据 gremlin-server.yaml 的 graphs 下的图进行初始化的。

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

#vertex.default_label=vertex

backend=rocksdb
serializer=binary

store=hugegraph

raft.mode=false
raft.safe_read=false
raft.use_snapshot=false
raft.endpoint=127.0.0.1:8281
raft.group_peers=127.0.0.1:8281,127.0.0.1:8282,127.0.0.1:8283
raft.path=./raft-log
raft.use_replicator_pipeline=true
raft.election_timeout=10000
raft.snapshot_interval=3600
raft.backend_threads=48
raft.read_index_threads=8
raft.queue_size=16384
raft.queue_publish_timeout=60
raft.apply_batch=1
raft.rpc_threads=80
raft.rpc_connect_timeout=5000
raft.rpc_timeout=60000

# if use 'ikanalyzer', need download jar from 'https://github.com/apache/hugegraph-doc/raw/ik_binary/dist/server/ikanalyzer-2012_u6.jar' to lib directory
search.text_analyzer=jieba
search.text_analyzer_mode=INDEX

# rocksdb backend config
#rocksdb.data_path=/path/to/disk
#rocksdb.wal_path=/path/to/disk

# cassandra backend config
cassandra.host=localhost
cassandra.port=9042
cassandra.username=
cassandra.password=
#cassandra.connect_timeout=5
#cassandra.read_timeout=20
#cassandra.keyspace.strategy=SimpleStrategy
#cassandra.keyspace.replication=3

# hbase backend config
#hbase.hosts=localhost
#hbase.port=2181
#hbase.znode_parent=/hbase
#hbase.threads_max=64

# mysql backend config
#jdbc.driver=com.mysql.jdbc.Driver
#jdbc.url=jdbc:mysql://127.0.0.1:3306
#jdbc.username=root
#jdbc.password=
#jdbc.reconnect_max_times=3
#jdbc.reconnect_interval=3
#jdbc.ssl_mode=false

# postgresql & cockroachdb backend config
#jdbc.driver=org.postgresql.Driver
#jdbc.url=jdbc:postgresql://localhost:5432/
#jdbc.username=postgres
#jdbc.password=

# palo backend config
#palo.host=127.0.0.1
#palo.poll_interval=10
#palo.temp_dir=./palo-data
#palo.file_limit_size=32
```

重点关注未注释的几项：

- gremlin.graph：GremlinServer 的启动入口，用户不要修改此项；
- backend：使用的后端存储，可选值有 memory、cassandra、scylladb、mysql、hbase、postgresql 和 rocksdb；
- serializer：主要为内部使用，用于将 schema、vertex 和 edge 序列化到后端，对应的可选值为 text、cassandra、scylladb 和 binary；(注：rocksdb 后端值需是 binary，其他后端 backend 与 serializer 值需保持一致，如 hbase 后端该值为 hbase)
- store：图存储到后端使用的数据库名，在 cassandra 和 scylladb 中就是 keyspace 名，此项的值与 GremlinServer 和 RestServer 中的图名并无关系，但是出于直观考虑，建议仍然使用相同的名字；
- cassandra.host：backend 为 cassandra 或 scylladb 时此项才有意义，cassandra/scylladb 集群的 seeds；
- cassandra.port：backend 为 cassandra 或 scylladb 时此项才有意义，cassandra/scylladb 集群的 native port；
- rocksdb.data_path：backend 为 rocksdb 时此项才有意义，rocksdb 的数据目录
- rocksdb.wal_path：backend 为 rocksdb 时此项才有意义，rocksdb 的日志目录
- admin.token: 通过一个 token 来获取服务器的配置信息，例如：<http://localhost:8080/graphs/hugegraph/conf?token=162f7848-0b6d-4faf-b557-3a0797869c55>

### 5 多图配置

我们的系统是可以存在多个图的，并且各个图的后端可以不一样，比如图 `hugegraph_rocksdb` 和 `hugegraph_mysql`，其中 `hugegraph_rocksdb` 以 `RocksDB` 作为后端，`hugegraph_mysql` 以 `MySQL` 作为后端。

配置方法也很简单：

**[可选]：修改 rest-server.properties**

通过修改 `rest-server.properties` 中的 `graphs` 配置项来设置图的配置文件目录。默认配置为 `graphs=./conf/graphs`，如果想要修改为其它目录则调整 `graphs` 配置项，比如调整为 `graphs=/etc/hugegraph/graphs`，示例如下：

```properties
graphs=./conf/graphs
```

在 `conf/graphs` 路径下基于 `hugegraph.properties` 修改得到 `hugegraph_mysql_backend.properties` 和 `hugegraph_rocksdb_backend.properties`

`hugegraph_mysql_backend.properties` 修改的部分如下：

```properties
backend=mysql
serializer=mysql

store=hugegraph_mysql

# mysql backend config
jdbc.driver=com.mysql.cj.jdbc.Driver
jdbc.url=jdbc:mysql://127.0.0.1:3306
jdbc.username=root
jdbc.password=xxx
jdbc.reconnect_max_times=3
jdbc.reconnect_interval=3
jdbc.ssl_mode=false
```

`hugegraph_rocksdb_backend.properties` 修改的部分如下：

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
2023-06-11 14:16:14 [main] [INFO] o.a.h.c.InitStore - Init graph with config file: ./conf/graphs/hugegraph_rocksdb_backend.properties
...
2023-06-11 14:16:15 [main] [INFO] o.a.h.StandardHugeGraph - Graph 'hugegraph_rocksdb' has been initialized
2023-06-11 14:16:15 [main] [INFO] o.a.h.c.InitStore - Init graph with config file: ./conf/graphs/hugegraph_mysql_backend.properties
...
2023-06-11 14:16:16 [main] [INFO] o.a.h.StandardHugeGraph - Graph 'hugegraph_mysql' has been initialized
2023-06-11 14:16:16 [main] [INFO] o.a.h.StandardHugeGraph - Close graph standardhugegraph[hugegraph_rocksdb]
...
2023-06-11 14:16:16 [main] [INFO] o.a.h.HugeFactory - HugeFactory shutdown
2023-06-11 14:16:16 [hugegraph-shutdown] [INFO] o.a.h.HugeFactory - HugeGraph is shutting down
Initialization finished.
```

```bash
$ ./bin/start-hugegraph.sh

Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)...OK
Started [pid 21614]
```

查看创建的图：

```bash
curl http://127.0.0.1:8080/graphs/

{"graphs":["hugegraph_rocksdb","hugegraph_mysql"]}
```

查看某个图的信息：

```bash
curl http://127.0.0.1:8080/graphs/hugegraph_mysql_backend

{"name":"hugegraph_mysql","backend":"mysql"}
```

```bash
curl http://127.0.0.1:8080/graphs/hugegraph_rocksdb_backend

{"name":"hugegraph_rocksdb","backend":"rocksdb"}
```
