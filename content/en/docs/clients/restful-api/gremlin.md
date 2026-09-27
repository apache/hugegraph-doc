---
title: "Gremlin API"
linkTitle: "Gremlin"
weight: 14
description: "Gremlin REST API: Execute Gremlin graph traversal language scripts via HTTP interface."
---

### 8.1 Gremlin

> [!WARNING]
> **Use native query APIs safely in production**
>
> The flexibility of graph query languages such as Gremlin and Cypher can introduce security risks. **Do not expose native query endpoints directly to the public network.**
> In production, enable **[authentication and authorization](/docs/config/config-authentication/)**, maintain an **IP allowlist**, and grant minimum permissions. Standard Server configuration writes authentication-proxy authorization records to `audit-*.log`; retain these files and restrict read access. `auth.audit_log_rate` limits per-user output rather than serving as a dedicated audit-log on/off switch.

#### 8.1.1 Send a Gremlin statement to HugeGraphServer (GET), synchronously

##### Params

- gremlin: The Gremlin statement to execute on HugeGraphServer.
- bindings: Parameter bindings with string keys and string or numeric values, similar to MySQL prepared statements, to speed up execution.
- language: Statement language, defaulting to `gremlin-groovy`.
- aliases: Adds aliases for existing variables in a graph space.

This REST proxy cannot reliably carry a JSON-braced `aliases` parameter in GET queries. Current graph binding names contain hyphens and cannot be used directly as Groovy variables. This GET example uses a simple expression; use the POST example with aliases below to select a graph for traversal.

##### Method & Url

```
curl --compressed --get \
  --data-urlencode "gremlin=1+1" \
  http://127.0.0.1:8080/gremlin
```

##### Response Status

```json
200
```

##### Response Body

```json
{
	"requestId": "<request_id>",
	"status": {"message": "", "code": 200, "attributes": {}},
	"result": {"data": [2], "meta": {}}
}
```

#### 8.1.2 Send a Gremlin statement to HugeGraphServer (POST), synchronously

**Count vertices**

##### Runnable request

```bash
curl --compressed -sS -X POST http://127.0.0.1:8080/gremlin \
  -H 'Content-Type: application/json' \
  --data-binary '{"gremlin":"g.V().count()","aliases":{"g":"__g_DEFAULT-hugegraph"}}'
```

`/gremlin` is a top-level endpoint. The traversal source for graph `hugegraph` in graph space `DEFAULT` is `__g_DEFAULT-hugegraph`; `aliases` maps it to script variable `g`. Adjust the alias to the Server binding name for another graph or graph space. Batch responses can use gzip; curl `--compressed` decompresses them automatically.

##### Response Status

```json
200
```

##### Response Body

```json
{
	"requestId": "<request_id>",
	"status": {"message": "", "code": 200, "attributes": {}},
	"result": {"data": [6], "meta": {}}
}
```

Vertex count depends on current graph data; `6` above is an example result.

> The response structure differs from the Vertex and Edge REST APIs; clients may need to parse it explicitly.

**Query edges**

##### Request Body

```json
{
	"gremlin": "g.E().hasLabel('created').limit(1)",
	"bindings": {},
	"language": "gremlin-groovy",
	"aliases": {
		"g": "__g_DEFAULT-hugegraph"
	}
}
```

##### Response Status

```json
200
```

##### Response Body

```json
{
	"requestId": "<request_id>",
	"status": {
		"message": "",
		"code": 200,
		"attributes": {}
	},
	"result": {
		"data": [{
			"id": "<edge_id>",
			"label": "created",
			"type": "edge",
			"outVLabel": "person",
			"inVLabel": "software",
			"outV": "<source_vertex_id>",
			"inV": "<target_vertex_id>",
			"properties": {
				"weight": 0.4,
				"date": "<date>"
			}
		}],
		"meta": {}
	}
}
```

Edge IDs, endpoints, and properties depend on current graph data.

#### 8.1.3 Send a Gremlin statement to HugeGraphServer (POST), asynchronously

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/gremlin
```

**Query vertices**

##### Request Body

```json
{
	"gremlin": "g.V('1:marko')",
	"bindings": {},
	"language": "gremlin-groovy",
	"aliases": {}
}
```

Note:

> Asynchronous requests cannot supply `aliases`. Server automatically binds `graph` to the current graph and `g` to its traversal source, and adds the URL graph name as an alias for `graph`. Scripts can use `graph`, `g`, or that graph name.

##### Response Status

```json
201
```

##### Response Body

```json
{
	"task_id": 1
}
```

Note:

> Query task status with `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/1`, where `1` is the task ID. See the [asynchronous task REST API](./task).

**Query edges**

##### Request Body

```json
{
	"gremlin": "g.E().hasLabel('created').limit(1)",
	"bindings": {},
	"language": "gremlin-groovy",
	"aliases": {}
}
```

##### Response Status

```json
201
```

##### Response Body

```json
{
	"task_id": 2
}
```

Note:

> Query task status with `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/2`, where `2` is the task ID. See the [asynchronous task REST API](./task).
