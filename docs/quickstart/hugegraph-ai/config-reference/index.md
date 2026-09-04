# Configuration Reference

LLMS index: [llms.txt](/llms.txt)

---

HugeGraph-LLM reads runtime settings from `hugegraph-llm/.env`. Prompts are stored separately in `hugegraph-llm/src/hugegraph_llm/resources/demo/config_prompt.yaml` and are not written to `.env`.

Create or update the files from configuration-class defaults with:

```bash
cd hugegraph-ai/hugegraph-llm
python -m hugegraph_llm.config.generate --update
```

`.env` contains keys and passwords. Do not commit it to version control.

## Basic Options

| Setting | Default | Description |
|---|---|---|
| `LANGUAGE` | `EN` | Prompt language: `EN` or `CN` |
| `CHAT_LLM_TYPE` | `openai` | Answer model: `openai`, `litellm`, or `ollama/local` |
| `EXTRACT_LLM_TYPE` | `openai` | Information extraction model; same choices as above |
| `TEXT2GQL_LLM_TYPE` | `openai` | Text2Gremlin model; same choices as above |
| `EMBEDDING_TYPE` | `openai` | Embedding model; same choices as above, or empty |
| `RERANKER_TYPE` | empty | `cohere` or `siliconflow` |
| `KEYWORD_EXTRACT_TYPE` | `llm` | `llm`, `textrank`, or `hybrid` |
| `WINDOW_SIZE` | `3` | TextRank window size, from 1 to 10 |
| `HYBRID_LLM_WEIGHTS` | `0.5` | Weight of LLM results in hybrid mode, from 0 to 1 |

## OpenAI-Compatible APIs

Chat, extraction, and Text2Gremlin can use different endpoints, keys, and models.

| Purpose | API base | Key | Model | Default maximum tokens |
|---|---|---|---|---|
| Answer | `OPENAI_CHAT_API_BASE` | `OPENAI_CHAT_API_KEY` | `OPENAI_CHAT_LANGUAGE_MODEL` | `OPENAI_CHAT_TOKENS=8192` |
| Extraction | `OPENAI_EXTRACT_API_BASE` | `OPENAI_EXTRACT_API_KEY` | `OPENAI_EXTRACT_LANGUAGE_MODEL` | `OPENAI_EXTRACT_TOKENS=256` |
| Text2Gremlin | `OPENAI_TEXT2GQL_API_BASE` | `OPENAI_TEXT2GQL_API_KEY` | `OPENAI_TEXT2GQL_LANGUAGE_MODEL` | `OPENAI_TEXT2GQL_TOKENS=4096` |
| Embedding | `OPENAI_EMBEDDING_API_BASE` | `OPENAI_EMBEDDING_API_KEY` | `OPENAI_EMBEDDING_MODEL` | Not applicable |

The default API base is `https://api.openai.com/v1`. The default language model for all three tasks is `gpt-4.1-mini`, and the default embedding model is `text-embedding-3-small`.

`OPENAI_BASE_URL` and `OPENAI_API_KEY` provide general fallback values. Embeddings also support `OPENAI_EMBEDDING_BASE_URL` and `OPENAI_EMBEDDING_API_KEY` as fallback values.

## LiteLLM

| Purpose | API base | Key | Model | Default maximum tokens |
|---|---|---|---|---|
| Answer | `LITELLM_CHAT_API_BASE` | `LITELLM_CHAT_API_KEY` | `LITELLM_CHAT_LANGUAGE_MODEL` | `LITELLM_CHAT_TOKENS=8192` |
| Extraction | `LITELLM_EXTRACT_API_BASE` | `LITELLM_EXTRACT_API_KEY` | `LITELLM_EXTRACT_LANGUAGE_MODEL` | `LITELLM_EXTRACT_TOKENS=256` |
| Text2Gremlin | `LITELLM_TEXT2GQL_API_BASE` | `LITELLM_TEXT2GQL_API_KEY` | `LITELLM_TEXT2GQL_LANGUAGE_MODEL` | `LITELLM_TEXT2GQL_TOKENS=4096` |
| Embedding | `LITELLM_EMBEDDING_API_BASE` | `LITELLM_EMBEDDING_API_KEY` | `LITELLM_EMBEDDING_MODEL` | Not applicable |

The default language model is `openai/gpt-4.1-mini`, and the default embedding model is `openai/text-embedding-3-small`. Model names generally use the `provider/model` form; supported values depend on the LiteLLM service.

## Ollama

