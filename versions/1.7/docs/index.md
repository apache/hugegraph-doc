# Documentation

LLMS index: [llms.txt](/versions/1.7/llms.txt)

---

## Apache HugeGraph Documentation

Apache HugeGraph includes graph database, graph computing, and graph AI components. The HugeGraph core engine manages property graphs, transactions, and real-time queries; Computer and Vermeer run graph algorithms; and HugeGraph-AI provides GraphRAG, graph machine learning, and a Python client.

### Quick Navigation by Scenario

| I want to... | Start here |
|----------|-----------|
| **Run graph queries** (OLTP) | [HugeGraph Server Quickstart](quickstart/hugegraph/hugegraph-server) |
| **Large-scale graph computing** (OLAP) | [Graph Computing Engine](quickstart/computing/hugegraph-computer) |
| **Build Graph + AI applications** | [HugeGraph-AI](quickstart/hugegraph-ai/quick_start) |
| **Batch import data** | [HugeGraph Loader](quickstart/toolchain/hugegraph-loader) |
| **Visualize and manage graphs** | [Hubble Web UI](quickstart/toolchain/hugegraph-hubble) |

### Ecosystem Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Apache HugeGraph Ecosystem                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ HugeGraph   │  │ HugeGraph   │  │ HugeGraph-AI            │  │
│  │ Core Engine │  │ Computer    │  │ (GraphRAG/ML/Python)    │  │
│  │ (OLTP)      │  │ (OLAP)      │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│         │               │                    │                   │
│  ┌──────┴───────────────┴────────────────────┴──────────────┐   │
│  │              HugeGraph Toolchain                          │   │
│  │  Hubble (UI) | Loader | Client (Java/Go/Py) | Tools      │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

- **HugeGraph Core Engine (OLTP)**: Exposes REST APIs through HugeGraph Server and supports Gremlin and Cypher queries
- **HugeGraph Toolchain**: Includes Java/Go clients, Loader, Hubble, Spark Connector, and Tools; the Python client is maintained in HugeGraph-AI, and a Rust client is under development
- **HugeGraph Computer**: Contains the distributed Computer engine and the in-memory Vermeer engine
- **HugeGraph-AI**: Includes GraphRAG, graph machine learning, the Python client, and the Vermeer Python client

### Deployment Modes

| Mode | Core Components | Suitable Scenarios | Data Scale |
|---|---|---|---|
| **Standalone** | Server + RocksDB | Development, testing, and small to medium-scale data | ≤ 2 TB |
| **Distributed** | Server + PD + Store (HStore) | Production, horizontal scaling, and multi-replica deployment | ≤ 1 PB |

See the [system introduction](introduction/) and the corresponding quick-start guides for each component's scope and startup instructions.

---

Section pages:

- [Apache HugeGraph Introduction](/versions/1.7/docs/introduction/)
- [Download Apache HugeGraph (Incubating)](/versions/1.7/docs/download/download/)
- [Quick Start](/versions/1.7/docs/quickstart/)
- [HugeGraph-Server Configuration](/versions/1.7/docs/config/)
- [Clients and APIs](/versions/1.7/docs/clients/)
- [GUIDES](/versions/1.7/docs/guides/)
- [Query Languages](/versions/1.7/docs/language/)
- [PERFORMANCE](/versions/1.7/docs/performance/)
- [Contribution Guidelines](/versions/1.7/docs/contribution-guidelines/)
- [CHANGELOGS](/versions/1.7/docs/changelog/)
- [Apache Contributor Agreements](/versions/1.7/docs/cla/)
