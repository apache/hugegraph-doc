---
title: "HugeGraph-Computer Configuration Reference"
linkTitle: "Computer Config Reference"
weight: 3
---

### Computer Config Options

> **Default Value Notes:**
> - Configuration items listed below show the **code default values** (defined in `ComputerOptions.java`)
> - When the **packaged configuration file** (`conf/computer.properties` in the distribution) specifies a different value, it's noted as: `value (packaged: value)`
> - Example: `300000 (packaged: 100000)` means the code default is 300000, but the distributed package defaults to 100000
> - For production deployments, the packaged defaults take precedence unless you explicitly override them

---

### 1. Basic Configuration

Core job settings for HugeGraph-Computer.

| config option | default value | description |
|---------------|---------------|-------------|
| hugegraph.url | http://127.0.0.1:8080 | The HugeGraph server URL to load data and write results back. |
| hugegraph.name | hugegraph | The graph name to load data and write results back. |
| hugegraph.username | "" (empty) | The username for HugeGraph authentication (leave empty if authentication is disabled). |
| hugegraph.password | "" (empty) | The password for HugeGraph authentication (leave empty if authentication is disabled). |
| job.id | local_0001 (packaged: local_001) | The job identifier on YARN cluster or K8s cluster. |
| job.namespace | "" (empty) | The job namespace that can separate different data sources. 🔒 **Managed by system - do not modify manually**. |
| job.workers_count | 1 | The number of workers for computing one graph algorithm job. 🔒 **Managed by system - do not modify manually in K8s**. |
| job.partitions_count | 1 | The number of partitions for computing one graph algorithm job. |
| job.partitions_thread_nums | 4 | The number of threads for partition parallel compute. |

---

### 2. Algorithm Configuration

Algorithm-specific configuration for computation logic.

| config option | default value | description |
|---------------|---------------|-------------|
| algorithm.params_class | org.apache.hugegraph.computer.core.config.Null | ⚠️ **REQUIRED** The class used to transfer algorithm parameters before the algorithm is run. |
| algorithm.result_class | org.apache.hugegraph.computer.core.config.Null | The class of vertex's value, used to store the computation result for the vertex. |
| algorithm.message_class | org.apache.hugegraph.computer.core.config.Null | The class of message passed when computing a vertex. |

---

### 3. Input Configuration

Configuration for loading input data from HugeGraph or other sources.

#### 3.1 Input Source

| config option | default value | description |
|---------------|---------------|-------------|
| input.source_type | hugegraph-server | The source type to load input data, allowed values: ['hugegraph-server', 'hugegraph-loader']. The 'hugegraph-loader' means use hugegraph-loader to load data from HDFS or file. If using 'hugegraph-loader', please configure 'input.loader_struct_path' and 'input.loader_schema_path'. |
| input.loader_struct_path | "" (empty) | The struct path of loader input, only takes effect when input.source_type=loader is enabled. |
| input.loader_schema_path | "" (empty) | The schema path of loader input, only takes effect when input.source_type=loader is enabled. |

#### 3.2 Input Splits

| config option | default value | description |
|---------------|---------------|-------------|
| input.split_size | 1048576 (1 MB) | The input split size in bytes. |
| input.split_max_splits | 10000000 | The maximum number of input splits. |
| input.split_page_size | 500 | The page size for streamed load input split data. |
| input.split_fetch_timeout | 300 | The timeout in seconds to fetch input splits. |

#### 3.3 Input Processing

| config option | default value | description |
|---------------|---------------|-------------|
| input.filter_class | org.apache.hugegraph.computer.core.input.filter.DefaultInputFilter | The class to create input-filter object. Input-filter is used to filter vertex edges according to user needs. |
| input.edge_direction | OUT | The direction of edges to load, allowed values: [OUT, IN, BOTH]. When the value is BOTH, edges in both OUT and IN directions will be loaded. |
| input.edge_freq | MULTIPLE | The frequency of edges that can exist between a pair of vertices, allowed values: [SINGLE, SINGLE_PER_LABEL, MULTIPLE]. SINGLE means only one edge can exist between a pair of vertices (identified by sourceId + targetId); SINGLE_PER_LABEL means each edge label can have one edge between a pair of vertices (identified by sourceId + edgeLabel + targetId); MULTIPLE means many edges can exist between a pair of vertices (identified by sourceId + edgeLabel + sortValues + targetId). |
| input.max_edges_in_one_vertex | 200 | The maximum number of adjacent edges allowed to be attached to a vertex. The adjacent edges will be stored and transferred together as a batch unit. |

