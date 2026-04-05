---
title: "Introduction with HugeGraph"
linkTitle: "Introduction"
weight: 1
aliases:
  - /cn/docs/introduction/readme/
  - /cn/docs/introduction/README/
---

### 什么是 Apache HugeGraph？

[Apache HugeGraph](https://hugegraph.apache.org/) 是一套易用、高效、通用的开源**全栈图系统**（[GitHub](https://github.com/apache/hugegraph)），
覆盖**图数据库**（OLTP 实时查询）、**图计算**（OLAP 大规模分析）与**图 AI**（GraphRAG / 图机器学习）三大领域。

HugeGraph 支持百亿以上的顶点和边的快速存储与查询，具备出色的 OLTP 性能。
其图引擎完全兼容 [Apache TinkerPop 3](https://tinkerpop.apache.org) 框架，同时支持
[Gremlin](https://tinkerpop.apache.org/gremlin.html) 和 [Cypher](https://en.wikipedia.org/wiki/Cypher)（OpenCypher 标准）双查询语言。

**典型应用场景：** 深度关系探索、关联分析、路径搜索、特征抽取、社区检测、知识图谱等，  
**适用领域：** 网络安全、电信反欺诈、金融风控、广告推荐、社交网络、智能问答等。

---

### 生态系统全景

```
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

### 核心组件

#### 🗄️ HugeGraph Server — 图引擎（OLTP）

HugeGraph 项目的核心模块，提供高性能的图数据存储与实时查询能力：

- **图引擎核心**：支持属性图（Property Graph）建模，包含 VertexLabel、EdgeLabel、PropertyKey、IndexLabel 完整 Schema 管理
- **双查询语言**：全面兼容 Gremlin（TinkerPop 3）和 Cypher（OpenCypher）
- **REST API**：内置 REST Server，提供 RESTful 图操作接口
- **多类型索引**：精确查询、范围查询、复合条件组合查询
- **插件式存储后端**：1.7.0+ 默认支持 `RocksDB`（单机默认）、`HStore`（分布式）、`HBase`、`Memory`，1.5.x 及以前还支持 MySQL / PostgreSQL / Cassandra 等

**子模块：**
- `Core` — 图引擎实现，向下连接 Backend，向上支持 API
- `Backend` — 多后端存储适配层
- `API` — RESTful 接入层，兼容 Gremlin/Cypher 查询

📖 [Server 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-server)

---

#### 📊 图计算引擎（OLAP）

提供两种互补的图分析引擎：

- **Vermeer**（推荐）：高性能纯内存图计算引擎，部署简单、响应快，适合中小规模图分析和快速上手
- **HugeGraph-Computer**：基于 [Pregel](https://kowshik.github.io/JPregel/pregel_paper.pdf) 的分布式 OLAP 引擎，可运行在 Kubernetes / Yarn 上，适合超大规模图算法任务

📖 [图计算快速开始](/cn/docs/quickstart/computing/hugegraph-vermeer)

---

#### 🤖 HugeGraph-AI — 图 AI 生态

HugeGraph 独立的 AI 组件，连接图与大语言模型（LLM）：

- **GraphRAG**：基于图的检索增强生成，实现 LLM 智能问答
- **知识图谱构建**：自动从非结构化文本中提取实体和关系，构建知识图谱
- **图神经网络**：支持 GNN 模型的训练与推理
- **20+ 图机器学习算法**：内置丰富的图分析算法，持续更新
- **Python Client**：为 AI 应用提供便捷的 Python SDK

📖 [HugeGraph-AI 快速开始](/cn/docs/quickstart/hugegraph-ai/quick_start)

---

#### 🛠️ HugeGraph Toolchain — 工具链

围绕图系统的完整工具生态（[toolchain 仓库](https://github.com/apache/hugegraph-toolchain)）：

| 工具 | 说明 |
|------|------|
| [Hubble](/cn/docs/quickstart/toolchain/hugegraph-hubble) | Web 可视化平台：数据建模 → 批量导入 → 在线/离线分析 一站式操作 |
| [Loader](/cn/docs/quickstart/toolchain/hugegraph-loader) | 数据导入工具：支持本地文件、HDFS、MySQL 等多数据源，TXT/CSV/JSON 等格式 |
| [Client](/cn/docs/quickstart/client/hugegraph-client) | 多语言 SDK：Java / Python / Go |
| [Spark-connector](/cn/docs/quickstart/toolchain/hugegraph-spark-connector) | Spark 集成：支持通过 Spark 批量读写图数据，适合大数据离线处理场景 |
| [Tools](/cn/docs/quickstart/toolchain/hugegraph-tools) | 命令行运维工具：图管理、备份恢复、Gremlin 执行等 |

---

### 部署模式

HugeGraph 支持两种主要部署模式：

| 模式 | 核心组件 | 适用场景 | 数据规模 | 高可用 |
|------|---------|---------|---------|-------|
| **单机 (Standalone)** | Server + RocksDB | 开发、测试、单节点生产 | < 4TB | 基础 |
| **分布式 (Distributed)** | Server + PD（3-5节点）+ Store（3+节点） | 生产环境、水平扩展 | < 1000TB | ✅ |

**Docker 快速体验：**

```bash
docker run -itd --name=hugegraph -p 8080:8080 hugegraph/hugegraph
```

---

### 快速入门导航

| 我想要... | 从这里开始 |
|---------|---------|
| 🚀 **快速体验** | [Docker 部署](/cn/docs/quickstart/hugegraph/hugegraph-server) |
| 🔍 **运行图查询** (OLTP) | [HugeGraph Server 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-server) |
| 📈 **大规模图计算** (OLAP) | [Vermeer / Computer](/cn/docs/quickstart/computing/hugegraph-computer) |
| 🤖 **构建 AI/RAG 应用** | [HugeGraph-AI](/cn/docs/quickstart/hugegraph-ai/quick_start) |
| 📥 **批量导入数据** | [HugeGraph Loader](/cn/docs/quickstart/toolchain/hugegraph-loader) |
| 🖥️ **可视化管理** | [Hubble Web UI](/cn/docs/quickstart/toolchain/hugegraph-hubble) |

---

### 系统特性

- **易用**：Gremlin/Cypher 双查询语言 + RESTful API，功能齐全的工具链，轻松上手
- **高效**：图存储与查询深度优化，毫秒级响应，支持数千并发在线操作，百亿级数据快速导入
- **通用**：支持 OLTP + OLAP 双模式，无缝对接 Apache Hadoop、Spark、Flink 大数据生态
- **可扩展**：分布式存储、数据多副本、横向扩容，插件式后端可灵活扩展
- **开放**：Apache 2.0 License，完全开源，欢迎社区贡献

---

### 联系我们

- [GitHub Issues](https://github.com/apache/hugegraph/issues)：问题反馈与功能建议（推荐）
- 邮件：[dev@hugegraph.apache.org](mailto:dev@hugegraph.apache.org)（[订阅方式](/cn/docs/contribution-guidelines/subscribe/)）
- 安全问题：[security@hugegraph.apache.org](mailto:security@hugegraph.apache.org)
- 微信公众号：Apache HugeGraph

<img src="https://github.com/apache/hugegraph-doc/blob/master/assets/images/wechat.png?raw=true" alt="微信公众号二维码" width="300"/>
