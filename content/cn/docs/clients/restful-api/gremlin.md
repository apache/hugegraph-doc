---
title: "Gremlin API"
linkTitle: "Gremlin"
weight: 14
description: "Gremlin（图查询语言）REST 接口:通过 HTTP 接口执行 Gremlin 图遍历查询语言脚本。"
---

### 8.1 Gremlin

> ⚠️ **SEC 提醒：生产环境下安全使用原生查询接口**
>
> 图查询语言 (如 Gremlin/Cypher) 本身的灵活性会带来一些潜在的安全隐患。为了保障核心安全，**请避免直接在公网环境暴露任何相关的原生查询接口**。
> 在必须对内暴露的生产场景中，必须开启 **[鉴权体系 (Auth)](/cn/docs/config/config-authentication/)** 并结合 **IP 白名单**作为双重保障机制，严格控制用户执行权限。同时建议结合 Audit Log (审计日志) 来审计具体执行的语句，以及采用 **[容器环境 (Docker/K8s)](/cn/docs/quickstart/hugegraph/hugegraph-server/#31-使用-docker-容器-便于测试)** 部署以提升系统级的安全隔离。

#### 8.1.1 向 HugeGraphServer 发送 gremlin 语句（GET），同步执行

##### Params

- gremlin: 要发送给`HugeGraphServer`执行的`gremlin`语句
- bindings: 用来绑定参数，key 是字符串，value 是绑定的值（只能是字符串或者数字），功能类似于 MySQL 的 Prepared Statement，用于加速语句执行
- language: 发送语句的语言类型，默认为`gremlin-groovy`
- aliases: 为存在于图空间的已有变量添加别名

此 REST 代理的 GET 查询不能可靠地传递含 JSON 花括号的 aliases 参数；当前图绑定名带连字符，也不能直接作为 Groovy 变量。以下用简单表达式示范 GET。需要选择图执行遍历时，请使用下方带 aliases 的 POST 示例。

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

#### 8.1.2 向 HugeGraphServer 发送 gremlin 语句（POST），同步执行

**查询顶点数**

##### 可执行请求命令

```bash
curl --compressed -sS -X POST http://127.0.0.1:8080/gremlin \
  -H 'Content-Type: application/json' \
  --data-binary '{"gremlin":"g.V().count()","aliases":{"g":"__g_DEFAULT-hugegraph"}}'
```

`/gremlin` 是顶层接口。图空间 `DEFAULT` 中图 `hugegraph` 对应的 traversal source 名为 `__g_DEFAULT-hugegraph`，请求通过 `aliases` 映射为脚本中的 `g`。若使用不同图空间或图名，应按 Server 绑定名调整 alias。批量结果可能以 gzip 返回，curl 使用 `--compressed` 可自动解压。

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

顶点数取决于当前图中的数据；上面的 `6` 仅为示例结果。

> 响应体的结构与其他 Vertex 或 Edge 的 RESTful API 的结构有区别，用户可能需要自行解析。

**查询边**

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

边 ID、端点和属性值取决于当前图中的数据。

#### 8.1.3 向 HugeGraphServer 发送 gremlin 语句（POST），异步执行

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/gremlin
```

**查询顶点**

##### Request Body

```json
{
	"gremlin": "g.V('1:marko')",
	"bindings": {},
	"language": "gremlin-groovy",
	"aliases": {}
}
```

注意：

> 异步请求不能自行传入 `aliases` 字段；Server 会自动绑定 `graph`（当前图对象）和 `g`（当前遍历源），并把 URL 中的图名作为 `graph` 的别名。因此脚本可以使用 `graph` 或 `g`，也可以使用当前请求路径中的图名。

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

注：

> 可以通过`GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/1`（其中"1"是 task_id）来查询异步任务的执行状态，更多[异步任务 RESTful API](./task)

**查询边**

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

注：

> 可以通过`GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/2`（其中"2"是 task_id）来查询异步任务的执行状态，更多[异步任务 RESTful API](./task)
