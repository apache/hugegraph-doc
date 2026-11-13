---
title: "配置 HStore 分布式后端"
linkTitle: "配置 HStore 后端"
weight: 6
search_keywords:
  - hstore
  - pd.peers
  - usePD
  - hstore.partition_count
---

### 1 概述

`hstore` 是 HugeGraph 的分布式存储后端。图使用该后端时，HugeGraph-Server 本地磁盘上不保存任何图数据，数据由另外两个进程负责：

- **HugeGraph-PD**（Placement Driver）保存集群元数据：已注册的 Store 列表、每个图的分区布局、分区到 Store
  的映射关系、图的 Schema 以及 Schema 的 id 计数器。
- **HugeGraph-Store** 保存实际的键值数据，并通过 Raft 在多个 Store 节点之间复制。

Server 进程内嵌了 PD 客户端和 Store 客户端。每次读写时，它先向 PD 查询该 key 属于哪个分区、当前哪个 Store 节点是这个分区的 leader，然后把请求直接发给这个 Store 节点。

服务端的适配层是 `hugegraph-hstore` 模块，它以后端名 `hstore` 注册，驱动版本为 `1.13`。

选择 `hstore` 影响的不只是数据写到哪里，Server 还会根据后端类型切换下列行为：

| 方面           | 使用 `hstore`                                | 使用本地后端                |
|----------------|----------------------------------------------|-----------------------------|
| Schema 存储    | 通过 PD 元数据驱动读写 Schema                | Schema 保存在 `m` store 中  |
| Schema id      | 通过 PD 客户端由 PD 分配                     | 由 schema store 分配        |
| System store   | 没有独立的 system store，系统数据写入 graph store | 独立的 `s` store       |
| 任务调度器     | `distributed`                                | `local`                     |
| 权限管理器     | `StandardAuthManagerV2`                      | `StandardAuthManager`       |
| 后端版本校验   | 读取 graph store                             | 读取 system store           |
| `init-store.sh`| 跳过该图，元数据由 PD 和 Store 负责          | 创建本地 store              |

### 2 前置条件

`hstore` 不能独立工作。在 Server 打开 `hstore` 图之前，PD 集群和至少一个 Store 节点必须已经运行，并且启动顺序如下：

1. **PD**，先启动以便组成 Raft 组。
2. **Store**，通过 gRPC 向 PD 注册。gRPC 地址出现在 PD 自身 `pd.initial-store-list` 中的 Store 会直接进入
   `Up` 状态；不在该列表中、并且 PD 从未见过它处于 `Up` 或 `Offline` 的 Store 会注册为 `Pending`，
   需要先激活才能提供数据服务。
3. **Server**，随后从 PD 读回 Store 列表。

服务端需要关注的默认端口：

| 进程  | gRPC 端口 | REST 端口 |
|-------|-----------|-----------|
| PD    | 8686      | 8620      |
| Store | 8500      | 8520      |

服务端的 `pd.peers` 指向 PD 的 **gRPC** 端口，而不是 REST 端口。

另外两个进程的安装与配置方式，参见 [安装/构建 HugeGraph-PD](/cn/docs/quickstart/hugegraph/hugegraph-pd/) 和 [安装/构建 HugeGraph-Store](/cn/docs/quickstart/hugegraph/hugegraph-hstore/)。

### 3 选择 hstore 后端

#### 3.1 图配置文件

在图的属性文件（例如 `conf/graphs/hugegraph.properties`）中设置后端：

```ini
backend=hstore
serializer=binary
store=hugegraph
pd.peers=127.0.0.1:8686
```

关于这四个配置项：

- `backend=hstore` 选择该适配层。自 1.7.0 起允许的取值为 `memory`、`rocksdb`、`hbase` 和 `hstore`。
  发行包中做校验的位置对该值不区分大小写。
- `serializer=binary` 是必需的。注册 `hstore` 后端时只注册了配置空间和存储 provider，并没有注册自己的
  序列化器，适配层就是按二进制序列化器编写的。`serializer` 的内置默认值是 `text`，因此必须显式写出该项。
- `store=hugegraph` 是 PD 看到的图名中的命名空间部分。Server 以 `<graphspace>/<store>` 打开 provider，
  每个底层 store 再追加自己的后缀，因此 PD 中每个 store 对应一个图条目：图数据是
  `DEFAULT/hugegraph/g`，schema store 位是 `DEFAULT/hugegraph/m`。`graphspace` 默认为 `DEFAULT`，
  `g` 和 `m` 是固定的。
