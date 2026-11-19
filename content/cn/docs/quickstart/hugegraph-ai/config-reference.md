---
title: "配置参考"
linkTitle: "配置参考"
weight: 4
---

HugeGraph-LLM 将部署默认值与应用保存的连接分开管理。本文说明当前 1.8 配置契约；
Kubernetes 安装和存储配置统一见 [Helm 指南](/cn/docs/quickstart/hugegraph/hugegraph-helm/#8-graphrag)。

## 保存连接 {#saved-connections}

通过 Web 页面或[配置 API](./rest-api.md#runtime-configuration)保存模型连接。
应用把完整连接写入 `settings.yaml`，立即生效，并在重启或 Helm 升级后继续使用。
优先级依次为：应用已保存连接、进程环境变量／Secret、`.env`、代码默认值。
因此修改 Helm 引导默认值不会替换应用中已经保存的连接。

`Save configuration` 只校验格式，不连接模型；`Test saved connection` 单独测试，失败不会撤销保存。
已有 key 不回显。页面 key 留空或 API 省略 `api_key` 时保留原 key；`Clear API key` 或 `clear_api_key: true` 才会删除。
更换目标地址或 provider 时必须提供新 key 或明确清除；同一端点仅更换模型可以保留 key。
未替换部署注入的 key 时，保存的是对应环境变量引用；轮换 Secret 后需重建 Pod。

抽取与 Text2Gremlin 未独立配置时跟随 Chat；`Use Chat connection` 可恢复继承。
Embedding、reranker 独立配置，登录和 Thin API 写入开关仍由部署管理。
离线重置连接时，删除 `settings.yaml` 中相应连接组并重启；不要与应用保存操作同时编辑该文件。

## 配置文件 {#configuration-files}

在启动前设置 `HUGEGRAPH_LLM_RESOURCE_PATH`，把设置、提示词、索引和生成文件放到可写持久化目录。
该目录缺少示例资源时，应用从安装包读取；启动不会复制资源或创建默认配置文件。

| 文件 | 路径选择顺序，从高到低 |
| --- | --- |
| 已保存连接 | `HUGEGRAPH_LLM_SETTINGS_PATH`；否则为资源目录的 `settings.yaml`，未指定资源目录时位于所选 `.env` 旁 |
| 部署默认值 | `HUGEGRAPH_LLM_ENV_PATH`；资源目录的 `.env`；源码目录的 `hugegraph-llm/.env`；当前工作目录的 `.env` |
| 提示词 | `HUGEGRAPH_LLM_PROMPT_CONFIG_PATH`；资源目录的 `demo/config_prompt.yaml`；源码资源文件；`${XDG_CONFIG_HOME:-~/.config}/hugegraph-llm/config_prompt.yaml` |
{.wide .expand}

覆盖路径会展开 `~`，相对路径以进程工作目录为基准。环境变量要在导入配置前设置，不能只写入由它们选择的 `.env`。
只读 `.env`／Secret 可以作为部署默认值；保存设置、显式修改提示词则需要可写存储。
请持久化整个资源目录，或明确挂载其中需要写入的文件。`.env` 和 `settings.yaml` 均可能含凭据，应限制卷与备份的访问权限。

需要部署文件时，可显式导出当前解析后的配置：

```bash
cd hugegraph-ai/hugegraph-llm
python -m hugegraph_llm.config.generate --update
```

生成器会在替换已有文件前询问。这是显式导出操作，不是启动前必需步骤，页面日常保存也不会写入这些部署文件。

<span id="基础选项"></span>

## 基础选项 {#basic-options}

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `LANGUAGE` | `EN` | 提示词语言，可选 `EN`、`CN` |
| `CHAT_LLM_TYPE` | `openai` | 回答模型，可选 `openai`、`ollama/local` |
| `EXTRACT_LLM_TYPE` | `openai` | 信息抽取模型，取值同上 |
| `TEXT2GQL_LLM_TYPE` | `openai` | Text2Gremlin 模型，取值同上 |
| `EMBEDDING_TYPE` | `openai` | 嵌入模型，取值同上 |
| `EXTRACT_USE_CHAT` / `TEXT2GQL_USE_CHAT` | `True` | 未独立配置时跟随 Chat |
| `RERANKER_TYPE` | 空 | 可选 `cohere`、`siliconflow` |
| `KEYWORD_EXTRACT_TYPE` | `llm` | 可选 `llm`、`textrank`、`hybrid` |
| `WINDOW_SIZE` | `3` | TextRank 滑窗，范围 1 到 10 |
| `HYBRID_LLM_WEIGHTS` | `0.5` | hybrid 模式中 LLM 结果的权重，范围 0 到 1 |

<span id="openai-兼容接口"></span>

## OpenAI 兼容接口 {#openai-compatible-apis}

聊天、抽取和 Text2Gremlin 可以使用不同端点、密钥和模型。

| 用途 | API 地址 | 密钥 | 模型 | 最大 token 默认值 |
|---|---|---|---|---|
| 回答 | `OPENAI_CHAT_API_BASE` | `OPENAI_CHAT_API_KEY` | `OPENAI_CHAT_LANGUAGE_MODEL` | `OPENAI_CHAT_TOKENS=8192` |
| 抽取 | `OPENAI_EXTRACT_API_BASE` | `OPENAI_EXTRACT_API_KEY` | `OPENAI_EXTRACT_LANGUAGE_MODEL` | `OPENAI_EXTRACT_TOKENS=256` |
| Text2Gremlin | `OPENAI_TEXT2GQL_API_BASE` | `OPENAI_TEXT2GQL_API_KEY` | `OPENAI_TEXT2GQL_LANGUAGE_MODEL` | `OPENAI_TEXT2GQL_TOKENS=4096` |
| 嵌入 | `OPENAI_EMBEDDING_API_BASE` | `OPENAI_EMBEDDING_API_KEY` | `OPENAI_EMBEDDING_MODEL` | 不适用 |
{.td-table--wide}

API 地址默认是 `https://api.openai.com/v1`；三个语言模型默认是 `gpt-4.1-mini`，嵌入模型默认是 `text-embedding-3-small`。

`OPENAI_BASE_URL` 和 `OPENAI_API_KEY` 可作为通用回退值。嵌入模型另有 `OPENAI_EMBEDDING_BASE_URL` 和 `OPENAI_EMBEDDING_API_KEY` 回退值。

## LiteLLM {#litellm}

应用不接受 `litellm` provider 或 `LITELLM_*` 配置。使用 LiteLLM 代理时请选择 `openai`，设置代理的 OpenAI 兼容 URL、key 和模型名。
[独立 SDK](./hugegraph-llm-sdk.md#模型适配器)仍提供 `LiteLLMClient` 适配器。

## Ollama {#ollama}

| 用途 | 主机 | 端口 | 模型 |
|---|---|---|---|
| 回答 | `OLLAMA_CHAT_HOST` | `OLLAMA_CHAT_PORT` | `OLLAMA_CHAT_LANGUAGE_MODEL` |
| 抽取 | `OLLAMA_EXTRACT_HOST` | `OLLAMA_EXTRACT_PORT` | `OLLAMA_EXTRACT_LANGUAGE_MODEL` |
| Text2Gremlin | `OLLAMA_TEXT2GQL_HOST` | `OLLAMA_TEXT2GQL_PORT` | `OLLAMA_TEXT2GQL_LANGUAGE_MODEL` |
| 嵌入 | `OLLAMA_EMBEDDING_HOST` | `OLLAMA_EMBEDDING_PORT` | `OLLAMA_EMBEDDING_MODEL` |
{.td-table--wide}

主机默认是 `127.0.0.1`，端口默认是 `11434`，模型名没有默认值。使用前先在 Ollama 中拉取对应模型。

<span id="重排序"></span>

## 重排序 {#reranking}

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `COHERE_BASE_URL` | `https://api.cohere.com/v1/rerank` | Cohere rerank 接口；`CO_API_URL` 可作为回退值 |
| `RERANKER_API_KEY` | 空 | Cohere 或 SiliconFlow 密钥 |
| `RERANKER_MODEL` | 空 | 服务端支持的模型名 |

<span id="hugegraph-连接与召回限制"></span>

## HugeGraph 连接与召回限制 {#hugegraph-connection-and-retrieval-limits}

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

<span id="向量索引后端"></span>

## 向量索引后端 {#vector-index-backend}

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `CUR_VECTOR_INDEX` | `Faiss` | 当前使用的向量库：`Faiss`、`Milvus` 或 `Qdrant` |
| `QDRANT_HOST` | 空 | |
| `QDRANT_PORT` | `6333` | |
| `QDRANT_API_KEY` | 空 | |
| `MILVUS_HOST` | 空 | |
| `MILVUS_PORT` | `19530` | |
| `MILVUS_USER` | 空 | |
| `MILVUS_PASSWORD` | 空 | |

FAISS 在本地运行，无需额外依赖。未安装可选依赖就选择 `Milvus` 或 `Qdrant` 时，会报错并指出缺少的包，因此需要先安装：

```bash
cd hugegraph-ai
uv sync --package hugegraph-llm --extra vectordb
```

Web 页面的 `5. Set up the vector engine.` 面板提供同样的选择，并会保存所选引擎的连接配置。

<span id="登录与日志接口"></span>

## 登录与日志接口 {#login-and-log-api}

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `ENABLE_LOGIN` | `False` | 是否要求 Bearer token；配置类按字符串读取 |
| `USER_TOKEN` | `4321` | Web 页面和普通 API 的 token |
| `ADMIN_TOKEN` | `xxxx` | `/logs` 使用的管理员 token |

`ADMIN_TOKEN` 为空或仍为 `xxxx` 时，`/logs` 会直接返回 403。

> [!WARNING]
> 生产环境必须设置 `ENABLE_LOGIN=True`，替换 `USER_TOKEN` 和 `ADMIN_TOKEN`，并通过防火墙或网络入口设置来源 IP 白名单。这只保护 HugeGraph-LLM；HugeGraph Server 还必须单独开启认证与授权（见[认证与授权说明](/cn/docs/config/config-authentication/)）并保留 Server 审计日志（标准日志文件为 `audit-*.log`），为 `GRAPH_USER` 设置最小必要权限。两端使用不同的认证凭据。

<span id="最小-openai-配置"></span>

## 最小 OpenAI 配置 {#minimal-openai-configuration}

```properties
LANGUAGE=CN
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

<span id="配置加载"></span>

## 配置加载 {#configuration-loading}

显式传入 Python 配置的参数优先，其后依次为应用已保存连接、进程环境变量、`.env` 和默认值，键名不区分大小写。
部署源中的空值通常会被忽略，但显式为空的 `GRAPH_PWD` 会保留，用于未启用认证的 Server。
抽取或 Text2GQL 的专用配置会选择独立连接，除非相应 `*_USE_CHAT` 标志明确启用继承。

部署字段可以跨来源组合，例如从 `.env` 读取地址、从 Secret 读取 key。
通过环境变量换用不同端点或 provider 时，不会继承低优先级文件中原端点的凭据；已保存连接则整体保留自己的目标与 key／引用。
手工修改部署文件后应重启服务；页面／API 保存会更新受支持的连接，不会改写 `.env` 或进程环境变量。

配置定义位于：

- `hugegraph-llm/src/hugegraph_llm/config/llm_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/hugegraph_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/index_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/admin_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/prompt_config.py`
- `hugegraph-llm/src/hugegraph_llm/config/models/base_config.py`：加载与文件同步逻辑
