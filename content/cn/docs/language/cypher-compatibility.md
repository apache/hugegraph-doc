---
title: "Cypher 兼容性"
linkTitle: "Cypher 兼容性"
weight: 3
---

### 概述与支持范围

HugeGraph 支持 openCypher 9 声明式图查询规范，支持在 TinkerPop 引擎之上直接执行模式匹配与图数据读写。
本页汇总 Cypher 请求形式、参数绑定规则、支持的语法子集与行为边界。

接口端点为 `/graphspaces/{graphspace}/graphs/{graph}/cypher`。常规语法示例与 Gremlin 对照参见 [HugeGraph Cypher 指南](/cn/docs/language/hugegraph-cypher/)。

### 请求形式与参数绑定

| 请求形式 | Content-Type | 说明 |
|---|---|---|
| `POST`（推荐） | `application/json` | 请求体为 JSON 对象 `{"cypher": "...", "parameters": {...}}`，支持参数绑定 |
| `POST` | `application/json` | 请求体为原始 Cypher 文本字符串（用于无参数的纯文本语句） |
| `GET` | — | 查询参数 `?cypher=<URL 编码语句>`，适合简单只读查询 |
{.wide}

JSON 对象参数化请求示例：

```json
{
  "cypher": "MATCH (n:person) WHERE n.name = $name RETURN n.name",
  "parameters": {"name": "marko"}
}
```

#### 参数绑定规则

- **参数格式**：`cypher` 字段必须为非空字符串；`parameters` 若提供必须为 JSON 对象（省略表示空参数表）。
- **参数数量**：顶层 `parameters` 最多接受 16 个键。若需要传入更多属性，可将相关字段组织为嵌套 Map 对象，并在 Cypher 语句中显式引用字段（例如 `$props.name`）。
- **未绑定变量处理**：语句中引用未提供的 `$param` 时会直接抛出执行错误，拒绝执行（显式传入 `null` 是允许的）。
- **保留标记**：引擎将 `"  cypher.null"`（前导双空格）用作内部保留哨兵标记，绑定值中禁止传入该精确字符串。
- **错误响应**：执行错误或参数校验失败时，服务端返回 HTTP 400（或在 `status.code` 为 400 的响应体中返回错误详情），并在 `status.attributes.errors` 中提供包含 `code`、`message` 与 `hint` 的结构化错误详情。

### 语法与功能支持矩阵

| 分类 | 支持特性 | 说明 |
|---|---|---|
| 查询与模式 | 标签扫描、等值与范围过滤、逻辑组合（AND/OR/NOT）、单跳与多跳有向关系、正则匹配（`=~` 全匹配） | 范围过滤等条件需预先建立相应索引 |
| 结果投影 | 节点与标量投影、别名（`AS`）、属性访问、嵌套结构、关系 ID、路径表达、空值（null）处理 | 返回结果映射为标准 JSON 格式 |
| 聚合与排序 | `count`、`sum`、`min`、`max`、`avg`、`DISTINCT`、`ORDER BY`、`SKIP`、`LIMIT` | 分页与聚合计算由引擎自动转换为对应图遍历步骤 |
| 数据写入 | 顶点与边 `CREATE`、属性 `SET` / `REMOVE`、边与顶点 `DELETE` / `DETACH DELETE` | 创建边前建议先为端点顶点赋值并创建，避免简写形式因非空约束或主键缺失失败 |
{.wide}

### 写入约束与注意事项

在包含非空属性或使用 `PRIMARY_KEY` 策略的 Schema 下，双顶点简写 `CREATE (a)-[:knows]->(b)` 会因未提供属性而触发非空属性校验失败（`checkNonnullProperty`）或主键缺失错误。
建议将顶点与边的创建语句分开执行，并显式为顶点填充所需属性。

### 暂未支持的范围

以下高级语法和特性在当前版本中尚未直接提供，建议改用 Gremlin 或相应 REST API：
- **复杂子句**：`MERGE`、`OPTIONAL MATCH`、`WITH`、`UNWIND`、`UNION`、变长路径匹配（`*1..3`）；
- **过程调用**：`CALL dbms.*` / `CALL algo.*`（请使用 [Traverser REST API](/cn/docs/clients/restful-api/traverser/)）；
- **模式定义**：Cypher Schema DDL（请使用 [Schema REST API](/cn/docs/clients/restful-api/schema/)）；
- **协议与驱动**：Bolt 协议与驱动（请使用 HTTP REST API 或 [HugeGraph 客户端](/cn/docs/clients/hugegraph-client/)）。