- `pd.peers` 是以逗号分隔的 PD gRPC 地址列表。适配层从**图**配置中读取该项，而不是从
  `rest-server.properties` 中读取，图级别的元数据连接也使用同一个值。

如果图配置文件中没有 `pd.peers`，那么在加载图时，只要 `usePD` 为 true 或者后端是 `hstore`， Server 会把 `rest-server.properties` 中的值复制到图配置里。不过在图配置文件中显式写出该项更清晰。

#### 3.2 rest-server.properties

```ini
# use pd
usePD=true
pd.peers=127.0.0.1:8686
```

`usePD=true` 让 Server 在启动时从 PD 加载元数据。在这条路径上，它会把元数据管理器连接到 PD，创建内置的 admin 账号和默认图空间，加载图空间与服务，创建内部的系统图（后端固定为 `hstore`），并加载 PD 中保存的图配置。

它和图级别的 `backend=hstore` 是两个独立的开关：一个图可以使用 `hstore` 而 `usePD` 保持默认的 `false`，此时 Server 不会走基于 PD 的元数据路径。发行包自带的测试启动脚本在后端为 `hstore` 时会设置该项。

#### 3.3 发行包中的模板文件

发行包在 `conf/graphs/hstore.properties.template` 中提供了一份该后端的现成图配置文件。它与 `hugegraph.properties` 的差别是：把 `backend` 设为 `hstore`、不注释 `pd.peers=127.0.0.1:8686`、
并且不包含内存管理配置段。

hstore 的 Docker 镜像会自动套用这份模板：它删除 `conf/graphs/hugegraph.properties`，再把模板重命名过去，因此容器启动时就已经选好了 `hstore` 后端。

本地构建的发行包默认编译了 `hstore` provider。`rocksdb-only` 这个 Maven profile 会把编译进去的后端列表
收窄为只有 `rocksdb`，`backend=hstore` 在 provider 工厂检查后会报 `Not exists BackendStoreProvider: hstore`。

### 4 hstore 配置项

`hstore` 配置空间中只有下面两个配置项，它们写在图的属性文件里。

| 配置项                 | 默认值 | 说明                                                            |
|------------------------|--------|-----------------------------------------------------------------|
| hstore.partition_count | 0      | 分区数量，PD 依据该值控制分区（Number of partitions）。         |
| hstore.shard_count     | 0      | 副本数量，PD 依据该值控制分区副本（Number of copies）。         |
{.td-table--wide}

#### 4.1 hstore.partition_count

每个 graph store 第一次被打开时，Server 会把这个数字连同图名一起发给 PD。取负值会在此处被拒绝，报错信息为 `The value of hstore.partition_count cannot be less than 0.`

PD 对该值的处理方式：

- `0`，也就是默认值，表示交给 PD 决定。对图数据 store，PD 使用自身集群级别的分区总数，该总数由
  `pd.initial-store-list` 中的条目数量、`partition.store-max-shard-count` 和
  `partition.default-shard-count` 推算得出；对 `/m` 和 `/s` store 固定使用 `1`。
- 取值在 `1` 到该总数之间时，按原值使用。
- 取值大于该总数时，会被下调到该总数。

该数字在 store 首次向 PD 注册时生效，之后再修改属性文件不会让已有的图重新分区。

#### 4.2 hstore.shard_count

`hstore.shard_count` 声明在 `hstore` 配置空间中，属性文件里也接受该项，但当前版本服务端没有任何代码读取它：适配层读取的只有 `hstore.partition_count` 一项。实际生效的副本数由 PD 的配置决定，即 PD `application.yml`
中的 `partition.default-shard-count`。

### 5 只在 hstore 模式下生效的其他配置项

下列配置项位于公共的 `rest-server.properties` 和图属性文件中，但只有在使用 PD 和 `hstore` 后端时才生效，或者才会改变行为。source 列给出该配置项在本轮核对的 Server 主线提交 `2f827d6` 中的声明位置（文件与行号）。

