---
title: "在 Kubernetes 上运维 HugeGraph"
linkTitle: "Kubernetes 运维 (Helm)"
weight: 5
search_keywords:
  - helm
  - kubernetes
  - operations
  - disaster recovery
  - networkpolicy
---

### 1 适用范围

本页面向已经用 Helm chart 部署好 HugeGraph 集群的运维场景。安装、升级、卸载见
[部署页](/cn/docs/quickstart/hugegraph/hugegraph-helm/)；完整参数参考仍在
[chart README](https://github.com/apache/hugegraph/tree/master/helm/hugegraph#configuration)。

下文命令假定 release 名为 `hugegraph`、namespace 为 `hugegraph`，请按需替换。两个凭据会反复用到，都从
chart 管理的 Secret 读取：

```bash
PASSWORD="$(kubectl get secret -n hugegraph hugegraph-admin \
  -o jsonpath='{.data.password}' | base64 --decode)"
PD_SECRET="$(kubectl get secret -n hugegraph hugegraph-pd-auth \
  -o jsonpath='{.data.secret-key}' | base64 --decode)"
```

### 2 端口与健康

| 组件 | 端口 | 用途 |
|------|------|------|
| PD | `8686` | gRPC（Store 与 Server 客户端） |
| PD | `8620` | REST / 健康探测 |
| PD | `8610` | Raft |
| Store | `8500` | gRPC |
| Store | `8510` | Raft |
| Store | `8520` | REST / 健康探测 |
| Server | `8080` | Gremlin 与 REST API |

所有端口都可以通过 values 配置；修改 `server.port` 会同时更新监听、容器端口和 Service。进程存活但停止响应的组件由
存活探测终结：默认 20 秒周期、3 次失败阈值把一个卡死 Store 的影响时间限制在约一分钟内，重启后 raft 几秒内就会转移
它持有的分区 leader。

通过 port-forward 访问 API：

```bash
kubectl port-forward -n hugegraph svc/hugegraph-server 8080:8080
curl --user "admin:${PASSWORD}" http://127.0.0.1:8080/versions
curl --user "admin:${PASSWORD}" http://127.0.0.1:8080/graphs
```

### 3 调度

每个组件（`pd`、`store`、`server`、`hubble`）都提供 `nodeSelector`、`tolerations`、`affinity`、
`topologySpreadConstraints` 和 `priorityClassName`。例如把 Store 固定到打了标签的节点：

```yaml
store:
  nodeSelector:
    hugegraph/role: storage
```

`antiAffinity`（`required` | `preferred` | `disabled`）为 `pd`、`store`、`server` 渲染按主机名的
pod 反亲和预设；Hubble 设计为单副本，没有这个配置项。设置原生 `affinity` 会整体替换预设。三者默认都是
`preferred`，因此节点数少于副本数的集群也能调度。代价是：节点资源紧张时调度器可能把副本放到同一节点，单个节点
故障就可能同时带走多个 PD 或 Store 副本。节点足够的生产集群应把 `pd.antiAffinity` 和 `store.antiAffinity`
固定为 `required`，`values-cluster.yaml` 即如此。

### 4 分区分片

全新安装会在 `store.replicas` 不低于 3 时把 PD 的分片数种子设为 3，否则设为 1；没有这个种子，PD 镜像会把
`partition.default-shard-count` 固定为 1，chart 部署的集群就没有 Store 级高可用。chart 通过 PD 的
`JAVA_OPTS` 传入 `-Dpartition.default-shard-count`，不影响镜像的 JVM 自动调优。

**种子只在首次引导时生效。** PD 第一次以空存储启动时把分片数持久化到自己的元数据里，此后存储的值才是权威：之后修改
`pd.partition.defaultShardCount` 或跨过推导边界地伸缩 `store.replicas`，对已初始化的集群都没有效果。要修改运行中
集群的分片数，请使用 PD 自己的配置 API（只接受不超过存活 Store 数的奇数），然后触发
`GET /v1/task/patrolPartitions`，并预期分片组会发生再分配。

分片数还决定初始分区数：`store.replicas x storeMaxShardCount / shardCount`，只在引导时计算一次。按镜像默认的
`store-max-shard-count`（12），默认 3 Store 安装得到 12 个分区；需要更多分区时调大
`pd.partition.storeMaxShardCount`（同样只在首次引导时生效）。

显式设置的 `pd.partition.defaultShardCount` 必须是奇数且不超过 `store.replicas`；其他值会在渲染时被 chart
拒绝，因为 PD 会悄悄钳制或拒绝它们，渲染通过并不等于设置生效。

### 5 NetworkPolicy

`networkPolicy.enabled` 为每个组件（PD、Store、Server，启用时还有 Hubble）渲染一个 NetworkPolicy。每个策略
都对自己的 Pod 做双向隔离并列出所需流量，因此应用顺序无关紧要。`values.yaml` 默认关闭（基础配置无法预知你的
客户端是谁），`values-cluster.yaml` 默认开启。

它只在集群网络插件强制执行 NetworkPolicy 时才生效（kind v0.25 及以上、k3s、Calico、Cilium）；其他插件会接受
对象但不执行。验证方法：在另一个 namespace 起一个不带 chart 标签的 Pod，`curl` PD 客户端 Service 的 REST
端口，必须超时。

策略开启后，release 只放行自己的流量：

| 目标 | 来源与端口 |
|---|---|
| PD | PD：raft、gRPC。Store、Server、`pd` 模式的 Hubble：gRPC、REST |
| Store | Store：raft。Server：gRPC、REST。`pd` 模式的 Hubble：REST |
| Server | Hubble 和 `helm test` Pod：`server.port` |
| Hubble | 无（port-forward 走回环，不需要规则） |

每个组件还可以走 53 端口解析 DNS。release 之外的任何来源都必须列入
`networkPolicy.<component>.extraIngress` 才被放行，包括 Ingress 控制器和 NodePort / LoadBalancer Service
的客户端。在 `extraIngress` 为空时暴露 PD、Server 或 Hubble，或设置 `server.advertiseUrl`，渲染会直接失败
而不是打开端口。该检查只看 chart 自己创建的暴露；你自行添加的 Service、Gateway 路由或代理需要自己的条目。

两个出向事实需要规划。PD、Store、Server 除 DNS 外不访问 release 以外的任何地址，因此需要外呼的功能在策略开启时
不可用；默认唯一的外呼方是 Store 镜像，它每次启动都从 github.com 下载 `libjemalloc.so`。策略开启时该连接约两分
钟后超时，Store 不带 jemalloc 继续启动（kind 上实测：就绪时间从 11 秒变为 151 秒）；无外网的集群同理。另外
`helm test` Pod 不被任何 chart 策略选中，因此在你自己的 namespace 级默认拒绝策略下，要给它放行到 `server.port`
和 DNS 的出向流量。

**放行其他工作负载。** 每条规则的 `from` 必须指明对端；要放行任意地址，请显式写 `0.0.0.0/0` 这样的
`ipBlock`。同一个对端里的 `namespaceSelector` 和 `podSelector` 必须同时匹配；写成两个对端则满足其一即可。
NodePort / LoadBalancer 客户端在 Pod 看来是什么地址，取决于网络插件、`externalTrafficPolicy` 和请求到达的
节点。在双节点 kind 集群上用 NodePort Server 实测：

- kindnet，以及开 kube-proxy replacement 的 Cilium：请求发到 Server 所在节点时带客户端地址；经另一节点转发时
  带那个节点的地址。
- Calico：经另一节点转发的请求来自该节点在 Pod CIDR 里的隧道地址。
- 用 kube-proxy 的 Cilium：任何 `ipBlock` 规则都放行不了 NodePort 流量，因为 Cilium 用自己的节点身份而不是
  CIDR 识别节点地址。

请用你实际运行的插件测试，并按看到的来源地址写 CIDR。放行 Ingress 控制器、应用 namespace 和 Prometheus 的
完整示例：

```yaml
networkPolicy:
  server:
    extraIngress:
      - from:
          - namespaceSelector:
              matchLabels:
                kubernetes.io/metadata.name: ingress-nginx
            podSelector:
              matchLabels:
                app.kubernetes.io/name: ingress-nginx
        ports:
          - port: 8080
      - from:
          - namespaceSelector:
              matchLabels:
                kubernetes.io/metadata.name: apps
        ports:
          - port: 8080
  pd:
    extraIngress:
      - from:
          - namespaceSelector:
              matchLabels:
                kubernetes.io/metadata.name: monitoring
        ports:
          - port: 8620
```

### 6 安全地滚动 Store 镜像

Store 的滚动更新以监听检查推进，而不是以分片恢复推进，控制器可能在上一个 Store 尚未重新加入分片组时就替换下一
个。生产环境滚动镜像时，设置 `store.updateStrategy.type=OnDelete`，逐个删除 Store Pod，并在两次删除之间做检查。

PD 里的 `Up` 不是这个检查。PD 在注册时就把 Store 标为 `Up`，此时它还没恢复任何分区；已停止的 Store 也会在
keep-alive 记录过期前（当前镜像为 300 秒）一直保持 `Up` 并留在所有分片组里：窗口内删除又回来的 Pod 根本不会离开
`Up` 状态。检查要从 Pod 开始：

```bash
kubectl -n hugegraph wait --for=condition=Ready \
  pod/hugegraph-store-<ordinal> --timeout=10m
```

然后从 PD leader 逐组检查分片成员与 leader（找 leader 的方法见下文"灾难恢复"）：

```bash
curl -s -u "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/shardGroups | jq '
  .shardGroups[] | {id: (.id // 0),
                    shards: [.shards[] | {storeId, role}],
                    leaders: [.shards[] | select(.role=="Leader")] | length}'
```

只有当被替换的 Pod 已 `Ready`、它的 Store id 在 `/v1/stores` 里显示新的 `lastHeartBeat`、且每个分片组都报告
完整分片数和恰好一个 `Leader` 时，才删除下一个 Store。

要清楚这证明不了什么：分片列表是 PD 的成员记录，不代表该 Store 已追上 raft 日志。当前镜像没有任何端点报告"恢复
完成"。想看得更近，port-forward 被替换的 Store，读它自己对某个分片组的视图：`GET :8520/v1/partition/<groupId>`
返回该 Store 持有的 raft 角色、term 和已提交 index，Store 停机时会失败；term 和 index 要与对端 Store 上的同一
组对比着看，不要单独读。复数形式的 `GET :8520/v1/partitions` 在
[apache/hugegraph#3232](https://github.com/apache/hugegraph/pull/3232)（2026-09-24 合入）之前构建的镜像上，
对任何跟随分片组的 Store 返回 500；之后的镜像对每个 Store 都返回 200，被跟随分组的 `conf` 和 `peers` 为
null。逐组路径在两类镜像上都可用。

成员检查通过后留出余量再删下一个 Pod，把 `store.pdb.minAvailable` 保持在 `replicas - 1`，意外的第二次驱逐会被
拒绝；任何缺分片或没有 leader 的分组都应视为停止信号。真正的"分区恢复完成"信号是上游工作，在
[apache/hugegraph#3229](https://github.com/apache/hugegraph/issues/3229) 跟踪。

### 7 灾难恢复

当前版本 PD 自动做的事很少：60 秒一次的巡检只把停止心跳的 Store 标为 `Offline`。没有自动副本重建；丢失 Store
的副本重新放置、按分片数校正分片组、处理 Tombstone Store，都只在显式触发分区巡检时执行。

任务端点在收到请求的那台 PD 上本地执行，follower 会返回空的成功响应但什么也不做。port-forward 客户端 Service
选中的 PD 是任意的，所以先找 leader，再 port-forward 那个 Pod（forward 在前台运行，需要第二个终端）：

```bash
kubectl port-forward -n hugegraph svc/hugegraph-pd-client 8620:8620
# 读 .data.pdLeader.raftUrl，其主机名即 leader Pod。
curl -su "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/members
# 停掉 Service 的 forward，改为 forward leader Pod。
kubectl port-forward -n hugegraph pod/<leader-pod> 8620:8620
# 校正分片组并处理 Tombstone Store。
curl -u "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/task/patrolPartitions
# 先摊平 Raft leader，再摊平分区数据。
curl -u "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/task/balanceLeaders
curl -u "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/task/balancePartitions
```

任务跑完后再读一次 `/v1/members`：如果中途 leader 迁移，后面的任务其实跑在 follower 上、什么也没做。
`balancePartitions` 之后至少等 180 秒再执行 `balanceLeaders`：`balancePartitions` 即使什么都没搬也会设置
180 秒的 balance-shard 标志，窗口内的 `balanceLeaders` 会被拒绝。在
[apache/hugegraph#3233](https://github.com/apache/hugegraph/pull/3233)（2026-09-24 合入）之前构建的镜像上，
拒绝表现为裸的 HTTP 500，原因只在 PD 日志里；之后的镜像把原因放进响应体：
`{"status":1001,"error":"balance shard is processing, please try later!"}`。

要分辨"真的执行了"和"空跑"，得看 PD leader 的日志，响应本身分辨不了：`patrolPartitions` 无论有没有修复、在
leader 还是 follower 上，都返回同样的空成功（看日志里的 `reallocShards`、`shardOffline`、`storeTurnoff`，或
对比前后的 `/v1/shardGroups`）；`balancePartitions` 在 leader 上返回 `{}`，在 follower 上返回空响应体。只有
`balanceLeaders` 的响应体携带工作内容。可区分的任务响应是上游工作，在
[apache/hugegraph#3231](https://github.com/apache/hugegraph/issues/3231) 跟踪。

替换一个回不来的 Store 之后执行 `patrolPartitions`，集群稳定后执行 `balancePartitions`，重启导致 leader 分布
倾斜后执行 `balanceLeaders`。

**丢失 Store 卷。** 带着空 PVC 重建的 Store，在携带
[apache/hugegraph#3234](https://github.com/apache/hugegraph/pull/3234)（2026-09-24 合入）的镜像上可以原地
恢复；更早的镜像，包括所有已发布版本的镜像，都不行。两种情况下替换者都会以**新的 Store ID** 注册，而 Pod 名、
DNS 名、raft 地址不变，`/v1/stores` 会在同一地址下列出两个 ID。

在含 #3234 的镜像上，退役流程是可用的：在 `/v1/stores` 里找到旧 ID（被替换 Pod 地址下不是新注册的那一行），在
PD leader 上 `POST /v1/store/<oldId>` 并携带 `{"storeState":"Tombstone"}`，执行
`GET /v1/task/patrolPartitions`，然后等待；确认每个分片组都恢复到完整分片数且恰好一个 leader、没有分组再引用
旧 ID、被替换 Store 自己的 `:8520/v1/partition/<groupId>` 对每个分组都返回 200；最后
`DELETE /v1/store/<oldId>` 清除退役记录。在 3+3+3 安装上用 `master` `dbb6663a` 构建的镜像实测：替换者 156 秒
就绪，Tombstone 加巡检之后 1 秒内 12 个分组全部收敛到新 ID（空 Store 通过 raft 快照安装追平数据），持续写入
没有丢失任何已确认的写。

在不含 #3234 的镜像上，同样的退役流程会执行但修不好分组：PD 发起配置变更，但分组 leader 看到该地址已在组内，
jraft 无可添加，分组继续记录旧 ID。实测：20 分钟、三次巡检之后，12 个分组仍全部引用退役 ID，替换 Store 不持有
任何分区。健康面板完全看不出这个故障：`/v1/stores`、集群状态、Hubble、Pod 就绪全部显示健康，而每个分片组实际
只运行在两个存活副本上。唯一能看出问题的检查是被替换 Store 自己的 `:8520/v1/partition/<groupId>`。

因此默认做法不变：替换 Store Pod 时保留它的 PVC（Store id 存在数据目录里，Pod 会以同一 id 回来）。空 PVC 替换
只作为含 #3234 镜像上的恢复手段；在已发布镜像上，卷真的丢了就当集群已降级处理，准备重建而不是原地恢复。

周期性 leader 均衡在 [apache/hugegraph#3135](https://github.com/apache/hugegraph/issues/3135) 跟踪；
灾难恢复指标在 [apache/hugegraph#3136](https://github.com/apache/hugegraph/issues/3136) 跟踪。

### 8 伸缩

PD 和 Store 在资源名里为最大 StatefulSet 序号预留了空间，伸缩不会改名 PersistentVolumeClaim、不会移动 Pod
身份；两者上限都是 99 副本。Server 通过 `server.replicas` 或 `server.hpa` 自由伸缩（HPA 开启时 Deployment
省略 `spec.replicas`，升级不会覆盖自动扩缩的副本数）。

分阶段上线没法写进 values 文件（schema 要求每个组件至少一个副本）；用 `kubectl scale statefulset
hugegraph-store --replicas=0` 分阶段，准备好后再扩回来。Server 会保持未就绪等待 Store 注册，下一次
`helm upgrade` 会按 values 恢复完整拓扑。

修改线上 release 的 PD 或 Store 副本数不是普通的 values 变更：raft 与分片成员关系是持久化的，Pod 本身不会
重新配置它们。chart 通过读取线上 StatefulSet 拒绝 PD 的双向变更和 Store 的缩容，全新安装不受影响。

**PD，双向。** chart 渲染的对端列表只作为 raft 的引导配置生效，已初始化的组会忽略它：3 扩到 5 只是多起两个
PD，投票配置仍是三个；3 缩到 1 直接失去多数派。成员变更走 PD 客户端 API（没有 REST 路由），chart 无法代劳。
先通过 PD 改成员、在 `/v1/members` 确认新配置、`kubectl scale` 线上 StatefulSet、再用匹配的 values 执行
`helm upgrade`；在你自己的构建上验证过这套流程之前，请按打算长期保留的 PD 数量安装。

**Store，缩容。** 迁出是状态转换，不是均衡：`patrolPartitions` 和 `balancePartitions` 都不会退役健康的
Store。像灾难恢复退役被替换 Store 那样退役要下线的 Store：

1. 确认剩余 Store 仍能承载持久化的分片数（`pd.partition.defaultShardCount`；留空时 `store.replicas` 不低于
   3 推导为 3）。
2. 通过 `/v1/stores` 按 Pod 地址把要删除的序号（最大的几个）映射到 Store id。
3. 对每个要下线的 id `POST /v1/store/<id>`，携带 `{"storeState":"Tombstone"}`。
4. 等到 `/v1/shardGroups` 不再列出这些 id，且每个分组都报告完整分片数和一个 leader。
5. `kubectl scale` 线上 StatefulSet，再用匹配的 values 执行 `helm upgrade`。

删除被移除序号的 PVC 是独立且不可逆的操作；只在第 4 步确认数据已迁走之后再做。

### 9 在集群外运行 Hubble

集群内 Hubble（`hubble.enabled=true` 加 port-forward）是推荐路径，部署页已覆盖。Hubble 必须在集群外运行时有
两条路径。

**直连 Server URL**（图、schema、数据、Gremlin；不需要 PD 发现）：关闭 chart 内的 Hubble，暴露 Server
（`server.service.type` NodePort/LoadBalancer，或 Ingress），用如下配置运行独立的 Hubble 镜像：

```properties
pd.enabled=false
server.direct_url=https://<reachable-server-host>:<port>
```

配置文件挂载到镜像内的 `/hubble/conf/hugegraph-hubble.properties`（工作目录是 `/hubble`）。
`server.direct_url` 要用 HTTPS 或可信通道：登录会把 Server 凭据发到这个 URL。

**PD 发现**（集群外的 Hubble 向 PD 询问 Server 地址）：`*.svc` 这类集群内名字在外部不可解析，chart 提供两个
配置项。把 `server.advertiseUrl` 设为外部 Hubble 发现后要使用的绝对 `http(s)://` URL，chart 会用它替代集群内
Service URL 注册到 PD。再暴露 PD 客户端 Service（`pd.service.type` NodePort/LoadBalancer），这需要
`pd.service.allowInsecureExposure=true`，因为 PD gRPC 没有认证；先限制谁能访问它（chart 的 NetworkPolicy
开启时，调用方没有列入 `networkPolicy.pd.extraIngress` 前渲染会拒绝这种暴露）。然后用如下配置运行独立
Hubble：

```properties
pd.enabled=true
pd.peers=<reachable-pd-host>:<grpc-port>
pd.server=<reachable-pd-host>:<rest-port>
```

取舍：设置 `server.advertiseUrl` 后，每个 Server 副本注册的都是同一个逻辑 URL，PD 会把它返回给所有发现客户
端，包括集群内的 Hubble。留空则走默认的集群内路径，每个 Server Pod 注册自己的 IP。

本机快速验证（集群和 Hubble 在同一台机器）：port-forward Server `8080` 和 PD 客户端 `8620`/`8686`，设置
`server.advertiseUrl=http://127.0.0.1:8080`，用 `--network host` 和上面的 PD 配置运行独立 Hubble，再打开
`8088` 端口。

### 10 Gremlin 报 "Could not rebind" 时

这个报错有两个成因，持续时间不同。

**建图后的收敛窗口。** 处理 `CreateGraph` 的 Server 会等自己的 Gremlin 绑定完成才返回 HTTP 200
（[#3138](https://github.com/apache/hugegraph/pull/3138)），所以在同一个 Server 上建图后立即查询是可靠的。
其他副本独立收敛，在完成之前，经负载均衡 Service 路由到未收敛副本的 Gremlin 查询可能报 400，如
`Could not rebind [g]`。带退避重试（窗口通常几秒内关闭），对"建图后立即验证"的流程用会话粘滞或
port-forward，或先在每个副本上轮询 `/graphs` 再放开查询流量。集群级就绪在
[#3137](https://github.com/apache/hugegraph/issues/3137) 跟踪。

**在 PD 滚动期间启动的 Server Pod。** Gremlin Server 只在启动时实例化一次图；那一刻 PD 客户端连不上的话，
这个 Pod 会终身通过就绪探测、正常提供 REST，而每个发到它的 Gremlin 请求都报 `Could not rebind [graph]`。
它的 `hugegraph-server.log` 会写明：

```
Graph [DEFAULT-hugegraph] configured at [...] could not be instantiated and
will not be available in Gremlin Server
```

任何同时滚动了 PD 和 Server 的升级之后，逐个检查 Server Pod 的 Gremlin（镜像不带 curl，逐个 port-forward）：

```bash
kubectl port-forward -n hugegraph pod/<server-pod> 8080:8080
curl -s --compressed -u "admin:${PASSWORD}" -H 'Content-Type: application/json' \
  -X POST http://127.0.0.1:8080/gremlin \
  -d '{"gremlin":"graph.traversal().V().limit(1).count()","aliases":{"graph":"DEFAULT-hugegraph"}}'
```

健康的 Pod 返回 `result.data`；返回 `Could not rebind` 的 Pod 直接删除。只要 PD 稳定，替换者会正常完成绑定
（实测：与 PD 滚动重叠的 12 次 Server 启动中 4 次命中，每次删除后都恢复）。
