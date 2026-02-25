---
title: "HugeGraph Python 客户端快速入门"
linkTitle: "Python 客户端"
weight: 2
---

`hugegraph-python-client` 是 HugeGraph 图数据库的 Python 客户端/SDK。

它用于定义图结构、对图数据执行 CRUD 操作、管理 Schema 以及执行 Gremlin 查询。`hugegraph-llm` 和 `hugegraph-ml` 模块都依赖于这个基础库。

## 安装

### 安装已发布的包（稳定版）

要安装 `hugegraph-python-client`，您可以使用 uv/pip 或从源码构建：

```bash
# uv 是可选的，您可以直接使用 pip
uv pip install hugegraph-python # 注意：可能不是最新版本，建议从源码安装
# WIP：我们很快会将 'hugegraph-python-client' 作为包名
```

### 从源码安装（最新代码）

要从源码安装，请克隆仓库并安装所需的依赖项：

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/hugegraph-python-client

# 普通安装
uv pip install .

# (可选) 安装开发版本
uv pip install -e .
```

## 使用示例

### 定义图结构

您可以使用 `hugegraph-python-client` 来定义图结构。以下是如何定义图的示例：

```python
from pyhugegraph.client import PyHugeClient

# 初始化客户端
# 对于 HugeGraph API 版本 ≥ v3：（或启用 graphspace 功能）
# - 如果启用了 graphspace，则 'graphspace' 参数变得相关（默认名称为 'DEFAULT'）
# - 否则，graphspace 参数是可选的，可以忽略。
client = PyHugeClient("127.0.0.1", "8080", user="admin", pwd="admin", graph="hugegraph", graphspace="DEFAULT")

""""
注意：
可以参考您 HugeGraph 版本的官方 REST-API 文档以获取准确的详细信息。
如果某些 API 与预期不符，请提交 issue 或联系我们。
"""
schema = client.schema()
schema.propertyKey("name").asText().ifNotExist().create()
schema.propertyKey("birthDate").asText().ifNotExist().create()
schema.vertexLabel("Person").properties("name", "birthDate").usePrimaryKeyId().primaryKeys("name").ifNotExist().create()
schema.vertexLabel("Movie").properties("name").usePrimaryKeyId().primaryKeys("name").ifNotExist().create()
schema.edgeLabel("ActedIn").sourceLabel("Person").targetLabel("Movie").ifNotExist().create()

print(schema.getVertexLabels())
print(schema.getEdgeLabels())
print(schema.getRelations())

# 初始化图
g = client.graph()
v_al_pacino = g.addVertex("Person", {"name": "Al Pacino", "birthDate": "1940-04-25"})
v_robert = g.addVertex("Person", {"name": "Robert De Niro", "birthDate": "1943-08-17"})
v_godfather = g.addVertex("Movie", {"name": "The Godfather"})
v_godfather2 = g.addVertex("Movie", {"name": "The Godfather Part II"})
v_godfather3 = g.addVertex("Movie", {"name": "The Godfather Coda The Death of Michael Corleone"})

g.addEdge("ActedIn", v_al_pacino.id, v_godfather.id, {})
g.addEdge("ActedIn", v_al_pacino.id, v_godfather2.id, {})
g.addEdge("ActedIn", v_al_pacino.id, v_godfather3.id, {})
g.addEdge("ActedIn", v_robert.id, v_godfather2.id, {})

res = g.getVertexById(v_al_pacino.id).label
print(res)
g.close()
```

### Schema 管理

`hugegraph-python-client` 提供了全面的 Schema 管理功能。

#### 定义属性键 (Property Key)

```python
# 定义属性键
client.schema().propertyKey('name').dataType('STRING').cardinality('SINGLE').create()
```

#### 定义顶点标签 (Vertex Label)

```python
# 定义顶点标签
client.schema().vertexLabel('person').properties('name', 'age').primaryKeys('name').create()
```

#### 定义边标签 (Edge Label)

```python
# 定义边标签
client.schema().edgeLabel('knows').sourceLabel('person').targetLabel('person').properties('since').create()
```

#### 定义索引标签 (Index Label)

```python
# 定义索引标签
client.schema().indexLabel('personByName').onV('person').by('name').secondary().create()
```

### CRUD 操作

客户端允许您对图数据执行 CRUD 操作。以下是如何创建、读取、更新和删除顶点和边的示例：

#### 创建顶点和边

```python
# 创建顶点
v1 = client.graph().addVertex('person').property('name', 'John').property('age', 29).create()
v2 = client.graph().addVertex('person').property('name', 'Jane').property('age', 25).create()

# 创建边
client.graph().addEdge(v1, 'knows', v2).property('since', '2020').create()
```

#### 读取顶点和边

```python
# 通过 ID 获取顶点
vertex = client.graph().getVertexById(v1.id)
print(vertex)

# 通过 ID 获取边
edge = client.graph().getEdgeById(edge.id) # 假设 edge 对象已定义并有 id 属性
print(edge)
```

#### 更新顶点和边

```python
# 更新顶点
client.graph().updateVertex(v1.id).property('age', 30).update()

# 更新边
client.graph().updateEdge(edge.id).property('since', '2021').update() # 假设 edge 对象已定义并有 id 属性
```

#### 删除顶点和边

```python
# 删除顶点
client.graph().deleteVertex(v1.id)

# 删除边
client.graph().deleteEdge(edge.id) # 假设 edge 对象已定义并有 id 属性
```

### 执行 Gremlin 查询

客户端还支持执行 Gremlin 查询：

```python
# 执行 Gremlin 查询
g = client.gremlin()
res = g.exec("g.V().limit(5)")
print(res)
```

其他信息正在建设中 🚧 (欢迎为此添加更多文档，用户可以参考 [java-client-doc](https://hugegraph.apache.org/docs/clients/hugegraph-client/) 获取类似用法)

## API 文档参考

<!-- 可以在此部分添加指向更详细 API 文档的链接 -->

## 贡献

* 欢迎为 `hugegraph-python-client` 做出贡献。请参阅 [贡献指南](https://hugegraph.apache.org/docs/contribution-guidelines/) 获取更多信息。
* 代码格式：请在提交 PR 前运行 `./style/code_format_and_analysis.sh` 来格式化您的代码。

感谢所有已经为 `hugegraph-python-client` 做出贡献的人！
