# HugeGraph-AI

LLMS index: [llms.txt](/llms.txt)

---

`hugegraph-ai` provides Python clients for HugeGraph, graph machine learning tools, and LLM tools for knowledge graph construction and GraphRAG applications.

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html) · [Ask DeepWiki](https://deepwiki.com/apache/hugegraph-ai)

## Modules

- [hugegraph-llm](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-llm): knowledge graph construction, GraphRAG, and natural-language graph queries.
- [hugegraph-ml](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-ml): reads graph data from HugeGraph and runs graph learning models.
- [hugegraph-python-client](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-python-client): a Python SDK for managing schemas and graph data and running Gremlin queries.
- [vermeer-python-client](https://github.com/apache/hugegraph-ai/tree/main/vermeer-python-client): a Python SDK for the Vermeer graph computing service.

The repository uses a `uv` workspace to manage the LLM and Python client packages. HugeGraph-ML is a path dependency rather than a workspace member.

## Requirements

- HugeGraph-LLM: Python 3.10 or 3.11
- HugeGraph-ML and the Python clients: Python 3.10 or later
- `uv` 0.7 or later
- HugeGraph Server 1.5 or later

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
- [Configuration reference](./config-reference.md)
- [REST API](./rest-api.md)
- [HugeGraph-ML](./hugegraph-ml.md)
- [Python client](../client/hugegraph-client-python.md)

---

Section pages:

- [HugeGraph-LLM](/docs/quickstart/hugegraph-ai/hugegraph-llm/)
- [HugeGraph-ML](/docs/quickstart/hugegraph-ai/hugegraph-ml/)
- [HugeGraph-LLM Workflow](/docs/quickstart/hugegraph-ai/quick_start/)
- [Configuration Reference](/docs/quickstart/hugegraph-ai/config-reference/)
- [HugeGraph-LLM REST API](/docs/quickstart/hugegraph-ai/rest-api/)
