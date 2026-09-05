---
title: "配置 HBase 后端"
linkTitle: "配置 HBase 后端"
weight: 7
---

### 概述

HBase 后端将图数据存储在 Apache HBase 表中。HugeGraph 仅作为 HBase 客户端：它通过 HBase 的 ZooKeeper 集群连接，为每个图创建一个 HBase namespace，并在其中创建该图的 schema 表、数据表和索引表。计数查询由 HBase 的 `AggregateImplementation` 协处理器完成，HugeGraph 在创建每张表时都会挂载该协处理器。

> 注意：HBase 后端已废弃，计划在 HugeGraph 2.0 中移除。新部署请使用 `hstore`（分布式）或 `rocksdb`（内嵌，默认值），已有的 HBase 部署请规划迁移。

自 1.7.0 起，发行包内置的后端只有 `hstore`、`rocksdb`、`hbase` 和 `memory`。HBase provider 上报的后端驱动版本为 `1.12`。

### 支持的 HBase 版本

客户端 jar 固定为 HBase `2.6.5`（`hbase-endpoint` 加 `hbase-shaded-client`）。服务端要求 HBase 2.x：当检测到的 HBase 版本低于 `2.0` 时，scan 逻辑会把 inclusive stop row 改写为 exclusive 并追加一个 `0` 字节，因为该版本之前 inclusive stop row 不生效。CI 任务和本地 Docker 镜像都使用 HBase 2.6.5，后端也是针对这个版本做测试的。

### 选择该后端

修改需要使用 HBase 的图的 `conf/graphs/hugegraph.properties`：

```ini
backend=hbase
serializer=hbase

# namespace 名称由该值推导得出
store=hugegraph

hbase.hosts=localhost
hbase.port=2181
hbase.znode_parent=/hbase
```

> 注意：`serializer` 必须设置为 `hbase`，而不是 `binary`。HBase 序列化器是 `BinarySerializer` 的子类，它不在 rowkey 中写入 id 前缀，并写入预分区的顶点表和边表所需要的分区前缀。使用 `serializer=binary` 时这两点都不生效。

然后初始化后端并启动服务：

```bash
./bin/init-store.sh
./bin/start-hugegraph.sh
```

默认发行包构建时包含 `rocksdb, hbase, hstore` 三个后端，无需额外引入 jar。使用 `rocksdb-only` Maven profile 构建的发行包不包含 HBase 后端，此时 `backend=hbase` 会以 `Not exists BackendStoreProvider: hbase` 打开失败。

下面所有配置项都位于图配置文件（`conf/graphs/hugegraph.properties`）中，而不是 `rest-server.properties`。只有当发行包包含 `hbase` 后端时，这些配置项才会被注册。

### 连接配置项

| 配置项                | 默认值       | 说明                                                                                                                    |
|--------------------|-----------|-----------------------------------------------------------------------------------------------------------------------|
| hbase.hosts        | localhost | HBase ZooKeeper 的主机名或 IP 地址，多个以逗号分隔，不允许为空。对应 `hbase.zookeeper.quorum`。                                                 |
| hbase.port         | 2181      | HBase ZooKeeper 的端口，取值范围 1 到 65535。对应 `hbase.zookeeper.property.clientPort`。                                           |
| hbase.znode_parent | /hbase    | HBase ZooKeeper 的 znode 父路径，不允许为空。对应 `zookeeper.znode.parent`。                                                         |
| hbase.zk_retry     | 3         | HBase ZooKeeper 的恢复重试次数，取值范围 0 到 1000。对应 `zookeeper.recovery.retry`。                                                   |
| hbase.threads_max  | 64        | HBase 连接的最大线程数，取值范围 1 到 1000。对应 `hbase.hconnection.threads.max`，HBase 自身默认值为 256，这里取更小的值以避免内存溢出。                        |

### 超时配置项

| 配置项                       | 默认值             | 说明                                                                       |
|---------------------------|-----------------|--------------------------------------------------------------------------|
| hbase.truncate_timeout    | 30              | 等待后端 truncate 的超时时间，单位秒，必须为正数。该超时按 store 计算，而一个图有三个 store，因此一次 truncate 最多耗时该值的三倍。 |
| hbase.aggregation_timeout | 43200（12 小时）    | 等待聚合的超时时间，单位秒，必须为正数。它会设置计数查询所用聚合客户端的 `hbase.rpc.timeout`。                 |

### Kerberos 与 HBase 配置文件配置项

