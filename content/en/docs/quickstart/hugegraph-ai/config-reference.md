---
title: "Configuration Reference"
linkTitle: "Configuration Reference"
weight: 4
---

HugeGraph-LLM separates deployment defaults from application-saved connections. This reference describes the current 1.8 configuration contract.
For Kubernetes installation and storage, use the [unified Helm guide](/docs/quickstart/hugegraph/hugegraph-helm/#8-graphrag).

## Saved Connections {#saved-connections}

Save model connections through the Web UI or [configuration API](./rest-api.md#runtime-configuration).
The application writes complete connections to `settings.yaml`, then uses them immediately and after restarts or Helm upgrades.
Saved connections take precedence over process environment/Secrets, `.env`, and code defaults, in that order.
Changing a Helm bootstrap value therefore does not replace a connection already saved in the application.

`Save configuration` validates format without contacting the model. Use `Test saved connection` separately; a failed test leaves the saved connection intact.

Keys are not displayed. A blank UI key or omitted API `api_key` retains the current key; `Clear API key` or `clear_api_key: true` removes it.
Changing a destination/provider requires a replacement key or explicit clearing. Changing only the model at the same endpoint can retain the key.
A connection saved with an unchanged deployment-injected key keeps a reference to that environment variable; restart the Pod after rotating the Secret.

Extraction and Text2Gremlin follow Chat unless configured independently. `Use Chat connection` restores inheritance.
Embeddings and reranking remain separate. Login and Thin API write-enable flags remain deployment-owned.
For an offline reset, remove the corresponding connection group from `settings.yaml` and restart; do not edit it while the application is saving.

## Configuration Files {#configuration-files}

Set `HUGEGRAPH_LLM_RESOURCE_PATH` before startup to put saved settings, prompts, indexes and generated files in a writable persistent directory.
Bundled examples remain readable from the installed package if absent from that directory; startup does not copy or create configuration files.

| File | Path selection, in priority order |
| --- | --- |
| Saved connections | `HUGEGRAPH_LLM_SETTINGS_PATH`; otherwise `settings.yaml` under the resource root, or beside the selected `.env` |
| Deployment defaults | `HUGEGRAPH_LLM_ENV_PATH`; resource root's `.env`; source checkout's `hugegraph-llm/.env`; current working directory's `.env` |
| Prompts | `HUGEGRAPH_LLM_PROMPT_CONFIG_PATH`; resource root's `demo/config_prompt.yaml`; source resource file; `${XDG_CONFIG_HOME:-~/.config}/hugegraph-llm/config_prompt.yaml` |
{.wide .expand}

Path overrides expand `~`; relative paths use the process working directory. Set overrides in the process environment before importing configuration,
not inside the `.env` file whose location they select. Read-only `.env`/Secret mounts work as bootstrap defaults; saved settings and explicit prompt edits need
writable storage.
Persist the whole resource directory or mount its writable files deliberately. Both `.env` and `settings.yaml` can contain credentials; restrict volume and
backup access.

Export the resolved configuration explicitly when a deployment file is needed:

```bash
cd hugegraph-ai/hugegraph-llm
python -m hugegraph_llm.config.generate --update
```

The generator asks before replacing existing files. This is an explicit export, not a required startup step or the destination for ordinary UI saves.

## Basic Options {#basic-options}

| Setting | Default | Description |
|---|---|---|
| `LANGUAGE` | `EN` | Prompt language: `EN` or `CN` |
| `CHAT_LLM_TYPE` | `openai` | Answer model: `openai` or `ollama/local` |
| `EXTRACT_LLM_TYPE` | `openai` | Information extraction model; same choices as above |
| `TEXT2GQL_LLM_TYPE` | `openai` | Text2Gremlin model; same choices as above |
| `EMBEDDING_TYPE` | `openai` | Embedding model; same choices as above |
| `EXTRACT_USE_CHAT` / `TEXT2GQL_USE_CHAT` | `True` | Follow Chat unless a role has its own configuration |
| `RERANKER_TYPE` | empty | `cohere` or `siliconflow` |
| `KEYWORD_EXTRACT_TYPE` | `llm` | `llm`, `textrank`, or `hybrid` |
| `WINDOW_SIZE` | `3` | TextRank window size, from 1 to 10 |
| `HYBRID_LLM_WEIGHTS` | `0.5` | Weight of LLM results in hybrid mode, from 0 to 1 |

## OpenAI-Compatible APIs {#openai-compatible-apis}

Chat, extraction, and Text2Gremlin can use different endpoints, keys, and models.

| Purpose | API base | Key | Model | Default maximum tokens |
|---|---|---|---|---|
| Answer | `OPENAI_CHAT_API_BASE` | `OPENAI_CHAT_API_KEY` | `OPENAI_CHAT_LANGUAGE_MODEL` | `OPENAI_CHAT_TOKENS=8192` |
| Extraction | `OPENAI_EXTRACT_API_BASE` | `OPENAI_EXTRACT_API_KEY` | `OPENAI_EXTRACT_LANGUAGE_MODEL` | `OPENAI_EXTRACT_TOKENS=256` |
| Text2Gremlin | `OPENAI_TEXT2GQL_API_BASE` | `OPENAI_TEXT2GQL_API_KEY` | `OPENAI_TEXT2GQL_LANGUAGE_MODEL` | `OPENAI_TEXT2GQL_TOKENS=4096` |
| Embedding | `OPENAI_EMBEDDING_API_BASE` | `OPENAI_EMBEDDING_API_KEY` | `OPENAI_EMBEDDING_MODEL` | Not applicable |
{.td-table--wide}

The default API base is `https://api.openai.com/v1`. The default language model for all three tasks is `gpt-4.1-mini`, and the default embedding model is `text-embedding-3-small`.

`OPENAI_BASE_URL` and `OPENAI_API_KEY` provide general fallback values. Embeddings also support `OPENAI_EMBEDDING_BASE_URL` and `OPENAI_EMBEDDING_API_KEY` as fallback values.

## LiteLLM {#litellm}

The application has no `litellm` provider or `LITELLM_*` settings. To use a LiteLLM proxy, select `openai` and configure its OpenAI-compatible URL,
key and model name. The [standalone SDK](./hugegraph-llm-sdk.md#model-adapters) still offers a `LiteLLMClient` adapter.

## Ollama {#ollama}

| Purpose | Host | Port | Model |
|---|---|---|---|
| Answer | `OLLAMA_CHAT_HOST` | `OLLAMA_CHAT_PORT` | `OLLAMA_CHAT_LANGUAGE_MODEL` |
| Extraction | `OLLAMA_EXTRACT_HOST` | `OLLAMA_EXTRACT_PORT` | `OLLAMA_EXTRACT_LANGUAGE_MODEL` |
| Text2Gremlin | `OLLAMA_TEXT2GQL_HOST` | `OLLAMA_TEXT2GQL_PORT` | `OLLAMA_TEXT2GQL_LANGUAGE_MODEL` |
| Embedding | `OLLAMA_EMBEDDING_HOST` | `OLLAMA_EMBEDDING_PORT` | `OLLAMA_EMBEDDING_MODEL` |
{.td-table--wide}

The default host is `127.0.0.1` and the default port is `11434`. Model names have no defaults; pull the required models in Ollama before use.

## Reranking {#reranking}

| Setting | Default | Description |
|---|---|---|
| `COHERE_BASE_URL` | `https://api.cohere.com/v1/rerank` | Cohere rerank endpoint; `CO_API_URL` is a fallback |
| `RERANKER_API_KEY` | empty | Cohere or SiliconFlow key |
| `RERANKER_MODEL` | empty | Model name supported by the service |

## HugeGraph Connection and Retrieval Limits {#hugegraph-connection-and-retrieval-limits}

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

## Vector Index Backend {#vector-index-backend}

| Setting | Default | Description |
|---|---|---|
| `CUR_VECTOR_INDEX` | `Faiss` | Active vector store: `Faiss`, `Milvus`, or `Qdrant` |
| `QDRANT_HOST` | empty | |
| `QDRANT_PORT` | `6333` | |
| `QDRANT_API_KEY` | empty | |
| `MILVUS_HOST` | empty | |
| `MILVUS_PORT` | `19530` | |
| `MILVUS_USER` | empty | |
| `MILVUS_PASSWORD` | empty | |

FAISS is local and needs no extra dependency. Selecting `Milvus` or `Qdrant` without the optional dependencies raises an error that names the missing package, so install them first:

```bash
cd hugegraph-ai
uv sync --package hugegraph-llm --extra vectordb
```

The same choice is available in the `5. Set up the vector engine.` panel of the Web UI, which also persists the connection settings for the selected engine.

## Login and Log API {#login-and-log-api}

| Setting | Default | Description |
|---|---|---|
| `ENABLE_LOGIN` | `False` | Whether to require a Bearer token; read as a string by the configuration class |
| `USER_TOKEN` | `4321` | Token for the Web UI and regular APIs |
| `ADMIN_TOKEN` | `xxxx` | Administrator token used by `/logs` |

`/logs` returns 403 when `ADMIN_TOKEN` is empty or still set to `xxxx`.

> [!WARNING]
> In production, set `ENABLE_LOGIN=True`, replace `USER_TOKEN` and `ADMIN_TOKEN`, and enforce a source IP allowlist at the firewall or network entry point. This protects only HugeGraph-LLM. Separately enable [Server authentication and authorization](/docs/config/config-authentication/), retain Server audit logs (normally `audit-*.log`), and grant `GRAPH_USER` minimum required permissions. The two services use different credentials.

## Minimal OpenAI Configuration {#minimal-openai-configuration}

```properties
LANGUAGE=EN
CHAT_LLM_TYPE=openai
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

## Configuration Loading {#configuration-loading}

Explicit Python configuration arguments take precedence, followed by saved application connections, process environment, `.env`, and defaults.
Keys are case-insensitive. Empty deployment values are normally ignored; an explicitly empty `GRAPH_PWD` is retained for an unauthenticated Server.
Role-specific extraction/Text2GQL settings select an independent connection unless the corresponding `*_USE_CHAT` flag explicitly enables inheritance.

Deployment fields can combine across sources, such as an endpoint from `.env` and its key from a Secret.
A different endpoint/provider supplied by the environment does not inherit a lower-priority file credential.
Saved connections retain their own destination and key/reference together. Hand-edited deployment files require a restart;
UI/API saves update supported connections without rewriting `.env` or process environment variables.

Configuration definitions are in:

- `hugegraph-llm/src/hugegraph_llm/config/llm_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/hugegraph_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/index_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/admin_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/prompt_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/models/base_config.py` for the loading and file-sync behaviour
