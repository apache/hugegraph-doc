---
title: "HugeGraph Python 客户端快速上手"
linkTitle: "Python 客户端"
weight: 2
aliases:
  - /docs/quickstart/client/hugegraph-client-python/
---

`hugegraph-python-client` 是 Apache HugeGraph 的 Python SDK。它支持管理 Schema、读写图数据、执行 Gremlin 查询、进行 OLTP 实时图遍历以及
提交异步 OLAP 全图计算任务。HugeGraph-LLM 和 HugeGraph-ML 也依赖该客户端进行图数据库交互。

客户端源码位于 [hugegraph-ai](https://github.com/apache/hugegraph-ai) 仓库的 `hugegraph-python-client/` 目录下，导入包名为 `pyhugegraph`。

## 环境要求

- Python >= 3.12（支持 Python 3.12–3.14）。
- HugeGraph Server 1.5.0 或更高版本（Server 1.7+ 推荐开启 GraphSpace 模式；1.5/1.6 使用传统路由）。
- `pip` 或 `uv` 包管理器。

运行时依赖包括 `decorator`、`requests`、`urllib3` 和 `rich`。

## 安装

客户端提供两种安装方式，具体取决于使用的是 PyPI 稳定发行版还是 master 分支最新的开发功能。

> [!NOTE]
> **版本与功能边界说明**：
> 已发布的 PyPI 发行包（`hugegraph-python` 1.7.x）为稳定基础版本，以 CamelCase 命名风格为主（带旧版 snake_case 别名）。
> 本文档演示的现代特性——包括原生 `snake_case` API、`client.olap()` 全图计算算法、`client.task().wait()` 任务轮询等待、
> `client.close()` 连接生命周期管理以及更新后的遍历器签名——均对齐 master 分支最新实现。
> 如需体验或测试这些新特性，请通过源码方式安装客户端。

```bash {tab="PyPI 稳定版 (1.7.x)"}
pip install hugegraph-python
# 或使用 uv:
# uv pip install hugegraph-python
```

```bash {tab="源码安装 (Master)"}
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/hugegraph-python-client
pip install -e .
```

```bash {tab="Workspace 同步 (uv)"}
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra python-client
source .venv/bin/activate
```

## 连接与数据写入

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
schema.property_key("name").as_text().if_not_exist().create()
schema.property_key("birthDate").as_text().if_not_exist().create()
schema.vertex_label("Person").properties("name", "birthDate") \
      .use_primary_key_id().primary_keys("name").if_not_exist().create()
schema.vertex_label("Movie").properties("name") \
      .use_primary_key_id().primary_keys("name").if_not_exist().create()
schema.edge_label("ActedIn").source_label("Person").target_label("Movie") \
      .if_not_exist().create()

graph = client.graph()
person = graph.add_vertex(
    "Person", {"name": "Al Pacino", "birthDate": "1940-04-25"}
)
movie = graph.add_vertex("Movie", {"name": "The Godfather"})
edge = graph.add_edge("ActedIn", person.id, movie.id, {})

print(graph.get_vertex_by_id(person.id))
print(graph.get_edge_by_id(edge.id))

client.close()
```

### 客户端初始化参数

`PyHugeClient(url, graph, user, pwd, graphspace=None, timeout=None, *, token=None)`

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | `str` | 必填 | HugeGraph Server 基础地址。若未携带协议前缀，会自动补齐 `http://`（例如 `127.0.0.1:8080`）。 |
| `graph` | `str` | 必填 | 目标图实例名称，为第二个位置参数。 |
| `user` | `str` | 必填 | 用户名，用于 HTTP Basic Auth 认证。 |
| `pwd` | `str` | 必填 | 密码，用于 HTTP Basic Auth 认证。 |
| `graphspace` | `str` 或 `None` | `None` | GraphSpace 名称。为 `None` 时通过版本探测自动决定路由。 |
| `timeout` | `float`、`tuple[float, float]` 或 `None` | `None` | `(connect, read)` 超时秒数，或统一指定单个浮点数。默认值为 `(0.5, 15.0)`。 |
| `token` | `str` 或 `None` | `None` | 显式指定 Bearer Token；提供时优先覆盖 Basic Auth 认证。 |
{.wide}

对于幂等请求，在收到 500、502、504 错误响应时最多重试 3 次（退避系数为 0.1）。异步任务轮询等待期间会自动管理截止时间预算，不额外触发重定向或 HTTP 重试。

### 服务端版本与 GraphSpace 路由

客户端在初始化阶段自动解析 GraphSpace 路由：
- 显式传入非空 `graphspace` 时，直接启用对应的 GraphSpace 路由模式。
- `graphspace=None` 时，客户端向 `GET {url}/versions` 发起探测以获取服务端内核版本。
- HugeGraph Server 1.7+ 默认启用 GraphSpace 并分配至 `DEFAULT`。
- HugeGraph Server 1.5 / 1.6 保持传统无 GraphSpace 路由。
- 低于 1.5.0 的版本不支持，初始化时会抛出 `RuntimeError`。
- 若版本探测失败且未显式指定 GraphSpace，客户端初始化将直接抛出异常，避免错误猜测服务端路由结构。

路由模式决定了服务端请求路径前缀：开启 GraphSpace 时为 `/graphspaces/<graphspace>/graphs/<graph>/...`，关闭时为 `/graphs/<graph>/...`。

### 客户端入口概览

`PyHugeClient` 实例维护全局共享的 HTTP Session。所有管理器均采用延迟加载并缓存复用：

| 访问入口 | 管理器类 | 功能范围 |
|----------|----------|----------|
| `client.schema()` | `SchemaManager` | 属性类型、顶点类型、边类型、索引类型管理 |
| `client.graph()` | `GraphManager` | 顶点与边增删改查、批量写入、条件分页查询 |
| `client.gremlin()` | `GremlinManager` | 执行 Gremlin 查询语句 |
| `client.traverser()` | `TraverserManager` | 实时图遍历与路径查询（OLTP） |
| `client.rank()` | `RankManager` | 实时个性化推荐排序（OLTP） |
| `client.olap()` | `OlapManager` | 异步全图计算算法作业（OLAP） |
| `client.task()` | `TaskManager` | 异步任务状态查询、结果轮询等待、任务取消与删除 |
| `client.graphs()` | `GraphsManager` | 图元数据查看、配置导出、图列表、清空全图数据 |
| `client.graphspaces()` | `GraphspaceManager` | 多图空间（GraphSpace）生命周期管理 |
| `client.schema_templates()` | `SchemaTemplateManager` | 可复用 Schema 模板管理 |
| `client.auth()` | `AuthManager` | 用户、用户组、目标资源、所属关系与权限管理 |
| `client.variable()` | `VariableManager` | 图级别持久化键值变量 |
| `client.metrics()` | `MetricsManager` | 服务端监控指标数据采集 |
| `client.version()` | `VersionManager` | 服务端及各组件版本信息 |
| `client.rest()` | `RestClient` | 底层 REST API 直接调用及扩展端点 |
{.wide}

## 常用操作

### 定义 Schema

Schema 构造器采用链式调用。调用 `create()` 执行创建，或使用 `append()`、`eliminate()`、`remove()` 修改已有定义：

```python
schema = client.schema()

# 属性类型：as_text / as_int / as_long / as_float / as_double / as_bool / as_date
# 基数模式：value_single / value_list / value_set
schema.property_key("age").as_int().value_single().if_not_exist().create()

# 顶点类型：use_automatic_id / use_customize_string_id / use_primary_key_id
schema.vertex_label("person").properties("name", "age", "city") \
      .primary_keys("name").nullable_keys("city").if_not_exist().create()

# 边类型：link() 快捷指定起点与终点顶点类型
schema.edge_label("knows").link("person", "person").multi_times() \
      .properties("date", "city").sort_keys("date").nullable_keys("city") \
      .if_not_exist().create()

# 索引类型：on_v / on_e，支持 secondary / range / search / shard / unique
schema.index_label("personByCity").on_v("person").by("city") \
      .secondary().if_not_exist().create()
```

### 查询 Schema

```python
schema = client.schema()
print(schema.get_schema())            # 获取全图 Schema 结构字典
print(schema.get_property_keys())
print(schema.get_vertex_labels())
print(schema.get_edge_labels())
print(schema.get_index_labels())

# 查询单个 Schema 定义
print(schema.get_property_key("name"))
print(schema.get_vertex_label("person"))
print(schema.get_edge_label("knows"))
print(schema.get_index_label("personByCity"))

# 边关联关系概览，格式形如 "Person--ActedIn-->Movie"
print(schema.get_relations())
```

### 增删改查图数据

图数据 API 直接接收 Python 属性字典：

```python
graph = client.graph()
graph.append_vertex(person.id, {"birthDate": "1940-04-25"})    # 追加属性
graph.eliminate_vertex(person.id, {"birthDate": "1940-04-25"}) # 移除属性
graph.append_edge(edge.id, {"city": "Beijing"})
graph.eliminate_edge(edge.id, {"city": "Beijing"})
graph.remove_edge_by_id(edge.id)
graph.remove_vertex_by_id(person.id)
```

`add_vertex` 返回包含 `id`、`label`、`type` 与 `properties` 的 `VertexData` 实例。
`add_edge` 返回包含 `id`、`label`、`type`、`outV`、`outVLabel`、`inV`、`inVLabel` 与 `properties` 的 `EdgeData` 实例。

传入客户端的顶点 ID 可以是字符串、整数或 `uuid.UUID` 对象。布尔类型会被拦截拒绝，整数必须位于 Java 64 位有符号整型范围内。

### 批量导入数据

`add_vertices` 接收 `(label, properties)` 元组列表，`add_edges` 接收 `(label, out_id, in_id, out_label, in_label, properties)` 元组列表：

```python
graph = client.graph()
vertices = graph.add_vertices([
    ("person", {"name": "Alice", "age": 20}),
    ("person", {"name": "Bob", "age": 23}),
])
edges = graph.add_edges([
    ("knows", vertices[0].id, vertices[1].id, "person", "person", {"date": "2012-01-10"}),
])
```

### 分页与条件查询

```python
graph = client.graph()

# 分页迭代查询：传入上一页返回的 next_page token 即可继续拉取下一页
vertices, next_page = graph.get_vertex_by_page("person", limit=10)
vertices, next_page = graph.get_vertex_by_page("person", limit=10, page=next_page)

# 服务端属性条件过滤
older = graph.get_vertex_by_condition("person", properties={"age": "P.gt(29)"})

# 边分页查询（指定 vertex_id 时必须同时指定 direction 方向）
edges, next_page = graph.get_edge_by_page(label="knows", limit=10)
edges, next_page = graph.get_edge_by_page(vertex_id=person.id, direction="OUT", limit=10)

# 根据 ID 列表批量查询顶点与边
graph.get_vertices_by_id([v1.id, v2.id])
graph.get_edges_by_id([e1.id, e2.id])
```

### 执行 Gremlin 查询

```python
gremlin = client.gremlin()
result = gremlin.exec("g.V().limit(5)")
print(result)
```

`exec()` 会根据图实例名称及解析出的 GraphSpace 自动绑定 `graph` 与 `g` 别名，并解析返回服务端响应中的 `result` 数据内容。

### 实时图遍历（OLTP）

`client.traverser()` 封装了服务端实时图遍历接口，支持多跳邻居、最短路径、共同邻居与相似度计算：

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

POST 方式的遍历接口支持复杂请求体：`advanced_paths`、`customized_paths`、`template_paths`、`customized_crosspoints` 以及 `fusiform_similarity`。

## OLAP 全图计算任务

对于全图级别的重型计算算法（如 PageRank、Louvain 社区发现、中心度计算等），请使用 `client.olap()`。这些作业在服务端以异步任务方式运行并通过 Task ID 进行跟踪管理：

```python
# 1. 提交异步计算任务
receipt = client.olap().count_vertex()
task_id = receipt["task_id"]

# 2. 轮询等待任务完成并获取计算结果
task = client.task().wait(task_id, timeout=300, poll_interval=1)
result = client.task().result(task)
print(result)

# 也可以直接使用 run() 一步完成提交、等待与结果解析：
result = client.olap().run("count_vertex", timeout=60)
```

### 支持的 OLAP 算法

服务端提供了 17 个唯一的全图计算算法名称：

| 算法类别 | 具体算法名称 |
|----------|--------------|
| 图统计 | `count_edge`、`count_vertex`、`subgraph_stat`、`triangle_count`、`rings` |
| 中心度 | `betweenness_centrality`、`closeness_centrality`、`degree_centrality`、`eigenvector_centrality`、`stress_centrality` |
| 社区与聚类 | `cluster_coefficient`、`k_core`、`louvain`、`lpa`、`weak_connected_component` |
| 排序与相似度 | `page_rank`、`fusiform_similarity` |
{.wide}

> [!TIP]
> 类似 `page_rank` 的算法会将计算出的权重属性回写到图中。在要求显式 Schema 声明的环境中，执行 PageRank 前需在参与计算的顶点类型上提前声明名为 `r_rank` 的可空 `DOUBLE` 属性。

## 任务生命周期管理

`TaskManager` 提供了对异步任务的完整管控能力：

```python
task = client.task()

# 查询任务历史列表
task.list_tasks(status="success", limit=10)

# 轮询等待指定任务完成
record = task.wait(task_id, timeout=300, poll_interval=1)

# 解码任务执行结果（只对序列化 JSON 解析一次）
result = task.result(record)

# 取消或删除任务
task.cancel_task(task_id)
task.delete_task(task_id, force=False)
```

- `wait(id, timeout=300, poll_interval=1)` 轮询期间仅查询任务状态而不拉取大体积结果，完成后再统一获取最终产出。
- `TaskTimeoutError` 仅代表客户端轮询等待超时，服务端后台运行的任务作业不会被终止。
- 如需强行终止服务端任务，请显式调用 `cancel_task(id)`。

## 图变量、监控与元数据

```python
# 图变量管理
variable = client.variable()
variable.set("owner", "mary")
print(variable.get("owner"))
print(variable.all())
variable.remove("owner")

# 监控指标数据
metrics = client.metrics()
metrics.get_all_basic_metrics()
metrics.get_system_metrics()
metrics.get_backend_metrics()

# 图管理与版本
graphs = client.graphs()
print(graphs.list())
print(client.version().version())
```

## 认证与权限控制

`PyHugeClient` 同时支持 HTTP Basic Auth 与 Bearer Token 认证：

```python
# 将会话切换为 Bearer Token 认证
client.use_token("your-jwt-token")

# 恢复为初始化配置的 HTTP Basic Auth 凭据
client.use_token(None)
```

`AuthManager` 支持在 GraphSpace 隔离下管理用户、用户组、目标资源、所属关系以及操作权限：

```python
auth = client.auth()

user = auth.create_user("test_user", "password")
auth.modify_user(user["id"], user_email="hugegraph@apache.org")
auth.get_user(user["id"])
auth.list_users(limit=10)

group = auth.create_group("test_group", "read only")
auth.modify_group(group["id"], group_description="updated")
auth.list_groups()

target = auth.create_target("target1", "hugegraph", "127.0.0.1:8080", [])
auth.update_target(target["id"], "target1", "hugegraph", "127.0.0.1:8080", [])
auth.list_targets()

belong = auth.create_belong(user["id"], group["id"])
auth.update_belong(belong["id"], "description")
auth.list_belongs()

access = auth.grant_accesses(group["id"], target["id"], "READ")
auth.modify_accesses(access["id"], "description")
auth.list_accesses()

# 按照依赖反向顺序清理资源
auth.revoke_accesses(access["id"])
auth.delete_belong(belong["id"])
auth.delete_target(target["id"])
auth.delete_group(group["id"])
auth.delete_user(user["id"])
```

## 方法命名规范与迁移说明

- **推荐规范**：新代码请统一使用 `snake_case` 方法名（如 `add_vertex`、`property_key` 等）。
- **兼容保证**：现有的公开 CamelCase 方法（如 `addVertex`、`propertyKey` 等）作为直接别名持续得到兼容支持。
- **客户端生命周期**：结束调用后请统一通过 `client.close()` 释放连接池会话资源，无需单独关闭单个 manager。
- **返回契约**：
  - 传统快捷接口 `get_all_graphs()`、`get_version()` 和 `get_graph_info()` 保持返回 JSON 字符串以维护向前兼容。
  - 标准现代接口 `client.graphs().list()`、`client.version().version()` 和 `client.graphs().get(graph_name)` 直接返回已解析的 Python 字典。
  - 带权最短路径与单源最短路径方法不再支持 `max_depth` 参数（服务端接口不支持）；请使用 `capacity`、`max_degree` 和 `skip_degree` 参数进行限制。

## 底层 REST API 直接调用

对于批量原生接口调用或高级管理器尚未封装的扩展接口，可通过 `client.rest()` 直接访问完整 REST 接口面：

```python
rest = client.rest()
print(rest.vertex.list(label="person", offset=0, limit=20))
print(rest.task.list(status="success", page="", limit=20))
```

下表列出与服务端完全对齐的 194 个底层 REST 端点：

<!-- BEGIN REST CONTRACT -->
| Python REST entry | Method | Path | Query parameters |
| --- | --- | --- | --- |
| `rest.access.create()` | POST | `/graphspaces/{graphspace}/auth/accesses` | — |
| `rest.access.delete()` | DELETE | `/graphspaces/{graphspace}/auth/accesses/{id}` | — |
| `rest.access.get()` | GET | `/graphspaces/{graphspace}/auth/accesses/{id}` | — |
| `rest.access.list()` | GET | `/graphspaces/{graphspace}/auth/accesses` | group, target, limit |
| `rest.access.update()` | PUT | `/graphspaces/{graphspace}/auth/accesses/{id}` | — |
| `rest.adamic_adar.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/adamicadar` | vertex, other, direction, label, max_degree, limit |
| `rest.algorithm.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/jobs/algorithm/{name}` | — |
| `rest.all_shortest_paths.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/allshortestpaths` | source, target, direction, label, max_depth, max_degree, skip_degree, with_vertex, with_edge, capacity |
| `rest.arthas.start_arthas()` | PUT | `/arthas` | — |
| `rest.belong.create()` | POST | `/graphspaces/{graphspace}/auth/belongs` | — |
| `rest.belong.delete()` | DELETE | `/graphspaces/{graphspace}/auth/belongs/{id}` | — |
| `rest.belong.get()` | GET | `/graphspaces/{graphspace}/auth/belongs/{id}` | — |
| `rest.belong.list()` | GET | `/graphspaces/{graphspace}/auth/belongs` | user, group, limit |
| `rest.belong.update()` | PUT | `/graphspaces/{graphspace}/auth/belongs/{id}` | — |
| `rest.computer.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/jobs/computer/{name}` | — |
| `rest.count.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/count` | — |
| `rest.crosspoints.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/crosspoints` | source, target, direction, label, max_depth, max_degree, capacity, limit |
| `rest.customized_crosspoints.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/customizedcrosspoints` | — |
| `rest.customized_paths.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/customizedpaths` | — |
| `rest.cypher.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/cypher` | — |
| `rest.cypher.query()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/cypher` | cypher |
| `rest.edge.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges` | — |
| `rest.edge.create_batch()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/batch` | check_vertex |
| `rest.edge.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/{id}` | label |
| `rest.edge.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/{id}` | — |
| `rest.edge.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges` | vertex_id, direction, label, properties, keep_start_p, offset, page, limit |
| `rest.edge.update_batch()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/batch` | — |
| `rest.edge.update_by_id()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/graph/edges/{id}` | action |
| `rest.edge_existence.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/edgeexist` | source, target, label, sort_values, limit |
| `rest.edge_label.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels` | — |
| `rest.edge_label.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels/{name}` | — |
| `rest.edge_label.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels/{name}` | — |
| `rest.edge_label.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels` | names |
| `rest.edge_label.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/schema/edgelabels/{name}` | action |
| `rest.edges.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/edges` | ids |
| `rest.edges.scan()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/edges/scan` | start, end, page, page_limit |
| `rest.edges.shards()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/edges/shards` | split_size |
| `rest.exception_trace.get()` | GET | `/exception/trace` | — |
| `rest.exception_trace.trace()` | PUT | `/exception/trace` | — |
| `rest.fusiform_similarity.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/fusiformsimilarity` | — |
| `rest.graph_space.check_default_role()` | GET | `/graphspaces/{graphspace}/role` | user, role, graph |
| `rest.graph_space.create()` | POST | `/graphspaces` | — |
| `rest.graph_space.delete()` | DELETE | `/graphspaces/{name}` | — |
| `rest.graph_space.delete_default_role()` | DELETE | `/graphspaces/{graphspace}/role` | user, role, graph |
| `rest.graph_space.get()` | GET | `/graphspaces/{graphspace}` | — |
| `rest.graph_space.list()` | GET | `/graphspaces` | — |
| `rest.graph_space.list_profile()` | GET | `/graphspaces/profile` | prefix |
| `rest.graph_space.manage()` | PUT | `/graphspaces/{name}` | — |
| `rest.graph_space.set_default_role()` | POST | `/graphspaces/{graphspace}/role` | — |
| `rest.graph_space_group.create()` | POST | `/graphspaces/{graphspace}/auth/groups` | — |
| `rest.graph_space_group.delete()` | DELETE | `/graphspaces/{graphspace}/auth/groups/{id}` | — |
| `rest.graph_space_group.get()` | GET | `/graphspaces/{graphspace}/auth/groups/{id}` | — |
| `rest.graph_space_group.list()` | GET | `/graphspaces/{graphspace}/auth/groups` | limit |
| `rest.graph_space_group.update()` | PUT | `/graphspaces/{graphspace}/auth/groups/{id}` | — |
| `rest.graphs.clear()` | DELETE | `/graphspaces/{graphspace}/graphs/{name}/clear` | confirm_message |
| `rest.graphs.clone_schema()` | POST | `/graphspaces/{graphspace}/graphs/{name}/schema-clone` | source |
| `rest.graphs.compact()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/compact` | — |
| `rest.graphs.create()` | POST | `/graphspaces/{graphspace}/graphs/{name}` | clone_graph_name |
| `rest.graphs.create_by_text()` | POST | `/graphspaces/{graphspace}/graphs/{name}` | clone_graph_name |
| `rest.graphs.create_snapshot()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/snapshot_create` | — |
| `rest.graphs.drop()` | DELETE | `/graphspaces/{graphspace}/graphs/{name}` | confirm_message |
| `rest.graphs.get()` | GET | `/graphspaces/{graphspace}/graphs/{name}` | — |
| `rest.graphs.get_conf()` | GET | `/graphspaces/{graphspace}/graphs/{name}/conf` | — |
| `rest.graphs.get_default()` | GET | `/graphspaces/{graphspace}/graphs/default` | — |
| `rest.graphs.graph_read_mode_get()` | GET | `/graphspaces/{graphspace}/graphs/{name}/graph_read_mode` | — |
| `rest.graphs.graph_read_mode_set()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/graph_read_mode` | — |
| `rest.graphs.list()` | GET | `/graphspaces/{graphspace}/graphs` | — |
| `rest.graphs.list_profile()` | GET | `/graphspaces/{graphspace}/graphs/profile` | prefix |
| `rest.graphs.loading_mode_get()` | GET | `/graphspaces/{graphspace}/graphs/{name}/mode/owners` | — |
| `rest.graphs.loading_mode_set()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/mode/owners` | — |
| `rest.graphs.manage()` | PUT | `/graphspaces/{graphspace}/graphs/{name}` | — |
| `rest.graphs.mode_get()` | GET | `/graphspaces/{graphspace}/graphs/{name}/mode` | — |
| `rest.graphs.mode_set()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/mode` | — |
| `rest.graphs.reload()` | PUT | `/graphspaces/{graphspace}/graphs/manage` | — |
| `rest.graphs.resume_snapshot()` | PUT | `/graphspaces/{graphspace}/graphs/{name}/snapshot_resume` | — |
| `rest.graphs.set_default()` | POST | `/graphspaces/{graphspace}/graphs/{name}/default` | — |
| `rest.graphs.unset_default()` | DELETE | `/graphspaces/{graphspace}/graphs/{name}/default` | — |
| `rest.gremlin.get()` | GET | `/gremlin` | gremlin, language; additional query map |
| `rest.gremlin.post()` | POST | `/gremlin` | — |
| `rest.gremlin_job.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/jobs/gremlin` | — |
| `rest.group.create()` | POST | `/auth/groups` | — |
| `rest.group.delete()` | DELETE | `/auth/groups/{id}` | — |
| `rest.group.get()` | GET | `/auth/groups/{id}` | — |
| `rest.group.list()` | GET | `/auth/groups` | limit |
| `rest.group.update()` | PUT | `/auth/groups/{id}` | — |
| `rest.index_label.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels` | — |
| `rest.index_label.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels/{name}` | — |
| `rest.index_label.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels/{name}` | — |
| `rest.index_label.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels` | names |
| `rest.index_label.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/schema/indexlabels/{name}` | action |
| `rest.jaccard_similarity.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/jaccardsimilarity` | vertex, other, direction, label, max_degree |
| `rest.jaccard_similarity.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/jaccardsimilarity` | — |
| `rest.kneighbor.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/kneighbor` | source, direction, label, max_depth, count_only, max_degree, limit |
| `rest.kneighbor.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/kneighbor` | — |
| `rest.kout.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/kout` | source, direction, label, max_depth, nearest, count_only, max_degree, capacity, limit |
| `rest.kout.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/kout` | — |
| `rest.login.login()` | POST | `/auth/login` | — |
| `rest.login.logout()` | DELETE | `/auth/logout` | — |
| `rest.login.verify_token()` | GET | `/auth/verify` | — |
| `rest.manager.check_default_role()` | GET | `/graphspaces/{graphspace}/auth/managers/default` | role, graph |
| `rest.manager.check_role()` | GET | `/graphspaces/{graphspace}/auth/managers/check` | type |
| `rest.manager.create_manager()` | POST | `/graphspaces/{graphspace}/auth/managers` | — |
| `rest.manager.delete()` | DELETE | `/graphspaces/{graphspace}/auth/managers` | user, type |
| `rest.manager.get_roles_in_gs()` | GET | `/graphspaces/{graphspace}/auth/managers/role` | user |
| `rest.manager.list()` | GET | `/graphspaces/{graphspace}/auth/managers` | type |
| `rest.metrics.all()` | GET | `/metrics` | type |
| `rest.metrics.backend()` | GET | `/metrics/backend` | — |
| `rest.metrics.counters()` | GET | `/metrics/counters` | — |
| `rest.metrics.gauges()` | GET | `/metrics/gauges` | — |
| `rest.metrics.histograms()` | GET | `/metrics/histograms` | — |
| `rest.metrics.meters()` | GET | `/metrics/meters` | — |
| `rest.metrics.statistics()` | GET | `/metrics/statistics` | type |
| `rest.metrics.system()` | GET | `/metrics/system` | — |
| `rest.metrics.timers()` | GET | `/metrics/timers` | — |
| `rest.multi_node_shortest_path.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/multinodeshortestpath` | — |
| `rest.neighbor_rank.neighbor_rank()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/neighborrank` | — |
| `rest.paths.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/paths` | source, target, direction, label, max_depth, max_degree, capacity, limit |
| `rest.paths.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/paths` | — |
| `rest.personal_rank.personal_rank()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/personalrank` | — |
| `rest.profile.get_profile()` | GET | `/` | — |
| `rest.profile.show_all_apis()` | GET | `/apis` | — |
| `rest.project.create()` | POST | `/graphspaces/{graphspace}/auth/projects` | — |
| `rest.project.delete()` | DELETE | `/graphspaces/{graphspace}/auth/projects/{id}` | — |
| `rest.project.get()` | GET | `/graphspaces/{graphspace}/auth/projects/{id}` | — |
| `rest.project.list()` | GET | `/graphspaces/{graphspace}/auth/projects` | limit |
| `rest.project.update()` | PUT | `/graphspaces/{graphspace}/auth/projects/{id}` | action |
| `rest.property_key.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys` | — |
| `rest.property_key.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys/{name}` | — |
| `rest.property_key.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys/{name}` | — |
| `rest.property_key.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys` | names |
| `rest.property_key.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys/{name}` | action |
| `rest.raft.add_peer()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/raft/add_peer` | group, endpoint |
| `rest.raft.get_leader()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/raft/get_leader` | group |
| `rest.raft.list_peers()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/raft/list_peers` | group |
| `rest.raft.remove_peer()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/raft/remove_peer` | group, endpoint |
| `rest.raft.set_leader()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/raft/set_leader` | group, endpoint |
| `rest.raft.transfer_leader()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/raft/transfer_leader` | group, endpoint |
| `rest.rays.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/rays` | source, direction, label, max_depth, max_degree, capacity, limit, with_vertex, with_edge |
| `rest.rebuild.edge_label_rebuild()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/jobs/rebuild/edgelabels/{name}` | — |
| `rest.rebuild.index_label_rebuild()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/jobs/rebuild/indexlabels/{name}` | — |
| `rest.rebuild.vertex_label_rebuild()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/jobs/rebuild/vertexlabels/{name}` | — |
| `rest.resource_allocation.create()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/resourceallocation` | vertex, other, direction, label, max_degree, limit |
| `rest.rings.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/rings` | source, direction, label, max_depth, source_in_ring, max_degree, capacity, limit, with_vertex, with_edge |
| `rest.same_neighbors.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/sameneighbors` | vertex, other, direction, label, max_degree, limit |
| `rest.same_neighbors.same_neighbors()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/sameneighbors` | — |
| `rest.same_neighbors_batch.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/sameneighborsbatch` | — |
| `rest.schema.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema` | — |
| `rest.schema_template.create()` | POST | `/graphspaces/{graphspace}/schematemplates` | — |
| `rest.schema_template.delete()` | DELETE | `/graphspaces/{graphspace}/schematemplates/{name}` | — |
| `rest.schema_template.get()` | GET | `/graphspaces/{graphspace}/schematemplates/{name}` | — |
| `rest.schema_template.list()` | GET | `/graphspaces/{graphspace}/schematemplates` | — |
| `rest.schema_template.update()` | PUT | `/graphspaces/{graphspace}/schematemplates/{name}` | — |
| `rest.shortest_path.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/shortestpath` | source, target, direction, label, max_depth, max_degree, skip_degree, with_vertex, with_edge, capacity |
| `rest.single_source_shortest_path.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/singlesourceshortestpath` | source, direction, label, weight, max_degree, skip_degree, with_vertex, with_edge, capacity, limit |
| `rest.target.create()` | POST | `/graphspaces/{graphspace}/auth/targets` | — |
| `rest.target.delete()` | DELETE | `/graphspaces/{graphspace}/auth/targets/{id}` | — |
| `rest.target.get()` | GET | `/graphspaces/{graphspace}/auth/targets/{id}` | — |
| `rest.target.list()` | GET | `/graphspaces/{graphspace}/auth/targets` | limit |
| `rest.target.update()` | PUT | `/graphspaces/{graphspace}/auth/targets/{id}` | — |
| `rest.task.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/tasks/{id}` | force |
| `rest.task.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/tasks/{id}` | with_result |
| `rest.task.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/tasks` | status, ids, limit, page |
| `rest.task.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/tasks/{id}` | action |
| `rest.template_paths.post()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/traversers/templatepaths` | — |
| `rest.user.create()` | POST | `/graphspaces/{graphspace}/auth/users` | — |
| `rest.user.delete()` | DELETE | `/graphspaces/{graphspace}/auth/users/{id}` | — |
| `rest.user.get()` | GET | `/graphspaces/{graphspace}/auth/users/{id}` | — |
| `rest.user.list()` | GET | `/graphspaces/{graphspace}/auth/users` | name, limit |
| `rest.user.role()` | GET | `/graphspaces/{graphspace}/auth/users/{id}/role` | — |
| `rest.user.update()` | PUT | `/graphspaces/{graphspace}/auth/users/{id}` | — |
| `rest.variables.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/variables/{key}` | — |
| `rest.variables.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/variables/{key}` | — |
| `rest.variables.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/variables` | — |
| `rest.variables.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/variables/{key}` | — |
| `rest.version.list()` | GET | `/versions` | — |
| `rest.vertex.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices` | — |
| `rest.vertex.create_batch()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/batch` | — |
| `rest.vertex.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/{id}` | label |
| `rest.vertex.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/{id}` | — |
| `rest.vertex.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices` | label, properties, keep_start_p, offset, page, limit |
| `rest.vertex.update_batch()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/batch` | — |
| `rest.vertex.update_by_id()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/graph/vertices/{id}` | action |
| `rest.vertex_label.create()` | POST | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels` | — |
| `rest.vertex_label.delete()` | DELETE | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels/{name}` | — |
| `rest.vertex_label.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels/{name}` | — |
| `rest.vertex_label.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels` | names |
| `rest.vertex_label.update()` | PUT | `/graphspaces/{graphspace}/graphs/{graph}/schema/vertexlabels/{name}` | action |
| `rest.vertices.list()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/vertices` | ids |
| `rest.vertices.scan()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/vertices/scan` | start, end, page, page_limit |
| `rest.vertices.shards()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/vertices/shards` | split_size |
| `rest.weighted_shortest_path.get()` | GET | `/graphspaces/{graphspace}/graphs/{graph}/traversers/weightedshortestpath` | source, target, direction, label, weight, max_degree, skip_degree, with_vertex, with_edge, capacity |
| `rest.white_ip_list.list()` | GET | `/whiteiplist` | — |
| `rest.white_ip_list.update_status()` | PUT | `/whiteiplist` | status |
| `rest.white_ip_list.update_white_ips()` | POST | `/whiteiplist` | — |
{.wide .expand}

<!-- END REST CONTRACT -->

## 异常处理

常见异常定义位于 `pyhugegraph.utils.exceptions`：

| 异常类型 | 触发场景 |
|----------|----------|
| `NotAuthorizedError` | 服务端返回 HTTP 401 未认证 |
| `NotFoundError` | 服务端返回 HTTP 404 资源未找到 |
| `ServerError` | 服务端返回非 2xx 响应（附带服务端错误详情） |
| `ResponseParseError` | 响应内容无法反序列化为预期格式 |
| `ServiceUnavailableError` | 服务端暂时不可用 |
| `InvalidParameterError`, `CreateError`, `RemoveError`, `UpdateError`, `DataFormatError` | 客户端本地参数或格式校验失败 |
{.wide}

敏感参数（密码、Token、密钥等）在日志输出中会自动脱敏处理。

```python
from pyhugegraph.utils.exceptions import NotFoundError

try:
    graph.get_vertex_by_id("missing-id")
except NotFoundError:
    print("未找到指定顶点")
```

## 开发与测试验证

在 HugeGraph-AI 仓库根目录下执行代码规范与测试套件：

1. 代码格式化与静态检查：

   ```bash
   uv run --extra dev ruff format --check .
   uv run --extra dev ruff check .
   uv run --extra dev ty check hugegraph-python-client/src/pyhugegraph
   ```

2. 运行单元测试与契约测试：

   ```bash
   uv run pytest hugegraph-python-client/src/tests -m "unit or contract"
   ```

3. 针对正在运行的 HugeGraph Server 执行集成测试：

   ```bash
   HUGEGRAPH_URL=http://127.0.0.1:8080 \
   HUGEGRAPH_GRAPH=hugegraph \
   HUGEGRAPH_USER=admin \
   HUGEGRAPH_PASSWORD=admin \
   uv run pytest hugegraph-python-client/src/tests -m "integration and hugegraph"
   ```
{.steps}

主线 CI 默认使用 `hugegraph/hugegraph:latest` 镜像进行集成验证，并对 `1.7.0` 执行兼容回归。源码与测试位于 `hugegraph-python-client/src/pyhugegraph/` 和 `hugegraph-python-client/src/tests/`。