#### 3.4 Input Performance

| config option | default value | description |
|---------------|---------------|-------------|
| input.send_thread_nums | 4 | The number of threads for parallel sending of vertices or edges. |

---

### 4. Snapshot & Storage Configuration

HugeGraph-Computer supports snapshot functionality to save vertex/edge partitions to local storage or MinIO object storage, enabling checkpoint recovery or accelerating repeated computations.

#### 4.1 Basic Snapshot Configuration

| config option | default value | description |
|---------------|---------------|-------------|
| snapshot.write | false | Whether to write snapshots of input vertex/edge partitions. |
| snapshot.load | false | Whether to load from snapshots of vertex/edge partitions. |
| snapshot.name | "" (empty) | User-defined snapshot name to distinguish different snapshots. |

#### 4.2 MinIO Integration (Optional)

MinIO can be used as a distributed object storage backend for snapshots in K8s deployments.

| config option | default value | description |
|---------------|---------------|-------------|
| snapshot.minio_endpoint | "" (empty) | MinIO service endpoint (e.g., `http://minio:9000`). Required when using MinIO. |
| snapshot.minio_access_key | minioadmin | MinIO access key for authentication. |
| snapshot.minio_secret_key | minioadmin | MinIO secret key for authentication. |
| snapshot.minio_bucket_name | "" (empty) | MinIO bucket name for storing snapshot data. |

**Usage Scenarios:**
- **Checkpoint Recovery**: Resume from snapshots after job failures, avoiding data reloading
- **Repeated Computations**: Load data from snapshots when running the same algorithm multiple times
- **A/B Testing**: Save multiple snapshot versions of the same dataset to test different algorithm parameters

**Example: Local Snapshot** (in `computer.properties`):
```properties
snapshot.write=true
snapshot.name=pagerank-snapshot-20260201
```

**Example: MinIO Snapshot** (in K8s CRD `computerConf`):
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

### 5. Worker & Master Configuration

Configuration for worker and master computation logic.

#### 5.1 Master Configuration

| config option | default value | description |
|---------------|---------------|-------------|
| master.computation_class | org.apache.hugegraph.computer.core.master.DefaultMasterComputation | Master-computation is computation that can determine whether to continue to the next superstep. It runs at the end of each superstep on the master. |

#### 5.2 Worker Computation

| config option | default value | description |
|---------------|---------------|-------------|
| worker.computation_class | org.apache.hugegraph.computer.core.config.Null | The class to create worker-computation object. Worker-computation is used to compute each vertex in each superstep. |
| worker.combiner_class | org.apache.hugegraph.computer.core.config.Null | Combiner can combine messages into one value for a vertex. For example, PageRank algorithm can combine messages of a vertex to a sum value. |
| worker.partitioner | org.apache.hugegraph.computer.core.graph.partition.HashPartitioner | The partitioner that decides which partition a vertex should be in, and which worker a partition should be in. |

#### 5.3 Worker Combiners

| config option | default value | description |
|---------------|---------------|-------------|
| worker.vertex_properties_combiner_class | org.apache.hugegraph.computer.core.combiner.OverwritePropertiesCombiner | The combiner can combine several properties of the same vertex into one properties at input step. |
| worker.edge_properties_combiner_class | org.apache.hugegraph.computer.core.combiner.OverwritePropertiesCombiner | The combiner can combine several properties of the same edge into one properties at input step. |

#### 5.4 Worker Buffers

| config option | default value | description |
|---------------|---------------|-------------|
| worker.received_buffers_bytes_limit | 104857600 (100 MB) | The limit bytes of buffers of received data. The total size of all buffers can't exceed this limit. If received buffers reach this limit, they will be merged into a file (spill to disk). |
| worker.write_buffer_capacity | 52428800 (50 MB) | The initial size of write buffer that used to store vertex or message. |
| worker.write_buffer_threshold | 52428800 (50 MB) | The threshold of write buffer. Exceeding it will trigger sorting. The write buffer is used to store vertex or message. |

