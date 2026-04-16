---
title: "Gremlin API"
linkTitle: "Gremlin"
weight: 14
description: "Gremlin REST API: Execute Gremlin graph traversal language scripts via HTTP interface."
---

### 8.1 Gremlin

> ⚠️ **SEC Reminder: Safe Usage of Native Query Endpoints in Production Environments**
>
> The flexibility of Graph Query Languages (such as Gremlin/Cypher) inherently introduces certain potential security risks. To ensure core security, **please avoid exposing any related native query endpoints directly to the public network**.
> In production scenarios where internal exposure is required, you must enable the **[Authentication System (Auth)](/docs/config/config-authentication/)** combined with an **IP Whitelist** as a dual-security mechanism to strictly control user execution permissions. Additionally, it is advised to use an Audit Log to audit the specific statements executed and to adopt **[Containerized Deployment (Docker/K8s)](/docs/quickstart/hugegraph/hugegraph-server/#31-use-docker-container-convenient-for-testdev)** to enhance system-level security isolation.

#### 8.1.1 Sending a gremlin statement (GET) to HugeGraphServer for synchronous execution

##### Params

- gremlin: The gremlin statement to be sent to `HugeGraphServer` for execution
- bindings: Used to bind parameters. Key is a string, and the value is the bound value (can only be a string or number). This functionality is similar to MySQL's Prepared Statement and is used to speed up statement execution.
- language: The language type of the sent statement. Default is `gremlin-groovy`.
- aliases: Adds aliases for existing variables in the graph space.

**Querying vertices**

##### Method & Url

```
GET http://127.0.0.1:8080/gremlin?gremlin=hugegraph.traversal().V('1:marko')
```

##### Response Status

```json
200
```

##### Response Body

```json
{
	"requestId": "c6ef47a8-b634-4b07-9d38-6b3b69a3a556",
	"status": {
		"message": "",
		"code": 200,
		"attributes": {}
	},
	"result": {
		"data": [{
			"id": "1:marko",
			"label": "person",
			"type": "vertex",
			"properties": {
				"city": [{
					"id": "1:marko>city",
					"value": "Beijing"
				}],
				"name": [{
					"id": "1:marko>name",
					"value": "marko"
				}],
				"age": [{
					"id": "1:marko>age",
					"value": 29
				}]
			}
		}],
		"meta": {}
	}
}
```

#### 8.1.2 Sending a gremlin statement (POST) to HugeGraphServer for synchronous execution

##### Method & Url

```
POST http://localhost:8080/gremlin
```

**Querying vertices**

##### Request Body

```json
{
	"gremlin": "hugegraph.traversal().V('1:marko')",
	"bindings": {},
	"language": "gremlin-groovy",
	"aliases": {}
}
```

##### Response Status

```json
200
```

##### Response Body

```json
{
	"requestId": "c6ef47a8-b634-4b07-9d38-6b3b69a3a556",
	"status": {
		"message": "",
		"code": 200,
		"attributes": {}
	},
	"result": {
		"data": [{
			"id": "1:marko",
			"label": "person",
			"type": "vertex",
			"properties": {
				"city": [{
					"id": "1:marko>city",
					"value": "Beijing"
				}],
				"name": [{
					"id": "1:marko>name",
					"value": "marko"
				}],
				"age": [{
					"id": "1:marko>age",
					"value": 29
				}]
			}
		}],
		"meta": {}
	}
}
```

Note:

> Here we directly use the graph object (`hugegraph`), first retrieve its traversal iterator (`traversal()`), and then retrieve the vertices. Instead of writing `graph.traversal().V()` or `g.V()`, you can use aliases to operate on the graph and traversal iterator. In this case, `hugegraph` is a native variable, and `__g_hugegraph` is an additional variable added by HugeGraphServer. Each graph will have a corresponding traversal iterator object in this format (`__g_${graph}`).

> The structure of the response body is different from the RESTful API structure of other vertices or edges. Users may need to parse it manually.

**Querying edges**

##### Request Body

```json
{
	"gremlin": "g.E('S1:marko>2>>S2:lop')",
	"bindings": {},
	"language": "gremlin-groovy",
	"aliases": {
		"graph": "hugegraph", 
		"g": "__g_hugegraph"
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
	"requestId": "3f117cd4-eedc-4e08-a106-ee01d7bb8249",
	"status": {
		"message": "",
		"code": 200,
		"attributes": {}
	},
	"result": {
		"data": [{
			"id": "S1:marko>2>>S2:lop",
			"label": "created",
			"type": "edge",
			"inVLabel": "software",
			"outVLabel": "person",
			"inV": "2:lop",
			"outV": "1:marko",
			"properties": {
				"weight": 0.4,
				"date": "20171210"
			}
		}],
		"meta": {}
	}
}
```

#### 8.1.3 Sending a gremlin statement (POST) to HugeGraphServer for asynchronous execution

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/gremlin
```

**Querying vertices**

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

> Asynchronous execution of Gremlin statements does not currently support aliases. You can use `graph` to represent the graph you want to operate on, or directly use the name of the graph, such as `hugegraph`. Additionally, `g` represents the traversal, which is equivalent to `graph.traversal()` or `hugegraph.traversal()`.

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

> You can query the execution status of an asynchronous task by using `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/1` (where "1" is the task_id). For more information, refer to the [Asynchronous Task RESTful API](./task).

**Querying edges**

##### Request Body

```json
{
	"gremlin": "g.E('S1:marko>2>>S2:lop')",
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

> You can query the execution status of an asynchronous task by using `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/2` (where "2" is the task_id). For more information, refer to the [Asynchronous Task RESTful API](./task).
