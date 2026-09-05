---
title: "HugeGraph-Store Quick Start"
linkTitle: "安装/构建 HugeGraph-Store"
weight: 3
search_keywords:
  - server.port
  - REST 端口
  - Store REST 端口
search_boost: 1.5
---

### 1 HugeGraph-Store 概述

HugeGraph-Store 是 HugeGraph 分布式版本的存储节点组件，负责实际存储和管理图数据。它与 HugeGraph-PD 协同工作，共同构成 HugeGraph 的分布式存储引擎，提供高可用性和水平扩展能力。

每个 Store 节点使用 RocksDB 保存图数据，并通过 Raft（JRaft）进行复制：每个分区是一个独立的 Raft 组，因此分区在丢失少数副本时仍可继续工作。Store 节点之间并不直接感知彼此，它们向 PD 注册，由 PD 下发分区分配，并通过心跳上报状态。HugeGraph-Server 先从 PD 查询分区位置，再通过 gRPC 访问 Store。

### 2 依赖

#### 2.1 前置条件

- 操作系统：Linux 或 macOS（Windows 尚未经过完整测试）
- Java 版本：≥ 11（编译期强制校验，`bin/start-hugegraph-store.sh` 启动时会再次检查）
- Maven 版本：≥ 3.5.0
- 如需进行多节点部署，请先部署 HugeGraph-PD

### 3 部署

有两种方式可以部署 HugeGraph-Store 组件：

- 方式 1：下载 tar 包
- 方式 2：源码编译

#### 3.1 下载 tar 包

从 Apache HugeGraph 官方下载页面下载最新版本的 HugeGraph-Store：

```bash
# 1.7.0 是项目孵化期发布的历史版本，因此文件名和目录名仍带 incubating
wget https://downloads.apache.org/hugegraph/1.7.0/apache-hugegraph-incubating-1.7.0.tar.gz
tar zxf apache-hugegraph-incubating-1.7.0.tar.gz
cd apache-hugegraph-incubating-1.7.0/apache-hugegraph-store-incubating-1.7.0
```

#### 3.2 源码编译

```bash
# 1. 克隆源代码
git clone https://github.com/apache/hugegraph.git

# 2. 编译项目
cd hugegraph
mvn clean install -DskipTests=true

# 3. 编译成功后，Store 目录和完整发布包分别位于
#    hugegraph-store/apache-hugegraph-store-{version}
#    target/apache-hugegraph-{version}.tar.gz
```

如果只想单独编译 Store 而不是整个仓库，需要先编译 `hugegraph-struct`，因为 Store 依赖它：

```bash
mvn install -pl hugegraph-struct -am -DskipTests
mvn clean package -pl hugegraph-store/hg-store-dist -am -DskipTests
```

生成的目录只包含 `bin/`、`conf/` 和 `lib/hg-store-node-{version}.jar`。

#### 3.3 Docker 部署

HugeGraph-Store Docker 镜像已发布在 Docker Hub，镜像名是 `hugegraph/store`。

> 注: 后续步骤皆假设你本地**已拉取** `hugegraph` 主仓库代码 (至少是 docker 目录)

有两个 compose 文件包含 Store：

| Compose 文件 | 拓扑 | 用途 |
|--------------|------|------|
| `docker-compose-hstore.yml` | 1 PD + 1 Store + 1 Server + 1 Hubble | 最小分布式部署 |
| `docker-compose-3pd-3store-3server.yml` | 3 PD + 3 Store + 3 Server + 1 Hubble | 多节点参考部署 |

```bash
cd hugegraph/docker
# 注意版本号请随时保持更新 → 1.x.0

# 最小分布式部署
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-hstore.yml up -d --wait

# 或者多节点集群
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-3pd-3store-3server.yml up -d
```

通过 `docker run` 运行单个 Store 节点：

```bash
docker run -d \
  -p 8520:8520 \
  -p 8500:8500 \
  -p 8510:8510 \
  -e HG_STORE_PD_ADDRESS=<pd-ip>:8686 \
  -e HG_STORE_GRPC_HOST=<your-ip> \
  -e HG_STORE_RAFT_ADDRESS=<your-ip>:8510 \
  -v /path/to/storage:/hugegraph-store/storage \
  --name hugegraph-store \
  hugegraph/store:1.7.0
```

