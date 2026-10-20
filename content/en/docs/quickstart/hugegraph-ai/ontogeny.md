---
title: "Ontogeny"
linkTitle: "Ontogeny"
weight: 7
---

Ontogeny is a self-improving operational ontology platform developed on the `ontogeny` branch of [HugeGraph-AI](https://github.com/apache/hugegraph-ai). It models an enterprise's business semantics (objects, properties, links) and business operations (actions, functions, policies) as declarative, Git-native YAML, then serves them to applications, analytics and AI agents through one governed API — optionally projected onto [HugeGraph](https://github.com/apache/hugegraph) for deep-graph queries. The name is the thesis: an ontology here is not a static schema but a living thing — declared in Git, compiled into tables and a graph, and grown through use.

The whole system on one board — this is the console's Overview dashboard and the map for the capabilities below:

![Ontogeny architecture board](/images/docs/hugegraph-ai/ontogeny-arch-board.png)

> [!NOTE]
> The API is session/bearer authenticated. The `X-Ontogeny-Principal` dev header is enabled by default for evaluation (`ONTOGENY_DEV_AUTH=0` disables it). Turn it off in production: the agent surfaces (REST + `/mcp`) then require a signed-in driver, and every session records who drove it.

## Requirements

- Docker for Compose deployment, or Python 3.10 or later with `uv` plus Node.js and npm to build the web console
- Optional, all swappable and safe to omit: an OpenAI-compatible LLM endpoint (Ollama works out of the box) shared by the assistant and the self-evolution proposer; HugeGraph Server 1.5.0 or later as the graph projection store (Compose can start one); Postgres instead of the default SQLite store
- An MCP-compatible client (Claude Desktop, Cursor, LangGraph, the `mcp` SDK) if you want to drive the platform as an agent

## Deploy with Docker Compose

```bash
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
docker compose up -d
# docker compose --profile postgres up -d   # Postgres-backed metadata/object store
# docker compose --profile graph up -d      # + HugeGraph for the graph projection
```

After startup, the console and the API are available at `http://localhost:8000`. The first boot creates an `admin` account and prints the generated password to the container log; preset `ONTOGENY_ADMIN_PASSWORD` to choose it yourself.

The default profile is a self-contained demo (SQLite plus seeded data), so one command gets you a live dashboard seeded with a real manufacturing domain — the ontology model, the agent surface and the RSI loop at a glance:

![Ontogeny overview dashboard](/images/docs/hugegraph-ai/ontogeny-dashboard.png)

## Start from Source

```bash
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai

# backend (with the MCP extra so /mcp is served)
uv venv && source .venv/bin/activate && uv pip install -e '.[mcp]'

# web console
cd web && npm install && npm run build && cd ..

# one-command demo: seeds a source database, installs the example ontology, serves UI + API
ontogeny serve --demo --open   # → http://127.0.0.1:8000/
```

`--demo` generates a self-contained directory `.ontogeny-demo/` (a seeded source database plus the example ontology package); it survives restarts, `--reseed` rebuilds it, and the demo story replays automatically on first boot. To attach an LLM, shared by the assistant and the RSI proposer:

```bash
ONTOGENY_LLM_BASE_URL=http://<ollama>:11434 ONTOGENY_LLM_MODEL=qwen3:27b ontogeny serve --demo --open
```

Already have a domain package? In the console's sidebar domain switcher choose **New domain → Import ontology package** and upload a zip (for example `domains/product-manufacturing.zip`) — validate, install and activate in one step.

## Main Capabilities

### Git-native ontology DSL

Eleven declarative resource kinds (`apiVersion: ontogeny/v1`) cover the semantic layer (object types, link types), the kinetic layer (actions, functions), governance (policy sets, agent plugins), derived data (projections) and self-evolution (eval suites, evolution policy). Modeling is YAML plus pull requests — consensus happens in code review, not a locked GUI. Object tables and the graph schema are compiled artifacts: the DSL is the single source of truth, so everything can be deleted and rebuilt from the repository at any time. The bundled `product-manufacturing` domain (7 objects, 6 links, 8 actions, 3 functions, policies, a projection and an eval suite) is both the console demo and the test-suite golden package.

### One write gate, full audit

Every write crosses a five-stage runtime — parameter validation → rules → Cedar policy → effects → immutable audit — and side effects ride a transactional outbox. Access control is a Cedar subset with row-level conditions and default deny; every execution and every refusal lands in an immutable audit stream, and every agent step is attributable and replayable.

### Agents as governed first-class citizens

Agents do not get a side door. The ontology is exposed as a tool surface over MCP at `/mcp`: `agent_open_session(plugin, task)` opens a governed session for a declared plugin, and every call carries `plugin` / `session_id` / `thought`, with budgets, tool allowlists, approval gates and the step trail applying identically to the REST session protocol. Writes park for human approval in the console; session-less calls are read-only. The same surface lives behind the floating icon at the bottom-right of every console page:

![The Ontogeny agent console](/images/docs/hugegraph-ai/ontogeny-agent-console.png)

### Self-evolution (RSI) inside the governance track

The evolution loop runs observe → propose → evaluate → promote → hot-reload. Telemetry detectors turn real runs into fitness signals, the LLM drafts mutations inside a closed mutation catalog, and deterministic eval suites (query regression plus action time-travel replay over system-versioned tables) do the selecting — never the LLM. Promotion is tiered: T0 auto-merge for low-risk additions, T1 human-reviewed PR by default, T2 canary, and a human-only constitutional tier for policy relaxation, markings and ownership. In one line: mutation of the model is outsourced to the model; selection never is.

### HugeGraph projection, on demand

A `Projection` resource allowlists objects and links into a HugeGraph graph for multi-hop and deep-graph queries. The projection is never authoritative: security markings never enter the graph, consistency is eventual, and when no projection is configured queries fall back to SQL recursion — unplug it and the platform degrades gracefully instead of stopping.

## More Resources

- Ontogeny source tree: <https://github.com/apache/hugegraph-ai/tree/ontogeny>
- In-repo documentation (architecture + usage, English and Chinese): [`docs/`](https://github.com/apache/hugegraph-ai/tree/ontogeny/docs)
- Full API contract: `GET /openapi.json` on a running instance
- [HugeGraph-LLM](./hugegraph-llm.md) — GraphRAG and knowledge-graph construction from the same repository's main line
