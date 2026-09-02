# HugeGraph RESTful API

LLMS 索引： [llms.txt](/cn/llms.txt)

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

---

本节页面：

- [Graphspace API](/cn/docs/clients/restful-api/graphspace/): Graphspace（图空间）REST 接口：多租户与资源隔离的创建、查看、更新与删除，以及使用前置条件与限制。
- [Schema API](/cn/docs/clients/restful-api/schema/): Schema（图模式）REST 接口:查询图的完整模式定义,包括属性键、顶点标签、边标签和索引标签的统一视图。
- [PropertyKey API](/cn/docs/clients/restful-api/propertykey/): PropertyKey（属性键）REST 接口:定义图中所有属性的数据类型和基数约束,是构建图模式的基础元素。
- [VertexLabel API](/cn/docs/clients/restful-api/vertexlabel/): VertexLabel（顶点标签）REST 接口:定义顶点类型、ID策略及关联的属性,决定顶点的结构和约束规则。
- [EdgeLabel API](/cn/docs/clients/restful-api/edgelabel/): EdgeLabel（边标签）REST 接口:定义边类型、源顶点和目标顶点的关系约束,构建图的连接规则。
- [IndexLabel API](/cn/docs/clients/restful-api/indexlabel/): IndexLabel（索引标签）REST 接口:为顶点和边的属性创建索引,加速基于属性的查询和过滤操作。
- [Rebuild API](/cn/docs/clients/restful-api/rebuild/): Rebuild（重建索引）REST 接口:重建图模式的索引,确保索引数据与图数据保持一致性。
- [Vertex API](/cn/docs/clients/restful-api/vertex/): Vertex（顶点）REST 接口:创建、查询、更新和删除图中的顶点数据,支持批量操作和条件过滤。
- [Edge API](/cn/docs/clients/restful-api/edge/): Edge（边）REST 接口:创建、查询、更新和删除顶点之间的关系数据,支持批量操作和方向查询。
- [Traverser API](/cn/docs/clients/restful-api/traverser/): Traverser（图遍历）REST 接口:执行复杂的图算法和路径查询,包括最短路径、K近邻、相似度计算等高级分析功能。
- [Rank API](/cn/docs/clients/restful-api/rank/): Rank（图排序）REST 接口:执行图节点排序算法,如 PageRank、个性化 PageRank 等中心性分析。
- [Variable API](/cn/docs/clients/restful-api/variable/): Variable（变量）REST 接口:存储和管理键值对形式的全局变量,支持图级别的配置和状态管理。
- [Graphs API](/cn/docs/clients/restful-api/graphs/): Graphs（图管理）REST 接口:管理图实例的生命周期,包括创建、查询、克隆、清空和删除图数据库。
- [Task API](/cn/docs/clients/restful-api/task/): Task（任务管理）REST 接口:查询和管理异步任务的执行状态,如索引重建、图遍历等长时任务。
- [Gremlin API](/cn/docs/clients/restful-api/gremlin/): Gremlin（图查询语言）REST 接口:通过 HTTP 接口执行 Gremlin 图遍历查询语言脚本。
- [Cypher API](/cn/docs/clients/restful-api/cypher/): Cypher（图查询语言）REST 接口:通过 HTTP 接口执行 OpenCypher 声明式图查询语言。
- [Authentication API](/cn/docs/clients/restful-api/auth/): Authentication（认证鉴权）REST 接口:管理用户、角色、权限和访问控制,实现细粒度的图数据安全机制。
- [Metrics API](/cn/docs/clients/restful-api/metrics/): Metrics（监控指标）REST 接口:获取系统运行时的性能指标、统计信息和健康状态数据。
- [Other API](/cn/docs/clients/restful-api/other/): Other（其他接口）REST 接口:提供系统版本查询和 API 版本信息等辅助功能。