| 配置项                       | 文件                   | 默认值         | 在 hstore 模式下的作用                                            | source                       |
|------------------------------|------------------------|----------------|-------------------------------------------------------------------|------------------------------|
| pd.peers                     | rest-server.properties | 127.0.0.1:8686 | 用于元数据、服务发现和系统图的 PD 地址                            | `ServerOptions.java:195-201` |
| pd.peers                     | {graph}.properties     | 127.0.0.1:8686 | 后端适配层自身使用的 PD 地址                                      | `CoreOptions.java:649-654`   |
| usePD                        | rest-server.properties | false          | Server 启动时是否从 PD 加载元数据                                 | `ServerOptions.java:401-407` |
| cluster                      | rest-server.properties | hg-test        | 集群名，作为所有 PD 元数据 key 的前缀                             | `ServerOptions.java:187-193` |
| init_store.enabled           | rest-server.properties | true           | PD/Store 部署下应设为 `false`，元数据已由存储侧负责               | `ServerOptions.java:382-390` |
| graph.load_from_local_config | rest-server.properties | false          | 控制构造阶段预加载。应用初始化仍扫描并尝试加载本地配置，`false` 不会阻止本地加载。图配置变化通过重启 Server 应用。 | `ServerOptions.java:366-372` |
| auth.graph_store             | rest-server.properties | hugegraph      | 保存权限数据的图，关闭 init-store 时会校验它使用 `hstore` 后端    | `ServerOptions.java:602-609` |
| graphspace                   | {graph}.properties     | DEFAULT        | PD 看到的图名的第一段                                             | `CoreOptions.java:679-685`   |
{.td-table--wide}

`init-store.sh` 从不初始化 `hstore` 图。在开启的路径上，它扫描 `conf/graphs` 并跳过后端为 `hstore` 的每一个图。如果用 `init_store.enabled=false` 整体关闭这一步，它会改为校验 admin 账号仍然能在 PD 启动路径上被创建：
`usePD` 必须为 true、权限图必须存在于本地配置中且后端为 `hstore`、`auth.admin_pa` 必须显式设置为非空值。否则启动会直接失败，而不是使用公开的默认密码创建账号。

### 6 Server 如何通过 PD 发现 Store

适配层在进程中第一次打开 `hstore` 图时，一次性构建这些客户端：

1. 用 `pd.peers` 构建 PD 客户端配置，带上 PD 的鉴权凭据，并开启客户端侧的分区缓存。
2. 创建进程级的 PD 客户端。
3. 用该 PD 客户端创建进程级的 Store 客户端。

创建 Store 客户端时，会把一个基于 PD 的分区器同时注册为 Store 客户端节点管理器的 node provider、 partitioner 和 notifier。路由逻辑全部在这个分区器中：

- **单点和前缀请求**：向 PD 查询拥有该 key 的分区，取该分区的 leader 副本，把请求发到对应的 store id。
- **按 code 的范围扫描**：按 code 逐个遍历分区直到覆盖整个范围，每个分区产生一个目标 Store。
- **全图扫描**：向 PD 查询该图的活跃 Store，并向全部 Store 扇出请求。
- **Store 地址解析**：通过 PD 把 store id 解析成主机和端口。
- **缓存失效**：当某个 Store 返回分区 leader 已迁移时，notifier 会更新 PD 客户端缓存中的分区 leader
  并使过期的分区条目失效，之后的请求就会跟随新的 leader。

由于 Store 列表来自 PD 而不是配置文件，增删 Store 节点只需要针对同一个 PD 集群启动或停止它，服务端不需要改任何配置。

### 7 后端能力

`hstore` 并不支持本地后端的所有查询形式。对用户可见的差异如下：

| 特性                  | 是否支持 |
|-----------------------|----------|
| 按 key 前缀扫描       | 支持     |
| 按 key 范围扫描       | 支持     |
| 带范围条件的查询      | 支持     |
| 带 order by 的查询    | 支持     |
| 分页查询              | 支持     |
| OLAP 属性             | 支持     |
| Task 和 Server 顶点   | 支持     |
| Scan token            | 不支持   |
| 按名称查询 Schema     | 不支持   |
| 按 label 查询         | 不支持   |
| 带 `in` 条件的查询    | 不支持   |
| 带 `contains` 的查询  | 不支持   |
| 带 `contains key` 的查询 | 不支持 |
| 按输入 id 顺序排序    | 不支持   |
| 按 label 删除边       | 不支持   |
| 更新顶点属性          | 不支持   |
| 更新边属性            | 不支持   |
| 事务                  | 不支持   |
| Number 类型           | 不支持   |
| 聚合属性              | 不支持   |
| TTL                   | 不支持   |

