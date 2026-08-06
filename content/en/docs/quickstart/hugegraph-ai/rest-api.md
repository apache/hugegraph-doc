---
title: "REST API Reference"
linkTitle: "REST API"
weight: 5
---

HugeGraph-LLM provides REST API endpoints for integrating RAG and Text2Gremlin capabilities into your applications.

## Base URL

```
http://localhost:8001
```

Change host/port as configured when starting the service:
```bash
python -m hugegraph_llm.demo.rag_demo.app --host 127.0.0.1 --port 8001
```

## Authentication

Currently, the API supports optional token-based authentication:

```bash
# Enable authentication in .env
ENABLE_LOGIN=true
USER_TOKEN=your-user-token
ADMIN_TOKEN=your-admin-token
```

Pass tokens in request headers:
```bash
Authorization: Bearer <token>
```

---

## RAG Endpoints

### 1. Complete RAG Query

**POST** `/rag`

Execute a full RAG pipeline including keyword extraction, graph retrieval, vector search, reranking, and answer generation.

#### Request Body

```json
{
  "query": "Tell me about Al Pacino's movies",
  "raw_answer": false,
  "vector_only": false,
  "graph_only": true,
  "graph_vector_answer": false,
  "graph_ratio": 0.5,
  "rerank_method": "cohere",
  "near_neighbor_first": false,
  "gremlin_tmpl_num": 5,
  "max_graph_items": 30,
  "topk_return_results": 20,
  "vector_dis_threshold": 0.9,
  "topk_per_keyword": 1,
  "custom_priority_info": "",
  "answer_prompt": "",
  "keywords_extract_prompt": "",
  "gremlin_prompt": "",
  "client_config": {
    "url": "127.0.0.1:8080",
    "graph": "hugegraph",
    "user": "admin",
    "pwd": "admin",
    "gs": ""
  }
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | User's natural language question |
| `raw_answer` | boolean | No | false | Return LLM answer without retrieval |
| `vector_only` | boolean | No | false | Use only vector search (no graph) |
| `graph_only` | boolean | No | false | Use only graph retrieval (no vector) |
| `graph_vector_answer` | boolean | No | false | Combine graph and vector results |
| `graph_ratio` | float | No | 0.5 | Ratio of graph vs vector results (0-1) |
| `rerank_method` | string | No | "" | Reranker: "cohere", "siliconflow", "" |
| `near_neighbor_first` | boolean | No | false | Prioritize direct neighbors |
| `gremlin_tmpl_num` | integer | No | 5 | Number of Gremlin templates to try |
| `max_graph_items` | integer | No | 30 | Max items from graph retrieval |
| `topk_return_results` | integer | No | 20 | Top-K after reranking |
| `vector_dis_threshold` | float | No | 0.9 | Vector similarity threshold (0-1) |
| `topk_per_keyword` | integer | No | 1 | Top-K vectors per keyword |
| `custom_priority_info` | string | No | "" | Custom context to prioritize |
| `answer_prompt` | string | No | "" | Custom answer generation prompt |
| `keywords_extract_prompt` | string | No | "" | Custom keyword extraction prompt |
| `gremlin_prompt` | string | No | "" | Custom Gremlin generation prompt |
| `client_config` | object | No | null | Override graph connection settings |

#### Response

```json
{
  "query": "Tell me about Al Pacino's movies",
  "graph_only": {
    "answer": "Al Pacino starred in The Godfather (1972), directed by Francis Ford Coppola...",
    "context": ["The Godfather is a 1972 crime film...", "..."],
    "graph_paths": ["..."],
    "keywords": ["Al Pacino", "movies"]
  }
}
```

#### Example (curl)

```bash
curl -X POST http://localhost:8001/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about Al Pacino",
    "graph_only": true,
    "max_graph_items": 30
  }'
```

### 2. Graph Retrieval Only

**POST** `/rag/graph`

Retrieve graph context without generating an answer. Useful for debugging or custom processing.

#### Request Body

```json
{
  "query": "Al Pacino movies",
  "max_graph_items": 30,
  "topk_return_results": 20,
  "vector_dis_threshold": 0.9,
  "topk_per_keyword": 1,
  "gremlin_tmpl_num": 5,
  "rerank_method": "cohere",
  "near_neighbor_first": false,
  "custom_priority_info": "",
  "gremlin_prompt": "",
  "get_vertex_only": false,
  "client_config": {
    "url": "127.0.0.1:8080",
    "graph": "hugegraph",
    "user": "admin",
    "pwd": "admin",
    "gs": ""
  }
}
```

**Additional Parameter:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `get_vertex_only` | boolean | false | Return only vertex IDs without full details |

#### Response

```json
{
  "graph_recall": {
    "query": "Al Pacino movies",
    "keywords": ["Al Pacino", "movies"],
    "match_vids": ["1:Al Pacino", "2:The Godfather"],
    "graph_result_flag": true,
    "gremlin": "g.V('1:Al Pacino').outE().inV().limit(30)",
    "graph_result": [
      {"id": "1:Al Pacino", "label": "person", "properties": {"name": "Al Pacino"}},
      {"id": "2:The Godfather", "label": "movie", "properties": {"title": "The Godfather"}}
    ],
    "vertex_degree_list": [5, 12]
  }
}
```

#### Example (curl)

```bash
curl -X POST http://localhost:8001/rag/graph \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Al Pacino",
    "max_graph_items": 30,
    "get_vertex_only": false
  }'
