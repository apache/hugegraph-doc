# HugeGraph-LLM

LLMS index: [llms.txt](/versions/1.7/llms.txt)

---

HugeGraph-LLM connects graph databases with large language models for knowledge graph construction, GraphRAG, and natural-language graph queries. Its demo service hosts the Gradio UI and FastAPI endpoints in the same process and listens on port `8001` by default.

## Requirements

> AI-generated project documentation: [Ask DeepWiki](https://deepwiki.com/apache/hugegraph-ai)

- Python 3.10 or 3.11
- `uv` 0.7 or later
- HugeGraph Server 1.5 or later

## Deploy with Docker Compose

Prepare the environment files from the HugeGraph-AI repository root:

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
cp docker/env.template docker/.env
# Edit docker/.env and set PROJECT_PATH to the absolute path of this repository
touch hugegraph-llm/.env
cd docker
docker compose -f docker-compose-network.yml up -d
docker compose -f docker-compose-network.yml ps
```

After startup, HugeGraph Server is available at `http://localhost:8080`, and the RAG service and Web UI are available at `http://localhost:8001`.

## Start from Source

Install dependencies through the workspace at the repository root:

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra llm
source .venv/bin/activate
cd hugegraph-llm
python -m hugegraph_llm.demo.rag_demo.app
```

To use a custom address and port:

```bash
python -m hugegraph_llm.demo.rag_demo.app \
  --host 127.0.0.1 \
  --port 18001
```

The service stores model, HugeGraph, and login settings in `hugegraph-llm/.env`. Prompts are stored separately in `hugegraph-llm/src/hugegraph_llm/resources/demo/config_prompt.yaml`. The configuration code creates missing files with default values.

## Main Capabilities

### Build RAG Indexes

The first Web UI tab splits text into a chunk vector index, extracts vertices and edges according to a schema, writes the graph to HugeGraph, and updates the vertex vector index. The schema can be inline JSON or the name of an existing graph. Through the REST API, a graph name requires a matching `client_config.graph`; inline JSON neither connects to HugeGraph nor accepts `client_config`.

### GraphRAG

The query pipeline can combine direct LLM answers, chunk-vector retrieval, and graph retrieval. Graph retrieval first extracts keywords and matches vertices, then attempts Text2Gremlin. If generation or execution fails, it can fall back to predefined graph traversals. Request parameters control result limits, vector distance thresholds, template counts, and reranking.

![Knowledge graph builder](/versions/1.7/images/docs/hugegraph-ai/gradio-kg.jpg)

### Text2Gremlin

`POST /text2gremlin` generates Gremlin from natural language, the graph schema, and optional examples. A custom prompt must retain `{query}`, `{schema}`, `{example}`, and `{vertices}`.

## Models and Vector Backends

Chat, information extraction, and Text2Gremlin can independently use an OpenAI-compatible endpoint, Ollama, or LiteLLM. The embedding model is configured separately. FAISS is the default vector index; Milvus or Qdrant are available after installing the optional dependencies:

```bash
cd hugegraph-ai
uv sync --package hugegraph-llm --extra vectordb
```

See the [configuration reference](./config-reference.md) and [REST API](./rest-api.md) for details.

## Development Checks

```bash
cd hugegraph-ai
./style/code_format_and_analysis.sh
cd hugegraph-llm
pytest
```