#### 5.5 Worker Data & Timeouts

| config option | default value | description |
|---------------|---------------|-------------|
| worker.data_dirs | [jobs] | The directories separated by ',' that received vertices and messages can persist into. |
| worker.wait_sort_timeout | 600000 (10 minutes) | The max timeout (in ms) for message-handler to wait for sort-thread to sort one batch of buffers. |
| worker.wait_finish_messages_timeout | 86400000 (24 hours) | The max timeout (in ms) for message-handler to wait for finish-message of all workers. |

---

### 6. I/O & Output Configuration

Configuration for output computation results.

#### 6.1 Output Class & Result

| config option | default value | description |
|---------------|---------------|-------------|
| output.output_class | org.apache.hugegraph.computer.core.output.LogOutput | The class to output the computation result of each vertex. Called after iteration computation. |
| output.result_name | value | The value is assigned dynamically by #name() of instance created by WORKER_COMPUTATION_CLASS. |
| output.result_write_type | OLAP_COMMON | The result write-type to output to HugeGraph, allowed values: [OLAP_COMMON, OLAP_SECONDARY, OLAP_RANGE]. |

#### 6.2 Output Behavior

| config option | default value | description |
|---------------|---------------|-------------|
| output.with_adjacent_edges | false | Whether to output the adjacent edges of the vertex. |
| output.with_vertex_properties | false | Whether to output the properties of the vertex. |
| output.with_edge_properties | false | Whether to output the properties of the edge. |

#### 6.3 Batch Output

| config option | default value | description |
|---------------|---------------|-------------|
| output.batch_size | 500 | The batch size of output. |
| output.batch_threads | 1 | The number of threads used for batch output. |
| output.single_threads | 1 | The number of threads used for single output. |

#### 6.4 HDFS Output

| config option | default value | description |
|---------------|---------------|-------------|
| output.hdfs_url | hdfs://127.0.0.1:9000 | The HDFS URL for output. |
| output.hdfs_user | hadoop | The HDFS user for output. |
| output.hdfs_path_prefix | /hugegraph-computer/results | The directory of HDFS output results. |
| output.hdfs_delimiter | , (comma) | The delimiter of HDFS output. |
| output.hdfs_merge_partitions | true | Whether to merge output files of multiple partitions. |
| output.hdfs_replication | 3 | The replication number of HDFS. |
| output.hdfs_core_site_path | "" (empty) | The HDFS core site path. |
| output.hdfs_site_path | "" (empty) | The HDFS site path. |
| output.hdfs_kerberos_enable | false | Whether Kerberos authentication is enabled for HDFS. |
| output.hdfs_kerberos_principal | "" (empty) | The HDFS principal for Kerberos authentication. |
| output.hdfs_kerberos_keytab | "" (empty) | The HDFS keytab file for Kerberos authentication. |
| output.hdfs_krb5_conf | /etc/krb5.conf | Kerberos configuration file path. |

#### 6.5 Retry & Timeout

| config option | default value | description |
|---------------|---------------|-------------|
| output.retry_times | 3 | The retry times when output fails. |
| output.retry_interval | 10 | The retry interval (in seconds) when output fails. |
| output.thread_pool_shutdown_timeout | 60 | The timeout (in seconds) of output thread pool shutdown. |

---

### 7. Network & Transport Configuration

Configuration for network communication between workers and master.

#### 7.1 Server Configuration

| config option | default value | description |
|---------------|---------------|-------------|
| transport.server_host | 127.0.0.1 | 🔒 **Managed by system** The server hostname or IP to listen on to transfer data. Do not modify manually. |
| transport.server_port | 0 | 🔒 **Managed by system** The server port to listen on to transfer data. The system will assign a random port if set to 0. Do not modify manually. |
| transport.server_threads | 4 | The number of transport threads for server. |

#### 7.2 Client Configuration

| config option | default value | description |
|---------------|---------------|-------------|
| transport.client_threads | 4 | The number of transport threads for client. |
| transport.client_connect_timeout | 3000 | The timeout (in ms) of client connect to server. |

