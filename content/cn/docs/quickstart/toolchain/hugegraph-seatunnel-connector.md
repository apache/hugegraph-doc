---
title: "HugeGraph-SeaTunnel Connector Quick Start"
linkTitle: "使用 SeaTunnel Connector 同步数据"
weight: 5
---

### 1 HugeGraph-SeaTunnel Connector 概述

[Apache SeaTunnel](https://seatunnel.apache.org/) 是一个高性能、分布式的数据集成平台，支持海量数据的实时同步与批处理。
HugeGraph 社区已向 Apache SeaTunnel 贡献了 Connector-V2 支持，用户可以通过 SeaTunnel 将 HugeGraph 与外部数据系统进行数据同步。

![HugeGraph + SeaTunnel 数据集成架构图](/cn/docs/images/seatunnel/hugegraph-seatunnel-architecture.png)

### 2 功能特性

HugeGraph-SeaTunnel Connector 提供以下能力：

- **HugeGraph Sink Connector**（已发布）：将外部数据写入 HugeGraph，支持顶点和边的批量写入、更新与删除
- **HugeGraph Source Connector**（开发中）：从 HugeGraph 读取图数据，支持顶点和边的批量读取
- **顶点同步**：支持全量或增量同步顶点数据，支持多种 ID 策略
- **边同步**：支持全量或增量同步边数据，自动关联源顶点与目标顶点
- **Schema 自动管理**：支持自动创建 PropertyKey、VertexLabel、EdgeLabel（`CREATE_SCHEMA_WHEN_NOT_EXIST`）
- **数据迁移**：支持在不同 HugeGraph 实例之间迁移数据，或从其他数据源导入图数据

![HugeGraph Source/Sink 双向数据流示意图](/cn/docs/images/seatunnel/hugegraph-seatunnel-source-sink.png)

### 3 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Java | 11+ | HugeGraph Client 1.5.0+ 运行环境要求 |
| Apache SeaTunnel | 2.3.13+ | Sink Connector 自此版本发布（内置 HugeGraph Client 1.5.0） |
| HugeGraph Server | 1.5.0+ | 需与 Connector 内置 Client 版本匹配 |

> **Source Connector 说明**：HugeGraph Source Connector 目前仅在 SeaTunnel 开发分支（Next/master）中可用，
> 尚未包含在正式 Release 中。如需使用 Source 功能，请从 SeaTunnel 源码编译或等待下一版本发布。

### 4 快速开始

#### 4.1 安装 SeaTunnel

请参考 [Apache SeaTunnel 部署指南](https://seatunnel.apache.org/docs/getting-started/) 完成 SeaTunnel 的安装部署。

#### 4.2 使用 HugeGraph Sink Connector（写入数据）

以下示例展示如何通过 SeaTunnel 将数据写入 HugeGraph：

**写入顶点数据：**

```hocon
env {
  job.mode = "BATCH"
}

source {
  FakeSource {
    plugin_output = "fake"
    schema = {
      fields = {
        name = "string"
        age = "int"
      }
    }
  }
}

sink {
  HugeGraph {
    host = "127.0.0.1"
    port = 8080
    graph_name = "hugegraph"
    mappings = [
      {
        type = "VERTEX"
        label = "person"
        idStrategy = "PRIMARY_KEY"
        idFields = ["name"]
        properties = ["name", "age"]
      }
    ]
  }
}
```

**写入边数据：**

```hocon
sink {
  HugeGraph {
    host = "127.0.0.1"
    port = 8080
    graph_name = "hugegraph"
    mappings = [
      {
        type = "EDGE"
        label = "knows"
        sourceConfig = {
          label = "person"
          idFields = ["person1_name"]
        }
        targetConfig = {
          label = "person"
          idFields = ["person2_name"]
        }
        properties = ["since"]
        fieldMapping = {
          person1_name = "name"
          person2_name = "name"
        }
      }
    ]
  }
}
```

> **注意**：HugeGraph 的 Schema（PropertyKey、VertexLabel、EdgeLabel）需要在执行写入任务前预先创建，
> 或使用 `schema_save_mode = CREATE_SCHEMA_WHEN_NOT_EXIST`（默认行为）由 Connector 自动创建。

#### 4.3 核心配置参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `host` | String | 是 | - | HugeGraph Server 地址 |
| `port` | Integer | 是 | - | HugeGraph Server 端口 |
| `graph_name` | String | 是 | - | 图名称 |
| `graph_space` | String | 否 | DEFAULT | 图空间名称 |
| `username` | String | 否 | - | 认证用户名 |
| `password` | String | 否 | - | 认证密码 |
| `protocol` | String | 否 | http | 协议，可选 `http` 或 `https` |
| `batch_size` | Integer | 否 | 500 | 每批写入的记录数 |
| `batch_interval_ms` | Integer | 否 | 5000 | 批次最大等待时间（毫秒） |
| `max_retries` | Integer | 否 | 3 | 写入失败最大重试次数 |
| `retry_backoff_ms` | Integer | 否 | 5000 | 重试间隔（毫秒） |

> 完整参数列表和详细说明请参考 [Apache SeaTunnel HugeGraph Connector 官方文档](https://seatunnel.apache.org/docs/connector-v2/sink/HugeGraph/)。

### 5 文档与资源

- [Apache SeaTunnel 官方网站](https://seatunnel.apache.org/)
- [Apache SeaTunnel HugeGraph Sink Connector 文档](https://seatunnel.apache.org/docs/connector-v2/sink/HugeGraph/)
- [Apache SeaTunnel GitHub](https://github.com/apache/seatunnel)
- [HugeGraph GitHub](https://github.com/apache/hugegraph)

### 6 许可证

与 HugeGraph 一样，HugeGraph-SeaTunnel Connector 采用 Apache 2.0 许可证。
