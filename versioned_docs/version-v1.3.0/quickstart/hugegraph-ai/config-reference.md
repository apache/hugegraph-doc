---
title: "Configuration Reference"
linkTitle: "Configuration Reference"
weight: 4
---

This document provides a comprehensive reference for all configuration options in HugeGraph-LLM.

## Configuration Files

- **Environment File**: `.env` (created from template or auto-generated)
- **Prompt Configuration**: `src/hugegraph_llm/resources/demo/config_prompt.yaml`

> [!TIP]
> Run `python -m hugegraph_llm.config.generate --update` to auto-generate or update configuration files with defaults.

## Environment Variables Overview

### 1. Language and Model Type Selection

```bash
# Prompt language (affects system prompts and generated text)
LANGUAGE=EN                     # Options: EN | CN

# LLM Type for different tasks
CHAT_LLM_TYPE=openai           # Chat/RAG: openai | litellm | ollama/local
EXTRACT_LLM_TYPE=openai        # Entity extraction: openai | litellm | ollama/local
TEXT2GQL_LLM_TYPE=openai       # Text2Gremlin: openai | litellm | ollama/local

# Embedding type
EMBEDDING_TYPE=openai          # Options: openai | litellm | ollama/local

# Reranker type (optional)
RERANKER_TYPE=                 # Options: cohere | siliconflow | (empty for none)
```

### 2. OpenAI Configuration

Each LLM task (chat, extract, text2gql) has independent configuration:

#### 2.1 Chat LLM (RAG Answer Generation)

```bash
OPENAI_CHAT_API_BASE=https://api.openai.com/v1
OPENAI_CHAT_API_KEY=sk-your-api-key-here
OPENAI_CHAT_LANGUAGE_MODEL=gpt-4o-mini
OPENAI_CHAT_TOKENS=8192        # Max tokens for chat responses
```

#### 2.2 Extract LLM (Entity & Relation Extraction)

```bash
OPENAI_EXTRACT_API_BASE=https://api.openai.com/v1
OPENAI_EXTRACT_API_KEY=sk-your-api-key-here
OPENAI_EXTRACT_LANGUAGE_MODEL=gpt-4o-mini
OPENAI_EXTRACT_TOKENS=1024     # Max tokens for extraction
```

#### 2.3 Text2GQL LLM (Natural Language to Gremlin)

```bash
OPENAI_TEXT2GQL_API_BASE=https://api.openai.com/v1
OPENAI_TEXT2GQL_API_KEY=sk-your-api-key-here
OPENAI_TEXT2GQL_LANGUAGE_MODEL=gpt-4o-mini
OPENAI_TEXT2GQL_TOKENS=4096    # Max tokens for query generation
```

#### 2.4 Embedding Model

```bash
OPENAI_EMBEDDING_API_BASE=https://api.openai.com/v1
OPENAI_EMBEDDING_API_KEY=sk-your-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

> [!NOTE]
> You can use different API keys/endpoints for each task to optimize costs or use specialized models.

### 3. LiteLLM Configuration (Multi-Provider Support)

LiteLLM enables unified access to 100+ LLM providers (OpenAI, Anthropic, Google, Azure, etc.).

#### 3.1 Chat LLM

```bash
LITELLM_CHAT_API_BASE=http://localhost:4000       # LiteLLM proxy URL
LITELLM_CHAT_API_KEY=sk-litellm-key              # LiteLLM API key
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

#### 3.4 Embedding

```bash
LITELLM_EMBEDDING_API_BASE=http://localhost:4000
LITELLM_EMBEDDING_API_KEY=sk-litellm-key
LITELLM_EMBEDDING_MODEL=openai/text-embedding-3-small
```

**Model Format**: `provider/model-name`

Examples:
- `openai/gpt-4o-mini`
- `anthropic/claude-3-5-sonnet-20241022`
- `google/gemini-2.0-flash-exp`
- `azure/gpt-4`

See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for the complete list.

### 4. Ollama Configuration (Local Deployment)

Run local LLMs with Ollama for privacy and cost control.

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

#### 4.4 Embedding

```bash
OLLAMA_EMBEDDING_HOST=127.0.0.1
OLLAMA_EMBEDDING_PORT=11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

> [!TIP]
> Download models: `ollama pull llama3.1:8b` or `ollama pull qwen2.5-coder:7b`

### 5. Reranker Configuration

Rerankers improve RAG accuracy by reordering retrieved results based on relevance.

#### 5.1 Cohere Reranker

```bash
RERANKER_TYPE=cohere
COHERE_BASE_URL=https://api.cohere.com/v1/rerank
RERANKER_API_KEY=your-cohere-api-key
RERANKER_MODEL=rerank-english-v3.0
```

Available models:
- `rerank-english-v3.0` (English)
- `rerank-multilingual-v3.0` (100+ languages)

#### 5.2 SiliconFlow Reranker

```bash
RERANKER_TYPE=siliconflow
RERANKER_API_KEY=your-siliconflow-api-key
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

