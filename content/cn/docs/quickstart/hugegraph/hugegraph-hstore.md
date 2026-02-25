---
title: "HugeGraph-Store Quick Start"
linkTitle: "安装/构建 HugeGraph-Store"
weight: 3
---

### 1 HugeGraph-Store 概述

HugeGraph-Store 是 HugeGraph 分布式版本的存储节点组件，负责实际存储和管理图数据。它与 HugeGraph-PD 协同工作，共同构成 HugeGraph 的分布式存储引擎，提供高可用性和水平扩展能力。

### 2 依赖

#### 2.1 前置条件

- 操作系统：Linux 或 MacOS（Windows 尚未经过完整测试）
- Java 版本：≥ 11
- Maven 版本：≥ 3.5.0
- 已部署的 HugeGraph-PD（如果是多节点部署）

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
2024-xx-xx xx:xx:xx [main] [INFO] o.a.h.s.n.StoreNodeApplication - Started StoreNodeApplication in x.xxx seconds (JVM running for x.xxx)
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

如果Store配置成功，上述接口的响应中应该包含当前节点的状态信息，状态为Up表示节点正常运行，这里只展示了一个节点配置成功的响应，如果三个节点都配置成功并正在运行，响应中`storeId`列表应该包含三个id，并且`stateCountMap`中`Up`、`numOfService`、`numOfNormalService`三个字段应该为3。
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