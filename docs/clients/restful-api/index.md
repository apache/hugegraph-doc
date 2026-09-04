# HugeGraph RESTful API

LLMS index: [llms.txt](/llms.txt)

---

> ⚠️ **Version compatibility notes**
>
> - Current graph resource paths begin with `/graphspaces/{graphspace}/graphs/{graph}`.
> - HugeGraph 1.5.x and earlier use `/graphs/{graph}`. The request formats of APIs such as graph creation and cloning also differ from the current version.
> - The default graph space is `DEFAULT`.
> - See the [HugeGraph 1.5.x RESTful API documentation](https://github.com/apache/hugegraph-doc/tree/release-1.5.0) for older versions.


After starting Server, open `http://localhost:8080/swagger-ui/index.html` to view the OpenAPI page for the current version. [See the usage example](/docs/quickstart/hugegraph/hugegraph-server#swaggerui-example).

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

- [Graphspace API](/docs/clients/restful-api/graphspace/): Graphspace REST API: Multi-tenancy and resource isolation for creating, viewing, updating, and deleting graph spaces with prerequisites and constraints.
- [Schema API](/docs/clients/restful-api/schema/): Schema REST API: Query the complete schema definition of a graph, including property keys, vertex labels, edge labels, and index labels.
- [PropertyKey API](/docs/clients/restful-api/propertykey/): PropertyKey REST API: Define data types and cardinality constraints for all properties in the graph, serving as fundamental schema elements.
- [VertexLabel API](/docs/clients/restful-api/vertexlabel/): VertexLabel REST API: Define vertex types, ID strategies, and associated properties that determine vertex structure and constraints.
- [EdgeLabel API](/docs/clients/restful-api/edgelabel/): EdgeLabel REST API: Define edge types and relationship constraints between source and target vertices to construct graph connection rules.
- [IndexLabel API](/docs/clients/restful-api/indexlabel/): IndexLabel REST API: Create indexes on vertex and edge properties to accelerate property-based queries and filtering operations.
- [Rebuild API](/docs/clients/restful-api/rebuild/): Rebuild REST API: Rebuild graph schema indexes to ensure consistency between index data and graph data.
- [Vertex API](/docs/clients/restful-api/vertex/): Vertex REST API: Create, query, update, and delete vertex data in the graph with support for batch operations and conditional filtering.
- [Edge API](/docs/clients/restful-api/edge/): Edge REST API: Create, query, update, and delete relationship data between vertices with support for batch operations and directional queries.
- [Traverser API](/docs/clients/restful-api/traverser/): Traverser REST API: Execute complex graph algorithms and path queries including shortest path, k-neighbors, similarity computation, and advanced analytics.
- [Rank API](/docs/clients/restful-api/rank/): Rank REST API: Execute graph node ranking algorithms such as PageRank and Personalized PageRank for centrality analysis.
- [Variable API](/docs/clients/restful-api/variable/): Variable REST API: Store and manage key-value pairs as global variables for graph-level configuration and state management.
- [Graphs API](/docs/clients/restful-api/graphs/): Graphs REST API: Manage graph instance lifecycle including creating, querying, cloning, clearing, and deleting graph databases.
- [Task API](/docs/clients/restful-api/task/): Task REST API: Query and manage asynchronous task execution status for long-running operations like index rebuilding and graph traversals.
- [Gremlin API](/docs/clients/restful-api/gremlin/): Gremlin REST API: Execute Gremlin graph traversal language scripts via HTTP interface.
- [Cypher API](/docs/clients/restful-api/cypher/): Cypher REST API: Execute OpenCypher declarative graph query language via HTTP interface.
- [Authentication API](/docs/clients/restful-api/auth/): Authentication REST API: Manage users, roles, permissions, and access control to implement fine-grained graph data security.
- [Metrics API](/docs/clients/restful-api/metrics/): Metrics REST API: Retrieve runtime performance metrics, statistics, and health status data of the system.
- [Other API](/docs/clients/restful-api/other/): Other REST API: Provide auxiliary functions such as system version query and API version information.
