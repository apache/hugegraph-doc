# Apache HugeGraph Introduction

LLMS index: [llms.txt](/versions/1.7/llms.txt)

---

## What Is Apache HugeGraph?

[Apache HugeGraph](https://hugegraph.apache.org/) is an easy-to-use, efficient, general-purpose open-source **full-stack graph system** ([GitHub](https://github.com/apache/hugegraph)). It covers three major areas: **graph databases** (OLTP real-time queries), **graph computing** (OLAP large-scale analysis), and **graph AI** (GraphRAG and graph machine learning).

HugeGraph supports fast storage and queries for tens of billions of vertices and edges, with strong OLTP performance. Its graph engine is compatible with [Apache TinkerPop 3](https://tinkerpop.apache.org) and supports both [Gremlin](https://tinkerpop.apache.org/gremlin.html) and [Cypher](https://en.wikipedia.org/wiki/Cypher) (the OpenCypher standard).

**Typical use cases:** deep relationship exploration, association analysis, path search, feature extraction, community detection, and knowledge graphs.
**Application areas:** network security, telecom anti-fraud, financial risk control, advertising and recommendations, social networks, and intelligent Q&A.

## Ecosystem Overview

```text
┌────────────────────────────────────────────────────────────────────┐
│            Apache HugeGraph - Full-Stack Graph System             │
├──────────────────┬────────────────────┬────────────────────────────┤
│  Graph DB (OLTP) │    Graph Compute   │          Graph AI          │
│  HugeGraph       │  Vermeer (Memory)  │       HugeGraph-AI         │
│  Server          │  Computer (Dist.)  │     GraphRAG / GNN / Py    │
├──────────────────┴────────────────────┴────────────────────────────┤
│                       HugeGraph Toolchain                          │
│ Hubble | Loader | Client (Java/Go/Python; Rust WIP) | Spark | Tools│
└────────────────────────────────────────────────────────────────────┘
```

## HugeGraph Server (OLTP Graph Engine)

HugeGraph Server is the OLTP engine and service entry point for the graph database. It handles property graph modeling, transaction processing, query execution, and API access. Graph data is stored in the configured RocksDB, HStore, or HBase backend.

- **Property graph and schema**: Manages VertexLabel, EdgeLabel, PropertyKey, and IndexLabel definitions
- **Query languages**: Supports Gremlin (TinkerPop 3) and Cypher (OpenCypher)
- **REST API**: Provides endpoints for schemas, graph data, queries, tasks, and operations
- **Indexes and queries**: Supports exact, range, and compound-condition queries
- **Storage backends**: Versions 1.7.0 through `master` primarily support RocksDB (standalone), HStore (distributed), and HBase

The main modules include `hugegraph-core`, the storage backend modules, and `hugegraph-api`. Core implements the graph model, transactions, and query logic; backend modules connect to specific storage systems; and the API module provides HTTP access. Current REST resource paths include the graph space and graph name, for example:

```text
/graphspaces/{graphspace}/graphs/{graph}
```

Standalone deployments commonly use RocksDB. Distributed deployments use HStore: PD manages cluster metadata and partition scheduling, while Store persists graph data and replicas. HBase can be used as a separate storage backend.

- [Server Quick Start](/versions/1.7/docs/quickstart/hugegraph/hugegraph-server/)
- [PD Quick Start](/versions/1.7/docs/quickstart/hugegraph/hugegraph-pd/)
- [HStore Quick Start](/versions/1.7/docs/quickstart/hugegraph/hugegraph-hstore/)
- [REST API](/versions/1.7/docs/clients/restful-api/)

## HugeGraph Toolchain

HugeGraph Toolchain provides clients, data import, visual management, Spark integration, and command-line operations. Together, these tools cover the main stages of a graph application's lifecycle, from data ingestion to routine management.

| Module | Purpose |
|---|---|
| [Client](/versions/1.7/docs/quickstart/client/hugegraph-client/) | Wraps schema management, graph data reads and writes, Gremlin, and Traverser APIs; supports Java, [Python](/versions/1.7/docs/quickstart/client/hugegraph-client-python/), and [Go](/versions/1.7/docs/quickstart/client/hugegraph-client-go/), with a Rust client under development |
| [Loader](/versions/1.7/docs/quickstart/toolchain/hugegraph-loader/) | Reads data from local files, HDFS, JDBC, Kafka, or another graph, converts it into vertices and edges, and imports it into HugeGraph in batches |
| [Hubble](/versions/1.7/docs/quickstart/toolchain/hugegraph-hubble/) | Provides a web management interface for graph connections, schemas, data import, Gremlin queries, and visual results |
| [Spark Connector](/versions/1.7/docs/quickstart/toolchain/hugegraph-spark-connector/) | Reads and writes HugeGraph data in Spark jobs for offline big-data processing |
| [Tools](/versions/1.7/docs/quickstart/toolchain/hugegraph-tools/) | Provides command-line operations for deployment, graph management, backup and restore, and Gremlin execution |

## Graph Computing Engines (OLAP)

The HugeGraph-Computer repository provides two complementary OLAP graph computing engines:

- **Vermeer**: Written in Go, it uses a master-worker architecture and primarily performs in-memory computation. It provides REST APIs, gRPC, and a web UI, and is suitable for fast small- and medium-scale graph analysis.
- **Computer**: Written in Java, it implements the distributed BSP/Pregel computing model and can run on Kubernetes, YARN, or local processes. It can spill data to disk when memory thresholds are exceeded and is suitable for larger graph computing workloads.

Both engines can read HugeGraph data, but their runtime architectures, resource requirements, configuration, and algorithm interfaces differ.

- [Vermeer Quick Start](/versions/1.7/docs/quickstart/computing/hugegraph-vermeer/)
- [Computer Quick Start](/versions/1.7/docs/quickstart/computing/hugegraph-computer/)

## HugeGraph-AI (Graph + AI)

HugeGraph-AI connects graph technology with large language models and graph machine learning frameworks. The repository uses Python 3.10 or later and manages its workspace with `uv`. Its main modules are:

- **hugegraph-llm**: Provides GraphRAG, knowledge graph construction, natural-language queries, and Text2Gremlin
- **hugegraph-ml**: Provides models for node classification, graph classification, graph embeddings, link prediction, and fraud detection
- **hugegraph-python-client**: Manages schemas, graph data, and Gremlin queries from Python
- **vermeer-python-client**: Calls Vermeer graph computing services from Python

[HugeGraph-AI Quick Start](/versions/1.7/docs/quickstart/hugegraph-ai/quick_start/)

## Deployment Modes

| Mode | Core Components | Suitable Scenarios | Data Scale |
|---|---|---|---|
| **Standalone (OLTP)** | Server + RocksDB | Development, testing, and small to medium-scale data | ≤ 2 TB |
| **Distributed (OLTP)** | Server + PD + Store (HStore) | Production, horizontal scaling, and multi-replica deployment | ≤ 1 PB |

Graph computing is an OLAP workload. Its capacity and resource requirements depend on the selected engine, graph structure, and algorithm, and do not use the OLTP storage capacity figures above.

## Where to Start

| Goal | Documentation |
|---|---|
| Start the graph database and run queries | [Server Quick Start](/versions/1.7/docs/quickstart/hugegraph/hugegraph-server/) |
| Import data in batches | [Loader](/versions/1.7/docs/quickstart/toolchain/hugegraph-loader/) |
| Manage graphs through a web interface | [Hubble](/versions/1.7/docs/quickstart/toolchain/hugegraph-hubble/) |
| Run graph algorithms | [Vermeer and Computer](/versions/1.7/docs/quickstart/computing/) |
| Build GraphRAG or graph machine learning applications | [HugeGraph-AI](/versions/1.7/docs/quickstart/hugegraph-ai/) |

## Community

- [GitHub Issues](https://github.com/apache/hugegraph/issues)
- Developer mailing list: [dev@hugegraph.apache.org](mailto:dev@hugegraph.apache.org)
- [How to subscribe to the mailing list](/versions/1.7/docs/contribution-guidelines/subscribe/)
- Security reports: [security@hugegraph.apache.org](mailto:security@hugegraph.apache.org)
- WeChat public account: Apache HugeGraph

![WeChat QR Code](/versions/1.7/images/docs/community/wechat.png)
{width="300" height="94"}

---

Section pages:

- [Introduction with HugeGraph](/versions/1.7/docs/introduction/readme/)
