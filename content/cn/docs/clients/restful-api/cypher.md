---
title: "Cypher API"
linkTitle: "Cypher"
weight: 15
description: "Cypher（图查询语言）REST 接口:通过 HTTP 接口执行 OpenCypher 声明式图查询语言。"
---

### 9.1 Cypher

> [!NOTE]
> Cypher 语法、语句示例与转译限制请查阅 [图查询语言 - Cypher](/cn/docs/language/hugegraph-cypher/) 及 [Cypher 兼容性矩阵](/cn/docs/language/cypher-compatibility/)。

> 当服务端未开启鉴权时，无需携带 `Authorization` 请求头且凭证不参与鉴权校验；
> 开启鉴权后，支持 `Basic`（标准 RFC 4648 Base64 编码）或 `Bearer` Token（未携带认证信息的请求返回 401），并沿用已验证的调用者权限执行查询。
> 在 1.2.0 至 1.7.0 版本中，未开启鉴权时也必须携带该头。

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

> 请求体包含原始 Cypher 纯文本语句（也支持传入 JSON 对象体，详见 9.1.3）。但服务端接口使用 `@Consumes(APPLICATION_JSON)` 约束，POST 请求必须显式声明 `-H "Content-Type: application/json"` 请求头；若使用 `text/plain` 会被拒绝并返回 HTTP 415。

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

#### 9.1.4 Cypher 结构化错误响应与错误码

当 Cypher 语句解析、转译或执行失败时，HugeGraphServer 返回兼容 Gremlin 规范的响应体，HTTP 状态码保持为 `200`，`status.code` 为 `400`。
结构化的错误详情挂载在 `status.attributes.errors` 数组中。

> [!NOTE]
> HTTP 层错误（如鉴权失败 `401` 或不支持的媒体类型 `415`）属于独立处理路径，不使用此响应封套。
> 客户端应检查响应体中的 `status.code`，而非单纯依赖 HTTP 状态码。响应中不包含顶层 `errors` 字段。

##### 错误响应结构

`status.attributes.errors` 中的每个元素包含以下字段：
- `code`: 稳定的错误代码字符串。
- `message`: 来自转译器或执行引擎的详细错误信息（具体文字描述不作为强约束契约）。
- `hint`: 明确的操作指引与排错建议（无具体指引时为空字符串）。

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

##### 错误码列表

| 错误码 | 识别的失败类型 | 提示信息（Hint） |
|---|---|---|
| `HugeGraph.Cypher.SyntaxError` | 语法解析错误、未知函数、多条语句或未定义变量 | 提示语法规则（如单语句、在 MATCH/WITH 声明变量） |
| `HugeGraph.Cypher.ExecutionError` | 顶点/边类型、属性或索引未定义；未识别错误兜底 | 建议通过 Schema API 创建元数据；兜底为空字符串 |
| `HugeGraph.Cypher.UnsupportedFeature` | 不支持的子句、match/create 模式或函数谓词 | 建议查阅 Cypher 兼容性指南确认受支持语法 |

- **SyntaxError**: 语法解析错误、不支持的内置函数、带行列位置的语义错误、单次请求包含多条语句，或未在 `MATCH`、`UNWIND`、`WITH` 中声明即引用的变量。
- **ExecutionError**: 顶点类型、边类型、属性或索引未定义错误。该错误码同时作为未分类转译错误及底层运行时异常的统一兜底分类，并不意味着图遍历已开始执行。
- **UnsupportedFeature**: 当前 Cypher 转译器不支持的子句、匹配/创建模式、属性类型或自定义谓词。
