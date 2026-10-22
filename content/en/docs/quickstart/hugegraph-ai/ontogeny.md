---
title: "Ontogeny"
linkTitle: "Ontogeny"
weight: 7
---

`ontogeny` — Greek *onto-* (being, root of *ontology*) + *genesis* (birth, development):
in biology, it names the **full-life-cycle development of an individual organism**.
The name is the thesis: an ontology here is not a static schema, but an evolving
operational system — declared in Git, compiled into tables and a graph, and grown
through actual usage. It is a **self-improving operational ontology platform** that
models enterprise business semantics (objects, properties, links) and actions
(actions, functions, policies) as declarative, Git-native YAML. It serves them to
applications, analytics, and AI agents through a governed API, with optional
projection onto [Apache HugeGraph](https://github.com/apache/hugegraph) for deep graph queries.

The whole system on one board — this is the console's Overview dashboard and the architecture map for the platform:

![Overall architecture board](/images/docs/hugegraph-ai/ontogeny-arch-board.png)

*Top: eight first-class DSL citizens (Action = single write gate, EvalSuite = selection gate).
Middle: online pipeline (build → explore → act → control → audit) and offline RSI loop,
connected by the agent spine. Bottom: supporting layer and three cross-cutting invariants
(ownership, single gate, Git as source of truth).*

## Key Features

- **Git-native ontology** — modeling is YAML + Pull Requests; consensus happens via code review rather than proprietary UI forms
- **Single-process kernel** — `ontogeny serve` bundles Registry, query engine, and Action runtime on SQLite or PostgreSQL
- **Agent-first** — governed MCP tool surface at `/mcp`; agents and humans share one policy surface, and writes pass human approval gates
- **Self-improving (RSI)** — observe → mutate (LLM-generated DSL diffs) → select (deterministic eval suites) → release (T0 auto-merge / T1 PR / T2 canary)
- **Constitutional guardrails** — machine proposals follow standard Git/CI workflows; policy relaxation, markings, and tiers always require human review
- **Bilingual enterprise console** — React 19 + TypeScript: ontology canvas (browse and edit),
  graph exploration, action runner, audit, and self-evolution console

Modeling is code review, not form-filling — the ontology canvas displays every object, link, action, and function, with dependencies highlighted on hover:

![Ontology definition canvas](/images/docs/hugegraph-ai/ontogeny-ontology-canvas.png)

## Quick Start

### Option 1: Docker (Recommended)

```bash
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai

docker compose up -d          # self-contained demo (SQLite + seeded data)
# docker compose --profile postgres up -d   # starts Postgres container only; the demo image uses SQLite by default
# docker compose --profile graph up -d      # starts HugeGraph; configure via admin API to enable graph projection
```

Console + API: **http://localhost:8000** — the first boot creates an `admin` account
with the fixed default password `ontogeny@2026` (printed in container logs).
Set `ONTOGENY_ADMIN_PASSWORD` before starting or change the password before exposing port 8000.
One command provides a live dashboard seeded with manufacturing domain data,
showcasing the ontology model, agent surface, and RSI loop:

![The Overview dashboard — ontology model section](/images/docs/hugegraph-ai/ontogeny-dashboard.png)

### Option 2: From Source

```bash
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai

# backend (with the MCP extra so /mcp is served)
uv venv && source .venv/bin/activate && uv pip install -e '.[mcp]'

# web console
cd web && npm install && npm run build && cd ..

# one-command demo: seeds a source db, installs the example ontology, serves UI + API
ontogeny serve --demo --open   # → http://127.0.0.1:8000/
```

Optional: attach an LLM shared by the assistant and the RSI proposer:
`ONTOGENY_LLM_BASE_URL=http://<ollama>:11434 ONTOGENY_LLM_MODEL=qwen3:27b ontogeny serve --demo --open`.

> [!NOTE]
> The API uses session/bearer authentication. The `X-Ontogeny-Principal` dev header is
> **enabled by default** for evaluation (`ONTOGENY_DEV_AUTH=0` disables it). Turn it off in
> production, where agent surfaces (REST + `/mcp`) require authenticated credentials and
> every session audits the operator identity.

Already have a domain package? In the sidebar domain switcher, navigate to **New domain → Import ontology package**, and upload a zip package (such as
`domains/product-manufacturing.zip`) to validate, install, and activate in one step.

## Connecting an Agent (MCP)

Point any MCP client (Claude Desktop, Cursor, LangGraph, or the `mcp` SDK) to **`http://<host>/mcp`**:

1. `agent_open_session(plugin, task)` — opens a governed session for a declared plugin;
2. Call any tool with `plugin` / `session_id` / `thought` — budget limits, tool catalog, approval gates, and step traces mirror the REST session protocol;
3. Write operations pause in the console for human approval; calls without a session are read-only.

In the console, the same surface is accessible via the floating icon at the bottom-right of every page:

![The agent console popup](/images/docs/hugegraph-ai/ontogeny-agent-console.png)

Observable governance: every execution and rejection is recorded in an immutable audit stream
(executed / rule-rejected / policy-denied), ensuring full traceability:

![The audit stream](/images/docs/hugegraph-ai/ontogeny-audit.png)

## Production Notes

- **Single-process kernel**: registry, outbox, derivation, evolution, and projection workers run in a single process. Do NOT scale with `uvicorn --workers N`;
  scale horizontally per domain (one process per database).
- **Observability**: `GET /api/v1/admin/metrics` provides query, action, agent, and outbox metrics
  directly from internal metadata tables with zero external dependencies.
- **Query baseline**: run `python tools/bench_query.py` to evaluate p50/p95 latency for search, filter, and traverse operations.

## More Resources

- Ontogeny source tree: <https://github.com/apache/hugegraph-ai/tree/ontogeny>
- Full API contract: `GET /openapi.json` on a running instance
- [HugeGraph-LLM](./hugegraph-llm.md) — GraphRAG and knowledge-graph construction from the same repository's main branch
