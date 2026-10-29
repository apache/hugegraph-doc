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
启用 SeaTunnel 还需配置的 `apache/seatunnel` 镜像；启用 Vermeer 使用按 digest 固定的 `hugegraph/vermeer:helm-30b67d93e7d0`，
Master、Worker 和令牌初始化共用它。官方发布运行记录源码与镜像 digest，
详见 [Vermeer 部署指南](https://github.com/apache/hugegraph/blob/e886e9a669cdfd47c9f83392f86fc47940167960/helm/hugegraph/docs/vermeer.md)。
自定义镜像覆盖还需同步更新 `vermeer.image.digest`，或显式清空以按标签选择；非空 digest 优先。
基础 local PV 示例不包含 Vermeer 卷：单机增加两个，集群增加一个 Master 卷及每 Worker 一个卷，默认增加四个。

## 2 端口和健康检查 {#2-ports-and-health}

PD 端口为 REST 8620、gRPC 8686、Raft 8610；Store 为 REST 8520、gRPC 8500、Raft 8510；Server HTTP 为 8080；Hubble HTTP 为 8088。
客户端 Service 隐藏 Pod 地址，NodePort 是节点上另外分配的端口，与应用监听端口不同。
PD `/v1/ready` 需要 Raft leader，`/v1/health` 只说明监听器已启动，Store 等待多数 PD peer ready 后启动。
Server 等待存储的默认上限为 300 秒，可以用 `server.storageWaitTimeoutSeconds` 调整。
本地模板渲染不能验证集群连通性、卷挂载或 JVM 运行容量。

### 保留元数据命名空间 {#metadata-namespace}

`metadataCluster: hg-test` 用于声明 Server 和 Store 访问 PD 时的元数据前缀（注入至 Server 的 `HG_SERVER_CLUSTER` 与 Store 的 `PD_CLUSTER`）。
它并非 Raft 分组名，修改该值不会自动迁移历史元数据。**切勿**为了启用 Vermeer 将已有集群的前缀随意变更。若遇到 Server 查询正常但 Vermeer 扫描 Store 报 `Schema missing` 或 `no such vertex label`，应优先核查各组件的元数据前缀是否完全一致。

若历史自建环境使用了非默认前缀，升级前需在 Server Deployment 显式标注确认：

```bash
kubectl -n hugegraph annotate deployment hugegraph-server \
  hugegraph.apache.org/metadata-cluster='<已核准的历史前缀>'
```

并在 values 中将 `metadataCluster` 设为同一值。对于采用 `store.updateStrategy.type=OnDelete` 策略的 Store 节点，需按[受控滚动升级流程](#6-rolling-store-images-safely)逐个重建 Pod，新配置方可生效。

> [!DETAILS]- 可选引擎运维：探针、凭据与拓扑切换
> - **端口与健康状态**：SeaTunnel HTTP/UI 端口为 `8080`；Vermeer Master HTTP/gRPC 为 `6688/6689`，Worker 为 `6788/6789`。
>   原生 HTTP/UI 在 easy 下默认 NodePort，strict 下默认 ClusterIP，两者均需登录；内部 RPC、Worker HTTP 与 SeaTunnel `5801` 保持私有。
>   `service.type: null` 继承模式默认值，显式 `ClusterIP` 保持私有，显式 `NodePort` 则开放需要登录的 HTTP/UI。
>   使用 `hugegraph-seatunnel` 或 `hugegraph-vermeer-master` Service 分配的 HTTP NodePort 与可达节点 IP 访问。
>   查询命令见[原生入口说明](/cn/docs/quickstart/hugegraph/hugegraph-helm/#optional-engines)；ClusterIP 可使用 port-forward。
> - **密码与会话**：初次部署生成的管理密码在 easy 模式下为 6 位字符，strict 模式下为 16 位；后续升级与模式切换均自动保留既有凭据。
>   Vermeer 原生控制台直接在 **Admin credential** 填入 `<release>-vermeer-admin` Secret 的 `password` 即可登录；Hubble 内部服务凭据已自动注入。
> - **拓扑与副本切换**：修改 `seatunnel.mode` 或 `vermeer.mode` 前，请确保所有计算与导入批任务已结束并卸载内存图副本。单机与集群使用独立的数据卷声明，拓扑切换不会自动迁移本地文件。
> - 完整恢复指引与进阶参数详见 [Vermeer 部署指南](https://github.com/apache/hugegraph/blob/e886e9a669cdfd47c9f83392f86fc47940167960/helm/hugegraph/docs/vermeer.md)
>   与 [SeaTunnel 部署指南](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/seatunnel.md)。

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

## 4 分区副本 {#4-partition-sharding}

首次初始化时，Store 至少三个则默认每个分区三副本，否则一副本。
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

原生引擎的 extraIngress 只接受显式内部 Pod／namespace selector，拒绝 IP block 和通配规则。
NodePort HTTP 访问已由生成的策略直接放行，无需额外的 extraIngress 规则。
上面的基础服务示例用于 Server。外部数据源可按需配置引擎 extraEgress，strict 进一步限制出站流量。

## 6 逐个升级 Store {#6-rolling-store-images-safely}

集群预设使用 `store.updateStrategy.type=OnDelete` 便于维护时控制逐个替换。
每次只删除一个 Store Pod，下一次删除前确认上一个 Pod Ready、Store 心跳新鲜，并从 PD leader 查询每个 shard group 都有完整成员及唯一 leader。
PD 的 `Up` 状态本身不证明 shard 恢复完成。PDB 限制主动驱逐，不限制 StatefulSet 控制器更新。
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
忙碌任务返回 body `status: 1001`。follower 可能返回空成功，leader 转移是异步的，HTTP 200 或转移计划不代表执行完成。
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

Server 副本可以常规变更，HPA 还需要 CPU requests。Store 扩容需要协调存储和 shard。
PD 扩缩容及 Store 缩容不能仅修改副本数，需要先更新持久化 Raft/shard 成员关系。
chart 对已初始化 StatefulSet 检查不支持的身份和成员变更，首次安装不执行升级专用查询。
按生命周期流程扩缩容，避免直接 `kubectl scale` 使 Hubble 的 Store metrics 配置过期。

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