#### 7.3 Protocol Configuration

| config option | default value | description |
|---------------|---------------|-------------|
| transport.provider_class | org.apache.hugegraph.computer.core.network.netty.NettyTransportProvider | The transport provider, currently only supports Netty. |
| transport.io_mode | AUTO | The network IO mode, allowed values: [NIO, EPOLL, AUTO]. AUTO means selecting the appropriate mode automatically. |
| transport.tcp_keep_alive | true | Whether to enable TCP keep-alive. |
| transport.transport_epoll_lt | false | Whether to enable EPOLL level-trigger (only effective when io_mode=EPOLL). |

#### 7.4 Buffer Configuration

| config option | default value | description |
|---------------|---------------|-------------|
| transport.send_buffer_size | 0 | The size of socket send-buffer in bytes. 0 means using system default value. |
| transport.receive_buffer_size | 0 | The size of socket receive-buffer in bytes. 0 means using system default value. |
| transport.write_buffer_high_mark | 67108864 (64 MB) | The high water mark for write buffer in bytes. It will trigger sending unavailable if the number of queued bytes > write_buffer_high_mark. |
| transport.write_buffer_low_mark | 33554432 (32 MB) | The low water mark for write buffer in bytes. It will trigger sending available if the number of queued bytes < write_buffer_low_mark. |

#### 7.5 Flow Control

| config option | default value | description |
|---------------|---------------|-------------|
| transport.max_pending_requests | 8 | The max number of client unreceived ACKs. It will trigger sending unavailable if the number of unreceived ACKs >= max_pending_requests. |
| transport.min_pending_requests | 6 | The minimum number of client unreceived ACKs. It will trigger sending available if the number of unreceived ACKs < min_pending_requests. |
| transport.min_ack_interval | 200 | The minimum interval (in ms) of server reply ACK. |

#### 7.6 Timeouts

| config option | default value | description |
|---------------|---------------|-------------|
| transport.close_timeout | 10000 | The timeout (in ms) of close server or close client. |
| transport.sync_request_timeout | 10000 | The timeout (in ms) to wait for response after sending sync-request. |
| transport.finish_session_timeout | 0 | The timeout (in ms) to finish session. 0 means using (transport.sync_request_timeout × transport.max_pending_requests). |
| transport.write_socket_timeout | 3000 | The timeout (in ms) to write data to socket buffer. |
| transport.server_idle_timeout | 360000 (6 minutes) | The max timeout (in ms) of server idle. |

#### 7.7 Heartbeat

| config option | default value | description |
|---------------|---------------|-------------|
| transport.heartbeat_interval | 20000 (20 seconds) | The minimum interval (in ms) between heartbeats on client side. |
| transport.max_timeout_heartbeat_count | 120 | The maximum times of timeout heartbeat on client side. If the number of timeouts waiting for heartbeat response continuously > max_timeout_heartbeat_count, the channel will be closed from client side. |

#### 7.8 Advanced Network Settings

| config option | default value | description |
|---------------|---------------|-------------|
| transport.max_syn_backlog | 511 | The capacity of SYN queue on server side. 0 means using system default value. |
| transport.recv_file_mode | true | Whether to enable receive buffer-file mode. It will receive buffer and write to file from socket using zero-copy if enabled. **Note**: Requires OS support for zero-copy (e.g., Linux sendfile/splice). |
| transport.network_retries | 3 | The number of retry attempts for network communication if network is unstable. |

---

### 8. Storage & Persistence Configuration

Configuration for HGKV (HugeGraph Key-Value) storage engine and value files.

#### 8.1 HGKV Configuration

| config option | default value | description |
|---------------|---------------|-------------|
| hgkv.max_file_size | 2147483648 (2 GB) | The max number of bytes in each HGKV file. |
| hgkv.max_data_block_size | 65536 (64 KB) | The max byte size of HGKV file data block. |
| hgkv.max_merge_files | 10 | The max number of files to merge at one time. |
| hgkv.temp_file_dir | /tmp/hgkv | This folder is used to store temporary files during the file merging process. |

#### 8.2 Value File Configuration

| config option | default value | description |
|---------------|---------------|-------------|
| valuefile.max_segment_size | 1073741824 (1 GB) | The max number of bytes in each segment of value-file. |

