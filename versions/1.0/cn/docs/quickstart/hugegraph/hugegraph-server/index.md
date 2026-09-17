# HugeGraph-Server Quick Start

LLMS 索引： [llms.txt](/versions/1.0/cn/llms.txt)

---

## 1 HugeGraph-Server概述

HugeGraph-Server 是 HugeGraph 项目的核心部分，包含Core、Backend、API等子模块。

Core模块是Tinkerpop接口的实现，Backend模块用于管理数据存储，目前支持的后端包括：Memory、Cassandra、ScyllaDB以及RocksDB，API模块提供HTTP Server，将Client的HTTP请求转化为对Core的调用。

> 文档中会大量出现`HugeGraph-Server`及`HugeGraphServer`这两种写法，其他组件也类似。这两种写法含义上并无大的差异，可以这么区分：`HugeGraph-Server`表示服务端相关组件代码，`HugeGraphServer`表示服务进程。

## 2 依赖

### 2.1 安装JDK-1.8

HugeGraph-Server 基于jdk-1.8开发，代码用到了较多jdk-1.8中的类和方法，请用户自行安装配置。

**在往下阅读之前务必执行`java -version`命令查看jdk版本**

```bash
java -version
```

### 2.2 安装GCC-4.3.0(GLIBCXX_3.4.10)或更新版本（可选）

如果使用的是RocksDB后端，请务必执行`gcc --version`命令查看gcc版本；若使用其他后端，则不需要。

```bash
gcc --version
```

## 3 部署

有三种方式可以部署HugeGraph-Server组件：

- 方式1：一键部署
- 方式2：下载tar包
- 方式3：源码编译

### 3.1 一键部署

HugeGraph-Tools提供了一键部署的命令行工具，用户可以使用该工具快速地一键下载、解压、配置并启动HugeGraphServer和HugeGraphStudio。
当然，还是得先下载HugeGraph-Tools的tar包。

```bash
wget https://github.com/hugegraph/hugegraph-tools/releases/download/v${version}/hugegraph-tools-${version}.tar.gz
tar -zxvf hugegraph-tools-${version}.tar.gz
cd hugegraph-tools-${version}
```

> 注：${version}为版本号，最新版本号可参考[Download页面](/versions/1.0/docs/download/download)，或直接从Download页面点击链接下载

HugeGraph-Tools 的总入口脚本是`bin/hugegraph`，用户可以使用`help`子命令查看其用法，这里只介绍一键部署的命令。

```bash
bin/hugegraph deploy -v {hugegraph-version} -p {install-path} [-u {download-path-prefix}]
```

`{hugegraph-version}`表示要部署的HugeGraphServer及HugeGraphStudio的版本，用户可查看`conf/version-mapping.yaml`文件获取版本信息，`{install-path}`指定HugeGraphServer及HugeGraphStudio的安装目录，`{download-path-prefix}`可选，指定HugeGraphServer及HugeGraphStudio tar包的下载地址，不提供时使用默认下载地址，比如要启动 0.6 版本的HugeGraph-Server及HugeGraphStudio将上述命令写为`bin/hugegraph deploy -v 0.6 -p services`即可。

### 3.2 下载tar包

```bash
wget https://github.com/hugegraph/hugegraph/releases/download/v${version}/hugegraph-${version}.tar.gz
tar -zxvf hugegraph-${version}.tar.gz
```

### 3.3 源码编译

下载HugeGraph源代码

```bash
git clone https://github.com/hugegraph/hugegraph.git
```

编译打包生成tar包

```bash
cd hugegraph
mvn package -DskipTests
```

执行日志如下：

```bash
......
[INFO] Reactor Summary:
[INFO] 
[INFO] hugegraph .......................................... SUCCESS [  0.003 s]
[INFO] hugegraph-core ..................................... SUCCESS [ 15.335 s]
[INFO] hugegraph-api ...................................... SUCCESS [  0.829 s]
[INFO] hugegraph-cassandra ................................ SUCCESS [  1.095 s]
[INFO] hugegraph-scylladb ................................. SUCCESS [  0.313 s]
[INFO] hugegraph-rocksdb .................................. SUCCESS [  0.506 s]
[INFO] hugegraph-mysql .................................... SUCCESS [  0.412 s]
[INFO] hugegraph-palo ..................................... SUCCESS [  0.359 s]
[INFO] hugegraph-dist ..................................... SUCCESS [  7.470 s]
[INFO] hugegraph-example .................................. SUCCESS [  0.403 s]
[INFO] hugegraph-test ..................................... SUCCESS [  1.509 s]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
......
```

