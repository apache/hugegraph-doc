---
title: "客户端与 API"
description: "通过 RESTful API、多语言客户端/SDK 与 Gremlin Console 连接并操作 HugeGraph。"
linkTitle: "客户端与 API"
weight: 5
search_keywords: [HugeGraph 客户端, RESTful API, Java 客户端, 客户端/SDK, Gremlin Console]
search_boost: 1.5
no_list: true
---

HugeGraph 提供多层次的访问与接入方式，涵盖标准化 RESTful API、多语言客户端/SDK 以及命令行交互式控制台。当前 Server REST API 使用图空间（GraphSpace）和图名称组成资源路径；具体路径以各 API 页面和 Server 的 OpenAPI 页面为准。

## 模块指引

- [RESTful API](/cn/docs/clients/restful-api/)

  基于 HTTP 的 REST 接口规范，覆盖图空间管理、元数据定义、顶点与边 CRUD、任务管理、指标监控等全量服务端能力。
- [客户端/SDK](/cn/docs/clients/client/)

  提供 Java、Python、Go 等语言的官方客户端 SDK，支持管理 Schema、读写顶点与边数据、执行 Gremlin 查询及调用高级图算法。
- [Gremlin Console](/cn/docs/clients/gremlin-console/)

  基于 Apache TinkerPop 的交互式命令行控制台，适合离线图操作、连接 Server 调试脚本与快速验证图遍历。
{.cards}
