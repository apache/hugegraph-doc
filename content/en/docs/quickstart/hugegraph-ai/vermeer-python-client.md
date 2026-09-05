---
title: "Vermeer Python Client"
linkTitle: "Vermeer Client"
weight: 6
---

`vermeer-python-client` is the Python SDK for [Vermeer](../computing/hugegraph-vermeer.md), the memory-first graph computing engine written in Go. The SDK wraps the REST API of the Vermeer master so you can list graphs, submit load and compute tasks, and read task state from Python. The import package is `pyvermeer`.

The module does not pin a Vermeer server version. It talks to the Vermeer master over HTTP using the endpoints listed in [API Surface](#api-surface).

## Requirements

- Python 3.9 or later for the module on its own. The HugeGraph-AI repository as a whole requires Python 3.10 or later.
- A running Vermeer master reachable over HTTP. The demo shipped with the module uses port `8688`.
- `uv` (recommended) or `pip`

Runtime dependencies: `requests`, `urllib3`, `python-dateutil`, `decorator`, `rich`, and `setuptools`.

## Installation

The distribution name in the packaging metadata is `vermeer-python-client` and the version is managed independently of the repository version. The package is not published on PyPI yet, so install it from source.

From the root of the HugeGraph-AI repository, the `vermeer` extra installs it into the shared virtual environment:

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra vermeer
source .venv/bin/activate
```

`vermeer-python-client` is wired in as an editable path dependency rather than a `uv` workspace member, so a plain `uv sync` at the repository root does not install it. You have to ask for the extra (or for `--all-extras`).

To install the module standalone:

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/vermeer-python-client
uv sync
source .venv/bin/activate
```

## Connect to a Vermeer Master

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

Constructor parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ip` | `str` | required | Host name or IP address of the Vermeer master |
| `port` | `int` | required | REST port of the Vermeer master |
| `token` | `str` | required | Sent verbatim as the `Authorization` request header |
| `timeout` | `(float, float)` or `None` | `None` | Connect and read timeouts in seconds |
| `log_level` | `str` | `"INFO"` | Level applied to the shared `VermeerClient` logger |

Behavior worth knowing before you connect:

- `token` may be an empty string when the master does not check authorization, but it cannot be `None`. The session raises `ValueError("Vermeer Token must be provided.")` in that case.
- `timeout` is a `(connect, read)` pair. `VermeerConfig` has its own default of `(0.5, 15.0)`, but the client always forwards its own argument, so omitting `timeout` stores `None` and the request waits without a deadline. Pass the pair explicitly if you want one.
- The base URL is always built as `http://{ip}:{port}/`, so the client speaks plain HTTP.
- Every request sets `Content-Type: application/json` and serializes `params` into the request body, including for `GET` requests.
- The underlying session retries up to 3 times with a backoff factor of `0.1` on HTTP 500, 502, and 504.
- `log_level` sets the level of the shared logger named `VermeerClient`. Its console handler is fixed at `INFO`, so `DEBUG` records are not printed to the console today.

## End-to-End Example

The module ships a runnable demo at `vermeer-python-client/src/pyvermeer/demo/task_demo.py`. The version below adds the polling step and reads the HugeGraph password from the environment:

```python
import os

from pyvermeer.client.client import PyVermeerClient
from pyvermeer.structure.task_data import TaskCreateRequest

client = PyVermeerClient(ip="127.0.0.1", port=8688, token="", log_level="INFO")

# List the tasks the master knows about
tasks = client.tasks.get_tasks()
print(tasks.to_dict())

# Load a graph from HugeGraph into Vermeer
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

# Read the task back and check its state
task_id = create_response.task.id
task = client.tasks.get_task(task_id)
print(task.task.state)

# Once the graph is loaded, inspect it
print(client.graph.get_graph("DEFAULT-example").to_dict())
```

Never hardcode a real HugeGraph password into a script or a configuration file. Read it from an environment variable or a credential store, as above.

After installing the module you can also run the shipped demo as is:

```bash
python vermeer-python-client/src/pyvermeer/demo/task_demo.py
```

## API Surface

`PyVermeerClient` exposes its API groups as attributes. Two groups are registered today, `graph` and `tasks`.

### client.graph

| Method | Vermeer endpoint | Returns |
|---|---|---|
| `get_graphs()` | `GET /graphs` | `GraphsResponse` |
| `get_graph(graph_name)` | `GET /graphs/{graph_name}` | `GraphResponse` |

### client.tasks

| Method | Vermeer endpoint | Returns |
|---|---|---|
| `get_tasks()` | `GET /tasks` | `TasksResponse` |
| `get_task(task_id)` | `GET /task/{task_id}` | `TaskResponse` |
| `create_task(create_task)` | `POST /tasks/create` | `TaskCreateResponse` |

`pyvermeer/api/master.py` and `pyvermeer/api/worker.py` contain only the license header, and neither group is registered on the client. Master and worker information is therefore not reachable from the client yet, even though `MasterResponse` and `WorkersResponse` already exist under `pyvermeer/structure/`.

`client.send_request(method, endpoint, params)` is the shared entry point behind both groups. You can call it directly to reach a Vermeer endpoint that has no wrapper yet; it returns the decoded JSON body as a plain `dict`.

### Requests and Responses

`TaskCreateRequest(task_type, graph_name, params)` is serialized as `{"task_type": ..., "graph": ..., "params": ...}`. Note that `graph_name` becomes `graph` on the wire, which matches the payload documented for the Vermeer REST API.

Every response type extends `BaseResponse` and exposes `errcode` and `message`, plus a `to_dict()` helper. `errcode` is `0` on success and `1` on error; `-1` means the field was missing from the response body.

- `GraphsResponse.graphs` and `GraphResponse.graph` yield `VermeerGraph` objects with `name`, `space_name`, `status`, `create_time`, `update_time`, `vertex_count`, `edge_count`, `workers`, `worker_group`, `use_out_edges`, `use_property`, `use_out_degree`, `use_undirected`, `on_disk`, and `backend_option`.
- `TasksResponse.tasks`, `TaskResponse.task`, and `TaskCreateResponse.task` yield `TaskInfo` objects with `id`, `state`, `create_user`, `create_type`, `create_time`, `start_time`, `update_time`, `graph_name`, `space_name`, `type`, `params`, and `workers`.
- Timestamps are parsed with `python-dateutil` into `datetime` objects. An empty timestamp string becomes `None`.

### Task Parameters

The client does not validate `params`. Keys and values are passed straight through to Vermeer, so the accepted names come from the engine, not from the SDK. For the load parameters and the parameters of the supported algorithms, see the [Vermeer quick start](../computing/hugegraph-vermeer.md).

The usual sequence is the same as with the REST API directly: create a `load` task to read the graph into Vermeer, wait for it to finish, then create computation tasks against the loaded graph.

### Errors

`pyvermeer.utils.exception` defines four exceptions, all raised from the underlying `requests` or JSON failure:

| Exception | Raised when |
|---|---|
| `ConnectError` | `requests.ConnectionError`, the master is unreachable |
| `TimeOutError` | `requests.Timeout`, the connect or read deadline expired |
| `JsonDecodeError` | The response body is not valid JSON |
| `UnknownError` | Any other failure during the request |

```python
from pyvermeer.utils.exception import ConnectError, TimeOutError

try:
    graphs = client.graph.get_graphs()
except (ConnectError, TimeOutError) as error:
    print(error)
```

The client does not check the HTTP status code of the response, so inspect `errcode` and `message` on the returned object to tell success from a Vermeer-side error.

## Development Checks

Run the formatting and static checks from the root of the HugeGraph-AI repository:

```bash
./style/code_format_and_analysis.sh
```

The source lives under `vermeer-python-client/src/pyvermeer/`. The module currently ships no test suite.

## References

- [vermeer-python-client on GitHub](https://github.com/apache/hugegraph-ai/tree/main/vermeer-python-client)
- [Vermeer graph computing engine](https://github.com/apache/hugegraph-computer/tree/master/vermeer)
- [Vermeer quick start](../computing/hugegraph-vermeer.md)
- [HugeGraph-AI quick start](./quick_start.md)
