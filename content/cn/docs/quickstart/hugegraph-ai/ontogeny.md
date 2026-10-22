---
title: "Ontogeny"
linkTitle: "Ontogeny"
weight: 7
---

`ontogeny` —— 希腊语 **onto-**（存在，即 *ontology* 本体论词根）+ **genesis**（诞生、发育）：在生物学中指个体从胚胎到成体的**全生命周期发育**。
名字即主张：本体在此不仅是静态的 Schema，更是随业务持续演进的动态生命系统——在 Git 中以声明式管理，编译为数据表与图结构，并在实际使用中持续成长。
它是一个**具备自我演进能力的运营本体平台**：将企业的业务语义（对象、属性、关联）与业务动作（Action、函数、策略）统一建模为 Git 原生的声明式 YAML，
通过受治理的统一 API 供给应用、分析及 AI Agent 使用，并支持可选投影到 [Apache HugeGraph](https://github.com/apache/hugegraph) 执行深度图查询。

全系统全貌架构看板——亦是控制台「总览」仪表盘与各子模块的关系导图：

![总体架构图](/images/docs/hugegraph-ai/ontogeny-arch-board-zh.png)

*上层：八类核心 DSL 实体（Action 为唯一写入口，EvalSuite 为评测选择器）。中层：在线主链路（建模 → 探索 → 执行 → 管控 → 审计）与离线 RSI 闭环，
由 Agent 主轴贯通——读写穿透相同的策略管控门禁，执行轨迹与人工审批回流为自进化信号。底层：支撑层与三项全局不变量（所有权、单一门禁、Git 作为单一可信源）。*

## 核心特性

- **Git 原生本体**——建模即 YAML + Pull Request；共识通过代码评审达成，而非依赖锁死的表单界面
- **单进程内核**——`ontogeny serve` 集成注册表、查询引擎与 Action 运行时，支持 SQLite 与 PostgreSQL
- **Agent 优先**——在 `/mcp` 暴露受治理的 MCP 工具面；Agent 与人类共享同一策略层，写操作必须经由人工审批门禁
- **自进化能力（RSI）**——观测 → 变异（LLM 生成 DSL diff）→ 选择（确定性评测套件）→ 发布（T0 自动合并 / T1 评审 / T2 金丝雀验证）；*变异由大模型驱动，评测选择严格基于确定性规则*
- **宪法级护栏**——机器提案与人类代码走相同的 Git/CI 流水线；策略放宽、密级调整与层级定义始终需要人工复审
- **双语企业级控制台**——基于 React 19 + TypeScript：提供本体画布（支持浏览与可视化编辑）、图探索、动作执行器、审计中心与自进化管理面板

建模即代码评审，而非繁琐填表——本体画布集中展示域内所有对象、关联、动作与函数，悬停即可高亮依赖引用：

![本体定义画布](/images/docs/hugegraph-ai/ontogeny-ontology-canvas-zh.png)

## 快速开始

### 方式一：Docker（推荐）

```bash
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai

docker compose up -d          # 自包含演示（SQLite + 预置种子数据）
# docker compose --profile postgres up -d   # 仅启动 Postgres 容器，演示镜像默认仍使用 SQLite
# docker compose --profile graph up -d      # 启动 HugeGraph，需通过管理 API 配置图投影
```

控制台与 API 服务入口：**http://localhost:8000** —— 首次启动会自动创建 `admin` 账号，初始默认密码为 `ontogeny@2026`（容器日志中亦会打印）。
在生产环境或对外暴露 8000 端口前，请通过设置 `ONTOGENY_ADMIN_PASSWORD` 环境变量或进入控制台修改初始密码。
单条命令即可启动包含真实制造域示例数据的运行看板——直观呈现本体模型、Agent 入口与 RSI 进化闭环：

![运行看板——本体模型区块](/images/docs/hugegraph-ai/ontogeny-dashboard-zh.png)

### 方式二：从源码启动

```bash
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai

# 后端（带 mcp extra 才会挂载 /mcp）
uv venv && source .venv/bin/activate && uv pip install -e '.[mcp]'

# 前端控制台
cd web && npm install && npm run build && cd ..

# 一条命令演示：播种源库、安装示例本体、同端口伺服 UI + API
ontogeny serve --demo --open   # → http://127.0.0.1:8000/
```

可选：为助手与 RSI 提案器接入大模型：
`ONTOGENY_LLM_BASE_URL=http://<ollama>:11434 ONTOGENY_LLM_MODEL=qwen3:27b ontogeny serve --demo --open`。

> [!NOTE]
> API 采用 session/bearer 鉴权机制。用于本地评估的开发请求头 `X-Ontogeny-Principal` 在当前模式下**默认启用**（可通过设置 `ONTOGENY_DEV_AUTH=0` 关闭）。
> 生产环境务必停用该开发头：届时所有 Agent 访问入口（REST 与 `/mcp`）均需经由真实登录凭证驱动，且每个会话均会准确审计操作者身份。

已有现成领域包？侧栏域切换器 → **新域 → 导入本体包**，上传 zip 压缩包（如 `domains/product-manufacturing.zip`）即可一步完成校验、安装与激活。

## 接入 Agent（MCP）

把任何 MCP 客户端（Claude Desktop、Cursor、LangGraph、`mcp` SDK）指向 **`http://<host>/mcp`**：

1. `agent_open_session(plugin, task)` —— 为指定插件开启受治理会话；
2. 每次工具调用携带 `plugin` / `session_id` / `thought` —— 预算配额、工具目录、审批门禁与调用轨迹与 REST 会话机制完全一致；
3. 写操作将在控制台挂起等待人工审批；无会话的请求默认仅限只读。

控制台全局右下角提供了便捷的悬浮入口——随时点击即可向声明的插件下发任务（如 Agent 任务执行、本体问答或 RSI 进化提案）：

![Agent 控制台弹窗](/images/docs/hugegraph-ai/ontogeny-agent-console.png)

全程可追溯的治理审计：每一次执行与阻断均会写入不可变审计流（已执行 / 规则拦截 / 策略拒绝），Agent 的完整调用链路均支持归因与回放：

![审计流](/images/docs/hugegraph-ai/ontogeny-audit-zh.png)

## 生产建议

- **单进程内核**：注册表、Outbox、派生计算、进化引擎与图投影 Worker 均运行在同一服务进程中。请勿使用 `uvicorn --workers N` 启动多 worker，
  建议按领域（Domain）维度横向扩容（每个数据库对应单一进程）。
- **可观测性**：提供 `GET /api/v1/admin/metrics` 接口——查询、动作、Agent 与 Outbox 统计指标直接取自平台内置元数据表，无需额外依赖监控组件。
- **查询性能基准**：可运行 `python tools/bench_query.py` 评估 search、filter 及 traverse 的 p50/p95 延迟。

## 更多资源

- Ontogeny 源码目录：<https://github.com/apache/hugegraph-ai/tree/ontogeny>
- 全量 API 契约：运行实例上的 `GET /openapi.json`
- [HugeGraph-LLM](./hugegraph-llm.md) —— 同仓库主分支上的 GraphRAG 与知识图谱构建工具
