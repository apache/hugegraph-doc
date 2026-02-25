---
title: "Documentation"
linkTitle: "Documentation"
weight: 20
menu:
  main:
    weight: 20
---

## Apache HugeGraph Documentation

Apache HugeGraph is a complete graph database ecosystem, supporting OLTP real-time queries, OLAP offline analysis, and AI intelligent applications.

### Quick Navigation by Scenario

| I want to... | Start here |
|----------|-----------|
| **Run graph queries** (OLTP) | [HugeGraph Server Quickstart](quickstart/hugegraph/hugegraph-server) |
| **Large-scale graph computing** (OLAP) | [Graph Computing Engine](quickstart/computing/hugegraph-computer) |
| **Build AI/RAG applications** | [HugeGraph-AI](quickstart/hugegraph-ai/quick_start) |
| **Batch import data** | [HugeGraph Loader](quickstart/toolchain/hugegraph-loader) |
| **Visualize and manage graphs** | [Hubble Web UI](quickstart/toolchain/hugegraph-hubble) |

### Ecosystem Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Apache HugeGraph Ecosystem                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ HugeGraph   │  │ HugeGraph   │  │ HugeGraph-AI            │  │
│  │ Server      │  │ Computer    │  │ (GraphRAG/ML/Python)    │  │
│  │ (OLTP)      │  │ (OLAP)      │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│         │               │                    │                   │
│  ┌──────┴───────────────┴────────────────────┴──────────────┐   │
│  │              HugeGraph Toolchain                          │   │
│  │  Hubble (UI) | Loader | Client (Java/Go/Python) | Tools   │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

- **HugeGraph Server** - Core graph database with REST API + Gremlin + Cypher support
- **HugeGraph Toolchain** - Client SDKs, data import, visualization, and operational tools
- **HugeGraph Computer** - Distributed graph computing (Vermeer high-performance in-memory / Computer massive external storage)
- **HugeGraph-AI** - GraphRAG, knowledge graph construction, 20+ graph ML algorithms

### Deployment Modes

| Mode | Use Case | Data Scale |
|-----|---------|---------|
| **Standalone** | High-speed stable, compute-storage integrated | < 4TB |
| **Distributed** | Massive storage, compute-storage separated | < 1000TB |
| **Docker** | Quick start | Any |

[📖 Detailed Introduction](introduction/)
