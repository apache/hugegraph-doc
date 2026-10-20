---
title: "Ontogeny"
linkTitle: "Ontogeny"
weight: 7
---

`ontogeny` —— 希腊语 **onto-**（存在，即 *ontology* 本体论的词根）+ **genesis**（诞生、发育）：生物学术语，指一个个体从胚胎到成体的**全生命周期发育**。名字即主张：本体在这里不是静态的 schema，而是一个活物——在 Git 里被定义，编译成表与图，再在使用中成长。它是一个**自我进化的运营本体平台**：把企业的业务语义（对象、属性、链接）与业务动作（动作、函数、策略）建模为 Git 中的声明式 YAML，通过一个受治理的统一 API 提供给应用、分析与 AI Agent，并可选投影到 [Apache HugeGraph](https://github.com/apache/hugegraph) 以支持深图查询。

整个系统画在一块看板上——这也是控制台的「总览」页，以及下文所有内容的地图：

![总体架构图](/images/docs/hugegraph-ai/ontogeny-arch-board-zh.png)

*上：八类一等 DSL 公民（Action = 唯一写入口，EvalSuite = 选择器）。中：在线主链路（建模 → 探索 → 执行 → 管控 → 审计）与离线 RSI 闭环，由 Agent 主轴相连——其读写穿越同一批门，轨迹与审批回流为进化信号。下：支撑层与三条贯穿不变量（所有权、单一门、Git 即真源）。*

## 核心特性

- **Git 原生本体**——建模即 YAML + Pull Request；共识发生在代码评审，而不是锁死的表单界面
- **单进程内核**——`ontogeny serve` = 注册表 + 查询引擎 + Action 运行时，跑在 SQLite / Postgres 上
- **Agent 优先**——`/mcp` 上的受治理 MCP 工具面；Agent 与人共用同一策略面，写操作必须过人工审批门
- **自进化（RSI）**——观测 → 变异（LLM 生成 DSL diff）→ 选择（确定性评测套件）→ 发布（T0 自动合并 / T1 评审 / T2 金丝雀）；*变异外包给 LLM，选择绝不外包*
- **宪法护栏**——机器提案与人类走同一 Git/CI 通道；放宽策略、密级与层级定义永远需要人工评审
- **双语企业控制台**——React 19 + TypeScript：本体画布（可浏览*也可编辑*）、图探索、动作执行器、审计、自进化控制台

建模即代码评审，而非填表——本体画布展示域内每个对象、链接、动作与函数，引用关系悬停高亮：

![本体定义画布](/images/docs/hugegraph-ai/ontogeny-ontology-canvas-zh.png)

## 快速开始

### 方式一：Docker（推荐）

```bash
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai

docker compose up -d          # 自包含演示（SQLite + 种子数据）
# docker compose --profile postgres up -d   # 换用 Postgres
# docker compose --profile graph up -d      # 追加 HugeGraph 图投影
```

控制台 + API：**http://localhost:8000** —— 首次启动会自动创建 `admin` 账号，生成的初始密码打印在容器日志中（也可预先设置 `ONTOGENY_ADMIN_PASSWORD`）。一条命令即可得到带真实制造域数据的运行看板——本体模型、Agent 入口与 RSI 闭环一屏可览：

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

可选：为助手与 RSI 提案器接入大模型——`ONTOGENY_LLM_BASE_URL=http://<ollama>:11434 ONTOGENY_LLM_MODEL=qwen3:27b ontogeny serve --demo --open`。

> [!NOTE]
> API 采用 session/bearer 认证。开发头 `X-Ontogeny-Principal` 在评估场景**默认开启**（`ONTOGENY_DEV_AUTH=0` 关闭）。生产环境务必关闭：届时 Agent 入口（REST + `/mcp`）要求真实登录驱动，且每个会话都记录实际操作者。

已有现成领域包？侧栏域切换器 → **新域 → 导入本体包**，上传 zip（如 `domains/product-manufacturing.zip`）即可校验-安装-激活一步完成。

## 接入 Agent（MCP）

把任何 MCP 客户端（Claude Desktop、Cursor、LangGraph、`mcp` SDK）指向 **`http://<host>/mcp`**：

1. `agent_open_session(plugin, task)` —— 为声明的插件打开受治理会话；
2. 每次工具调用携带 `plugin` / `session_id` / `thought` —— 预算、工具目录、审批门与步骤轨迹对 REST 会话协议同等生效；
3. 写操作在控制台泊位等待人工审批；无会话调用只读。

同一入口在控制台每页右下角的悬浮图标之后——点开即可把任务交给声明的插件（Agent 运行、本体问答或 RSI 提案）：

![Agent 控制台弹窗](/images/docs/hugegraph-ai/ontogeny-agent-console.png)

看得见的治理：每次执行与每次拒绝都落入不可变审计流（已执行 / 规则拒绝 / 策略拒绝），Agent 的每一步都可归因、可回放：

![审计流](/images/docs/hugegraph-ai/ontogeny-audit-zh.png)

## 生产建议

- **单进程内核**：注册表、outbox、派生、进化与投影 Worker 都在同一服务进程内。不要用 `uvicorn --workers N` 扩容；按域扩容（一库一进程）。
- **可观测性**：`GET /api/v1/admin/metrics` —— 查询/动作/Agent/outbox 计数器直接来自平台自身的表，零额外依赖。
- **查询基线**：`python tools/bench_query.py`（search/filter/traverse 的 p50/p95）。

## 更多资源

- Ontogeny 源码目录：<https://github.com/apache/hugegraph-ai/tree/ontogeny>
- 全量 API 契约：运行实例上的 `GET /openapi.json`
- [HugeGraph-LLM](./hugegraph-llm.md) —— 同仓库主线上的 GraphRAG 与知识图谱构建
