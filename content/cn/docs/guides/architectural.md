---
title: "HugeGraph Architecture Overview"
linkTitle: "架构概览"
weight: 1
---

### 1 概述

HugeGraph 包含图数据库、图计算和图 AI 组件。HugeGraph Server 实现 Apache TinkerPop 接口，提供 Gremlin、Cypher 和 REST API；Computer 负责 OLAP 图计算，AI 仓库提供图与大模型相关工具。

下面是 HugeGraph 的整体架构图：

<div style="text-align: center;">
  <img src="/docs/images/design/architectural-revised.png" alt="image">
</div>

HugeGraph 包括三个层次的功能，分别是应用程序层、图引擎层和存储层。

- 应用程序层：
  - [Hubble](/cn/docs/quickstart/toolchain/hugegraph-hubble/): 图建模、数据导入、查询和管理的 Web 界面。
  - [Loader](/cn/docs/quickstart/toolchain/hugegraph-loader/): 将外部数据转换为顶点和边并批量写入 HugeGraph。
  - [Tools](/cn/docs/quickstart/toolchain/hugegraph-tools/): 命令行工具，用于部署、管理和备份/恢复 HugeGraph 中的数据。
  - [Computer](/cn/docs/quickstart/computing/hugegraph-computer/): 基于 Pregel 模型的分布式图计算系统，可运行在 Kubernetes 上。
  - [Client](/cn/docs/quickstart/client/hugegraph-client/): Java 客户端。文档还提供 Python 和 Go 客户端入口。
- [图引擎层](/cn/docs/quickstart/hugegraph/hugegraph-server/)：
  - REST Server: 提供 RESTful API 用于查询 Graph/Schema 等信息，支持 [Gremlin](https://tinkerpop.apache.org/gremlin.html) 和 [Cypher](https://en.wikipedia.org/wiki/Cypher) 查询语言，提供服务监控和运维的 APIs。
  - Graph Engine: 支持 OLTP 和 OLAP 两种图计算类型，其中 OLTP 实现了 [Apache TinkerPop3](https://tinkerpop.apache.org) 框架。
  - Backend Interface: 实现将图数据存储到后端。
- 存储层：
  - Storage Backend: 1.7.0 支持 RocksDB、HStore、HBase 和 Memory。自定义后端可通过插件扩展。
