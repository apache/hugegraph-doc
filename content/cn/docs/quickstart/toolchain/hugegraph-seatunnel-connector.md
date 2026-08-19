---
title: "HugeGraph-SeaTunnel Connector Quick Start"
linkTitle: "使用 SeaTunnel Connector 同步数据"
weight: 5
---

<!--
  TODO(apache/hugegraph-doc#464)：本文 SeaTunnel 官方文档链接暂指向 latest（无版本号）页面。
  HugeGraph Source Connector 尚未随正式版本发布，官网 latest 无对应页面，
  故 Source 文档链接暂指向 GitHub dev 分支文件。
  待 Source 随正式版本发布后，将链接切换为官网版本化地址，
  例如 https://seatunnel.apache.org/docs/2.3.14/connectors/source/HugeGraph/
-->

### 1 HugeGraph-SeaTunnel Connector 概述

[Apache SeaTunnel](https://seatunnel.apache.org/) 是开源数据集成平台，批处理、流式同步都支持，自带 100+ 连接器。HugeGraph 的 Connector-V2 已经合入：

| 组件 | 状态 | 能力 |
|------|------|------|
| HugeGraph Sink | ✅ 已发布（2.3.12 起合入） | 外部数据写入 HugeGraph：顶点/边批量写入、更新、删除 |
| HugeGraph Source | 🚧 开发中（仅 next 分支） | 从 HugeGraph 读数据：顶点/边批量读取、整图迁移 |

![HugeGraph + SeaTunnel 数据集成架构图](/cn/docs/images/seatunnel/hugegraph-seatunnel-architecture.png)

### 2 选型：SeaTunnel 还是 Loader

可以把 SeaTunnel 理解为 [Loader](/cn/docs/quickstart/toolchain/hugegraph-loader) + [Tools](/cn/docs/quickstart/toolchain/hugegraph-tools) 的合集。两者不冲突：Loader 只管 HugeGraph，开箱即用；SeaTunnel 面向所有数据系统。按场景选：

| 你的场景 | 推荐 | 理由 |
|---------|------|------|
| 一次性 / 定时把本地文件、HDFS、MySQL 等导入 HugeGraph | Loader | 免部署，映射文件即写即用 |
| 数据已在（或必须经过）Flink、Spark、Kafka 等大数据管道 | SeaTunnel | 复用现有管道，不引入第二套导入工具 |
| 实时流式导入、CDC 增量同步 | SeaTunnel | 原生流式作业 + checkpoint 断点恢复 |
| 导入时自动创建 Schema（PropertyKey / VertexLabel / EdgeLabel） | SeaTunnel | Sink 默认 `CREATE_SCHEMA_WHEN_NOT_EXIST` |
| 只维护 HugeGraph 一张图，规模可控、追求简单 | Loader | 工具链内闭环，无额外集群 |

选 SeaTunnel 要接受两点：部署一套 SeaTunnel 集群（或复用现有的），作业用通用 HOCON 配置，而不是 HugeGraph 映射文件。

### 3 快速开始

前置条件：HugeGraph Server 1.5.0+（[部署指南](/cn/docs/quickstart/hugegraph/hugegraph-server)）、SeaTunnel 2.3.13+。

#### 3.1 安装 HugeGraph 连接器插件

```bash
sh bin/install-plugin.sh 2.3.13
```

#### 3.2 最小示例：FakeSource → person 顶点

```hocon
env {
  job.mode = "BATCH"
}

source {
  FakeSource {
    plugin_output = "fake"
    row.num = 3
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
    # 以下为可选参数，默认值见第 5 节；认证开启时再填 username/password
    # protocol = "http"
    # graph_space = "DEFAULT"
    # username = "admin"
    # password = "admin"
    # schema_save_mode = CREATE_SCHEMA_WHEN_NOT_EXIST
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

一条输入行到图顶点的映射过程：

```text
┌───────────────── 输入行 (SeaTunnel Row) ─────────────────┐
│  name = "marko"        age = 29                          │
└──────────────────────────┬───────────────────────────────┘
                           │ mappings:
                           │   type = VERTEX, label = person
                           │   idStrategy = PRIMARY_KEY, idFields = [name]
                           ▼
                 ┌───────────────────────────────┐
                 │ HugeGraph 顶点                 │
                 │ id   = person:marko           │
                 │ label = person                │
                 │ props = { age: 29 }           │
                 └───────────────────────────────┘
```

#### 3.3 运行与验证

```bash
sh bin/seatunnel.sh --config ./config/hugegraph-sync.conf -e local
```

运行后，在 Hubble 或 REST API 里执行这条 Gremlin 验证：

```groovy
g.V().hasLabel('person').valueMap()
```

> **Schema 说明**：`mappings` 模式下默认 `schema_save_mode = CREATE_SCHEMA_WHEN_NOT_EXIST`，写入前自动补建缺失的 PropertyKey / VertexLabel / EdgeLabel。要严格管控就自己先建 Schema，并设 `ERROR_WHEN_SCHEMA_NOT_EXIST`。

#### 3.4 写入边

关系行到边的映射同样通过 `mappings` 完成，用 `sourceConfig` / `targetConfig` 还原边的两个端点：

<details>
<summary>展开查看：关系表 → knows 边 完整配置</summary>

```hocon
env {
  job.mode = "BATCH"
}

source {
  FakeSource {
    plugin_output = "fake"
    row.num = 3
    schema = {
      fields = {
        person1_name = "string"
        person2_name = "string"
        since = "int"
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

</details>

```text
person1_name = "marko"   person2_name = "vadas"   since = 2020
        │                        │
        ▼                        ▼
  sourceConfig             targetConfig
  label = person           label = person
  idFields = [person1_name] idFields = [person2_name]
        └───────────┬────────────┘
                    ▼
      edge: person:marko -[knows]-> person:vadas
      properties = { since: 2020 }
```

> 边的端点 ID 策略从服务端已有的 VertexLabel 读取，`sourceConfig.idFields` / `targetConfig.idFields` 必须能拼出端点 ID。默认 `check_vertex = false`，顶点和边允许乱序写入，跑完图最终一致；设成 `true` 则服务端直接拒绝端点不存在的边。

### 4 常见场景

#### 4.1 Kafka 实时流导入

```mermaid
flowchart LR
    P["业务系统"] --> K[("Kafka Topic")]
    K -->|"STREAMING + checkpoint"| ST["SeaTunnel<br/>Kafka Source → HugeGraph Sink"]
    ST --> HG[("HugeGraph Server")]
```

<details>
<summary>展开查看：Kafka → HugeGraph 流式作业配置</summary>

```hocon
env {
  job.mode = "STREAMING"
  checkpoint.interval = 10000
}

source {
  Kafka {
    bootstrap.servers = "localhost:9092"
    topics = "user-events"
    consumer.group = "hugegraph-import"
    format = json
    schema = {
      fields = {
        name = "string"
        age = "int"
      }
    }
    plugin_output = "kafka_events"
  }
}

sink {
  HugeGraph {
    plugin_input = "kafka_events"
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

</details>

> 要点：`job.mode = "STREAMING"` 加 `checkpoint.interval`，任务就能断点恢复。Sink 是 at-least-once 语义，`PRIMARY_KEY` / `CUSTOMIZE_*` 这类可还原的 ID 重放只是幂等更新。Kafka 的 offset、分区、format 等参数见 [Kafka Source 官方文档](https://seatunnel.apache.org/docs/connectors/source/Kafka/)。

#### 4.2 在 Flink / Spark 引擎上运行

SeaTunnel 有三种执行引擎：**Zeta**（默认、自带）、**Flink**、**Spark**。连接器与引擎无关，同一份配置换引擎提交即可，内容不用改：

```mermaid
flowchart LR
    J["作业配置 job.conf<br/>（与引擎无关）"] --> E{"选择执行引擎"}
    E -->|"默认"| Z["SeaTunnel Zeta"]
    E -->|"已有 Flink 集群"| F["Apache Flink"]
    E -->|"已有 Spark 集群"| S["Apache Spark"]
    Z --> HG[("HugeGraph")]
    F --> HG
    S --> HG
```

```bash
# Zeta（默认，推荐）
sh bin/seatunnel.sh --config ./config/hugegraph-sync.conf -e local

# Spark 3 引擎（集群版将 --master 改为 yarn / k8s 地址）
sh bin/start-seatunnel-spark-3-connector-v2.sh --master local[4] --deploy-mode client --config ./config/hugegraph-sync.conf

# Flink 引擎（需本机已安装 Flink 客户端）
sh bin/start-seatunnel-flink-2-connector-v2.sh --config ./config/hugegraph-sync.conf
```

> Flink / Spark 引擎要用与集群版本匹配的 starter 脚本和 translation jar，支持矩阵见官方 [Flink 引擎文档](https://seatunnel.apache.org/docs/engines/flink/) 与 [Spark 引擎文档](https://seatunnel.apache.org/docs/engines/spark/)。社区新特性优先在 Zeta 验证；没有现成 Flink/Spark 集群就直接用 Zeta。

#### 4.3 HugeGraph → HugeGraph 图迁移（Source Connector，next 分支）

```mermaid
flowchart LR
    A[("HugeGraph 源实例")] -->|"Source 批量读取"| ST["SeaTunnel"]
    ST -->|"Sink 批量写入"| B[("HugeGraph 目标实例")]
```

<details>
<summary>展开查看：图迁移作业配置（需 next 版本 SeaTunnel）</summary>

```hocon
env {
  job.mode = "BATCH"
}

source {
  HugeGraph {
    host = "127.0.0.1"
    port = 8080
    graph_name = "hugegraph"
    label = "person"
    label_type = "VERTEX"
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
    host = "127.0.0.2"
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

</details>

> 克隆边时，Source 输出自带保留列 `~source_id` / `~target_id`，Sink 直接配 `sourceConfig.idFields = ["~source_id"]`、`targetConfig.idFields = ["~target_id"]` 就能复用，不用重新拼 ID。Source 还支持省略 `label` 读全量、`parallelism > 1` 分片并行，详见 [HugeGraph Source 文档](https://github.com/apache/seatunnel/blob/dev/docs/zh/connectors/source/HugeGraph.md)。

### 5 核心配置参数

常用参数如下，完整列表见 [官方文档](https://seatunnel.apache.org/docs/connectors/sink/HugeGraph/)：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `host` | String | 是 | - | HugeGraph Server 地址 |
| `port` | Integer | 是 | - | HugeGraph Server 端口 |
| `graph_name` | String | 是 | - | 图名称 |
| `mappings` | List | 是 | - | 顶点/边映射配置，每项一个 label |
| `protocol` | String | 否 | `http` | 服务协议，支持 `http` / `https` |
| `graph_space` | String | 否 | `DEFAULT` | 图空间 |
| `username` | String | 否 | - | 认证用户名（服务端开启认证时必填） |
| `password` | String | 否 | - | 认证密码（服务端开启认证时必填） |
| `schema_save_mode` | Enum | 否 | `CREATE_SCHEMA_WHEN_NOT_EXIST` | 缺失 Schema 时自动建；`ERROR_WHEN_SCHEMA_NOT_EXIST` 则报错 |
| `data_save_mode` | Enum | 否 | `APPEND_DATA` | `APPEND_DATA` 保留已有数据；`DROP_DATA` 仅清空本任务涉及的 label |
| `batch_size` | Integer | 否 | 500 | 单批写入前缓冲的记录数 |
| `batch_interval_ms` | Integer | 否 | 5000 | 刷新批次的最大等待时间（毫秒） |
| `check_vertex` | Boolean | 否 | false | 写边时校验端点是否存在，开启后拒绝孤儿边 |
| `max_retries` | Integer | 否 | 3 | 请求失败后的重试次数 |
| `retry_backoff_ms` | Integer | 否 | 5000 | 重试基础退避时间（毫秒），指数增长 |

mappings 每项的常用字段：`type`、`label`、`properties`、`idStrategy` / `idFields`（顶点）、`sourceConfig` / `targetConfig`（边）、`fieldMapping`、`ttl`、`updateStrategies`，详见 [官方文档](https://seatunnel.apache.org/docs/connectors/sink/HugeGraph/)。

### 6 版本与兼容性

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Java | 11+ | HugeGraph Client 1.5.0+ 运行环境要求 |
| Apache SeaTunnel | 2.3.13+（推荐） | Sink 自 2.3.12 合入；2.3.13 起内置 HugeGraph Client 1.5.0 |
| HugeGraph Server | 1.5.0+ | 需与 Connector 内置 Client 版本匹配 |

> **Source Connector 说明**：Source 目前只在 SeaTunnel next（dev）分支，正式版还没带。要用就从源码编译，或等下一个 Release；next 分支内置的 HugeGraph Client 已升到 1.7.0，需搭配对应版本的 Server。

### 7 文档与资源

- [Apache SeaTunnel 官方网站](https://seatunnel.apache.org/)
- [HugeGraph Sink Connector 官方文档](https://seatunnel.apache.org/docs/connectors/sink/HugeGraph/)
- [HugeGraph Source Connector 官方文档](https://github.com/apache/seatunnel/blob/dev/docs/zh/connectors/source/HugeGraph.md)
- [Apache SeaTunnel GitHub](https://github.com/apache/seatunnel)
- [HugeGraph GitHub](https://github.com/apache/hugegraph)

### 8 许可证

与 HugeGraph 一样，HugeGraph-SeaTunnel Connector 采用 Apache 2.0 许可证。