### 6. HugeGraph Connection

Configure connection to your HugeGraph server instance.

```bash
# Server connection
GRAPH_IP=127.0.0.1
GRAPH_PORT=8080
GRAPH_NAME=hugegraph            # Graph instance name
GRAPH_USER=admin                # Username
GRAPH_PWD=admin-password        # Password
GRAPH_SPACE=                    # Graph space (optional, for multi-tenancy)
```

### 7. Query Parameters

Control graph traversal behavior and result limits.

```bash
# Graph traversal limits
MAX_GRAPH_PATH=10               # Max path depth for graph queries
MAX_GRAPH_ITEMS=30              # Max items to retrieve from graph
EDGE_LIMIT_PRE_LABEL=8          # Max edges per label type

# Property filtering
LIMIT_PROPERTY=False            # Limit properties in results (True/False)
```

### 8. Vector Search Configuration

Configure vector similarity search parameters.

```bash
# Vector search thresholds
VECTOR_DIS_THRESHOLD=0.9        # Min cosine similarity (0-1, higher = stricter)
TOPK_PER_KEYWORD=1              # Top-K results per extracted keyword
```

### 9. Rerank Configuration

```bash
# Rerank result limits
TOPK_RETURN_RESULTS=20          # Number of top results after reranking
```

## Configuration Priority

The system loads configuration in the following order (later sources override earlier ones):

1. **Default Values** (in `*_config.py` files)
2. **Environment Variables** (from `.env` file)
3. **Runtime Updates** (via Web UI or API calls)

## Example Configurations

### Minimal Setup (OpenAI)

```bash
# Language
LANGUAGE=EN

# LLM Types
CHAT_LLM_TYPE=openai
EXTRACT_LLM_TYPE=openai
TEXT2GQL_LLM_TYPE=openai
EMBEDDING_TYPE=openai

# OpenAI Credentials (single key for all tasks)
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_LANGUAGE_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# HugeGraph Connection
GRAPH_IP=127.0.0.1
GRAPH_PORT=8080
GRAPH_NAME=hugegraph
GRAPH_USER=admin
GRAPH_PWD=admin
```

### Production Setup (LiteLLM + Reranker)

```bash
# Bilingual support
LANGUAGE=EN

# LiteLLM for flexibility
CHAT_LLM_TYPE=litellm
EXTRACT_LLM_TYPE=litellm
TEXT2GQL_LLM_TYPE=litellm
EMBEDDING_TYPE=litellm

# LiteLLM Proxy
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

# Cohere Reranker for better accuracy
RERANKER_TYPE=cohere
COHERE_BASE_URL=https://api.cohere.com/v1/rerank
RERANKER_API_KEY=your-cohere-key
RERANKER_MODEL=rerank-multilingual-v3.0

# HugeGraph with authentication
GRAPH_IP=prod-hugegraph.example.com
GRAPH_PORT=8080
GRAPH_NAME=production_graph
GRAPH_USER=rag_user
GRAPH_PWD=secure-password
GRAPH_SPACE=prod_space

# Optimized query parameters
MAX_GRAPH_PATH=15
MAX_GRAPH_ITEMS=50
VECTOR_DIS_THRESHOLD=0.85
TOPK_RETURN_RESULTS=30
```

### Local/Offline Setup (Ollama)

```bash
# Language
LANGUAGE=EN

# All local models via Ollama
CHAT_LLM_TYPE=ollama/local
EXTRACT_LLM_TYPE=ollama/local
TEXT2GQL_LLM_TYPE=ollama/local
EMBEDDING_TYPE=ollama/local

# Ollama endpoints
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

# No reranker for offline setup
RERANKER_TYPE=

# Local HugeGraph
GRAPH_IP=127.0.0.1
GRAPH_PORT=8080
GRAPH_NAME=hugegraph
GRAPH_USER=admin
GRAPH_PWD=admin
```

## Configuration Validation

After modifying `.env`, verify your configuration:

1. **Via Web UI**: Visit `http://localhost:8001` and check the settings panel
2. **Via Python**:
```python
from hugegraph_llm.config import settings
print(settings.llm_config)
print(settings.hugegraph_config)
```
3. **Via REST API**:
```bash
curl http://localhost:8001/config
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key not found" | Check `*_API_KEY` is set correctly in `.env` |
| "Connection refused" | Verify `GRAPH_IP` and `GRAPH_PORT` are correct |
| "Model not found" | For Ollama: run `ollama pull <model-name>` |
| "Rate limit exceeded" | Reduce `MAX_GRAPH_ITEMS` or use different API keys |
| "Embedding dimension mismatch" | Delete existing vectors and rebuild with correct model |

## See Also

- [HugeGraph-LLM Overview](./hugegraph-llm.md)
- [REST API Reference](./rest-api.md)
- [Quick Start Guide](./quick_start.md)
