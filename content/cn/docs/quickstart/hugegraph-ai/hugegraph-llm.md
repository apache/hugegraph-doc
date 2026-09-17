---
title: "HugeGraph-LLM"
linkTitle: "HugeGraph-LLM"
weight: 1
---

HugeGraph-LLM 用于知识图谱构建、GraphRAG 和自然语言图查询。演示服务把 Gradio 页面和 FastAPI 接口挂在同一个进程上，默认监听 `8001` 端口。

## 环境要求

> AI 总结项目文档：[Ask DeepWiki](https://deepwiki.com/apache/hugegraph-ai)

- Python 3.10 或 3.11（`>=3.10,<3.12`）
- `uv` 0.7 或更高版本
- HugeGraph Server 1.3 或更高版本（推荐 1.5 或更高版本）

## Docker Compose 部署

在 HugeGraph-AI 仓库根目录准备环境文件：

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
cp docker/env.template docker/.env
# 编辑 docker/.env，将 PROJECT_PATH 改为当前仓库的绝对路径
touch hugegraph-llm/.env
cd docker
docker compose -f docker-compose-network.yml up -d
docker compose -f docker-compose-network.yml ps
```

启动后可访问：

- HugeGraph Server：`http://localhost:8080`
- RAG 服务和 Web 页面：`http://localhost:8001`

Compose 文件会把 `${PROJECT_PATH}/hugegraph-llm/.env` 挂载到容器内的 `/home/work/hugegraph-llm/.env`，因此该文件必须在容器启动前存在。资源目录 `hugegraph-llm/src/hugegraph_llm/resources` 也可以用同样方式挂载，该挂载默认被注释掉。

## 容器镜像

| 镜像 | 构建文件 | 内容 |
|---|---|---|
| `hugegraph/rag` | `docker/Dockerfile.llm` | 包含源码的 Python 3.10 运行环境，入口是 `python -m hugegraph_llm.demo.rag_demo.app --host 0.0.0.0 --port 8001` |
| `hugegraph/rag-bin` | `docker/Dockerfile.nk` | 基于 `nk-llm` extra 用 Nuitka 编译的二进制，入口是 `./app.dist/app.bin` |

两个镜像都暴露 `8001` 端口，以非 root 用户 `work` 运行，为 `hugegraph-llm/src/hugegraph_llm/resources` 声明数据卷，并使用 `curl -f http://localhost:8001/` 作为健康检查。

`scripts/build_llm_image.sh` 会用 `docker/Dockerfile.llm` 构建并打上 `hugegraph/graphrag:1.7.0` 标签。

## Kubernetes 部署

`docker/charts/hg-llm` 是 RAG 服务的 Helm chart，部署 `hugegraph/graphrag` 镜像。默认发布 `NodePort` 类型的 Service，把节点端口 `8039` 和服务端口 `8080` 映射到容器端口 `8001`，名称固定为 `hg-llm-service`。Ingress 和水平自动扩缩容已定义但默认关闭。

chart 中 `image.tag` 仍默认为 `v0.0.1`，因此需要通过 `--set image.tag=1.7.0` 或修改 `values.yaml` 指向实际构建的标签。

chart 的 `values.yaml` 中，`.env` 和提示词 YAML 的挂载默认被注释掉。要使用自定义配置，先创建两个 ConfigMap，再取消对应 `volumes` 和 `volumeMounts` 段落的注释：

```bash
kubectl create configmap hugegraph-llm-env --from-file=/path/to/.env
kubectl create configmap hugegraph-llm-prompt-config --from-file=/path/to/config_prompt.yaml
```

## 从源码启动

依赖应从仓库根目录按 workspace 安装：

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra llm
source .venv/bin/activate
cd hugegraph-llm
python -m hugegraph_llm.demo.rag_demo.app
```

自定义监听地址和端口：

```bash
python -m hugegraph_llm.demo.rag_demo.app \
  --host 127.0.0.1 \
  --port 18001
```

设置 `HG_DEV_RELOAD=1` 可让 uvicorn 以自动重载方式启动，便于开发调试。

服务以 `hugegraph-llm/.env` 保存模型、HugeGraph 和登录配置。提示词放在 `hugegraph-llm/src/hugegraph_llm/resources/demo/config_prompt.yaml`。缺少文件时，配置代码会按默认值创建。

`.env` 路径按以下顺序解析：先看是否设置了 `HUGEGRAPH_LLM_ENV_PATH`；未设置时，从源码运行则使用 `hugegraph-llm/.env`；否则使用当前工作目录下的 `.env`。

## 主要功能

### 构建 RAG 索引

Web 页面的第一个标签页可以处理文本或文件，并执行以下操作：

1. 切分文本并写入 chunk 向量索引。
2. 按给定 Schema 从文本抽取顶点和边。
3. 将抽取结果写入 HugeGraph，并更新顶点向量索引。

文本可以在 `text` 子页直接输入，也可以在 `file` 子页上传。上传支持 `.txt`、`.docx` 和 `.pdf`，并可一次选择多个文件。加密 PDF 以及没有可提取文本层的扫描件 PDF 会被拒绝。

Schema 可以是内联 JSON，也可以是现有图名。通过 REST API 使用图名时，必须同时传入匹配的 `client_config.graph`；内联 JSON 不会连接 HugeGraph，也不能附带 `client_config`。

该标签页还提供两个生成器。`Graph Schema Generator` 根据查询示例和少样本示例生成 Schema。`Graph Extraction Prompt Generator` 根据描述的场景和选定的参考示例生成抽取提示词。`Graph Extraction Split Type` 下拉框可在抽取前选择 `document`、`paragraph` 或 `sentence` 粒度。

### GraphRAG

查询流程可以组合直接回答、chunk 向量召回和图召回。图召回先抽取关键词并匹配顶点，再尝试 Text2Gremlin；生成或执行失败时可回退到预定义的图遍历方式。请求参数可控制返回数量、向量距离阈值、模板数量和重排序方式。

同一标签页还有批量回归测试面板，可从 `.xlsx` 或 `.csv` 文件读取问题、逐条作答，并返回可下载的结果文件。上传控件旁提供模板文件下载。

![知识图谱构建器](/images/docs/hugegraph-ai/gradio-kg.jpg)

### Text2Gremlin

`POST /text2gremlin` 根据自然语言、图 Schema 和可选示例生成 Gremlin。自定义提示词必须保留 `{query}`、`{schema}`、`{example}` 和 `{vertices}` 四个占位符。

对应的页面标签可以先用问题与 Gremlin 对照文件（`.json` 或 `.csv`）构建示例向量索引。未上传文件时使用内置的 `resources/demo/text2gremlin.csv`。

### 图工具与管理工具

`Graph Tools` 标签页可直接执行 Gremlin 查询、手动触发图备份，以及初始化 HugeGraph 演示数据。`Admin Tools` 标签页在校验 `ADMIN_TOKEN` 后展示 `logs/llm-server.log` 的末尾内容，并可刷新或清空该文件。

进程运行期间还有两个后台任务：每天 01:00 执行图备份的定时任务，以及持续更新顶点 id 向量的任务。

## 模型与向量后端

聊天、信息抽取和 Text2Gremlin 可以分别使用 OpenAI 兼容接口、Ollama 或 LiteLLM。嵌入模型可独立选择，同样支持这三种提供方。重排序支持 Cohere 和 SiliconFlow。

默认向量索引使用 FAISS。`CUR_VECTOR_INDEX` 可选 `Faiss`、`Milvus` 或 `Qdrant`，Web 页面的 `5. Set up the vector engine.` 面板提供同样的选择。Milvus 和 Qdrant 需要安装可选依赖：

```bash
cd hugegraph-ai
uv sync --package hugegraph-llm --extra vectordb
```

页面操作流程见[使用流程](./quick_start.md)，完整环境变量见[配置参考](./config-reference.md)，HTTP 请求格式见[REST API](./rest-api.md)。

## 程序化调用

原有的 `RAGPipeline` 和 `KgBuilder` 类已被流水线调度器取代。通过 `SchedulerSingleton` 按名称调用流程：

```python
from hugegraph_llm.flows.scheduler import SchedulerSingleton

scheduler = SchedulerSingleton.get_instance()
res = scheduler.schedule_flow(
    "rag_graph_only",
    query="Tell me about Al Pacino.",
    graph_only_answer=True,
    vector_only_answer=False,
    raw_answer=False,
    gremlin_tmpl_num=-1,
    gremlin_prompt=None,
)
print(res.get("graph_only_answer"))
```

已注册的流程名包括 `rag_raw`、`rag_vector_only`、`rag_graph_only`、`rag_graph_vector`、`text2gremlin`、`build_examples_index`、`build_vector_index`、`graph_extract`、`import_graph_data`、`update_vid_embeddings`、`get_graph_index_info`、`build_schema` 和 `prompt_generate`。`schedule_stream_flow` 是对应的异步流式版本。

## 开发检查

先在仓库根目录安装模块和开发工具，再运行与 CI 一致的检查：

```bash
cd hugegraph-ai
uv sync --extra llm --extra dev
uv run ruff format --check .
uv run ruff check .

cd hugegraph-llm
SKIP_EXTERNAL_SERVICES=true uv run pytest src/tests/config/ src/tests/document/ src/tests/middleware/ \
  src/tests/operators/ src/tests/models/ src/tests/indices/ src/tests/test_utils.py -v --tb=short
SKIP_EXTERNAL_SERVICES=true uv run pytest src/tests/integration/test_graph_rag_pipeline.py \
  src/tests/integration/test_kg_construction.py src/tests/integration/test_rag_pipeline.py -v --tb=short
```

Git hook 通过 pre-commit 启用：

```bash
cd hugegraph-ai
pre-commit install
pre-commit run --all-files
```
