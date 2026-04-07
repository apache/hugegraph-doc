---
title: "HugeGraph-Store Quick Start"
linkTitle: "安装/构建 HugeGraph-Store"
weight: 3
---

### 1 HugeGraph-Store 概述

HugeGraph-Store 是 HugeGraph 分布式版本的存储节点组件，负责实际存储和管理图数据。它与 HugeGraph-PD 协同工作，共同构成 HugeGraph 的分布式存储引擎，提供高可用性和水平扩展能力。

### 2 依赖

#### 2.1 前置条件

- 操作系统：Linux 或 macOS（Windows 尚未经过完整测试）
- Java 版本：≥ 11
- Maven 版本：≥ 3.5.0
- 如需进行多节点部署，请先部署 HugeGraph-PD

### 3 部署

有两种方式可以部署 HugeGraph-Store 组件：

- 方式 1：下载 tar 包
- 方式 2：源码编译

#### 3.1 下载 tar 包

从 Apache HugeGraph 官方下载页面下载最新版本的 HugeGraph-Store：

```bash
# 用最新版本号替换 {version}，例如 1.5.0
wget https://downloads.apache.org/hugegraph/{version}/apache-hugegraph-incubating-{version}.tar.gz  
tar zxf apache-hugegraph-incubating-{version}.tar.gz
cd apache-hugegraph-incubating-{version}/apache-hugegraph-hstore-incubating-{version}
```

#### 3.2 源码编译

```bash
# 1. 克隆源代码
git clone https://github.com/apache/hugegraph.git

# 2. 编译项目
cd hugegraph
mvn clean install -DskipTests=true

# 3. 编译成功后，Store 模块的构建产物将位于
#    apache-hugegraph-incubating-{version}/apache-hugegraph-hstore-incubating-{version}
#    target/apache-hugegraph-incubating-{version}.tar.gz
```

#### 3.3 Docker 部署

HugeGraph-Store Docker 镜像已发布在 Docker Hub，镜像名是 `hugegraph/store`。

> 注: 后续步骤皆假设你本地**已拉取** `hugegraph` 主仓库代码 (至少是 docker 目录)

使用 docker-compose 文件部署完整的 3 节点集群（PD + Store + Server）：

```bash
cd hugegraph/docker
# 注意版本号请随时保持更新 → 1.x.0
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

| 变量 | 必填 | 默认值 | 描述 |
|------|------|--------|------|
| `HG_STORE_PD_ADDRESS` | 是 | — | PD gRPC 地址（如 `pd0:8686,pd1:8686,pd2:8686`） |
| `HG_STORE_GRPC_HOST` | 是 | — | 本节点的 gRPC 主机名/IP（如 `store0`） |
| `HG_STORE_RAFT_ADDRESS` | 是 | — | 本节点的 Raft 地址（如 `store0:8510`） |
| `HG_STORE_GRPC_PORT` | 否 | `8500` | gRPC 服务端口 |
| `HG_STORE_REST_PORT` | 否 | `8520` | REST API 端口 |
| `HG_STORE_DATA_PATH` | 否 | `/hugegraph-store/storage` | 数据存储路径 |

> **注意**：在 Docker 桥接网络中，`HG_STORE_GRPC_HOST` 应使用容器主机名（如 `store0`）而非 IP 地址。

> **已弃用的别名**：`PD_ADDRESS`、`GRPC_HOST`、`RAFT_ADDRESS` 仍可使用，但会输出弃用警告。新部署请使用 `HG_STORE_*` 名称。

### 4 配置

Store 的主要配置文件为 `conf/application.yml`，以下是关键配置项：

```yaml
pdserver:
  # PD 服务地址，多个 PD 地址用逗号分割（配置 PD 的 gRPC 端口）
  address: 127.0.0.1:8686

grpc:
  # gRPC 的服务地址
  host: 127.0.0.1
  port: 8500
  netty-server:
    max-inbound-message-size: 1000MB

raft:
  # raft 缓存队列大小
  disruptorBufferSize: 1024
  address: 127.0.0.1:8510
  max-log-file-size: 600000000000
  # 快照生成时间间隔，单位秒
  snapshotInterval: 1800

server:
  # REST 服务地址
  port: 8520

app:
  # 存储路径，支持多个路径，逗号分割
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

对于多节点部署，需要为每个 Store 节点修改以下配置：

1. 每个节点的 `grpc.port`（RPC 端口）
2. 每个节点的 `raft.address`（Raft 协议端口）
3. 每个节点的 `server.port`（REST 端口）
4. 每个节点的 `app.data-path`（数据存储路径）

### 5 启动与停止

#### 5.1 启动 Store

确保 PD 服务已经启动，然后在 Store 安装目录下执行：

```bash
./bin/start-hugegraph-store.sh
```

启动成功后，可以在 `logs/hugegraph-store-server.log` 中看到类似以下的日志：

```
YYYY-mm-dd xx:xx:xx [main] [INFO] o.a.h.s.n.StoreNodeApplication - Started StoreNodeApplication in x.xxx seconds (JVM running for x.xxx)
```

#### 5.2 停止 Store

在 Store 安装目录下执行：

```bash
./bin/stop-hugegraph-store.sh
```

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

#### 6.3 Docker 分布式集群配置

3 节点 Store 集群包含在 `docker/docker-compose-3pd-3store-3server.yml` 中。每个 Store 节点拥有独立的主机名和环境变量：

```yaml
# store0
HG_STORE_PD_ADDRESS: pd0:8686,pd1:8686,pd2:8686
HG_STORE_GRPC_HOST: store0
HG_STORE_GRPC_PORT: "8500"
HG_STORE_REST_PORT: "8520"
HG_STORE_RAFT_ADDRESS: store0:8510
HG_STORE_DATA_PATH: /hugegraph-store/storage

# store1
HG_STORE_PD_ADDRESS: pd0:8686,pd1:8686,pd2:8686
HG_STORE_GRPC_HOST: store1
HG_STORE_RAFT_ADDRESS: store1:8510

# store2
HG_STORE_PD_ADDRESS: pd0:8686,pd1:8686,pd2:8686
HG_STORE_GRPC_HOST: store2
HG_STORE_RAFT_ADDRESS: store2:8510
```

Store 节点仅在所有 PD 节点通过健康检查后才会启动，其中 docker-compose 中的 healthcheck 实际访问的是 PD 的 REST 接口 `/v1/health`（也可以通过 Actuator 暴露的 `/actuator/health` 进行手动检查），并通过 `depends_on: condition: service_healthy` 强制执行依赖关系。

运行时日志可通过 `docker logs <container-name>`（如 `docker logs hg-store0`）直接查看，无需进入容器。

完整的部署指南请参阅 [docker/README.md](https://github.com/apache/hugegraph/blob/master/docker/README.md)。

### 7 验证 Store 服务

确认 Store 服务是否正常运行：

```bash
curl http://localhost:8520/actuator/health
```

如果返回 `{"status":"UP"}`，则表示 Store 服务已成功启动。

此外，可以通过 PD 的 API 查看集群中的 Store 节点状态：

```bash
curl http://localhost:8620/v1/stores
```

如果 Store 配置成功，上述接口响应中应包含当前节点的状态信息，其中 `state` 为 `Up` 表示节点运行正常。

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
        "deployPath": "/Users/{your_user_name}/hugegraph/apache-hugegraph-incubating-1.5.0/apache-hugegraph-store-incubating-1.5.0/lib/hg-store-node-1.5.0.jar",
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
