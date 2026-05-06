---
title: "配置参考"
linkTitle: "配置参考"
weight: 4
---

本文档提供 HugeGraph-LLM 所有配置选项的完整参考。

## 配置文件

- **环境文件**：`.env`（从模板创建或自动生成)
- **提示词配置**：`src/hugegraph_llm/resources/demo/config_prompt.yaml`

> [!TIP]
> 运行 `python -m hugegraph_llm.config.generate --update` 可自动生成或更新带有默认值的配置文件。

## 环境变量概览

### 1. 语言和模型类型选择

```bash
# 提示词语言（影响系统提示词和生成文本）
LANGUAGE=EN                     # 选项: EN | CN

# 不同任务的 LLM 类型
CHAT_LLM_TYPE=openai           # 对话/RAG: openai | litellm | ollama/local
EXTRACT_LLM_TYPE=openai        # 实体抽取: openai | litellm | ollama/local
TEXT2GQL_LLM_TYPE=openai       # 文本转 Gremlin: openai | litellm | ollama/local

# 嵌入模型类型
EMBEDDING_TYPE=openai          # 选项: openai | litellm | ollama/local

# Reranker 类型（可选）
RERANKER_TYPE=                 # 选项: cohere | siliconflow | (留空表示无)
```

### 2. OpenAI 配置

每个 LLM 任务（chat、extract、text2gql）都有独立配置：

#### 2.1 Chat LLM（RAG 答案生成）

```bash
OPENAI_CHAT_API_BASE=https://api.openai.com/v1
OPENAI_CHAT_API_KEY=sk-your-api-key-here
OPENAI_CHAT_LANGUAGE_MODEL=gpt-4o-mini
OPENAI_CHAT_TOKENS=8192        # 对话响应的最大 tokens
```

#### 2.2 Extract LLM（实体和关系抽取）

```bash
OPENAI_EXTRACT_API_BASE=https://api.openai.com/v1
OPENAI_EXTRACT_API_KEY=sk-your-api-key-here
OPENAI_EXTRACT_LANGUAGE_MODEL=gpt-4o-mini
OPENAI_EXTRACT_TOKENS=1024     # 抽取任务的最大 tokens
```

#### 2.3 Text2GQL LLM（自然语言转 Gremlin）

```bash
OPENAI_TEXT2GQL_API_BASE=https://api.openai.com/v1
OPENAI_TEXT2GQL_API_KEY=sk-your-api-key-here
OPENAI_TEXT2GQL_LANGUAGE_MODEL=gpt-4o-mini
OPENAI_TEXT2GQL_TOKENS=4096    # 查询生成的最大 tokens
```

#### 2.4 嵌入模型

```bash
OPENAI_EMBEDDING_API_BASE=https://api.openai.com/v1
OPENAI_EMBEDDING_API_KEY=sk-your-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

> [!NOTE]
> 您可以为每个任务使用不同的 API 密钥/端点，以优化成本或使用专用模型。

### 3. LiteLLM 配置（多供应商支持）

LiteLLM 支持统一访问 100 多个 LLM 供应商（OpenAI、Anthropic、Google、Azure 等）。

#### 3.1 Chat LLM

```bash
LITELLM_CHAT_API_BASE=http://localhost:4000       # LiteLLM 代理 URL
LITELLM_CHAT_API_KEY=sk-litellm-key              # LiteLLM API 密钥
LITELLM_CHAT_LANGUAGE_MODEL=anthropic/claude-3-5-sonnet-20241022
LITELLM_CHAT_TOKENS=8192
```

#### 3.2 Extract LLM

```bash
LITELLM_EXTRACT_API_BASE=http://localhost:4000
LITELLM_EXTRACT_API_KEY=sk-litellm-key
LITELLM_EXTRACT_LANGUAGE_MODEL=openai/gpt-4o-mini
LITELLM_EXTRACT_TOKENS=256
```

#### 3.3 Text2GQL LLM

```bash
LITELLM_TEXT2GQL_API_BASE=http://localhost:4000
LITELLM_TEXT2GQL_API_KEY=sk-litellm-key
LITELLM_TEXT2GQL_LANGUAGE_MODEL=openai/gpt-4o-mini
LITELLM_TEXT2GQL_TOKENS=4096
```

#### 3.4 嵌入模型

```bash
LITELLM_EMBEDDING_API_BASE=http://localhost:4000
LITELLM_EMBEDDING_API_KEY=sk-litellm-key
LITELLM_EMBEDDING_MODEL=openai/text-embedding-3-small
```

**模型格式**: `供应商/模型名称`

示例：
- `openai/gpt-4o-mini`
- `anthropic/claude-3-5-sonnet-20241022`
- `google/gemini-2.0-flash-exp`
- `azure/gpt-4`

完整列表请参阅 [LiteLLM Providers](https://docs.litellm.ai/docs/providers)。

### 4. Ollama 配置（本地部署）

使用 Ollama 运行本地 LLM，确保隐私和成本控制。

#### 4.1 Chat LLM

```bash
OLLAMA_CHAT_HOST=127.0.0.1
OLLAMA_CHAT_PORT=11434
OLLAMA_CHAT_LANGUAGE_MODEL=llama3.1:8b
```

#### 4.2 Extract LLM

```bash
OLLAMA_EXTRACT_HOST=127.0.0.1
OLLAMA_EXTRACT_PORT=11434
OLLAMA_EXTRACT_LANGUAGE_MODEL=llama3.1:8b
```

#### 4.3 Text2GQL LLM

```bash
OLLAMA_TEXT2GQL_HOST=127.0.0.1
OLLAMA_TEXT2GQL_PORT=11434
OLLAMA_TEXT2GQL_LANGUAGE_MODEL=qwen2.5-coder:7b
```

#### 4.4 嵌入模型

```bash
OLLAMA_EMBEDDING_HOST=127.0.0.1
OLLAMA_EMBEDDING_PORT=11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

