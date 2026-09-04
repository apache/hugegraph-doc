---
title: "Apache HugeGraph 介绍"
linkTitle: "系统介绍"
weight: 1
aliases:
  - /cn/docs/introduction/readme/
  - /cn/docs/introduction/README/
---

## Apache HugeGraph 是什么

Apache HugeGraph 由多个独立仓库组成，覆盖图数据库、图计算和图 AI。各组件可以单独使用，也可以通过 HugeGraph Server 的 REST API 或分布式存储接口协作。

```text
应用与工具
  ├─ HugeGraph Toolchain：Client、Loader、Hubble、Spark Connector、Tools
  └─ HugeGraph-AI：GraphRAG、图机器学习、Python Client
                         │
图数据库                 ▼
  HugeGraph Server：REST API、Gremlin、Cypher
       ├─ RocksDB 等单机后端
       └─ HStore 分布式后端 → PD + Store
                         │
图计算                   ▼
  HugeGraph-Computer：Vermeer（Go）与 Computer（Java）
```

## HugeGraph Server

Server 是图数据库服务。`hugegraph-core` 实现属性图、Schema、查询和后端接口，`hugegraph-api` 提供 REST API。当前 REST 资源路径包含图空间与图名称，例如：

```text
/graphspaces/{graphspace}/graphs/{graph}
```

Server 支持 Gremlin 和 Cypher。单机部署通常使用 RocksDB；分布式部署使用 HStore，并由 PD 管理元数据和分区、Store 保存数据副本。

- [Server 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-server/)
- [PD 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-pd/)
- [HStore 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-hstore/)
- [REST API](/cn/docs/clients/restful-api/)

## Toolchain

Toolchain 仓库包含以下模块：

| 模块 | 用途 |
|---|---|
| [Java Client](/cn/docs/quickstart/client/hugegraph-client/) | 调用 Server 的 Schema、图数据、Gremlin 和 Traverser API |
| [Go Client](/cn/docs/quickstart/client/hugegraph-client-go/) | Go 语言客户端；当前仍处于开发阶段 |
| [Loader](/cn/docs/quickstart/toolchain/hugegraph-loader/) | 从文件、HDFS、JDBC、Kafka 或其他图读取数据并写入 HugeGraph |
| [Hubble](/cn/docs/quickstart/toolchain/hugegraph-hubble/) | 图管理 Web 界面和后端服务 |
| [Spark Connector](/cn/docs/quickstart/toolchain/hugegraph-spark-connector/) | 在 Spark 作业中读写 HugeGraph |
| [Tools](/cn/docs/quickstart/toolchain/hugegraph-tools/) | 图管理、备份和恢复命令 |

## 图计算

HugeGraph-Computer 仓库包含两个实现：

- Vermeer 使用 Go 编写，采用 master-worker 架构，图数据以内存存储为主，并提供 REST API、gRPC 和 Web UI。
- Computer 使用 Java 编写，是 BSP/Pregel 风格的分布式计算框架，可部署到 Kubernetes 或 YARN。

两者都能读取 HugeGraph 数据，但部署方式、配置和算法接口不同。

- [Vermeer 快速开始](/cn/docs/quickstart/computing/hugegraph-vermeer/)
- [Computer 快速开始](/cn/docs/quickstart/computing/hugegraph-computer/)

## HugeGraph-AI

HugeGraph-AI 要求 Python 3.10 或更高版本，使用 `uv` 管理工作区。仓库包含 `hugegraph-llm`、`hugegraph-ml`、`hugegraph-python-client` 和 `vermeer-python-client`：

- `hugegraph-llm` 提供 GraphRAG、知识图谱构建和自然语言查询相关功能。
- `hugegraph-ml` 包含图分类、节点分类、图嵌入和链接预测实现。
- 两个 Python Client 分别连接 HugeGraph Server 和 Vermeer。

[HugeGraph-AI 快速开始](/cn/docs/quickstart/hugegraph-ai/quick_start/)

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
