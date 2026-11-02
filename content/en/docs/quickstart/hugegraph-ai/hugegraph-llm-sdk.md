---
title: "HugeGraph-LLM SDK Quick Start"
linkTitle: "HugeGraph-LLM SDK"
weight: 8
description: "Standalone Python SDK for schema design, entity/relation extraction, graph validation, and reviewed graph construction from text."
search_keywords: [HugeGraph-LLM SDK, hugegraph_llm_sdk, schema design, graph extraction, knowledge graph, Python SDK]
---

`hugegraph-llm-sdk` is a lightweight, standalone Python SDK for programmatically designing schemas, extracting property graphs from unstructured text,
validating schemas against HugeGraph rules, and performing iterative model review and bounded repair.

Unlike the full `hugegraph-llm` application, the SDK is completely headless and does not require HugeGraph Server, Gradio Web UI, FastAPI, or a vector
database. Its core runtime depends only on `pydantic>=2.14,<3`.

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html) · [Ask DeepWiki](https://deepwiki.com/apache/hugegraph-ai)

## Requirements and Installation

- **Python**: `>=3.12` (tested and supported on Python 3.12, 3.13, and 3.14).
- **Package name**: `hugegraph-llm-sdk`
- **Import name**: `hugegraph_llm_sdk`

### Install from source or a local wheel

The SDK is currently provided by the `hugegraph-ai` source tree and has not yet been published to a public package index. Install it from a checkout or a locally built wheel.

```bash
pip install -e /path/to/hugegraph-ai/hugegraph-llm-sdk
# or
uv add --editable /path/to/hugegraph-ai/hugegraph-llm-sdk

uv build --no-sources /path/to/hugegraph-ai/hugegraph-llm-sdk --out-dir /tmp/llm-sdk-dist
pip install /tmp/llm-sdk-dist/hugegraph_llm_sdk-1.8.0-py3-none-any.whl
```

### Provider Extras

Install provider extras from the same checkout:

```bash
pip install -e "/path/to/hugegraph-ai/hugegraph-llm-sdk[openai]"
pip install -e "/path/to/hugegraph-ai/hugegraph-llm-sdk[ollama]"
pip install -e "/path/to/hugegraph-ai/hugegraph-llm-sdk[litellm]"
# uv example: uv add --editable /path/to/hugegraph-ai/hugegraph-llm-sdk --extra openai
```
## Quick Start: Minimal Example

Here is a complete example demonstrating schema design, schema validation, and reviewed graph extraction using a custom model function:

```python
from hugegraph_llm_sdk import (
    FunctionModel,
    design_schema,
    validate_schema,
    extract_graph,
)

# 1. Define or wrap your LLM caller
model = FunctionModel(generate=lambda prompt: my_agent_model.invoke(prompt).content)

# 2. Design a graph schema from sample texts and target questions
draft = design_schema(
    texts=["Alice works for Acme Corp. Bob reports to Alice."],
    questions=["Which company does each person work for? Who reports to whom?"],
    model=model,
)

# Inspect any structural or conceptual issues flagged during design
if draft.issues:
    print(f"Schema draft issues: {draft.issues}")

schema = draft.schema

# 3. Validate schema structure against HugeGraph rules
validation_issues = validate_schema(schema)
assert not validation_issues, f"Validation failed: {validation_issues}"

# 4. Extract property graph from text
result = extract_graph(
    texts="Alice works for Acme Corp as Chief Engineer.",
    schema=schema,
    model=model,
)

# 5. Process chunk outcomes
print(f"Overall status: {result.status}")  # 'succeeded', 'partial', or 'failed'
for chunk in result.chunks:
    if chunk.status == "final":
        print(f"Extracted graph: {chunk.graph}")
    else:
        print(f"Chunk {chunk.index} status: {chunk.status}, reason: {chunk.reason}, issues: {chunk.issues}")
```

## Core API Capabilities

| Function | Signature | Description |
|---|---|---|
| `design_schema` | `(texts, *, model, questions=(), example_schema=None, prompt=None) -> SchemaDraft` | Generates a candidate schema (`SchemaDraft(schema, issues)`) from texts and domain queries. |
| `adesign_schema` | `(texts, *, model, questions=(), example_schema=None, prompt=None) -> SchemaDraft` | Asynchronous schema design variant. |
| `validate_schema` | `(schema) -> list[Issue]` | Validates schema structure against HugeGraph property graph constraints without mutating the input. |
| `extract_graph` | `(texts, *, schema, model=None, model_factory=None, review=True, options=None, prompts=None, validators=()) -> ExtractionResult` | Executes chunked graph extraction, validation, and review/repair loops. |
| `aextract_graph` | `(texts, *, schema, model=None, model_factory=None, review=True, options=None, prompts=None, validators=()) -> ExtractionResult` | Asynchronous graph extraction variant. |

### Schema Validation Rules

- `validate_schema` inspects vertex labels, edge labels, ID strategies (`DEFAULT`, `AUTOMATIC`, `PRIMARY_KEY`, `CUSTOMIZE_STRING`, `CUSTOMIZE_NUMBER`, `CUSTOMIZE_UUID`), and property declarations.
- When `propertykeys` is omitted, global property definitions are not strictly checked. When a label omits `properties`, its property set is unconstrained.
- An explicit empty `properties: []` indicates that no properties are allowed for that label.
- For edge labels, `sort_keys` cannot be members of `nullable_keys`. When `frequency` is `SINGLE` or `DEFAULT`, sort keys are disallowed;
  `MULTIPLE` requires non-empty sort keys.

## Model Adapters

The SDK includes standard model adapters under `hugegraph_llm_sdk.providers`:

```python
from hugegraph_llm_sdk.providers.openai import OpenAIClient

model = OpenAIClient(
    api_key="your-api-key",
    api_base="https://api.openai.com/v1",
    model_name="gpt-4o-mini",
)
```

- **`FunctionModel`**: Wraps any custom function `generate(prompt: str) -> str` or async `agenerate(prompt: str) -> str`.
- **`OpenAIClient`**: Adapter for OpenAI and OpenAI-compatible endpoints (supports `close()` and `await aclose()`).
- **`OllamaClient`**: Adapter for local Ollama instances.
- **`LiteLLMClient`**: Adapter using LiteLLM connection routing.
- **`ThreadedModel`**: Wraps a synchronous model so calls execute inside worker threads during async execution without blocking the event loop.

## Review and Bounded Repair

By default, extraction executes an iterative review and bounded repair loop:

```text
extract -> validate -> review
              ^           |
              |           +-- pass  -> final
              |           +-- block -> blocked
              +-- repair <- fix
```

Review options are configured via `ExtractionOptions`:

```python
from hugegraph_llm_sdk import ExtractionOptions, extract_graph

options = ExtractionOptions(
    max_reviews=2,  # Maximum review attempts per chunk (0–5, default: 2)
    max_fixes=1,    # Maximum repair attempts per chunk (0–3, default: 1)
    max_workers=1,  # Worker concurrency (1–8, default: 1)
)

result = extract_graph(
    texts="Bob manages Charlie at Beta Corp.",
    schema=schema,
    model=model,
    options=options,
)
```

### Chunk and Result Statuses

- **Chunk status**:
  - `final`: Graph passed structural validation and model review. Only `final` chunks are merged into `result.graph`.
  - `candidate`: Validation passed, but review budget was exhausted or review could not conclude.
  - `blocked`: Graph could not pass validation within the repair budget or was explicitly rejected by review.
  - `failed`: An exception or unrecoverable error occurred during execution.
- **Aggregate status**:
  - `succeeded`: All chunks achieved `final` status.
  - `partial`: At least one chunk is `final`, but one or more chunks failed or remain candidate/blocked.
  - `failed`: No chunk reached `final` status.

## Concurrency and Async Processing

When setting `max_workers > 1`, you must pass a stateless `model_factory` callable instead of a single `model` instance. This ensures thread-safety and
isolated model state per worker:

```python
from hugegraph_llm_sdk import ExtractionOptions, extract_graph
from hugegraph_llm_sdk.providers.openai import OpenAIClient

chunks = [
    "Alice joined Acme Corp in 2022.",
    "Bob joined Beta LLC in 2023.",
    "Charlie works with Alice at Acme Corp.",
]

result = extract_graph(
    texts=chunks,
    schema=schema,
    model_factory=lambda: OpenAIClient(api_key="your-api-key", model_name="gpt-4o-mini"),
    options=ExtractionOptions(max_workers=3),
)

print(f"Total vertices: {len(result.graph.get('vertices', []))}")
print(f"Total edges: {len(result.graph.get('edges', []))}")
```

The SDK automatically manages the lifecycle of models created by `model_factory`, disposing of them when each worker batch finishes.

## Relationship with HugeGraph-LLM

`hugegraph-llm-sdk` and `hugegraph-llm` reside in the same repository under separate modules:

```text
hugegraph-ai/
├── hugegraph-llm-sdk/      # Standalone headless Python SDK (pydantic-only baseline)
├── hugegraph-llm/          # Full application layer (FastAPI, Gradio UI, GraphRAG, vector DB)
├── hugegraph-python-client/# Low-level HugeGraph Server client (pyhugegraph)
└── hugegraph-mcp/          # Model Context Protocol server
```

- **`hugegraph-llm-sdk`**: Embeddable library for Python pipelines, LLM agent toolchains, and data transformation scripts requiring schema design and graph
  extraction.
- **`hugegraph-llm`**: Production application service providing Web UI, REST endpoints (`POST /graph/extract`, `POST /rag`), vector index persistence, and
  automated ingestion into HugeGraph Server.
