---
title: "HugeGraph-Server Quick Start"
linkTitle: "安装/构建 HugeGraph-Server"
weight: 1
---

### 1 HugeGraph-Server 概述

HugeGraph-Server 是 HugeGraph 项目的核心部分，包含 graph-core、backend、API 等子模块。

Core 模块是 Tinkerpop 接口的实现，Backend 模块用于管理数据存储，1.7.0+ 版本支持的后端包括：RocksDB（单机默认）、HStore（分布式）、HBase 和 Memory。API 模块提供 HTTP Server，将 Client 的 HTTP 请求转化为对 Core 的调用。

> ⚠️ **重要变更**: 从 1.7.0 版本开始，MySQL、PostgreSQL、Cassandra、ScyllaDB 等遗留后端已被移除。如需使用这些后端，请使用 1.5.x 或更早版本。

> 文档中会出现 `HugeGraph-Server` 与 `HugeGraphServer` 两种写法，其他组件也类似。
> 两者在含义上并无明显差异，可简单区分为：`HugeGraph-Server` 表示服务端相关组件代码，`HugeGraphServer` 表示服务进程。

### 2 依赖

#### 2.1 安装 Java 11 (JDK 11)

建议在 Java 11 环境中运行 `HugeGraph-Server`（1.5.0 之前的版本仍保留对 Java 8 的基本兼容）。

**在继续阅读前，请先执行 `java -version` 命令确认 JDK 版本。**

> 注：使用 Java 8 启动 HugeGraph-Server 会失去部分**安全性**保障，也会影响性能表现。请尽早升级或迁移，1.7.0 起已不再支持 Java 8。

### 3 部署

有四种方式可以部署 HugeGraph-Server 组件：

- 方式 1：使用 Docker 容器 (便于**测试**)
- 方式 2：下载 tar 包
- 方式 3：源码编译
- 方式 4：使用 tools 工具部署 (Outdated)

