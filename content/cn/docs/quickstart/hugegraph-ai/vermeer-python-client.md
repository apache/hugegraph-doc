---
title: "Vermeer Python 客户端"
linkTitle: "Vermeer 客户端"
weight: 6
---

`vermeer-python-client` 是 [Vermeer](../computing/hugegraph-vermeer.md) 的 Python SDK。Vermeer 是使用 Go 编写、以内存计算为主的图计算引擎。该 SDK 封装了 Vermeer master 的 REST API，可以在 Python 中列出图、提交加载和计算任务、读取任务状态。导入时使用的包名是 `pyvermeer`。

模块没有固定 Vermeer 服务端版本，它通过 HTTP 访问 Vermeer master，调用的接口见 [API 概览](#api-概览)。

## 环境要求

- 当前源码实际要求 Python 3.10 或更高版本；虽然该模块打包元数据声明 `>=3.9`，代码中的类型标注使用了 Python 3.10 语法
- 一个可通过 HTTP 访问的 Vermeer master。默认 HTTP 端口为 `6688`；Docker 部署需发布 `6688:6688`，见 [Vermeer 快速开始](../computing/hugegraph-vermeer.md)。
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
    port=6688,
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

如果 Python 客户端运行在宿主机，`ip` 填宿主机可访问的 master 地址；如果运行在容器中，则填容器网络内的 master 地址。客户端只连接 master 的 HTTP API，HugeGraph PD/Store 地址则必须能由执行加载任务的 Vermeer 节点访问。

连接前需要了解的行为：

- 当 master 不校验鉴权时，`token` 可以是空字符串，但不能是 `None`，否则会话会抛出 `ValueError("Vermeer Token must be provided.")`。
- `timeout` 是 `(连接超时, 读取超时)` 二元组。`VermeerConfig` 自身的默认值是 `(0.5, 15.0)`，但客户端总是把自己的参数传下去，因此不传 `timeout` 时实际存入的是 `None`，请求会一直等待。需要超时就显式传入该二元组。
- 基础 URL 固定拼接为 `http://{ip}:{port}/`，即客户端只使用明文 HTTP。
- 每个请求都会设置 `Content-Type: application/json`，并把 `params` 序列化进请求体，`GET` 请求也是如此。
- 底层会话配置了对 HTTP 500、502、504 的最多 3 次重试和 `0.1` 的退避系数；状态码重试遵循 urllib3 默认允许的方法，`POST` 不在其中，因此不能依赖它自动重试任务提交。
- `log_level` 设置的是名为 `VermeerClient` 的共享日志器的级别。它的控制台 handler 固定为 `INFO`，因此目前 `DEBUG` 级别的记录不会打印到控制台。

## 端到端示例

模块自带一个可运行的示例：`vermeer-python-client/src/pyvermeer/demo/task_demo.py`。下面的版本在其基础上增加了有截止时间的任务轮询，先等待加载成功、再读取图并提交 PageRank 计算；PD 地址和 HugeGraph 密码从环境变量读取。服务端 worker group 也必须与任务空间的分配匹配；单 worker 快速开始可将 `worker_group` 设为 `$`，保留命名组时先按 [Vermeer 快速开始](../computing/hugegraph-vermeer.md) 将该组绑定到任务空间。

```python
import os
import time

from pyvermeer.client.client import PyVermeerClient
from pyvermeer.structure.task_data import TaskCreateRequest

client = PyVermeerClient(
    ip="127.0.0.1",
    port=6688,
    token=os.getenv("VERMEER_TOKEN", ""),
    timeout=(0.5, 15.0),
    log_level="INFO",
)

# 列出 master 上的任务
tasks = client.tasks.get_tasks()
print(tasks.to_dict())

# 从 HugeGraph 把图数据加载到 Vermeer
create_response = client.tasks.create_task(
    create_task=TaskCreateRequest(
        task_type="load",
        graph_name="DEFAULT-example",
        params={
            "load.hg_pd_peers": os.environ["VERMEER_PD_PEERS"],
            "load.hugegraph_name": "DEFAULT/example/g",
            "load.hugegraph_username": "admin",
            "load.hugegraph_password": os.environ["HUGEGRAPH_PASSWORD"],
            "load.parallel": "10",
            "load.type": "hugegraph",
        },
    )
)
print(create_response.errcode, create_response.message)
if create_response.errcode != 0:
    raise RuntimeError(f"Could not create load task: {create_response.message}")

def wait_task(task_id, success_state, poll_timeout=300.0):
    deadline = time.monotonic() + poll_timeout
    while True:
        response = client.tasks.get_task(task_id)
        if response.errcode != 0:
            raise RuntimeError(f"Could not read task {task_id}: {response.message}")
        task = response.task
        print(task_id, task.state)
        if task.state == success_state:
            return task
        if task.state in ("error", "canceled"):
            raise RuntimeError(f"Task {task_id} ended with state {task.state}")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"Task {task_id} did not finish within {poll_timeout}s")
        time.sleep(min(1.0, remaining))


# 等待加载完成后再读取图
wait_task(create_response.task.id, success_state="loaded")

# 图加载完成后查看图信息
print(client.graph.get_graph("DEFAULT-example").to_dict())

# 在已加载的图上提交 PageRank 计算
compute_response = client.tasks.create_task(
    create_task=TaskCreateRequest(
        task_type="compute",
        graph_name="DEFAULT-example",
        params={
            "compute.algorithm": "pagerank",
            "compute.parallel": "10",
            "compute.max_step": "10",
            "output.type": "local",
            "output.parallel": "1",
            "output.file_path": "result/pagerank",
        },
    )
)
if compute_response.errcode != 0:
    raise RuntimeError(f"Could not create compute task: {compute_response.message}")
wait_task(compute_response.task.id, success_state="complete")
```

加载任务以 `loaded` 表示成功，计算任务以 `complete` 表示成功；`error` 或 `canceled` 会中止示例。运行前设置 `VERMEER_PD_PEERS`，其值是 JSON 数组字符串，例如 `export VERMEER_PD_PEERS='["hugegraph-pd:8686"]'`；其中地址必须能由 Vermeer master 访问，PD 返回的 Store 地址也必须能由 worker 访问。只有 master 配置为 token 鉴权时才设置 `VERMEER_TOKEN`；不启用鉴权时空字符串可用。

示例的 `output.type=local` 会把结果写到执行任务的 worker 本地文件系统，文件名以 `result/pagerank` 为前缀。容器部署时需把 worker 的结果目录挂载出来才能从宿主机读取。`poll_timeout` 是客户端轮询截止时间；检查期限之间的请求仍受 HTTP 超时和 SDK 重试影响，因此实际结束时间可能越过该值。超时只停止客户端等待，不会取消服务端任务。

不要把真实的 HugeGraph 密码写死在脚本或配置文件中，请像上面这样从环境变量或凭据管理系统读取。

### 保存并运行文档中的端到端示例

将上方完整的增强示例代码保存为 `vermeer_client_example.py`，放在 `hugegraph-ai/` 仓库根目录。在该目录使用已安装 `vermeer` extra 的 workspace 环境运行：

```bash
uv sync --extra vermeer
export VERMEER_PD_PEERS='["hugegraph-pd:8686"]'
read -s -r HUGEGRAPH_PASSWORD
export HUGEGRAPH_PASSWORD
uv run --extra vermeer python vermeer_client_example.py
```

输入密码后按回车。将 `hugegraph-pd:8686` 替换为 Vermeer master 可访问的 PD 地址；若 master 启用了 token 鉴权，还要从本机凭据管理方式设置 `VERMEER_TOKEN`。上述命令运行的是文档增强示例，不是包内原始 demo。

### 包内原始 demo

`vermeer-python-client/src/pyvermeer/demo/task_demo.py` 是另一份精简示例：它把客户端端口写为 `8688`，把 PD 地址写为 `127.0.0.1:8686`，并使用 `xxx` 占位用户名和密码。它不会读取本页增强示例使用的环境变量，也没有任务状态轮询或 PageRank 计算。若运行该文件，需单独调整其中的服务地址和 HugeGraph 凭据；不能用它替代上面的文档示例命令。

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
- `TasksResponse.tasks`、`TaskResponse.task` 和 `TaskCreateResponse.task` 返回 `TaskInfo` 对象，SDK 读取 `id`、`state`、`create_user`、`create_type`、`create_time`、`start_time`、`update_time`、`graph_name`、`space_name`、`params`、`workers` 和 `error_message`。
- 时间字段由 `python-dateutil` 解析为 `datetime` 对象，空字符串会解析为 `None`。

当前服务端以 `task_type` 返回任务类型，而 SDK 的 `TaskInfo.type` 按 `type` 读取，因此该属性目前为空；服务端还返回的 `statistics_result` 不会被 SDK 的 `TaskInfo` 保留。轮询状态请使用 `TaskInfo.state`。这是当前源码的字段契约差异。

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

源码位于 `vermeer-python-client/src/pyvermeer/`。目前有少量 `src/tests/structure/test_task_data.py` 结构测试，没有覆盖 HTTP API 的集成测试。

## 参考

- [GitHub 上的 vermeer-python-client](https://github.com/apache/hugegraph-ai/tree/main/vermeer-python-client)
- [Vermeer 图计算引擎](https://github.com/apache/hugegraph-computer/tree/master/vermeer)
- [Vermeer 快速开始](../computing/hugegraph-vermeer.md)
- [HugeGraph-AI 快速开始](./quick_start.md)
