---
title: "HugeGraph Python Client Quick Start"
linkTitle: "Python Client"
weight: 2
aliases:
  - /docs/quickstart/client/hugegraph-client-python/
---

`hugegraph-python-client` is the Python SDK for Apache HugeGraph. It provides schema management, graph data manipulation, Gremlin execution, real-time
traversals, and asynchronous whole-graph computing. HugeGraph-LLM and HugeGraph-ML also use this client for database operations.

The client source code is hosted in the [hugegraph-ai](https://github.com/apache/hugegraph-ai) repository under `hugegraph-python-client/`. The import package
name is `pyhugegraph`.

## Requirements

- Python >= 3.12 (Python 3.12–3.14 supported).
- HugeGraph Server 1.5.0 or later (Server 1.7+ recommends GraphSpace mode; 1.5/1.6 uses legacy routing).
- `pip` or `uv` package manager.

Runtime dependencies include `decorator`, `requests`, `urllib3`, and `rich`.

## Installation

The client provides two installation methods depending on whether you require the stable PyPI release or development features from the master branch.

> [!NOTE]
> **Version & Feature Boundary**:
> The published PyPI release (`hugegraph-python` 1.7.x) provides the baseline client supporting CamelCase methods with legacy snake_case aliases.
> The modern features demonstrated in this guide — including native `snake_case` APIs, `client.olap()` whole-graph algorithms, `client.task().wait()`,
> `client.close()`, and updated traverser signatures — align with the master development branch.
> For testing these features, install the client from source.

```bash {tab="PyPI (Stable 1.7.x)"}
pip install hugegraph-python
# Or using uv:
# uv pip install hugegraph-python
```

```bash {tab="Source (Master)"}
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/hugegraph-python-client
pip install -e .
```

```bash {tab="Workspace (uv)"}
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra python-client
source .venv/bin/activate
```

## Connect and Write Data

```python
from pyhugegraph.client import PyHugeClient

client = PyHugeClient(
    url="http://127.0.0.1:8080",
    graph="hugegraph",
    user="admin",
    pwd="admin",
    graphspace=None,
)

schema = client.schema()
schema.property_key("name").as_text().if_not_exist().create()
schema.property_key("birthDate").as_text().if_not_exist().create()
schema.vertex_label("Person").properties("name", "birthDate") \
      .use_primary_key_id().primary_keys("name").if_not_exist().create()
schema.vertex_label("Movie").properties("name") \
      .use_primary_key_id().primary_keys("name").if_not_exist().create()
schema.edge_label("ActedIn").source_label("Person").target_label("Movie") \
      .if_not_exist().create()

graph = client.graph()
person = graph.add_vertex(
    "Person", {"name": "Al Pacino", "birthDate": "1940-04-25"}
)
movie = graph.add_vertex("Movie", {"name": "The Godfather"})
edge = graph.add_edge("ActedIn", person.id, movie.id, {})

print(graph.get_vertex_by_id(person.id))
print(graph.get_edge_by_id(edge.id))

client.close()
```

### Client Parameters

`PyHugeClient(url, graph, user, pwd, graphspace=None, timeout=None, *, token=None)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | required | Base URL of HugeGraph Server. Prepends `http://` if no scheme is provided (e.g. `127.0.0.1:8080`). |
| `graph` | `str` | required | Target graph name. Second positional parameter. |
| `user` | `str` | required | Username sent via HTTP Basic Auth. |
| `pwd` | `str` | required | Password sent via HTTP Basic Auth. |
| `graphspace` | `str` or `None` | `None` | GraphSpace name. When `None`, resolved automatically via version probe. |
| `timeout` | `float`, `tuple[float, float]` or `None` | `None` | `(connect, read)` timeouts in seconds, or a single float for both. Defaults to `(0.5, 15.0)`. |
| `token` | `str` or `None` | `None` | Explicit Bearer token; overrides Basic Auth when provided. |
{.wide}

Idempotent requests retry on 500, 502, and 504 responses up to three times with a 0.1 backoff factor. Task waiting automatically manages its polling budget
without extra HTTP retries.

### Server Version and GraphSpace

The client resolves GraphSpace routing at initialization:
- When an explicit `graphspace` string is passed, GraphSpace routing is activated immediately.
- When `graphspace=None`, the client checks `GET {url}/versions` to determine the server core version.
- HugeGraph Server 1.7+ defaults to GraphSpace `DEFAULT`.
- HugeGraph Server 1.5 / 1.6 uses legacy non-GraphSpace routing.
- Servers prior to 1.5.0 are not supported and raise `RuntimeError`.
- If the version probe fails and no GraphSpace was specified, client initialization raises an error rather than assuming an invalid route layout.

The routing mode determines request path prefixes: `/graphspaces/<graphspace>/graphs/<graph>/...` when GraphSpace is enabled, or `/graphs/<graph>/...` when
disabled.

### Client Accessors

`PyHugeClient` maintains a shared HTTP session across all accessors. Accessors cache their managers lazily:

| Accessor | Manager | Purpose |
|----------|---------|---------|
| `client.schema()` | `SchemaManager` | Property keys, vertex labels, edge labels, index labels |
| `client.graph()` | `GraphManager` | Vertex and edge CRUD, batch ingestion, paging |
| `client.gremlin()` | `GremlinManager` | Gremlin script execution |
| `client.traverser()` | `TraverserManager` | Real-time graph traversals and paths (OLTP) |
| `client.rank()` | `RankManager` | Real-time personalized recommendation ranking (OLTP) |
| `client.olap()` | `OlapManager` | Asynchronous whole-graph computing algorithms (OLAP) |
| `client.task()` | `TaskManager` | Asynchronous task status, polling, cancellation, and deletion |
| `client.graphs()` | `GraphsManager` | Graph metadata, configuration, graph list, data clearing |
| `client.graphspaces()` | `GraphspaceManager` | Multi-graphspace management |
| `client.schema_templates()` | `SchemaTemplateManager` | Reusable schema templates |
| `client.auth()` | `AuthManager` | Users, groups, targets, belongs, and access privileges |
| `client.variable()` | `VariableManager` | Graph-level persistent key-value variables |
| `client.metrics()` | `MetricsManager` | Server monitoring metrics |
| `client.version()` | `VersionManager` | Server component versions |
| `client.rest()` | `RestClient` | Direct REST API calls and extended operations |
{.wide}

## Common Operations

### Build the Schema

Schema builders are fluent. Call `create()` to apply, or use `append()`, `eliminate()`, and `remove()` to update existing definitions:

```python
schema = client.schema()

# Property keys: as_text / as_int / as_long / as_float / as_double / as_bool / as_date
# Cardinality: value_single / value_list / value_set
schema.property_key("age").as_int().value_single().if_not_exist().create()

# Vertex labels: use_automatic_id / use_customize_string_id / use_primary_key_id
schema.vertex_label("person").properties("name", "age", "city") \
      .primary_keys("name").nullable_keys("city").if_not_exist().create()

# Edge labels: link() specifies source and target vertex labels
schema.edge_label("knows").link("person", "person").multi_times() \
      .properties("date", "city").sort_keys("date").nullable_keys("city") \
      .if_not_exist().create()

# Index labels: on_v / on_e, secondary / range / search / shard / unique
schema.index_label("personByCity").on_v("person").by("city") \
      .secondary().if_not_exist().create()
```

### Query the Schema

```python
schema = client.schema()
print(schema.get_schema())            # Returns whole schema definition dictionary
print(schema.get_property_keys())
print(schema.get_vertex_labels())
print(schema.get_edge_labels())
print(schema.get_index_labels())

# Query single definitions by name
print(schema.get_property_key("name"))
print(schema.get_vertex_label("person"))
print(schema.get_edge_label("knows"))
print(schema.get_index_label("personByCity"))

# Edge relations formatted as "Person--ActedIn-->Movie"
print(schema.get_relations())
```

### Read, Update, and Delete Graph Data

The graph API accepts property dictionaries:

```python
graph = client.graph()
graph.append_vertex(person.id, {"birthDate": "1940-04-25"})    # Append properties
graph.eliminate_vertex(person.id, {"birthDate": "1940-04-25"}) # Drop properties
graph.append_edge(edge.id, {"city": "Beijing"})
graph.eliminate_edge(edge.id, {"city": "Beijing"})
graph.remove_edge_by_id(edge.id)
graph.remove_vertex_by_id(person.id)
```

`add_vertex` returns a `VertexData` instance containing `id`, `label`, `type`, and `properties`. `add_edge` returns an `EdgeData` instance containing `id`,
`label`, `type`, `outV`, `outVLabel`, `inV`, `inVLabel`, and `properties`.

Vertex IDs passed to the client may be strings, integers, or `uuid.UUID` objects. Booleans are rejected, and integer values must fall within the 64-bit signed
range.

### Batch Writes

`add_vertices` accepts `(label, properties)` tuples, and `add_edges` accepts `(label, out_id, in_id, out_label, in_label, properties)` tuples:

```python
graph = client.graph()
vertices = graph.add_vertices([
    ("person", {"name": "Alice", "age": 20}),
    ("person", {"name": "Bob", "age": 23}),
])
edges = graph.add_edges([
    ("knows", vertices[0].id, vertices[1].id, "person", "person", {"date": "2012-01-10"}),
])
```

### Paging and Conditional Queries

```python
graph = client.graph()

# Paging with next_page token
vertices, next_page = graph.get_vertex_by_page("person", limit=10)
vertices, next_page = graph.get_vertex_by_page("person", limit=10, page=next_page)

# Server-side property predicates
older = graph.get_vertex_by_condition("person", properties={"age": "P.gt(29)"})

# Edge paging. When vertex_id is provided, direction is required
edges, next_page = graph.get_edge_by_page(label="knows", limit=10)
edges, next_page = graph.get_edge_by_page(vertex_id=person.id, direction="OUT", limit=10)

# Batch lookup by ID list
graph.get_vertices_by_id([v1.id, v2.id])
graph.get_edges_by_id([e1.id, e2.id])
```

### Execute Gremlin

```python
gremlin = client.gremlin()
result = gremlin.exec("g.V().limit(5)")
print(result)
```

`exec()` automatically binds the `graph` and `g` aliases according to the target graph name and resolved GraphSpace.

### Traverse the Graph (OLTP)

`client.traverser()` wraps the server's real-time traverser endpoints for neighborhood, path, and similarity queries:

```python
traverser = client.traverser()

traverser.k_out(marko_id, 2)
traverser.k_neighbor(marko_id, 2)
traverser.same_neighbors(marko_id, josh_id)
traverser.jaccard_similarity(marko_id, josh_id)
traverser.shortest_path(marko_id, ripple_id, 3)
traverser.all_shortest_paths(marko_id, ripple_id, 3)
traverser.weighted_shortest_path(marko_id, ripple_id, "weight", 3)
traverser.single_source_shortest_path(marko_id, 2)
traverser.multi_node_shortest_path([marko_id, josh_id], max_depth=2)
traverser.paths(marko_id, josh_id, 2)
traverser.crosspoints(marko_id, josh_id, 2)
traverser.rings(marko_id, 3)
traverser.rays(marko_id, 2)
traverser.vertices(marko_id)
traverser.edges(edge_id)
```

The POST-based variants accept complex request bodies: `advanced_paths`, `customized_paths`, `template_paths`, `customized_crosspoints`, and
`fusiform_similarity`.

## OLAP Whole-Graph Computing

For heavy full-graph algorithms (such as PageRank, Louvain, or Centrality), use `client.olap()`. These jobs run asynchronously on the server and are tracked
through task IDs:

```python
# 1. Submit an asynchronous computation task
receipt = client.olap().count_vertex()
task_id = receipt["task_id"]

# 2. Wait for completion and retrieve results
task = client.task().wait(task_id, timeout=300, poll_interval=1)
result = client.task().result(task)
print(result)

# Or combine submit, wait, and decode in one step:
result = client.olap().run("count_vertex", timeout=60)
```

### Supported OLAP Algorithms

The server provides 17 unique whole-graph algorithm endpoints:

| Category | Algorithm Names |
|----------|-----------------|
| Statistics | `count_edge`, `count_vertex`, `subgraph_stat`, `triangle_count`, `rings` |
| Centrality | `betweenness_centrality`, `closeness_centrality`, `degree_centrality`, `eigenvector_centrality`, `stress_centrality` |
| Community & Clustering | `cluster_coefficient`, `k_core`, `louvain`, `lpa`, `weak_connected_component` |
| Ranking & Similarity | `page_rank`, `fusiform_similarity` |
{.wide}

> [!TIP]
> Algorithms like `page_rank` write calculated rank properties back to the graph. For graphs requiring strict schema definitions, declare a nullable `DOUBLE`
> property named `r_rank` on participating vertex labels prior to execution.

## Task Lifecycle Management

The `TaskManager` provides control over asynchronous jobs:

```python
task = client.task()

# List recent tasks
task.list_tasks(status="success", limit=10)

# Poll and wait for a task to complete
record = task.wait(task_id, timeout=300, poll_interval=1)

# Decode task results (parses JSON response once)
result = task.result(record)

# Cancel or delete tasks
task.cancel_task(task_id)
task.delete_task(task_id, force=False)
```

- `wait(id, timeout=300, poll_interval=1)` polls status without fetching the full result payload on every tick.
- `TaskTimeoutError` indicates client-side polling timed out; the background job on the server continues running.
- To terminate a running server task, invoke `cancel_task(id)` explicitly.

## Graph Variables, Metrics, and Metadata

```python
# Graph variables
variable = client.variable()
variable.set("owner", "mary")
print(variable.get("owner"))
print(variable.all())
variable.remove("owner")

# Server metrics
metrics = client.metrics()
metrics.get_all_basic_metrics()
metrics.get_system_metrics()
metrics.get_backend_metrics()

# Graph management and version
graphs = client.graphs()
print(graphs.list())
print(client.version().version())
```

## Authentication and Authorization

`PyHugeClient` supports both HTTP Basic Auth and Bearer Token authentication:

```python
# Switch session to Bearer Token authentication
client.use_token("your-jwt-token")

# Revert back to HTTP Basic Auth credentials
client.use_token(None)
```

`AuthManager` manages users, groups, targets, belongs, and access privileges:

```python
auth = client.auth()

user = auth.create_user("test_user", "password")
auth.modify_user(user["id"], user_email="hugegraph@apache.org")
auth.get_user(user["id"])
auth.list_users(limit=10)

group = auth.create_group("test_group", "read only")
auth.modify_group(group["id"], group_description="updated")
auth.list_groups()

target = auth.create_target("target1", "hugegraph", "127.0.0.1:8080", [])
auth.update_target(target["id"], "target1", "hugegraph", "127.0.0.1:8080", [])
auth.list_targets()

belong = auth.create_belong(user["id"], group["id"])
auth.update_belong(belong["id"], "description")
auth.list_belongs()

access = auth.grant_accesses(group["id"], target["id"], "READ")
auth.modify_accesses(access["id"], "description")
auth.list_accesses()

# Clean up in reverse dependency order
auth.revoke_accesses(access["id"])
auth.delete_belong(belong["id"])
auth.delete_target(target["id"])
auth.delete_group(group["id"])
auth.delete_user(user["id"])
```

## Method Naming and Migration

- **Preferred style**: New code should use `snake_case` methods (`add_vertex`, `property_key`, etc.).
- **Backward compatibility**: Existing public CamelCase methods (`addVertex`, `propertyKey`, etc.) remain supported as direct aliases.
- **Client lifecycle**: Use `client.close()` to release connection pool resources rather than closing individual managers.
- **Return contracts**:
  - Legacy convenience helpers `get_all_graphs()`, `get_version()`, and `get_graph_info()` retain JSON strings for backwards compatibility.
  - Modern accessors `client.graphs().list()`, `client.version().version()`, and `client.graphs().get(graph_name)` return parsed Python dictionaries.
  - Weighted and single-source shortest path methods no longer accept `max_depth` (unsupported by the server endpoint); use `capacity`, `max_degree`, and
    `skip_degree` controls instead.

## Direct REST API Reference

For raw endpoint interactions, batch operations, or capabilities not wrapped by high-level managers, `client.rest()` exposes the full REST surface:

```python
rest = client.rest()
print(rest.vertex.list(label="person", offset=0, limit=20))
print(rest.task.list(status="success", page="", limit=20))
```

The table below lists all 194 supported operations aligned with the server contract:

<!-- BEGIN REST CONTRACT -->
| Python REST entry | Method | Path | Query parameters |
| --- | --- | --- | --- |
| `rest.access.create()` | POST | `/graphspaces/{graphspace}/auth/accesses` | — |
| `rest.access.delete()` | DELETE | `/graphspaces/{graphspace}/auth/accesses/{id}` | — |
| `rest.access.get()` | GET | `/graphspaces/{graphspace}/auth/accesses/{id}` | — |
| `rest.access.list()` | GET | `/graphspaces/{graphspace}/auth/accesses` | group, target, limit |
| `rest.access.update()` | PUT | `/graphspaces/{graphspace}/auth/accesses/{id}` | — |
| `rest.adamic_adar.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/adamicadar` | vertex, other, direction, label, max_degree, limit |
| `rest.algorithm.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/jobs/algorithm/{name}` | — |
| `rest.all_shortest_paths.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/allshortestpaths` | source, target, direction, label, max_depth, max_degree, skip_degree, with_vertex, with_edge, capacity |
| `rest.arthas.start_arthas()` | PUT | `/arthas` | — |
| `rest.belong.create()` | POST | `/graphspaces/{graphspace}/auth/belongs` | — |
| `rest.belong.delete()` | DELETE | `/graphspaces/{graphspace}/auth/belongs/{id}` | — |
| `rest.belong.get()` | GET | `/graphspaces/{graphspace}/auth/belongs/{id}` | — |
| `rest.belong.list()` | GET | `/graphspaces/{graphspace}/auth/belongs` | user, group, limit |
| `rest.belong.update()` | PUT | `/graphspaces/{graphspace}/auth/belongs/{id}` | — |
| `rest.computer.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/jobs/computer/{name}` | — |
| `rest.count.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/count` | — |
| `rest.crosspoints.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/crosspoints` | source, target, direction, label, max_depth, max_degree, capacity, limit |
| `rest.customized_crosspoints.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/customizedcrosspoints` | — |
| `rest.customized_paths.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/customizedpaths` | — |
| `rest.cypher.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/cypher` | — |
| `rest.cypher.query()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/cypher` | cypher |
| `rest.edge.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges` | — |
| `rest.edge.create_batch()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/batch` | check_vertex |
| `rest.edge.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/{id}` | label |
| `rest.edge.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/{id}` | — |
| `rest.edge.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges` | vertex_id, direction, label, properties, keep_start_p, offset, page, limit |
| `rest.edge.update_batch()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/batch` | — |
| `rest.edge.update_by_id()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/{id}` | action |
| `rest.edge_existence.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/edgeexist` | source, target, label, sort_values, limit |
| `rest.edge_label.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels` | — |
| `rest.edge_label.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels/{name}` | — |
| `rest.edge_label.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels/{name}` | — |
| `rest.edge_label.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels` | names |
| `rest.edge_label.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels/{name}` | action |
| `rest.edges.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/edges` | ids |
| `rest.edges.scan()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/edges/scan` | start, end, page, page_limit |
| `rest.edges.shards()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/edges/shards` | split_size |
| `rest.exception_trace.get()` | GET | `/exception/trace` | — |
| `rest.exception_trace.trace()` | PUT | `/exception/trace` | — |
| `rest.fusiform_similarity.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/fusiformsimilarity` | — |
| `rest.graph_space.check_default_role()` | GET | `/graphspaces/{graphspace}/role` | user, role, graph |
| `rest.graph_space.create()` | POST | `/graphspaces` | — |
| `rest.graph_space.delete()` | DELETE | `/graphspaces/{name}` | — |
| `rest.graph_space.delete_default_role()` | DELETE | `/graphspaces/{graphspace}/role` | user, role, graph |
| `rest.graph_space.get()` | GET | `/graphspaces/{graphspace}` | — |
| `rest.graph_space.list()` | GET | `/graphspaces` | — |
| `rest.graph_space.list_profile()` | GET | `/graphspaces/profile` | prefix |
| `rest.graph_space.manage()` | PUT | `/graphspaces/{name}` | — |
| `rest.graph_space.set_default_role()` | POST | `/graphspaces/{graphspace}/role` | — |
| `rest.graph_space_group.create()` | POST | `/graphspaces/{graphspace}/auth/groups` | — |
| `rest.graph_space_group.delete()` | DELETE | `/graphspaces/{graphspace}/auth/groups/{id}` | — |
| `rest.graph_space_group.get()` | GET | `/graphspaces/{graphspace}/auth/groups/{id}` | — |
| `rest.graph_space_group.list()` | GET | `/graphspaces/{graphspace}/auth/groups` | limit |
| `rest.graph_space_group.update()` | PUT | `/graphspaces/{graphspace}/auth/groups/{id}` | — |
| `rest.graphs.clear()` | DELETE | `/graphspaces/{graphspace}/graphs/{name}/clear` | confirm_message |
| `rest.graphs.clone_schema()` | POST | `/graphspaces/{graphspace}/graphs/{name}/schema-clone` | source |
| `rest.graphs.compact()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/compact` | — |
| `rest.graphs.create()` | POST | `/graphspaces/{graphspace}/graphs/{name}` | clone_graph_name |
| `rest.graphs.create_by_text()` | POST | `/graphspaces/{graphspace}/graphs/{name}` | clone_graph_name |
| `rest.graphs.create_snapshot()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/snapshot_create` | — |
| `rest.graphs.drop()` | DELETE | `/graphspaces/{graphspace}/graphs/{name}` | confirm_message |
| `rest.graphs.get()` | GET | `/graphspaces/{graphspace}/graphs/{name}` | — |
| `rest.graphs.get_conf()` | GET | `/graphspaces/{graphspace}/graphs/{name}/conf` | — |
| `rest.graphs.get_default()` | GET | `/graphspaces/{graphspace}/graphs/default` | — |
| `rest.graphs.graph_read_mode_get()` | GET | `/graphspaces/{graphspace}/graphs/{name}/graph_read_mode` | — |
| `rest.graphs.graph_read_mode_set()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/graph_read_mode` | — |
| `rest.graphs.list()` | GET | `/graphspaces/{graphspace}/graphs` | — |
| `rest.graphs.list_profile()` | GET | `/graphspaces/{graphspace}/graphs/profile` | prefix |
| `rest.graphs.loading_mode_get()` | GET | `/graphspaces/{graphspace}/graphs/{name}/mode/owners` | — |
| `rest.graphs.loading_mode_set()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/mode/owners` | — |
| `rest.graphs.manage()` | PUT | `/graphspaces/{graphspace}/graphs/{name}` | — |
| `rest.graphs.mode_get()` | GET | `/graphspaces/{graphspace}/graphs/{name}/mode` | — |
| `rest.graphs.mode_set()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/mode` | — |
| `rest.graphs.reload()` | PUT | `/graphspaces/{graphspace}/graphs/manage` | — |
| `rest.graphs.resume_snapshot()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/snapshot_resume` | — |
| `rest.graphs.set_default()` | POST | `/graphspaces/{graphspace}/graphs/{name}/default` | — |
| `rest.graphs.unset_default()` | DELETE | `/graphspaces/{graphspace}/graphs/{name}/default` | — |
| `rest.gremlin.get()` | GET | `/gremlin` | gremlin, language; additional query map |
| `rest.gremlin.post()` | POST | `/gremlin` | — |
| `rest.gremlin_job.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/jobs/gremlin` | — |
| `rest.group.create()` | POST | `/auth/groups` | — |
| `rest.group.delete()` | DELETE | `/auth/groups/{id}` | — |
| `rest.group.get()` | GET | `/auth/groups/{id}` | — |
| `rest.group.list()` | GET | `/auth/groups` | limit |
| `rest.group.update()` | PUT | `/auth/groups/{id}` | — |
| `rest.index_label.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels` | — |
| `rest.index_label.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels/{name}` | — |
| `rest.index_label.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels/{name}` | — |
| `rest.index_label.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels` | names |
| `rest.index_label.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels/{name}` | action |
| `rest.jaccard_similarity.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/jaccardsimilarity` | vertex, other, direction, label, max_degree |
| `rest.jaccard_similarity.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/jaccardsimilarity` | — |
| `rest.kneighbor.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/kneighbor` | source, direction, label, max_depth, count_only, max_degree, limit |
| `rest.kneighbor.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/kneighbor` | — |
| `rest.kout.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/kout` | source, direction, label, max_depth, nearest, count_only, max_degree, capacity, limit |
| `rest.kout.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/kout` | — |
| `rest.login.login()` | POST | `/auth/login` | — |
| `rest.login.logout()` | DELETE | `/auth/logout` | — |
| `rest.login.verify_token()` | GET | `/auth/verify` | — |
| `rest.manager.check_default_role()` | GET | `/graphspaces/{graphspace}/auth/managers/default` | role, graph |
| `rest.manager.check_role()` | GET | `/graphspaces/{graphspace}/auth/managers/check` | type |
| `rest.manager.create_manager()` | POST | `/graphspaces/{graphspace}/auth/managers` | — |
| `rest.manager.delete()` | DELETE | `/graphspaces/{graphspace}/auth/managers` | user, type |
| `rest.manager.get_roles_in_gs()` | GET | `/graphspaces/{graphspace}/auth/managers/role` | user |
| `rest.manager.list()` | GET | `/graphspaces/{graphspace}/auth/managers` | type |
| `rest.metrics.all()` | GET | `/metrics` | type |
| `rest.metrics.backend()` | GET | `/metrics/backend` | — |
| `rest.metrics.counters()` | GET | `/metrics/counters` | — |
| `rest.metrics.gauges()` | GET | `/metrics/gauges` | — |
| `rest.metrics.histograms()` | GET | `/metrics/histograms` | — |
| `rest.metrics.meters()` | GET | `/metrics/meters` | — |
| `rest.metrics.statistics()` | GET | `/metrics/statistics` | type |
| `rest.metrics.system()` | GET | `/metrics/system` | — |
| `rest.metrics.timers()` | GET | `/metrics/timers` | — |
| `rest.multi_node_shortest_path.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/multinodeshortestpath` | — |
| `rest.neighbor_rank.neighbor_rank()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/neighborrank` | — |
| `rest.paths.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/paths` | source, target, direction, label, max_depth, max_degree, capacity, limit |
| `rest.paths.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/paths` | — |
| `rest.personal_rank.personal_rank()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/personalrank` | — |
| `rest.profile.get_profile()` | GET | `/` | — |
| `rest.profile.show_all_apis()` | GET | `/apis` | — |
| `rest.project.create()` | POST | `/graphspaces/{graphspace}/auth/projects` | — |
| `rest.project.delete()` | DELETE | `/graphspaces/{graphspace}/auth/projects/{id}` | — |
| `rest.project.get()` | GET | `/graphspaces/{graphspace}/auth/projects/{id}` | — |
| `rest.project.list()` | GET | `/graphspaces/{graphspace}/auth/projects` | limit |
| `rest.project.update()` | PUT | `/graphspaces/{graphspace}/auth/projects/{id}` | action |
| `rest.property_key.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys` | — |
| `rest.property_key.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys/{name}` | — |
| `rest.property_key.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys/{name}` | — |
| `rest.property_key.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys` | names |
| `rest.property_key.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys/{name}` | action |
| `rest.raft.add_peer()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/raft/add_peer` | group, endpoint |
| `rest.raft.get_leader()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/raft/get_leader` | group |
| `rest.raft.list_peers()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/raft/list_peers` | group |
| `rest.raft.remove_peer()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/raft/remove_peer` | group, endpoint |
| `rest.raft.set_leader()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/raft/set_leader` | group, endpoint |
| `rest.raft.transfer_leader()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/raft/transfer_leader` | group, endpoint |
| `rest.rays.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/rays` | source, direction, label, max_depth, max_degree, capacity, limit, with_vertex, with_edge |
| `rest.rebuild.edge_label_rebuild()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/jobs/rebuild/edgelabels/{name}` | — |
| `rest.rebuild.index_label_rebuild()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/jobs/rebuild/indexlabels/{name}` | — |
| `rest.rebuild.vertex_label_rebuild()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/jobs/rebuild/vertexlabels/{name}` | — |
| `rest.resource_allocation.create()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/resourceallocation` | vertex, other, direction, label, max_degree, limit |
| `rest.rings.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/rings` | source, direction, label, max_depth, source_in_ring, max_degree, capacity, limit, with_vertex, with_edge |
| `rest.same_neighbors.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/sameneighbors` | vertex, other, direction, label, max_degree, limit |
| `rest.same_neighbors.same_neighbors()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/sameneighbors` | — |
| `rest.same_neighbors_batch.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/sameneighborsbatch` | — |
| `rest.schema.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema` | — |
| `rest.schema_template.create()` | POST | `/graphspaces/{graphspace}/schematemplates` | — |
| `rest.schema_template.delete()` | DELETE | `/graphspaces/{graphspace}/schematemplates/{name}` | — |
| `rest.schema_template.get()` | GET | `/graphspaces/{graphspace}/schematemplates/{name}` | — |
| `rest.schema_template.list()` | GET | `/graphspaces/{graphspace}/schematemplates` | — |
| `rest.schema_template.update()` | PUT | `/graphspaces/{graphspace}/schematemplates/{name}` | — |
| `rest.shortest_path.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/shortestpath` | source, target, direction, label, max_depth, max_degree, skip_degree, with_vertex, with_edge, capacity |
| `rest.single_source_shortest_path.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/singlesourceshortestpath` | source, direction, label, weight, max_degree, skip_degree, with_vertex, with_edge, capacity, limit |
| `rest.target.create()` | POST | `/graphspaces/{graphspace}/auth/targets` | — |
| `rest.target.delete()` | DELETE | `/graphspaces/{graphspace}/auth/targets/{id}` | — |
| `rest.target.get()` | GET | `/graphspaces/{graphspace}/auth/targets/{id}` | — |
| `rest.target.list()` | GET | `/graphspaces/{graphspace}/auth/targets` | limit |
| `rest.target.update()` | PUT | `/graphspaces/{graphspace}/auth/targets/{id}` | — |
| `rest.task.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/tasks/{id}` | force |
| `rest.task.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/tasks/{id}` | with_result |
| `rest.task.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/tasks` | status, ids, limit, page |
| `rest.task.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/tasks/{id}` | action |
| `rest.template_paths.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/templatepaths` | — |
| `rest.user.create()` | POST | `/graphspaces/{graphspace}/auth/users` | — |
| `rest.user.delete()` | DELETE | `/graphspaces/{graphspace}/auth/users/{id}` | — |
| `rest.user.get()` | GET | `/graphspaces/{graphspace}/auth/users/{id}` | — |
| `rest.user.list()` | GET | `/graphspaces/{graphspace}/auth/users` | name, limit |
| `rest.user.role()` | GET | `/graphspaces/{graphspace}/auth/users/{id}/role` | — |
| `rest.user.update()` | PUT | `/graphspaces/{graphspace}/auth/users/{id}` | — |
| `rest.variables.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/variables/{key}` | — |
| `rest.variables.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/variables/{key}` | — |
| `rest.variables.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/variables` | — |
| `rest.variables.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/variables/{key}` | — |
| `rest.version.list()` | GET | `/versions` | — |
| `rest.vertex.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices` | — |
| `rest.vertex.create_batch()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/batch` | — |
| `rest.vertex.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/{id}` | label |
| `rest.vertex.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/{id}` | — |
| `rest.vertex.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices` | label, properties, keep_start_p, offset, page, limit |
| `rest.vertex.update_batch()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/batch` | — |
| `rest.vertex.update_by_id()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/{id}` | action |
| `rest.vertex_label.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels` | — |
| `rest.vertex_label.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels/{name}` | — |
| `rest.vertex_label.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels/{name}` | — |
| `rest.vertex_label.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels` | names |
| `rest.vertex_label.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels/{name}` | action |
| `rest.vertices.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/vertices` | ids |
| `rest.vertices.scan()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/vertices/scan` | start, end, page, page_limit |
| `rest.vertices.shards()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/vertices/shards` | split_size |
| `rest.weighted_shortest_path.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/weightedshortestpath` | source, target, direction, label, weight, max_degree, skip_degree, with_vertex, with_edge, capacity |
| `rest.white_ip_list.list()` | GET | `/whiteiplist` | — |
| `rest.white_ip_list.update_status()` | PUT | `/whiteiplist` | status |
| `rest.white_ip_list.update_white_ips()` | POST | `/whiteiplist` | — |
{.wide .expand}

<!-- END REST CONTRACT -->

## Error Handling

Exceptions reside in `pyhugegraph.utils.exceptions`:

| Exception | Raised when |
|-----------|-------------|
| `NotAuthorizedError` | Server responds with HTTP 401 |
| `NotFoundError` | Server responds with HTTP 404 |
| `ServerError` | Non-2xx server response (attaches server error payload) |
| `ResponseParseError` | Response body cannot be decoded to the expected structure |
| `ServiceUnavailableError` | Server is temporarily unavailable |
| `InvalidParameterError`, `CreateError`, `RemoveError`, `UpdateError`, `DataFormatError` | Raised on client-side validation failures |
{.wide}

Sensitive fields (passwords, tokens, secrets) are masked automatically in logs.

```python
from pyhugegraph.utils.exceptions import NotFoundError

try:
    graph.get_vertex_by_id("missing-id")
except NotFoundError:
    print("Vertex not found")
```

## Development and Verification

Run code quality and test suites from the root of the HugeGraph-AI repository:

1. Format and lint checks:

   ```bash
   uv run --extra dev ruff format --check .
   uv run --extra dev ruff check .
   uv run --extra dev ty check hugegraph-python-client/src/pyhugegraph
   ```

2. Run unit and contract tests:

   ```bash
   uv run pytest hugegraph-python-client/src/tests -m "unit or contract"
   ```

3. Run integration tests against a HugeGraph Server:

   ```bash
   HUGEGRAPH_URL=http://127.0.0.1:8080 \
   HUGEGRAPH_GRAPH=hugegraph \
   HUGEGRAPH_USER=admin \
   HUGEGRAPH_PASSWORD=admin \
   uv run pytest hugegraph-python-client/src/tests -m "integration and hugegraph"
   ```
{.steps}

Upstream CI validates against `hugegraph/hugegraph:latest` and regression tests against `1.7.0`. Source code and test suites reside in
`hugegraph-python-client/src/pyhugegraph/` and `hugegraph-python-client/src/tests/`.
