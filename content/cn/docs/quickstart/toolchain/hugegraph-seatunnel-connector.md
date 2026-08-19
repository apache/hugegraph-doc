---
title: "HugeGraph-SeaTunnel Connector Quick Start"
linkTitle: "使用 SeaTunnel Connector 同步数据"
weight: 5
---

SeaTunnel 负责连接数据源和数据目的地。HugeGraph Connector 提供两种能力。

- `HugeGraph Sink` 把文件、数据库、Kafka 等数据写入 HugeGraph。
- `HugeGraph Source` 从 HugeGraph 读出顶点和边，目前只在 SeaTunnel `dev` 分支提供。

![SeaTunnel 与 HugeGraph 数据流总览](/cn/docs/images/seatunnel/seatunnel-overview.png)

## 1 先看版本

本文把发布版和开发版分开写。配置放错版本，任务会在启动阶段失败。

| 使用内容 | SeaTunnel 版本 | 配置方式 | 状态 |
| --- | --- | --- | --- |
| JDBC / Kafka 写入 HugeGraph | 2.3.13 | `schema_config` | 发布版 |
| HugeGraph 读取和图迁移 | 当前 `dev` | HugeGraph Source + `mappings` | 开发预览 |
| `graph2graph` | 当前 `dev` | Source + Sink | 开发预览 |

