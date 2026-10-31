---
title: "HugeGraph-MCP"
linkTitle: "HugeGraph-MCP"
weight: 7
---

`hugegraph-mcp` 通过 Model Context Protocol（MCP）向 AI 客户端提供 HugeGraph 工具，
包括 Schema 检查、结构化图查询、受控写入，以及可选的自然语言查询生成和图数据抽取。
服务使用 STDIO 传输，由 MCP 客户端启动本地进程；它不是 HugeGraph Server，也不提供独立的 HTTP MCP 端口。

普通图查询直接访问 HugeGraph Server。自然语言生成、抽取和向量刷新还需要
[HugeGraph-LLM](./hugegraph-llm.md) 服务，模型凭据配置在该服务中。

## 环境要求

- Python 3.10 或更高版本；单独运行 HugeGraph-LLM 时，请同时满足该模块的 Python 版本要求。
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 和支持 STDIO 的 MCP 客户端。
- 可从 MCP 进程访问的 HugeGraph Server 1.7.0 或更高版本。默认图路径为 `DEFAULT/hugegraph`，使用 graphspace API。
- 已创建的图及具备相应权限的账号。服务端认证配置见[认证与授权](../../config/config-authentication.md)。

## 安装与连接

以下示例固定使用已发布的 `hugegraph-mcp==1.7.1`，不需要克隆代码仓库。
将地址、图路径和凭据替换为实际部署值。先使用只读模式验证连接，再按需要开放受支持的写入。

支持 `mcpServers` JSON 配置的客户端可添加：

```json
{
  "mcpServers": {
    "hugegraph": {
      "command": "uvx",
      "args": ["hugegraph-mcp@1.7.1"],
      "env": {
        "HUGEGRAPH_URL": "http://127.0.0.1:8080",
        "HUGEGRAPH_GRAPH_PATH": "DEFAULT/hugegraph",
        "HUGEGRAPH_USER": "your-user",
        "HUGEGRAPH_PASSWORD": "your-password",
        "HUGEGRAPH_MCP_READONLY": "true"
      }
    }
  }
}
```

不同客户端的配置文件位置和结构可能不同，请按客户端说明填写相同的启动命令、参数和环境变量。
如果客户端找不到 `uvx`，将 `command` 改为本机 `uvx` 的绝对路径。修改配置后重启 MCP 进程。

也可在已配置上述环境变量的终端中启动：

```bash
uvx hugegraph-mcp@1.7.1
```

进程启动后等待 MCP 客户端通过标准输入发送协议消息，不会打开网页。
stdout 用于 MCP JSON-RPC，不要将额外的 shell 输出写入该通道。

### 验证连接

通过客户端列出工具，再调用 `inspect_graph_tool`。以下 JSON 是 MCP `tools/call` 的参数内容，
不是向 HugeGraph REST API 直接发送的请求。

```json
{
  "name": "inspect_graph_tool",
  "arguments": {"include_raw_schema": true}
}
```

确认返回 `ok=true`、`data.hugegraph_server_status="available"`。
从 Schema 中选择已有的顶点标签，将下例中的 `person` 替换为该标签：

```json
{
  "name": "query_graph_data_tool",
  "arguments": {
    "target": "vertex",
    "operation": "page",
    "label": "person",
    "limit": 5
  }
}
```

该工具属于默认的 16 工具集。分页时使用响应中的 `next_page` 作为下一次调用的 `page`，
并保留相同的查询条件。结果为空不一定表示连接失败，请同时检查图路径、标签和已有数据。

## 工具集与版本

工具集选择的是同一个包提供的工具分组，不是软件包版本、HugeGraph Server 版本或 MCP 协议版本。
`1.7.1` 的配置名称如下：

| `HUGEGRAPH_MCP_TOOLSET` | 工具数量 | 用途 |
|---|---|---|
| 未设置，或 `v2_core` | 16 | 默认工具集，包含结构化查询和持久化写入计划工具 |
| `v1` | 10 | 兼容工具集，保留较早的工具入口 |

其他任何值（包括 `v2`、`core`、`legacy` 或空字符串），在 1.7.1 中均会记录错误日志并回退到包含 10 个工具的 `v1` 兼容工具集。
两种工具集的 `mcp_tool_contract_version` 均为 `2.0`，该字段表示工具契约，不表示包版本。

### 工具集命名演进 {#toolset-evolution}

最新源码已将默认工具集更名为 `core`，兼容工具集更名为 `legacy`。该规范将在后续版本正式发布；若使用 `1.7.1` 安装包，请继续遵循上述配置。

