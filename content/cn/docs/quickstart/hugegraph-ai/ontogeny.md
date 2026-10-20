---
title: "Ontogeny"
linkTitle: "Ontogeny"
weight: 7
---

Ontogeny（个体发育）是一个自我进化的运营本体平台，随 [HugeGraph-AI](https://github.com/apache/hugegraph-ai) 仓库的 `ontogeny` 分支发布。它把企业的业务语义（对象、属性、链接）与业务操作（动作、函数、策略）建模为 Git 中的声明式 YAML，再通过一个受治理的统一 API 提供给应用、分析与 AI Agent，并可选投影到 [HugeGraph](https://github.com/apache/hugegraph) 以支持深图查询。名字即主张：本体不是静态的 schema，而是一个活物——在 Git 里被定义，编译成表与图，再在使用中成长。

整个系统画在一块看板上——这也是控制台的「总览」页，以及下文各能力的地图：

![Ontogeny 总体架构图](/images/docs/hugegraph-ai/ontogeny-arch-board-zh.png)

> [!NOTE]
> API 采用 session/bearer 认证。开发头 `X-Ontogeny-Principal` 在评估场景默认开启（`ONTOGENY_DEV_AUTH=0` 关闭）。生产环境务必关闭：届时 Agent 入口（REST + `/mcp`）要求真实登录驱动，且每个会话都记录实际操作者。

## 环境要求

- Docker（Compose 部署），或 Python 3.10 及以上并安装 `uv`，另需 Node.js 与 npm 构建前端控制台
- 可选组件，均可替换、缺省即降级，不影响运行：OpenAI 兼容的 LLM 端点（Ollama 开箱即用，助手与自进化提案器共用）；HugeGraph Server 1.5.0 及以上作为图投影存储（Compose 可一键启动）；以 Postgres 替换默认的 SQLite 存储
- 如需以 Agent 驱动平台，准备一个 MCP 客户端（Claude Desktop、Cursor、LangGraph、`mcp` SDK 均可）

## 使用 Docker Compose 部署

```bash
git clone -b ontogeny https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
docker compose up -d
# docker compose --profile postgres up -d   # 元数据/对象存储换用 Postgres
# docker compose --profile graph up -d      # 追加 HugeGraph 图投影
```

启动后，控制台与 API 位于 `http://localhost:8000`。首次启动会自动创建管理员 `admin`，生成的初始密码打印在容器日志中；也可预先设置 `ONTOGENY_ADMIN_PASSWORD` 自定密码。

默认 profile 是自包含演示（SQLite + 种子数据），一条命令即可得到带真实制造域数据的运行看板——本体模型、Agent 入口与 RSI 闭环一屏可览：

![Ontogeny 运行看板](/images/docs/hugegraph-ai/ontogeny-dashboard-zh.png)

## 从源码启动

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

`--demo` 生成自包含目录 `.ontogeny-demo/`（播种的源库 + 示例本体包）；重启保留，`--reseed` 重建，首次启动自动重放演示剧本。为助手与 RSI 提案器接入大模型：

```bash
ONTOGENY_LLM_BASE_URL=http://<ollama>:11434 ONTOGENY_LLM_MODEL=qwen3:27b ontogeny serve --demo --open
```

已有现成领域包？在控制台侧栏的域切换器中选择**新域 → 导入本体包**，上传 zip（例如 `domains/product-manufacturing.zip`）即可校验-安装-激活一步完成。

## 核心能力

### Git 原生本体 DSL

11 种声明式资源（`apiVersion: ontogeny/v1`）覆盖语义层（对象类型、链接类型）、动力学层（动作、函数）、治理层（策略集、Agent 插件）、派生数据（投影）与自进化（评测套件、进化策略）。建模即 YAML + Pull Request——共识发生在代码评审，而不是锁死的表单界面。对象表与图 schema 都是编译产物：DSL 是唯一真源，一切都可以删除后从仓库重建。内置的 `product-manufacturing` 领域（7 对象、6 链接、8 动作、3 函数，含策略、投影与评测套件）既是控制台演示，也是测试套件的黄金样例。

### 唯一写入口，全程审计

所有写入都经过五段式运行时——参数校验 → 规则 → Cedar 策略 → 效果 → 不可变审计——副作用经事务性 outbox 投递。访问控制为 Cedar 子集，支持行级条件与默认拒绝；每次执行与每次拒绝都落入不可变审计流，Agent 的每一步都可归因、可回放。

### Agent 是一等公民，同样受治理

Agent 没有侧门。本体以 MCP 工具面的形式挂在 `/mcp`：`agent_open_session(plugin, task)` 为声明的插件打开受治理会话，每次调用携带 `plugin` / `session_id` / `thought`；预算、工具白名单、审批门与步骤轨迹对 REST 会话协议同等生效。写操作在控制台泊位等待人工审批；无会话调用只读。同一入口在控制台每页右下角的悬浮图标之后：

![Ontogeny Agent 控制台](/images/docs/hugegraph-ai/ontogeny-agent-console.png)

### 治理轨道内的自进化（RSI）

进化闭环按「观测 → 提案 → 评测 → 晋升 → 热加载」运行：遥测检测器把真实运行转成适应度信号，LLM 在封闭变异目录内起草变更，确定性评测套件（查询回归 + 动作时序穿越回放）负责选择——选择权从不交给 LLM。晋升分层：T0 低风险变更自动合并，T1 默认走人工评审 PR，T2 金丝雀发布，T3 宪法层（放宽策略、密级、所有权）仅限人工。一句话：模型变异外包给模型，选择绝不外包。

### 按需的 HugeGraph 图投影

`Projection` 资源把对象与链接按白名单投影进 HugeGraph，服务多跳与深图查询。投影永不做真源：安全密级永不入图，一致性为最终一致；未配置投影时查询自动回退 SQL 递归——拔掉它，平台优雅降级而非停摆。

## 更多资源

- Ontogeny 源码目录：<https://github.com/apache/hugegraph-ai/tree/ontogeny>
- 仓库内文档（架构 + 使用，中英双语）：[`docs/`](https://github.com/apache/hugegraph-ai/tree/ontogeny/docs)
- 全量 API 契约：运行实例上的 `GET /openapi.json`
- [HugeGraph-LLM](./hugegraph-llm.md) —— 同仓库主线上的 GraphRAG 与知识图谱构建