| Purpose | Host | Port | Model |
|---|---|---|---|
| Answer | `OLLAMA_CHAT_HOST` | `OLLAMA_CHAT_PORT` | `OLLAMA_CHAT_LANGUAGE_MODEL` |
| Extraction | `OLLAMA_EXTRACT_HOST` | `OLLAMA_EXTRACT_PORT` | `OLLAMA_EXTRACT_LANGUAGE_MODEL` |
| Text2Gremlin | `OLLAMA_TEXT2GQL_HOST` | `OLLAMA_TEXT2GQL_PORT` | `OLLAMA_TEXT2GQL_LANGUAGE_MODEL` |
| Embedding | `OLLAMA_EMBEDDING_HOST` | `OLLAMA_EMBEDDING_PORT` | `OLLAMA_EMBEDDING_MODEL` |

The default host is `127.0.0.1` and the default port is `11434`. Model names have no defaults; pull the required models in Ollama before use.

## Reranking

| Setting | Default | Description |
|---|---|---|
| `COHERE_BASE_URL` | `https://api.cohere.com/v1/rerank` | Cohere rerank endpoint; `CO_API_URL` is a fallback |
| `RERANKER_API_KEY` | empty | Cohere or SiliconFlow key |
| `RERANKER_MODEL` | empty | Model name supported by the service |

## HugeGraph Connection and Retrieval Limits

| Setting | Default | Description |
|---|---|---|
| `GRAPH_URL` | `127.0.0.1:8080` | HugeGraph address; it is not split into IP and port |
| `GRAPH_NAME` | `hugegraph` | Graph name |
| `GRAPH_USER` | `admin` | User name |
| `GRAPH_PWD` | `xxx` | Password |
| `GRAPH_SPACE` | empty | GraphSpace name |
| `LIMIT_PROPERTY` | `False` | Whether to limit returned properties; read as a string by the configuration class |
| `MAX_GRAPH_PATH` | `10` | Maximum graph path length |
| `MAX_GRAPH_ITEMS` | `30` | Maximum number of graph retrieval items |
| `EDGE_LIMIT_PRE_LABEL` | `8` | Result limit for each edge label |
| `VECTOR_DIS_THRESHOLD` | `0.9` | Results beyond this vector-distance threshold are ignored |
| `TOPK_PER_KEYWORD` | `1` | Candidates per keyword |
| `TOPK_RETURN_RESULTS` | `20` | Results returned after reranking |

## External Vector Databases

The default implementation can use local FAISS. After enabling optional dependencies, the following settings are also available:

| Setting | Default |
|---|---|
| `QDRANT_HOST` | empty |
| `QDRANT_PORT` | `6333` |
| `QDRANT_API_KEY` | empty |
| `MILVUS_HOST` | empty |
| `MILVUS_PORT` | `19530` |
| `MILVUS_USER` | empty |
| `MILVUS_PASSWORD` | empty |

```bash
cd hugegraph-ai
uv sync --package hugegraph-llm --extra vectordb
```

## Login and Log API

| Setting | Default | Description |
|---|---|---|
| `ENABLE_LOGIN` | `False` | Whether to require a Bearer token; read as a string by the configuration class |
| `USER_TOKEN` | `4321` | Token for the Web UI and regular APIs |
| `ADMIN_TOKEN` | `xxxx` | Administrator token used by `/logs` |

`/logs` returns 403 when `ADMIN_TOKEN` is empty or still set to `xxxx`. Replace both the user and administrator tokens in production.

## Minimal OpenAI Configuration

```properties
LANGUAGE=EN
CHAT_LLM_TYPE=openai
EXTRACT_LLM_TYPE=openai
TEXT2GQL_LLM_TYPE=openai
EMBEDDING_TYPE=openai

OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_LANGUAGE_MODEL=gpt-4.1-mini
OPENAI_EXTRACT_LANGUAGE_MODEL=gpt-4.1-mini
OPENAI_TEXT2GQL_LANGUAGE_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

GRAPH_URL=127.0.0.1:8080
GRAPH_NAME=hugegraph
GRAPH_USER=admin
GRAPH_PWD=your-password
```

## Configuration Loading

Configuration classes supply code defaults and then apply overrides from `.env` and the process environment. The Web UI and configuration APIs can update current settings at runtime and write supported fields back to `.env`. Restart the service after editing `.env` manually; prompt YAML can be refreshed by the page-loading logic.

Configuration definitions are in:

- `hugegraph-llm/src/hugegraph_llm/config/llm_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/hugegraph_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/admin_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/prompt_config.py`
