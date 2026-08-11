---
title: "HugeGraph 与 SeaTunnel Connector 快速开始"
linkTitle: "使用 SeaTunnel 读写 HugeGraph"
weight: 5
---

### 1 先了解版本范围

Apache SeaTunnel 的 HugeGraph Connector 可以从 HugeGraph 读取顶点或边，也可以把上游数据写成 HugeGraph 顶点或边。

本文跟随 SeaTunnel 官网的 `Next` 文档和 `dev` 分支代码。固定版本的发行包可能只包含其中一部分能力。准备生产任务时，请在 SeaTunnel 官网切换到所用版本，再核对该版本的参数和限制。

![SeaTunnel Next 和 dev 中，从 HugeGraph 经 HugeGraph Source 读取到下游，以及从外部数据源经 HugeGraph Sink 写入 HugeGraph 的两条独立数据流](/cn/docs/images/seatunnel/hugegraph-seatunnel-architecture.png)

图中上下两条流程是独立的批量任务，不表示实时双向同步。`Transform` 是按需添加的可选步骤。小屏阅读时可[查看原图](/cn/docs/images/seatunnel/hugegraph-seatunnel-architecture.png)。

### 2 用单机 SeaTunnel 完成第一次导入

这条路径使用 `FakeSource` 生成两个人物顶点，再写入本机 HugeGraph。整个任务只需要 SeaTunnel、HugeGraph 和三个 Connector 插件。

#### 2.1 启动 HugeGraph

按照 [HugeGraph Server 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-server) 启动服务。默认地址为 `http://localhost:8080`，可以先检查服务是否可访问。

```bash
curl http://localhost:8080/versions
```

#### 2.2 安装 Connector

准备一个包含 HugeGraph Connector 的 SeaTunnel `Next` 或 `dev` 构建。在 `config/plugin_config` 中保留下列插件。

```text
--seatunnel-connectors--
connector-fake
connector-console
connector-hugegraph
--end--
```

发行包能够取得对应版本插件时，在 SeaTunnel 目录中执行安装脚本。

```bash
sh bin/install-plugin.sh
```

