---
title: "HugeGraph RESTful API"
linkTitle: "RESTful API"
weight: 1
search_keywords: [HugeGraph REST API, RESTful API, OpenAPI]
search_boost: 1.7
---

> ⚠️ **版本兼容性说明**
>
> - 当前 API 的图资源路径以 `/graphspaces/{graphspace}/graphs/{graph}` 开头。
> - HugeGraph 1.5.x 及更早版本使用 `/graphs/{graph}`。创建、克隆图等接口的请求格式也与当前版本不同。
> - 默认图空间名是 `DEFAULT`。
> - 旧版本 doc 参考：[HugeGraph 1.5.x RESTful API](https://github.com/apache/hugegraph-doc/tree/release-1.5.0)

Server 启动后，可访问 `http://localhost:8080/swagger-ui/index.html` 查看当前版本的 OpenAPI 页面。[使用示例](/cn/docs/quickstart/hugegraph/hugegraph-server#swaggerui-example)

[comment]: <> (- Graph Schema)

[comment]: <> (    - [Schema]&#40;restful-api/schema.md&#41;)

[comment]: <> (    - [PropertyKey]&#40;restful-api/propertykey.md&#41;)

[comment]: <> (    - [VertexLabel]&#40;restful-api/vertexlabel.md&#41;)

[comment]: <> (    - [EdgeLabel]&#40;restful-api/edgelabel.md&#41;)

[comment]: <> (    - [IndexLabel]&#40;restful-api/indexlabel.md&#41;)

[comment]: <> (    - [Rebuild]&#40;restful-api/rebuild.md&#41;)

[comment]: <> (- Graph Vertex & Edge)

[comment]: <> (    - [Vertex]&#40;restful-api/vertex.md&#41;)

[comment]: <> (    - [Edge]&#40;restful-api/edge.md&#41;)

[comment]: <> (- [Traverser]&#40;restful-api/traverser.md&#41;)

[comment]: <> (- [Rank]&#40;restful-api/rank.md&#41;)

[comment]: <> (- [Variable]&#40;restful-api/variable.md&#41;)

[comment]: <> (- [Graphs]&#40;restful-api/graphs.md&#41;)

[comment]: <> (- [Task]&#40;restful-api/task.md&#41;)

[comment]: <> (- [Gremlin]&#40;restful-api/gremlin.md&#41;)

[comment]: <> (- [Cypher]&#40;restful-api/cypher.md&#41;)

[comment]: <> (- [Authentication]&#40;restful-api/auth.md&#41;)

[comment]: <> (- [Metrics]&#40;restful-api/metrics.md&#41;)

[comment]: <> (- [Other]&#40;restful-api/other.md&#41;)
