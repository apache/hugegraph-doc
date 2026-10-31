---
title: "HugeGraph-MCP"
linkTitle: "HugeGraph-MCP"
weight: 7
---

`hugegraph-mcp` exposes HugeGraph tools to AI clients through the Model Context Protocol (MCP).
It supports schema inspection, structured graph queries, controlled writes, and optional natural-language query generation and graph extraction.
The MCP client starts a local process and communicates over STDIO. This process is not HugeGraph Server and does not expose an HTTP MCP endpoint.

Ordinary graph queries connect directly to HugeGraph Server. Query generation, extraction, and embedding refresh also require
[HugeGraph-LLM](./hugegraph-llm.md), where model credentials are configured.

## Requirements

- Python 3.10 or later. A separate HugeGraph-LLM service must also meet that module's Python requirements.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) and an MCP client that supports STDIO.
- HugeGraph Server 1.7.0 or later, reachable from the MCP process. The default graph path is `DEFAULT/hugegraph` and uses the graphspace API.
- An existing graph and an account with the required permissions. See [authentication and authorization](../../config/config-authentication.md).

## Installation and Connection

These examples pin the published `hugegraph-mcp==1.7.1` package. Cloning the repository is not required.
Replace the address, graph path, and credentials with your deployment values. Verify the connection in read-only mode before enabling supported writes.

For clients that accept a `mcpServers` JSON configuration, add:

```json
{
  "mcpServers": {
    "hugegraph": {
      "command": "uvx",
      "args": ["hugegraph-mcp@1.7.1"],
      "env": {
        "HUGEGRAPH_URL": "http://127.0.0.1:8080",
        "HUGEGRAPH_GRAPH_PATH": "DEFAULT/hugegraph",
        "HUGEGRAPH_USER": "your-user",
        "HUGEGRAPH_PASSWORD": "your-password",
        "HUGEGRAPH_MCP_READONLY": "true"
      }
    }
  }
}
```

Configuration locations and formats vary between clients. Use your client's instructions to set the same command, arguments, and environment variables.
If the client cannot find `uvx`, use its absolute path for `command`. Restart the MCP process after changing the configuration.

You can also start it in a terminal with the environment variables above already configured:

```bash
uvx hugegraph-mcp@1.7.1
```

The process waits for protocol messages from the MCP client on stdin; it does not open a web page.
stdout carries MCP JSON-RPC. Do not write extra shell output to that channel.

### Verify the Connection

List tools through the client, then call `inspect_graph_tool`. The following JSON is the parameter body for MCP `tools/call`,
not a request to send directly to the HugeGraph REST API.

```json
{
  "name": "inspect_graph_tool",
  "arguments": {"include_raw_schema": true}
}
```

Check for `ok=true` and `data.hugegraph_server_status="available"`.
Choose an existing vertex label from the schema and replace `person` below with that label:

```json
{
  "name": "query_graph_data_tool",
  "arguments": {
    "target": "vertex",
    "operation": "page",
    "label": "person",
    "limit": 5
  }
}
```

This tool belongs to the default set of 16 tools. To paginate, pass the returned `next_page` as `page` on the next call,
keeping the same query conditions. An empty result does not necessarily mean the connection failed; check the graph path, label, and existing data.

## Toolsets and Versions

A toolset selects a group of tools within the same package. It is not a package version, HugeGraph Server version, or MCP protocol version.
Version `1.7.1` accepts the following configuration names:

| `HUGEGRAPH_MCP_TOOLSET` | Tools | Purpose |
|---|---|---|
| Unset, or `v2_core` | 16 | Default toolset, including structured queries and persistent write-plan tools |
| `v1` | 10 | Compatibility toolset retaining earlier tool entry points |

Any other value, including `v2`, `core`, `legacy` or an empty string, falls back to the 10-tool `v1` set in 1.7.1 and logs an error.
Both toolsets report `mcp_tool_contract_version="2.0"`. This field describes the tool contract, not the package version.

### Toolset Naming Evolution {#toolset-evolution}

In upcoming releases, the default toolset is renamed to `core` and the compatibility toolset to `legacy`. For the current `1.7.1` release package, continue using the configurations documented above.

