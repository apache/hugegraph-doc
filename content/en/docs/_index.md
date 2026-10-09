---
title: "Documentation"
linkTitle: "Documentation"
weight: 20
outputs: [HTML, RSS, print, markdown, LLMSFULL]
---

## Apache HugeGraph Documentation

Apache HugeGraph includes graph database, graph computing, and graph AI components. The HugeGraph core engine manages property graphs, transactions, and real-time queries; Computer and Vermeer run graph algorithms; and HugeGraph-AI provides GraphRAG, graph machine learning, and a Python client.

### Quick Navigation by Scenario

| I want to... | Start here |
|----------|-----------|
| **Run graph queries** (OLTP) | [HugeGraph Server Quick Start](quickstart/hugegraph/hugegraph-server) |
| **Run graph algorithms** (OLAP) | [HugeGraph Computing](quickstart/computing/hugegraph-vermeer) |
| **Build Graph + AI applications** | [HugeGraph-AI](quickstart/hugegraph-ai/quick_start) |
| **Batch import data** | [HugeGraph Loader](quickstart/toolchain/hugegraph-loader), [SeaTunnel](/docs/quickstart/toolchain/import/hugegraph-seatunnel-connector/) |
| **Visualize and manage graphs** | [Hubble Web UI](quickstart/toolchain/hugegraph-hubble) |

### Ecosystem Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Apache HugeGraph Ecosystem                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ HugeGraph   │  │ Vermeer*    │  │ HugeGraph-AI            │  │
│  │ Core Engine │  │ Computer    │  │ (GraphRAG/ML/Python)    │  │
│  │ (OLTP)      │  │ (Java BSP)  │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│         │               │                    │                   │
│  ┌──────┴───────────────┴────────────────────┴──────────────┐   │
│  │              HugeGraph Toolchain                          │   │
│  │  Hubble (UI) | Loader | Client (Java/Go/Py) | Tools      │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

* Vermeer is the default graph computing entry; Computer runs Java BSP jobs.

### Core Components

- **HugeGraph Core Engine (OLTP)**: Exposes REST APIs through HugeGraph Server and supports Gremlin and Cypher queries
- **HugeGraph Toolchain**: Includes Java/Go clients, Loader, Hubble, Spark Connector, and Tools; the Python client is maintained in HugeGraph-AI, and a Rust client is under development
- **HugeGraph Computer**: Contains the distributed Computer engine and the in-memory Vermeer engine
- **HugeGraph-AI**: Includes GraphRAG, graph machine learning, the Python client, and the Vermeer Python client

### Deployment Modes

| Mode | Core Components | Suitable Scenarios | Data Scale |
|---|---|---|---|
| **Standalone** | Server + RocksDB | Development, testing, Graph AI, and small to medium-scale production environments | ≤ 2 TB |
| **Distributed** | Server + PD + Store (HStore) | Production, horizontal scaling, and multi-replica deployment | ≤ 1 PB |

See the [system introduction](introduction/) and the corresponding quick-start guides for each component's scope and startup instructions.