| 配置项                      | 默认值                            | 说明                                                                     |
|--------------------------|--------------------------------|------------------------------------------------------------------------|
| hbase.kerberos_enable    | false                          | 是否为 HBase 启用 Kerberos 认证。                                              |
| hbase.krb5_conf          | /etc/krb5.conf                 | Kerberos 配置文件，包含 KDC IP、默认 realm 等。会被设置为 `java.security.krb5.conf` 系统属性。 |
| hbase.hbase_site         | /etc/hbase/conf/hbase-site.xml | HBase 的配置文件。无论是否启用 Kerberos，每次建立连接时都会把它作为配置资源加载。                        |
| hbase.kerberos_principal | （空）                            | Kerberos 认证使用的 HBase principal。                                        |
| hbase.kerberos_keytab    | （空）                            | Kerberos 认证使用的 HBase keytab 文件。                                        |

当 `hbase.kerberos_enable=true` 时，HugeGraph 会在连接上把 `hadoop.security.authentication` 和 `hbase.security.authentication` 设置为 `kerberos`，然后在打开连接之前用配置的 principal 从 keytab 登录。因此 Kerberos 环境下 `hbase.krb5_conf`、`hbase.hbase_site`、`hbase.kerberos_principal` 和 `hbase.kerberos_keytab` 四项都必须有效：

```ini
hbase.kerberos_enable=true
hbase.krb5_conf=/etc/krb5.conf
hbase.hbase_site=/etc/hbase/conf/hbase-site.xml
hbase.kerberos_principal=hugegraph/host@EXAMPLE.COM
hbase.kerberos_keytab=/etc/security/keytabs/hugegraph.keytab
```

即使关闭 Kerberos，`hbase.hbase_site` 也会被读取，路径不存在时相当于加载了一个空资源。当需要上述配置项之外的 HBase 设置时，把它指向集群自身的 `hbase-site.xml`。

### 预分区配置项

| 配置项                     | 默认值  | 说明                                                     |
|-------------------------|------|--------------------------------------------------------|
| hbase.enable_partition  | true | 是否为 HBase 启用预分区。它同时决定后端是否声明支持前缀扫描和范围扫描。                 |
| hbase.vertex_partitions | 10   | HBase 顶点表的分区数，不允许为负数。                                  |
| hbase.edge_partitions   | 30   | HBase 边表的分区数，不允许为负数。                                   |

启用预分区后，顶点表按 `hbase.vertex_partitions` 个 region 创建，两张边表各按 `hbase.edge_partitions` 个 region 创建，序列化器会在 rowkey 前面加上 id 哈希得到的分区前缀。

> 注意：请在初始化后端之前，按实际数据量和 region server 数量调整分区数。它对导入速度影响很大，并且只在建表时生效。

关闭 `hbase.enable_partition` 会恢复不带前缀的原始 rowkey。作为交换，后端此时会声明支持前缀扫描和范围扫描，这两类扫描在预分区 rowkey 下无法工作。

### Namespace 与表结构

每个图对应一个 HBase namespace，名称为 `<graphspace>/<store>` 转小写，并把 `/` 替换为 `_`，因为 HBase namespace 名称只允许字母数字和 `_` 字符。在默认配置 `graphspace=DEFAULT`、`store=hugegraph` 下，namespace 为 `default_hugegraph`。

在该 namespace 内，一个图包含三个 store：schema store `m`、graph store `g` 和 system store `s`：

| Store        | 表                                                                                                                    |
|--------------|----------------------------------------------------------------------------------------------------------------------|
| schema (`m`) | `VL`、`EL`、`PK`、`IL`、`C`、`m_si`                                                                                        |
| graph (`g`)  | `g_v`、`g_oe`、`g_ie`、`g_si`、`g_vi`、`g_ei`、`g_ii`、`g_fi`、`g_li`、`g_di`、`g_ai`、`g_hi`、`g_ui`                              |
| system (`s`) | `s_v`、`s_oe`、`s_ie`、`s_si`、`s_vi`、`s_ei`、`s_ii`、`s_fi`、`s_li`、`s_di`、`s_ai`、`s_hi`、`s_ui`、`M`                          |

`g_v` 是顶点表，`g_oe` 和 `g_ie` 分别是出边表和入边表，其余 `g_*` 表依次是二级索引、顶点标签索引、边标签索引、范围索引（int、float、long、double）、全文索引、shard 索引和唯一索引表。所有表都只有一个名为 `f` 的列族，并且都在建表时挂载了 `org.apache.hadoop.hbase.coprocessor.AggregateImplementation` 协处理器。只有 `g_v`、`g_oe` 和 `g_ie` 会预分区，system store 中同名的那几张表按单个 region 创建。

