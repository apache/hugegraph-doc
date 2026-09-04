# HugeGraph-LLM REST API

LLMS 索引： [llms.txt](/cn/llms.txt)

---

HugeGraph-LLM 演示进程同时提供 Web 页面和 REST API。默认地址是 `http://localhost:8001`：

```bash
cd hugegraph-ai/hugegraph-llm
python -m hugegraph_llm.demo.rag_demo.app \
  --host 127.0.0.1 \
  --port 8001
```

## 认证

在 `.env` 中启用登录：

```properties
ENABLE_LOGIN=True
USER_TOKEN=replace-with-a-secret
```

启用后，请求需要 Bearer token：

```http
Authorization: Bearer replace-with-a-secret
```

## RAG

### `POST /rag`

根据开关返回一种或多种回答。未显式指定时只启用 `graph_only`。

```bash
curl -X POST http://localhost:8001/rag \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Al Pacino 出演过哪些电影？",
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

响应只包含已启用的回答字段：

```json
{
  "query": "Al Pacino 出演过哪些电影？",
  "graph_only": "..."
}
```

其他可选参数包括 `graph_ratio`、`rerank_method`（`bleu` 或 `reranker`）、`near_neighbor_first`、`custom_priority_info`，以及三类自定义提示词。

### `POST /rag/graph`

只执行图召回，不生成最终自然语言答案：

```bash
curl -X POST http://localhost:8001/rag/graph \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Al Pacino 出演过哪些电影？",
    "get_vertex_only": false,
    "gremlin_tmpl_num": 1,
    "rerank_method": "bleu"
  }'
```

响应的 `graph_recall` 可能包含 `keywords`、`match_vids`、`gremlin`、`graph_result` 和 `vertex_degree_list`。设置 `get_vertex_only=true` 可在顶点匹配后提前返回。

## 图抽取

### `POST /graph/extract`

使用内联 Schema 时不会连接 HugeGraph：

```bash
curl -X POST http://localhost:8001/graph/extract \
  -H 'Content-Type: application/json' \
  -d '{
    "texts": ["Alice 在 Acme 工作。"],
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
    "language": "zh",
    "split_type": "sentence",
    "include_meta": true
  }'
```

`texts` 可以是字符串或字符串数组。`language` 可选 `zh`、`en`，`split_type` 可选 `document`、`paragraph`、`sentence`。

若 `schema` 传现有图名，必须同时传入 `client_config`，且 `client_config.graph` 必须和图名相同：

```json
{
  "texts": "Alice 在 Acme 工作。",
  "schema": "hugegraph",
  "client_config": {
    "graph": "hugegraph",
    "user": "admin",
    "pwd": "admin",
    "gs": "DEFAULT"
  }
}
```

成功响应固定包含 `status`、`result.vertices`、`result.edges`、`warnings` 和 `meta`。

## Text2Gremlin

### `POST /text2gremlin`

```bash
curl -X POST http://localhost:8001/text2gremlin \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "查找所有 person 顶点",
    "example_num": 1,
    "output_types": ["template_gremlin", "template_execution_result"]
  }'
```

`output_types` 可包含：

- `match_result`
- `template_gremlin`
- `raw_gremlin`
- `template_execution_result`
- `raw_execution_result`

省略该字段时默认只返回 `template_gremlin`；传空数组表示由实现返回全部输出。自定义 `gremlin_prompt` 必须包含 `{query}`、`{schema}`、`{example}` 和 `{vertices}`。

## 运行时配置

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

### `POST /config/llm` 与 `POST /config/embedding`

两个端点使用同一个请求模型。OpenAI 或 LiteLLM 示例：

```json
{
  "llm_type": "openai",
  "api_key": "your-key",
  "api_base": "https://api.openai.com/v1",
  "language_model": "gpt-4.1-mini",
  "max_tokens": "4096"
}
```

Ollama 请求仍要提供公共字段；`api_key` 和 `api_base` 可传空字符串：

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

`reranker_type` 可选 `cohere`、`siliconflow`。Cohere 还可以传 `cohere_base_url`。

这些配置端点会改动进程当前配置，并可能同步到 `.env`。`/rag`、`/rag/graph` 和 `/text2gremlin` 的 `client_config` 只在单次请求期间覆盖 HugeGraph 连接；当前实现仍会临时改动进程全局设置，不适合用不同连接并发发起长请求。

## 日志

### `POST /logs`

该接口要求 `.env` 中的 `ADMIN_TOKEN` 已改成安全值。请求体示例：

```json
{
  "admin_token": "replace-with-an-admin-secret",
  "log_file": "llm-server.log"
}
```

`log_file` 只能是 `logs/` 目录下的文件名，不能包含路径分隔符。
