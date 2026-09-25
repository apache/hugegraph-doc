# 配置参考

LLMS 索引： [llms.txt](/versions/1.7/cn/llms.txt)

---

HugeGraph-LLM 从 `hugegraph-llm/.env` 读取运行配置。提示词单独保存在 `hugegraph-llm/src/hugegraph_llm/resources/demo/config_prompt.yaml`，不会写入 `.env`。

运行以下命令可按配置类的默认值创建或更新文件：

```bash
cd hugegraph-ai/hugegraph-llm
python -m hugegraph_llm.config.generate --update
```

`.env` 包含密钥和密码，不要提交到版本库。

## 基础选项

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `LANGUAGE` | `EN` | 提示词语言，可选 `EN`、`CN` |
| `CHAT_LLM_TYPE` | `openai` | 回答模型，可选 `openai`、`litellm`、`ollama/local` |
| `EXTRACT_LLM_TYPE` | `openai` | 信息抽取模型，取值同上 |
| `TEXT2GQL_LLM_TYPE` | `openai` | Text2Gremlin 模型，取值同上 |
| `EMBEDDING_TYPE` | `openai` | 嵌入模型，取值同上，也可以留空 |
| `RERANKER_TYPE` | 空 | 可选 `cohere`、`siliconflow` |
| `KEYWORD_EXTRACT_TYPE` | `llm` | 可选 `llm`、`textrank`、`hybrid` |
| `WINDOW_SIZE` | `3` | TextRank 滑窗，范围 1 到 10 |
| `HYBRID_LLM_WEIGHTS` | `0.5` | hybrid 模式中 LLM 结果的权重，范围 0 到 1 |

## OpenAI 兼容接口

聊天、抽取和 Text2Gremlin 可以使用不同端点、密钥和模型。

| 用途 | API 地址 | 密钥 | 模型 | 最大 token 默认值 |
|---|---|---|---|---|
| 回答 | `OPENAI_CHAT_API_BASE` | `OPENAI_CHAT_API_KEY` | `OPENAI_CHAT_LANGUAGE_MODEL` | `OPENAI_CHAT_TOKENS=8192` |
| 抽取 | `OPENAI_EXTRACT_API_BASE` | `OPENAI_EXTRACT_API_KEY` | `OPENAI_EXTRACT_LANGUAGE_MODEL` | `OPENAI_EXTRACT_TOKENS=256` |
| Text2Gremlin | `OPENAI_TEXT2GQL_API_BASE` | `OPENAI_TEXT2GQL_API_KEY` | `OPENAI_TEXT2GQL_LANGUAGE_MODEL` | `OPENAI_TEXT2GQL_TOKENS=4096` |
| 嵌入 | `OPENAI_EMBEDDING_API_BASE` | `OPENAI_EMBEDDING_API_KEY` | `OPENAI_EMBEDDING_MODEL` | 不适用 |

API 地址默认是 `https://api.openai.com/v1`；三个语言模型默认是 `gpt-4.1-mini`，嵌入模型默认是 `text-embedding-3-small`。

`OPENAI_BASE_URL` 和 `OPENAI_API_KEY` 可作为通用回退值。嵌入模型另有 `OPENAI_EMBEDDING_BASE_URL` 和 `OPENAI_EMBEDDING_API_KEY` 回退值。

## LiteLLM

| 用途 | API 地址 | 密钥 | 模型 | 最大 token 默认值 |
|---|---|---|---|---|
| 回答 | `LITELLM_CHAT_API_BASE` | `LITELLM_CHAT_API_KEY` | `LITELLM_CHAT_LANGUAGE_MODEL` | `LITELLM_CHAT_TOKENS=8192` |
| 抽取 | `LITELLM_EXTRACT_API_BASE` | `LITELLM_EXTRACT_API_KEY` | `LITELLM_EXTRACT_LANGUAGE_MODEL` | `LITELLM_EXTRACT_TOKENS=256` |
| Text2Gremlin | `LITELLM_TEXT2GQL_API_BASE` | `LITELLM_TEXT2GQL_API_KEY` | `LITELLM_TEXT2GQL_LANGUAGE_MODEL` | `LITELLM_TEXT2GQL_TOKENS=4096` |
| 嵌入 | `LITELLM_EMBEDDING_API_BASE` | `LITELLM_EMBEDDING_API_KEY` | `LITELLM_EMBEDDING_MODEL` | 不适用 |