**环境变量参考：**

| 变量 | 必填 | 默认值 | 对应配置项 | 描述 |
|------|------|--------|------------|------|
| `HG_STORE_PD_ADDRESS` | 是 | n/a | `pdserver.address` | PD gRPC 地址（如 `pd0:8686,pd1:8686,pd2:8686`） |
| `HG_STORE_GRPC_HOST` | 是 | n/a | `grpc.host` | 本节点的 gRPC 主机名/IP（如 `store0`） |
| `HG_STORE_RAFT_ADDRESS` | 是 | n/a | `raft.address` | 本节点的 Raft 地址（如 `store0:8510`） |
| `HG_STORE_GRPC_PORT` | 否 | `8500` | `grpc.port` | gRPC 服务端口 |
| `HG_STORE_REST_PORT` | 否 | `8520` | `server.port` | REST API 端口 |
| `HG_STORE_DATA_PATH` | 否 | `/hugegraph-store/storage` | `app.data-path` | 数据存储路径 |

入口脚本会把这些变量转换为 `SPRING_APPLICATION_JSON`，覆盖在 `conf/application.yml` 之上，然后执行 `bin/start-hugegraph-store.sh -d false -j "$JAVA_OPTS"`。上表未覆盖的配置项仍需要修改 `conf/application.yml`，或者自行提供 `SPRING_APPLICATION_JSON`。

镜像细节：

- `JAVA_OPTS` 默认值为 `-XX:+UnlockExperimentalVMOptions -XX:+UseContainerSupport -XX:MaxRAMPercentage=50 -XshowSettings:vm`
- `STDOUT_MODE=true`，因此 Java 日志输出到容器 stdout，而不是 `logs/hugegraph-store-server.log`
- `HEALTHCHECK` 在 90 秒启动期后每 15 秒访问一次 `GET http://localhost:8520/v1/health`
- 镜像只声明了 `EXPOSE 8520`；如果需要从 Docker 网络之外访问 8500 和 8510，请自行发布这两个端口

> **注意**：在 Docker 桥接网络中，`HG_STORE_GRPC_HOST` 应使用容器主机名（如 `store0`）而非 IP 地址。

> **已弃用的别名**：`PD_ADDRESS`、`GRPC_HOST`、`RAFT_ADDRESS` 仍可使用，但会输出弃用警告。新部署请使用 `HG_STORE_*` 名称。

### 4 配置

Store 从 `conf/` 读取两个配置文件：

- `application.yml`，主配置文件（PD 地址、各端口、Raft、数据路径）
- `application-pd.yml`，由 `application.yml` 中的 `spring.profiles.include: pd` 引入，包含 RocksDB 内存设置和 Actuator 暴露配置

#### 4.1 application.yml

发布包中自带的文件内容如下：

```yaml
pdserver:
  # PD service address, multiple PD addresses separated by commas
  address: localhost:8686

management:
  metrics:
    export:
      prometheus:
        enabled: true
  endpoints:
    web:
      exposure:
        include: "*"

grpc:
  # grpc service address
  host: 127.0.0.1
  port: 8500
  netty-server:
    max-inbound-message-size: 1000MB
raft:
  # raft cache queue size
  disruptorBufferSize: 1024
  address: 127.0.0.1:8510
  max-log-file-size: 600000000000
  # Snapshot generation interval, in seconds
  snapshotInterval: 1800
server:
  # rest service address
  port: 8520

app:
  # Storage path, support multiple paths, separated by commas
  data-path: ./storage
  #raft-path: ./storage

spring:
  application:
    name: store-node-grpc-server
  profiles:
    active: default
    include: pd

logging:
  config: 'file:./conf/log4j2.xml'
  level:
    root: info
```

#### 4.2 application-pd.yml

```yaml
management:
  metrics:
    export:
      prometheus:
        enabled: true
  endpoints:
    web:
      exposure:
        include: "*"

rocksdb:
  # rocksdb total memory usage, force flush to disk when reaching this value
  total_memory_size: 32000000000
  # memtable size used by rocksdb
  write_buffer_size: 32000000
  # For each rocksdb, the number of memtables reaches this value for writing to disk.
  min_write_buffer_number_to_merge: 16
```

