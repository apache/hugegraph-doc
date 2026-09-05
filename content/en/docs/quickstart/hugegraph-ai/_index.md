---
title: "HugeGraph-AI"
linkTitle: "HugeGraph-AI"
weight: 3
---

`hugegraph-ai` provides Python clients for HugeGraph, graph machine learning tools, and LLM tools for knowledge graph construction and GraphRAG applications.

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html) · [Ask DeepWiki](https://deepwiki.com/apache/hugegraph-ai)

## Modules

- [hugegraph-llm](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-llm): knowledge graph construction, GraphRAG, and natural-language graph queries.
- [hugegraph-ml](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-ml): reads graph data from HugeGraph and runs graph learning models.
- [hugegraph-python-client](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-python-client): a Python SDK for managing schemas and graph data and running Gremlin queries.
- [vermeer-python-client](https://github.com/apache/hugegraph-ai/tree/main/vermeer-python-client): a Python SDK for the Vermeer graph computing service.

The repository uses a `uv` workspace whose members are `hugegraph-llm` and `hugegraph-python-client`. `hugegraph-ml` and `vermeer-python-client` are editable path dependencies rather than workspace members. The current repository version is `1.7.0`.

## Requirements

- HugeGraph-LLM: Python 3.10 or 3.11 (`>=3.10,<3.12`)
- HugeGraph-ML: Python 3.10 or later
- HugeGraph Python client and Vermeer Python client: Python 3.9 or later
- `uv` 0.7 or later
- HugeGraph Server 1.3 or later (1.5 or later recommended)

## Optional Dependency Groups

The root project declares one extra per module plus a few combined ones:

| Extra | Installs |
|---|---|
| `llm` | `hugegraph-llm` |
| `ml` | `hugegraph-ml` |
| `python-client` | `hugegraph-python-client` |
| `vermeer` | `vermeer-python-client` |
| `dev` | pytest, pytest-cov, coverage, pylint, ruff, mypy, ty, pre-commit |
| `nk-llm` | `hugegraph-llm`, `hugegraph-python-client`, and Nuitka for the compiled image |
| `all` | all four module packages |

`hugegraph-llm` itself declares a `vectordb` extra that adds `pymilvus` and `qdrant-client`.

## Deploy with Docker Compose

The repository includes a Compose file that starts both HugeGraph Server and the RAG service:

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
cp docker/env.template docker/.env
# Edit docker/.env and set PROJECT_PATH to the absolute path of this repository
touch hugegraph-llm/.env
cd docker
docker compose -f docker-compose-network.yml up -d
```

Default addresses:

- HugeGraph Server: `http://localhost:8080`
- RAG service and Web UI: `http://localhost:8001`

## Start the RAG Service from Source

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra llm
source .venv/bin/activate
cd hugegraph-llm
python -m hugegraph_llm.demo.rag_demo.app
```

`uv sync` creates `.venv` at the repository root. Do not create a separate environment under `hugegraph-llm`, because doing so can bypass the dependencies locked by the workspace.

## Install ML Dependencies

```bash
cd hugegraph-ai
uv sync --extra ml
source .venv/bin/activate
cd hugegraph-ml/src
```

Example scripts are under `hugegraph-ml/src/hugegraph_ml/examples/`.

## Next Steps

- [HugeGraph-LLM](./hugegraph-llm.md)
- [HugeGraph-LLM workflow](./quick_start.md)
- [Configuration reference](./config-reference.md)
- [REST API](./rest-api.md)
- [HugeGraph-ML](./hugegraph-ml.md)
- [Python client](../client/hugegraph-client-python.md)
