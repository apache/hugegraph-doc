---
title: "Cypher API"
linkTitle: "Cypher"
weight: 15
description: "Cypher（图查询语言）REST 接口:通过 HTTP 接口执行 OpenCypher 声明式图查询语言。"
---

### 9.1 Cypher

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

#### 9.1.2 向 HugeGraphServer 发送 Cypher 语句（POST），同步执行


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

> 不是 JSON 格式，是纯文本的 Cypher 语句

##### 使用示例

```javascript
POST
http://localhost:8080/graphspaces/DEFAULT/graphs/hugecypher1/cypher
```

###### Request Body

```cypher
match(n:person) return n.name as name order by n.name limit 1
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