- `v2_core` 对应新版 `core`，`v1` 对应新版 `legacy`；旧名称作为兼容别名保留，使用时将输出迁移提示。
- 检查接口统一返回 `core` 或 `legacy`，依赖 `data.toolset` 或 `meta.toolset` 的客户端需同步适配。
- 未设置变量时默认启用 `core`；空值或未知值将直接拦截启动，不再静默回退。
- 工具集在启动时加载，变更配置后需重启客户端；切换兼容工具集不会绕过鉴权与只读约束。

## 工具能力

工具已注册不代表所有操作都可以执行。当前能力范围如下，实际工具参数以客户端的工具 Schema 为准。

| 功能 | 工具 | 使用范围 |
|---|---|---|
| 检查与设计 | `inspect_graph_tool`、`inspect_schema_tool`、`design_schema_tool` | 查看连接、Schema 和设计指导 |
| 结构化读取 | `query_graph_data_tool` | 按 ID、ID 列表、分页或条件读取顶点和边 |
| Schema 创建 | `apply_schema_tool` | 校验和预览；默认工具集支持确认单个属性键、顶点标签或边标签创建 |
| 写入计划 | `confirm_write_tool`、`get_write_status_tool`、`reconcile_write_tool` | 确认、查询及协调持久化计划 |
| 图导入 | `import_graph_data_tool` | `extract` 调用 AI；`ingest` 仅预览，`table` 当前禁用 |
| 图删除 | `delete_graph_data_tool` | 精确边删除可确认；顶点删除仅预览 |
| 属性变更 | `mutate_graph_properties_tool` | 仅预览，确认当前禁用 |
| AI 生成与抽取 | `generate_gremlin_tool`、`extract_graph_data_tool` | 生成查询或抽取候选图数据，不自动执行生成的查询 |
| 向量刷新 | `refresh_vid_embeddings_tool` | 需要 AI、管理模式、允许写入以及显式确认；当前源码的服务侧门禁见下文 |
| 原始 Gremlin | `execute_gremlin_read_tool`、`execute_gremlin_write_tool` | 当前均返回 `FEATURE_DISABLED`；管理模式不能绕过 |

兼容工具集不包含 `inspect_schema_tool`、`query_graph_data_tool`、`mutate_graph_properties_tool`，
以及三个写入计划工具。原始 Gremlin 执行也不会因切换到兼容工具集而开放。

### 受控写入

需要写入时，将 `HUGEGRAPH_MCP_READONLY` 设为 `false`，并使用有相应权限的 HugeGraph 账号。
对于可确认的操作，先执行 dry-run，检查具体目标、变更内容和警告，再使用返回的 `plan_id` 确认：

```json
{
  "name": "confirm_write_tool",
  "arguments": {"plan_id": "<PLAN_ID>"}
}
```

用 `get_write_status_tool(plan_id)` 查询持久化结果。`APPLIED` 表示全部操作已确认成功；
`PARTIAL` 或 `UNKNOWN` 表示部分完成或结果尚不能确定，应先查询和协调状态，不要重新生成计划盲目重试。
已完成的同一计划再次确认会返回记录的结果，不会重复写入。

内置 SQLite 状态存储要求单个可写 MCP 实例，并需要可持久保存的状态目录。
多个客户端各自启动进程时，应先保持只读；多实例写入需要另行设计共享事务存储。
预览返回 `confirmable=false` 的操作不能通过关闭只读或开启管理模式强制执行。

## 配置

下表对应已发布的 `1.7.1`。MCP 图账号与 HugeGraph-LLM 的 API token 是两种不同的凭据。

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `HUGEGRAPH_URL` | `http://127.0.0.1:8080` | MCP 进程访问的 HugeGraph 地址 |
| `HUGEGRAPH_GRAPH_PATH` | `DEFAULT/hugegraph` | `GRAPH_SPACE/GRAPH_NAME` |
| `HUGEGRAPH_GRAPHSPACE` | 未设置 | 覆盖 `HUGEGRAPH_GRAPH_PATH` 中的 graphspace |
| `HUGEGRAPH_GRAPH` | 未设置 | 覆盖 `HUGEGRAPH_GRAPH_PATH` 中的图名 |
| `HUGEGRAPH_USER` | `admin` | HugeGraph 用户名 |
| `HUGEGRAPH_PASSWORD` | 空 | HugeGraph 密码 |
| `HUGEGRAPH_MCP_TOOLSET` | `v2_core` | 该版本支持 `v2_core`、`v1` |
| `HUGEGRAPH_MCP_READONLY` | `true` | 禁止受控写入 |
| `HUGEGRAPH_MCP_ALLOW_AI` | `false` | 允许调用 HugeGraph-LLM |
| `HUGEGRAPH_MCP_ADMIN_MODE` | `false` | 开放符合条件的管理操作 |
| `HUGEGRAPH_AI_URL` | `http://127.0.0.1:8001` | HugeGraph-LLM 服务地址 |
| `HUGEGRAPH_AI_TOKEN` | 未设置 | HugeGraph-LLM bearer token |
| `HUGEGRAPH_AI_GRAPH_URL` | 未设置 | 不用于改变 AI 服务目标；当前源码已忽略此项 |
| `HUGEGRAPH_AI_TIMEOUT_SECONDS` | `30` | AI HTTP 请求超时，单位为秒 |
| `HUGEGRAPH_MCP_STATE_DIR` | XDG 状态目录或 `~/.local/state/hugegraph-mcp` | 写入计划与回执的持久化目录 |

