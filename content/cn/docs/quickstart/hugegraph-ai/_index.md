---
title: "HugeGraph-AI"
linkTitle: "HugeGraph-AI"
weight: 3
---

`hugegraph-ai` 提供 HugeGraph 的 Python 客户端、图机器学习工具，以及面向知识图谱构建和 GraphRAG 的 LLM 工具。

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html) · [Ask DeepWiki](https://deepwiki.com/apache/hugegraph-ai)

## 模块

- [hugegraph-llm](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-llm)：知识图谱构建、GraphRAG 和自然语言图查询。
- [hugegraph-ml](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-ml)：从 HugeGraph 读取图数据并运行图学习模型。
- [hugegraph-python-client](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-python-client)：管理 Schema、图数据和 Gremlin 查询的 Python SDK。
- [vermeer-python-client](https://github.com/apache/hugegraph-ai/tree/main/vermeer-python-client)：调用 Vermeer 图计算服务的 Python SDK。

仓库使用 `uv` workspace，其成员是 `hugegraph-llm` 和 `hugegraph-python-client`。`hugegraph-ml` 和 `vermeer-python-client` 是可编辑的路径依赖，不在 workspace members 中。当前仓库版本为 `1.7.0`。

## 环境要求

- HugeGraph-LLM：Python 3.10 或 3.11（`>=3.10,<3.12`）
- HugeGraph-ML：Python 3.10 或更高版本
- HugeGraph Python 客户端、Vermeer Python 客户端：Python 3.9 或更高版本
- `uv` 0.7 或更高版本
- HugeGraph Server 1.3 或更高版本（推荐 1.5 或更高版本）

## 可选依赖组

根项目为每个模块声明一个 extra，另有几个组合项：

| Extra | 安装内容 |
|---|---|
| `llm` | `hugegraph-llm` |
| `ml` | `hugegraph-ml` |
| `python-client` | `hugegraph-python-client` |
| `vermeer` | `vermeer-python-client` |
| `dev` | pytest、pytest-cov、coverage、pylint、ruff、mypy、ty、pre-commit |
| `nk-llm` | `hugegraph-llm`、`hugegraph-python-client`，以及编译镜像所需的 Nuitka |
| `all` | 四个模块包 |

`hugegraph-llm` 自身还声明了 `vectordb` extra，用于安装 `pymilvus` 和 `qdrant-client`。

## Docker Compose 部署

仓库提供同时启动 HugeGraph Server 和 RAG 服务的 Compose 文件：

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
cp docker/env.template docker/.env
# 编辑 docker/.env，将 PROJECT_PATH 改为当前仓库的绝对路径
touch hugegraph-llm/.env
cd docker
docker compose -f docker-compose-network.yml up -d
```

默认地址：

- HugeGraph Server：`http://localhost:8080`
- RAG 服务和 Web 界面：`http://localhost:8001`

## 从源码启动 RAG 服务

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra llm
source .venv/bin/activate
cd hugegraph-llm
python -m hugegraph_llm.demo.rag_demo.app
```

`uv sync` 会创建根目录下的 `.venv`。不要在 `hugegraph-llm` 子目录另建一套环境，否则容易绕过 workspace 锁定的依赖。

## 安装 ML 依赖

```bash
cd hugegraph-ai
uv sync --extra ml
source .venv/bin/activate
cd hugegraph-ml/src
```

示例脚本位于 `hugegraph-ml/src/hugegraph_ml/examples/`。

## 后续阅读

- [HugeGraph-LLM](./hugegraph-llm.md)
- [HugeGraph-LLM 使用流程](./quick_start.md)
- [配置参考](./config-reference.md)
- [REST API](./rest-api.md)
- [HugeGraph-ML](./hugegraph-ml.md)
- [Python 客户端](../client/hugegraph-client-python.md)
