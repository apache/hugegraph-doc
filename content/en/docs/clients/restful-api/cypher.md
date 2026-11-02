---
title: "Cypher API"
linkTitle: "Cypher"
weight: 15
description: "Cypher REST API: Execute OpenCypher declarative graph query language via HTTP interface."
---

### 9.1 Cypher

> [!NOTE]
> For Cypher syntax, query examples, and translation limits, see [HugeGraph Cypher](/docs/language/hugegraph-cypher/)
> and [Cypher Compatibility](/docs/language/cypher-compatibility/).

> When authentication is disabled, no `Authorization` header is required and credentials are not evaluated;
> when enabled, `Basic` (standard RFC 4648 Base64) or `Bearer` tokens are supported (requests without credentials return 401),
> and queries execute under the caller's verified permissions. On 1.2.0 to 1.7.0, an `Authorization` header was always required even without authentication.

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

> The request body contains a raw Cypher string (a JSON object body is also accepted; see 9.1.3). However, because the server endpoint uses `@Consumes(APPLICATION_JSON)`, requests must include `-H "Content-Type: application/json"` (requests sent with `text/plain` are rejected with HTTP 415).

##### Example

```bash
curl -X POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugecypher1/cypher \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d 'match(n:person) return n.name as name order by n.name limit 1'
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

#### 9.1.4 Cypher Error Response Envelope and Error Codes

When query submission, translation, or execution fails inside the Cypher processing pipeline, HugeGraphServer returns a Gremlin-compatible response envelope
with HTTP status `200` and `status.code = 400`. Structured error details are provided under `status.attributes.errors`.

> [!NOTE]
> HTTP-layer errors (such as authentication failure `401` or unsupported media type `415`) remain separate and do not use this envelope.
> Clients must inspect `status.code` rather than relying solely on the HTTP response code. There is no top-level `errors` field in the response.

##### Error Response Structure

Each entry in `status.attributes.errors` contains:
- `code`: Stable error code string.
- `message`: Detailed failure message from the translator or execution engine (wording is not a frozen contract).
- `hint`: Actionable guidance to resolve the issue (empty string when no specific hint is available).

```json
{
  "requestId": "example-request-id",
  "status": {
    "message": "Expected exactly one statement per query but got: 2",
    "code": 400,
    "attributes": {
      "errors": [
        {
          "code": "HugeGraph.Cypher.SyntaxError",
          "message": "Expected exactly one statement per query but got: 2",
          "hint": "Submit exactly one Cypher statement per request"
        }
      ]
    }
  },
  "result": {
    "data": null,
    "meta": {}
  }
}
```

##### Error Codes

| Error Code | Recognized Failure Condition | Hint |
|---|---|---|
| `HugeGraph.Cypher.SyntaxError` | Parser syntax/semantic errors, multiple statements, or undefined variables | Guidance on Cypher syntax rules |
| `HugeGraph.Cypher.ExecutionError` | Undefined schema labels or property keys; unclassified error fallback | Suggests creating schema elements via schema API |
| `HugeGraph.Cypher.UnsupportedFeature` | Unsupported clauses, match/create patterns, or predicates | Refers to Cypher compatibility guide |

- **SyntaxError**: Triggered by parser syntax rejections, unknown functions, semantic errors with position offsets, multiple statements per request,
  or variables referenced without prior definition in `MATCH`, `UNWIND`, or `WITH`.
- **ExecutionError**: Triggered by undefined vertex/edge labels, property keys, or index labels. Also serves as the fallback for unclassified translation
  or runtime failures; it does not imply traversal execution actually started.
- **UnsupportedFeature**: Triggered by clauses, patterns, property types, or predicates unsupported by the translator.