#### 4.3 配置项参考

下表中「模板值」是上面两个文件中的取值，「代码默认值」是配置项缺失时节点使用的回退值；模板未列出的配置项应以代码默认值为准。

**核心**

| 配置项 | 模板值 | 代码默认值 | 说明 |
|--------|--------|------------|------|
| `pdserver.address` | `localhost:8686` | 必填 | PD gRPC 地址，多个地址用逗号分隔。Store 在此注册并获取分区分配。必须填写 PD 的 `grpc.port`，不是 PD 的 REST 端口。 |
| `grpc.host` | `127.0.0.1` | 必填 | 本节点对外公布的 gRPC 地址。应设置为可路由的 IP 或主机名，`127.0.0.1` 只适用于单机部署。 |
| `grpc.port` | `8500` | 必填 | gRPC 端口，Server 和 Store 客户端连接此端口。 |
| `grpc.netty-server.max-inbound-message-size` | `1000MB` | gRPC 默认值 | 单个入站 gRPC 消息的最大大小，由 `grpc-spring-boot-starter` 的 Netty 服务端读取。 |
| `grpc.server.wait-time` | 未设置 | `3600` | 扫描流等待客户端消费一页数据的秒数，超时后服务端中止该流。 |
| `server.port` | `8520` | 必填 | REST 和 Actuator 端口，同时以 `rest.port` 标签上报给 PD。 |

**Raft**

| 配置项 | 模板值 | 代码默认值 | 说明 |
|--------|--------|------------|------|
| `raft.address` | `127.0.0.1:8510` | 必填 | 本节点的 Raft 服务地址，格式为 `host:port`，必须能被其他 Store 节点访问。这里不需要配置 peer 列表：分区 Raft 组的成员由 PD 下发。 |
| `raft.disruptorBufferSize` | `1024` | `0` | Raft 任务队列大小。设为 `0` 时按 `rocksdb.total_memory_size` 推导：将该内存量的 GB 数取最接近的 2 的幂，再乘以 32。 |
| `raft.max-log-file-size` | `600000000000` | `50000000000` | Raft 日志的最大字节数。 |
| `raft.snapshotInterval` | `1800` | `300` | 生成 Raft 快照的时间间隔，单位秒。 |
| `raft.snapshotLogIndexMargin` | 未设置 | `0` | 距上次快照的最小 applied index 差值，达到后才真正生成快照。设为 `0` 关闭该判断。 |
| `raft.rpc-timeout` | 未设置 | `10000` | Raft RPC 超时时间，单位毫秒。 |
| `raft.metrics` | 未设置 | `true` | 采集 JRaft 节点指标，可通过 `/metrics/raft` 读取。 |
| `raft.useRocksDBSegmentLogStorage` | 未设置 | `true` | 使用 RocksDB 分段日志存储保存 Raft 日志。 |
| `raft.maxSegmentFileSize` | 未设置 | `67108864` | 分段日志文件大小，单位字节（64 MB）。 |
| `raft.maxReplicatorInflightMsgs` | 未设置 | `256` | 每个 follower 的最大在途复制请求数。 |
| `raft.maxEntriesSize` | 未设置 | `256` | 单次 `AppendEntries` 请求包含的最大条目数。 |
| `raft.maxBodySize` | 未设置 | `524288` | 单次 `AppendEntries` 请求的最大字节数。 |
| `ave-logEntry-size-ratio` | 未设置 | `0.95` | 估算日志条目平均大小时的平滑系数。注意该配置项位于顶层，不在 `raft` 下。 |

**存储与标签**

| 配置项 | 模板值 | 代码默认值 | 说明 |
|--------|--------|------------|------|
| `app.data-path` | `./storage` | `store` | RocksDB 数据目录。用逗号分隔多个路径可将分区分散到多块磁盘。 |
| `app.raft-path` | 已注释 | 空 | Raft 日志和快照目录。为空时回退到 `app.data-path`。 |
| `app.fake-pd` | 未设置 | `false` | 内置 PD 模式，仅用于单机测试，不要用于生产。 |
| `app.placeholder-size` | 未设置 | `10` | 启动时在每个数据路径下创建的 `placeholder` 占位文件大小，单位 GB，便于紧急情况下释放空间。设为 `0` 关闭。 |
| `app.label.<name>` | 未设置 | 无 | 随 store 心跳上报给 PD 的自定义键值标签。节点会自动追加 `rest.port`。 |

