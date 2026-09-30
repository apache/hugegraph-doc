---
title: "使用 Hubble 管理 HStore 分布式集群"
description: "连接 HStore 与 PD，理解 Hubble 的图空间、Schema 模板、集群拓扑和节点指标。"
linkTitle: "Hubble 分布式补充"
weight: 2
search_keywords: [HugeGraph Hubble, HStore, PD, GraphSpace, 集群管理]
---

本篇补充 HStore + PD 部署与单机 RocksDB 的差异。建模、导入和查询的通用操作见
[Hubble 基础与单机指南](/cn/docs/quickstart/toolchain/hugegraph-hubble/)。
内容以 Toolchain `master` 为准。

主仓库的 [docker/docker-compose-hstore.yml](https://github.com/apache/hugegraph/blob/master/docker/docker-compose-hstore.yml)
已提供 PD、Store、Server 与 Hubble 的组合。按同目录 [Docker README](https://github.com/apache/hugegraph/blob/master/docker/README.md)
准备 `.env` 和生成的 Hubble 本地配置，再从 `docker/` 目录启动；不要另维护一份部署 YAML。
下文配置用于解释连接差异，不能替代 README 中 PD 凭据及服务就绪的要求。
图中的组合使用 Hubble `1.8.0` 与 Server、PD、Store `1.7.0`；不同版本可提供的指标和权限接口有所区别。

## 连接分布式集群

Hubble 仍通过 **Server 的图 API** 管理数据。区别在于，分布式模式通过 PD 发现 Server，
同时从 PD 和 Store 获取集群信息；Hubble 不直接读写 Store 中的图数据。

先按 [PD 部署指南](/cn/docs/quickstart/hugegraph/hugegraph-pd/) 和
[HStore 部署指南](/cn/docs/quickstart/hugegraph/hugegraph-hstore/) 启动匹配版本的 PD、Store 和 Server，
确认 Server 已注册、Store 已就绪，再修改 Hubble 的 `conf/hugegraph-hubble.properties`。
下面的主机名仅演示同一容器网络中的最小拓扑，请替换成 Hubble 后端实际可达的地址：

```properties
pd.enabled=true
cluster=hg
pd.peers=pd:8686
pd.server=pd:8620
```

| 配置 | 用途 | 随包配置值 |
|---|---|---|
| `pd.enabled` | 显式启用 PD 模式；此时不使用 `server.direct_url`。 | `false` |
| `cluster` | 用于 Server 服务发现的集群名称，应与注册信息一致。 | `hg` |
| `pd.peers` | PD **gRPC** 地址；多个地址用逗号分隔。 | `127.0.0.1:8686` |
| `pd.server` | 集群运维使用的 PD **REST** 地址，不是 gRPC peer 列表。 | `127.0.0.1:8620` |

不要把 `8686` 和 `8620` 混用，也不要在跨容器连接时保留 `127.0.0.1`。
随包文件显式设置 `pd.enabled=false`，而该键缺失时 Java 默认值是 `true`，因此两种部署都应显式设置它。
修改配置后重启 Hubble；页面无需逐图填写 Server 主机和端口。

## 用图空间组织图与权限

GraphSpace（图空间）将图、Schema 模板和访问权限组织在同一个范围内。例如，分别为业务团队创建 `sales` 与 `research`，
让各团队只看到并操作自己的图。进入图空间后，图的建模、导入和查询仍沿用基础指南的流程。

### 创建与调整图空间

开启 Server 认证时，创建、编辑和删除图空间要求超级管理员权限。创建时先填写全局唯一的 GraphSpace 名称、
可选的显示别名及最大图数；例如用 `research` 作 API 标识，用“研究图谱”作显示名。GraphSpace 名称创建后不可修改，
别名和描述可随后调整，别名不参与 URL 或权限匹配。图空间管理员从已有账号中选择。

“高级部署与资源限制”包含图查询/写入服务、异步计算任务的 CPU 与内存上限，以及存储容量限制。
这些值用于部署和配额场景，不是当前资源用量，也不代表提交表单后会立即扩容 Docker 容器。
默认最大图数为 100；图服务与计算任务分别为 64 核、128 GB，存储上限为 1000000 GB。
普通容器试用可先保留默认值；Kubernetes 命名空间、Operator 和算法镜像仅在对应部署或计算场景中填写。

选择图空间后，再进入其中的图。切换空间时应重新确认当前图，尤其是不同空间中存在同名图时。
列表只显示账号可访问的空间；看不到预期空间时，先检查成员权限，不要反复新建图。

![图空间创建表单与高级资源限制入口](/cn/docs/images/hubble/graphspace.jpg)

### 复用 Schema 模板

**用户 Schema 模板仅适用于 PD 模式**，按图空间持久化保存 Groovy Schema。
当一组业务图需要同样的顶点类型、边类型和索引时，可以先保存模板，再在创建图时选择它，减少重复建模。
例如 `research` 中的用户模板用于该空间后续创建的图；切换到另一个空间后，应重新选择该空间的模板。

用户模板与主篇的内置示例模板不同：内置模板用于快速体验预设模型，用户模板用于保存自己的模型并长期复用。
模板本身不等于导入数据；是否加载示例数据是创建图时的另一个选择。
开启 Server 认证时，创建用户模板需要所在空间的写权限，更新或删除还要求模板所有者或相应管理权限。
匿名模式不进行按用户的权限与模板所有者检查。
单机模式不提供用户模板管理。

## 给用户分配图空间权限

账号创建、登录和个人资料管理见[基础指南](/cn/docs/quickstart/toolchain/hugegraph-hubble/)；
分布式模式额外提供“管理 GraphSpace 成员”，在已有账号与指定空间之间分配权限。
支持权限预设的 Server 提供以下常用选择：

| 预设 | 适用对象 | 作用范围 |
|---|---|---|
| GraphSpace 只读 | 查看、查询图数据的使用者 | 所选空间。 |
| GraphSpace 读写 | 建模、导入和维护图数据的使用者 | 所选空间。 |
| GraphSpace 管理员 | 管理该空间的成员与图资源的负责人 | 所选空间，不因此获得创建/编辑图空间或集群运维权限。 |
| 超级管理员 | 管理账号、图空间及集群的运维人员 | 全局，应按实际职责分配。 |

同一账号可在不同空间拥有不同权限，例如对 `research` 读写、对 `sales` 只读。
账号与空间成员分开管理，移除成员不会删除全局账号。创建账号后可以立即继续分配空间权限；调整已有成员时，确认当前空间及预设，保留其他空间仍需要的权限。
仅启用 `pd.enabled` 不会授予权限，旧 Server 的自定义角色也不能直接当作这些预设处理。
认证配置见 [Server 认证与授权](/cn/docs/config/config-authentication/)。

![GraphSpace 成员与权限预设](/cn/docs/images/hubble/members.jpg)

## 从集群概览定位异常

集群概览用一张拓扑展示 **Server → PD → Store**，可切换节点列表按类型、状态或名称筛选。
概览中的 PD Leader、在线 Store 数、图数、分区数、副本数和数据量，帮助判断当前连接的规模及哪些节点需要关注。
分区和副本描述数据分布；数据量是采集到的用量，不是图空间配置的存储上限。

先看集群和来源状态，再进入异常节点：`UP` 表示本次采集的来源正常；`DEGRADED` 表示集群或部分来源异常；
`DOWN` 表示相应探测未成功。拓扑可用而指标部分缺失时，仍可能正常查询图。
页面会区分不支持、不可用、数据过期和采集失败，并显示采集时间；空值不是零，历史值也不等于当前状态。

![集群拓扑、节点状态与容量信息](/cn/docs/images/hubble/cluster-overview.jpg)

### 节点详情读什么

| 节点 | 主要关注信息 | 如何使用 |
|---|---|---|
| Server | 节点可用性、JVM/CPU/内存及后端指标 | 判断查询与写入入口是否可达，并检查资源压力。 |
| PD | Leader/Follower 角色、状态及上游可提供的运行指标 | 确认元数据与调度入口；Leader 信息缺失时不推断角色。 |
| Store | 分区数、Leader 分区数、系统/磁盘指标，以及 Raft 组数和启用组数 | 检查存储节点及副本服务，结合其他节点比较分布。 |

![Store 节点的系统、磁盘、Raft 和分区指标](/cn/docs/images/hubble/store-node.jpg)

PD Leader 与 Store 的 Leader 分区不是同一概念：前者协调集群元数据，后者负责相应数据分区的 Raft 组。
Hubble 展示上游提供的观测值，不代替完整的 Raft 副本一致性检查；各版本可用的指标不同。

开启 Server 认证时，集群运维读取要求超级管理员（`ADMIN` 级别），空间管理员和普通成员不会因此获得集群读取权限。
部署时使用容器隔离、可信 HTTPS 入口、Server 认证与网络白名单，避免直接公开 Hubble 和组件端口。

### 配置运维访问

PD/Store 的运维凭据由 Hubble **后端**使用，与浏览器登录 Server 的账号分开。
在实际配置文件中填写部署对应的凭据，不要把密码写进文档、截图或提交的配置：

| 配置 | 随包默认值 | 设置方式 |
|---|---|---|
| `operations.pd.username` / `operations.pd.password` | 用户名 `hubble`，密码为空 | 与 PD 运维 REST 认证匹配。 |
| `operations.store.username` / `operations.store.password` | 用户名 `hubble`，密码为空 | 上游 Store REST 启用认证时配置对应服务账号。 |
| `operations.store.allowed_targets` | `[http://127.0.0.1:8520,http://[::1]:8520]` | 列出信任的 Store 指标来源。 |

例如容器中的 Store 上报 `store:8520`，将白名单配置为：

```properties
operations.store.allowed_targets=[http://store:8520]
```

多节点时列出每个允许访问的来源。每项必须是带显式端口的 `http` 或 `https` origin，不能带路径、凭据或通配符，
并且应与 PD 返回的 Store 指标目标一致。仅在白名单里添加地址不会建立节点发现信息。

若拓扑可见但指标不完整，依次检查 Hubble 后端到 PD REST 的连通性与认证、PD 返回的 Store REST/指标目标，
以及目标是否与白名单一致。概览的部分可用状态表示某些来源尚未成功采集，不等同于所有图 API 都不可用。
