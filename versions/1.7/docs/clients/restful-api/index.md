# HugeGraph RESTful API

LLMS index: [llms.txt](/versions/1.7/llms.txt)

---

> ⚠️ **Version compatibility notes**
>
> - HugeGraph 1.7.0+ introduces graphspaces, and REST paths follow `/graphspaces/{graphspace}/graphs/{graph}`.
> - HugeGraph 1.5.x and earlier still rely on the legacy `/graphs/{graph}` path, and the create/clone graph APIs require `Content-Type: text/plain`; 1.7.0+ expects JSON bodies.
> - The default graphspace name is `DEFAULT`, which you can use directly if you do not need multi-tenant isolation.
> - **Note**: Before version 1.5.0, the format of ids such as group/target was similar to -69:grant. After version 1.7.0, the id and name were consistent, such as admin [HugeGraph 1.5.x RESTful API](https://github.com/apache/incubator-hugegraph-doc/tree/release-1.5.0)


Besides the documentation below, you can also open `swagger-ui` at `localhost:8080/swagger-ui/index.html` to explore the RESTful API. [Here is an example](/versions/1.7/docs/quickstart/hugegraph/hugegraph-server#swaggerui-example)

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

Section pages:

- [Graphspace API](/versions/1.7/docs/clients/restful-api/graphspace/)
- [Schema API](/versions/1.7/docs/clients/restful-api/schema/)
- [PropertyKey API](/versions/1.7/docs/clients/restful-api/propertykey/)
- [VertexLabel API](/versions/1.7/docs/clients/restful-api/vertexlabel/)
- [EdgeLabel API](/versions/1.7/docs/clients/restful-api/edgelabel/)
- [IndexLabel API](/versions/1.7/docs/clients/restful-api/indexlabel/)
- [Rebuild API](/versions/1.7/docs/clients/restful-api/rebuild/)
- [Vertex API](/versions/1.7/docs/clients/restful-api/vertex/)
- [Edge API](/versions/1.7/docs/clients/restful-api/edge/)
- [Traverser API](/versions/1.7/docs/clients/restful-api/traverser/)
- [Rank API](/versions/1.7/docs/clients/restful-api/rank/)
- [Variable API](/versions/1.7/docs/clients/restful-api/variable/)
- [Graphs API](/versions/1.7/docs/clients/restful-api/graphs/)
- [Task API](/versions/1.7/docs/clients/restful-api/task/)
- [Gremlin API](/versions/1.7/docs/clients/restful-api/gremlin/)
- [Cypher API](/versions/1.7/docs/clients/restful-api/cypher/)
- [Authentication API](/versions/1.7/docs/clients/restful-api/auth/)
- [Metrics API](/versions/1.7/docs/clients/restful-api/metrics/)
- [Other API](/versions/1.7/docs/clients/restful-api/other/)