**RocksDB**

| 配置项 | 模板值 | 代码默认值 | 说明 |
|--------|--------|------------|------|
| `rocksdb.total_memory_size` | `32000000000` | `51539607552` | 本节点所有 RocksDB 实例共享的内存预算。缺失或为 `0` 时使用 JVM 最大堆内存。 |
| `rocksdb.write_buffer_size` | `32000000` | `33554432` | memtable 大小，单位字节。缺失或为 `0` 时取 `total_memory_size / 1000`。 |
| `rocksdb.min_write_buffer_number_to_merge` | `16` | `16` | 落盘前合并的 memtable 数量。 |
| `rocksdb.write_buffer_ratio` | 未设置 | `0.66` | `total_memory_size` 中分配给写缓存的比例，其余作为 block cache。 |

`org/apache/hugegraph/rocksdb/access/RocksDBOptions.java` 中定义的其他选项都可以加在同一个 `rocksdb:` 块下，例如 `rocksdb.max_background_jobs`、`rocksdb.level0_file_num_compaction_trigger` 或 `rocksdb.bloom_filter_bits_per_key`。

**线程池**

| 配置项 | 代码默认值 | 说明 |
|--------|------------|------|
| `thread.pool.grpc.core` | `600` | 处理 gRPC 请求的核心线程数。 |
| `thread.pool.grpc.max` | `1000` | gRPC 最大线程数。 |
| `thread.pool.grpc.queue` | `2147483647` | gRPC 任务队列容量。 |
| `thread.pool.scan.core` | `128` | 处理扫描的核心线程数。设为 `0` 时取 CPU 核数的 4 倍。 |
| `thread.pool.scan.max` | `1000` | 扫描最大线程数。 |
| `thread.pool.scan.queue` | `0` | 扫描任务队列容量。 |

**查询下推**

| 配置项 | 代码默认值 | 说明 |
|--------|------------|------|
| `query.push-down.threads` | `1500` | 下推查询的线程池大小。 |
| `query.push-down.fetch_batch` | `20000` | 单次请求拉取的行数。 |
| `query.push-down.fetch_timeout` | `300000` | 拉取超时时间，单位毫秒。 |
| `query.push-down.memory_limit_count` | `50000` | 排序等内存操作的行数上限。 |
| `query.push-down.index_size_limit_count` | `50000` | 索引 sst 文件大小上限，单位 kB。 |

**后台任务**

| 配置项 | 代码默认值 | 说明 |
|--------|------------|------|
| `job.interruptableThreadPool.core` | `128` | TTL 清理线程池的核心线程数。设为 `0` 时取 CPU 核数。 |
| `job.interruptableThreadPool.max` | `256` | TTL 清理线程池的最大线程数。设为 `0` 时取 CPU 核数的 4 倍。 |
| `job.interruptableThreadPool.queue` | `2147483647` | TTL 清理线程池的队列容量。 |
| `job.uninterruptibleThreadPool.core` | `0` | 存储引擎不可中断任务线程池的核心线程数。设为 `0` 时取 CPU 核数。 |
| `job.uninterruptibleThreadPool.max` | `256` | 不可中断任务线程池的最大线程数。 |
| `job.uninterruptibleThreadPool.queue` | `2147483647` | 不可中断任务线程池的队列容量。 |
| `job.cleaner.batch.size` | `10000` | TTL 清理任务每批删除的 key 数量。 |
| `job.start-time` | `0` | 每日 TTL 清理执行的小时数（0 到 23）。超出该范围时回退为 19。 |

**内置 PD 模式**

仅用于单机开发调试，通过 `app.fake-pd: true` 开启。此时节点自行扮演 PD 角色，并忽略 `pdserver.address`。

| 配置项 | 代码默认值 | 说明 |
|--------|------------|------|
| `fake-pd.store-list` | `''` | 伪集群中各 Store 节点的 gRPC 地址。 |
| `fake-pd.peers-list` | `''` | 同一批节点的 Raft 地址。 |
| `fake-pd.partition-count` | `3` | 分区数量。 |
| `fake-pd.shard-count` | `3` | 每个分区的副本数。 |

