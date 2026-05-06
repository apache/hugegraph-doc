---
title: "REST API 参考"
linkTitle: "REST API"
weight: 5
---

HugeGraph-LLM 提供 REST API 端点，用于将 RAG 和 Text2Gremlin 功能集成到您的应用程序中。

## 基础 URL

```
http://localhost:8001
```

启动服务时更改主机/端口：
```bash
python -m hugegraph_llm.demo.rag_demo.app --host 127.0.0.1 --port 8001
```

## 认证

目前 API 支持可选的基于令牌的认证：

```bash
# 在 .env 中启用认证
ENABLE_LOGIN=true
USER_TOKEN=your-user-token
ADMIN_TOKEN=your-admin-token
```

在请求头中传递令牌：
```bash
Authorization: Bearer <token>
```

---

## RAG 端点

### 1. 完整 RAG 查询

**POST** `/rag`

执行完整的 RAG 工作流，包括关键词提取、图检索、向量搜索、重排序和答案生成。

#### 请求体

```json
{
  "query": "给我讲讲阿尔·帕西诺的电影",
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

**参数说明：**

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|-----|------|------|-------|------|
| `query` | string | 是 | - | 用户的自然语言问题 |
| `raw_answer` | boolean | 否 | false | 返回 LLM 答案而不检索 |
| `vector_only` | boolean | 否 | false | 仅使用向量搜索（无图） |
| `graph_only` | boolean | 否 | false | 仅使用图检索（无向量） |
| `graph_vector_answer` | boolean | 否 | false | 结合图和向量结果 |
| `graph_ratio` | float | 否 | 0.5 | 图与向量结果的比例（0-1） |
| `rerank_method` | string | 否 | "" | 重排序器："cohere"、"siliconflow"、"" |
| `near_neighbor_first` | boolean | 否 | false | 优先选择直接邻居 |
| `gremlin_tmpl_num` | integer | 否 | 5 | 尝试的 Gremlin 模板数量 |
| `max_graph_items` | integer | 否 | 30 | 图检索的最大项数 |
| `topk_return_results` | integer | 否 | 20 | 重排序后的 Top-K |
| `vector_dis_threshold` | float | 否 | 0.9 | 向量相似度阈值（0-1） |
| `topk_per_keyword` | integer | 否 | 1 | 每个关键词的 Top-K 向量 |
| `custom_priority_info` | string | 否 | "" | 要优先考虑的自定义上下文 |
| `answer_prompt` | string | 否 | "" | 自定义答案生成提示词 |
| `keywords_extract_prompt` | string | 否 | "" | 自定义关键词提取提示词 |
| `gremlin_prompt` | string | 否 | "" | 自定义 Gremlin 生成提示词 |
| `client_config` | object | 否 | null | 覆盖图连接设置 |

#### 响应

```json
{
  "query": "给我讲讲阿尔·帕西诺的电影",
  "graph_only": {
    "answer": "阿尔·帕西诺主演了《教父》（1972 年），由弗朗西斯·福特·科波拉执导...",
    "context": ["《教父》是 1972 年的犯罪电影...", "..."],
    "graph_paths": ["..."],
    "keywords": ["阿尔·帕西诺", "电影"]
  }
}
```

#### 示例（curl）

```bash
curl -X POST http://localhost:8001/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "给我讲讲阿尔·帕西诺",
    "graph_only": true,
    "max_graph_items": 30
  }'
```

### 2. 仅图检索

**POST** `/rag/graph`

检索图上下文而不生成答案。用于调试或自定义处理。

#### 请求体

```json
{
  "query": "阿尔·帕西诺的电影",
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

**额外参数：**

| 字段 | 类型 | 默认值 | 描述 |
|-----|------|-------|------|
| `get_vertex_only` | boolean | false | 仅返回顶点 ID，不返回完整详情 |

#### 响应

```json
{
  "graph_recall": {
    "query": "阿尔·帕西诺的电影",
    "keywords": ["阿尔·帕西诺", "电影"],
    "match_vids": ["1:阿尔·帕西诺", "2:教父"],
    "graph_result_flag": true,
    "gremlin": "g.V('1:阿尔·帕西诺').outE().inV().limit(30)",
    "graph_result": [
      {"id": "1:阿尔·帕西诺", "label": "person", "properties": {"name": "阿尔·帕西诺"}},
      {"id": "2:教父", "label": "movie", "properties": {"title": "教父"}}
    ],
    "vertex_degree_list": [5, 12]
  }
}
```

#### 示例（curl）

```bash
curl -X POST http://localhost:8001/rag/graph \
  -H "Content-Type: application/json" \
  -d '{
    "query": "阿尔·帕西诺",
    "max_graph_items": 30,
    "get_vertex_only": false
  }'
```

---

## Text2Gremlin 端点

### 3. 自然语言转 Gremlin

**POST** `/text2gremlin`

将自然语言查询转换为可执行的 Gremlin 命令。

#### 请求体

```json
{
  "query": "查找所有由弗朗西斯·福特·科波拉执导的电影",
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

**参数说明：**

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|-----|------|------|-------|------|
| `query` | string | 是 | - | 自然语言查询 |
| `example_num` | integer | 否 | 5 | 使用的示例模板数量 |
| `gremlin_prompt` | string | 否 | "" | Gremlin 生成的自定义提示词 |
| `output_types` | array | 否 | null | 输出类型：["GREMLIN", "RESULT", "CYPHER"] |
| `client_config` | object | 否 | null | 图连接覆盖 |

**输出类型：**
- `GREMLIN`：生成的 Gremlin 查询
- `RESULT`：图的执行结果
- `CYPHER`：Cypher 查询（如果请求）

#### 响应

```json
{
  "gremlin": "g.V().has('person','name','弗朗西斯·福特·科波拉').out('directed').hasLabel('movie').values('title')",
  "result": [
    "教父",
    "教父 2",
    "现代启示录"
  ]
}
```

#### 示例（curl）

```bash
curl -X POST http://localhost:8001/text2gremlin \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查找所有由弗朗西斯·福特·科波拉执导的电影",
    "output_types": ["GREMLIN", "RESULT"]
  }'