执行成功后，在hugegraph目录下生成 hugegraph-*.tar.gz 文件，就是编译生成的tar包。

## 4 配置

如果需要快速启动HugeGraph仅用于测试，那么只需要进行少数几个配置项的修改即可（见下一节）。
详细的配置介绍请参考[配置文档](/versions/1.0/docs/config/config-guide)及[配置项介绍](/versions/1.0/docs/config/config-option)

## 5 启动

启动分为"首次启动"和"非首次启动"，这么区分是因为在第一次启动前需要初始化后端数据库，然后启动服务。
而在人为停掉服务后，或者其他原因需要再次启动服务时，因为后端数据库是持久化存在的，直接启动服务即可。

HugeGraphServer启动时会连接后端存储并尝试检查后端存储版本号，如果未初始化后端或者后端已初始化但版本不匹配时（旧版本数据），HugeGraphServer会启动失败，并给出错误信息。

如果需要外部访问HugeGraphServer，请修改`rest-server.properties`的`restserver.url`配置项
（默认为`http://127.0.0.1:8080`），修改成机器名或IP地址。

由于各种后端所需的配置（hugegraph.properties）及启动步骤略有不同，下面逐一对各后端的配置及启动做介绍。

### 5.1 Memory

修改 hugegraph.properties

```properties
backend=memory
serializer=text
```

> Memory后端的数据是保存在内存中无法持久化的，不需要初始化后端，这也是唯一一个不需要初始化的后端。

启动 server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

提示的 url 与 rest-server.properties 中配置的 restserver.url 一致

### 5.2 RocksDB

> RocksDB是一个嵌入式的数据库，不需要手动安装部署, 要求 GCC 版本 >= 4.3.0（GLIBCXX_3.4.10），如不满足，需要提前升级 GCC

修改 hugegraph.properties

```properties
backend=rocksdb
serializer=binary
rocksdb.data_path=.
rocksdb.wal_path=.
```

初始化数据库（仅第一次启动时需要）

```bash
cd hugegraph-${version}
bin/init-store.sh
```

启动server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

### 5.3 Cassandra

