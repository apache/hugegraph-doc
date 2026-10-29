---
title: "HugeGraph 1.8.0 Release Notes"
linkTitle: "Release-1.8.0"
weight: 1
---

> WIP: This doc is under construction, please wait for the final version (BETA)

### 运行环境/版本说明

- **Java 运行环境**：**1.8.0** 版 HugeGraph 组件（Server、PD、Store）统一要求 **Java 17** 运行与源码构建环境（1.7.0 是最后一个支持 Java 11 的版本）。
- **查询与脚本引擎**：图遍历与查询框架升级至 **Apache TinkerPop 3.8.1**，脚本引擎统一升级至 **Groovy 4.0.25**。

### 升级与兼容性重点（Breaking Changes）

#### 1. Gremlin 查询语法重要破坏性变更
- **移除 `has(key, traversal)` 重载**：Groovy 下旧写法在 HugeGraph 1.8 下会因强类型校验直接抛出 `Invalid data type of query value` 异常报错（纯 TinkerGraph 下会返回空结果）。简单条件直写谓词 `has('age', gt(30))`，复杂过滤改用 `filter(__.values('age').is(gt(30)))`。
- **移除 `store()` 与带 Scope 的 `aggregate()`**：全局贪心收集统一改用 `aggregate('x')`，局部/逐对象收集改用 `local(__.aggregate('x'))`。
- **无参 `none()` 更名为 `discard()`**：丢弃输入遍历必须使用 `discard()`（避免与新集合过滤 `none(P)` 冲突）。
- **`by()` 缺失属性严检**：缺失属性在 `order().by()` 下直接过滤顶点，在 `project().by()` 下不再返回该 key，在 `path().by()` 下直接过滤路径；需保留缺失字段请在 `by()` 中显式使用 `coalesce()` 补默认值。
- **`choose()` 分支语义收敛**：多条件重叠仅执行首个匹配分支；无匹配或属性缺失默认原样放行穿透（需过滤请显式加 `Pick.none` / `Pick.unproductive` 分支配合 `discard()`）。

> 完整改写代码对照与全量细则速查表请参阅：[HugeGraph 1.8.0 Gremlin 迁移与兼容性指南](../guides/gremlin-migration-3.8)。

#### 2. 服务端配置与客户端兼容
- **Serializer 类名迁移**：`conf/gremlin-server.yaml` 中序列化器包路径由 `org.apache.tinkerpop.gremlin.driver.ser.*` 迁移至 `org.apache.tinkerpop.gremlin.util.ser.*`。
- **HugeGraph Client 1.5.0**：服务端提供向后兼容适配，1.5.0 客户端常规 CRUD 与 Schema 操作可正常连通 1.8.0；但 Gremlin 查询因别名缺少 GraphSpace 前缀会执行失败，且鉴权路径变更，需升级客户端或改用 HTTP 接口。
- **不再默认捆绑 GPL word 分词器**：因开源协议合规，默认发行包不再捆绑 GPLv3 的 `word-1.3.jar`。配置了 `search.text_analyzer=word` 的图仍受支持，
  只需将 `word-1.3.jar` 放入 Server 的 `lib/` 目录即可正常使用；亦可切换为内置的 IK 或 SmartCN（注意切换分词器后需重建已有搜索索引）。

---

### hugegraph

#### API Changes
- **BREAKING CHANGE**: Upgrade TinkerPop to 3.8.1 and require Java 17 runtime
- **BREAKING CHANGE**: Shared foundation module migration (`hugegraph-struct`)

#### Feature Changes
- 支持 TinkerPop 3.8 步骤，包括 `discard()`、`mergeV()`、`mergeE()` 以及日期步骤（`datetime()`、`dateAdd()`、`dateDiff()`）
- Adapt HugeSecurityManager and Groovy 4.0.25 on Java 17
- Improve count query visibility inside uncommitted transactions
