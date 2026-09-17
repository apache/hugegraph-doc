---
title: "HugeGraph-LLM"
linkTitle: "HugeGraph-LLM"
weight: 1
---

HugeGraph-LLM connects graph databases with large language models for knowledge graph construction, GraphRAG, and natural-language graph queries. Its demo service hosts the Gradio UI and FastAPI endpoints in the same process and listens on port `8001` by default.

## Requirements

> AI-generated project documentation: [Ask DeepWiki](https://deepwiki.com/apache/hugegraph-ai)

- Python 3.10 or 3.11 (`>=3.10,<3.12`)
- `uv` 0.7 or later
- HugeGraph Server 1.3 or later (1.5 or later recommended)

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

The Compose file mounts `${PROJECT_PATH}/hugegraph-llm/.env` into the container at `/home/work/hugegraph-llm/.env`, so the file has to exist before the container starts. The resource directory `hugegraph-llm/src/hugegraph_llm/resources` can be mounted the same way; the mount is commented out by default.

## Container Images

| Image | Built from | Contents |
|---|---|---|
| `hugegraph/rag` | `docker/Dockerfile.llm` | Python 3.10 runtime with the source tree, started with `python -m hugegraph_llm.demo.rag_demo.app --host 0.0.0.0 --port 8001` |
| `hugegraph/rag-bin` | `docker/Dockerfile.nk` | Nuitka-compiled binary built from the `nk-llm` extra, started with `./app.dist/app.bin` |

Both images expose port `8001`, run as the non-root user `work`, declare a volume for `hugegraph-llm/src/hugegraph_llm/resources`, and use `curl -f http://localhost:8001/` as their health check.

`scripts/build_llm_image.sh` builds `docker/Dockerfile.llm` and tags the result `hugegraph/graphrag:1.7.0`.

## Deploy on Kubernetes

`docker/charts/hg-llm` is a Helm chart for the RAG service. It deploys the `hugegraph/graphrag` image and, by default, publishes a `NodePort` service that maps node port `8039` and service port `8080` onto container port `8001`. The release name is fixed to `hg-llm-service`. Ingress and horizontal pod autoscaling are present but disabled by default.

The chart still defaults `image.tag` to `v0.0.1`, so set `--set image.tag=1.7.0` or edit `values.yaml` to match the tag you built.

The chart ships the `.env` and prompt YAML mounts commented out in `values.yaml`. To supply your own configuration, create the two config maps and then uncomment the matching `volumes` and `volumeMounts` blocks:

```bash
kubectl create configmap hugegraph-llm-env --from-file=/path/to/.env
kubectl create configmap hugegraph-llm-prompt-config --from-file=/path/to/config_prompt.yaml
```

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

Set `HG_DEV_RELOAD=1` to start uvicorn with auto-reload during development.

The service stores model, HugeGraph, and login settings in `hugegraph-llm/.env`. Prompts are stored separately in `hugegraph-llm/src/hugegraph_llm/resources/demo/config_prompt.yaml`. The configuration code creates missing files with default values.

The `.env` location is resolved in this order: `HUGEGRAPH_LLM_ENV_PATH` if it is set, then `hugegraph-llm/.env` when the package runs from a source checkout, then `.env` in the current working directory.

## Main Capabilities

### Build RAG Indexes

The first Web UI tab splits text into a chunk vector index, extracts vertices and edges according to a schema, writes the graph to HugeGraph, and updates the vertex vector index. Input can be typed into the `text` tab or uploaded through the `file` tab, which accepts `.txt`, `.docx`, and `.pdf` files and allows selecting several at once. Encrypted PDFs and scanned PDFs without an extractable text layer are rejected.

The schema can be inline JSON or the name of an existing graph. Through the REST API, a graph name requires a matching `client_config.graph`; inline JSON neither connects to HugeGraph nor accepts `client_config`.

The tab also carries two generators. `Graph Schema Generator` derives a schema from query examples plus a few-shot example. `Graph Extraction Prompt Generator` writes an extraction prompt from a described scenario and a selected reference example. A `Graph Extraction Split Type` dropdown chooses `document`, `paragraph`, or `sentence` granularity before extraction.

### GraphRAG

The query pipeline can combine direct LLM answers, chunk-vector retrieval, and graph retrieval. Graph retrieval first extracts keywords and matches vertices, then attempts Text2Gremlin. If generation or execution fails, it can fall back to predefined graph traversals. Request parameters control result limits, vector distance thresholds, template counts, and reranking.

The same tab has a batch back-testing panel that reads questions from an `.xlsx` or `.csv` file, answers each one, and returns a downloadable file. A template file is offered for download next to the upload control.

![Knowledge graph builder](/images/docs/hugegraph-ai/gradio-kg.jpg)

### Text2Gremlin

`POST /text2gremlin` generates Gremlin from natural language, the graph schema, and optional examples. A custom prompt must retain `{query}`, `{schema}`, `{example}`, and `{vertices}`.

The matching UI tab can first build the example vector index from a `.json` or `.csv` file of question and Gremlin pairs. The bundled `resources/demo/text2gremlin.csv` is used when no file is supplied.

### Graph and Admin Tools

The `Graph Tools` tab runs a Gremlin query directly, triggers a manual graph backup, and can initialize demo data in HugeGraph. The `Admin Tools` tab shows the last lines of `logs/llm-server.log` behind an `ADMIN_TOKEN` prompt, and can refresh or clear that file.

Two background tasks run for the lifetime of the process: a cron job that backs up the graph every day at 01:00, and a task that keeps vertex-id embeddings up to date.

## Models and Vector Backends

Chat, information extraction, and Text2Gremlin can independently use an OpenAI-compatible endpoint, Ollama, or LiteLLM. The embedding model is configured separately and supports the same three providers. Reranking supports Cohere and SiliconFlow.

FAISS is the default vector index. `CUR_VECTOR_INDEX` selects `Faiss`, `Milvus`, or `Qdrant`, and the same choice is available in the `5. Set up the vector engine.` panel of the Web UI. Milvus and Qdrant require the optional dependencies:

```bash
cd hugegraph-ai
uv sync --package hugegraph-llm --extra vectordb
```

See the [workflow guide](./quick_start.md), the [configuration reference](./config-reference.md), and the [REST API](./rest-api.md) for details.

## Programmatic Use

The former `RAGPipeline` and `KgBuilder` classes were replaced by a pipeline scheduler. Call a flow by name through `SchedulerSingleton`:

```python
from hugegraph_llm.flows.scheduler import SchedulerSingleton

scheduler = SchedulerSingleton.get_instance()
res = scheduler.schedule_flow(
    "rag_graph_only",
    query="Tell me about Al Pacino.",
    graph_only_answer=True,
    vector_only_answer=False,
    raw_answer=False,
    gremlin_tmpl_num=-1,
    gremlin_prompt=None,
)
print(res.get("graph_only_answer"))
```

The registered flow names are `rag_raw`, `rag_vector_only`, `rag_graph_only`, `rag_graph_vector`, `text2gremlin`, `build_examples_index`, `build_vector_index`, `graph_extract`, `import_graph_data`, `update_vid_embeddings`, `get_graph_index_info`, `build_schema`, and `prompt_generate`. `schedule_stream_flow` is the async streaming variant.

## Development Checks

Install the module and the development tools from the repository root, then run the checks that mirror CI:

```bash
cd hugegraph-ai
uv sync --extra llm --extra dev
uv run ruff format --check .
uv run ruff check .

cd hugegraph-llm
SKIP_EXTERNAL_SERVICES=true uv run pytest src/tests/config/ src/tests/document/ src/tests/middleware/ \
  src/tests/operators/ src/tests/models/ src/tests/indices/ src/tests/test_utils.py -v --tb=short
SKIP_EXTERNAL_SERVICES=true uv run pytest src/tests/integration/test_graph_rag_pipeline.py \
  src/tests/integration/test_kg_construction.py src/tests/integration/test_rag_pipeline.py -v --tb=short
```

Git hooks are available through pre-commit:

```bash
cd hugegraph-ai
pre-commit install
pre-commit run --all-files
```