> [!TIP]
> 下载模型：`ollama pull llama3.1:8b` 或 `ollama pull qwen2.5-coder:7b`

### 5. Reranker 配置

Reranker 通过根据相关性重新排序检索结果来提高 RAG 准确性。

#### 5.1 Cohere Reranker

```bash
RERANKER_TYPE=cohere
COHERE_BASE_URL=https://api.cohere.com/v1/rerank
RERANKER_API_KEY=your-cohere-api-key
RERANKER_MODEL=rerank-english-v3.0
```

可用模型：
- `rerank-english-v3.0`（英文）
- `rerank-multilingual-v3.0`（100+ 种语言）

#### 5.2 SiliconFlow Reranker

```bash
RERANKER_TYPE=siliconflow
RERANKER_API_KEY=your-siliconflow-api-key
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

### 6. HugeGraph 连接

配置与 HugeGraph 服务器实例的连接。

```bash
# 服务器连接
GRAPH_IP=127.0.0.1
GRAPH_PORT=8080
GRAPH_NAME=hugegraph            # 图实例名称
GRAPH_USER=admin                # 用户名
GRAPH_PWD=admin-password        # 密码
GRAPH_SPACE=                    # 图空间（可选，用于多租户）
```

### 7. 查询参数

控制图遍历行为和结果限制。

```bash
# 图遍历限制
MAX_GRAPH_PATH=10               # 图查询的最大路径深度
MAX_GRAPH_ITEMS=30              # 从图中检索的最大项数
EDGE_LIMIT_PRE_LABEL=8          # 每个标签类型的最大边数

# 属性过滤
LIMIT_PROPERTY=False            # 限制结果中的属性（True/False）
```

### 8. 向量搜索配置

配置向量相似性搜索参数。

```bash
# 向量搜索阈值
VECTOR_DIS_THRESHOLD=0.9        # 最小余弦相似度（0-1，越高越严格）
TOPK_PER_KEYWORD=1              # 每个提取关键词的 Top-K 结果
```

### 9. Rerank 配置

```bash
# Rerank 结果限制
TOPK_RETURN_RESULTS=20          # 重排序后的 top 结果数
```

## 配置优先级

系统按以下顺序加载配置（后面的来源覆盖前面的）：

1. **默认值**（在 `*_config.py` 文件中）
2. **环境变量**（来自 `.env` 文件）
3. **运行时更新**（通过 Web UI 或 API 调用）

## 配置示例

### 最小配置（OpenAI）

```bash
# 语言
LANGUAGE=EN

# LLM 类型
CHAT_LLM_TYPE=openai
EXTRACT_LLM_TYPE=openai
TEXT2GQL_LLM_TYPE=openai
EMBEDDING_TYPE=openai

# OpenAI 凭据（所有任务共用一个密钥）
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_LANGUAGE_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# HugeGraph 连接
GRAPH_IP=127.0.0.1
GRAPH_PORT=8080
GRAPH_NAME=hugegraph
GRAPH_USER=admin
GRAPH_PWD=admin
```

### 生产环境配置（LiteLLM + Reranker）

```bash
# 双语支持
LANGUAGE=EN

