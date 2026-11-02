# 客户端与 API

> 通过 RESTful API、多语言客户端/SDK 与 Gremlin Console 连接并操作 HugeGraph。

---

LLMS 索引： [llms.txt](/cn/llms.txt)

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

---

本节页面：

- [HugeGraph RESTful API](/cn/docs/clients/restful-api/)
- [客户端/SDK](/cn/docs/clients/client/): HugeGraph 官方多语言客户端 SDK（Java、Python、Go 等）概览与接入指引。
- [Gremlin-Console](/cn/docs/clients/gremlin-console/)