---

### 9. BSP & Coordination Configuration

Configuration for Bulk Synchronous Parallel (BSP) protocol and etcd coordination.

| config option | default value | description |
|---------------|---------------|-------------|
| bsp.etcd_endpoints | http://localhost:2379 | 🔒 **Managed by system in K8s** The endpoints to access etcd. For multiple endpoints, use comma-separated list: `http://host1:port1,http://host2:port2`. Do not modify manually in K8s deployments. |
| bsp.max_super_step | 10 (packaged: 2) | The max super step of the algorithm. |
| bsp.register_timeout | 300000 (packaged: 100000) | The max timeout (in ms) to wait for master and workers to register. |
| bsp.wait_workers_timeout | 86400000 (24 hours) | The max timeout (in ms) to wait for workers BSP event. |
| bsp.wait_master_timeout | 86400000 (24 hours) | The max timeout (in ms) to wait for master BSP event. |
| bsp.log_interval | 30000 (30 seconds) | The log interval (in ms) to print the log while waiting for BSP event. |

---

### 10. Performance Tuning Configuration

Configuration for performance optimization.

| config option | default value | description |
|---------------|---------------|-------------|
| allocator.max_vertices_per_thread | 10000 | Maximum number of vertices per thread processed in each memory allocator. |
| sort.thread_nums | 4 | The number of threads performing internal sorting. |

---

### 11. System Administration Configuration

⚠️ **Configuration items managed by the system - users are prohibited from modifying these manually.**

The following configuration items are automatically managed by the K8s Operator, Driver, or runtime system. Manual modification will cause cluster communication failures or job scheduling errors.

| config option | managed by | description |
|---------------|------------|-------------|
| bsp.etcd_endpoints | K8s Operator | Automatically set to operator's etcd service address |
| transport.server_host | Runtime | Automatically set to pod/container hostname |
| transport.server_port | Runtime | Automatically assigned random port |
| job.namespace | K8s Operator | Automatically set to job namespace |
| job.id | K8s Operator | Automatically set to job ID from CRD |
| job.workers_count | K8s Operator | Automatically set from CRD `workerInstances` |
| rpc.server_host | Runtime | RPC server hostname (system-managed) |
| rpc.server_port | Runtime | RPC server port (system-managed) |
| rpc.remote_url | Runtime | RPC remote URL (system-managed) |

**Why These Are Forbidden:**
- **BSP/RPC Configuration**: Must match the actual deployed etcd/RPC services. Manual overrides break coordination.
- **Job Configuration**: Must match K8s CRD specifications. Mismatches cause worker count errors.
- **Transport Configuration**: Must use actual pod hostnames/ports. Manual values prevent inter-worker communication.

---

### K8s Operator Config Options

> NOTE: Option needs to be converted through environment variable settings, e.g. k8s.internal_etcd_url => INTERNAL_ETCD_URL

| config option | default value | description |
|------------------------------|---------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| k8s.auto_destroy_pod | true | Whether to automatically destroy all pods when the job is completed or failed. |
| k8s.close_reconciler_timeout | 120 | The max timeout (in ms) to close reconciler. |
| k8s.internal_etcd_url | http://127.0.0.1:2379 | The internal etcd URL for operator system. |
| k8s.max_reconcile_retry | 3 | The max retry times of reconcile. |
| k8s.probe_backlog | 50 | The maximum backlog for serving health probes. |
| k8s.probe_port | 9892 | The port that the controller binds to for serving health probes. |
| k8s.ready_check_internal | 1000 | The time interval (ms) of check ready. |
| k8s.ready_timeout | 30000 | The max timeout (in ms) of check ready. |
| k8s.reconciler_count | 10 | The max number of reconciler threads. |
| k8s.resync_period | 600000 | The minimum frequency at which watched resources are reconciled. |
| k8s.timezone | Asia/Shanghai | The timezone of computer job and operator. |
| k8s.watch_namespace | hugegraph-computer-system | The namespace to watch custom resources in. Use '*' to watch all namespaces. |

---

### HugeGraph-Computer CRD

