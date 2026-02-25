---
title: "Introduction with HugeGraph"
linkTitle: "Introduction"
weight: 1
aliases:
  - /cn/docs/introduction/readme/
  - /cn/docs/introduction/README/
---

### Summary

Apache HugeGraph 是一款易用、高效、通用的开源图数据库系统（Graph Database，[GitHub 项目地址](https://github.com/apache/hugegraph)），
实现了[Apache TinkerPop3](https://tinkerpop.apache.org)框架及完全兼容[Gremlin](https://tinkerpop.apache.org/gremlin.html)查询语言，
同时支持 [Cypher](https://opencypher.org/) 查询语言（OpenCypher 标准），
具备完善的工具链组件，助力用户轻松构建基于图数据库之上的应用和产品。HugeGraph 支持百亿以上的顶点和边快速导入，并提供毫秒级的关联关系查询能力（OLTP），
并支持大规模分布式图分析（OLAP）。

HugeGraph 典型应用场景包括深度关系探索、关联分析、路径搜索、特征抽取、数据聚类、社区检测、知识图谱等，
适用业务领域有如网络安全、电信诈骗、金融风控、广告推荐、社交网络和智能机器人等。

本系统的主要应用场景是解决反欺诈、威胁情报、黑产打击等业务的图数据存储和建模分析需求，在此基础上逐步扩展及支持了更多的通用图应用。

### Features

HugeGraph 支持在线及离线环境下的图操作，支持批量导入数据，支持高效的复杂关联关系分析，并且能够与大数据平台无缝集成。
HugeGraph 支持多用户并行操作，用户可输入 Gremlin/Cypher 查询语句，并及时得到图查询结果，也可在用户程序中调用 HugeGraph API 进行图分析或查询。

本系统具备如下特点：

- 易用：HugeGraph 支持 Gremlin/Cypher 图查询语言与 RESTful API，同时提供图检索常用接口，具备功能齐全的周边工具，轻松实现基于图的各种查询分析运算。
- 高效：HugeGraph 在图存储和图计算方面做了深度优化，提供多种批量导入工具，轻松完成百亿级数据快速导入，通过优化过的查询达到图检索的毫秒级响应。支持数千用户并发的在线实时操作。
- 通用：HugeGraph 支持 Apache Gremlin 标准图查询语言和 Property Graph 标准图建模方法，支持基于图的 OLTP 和 OLAP 方案。集成 Apache Hadoop 及 Apache Spark 大数据平台。
- 可扩展：支持分布式存储、数据多副本及横向扩容，内置多种后端存储引擎，也可插件式轻松扩展后端存储引擎。
- 开放：HugeGraph 代码开源（Apache 2 License），客户可自主修改定制，选择性回馈开源社区。

### 部署模式

HugeGraph 支持多种部署模式，满足不同规模和场景的需求：

**单机模式 (Standalone)**
- Server + RocksDB 后端存储
- 适合开发测试和中小规模数据（< 4TB）
- Docker 快速启动: `docker run hugegraph/hugegraph`
- 详见 [Server 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-server)

**分布式模式 (Distributed)**
- HugeGraph-PD: 元数据管理和集群调度
- HugeGraph-Store (HStore): 分布式存储引擎
- 支持水平扩展和高可用（< 1000TB 数据规模）
- 适合生产环境和大规模图数据应用

### 快速入门指南

| 使用场景 | 推荐路径 |
|---------|---------|
| 快速体验 | [Docker 部署](/cn/docs/quickstart/hugegraph/hugegraph-server#docker) |
| 构建 OLTP 应用 | Server → REST API / Gremlin / Cypher |
| 图分析 (OLAP) | [Vermeer](/cn/docs/quickstart/computing/hugegraph-computer) (推荐) 或 Computer |
| 构建 AI 应用 | [HugeGraph-AI](/cn/docs/quickstart/hugegraph-ai) (GraphRAG/知识图谱) |
| 批量导入数据 | [Loader](/cn/docs/quickstart/toolchain/hugegraph-loader) + [Hubble](/cn/docs/quickstart/toolchain/hugegraph-hubble) |

### 功能特性

- 支持从多数据源批量导入数据 (包括本地文件、HDFS 文件、MySQL 数据库等数据源)，支持多种文件格式导入 (包括 TXT、CSV、JSON 等格式)
- 具备可视化操作界面，可用于操作、分析及展示图，降低用户使用门槛
- 优化的图接口：最短路径 (Shortest Path)、K 步连通子图 (K-neighbor)、K 步到达邻接点 (K-out)、个性化推荐算法 PersonalRank 等
- 基于 Apache TinkerPop3 框架实现，支持 Gremlin 图查询语言
- 支持属性图，顶点和边均可添加属性，支持丰富的属性类型
- 具备独立的 Schema 元数据信息，拥有强大的图建模能力，方便第三方系统集成
- 支持多顶点 ID 策略：支持主键 ID、支持自动生成 ID、支持用户自定义字符串 ID、支持用户自定义数字 ID	
- 可以对边和顶点的属性建立索引，支持精确查询、范围查询、全文检索	
- 存储系统采用插件方式，支持 RocksDB(单机/集群)、Cassandra、ScyllaDB、HBase、MySQL、PostgreSQL、Palo 以及 Memory 等
- 与 HDFS、Spark/Flink、GraphX 等大数据系统集成，支持 BulkLoad 操作导入海量数据
- 支持高可用 HA、数据多副本、备份恢复、监控、分布式 Trace 等

### Modules

- [HugeGraph-Server](/cn/docs/quickstart/hugegraph/hugegraph-server): HugeGraph-Server 是 HugeGraph 项目的核心部分，包含 Core、Backend、API 等子模块；
  - Core：图引擎实现，向下连接 Backend 模块，向上支持 API 模块；
  - Backend：实现将图数据存储到后端，支持的后端包括：Memory、Cassandra、ScyllaDB、RocksDB、HBase、MySQL 及 PostgreSQL，用户根据实际情况选择一种即可；
  - API：内置 REST Server，向用户提供 RESTful API，同时完全兼容 Gremlin 查询。(支持分布式存储和计算下推)
- [HugeGraph-Toolchain](https://github.com/apache/hugegraph-toolchain): (工具链)
  - [HugeGraph-Client](/cn/docs/quickstart/client/hugegraph-client)：HugeGraph-Client 提供了 RESTful API 的客户端，用于连接 HugeGraph-Server，支持 Java/Python/Go 多语言版本；
  - [HugeGraph-Loader](/cn/docs/quickstart/toolchain/hugegraph-loader)：HugeGraph-Loader 是基于 HugeGraph-Client 的数据导入工具，将普通文本数据转化为图形的顶点和边并插入图形数据库中；
  - [HugeGraph-Hubble](/cn/docs/quickstart/toolchain/hugegraph-hubble)：HugeGraph-Hubble 是 HugeGraph 的 Web
可视化管理平台，一站式可视化分析平台，平台涵盖了从数据建模，到数据快速导入，再到数据的在线、离线分析、以及图的统一管理的全过程；
  - [HugeGraph-Tools](/cn/docs/quickstart/toolchain/hugegraph-tools)：HugeGraph-Tools 是 HugeGraph 的部署和管理工具，包括管理图、备份/恢复、Gremlin 执行等功能。
- [HugeGraph-Computer](/cn/docs/quickstart/computing/hugegraph-computer)：HugeGraph-Computer 是分布式图处理系统 (OLAP)。
  它是 [Pregel](https://kowshik.github.io/JPregel/pregel_paper.pdf) 的一个实现。它可以运行在 Kubernetes/Yarn
  等集群上，支持超大规模图计算。同时提供 Vermeer 轻量级图计算引擎，适合快速开始和中小规模图分析。
- [HugeGraph-AI](/cn/docs/quickstart/hugegraph-ai)：HugeGraph-AI 是 HugeGraph 独立的 AI
  组件，提供 LLM/GraphRAG 智能问答、自动化知识图谱构建、图神经网络训练/推理、Python-Client 等功能，内置 20+ 图机器学习算法，持续更新中。

### Contact Us

- [GitHub Issues](https://github.com/apache/hugegraph/issues): 使用途中出现问题或提供功能性建议，可通过此反馈 (推荐)
- 邮件反馈：[dev@hugegraph.apache.org](mailto:dev@hugegraph.apache.org) ([邮箱订阅方式](https://hugegraph.apache.org/docs/contribution-guidelines/subscribe/))
- SEC 反馈： [security@hugegraph.apache.org](mailto:security@hugegraph.apache.org) (报告安全相关问题)
- 微信公众号：Apache HugeGraph, 欢迎扫描下方二维码加入我们！

 <img src="https://github.com/apache/hugegraph-doc/blob/master/assets/images/wechat.png?raw=true" alt="QR png" width="300"/>