不支持按输入 id 顺序排序，是因为多节点批量扫描会按 Store 对输入 key 分组，从而丢失全局顺序；不支持更新顶点和边属性，是因为属性被存放在单个 cell 中。

### 8 验证

Server 启动后，后端指标接口会返回 PD 当前认为处于活跃状态的 Store 数量：

```bash
curl http://localhost:8080/metrics/backend
```

响应中的 `nodes` 就是 PD 返回的活跃 Store 数量。`nodes` 为 `0` 说明 Server 连上了 PD，但 PD 中没有状态为 `Up` 的 Store，通常是 Store 节点还没注册，或者因为不在 PD 的 `pd.initial-store-list` 中而注册成了 `Pending`。

### 9 旧 GraphID 升级预检

部分 1.7 Store 批量写入会在缺失 GraphID 映射时使用保留前缀 `FFFE`。新版分配真实 GraphID 后，旧行不会自动移动，
读取可能看不到旧数据；Raft 回放也可能触发分配。这不意味着所有 1.7 数据库都需要迁移。

> [!NOTE]
> 已发布的 1.7.0 不包含此保护。依赖下述行为前，请确认 Store 构建已包含 [GraphID 预检补丁](https://github.com/apache/hugegraph/pull/3330)。

包含补丁的 Store 会在注册 Store、启动心跳和 Raft 前，只读检查配置目录中所有仍保留的有效分区 DB 版本。
每个业务列族通过有序定位检查 `FFFE`，不做全库扫描。发现旧行、无法安全读取 DB、非空 DB 目录缺少 `CURRENT`，
或选中的不完整版本会遮蔽有效旧版本时，启动失败，
并报告阶段、分区和路径；发现旧行时还会报告列族。本次启动不会向 PD 注册为 `Up`，此前的注册可能要等心跳超时才失效。

检查不会创建、清理或重写分区 DB，也不改变持久化 ID 格式。分配缺失 ID、冷打开 DB、初始化 Raft 和激活暂存快照前仍有相同保护；
已缓存的主会话会直接检查，以覆盖关闭 WAL 后未刷盘的数据。后续本地恢复中的 GraphID 预检失败会请求非零退出。
快照被拒绝时保留当前 DB 和提交索引、输入快照及暂存副本。整个应用启动并非只读：配置加载可能已访问 PD，后续启动阶段中的 Store/Raft 位置元数据也可能已更新。

#### 启动前的离线检查命令

> [!NOTE]
> 以下命令另需 Store 构建包含 [离线检查器补丁](https://github.com/apache/hugegraph/pull/3399)。
> 工具可用性取决于该运行时变更合入并进入所用发行包，不能据此推断某个已发布 tag 已提供脚本。
> 注册前保护与离线命令是不同入口；仅包含上述注册前保护的构建不一定包含此命令。

先停写、保留匹配的 PD、Store 数据与 Raft 备份，并按原版本流程完成快照和停止 Store。
使用 Java 17（由 `JAVA_HOME` 或 `PATH` 选择），从包含补丁的 Store 发行包目录运行：

```bash
bin/hugegraph-store-check.sh --check
```

`--config` 指定本地配置目录，默认是发行包下的 `conf`；`--data-path` 可显式指定实际数据根目录。
多个根目录在同一个参数中用逗号分隔，不要重复 `--data-path`：重复选项会被拒绝，而不会累加。

```bash
bin/hugegraph-store-check.sh --check \
  --config /srv/hugegraph-store/conf \
  --data-path /srv/store-data-a,/srv/store-data-b
```

路径示例需替换为实际部署值。相对路径从 Store 发行包目录解析。命令依次读取 `application.yml` 和存在时的
`application-pd.yml`，不启动 Spring、PD、Server 或 Raft，也不创建被检查的数据库。
它不会自动应用 Spring 环境变量、JSON 或 profile 覆盖；例如容器的 `HG_STORE_DATA_PATH` 需通过 `--data-path` 显式传入，
不能依赖入口脚本的 `SPRING_APPLICATION_JSON`。使用这类覆盖时，配置文件也必须包含解析后的有效 RocksDB 设置。

Topling 部署须先准备经过验证的运行时资产，设置 `TOPLINGDB_ROCKSDB_PROVIDER=topling`，并在有效配置中保留
`rocksdb.provider=topling`。检查器复用 Store 启动器的运行时选择逻辑，选中的 JNI JAR 优先于发行包内标准 RocksDB 类；
资产缺失或验证失败会拒绝检查，不应改用其他 provider 把它当作通过。

逐个检查每台已停止的 Store。活动数据库锁会导致拒绝；另一个只读进程也无法看到运行中 Store 的未刷盘 memtable。
检查范围包括配置的数据根、保留的 DB 版本、各分区最新本地快照和记录的其他存储位置。它按列族定位 `FFFE` 并校验
GraphID 元数据，不全量扫描业务行，也不通过可能清理旧版本的普通 DB 打开流程。

| 结果 | 含义与处理 |
| --- | --- |
| 退出 0 | 所检查的持久化 DB 和最新快照未发现不兼容前缀或无效映射；保留备份，继续常规升级验收 |
| 退出 2 | 发现旧数据、无效映射、活动锁、配置或 I/O 问题；根据路径和诊断处理后重查，不得继续升级 |
| 其他非零退出 | 启动器或 JVM 等检查未成功；同样按拒绝处理，不能当作干净结果 |

退出 0 不证明历史数据归属、备份完整或整个升级已经通过，也不授权合并新旧前缀。
遇到拒绝时按下述可信源恢复边界处理。详细命令契约见
[运行时升级指南](https://github.com/hugegraph/hugegraph/blob/fix/graphid-upgrade-guard/docs/graphid-upgrade.md)。

#### 升级与迁移

先停写并备份原集群的数据、元数据和 Raft 状态。未遇到 GraphID 拦截的数据无需为本问题迁移，完成常规升级验证后再恢复写入。

若启动报告 `FFFE`，停止升级并保留原始 DB、WAL、元数据和快照。首选从完整可信的 1.7 源，通过现有 HugeGraph-Tools 逻辑迁移到全新 1.8 集群，
目标数据由正常 GraphID 与 Raft 写入路径生成。需要时从升级前备份恢复隔离的 1.7 源；确认源视图完整、数据归属明确后再导出。
当前只配置了一个图，不能证明历史 `FFFE` 行都属于它。

以下示例适用于 `DEFAULT` 图空间，在空目标图中使用包含
[数据页导出失败修复](https://github.com/hugegraph/hugegraph-toolchain/pull/96) 的 Tools 构建，确保导出失败后不会继续恢复目标：

```bash
bin/hugegraph --url http://old-1.7:8080 --graph hugegraph \
  migrate --target-url http://new-1.8:8080 --target-graph hugegraph \
  --graph-mode RESTORING --directory /safe-backup/hugegraph \
  --huge-types all --keep-local-data
```

全程保持应用停写，导出不提供跨请求的一致性快照。`RESTORING` 保留空目标中的 Schema ID，`--keep-local-data` 保留逻辑备份；
当前命令使用默认图空间，不能直接套用于其他图空间。导出或恢复出现错误时不要切流，保留备份并改用全新空目标重试；失败目标可能残留部分数据及 `RESTORING` 模式。
成功退出和数量一致也不足以证明完整：需按已知基线核对顶点/边 ID、端点、属性、Schema、索引及业务查询，
并在目标快照、重启后复查；多副本部署还需验证 Follower 重建。验收后切换流量，保留源与备份；目标接受的新写入不在旧备份中。

若已升级并产生新 ID，当前源视图可能不完整，映射改回 `FFFE` 又可能隐藏新行。优先使用升级前备份；仅回滚 JAR 不会撤销已持久化的映射。
多个图可能共享旧前缀，物理 Key 无法证明归属，已覆盖或删除的值也不能凭空恢复。不要自动合并新旧前缀、将全部旧行归给一个图，或逐副本改写 RocksDB。
这些情况需要先依据备份和写入历史恢复数据。预检只负责检测和拒绝，不是自动迁移，也不表示受影响数据支持原地滚动升级。

详细机制见 [Store GraphID 升级说明](https://github.com/hugegraph/hugegraph/blob/fix/store-legacy-graph-prefix-preflight/docs/store-graphid-upgrade.md)。
