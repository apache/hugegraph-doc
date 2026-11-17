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

下列 RAG 和配置接口使用 `POST`：

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

<span id="认证"></span>

## 认证 {#authentication}

在 `.env` 中启用登录：

```properties
ENABLE_LOGIN=True
USER_TOKEN=replace-with-a-secret
```

启用后，请求需要 Bearer token：

```http
Authorization: Bearer replace-with-a-secret
```

同一开关也会给 Gradio 页面加上基础认证，用户名固定为 `rag`，密码是 `USER_TOKEN`。token 不正确时返回 401，并带上 `WWW-Authenticate: Bearer` 响应头。`ENABLE_LOGIN=False` 时，这些 RAG／配置路由不检查 Bearer token。
`/logs` 仍要求管理员 token，Thin API 写路由另有部署开关。应用登录不保护每个 HTTP 路由，仍需可信网络或带认证的反向代理。

> [!WARNING]
> 生产环境必须启用 HugeGraph-LLM 自身的登录认证，并在防火墙或网络入口设置来源 IP 白名单。该认证只保护 HugeGraph-LLM 的页面和 REST API；HugeGraph Server 还必须单独开启认证与授权（见[认证与授权说明](/cn/docs/config/config-authentication/)）并保留 Server 审计日志（标准日志文件为 `audit-*.log`），为 `GRAPH_USER` 配置最小必要权限。`USER_TOKEN` 不会替代 Server 认证。

## RAG {#rag}

### `POST /rag` {#post-rag}

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
    "gremlin_tmpl_num": 1
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

### `POST /rag/graph` {#post-raggraph}

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

<span id="图抽取"></span>

## 图抽取 {#graph-extraction}

### `POST /graph/extract` {#post-graphextract}

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
| `review_options` | 无（禁用） | 可选 JSON 对象，启用多轮模型审阅与有限修复：`max_reviews`、`max_fixes`、`max_workers` |
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

<span id="模型审阅与修复review_options"></span>

### 模型审阅与修复（`review_options`） {#model-review-and-repair-review_options}

传入 `review_options` 可为每个切分后的文本块启用迭代式模型审阅与有限 Schema 自动修复：

```json
{
  "texts": ["Alice 在 Acme 集团工作。", "Bob 在 Beta 公司工作。"],
  "schema": {
    "vertexlabels": [
      {"name": "person", "properties": ["name"]},
      {"name": "company", "properties": ["name"]}
    ],
    "edgelabels": [
      {"name": "works_at", "source_label": "person", "target_label": "company", "properties": []}
    ]
  },
  "review_options": {
    "max_reviews": 2,
    "max_fixes": 1,
    "max_workers": 4
  }
}
```

- `max_reviews`（默认 `2`，范围 `0`–`5`）：每个文本块允许的最大模型审阅轮数。
- `max_fixes`（默认 `1`，范围 `0`–`3`）：每个文本块允许的最大自动修复尝试次数。
- `max_workers`（默认 `4`，范围 `1`–`8`）：并发处理文本块的工作线程数。
- 传入 `{}` 使用上述默认值；省略 `review_options` 或设为 `null` 则保持旧版直接抽取且不审阅。

<span id="响应格式说明"></span>

### 响应格式说明 {#response-format}

省略 `review_options` 时，HTTP 200 响应中的 `status` 始终为 `succeeded`。开启 `review_options` 后：
- 全局 `status` 综合各分块状态计算：`succeeded`（所有分块达成 final）、`partial`（部分分块达成 final）或 `failed`（没有任何分块达成 final）。
- 仅达成 `final` 状态的分块会被汇总合并到顶层 `result.vertices` 与 `result.edges`。
- 响应体包含 `chunk_results` 列表，记录每个文本块的具体执行结果：
  - `index`：文本块在输入序列中的 0 起始索引。
  - `status`：`final`（通过结构校验与模型审阅）、`candidate`（通过校验但审阅配额耗尽）、`blocked`（Schema 约束无法修复或被审阅拦截）或 `failed`（调用异常或截断）。
  - `graph`：当前抽取的子图数据对象（`vertices` 与 `edges`），失败时为 `null`。
  - `issues`：校验或审阅中发现的问题列表，包含 `path`、`message` 及可选的原文 `evidence`。
  - `reason` 与 `stage`：失败原因与发生阶段（`prepare`、`extract`、`validate`、`review` 或 `repair`）。
  - `reviews_used`、`fixes_used` 与 `llm_calls`：记录该文本块消耗的大模型调用计数。

## Text2Gremlin {#text2gremlin}

