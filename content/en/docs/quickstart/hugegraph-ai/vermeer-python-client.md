---
title: "Vermeer Python Client"
linkTitle: "Vermeer Client"
weight: 6
---

`vermeer-python-client` is the Python SDK for [Vermeer](../computing/hugegraph-vermeer.md), the memory-first graph computing engine written in Go. The SDK wraps the REST API of the Vermeer master so you can list graphs, submit load and compute tasks, and read task state from Python. The import package is `pyvermeer`.

The module does not pin a Vermeer server version. It talks to the Vermeer master over HTTP using the endpoints listed in [API Surface](#api-surface).

## Requirements

- Current source requires Python 3.10 or later because its type annotations use Python 3.10 features, although packaging metadata still declares `>=3.9`.
- A running Vermeer master reachable over HTTP on its default port `6688`. Docker deployments must publish `6688:6688`; see the [Vermeer quick start](../computing/hugegraph-vermeer.md).
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
    port=6688,
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

For a client running on the host, use a master address reachable from that host. For a container client, use its container-network address. The client connects only to the master HTTP API; PD and Store addresses must be reachable from the Vermeer nodes that perform loading.

Behavior worth knowing before you connect:

- `token` may be an empty string when the master does not check authorization, but it cannot be `None`. The session raises `ValueError("Vermeer Token must be provided.")` in that case.
- `timeout` is a `(connect, read)` pair. `VermeerConfig` has its own default of `(0.5, 15.0)`, but the client always forwards its own argument, so omitting `timeout` stores `None` and the request waits without a deadline. Pass the pair explicitly if you want one.
- The base URL is always built as `http://{ip}:{port}/`, so the client speaks plain HTTP.
- Every request sets `Content-Type: application/json` and serializes `params` into the request body, including for `GET` requests.
- The session configures up to 3 retries on HTTP 500, 502, and 504 with backoff factor `0.1`. Status retries follow urllib3's default allowed methods, which exclude `POST`; do not rely on automatic retries for task submission.
- `log_level` sets the level of the shared logger named `VermeerClient`. Its console handler is fixed at `INFO`, so `DEBUG` records are not printed to the console today.

## End-to-End Example

The module ships `vermeer-python-client/src/pyvermeer/demo/task_demo.py`. This extended example polls with a deadline, waits for loading, reads the graph, and submits PageRank. It reads PD peers and the HugeGraph password from environment variables. The worker group must match the task-space allocation; a single-worker quick start can use `worker_group=$`. Bind a named group to the task space first, as shown in the [Vermeer quick start](../computing/hugegraph-vermeer.md).

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

# List tasks on the master
tasks = client.tasks.get_tasks()
print(tasks.to_dict())

# Load graph data from HugeGraph into Vermeer
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


# Wait for loading before reading the graph
wait_task(create_response.task.id, success_state="loaded")

# Inspect the loaded graph
print(client.graph.get_graph("DEFAULT-example").to_dict())

# Submit PageRank on the loaded graph
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

Loading succeeds with `loaded`; computation succeeds with `complete`. `error` or `canceled` stops the example. Set `VERMEER_PD_PEERS` to a JSON array string, for example `export VERMEER_PD_PEERS='["hugegraph-pd:8686"]'`. The master must reach these PD addresses, and workers must reach the Store addresses returned by PD. Set `VERMEER_TOKEN` only if the master uses token authentication; an empty string works without it.

`output.type=local` writes results to the executing worker's local filesystem with file-name prefix `result/pagerank`. Mount its result directory to read container output from the host. `poll_timeout` is the client polling deadline; requests between checks remain subject to HTTP timeouts and SDK retries, so completion can exceed that deadline. A timeout stops client waiting, not the Server task.

Never hardcode a real HugeGraph password into a script or configuration file. Use an environment variable or credential store.

### Save and Run the Documentation Example

Save the complete extended example above as `vermeer_client_example.py` at the `hugegraph-ai/` repository root. Run it with the workspace's `vermeer` extra:

```bash
uv sync --extra vermeer
export VERMEER_PD_PEERS='["hugegraph-pd:8686"]'
read -s -r HUGEGRAPH_PASSWORD
export HUGEGRAPH_PASSWORD
uv run --extra vermeer python vermeer_client_example.py
```

Enter the password and press Enter. Replace `hugegraph-pd:8686` with a PD address reachable from the Vermeer master. If token authentication is enabled, supply `VERMEER_TOKEN` through your local credential-management method. These commands run the extended documentation example, not the bundled demo.

### Original Bundled Demo

`vermeer-python-client/src/pyvermeer/demo/task_demo.py` is a separate minimal example. It hardcodes client port `8688`, PD address `127.0.0.1:8686`, and placeholder credentials `xxx`. It does not read the extended example's environment variables, poll task state, or compute PageRank. Adjust its addresses and credentials separately if running it; it does not replace the documentation commands above.

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
- `TasksResponse.tasks`, `TaskResponse.task`, and `TaskCreateResponse.task` yield `TaskInfo` objects with `id`, `state`, `create_user`, `create_type`, `create_time`, `start_time`, `update_time`, `graph_name`, `space_name`, `params`, `workers`, and `error_message`.
- Timestamps are parsed with `python-dateutil` into `datetime` objects. An empty timestamp string becomes `None`.

Server returns the task type as `task_type`, but SDK `TaskInfo.type` reads `type`, so that property is currently empty. The SDK also drops Server `statistics_result`. Use `TaskInfo.state` for polling. This is a field-contract mismatch in current source.

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

The source lives under `vermeer-python-client/src/pyvermeer/`. A few structure tests are available under `src/tests/structure/test_task_data.py`; they do not cover HTTP API integration.

## References

- [vermeer-python-client on GitHub](https://github.com/apache/hugegraph-ai/tree/main/vermeer-python-client)
- [Vermeer graph computing engine](https://github.com/apache/hugegraph-computer/tree/master/vermeer)
- [Vermeer quick start](../computing/hugegraph-vermeer.md)
- [HugeGraph-AI quick start](./quick_start.md)
