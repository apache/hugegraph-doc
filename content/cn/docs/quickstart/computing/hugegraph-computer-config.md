---
title: "HugeGraph-Computer 配置参考"
linkTitle: "Computer 配置参考"
weight: 3
---

## Computer 配置选项

表格中的默认值来自 `computer-api` 模块的 `ComputerOptions.java`；发行包的 `conf/computer.properties` 显式设置的值以“代码默认值（发行包：实际值）”标注。`rpc.*` 等通用配置由 HugeGraph Commons 提供，以下会单独标出发行包实际值。

### 配置文件从哪里来

- 源码模板：[`computer/computer-dist/src/assembly/static/conf/computer.properties`](https://github.com/apache/hugegraph-computer/blob/1.7.0/computer/computer-dist/src/assembly/static/conf/computer.properties)；日志配置模板为同目录的 `log4j2.xml`。Maven `package` 阶段将模板复制进发行目录的 `conf/`，并将运行依赖和内置算法 JAR 装入 `lib/`、`algorithm/`。模板由源码维护，没有单独的配置生成命令。
- 单机、YARN：启动脚本默认读取发行目录的 `conf/computer.properties`，可使用 `bin/start-computer.sh -c <配置文件路径>` 覆盖；master 和 worker 应读到同一组作业参数。
- Kubernetes Operator：用户在 CRD 的 `spec.computerConf` 中提供键值；Operator 将它写成 ConfigMap，挂载为容器内的 `computer.properties`。Operator 会补入作业 ID、worker 数量、Pod 地址和未指定时的 etcd 地址，并在未指定或设为 `0` 时将数据传输端口设为 `8099`、master RPC 端口设为 `8190`。`transport.server_host` 与 `rpc.server_host` 会被设置为 Pod IP。作业容器启动脚本只对 `${POD_IP}`、`${HOSTNAME}`、`${POD_NAME}`、`${POD_NAMESPACE}` 做环境变量替换。
- Kubernetes 作业镜像必须包含 Computer 运行时及所需算法 JAR；CRD 的 `jarFile` 可指向镜像内 JAR，`remoteJarUri` 可让启动脚本从 HTTP(S) 地址下载算法 JAR。示例与字段见[Computer 快速开始](/cn/docs/quickstart/computing/hugegraph-computer/)及下方 CRD 表。

Apache 1.7.0 下载目录中的独立 Computer 包是源码归档 `apache-hugegraph-computer-incubating-1.7.0-src.tar.gz`。从源码构建时，在仓库的 `computer/` Maven 聚合工程目录运行 `mvn clean package -DskipTests`；发行包位于该目录下的 `target/apache-hugegraph-computer-1.7.0.tar.gz`，解压后发行目录也位于 `computer/` 下。不要把 `-src.tar.gz` 当作可直接启动的二进制发行包。

---

### 1. 基础配置

HugeGraph-Computer 核心作业设置。

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| hugegraph.url | http://127.0.0.1:8080 | HugeGraph 服务器 URL,用于加载数据和写回结果。 |
| hugegraph.name | hugegraph | 图名称,用于加载数据和写回结果。 |
| hugegraph.username | "" (空) | HugeGraph 认证用户名(如果未启用认证则留空)。 |
| hugegraph.password | "" (空) | HugeGraph 认证密码(如果未启用认证则留空)。 |
| job.id | local_0001 (打包: local_001) | YARN 集群或 K8s 集群上的作业标识符。 |
| job.namespace | "" (空) | 可选的 etcd 作业键名前缀，可用于隔离不同命名空间；它不是 Kubernetes metadata.namespace，Operator 不会自动填入。 |
| job.workers_count | 1 | 执行一个图算法作业的 Worker 数量。在 K8s 中由 Operator 设置。 |
| job.partitions_count | 1 | 执行一个图算法作业的分区数量。 |
| job.partitions_thread_nums | 4 | 分区并行计算的线程数量。 |

---

### 2. 算法配置

计算逻辑的算法特定配置。

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| algorithm.params_class | `ComputerOptions.Null` 占位类 | 必填。用于在算法运行前传递算法参数的类。 |
| algorithm.result_class | `ComputerOptions.Null` 占位类 | 顶点值的类，用于存储顶点的计算结果。 |
| algorithm.message_class | `ComputerOptions.Null` 占位类 | 计算顶点时传递的消息类。 |

---

### 3. 输入配置

从 HugeGraph 或其他数据源加载输入数据的配置。

#### 3.1 输入源

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| input.source_type | hugegraph-server | 加载输入数据的源类型,允许值:['hugegraph-server', 'hugegraph-loader']。'hugegraph-loader' 表示使用 hugegraph-loader 从 HDFS 或文件加载数据。如果使用 'hugegraph-loader',请配置 'input.loader_struct_path' 和 'input.loader_schema_path'。 |
| input.loader_struct_path | "" (空) | Loader 输入的结构路径，仅在 `input.source_type=hugegraph-loader` 时生效。 |
| input.loader_schema_path | "" (空) | Loader 输入的 Schema 路径，仅在 `input.source_type=hugegraph-loader` 时生效。 |

#### 3.2 输入分片

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| input.split_size | 1048576 (1 MB) | 输入分片大小(字节)。 |
| input.split_max_splits | 10000000 | 最大输入分片数量。 |
| input.split_page_size | 500 | 流式加载输入分片数据的页面大小。 |
| input.split_fetch_timeout | 300 | 获取输入分片的超时时间(秒)。 |

#### 3.3 输入处理

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| input.filter_class | org.apache.hugegraph.computer.core.input.filter.DefaultInputFilter | 创建输入过滤器对象的类。输入过滤器用于根据用户需求过滤顶点边。 |
| input.edge_direction | OUT | 要加载的边的方向,允许值:[OUT, IN, BOTH]。当值为 BOTH 时,将加载 OUT 和 IN 两个方向的边。 |
| input.edge_freq | MULTIPLE | 一对顶点之间可以存在的边的频率,允许值:[SINGLE, SINGLE_PER_LABEL, MULTIPLE]。SINGLE 表示一对顶点之间只能存在一条边(通过 sourceId + targetId 标识);SINGLE_PER_LABEL 表示每个边标签在一对顶点之间可以有一条边(通过 sourceId + edgeLabel + targetId 标识);MULTIPLE 表示一对顶点之间可以存在多条边(通过 sourceId + edgeLabel + sortValues + targetId 标识)。 |
| input.max_edges_in_one_vertex | 200 | 允许附加到一个顶点的最大邻接边数量。邻接边将作为一个批处理单元一起存储和传输。 |

#### 3.4 输入性能

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| input.send_thread_nums | 4 | 并行发送顶点或边的线程数量。 |

---

### 4. 快照与存储配置

HugeGraph-Computer 支持快照功能,可将顶点/边分区保存到本地存储或 MinIO 对象存储,用于断点恢复或加速重复计算。

#### 4.1 基础快照配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| snapshot.write | false | 是否写入输入顶点/边分区的快照。 |
| snapshot.load | false | 是否从顶点/边分区的快照加载。 |
| snapshot.name | "" (空) | 用户自定义的快照名称,用于区分不同的快照。 |

#### 4.2 MinIO 集成(可选)

MinIO 可用作 K8s 部署中快照的分布式对象存储后端。

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| snapshot.minio_endpoint | "" (空) | MinIO 服务端点(例如 `http://minio:9000`)。使用 MinIO 时必填。 |
| snapshot.minio_access_key | minioadmin | MinIO 认证访问密钥。 |
| snapshot.minio_secret_key | minioadmin | MinIO 认证密钥。 |
| snapshot.minio_bucket_name | "" (空) | 用于存储快照数据的 MinIO 存储桶名称。 |

**使用场景:**
- **断点恢复**:作业失败后从快照恢复,避免重新加载数据
- **重复计算**:多次运行同一算法时从快照加载数据以加速启动
- **A/B 测试**:保存同一数据集的多个快照版本,测试不同的算法参数

**示例:本地快照**(在 `computer.properties` 中):
```properties
snapshot.write=true
snapshot.name=pagerank-snapshot-20260201
```

**示例:MinIO 快照**(在 K8s CRD `computerConf` 中):
```yaml
computerConf:
  snapshot.write: "true"
  snapshot.name: "pagerank-snapshot-v1"
  snapshot.minio_endpoint: "http://minio:9000"
  snapshot.minio_access_key: "my-access-key"
  snapshot.minio_secret_key: "my-secret-key"
  snapshot.minio_bucket_name: "hugegraph-snapshots"
```

---

### 5. Worker 与 Master 配置

Worker 和 Master 计算逻辑的配置。

#### 5.1 Master 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| master.computation_class | org.apache.hugegraph.computer.core.master.DefaultMasterComputation | Master 计算是可以决定是否继续下一个超步的计算。它在每个超步结束时在 master 上运行。 |

#### 5.2 Worker 计算

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| worker.computation_class | org.apache.hugegraph.computer.core.config.Null | 创建 worker 计算对象的类。Worker 计算用于在每个超步中计算每个顶点。 |
| worker.combiner_class | org.apache.hugegraph.computer.core.config.Null | Combiner 可以将消息组合为一个顶点的一个值。例如,PageRank 算法可以将一个顶点的消息组合为一个求和值。 |
| worker.partitioner | org.apache.hugegraph.computer.core.graph.partition.HashPartitioner | 分区器,决定顶点应该在哪个分区中,以及分区应该在哪个 worker 中。 |

#### 5.3 Worker 组合器

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| worker.vertex_properties_combiner_class | org.apache.hugegraph.computer.core.combiner.OverwritePropertiesCombiner | 组合器可以在输入步骤将同一顶点的多个属性组合为一个属性。 |
| worker.edge_properties_combiner_class | org.apache.hugegraph.computer.core.combiner.OverwritePropertiesCombiner | 组合器可以在输入步骤将同一边的多个属性组合为一个属性。 |

#### 5.4 Worker 缓冲区

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| worker.received_buffers_bytes_limit | 104857600 (100 MB) | 接收数据缓冲区的限制字节数。所有缓冲区的总大小不能超过此限制。如果接收缓冲区达到此限制,它们将被合并到文件中(溢出到磁盘)。 |
| worker.write_buffer_capacity | 52428800 (50 MB) | 用于存储顶点或消息的写缓冲区的初始大小。 |
| worker.write_buffer_threshold | 52428800 (50 MB) | 写缓冲区的阈值。超过它将触发排序。写缓冲区用于存储顶点或消息。 |

#### 5.5 Worker 数据与超时

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| worker.data_dirs | [jobs] | 用逗号分隔的目录,接收的顶点和消息可以持久化到其中。 |
| worker.wait_sort_timeout | 600000 (10 分钟) | 消息处理程序等待排序线程对一批缓冲区进行排序的最大超时时间(毫秒)。 |
| worker.wait_finish_messages_timeout | 86400000 (24 小时) | 消息处理程序等待所有 worker 完成消息的最大超时时间(毫秒)。 |

---

### 6. I/O 与输出配置

输出计算结果的配置。

#### 6.1 输出类与结果

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| output.output_class | org.apache.hugegraph.computer.core.output.LogOutput | 输出每个顶点计算结果的类。在迭代计算后调用。 |
| output.result_name | value | 该值由 WORKER_COMPUTATION_CLASS 创建的实例的 #name() 动态分配。 |
| output.result_write_type | OLAP_COMMON | 输出到 HugeGraph 的结果写入类型,允许值:[OLAP_COMMON, OLAP_SECONDARY, OLAP_RANGE]。 |

#### 6.2 输出行为

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| output.with_adjacent_edges | false | 是否输出顶点的邻接边。 |
| output.with_vertex_properties | false | 是否输出顶点的属性。 |
| output.with_edge_properties | false | 是否输出边的属性。 |

#### 6.3 批量输出

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| output.batch_size | 500 | 输出的批处理大小。 |
| output.batch_threads | 1 | 用于批量输出的线程数量。 |
| output.single_threads | 1 | 用于单个输出的线程数量。 |

#### 6.4 HDFS 输出

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| output.hdfs_url | hdfs://127.0.0.1:9000 | 输出的 HDFS URL。 |
| output.hdfs_user | hadoop | 输出的 HDFS 用户。 |
| output.hdfs_path_prefix | /hugegraph-computer/results | HDFS 输出结果的目录。 |
| output.hdfs_delimiter | , (逗号) | HDFS 输出的分隔符。 |
| output.hdfs_merge_partitions | true | 是否合并多个分区的输出文件。 |
| output.hdfs_replication | 3 | HDFS 的副本数。 |
| output.hdfs_core_site_path | "" (空) | HDFS core site 路径。 |
| output.hdfs_site_path | "" (空) | HDFS site 路径。 |
| output.hdfs_kerberos_enable | false | 是否为 HDFS 启用 Kerberos 认证。 |
| output.hdfs_kerberos_principal | "" (空) | HDFS 的 Kerberos 认证 principal。 |
| output.hdfs_kerberos_keytab | "" (空) | HDFS 的 Kerberos 认证 keytab 文件。 |
| output.hdfs_krb5_conf | /etc/krb5.conf | Kerberos 配置文件路径。 |

#### 6.5 重试与超时

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| output.retry_times | 3 | 输出失败时的重试次数。 |
| output.retry_interval | 10 | 输出失败时的重试间隔(秒)。 |
| output.thread_pool_shutdown_timeout | 60 | 输出线程池关闭的超时时间(秒)。 |

---

### 7. 网络与传输配置

Worker 和 Master 之间网络通信的配置。

#### 7.1 服务器配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| transport.server_host | 127.0.0.1 | worker 数据服务监听并向其他 worker 公告的地址。多主机场景必须使用其他节点可达的地址；Operator 会改为 Pod IP。 |
| transport.server_port | 0（发行包：0；K8s Operator：8099） | worker 数据传输监听端口。单机值 `0` 表示系统分配端口；Operator 会将 K8s 默认值改为固定端口 `8099`，以便 Pod 间通信。 |
| transport.server_threads | 4 | 服务器传输线程的数量。 |

#### 7.2 客户端配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| transport.client_threads | 4 | 客户端传输线程的数量。 |
| transport.client_connect_timeout | 3000 | 客户端连接到服务器的超时时间(毫秒)。 |

#### 7.3 协议配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| transport.provider_class | org.apache.hugegraph.computer.core.network.netty.NettyTransportProvider | 传输提供程序,目前仅支持 Netty。 |
| transport.io_mode | AUTO | 网络 IO 模式,允许值:[NIO, EPOLL, AUTO]。AUTO 表示自动选择适当的模式。 |
| transport.tcp_keep_alive | true | 是否启用 TCP keep-alive。 |
| transport.transport_epoll_lt | false | 是否启用 EPOLL 水平触发(仅在 io_mode=EPOLL 时有效)。 |

#### 7.4 缓冲区配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| transport.send_buffer_size | 0 | Socket 发送缓冲区大小(字节)。0 表示使用系统默认值。 |
| transport.receive_buffer_size | 0 | Socket 接收缓冲区大小(字节)。0 表示使用系统默认值。 |
| transport.write_buffer_high_mark | 67108864 (64 MB) | 写缓冲区的高水位标记(字节)。如果排队字节数 > write_buffer_high_mark,将触发发送不可用。 |
| transport.write_buffer_low_mark | 33554432 (32 MB) | 写缓冲区的低水位标记(字节)。如果排队字节数 < write_buffer_low_mark,将触发发送可用。 |

#### 7.5 流量控制

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| transport.max_pending_requests | 8 | 客户端未接收 ACK 的最大数量。如果未接收 ACK 的数量 >= max_pending_requests,将触发发送不可用。 |
| transport.min_pending_requests | 6 | 客户端未接收 ACK 的最小数量。如果未接收 ACK 的数量 < min_pending_requests,将触发发送可用。 |
| transport.min_ack_interval | 200 | 服务器回复 ACK 的最小间隔(毫秒)。 |

#### 7.6 超时配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| transport.close_timeout | 10000 | 关闭服务器或关闭客户端的超时时间(毫秒)。 |
| transport.sync_request_timeout | 10000 | 发送同步请求后等待响应的超时时间(毫秒)。 |
| transport.finish_session_timeout | 0 | 完成会话的超时时间(毫秒)。0 表示使用 (transport.sync_request_timeout × transport.max_pending_requests)。 |
| transport.write_socket_timeout | 3000 | 将数据写入 socket 缓冲区的超时时间(毫秒)。 |
| transport.server_idle_timeout | 360000 (6 分钟) | 服务器空闲的最大超时时间(毫秒)。 |

#### 7.7 心跳配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| transport.heartbeat_interval | 20000 (20 秒) | 客户端心跳之间的最小间隔(毫秒)。 |
| transport.max_timeout_heartbeat_count | 120 | 客户端超时心跳的最大次数。如果连续等待心跳响应超时的次数 > max_timeout_heartbeat_count,通道将从客户端关闭。 |

#### 7.8 高级网络设置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| transport.max_syn_backlog | 511 | 服务器端 SYN 队列的容量。0 表示使用系统默认值。 |
| transport.recv_file_mode | true | 是否启用接收缓冲文件模式。如果启用,将使用零拷贝从 socket 接收缓冲区并写入文件。**注意**:需要操作系统支持零拷贝(例如 Linux sendfile/splice)。 |
| transport.network_retries | 3 | 网络通信不稳定时的重试次数。 |

#### 7.9 Master RPC 配置

以下两个键由 HugeGraph Commons 的 RPC 配置定义；`computer.properties` 发行模板显式设置了主机和端口。Kubernetes Operator 会公告 Pod IP，并在未指定有效端口时使用 `8190`。

| 配置项 | 发行包值 | 说明 |
|--------|----------|------|
| rpc.server_host | 127.0.0.1（K8s：Pod IP） | Master RPC 服务地址，worker 必须能访问此地址。 |
| rpc.server_port | 8190（K8s 默认：8190） | Master RPC 监听端口；集群安全组和网络策略须允许 worker 连接。 |

---

### 8. 存储与持久化配置

HGKV(HugeGraph Key-Value)存储引擎和值文件的配置。

#### 8.1 HGKV 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| hgkv.max_file_size | 2147483648 (2 GB) | 每个 HGKV 文件的最大字节数。 |
| hgkv.max_data_block_size | 65536 (64 KB) | HGKV 文件数据块的最大字节大小。 |
| hgkv.max_merge_files | 10 | 一次合并的最大文件数。 |
| hgkv.temp_file_dir | /tmp/hgkv | 此文件夹用于在文件合并过程中存储临时文件。 |

#### 8.2 值文件配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| valuefile.max_segment_size | 1073741824 (1 GB) | 值文件每个段的最大字节数。 |

---

### 9. BSP 与协调配置

批量同步并行(BSP)协议和 etcd 协调的配置。

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| bsp.etcd_endpoints | http://localhost:2379（发行包：http://127.0.0.1:2379） | etcd 客户端端点；多个地址用逗号分隔。K8s Operator 在未由 `computerConf` 指定时使用 Operator 的 `INTERNAL_ETCD_URL`。 |
| bsp.max_super_step | 10 (打包: 2) | 算法的最大超步数。 |
| bsp.register_timeout | 300000 (打包: 100000) | 等待 master 和 worker 注册的最大超时时间(毫秒)。 |
| bsp.wait_workers_timeout | 86400000 (24 小时) | 等待 worker BSP 事件的最大超时时间(毫秒)。 |
| bsp.wait_master_timeout | 86400000 (24 小时) | 等待 master BSP 事件的最大超时时间(毫秒)。 |
| bsp.log_interval | 30000 (30 秒) | 等待 BSP 事件时打印日志的日志间隔(毫秒)。 |

---

### 10. 性能调优配置

性能优化的配置。

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| allocator.max_vertices_per_thread | 10000 | 每个内存分配器中每个线程处理的最大顶点数。 |
| sort.thread_nums | 4 | 执行内部排序的线程数量。 |

---

### 11. 系统管理配置

以下配置在 Kubernetes 作业中由 Operator 自动补齐或覆盖。除非自定义了 Operator 或网络，不应手动覆盖这些值；`job.namespace` 是可选的用户配置，见基础配置表。

| 配置项 | 管理者 | 说明 |
|--------|--------|------|
| bsp.etcd_endpoints | K8s Operator | 仅在 `computerConf` 未设置时，取 Operator 的 `INTERNAL_ETCD_URL`。 |
| transport.server_host | K8s Operator | 覆盖为 Pod IP；worker 需要互相访问。 |
| transport.server_port | K8s Operator | 未设置或为 `0` 时设置为 `8099`，不是随机端口。 |
| job.id | K8s Operator | 自动从 CRD 设置为作业 ID |
| job.workers_count | K8s Operator | 自动从 CRD `workerInstances` 设置 |
| rpc.server_host | K8s Operator | 覆盖为 master Pod IP。 |
| rpc.server_port | K8s Operator | 未设置或为 `0` 时设置为 `8190`。 |
| rpc.remote_url | Computer 启动流程 | 读取配置时会移除该项，不应作为作业配置设置。 |

**为什么禁止修改:**
- **BSP/RPC 配置**:必须与实际部署的 etcd/RPC 服务匹配。手动覆盖会破坏协调。
- **作业配置**:必须与 K8s CRD 规范匹配。不匹配会导致 worker 数量错误。
- **传输配置**:必须使用 worker 互相可达的 Pod IP 和端口；K8s 的默认端口为 `8099`。

---

### K8s Operator 配置选项

> 注意:选项需要通过环境变量设置进行转换,例如 k8s.internal_etcd_url => INTERNAL_ETCD_URL

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| k8s.auto_destroy_pod | true | 作业完成或失败后是否删除作业 CR；CR 删除后 Operator 会清理关联计算资源。 |
| k8s.close_reconciler_timeout | 120 | 关闭 reconciler 的最大超时时间(毫秒)。 |
| k8s.internal_etcd_url | 代码默认 `http://127.0.0.1:2379`；发行清单覆盖为 `http://hugegraph-computer-operator-etcd.hugegraph-computer-operator-system:2379` | Operator 作业使用的 etcd URL。使用随附清单时实际值是 etcd Service 地址。 |
| k8s.internal_minio_url | 代码默认 `http://127.0.0.1:9000`；发行清单覆盖为 `http://hugegraph-computer-operator-minio.hugegraph-computer-operator-system:9000` | Operator 为作业补入的 MinIO 地址；仅启用 MinIO 快照时需要。 |
| k8s.max_reconcile_retry | 3 | reconcile 的最大重试次数。 |
| k8s.probe_backlog | 50 | 服务健康探针的最大积压。 |
| k8s.probe_port | 9892 | controller 绑定的用于服务健康探针的端口。 |
| k8s.ready_check_internal | 1000 | 检查就绪的时间间隔(毫秒)。 |
| k8s.ready_timeout | 30000 | 检查就绪的最大超时时间(毫秒)。 |
| k8s.reconciler_count | 代码默认 `Runtime.getRuntime().availableProcessors()`；发行清单覆盖为 `6` | reconciler 线程的最大数量。 |
| k8s.resync_period | 600000 | 被监视资源进行 reconcile 的最小频率。 |
| k8s.timezone | Asia/Shanghai | computer 作业和 operator 的时区。 |
| k8s.watch_namespace | hugegraph-computer-operator-system | 监视自定义资源的命名空间。随附发行清单也设置为此值；使用 `*` 可监视所有命名空间。 |

---

### HugeGraph-Computer CRD

> CRD: https://github.com/apache/hugegraph-computer/blob/1.7.0/computer/computer-k8s-operator/manifest/hugegraph-computer-crd.v1.yaml

| 字段 | 默认值 | 说明 | 必填 |
|------|--------|------|------|
| algorithmName | | 算法名称。 | true |
| jobId | | 作业 ID。 | true |
| image | | Computer 作业使用的容器镜像；需包含运行时及目标算法 JAR，或配合 `remoteJarUri` 提供算法 JAR。 | true |
| computerConf | | computer 配置选项的映射。 | true |
| workerInstances | | worker 实例数量,将覆盖 'job.workers_count' 选项。 | true |
| pullPolicy | 未设置时由 Kubernetes 按镜像标签决定：`latest` 为 `Always`，其他标签为 `IfNotPresent` | 可显式设置 `Always`、`Never` 或 `IfNotPresent`；CRD 未提供默认值。详见 [镜像拉取策略](https://kubernetes.io/docs/concepts/containers/images/#image-pull-policy)。 | false |
| pullSecrets | | 镜像拉取密钥,详情请参考:https://kubernetes.io/docs/concepts/containers/images/#specifying-imagepullsecrets-on-a-pod | false |
| masterCpu | | master 的 CPU 限制,单位可以是 'm' 或无单位,详情请参考:[https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu) | false |
| workerCpu | | worker 的 CPU 限制,单位可以是 'm' 或无单位,详情请参考:[https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu) | false |
| masterMemory | | master 的内存限制,单位可以是 Ei、Pi、Ti、Gi、Mi、Ki 之一,详情请参考:[https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory) | false |
| workerMemory | | worker 的内存限制,单位可以是 Ei、Pi、Ti、Gi、Mi、Ki 之一,详情请参考:[https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory) | false |
| log4jXml | | computer 作业的 log4j.xml 内容。 | false |
| jarFile | | 容器镜像内算法 JAR 的路径。 | false |
| remoteJarUri | | 算法 JAR 的 HTTP(S) 地址；启动脚本会下载该 JAR 并加载。 | false |
| jvmOptions | | computer 作业的 Java 启动参数。 | false |
| envVars | | 请参考:https://kubernetes.io/docs/tasks/inject-data-application/define-interdependent-environment-variables/ | false |
| envFrom | | 请参考:https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/ | false |
| masterCommand | bin/start-computer.sh | master 的运行命令,等同于 Docker 的 'Entrypoint' 字段。 | false |
| masterArgs | ["-r master", "-d k8s"] | master 的运行参数,等同于 Docker 的 'Cmd' 字段。 | false |
| workerCommand | bin/start-computer.sh | worker 的运行命令,等同于 Docker 的 'Entrypoint' 字段。 | false |
| workerArgs | ["-r worker", "-d k8s"] | worker 的运行参数,等同于 Docker 的 'Cmd' 字段。 | false |
| volumes | | 请参考:https://kubernetes.io/docs/concepts/storage/volumes/ | false |
| volumeMounts | | 请参考:https://kubernetes.io/docs/concepts/storage/volumes/ | false |
| secretPaths | | k8s-secret 名称和挂载路径的映射。 | false |
| configMapPaths | | k8s-configmap 名称和挂载路径的映射。 | false |
| podTemplateSpec | | 请参考:https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-template-v1/#PodTemplateSpec | false |
| securityContext | | 请参考:https://kubernetes.io/docs/tasks/configure-pod-container/security-context/ | false |

---

### KubeDriver 配置选项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| k8s.build_image_bash_path | | 用于构建镜像的命令路径。 |
| k8s.enable_internal_algorithm | true | 是否启用内部算法。 |
| k8s.framework_image_url | hugegraph/hugegraph-computer:latest | computer 框架的镜像 URL。 |
| k8s.image_repository_password | | 登录镜像仓库的密码。 |
| k8s.image_repository_registry | | 登录镜像仓库的地址。 |
| k8s.image_repository_url | hugegraph/hugegraph-computer | 镜像仓库的 URL。 |
| k8s.image_repository_username | | 登录镜像仓库的用户名。 |
| k8s.internal_algorithm | [pageRank] | 所有内部算法的名称列表。**注意**:算法名称在这里使用驼峰命名法(例如 `pageRank`),但算法实现返回下划线命名法(例如 `page_rank`)。 |
| k8s.internal_algorithm_image_url | hugegraph/hugegraph-computer:latest | 内部算法的镜像 URL。 |
| k8s.jar_file_dir | /cache/jars/ | 算法 jar 将上传到的目录。 |
| k8s.kube_config | ~/.kube/config | k8s 配置文件的路径。 |
| k8s.log4j_xml_path | | computer 作业的 log4j.xml 路径。 |
| k8s.namespace | hugegraph-computer-operator-system | hugegraph-computer 系统的命名空间。 |
| k8s.pull_secret_names | [] | 拉取镜像的 pull-secret 名称。 |
