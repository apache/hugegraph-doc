---
title: "Documentation"
linkTitle: "Documentation"
weight: 20
---

## Apache HugeGraph 文档

Apache HugeGraph 包含图数据库、图计算和图 AI 组件。Server 负责图数据存储与查询，Computer 和 Vermeer 运行图算法，HugeGraph-AI 提供 GraphRAG、图机器学习和 Python 客户端。

### 按场景快速导航

| 我想要... | 从这里开始 |
|----------|-----------|
| **运行图查询** (OLTP) | [HugeGraph Server 快速开始](quickstart/hugegraph/hugegraph-server) |
| **大规模图计算** (OLAP) | [图计算引擎](quickstart/computing/hugegraph-computer) |
| **构建 GraphRAG 应用** | [HugeGraph-AI](quickstart/hugegraph-ai/quick_start) |
| **批量导入数据** | [HugeGraph Loader](quickstart/toolchain/hugegraph-loader) |
| **可视化管理图** | [Hubble Web UI](quickstart/toolchain/hugegraph-hubble) |

### 生态系统一览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Apache HugeGraph 生态                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ HugeGraph   │  │ HugeGraph   │  │ HugeGraph-AI            │  │
│  │ Server      │  │ Computer    │  │ (GraphRAG/ML/Python)    │  │
│  │ (OLTP)      │  │ (OLAP)      │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│         │               │                    │                   │
│  ┌──────┴───────────────┴────────────────────┴──────────────┐   │
│  │              HugeGraph Toolchain                          │   │
│  │  Hubble (UI) | Loader | Client (Java/Go) | Tools         │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

- **HugeGraph Server**：提供 REST API，并支持 Gremlin 和 Cypher 查询
- **HugeGraph Toolchain**：包含 Java/Go Client、Loader、Hubble、Spark Connector 和 Tools
- **HugeGraph Computer**：仓库内包含分布式 Computer 引擎和内存计算引擎 Vermeer
- **HugeGraph-AI**：包含 GraphRAG、图机器学习、Python Client 和 Vermeer Python Client

部署 Server 时可以使用单机 RocksDB 后端，也可以使用由 PD 和 Store 组成的 HStore 分布式后端。各组件的适用范围和启动方式见[系统介绍](introduction/)及对应快速开始文档。
