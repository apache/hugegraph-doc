# HugeGraph Python 客户端快速入门

LLMS 索引： [llms.txt](/cn/llms.txt)

---

`hugegraph-python-client` 是 HugeGraph 的 Python SDK，可管理 Schema、读写图数据并执行 Gremlin 查询。HugeGraph-LLM 和 HugeGraph-ML 也使用这个客户端。

## 环境要求

- Python 3.9 或更高版本
- 可访问的 HugeGraph Server
- `uv`（推荐）或 `pip`

## 安装

PyPI 上的包名目前是 `hugegraph-python`：

```bash
uv pip install hugegraph-python
# 也可以使用 pip install hugegraph-python
```

如需使用仓库中的最新代码，请从 HugeGraph-AI 仓库根目录同步 workspace：

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync
source .venv/bin/activate
```

## 连接并写入数据

```python
from pyhugegraph.client import PyHugeClient

client = PyHugeClient(
    "127.0.0.1:8080",
    graph="hugegraph",
    user="admin",
    pwd="admin",
    graphspace="DEFAULT",
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

如果 HugeGraph 没有启用 GraphSpace，可以省略 `graphspace`。启用后请传入实际空间名；默认空间通常是 `DEFAULT`。

## 常用操作

### 查询 Schema

```python
schema = client.schema()
print(schema.getPropertyKeys())
print(schema.getVertexLabels())
print(schema.getEdgeLabels())
print(schema.getIndexLabels())
```

### 更新和删除图数据

图接口直接接收对象属性字典：

```python
graph = client.graph()
graph.appendVertex(person.id, {"birthDate": "1940-04-25"})
graph.removeEdgeById(edge.id)
graph.removeVertexById(person.id)
graph.close()
```

### 执行 Gremlin

```python
gremlin = client.gremlin()
result = gremlin.exec("g.V().limit(5)")
print(result)
```

接口参数会随 HugeGraph REST API 版本变化。遇到不兼容时，先核对当前 Server 的 REST API 文档与客户端测试用例。

## 开发检查

在 HugeGraph-AI 仓库根目录运行格式与静态检查：

```bash
./style/code_format_and_analysis.sh
```

源码与测试位于 `hugegraph-python-client/src/pyhugegraph/` 和 `hugegraph-python-client/src/tests/`。
