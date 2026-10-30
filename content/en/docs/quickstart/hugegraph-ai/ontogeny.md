---
title: "Ontogeny"
linkTitle: "Ontogeny"
weight: 7
---

**Ontogeny** is an evolving operational ontology platform for AI applications, located in the [HugeGraph-AI](https://github.com/apache/hugegraph-ai/tree/ontogeny) module.
It models business semantics (entities, properties, relations) and operations (actions, functions, policies) as declarative, Git-native YAML specifications.
These are exposed to applications and AI agents through a governed API, with optional projection to [Apache HugeGraph](https://github.com/apache/hugegraph) for deep graph queries.

### Architecture Overview

The following diagram illustrates core modules and operational flows:

![Overall architecture board](/images/docs/hugegraph-ai/ontogeny-arch-board.png)

The system consists of three architectural layers:
- **Top Layer**: Core DSL definitions, where Action serves as the sole write gateway and EvalSuite provides quality evaluation.
- **Middle Layer**: The online pipeline (modeling → exploration → execution → control → audit) and offline self-evolution (RSI) loop, with Agent operations unified under policy access control.
- **Bottom Layer**: Platform runtime and cross-cutting invariants (clear ownership, single control gate, Git as single source of truth).

## Key Features

- **Declarative Git-Native Modeling**: Ontology definitions are managed in YAML and reviewed via Pull Requests, eliminating opaque UI configuration.
- **Lightweight Single-Process Kernel**: `ontogeny serve` integrates registry, query engine, and Action runtime on SQLite or PostgreSQL.
- **Agent Governance**: Exposes a governed MCP tool surface at `/mcp`. Agents and human users share unified policies, and writes support human approval gates.
- **Deterministic Self-Evolution (RSI)**: Closed-loop cycle of observation → mutation (LLM-assisted DSL diffs) → selection (rule-based deterministic evaluations) → release.
- **Immutable Audit Stream**: Every tool invocation and policy block is recorded for full traceability and replay.
- **Bilingual Web Console**: Built with React 19, offering an interactive ontology canvas, graph explorer, action executor, audit viewer, and evolution panel.

The ontology canvas provides a comprehensive view of domain objects, relations, actions, and functions, highlighting dependencies on hover:

![Ontology definition canvas](/images/docs/hugegraph-ai/ontogeny-ontology-canvas.png)

## Quick Start

```bash {tab="Docker (Recommended)"}
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/ontogeny

# Start self-contained demo environment (SQLite + seeded data)
docker compose up -d

# Optional profiles:
# docker compose --profile postgres up -d
# docker compose --profile graph up -d
```

```bash {tab="From Source"}
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/ontogeny

# Install backend with MCP dependencies
uv venv && source .venv/bin/activate && uv pip install -e '.[mcp]'

# Build web console
cd web && npm install && npm run build && cd ..

# Launch demo service
ontogeny serve --demo --open
```

Access the console and API at **http://localhost:8000**. The initial launch creates an `admin` account with default password `ontogeny@2026`.
When starting from source, you can customize the initial password via `ONTOGENY_ADMIN_PASSWORD`; in Docker Compose mode, this host variable is not automatically passed into the container, so change the default password via the web console after logging in.

Optionally configure a local LLM for the assistant and RSI proposer:
```bash
ONTOGENY_LLM_BASE_URL=http://<ollama>:11434 ONTOGENY_LLM_MODEL=qwen3:27b ontogeny serve --demo --open
```

> [!NOTE]
> The API uses session/bearer authentication. When enabled, the evaluation header `X-Ontogeny-Principal` treats any client request as an administrator. Disable it via `ONTOGENY_DEV_AUTH=0` when running from source, or explicitly set `ONTOGENY_DEV_AUTH: "0"` in `docker-compose.yml` or container environment for Docker deployments. In production environments, always disable this header and authenticate with valid credentials.

To import a custom domain package, navigate to **New domain → Import ontology package** in the sidebar, and upload a zip archive containing domain YAML definitions (built-in demo domains such as `domains/product-manufacturing` are loaded automatically in demo mode and do not need to be imported again).

The Overview dashboard shows ontology metrics, agent activities, and runtime status:

![The Overview dashboard](/images/docs/hugegraph-ai/ontogeny-dashboard.png)

## Connecting an Agent (MCP)

Point any MCP-compatible client (such as Claude Desktop, Cursor, LangGraph, or the `mcp` SDK) to **`http://<host>/mcp`**:

1. **Initialize Session**: Call `agent_open_session(plugin, task)` to establish governed context for a specified plugin.
2. **Execute Governed Calls**: Supply `plugin`, `session_id`, and `thought` with each invocation to adhere to quotas and policy controls.
3. **Approval Gates**: Write operations pause in the console awaiting administrator approval by default (`approval.writes=confirm`); actions whitelisted under `approval.auto_actions` execute automatically, while plugins configured with `approval.writes=never` reject write attempts entirely. Invocations without a session remain read-only.
{.steps}

The console includes a floating agent dialog for executing tasks, querying ontology definitions, or triggering RSI proposals:

![The agent console popup](/images/docs/hugegraph-ai/ontogeny-agent-console.png)

All executions and blocked attempts are written to the audit stream:

![The audit stream](/images/docs/hugegraph-ai/ontogeny-audit.png)

## Production Notes

- **Single-Process Kernel**: Registry, outbox, compute tasks, and graph projection workers run in a single process. Do not run with `uvicorn --workers N`; scale horizontally by domain (one process per database).
- **Observability**: Query `GET /api/v1/admin/metrics` for built-in query, action, agent, and outbox metrics without extra external monitoring agents.
- **Query Benchmarks**: Execute `python tools/bench_query.py` to evaluate p50/p95 latency across search, filter, and traversal workloads.

## More Resources

- Ontogeny repository branch: <https://github.com/apache/hugegraph-ai/tree/ontogeny>
- OpenAPI specifications: `GET /openapi.json` on a running instance
- [HugeGraph-LLM](./hugegraph-llm.md) — GraphRAG and knowledge graph construction from the main branch