system store 中的 `M` 表保存 `init-store.sh` 写入的后端版本。truncate 图时会排除该表，因为丢失它会导致下次启动的版本校验失败。清空图会删除这些表；连同存储空间一起清空则会删除整个 namespace。

`GET /metrics/backend` 会返回 HBase 集群状态：`cluster_id`、`master_name`、`average_load`、`hbase_version`、`region_count`、`leaving_servers`、`nodes`、`region_servers`，以及一个 `servers` map，其中包含每个 region server 的堆内存、磁盘、请求数和 region 明细。`PUT /graphspaces/{graphspace}/graphs/{name}/compact` 会请求 HBase 对该图的所有表做 compaction。

### 使用 Docker 做本地测试

Server 仓库中的 `docker/hbase` 会构建一个 HBase 2.6.5 单机镜像（`hugegraph/hbase:2.6.5`，容器名 `hg-hbase-test`），用于本地开发和测试。以下命令都在仓库根目录执行。

为运行在宿主机上的 HugeGraph 启动 HBase：

```bash
docker compose -p hg-hbase -f docker/hbase/docker-compose.hbase.yml build --no-cache hbase
HBASE_MASTER_HOSTNAME=localhost HBASE_REGIONSERVER_HOSTNAME=localhost \
docker compose -p hg-hbase -f docker/hbase/docker-compose.hbase.yml up -d
until docker exec hg-hbase-test nc -z localhost 2181 >/dev/null 2>&1; do sleep 2; done
```

为运行在同一个 Docker 网络中的容器化 HugeGraph 启动 HBase：

```bash
HBASE_HOSTNAME=hbase docker compose -p hg-hbase -f docker/hbase/docker-compose.hbase.yml up -d
```

对外公布的主机名很重要：容器启动时会把 `HBASE_MASTER_HOSTNAME` 和 `HBASE_REGIONSERVER_HOSTNAME` 写入自己的 `hbase-site.xml`，未设置时回退到 `HBASE_HOSTNAME`（默认 `hbase`）。如果客户端无法解析这个主机名，即使 ZooKeeper 可用，也会报 `UnknownHostException: hbase:16000`。

映射到宿主机的端口：

| 端口    | 服务                                                |
|-------|---------------------------------------------------|
| 2181  | ZooKeeper，与 `hbase.port` 默认值一致                    |
| 16000 | HBase Master RPC                                  |
| 16010 | HBase Master Web UI，`http://localhost:16010`      |
| 16020 | HBase RegionServer RPC                            |
| 16030 | HBase RegionServer Web UI，`http://localhost:16030` |

针对它运行后端测试：

```bash
mvn test -pl hugegraph-server/hugegraph-test -am -P core-test,hbase
```

停止并删除数据卷：

```bash
docker compose -p hg-hbase -f docker/hbase/docker-compose.hbase.yml down -v
```

该镜像会分别启动 ZooKeeper、master 和 region server 三个守护进程，并等到 master 上报有存活的 server 之后才开始 tail 日志，因此首次启动会比较慢。请给 Docker 分配至少 4 GB 内存。compose 的健康检查也因此设置了 90 秒的 start period。

### 限制

HBase 后端不支持以下特性：

- 事务。rollback 只会丢弃尚未提交的批次，而 commit 是逐表写入的，因此跨表不是原子的。
- 原地更新单个顶点或边属性，以及合并顶点属性。属性存放在一个 cell 中，因此会重写整个属性列。
- 按名称查询 schema，以及仅按标签查询顶点或边。这两者都需要 HBase 二级索引。
- 按标签删除边。
- 带 `in` 条件、`contains` 条件或 `contains_key` 条件的查询。
- 聚合属性和 OLAP 属性。
- 原生数值类型（后端特性 `supportsNumberType` 为关闭状态）。
- scan token。
- `hbase.enable_partition` 为 `true` 时的前缀扫描和范围扫描。
- 除 `count` 以外的聚合函数，其它聚合函数会被拒绝。
- 快照。创建或恢复后端快照会抛出 `UnsupportedOperationException`。

已支持的特性包括顶点和边的 TTL、分页查询、order by 查询、范围条件，以及按输入 id 排序。
