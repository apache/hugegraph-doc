---
title: "Cypher API"
linkTitle: "Cypher"
weight: 15
description: "Cypher（图查询语言）REST 接口:通过 HTTP 接口执行 OpenCypher 声明式图查询语言。"
---

### 9.1 Cypher

> 当服务端未开启鉴权时，无需携带 `Authorization` 请求头；开启鉴权后，支持 `Basic`（标准 RFC 4648 Base64 编码）或 `Bearer` Token（未携带认证信息的请求返回 401）。认证信息通过 `conf/remote-objects.yaml` 透传给 Gremlin Server。

#### 9.1.1 向 HugeGraphServer 发送 Cypher 语句（GET），同步执行

##### Method & Url

```javascript
GET /graphspaces/{graphspace}/graphs/{graph}/cypher?cypher={cypher}
```

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

**请求参数说明：**

- cypher: cypher 语句


##### 使用示例

```javascript
GET
http://localhost:8080/graphspaces/DEFAULT/graphs/hugecypher1/cypher?cypher=match(n:person) return n.name as name order by n.name limit 1
```

##### Response Status

```javascript
200
```
##### Response Body

```javascript
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

#### 9.1.2 向 HugeGraphServer 发送 Cypher 语句（POST 原始文本），同步执行


##### Method & Url

```javascript
POST /graphspaces/{graphspace}/graphs/{graph}/cypher
```

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

##### Body
{cypher}

- cypher: cypher 语句

注意：

> 虽然请求体是原始 Cypher 纯文本语句而非 JSON 对象，但服务端接口使用 `@Consumes(APPLICATION_JSON)` 约束。POST 请求必须显式声明 `-H "Content-Type: application/json"` 请求头；若使用 `text/plain` 会被拒绝并返回 HTTP 415。

##### 使用示例

```bash
curl -X POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugecypher1/cypher \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d 'match(n:person) return n.name as name order by n.name limit 1'
```
##### Response Status

```javascript
200
```
##### Response Body

```javascript
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

#### 9.1.3 向 HugeGraphServer 发送参数化 Cypher 语句（POST JSON，推荐），同步执行

##### Method & Url

```javascript
POST /graphspaces/{graphspace}/graphs/{graph}/cypher
```

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

##### Body

```json
{
    "cypher": "match(n:person) where n.name = $name return n.name as name order by n.name limit 1",
    "parameters": {
        "name": "hello"
    }
}
```

- cypher: Cypher 查询语句（引用绑定参数使用 `$param` 形式）
- parameters: 参数映射表（JSON 对象，顶层最多支持 16 个键；更多属性可放入嵌套 Map 中）

##### 使用示例

```bash
curl -X POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugecypher1/cypher \
  -H "Content-Type: application/json" \
  -d '{"cypher":"match(n:person) where n.name = $name return n.name as name order by n.name limit 1","parameters":{"name":"hello"}}'
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
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