# 灵活使用 LiteLLM
CHAT_LLM_TYPE=litellm
EXTRACT_LLM_TYPE=litellm
TEXT2GQL_LLM_TYPE=litellm
EMBEDDING_TYPE=litellm

# LiteLLM 代理
LITELLM_CHAT_API_BASE=http://localhost:4000
LITELLM_CHAT_API_KEY=sk-litellm-master-key
LITELLM_CHAT_LANGUAGE_MODEL=anthropic/claude-3-5-sonnet-20241022
LITELLM_CHAT_TOKENS=8192

LITELLM_EXTRACT_API_BASE=http://localhost:4000
LITELLM_EXTRACT_API_KEY=sk-litellm-master-key
LITELLM_EXTRACT_LANGUAGE_MODEL=openai/gpt-4o-mini
LITELLM_EXTRACT_TOKENS=256

LITELLM_TEXT2GQL_API_BASE=http://localhost:4000
LITELLM_TEXT2GQL_API_KEY=sk-litellm-master-key
LITELLM_TEXT2GQL_LANGUAGE_MODEL=openai/gpt-4o-mini
LITELLM_TEXT2GQL_TOKENS=4096

LITELLM_EMBEDDING_API_BASE=http://localhost:4000
LITELLM_EMBEDDING_API_KEY=sk-litellm-master-key
LITELLM_EMBEDDING_MODEL=openai/text-embedding-3-small

# Cohere Reranker 提高准确性
RERANKER_TYPE=cohere
COHERE_BASE_URL=https://api.cohere.com/v1/rerank
RERANKER_API_KEY=your-cohere-key
RERANKER_MODEL=rerank-multilingual-v3.0

# 带认证的 HugeGraph
GRAPH_IP=prod-hugegraph.example.com
GRAPH_PORT=8080
GRAPH_NAME=production_graph
GRAPH_USER=rag_user
GRAPH_PWD=secure-password
GRAPH_SPACE=prod_space

# 优化的查询参数
MAX_GRAPH_PATH=15
MAX_GRAPH_ITEMS=50
VECTOR_DIS_THRESHOLD=0.85
TOPK_RETURN_RESULTS=30
```

### 本地/离线配置（Ollama）

```bash
# 语言
LANGUAGE=EN

# 全部通过 Ollama 使用本地模型
CHAT_LLM_TYPE=ollama/local
EXTRACT_LLM_TYPE=ollama/local
TEXT2GQL_LLM_TYPE=ollama/local
EMBEDDING_TYPE=ollama/local

# Ollama 端点
OLLAMA_CHAT_HOST=127.0.0.1
OLLAMA_CHAT_PORT=11434
OLLAMA_CHAT_LANGUAGE_MODEL=llama3.1:8b

OLLAMA_EXTRACT_HOST=127.0.0.1
OLLAMA_EXTRACT_PORT=11434
OLLAMA_EXTRACT_LANGUAGE_MODEL=llama3.1:8b

OLLAMA_TEXT2GQL_HOST=127.0.0.1
OLLAMA_TEXT2GQL_PORT=11434
OLLAMA_TEXT2GQL_LANGUAGE_MODEL=qwen2.5-coder:7b

OLLAMA_EMBEDDING_HOST=127.0.0.1
OLLAMA_EMBEDDING_PORT=11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# 离线环境不使用 reranker
RERANKER_TYPE=

# 本地 HugeGraph
GRAPH_IP=127.0.0.1
GRAPH_PORT=8080
GRAPH_NAME=hugegraph
GRAPH_USER=admin
GRAPH_PWD=admin
```

## 配置验证

修改 `.env` 后，验证配置：

1. **通过 Web UI**：访问 `http://localhost:8001` 并检查设置面板
2. **通过 Python**：
```python
from hugegraph_llm.config import settings
print(settings.llm_config)
print(settings.hugegraph_config)
```
3. **通过 REST API**：
```bash
curl http://localhost:8001/config
```

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| "API key not found" | 检查 `.env` 中的 `*_API_KEY` 是否正确设置 |
| "Connection refused" | 验证 `GRAPH_IP` 和 `GRAPH_PORT` 是否正确 |
| "Model not found" | 对于 Ollama：运行 `ollama pull <模型名称>` |
| "Rate limit exceeded" | 减少 `MAX_GRAPH_ITEMS` 或使用不同的 API 密钥 |
| "Embedding dimension mismatch" | 删除现有向量并使用正确模型重建 |

## 另见

- [HugeGraph-LLM 概述](./hugegraph-llm.md)
- [REST API 参考](./rest-api.md)
- [快速入门指南](./quick_start.md)