三个语言模型默认是 `openai/gpt-4.1-mini`，嵌入模型默认是 `openai/text-embedding-3-small`。模型名通常使用 `供应商/模型` 格式，具体取值由 LiteLLM 服务决定。

## Ollama

| 用途 | 主机 | 端口 | 模型 |
|---|---|---|---|
| 回答 | `OLLAMA_CHAT_HOST` | `OLLAMA_CHAT_PORT` | `OLLAMA_CHAT_LANGUAGE_MODEL` |
| 抽取 | `OLLAMA_EXTRACT_HOST` | `OLLAMA_EXTRACT_PORT` | `OLLAMA_EXTRACT_LANGUAGE_MODEL` |
| Text2Gremlin | `OLLAMA_TEXT2GQL_HOST` | `OLLAMA_TEXT2GQL_PORT` | `OLLAMA_TEXT2GQL_LANGUAGE_MODEL` |
| 嵌入 | `OLLAMA_EMBEDDING_HOST` | `OLLAMA_EMBEDDING_PORT` | `OLLAMA_EMBEDDING_MODEL` |

主机默认是 `127.0.0.1`，端口默认是 `11434`，模型名没有默认值。使用前先在 Ollama 中拉取对应模型。

## 重排序

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `COHERE_BASE_URL` | `https://api.cohere.com/v1/rerank` | Cohere rerank 接口；`CO_API_URL` 可作为回退值 |
| `RERANKER_API_KEY` | 空 | Cohere 或 SiliconFlow 密钥 |
| `RERANKER_MODEL` | 空 | 服务端支持的模型名 |

## HugeGraph 连接与召回限制

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `GRAPH_URL` | `127.0.0.1:8080` | HugeGraph 地址，不拆分为 IP 和端口 |
| `GRAPH_NAME` | `hugegraph` | 图名 |
| `GRAPH_USER` | `admin` | 用户名 |
| `GRAPH_PWD` | `xxx` | 密码 |
| `GRAPH_SPACE` | 空 | GraphSpace 名称 |
| `LIMIT_PROPERTY` | `False` | 是否限制返回属性；配置类按字符串读取 |
| `MAX_GRAPH_PATH` | `10` | 最大图路径长度 |
| `MAX_GRAPH_ITEMS` | `30` | 图召回的最大项目数 |
| `EDGE_LIMIT_PRE_LABEL` | `8` | 每个边标签的返回上限 |
| `VECTOR_DIS_THRESHOLD` | `0.9` | 向量距离阈值；超过阈值的结果会被忽略 |
| `TOPK_PER_KEYWORD` | `1` | 每个关键词的候选数 |
| `TOPK_RETURN_RESULTS` | `20` | 重排序后返回的结果数 |

## 外部向量数据库

默认实现可以使用本地 FAISS。启用可选依赖后还可配置：

| 配置项 | 默认值 |
|---|---|
| `QDRANT_HOST` | 空 |
| `QDRANT_PORT` | `6333` |
| `QDRANT_API_KEY` | 空 |
| `MILVUS_HOST` | 空 |
| `MILVUS_PORT` | `19530` |
| `MILVUS_USER` | 空 |
| `MILVUS_PASSWORD` | 空 |

安装对应依赖：

```bash
cd hugegraph-ai
uv sync --package hugegraph-llm --extra vectordb
```

## 登录与日志接口

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `ENABLE_LOGIN` | `False` | 是否要求 Bearer token；配置类按字符串读取 |
| `USER_TOKEN` | `4321` | Web 页面和普通 API 的 token |
| `ADMIN_TOKEN` | `xxxx` | `/logs` 使用的管理员 token |

`ADMIN_TOKEN` 为空或仍为 `xxxx` 时，`/logs` 会直接返回 403。生产环境应同时替换用户 token 和管理员 token。

## 最小 OpenAI 配置

```properties
LANGUAGE=CN
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

## 配置加载

配置类先提供代码默认值，再从 `.env` 和进程环境读取覆盖值。Web 页面和配置 API 可以在运行时更新当前设置，并把受支持的字段同步回 `.env`。手工改动 `.env` 后应重启服务；提示词 YAML 可由页面加载逻辑刷新。

配置定义位于：

- `hugegraph-llm/src/hugegraph_llm/config/llm_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/hugegraph_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/admin_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/prompt_config.py`
