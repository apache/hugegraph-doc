---
title: "HugeGraph Architecture Overview"
linkTitle: "架构概览"
weight: 1
---

### 1 概述

作为一套覆盖**图数据库、图计算与图 AI** 的全栈图系统，HugeGraph 以高性能图引擎（HugeGraph Server）为核心，支持 OLTP 和 OLAP 两种图计算类型。其中 OLTP 层实现了 [Apache TinkerPop3](https://tinkerpop.apache.org) 框架，支持 [Gremlin](https://tinkerpop.apache.org/gremlin.html) 和 [Cypher](https://en.wikipedia.org/wiki/Cypher) 查询语言，拥有功能齐全的应用工具链，还提供了插件式后端存储驱动框架。

下面是 HugeGraph 的整体架构图：

<div style="text-align: center;">
  <img src="/docs/images/design/architectural-revised.png" alt="image">
</div>

HugeGraph 包括三个层次的功能，分别是应用程序层、图引擎层和存储层。

- 应用程序层：
  - [Hubble](/cn/docs/quickstart/toolchain/hugegraph-hubble/): 一站式可视化分析平台，平台涵盖了从数据建模，到数据快速导入，再到数据的在线、离线分析、以及图的统一管理的全过程，实现了图应用的全流程向导式操作。
  - [Loader](/cn/docs/quickstart/toolchain/hugegraph-loader/): 数据导入组件，能够将多种数据源的数据转化为图的顶点和边并批量导入到图数据库中。
  - [Tools](/cn/docs/quickstart/toolchain/hugegraph-tools/): 命令行工具，用于部署、管理和备份/恢复 HugeGraph 中的数据。
  - [Computer](/cn/docs/quickstart/computing/hugegraph-computer/): 分布式图处理系统 (OLAP)，它是 [Pregel](https://kowshik.github.io/JPregel/pregel_paper.pdf) 的一个实现，可以运行在 Kubernetes 上。
  - [Client](/cn/docs/quickstart/client/hugegraph-client/): 使用 Java 编写的 HugeGraph 客户端，用户可以使用 Client 编写 Java 代码操作 HugeGraph，后续可根据需要提供 Python、Go、C++ 等多语言支持。
- [图引擎层](/cn/docs/quickstart/hugegraph/hugegraph-server/)：
  - REST Server: 提供 RESTful API 用于查询 Graph/Schema 等信息，支持 [Gremlin](https://tinkerpop.apache.org/gremlin.html) 和 [Cypher](https://en.wikipedia.org/wiki/Cypher) 查询语言，提供服务监控和运维的 APIs。
  - Graph Engine: 支持 OLTP 和 OLAP 两种图计算类型，其中 OLTP 实现了 [Apache TinkerPop3](https://tinkerpop.apache.org) 框架。
  - Backend Interface: 实现将图数据存储到后端。
- 存储层：
  - Storage Backend: 支持多种内置存储后端 (RocksDB/MySQL/HBase/...)，也允许用户无需更改现有源码的情况下扩展自定义后端。
