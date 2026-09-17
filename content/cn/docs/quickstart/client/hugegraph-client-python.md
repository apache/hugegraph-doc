---
title: "HugeGraph Python 客户端快速入门"
linkTitle: "Python 客户端"
weight: 2
---

`hugegraph-python-client` 是 HugeGraph 的 Python SDK，可管理 Schema、读写图数据并执行 Gremlin 查询。HugeGraph-LLM 和 HugeGraph-ML 也使用这个客户端。

该模块位于 [hugegraph-ai](https://github.com/apache/hugegraph-ai) 仓库的 `hugegraph-python-client/` 目录下，导入名为 `pyhugegraph`。

## 环境要求

- 客户端本身要求 Python 3.9 或更高版本。HugeGraph-AI workspace 要求 Python 3.10 或更高版本，CI 在 3.10 和 3.11 上运行客户端测试。
- HugeGraph Server 1.5.0 或更高版本。客户端会拒绝连接更低版本的 Server，此类场景请改用 v1.3.x 客户端。
- `uv`（推荐）或 `pip`

运行时依赖为 `decorator`、`requests`、`setuptools`、`urllib3` 和 `rich`。

## 安装

发布到 PyPI 的包名是 `hugegraph-python`：

```bash
uv pip install hugegraph-python
# 也可以使用 pip install hugegraph-python
```

> PyPI 上的发布版本落后于仓库代码。在源码中该发行包声明为 `hugegraph-python-client`，版本号与 HugeGraph-AI 其他模块保持一致，需要最新代码时请从源码安装。

如需使用仓库中的最新代码，请从 HugeGraph-AI 仓库根目录同步 workspace。`hugegraph-python-client` 是 workspace 成员，通过 `python-client` extra 暴露，因此仅执行 `uv sync` 不会安装它：

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra python-client
source .venv/bin/activate
```

## 连接并写入数据

```python
from pyhugegraph.client import PyHugeClient

client = PyHugeClient(
    url="http://127.0.0.1:8080",
    graph="hugegraph",
    user="admin",
    pwd="admin",
    graphspace=None,
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

### 客户端参数

`PyHugeClient(url, graph, user, pwd, graphspace=None, timeout=None)`

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | `str` | 必填 | HugeGraph Server 的基础 URL。若未带协议头，客户端会自动补上 `http://`，因此 `127.0.0.1:8080` 也可以使用。 |
| `graph` | `str` | 必填 | 图名称，是第二个位置参数。 |
| `user` | `str` | 必填 | 用户名，以 HTTP Basic Auth 发送。 |
| `pwd` | `str` | 必填 | 密码，以 HTTP Basic Auth 发送。 |
| `graphspace` | `str` 或 `None` | `None` | GraphSpace 名称，`None` 的解析规则见下文。 |
| `timeout` | `tuple[float, float]` 或 `None` | `None` | `(连接, 读取)` 超时时间，单位为秒。`None` 会取 `(0.5, 15.0)`。 |

每个 HTTP 会话在收到 500、502、504 响应时会重试 3 次，退避因子为 0.1。

### Server 版本与 GraphSpace

客户端在构造时解析 GraphSpace：

- 传入非空的 `graphspace` 字符串时直接开启 GraphSpace 模式。
- 否则客户端会请求 `GET {url}/versions` 并读取 `versions.core`。
- Server 版本低于 1.5.0 时抛出 `RuntimeError`，提示升级 Server 或改用 v1.3.x 客户端。
- Server 版本高于 1.5.0 时会把 `graphspace` 设为 `DEFAULT` 并开启 GraphSpace 模式，同时在日志中打印警告。版本恰好为 1.5.0 时保持关闭。
- 若因网络原因探测失败，GraphSpace 模式保持关闭。

该模式决定请求前缀：开启时为 `/graphspaces/<graphspace>/graphs/<graph>/...`，关闭时为 `/graphs/<graph>/...`。

### 客户端提供的 Manager

每个访问器都会惰性创建对应的 Manager，并为其分配独立的 HTTP 会话。

| 访问器 | Manager | 覆盖范围 |
|--------|---------|----------|
| `client.schema()` | `SchemaManager` | 属性、顶点标签、边标签、索引标签 |
| `client.graph()` | `GraphManager` | 顶点与边的增删改查、批量写入、分页 |
| `client.gremlin()` | `GremlinManager` | 执行 Gremlin |
| `client.graphs()` | `GraphsManager` | 图列表、图信息、配置、清空数据 |
| `client.traverser()` | `TraverserManager` | 遍历与路径算法 |
| `client.variable()` | `VariableManager` | 图变量 |
| `client.task()` | `TaskManager` | 异步任务的查询、取消、删除 |
| `client.auth()` | `AuthManager` | 用户、用户组、资源、归属、权限 |
| `client.metrics()` | `MetricsManager` | Server 指标 |
| `client.version()` | `VersionManager` | Server 版本 |

`pyhugegraph.api` 中还提供了 `RankManager`、`RebuildManager` 和 `ServicesManager`，但 `PyHugeClient` 暂未提供对应的访问器，需要时可自行传入 session 构造。

## 常用操作

### 构建 Schema

Schema 构建器采用链式调用，最后调用 `create()`，也可以用 `append()`、`eliminate()` 和 `remove()` 修改已有定义。

```python
schema = client.schema()

# 属性类型：asText/asInt/asLong/asFloat/asDouble/asBool/asByte/asBlob/asDate/asObject
# 基数：valueSingle/valueList/valueSet
# 聚合：calcMax/calcMin/calcSum/calcOld
schema.propertyKey("age").asInt().valueSingle().ifNotExist().create()

# 顶点标签 ID 策略：useAutomaticId/useCustomizeStringId/useCustomizeNumberId/usePrimaryKeyId
schema.vertexLabel("person").properties("name", "age", "city") \
      .primaryKeys("name").nullableKeys("city").ifNotExist().create()

# 边标签：link() 等价于 sourceLabel() 加 targetLabel()
schema.edgeLabel("knows").link("person", "person").multiTimes() \
      .properties("date", "city").sortKeys("date").nullableKeys("city") \
      .ifNotExist().create()

# 索引标签：先 onV/onE，再选择 secondary/range/search/shard/unique
schema.indexLabel("personByCity").onV("person").by("city") \
      .secondary().ifNotExist().create()
```

### 查询 Schema

```python
schema = client.schema()
print(schema.getSchema())            # 完整 Schema，format 默认为 json
print(schema.getPropertyKeys())
print(schema.getVertexLabels())
print(schema.getEdgeLabels())
print(schema.getIndexLabels())

# 查询单个定义
print(schema.getPropertyKey("name"))
print(schema.getVertexLabel("person"))
print(schema.getEdgeLabel("knows"))
print(schema.getIndexLabel("personByCity"))

# 边标签的连接关系，格式形如 Person--ActedIn-->Movie
print(schema.getRelations())
```

### 读取、更新和删除图数据

图接口直接接收属性字典，不支持链式的属性构建器：

```python
graph = client.graph()
graph.appendVertex(person.id, {"birthDate": "1940-04-25"})    # 追加属性
graph.eliminateVertex(person.id, {"birthDate": "1940-04-25"}) # 删除属性
graph.appendEdge(edge.id, {"city": "Beijing"})
graph.eliminateEdge(edge.id, {"city": "Beijing"})
graph.removeEdgeById(edge.id)
graph.removeVertexById(person.id)
graph.close()
```

`addVertex` 返回 `VertexData`，包含 `id`、`label`、`type` 和 `properties`。`addEdge` 返回 `EdgeData`，包含 `id`、`label`、`type`、`outV`、`outVLabel`、`inV`、`inVLabel` 和 `properties`。

传给客户端的顶点 ID 可以是字符串、整数或 `uuid.UUID`。布尔值会被拒绝，整数必须落在 Java signed long 范围内。

### 批量写入

`addVertices` 接收 `(label, properties)` 二元组，`addEdges` 接收 `(label, out_id, in_id, out_label, in_label, properties)` 六元组。两者返回的对象只携带生成的 ID。

```python
graph = client.graph()
vertices = graph.addVertices([
    ("person", {"name": "Alice", "age": 20}),
    ("person", {"name": "Bob", "age": 23}),
])
edges = graph.addEdges([
    ("knows", vertices[0].id, vertices[1].id, "person", "person", {"date": "2012-01-10"}),
])
```

### 分页与条件查询

```python
graph = client.graph()

# 返回 (vertices, next_page)，把 next_page 传回即可继续翻页
vertices, next_page = graph.getVertexByPage("person", limit=10)
vertices, next_page = graph.getVertexByPage("person", limit=10, page=next_page)

# 服务端属性条件
older = graph.getVertexByCondition("person", properties={"age": "P.gt(29)"})

# 边分页查询，传入 vertex_id 时必须同时传 direction
edges, next_page = graph.getEdgeByPage(label="knows", limit=10)
edges, next_page = graph.getEdgeByPage(vertex_id=person.id, direction="OUT", limit=10)

# 按 ID 批量查询
graph.getVerticesById([v1.id, v2.id])
graph.getEdgesById([e1.id, e2.id])
```

### 执行 Gremlin

```python
gremlin = client.gremlin()
result = gremlin.exec("g.V().limit(5)")
print(result)
```

`exec` 会根据图名称和解析出的 GraphSpace 自动绑定 `graph` 与 `g` 别名，并返回服务端响应中的 `result` 字段。响应缺少 `requestId`、`status` 或 `result` 时抛出 `ResponseParseError`。

### 图遍历

`TraverserManager` 封装了 Server 的 traverser 接口，方法名使用蛇形命名。

```python
traverser = client.traverser()

traverser.k_out(marko_id, 2)
traverser.k_neighbor(marko_id, 2)
traverser.same_neighbors(marko_id, josh_id)
traverser.jaccard_similarity(marko_id, josh_id)
traverser.shortest_path(marko_id, ripple_id, 3)
traverser.all_shortest_paths(marko_id, ripple_id, 3)
traverser.weighted_shortest_path(marko_id, ripple_id, "weight", 3)
traverser.single_source_shortest_path(marko_id, 2)
traverser.multi_node_shortest_path([marko_id, josh_id], max_depth=2)
traverser.paths(marko_id, josh_id, 2)
traverser.crosspoints(marko_id, josh_id, 2)
traverser.rings(marko_id, 3)
traverser.rays(marko_id, 2)
traverser.vertices(marko_id)
traverser.edges(edge_id)
```

基于 POST 的接口需要传入请求体：`advanced_paths`、`customized_paths`、`template_paths`、`customized_crosspoints` 和 `fusiform_similarity`。

### 图变量

```python
variable = client.variable()
variable.set("owner", "mary")
print(variable.get("owner"))
print(variable.all())
variable.remove("owner")
```

### 异步任务

```python
task = client.task()
print(task.list_tasks(status="success", limit=10))
print(task.get_task(task_id))
task.cancel_task(task_id)
task.delete_task(task_id)
```

### Server 指标与图信息

```python
metrics = client.metrics()
metrics.get_all_basic_metrics()
metrics.get_gauges_metrics()
metrics.get_counters_metrics()
metrics.get_histograms_metrics()
metrics.get_meters_metrics()
metrics.get_timers_metrics()
metrics.get_statistics_metrics()
metrics.get_system_metrics()
metrics.get_backend_metrics()

graphs = client.graphs()
graphs.get_all_graphs()
graphs.get_version()
graphs.get_graph_info()
graphs.get_graph_config()
graphs.clear_graph_all_data()   # 删除全部顶点、边和 Schema

print(client.version().version())
```

### 认证与授权

`AuthManager` 与 Server 的路由保持一致：用户、资源、归属和权限挂载在 `/graphspaces/{graphspace}/auth/...` 下，用户组仍在 Server 级别的 `/auth/groups`。在 HugeGraph 1.7.0 及以上版本必须能解析出 graphspace，否则这些调用会在发出请求前抛出 `ValueError`。

```python
auth = client.auth()

user = auth.create_user("test_user", "password")
auth.modify_user(user["id"], user_email="hugegraph@apache.org")
auth.get_user(user["id"])
auth.list_users(limit=10)
auth.delete_user(user["id"])

group = auth.create_group("test_group", "read only")
auth.modify_group(group["id"], group_description="updated")
auth.list_groups()
auth.delete_group(group["id"])

target = auth.create_target("target1", "hugegraph", "127.0.0.1:8080", [])
auth.update_target(target["id"], "target1", "hugegraph", "127.0.0.1:8080", [])
auth.list_targets()
auth.delete_target(target["id"])

belong = auth.create_belong(user["id"], group["id"])
auth.update_belong(belong["id"], "description")
auth.list_belongs()
auth.delete_belong(belong["id"])

access = auth.grant_accesses(group["id"], target["id"], "READ")
auth.modify_accesses(access["id"], "description")
auth.list_accesses()
auth.revoke_accesses(access["id"])
```

## 方法命名

Manager 中以驼峰命名的方法（例如 `addVertex`、`getVertexById`）会在构造时自动生成蛇形命名别名，`graph.add_vertex(...)` 与 `graph.addVertex(...)` 指向同一个方法。驼峰写法已在 debug 日志中标记为废弃，新代码建议使用蛇形命名。

## 错误处理

异常定义在 `pyhugegraph.utils.exceptions` 中：

| 异常 | 触发条件 |
|------|----------|
| `NotAuthorizedError` | Server 返回 401 |
| `NotFoundError` | Server 返回 404，或缺少必填参数 |
| `ServerError` | 其他非 2xx 响应，异常信息中附带服务端消息 |
| `ResponseParseError` | 成功响应无法解析为预期结构 |
| `ServiceUnavailableError` | Server 返回 `ServiceUnavailableException` |
| `InvalidParameterError`、`CreateError`、`RemoveError`、`UpdateError`、`DataFormatError` | 由各构建器和数据结构抛出 |

请求体与响应体写入日志时，会对密码、token 和 secret 等字段做脱敏处理。

```python
from pyhugegraph.utils.exceptions import NotFoundError

try:
    graph.getVertexById("no-such-id")
except NotFoundError:
    print("vertex missing")
```

接口参数会随 HugeGraph REST API 版本变化。遇到不兼容时，先核对当前 Server 的 REST API 文档与客户端测试用例。

## 开发检查

在 HugeGraph-AI 仓库根目录运行格式与静态检查：

```bash
./style/code_format_and_analysis.sh
```

按照 CI 的方式运行测试：

```bash
# 单元测试与契约测试，无需 Server
uv run pytest hugegraph-python-client/src/tests -m "unit or contract"

# 集成测试，需要可访问的 Server
HUGEGRAPH_URL=http://127.0.0.1:8080 \
HUGEGRAPH_GRAPH=hugegraph \
HUGEGRAPH_USER=admin \
HUGEGRAPH_PASSWORD=admin \
uv run pytest hugegraph-python-client/src/tests -m "integration and hugegraph"
```

CI 的集成测试作业使用 `hugegraph/hugegraph:1.7.0` 镜像。需要非默认空间时，还可以设置 `HUGEGRAPH_GRAPHSPACE`。

源码与测试位于 `hugegraph-python-client/src/pyhugegraph/` 和 `hugegraph-python-client/src/tests/`，可直接运行的示例在 `hugegraph-python-client/src/pyhugegraph/example/hugegraph_example.py`。
