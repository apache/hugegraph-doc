---
title: "Server 启动指南"
linkTitle: "Server 启动指南"
weight: 1
search_keywords: [HugeGraph 配置, Server 配置, 配置指南]
search_boost: 1.6
---

### 1 概述

默认配置位于发行包解压目录的 `conf/` 下。HBase、Kerberos 和 HTTPS 等外部文件可以由用户提供到其他路径，详见对应的后端、认证和 HTTPS 页面。

主要的配置文件包括：gremlin-server.yaml、rest-server.properties 和 hugegraph.properties

HugeGraphServer 内部集成了 GremlinServer 和 RestServer，而 gremlin-server.yaml 和 rest-server.properties 就是用来配置这两个 Server 的。

- [GremlinServer](https://tinkerpop.apache.org/docs/3.5.1/reference/#gremlin-server)：GremlinServer 接收 Gremlin 请求并调用图引擎。
- RestServer：提供 RESTful API，根据不同的 HTTP 请求，调用对应的 Core API，如果用户请求体是 gremlin 语句，则会转发给 GremlinServer，实现对图数据的操作。

下面对这三个配置文件逐一介绍。

发行包把默认配置放在安装目录的 `conf/` 下；这些文件来自 Server 仓库的静态发行素材，构建时随包复制。未在配置文件中出现的选项采用代码定义的默认值；配置文件显式写入的值会覆盖该默认值。
本页的默认文件行为按固定 Server 主线 `2f827d6` 核对；实际使用的发布包应以其自身版本对应的配置文件和入口脚本为准。

| 文件 | 来源和用途 | 装载行为 |
|------|------------|----------|
| `conf/gremlin-server.yaml` | 随发行包提供；配置 Gremlin Server。 | `start-hugegraph.sh` 将它作为 Server 启动参数传入。 |
| `conf/rest-server.properties` | 按固定 Server 主线构建时随发行包提供；配置 REST Server、PD、认证等。 | 启动脚本和 Server 进程读取；对应主线构建的容器入口脚本也会在启动前更新其中受支持的选项。 |
| `conf/graphs/hugegraph.properties` | 随发行包提供的默认图配置，使用 RocksDB。 | `init-store.sh` 和 Server 应用初始化都会扫描该目录；初始化阶段会尝试加载其中的图配置。`graph.load_from_local_config` 默认 `false`，只控制管理器构造阶段预加载及 `reload()` 重扫。 |
| `conf/graphs/hstore.properties.template` | 随发行包提供的 HStore 模板；其他图配置由用户按需创建。 | HStore 镜像在构建时把模板改名为 `hugegraph.properties`；裸发行包用户可复制模板并修改。 |

完整的默认文件见固定的 Server 源码：[gremlin-server.yaml](https://github.com/apache/hugegraph/blob/2f827d6e8c9c62ae858f2fc122b3a192d015e2f4/hugegraph-server/hugegraph-dist/src/assembly/static/conf/gremlin-server.yaml)、[rest-server.properties](https://github.com/apache/hugegraph/blob/2f827d6e8c9c62ae858f2fc122b3a192d015e2f4/hugegraph-server/hugegraph-dist/src/assembly/static/conf/rest-server.properties)、[hugegraph.properties](https://github.com/apache/hugegraph/blob/2f827d6e8c9c62ae858f2fc122b3a192d015e2f4/hugegraph-server/hugegraph-dist/src/assembly/static/conf/graphs/hugegraph.properties) 和 [hstore.properties.template](https://github.com/apache/hugegraph/blob/2f827d6e8c9c62ae858f2fc122b3a192d015e2f4/hugegraph-server/hugegraph-dist/src/assembly/static/conf/graphs/hstore.properties.template)。

以下 Docker 环境变量行为仅适用于从固定主线 `2f827d6` 构建的镜像，不会把任意环境变量名转换为配置项。该版本的入口脚本在初始化和启动前处理 `HG_SERVER_BACKEND`、`HG_SERVER_PD_PEERS`、`HG_SERVER_USE_PD`、`HG_SERVER_CLUSTER`、`HG_SERVER_REST_URL`、`HG_SERVER_MIN_FREE_MEMORY`、`HG_SERVER_AUTH_TOKEN_SECRET`、`HG_SERVER_INIT_STORE_ENABLED` 和 `PASSWORD`；历史发布镜像需按各自 tag 对应的 entrypoint 核实支持项。见 [Docker entrypoint](https://github.com/apache/hugegraph/blob/2f827d6e8c9c62ae858f2fc122b3a192d015e2f4/hugegraph-server/hugegraph-dist/docker/docker-entrypoint.sh)。

### 2 gremlin-server.yaml

只展示启动时常调整的选项；完整文件及序列化器、插件配置见上方源码链接。

发行包中的 `host` 和 `port` 默认行是注释；未指定时使用 `127.0.0.1:8182`。若要修改监听地址，取消注释并设置这两项：

```yaml
#host: 127.0.0.1
#port: 8182
evaluationTimeout: 30000
channelizer: org.apache.tinkerpop.gremlin.server.channel.WsAndHttpChannelizer
graphs: {}
ssl: { enabled: false }
```

通常只需关注 `channelizer`、`host` 和 `port`。图不在 Gremlin Server 的 `graphs` 段加载；REST 侧管理器会在 Server 应用初始化时扫描 `graphs` 目录并尝试载入本地图配置。`graph.load_from_local_config` 只控制管理器构造阶段的预加载与 `reload()` 重扫；默认 `false` 不会关闭应用初始化阶段的本地加载。

- channelizer：默认的 `WsAndHttpChannelizer` 同时支持 WebSocket 和 HTTP。Gremlin-Console 使用 WebSocket，HugeGraph-Client、Loader 和 Hubble 使用 HTTP；

默认 GremlinServer 是服务在 127.0.0.1:8182，如果需要修改，配置 host、port 即可

- host：部署 GremlinServer 机器的机器名或 IP，GremlinServer 不直接暴露给用户，由 RestServer 转发 Gremlin 请求;
- port：部署 GremlinServer 机器的端口；

同时需要在 rest-server.properties 中增加对应的配置项 gremlinserver.url=http://host:port

### 3 rest-server.properties

下面是可用的 `rest-server.properties` 示例。固定主线模板未写出 `graph.load_from_local_config`，源码默认值为 `false`。示例中设为 `true` 是可选的：它开启管理器构造阶段预加载和 `reload()` 重扫；Server 应用初始化阶段仍会扫描并尝试加载本地图配置。

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

- restserver.url：RestServer 提供服务的 url，根据实际环境修改。如果其他 IP 地址无法访问，可以尝试修改为特定的地址；或修改为 `http://0.0.0.0` 来监听来自任何 IP 地址的请求，这种方案较为便捷，但需要留意服务可被访问的网络范围；
- graphs：图配置文件所在目录，默认值是 `./conf/graphs`。`init-store.sh` 会扫描该目录；Server 应用初始化也会扫描并尝试加载其中的 properties 文件；
- graph.load_from_local_config：是否在管理器构造阶段预加载本地图配置，以及在 `reload()` 时重新扫描；源码默认值为 `false`。它不会禁止 Server 应用初始化阶段的本地加载，也不是安全隔离开关；

> 当前上游模板中的 Arthas 键仍写作 `arthas.telnet_port`、`arthas.http_port` 和 `arthas.disabled_commands`，但 `ServerOptions` 读取的是下方示例中的 camelCase 名称。自定义配置应使用 `arthas.telnetPort`、`arthas.httpPort` 和 `arthas.disabledCommands`。

> 配置项 gremlinserver.url 是 GremlinServer 为 RestServer 提供服务的 url，该配置项默认为 http://127.0.0.1:8182，如需修改，需要和 gremlin-server.yaml 中的 host 和 port 相匹配；该值可以像模板那样省略协议前缀，缺失时会自动补上 `http://`。

### 4 hugegraph.properties

hugegraph.properties 是随发行包提供的默认图配置；每个额外的图都应在 `conf/graphs` 下提供自己的 properties 文件。这里展示选择默认 RocksDB 后端所需的关键配置，完整文件见上方源码链接。

```properties
gremlin.graph=org.apache.hugegraph.HugeFactory
backend=rocksdb
serializer=binary
store=hugegraph
```

重点关注未注释的几项：

- gremlin.graph：GremlinServer 的启动入口，用户不要修改此项；开启鉴权时才改为 `org.apache.hugegraph.auth.HugeFactoryAuthProxy`；
- vertex.cache_type / edge.cache_type：缓存实现，可选值为 `l1` 和 `l2`，默认 `l2`；
- backend：使用的后端存储。1.7.0 支持 memory、rocksdb、hstore 和 hbase；
- serializer：schema、vertex 和 edge 写入后端时使用的序列化器。RocksDB 使用 binary；
- store：图在后端使用的存储名称；
- task.schedule_period、task.retry、task.wait_timeout：异步任务的调度周期（秒）、重试次数和等待超时（秒）。调度器由后端决定，`hstore` 使用分布式调度器，其余后端使用本地调度器；旧的 `task.scheduler_type` 键已被忽略；
- search.text_analyzer / search.text_analyzer_mode：全文索引使用的分词器及其模式。可选分词器为 `ansj`、`hanlp`、`smartcn`、`jieba`、`jcseg`、`mmseg4j` 和 `ikanalyzer`，每种分词器有各自的模式取值；
- rocksdb.data_path：backend 为 rocksdb 时此项才有意义，rocksdb 的数据目录，默认为 `rocksdb-data/data`
- rocksdb.wal_path：backend 为 rocksdb 时此项才有意义，rocksdb 的日志目录，默认为 `rocksdb-data/wal`

### 5 多图配置

一个 Server 可以加载多个图，每个图使用单独的 properties 文件。下面创建 RocksDB 图 `hugegraph_rocksdb` 和内存图 `hugegraph_memory`。

**[可选]：修改 rest-server.properties**

通过修改 `rest-server.properties` 中的 `graphs` 配置项来设置图的配置文件目录。默认配置为 `graphs=./conf/graphs`；需要其他目录时调整 `graphs`。下面将 `graph.load_from_local_config` 设为 `true`，作为管理器构造阶段预加载和 `reload()` 重扫的可选设置；应用初始化仍会读取该目录中的本地图配置：

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

Starting HugeGraphServer in daemon mode...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)...OK
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
