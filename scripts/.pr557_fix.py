import json
import re
from pathlib import Path

SDK = {
    "en": Path("content/en/docs/quickstart/hugegraph-ai/hugegraph-llm-sdk.md"),
    "cn": Path("content/cn/docs/quickstart/hugegraph-ai/hugegraph-llm-sdk.md"),
}
VERMEER = {
    "en": Path("content/en/docs/quickstart/computing/hugegraph-vermeer.md"),
    "cn": Path("content/cn/docs/quickstart/computing/hugegraph-vermeer.md"),
}
ROUTES = Path("data/version_routes.json")
NAV = Path("data/docs_nav.json")


def sub1(text, pattern, replacement, label):
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.S | re.M)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 replacement, got {count}")
    return text


install = {
    "en": """### Install from source or a local wheel

The SDK is currently provided by the `hugegraph-ai` source tree and has not yet been published to a public package index. Install it from a checkout or a locally built wheel.

```bash
pip install -e /path/to/hugegraph-ai/hugegraph-llm-sdk
# or
uv add --editable /path/to/hugegraph-ai/hugegraph-llm-sdk

uv build --no-sources /path/to/hugegraph-ai/hugegraph-llm-sdk --out-dir /tmp/llm-sdk-dist
pip install /tmp/llm-sdk-dist/hugegraph_llm_sdk-1.8.0-py3-none-any.whl
```

### Provider Extras

Install provider extras from the same checkout:

```bash
pip install -e \"/path/to/hugegraph-ai/hugegraph-llm-sdk[openai]\"
pip install -e \"/path/to/hugegraph-ai/hugegraph-llm-sdk[ollama]\"
pip install -e \"/path/to/hugegraph-ai/hugegraph-llm-sdk[litellm]\"
# uv example: uv add --editable /path/to/hugegraph-ai/hugegraph-llm-sdk --extra openai
```
""",
    "cn": """### 从源码或本地 wheel 安装

当前 SDK 随 `hugegraph-ai` 源码提供，尚未发布到公共软件包索引。请从本地源码目录或自行构建的 wheel 安装。

```bash
pip install -e /path/to/hugegraph-ai/hugegraph-llm-sdk
# 或
uv add --editable /path/to/hugegraph-ai/hugegraph-llm-sdk

uv build --no-sources /path/to/hugegraph-ai/hugegraph-llm-sdk --out-dir /tmp/llm-sdk-dist
pip install /tmp/llm-sdk-dist/hugegraph_llm_sdk-1.8.0-py3-none-any.whl
```

### 模型厂商适配器（Extras）

请从同一源码目录安装所需的适配器 extra：

```bash
pip install -e \"/path/to/hugegraph-ai/hugegraph-llm-sdk[openai]\"
pip install -e \"/path/to/hugegraph-ai/hugegraph-llm-sdk[ollama]\"
pip install -e \"/path/to/hugegraph-ai/hugegraph-llm-sdk[litellm]\"
# uv 示例：uv add --editable /path/to/hugegraph-ai/hugegraph-llm-sdk --extra openai
```
""",
}

signatures = {
    "design_schema": "(texts, *, model, questions=(), example_schema=None, prompt=None) -> SchemaDraft",
    "adesign_schema": "(texts, *, model, questions=(), example_schema=None, prompt=None) -> SchemaDraft",
    "extract_graph": "(texts, *, schema, model=None, model_factory=None, review=True, options=None, prompts=None, validators=()) -> ExtractionResult",
    "aextract_graph": "(texts, *, schema, model=None, model_factory=None, review=True, options=None, prompts=None, validators=()) -> ExtractionResult",
}

