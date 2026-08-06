---
title: "Introduction with HugeGraph"
linkTitle: "Introduction"
weight: 1
aliases:
  - /docs/introduction/readme/
  - /docs/introduction/README/
---

### What is Apache HugeGraph?

[Apache HugeGraph](https://hugegraph.apache.org/) is an easy-to-use, efficient, and general-purpose open-source **full-stack graph system** ([GitHub](https://github.com/apache/hugegraph)), covering three major areas: **Graph Database** (OLTP real-time queries), **Graph Computing** (OLAP large-scale analysis), and **Graph AI** (GraphRAG / Graph Machine Learning).

HugeGraph supports the rapid storage and querying of tens of billions of vertices and edges, possessing excellent OLTP performance. Its graph engine is fully compliant with the [Apache TinkerPop 3](https://tinkerpop.apache.org) framework and supports both [Gremlin](https://tinkerpop.apache.org/gremlin.html) and [Cypher](https://en.wikipedia.org/wiki/Cypher) (OpenCypher standard) query languages.

**Typical Application Scenarios:** Deep relationship exploration, association analysis, path search, feature extraction, community detection, knowledge graphs, etc.  
**Applicable Fields:** Network security, telecom anti-fraud, financial risk control, personalized recommendations, social networks, intelligent Q&A, etc.

---

### Ecosystem Overview

```text
┌──────────────────────────────────────────────────────────────┐
│         Apache HugeGraph - Full-Stack Graph System           │
├──────────────────┬────────────────────┬──────────────────────┤
│  Graph DB (OLTP) │    Graph Compute   │       Graph AI       │
│  HugeGraph       │  Vermeer (Memory)  │    HugeGraph-AI      │
│  Server          │  Computer (Dist.)  │  GraphRAG/GNN/Py     │
├──────────────────┴────────────────────┴──────────────────────┤
│                    HugeGraph Toolchain                       │
│  Hubble | Loader | Client(Java/Go/Py) | Spark | Tools        │
└──────────────────────────────────────────────────────────────┘
```

---

### Core Components

#### 🗄️ HugeGraph Server — Graph Engine (OLTP)

The core module of the HugeGraph project, providing high-performance graph data storage and real-time query capabilities:

- **Core Engine**: Supports Property Graph modeling, including complete Schema management for VertexLabel, EdgeLabel, PropertyKey, and IndexLabel.
- **Dual Query Languages**: Fully compatible with Gremlin (TinkerPop 3) and Cypher (OpenCypher).
- **REST API**: Built-in REST Server, providing RESTful graph operation interfaces.
- **Multi-type Indexes**: Exact query, range query, and complex condition combination queries.
- **Pluggable Storage Backends**: For 1.7.0 and later, supports `RocksDB` (standalone default), `HStore` (distributed), `HBase`, and `Memory`; for 1.5.x or earlier, supports `MySQL` / `PostgreSQL` / `Cassandra`, etc.

**Submodules:**
- `Core`: Graph engine implementation, connecting downwards to Backend and upwards to API.
- `Backend`: Adapter layer for multiple backend storages.
- `API`: RESTful access layer, compatible with Gremlin/Cypher queries.

📖 [Server Quick Start](/docs/quickstart/hugegraph/hugegraph-server)

---

#### 📊 Graph Computing Engine (OLAP)

Provides two complementary graph analysis engines:

- **Vermeer** (Recommended): High-performance pure in-memory graph computing engine, simple to deploy, fast response, suitable for small to medium-scale graph analysis and quick onboarding.
- **HugeGraph-Computer**: Distributed OLAP engine based on the [Pregel](https://kowshik.github.io/JPregel/pregel_paper.pdf) model, can run on Kubernetes / Yarn clusters, suitable for mega-scale graph algorithm tasks.

📖 [Computing Quick Start](/docs/quickstart/computing/hugegraph-vermeer)

---

#### 🤖 HugeGraph-AI — Graph AI Ecosystem

An independent AI component of HugeGraph, bridging graphs with Large Language Models (LLMs):

- **GraphRAG**: Graph-based Retrieval-Augmented Generation, enabling LLM intelligent Q&A.
- **Knowledge Graph Construction**: Automatically extracting entities and relationships from unstructured text to build knowledge graphs.
- **Graph Neural Networks**: Supports training and inference of GNN models.
- **20+ Graph Machine Learning Algorithms**: Built-in rich graph analysis algorithms, continuously updated.
- **Python Client**: Convenient Python SDK for AI applications.

📖 [HugeGraph-AI Quick Start](/docs/quickstart/hugegraph-ai/quick_start)

---

#### 🛠️ HugeGraph Toolchain

A complete tool ecosystem surrounding the graph system ([toolchain repository](https://github.com/apache/hugegraph-toolchain)):

| Tool | Description |
|------|-------------|
| [Hubble](/docs/quickstart/toolchain/hugegraph-hubble) | Web visualization platform: one-stop operation for data modeling → batch importing → online/offline analysis. |
| [Loader](/docs/quickstart/toolchain/hugegraph-loader) | Data import tool: supports multiple data sources like local files, HDFS, MySQL, and formats like TXT/CSV/JSON. |
| [Client](/docs/quickstart/client/hugegraph-client) | Multi-language SDKs: Java / Python / Go. |
| [Spark-connector](/docs/quickstart/toolchain/hugegraph-spark-connector) | Spark integration: supports batch graph data read/write via Spark, suitable for big data offline processing. |
| [Tools](/docs/quickstart/toolchain/hugegraph-tools) | Command-line operational tools: graph management, backup/restore, Gremlin execution, etc. |

---

### Deployment Modes

HugeGraph supports two primary deployment modes:

| Mode | Core Components | Suitable Scenarios | Data Scale | High Availability (HA) |
|------|-----------------|--------------------|------------|------------------------|
| **Standalone** | Server + RocksDB | Development, testing, single-node production | < 4TB | Basic |
| **Distributed** | Server + PD (3-5 nodes) + Store (3+ nodes) | Production environments, horizontal scaling | < 1000TB | ✅ |

**Docker Quick Experience:**

```bash
docker run -itd --name=hugegraph -p 8080:8080 hugegraph/hugegraph
```

---

### Quick Start Navigation

| I want to... | Start Here |
|--------------|------------|
| 🚀 **Quick Experience** | [Docker Deployment](/docs/quickstart/hugegraph/hugegraph-server) |
| 🔍 **Run Graph Queries** (OLTP) | [Server Quick Start](/docs/quickstart/hugegraph/hugegraph-server) |
| 📈 **Large-scale Graph Computing** (OLAP) | [Vermeer / Computer](/docs/quickstart/computing/hugegraph-computer) |
| 🤖 **Build AI/RAG Applications** | [HugeGraph-AI](/docs/quickstart/hugegraph-ai/quick_start) |
| 📥 **Batch Import Data** | [HugeGraph-Loader](/docs/quickstart/toolchain/hugegraph-loader) |
| 🖥️ **Visual Management** | [Hubble Web UI](/docs/quickstart/toolchain/hugegraph-hubble) |

---

### System Features

- **Easy to Use**: Dual Gremlin/Cypher query languages + RESTful API, comprehensive toolchain, extremely easy to get started.
- **Efficient**: Deeply optimized graph storage and queries, millisecond-level response, supports thousands of concurrent online operations, fast import of billions of data records.
- **Universal**: Supports both OLTP and OLAP modes, seamlessly integrates with Apache Hadoop, Spark, and Flink big data ecosystems.
- **Scalable**: Distributed storage, multi-replica data, horizontal scaling, flexible expansion through pluggable backends.
- **Open**: Apache 2.0 License, fully open-source, warmly welcoming community contributions.

---

### Contact Us

- [GitHub Issues](https://github.com/apache/hugegraph/issues): Feedback on usage issues and functional requirements (Recommended)
- Email: [dev@hugegraph.apache.org](mailto:dev@hugegraph.apache.org) ([How to subscribe](/docs/contribution-guidelines/subscribe/))
- Security: [security@hugegraph.apache.org](mailto:security@hugegraph.apache.org) (Report security issues)
- WeChat Public Account: Apache HugeGraph

<img src="https://github.com/apache/hugegraph-doc/blob/master/assets/images/wechat.png?raw=true" alt="WeChat QR Code" width="300"/>
