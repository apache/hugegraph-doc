---
title: "HugeGraph-LLM REST API"
linkTitle: "REST API"
weight: 5
---

HugeGraph-LLM 演示进程同时提供 Web 页面和 REST API。默认地址是 `http://localhost:8001`：

```bash
cd hugegraph-ai/hugegraph-llm
python -m hugegraph_llm.demo.rag_demo.app \
  --host 127.0.0.1 \
  --port 8001
```

所有接口都使用 `POST`：

| 路径 | 成功状态码 | 用途 |
|---|---|---|
| `/rag` | 200 | 按所选召回方式回答问题 |
| `/rag/graph` | 200 | 只做图召回，不生成最终答案 |
| `/graph/extract` | 200 | 从文本抽取顶点和边 |
| `/text2gremlin` | 200 | 由自然语言生成 Gremlin |
| `/config/graph` | 201 | 更新 HugeGraph 连接 |
| `/config/llm` | 201 | 更新语言模型 |
| `/config/embedding` | 201 | 更新嵌入模型 |
| `/config/rerank` | 201 | 更新重排序模型 |
| `/logs` | 200 | 流式返回服务日志 |

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

同一开关也会给 Gradio 页面加上基础认证，用户名固定为 `rag`，密码是 `USER_TOKEN`。token 不正确时返回 401，并带上 `WWW-Authenticate: Bearer` 响应头。`ENABLE_LOGIN` 保持 `False` 时所有接口都不做鉴权。

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

其他可选参数包括 `graph_ratio`（默认 `0.5`）、`rerank_method`（`bleu` 或 `reranker`，默认 `bleu`）、`near_neighbor_first`（默认 `false`）、`custom_priority_info`，以及三个自定义提示词字段 `answer_prompt`、`keywords_extract_prompt` 和 `gremlin_prompt`。省略提示词字段时使用 `config_prompt.yaml` 中的值。

`gremlin_tmpl_num` 决定图召回阶段 Text2Gremlin 的执行方式：小于 0 表示跳过 Text2Gremlin，直接使用预定义的图遍历；等于 0 表示不带示例生成 Gremlin；大于 0 表示从示例索引中取相应数量的示例。

`query` 为空或只有空白字符时返回 400。

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

响应的 `graph_recall` 可能包含 `query`、`keywords`、`match_vids`、`graph_result_flag`、`gremlin`、`graph_result` 和 `vertex_degree_list`。设置 `get_vertex_only=true` 可在顶点匹配后提前返回，此时接口会把 `match_vids` 替换为完整的顶点详情。

`query` 为空返回 400，请求类型错误返回 400，其他失败返回 500。

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

请求字段：

| 字段 | 默认值 | 说明 |
|---|---|---|
| `texts` | 必填 | 字符串或字符串数组；空白项会被丢弃，全部为空时报错 |
| `schema` | 必填 | 内联 JSON 对象或字符串，或现有图名 |
| `example_prompt` | 提示词 YAML 中的值 | 抽取提示词头部 |
| `extract_type` | `property_graph` | 目前仅接受该值 |
| `language` | `zh` | `zh` 或 `en`，用于文本切分 |
| `split_type` | `document` | `document`、`paragraph` 或 `sentence` |
| `include_meta` | `false` | 在 `meta` 中加入 `vertex_count`、`edge_count` 和 `text_count` |
| `client_config` | 无 | 仅在 `schema` 为图名时允许传入 |

内联 Schema 必须是包含 `vertexlabels` 和 `edgelabels` 两个列表的对象。每个顶点标签需要非空的 `name` 和非空的 `properties` 列表；每条边标签需要非空的 `name`、`source_label` 和 `target_label`。`propertykeys` 可选，若存在必须是列表。

若 `schema` 传现有图名，必须同时传入 `client_config`，且 `client_config.graph` 必须和图名相同。这里的 `client_config` 只接受 `graph`、`user`、`pwd` 和 `gs`，未知字段会被拒绝，且没有 `url` 字段：

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

成功响应固定包含 `status`（始终为 `succeeded`）、`result.vertices`、`result.edges`、`warnings` 和 `meta`。`include_meta` 不为 `true` 时 `meta` 为空。

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

省略该字段时默认只返回 `template_gremlin`；传空数组表示由实现返回全部输出。自定义 `gremlin_prompt` 必须包含 `{query}`、`{schema}`、`{example}` 和 `{vertices}`，缺少占位符时请求校验失败，并会列出缺失的占位符。

`example_num` 默认是 `0`，表示不使用模板，取值会被限制在 0 到 10 之间。`client_config` 只在单次请求内覆盖 HugeGraph 连接，生成时使用的 Schema 是当前生效的图名。`query` 为空返回 400，生成失败返回 500。

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

`user` 和 `pwd` 默认是空字符串，`gs` 可选。

### `POST /config/llm` 与 `POST /config/embedding`

两个端点使用同一个请求模型。`/config/llm` 会把 `chat_llm_type`、`extract_llm_type` 和 `text2gql_llm_type` 一起设为相同的值；要分别设置各任务的类型，只能通过 `.env` 或 Web 页面。OpenAI 或 LiteLLM 示例：

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

四个配置端点成功时都返回 201。它们会改动进程当前配置，并可能同步到 `.env`。`/config/llm`、`/config/embedding` 和 `/config/rerank` 在应用过程中抛出异常时会回滚到原有取值，`/config/graph` 不会。

`/rag`、`/rag/graph` 和 `/text2gremlin` 的 `client_config` 只在单次请求期间覆盖 HugeGraph 连接，且仅应用请求中实际出现的字段。当前实现仍会临时改动进程全局设置，不适合用不同连接并发发起长请求。

## 日志

### `POST /logs`

该接口要求 `.env` 中的 `ADMIN_TOKEN` 已改成安全值。请求体示例：

```json
{
  "admin_token": "replace-with-an-admin-secret",
  "log_file": "llm-server.log"
}
```

`log_file` 默认是 `llm-server.log`，只能是 `logs/` 目录下的文件名，不能是绝对路径、不能包含路径分隔符，也不能解析为 `.` 或 `..`。非法文件名返回 400。

`ADMIN_TOKEN` 未设置或仍是占位值时，在比对 token 之前就返回 403；token 不匹配时返回内容为 `Invalid admin_token` 的 403 响应。

成功时返回 `text/plain` 流：先回放文件末尾 125 行，然后像 `tail -f` 一样持续输出新内容。