```

---

## Text2Gremlin Endpoint

### 3. Natural Language to Gremlin

**POST** `/text2gremlin`

Convert natural language queries to executable Gremlin commands.

#### Request Body

```json
{
  "query": "Find all movies directed by Francis Ford Coppola",
  "example_num": 5,
  "gremlin_prompt": "",
  "output_types": ["GREMLIN", "RESULT"],
  "client_config": {
    "url": "127.0.0.1:8080",
    "graph": "hugegraph",
    "user": "admin",
    "pwd": "admin",
    "gs": ""
  }
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Natural language query |
| `example_num` | integer | No | 5 | Number of example templates to use |
| `gremlin_prompt` | string | No | "" | Custom prompt for Gremlin generation |
| `output_types` | array | No | null | Output types: ["GREMLIN", "RESULT", "CYPHER"] |
| `client_config` | object | No | null | Graph connection override |

**Output Types:**
- `GREMLIN`: Generated Gremlin query
- `RESULT`: Execution result from graph
- `CYPHER`: Cypher query (if requested)

#### Response

```json
{
  "gremlin": "g.V().has('person','name','Francis Ford Coppola').out('directed').hasLabel('movie').values('title')",
  "result": [
    "The Godfather",
    "The Godfather Part II",
    "Apocalypse Now"
  ]
}
```

#### Example (curl)

```bash
curl -X POST http://localhost:8001/text2gremlin \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all movies directed by Francis Ford Coppola",
    "output_types": ["GREMLIN", "RESULT"]
  }'
```

---

## Configuration Endpoints

### 4. Update Graph Connection

**POST** `/config/graph`

Dynamically update HugeGraph connection settings.

#### Request Body

```json
{
  "url": "127.0.0.1:8080",
  "name": "hugegraph",
  "user": "admin",
  "pwd": "admin",
  "gs": ""
}
```

#### Response

```json
{
  "status_code": 201,
  "message": "Graph configuration updated successfully"
}
```

### 5. Update LLM Configuration

**POST** `/config/llm`

Update chat/extract LLM settings at runtime.

#### Request Body (OpenAI)

```json
{
  "llm_type": "openai",
  "api_key": "sk-your-api-key",
  "api_base": "https://api.openai.com/v1",
  "language_model": "gpt-4o-mini",
  "max_tokens": 4096
}
```

#### Request Body (Ollama)

```json
{
  "llm_type": "ollama/local",
  "host": "127.0.0.1",
  "port": 11434,
  "language_model": "llama3.1:8b"
}
```

### 6. Update Embedding Configuration

**POST** `/config/embedding`

Update embedding model settings.

#### Request Body

```json
{
  "llm_type": "openai",
  "api_key": "sk-your-api-key",
  "api_base": "https://api.openai.com/v1",
  "language_model": "text-embedding-3-small"
}
```

### 7. Update Reranker Configuration

**POST** `/config/rerank`

Configure reranker settings.

#### Request Body (Cohere)

```json
{
  "reranker_type": "cohere",
  "api_key": "your-cohere-key",
  "reranker_model": "rerank-multilingual-v3.0",
  "cohere_base_url": "https://api.cohere.com/v1/rerank"
}
```

#### Request Body (SiliconFlow)

```json
{
  "reranker_type": "siliconflow",
  "api_key": "your-siliconflow-key",
  "reranker_model": "BAAI/bge-reranker-v2-m3"
}
```

---

## Error Responses

All endpoints return standard HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (config updated) |
| 400 | Bad Request (invalid parameters) |
| 500 | Internal Server Error |
| 501 | Not Implemented |

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8001"

# 1. Configure graph connection
graph_config = {
    "url": "127.0.0.1:8080",
    "name": "hugegraph",
    "user": "admin",
    "pwd": "admin"
}
requests.post(f"{BASE_URL}/config/graph", json=graph_config)

# 2. Execute RAG query
rag_request = {
    "query": "Tell me about Al Pacino",
    "graph_only": True,
    "max_graph_items": 30
}
response = requests.post(f"{BASE_URL}/rag", json=rag_request)
print(response.json())

# 3. Generate Gremlin from natural language
text2gql_request = {
    "query": "Find all directors who worked with Al Pacino",
    "output_types": ["GREMLIN", "RESULT"]
}
response = requests.post(f"{BASE_URL}/text2gremlin", json=text2gql_request)
print(response.json())
```

---

## See Also

- [Configuration Reference](./config-reference.md) - Complete .env configuration guide
- [HugeGraph-LLM Overview](./hugegraph-llm.md) - Architecture and features
- [Quick Start Guide](./quick_start.md) - Getting started with the Web UI