- `v2_core` maps to `core`, and `v1` maps to `legacy`. Legacy identifiers are retained as backward-compatible aliases with migration warnings.
- Inspection endpoints report `core` or `legacy`. Clients checking `data.toolset` or `meta.toolset` should update their checks accordingly.
- An unset variable defaults to `core`. Empty or unrecognized values halt startup rather than silently falling back.
- Toolset selection is resolved at launch; modifying configuration requires restarting the client. Compatibility mode does not bypass security or read-only controls.

## Tool Capabilities

A registered tool does not imply that every operation is enabled. The current capability boundaries are summarized below.
Use the tool schema returned to your client for exact parameters.

| Feature | Tools | Scope |
|---|---|---|
| Inspection and design | `inspect_graph_tool`, `inspect_schema_tool`, `design_schema_tool` | Connection status, schema, and design guidance |
| Structured reads | `query_graph_data_tool` | Read vertices and edges by ID, ID list, page, or conditions |
| Schema creation | `apply_schema_tool` | Validate and preview; the default toolset can confirm one property key, vertex label, or edge label creation |
| Write plans | `confirm_write_tool`, `get_write_status_tool`, `reconcile_write_tool` | Confirm, inspect, and reconcile persistent plans |
| Graph import | `import_graph_data_tool` | AI-backed `extract`; preview-only `ingest`; `table` is currently disabled |
| Graph deletion | `delete_graph_data_tool` | Exact edge deletion can be confirmed; vertex deletion is preview-only |
| Property changes | `mutate_graph_properties_tool` | Preview-only; confirmation is currently disabled |
| AI generation and extraction | `generate_gremlin_tool`, `extract_graph_data_tool` | Generate queries or graph data without executing generated queries |
| Embedding refresh | `refresh_vid_embeddings_tool` | Requires AI, admin mode, writes enabled, and confirmation; see service gates below |
| Raw Gremlin | `execute_gremlin_read_tool`, `execute_gremlin_write_tool` | Both return `FEATURE_DISABLED`; admin mode cannot override this |

The compatibility toolset excludes `inspect_schema_tool`, `query_graph_data_tool`, `mutate_graph_properties_tool`,
and the three write-plan tools. Switching to compatibility mode does not enable raw Gremlin execution.

### Controlled Writes

To use writes, set `HUGEGRAPH_MCP_READONLY=false` and use a HugeGraph account with the appropriate permissions.
For a confirmable operation, first run a dry-run, review its exact targets, changes, and warnings, then confirm the returned `plan_id`:

```json
{
  "name": "confirm_write_tool",
  "arguments": {"plan_id": "<PLAN_ID>"}
}
```

Use `get_write_status_tool(plan_id)` to inspect the persisted result. `APPLIED` means all operations are confirmed successful.
`PARTIAL` or `UNKNOWN` means the workflow is incomplete or its outcome is uncertain. Inspect and reconcile status before retrying;
do not blindly create a replacement plan. Confirming the same completed plan again returns its recorded result without repeating the write.

The built-in SQLite state store requires a single writable MCP instance and a persistent state directory.
When multiple clients start separate processes, keep them read-only initially; multi-instance writes require a shared transactional store design.
Operations returning `confirmable=false` cannot be forced through by disabling read-only mode or enabling admin mode.

## Configuration

The following defaults apply to published version `1.7.1`. HugeGraph credentials and the HugeGraph-LLM API token are separate credentials.

| Environment variable | Default | Description |
|---|---|---|
| `HUGEGRAPH_URL` | `http://127.0.0.1:8080` | HugeGraph address reachable from the MCP process |
| `HUGEGRAPH_GRAPH_PATH` | `DEFAULT/hugegraph` | `GRAPH_SPACE/GRAPH_NAME` |
| `HUGEGRAPH_GRAPHSPACE` | Unset | Overrides the graphspace in `HUGEGRAPH_GRAPH_PATH` |
| `HUGEGRAPH_GRAPH` | Unset | Overrides the graph name in `HUGEGRAPH_GRAPH_PATH` |
| `HUGEGRAPH_USER` | `admin` | HugeGraph user |
| `HUGEGRAPH_PASSWORD` | Empty | HugeGraph password |
| `HUGEGRAPH_MCP_TOOLSET` | `v2_core` | This release accepts `v2_core` and `v1` |
| `HUGEGRAPH_MCP_READONLY` | `true` | Disable controlled writes |
| `HUGEGRAPH_MCP_ALLOW_AI` | `false` | Allow calls to HugeGraph-LLM |
| `HUGEGRAPH_MCP_ADMIN_MODE` | `false` | Enable eligible administrative operations |
| `HUGEGRAPH_AI_URL` | `http://127.0.0.1:8001` | HugeGraph-LLM service address |
| `HUGEGRAPH_AI_TOKEN` | Unset | HugeGraph-LLM bearer token |
| `HUGEGRAPH_AI_GRAPH_URL` | Unset | Does not change the AI target; ignored in current source |
| `HUGEGRAPH_AI_TIMEOUT_SECONDS` | `30` | AI HTTP request timeout in seconds |
| `HUGEGRAPH_MCP_STATE_DIR` | XDG state directory or `~/.local/state/hugegraph-mcp` | Persistent directory for write plans and receipts |

