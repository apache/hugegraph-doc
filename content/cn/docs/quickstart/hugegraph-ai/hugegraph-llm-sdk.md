---
title: "HugeGraph-LLM SDK 快速上手"
linkTitle: "HugeGraph-LLM SDK"
weight: 8
description: "面向独立 Python 项目的轻量级 SDK，支持 Schema 设计、实体与关系抽取、图校验以及模型审阅修复。"
search_keywords: [HugeGraph-LLM SDK, hugegraph_llm_sdk, Schema 设计, 图数据抽取, 知识图谱, Python SDK]
---

`hugegraph-llm-sdk` 是面向独立 Python 项目的轻量级 SDK，提供编程式 Schema 设计、非结构化文本属性图抽取、遵循 HugeGraph 规则的结构校验，以及多轮模型审阅与有限修复能力。

与完整的 `hugegraph-llm` 应用不同，该 SDK 采用无界面（Headless）设计，无需依赖 HugeGraph Server、Gradio Web 界面、FastAPI 服务或向量数据库。基础运行环境仅依赖 `pydantic>=2.14,<3`。

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html) · [Ask DeepWiki](https://deepwiki.com/apache/hugegraph-ai)

## 环境要求与安装

- **Python 版本**：`>=3.12`（在 Python 3.12、3.13 与 3.14 上均通过验证与支持）。
- **发行包名**：`hugegraph-llm-sdk`
- **导入模块名**：`hugegraph_llm_sdk`

### 从源码或本地 wheel 安装

当前 SDK 随 `hugegraph-ai` 源码提供，尚未发布到公共软件包索引。请从本地源码目录或自行构建的 wheel 安装。

```bash
pip install -e /path/to/hugegraph-ai/hugegraph-llm-sdk
# 或
uv add --editable /path/to/hugegraph-ai/hugegraph-llm-sdk

uv build --no-sources /path/to/hugegraph-ai/hugegraph-llm-sdk --out-dir /tmp/llm-sdk-dist
pip install /tmp/llm-sdk-dist/hugegraph_llm_sdk-1.8.0-py3-none-any.whl
```

### 模型厂商适配器（Extras）

请从同一源码目录安装所需的适配器 extra：

```bash
pip install -e "/path/to/hugegraph-ai/hugegraph-llm-sdk[openai]"
pip install -e "/path/to/hugegraph-ai/hugegraph-llm-sdk[ollama]"
pip install -e "/path/to/hugegraph-ai/hugegraph-llm-sdk[litellm]"
# uv 示例：uv add --editable /path/to/hugegraph-ai/hugegraph-llm-sdk --extra openai
```
## 快速上手：最小示例

以下展示使用自定义模型函数完成“设计 Schema → 校验 Schema → 抽取并审阅属性图”的完整流程：

```python
from hugegraph_llm_sdk import (
    FunctionModel,
    design_schema,
    validate_schema,
    extract_graph,
)

# 1. 定义或封装大模型调用接口
model = FunctionModel(generate=lambda prompt: my_agent_model.invoke(prompt).content)

# 2. 根据业务文本与问题设计图 Schema
draft = design_schema(
    texts=["Alice 在 Acme 集团工作，Bob 向 Alice 汇报工作。"],
    questions=["每个人在哪个公司工作？谁向谁汇报？"],
    model=model,
)

# 检查设计阶段标记的结构或语义问题
if draft.issues:
    print(f"Schema 设计问题: {draft.issues}")

schema = draft.schema

# 3. 按照 HugeGraph 规则对 Schema 结构进行合法性校验
validation_issues = validate_schema(schema)
assert not validation_issues, f"Schema 校验失败: {validation_issues}"

# 4. 从文本中抽取属性图
result = extract_graph(
    texts="Alice 在 Acme 集团担任首席工程师。",
    schema=schema,
    model=model,
)

# 5. 处理分块抽取结果
print(f"整体执行状态: {result.status}")  # 'succeeded'、'partial' 或 'failed'
for chunk in result.chunks:
    if chunk.status == "final":
        print(f"抽取的子图数据: {chunk.graph}")
    else:
        print(f"分块 {chunk.index} 状态: {chunk.status}, 原因: {chunk.reason}, 问题: {chunk.issues}")
```

## 核心接口说明

| 接口名称 | 签名 | 说明 |
|---|---|---|
| `design_schema` | `(texts, *, model, questions=(), example_schema=None, prompt=None) -> SchemaDraft` | 根据文本与问题生成候选图结构草案（`SchemaDraft(schema, issues)`）。 |
| `adesign_schema` | `(texts, *, model, questions=(), example_schema=None, prompt=None) -> SchemaDraft` | 异步版本的 Schema 设计接口。 |
| `validate_schema` | `(schema) -> list[Issue]` | 校验 Schema 结构是否符合 HugeGraph 属性图约束，不修改输入对象。 |
| `extract_graph` | `(texts, *, schema, model=None, model_factory=None, review=True, options=None, prompts=None, validators=()) -> ExtractionResult` | 执行分块图抽取、结构校验以及多轮审阅修复循环。 |
| `aextract_graph` | `(texts, *, schema, model=None, model_factory=None, review=True, options=None, prompts=None, validators=()) -> ExtractionResult` | 异步版本的图抽取接口。 |

### Schema 校验规则

- `validate_schema` 检查顶点标签、边标签、主键策略（`DEFAULT`、`AUTOMATIC`、`PRIMARY_KEY`、`CUSTOMIZE_STRING`、`CUSTOMIZE_NUMBER`、`CUSTOMIZE_UUID`）以及属性声明。
- 省略 `propertykeys` 时，不对全局属性引用作硬性约束；省略标签的 `properties` 时，不限制其属性集合。
- 显式声明 `properties: []` 表示该标签严禁携带任何属性。
- 边标签的 `sort_keys` 不能同时属于 `nullable_keys`；当 `frequency` 为 `SINGLE` 或 `DEFAULT` 时禁止排序键，为 `MULTIPLE` 时必须声明非空排序键。

## 模型适配器

SDK 在 `hugegraph_llm_sdk.providers` 模块中提供了常见大模型的适配器：

```python
from hugegraph_llm_sdk.providers.openai import OpenAIClient

model = OpenAIClient(
    api_key="your-api-key",
    api_base="https://api.openai.com/v1",
    model_name="gpt-4o-mini",
)
```

- **`FunctionModel`**：包装任意同步函数 `generate(prompt: str) -> str` 或异步函数 `agenerate(prompt: str) -> str`。
- **`OpenAIClient`**：适用于 OpenAI 及兼容接口的适配器（支持 `close()` 与 `await aclose()` 显式资源释放）。
- **`OllamaClient`**：适用于本地私有化 Ollama 服务的适配器。
- **`LiteLLMClient`**：基于 LiteLLM 路由连接池的适配器。
- **`ThreadedModel`**：包装同步模型，在异步事件循环中通过独立工作线程执行模型调用，避免阻塞主循环。

## 审阅与有限修复机制

默认情况下，属性图抽取会执行迭代审阅与有限自动修复流程：

```text
extract -> validate -> review
              ^           |
              |           +-- pass  -> final
              |           +-- block -> blocked
              +-- repair <- fix
```

审阅参数可通过 `ExtractionOptions` 进行配置：

```python
from hugegraph_llm_sdk import ExtractionOptions, extract_graph

options = ExtractionOptions(
    max_reviews=2,  # 每个分块的最大审阅轮数（范围 0–5，默认 2）
    max_fixes=1,    # 每个分块的最大自动修复尝试次数（范围 0–3，默认 1）
    max_workers=1,  # 并发执行的 Worker 数量（范围 1–8，默认 1）
)

result = extract_graph(
    texts="Bob 在 Beta 公司管理 Charlie。",
    schema=schema,
    model=model,
    options=options,
)
```

### 分块与整体状态

- **分块状态（Chunk status）**：
  - `final`：子图成功通过结构校验与模型审阅。只有 `final` 状态的分块会被合并到全局 `result.graph` 中。
  - `candidate`：通过了结构校验，但审阅配额耗尽或未能完成最终核对。
  - `blocked`：未能通过 Schema 校验修复，或被模型审阅判定存在明显事实错误予以拦截。
  - `failed`：在准备、调用或解析阶段发生异常。
- **整体状态（Aggregate status）**：
  - `succeeded`：所有文本分块均达成 `final` 状态。
  - `partial`：至少一个分块达成 `final`，但同时存在未完成（candidate、blocked 或 failed）的分块。
  - `failed`：没有任何分块达成 `final` 状态。

## 并发与异步批量抽取

当配置 `max_workers > 1` 时，必须传入无参 `model_factory` 可调用对象，而不是单一的 `model` 实例，以保证各并发线程状态隔离：

```python
from hugegraph_llm_sdk import ExtractionOptions, extract_graph
from hugegraph_llm_sdk.providers.openai import OpenAIClient

chunks = [
    "Alice 于 2022 年加入 Acme 集团。",
    "Bob 于 2023 年加入 Beta 科技。",
    "Charlie 与 Alice 在 Acme 集团共事。",
]

result = extract_graph(
    texts=chunks,
    schema=schema,
    model_factory=lambda: OpenAIClient(api_key="your-api-key", model_name="gpt-4o-mini"),
    options=ExtractionOptions(max_workers=3),
)

print(f"顶点总数: {len(result.graph.get('vertices', []))}")
print(f"边总数: {len(result.graph.get('edges', []))}")
```

SDK 会自动管理由 `model_factory` 创建的实例生命周期，每批 Worker 执行完毕后自动释放对应连接资源。

## 与 HugeGraph-LLM 的关系

`hugegraph-llm-sdk` 与 `hugegraph-llm` 同属 `hugegraph-ai` 代码仓库：

```text
hugegraph-ai/
├── hugegraph-llm-sdk/      # 独立轻量级 Python SDK（仅依赖 Pydantic）
├── hugegraph-llm/          # 完整上层应用工程（FastAPI、Gradio 界面、GraphRAG、向量库）
├── hugegraph-python-client/# HugeGraph Server 基础通信客户端（pyhugegraph）
└── hugegraph-mcp/          # Model Context Protocol 服务端
```

- **`hugegraph-llm-sdk`**：适合嵌入数据处理流水线、LLM Agent 工具链或外部 Python 应用中，专门负责 Schema 建模与属性图提取。
- **`hugegraph-llm`**：面向终端用户的完整生产服务，提供 Web 界面、RESTful API（`POST /graph/extract`、`POST /rag`）、向量索引持久化与图数据直接入库能力。
