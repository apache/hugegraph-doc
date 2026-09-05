---
title: "HugeGraph Python Client Quick Start"
linkTitle: "Python Client"
weight: 2
---

`hugegraph-python-client` is the Python SDK for HugeGraph. It manages schemas, reads and writes graph data, and executes Gremlin queries. HugeGraph-LLM and HugeGraph-ML also use this client.

The module lives in the [hugegraph-ai](https://github.com/apache/hugegraph-ai) repository under `hugegraph-python-client/`. The import name is `pyhugegraph`.

## Requirements

- Python 3.9 or later for the client itself. The HugeGraph-AI workspace requires Python 3.10 or later, and CI runs the client tests on 3.10 and 3.11.
- HugeGraph Server 1.5.0 or later. The client refuses to connect to older servers; use client v1.3.x for those.
- `uv` (recommended) or `pip`

Runtime dependencies are `decorator`, `requests`, `setuptools`, `urllib3` and `rich`.

## Installation

The released package is published on PyPI as `hugegraph-python`:

```bash
uv pip install hugegraph-python
# Alternatively: pip install hugegraph-python
```

> The PyPI release lags behind the repository. In the source tree the distribution is declared as `hugegraph-python-client` and versioned with the rest of HugeGraph-AI, so install from source if you need the newest code.

To use the latest repository code, sync the workspace from the root of the HugeGraph-AI repository. `hugegraph-python-client` is a workspace member exposed through the `python-client` extra, so plain `uv sync` does not pull it in:

```bash
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
schema.propertyKey("name").asText().ifNotExist().create()
schema.propertyKey("birthDate").asText().ifNotExist().create()
schema.vertexLabel("Person").properties("name", "birthDate") \
      .usePrimaryKeyId().primaryKeys("name").ifNotExist().create()
schema.vertexLabel("Movie").properties("name") \
      .usePrimaryKeyId().primaryKeys("name").ifNotExist().create()
schema.edgeLabel("ActedIn").sourceLabel("Person").targetLabel("Movie") \
      .ifNotExist().create()

graph = client.graph()
person = graph.addVertex(
    "Person", {"name": "Al Pacino", "birthDate": "1940-04-25"}
)
movie = graph.addVertex("Movie", {"name": "The Godfather"})
edge = graph.addEdge("ActedIn", person.id, movie.id, {})

print(graph.getVertexById(person.id))
print(graph.getEdgeById(edge.id))
graph.close()
```

### Client Parameters

`PyHugeClient(url, graph, user, pwd, graphspace=None, timeout=None)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | required | Base URL of HugeGraph Server. If the value has no scheme, `http://` is prepended, so `127.0.0.1:8080` also works. |
| `graph` | `str` | required | Graph name. This is the second positional parameter. |
| `user` | `str` | required | Username, sent as HTTP basic auth. |
| `pwd` | `str` | required | Password, sent as HTTP basic auth. |
| `graphspace` | `str` or `None` | `None` | GraphSpace name. See below for how `None` is resolved. |
| `timeout` | `tuple[float, float]` or `None` | `None` | `(connect, read)` timeouts in seconds. `None` becomes `(0.5, 15.0)`. |

Every HTTP session retries three times with a 0.1 backoff factor on 500, 502 and 504 responses.

### Server Version and GraphSpace

The client resolves GraphSpace at construction time:

- A non-empty `graphspace` string turns GraphSpace mode on directly.
- Otherwise the client sends `GET {url}/versions` and reads `versions.core`.
- A server older than 1.5.0 raises `RuntimeError` asking you to upgrade the server or use client v1.3.x.
- A server newer than 1.5.0 gets `graphspace` set to `DEFAULT` and GraphSpace mode turned on, with a warning in the log. A server at exactly 1.5.0 keeps GraphSpace mode off.
- If the probe fails for network reasons, GraphSpace mode stays off.

The mode decides the request prefix: `/graphspaces/<graphspace>/graphs/<graph>/...` when GraphSpace is on, `/graphs/<graph>/...` when it is off.

### Managers on the Client

Each accessor builds its manager lazily and gives it a dedicated HTTP session.

| Accessor | Manager | Covers |
|----------|---------|--------|
| `client.schema()` | `SchemaManager` | Property keys, vertex labels, edge labels, index labels |
| `client.graph()` | `GraphManager` | Vertex and edge CRUD, batch writes, paging |
| `client.gremlin()` | `GremlinManager` | Gremlin execution |
| `client.graphs()` | `GraphsManager` | Graph list, graph info, config, clear data |
| `client.traverser()` | `TraverserManager` | Traversal and path algorithms |
| `client.variable()` | `VariableManager` | Graph variables |
| `client.task()` | `TaskManager` | Async task list, query, cancel, delete |
| `client.auth()` | `AuthManager` | Users, groups, targets, belongs, accesses |
| `client.metrics()` | `MetricsManager` | Server metrics |
| `client.version()` | `VersionManager` | Server version |

`RankManager`, `RebuildManager` and `ServicesManager` also ship in `pyhugegraph.api`, but `PyHugeClient` does not expose accessors for them yet; construct them directly with a session if you need them.

## Common Operations

### Build the Schema

The schema builders are fluent. Call `create()` last, or `append()`, `eliminate()` and `remove()` to change an existing definition.

```python
schema = client.schema()

# Property keys: asText/asInt/asLong/asFloat/asDouble/asBool/asByte/asBlob/asDate/asObject
# cardinality: valueSingle/valueList/valueSet
# aggregation: calcMax/calcMin/calcSum/calcOld
schema.propertyKey("age").asInt().valueSingle().ifNotExist().create()

# Vertex labels: useAutomaticId/useCustomizeStringId/useCustomizeNumberId/usePrimaryKeyId
schema.vertexLabel("person").properties("name", "age", "city") \
      .primaryKeys("name").nullableKeys("city").ifNotExist().create()

# Edge labels: link() is shorthand for sourceLabel() plus targetLabel()
schema.edgeLabel("knows").link("person", "person").multiTimes() \
      .properties("date", "city").sortKeys("date").nullableKeys("city") \
      .ifNotExist().create()

# Index labels: onV/onE, then secondary/range/search/shard/unique
schema.indexLabel("personByCity").onV("person").by("city") \
      .secondary().ifNotExist().create()
```

### Query the Schema

```python
schema = client.schema()
print(schema.getSchema())            # whole schema, format defaults to "json"
print(schema.getPropertyKeys())
print(schema.getVertexLabels())
print(schema.getEdgeLabels())
print(schema.getIndexLabels())

# Single definitions
print(schema.getPropertyKey("name"))
print(schema.getVertexLabel("person"))
print(schema.getEdgeLabel("knows"))
print(schema.getIndexLabel("personByCity"))

# Edge label links, formatted as "Person--ActedIn-->Movie"
print(schema.getRelations())
```

### Read, Update and Delete Graph Data

The graph API takes property dictionaries, not chained property builders:

```python
graph = client.graph()
graph.appendVertex(person.id, {"birthDate": "1940-04-25"})    # add properties
graph.eliminateVertex(person.id, {"birthDate": "1940-04-25"}) # drop properties
graph.appendEdge(edge.id, {"city": "Beijing"})
graph.eliminateEdge(edge.id, {"city": "Beijing"})
graph.removeEdgeById(edge.id)
graph.removeVertexById(person.id)
graph.close()
```

`addVertex` returns a `VertexData` with `id`, `label`, `type` and `properties`. `addEdge` returns an `EdgeData` with `id`, `label`, `type`, `outV`, `outVLabel`, `inV`, `inVLabel` and `properties`.

Vertex ids passed to the client may be strings, integers or `uuid.UUID` values. Booleans are rejected, and integers must fit the Java signed long range.

### Batch Writes

`addVertices` takes `(label, properties)` pairs, and `addEdges` takes `(label, out_id, in_id, out_label, in_label, properties)` tuples. Both return objects that carry only the generated ids.

```python
graph = client.graph()
vertices = graph.addVertices([
    ("person", {"name": "Alice", "age": 20}),
    ("person", {"name": "Bob", "age": 23}),
])
edges = graph.addEdges([
    ("knows", vertices[0].id, vertices[1].id, "person", "person", {"date": "2012-01-10"}),
])
```

### Paging and Conditional Queries

```python
graph = client.graph()

# Returns (vertices, next_page); pass next_page back in to continue
vertices, next_page = graph.getVertexByPage("person", limit=10)
vertices, next_page = graph.getVertexByPage("person", limit=10, page=next_page)

# Server-side property predicates
older = graph.getVertexByCondition("person", properties={"age": "P.gt(29)"})

# Edges by page. When vertex_id is given, direction is required
edges, next_page = graph.getEdgeByPage(label="knows", limit=10)
edges, next_page = graph.getEdgeByPage(vertex_id=person.id, direction="OUT", limit=10)

# Batch lookup by id
graph.getVerticesById([v1.id, v2.id])
graph.getEdgesById([e1.id, e2.id])
```

### Execute Gremlin

```python
gremlin = client.gremlin()
result = gremlin.exec("g.V().limit(5)")
print(result)
```

`exec` binds the `graph` and `g` aliases for you, based on the graph name and the resolved GraphSpace, and returns the `result` field of the server response. A response missing `requestId`, `status` or `result` raises `ResponseParseError`.

### Traverse the Graph

`TraverserManager` wraps the server traverser endpoints. Its methods use snake_case.

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

The POST-based variants take request bodies: `advanced_paths`, `customized_paths`, `template_paths`, `customized_crosspoints` and `fusiform_similarity`.

### Graph Variables

```python
variable = client.variable()
variable.set("owner", "mary")
print(variable.get("owner"))
print(variable.all())
variable.remove("owner")
```

### Async Tasks

```python
task = client.task()
print(task.list_tasks(status="success", limit=10))
print(task.get_task(task_id))
task.cancel_task(task_id)
task.delete_task(task_id)
```

### Server Metrics and Graph Info

```python
metrics = client.metrics()
metrics.get_all_basic_metrics()
metrics.get_gauges_metrics()
metrics.get_counters_metrics()
metrics.get_histograms_metrics()
metrics.get_meters_metrics()
metrics.get_timers_metrics()
metrics.get_statistics_metrics()
metrics.get_system_metrics()
metrics.get_backend_metrics()

graphs = client.graphs()
graphs.get_all_graphs()
graphs.get_version()
graphs.get_graph_info()
graphs.get_graph_config()
graphs.clear_graph_all_data()   # deletes every vertex, edge and schema entry

print(client.version().version())
```

### Authentication and Authorization

`AuthManager` follows the server routing: users, targets, belongs and accesses are mounted under `/graphspaces/{graphspace}/auth/...`, while groups stay at the server-level `/auth/groups`. On HugeGraph 1.7.0 and later a graphspace must be resolved, otherwise these calls raise `ValueError` before any request is sent.

```python
auth = client.auth()

user = auth.create_user("test_user", "password")
auth.modify_user(user["id"], user_email="hugegraph@apache.org")
auth.get_user(user["id"])
auth.list_users(limit=10)
auth.delete_user(user["id"])

group = auth.create_group("test_group", "read only")
auth.modify_group(group["id"], group_description="updated")
auth.list_groups()
auth.delete_group(group["id"])

target = auth.create_target("target1", "hugegraph", "127.0.0.1:8080", [])
auth.update_target(target["id"], "target1", "hugegraph", "127.0.0.1:8080", [])
auth.list_targets()
auth.delete_target(target["id"])

belong = auth.create_belong(user["id"], group["id"])
auth.update_belong(belong["id"], "description")
auth.list_belongs()
auth.delete_belong(belong["id"])

access = auth.grant_accesses(group["id"], target["id"], "READ")
auth.modify_accesses(access["id"], "description")
auth.list_accesses()
auth.revoke_accesses(access["id"])
```

## Method Naming

Manager methods written in camelCase, such as `addVertex` and `getVertexById`, also get a snake_case alias generated at construction time. `graph.add_vertex(...)` and `graph.addVertex(...)` reach the same method. The camelCase spellings are marked deprecated in the debug log, so prefer snake_case in new code.

## Error Handling

Exceptions live in `pyhugegraph.utils.exceptions`:

| Exception | Raised when |
|-----------|-------------|
| `NotAuthorizedError` | The server answers 401 |
| `NotFoundError` | The server answers 404, or a required argument is missing |
| `ServerError` | Any other non-2xx response, with the server message attached |
| `ResponseParseError` | A successful response cannot be parsed into the expected shape |
| `ServiceUnavailableError` | The server reports `ServiceUnavailableException` |
| `InvalidParameterError`, `CreateError`, `RemoveError`, `UpdateError`, `DataFormatError` | Raised by individual builders and structures |

Request and response bodies are logged with password, token and secret values redacted.

```python
from pyhugegraph.utils.exceptions import NotFoundError

try:
    graph.getVertexById("no-such-id")
except NotFoundError:
    print("vertex missing")
```

API parameters may change with the HugeGraph REST API version. If an interface is incompatible, first check the REST API documentation for the current server version and the client test cases.

## Development Checks

Run formatting and static checks from the root of the HugeGraph-AI repository:

```bash
./style/code_format_and_analysis.sh
```

Run the tests the same way CI does:

```bash
# Unit and contract tests, no server needed
uv run pytest hugegraph-python-client/src/tests -m "unit or contract"

# Integration tests against a running server
HUGEGRAPH_URL=http://127.0.0.1:8080 \
HUGEGRAPH_GRAPH=hugegraph \
HUGEGRAPH_USER=admin \
HUGEGRAPH_PASSWORD=admin \
uv run pytest hugegraph-python-client/src/tests -m "integration and hugegraph"
```

CI runs the integration job against the `hugegraph/hugegraph:1.7.0` image. `HUGEGRAPH_GRAPHSPACE` is also read when you need a non-default space.

The source code and tests are under `hugegraph-python-client/src/pyhugegraph/` and `hugegraph-python-client/src/tests/`. A runnable example is at `hugegraph-python-client/src/pyhugegraph/example/hugegraph_example.py`.
