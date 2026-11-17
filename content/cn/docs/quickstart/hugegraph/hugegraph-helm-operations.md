---
title: "HugeGraph Kubernetes 运维"
linkTitle: "Kubernetes 运维"
weight: 5
search_keywords: [HugeGraph Helm 运维, local PV, NetworkPolicy, PD, Store]
---

本文配合 [Helm 部署](./hugegraph-helm.md)使用。生命周期检查和恢复说明见
[运维参考](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md)，所有参数说明见 chart 的 `values.yaml`。

命令假设 release 和 namespace 都是 `hugegraph`，覆盖名称时请替换实际工作负载名。

## 1 存储和内网镜像 {#1-storage-and-private-images}

基础安装需要七个持久卷。动态存储需要正常的 provisioner，静态 local 存储需要预建目录和绑定节点的匹配 PV。
[完整例子](https://github.com/apache/hugegraph/tree/master/helm/hugegraph/examples)包含七个 local PV、`WaitForFirstConsumer`、镜像仓库和 GitOps Secret。

`WaitForFirstConsumer` 的 PVC 初期 Pending 可以是正常等待；持续 Pending 应检查 PVC/Pod 事件和 PV 匹配。
PVC 已绑定但目录不存在或权限不匹配时可能挂载失败，不能把故障 PVC 静默替换成临时目录。

```bash
kubectl -n hugegraph get pvc,pods
kubectl -n hugegraph describe pvc <claim-name>
kubectl -n hugegraph describe pod <pod-name>
kubectl get pv,storageclass
```

出现 `ImagePullBackOff` 时检查 Pod 事件、仓库连通性和拉取凭据。默认只需四个组件镜像，等待 Store/Helm test 复用已包含 curl 的组件镜像。
如显式覆盖 helper 镜像，该镜像也需要同步到内网仓库。

启用 SeaTunnel 还需配置的 `apache/seatunnel` 镜像；Vermeer 默认使用 `hugegraph/vermeer:latest`，Master、Worker 和令牌初始化共用它。
需要可复现时固定兼容的标签或 digest。启用 RAG 还需 `values-rag.yaml` 中固定 digest 的镜像。

详见 [Vermeer 部署指南](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/vermeer.md)。
自定义镜像覆盖还需同步更新 `vermeer.image.digest`，或显式清空以按标签选择；非空 digest 优先。

基础 local PV 示例不包含 Vermeer 卷：单机增加两个，集群增加一个 Master 卷及每 Worker 一个卷，默认增加四个。

### 保留 Text2GQL 加密主密钥 {#text2gql-master-key}

Chart 现在将 `text2gql.shared.master_key_file` 设为 `/hubble-data/text2gql-master.key`，与 H2 一起保存在 Hubble 数据卷。
备份和恢复时二者应配套；关闭 Hubble 持久化后，Pod 替换会丢失 `emptyDir` 中的数据与密钥。

从旧的容器内路径 `/hubble/data/text2gql-master.key` 升级时，将原密钥保留到新路径，或在升级后**重新输入并保存一次模型 API Key**。
H2 可能仍显示已保存 API Key，但生成请求返回 HTTP 503；仅保存其他设置不能修复缺失的加密密钥。
新密钥在保存 API Key 时创建，不是在启动或解密时创建。

Pod 替换后应保持文件 owner UID 和 `0600` 权限。
若通过 Secret 提供 `HUBBLE_TEXT2GQL_MASTER_KEY`，它优先于文件；解密旧数据需保留相同 Secret 值。

详见[完整密钥恢复约定](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#hubble-text2gql-credentials)。

## 2 端口和健康检查 {#2-ports-and-health}

PD 端口为 REST 8620、gRPC 8686、Raft 8610；Store 为 REST 8520、gRPC 8500、Raft 8510；Server HTTP 为 8080；Hubble HTTP 为 8088。
客户端 Service 隐藏 Pod 地址，NodePort 是节点上另外分配的端口，与应用监听端口不同。

PD `/v1/ready` 需要 Raft leader，`/v1/health` 只说明监听器已启动，Store 等待多数 PD peer ready 后启动。
Server 等待存储的默认上限为 300 秒，可以用 `server.storageWaitTimeoutSeconds` 调整。
本地模板渲染不能验证集群连通性、卷挂载或 JVM 运行容量。

Store 探针使用 `/v1/health`。支持该接口的版本中，`/-/lifecycle: STARTED` 只说明 Spring 已就绪且 gRPC listener 正在运行；
`/-/state` 是独立的运维管理标记，仍可能为 `STARTING`。因此 Kubernetes Ready 与 Hubble 的 `NOT_READY` 观测可以同时出现。

应分别核对 PD 注册、分区恢复和实际图查询，见 [Store 生命周期约定](https://github.com/apache/hugegraph/blob/master/hugegraph-store/docs/deployment-guide.md#step-3-deploy-store-cluster)。

PD 集群统计与逐成员指标采集也独立。Service origin 无法归属某个上报成员时，可能显示 `pd_metrics_unmapped`，而集群统计仍可用。
Hubble 不会按 Service 别名推断成员，也不会将该样本归到 leader。

检查配置与上报的 origin、采集详情；
[运维诊断说明](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-hubble/docs/operations-diagnostics-20261023.md)记录了可信 origin 边界。

### 保留元数据命名空间 {#metadata-namespace}

`metadataCluster: hg-test` 用于声明 Server 和 Store 访问 PD 时的元数据前缀（注入至 Server 的 `HG_SERVER_CLUSTER` 与 Store 的 `PD_CLUSTER`）。
它并非 Raft 分组名，修改该值不会自动迁移历史元数据。**切勿**为了启用 Vermeer 将已有集群的前缀随意变更。

若遇到 Server 查询正常但 Vermeer 扫描 Store 报 `Schema missing` 或 `no such vertex label`，应优先核查各组件的元数据前缀是否完全一致。

若历史自建环境使用了非默认前缀，升级前需在 Server Deployment 显式标注确认：

```bash
kubectl -n hugegraph annotate deployment hugegraph-server \
  hugegraph.apache.org/metadata-cluster='<已核准的历史前缀>'
```

并在 values 中将 `metadataCluster` 设为同一值。对于采用 `store.updateStrategy.type=OnDelete` 策略的 Store 节点，需按[受控滚动升级流程](#6-rolling-store-images-safely)逐个重建 Pod，新配置方可生效。

可选引擎的端口、原生登录和 Service 访问方式见 [SeaTunnel 部署流程](./hugegraph-helm.md#6-start-seatunnel)
与 [Vermeer 工作流](./hugegraph-helm.md#7-vermeer-through-hubble)。
计算拓扑变更前，先按 [Vermeer 维护步骤](#vermeer-upgrade)处理任务与计算图。

### Helm test 检查范围 {#helm-test-coverage}

`helm test` 逐 Server Pod 检查图绑定（默认检查 `DEFAULT-hugegraph`，可通过 `server.testGraphAlias` 指定图别名），并要求当前可见关联索引处于 `CREATED` 状态。
请在索引创建／重建任务结束后执行，检查期间不要并发修改 schema。
在 HStore 上，读取尚未完成的索引可能将临时状态缓存到其他 Pod；重试不会刷新该状态。

即使任务随后成功，这些 Pod 的索引查询也可能继续失败；应在任务结束后再替换受影响的 Server Pod。
hook 不修复跨 Server 的 schema 缓存一致性。内部 150 秒重试窗口用于等待短暂选举等状态恢复，
Helm 的 `--timeout` 不会修改这个窗口。
它按 ID 读取索引，不刷新全量索引缓存；不证明索引查询结果或完整 schema 一致性。

对已有数据，可在 Helm 升级时用 `--set-file server.testGremlin=assertions.groovy` 添加逐 Pod 的只读业务断言。
脚本必须用 `assert` 或抛异常表示结果不符，仅返回 `false` 不会让请求失败。

[业务查询断言](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#business-query-assertions)
给出了示例与检查边界。未配置脚本时明确显示业务断言已跳过，默认 hook 不创建 schema 或数据。

自定义脚本使用 hook 的 Server 凭据执行（开启鉴权时为 `admin`），不强制只读；请提供可信的只读断言。

Server API 根据 `Accept-Encoding` 协商响应压缩。支持 gzip 的客户端可请求 `gzip` 或使用 `curl --compressed`；
`identity` 或未请求压缩时返回未压缩内容。需从更新后的源码重新构建 Server 镜像才能包含该行为，仅更新 chart 不会改变现有镜像。

### PD REST 鉴权 {#pd-rest-authentication}

PD REST 使用 HTTP Basic 鉴权，`hg`、`store`、`hubble` 和 `vermeer` 共用 PD REST Secret 密码。
Server 的 `admin` 不是 PD REST 账户，使用它会返回 401。默认 release/Secret 的查询示例，地址应为可达的 PD REST 地址：

```bash
PD_SECRET=$(kubectl -n hugegraph get secret hugegraph-pd-auth \
  -o jsonpath='{.data.secret-key}' | base64 --decode)
curl --user "hg:${PD_SECRET}" "http://<pd-rest-address>:8620/v1/stores"
```

以上 HTTP 示例适用于可信内网。其他访问路径可使用 HTTPS 网关，或按需执行
`kubectl -n hugegraph port-forward service/hugegraph-pd-client 8620:8620`，再访问 `http://127.0.0.1:8620`。

使用 `pd.auth.existingSecret` 或自定义 `pd.auth.key` 时读取实际 Secret 和 key，不使用 Server 管理员密码。
变量式示例避免将密码字面值写入 shell 历史，但展开后的凭据可能短暂出现在进程参数中。

共享终端可选用 `curl --user hg` 提示输入密码，或权限为 `600` 的私有 curl 配置文件；
[凭据操作说明](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#credentials)
也包含改密请求体的处理方式。不要记录或提交凭据文件。

## 3 调度 {#3-scheduling}

默认 `preferred` 反亲和允许节点少于副本数时调度；`values-cluster.yaml` 对 PD/Store 设置 required 反亲和，因此需要至少三个可调度节点。
显式 affinity 优先于预设。local PV 节点亲和必须匹配工作负载位置约束，PV 容量声明不等于文件系统配额。
持久化 PD/Store 的 Raft 主机名和端口会记录为成员身份，不能作为普通配置随意变更。

### 区分初始化历史与当前成员关系 {#stable-bootstrap-topology}

Chart 将首次 PD peers、Store allowlist 数量和启动 Store 门槛记录在不可变、保留的 `<fullname>-bootstrap` ConfigMap 中。
执行 Helm 的账号需要 namespace 的 ConfigMap 读取和 PVC 列表权限。没有 `bootstrap.enabled` 开关。

升级、回退与手动节点变更时保留这份记录；它是初始化历史，不是当前 PD 投票成员或所有已准入 Store 的清单。

| 参数 | 新安装 | 已初始化安装 |
|---|---|---|
| `bootstrap.pdReplicas` | 留空使用本次请求的 PD 副本数 | 保留记录中的首次数量 |
| `bootstrap.storeReplicas` | 留空使用本次请求的 Store 副本数 | 保留首次 allowlist 数量 |
| `bootstrap.initialStoreCount` | 留空使用本次请求的 Store 副本数 | 保留首次启动门槛 |
| `pd.partition.defaultShardCount` | 显式奇数 RF；否则首次 Store 准入数量（`bootstrap.storeReplicas`）少于 3 为 RF=1，其余 RF=3 | PD 持久化的副本策略保持权威 |
{.wide .expand}

例如，将一个 Store 扩为三个不会把持久化 RF=1 自动转为 RF=3。五个 PD 副本要求 PDB 至少保留三个可用投票节点
（`pd.pdb.minAvailable=3`），默认的两个不足。PD 镜像需实现区分 bootstrap 准入与运行时投票 quorum 的检查；
应核验所选镜像的能力，不能仅凭 `latest` 推断。

没有记录的旧测试安装，仅能在拓扑、RF、名称、端口、PVC 绑定与 Raft 身份均不变且已核验时接管。
使用匹配 Server 源码的只读 `helm/check_bootstrap_adoption.py` 检查 PD 与每个 Store，保留 before 报告；
再以审阅后的 values 升级，随后通过 `--before` 比对。

按[完整接管流程](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#adopting-same-topology-test-data)
继续验证图读写。不要删除冲突记录，也不要按当前副本数猜测首次成员关系。

离线升级无法发现保留的历史，应使用 `helm template --is-upgrade` 并显式固定三个已记录的 bootstrap 计数。
离线渲染不能证明已有 PVC 可安全复用。旧 values 含 `bootstrap.enabled` 时，通过审阅后的
`--reset-values -f reviewed-values.yaml` 移除；继续用 `--reuse-values` 携带该键会被拒绝。

## 4 分区副本 {#4-partition-sharding}

首次初始化时，记录的首次 Store 准入数量（`bootstrap.storeReplicas`）至少三个则默认每个分区三副本，否则一副本。
PD 会持久化分区设置，初始化后修改 chart 值不会覆盖已有元数据，应使用 PD 配置 API 并协调分区巡检。

显式 shard 数必须为奇数且不超过 Store 数，操作在线集群前先核对
[拓扑约束](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#topology-and-scheduling)；chart 不负责迁移已有 shard 元数据。

## 5 NetworkPolicy {#5-networkpolicy}

基础服务的完整隔离在 easy 和普通集群预设下默认关闭，strict 下开启。
SeaTunnel 和 Vermeer 始终需要登录。原生策略仅在最终 Service 类型为 NodePort 时允许外部 HTTP，
内部 RPC、Worker HTTP 与 SeaTunnel 成员端口仍限制为相应 release 调用方，`networkPolicy.enabled=false` 也不例外。

集群网络插件必须支持策略执行，才有实际隔离效果。
生成策略允许组件间通信和 DNS，基础服务的外部客户端、Ingress 控制器需要适当的 `networkPolicy.<component>.extraIngress`，
外部发现地址可能还需要 `extraEgress`。基础服务规则的空列表合法但可能阻止外部访问，并支持 Kubernetes 原生规则，包括允许全部的 `{}`。

按实际来源地址或 selector 配置，并考虑 NodePort SNAT 和控制器行为。

```yaml
networkPolicy:
  enabled: true
  server:
    extraIngress:
      - from:
          - ipBlock:
              cidr: 10.20.0.0/16
        ports:
          - protocol: TCP
            port: 8080
  hubble:
    extraIngress:
      - from:
          - ipBlock:
              cidr: 10.20.0.0/16
        ports:
          - protocol: TCP
            port: 8088
```

SeaTunnel 与 Vermeer 的 `extraIngress` 只接受显式内部 Pod／namespace selector，拒绝 IP block 和通配规则。
NodePort HTTP 访问已由生成的策略直接放行，无需额外的 extraIngress 规则。
上面的基础服务示例用于 Server 与 Hubble。外部数据源可按需配置引擎 extraEgress，strict 进一步限制出站流量。

### 放行 RAG 模型与浏览器流量 {#rag-network-access}

strict 模式或 `networkPolicy.enabled=true` 时，RAG 生成的策略允许 DNS 和自动连接的同 release Server，
不会自动放行外部模型服务或浏览器/控制器的入站访问。

1. 通过 `rag.networkPolicy.extraEgress` 放行实际 Chat/Embedding 目标和端口；外部 Server 连接也需要对应出站规则。
1. 通过 `rag.networkPolicy.extraIngress` 放行选定的鉴权代理或 Ingress 控制器；修改 Service 类型不会自动创建这些 RAG 入站规则。
1. 确认集群 CNI 执行 NetworkPolicy，再从 RAG 界面测试已保存的模型连接。界面可访问不代表 Pod 能连接模型服务。
{.steps}

这两个字段使用 Kubernetes 原生 NetworkPolicy 规则，按实际目标配置 Pod/namespace peer 或 IP 范围与端口；
模型 URL 中的 HTTP 主机名不能直接作为 NetworkPolicy 目标 selector。
RAG Service 应保持私有，或将外部入口置于鉴权边界之后，因为应用登录没有保护全部路由。

完整配置归属与部署选项见 [RAG 部署指南](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/rag.md#external-server-and-deployment-options)。

## 6 逐个升级 Store {#6-rolling-store-images-safely}

集群预设使用 `store.updateStrategy.type=OnDelete` 便于维护时控制逐个替换。
每次只删除一个 Store Pod，下一次删除前确认上一个 Pod Ready、Store 心跳新鲜，并从 PD leader 查询每个 shard group 都有完整成员及唯一 leader。
PD 的 `Up` 状态本身不证明 shard 恢复完成。

PDB 限制主动驱逐，不限制 StatefulSet 控制器更新。
发现缺成员或无 leader 时停止继续替换。

[运维参考](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#rolling-store-updates-and-recovery)说明这些升级条件，
但不提供完整的逐组诊断或丢盘恢复步骤。

即使副本完整，替换单个 Store 时，Raft leader 和客户端路由收敛期间仍可能出现请求失败或超时，不保证零错误。
继续维护前同时观察应用错误和 shard 恢复状态，不要盲目重试写请求。

### PD 巡检和 leader 均衡 {#pd-patrol-and-leader-balance}

分区巡检修复 shard 成员关系；leader 均衡是单独的手动任务，不会自动定时执行。
执行前通过鉴权的 `/v1/members` 查询 `data.pdLeader.restUrl`，并确认该 PD 的 `/v1/ready` 返回 `isLeader: true`。

GET 任务 `/v1/task/patrolPartitions` 和 `/v1/task/balanceLeaders` 会改变集群状态，应携带 PD REST 凭据请求已确认的 leader。
成员恢复和 split/move 任务完成后才能执行 leader 均衡；Store 心跳需新鲜，各组成员需完整、健康。
忙碌任务返回 body `status: 1001`。

follower 可能返回空成功，leader 转移是异步的，HTTP 200 或转移计划不代表执行完成。
继续维护前重新检查 `/v1/partitions`、`/v1/stores` 和应用错误。

[任务操作步骤](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#pd-patrol-and-leader-balance)
说明巡检和均衡的独立操作；维护忙碌时不要循环请求任务。

## 7 灾难恢复 {#7-disaster-recovery}

保留原卷、claim 身份和 PD 成员关系，不通过删除 RocksDB lock 文件恢复，也不把持久化成员配置替换为全新的节点。
Store 丢盘后，新建空 PVC 并不能恢复原有数据。
local 磁盘不能在节点故障时自动迁移文件。备份应放在这些 PV 之外，并单独验证恢复；chart 不提供自动备份和自动恢复。

[恢复说明](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#rolling-store-updates-and-recovery)列出恢复约束，不是完整的恢复操作顺序。
破坏性变更前，应结合部署版本、剩余副本或备份制定并验证恢复方案。

## 8 扩缩容 {#8-scaling}

Server 副本可以常规变更，HPA 还需要 CPU requests。PD 与 Store 变更应先协调数据库成员，再同步 Helm 资源，
过程中始终保留 [bootstrap 记录](#stable-bootstrap-topology)：

- **PD 扩缩容**：先准备并验证实际 Raft 成员关系，期望副本数不会修改成员关系。
- **Store 扩容**：准备存储、核验容量，再显式准入新的 Pending Store 身份。
- **Store 缩容**：将源节点设为 Exiting，等待迁移与恢复，确认实际成员已排除它且本地引擎为空，再减少资源；退役与数据检查完成前保留 PVC。
- **Vermeer Worker**：先完成/取消任务并卸载计算图，再修改数量；随后重新检查 Worker 可用性并加载图。

Store 启动仍使用历史 PD seeds。首次一个 PD 后扩为三个，新增 Store 仍依赖 PD0；当前 PD quorum 正常还不够。
不支持缩到记录的 seed 多数以下。重启或新增 Store 前，同时检查历史 seed 多数可达与当前实际 PD quorum。

按[受控节点变更流程](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#controlled-node-changes-and-recovery-limits)操作，
避免用直接 `kubectl scale` 代替生命周期流程；它还可能使 Hubble 的可信 Store 指标目标配置过期。

## 9 集群外的 Hubble {#9-running-hubble-outside-the-cluster}

direct 模式只需要可达的 Server URL；PD discovery 还需要集群外可达的 PD gRPC，PD 注册的 Server 地址也必须可达。
必要时用 `server.advertiseUrl` 注册共享 Server 地址，这会影响所有 discovery 客户端，包括集群内 Hubble。
chart 内置 Hubble 已配置内部服务发现，不需要公开 PD 入口。

HTTP 可以直接使用，TLS 终止可选。Hubble 仍是单副本，当前登录依赖 Server 鉴权。

## 10 Gremlin 报 Could not rebind {#10-when-gremlin-fails-with-could-not-rebind}

PD 滚动更新期间，Server 可能 Ready、能响应 REST，但 Gremlin binding 失败。
执行 `helm test hugegraph -n hugegraph --logs --timeout 5m` 检查每个 Server Pod 的鉴权图查询；PD 稳定后替换失败 Pod 并再次验证。
只查询 `/versions` 不证明图绑定成功，还应检查 Hubble 新登录和图查询。

出现 `ERROR: missing required env 'HG_PD_AUTH_SECRET_KEY'` 时，检查 PD Pod 的 Secret 引用和对应 key，不要把 Secret 值输出到日志。
chart 正常情况下自动注入共享 PD REST 凭据，自定义容器或 manifest 必须向 PD 和客户端提供同一值。

GitOps 先创建外部 Secret 再调谐工作负载，普通 Helm 保留自动创建的 release Secret。

## 11 Vermeer 与 RAG 恢复 {#vermeer-and-rag-recovery}

### 配套升级 Master 与 Worker {#vermeer-upgrade}

Vermeer 注册时会将 Worker 报告的版本与 Master 版本精确比较，不一致时以 `inconsistent registration version` 拒绝注册。
镜像标签同名不能证明进程报告的版本一致。

1. 在维护窗口前停止新提交，完成或取消活动任务，并卸载计算图。
1. 为 Master 和全部 Worker 选择配套构建，保留审阅后的凭据、PVC 与图集群的 bootstrap 历史。
1. 协调执行发布，再检查注册日志和图空间范围的 Worker 可用性，随后才接收新任务。
1. 重新加载源图，计算所需结果并核对任务值。保留的任务元数据或 PVC 不能重建内存结果缓存。
{.steps}

原生引擎部署和操作见 [Vermeer 指南](/cn/docs/quickstart/computing/hugegraph-vermeer/)。
该流程不支持混合版本注册，也不保证滚动期间计算不中断。

### 保留计算文件并恢复结果 {#vermeer-storage-recovery}

Vermeer 单机增加两个 claim；集群增加一个 Master claim 与每个 Worker 一个 claim。
即便两个容器在同一 Pod，Master、Worker 也不能共享 Pebble 目录。关闭/卸载 Vermeer 或减少 Worker 时，claim 会保留。
显式关闭存储才使用 `emptyDir`，PVC 故障不会自动降级。切换拓扑不会迁移单机与集群各自的 claim。

持久化元数据、Worker 文件与任务历史不能恢复内存图、结果缓存或运行任务。

应用日志写入 stdout，不在数据卷内。单机 Pod 可执行：

```bash
kubectl -n hugegraph logs hugegraph-vermeer-master-0 -c master
kubectl -n hugegraph logs hugegraph-vermeer-master-0 -c worker
```

集群模式第二条命令使用对应 Worker Pod 名，例如 `hugegraph-vermeer-worker-0`。
图加载失败时检查 PD discovery、Store gRPC 连通性、元数据命名空间与 Worker Schema 凭据；
Pod Ready 或 `/healthcheck` 都不能单独证明 Worker 可分配。

见 [Vermeer 加载与计算验证](./hugegraph-helm.md#vermeer-workflow)。

### 恢复 RAG 设置 {#rag-settings-recovery}

RAG 使用一份持久化资源树、单副本与 Recreate 部署。`settings.yaml` 中保存的连接优先于部署默认值。
Secret/文件变更需要重启，不会覆盖用户已保存的连接字段；保留 PVC，通过界面更新保存的凭据。
界面保存只校验并持久化配置，不调用模型；**Test saved connection** 执行独立的连接检查。

详见 [RAG 配置与恢复约定](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/rag.md)。

### 验证完整工作流 {#integrated-verification}

1. 执行 `helm test hugegraph -n hugegraph --logs --timeout 5m`，检查工作负载与 PVC 状态。
1. 在 Hubble 重新登录，对具有已知预期数据的隔离图执行读写。
1. 将该图加载到 Vermeer，运行算法，确认任务成功并读取分页结果，核对引擎与图上下文。
1. 在 Hubble 运维中打开 Vermeer 计算摘要，检查就绪状态与观测时间。
1. 启用 RAG 时，分别测试已保存的 Chat/Embedding 连接及小规模抽取/检索流程。
{.steps}

Helm 渲染检查配置，`--wait` 检查 Kubernetes readiness，测试 hook 检查其说明范围内的图断言。
任何单项都不能证明 Vermeer 计算、RAG 模型可用性、升级数据保留或恢复成功。