### 可选 AI 功能

先按 [HugeGraph-LLM 指南](./hugegraph-llm.md) 配置并启动模型服务，再在 MCP 客户端的 `env` 中加入：

```json
{
  "HUGEGRAPH_MCP_ALLOW_AI": "true",
  "HUGEGRAPH_AI_URL": "http://127.0.0.1:8001",
  "HUGEGRAPH_AI_TOKEN": "your-ai-service-token"
}
```

这段内容应合并到前面的 `env` 对象中。生成和抽取可保持只读；向量刷新要求满足以下条件：
- 客户端配置：`HUGEGRAPH_MCP_READONLY=false`、`HUGEGRAPH_MCP_ADMIN_MODE=true`，且调用时需传入 `confirm=true`。
- 服务端配置（HugeGraph-LLM）：需设置 `ENABLE_LOGIN=true` 与 `HUGEGRAPH_LLM_ENABLE_THIN_WRITES=true`，配置非默认的强 `USER_TOKEN`（避免使用弱默认值 `4321`），
  并通过 MCP 的 `HUGEGRAPH_AI_TOKEN` 传递有效认证。若服务端未开启写入门禁，刷新请求将被拒绝并返回 `FEATURE_DISABLED`（"Legacy Thin API writes are disabled"）。

MCP 与 HugeGraph-LLM 必须连接至同一个底层 HugeGraph 实例。能力校验协议仅校验图名与图空间，
而实际刷新完全由 AI 服务依据其自身的 `GRAPH_URL` 独立执行；修改 MCP 的 `HUGEGRAPH_URL` 并不会改变 AI 服务的数据目标。
若 MCP 在宿主机运行，而 AI 在容器中运行，二者访问图服务的网络地址可能不同：应在 AI 服务侧配置 `GRAPH_URL` 为容器可访问的地址
（例如 `http://server:8080`），并确保 `GRAPH_NAME` 与 `GRAPH_SPACE` 与 MCP 目标一致；不要让容器通过 `127.0.0.1` 访问宿主机上的图服务。

**能力校验协议**：
新版协议要求调用 `GET /vid-embeddings/refresh-capabilities` 返回 `protocol_version=1`，并在刷新前传递预期图名与 graphspace 由服务端进行合法性校验；不支持该协议的服务将被拒绝。该机制用于保障多租户与图空间隔离，未发布该特性的旧版本不强制依赖。

## 常见问题

- **客户端启动后没有工具**：检查 `uvx` 路径、Python 版本和进程 stderr；终端进程等待协议输入是正常行为。
- **找不到结构化查询工具**：检查是否选择了兼容工具集。`1.7.1` 使用 `v2_core`，也可直接不设置工具集变量。
- **返回 `FEATURE_DISABLED`**：先检查能力表、只读、AI 和管理开关；部分操作是后端能力限制，不能仅靠修改配置开放。
- **AI 调用失败**：检查服务地址、token、容器网络和 AI 日志。MCP 返回的服务不可用错误不一定意味着模型已下线。
- **向量接口返回 400 或 429**：检查提供商的单次输入条数及请求频率限制。每批最大条数和并发请求数是不同限制；
  应在 HugeGraph-LLM 的向量适配与索引构建路径中处理，而不是更换 MCP 工具集。

工具响应中的 `ok=false` 表示失败，请同时检查 `error.type`、`error.retryable` 和 `warnings`，
不要只根据 MCP 连接成功或 HTTP 状态判断业务操作成功。

## 后续阅读

- [HugeGraph-LLM](./hugegraph-llm.md)
- [HugeGraph-MCP 源码与 README](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-mcp)
- [集成验证](https://github.com/apache/hugegraph-ai/blob/main/hugegraph-mcp/docs/integration.md)
- [PyPI 发行包](https://pypi.org/project/hugegraph-mcp/)

仓库 `main` 的文档随源码更新。使用固定发行包时，应先核对对应版本；本文安装示例固定为 `1.7.1`。
