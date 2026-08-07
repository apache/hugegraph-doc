---
title: "HugeGraph-SeaTunnel Connector Quick Start"
linkTitle: "Sync Data with SeaTunnel Connector"
weight: 5
---

### 1 HugeGraph-SeaTunnel Connector Overview

[Apache SeaTunnel](https://seatunnel.apache.org/) is a high-performance, distributed data integration platform
that supports real-time synchronization and batch processing of massive data. The HugeGraph community has contributed
Connector-V2 support to Apache SeaTunnel, enabling users to synchronize data between HugeGraph and external data systems.

![HugeGraph + SeaTunnel Integration Architecture](/docs/images/seatunnel/hugegraph-seatunnel-architecture.png)

### 2 Features

HugeGraph-SeaTunnel Connector provides the following capabilities:

- **HugeGraph Sink Connector** (Released): Write external data to HugeGraph, supporting batch write, update, and delete of vertices and edges
- **HugeGraph Source Connector** (In Development): Read graph data from HugeGraph, supporting batch reading of vertices and edges
- **Vertex Synchronization**: Support full or incremental vertex data synchronization with multiple ID strategies
- **Edge Synchronization**: Support full or incremental edge data synchronization, auto-resolving source and target vertices
- **Automatic Schema Management**: Support auto-creating PropertyKey, VertexLabel, EdgeLabel (`CREATE_SCHEMA_WHEN_NOT_EXIST`)
- **Data Migration**: Support data migration between different HugeGraph instances, or importing graph data from other data sources

![HugeGraph Source/Sink Bidirectional Data Flow](/docs/images/seatunnel/hugegraph-seatunnel-source-sink.png)

### 3 Environment Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Java | 8+ | SeaTunnel runtime requirement |
| Apache SeaTunnel | 2.3.12+ | Sink Connector released since this version |
| HugeGraph Server | 1.0.0+ | Latest stable version recommended |

> **Source Connector Note**: The HugeGraph Source Connector is currently only available in the SeaTunnel development
> branch (Next/master) and has not been included in an official release. If you need the Source feature, please build
> SeaTunnel from source or wait for the next release.

### 4 Quick Start

#### 4.1 Install SeaTunnel

Please refer to the [Apache SeaTunnel Deployment Guide](https://seatunnel.apache.org/docs/getting-started/) to install and deploy SeaTunnel.

#### 4.2 Use HugeGraph Sink Connector (Write Data)

The following examples demonstrate how to write data to HugeGraph via SeaTunnel:

**Write vertices:**

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

**Write edges:**

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

> **Note**: The HugeGraph schema (PropertyKey, VertexLabel, EdgeLabel) must be created before executing write tasks,
> or you can use `schema_save_mode = CREATE_SCHEMA_WHEN_NOT_EXIST` (default behavior) for the Connector to auto-create it.

#### 4.3 Core Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | String | Yes | - | HugeGraph Server host |
| `port` | Integer | Yes | - | HugeGraph Server port |
| `graph_name` | String | Yes | - | Graph name |
| `graph_space` | String | No | DEFAULT | Graph space name |
| `username` | String | No | - | Authentication username |
| `password` | String | No | - | Authentication password |
| `protocol` | String | No | http | Protocol, `http` or `https` |
| `batch_size` | Integer | No | 500 | Records per batch write |
| `batch_interval_ms` | Integer | No | 5000 | Max wait time per batch (ms) |
| `max_retries` | Integer | No | 3 | Max retries on write failure |
| `retry_backoff_ms` | Integer | No | 5000 | Retry backoff interval (ms) |

> For the complete parameter list and detailed documentation, please refer to the
> [Apache SeaTunnel HugeGraph Connector Official Docs](https://seatunnel.apache.org/docs/connector-v2/sink/HugeGraph/).

### 5 Documentation & Resources

- [Apache SeaTunnel Official Website](https://seatunnel.apache.org/)
- [Apache SeaTunnel Connector-V2 Documentation](https://seatunnel.apache.org/docs/connector-v2/)
- [Apache SeaTunnel GitHub](https://github.com/apache/seatunnel)
- [HugeGraph GitHub](https://github.com/apache/hugegraph)

### 6 License

Same as HugeGraph, HugeGraph-SeaTunnel Connector is licensed under Apache 2.0.