for lang, path in SDK.items():
    text = path.read_text(encoding="utf-8")
    if lang == "en":
        text = sub1(text, r"### Install with pip or uv\n.*?(?=\n## Quick Start: Minimal Example)", install[lang].rstrip(), f"{lang} install")
    else:
        text = sub1(text, r"### 通过 pip 或 uv 安装\n.*?(?=\n## 快速上手：最小示例)", install[lang].rstrip(), f"{lang} install")
    for name, signature in signatures.items():
        text = sub1(text, rf"^(\| `{name}` \| )`[^`]+`( \|)", rf"\1`{signature}`\2", f"{lang} {name}")
    text, count1 = re.subn(r"(result = extract_graph\(\n\s+)text=", r"\1texts=", text)
    text, count2 = re.subn(r"(result = extract_graph\(\n\s+)text_or_chunks=", r"\1texts=", text)
    if (count1, count2) != (2, 1):
        raise RuntimeError(f"{lang} extract args: {(count1, count2)}")
    if lang == "en":
        text = text.replace("(`PRIMARY_KEY`, `CUSTOMIZE_STRING`, `CUSTOMIZE_NUMBER`)", "(`DEFAULT`, `AUTOMATIC`, `PRIMARY_KEY`, `CUSTOMIZE_STRING`, `CUSTOMIZE_NUMBER`, `CUSTOMIZE_UUID`)")
    else:
        text = text.replace("（`PRIMARY_KEY`、`CUSTOMIZE_STRING`、`CUSTOMIZE_NUMBER`）", "（`DEFAULT`、`AUTOMATIC`、`PRIMARY_KEY`、`CUSTOMIZE_STRING`、`CUSTOMIZE_NUMBER`、`CUSTOMIZE_UUID`）")
    for stale in ("pip install hugegraph-llm-sdk", "text_or_chunks", "examples=..."):
        if stale in text:
            raise RuntimeError(f"{lang}: stale SDK contract {stale}")
    path.write_text(text, encoding="utf-8")

cluster_json = """```json
{
  \"schema_version\": 1,
  \"observed_at\": 1730419200000,
  \"status\": \"UP\",
  \"registered_workers\": 1,
  \"ready_workers\": 1,
  \"master\": {
    \"id\": \"master\", \"name\": \"Vermeer Master\", \"role\": \"MASTER\",
    \"grpc_peer\": \"127.0.0.1:6688\", \"version\": \"1.8.0\",
    \"launch_time\": \"2026-11-01T08:00:00Z\", \"status\": \"UP\", \"ready\": true,
    \"checks\": {\"http_ready\": true, \"initialized\": true, \"service_online\": true},
    \"metrics\": {\"cpu_cores\": 0.15, \"rss_bytes\": 134217728, \"sample_window_seconds\": 10.0},
    \"metric_status\": {\"availability\": \"AVAILABLE\", \"observed_at\": 1730419200000}
  },
  \"workers\": [{
    \"id\": \"worker-1\", \"name\": \"worker-1\", \"role\": \"WORKER\", \"group\": \"default\",
    \"grpc_peer\": \"127.0.0.1:6689\", \"version\": \"1.8.0\",
    \"launch_time\": \"2026-11-01T08:00:05Z\", \"status\": \"UP\", \"ready\": true,
    \"checks\": {\"registered\": true, \"connection_ready\": true, \"load_stream_ready\": true,
      \"compute_stream_ready\": true, \"superstep_stream_ready\": true},
    \"metrics\": {\"cpu_cores\": 1.42, \"rss_bytes\": 2147483648, \"sample_window_seconds\": 10.0},
    \"metric_status\": {\"availability\": \"AVAILABLE\", \"observed_at\": 1730419200000}
  }]
}
```"""