当前 `dev` 示例按 commit [`f1a1a0a`](https://github.com/apache/seatunnel/commit/f1a1a0abbe24bdac8cf23307995a78f778a3f467) 核对，固定版本的 [HugeGraph Source 文档](https://github.com/apache/seatunnel/blob/f1a1a0abbe24bdac8cf23307995a78f778a3f467/docs/zh/connectors/source/HugeGraph.md) 和 [HugeGraph Sink 文档](https://github.com/apache/seatunnel/blob/f1a1a0abbe24bdac8cf23307995a78f778a3f467/docs/zh/connectors/sink/HugeGraph.md) 与本文对应。`dev` 会继续变化，使用新版本前请重新核对配置。

2.3.13 的 HugeGraph Sink 使用 `schema_config`，这个版本没有 HugeGraph Source。本文所有发布版示例都按这个边界编写。

## 2 选哪个工具

先看数据从哪里来，以及任务是否已经属于一条大数据管道。

| 你的任务 | 推荐工具 | 适合原因 |
| --- | --- | --- |
| 管理图、执行 Gremlin、备份恢复、图克隆 | [HugeGraph-Tools](/cn/docs/quickstart/toolchain/hugegraph-tools) | 只操作 HugeGraph，命令直接 |
| 把本地文件、HDFS、MySQL 等数据批量导入 HugeGraph | [HugeGraph-Loader](/cn/docs/quickstart/toolchain/hugegraph-loader) | 配置简单，导入流程短 |
| 数据要经过 Kafka、JDBC、Flink、Spark 或多个外部系统 | SeaTunnel | 可以复用已有数据管道 |
| 需要流式任务、checkpoint 或统一管理多个连接器 | SeaTunnel | 支持 Source、Transform 和 Sink 组合 |
| 稳定地把一张 HugeGraph 图复制到另一张图 | Tools 优先 | 发布版工具更直接；SeaTunnel Source 仍是 dev 预览 |

只维护一张图、没有现成大数据管道时，优先从 Loader 或 Tools 开始。SeaTunnel 需要额外准备连接器插件，并使用 HOCON 配置文件。

## 3 准备工作

### 3.1 HugeGraph

本文示例使用以下图模型。

| 图元素 | 配置 |
| --- | --- |
| VertexLabel | `person`，主键为 `name` |
| PropertyKey | `name` 为 Text，`age` 为 Int |
| EdgeLabel | `knows`，源和目标都是 `person`，属性为 `since` |

2.3.13 的 Sink 会按 `schema_config` 读取已有的 VertexLabel、EdgeLabel 和 PropertyKey。运行写入任务前，请先在 Hubble、REST API 或 Gremlin 中创建 Schema。

### 3.2 SeaTunnel

请按 [SeaTunnel 本地部署文档](https://seatunnel.apache.org/docs/getting-started/locally/deployment/) 获取发行包。2.2.0-beta 之后，发行包默认不带连接器依赖，需要按任务安装 JDBC、Kafka 和 HugeGraph 插件；JDBC 还需要对应数据库的驱动。

如果 SeaTunnel 与 HugeGraph 不在同一台机器，`host` 要填写 SeaTunnel 运行环境可以访问的地址。容器内的 `127.0.0.1` 指向 SeaTunnel 容器自身；同一 Docker 网络中的服务则使用 HugeGraph 的服务名。

## 4 sql2graph

JDBC 方式适合把关系库中的表或 SQL 查询结果导入 HugeGraph。下面的例子把 `person` 表写成顶点，使用 `name` 生成 HugeGraph 主键。

![关系表写入 HugeGraph](/cn/docs/images/seatunnel/seatunnel-sql2graph.png)

### 4.1 关系库到顶点

假设 MySQL 中有一张表。

```sql
CREATE TABLE person (
  name VARCHAR(64) PRIMARY KEY,
  age INT NOT NULL
);
```

在 SeaTunnel 安装目录下创建 `config/sql2graph-person.conf`。

```hocon
env {
  job.mode = "BATCH"
}

source {
  Jdbc {
    url = "jdbc:mysql://mysql:3306/demo?useSSL=false&serverTimezone=UTC"
    driver = "com.mysql.cj.jdbc.Driver"
    username = "seatunnel"
    password = "change_me"
    query = "SELECT name, age FROM person ORDER BY name"
  }
}

sink {
  HugeGraph {
    host = "hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "default"
    schema_config = {
      type = "VERTEX"
      label = "person"
      idStrategy = "PRIMARY_KEY"
      idFields = ["name"]
      properties = ["name", "age"]
    }
  }
}
```

执行任务。

```bash
./bin/seatunnel.sh --config ./config/sql2graph-person.conf -m local
```

执行后可以在 HugeGraph 中检查顶点。

```groovy
g.V().hasLabel('person').valueMap('name', 'age')
```

`Jdbc` 的 `url` 和 `driver` 必填。`username` 和 `password` 按数据库认证配置填写，匿名连接时可以省略；示例中的密码需要替换。MySQL 驱动需要放到 SeaTunnel 对应引擎的插件目录，具体位置见 [JDBC Source 文档](https://seatunnel.apache.org/docs/connectors/source/Jdbc/)。

### 4.2 关系库到边

如果关系表中的端点字段已经能直接对应 `person.name`，可以再运行一个边任务。假设表结构如下。

```sql
CREATE TABLE knows (
  source_name VARCHAR(64) NOT NULL,
  target_name VARCHAR(64) NOT NULL,
  since INT NOT NULL
);
```

<details>
<summary>展开查看边任务配置</summary>

```hocon
env {
  job.mode = "BATCH"
}

source {
  Jdbc {
    url = "jdbc:mysql://mysql:3306/demo?useSSL=false&serverTimezone=UTC"
    driver = "com.mysql.cj.jdbc.Driver"
    username = "seatunnel"
    password = "change_me"
    query = "SELECT source_name, target_name, since FROM knows ORDER BY source_name, target_name"
  }
}

sink {
  HugeGraph {
    host = "hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "default"
    schema_config = {
      type = "EDGE"
      label = "knows"
      sourceConfig = {
        label = "person"
        idFields = ["source_name"]
      }
      targetConfig = {
        label = "person"
        idFields = ["target_name"]
      }
      properties = ["since"]
      mapping = {
        fieldMapping = {
          source_name = "name"
          target_name = "name"
        }
      }
    }
  }
}
```

</details>

先写顶点，再写边。端点字段如果只是外键，不能直接拼出 HugeGraph 顶点 ID，需要先在 SQL 中完成关联查询，或者先把端点名称写入结果集。

CDC 配置请参考 SeaTunnel 的 [MySQL CDC 文档](https://seatunnel.apache.org/docs/connectors/source/MySQL-CDC/)。

## 5 kafka2graph

Kafka 适合持续把事件写入 HugeGraph。下面的消息使用 JSON 格式，每条消息对应一个 `person` 顶点。

![Kafka 事件写入 HugeGraph](/cn/docs/images/seatunnel/seatunnel-kafka2graph.png)

Kafka topic `user-events` 中的消息示例。

```json
{"name":"marko","age":29}
```

创建 `config/kafka2graph.conf`。

```hocon
env {
  job.mode = "STREAMING"
  checkpoint.interval = 10000
}

source {
  Kafka {
    bootstrap.servers = "kafka:9092"
    topic = "user-events"
    consumer.group = "hugegraph-import"
    start_mode = "earliest"
    format = "json"
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
    host = "hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "default"
    schema_config = {
      type = "VERTEX"
      label = "person"
      idStrategy = "PRIMARY_KEY"
      idFields = ["name"]
      properties = ["name", "age"]
    }
  }
}
```

```bash
./bin/seatunnel.sh --config ./config/kafka2graph.conf -m local
```

`checkpoint.interval` 用于保存任务状态。HugeGraph Sink 使用 at-least-once 写入语义，使用 `PRIMARY_KEY` 时，重复写入同一个 `name` 会落到同一个顶点，不会因为重放生成新的随机顶点 ID。

Kafka 的参数和消息格式见 [Kafka Source 文档](https://seatunnel.apache.org/docs/connectors/source/Kafka/)。写边时，把 Sink 的 `schema_config.type` 改为 `EDGE`，再补充 `sourceConfig`、`targetConfig` 和边属性。

## 6 graph2graph

HugeGraph Source 目前只在 SeaTunnel `dev` 分支提供。下面的配置按 [`f1a1a0a`](https://github.com/apache/seatunnel/tree/f1a1a0abbe24bdac8cf23307995a78f778a3f467) 核对，不能直接放进 2.3.13 发行包。

![HugeGraph 图迁移](/cn/docs/images/seatunnel/seatunnel-graph2graph.png)

`mappings` 默认会创建缺失的 Schema。边映射的源和目标顶点标签仍需存在，因此要按下面的顺序先跑顶点任务，再跑边任务；如果把 `schema_save_mode` 改成 `ERROR_WHEN_SCHEMA_NOT_EXIST`，请提前创建目标图 Schema。

一次迁移按两个任务执行。

1. 先迁移顶点。
2. 再迁移边。

### 6.1 迁移顶点

下面的 Source 读取源图的 `person` 顶点，Sink 使用 `name` 重新生成 `PRIMARY_KEY` 顶点 ID。

<details>
<summary>展开查看顶点迁移配置</summary>

```hocon
env {
  job.mode = "BATCH"
}

source {
  HugeGraph {
    host = "source-hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
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
    host = "target-hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
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

### 6.2 迁移边

Source 会为边补充 `~source_id` 和 `~target_id` 保留列。Sink 可以直接使用这两列还原端点 ID。

<details>
<summary>展开查看边迁移配置</summary>

```hocon
env {
  job.mode = "BATCH"
}

source {
  HugeGraph {
    host = "source-hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
    label = "knows"
    label_type = "EDGE"
    schema = {
      fields = {
        since = "int"
      }
    }
  }
}

sink {
  HugeGraph {
    host = "target-hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
    mappings = [
      {
        type = "EDGE"
        label = "knows"
        sourceConfig = {
          label = "person"
          idFields = ["~source_id"]
        }
        targetConfig = {
          label = "person"
          idFields = ["~target_id"]
        }
        properties = ["since"]
      }
    ]
  }
}
```

</details>

如果源图使用 `AUTOMATIC` 顶点 ID，Source 无法把原 ID 作为主键重新生成。需要保留原 ID 时，应按 dev 文档使用 `CUSTOMIZE_*` 策略和 `~id` 保留列，并先确认目标图 Schema 与 ID 策略一致。

## 7 常用配置

以下字段同时出现在本文的发布版示例中。

| 字段 | 作用 |
| --- | --- |
| `host` | HugeGraph Server 主机名或 IP，不要把端口写进来 |
| `port` | HugeGraph Server 端口 |
| `graph_name` | 图名称 |
| `graph_space` | 图空间，发布版示例沿用 2.3.13 官方配置的 `default`，dev 示例使用源码默认值 `DEFAULT`，不要跨版本复制 |
| `schema_config` | 2.3.13 Sink 的顶点或边映射 |
| `mappings` | dev Sink 的多映射配置 |
| `batch_size` | 单批写入的记录数，默认值为 500 |
| `batch_interval_ms` | 批次刷新等待时间，默认值为 5000 毫秒 |

2.3.13 不支持本文 dev 示例中的 `mappings`、HugeGraph Source 和 `schema_save_mode`。遇到配置校验失败时，先检查 SeaTunnel 发行包版本和配置 API 是否对应。

## 8 参考文档

- [SeaTunnel 本地部署](https://seatunnel.apache.org/docs/getting-started/locally/deployment/)
- [HugeGraph Sink 2.3.13](https://github.com/apache/seatunnel/blob/2.3.13/docs/zh/connectors/sink/HugeGraph.md)
- [HugeGraph Sink dev（本文核对版本）](https://github.com/apache/seatunnel/blob/f1a1a0abbe24bdac8cf23307995a78f778a3f467/docs/zh/connectors/sink/HugeGraph.md)
- [HugeGraph Source dev（本文核对版本）](https://github.com/apache/seatunnel/blob/f1a1a0abbe24bdac8cf23307995a78f778a3f467/docs/zh/connectors/source/HugeGraph.md)
- [JDBC Source](https://seatunnel.apache.org/docs/connectors/source/Jdbc/)
- [Kafka Source](https://seatunnel.apache.org/docs/connectors/source/Kafka/)
- [MySQL CDC Source](https://seatunnel.apache.org/docs/connectors/source/MySQL-CDC/)
- [HugeGraph-Loader](/cn/docs/quickstart/toolchain/hugegraph-loader)
- [HugeGraph-Tools](/cn/docs/quickstart/toolchain/hugegraph-tools)
- [Apache SeaTunnel GitHub](https://github.com/apache/seatunnel)
- [Apache HugeGraph GitHub](https://github.com/apache/hugegraph)
