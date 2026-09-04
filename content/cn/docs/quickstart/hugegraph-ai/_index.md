---
title: "HugeGraph-AI"
linkTitle: "HugeGraph-AI"
weight: 3
---

`hugegraph-ai` 提供 HugeGraph 的 Python 客户端、图机器学习工具，以及面向知识图谱构建和 GraphRAG 的 LLM 工具。

## 模块

- [hugegraph-llm](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-llm)：知识图谱构建、GraphRAG 和自然语言图查询。
- [hugegraph-ml](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-ml)：从 HugeGraph 读取图数据并运行图学习模型。
- [hugegraph-python-client](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-python-client)：管理 Schema、图数据和 Gremlin 查询的 Python SDK。
- [vermeer-python-client](https://github.com/apache/hugegraph-ai/tree/main/vermeer-python-client)：调用 Vermeer 图计算服务的 Python SDK。

仓库使用 `uv` workspace 管理 LLM 和 Python 客户端。HugeGraph-ML 是路径依赖模块，不在 workspace members 中。

## 环境要求

- HugeGraph-LLM：Python 3.10 或 3.11
- HugeGraph-ML、Python 客户端：Python 3.10 或更高版本
- `uv` 0.7 或更高版本
- HugeGraph Server 1.5 或更高版本

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
- [配置参考](./config-reference.md)
- [REST API](./rest-api.md)
- [HugeGraph-ML](./hugegraph-ml.md)
- [Python 客户端](../client/hugegraph-client-python.md)
