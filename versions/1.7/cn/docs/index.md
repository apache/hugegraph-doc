# Documentation

LLMS 索引： [llms.txt](/versions/1.7/cn/llms.txt)

---

## Apache HugeGraph 文档

Apache HugeGraph 包含图数据库、图计算和图 AI 组件。HugeGraph 核心引擎负责属性图管理、事务处理与实时查询，Computer 和 Vermeer 运行图算法，HugeGraph-AI 提供 GraphRAG、图机器学习和 Python 客户端。

### 按场景快速导航

| 我想要... | 从这里开始 |
|----------|-----------|
| **运行图查询** (OLTP) | [HugeGraph Server 快速开始](quickstart/hugegraph/hugegraph-server) |
| **大规模图计算** (OLAP) | [图计算引擎](quickstart/computing/hugegraph-computer) |
| **构建 Graph + AI 应用** | [HugeGraph-AI](quickstart/hugegraph-ai/quick_start) |
| **批量导入数据** | [HugeGraph Loader](quickstart/toolchain/hugegraph-loader) |
| **可视化管理图** | [Hubble Web UI](quickstart/toolchain/hugegraph-hubble) |

### 生态系统一览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Apache HugeGraph 生态                         │
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

### 核心组件

- **HugeGraph 核心引擎（OLTP）**：通过 HugeGraph Server 提供 REST API，并支持 Gremlin 和 Cypher 查询
- **HugeGraph Toolchain**：包含 Java/Go Client、Loader、Hubble、Spark Connector 和 Tools；Python Client 位于 HugeGraph-AI，Rust Client 正在开发中
- **HugeGraph Computer**：仓库内包含分布式 Computer 引擎和内存计算引擎 Vermeer
- **HugeGraph-AI**：包含 GraphRAG、图机器学习、Python Client 和 Vermeer Python Client

### 部署模式

| 模式 | 核心组件 | 适用场景 | 数据规模 |
|---|---|---|---|
| **单机模式** | Server + RocksDB | 开发、测试和中小规模数据 | ≤ 2 TB |
| **分布式模式** | Server + PD + Store（HStore） | 生产环境、水平扩展和多副本部署 | ≤ 1 PB |

各组件的适用范围和启动方式见[系统介绍](introduction/)及对应快速开始文档。

---

本节页面：

- [Apache HugeGraph 介绍](/versions/1.7/cn/docs/introduction/)
- [下载 Apache HugeGraph (Incubating)](/versions/1.7/cn/docs/download/download/)
- [Quick Start](/versions/1.7/cn/docs/quickstart/)
- [HugeGraph-Server 配置](/versions/1.7/cn/docs/config/)
- [客户端与 API](/versions/1.7/cn/docs/clients/)
- [使用指南](/versions/1.7/cn/docs/guides/)
- [查询语言](/versions/1.7/cn/docs/language/)
- [PERFORMANCE](/versions/1.7/cn/docs/performance/)
- [贡献指南](/versions/1.7/cn/docs/contribution-guidelines/)
- [CHANGELOGS](/versions/1.7/cn/docs/changelog/)
- [Apache 贡献者协议](/versions/1.7/cn/docs/cla/)
