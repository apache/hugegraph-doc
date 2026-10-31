---
title: "Ontogeny"
linkTitle: "Ontogeny"
weight: 7
---

**Ontogeny** 是面向 AI 业务场景的可演进业务本体（Ontology）平台，位于 [HugeGraph-AI](https://github.com/apache/hugegraph-ai/tree/ontogeny) 模块。
它将业务语义（实体、属性、关联）与业务操作（Action、函数、校验策略）统一为 Git 原生的声明式 YAML 规范，
通过统一且受管控的 API 提供给应用服务与 AI Agent 调用，并支持将数据投影至 [Apache HugeGraph](https://github.com/apache/hugegraph) 进行深度图分析。

### 架构全景

下图展示了系统核心模块与执行链路关系：

![总体架构图](/images/docs/hugegraph-ai/ontogeny-arch-board-zh.png)

系统分为三层设计：
- **上层**：核心 DSL 规范定义，其中 Action 为唯一的写入口，EvalSuite 负责质量评估。
- **中层**：在线链路（建模 → 探索 → 执行 → 管控 → 审计）与离线自进化（RSI）闭环，Agent 读写统一穿透策略管控门禁，调用轨迹回流为进化信号。
- **底层**：平台运行时与全局不变量（明确所有权、单一门禁、Git 作为单一可信源）。

## 核心特性

- **声明式 Git 原生建模**：本体模型以 YAML 维护，通过 Pull Request 进行版本追踪与代码评审，避免依赖黑盒配置。
- **轻量单进程内核**：`ontogeny serve` 集成注册表、查询引擎与 Action 运行时，支持 SQLite 与 PostgreSQL。
- **面向 Agent 的治理**：通过 `/mcp` 端点对外暴露受控 MCP 工具面，Agent 与用户共享统一策略层，写操作支持人工审批门禁。
- **确定性自进化（RSI）**：通过“观测 → 变异（LLM 辅助生成 DSL diff）→ 选择（基于规则的确定性评测套件）→ 发布”完成闭环，规则保障安全底线。
- **全链路审计**：每一次调用与拦截均记录不可变审计流，支持溯源分析与回放。
- **双语控制台**：基于 React 19 构建，提供本体画布可视化、图探索、动作执行器、审计中心与自进化管理。

本体画布集中展示领域内的对象、关联、动作与函数，支持可视化依赖分析与编辑：

![本体定义画布](/images/docs/hugegraph-ai/ontogeny-ontology-canvas-zh.png)

## 快速开始

```bash {tab="Docker (推荐)"}
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/ontogeny

# 启动自包含演示环境（SQLite + 预置种子数据）
docker compose up -d

# 可选：启动附加的 Postgres 或 HugeGraph 容器（注意：Ontogeny 默认仍使用内置 SQLite，若需切换至 Postgres 需同时配置 ONTOGENY_DB_DSN 环境变量）
# docker compose --profile postgres up -d
# docker compose --profile graph up -d
```

```bash {tab="源码编译"}
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/ontogeny

# 后端安装（包含 mcp 依赖）
uv venv && source .venv/bin/activate && uv pip install -e '.[mcp]'

# 前端控制台构建
cd web && npm install && npm run build && cd ..

# 启动演示服务
ontogeny serve --demo --open
```

服务启动后访问 **http://localhost:8000**。系统首次启动会自动创建 `admin` 账号，初始默认密码为 `ontogeny@2026`。
在源码启动时，可通过环境变量 `ONTOGENY_ADMIN_PASSWORD` 自定义初始密码；Docker 部署时该变量不会自动传入容器，建议登录后通过控制台修改默认密码。

可选接入大语言模型以启用助手与 RSI 进化功能：
```bash
ONTOGENY_LLM_BASE_URL=http://<ollama>:11434 ONTOGENY_LLM_MODEL=qwen3:27b ontogeny serve --demo --open
```

> [!NOTE]
> API 采用 session/bearer 鉴权。用于评估的开发请求头 `X-Ontogeny-Principal` 在未关闭时会将任意请求视为管理员权限。
> 源码运行可通过 `ONTOGENY_DEV_AUTH=0` 关闭；Docker 部署时需在 `docker-compose.yml` 或容器环境中显式配置 `ONTOGENY_DEV_AUTH: "0"`。
> 生产环境务必关闭该头并使用真实凭据登录。

若需导入自定义领域包，可在控制台侧栏选择 **新域 → 导入本体包**，上传包含自定义领域 YAML 规范的 zip 压缩包进行安装与激活
（演示模式下已默认加载 `domains/product-manufacturing` 等内置领域，无需重复导入）。

运行看板展示模型规模、Agent 交互与系统状态：

![运行看板](/images/docs/hugegraph-ai/ontogeny-dashboard-zh.png)

## 接入 Agent（MCP）

任何支持 MCP 协议的客户端（如 Claude Desktop、Cursor、LangGraph、`mcp` SDK）均可连接至 **`http://<host>/mcp`**：

1. **开启受控会话**：通过 `agent_open_session(plugin, task)` 为指定插件初始化会话上下文。
2. **携带治理上下文调用**：工具调用时传递 `plugin`、`session_id` 和 `thought`，统一遵循配额与策略拦截。
3. **写入门禁审核**：写操作默认在控制台挂起等待管理员审批（`approval.writes=confirm`）；对于配置为
   `approval.auto_actions` 白名单内的操作可自动执行，配置为 `never` 时则完全拒绝写入；无会话的请求默认仅限只读。
{.steps}

控制台提供悬浮 Agent 对话入口，可直接执行任务调用、本体问答或触发 RSI 提案：

![Agent 控制台弹窗](/images/docs/hugegraph-ai/ontogeny-agent-console.png)

所有操作与拦截记录均实时写入审计流，支持全链路追溯：

![审计流](/images/docs/hugegraph-ai/ontogeny-audit-zh.png)

## 生产运维建议

- **单进程内核**：注册表、Outbox、计算与投影 Worker 均运行在同一进程中。请勿使用 `uvicorn --workers N` 启动多个 worker，建议按领域（Domain）维度横向划分。
- **可观测性指标**：通过 `GET /api/v1/admin/metrics` 获取查询、动作、Agent 与 Outbox 的监控统计指标。
- **性能基准评估**：可运行 `python tools/bench_query.py` 评估 search、filter 及 traverse 操作的延迟表现。

## 更多资源

- Ontogeny 源码目录：<https://github.com/apache/hugegraph-ai/tree/ontogeny>
- OpenAPI 契约接口：访问运行实例的 `GET /openapi.json`
- [HugeGraph-LLM](./hugegraph-llm.md) —— 同仓库主分支上的 GraphRAG 与知识图谱构建工具
