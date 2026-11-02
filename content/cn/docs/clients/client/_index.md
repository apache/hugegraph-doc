---
title: "客户端/SDK"
linkTitle: "客户端/SDK"
weight: 2
description: "HugeGraph 官方多语言客户端 SDK（Java、Python、Go 等）概览与接入指引。"
aliases:
  - /docs/quickstart/client/
---

HugeGraph 提供多语言客户端 SDK，方便在不同语言与技术栈中连接 HugeGraph Server，进行 Schema 管理、顶点与边数据读写、Gremlin 遍历及高级分析。

## 支持的客户端

- [HugeGraph Java Client](/cn/docs/clients/client/hugegraph-client/)

  官方核心 Java SDK，提供与 Gremlin 语法相近的 API 风格，支持完整的 Schema 管理、CRUD、Gremlin 查询及 Traverser 算法，并支持 GraphSpace 隔离。
- [HugeGraph Python Client](/cn/docs/clients/client/hugegraph-client-python/)

  官方 Python SDK（`pyhugegraph`），位于 HugeGraph-AI 仓库，支持管理 Schema、读写图数据及提交 Gremlin 查询，深度集成 HugeGraph-LLM 与 HugeGraph-ML。
- [HugeGraph Go Client](/cn/docs/clients/client/hugegraph-client-go/)

  官方 Go SDK，支持版本查询、Schema 定义（PropertyKey/VertexLabel/EdgeLabel）、顶点操作与 Gremlin 查询。
{.cards}

## 选择建议

- **生产级 Java/Scala 服务**：推荐使用 **HugeGraph Java Client**，功能最完备，覆盖所有底层能力与连接池管理。
- **AI/LLM/算法与数据科学应用**：推荐使用 **HugeGraph Python Client**（`pyhugegraph`），深度适配 HugeGraph-LLM、HugeGraph-ML 及 Python 数据科学分析工作流。
- **微服务与云原生工具构建**：推荐使用 **HugeGraph Go Client** 或直接调用 [RESTful API](/cn/docs/clients/restful-api/)。
- **终端离线调试或临时查询**：推荐使用 [Gremlin Console](/cn/docs/clients/gremlin-console/)。
