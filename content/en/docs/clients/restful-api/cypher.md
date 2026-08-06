---
title: "Cypher API"
linkTitle: "Cypher"
weight: 15
description: "Cypher REST API: Execute OpenCypher declarative graph query language via HTTP interface."
---

### 9.1 Cypher

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

#### 9.1.2 Sending a cypher statement (POST) to HugeGraphServer for synchronous execution


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