**诊断**

| 配置项 | 代码默认值 | 说明 |
|--------|------------|------|
| `arthas.telnetPort` | `8566` | 调用 `/v1/arthasstart` 后 Arthas 的 telnet 端口。 |
| `arthas.httpPort` | `8565` | Arthas HTTP 端口。 |
| `arthas.ip` | `0.0.0.0` | Arthas 监听地址。 |
| `arthas.disabledCommands` | `jad` | 需要禁用的 Arthas 命令。 |

#### 4.4 各节点需要区分的配置

对于多节点部署，需要为每个 Store 节点修改以下配置：

1. `grpc.host` 和 `grpc.port`（其他组件访问本节点的地址）
2. `raft.address`（Raft 协议地址）
3. `server.port`（REST 端口）
4. `app.data-path`（数据存储路径）

`pdserver.address` 在所有节点上保持一致，它列出的是整个 PD 集群。

### 5 启动与停止

#### 5.1 启动 Store

确保 PD 服务已经启动，然后在 Store 安装目录下执行：

```bash
./bin/start-hugegraph-store.sh
```

启动脚本支持四个参数：

| 参数 | 取值 | 默认值 | 说明 |
|------|------|--------|------|
| `-d` | `true`、`false` | `true` | 守护进程模式，见下文。 |
| `-g` | `ZGC`、`zgc` | 未设置 | 垃圾回收器。不传该参数即使用默认的 G1。除 `ZGC` 和 `zgc` 之外的任何取值都会直接退出，包括 `g1`，尽管脚本自身的用法提示里写了它。 |
| `-j` | JVM 参数字符串 | 空 | 附加的 JVM 参数，例如 `-j "-Xmx16g -Xms8g"`。 |
| `-y` | `true`、`false` | `false` | 挂载 OpenTelemetry Java agent（首次使用时下载到 `plugins/`），并将 trace 导出到 `127.0.0.1:4317`。 |

守护进程模式：

- `-d true`（默认）：以后台守护进程方式运行，脚本立即返回，并把 Java 进程号写入 `bin/pid`。
- `-d false`：以前台模式运行，脚本通过 `exec` 替换为 Java 进程，容器或进程管理器的进程即为 Java 本身。在 Docker 或进程管理器（systemd、supervisord）下运行时请使用此参数，以便在崩溃时自动检测并重启服务。

JVM 内存方面，如果没有自行设置 `JAVA_OPTIONS`：`-Xms512m`，`-Xmx` 取空闲内存的一半并限制在 512 MB 到 2048 MB 之间。脚本还会加上 `-XX:MetaspaceSize=256M`、OOM 时把堆转储写入 `logs/`，以及滚动的 GC 日志 `logs/gc.log`。生产节点通常需要大得多的堆，请显式指定，例如 `-j "-Xmx32g -Xms32g"`。

当 `ulimit -n` 或 `ulimit -u` 低于 1024 时脚本会拒绝启动；在 x86_64 和 arm64 上，如果能成功下载并校验对应的动态库，脚本会预加载 jemalloc。

启动成功后，可以在 `logs/hugegraph-store-server.log` 中看到类似以下的日志：

```
YYYY-mm-dd xx:xx:xx [main] [INFO] o.a.h.s.n.StoreNodeApplication - Started StoreNodeApplication in x.xxx seconds (JVM running for x.xxx)
```

#### 5.2 停止 Store

在 Store 安装目录下执行：

```bash
./bin/stop-hugegraph-store.sh
```

脚本读取 `bin/pid`，向该进程发送信号，最多等待 30 秒直至进程退出，然后删除 pid 文件。如果 `bin/pid` 不存在，脚本直接退出且不做任何操作。

#### 5.3 重启 Store

```bash
./bin/restart-hugegraph-store.sh
```

该脚本依次 source 停止脚本和启动脚本，并转发 5.1 中的参数。

#### 5.4 启动顺序

