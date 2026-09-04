---
title: "Apache HugeGraph 介绍"
linkTitle: "系统介绍"
weight: 1
aliases:
  # Hugo 0.165 prefixes aliases with the current language path.
  - /docs/introduction/readme/
  - /docs/introduction/README/
---

## 什么是 Apache HugeGraph？

[Apache HugeGraph](https://hugegraph.apache.org/) 是一套易用、高效、通用的开源**全栈图系统**（[GitHub](https://github.com/apache/hugegraph)），覆盖**图数据库**（OLTP 实时查询）、**图计算**（OLAP 大规模分析）与**图 AI**（GraphRAG / 图机器学习）三大领域。

HugeGraph 支持百亿以上的顶点和边的快速存储与查询，具备出色的 OLTP 性能。其图引擎兼容 [Apache TinkerPop 3](https://tinkerpop.apache.org) 框架，同时支持 [Gremlin](https://tinkerpop.apache.org/gremlin.html) 和 [Cypher](https://en.wikipedia.org/wiki/Cypher)（OpenCypher 标准）查询语言。

**典型应用场景：** 深度关系探索、关联分析、路径搜索、特征抽取、社区检测、知识图谱等。  
**适用领域：** 网络安全、电信反欺诈、金融风控、广告推荐、社交网络、智能问答等。

## 生态系统全景

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

## HugeGraph Server（OLTP 图引擎）

HugeGraph Server 是图数据库的 OLTP 引擎和服务入口，负责属性图建模、事务处理、查询执行和 API 接入。图数据实际保存在配置的 RocksDB、HStore 或 HBase 后端中。

- **属性图与 Schema**：支持 VertexLabel、EdgeLabel、PropertyKey 和 IndexLabel 管理
- **查询语言**：支持 Gremlin（TinkerPop 3）和 Cypher（OpenCypher）
- **REST API**：提供 Schema、图数据、查询、任务和运维接口
- **索引与查询**：支持精确查询、范围查询和复合条件查询
- **存储后端**：1.7.0 至 `master` 主要支持 RocksDB（单机）、HStore（分布式）和 HBase

主要模块包括 `hugegraph-core`、存储后端模块和 `hugegraph-api`。Core 实现图模型、事务和查询逻辑，后端模块负责连接具体存储系统，API 模块负责 HTTP 接入。当前 REST 资源路径包含图空间与图名称，例如：

```text
/graphspaces/{graphspace}/graphs/{graph}
```

单机部署通常使用 RocksDB。分布式部署使用 HStore，由 PD 管理集群元数据和分区调度，Store 保存图数据及其副本。HBase 可作为独立的后端存储。

- [Server 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-server/)
- [PD 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-pd/)
- [HStore 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-hstore/)
- [REST API](/cn/docs/clients/restful-api/)

## HugeGraph Toolchain

HugeGraph Toolchain 提供客户端、数据导入、可视化管理、Spark 集成和命令行运维工具，覆盖图应用从接入数据到日常管理的主要环节。

| 模块 | 用途 |
|---|---|
| [Client](/cn/docs/quickstart/client/hugegraph-client/) | 封装 Schema 管理、图数据读写、Gremlin 和 Traverser API；支持 Java、[Python](/cn/docs/quickstart/client/hugegraph-client-python/) 和 [Go](/cn/docs/quickstart/client/hugegraph-client-go/)，Rust 客户端正在开发中 |
| [Loader](/cn/docs/quickstart/toolchain/hugegraph-loader/) | 从本地文件、HDFS、JDBC、Kafka 或其他图读取数据，转换为顶点和边后批量导入 HugeGraph |
| [Hubble](/cn/docs/quickstart/toolchain/hugegraph-hubble/) | 提供图连接、Schema、数据导入、Gremlin 查询和图形化结果展示的 Web 管理界面 |
| [Spark Connector](/cn/docs/quickstart/toolchain/hugegraph-spark-connector/) | 在 Spark 作业中批量读写 HugeGraph，适合大数据离线处理 |
| [Tools](/cn/docs/quickstart/toolchain/hugegraph-tools/) | 提供部署、图管理、备份恢复和 Gremlin 执行等命令行能力 |

## 图计算引擎（OLAP）

HugeGraph-Computer 仓库提供两种互补的 OLAP 图计算引擎：

- **Vermeer**：使用 Go 编写，采用 master-worker 架构，以内存计算为主，提供 REST API、gRPC 和 Web UI，适合快速执行中小规模图分析任务。
- **Computer**：使用 Java 编写，实现 BSP/Pregel 分布式计算模型，可运行在 Kubernetes、YARN 或本地进程中。数据超过内存阈值时可以落盘，适合更大规模的图计算任务。

两者都可以读取 HugeGraph 数据，但运行架构、资源需求、配置和算法接口不同。

- [Vermeer 快速开始](/cn/docs/quickstart/computing/hugegraph-vermeer/)
- [Computer 快速开始](/cn/docs/quickstart/computing/hugegraph-computer/)

## HugeGraph-AI（Graph + AI）

HugeGraph-AI 连接图技术与大语言模型、图机器学习框架。仓库使用 Python 3.10 或更高版本，并通过 `uv` 管理工作区，主要包含以下模块：

- **hugegraph-llm**：提供 GraphRAG、知识图谱构建、自然语言查询和 Text2Gremlin
- **hugegraph-ml**：提供节点分类、图分类、图嵌入、链接预测和欺诈检测等模型
- **hugegraph-python-client**：通过 Python 管理 Schema、图数据和 Gremlin 查询
- **vermeer-python-client**：通过 Python 调用 Vermeer 图计算服务

[HugeGraph-AI 快速开始](/cn/docs/quickstart/hugegraph-ai/quick_start/)

## 部署模式

| 模式 | 核心组件 | 适用场景 | 数据规模 |
|---|---|---|---|
| **单机模式（OLTP）** | Server + RocksDB | 开发、测试和中小规模数据 | ≤ 2 TB |
| **分布式模式（OLTP）** | Server + PD + Store（HStore） | 生产环境、水平扩展和多副本部署 | ≤ 1 PB |

图计算属于 OLAP 任务，容量和资源需求取决于所选引擎、图结构与算法，不沿用上表的 OLTP 存储容量口径。

## 选择入口

| 需求 | 文档 |
|---|---|
| 启动图数据库并执行查询 | [Server 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-server/) |
| 批量导入数据 | [Loader](/cn/docs/quickstart/toolchain/hugegraph-loader/) |
| 使用 Web 界面管理图 | [Hubble](/cn/docs/quickstart/toolchain/hugegraph-hubble/) |
| 运行图算法 | [Vermeer 与 Computer](/cn/docs/quickstart/computing/) |
| 构建 GraphRAG 或图机器学习应用 | [HugeGraph-AI](/cn/docs/quickstart/hugegraph-ai/) |

## 社区

- [GitHub Issues](https://github.com/apache/hugegraph/issues)
- 开发者邮件列表：[dev@hugegraph.apache.org](mailto:dev@hugegraph.apache.org)
- [邮件列表订阅方法](/cn/docs/contribution-guidelines/subscribe/)
- 安全问题：[security@hugegraph.apache.org](mailto:security@hugegraph.apache.org)
- 微信公众号：Apache HugeGraph

![微信公众号二维码](/images/docs/community/wechat.png)
{width="300" height="94"}