```

---

## 配置端点

### 4. 更新图连接

**POST** `/config/graph`

动态更新 HugeGraph 连接设置。

#### 请求体

```json
{
  "url": "127.0.0.1:8080",
  "name": "hugegraph",
  "user": "admin",
  "pwd": "admin",
  "gs": ""
}
```

#### 响应

```json
{
  "status_code": 201,
  "message": "图配置更新成功"
}
```

### 5. 更新 LLM 配置

**POST** `/config/llm`

运行时更新聊天/提取 LLM 设置。

#### 请求体（OpenAI）

```json
{
  "llm_type": "openai",
  "api_key": "sk-your-api-key",
  "api_base": "https://api.openai.com/v1",
  "language_model": "gpt-4o-mini",
  "max_tokens": 4096
}
```

#### 请求体（Ollama）

```json
{
  "llm_type": "ollama/local",
  "host": "127.0.0.1",
  "port": 11434,
  "language_model": "llama3.1:8b"
}
```

### 6. 更新嵌入配置

**POST** `/config/embedding`

更新嵌入模型设置。

#### 请求体

```json
{
  "llm_type": "openai",
  "api_key": "sk-your-api-key",
  "api_base": "https://api.openai.com/v1",
  "language_model": "text-embedding-3-small"
}
```

### 7. 更新 Reranker 配置

**POST** `/config/rerank`

配置重排序器设置。

#### 请求体（Cohere）

```json
{
  "reranker_type": "cohere",
  "api_key": "your-cohere-key",
  "reranker_model": "rerank-multilingual-v3.0",
  "cohere_base_url": "https://api.cohere.com/v1/rerank"
}
```

#### 请求体（SiliconFlow）

```json
{
  "reranker_type": "siliconflow",
  "api_key": "your-siliconflow-key",
  "reranker_model": "BAAI/bge-reranker-v2-m3"
}
```

---

## 错误响应

所有端点返回标准 HTTP 状态码：

| 代码 | 含义 |
|-----|------|
| 200 | 成功 |
| 201 | 已创建（配置已更新） |
| 400 | 错误请求（无效参数） |
| 500 | 内部服务器错误 |
| 501 | 未实现 |

错误响应格式：
```json
{
  "detail": "描述错误的消息"
}
```

---

## Python 客户端示例

```python
import requests

BASE_URL = "http://localhost:8001"

# 1. 配置图连接
graph_config = {
    "url": "127.0.0.1:8080",
    "name": "hugegraph",
    "user": "admin",
    "pwd": "admin"
}
requests.post(f"{BASE_URL}/config/graph", json=graph_config)

# 2. 执行 RAG 查询
rag_request = {
    "query": "给我讲讲阿尔·帕西诺",
    "graph_only": True,
    "max_graph_items": 30
}
response = requests.post(f"{BASE_URL}/rag", json=rag_request)
print(response.json())

# 3. 从自然语言生成 Gremlin
text2gql_request = {
    "query": "查找所有与阿尔·帕西诺合作的导演",
    "output_types": ["GREMLIN", "RESULT"]
}
response = requests.post(f"{BASE_URL}/text2gremlin", json=text2gql_request)
print(response.json())
```

---

## 另见

- [配置参考](./config-reference.md) - 完整的 .env 配置指南
- [HugeGraph-LLM 概述](./hugegraph-llm.md) - 架构和功能
- [快速入门指南](./quick_start.md) - Web UI 入门