1. **先启动 PD**。每个 Store 的 `grpc.host:grpc.port` 都应出现在 PD 的 `pd.initial-store-list` 中，否则 PD 只会把该节点登记为 `Pending` 而不会置为 `Up`，分区分配也就无法完成。
2. **再启动 Store**。Store 早于 PD 启动并不致命：心跳线程会持续重试注册，并在 PD 可用之前打印 `store heartbeat error: PD UNREACHABLE`。
3. **最后启动 HugeGraph-Server**，此时所有 Store 节点都应上报 `state: "Up"`。Server 需要分区就绪之后才能初始化或打开图。

compose 文件用 `depends_on: condition: service_healthy` 表达同样的顺序：Store 等待所有 PD 健康检查通过，Server 等待所有 Store 健康检查通过。

### 6 多节点部署示例

以下是一个三节点部署的配置示例：

#### 6.1 三节点配置参考

- 3 PD 节点
  - raft 端口：8610, 8611, 8612
  - rpc 端口：8686, 8687, 8688
  - rest 端口：8620, 8621, 8622
- 3 Store 节点
  - raft 端口：8510, 8511, 8512
  - rpc 端口：8500, 8501, 8502
  - rest 端口：8520, 8521, 8522

#### 6.2 Store 节点配置

对于三个 Store 节点，每个节点的主要配置差异如下：

节点 A：
```yaml
grpc:
  port: 8500
raft:
  address: 127.0.0.1:8510
server:
  port: 8520
app:
  data-path: ./storage-a
```

节点 B：
```yaml
grpc:
  port: 8501
raft:
  address: 127.0.0.1:8511
server:
  port: 8521
app:
  data-path: ./storage-b
```

节点 C：
```yaml
grpc:
  port: 8502
raft:
  address: 127.0.0.1:8512
server:
  port: 8522
app:
  data-path: ./storage-c
```

所有节点都应该指向相同的 PD 集群：
```yaml
pdserver:
  address: 127.0.0.1:8686,127.0.0.1:8687,127.0.0.1:8688
```

同时每个 PD 节点都应列出三个 Store 的 gRPC 地址：
```yaml
pd:
  initial-store-list: 127.0.0.1:8500,127.0.0.1:8501,127.0.0.1:8502
```

#### 6.3 Docker 分布式集群配置

3 节点 Store 集群包含在 `docker/docker-compose-3pd-3store-3server.yml` 中。每个 Store 节点拥有独立的主机名和环境变量：

```yaml
# store0，宿主机端口 8500（gRPC）、8510（Raft）、8520（REST）
HG_STORE_PD_ADDRESS: pd0:8686,pd1:8686,pd2:8686
HG_STORE_GRPC_HOST: store0
HG_STORE_GRPC_PORT: "8500"
HG_STORE_REST_PORT: "8520"
HG_STORE_RAFT_ADDRESS: store0:8510
HG_STORE_DATA_PATH: /hugegraph-store/storage

# store1，宿主机端口 8501、8511、8521
HG_STORE_GRPC_HOST: store1
HG_STORE_RAFT_ADDRESS: store1:8510

# store2，宿主机端口 8502、8512、8522
HG_STORE_GRPC_HOST: store2
HG_STORE_RAFT_ADDRESS: store2:8510
```

每个节点的容器内端口都是 8500/8510/8520，只有映射到宿主机的端口不同。PD 节点相应地设置 `HG_PD_INITIAL_STORE_LIST: store0:8500,store1:8500,store2:8500`。

Store 节点仅在所有 PD 节点通过健康检查后才会启动，其中 docker-compose 中的 healthcheck 实际访问的是 PD 的 REST 接口 `/v1/health`（也可以通过 Actuator 暴露的 `/actuator/health` 进行手动检查），并通过 `depends_on: condition: service_healthy` 强制执行依赖关系。

运行时日志可通过 `docker logs <container-name>`（如 `docker logs hg-store0`）直接查看，无需进入容器。

