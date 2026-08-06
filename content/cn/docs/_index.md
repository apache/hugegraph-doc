---
title: "Documentation"
linkTitle: "Documentation"
weight: 20
menu:
  main:
    weight: 20
---

## Apache HugeGraph 文档

Apache HugeGraph 是一套完整的图数据库生态系统，支持 OLTP 实时查询、OLAP 离线分析和 AI 智能应用。

### 按场景快速导航

| 我想要... | 从这里开始 |
|----------|-----------|
| **运行图查询** (OLTP) | [HugeGraph Server 快速开始](quickstart/hugegraph/hugegraph-server) |
| **大规模图计算** (OLAP) | [图计算引擎](quickstart/computing/hugegraph-computer) |
| **构建 AI/RAG 应用** | [HugeGraph-AI](quickstart/hugegraph-ai/quick_start) |
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
│  │  Hubble (UI) | Loader | Client (Java/Go/Python) | Tools   │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

- **HugeGraph Server** - 图数据库核心，REST API + Gremlin + Cypher 支持
- **HugeGraph Toolchain** - 客户端 SDK、数据导入、可视化、运维工具
- **HugeGraph Computer** - 分布式图计算 (Vermeer 高性能内存版 / Computer 海量存储外存版)
- **HugeGraph-AI** - GraphRAG、知识图谱构建、20+ 图机器学习算法

### 部署模式

| 模式 | 适用场景 | 数据规模 |
|-----|---------|---------|
| **单机版** | 极速稳定、存算一体 | < 4TB |
| **分布式** | 海量存储、存算分离 | < 1000TB |
| **Docker** | 快速体验 | 任意 |

[📖 详细介绍](introduction/)
