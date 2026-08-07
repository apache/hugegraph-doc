---
title: "HugeGraph-SeaTunnel Connector Quick Start"
linkTitle: "使用 SeaTunnel Connector 同步数据"
weight: 5
---

### 1 HugeGraph-SeaTunnel Connector 概述

[Apache SeaTunnel](https://seatunnel.apache.org/) 是一个高性能、分布式的数据集成平台，支持海量数据的实时同步与批处理。
HugeGraph 为 Apache SeaTunnel 提供了 Connector-V2 支持，用户可以通过 SeaTunnel 方便地在 HugeGraph
与外部数据系统之间进行数据同步。

> **注意**：SeaTunnel Connector 由 HugeGraph 社区贡献至 Apache SeaTunnel 项目，具体使用方式请参考
> [Apache SeaTunnel 官方文档](https://seatunnel.apache.org/docs/)。

![HugeGraph + SeaTunnel 数据集成架构图](/cn/docs/images/seatunnel/hugegraph-seatunnel-architecture.png)

### 2 功能特性

HugeGraph-SeaTunnel Connector 提供以下能力：

- **HugeGraph Source Connector**：从 HugeGraph 读取图数据，支持顶点和边的批量读取
- **HugeGraph Sink Connector**：将外部数据写入 HugeGraph，支持顶点和边的批量写入
- **顶点同步**：支持全量或增量同步顶点数据
- **边同步**：支持全量或增量同步边数据
- **Schema 映射**：自动映射 HugeGraph Schema（PropertyKey、VertexLabel、EdgeLabel）与外部数据字段
- **数据迁移**：支持在不同 HugeGraph 实例之间进行数据迁移，或从其他数据源导入图数据

![HugeGraph Source/Sink 双向数据流示意图](/cn/docs/images/seatunnel/hugegraph-seatunnel-source-sink.png)

### 3 环境要求

- Java 8+
- Apache SeaTunnel 2.3.x+
- HugeGraph Server 1.0.0+

### 4 快速开始

#### 4.1 安装 SeaTunnel

请参考 [Apache SeaTunnel 安装指南](https://seatunnel.apache.org/docs/start-v2/) 完成 SeaTunnel 的部署。

#### 4.2 使用 HugeGraph Connector

HugeGraph Connector 已包含在 SeaTunnel 的 Connector-V2 生态中。在 SeaTunnel 配置文件中直接引用即可：

**从 HugeGraph 读取数据（Source）示例：**

```hocon
source {
  HugeGraph {
    url = "http://127.0.0.1:8080"
    graph = "hugegraph"
    label = "person"
    # 更多配置请参考 SeaTunnel 官方文档
  }
}
```

**向 HugeGraph 写入数据（Sink）示例：**

```hocon
sink {
  HugeGraph {
    url = "http://127.0.0.1:8080"
    graph = "hugegraph"
    # 更多配置请参考 SeaTunnel 官方文档
  }
}
```

> 完整配置参数和详细用法请参考 [Apache SeaTunnel Connector-V2 文档](https://seatunnel.apache.org/docs/connector-v2/)。

### 5 文档与资源

- [Apache SeaTunnel 官方网站](https://seatunnel.apache.org/)
- [Apache SeaTunnel Connector-V2 文档](https://seatunnel.apache.org/docs/connector-v2/)
- [Apache SeaTunnel GitHub](https://github.com/apache/seatunnel)
- [HugeGraph GitHub](https://github.com/apache/hugegraph)

### 6 许可证

与 HugeGraph 一样，HugeGraph-SeaTunnel Connector 采用 Apache 2.0 许可证。