sections = {
    "en": f"""#### Health and Readiness Semantics
- Registration alone is not readiness. A Worker must be registered, connected to Master, and have `load`, `compute`, and `superstep` streams ready.
- Cluster status is `DEGRADED` for an unready Master, no Workers, or any unready Worker; aggregate reasons are `master_initializing` / `service_offline`, `no_workers`, or `workers_not_ready`. Otherwise status is `UP`.
- `metric_status` is an object with `availability` (`AVAILABLE`, `UNAVAILABLE`, or `UNSUPPORTED`), `observed_at`, and optional `reason`.
- Master checks are `http_ready`, `initialized`, and `service_online`; Worker checks are `registered`, `connection_ready`, and the three `*_stream_ready` fields.
- Worker telemetry uses one 800 ms aggregate deadline outside the Worker manager lock and does not affect readiness.

#### Example Request and Response

```bash
curl -H \"Authorization: Bearer <admin-token>\" \\
  http://localhost:6688/api/v1/admin/cluster
```

{cluster_json}
""",
    "cn": f"""#### 健康与就绪语义
- 仅注册不代表就绪。Worker 必须已注册、连接 Master，并使 `load`、`compute`、`superstep` 三个任务流均就绪。
- Master 未就绪、无 Worker 或存在未就绪 Worker 时，集群状态为 `DEGRADED`；聚合原因分别为 `master_initializing` / `service_offline`、`no_workers` 或 `workers_not_ready`。其余情况为 `UP`。
- `metric_status` 是对象，包含 `availability`（`AVAILABLE`、`UNAVAILABLE` 或 `UNSUPPORTED`）、`observed_at` 与可选 `reason`。
- Master 检查项为 `http_ready`、`initialized`、`service_online`；Worker 检查项为 `registered`、`connection_ready` 和三个 `*_stream_ready` 字段。
- Worker 遥测在管理器锁外使用整批 800 ms 截止时间，不影响就绪判定。

#### 请求与响应示例

```bash
curl -H \"Authorization: Bearer <admin-token>\" \\
  http://localhost:6688/api/v1/admin/cluster
```

{cluster_json}
""",
}

for lang, path in VERMEER.items():
    text = path.read_text(encoding="utf-8")
    end = r"(?=\n### 4\.2 Space Worker Availability Probe)" if lang == "en" else r"(?=\n### 4\.2 图空间 Worker 可用性探针)"
    start = "Health and Readiness Semantics" if lang == "en" else "健康与就绪语义"
    text = sub1(text, rf"#### {start}\n.*?{end}", sections[lang].rstrip(), f"{lang} Vermeer")
    for stale in ('\"metric_status\": \"ok\"', '\"grpc_reverse\"', 'worker_not_ready', 'HEALTHY'):
        if stale in text:
            raise RuntimeError(f"{lang}: stale Vermeer contract {stale}")
    path.write_text(text, encoding="utf-8")

routes = json.loads(ROUTES.read_text(encoding="utf-8"))
pages = routes["pages"]
for lang, prefix in (("cn", "cn/"), ("en", "")):
    anchor = f"{lang}:quickstart/hugegraph-ai/hugegraph-llm"
    key = f"{lang}:quickstart/hugegraph-ai/hugegraph-llm-sdk"
    if key in pages or anchor not in pages:
        raise RuntimeError(f"route state invalid: {key}")
    new = {}
    for k, v in pages.items():
        new[k] = v
        if k == anchor:
            new[key] = {"latest": f"{prefix}docs/quickstart/hugegraph-ai/hugegraph-llm-sdk/", "1.7": None, "1.5": None, "1.3": None, "1.0": None}
    pages = new
routes["pages"] = pages
ROUTES.write_text(json.dumps(routes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

nav = json.loads(NAV.read_text(encoding="utf-8"))
parent = "/docs/quickstart/hugegraph-ai"
child = parent + "/hugegraph-llm-sdk"
updated = 0

def visit(value):
    global updated
    if isinstance(value, dict):
        children = value.get("children")
        if value.get("page") == parent and isinstance(children, list):
            if any(isinstance(x, dict) and x.get("page") == child for x in children):
                raise RuntimeError("SDK nav already exists")
            entry = {"page": child}
            if any(isinstance(x, dict) and "url" in x for x in children):
                entry.update(url=child + "/", children=[])
            index = max((i for i, x in enumerate(children) if isinstance(x, dict) and x.get("page") in {parent + "/hugegraph-llm", parent + "/hugegraph-mcp"}), default=-1)
            if index < 0:
                raise RuntimeError("HugeGraph-AI nav anchor missing")
            children.insert(index + 1, entry)
            updated += 1
        for x in value.values():
            visit(x)
    elif isinstance(value, list):
        for x in value:
            visit(x)

visit(nav)
if updated != 2:
    raise RuntimeError(f"expected 2 nav updates, got {updated}")
NAV.write_text(json.dumps(nav, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

assert json.loads(ROUTES.read_text())["pages"]["en:quickstart/hugegraph-ai/hugegraph-llm-sdk"]["latest"]
assert NAV.read_text().count('"page": "/docs/quickstart/hugegraph-ai/hugegraph-llm-sdk"') == 2
