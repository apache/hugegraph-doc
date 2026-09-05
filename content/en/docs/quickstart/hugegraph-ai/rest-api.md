---
title: "HugeGraph-LLM REST API"
linkTitle: "REST API"
weight: 5
---

The HugeGraph-LLM demo process serves both the Web UI and REST API. The default address is `http://localhost:8001`:

```bash
cd hugegraph-ai/hugegraph-llm
python -m hugegraph_llm.demo.rag_demo.app \
  --host 127.0.0.1 \
  --port 8001
```

All endpoints are `POST`:

| Path | Success status | Purpose |
|---|---|---|
| `/rag` | 200 | Answer a question with the selected retrieval modes |
| `/rag/graph` | 200 | Graph retrieval only, without a final answer |
| `/graph/extract` | 200 | Extract vertices and edges from text |
| `/text2gremlin` | 200 | Generate Gremlin from natural language |
| `/config/graph` | 201 | Update the HugeGraph connection |
| `/config/llm` | 201 | Update the language model |
| `/config/embedding` | 201 | Update the embedding model |
| `/config/rerank` | 201 | Update the reranker |
| `/logs` | 200 | Stream the server log |

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

The same setting puts the Gradio UI behind basic authentication, with the fixed user name `rag` and `USER_TOKEN` as the password. A wrong token returns 401 with a `WWW-Authenticate: Bearer` header. When `ENABLE_LOGIN` is left at `False`, every endpoint is open.

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

Other optional parameters include `graph_ratio` (default `0.5`), `rerank_method` (`bleu` or `reranker`, default `bleu`), `near_neighbor_first` (default `false`), `custom_priority_info`, and the three custom prompt fields `answer_prompt`, `keywords_extract_prompt`, and `gremlin_prompt`. Omitting a prompt field uses the value from `config_prompt.yaml`.

`gremlin_tmpl_num` selects how Text2Gremlin runs during graph retrieval. A negative value skips Text2Gremlin and goes straight to the predefined traversal, `0` generates Gremlin without examples, and a positive value retrieves that many examples from the example index.

An empty or whitespace-only `query` returns 400.

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

`graph_recall` in the response can contain `query`, `keywords`, `match_vids`, `graph_result_flag`, `gremlin`, `graph_result`, and `vertex_degree_list`. Set `get_vertex_only=true` to return immediately after vertex matching; the endpoint then replaces `match_vids` with the full vertex details.

An empty `query` returns 400, a type error in the request returns 400, and any other failure returns 500.

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

Request fields:

| Field | Default | Notes |
|---|---|---|
| `texts` | required | A string or an array of strings; empty or blank entries are dropped and an empty result is rejected |
| `schema` | required | Inline JSON object or string, or the name of an existing graph |
| `example_prompt` | prompt YAML value | Extraction prompt header |
| `extract_type` | `property_graph` | Only value currently accepted |
| `language` | `zh` | `zh` or `en`, used for chunk splitting |
| `split_type` | `document` | `document`, `paragraph`, or `sentence` |
| `include_meta` | `false` | Adds `vertex_count`, `edge_count`, and `text_count` to `meta` |
| `client_config` | none | Only allowed with a graph-name schema |

An inline schema must be an object with `vertexlabels` and `edgelabels` lists. Every vertex label needs a non-empty `name` and a non-empty `properties` list; every edge label needs a non-empty `name`, `source_label`, and `target_label`. `propertykeys` is optional and must be a list when present.

When `schema` is an existing graph name, also pass `client_config`, and make `client_config.graph` match that name. `client_config` here accepts only `graph`, `user`, `pwd`, and `gs`; unknown fields are rejected, and there is no `url` field:

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

A successful response always contains `status` (always `succeeded`), `result.vertices`, `result.edges`, `warnings`, and `meta`. `meta` stays empty unless `include_meta` is `true`.

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

If omitted, only `template_gremlin` is returned by default. An empty array lets the implementation return all outputs. A custom `gremlin_prompt` must contain `{query}`, `{schema}`, `{example}`, and `{vertices}`; a missing placeholder fails request validation and names the placeholders that are absent.

`example_num` defaults to `0`, which means no templates, and is clamped to the range 0 to 10. `client_config` overrides the HugeGraph connection for the request; the schema used for generation is the active graph name. An empty `query` returns 400, and a generation failure returns 500.

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

`user` and `pwd` default to empty strings, and `gs` is optional.

### `POST /config/llm` and `POST /config/embedding`

Both endpoints use the same request model. `/config/llm` sets `chat_llm_type`, `extract_llm_type`, and `text2gql_llm_type` to the same value; per-task types can only be set separately through `.env` or the Web UI. OpenAI or LiteLLM example:

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

All four configuration endpoints return 201 on success. They change the process's active configuration and may write values back to `.env`. `/config/llm`, `/config/embedding`, and `/config/rerank` restore the previous values if applying a change raises; `/config/graph` does not.

`client_config` in `/rag`, `/rag/graph`, and `/text2gremlin` overrides the HugeGraph connection for one request, and only the fields actually present in the request are applied. The current implementation still changes process-global settings temporarily, so do not issue long-running requests with different connections concurrently.

## Logs

### `POST /logs`

This endpoint requires `ADMIN_TOKEN` in `.env` to be changed to a secure value. Example request body:

```json
{
  "admin_token": "replace-with-an-admin-secret",
  "log_file": "llm-server.log"
}
```

`log_file` defaults to `llm-server.log`, must be a file name under `logs/`, and cannot be absolute, contain path separators, or resolve to `.` or `..`. Invalid names return 400.

An unset or placeholder `ADMIN_TOKEN` returns 403 before the token is even compared, and a wrong token returns a 403 body with the message `Invalid admin_token`.

The successful response is a `text/plain` stream that first replays the last 125 lines of the file and then follows it, in the manner of `tail -f`.
