# HugeGraph-LLM REST API

LLMS index: [llms.txt](/llms.txt)

---

The HugeGraph-LLM demo process serves both the Web UI and REST API. The default address is `http://localhost:8001`:

```bash
cd hugegraph-ai/hugegraph-llm
python -m hugegraph_llm.demo.rag_demo.app \
  --host 127.0.0.1 \
  --port 8001
```

## Authentication

Enable login in `.env`:

```properties
ENABLE_LOGIN=True
USER_TOKEN=replace-with-a-secret
```

Requests then require a Bearer token:

```http
Authorization: Bearer replace-with-a-secret
```

## RAG

### `POST /rag`

Returns one or more answer types according to the switches. When none is explicitly selected, only `graph_only` is enabled.

```bash
curl -X POST http://localhost:8001/rag \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Which movies feature Al Pacino?",
    "raw_answer": false,
    "vector_only": false,
    "graph_only": true,
    "graph_vector_answer": false,
    "max_graph_items": 30,
    "topk_return_results": 20,
    "vector_dis_threshold": 0.9,
    "topk_per_keyword": 1,
    "gremlin_tmpl_num": 1,
    "client_config": {
      "url": "127.0.0.1:8080",
      "graph": "hugegraph",
      "user": "admin",
      "pwd": "admin",
      "gs": "DEFAULT"
    }
  }'
```

The response contains only enabled answer fields:

```json
{
  "query": "Which movies feature Al Pacino?",
  "graph_only": "..."
}
```

Other optional parameters include `graph_ratio`, `rerank_method` (`bleu` or `reranker`), `near_neighbor_first`, `custom_priority_info`, and three custom prompt fields.

### `POST /rag/graph`

Runs graph retrieval without generating a final natural-language answer:

```bash
curl -X POST http://localhost:8001/rag/graph \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Which movies feature Al Pacino?",
    "get_vertex_only": false,
    "gremlin_tmpl_num": 1,
    "rerank_method": "bleu"
  }'
```

`graph_recall` in the response can contain `keywords`, `match_vids`, `gremlin`, `graph_result`, and `vertex_degree_list`. Set `get_vertex_only=true` to return immediately after vertex matching.

## Graph Extraction

### `POST /graph/extract`

An inline schema does not connect to HugeGraph:

```bash
curl -X POST http://localhost:8001/graph/extract \
  -H 'Content-Type: application/json' \
  -d '{
    "texts": ["Alice works at Acme."],
    "schema": {
      "vertexlabels": [
        {"name": "person", "properties": ["name"]},
        {"name": "company", "properties": ["name"]}
      ],
      "edgelabels": [
        {
          "name": "works_at",
          "source_label": "person",
          "target_label": "company",
          "properties": []
        }
      ]
    },
    "language": "en",
    "split_type": "sentence",
    "include_meta": true
  }'
```

`texts` can be a string or an array of strings. `language` accepts `zh` or `en`; `split_type` accepts `document`, `paragraph`, or `sentence`.

When `schema` is an existing graph name, also pass `client_config`, and make `client_config.graph` match that name:

```json
{
  "texts": "Alice works at Acme.",
  "schema": "hugegraph",
  "client_config": {
    "graph": "hugegraph",
    "user": "admin",
    "pwd": "admin",
    "gs": "DEFAULT"
  }
}
```

A successful response always contains `status`, `result.vertices`, `result.edges`, `warnings`, and `meta`.

## Text2Gremlin

### `POST /text2gremlin`

```bash
curl -X POST http://localhost:8001/text2gremlin \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Find all person vertices",
    "example_num": 1,
    "output_types": ["template_gremlin", "template_execution_result"]
  }'
```

`output_types` can contain:

- `match_result`
- `template_gremlin`
- `raw_gremlin`
- `template_execution_result`
- `raw_execution_result`

If omitted, only `template_gremlin` is returned by default. An empty array lets the implementation return all outputs. A custom `gremlin_prompt` must contain `{query}`, `{schema}`, `{example}`, and `{vertices}`.

## Runtime Configuration

### `POST /config/graph`

```json
{
  "url": "127.0.0.1:8080",
  "graph": "hugegraph",
  "user": "admin",
  "pwd": "admin",
  "gs": "DEFAULT"
}
```

### `POST /config/llm` and `POST /config/embedding`

Both endpoints use the same request model. OpenAI or LiteLLM example:

```json
{
  "llm_type": "openai",
  "api_key": "your-key",
  "api_base": "https://api.openai.com/v1",
  "language_model": "gpt-4.1-mini",
  "max_tokens": "4096"
}
```

Ollama requests still require the common fields; `api_key` and `api_base` can be empty strings:

```json
{
  "llm_type": "ollama/local",
  "api_key": "",
  "api_base": "",
  "language_model": "qwen2.5:7b",
  "host": "127.0.0.1",
  "port": "11434"
}
```

### `POST /config/rerank`

```json
{
  "reranker_type": "siliconflow",
  "reranker_model": "BAAI/bge-reranker-v2-m3",
  "api_key": "your-key"
}
```

`reranker_type` accepts `cohere` or `siliconflow`. Cohere also accepts `cohere_base_url`.

These endpoints change the process's active configuration and may write values back to `.env`. `client_config` in `/rag`, `/rag/graph`, and `/text2gremlin` overrides the HugeGraph connection for one request. The current implementation still changes process-global settings temporarily, so do not issue long-running requests with different connections concurrently.

## Logs

### `POST /logs`

This endpoint requires `ADMIN_TOKEN` in `.env` to be changed to a secure value. Example request body:

```json
{
  "admin_token": "replace-with-an-admin-secret",
  "log_file": "llm-server.log"
}
```

`log_file` must be a file name under `logs/` and cannot contain path separators.
