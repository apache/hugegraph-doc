---
title: "HugeGraph-AI"
linkTitle: "HugeGraph-AI"
weight: 3
---

`hugegraph-ai` 提供图客户端、知识图谱构建、GraphRAG、MCP 工具和图学习能力。
按任务选择模块，部署与 API 示例统一维护在对应指南中。
当前源码工作区版本为 `1.8.0`，源码版本不代表每个发行包或镜像均已发布。

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html) · [源码仓库](https://github.com/apache/hugegraph-ai)

<span id="模块"></span>

## 模块 {#modules}

- [GraphRAG 应用](./hugegraph-llm.md) — 运行文档导入、图检索和自然语言查询的 Web 页面与 REST 服务。
- [独立 LLM SDK](./hugegraph-llm-sdk.md) — 在 Python 应用中集成 Schema 设计、校验及带审阅的图抽取。
- [MCP 工具](./hugegraph-mcp.md) — 向 AI 客户端提供图查询、Schema 和受控写入能力。
- [Python 图客户端](/cn/docs/clients/client/hugegraph-client-python/) — 管理 Schema、图数据和 Gremlin 请求。
- [Vermeer Python 客户端](./vermeer-python-client.md) — 自动化加载图、计算和获取结果。
- [图学习](./hugegraph-ml.md) — 读取 HugeGraph 数据并运行图学习示例。
{.cards .td-cards-list}

<span id="环境要求"></span>

## 环境要求 {#requirements}

- 当前源码模块要求 Python **3.12+**；LLM 应用支持 Python **3.12–3.14**。
- 源码工作区使用 [`uv`](https://docs.astral.sh/uv/getting-started/installation/)。
- 图客户端要求 HugeGraph Server **1.5.0+**，会拒绝可探测到的更早版本；各功能的 Server 版本要求需另行确认。

`uv` workspace 包含 `hugegraph-llm-sdk`、`hugegraph-llm` 和 `hugegraph-python-client`。
Vermeer 是可编辑路径依赖；ML 和 MCP 有各自的安装指南。
Python 客户端源码目录叫 `hugegraph-python-client`，发行包名为 `hugegraph-python`。

<span id="可选依赖组"></span>

## 可选依赖组 {#optional-dependency-groups}

在源码仓库根目录执行 workspace 命令：

| Extra | 安装内容 |
| --- | --- |
| `llm` | LLM 应用及其依赖 |
| `vectordb` | LLM 应用及 Milvus／Qdrant 支持 |
| `python-client` | `hugegraph-python` |
| `vermeer` | `vermeer-python-client` |
| `dev` | pytest、coverage、Ruff、ty 和 pre-commit |
| `nk-llm` | LLM 应用、图客户端及 Nuitka 镜像构建依赖 |
| `all` | LLM 应用、图客户端、Vermeer 客户端，不含 ML 或 MCP |

根目录没有 `ml` extra。ML 和 MCP 应使用各自的安装指南，无需把它们的依赖加入 LLM 部署。

<span id="docker-compose-部署"></span>

## Docker Compose 部署 {#deploy-with-docker-compose}

使用[统一维护的 Compose 步骤](./hugegraph-llm.md#deploy-with-docker-compose)，
准备引导配置并构建源码工作区要求的 RAG 镜像，再同时启动 Server 与 RAG。
Kubernetes 和持久化应用配置使用[统一 Helm 部署](/cn/docs/quickstart/hugegraph/hugegraph-helm/#8-graphrag)。

<span id="从源码启动-rag-服务"></span>

## 从源码启动 RAG 服务 {#start-the-rag-service-from-source}

先按[源码启动步骤](./hugegraph-llm.md#start-from-source)运行服务，再阅读[使用流程](./quick_start.md)。
`uv sync --extra llm` 会在 workspace 根目录创建 `.venv`。仓库不跟踪 `uv.lock`，依赖按 `pyproject.toml` 约束解析。
部署默认值、已保存模型连接和持久化文件见[配置参考](./config-reference.md)。

<span id="安装-ml-依赖"></span>

## 安装 ML 依赖 {#install-ml-dependencies}

ML 是独立项目，安装和示例见 [ML 指南](./hugegraph-ml.md)；根目录 `--extra all` 不会安装它。

<span id="后续阅读"></span>

## 后续阅读 {#next-steps}

- [建立索引与查询文档](./quick_start.md)
- [配置模型、存储和凭据](./config-reference.md)
- [调用 RAG 与配置 API](./rest-api.md)
