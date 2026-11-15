---
title: "HugeGraph-AI"
linkTitle: "HugeGraph-AI"
weight: 3
---

`hugegraph-ai` provides graph clients, knowledge-graph construction, GraphRAG, MCP tools and graph learning.
Choose the module for your task; deployment and API examples are maintained in its guide.
Current source is the `1.8.0` workspace; source versions do not establish that every package or image has been published.

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html) · [Source repository](https://github.com/apache/hugegraph-ai)

## Modules {#modules}

- [GraphRAG application](./hugegraph-llm.md) — Run the Web UI and REST service for document ingestion, graph retrieval and natural-language queries.
- [Standalone LLM SDK](./hugegraph-llm-sdk.md) — Embed schema design, validation and reviewed graph extraction in Python applications.
- [MCP tools](./hugegraph-mcp.md) — Connect AI clients to graph queries, schemas and controlled writes.
- [Python graph client](/docs/clients/client/hugegraph-client-python/) — Manage schemas, graph data and Gremlin requests.
- [Vermeer Python client](./vermeer-python-client.md) — Automate graph loading, computation and result retrieval.
- [Graph learning](./hugegraph-ml.md) — Read HugeGraph data and run graph-learning examples.
{.cards .td-cards-list}

## Requirements {#requirements}

- Current source modules require Python **3.12+**; the LLM application supports Python **3.12–3.14**.
- Use [`uv`](https://docs.astral.sh/uv/getting-started/installation/) for the source workspace.
- The graph client requires HugeGraph Server **1.5.0+** and rejects detectable older versions. Check each feature's Server-version requirement separately.

The `uv` workspace contains `hugegraph-llm-sdk`, `hugegraph-llm`, and `hugegraph-python-client`.
Vermeer is an editable path dependency; ML and MCP have their own installation guides.
The Python client's source directory is `hugegraph-python-client`, while its distribution name is `hugegraph-python`.

## Optional Dependency Groups {#optional-dependency-groups}

Run root workspace commands from the repository checkout:

| Extra | Installs |
| --- | --- |
| `llm` | LLM application and its dependencies |
| `vectordb` | LLM application with Milvus/Qdrant support |
| `python-client` | `hugegraph-python` |
| `vermeer` | `vermeer-python-client` |
| `dev` | pytest, coverage, Ruff, ty and pre-commit |
| `nk-llm` | LLM application, graph client and Nuitka image-build dependencies |
| `all` | LLM application, graph client and Vermeer client; does not include ML or MCP |

There is no root `ml` extra. Follow the separate ML and MCP guides rather than adding their dependencies to the LLM deployment.

## Deploy with Docker Compose {#deploy-with-docker-compose}

Follow the [canonical Compose procedure](./hugegraph-llm.md#deploy-with-docker-compose).
It prepares the bootstrap file and builds the source workspace's expected RAG image before starting Server and RAG together.
For Kubernetes and persistent application configuration, use the [unified Helm deployment](/docs/quickstart/hugegraph/hugegraph-helm/#8-graphrag).

## Start the RAG Service from Source {#start-the-rag-service-from-source}

Follow [source startup](./hugegraph-llm.md#start-from-source), then the [workflow guide](./quick_start.md).
`uv sync --extra llm` creates `.venv` at the workspace root. The checkout does not track `uv.lock`, so resolution follows `pyproject.toml` constraints.
For deployment defaults, saved model connections and persistent files, read the [configuration reference](./config-reference.md).

## Install ML Dependencies {#install-ml-dependencies}

ML is a separate project. Use the [ML installation and examples](./hugegraph-ml.md); root `--extra all` does not install it.

## Next Steps {#next-steps}

- [Build indexes and query documents](./quick_start.md)
- [Configure models, storage and credentials](./config-reference.md)
- [Call the RAG and configuration APIs](./rest-api.md)