### `POST /text2gremlin` {#post-text2gremlin}

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

`example_num` 默认是 `0`，表示不使用模板，取值会被限制在 0 到 10 之间。`client_config` 只能确认已配置的 HugeGraph 连接：传入的 URL、图、GraphSpace 和凭据必须匹配，否则返回 400。
它不能选择其他目标，生成时使用已配置图的 Schema。`query` 为空返回 400，生成失败返回 500。

<span id="运行时配置"></span>

## 运行时配置 {#runtime-configuration}

### `POST /config/graph` {#post-configgraph}

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

<span id="post-configllm-与-post-configembedding"></span>

### `POST /config/llm` 与 `POST /config/embedding` {#post-configllm-and-post-configembedding}

`/config/llm` 保存一个 `role`：`chat`（默认）、`extract` 或 `text2gql`。
未独立配置的抽取／Text2Gremlin 动态跟随 Chat；保存某角色后，它使用自己的连接。`/config/embedding` 保存独立的嵌入模型连接。
Provider 可选 `openai`、`ollama/local`。OpenAI 兼容服务示例：

```json
{
  "role": "chat",
  "llm_type": "openai",
  "api_key": "your-key",
  "api_base": "https://api.openai.com/v1",
  "language_model": "gpt-4.1-mini",
  "max_tokens": 4096
}
```

Ollama 使用 `host`、整数 `port` 和 `language_model`，无需 API-key 字段：

```json
{
  "llm_type": "ollama/local",
  "language_model": "qwen2.5:7b",
  "host": "127.0.0.1",
  "port": 11434
}
```

### `POST /config/rerank` {#post-configrerank}

```json
{
  "reranker_type": "siliconflow",
  "reranker_model": "BAAI/bge-reranker-v2-m3",
  "api_key": "your-key"
}
```

`reranker_type` 可选 `cohere`、`siliconflow`。Cohere 还可以传 `cohere_base_url`。

四个配置端点成功时返回 201。应用连接保存到可写的 `settings.yaml`，不改写引导配置 `.env`。
模型保存只校验格式，不连接服务；请求 Schema 校验错误（如类型不合法或端口越界）返回 422，被拒绝的配置项（如更换目标但未提供 key）返回 400，存储写入失败返回 503。
key 留空或省略时保留原 key；`clear_api_key: true` 才会明确清除。
更换 provider 或端点时须输入新 key 或明确清除，原 key 不会静默发送到其他服务。

### 测试与继承模型连接 {#test-model-connections}

保存后调用 `POST /config/model/{role}/test` 测试连接，支持 `chat`、`extract`、`text2gql`、`embedding`、`reranker`。
成功返回 200；连接测试失败返回 502，已保存配置保持不变。
调用 `POST /config/llm/extract/use-chat` 或 `POST /config/llm/text2gql/use-chat` 可恢复跟随 Chat，成功返回 200。

`/rag`、`/rag/graph` 接受 `client_config` 仅为请求兼容，实际忽略该字段，使用已配置连接。
`/text2gremlin` 则要求传入的目标和凭据与已配置连接一致。这些请求字段不会保存设置，也不提供逐请求多租户路由。
需要改变部署连接时，应明确调用 `/config/graph`。已保存连接和部署默认值的关系见[配置参考](./config-reference.md#saved-connections)。

## 自动化接口 {#automation-endpoints}

Thin API 提供 `GET /graph-index-info` 和 `GET /vid-embeddings/refresh-capabilities` 只读发现接口。
需要带审查／修复的抽取时使用 `/graph/extract`；旧 `/graph-extract` 包装接口的响应 envelope 不同，也不支持 `review_options`。

Thin 写路由 `POST /graph-import`、`POST /vid-embeddings/refresh` 默认关闭，仅在内部已认证部署同时设置
`ENABLE_LOGIN=true` 与 `HUGEGRAPH_LLM_ENABLE_THIN_WRITES=true` 后启用。
需要验证目标的自动刷新请用 `POST /v1/vid-embeddings/refresh`，同时提供与当前配置匹配的 `expected_graph`、`expected_graphspace`。
仅发现能力接口可用，不能保证旧副本也会验证这些字段。

Thin 响应使用 `ok`、`data`、`error`、`warnings`、`next_actions`、`meta` envelope。
写入被禁用或流程失败时可能仍返回 HTTP 200、`ok:false`；请检查 `ok` 和 `error.type`，不要只按 HTTP 状态判断成功。

<span id="日志"></span>

## 日志 {#logs}

### `POST /logs` {#post-logs}

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