如果开发版插件尚未发布到仓库，需要从 SeaTunnel `dev` 分支构建。插件代码和 SeaTunnel 运行时应来自同一版本。安装方法可参考 [SeaTunnel 本地部署说明](https://seatunnel.apache.org/zh-CN/docs/getting-started/locally/deployment/)。

#### 2.3 保存顶点导入配置

把下面内容保存为 `config/hugegraph-vertex-sink.conf`。`mappings` 描述输入字段和 HugeGraph 顶点之间的关系。`CREATE_SCHEMA_WHEN_NOT_EXIST` 会在首次运行时创建缺失的属性键和 `person` 顶点标签。示例使用 `CUSTOMIZE_STRING`，把 `name` 的值直接作为顶点 ID，便于后续迁移时保留 ID。

```hocon
env {
  job.mode = "BATCH"
}

source {
  FakeSource {
    schema = {
      fields = {
        name = "string"
        age = "int"
      }
    }
    rows = [
      {
        kind = INSERT
        fields = ["alice", 29]
      }
      {
        kind = INSERT
        fields = ["bob", 31]
      }
    ]
  }
}

sink {
  HugeGraph {
    host = "localhost"
    port = 8080
    protocol = "http"
    graph_name = "hugegraph"
    schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
    mappings = [
      {
        type = "VERTEX"
        label = "person"
        idStrategy = "CUSTOMIZE_STRING"
        idFields = ["name"]
        properties = ["name", "age"]
      }
    ]
  }
}
```

#### 2.4 运行并检查结果

```bash
bin/seatunnel.sh -m local --config config/hugegraph-vertex-sink.conf
curl --compressed "http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices"
```

返回结果中应当出现标签为 `person`、`name` 分别为 `alice` 和 `bob` 的两个顶点。

#### 2.5 再导入一条边

顶点导入完成后，把下面内容保存为 `config/hugegraph-edge-sink.conf`。这个任务创建一条从 `alice` 指向 `bob` 的 `knows` 边。

```hocon
env {
  job.mode = "BATCH"
}

source {
  FakeSource {
    schema = {
      fields = {
        person1_name = "string"
        person2_name = "string"
        since = "int"
      }
    }
    rows = [
      {
        kind = INSERT
        fields = ["alice", "bob", 2024]
      }
    ]
  }
}

sink {
  HugeGraph {
    host = "localhost"
    port = 8080
    protocol = "http"
    graph_name = "hugegraph"
    check_vertex = true
    schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
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

```bash
bin/seatunnel.sh -m local --config config/hugegraph-edge-sink.conf
curl --compressed "http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges"
```

`check_vertex = true` 会拒绝端点顶点尚未写入的边。迁移任务通常应先导入顶点，再导入边。

### 3 从 HugeGraph 读取数据

下面的任务读取 `person` 顶点，并把结果输出到控制台。保存为 `config/hugegraph-source.conf`。

```hocon
env {
  job.mode = "BATCH"
}

source {
  HugeGraph {
    host = "localhost"
    port = 8080
    protocol = "http"
    graph_name = "hugegraph"
    label = "person"
    label_type = "VERTEX"
    page_size = 1000
    parallelism = 1
    schema = {
      fields = {
        name = "string"
        age = "int"
      }
    }
  }
}

sink {
  Console {}
}
```

```bash
bin/seatunnel.sh -m local --config config/hugegraph-source.conf
```

顶点结果会自动带上 `~id` 和 `~label`。读取边时，把 `label_type` 改为 `EDGE` 并填写边标签。边结果还会带上 `~source_id`、`~source_label`、`~target_id` 和 `~target_label`。

省略 `schema` 时，Source 会从 HugeGraph 读取标签定义并发现属性列。省略 `label` 时，它会读取 `label_type` 下的全部标签，每个标签输出一张表。全部标签模式不能配置 `schema` 或 `filter`。

单标签大数据量读取可以把 `parallelism` 设为大于 `1`，并用 `split_size` 控制分片大小。该模式要求 HugeGraph 后端支持 scan，不能与 `filter` 同时使用。`memory` 后端应保持 `parallelism = 1`。

### 4 在两个 HugeGraph 图之间迁移

Source 和 Sink 可以直接组成迁移任务。下面的配置把源图中的 `person` 顶点写入目标图。示例用不同主机名区分两套服务，请按实际地址修改。

目标图要先创建兼容的 `person` Schema，并把顶点 ID 策略设为 `CUSTOMIZE_STRING`。本文将 `schema_save_mode` 设为 `ERROR_WHEN_SCHEMA_NOT_EXIST`，避免迁移时意外改变已有图模型。

```hocon
env {
  job.mode = "BATCH"
}

source {
  HugeGraph {
    host = "source-hugegraph"
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
    host = "target-hugegraph"
    port = 8080
    graph_name = "hugegraph"
    schema_save_mode = "ERROR_WHEN_SCHEMA_NOT_EXIST"
    mappings = [
      {
        type = "VERTEX"
        label = "person"
        idStrategy = "CUSTOMIZE_STRING"
        idFields = ["~id"]
        properties = ["name", "age"]
      }
    ]
  }
}
```

保存为 `config/hugegraph-clone-vertices.conf` 后运行。

```bash
bin/seatunnel.sh -m local --config config/hugegraph-clone-vertices.conf
```

边迁移要在顶点迁移完成后执行。这个示例已经通过 `CUSTOMIZE_STRING` 保留了顶点 ID，因此 Sink 可以直接复用 HugeGraph Source 输出的完整端点 ID `~source_id` 和 `~target_id`。

```hocon
env {
  job.mode = "BATCH"
}

source {
  HugeGraph {
    host = "source-hugegraph"
    port = 8080
    graph_name = "hugegraph"
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
    check_vertex = true
    schema_save_mode = "ERROR_WHEN_SCHEMA_NOT_EXIST"
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

保存为 `config/hugegraph-clone-edges.conf`，再用 `bin/seatunnel.sh -m local --config config/hugegraph-clone-edges.conf` 执行。

#### 4.1 迁移边界

- Source 是有界批量读取，不提供 HugeGraph CDC。
- Sink 提供 at-least-once 语义。使用 `AUTOMATIC` ID 时，重试可能产生重复顶点，且原始顶点 ID 无法保留。
- 使用保留列克隆边之前，目标图的顶点标签和端点顶点都要存在，端点 ID 也必须与源图一致。本文的 `CUSTOMIZE_STRING` 示例满足这个条件。
- 自定义字符串、数字或 UUID 顶点可以用 `~id` 作为 Sink 的 `idFields`，并选择对应的 `CUSTOMIZE_*` 策略。
- `PRIMARY_KEY` 顶点应使用主键属性在目标图中重新生成 ID。它的完整 ID 包含标签的 Schema ID，两个独立图中的值可能不同。此时不能直接复用边的 `~source_id` 和 `~target_id`。边输入还需要携带端点主键属性并按目标标签重建 ID，或者通过备份恢复等方式保留 Schema ID。
- 省略 `label` 可以读取同一类型下的全部标签，但顶点和边仍需分成两个任务，并按先顶点后边的顺序执行。

### 5 生产任务还要检查什么

快速示例使用自动建 Schema。已有图模型建议预先创建 Schema，并设置 `schema_save_mode = ERROR_WHEN_SCHEMA_NOT_EXIST`。Sink 的 `idStrategy` 必须与目标顶点标签一致，边的 `sourceConfig` 和 `targetConfig` 也要能还原端点 ID。

连接认证可配置 `username` 和 `password`。`protocol` 默认是 `http`，使用 `https` 时需要为 SeaTunnel Worker 配置 JVM trust store。图空间可通过 `graph_space` 指定，默认值为 `DEFAULT`。

常用的吞吐参数包括 Sink 的 `batch_size`、`batch_interval_ms`，以及 Source 的 `page_size`、`parallelism` 和 `split_size`。完整参数和类型映射以 SeaTunnel 当前文档为准。

### 6 进一步阅读

- [SeaTunnel HugeGraph Source 开发版文档](https://seatunnel.apache.org/zh-CN/docs/connectors/source/HugeGraph/)
- [SeaTunnel HugeGraph Sink 开发版文档](https://seatunnel.apache.org/zh-CN/docs/connectors/sink/HugeGraph/)
- [SeaTunnel GitHub 仓库](https://github.com/apache/seatunnel)
- [HugeGraph Schema 和 Client](/cn/docs/quickstart/client/hugegraph-client)