完整的部署指南请参阅 [docker/README.md](https://github.com/apache/hugegraph/blob/master/docker/README.md)。

### 7 验证 Store 服务

确认 Store 服务是否正常运行：

```bash
curl http://localhost:8520/actuator/health
```

如果返回 `{"status":"UP"}`，则表示 Store 服务已成功启动。

`GET /v1/health` 是 Docker 镜像和 compose 文件使用的轻量检查接口，它返回 HTTP 200 且响应体为空，因此应使用 `curl -fsS` 并检查退出码，而不是检查输出内容：

```bash
curl -fsS http://localhost:8520/v1/health && echo OK
```

#### 7.1 Store REST 接口

Store 节点在 `server.port` 上提供以下只读接口：

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/v1/health` | 存活探测，HTTP 200 且响应体为空 |
| GET | `/actuator/health` | Spring Boot Actuator 健康检查，返回 `{"status":"UP"}` |
| GET | `/actuator/prometheus` | Prometheus 抓取接口 |
| GET | `/` | 节点概览，包含 `leaderCount` 和 `partitionCount` |
| GET | `/-/state` | 节点状态，取值为 `STARTING`、`ONLINE`、`STOPPING` |
| GET | `/-/echo?name=<text>` | 回显检查 |
| GET | `/-/scan` | 当前扫描流的状态 |
| GET | `/v1/partitions` | 本节点上的所有 Raft 组及分区指标。加上 `?flags=accurate` 可获取精确的 key 数量，但更慢。 |
| GET | `/v1/partition/{id}` | 按分区 id 查询单个 Raft 组，包含角色、leader、peers 和已提交索引 |
| GET | `/metrics/system` | 主机 CPU 和内存指标 |
| GET | `/metrics/drive` | 数据路径所在磁盘的指标 |
| GET | `/metrics/raft` | JRaft 节点指标，需要 `raft.metrics: true` |

Actuator 和 Prometheus 之所以可访问，是因为自带配置设置了 `management.endpoints.web.exposure.include: "*"` 和 `management.metrics.export.prometheus.enabled: true`。

节点还提供一批会修改状态或执行重负载操作的运维接口：`PUT /-/state`、`GET /-/cleaner`、`GET /v1/partition/dump/{id}`、`GET /v1/partition/clean/{id}`、`POST /v1/compat?id=<partition>`、`GET /v1/arthasstart`、`POST /raft/options`，以及 `/fix/*` 和 `/test/*` 两组接口。请仅在排查问题时使用，并且不要把 REST 端口暴露到不可信网络。

#### 7.2 通过 PD 检查注册结果

也可以通过 PD API 查看集群中的 Store 节点状态：

```bash
curl -u store:admin http://localhost:8620/v1/stores
```

PD 的 REST 端口默认开启 basic 认证：用户名必须是 `hg`、`store`、`hubble`、`vermeer` 之一，密码目前还不校验。不带凭据的请求会返回 `{"status":-1,"error":"Unauthorized!"}`。只有 `/v1/health`、`/actuator/*` 和 `/v1/prom/targets/*` 不需要认证。

如果 Store 配置成功，上述接口响应中应包含当前节点的状态信息，其中 `state` 为 `Up` 表示节点运行正常。如果节点长期停留在 `Pending`，通常是因为它没有出现在 PD 的 `pd.initial-store-list` 中。

下方示例仅展示 1 个 Store 节点的返回结果。如果 3 个节点都已正确配置并正在运行，则响应中的 `storeId` 列表应包含 3 个 ID，且 `stateCountMap.Up`、`numOfService` 和 `numOfNormalService` 都应为 `3`。
```javascript
{
  "message": "OK",
  "data": {
    "stores": [
      {
        "storeId": 8319292642220586694,
        "address": "127.0.0.1:8500",
        "raftAddress": "127.0.0.1:8510",
        "version": "",
        "state": "Up",
        "deployPath": "/Users/{your_user_name}/hugegraph/hugegraph-store/apache-hugegraph-store-{version}/lib/hg-store-node-{version}.jar",
        "dataPath": "./storage",
        "startTimeStamp": 1754027127969,
        "registedTimeStamp": 1754027127969,
        "lastHeartBeat": 1754027909444,
        "capacity": 494384795648,
        "available": 346535829504,
        "partitionCount": 0,
        "graphSize": 0,
        "keyCount": 0,
        "leaderCount": 0,
        "serviceName": "127.0.0.1:8500-store",
        "serviceVersion": "",
        "serviceCreatedTimeStamp": 1754027127000,
        "partitions": []
      }
    ],
    "stateCountMap": {
      "Up": 1
    },
    "numOfService": 1,
    "numOfNormalService": 1
  },
  "status": 0
}
```
