---
title: "HugeGraph-PD Quick Start"
linkTitle: "安装/构建 HugeGraph-PD"
weight: 2
---

### 1 HugeGraph-PD 概述

HugeGraph-PD (Placement Driver) 是 HugeGraph 分布式版本的元数据管理组件，负责管理图数据的分布和存储节点的协调。它在分布式 HugeGraph 中扮演着核心角色，维护集群状态并协调 HugeGraph-Store 存储节点。

### 2 依赖

#### 2.1 前置条件

- 操作系统：Linux 或 MacOS（Windows 尚未经过完整测试）
- Java 版本：≥ 11
- Maven 版本：≥ 3.5.0

### 3 部署

有两种方式可以部署 HugeGraph-PD 组件：

- 方式 1：下载 tar 包
- 方式 2：源码编译

#### 3.1 下载 tar 包

从 Apache HugeGraph 官方下载页面下载最新版本的 HugeGraph-PD：

```bash
# 用最新版本号替换 {version}，例如 1.5.0
wget https://downloads.apache.org/hugegraph/{version}/apache-hugegraph-incubating-{version}.tar.gz  
tar zxf apache-hugegraph-incubating-{version}.tar.gz
cd apache-hugegraph-incubating-{version}/apache-hugegraph-pd-incubating-{version}
```

#### 3.2 源码编译

```bash
# 1. 克隆源代码
git clone https://github.com/apache/hugegraph.git

# 2. 编译项目
cd hugegraph
mvn clean install -DskipTests=true

# 3. 编译成功后，PD 模块的构建产物将位于
#    apache-hugegraph-incubating-{version}/apache-hugegraph-pd-incubating-{version}
#    target/apache-hugegraph-incubating-{version}.tar.gz
```

### 4 配置

PD 的主要配置文件为 `conf/application.yml`，以下是关键配置项：

```yaml
spring:
  application:
    name: hugegraph-pd

grpc:
  # 集群模式下的 gRPC 端口
  port: 8686
  host: 127.0.0.1

server:
  # REST 服务端口号
  port: 8620

pd:
  # 存储路径
  data-path: ./pd_data
  # 自动扩容的检查周期（秒）
  patrol-interval: 1800
  # 初始 store 列表，在列表内的 store 自动激活
  initial-store-count: 1
  # store 的配置信息，格式为 IP:gRPC端口
  initial-store-list: 127.0.0.1:8500

raft:
  # 集群模式
  address: 127.0.0.1:8610
  # 集群中所有 PD 节点的 raft 地址
  peers-list: 127.0.0.1:8610

store:
  # store 下线时间（秒）。超过该时间，认为 store 永久不可用，分配副本到其他机器
  max-down-time: 172800
  # 是否开启 store 监控数据存储
  monitor_data_enabled: true
  # 监控数据的间隔
  monitor_data_interval: 1 minute
  # 监控数据的保留时间
  monitor_data_retention: 1 day
  initial-store-count: 1

partition:
  # 默认每个分区副本数
  default-shard-count: 1
  # 默认每机器最大副本数
  store-max-shard-count: 12
```

对于多节点部署，需要修改各节点的端口和地址配置，确保各节点之间能够正常通信。

### 5 启动与停止

#### 5.1 启动 PD

在 PD 安装目录下执行：

```bash
./bin/start-hugegraph-pd.sh
```

启动成功后，可以在 `logs/hugegraph-pd-stdout.log` 中看到类似以下的日志：

```
2024-xx-xx xx:xx:xx [main] [INFO] o.a.h.p.b.HugePDServer - Started HugePDServer in x.xxx seconds (JVM running for x.xxx)
```

#### 5.2 停止 PD

在 PD 安装目录下执行：

```bash
./bin/stop-hugegraph-pd.sh
```

### 6 验证

确认 PD 服务是否正常运行：

```bash
curl http://localhost:8620/actuator/health
```

如果返回 `{"status":"UP"}`，则表示 PD 服务已成功启动。
