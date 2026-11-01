---
title: "Cypher API"
linkTitle: "Cypher"
weight: 15
description: "Cypher REST API: Execute OpenCypher declarative graph query language via HTTP interface."
---

### 9.1 Cypher

> When authentication is disabled, no `Authorization` header is required; when enabled, `Basic` (standard RFC 4648 Base64) or `Bearer` tokens are supported.
> The credentials are forwarded to the Gremlin Server through `conf/remote-objects.yaml`.

#### 9.1.1 Sending a cypher statement (GET) to HugeGraphServer for synchronous execution

##### Method & Url

```http
GET /graphspaces/{graphspace}/graphs/{graph}/cypher?cypher={cypher}
```

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

**Query parameters**

- cypher: Cypher statement


##### Example

```http
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugecypher1/cypher?cypher=match(n:person) return n.name as name order by n.name limit 1
```

##### Response Status

```json
200
```
##### Response Body

```json
{
    "requestId": "766b9f48-2f10-40d9-951a-3027d0748ab7",
    "status": {
        "message": "",
        "code": 200,
        "attributes": {
        }
    },
    "result": {
        "data": [
            {
                "name": "hello"
            }
        ],
        "meta": {
        }
    }
}
```

#### 9.1.2 Sending a cypher statement (POST raw text) to HugeGraphServer for synchronous execution


##### Method & Url

```http
POST /graphspaces/{graphspace}/graphs/{graph}/cypher
```

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

##### Body
{cypher}
- cypher: Cypher statement

Note:

> It is not in JSON format, but a plain text Cypher statement.

##### Example

```http
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugecypher1/cypher
```

###### Request Body

```cypher
match(n:person) return n.name as name order by n.name limit 1
```
##### Response Status

```json
200
```
##### Response Body

```json
{
    "requestId": "f096bee0-e249-498f-b5a3-ea684fc84f57",
    "status": {
        "message": "",
        "code": 200,
        "attributes": {
        }
    },
    "result": {
        "data": [
            {
                "name": "hello"
            }
        ],
        "meta": {
        }
    }
}
```

#### 9.1.3 Sending a parameterized cypher statement (POST JSON, recommended) to HugeGraphServer for synchronous execution

##### Method & Url

```http
POST /graphspaces/{graphspace}/graphs/{graph}/cypher
```

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

##### Body

```json
{
    "cypher": "match(n:person) where n.name = $name return n.name as name order by n.name limit 1",
    "parameters": {
        "name": "hello"
    }
}
```

- cypher: Cypher statement (reference bound parameters using `$param`)
- parameters: Parameter map (JSON object, up to 16 top-level keys; group additional properties into a nested Map)

##### Example

```bash
curl -X POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugecypher1/cypher \
  -H "Content-Type: application/json" \
  -d '{"cypher":"match(n:person) where n.name = $name return n.name as name order by n.name limit 1","parameters":{"name":"hello"}}'
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "requestId": "f096bee0-e249-498f-b5a3-ea684fc84f57",
    "status": {
        "message": "",
        "code": 200,
        "attributes": {
        }
    },
    "result": {
        "data": [
            {
                "name": "hello"
            }
        ],
        "meta": {
        }
    }
}
```
