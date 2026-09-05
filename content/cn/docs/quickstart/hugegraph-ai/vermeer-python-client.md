---
title: "Vermeer Python 客户端"
linkTitle: "Vermeer 客户端"
weight: 6
---

`vermeer-python-client` 是 [Vermeer](../computing/hugegraph-vermeer.md) 的 Python SDK。Vermeer 是使用 Go 编写、以内存计算为主的图计算引擎。该 SDK 封装了 Vermeer master 的 REST API，可以在 Python 中列出图、提交加载和计算任务、读取任务状态。导入时使用的包名是 `pyvermeer`。

模块没有固定 Vermeer 服务端版本，它通过 HTTP 访问 Vermeer master，调用的接口见 [API 概览](#api-概览)。

## 环境要求

- 单独使用该模块需要 Python 3.9 或更高版本；HugeGraph-AI 仓库整体要求 Python 3.10 或更高版本
- 一个可通过 HTTP 访问的 Vermeer master。模块自带的示例使用端口 `8688`
- `uv`（推荐）或 `pip`

运行时依赖：`requests`、`urllib3`、`python-dateutil`、`decorator`、`rich` 和 `setuptools`。

## 安装

打包元数据中的发行包名是 `vermeer-python-client`，其版本号独立于仓库版本号管理。该包尚未发布到 PyPI，请从源码安装。

在 HugeGraph-AI 仓库根目录，使用 `vermeer` extra 把它安装到共用的虚拟环境中：

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra vermeer
source .venv/bin/activate
```

`vermeer-python-client` 是以可编辑路径依赖的方式接入的，并不是 `uv` workspace member，因此在仓库根目录直接执行 `uv sync` 不会安装它，必须显式指定该 extra（或使用 `--all-extras`）。

单独安装该模块：

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/vermeer-python-client
uv sync
source .venv/bin/activate
```

## 连接 Vermeer master

```python
from pyvermeer.client.client import PyVermeerClient

client = PyVermeerClient(
    ip="127.0.0.1",
    port=8688,
    token="",
    timeout=(0.5, 15.0),
    log_level="INFO",
)
```

构造函数参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `ip` | `str` | 必填 | Vermeer master 的主机名或 IP 地址 |
| `port` | `int` | 必填 | Vermeer master 的 REST 端口 |
| `token` | `str` | 必填 | 原样作为 `Authorization` 请求头发送 |
| `timeout` | `(float, float)` 或 `None` | `None` | 连接超时和读取超时，单位为秒 |
| `log_level` | `str` | `"INFO"` | 应用到共享 `VermeerClient` 日志器的级别 |

连接前需要了解的行为：

- 当 master 不校验鉴权时，`token` 可以是空字符串，但不能是 `None`，否则会话会抛出 `ValueError("Vermeer Token must be provided.")`。
- `timeout` 是 `(连接超时, 读取超时)` 二元组。`VermeerConfig` 自身的默认值是 `(0.5, 15.0)`，但客户端总是把自己的参数传下去，因此不传 `timeout` 时实际存入的是 `None`，请求会一直等待。需要超时就显式传入该二元组。
- 基础 URL 固定拼接为 `http://{ip}:{port}/`，即客户端只使用明文 HTTP。
- 每个请求都会设置 `Content-Type: application/json`，并把 `params` 序列化进请求体，`GET` 请求也是如此。
- 底层会话在 HTTP 500、502、504 时最多重试 3 次，退避系数为 `0.1`。
- `log_level` 设置的是名为 `VermeerClient` 的共享日志器的级别。它的控制台 handler 固定为 `INFO`，因此目前 `DEBUG` 级别的记录不会打印到控制台。

## 端到端示例

模块自带一个可运行的示例：`vermeer-python-client/src/pyvermeer/demo/task_demo.py`。下面的版本在其基础上增加了任务状态查询，并从环境变量读取 HugeGraph 密码：

```python
import os

from pyvermeer.client.client import PyVermeerClient
from pyvermeer.structure.task_data import TaskCreateRequest

client = PyVermeerClient(ip="127.0.0.1", port=8688, token="", log_level="INFO")

# 列出 master 上的任务
tasks = client.tasks.get_tasks()
print(tasks.to_dict())

# 从 HugeGraph 把图数据加载到 Vermeer
create_response = client.tasks.create_task(
    create_task=TaskCreateRequest(
        task_type="load",
        graph_name="DEFAULT-example",
        params={
            "load.hg_pd_peers": '["127.0.0.1:8686"]',
            "load.hugegraph_name": "DEFAULT/example/g",
            "load.hugegraph_username": "admin",
            "load.hugegraph_password": os.environ["HUGEGRAPH_PASSWORD"],
            "load.parallel": "10",
            "load.type": "hugegraph",
        },
    )
)
print(create_response.errcode, create_response.message)

# 回查任务并读取状态
task_id = create_response.task.id
task = client.tasks.get_task(task_id)
print(task.task.state)

# 图加载完成后查看图信息
print(client.graph.get_graph("DEFAULT-example").to_dict())
```

不要把真实的 HugeGraph 密码写死在脚本或配置文件中，请像上面这样从环境变量或凭据管理系统读取。

安装模块后，也可以直接运行自带的示例：

```bash
python vermeer-python-client/src/pyvermeer/demo/task_demo.py
```

## API 概览

`PyVermeerClient` 以属性的方式暴露各个 API 组，目前注册了 `graph` 和 `tasks` 两个组。

### client.graph

| 方法 | Vermeer 接口 | 返回值 |
|---|---|---|
| `get_graphs()` | `GET /graphs` | `GraphsResponse` |
| `get_graph(graph_name)` | `GET /graphs/{graph_name}` | `GraphResponse` |

### client.tasks

| 方法 | Vermeer 接口 | 返回值 |
|---|---|---|
| `get_tasks()` | `GET /tasks` | `TasksResponse` |
| `get_task(task_id)` | `GET /task/{task_id}` | `TaskResponse` |
| `create_task(create_task)` | `POST /tasks/create` | `TaskCreateResponse` |

`pyvermeer/api/master.py` 和 `pyvermeer/api/worker.py` 目前只有许可证头，也没有注册到客户端上。因此尽管 `pyvermeer/structure/` 下已经有 `MasterResponse` 和 `WorkersResponse`，master 和 worker 信息暂时还无法通过客户端获取。

`client.send_request(method, endpoint, params)` 是这两个组共用的请求入口。对于还没有封装的 Vermeer 接口，可以直接调用它，返回值是解析后的 JSON 字典。

### 请求与响应对象

`TaskCreateRequest(task_type, graph_name, params)` 序列化为 `{"task_type": ..., "graph": ..., "params": ...}`。注意 `graph_name` 在报文中的字段名是 `graph`，与 Vermeer REST API 的请求体一致。

所有响应类型都继承 `BaseResponse`，提供 `errcode`、`message` 属性和 `to_dict()` 方法。`errcode` 为 `0` 表示成功，`1` 表示错误，`-1` 表示响应体中没有该字段。

- `GraphsResponse.graphs` 和 `GraphResponse.graph` 返回 `VermeerGraph` 对象，包含 `name`、`space_name`、`status`、`create_time`、`update_time`、`vertex_count`、`edge_count`、`workers`、`worker_group`、`use_out_edges`、`use_property`、`use_out_degree`、`use_undirected`、`on_disk` 和 `backend_option`。
- `TasksResponse.tasks`、`TaskResponse.task` 和 `TaskCreateResponse.task` 返回 `TaskInfo` 对象，包含 `id`、`state`、`create_user`、`create_type`、`create_time`、`start_time`、`update_time`、`graph_name`、`space_name`、`type`、`params` 和 `workers`。
- 时间字段由 `python-dateutil` 解析为 `datetime` 对象，空字符串会解析为 `None`。

### 任务参数

客户端不会校验 `params`，键和值都会原样传给 Vermeer，因此可用的参数名由引擎决定，而不是由 SDK 决定。加载参数以及各算法的参数请参考 [Vermeer 快速开始](../computing/hugegraph-vermeer.md)。

使用流程与直接调用 REST API 相同：先创建 `load` 任务把图读入 Vermeer，等待任务完成，再针对已加载的图创建计算任务。

### 异常

`pyvermeer.utils.exception` 定义了四种异常，都由底层的 `requests` 或 JSON 解析失败包装而来：

| 异常 | 触发场景 |
|---|---|
| `ConnectError` | `requests.ConnectionError`，无法连接 master |
| `TimeOutError` | `requests.Timeout`，连接或读取超时 |
| `JsonDecodeError` | 响应体不是合法的 JSON |
| `UnknownError` | 请求过程中的其他失败 |

```python
from pyvermeer.utils.exception import ConnectError, TimeOutError

try:
    graphs = client.graph.get_graphs()
except (ConnectError, TimeOutError) as error:
    print(error)
```

客户端不检查响应的 HTTP 状态码，请通过返回对象的 `errcode` 和 `message` 判断是成功还是 Vermeer 端返回了错误。

## 代码检查

在 HugeGraph-AI 仓库根目录执行格式化和静态检查：

```bash
./style/code_format_and_analysis.sh
```

源码位于 `vermeer-python-client/src/pyvermeer/`。该模块目前没有测试用例。

## 参考

- [GitHub 上的 vermeer-python-client](https://github.com/apache/hugegraph-ai/tree/main/vermeer-python-client)
- [Vermeer 图计算引擎](https://github.com/apache/hugegraph-computer/tree/master/vermeer)
- [Vermeer 快速开始](../computing/hugegraph-vermeer.md)
- [HugeGraph-AI 快速开始](./quick_start.md)
