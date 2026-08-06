---
title: "HugeGraph-AI"
linkTitle: "HugeGraph-AI"
weight: 3
---

[![License](https://img.shields.io/badge/license-Apache%202-0E78BA.svg)](https://www.apache.org/licenses/LICENSE-2.0.html)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/apache/hugegraph-ai)

> DeepWiki 提供实时更新的项目文档，内容更全面准确，适合快速了解项目最新情况。
>
> 📖 [https://deepwiki.com/apache/hugegraph-ai](https://deepwiki.com/apache/hugegraph-ai)

`hugegraph-ai` 整合了 [HugeGraph](https://github.com/apache/hugegraph) 与人工智能功能，为开发者构建 AI 驱动的图应用提供全面支持。

## ✨ 核心功能

- **GraphRAG**：利用图增强检索构建智能问答系统
- **Text2Gremlin**：自然语言到图查询的转换，支持 REST API
- **知识图谱构建**：使用大语言模型从文本自动构建图谱
- **图机器学习**：集成 21 种图学习算法（GCN、GAT、GraphSAGE 等）
- **Python 客户端**：易于使用的 HugeGraph Python 操作接口
- **AI 智能体**：提供智能图分析与推理能力

### 🎉 v1.5.0 新特性

- **Text2Gremlin REST API**：通过 REST 端点将自然语言查询转换为 Gremlin 命令
- **多模型向量支持**：每个图实例可以使用独立的嵌入模型
- **双语提示支持**：支持英文和中文提示词切换（EN/CN）
- **半自动 Schema 生成**：从文本数据智能推断 Schema
- **半自动 Prompt 生成**：上下文感知的提示词模板
- **增强的 Reranker 支持**：集成 Cohere 和 SiliconFlow 重排序器
- **LiteLLM 多供应商支持**：统一接口支持 OpenAI、Anthropic、Gemini 等

## 🚀 快速开始

> [!NOTE]
> 如需完整的部署指南和详细示例，请参阅 [hugegraph-llm/README.md](https://github.com/apache/hugegraph-ai/blob/main/hugegraph-llm/README.md)。

### 环境要求
- Python 3.10+（hugegraph-llm 必需）
- [uv](https://docs.astral.sh/uv/) 0.7+（推荐的包管理器）
- HugeGraph Server 1.5+（必需）
- Docker（可选，用于容器化部署）

### 方案一：Docker 部署（推荐）

```bash
# 克隆仓库
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai

# 设置环境并启动服务
cp docker/env.template docker/.env
# 编辑 docker/.env 设置你的 PROJECT_PATH
cd docker
docker-compose -f docker-compose-network.yml up -d

# 访问服务：
# - HugeGraph Server: http://localhost:8080
# - RAG 服务: http://localhost:8001
```

### 方案二：源码安装

```bash
# 1. 启动 HugeGraph Server
docker run -itd --name=server -p 8080:8080 hugegraph/hugegraph

# 2. 克隆并设置项目
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/hugegraph-llm

# 3. 安装依赖
uv venv && source .venv/bin/activate
uv pip install -e .

# 4. 启动演示
python -m hugegraph_llm.demo.rag_demo.app
# 访问 http://127.0.0.1:8001
```

### 基本用法示例

#### GraphRAG - 问答
```python
from hugegraph_llm.operators.graph_rag_task import RAGPipeline

# 初始化 RAG 工作流
graph_rag = RAGPipeline()

# 对你的图进行提问
result = (graph_rag
    .extract_keywords(text="给我讲讲 Al Pacino 的故事。")
    .keywords_to_vid()
    .query_graphdb(max_deep=2, max_graph_items=30)
    .synthesize_answer()
    .run())
```

#### 知识图谱构建
```python
from hugegraph_llm.models.llms.init_llm import LLMs
from hugegraph_llm.operators.kg_construction_task import KgBuilder

# 从文本构建知识图谱
TEXT = "你的文本内容..."
builder = KgBuilder(LLMs().get_chat_llm())

(builder
    .import_schema(from_hugegraph="hugegraph")
    .chunk_split(TEXT)
    .extract_info(extract_type="property_graph")
    .commit_to_hugegraph()
    .run())
```

#### 图机器学习
```python
from pyhugegraph.client import PyHugeClient
# 连接 HugeGraph 并运行机器学习算法
# 详细示例请参阅 hugegraph-ml 文档
```

## 📦 模块

### [hugegraph-llm](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-llm) [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/apache/hugegraph-ai)
用于图应用的大语言模型集成：
- **GraphRAG**：基于图数据的检索增强生成
- **知识图谱构建**：从文本自动构建知识图谱
- **自然语言接口**：使用自然语言查询图
- **AI 智能体**：智能图分析与推理

### [hugegraph-ml](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-ml)
包含 21 种算法的图机器学习：
- **节点分类**：GCN、GAT、GraphSAGE、APPNP、AGNN、ARMA、DAGNN、DeeperGCN、GRAND、JKNet、Cluster-GCN
- **图分类**：DiffPool、GIN
- **图嵌入**：DGI、BGRL、GRACE
- **链接预测**：SEAL、P-GNN、GATNE
- **欺诈检测**：CARE-GNN、BGNN
- **后处理**：C&S（Correct & Smooth）

### [hugegraph-python-client](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-python-client)
用于 HugeGraph 操作的 Python 客户端：
- **Schema 管理**：定义顶点/边标签和属性
- **CRUD 操作**：创建、读取、更新、删除图数据
- **Gremlin 查询**：执行图遍历查询
- **REST API**：完整的 HugeGraph REST API 覆盖

## 📚 了解更多

- [项目主页](https://hugegraph.apache.org/docs/quickstart/hugegraph-ai/)
- [LLM 快速入门指南](https://github.com/apache/hugegraph-ai/blob/main/hugegraph-llm/quick_start.md)
- [DeepWiki AI 文档](https://deepwiki.com/apache/hugegraph-ai)

## 🔗 相关项目

- [hugegraph](https://github.com/apache/hugegraph) - 核心图数据库
- [hugegraph-toolchain](https://github.com/apache/hugegraph-toolchain) - 开发工具（加载器、仪表盘等）
- [hugegraph-computer](https://github.com/apache/hugegraph-computer) - 图计算系统

## 🤝 贡献

我们欢迎贡献！详情请参阅我们的[贡献指南](https://hugegraph.apache.org/docs/contribution-guidelines/)。

**开发设置：**
- 使用 [GitHub Desktop](https://desktop.github.com/) 更轻松地管理 PR
- 提交 PR 前运行 `./style/code_format_and_analysis.sh`
- 报告错误前检查现有问题

[![contributors graph](https://contrib.rocks/image?repo=apache/hugegraph-ai)](https://github.com/apache/hugegraph-ai/graphs/contributors)

## 📄 许可证

hugegraph-ai 采用 [Apache 2.0 许可证](https://github.com/apache/hugegraph-ai/blob/main/LICENSE)。

## 📞 联系我们

- **GitHub Issues**：[报告错误或请求功能](https://github.com/apache/hugegraph-ai/issues)（响应最快）
- **电子邮件**：[dev@hugegraph.apache.org](mailto:dev@hugegraph.apache.org)（[需要订阅](https://hugegraph.apache.org/docs/contribution-guidelines/subscribe/)）
- **微信**：关注 "Apache HugeGraph" 微信公众号

<img src="https://raw.githubusercontent.com/apache/hugegraph-doc/master/assets/images/wechat.png" alt="Apache HugeGraph WeChat QR Code" width="200"/>