> 用户需自行安装 Cassandra，要求版本 3.0 以上，[下载地址](http://cassandra.apache.org/download/)

修改 hugegraph.properties

```properties
backend=cassandra
serializer=cassandra

# cassandra backend config
cassandra.host=localhost
cassandra.port=9042
cassandra.username=
cassandra.password=
#cassandra.connect_timeout=5
#cassandra.read_timeout=20

#cassandra.keyspace.strategy=SimpleStrategy
#cassandra.keyspace.replication=3
```

初始化数据库（仅第一次启动时需要）

```bash
cd hugegraph-${version}
bin/init-store.sh
Initing HugeGraph Store...
2017-12-01 11:26:51 1424  [main] [INFO ] com.baidu.hugegraph.HugeGraph [] - Opening backend store: 'cassandra'
2017-12-01 11:26:52 2389  [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph, try init keyspace later
2017-12-01 11:26:52 2472  [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph, try init keyspace later
2017-12-01 11:26:52 2557  [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph, try init keyspace later
2017-12-01 11:26:53 2797  [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_graph
2017-12-01 11:26:53 2945  [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_schema
2017-12-01 11:26:53 3044  [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_index
2017-12-01 11:26:53 3046  [pool-3-thread-1] [INFO ] com.baidu.hugegraph.backend.Transaction [] - Clear cache on event 'store.init'
2017-12-01 11:26:59 9720  [main] [INFO ] com.baidu.hugegraph.HugeGraph [] - Opening backend store: 'cassandra'
2017-12-01 11:27:00 9805  [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph1, try init keyspace later
2017-12-01 11:27:00 9886  [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph1, try init keyspace later
2017-12-01 11:27:00 9955  [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph1, try init keyspace later
2017-12-01 11:27:00 10175 [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_graph
2017-12-01 11:27:00 10321 [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_schema
2017-12-01 11:27:00 10413 [main] [INFO ] com.baidu.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_index
2017-12-01 11:27:00 10413 [pool-3-thread-1] [INFO ] com.baidu.hugegraph.backend.Transaction [] - Clear cache on event 'store.init'
```

启动server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

### 5.4 ScyllaDB

> 用户需自行安装 ScyllaDB，推荐版本 2.1 以上，[下载地址](https://docs.scylladb.com/getting-started/)

修改 hugegraph.properties

```properties
backend=scylladb
serializer=scylladb

# cassandra backend config
cassandra.host=localhost
cassandra.port=9042
cassandra.username=
cassandra.password=
#cassandra.connect_timeout=5
#cassandra.read_timeout=20

#cassandra.keyspace.strategy=SimpleStrategy
#cassandra.keyspace.replication=3
```

由于 scylladb 数据库本身就是基于 cassandra 的"优化版"，如果用户未安装 scylladb ，也可以直接使用 cassandra 作为后端存储，只需要把 backend 和 serializer 修改为 scylladb，host 和 post 指向 cassandra 集群的 seeds 和 port 即可，但是并不建议这样做，这样发挥不出 scylladb 本身的优势了。

初始化数据库（仅第一次启动时需要）

```bash
cd hugegraph-${version}
bin/init-store.sh
```

启动server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

### 5.5 HBase

> 用户需自行安装 HBase，要求版本 2.0 以上，[下载地址](https://hbase.apache.org/downloads.html)

修改 hugegraph.properties

```properties
backend=hbase
serializer=hbase

# hbase backend config
hbase.hosts=localhost
hbase.port=2181
# Note: recommend to modify the HBase partition number by the actual/env data amount & RS amount before init store
# it may influence the loading speed a lot
#hbase.enable_partition=true
#hbase.vertex_partitions=10
#hbase.edge_partitions=30
```

初始化数据库（仅第一次启动时需要）

```bash
cd hugegraph-${version}
bin/init-store.sh
```

启动server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

> 更多其它后端配置可参考[配置项介绍](/versions/1.0/docs/config/config-option)

## 6 访问Server

### 6.1 服务启动状态校验

`jps`查看服务进程

```bash
jps
6475 HugeGraphServer
```

`curl`请求`RESTfulAPI`

```bash
echo `curl -o /dev/null -s -w %{http_code} "http://localhost:8080/graphs/hugegraph/graph/vertices"`
```

返回结果200，代表server启动正常

### 6.2 请求Server

HugeGraphServer的RESTful API包括多种类型的资源，典型的包括graph、schema、gremlin、traverser和task，

- `graph`包含`vertices`、`edges`
- `schema` 包含`vertexlabels`、 `propertykeys`、 `edgelabels`、`indexlabels`
- `gremlin`包含各种`Gremlin`语句，如`g.v()`，可以同步或者异步执行
- `traverser`包含各种高级查询，包括最短路径、交叉点、N步可达邻居等
- `task`包含异步任务的查询和删除

#### 6.2.1 获取`hugegraph`的顶点及相关属性

```bash
curl http://localhost:8080/graphs/hugegraph/graph/vertices 
```

_说明_

1. 由于图的点和边很多，对于 list 型的请求，比如获取所有顶点，获取所有边等，Server 会将数据压缩再返回，
所以使用 curl 时得到一堆乱码，可以重定向至 `gunzip` 进行解压。推荐使用 Chrome 浏览器 + Restlet 插件发送 HTTP 请求进行测试。

    ```
    curl "http://localhost:8080/graphs/hugegraph/graph/vertices" | gunzip
    ```

2. 当前HugeGraphServer的默认配置只能是本机访问，可以修改配置，使其能在其他机器访问。

    ```
    vim conf/rest-server.properties
    
    restserver.url=http://0.0.0.0:8080
    ```

响应体如下：

```json
{
    "vertices": [
        {
            "id": "2lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "price": [
                    {
                        "id": "price",
                        "value": 328
                    }
                ],
                "name": [
                    {
                        "id": "name",
                        "value": "lop"
                    }
                ],
                "lang": [
                    {
                        "id": "lang",
                        "value": "java"
                    }
                ]
            }
        },
        {
            "id": "1josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": [
                    {
                        "id": "name",
                        "value": "josh"
                    }
                ],
                "age": [
                    {
                        "id": "age",
                        "value": 32
                    }
                ]
            }
        },
        ...
    ]
}
```

详细的API请参考[RESTful-API](/versions/1.0/cn/docs/clients/restful-api/)文档

## 7 停止Server

```bash
$cd hugegraph-${version}
$bin/stop-hugegraph.sh
```