> CRD: https://github.com/apache/hugegraph-computer/blob/master/computer-k8s-operator/manifest/hugegraph-computer-crd.v1.yaml

| spec | default value | description | required |
|-----------------|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| algorithmName | | The name of algorithm. | true |
| jobId | | The job id. | true |
| image | | The image of algorithm. | true |
| computerConf | | The map of computer config options. | true |
| workerInstances | | The number of worker instances, it will override the 'job.workers_count' option. | true |
| pullPolicy | Always | The pull-policy of image, detail please refer to: https://kubernetes.io/docs/concepts/containers/images/#image-pull-policy | false |
| pullSecrets | | The pull-secrets of Image, detail please refer to: https://kubernetes.io/docs/concepts/containers/images/#specifying-imagepullsecrets-on-a-pod | false |
| masterCpu | | The cpu limit of master, the unit can be 'm' or without unit detail please refer to: [https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu) | false |
| workerCpu | | The cpu limit of worker, the unit can be 'm' or without unit detail please refer to: [https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu) | false |
| masterMemory | | The memory limit of master, the unit can be one of Ei、Pi、Ti、Gi、Mi、Ki detail please refer to: [https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory) | false |
| workerMemory | | The memory limit of worker, the unit can be one of Ei、Pi、Ti、Gi、Mi、Ki detail please refer to: [https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory) | false |
| log4jXml | | The content of log4j.xml for computer job. | false |
| jarFile | | The jar path of computer algorithm. | false |
| remoteJarUri | | The remote jar uri of computer algorithm, it will overlay algorithm image. | false |
| jvmOptions | | The java startup parameters of computer job. | false |
| envVars | | please refer to: https://kubernetes.io/docs/tasks/inject-data-application/define-interdependent-environment-variables/ | false |
| envFrom | | please refer to: https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/ | false |
| masterCommand | bin/start-computer.sh | The run command of master, equivalent to 'Entrypoint' field of Docker. | false |
| masterArgs | ["-r master", "-d k8s"] | The run args of master, equivalent to 'Cmd' field of Docker. | false |
| workerCommand | bin/start-computer.sh | The run command of worker, equivalent to 'Entrypoint' field of Docker. | false |
| workerArgs | ["-r worker", "-d k8s"] | The run args of worker, equivalent to 'Cmd' field of Docker. | false |
| volumes | | Please refer to: https://kubernetes.io/docs/concepts/storage/volumes/ | false |
| volumeMounts | | Please refer to: https://kubernetes.io/docs/concepts/storage/volumes/ | false |
| secretPaths | | The map of k8s-secret name and mount path. | false |
| configMapPaths | | The map of k8s-configmap name and mount path. | false |
| podTemplateSpec | | Please refer to: https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-template-v1/#PodTemplateSpec | false |
| securityContext | | Please refer to: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/ | false |

---

### KubeDriver Config Options

| config option | default value | description |
|----------------------------------|------------------------------------------|-----------------------------------------------------------|
| k8s.build_image_bash_path | | The path of command used to build image. |
| k8s.enable_internal_algorithm | true | Whether enable internal algorithm. |
| k8s.framework_image_url | hugegraph/hugegraph-computer:latest | The image url of computer framework. |
| k8s.image_repository_password | | The password for login image repository. |
| k8s.image_repository_registry | | The address for login image repository. |
| k8s.image_repository_url | hugegraph/hugegraph-computer | The url of image repository. |
| k8s.image_repository_username | | The username for login image repository. |
| k8s.internal_algorithm | [pageRank] | The name list of all internal algorithm. **Note**: Algorithm names use camelCase here (e.g., `pageRank`), but algorithm implementations return underscore_case (e.g., `page_rank`). |
| k8s.internal_algorithm_image_url | hugegraph/hugegraph-computer:latest | The image url of internal algorithm. |
| k8s.jar_file_dir | /cache/jars/ | The directory where the algorithm jar will be uploaded. |
| k8s.kube_config | ~/.kube/config | The path of k8s config file. |
| k8s.log4j_xml_path | | The log4j.xml path for computer job. |
| k8s.namespace | hugegraph-computer-system | The namespace of hugegraph-computer system. |
| k8s.pull_secret_names | [] | The names of pull-secret for pulling image. |
