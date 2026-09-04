---
title: "HugeGraph Python Client Quick Start"
linkTitle: "Python Client"
weight: 2
---

`hugegraph-python-client` is the Python SDK for HugeGraph. It manages schemas, reads and writes graph data, and executes Gremlin queries. HugeGraph-LLM and HugeGraph-ML also use this client.

## Requirements

- Python 3.9 or later
- An accessible HugeGraph Server
- `uv` (recommended) or `pip`

## Installation

The package is currently published on PyPI as `hugegraph-python`:

```bash
uv pip install hugegraph-python
# Alternatively: pip install hugegraph-python
```

To use the latest repository code, sync the workspace from the root of the HugeGraph-AI repository:

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync
source .venv/bin/activate
```

## Connect and Write Data

```python
from pyhugegraph.client import PyHugeClient

client = PyHugeClient(
    "127.0.0.1:8080",
    graph="hugegraph",
    user="admin",
    pwd="admin",
    graphspace="DEFAULT",
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

If GraphSpace is disabled in HugeGraph, omit `graphspace`. When it is enabled, pass the actual space name; the default space is usually `DEFAULT`.

## Common Operations

### Query the Schema

```python
schema = client.schema()
print(schema.getPropertyKeys())
print(schema.getVertexLabels())
print(schema.getEdgeLabels())
print(schema.getIndexLabels())
```

### Update and Delete Graph Data

The graph API accepts dictionaries containing object properties:

```python
graph = client.graph()
graph.appendVertex(person.id, {"birthDate": "1940-04-25"})
graph.removeEdgeById(edge.id)
graph.removeVertexById(person.id)
graph.close()
```

### Execute Gremlin

```python
gremlin = client.gremlin()
result = gremlin.exec("g.V().limit(5)")
print(result)
```

API parameters may change with the HugeGraph REST API version. If an interface is incompatible, first check the REST API documentation for the current server version and the client test cases.

## Development Checks

Run formatting and static checks from the root of the HugeGraph-AI repository:

```bash
./style/code_format_and_analysis.sh
```

The source code and tests are under `hugegraph-python-client/src/pyhugegraph/` and `hugegraph-python-client/src/tests/`.
