---
title: "HugeGraph RESTful API"
linkTitle: "RESTful API"
weight: 1
---

> ⚠️ **版本兼容性说明**
>
> - HugeGraph 1.7.0+ 引入了图空间功能，API 路径格式为：`/graphspaces/{graphspace}/graphs/{graph}`
> - HugeGraph 1.5.x 及之前版本使用旧路径：`/graphs/{graph}`, 以及创建/克隆图的 api 使用 text/plain 作为 Content-Type, 1.7.0 及之后使用 json
> - 默认图空间名称为 `DEFAULT`,可直接使用
> - 旧版本 doc 参考：[HugeGraph 1.5.x RESTful API](https://github.com/apache/hugegraph-doc/tree/release-1.5.0)

除了下方的文档，你还可以通过 `localhost:8080/swagger-ui/index.html` 访问 `swagger-ui` 以查看 `RESTful API`。[示例可以参考此处](/cn/docs/quickstart/hugegraph/hugegraph-server#swaggerui-example)

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