> ⚠️ **SEC 提醒**：由于图查询语言 (如 Gremlin/Cypher) 的高度灵活性，直接暴露原生查询接口会带来潜在的安全隐患，因此**请避免直接在公网环境中暴露任何查询相关接口**。生产环境中务必开启 **[鉴权体系 (Auth)](/cn/docs/config/config-authentication/)** 配合 **IP 白名单** 构成双重保障机制，同时建议辅以 Audit Log (审计日志) 追踪具体查询语句。推荐整体采用 **[容器化环境 (Docker/K8s)](#31-使用-docker-容器-便于测试)** 进行部署以获得更好的系统级安全隔离。

#### 3.1 使用 Docker 容器 (便于**测试**)
<!-- 3.1 is linked by another place. if change 3.1's title, please check -->

可参考 [Docker 部署方式](https://github.com/apache/hugegraph/blob/master/docker/README.md)。

可以使用 `docker run -itd --name=server -p 8080:8080 -e PASSWORD=xxx hugegraph/hugegraph:1.7.0` 快速启动一个内置 `RocksDB` 后端的 `HugeGraph-Server` 实例。

可选项：

1. 可以使用 `docker exec -it server bash` 进入容器执行运维或调试操作。
2. 可以使用 `docker run -itd --name=server -p 8080:8080 -e PRELOAD="true" hugegraph/hugegraph:1.7.0` 在启动时预加载一个**内置**样例图。可通过 `RESTful API` 进行验证，具体步骤可参考 [5.1.8](#518-%E5%90%AF%E5%8A%A8-server-%E7%9A%84%E6%97%B6%E5%80%99%E5%88%9B%E5%BB%BA%E7%A4%BA%E4%BE%8B%E5%9B%BE)。
3. 可以使用 `-e PASSWORD=xxx` 开启鉴权模式并设置 admin 密码，具体步骤可参考 [Config Authentication](/cn/docs/config/config-authentication#使用-docker-时开启鉴权模式)。

如果使用 Docker Desktop，则可以按如下方式设置相关选项：
<div style="text-align: center;">
    <img src="/docs/images/images-server/31docker-option.jpg" alt="image" style="width:33%;">
</div>


> **注意**：Docker Compose 文件使用桥接网络（`hg-net`），适用于 Linux 和 Mac（Docker Desktop）。如需运行 3 节点分布式集群，请为 Docker Desktop 分配至少 **12 GB** 内存（设置 → 资源 → 内存）。Linux 上 Docker 直接使用宿主机内存。

如果希望通过一个配置文件统一管理 HugeGraph 的多个服务实例，则可以使用 `docker compose`。
[`docker/`](https://github.com/apache/hugegraph/tree/master/docker) 目录下提供了两个 compose 文件：

- **单节点快速启动**（预构建镜像）：`docker/docker-compose.yml`
- **单节点开发构建**（从源码构建）：`docker/docker-compose.dev.yml`

```bash
cd hugegraph/docker
# 注意版本号请随时保持更新 → 1.x.0
HUGEGRAPH_VERSION=1.7.0 docker compose up -d
```

如需开启鉴权，可在 compose 文件的环境变量中添加 `PASSWORD=xxx`，或在 `docker run` 命令中传入 `-e PASSWORD=xxx`。

完整的部署指南请参阅 [docker/README.md](https://github.com/apache/hugegraph/blob/master/docker/README.md)。

> 注意：
> 
> 1. HugeGraph 的 Docker 镜像主要用于便捷地快速启动 HugeGraph，并不是 **ASF 官方发布物料包**。你可以从 [ASF Release Distribution Policy](https://infra.apache.org/release-distribution.html#dockerhub) 中了解更多细节。
>
> 2. 推荐使用 `release tag` (如 `1.7.0/1.x.0`) 以获取稳定版。使用 `latest` tag 可以使用开发中的最新功能。

#### 3.2 下载 tar 包

```bash
# use the latest version, here is 1.7.0 for example
wget https://downloads.apache.org/hugegraph/{version}/apache-hugegraph-incubating-{version}.tar.gz
tar zxf *hugegraph*.tar.gz
```

#### 3.3 源码编译

源码编译前请确保本机有安装 `wget/curl` 命令

下载 HugeGraph 源代码

```bash
git clone https://github.com/apache/hugegraph.git
```

编译打包生成 tar 包

```bash
cd hugegraph
# (Optional) use "-P stage" param if you build failed with the latest code(during pre-release period)
mvn package -DskipTests
```

执行日志如下：

```bash
......
[INFO] Reactor Summary for hugegraph 1.5.0:
[INFO] 
[INFO] hugegraph .......................................... SUCCESS [  2.405 s]
[INFO] hugegraph-core ..................................... SUCCESS [ 13.405 s]
[INFO] hugegraph-api ...................................... SUCCESS [ 25.943 s]
[INFO] hugegraph-cassandra ................................ SUCCESS [ 54.270 s]
[INFO] hugegraph-scylladb ................................. SUCCESS [  1.032 s]
[INFO] hugegraph-rocksdb .................................. SUCCESS [ 34.752 s]
[INFO] hugegraph-mysql .................................... SUCCESS [  1.778 s]
[INFO] hugegraph-palo ..................................... SUCCESS [  1.070 s]
[INFO] hugegraph-hbase .................................... SUCCESS [ 32.124 s]
[INFO] hugegraph-postgresql ............................... SUCCESS [  1.823 s]
[INFO] hugegraph-dist ..................................... SUCCESS [ 17.426 s]
[INFO] hugegraph-example .................................. SUCCESS [  1.941 s]
[INFO] hugegraph-test ..................................... SUCCESS [01:01 min]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
......
```

执行成功后，在 hugegraph 目录下生成 `*hugegraph-*.tar.gz` 文件，就是编译生成的 tar 包。

<details>
<summary>过时的 tools 工具安装</summary>

#### 3.4 使用 tools 工具部署 (Outdated)

HugeGraph-Tools 提供了一键部署的命令行工具，用户可以使用该工具快速地一键下载、解压、配置并启动 HugeGraph-Server 和 HugeGraph-Hubble，最新的 HugeGraph-Toolchain 中已经包含所有的这些工具，直接下载它解压就有工具包集合了

```bash
# download toolchain package, it includes loader + tool + hubble, please check the latest version (here is 1.7.0)
wget https://downloads.apache.org/hugegraph/1.7.0/apache-hugegraph-toolchain-incubating-1.7.0.tar.gz
tar zxf *hugegraph-*.tar.gz
# enter the tool's package
cd *hugegraph*/*tool*
```

> 注：`${version}` 为版本号，最新版本号可参考 [Download 页面](/docs/download/download)，或直接从 Download 页面点击链接下载

HugeGraph-Tools 的总入口脚本是 `bin/hugegraph`，用户可以使用 `help` 子命令查看其用法，这里只介绍一键部署的命令。

```bash
bin/hugegraph deploy -v {hugegraph-version} -p {install-path} [-u {download-path-prefix}]
```

`{hugegraph-version}` 表示要部署的 HugeGraphServer 及 HugeGraphStudio 的版本，用户可查看 `conf/version-mapping.yaml` 文件获取版本信息，`{install-path}` 指定 HugeGraphServer 及 HugeGraphStudio 的安装目录，`{download-path-prefix}` 可选，指定 HugeGraphServer 及 HugeGraphStudio tar 包的下载地址，不提供时使用默认下载地址，比如要启动 0.6 版本的 HugeGraph-Server 及 HugeGraphStudio 将上述命令写为 `bin/hugegraph deploy -v 0.6 -p services` 即可。
</details>

### 4 配置

如果需要快速启动 HugeGraph 仅用于测试，那么只需要进行少数几个配置项的修改即可（见下一节）。

详细的配置介绍请参考[配置文档](/docs/config/config-guide)及[配置项介绍](/docs/config/config-option)。

### 5 启动

#### 5.1 使用启动脚本启动

启动流程分为“首次启动”和“非首次启动”。首次启动前需要先初始化后端数据库，然后再启动服务。

如果服务曾被手动停止，或因其他原因需要再次启动，由于后端数据库已持久化存在，通常可以直接启动服务。

HugeGraphServer 启动时会连接后端存储并检查其版本信息。如果后端尚未初始化，或者已初始化但版本不匹配（例如存在旧版本数据），HugeGraphServer 会启动失败并给出错误信息。

如果需要外部访问 HugeGraphServer，请修改 `rest-server.properties` 的 `restserver.url` 配置项（默认为 `http://127.0.0.1:8080`），修改成机器名或 IP 地址。

由于各种后端所需的配置（hugegraph.properties）及启动步骤略有不同，下面逐一对各后端的配置及启动做介绍。

**注:** 如果想要开启 HugeGraph 权限系统，在启动 Server 之前应按照 [Server 鉴权配置](/cn/docs/config/config-authentication/) 进行配置。(尤其是生产环境/外网环境须开启)

##### 5.1.1 分布式存储 (HStore)

<details>
<summary>点击展开/折叠 分布式存储 配置及启动方法</summary>

> 分布式存储是 HugeGraph 1.5.0 之后推出的新特性，它基于 HugeGraph-PD 和 HugeGraph-Store 组件实现了分布式的数据存储和计算。

要使用分布式存储引擎，需要先部署 HugeGraph-PD 和 HugeGraph-Store，详见 [HugeGraph-PD 快速入门](/cn/docs/quickstart/hugegraph/hugegraph-pd/) 和 [HugeGraph-Store 快速入门](/cn/docs/quickstart/hugegraph/hugegraph-hstore/)。

确保 PD 和 Store 服务均已启动后

1. 修改 HugeGraph-Server 的 `hugegraph.properties` 配置：

```properties
backend=hstore
serializer=binary
task.scheduler_type=distributed

# PD 服务地址，多个 PD 地址用逗号分割，配置 PD 的 RPC 端口
pd.peers=127.0.0.1:8686,127.0.0.1:8687,127.0.0.1:8688
```

```properties
# 简单示例（带鉴权）
gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy

# 指定存储 hstore（必须）
backend=hstore
serializer=binary
store=hugegraph

# 指定任务调度器（1.7.0及之前，hstore 存储必须）
task.scheduler_type=distributed

# pd config
pd.peers=127.0.0.1:8686
```

2. 修改 HugeGraph-Server 的 `rest-server.properties` 配置：

```properties
usePD=true
# 注意，1.7.0 必须在 rest-server.properties 配置 pd.peers
pd.peers=127.0.0.1:8686,127.0.0.1:8687,127.0.0.1:8688

# 若需要 auth 
# auth.authenticator=org.apache.hugegraph.auth.StandardAuthenticator
```

如果配置多个 HugeGraph-Server 节点，需要为每个节点修改 `rest-server.properties` 配置文件，例如：

节点 1（主节点）：
```properties
usePD=true
restserver.url=http://127.0.0.1:8081
gremlinserver.url=http://127.0.0.1:8181
pd.peers=127.0.0.1:8686

rpc.server_host=127.0.0.1
rpc.server_port=8091

server.id=server-1
server.role=master
```

节点 2（工作节点）：
```properties
usePD=true
restserver.url=http://127.0.0.1:8082
gremlinserver.url=http://127.0.0.1:8182
pd.peers=127.0.0.1:8686

rpc.server_host=127.0.0.1
rpc.server_port=8092

server.id=server-2
server.role=worker
```

同时，还需要修改每个节点的 `gremlin-server.yaml` 中的端口配置：

节点 1：
```yaml
host: 127.0.0.1
port: 8181
```

节点 2：
```yaml
host: 127.0.0.1
port: 8182
```

初始化数据库：

```bash
cd *hugegraph-${version}
bin/init-store.sh
```

启动 Server：

```bash
bin/start-hugegraph.sh
```

使用分布式存储引擎的启动顺序为：
1. 启动 HugeGraph-PD
2. 启动 HugeGraph-Store
3. 初始化数据库（仅首次）
4. 启动 HugeGraph-Server

验证服务是否正常启动：

```bash
curl http://localhost:8081/graphs
# 应返回：{"graphs":["hugegraph"]}
```

停止服务的顺序应该与启动顺序相反：
1. 停止 HugeGraph-Server
2. 停止 HugeGraph-Store
3. 停止 HugeGraph-PD

```bash
bin/stop-hugegraph.sh
```

###### Docker 分布式集群

通过 Docker-Compose 运行完整的分布式集群（3 PD + 3 Store + 3 Server）：


```bash
cd hugegraph/docker
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-3pd-3store-3server.yml up -d
```

服务通过 `hg-net` 桥接网络上的容器主机名进行通信。配置通过环境变量注入：

```yaml
# Server 配置
HG_SERVER_BACKEND: hstore
HG_SERVER_PD_PEERS: pd0:8686,pd1:8686,pd2:8686
```

验证集群：
```bash
curl http://localhost:8080/versions
curl http://localhost:8620/v1/stores
```

运行时日志可通过 `docker logs <container-name>`（如 `docker logs hg-pd0`）直接查看，无需进入容器。

完整的环境变量参考、端口表和故障排查指南请参阅 [docker/README.md](https://github.com/apache/hugegraph/blob/master/docker/README.md)。
</details>

##### 5.1.2 RocksDB / ToplingDB

<details>
<summary>点击展开/折叠 RocksDB 配置及启动方法</summary>


> RocksDB 是一个嵌入式的数据库，不需要手动安装部署，要求 GCC 版本 >= 4.3.0（GLIBCXX_3.4.10），如不满足，需要提前升级 GCC

修改 `hugegraph.properties`

```properties
backend=rocksdb
serializer=binary
rocksdb.data_path=.
rocksdb.wal_path=.
```

初始化数据库（第一次启动时或在 `conf/graphs/` 下手动添加了新配置时需要进行初始化）

```bash
cd *hugegraph-${version}
bin/init-store.sh
```

启动 server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

提示的 url 与 `rest-server.properties` 中配置的 `restserver.url` 一致

**ToplingDB (Beta)**: 作为 RocksDB 的高性能替代方案，配置方式请参考: [ToplingDB Quick Start]({{< ref path="/blog/hugegraph/toplingdb/toplingdb-quick-start.md" lang="cn">}})

</details>

##### 5.1.3 HBase

<details>
<summary>点击展开/折叠 HBase 配置及启动方法</summary>

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

初始化数据库（第一次启动时或在 `conf/graphs/` 下手动添加了新配置时需要进行初始化）

```bash
cd *hugegraph-${version}
bin/init-store.sh
```

启动 server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

> 更多其它后端配置可参考[配置项介绍](/docs/config/config-option)

</details>

##### 5.1.4 MySQL

> ⚠️ **已废弃**: 此后端从 HugeGraph 1.7.0 版本开始已移除。如需使用，请参考 1.5.x 版本文档。

<details>
<summary>点击展开/折叠 MySQL 配置及启动方法</summary>

> 由于 MySQL 是在 GPL 协议下，与 Apache 协议不兼容，用户需自行安装 MySQL，[下载地址](https://dev.mysql.com/downloads/mysql/)

下载 MySQL 的[驱动包](https://repo1.maven.org/maven2/mysql/mysql-connector-java/)，比如 `mysql-connector-java-8.0.30.jar`，并放入 HugeGraph-Server 的 `lib` 目录下。

修改 `hugegraph.properties`，配置数据库 URL，用户名和密码，`store` 是数据库名，如果没有会被自动创建。

```properties
backend=mysql
serializer=mysql

store=hugegraph

# mysql backend config
jdbc.driver=com.mysql.cj.jdbc.Driver
jdbc.url=jdbc:mysql://127.0.0.1:3306
jdbc.username=
jdbc.password=
jdbc.reconnect_max_times=3
jdbc.reconnect_interval=3
jdbc.ssl_mode=false
```

初始化数据库（第一次启动时或在 `conf/graphs/` 下手动添加了新配置时需要进行初始化）

```bash
cd *hugegraph-${version}
bin/init-store.sh
```

启动 server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

</details>

##### 5.1.5 Cassandra

> ⚠️ **已废弃**: 此后端从 HugeGraph 1.7.0 版本开始已移除。如需使用，请参考 1.5.x 版本文档。

<details>
<summary>点击展开/折叠 Cassandra 配置及启动方法</summary>

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

初始化数据库（第一次启动时或在 `conf/graphs/` 下手动添加了新配置时需要进行初始化）

```bash
cd *hugegraph-${version}
bin/init-store.sh
Initing HugeGraph Store...
2017-12-01 11:26:51 1424  [main] [INFO ] org.apache.hugegraph.HugeGraph [] - Opening backend store: 'cassandra'
2017-12-01 11:26:52 2389  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph, try init keyspace later
2017-12-01 11:26:52 2472  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph, try init keyspace later
2017-12-01 11:26:52 2557  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph, try init keyspace later
2017-12-01 11:26:53 2797  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_graph
2017-12-01 11:26:53 2945  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_schema
2017-12-01 11:26:53 3044  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_index
2017-12-01 11:26:53 3046  [pool-3-thread-1] [INFO ] org.apache.hugegraph.backend.Transaction [] - Clear cache on event 'store.init'
2017-12-01 11:26:59 9720  [main] [INFO ] org.apache.hugegraph.HugeGraph [] - Opening backend store: 'cassandra'
2017-12-01 11:27:00 9805  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph1, try init keyspace later
2017-12-01 11:27:00 9886  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph1, try init keyspace later
2017-12-01 11:27:00 9955  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph1, try init keyspace later
2017-12-01 11:27:00 10175 [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_graph
2017-12-01 11:27:00 10321 [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_schema
2017-12-01 11:27:00 10413 [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_index
2017-12-01 11:27:00 10413 [pool-3-thread-1] [INFO ] org.apache.hugegraph.backend.Transaction [] - Clear cache on event 'store.init'
```

启动 server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

</details>

##### 5.1.6 Memory

<details>
<summary>点击展开/折叠 Memory 配置及启动方法</summary>

修改 hugegraph.properties

```properties
backend=memory
serializer=text
```

> Memory 后端的数据是保存在内存中无法持久化的，不需要初始化后端，这也是唯一一个不需要初始化的后端。

启动 server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

提示的 url 与 rest-server.properties 中配置的 restserver.url 一致

</details>

##### 5.1.7 ScyllaDB

> ⚠️ **已废弃**: 此后端从 HugeGraph 1.7.0 版本开始已移除。如需使用，请参考 1.5.x 版本文档。

<details>
<summary>点击展开/折叠 ScyllaDB 配置及启动方法</summary>

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

由于 scylladb 数据库本身就是基于 cassandra 的"优化版"，如果用户未安装 scylladb，也可以直接使用 cassandra 作为后端存储，只需要把 backend 和 serializer 修改为 scylladb，host 和 post 指向 cassandra 集群的 seeds 和 port 即可，但是并不建议这样做，这样发挥不出 scylladb 本身的优势了。

初始化数据库（第一次启动时或在 `conf/graphs/` 下手动添加了新配置时需要进行初始化）

```bash
cd *hugegraph-${version}
bin/init-store.sh
```

启动 server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

</details>

##### 5.1.8 启动 server 的时候创建示例图

在启动脚本时携带 `-p true` 参数，表示开启 preload，即创建示例图。

```
bin/start-hugegraph.sh -p true
Starting HugeGraphServer in daemon mode...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)......OK
```

并且使用 RESTful API 请求 `HugeGraphServer` 得到如下结果：

```javascript
> curl "http://localhost:8080/graphs/hugegraph/graph/vertices" | gunzip

{"vertices":[{"id":"2:lop","label":"software","type":"vertex","properties":{"name":"lop","lang":"java","price":328}},{"id":"1:josh","label":"person","type":"vertex","properties":{"name":"josh","age":32,"city":"Beijing"}},{"id":"1:marko","label":"person","type":"vertex","properties":{"name":"marko","age":29,"city":"Beijing"}},{"id":"1:peter","label":"person","type":"vertex","properties":{"name":"peter","age":35,"city":"Shanghai"}},{"id":"1:vadas","label":"person","type":"vertex","properties":{"name":"vadas","age":27,"city":"Hongkong"}},{"id":"2:ripple","label":"software","type":"vertex","properties":{"name":"ripple","lang":"java","price":199}}]}
```

代表创建示例图成功。

#### 5.2 使用 Docker

在 [3.1 使用 Docker 容器](#31-使用-docker-容器-便于测试) 中，我们已经介绍了如何使用 `docker` 部署 `hugegraph-server`。此外，也可以通过切换后端存储或设置参数，在 Server 启动时加载样例图。

##### 5.2.1 使用 Cassandra 作为后端

> ⚠️ **已废弃**: Cassandra 后端从 HugeGraph 1.7.0 版本开始已移除。如需使用，请参考 1.5.x 版本文档。

<details>
<summary>点击展开/折叠 Cassandra 配置及启动方法</summary>

在使用 Docker 的时候，我们可以使用 Cassandra 作为后端存储。我们更加推荐直接使用 docker-compose 来对于 server 以及 Cassandra 进行统一管理

样例的 `docker-compose.yml` 可以在 [github](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/docker/example/docker-compose-cassandra.yml) 中获取，使用 `docker-compose up -d` 启动。(如果使用 cassandra 4.0 版本作为后端存储，则需要大约两个分钟初始化，请耐心等待)

```yaml
version: "3"

services:
  server:
    image: hugegraph/hugegraph
    container_name: cas-server
    ports:
      - 8080:8080
    environment:
      hugegraph.backend: cassandra
      hugegraph.serializer: cassandra
      hugegraph.cassandra.host: cas-cassandra
      hugegraph.cassandra.port: 9042
    networks:
      - ca-network
    depends_on:
      - cassandra
    healthcheck:
      test: ["CMD", "bin/gremlin-console.sh", "--" ,"-e", "scripts/remote-connect.groovy"]
      interval: 10s
      timeout: 30s
      retries: 3

  cassandra:
    image: cassandra:4
    container_name: cas-cassandra
    ports:
      - 7000:7000
      - 9042:9042
    security_opt:
      - seccomp:unconfined
    networks:
      - ca-network
    healthcheck:
      test: ["CMD", "cqlsh", "--execute", "describe keyspaces;"]
      interval: 10s
      timeout: 30s
      retries: 5

networks:
  ca-network:

volumes:
  hugegraph-data:
```

在这个 yaml 中，需要在环境变量中以 `hugegraph.<parameter_name>`的形式进行参数传递，配置 Cassandra 相关的参数。

具体来说，在 `hugegraph.properties` 配置文件中，提供了 `backend=xxx`、`cassandra.host=xxx` 等配置项。为了通过环境变量传递这些配置，需要在配置项前加上 `hugegraph.`，例如 `hugegraph.backend` 和 `hugegraph.cassandra.host`。

其他配置可以参照 [4 配置](#4-配置)

</details>

##### 5.2.2 启动 server 的时候创建示例图

在 Docker 启动时设置环境变量 `PRELOAD=true`，即可在启动脚本执行过程中加载样例数据。

1. 使用`docker run`

    使用 `docker run -itd --name=server -p 8080:8080 -e PRELOAD=true hugegraph/hugegraph:1.7.0`

2. 使用`docker-compose`

    创建`docker-compose.yml`，具体文件如下，在环境变量中设置 PRELOAD=true。其中，[`example.groovy`](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/scripts/example.groovy) 是一个预定义的脚本，用于预加载样例数据。如果有需要，可以通过挂载新的 `example.groovy` 脚本改变预加载的数据。

    ```yaml
    version: '3'
    services:
      server:
        image: hugegraph/hugegraph:1.7.0
        container_name: server
        environment:
          - PRELOAD=true
          - PASSWORD=xxx
        volumes:
          - /path/to/yourscript:/hugegraph/scripts/example.groovy
        ports:
          - 8080:8080
    ```

    使用命令 `docker-compose up -d` 启动容器

使用 RESTful API 请求 `HugeGraphServer` 得到如下结果：

```javascript
> curl "http://localhost:8080/graphs/hugegraph/graph/vertices" | gunzip

{"vertices":[{"id":"2:lop","label":"software","type":"vertex","properties":{"name":"lop","lang":"java","price":328}},{"id":"1:josh","label":"person","type":"vertex","properties":{"name":"josh","age":32,"city":"Beijing"}},{"id":"1:marko","label":"person","type":"vertex","properties":{"name":"marko","age":29,"city":"Beijing"}},{"id":"1:peter","label":"person","type":"vertex","properties":{"name":"peter","age":35,"city":"Shanghai"}},{"id":"1:vadas","label":"person","type":"vertex","properties":{"name":"vadas","age":27,"city":"Hongkong"}},{"id":"2:ripple","label":"software","type":"vertex","properties":{"name":"ripple","lang":"java","price":199}}]}
```

代表创建示例图成功。


### 6 访问 Server

#### 6.1 服务启动状态校验

`jps` 查看服务进程

```bash
jps
6475 HugeGraphServer
```

`curl` 请求 RESTful API

```bash
echo `curl -o /dev/null -s -w %{http_code} "http://localhost:8080/graphs/hugegraph/graph/vertices"`
```

返回结果 200，代表 server 启动正常

#### 6.2 请求 Server

HugeGraphServer 的 RESTful API 包括多种类型的资源，典型的包括 graph、schema、gremlin、traverser 和 task

- `graph` 包含 `vertices`、`edges`
- `schema` 包含 `vertexlabels`、`propertykeys`、`edgelabels`、`indexlabels`
- `gremlin` 包含各种 `Gremlin` 语句，如 `g.v()`，可以同步或者异步执行
- `traverser` 包含各种高级查询，包括最短路径、交叉点、N 步可达邻居等
- `task` 包含异步任务的查询和删除

##### 6.2.1 获取 `hugegraph` 的顶点及相关属性

```bash
curl http://localhost:8080/graphs/hugegraph/graph/vertices 
```

_说明_

1. 由于图的点和边很多，对于 list 型的请求，比如获取所有顶点，获取所有边等，Server 会将数据压缩再返回，所以使用 curl 时得到一堆乱码，可以重定向至 `gunzip` 进行解压。推荐使用 Chrome 浏览器 + Restlet 插件发送 HTTP 请求进行测试。

    ```
    curl "http://localhost:8080/graphs/hugegraph/graph/vertices" | gunzip
    ```

2. 当前 HugeGraphServer 的默认配置只能是本机访问，可以修改配置，使其能在其他机器访问。

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

<p id="swaggerui-example"></p>

详细的 API 请参考 [RESTful-API](/docs/clients/restful-api) 文档。

另外也可以通过访问 `localhost:8080/swagger-ui/index.html` 查看 API。

<div style="text-align: center;">
  <img src="/docs/images/images-server/swagger-ui.png" alt="image">
</div>

在使用 Swagger UI 调试 HugeGraph 提供的 API 时，如果 HugeGraph Server 开启了鉴权模式，可以在 Swagger 页面输入鉴权信息。

<div style="text-align: center;">
  <img src="/docs/images/images-server/swagger-ui-where-set-auth-example.png" alt="image">
</div>

当前 HugeGraph 支持基于 Basic 和 Bearer 两种形式设置鉴权信息。

<div style="text-align: center;">
  <img src="/docs/images/images-server/swagger-ui-set-auth-example.png" alt="image">
</div>

### 7 停止 Server

```bash
$cd *hugegraph-${version}
$bin/stop-hugegraph.sh
```

### 8 使用 IntelliJ IDEA 调试 Server

请参考[在 IDEA 中配置 Server 开发环境](/docs/contribution-guidelines/hugegraph-server-idea-setup)
