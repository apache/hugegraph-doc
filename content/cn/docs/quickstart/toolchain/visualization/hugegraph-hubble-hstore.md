---
title: "使用 Hubble 管理 HStore 分布式集群"
description: "连接 HStore 与 PD，理解 Hubble 的图空间、Schema 模板、集群拓扑和节点指标。"
linkTitle: "Hubble 分布式补充"
weight: 2
search_keywords: [HugeGraph Hubble, HStore, PD, GraphSpace, 集群管理]
---

本篇补充 HStore + PD 部署与单机 RocksDB 的差异。建模、导入和查询的通用操作见
[Hubble 基础与单机指南](/cn/docs/quickstart/toolchain/hugegraph-hubble/)。
内容以 Toolchain `master` 为准；本篇配置与功能经源码核查，未进行分布式环境运行验证。

主仓库的 [docker/docker-compose-hstore.yml](https://github.com/apache/hugegraph/blob/master/docker/docker-compose-hstore.yml)
已提供 PD、Store、Server 与 Hubble 的组合。按同目录 [Docker README](https://github.com/apache/hugegraph/blob/master/docker/README.md)
准备 `.env` 和生成的 Hubble 本地配置，再从 `docker/` 目录启动；不要另维护一份部署 YAML。
下文配置用于解释连接差异，不能替代 README 中 PD 凭据及服务就绪的要求。

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

## 先选择图空间，再操作图

GraphSpace（图空间）用于组织图及其访问权限。PD 模式下，先在图概览选择有权访问的图空间，
再进入其中的图进行建模、导入或查询。切换图空间后，应重新确认当前图，避免在同名图之间误操作。

启用 Server 认证时，图空间列表按账号权限展示。支持图空间权限预设的 Server 可以通过 Hubble 账号管理分配权限；
仅启用 `pd.enabled` 不会授予管理权限。认证配置见 [Server 认证与授权](/cn/docs/config/config-authentication/)。

**用户 Schema 模板仅适用于 PD 模式**。模板按图空间保存 Groovy Schema，可在创建图时复用。
创建模板需要该空间的写权限；更新或删除还要求模板所有者或相应管理权限。
它与基础指南中的内置示例数据不同，单机模式不提供用户模板管理。

## 查看集群与节点

集群概览将 Server、PD、Store 放在同一拓扑中，展示节点状态及可获取的分区等集群信息。
节点列表支持筛选；进入节点详情后，可查看上游提供的 JVM、CPU、内存、后端或分区指标。
不同组件和版本提供的指标不同，缺失、过期或采集失败会单独标注，不能将空值理解为零。

开启 Server 认证时，集群运维读取要求 `ADMIN` 级别；图空间写权限并不等于集群运维权限。
匿名 Server 模式下也可读取运维信息，因此部署时应限制 Hubble 与上游端口的网络访问。

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