### Optional AI Features

Configure and start the model service using the [HugeGraph-LLM guide](./hugegraph-llm.md), then add these entries to the MCP client's `env`:

```json
{
  "HUGEGRAPH_MCP_ALLOW_AI": "true",
  "HUGEGRAPH_AI_URL": "http://127.0.0.1:8001",
  "HUGEGRAPH_AI_TOKEN": "your-ai-service-token"
}
```

Merge these entries into the earlier `env` object. Generation and extraction can remain read-only.
Embedding refresh additionally requires:
- Client settings: `HUGEGRAPH_MCP_READONLY=false`, `HUGEGRAPH_MCP_ADMIN_MODE=true`, and `confirm=true` in the tool call.
- Service settings (HugeGraph-LLM): `ENABLE_LOGIN=true`, `HUGEGRAPH_LLM_ENABLE_THIN_WRITES=true`, a strong non-default `USER_TOKEN` (avoiding the well-known default `4321`),
  and valid authentication passed via MCP's `HUGEGRAPH_AI_TOKEN`. Without these service-side gates, refresh requests are rejected
  with `FEATURE_DISABLED` ("Legacy Thin API writes are disabled").

MCP and HugeGraph-LLM must connect to the same underlying HugeGraph instance. The capability check protocol only verifies `graph_name` and `graphspace`, while the actual embedding refresh executes entirely using the AI service's independent `GRAPH_URL`. Modifying MCP's `HUGEGRAPH_URL` does not redirect the AI service's data target.
If MCP runs on the host and AI runs in a container, they may need different addresses to reach HugeGraph: configure `GRAPH_URL` on the AI service to an address reachable from its container, such as `http://server:8080`, and ensure `GRAPH_NAME` and `GRAPH_SPACE` match MCP. Do not use the container's `127.0.0.1` to reach the host graph service.

**Capability check protocol**:
The updated protocol requires `GET /vid-embeddings/refresh-capabilities` to return `protocol_version=1`, transmitting the target graph and graphspace for server-side validation before refreshing embeddings. Services without this endpoint will reject refresh requests. This validation protects multi-tenant boundary integrity in future releases.

## Troubleshooting

- **No tools after client startup**: check the `uvx` path, Python version, and process stderr. Waiting for protocol input in a terminal is normal.
- **Structured query tool missing**: check whether the compatibility toolset was selected. For `1.7.1`, use `v2_core` or leave the variable unset.
- **`FEATURE_DISABLED` response**: check the capability table and read-only, AI, and admin settings.
  Some operations are disabled because of backend capability limits and cannot be enabled through configuration alone.
- **AI calls fail**: check the service address, token, container networking, and AI logs. An unavailable-service error does not necessarily mean a model was
  retired.
- **Embedding calls return 400 or 429**: check the provider's input-count and request-rate limits.
  Batch size and concurrent request count are different limits; handle them in HugeGraph-LLM's embedding and index-building paths, not by changing MCP toolsets.

An `ok=false` tool response indicates failure. Inspect `error.type`, `error.retryable`, and `warnings`;
an established MCP connection or successful HTTP status alone does not prove that a business operation succeeded.

## Next Steps

- [HugeGraph-LLM](./hugegraph-llm.md)
- [HugeGraph-MCP source and README](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-mcp)
- [Integration checks](https://github.com/apache/hugegraph-ai/blob/main/hugegraph-mcp/docs/integration.md)
- [PyPI package](https://pypi.org/project/hugegraph-mcp/)

Documentation on the repository's `main` branch follows source changes. Check version applicability when using a pinned package;
the installation examples on this page use `1.7.1`.
