---
title: "HugeGraph Gremlin"
linkTitle: "Gremlin 查询语言"
weight: 1
---

### 概述

HugeGraph 原生支持 [Apache TinkerPop3](https://tinkerpop.apache.org) 的图遍历查询语言 [Gremlin](https://tinkerpop.apache.org/gremlin.html)。
与关系型数据库使用的声明式 SQL 不同，Gremlin 是一种通用的图遍历与计算语言，能够精准控制图的拓扑路径探索，执行实体创建（Vertex 与 Edge）、属性修改、批量删除以及复杂的图分析。

HugeGraph 基于 TinkerPop **3.8.1** 引擎构建。完整规范与语法参考请查阅 [Apache TinkerPop 3.8.1 官方参考文档](https://tinkerpop.apache.org/docs/3.8.1/reference/)。
若习惯声明式模式匹配（类似 SQL 或 Neo4j 风格），HugeGraph 同时提供 [Cypher 查询语言](/cn/docs/language/hugegraph-cypher/) 支持。

---

### TinkerPop 特性支持

HugeGraph 实现了 TinkerPop 规范核心接口，针对图存储、顶点、边以及属性数据类型的具体支持情况如下：

#### 图级特性（Graph Features）

| 特性名称 | 含义与说明 | 支持情况 |
|---|---|---|
| `Computer` | 是否支持基于 `GraphComputer` 的 OLAP 图计算引擎（HugeGraph 服务端专注实时 OLTP 遍历，大规模图计算由独立组件支持） | `false` |
| `Transactions` | 是否支持事务机制（原生支持 ACID 事务提交与回滚） | `true` |
| `Persistence` | 是否原生将数据持久化到磁盘介质（取决于所配置的底层存储后端，RocksDB/Cassandra/HBase 等均持久化存储） | 取决于后端 |
| `ThreadedTransactions` | 是否支持通过 `createThreadedTx()` 在多个线程间共享同一个执行事务 | `false` |
| `ConcurrentAccess` | 是否支持同一底层数据实例的多连接并发访问 | `false` |
{.wide}

#### 顶点特性（Vertex Features）

| 特性名称 | 含义与说明 | 支持情况 |
|---|---|---|
| `UserSuppliedIds` | 是否允许在创建顶点时由用户指定自定义标识符（HugeGraph 支持用户自定义、主键和自动生成等策略） | `true` |
| `NumericIds` | 顶点内部标识符是否限定为纯数值类型 | `false` |
| `StringIds` | 顶点内部标识符是否支持字符串类型 | `true` |
| `UuidIds` | 顶点内部标识符是否原生限定为 UUID 格式 | `false` |
| `CustomIds` | 顶点内部标识符是否支持复合自定义对象 | `true` |
| `AnyIds` | 顶点内部标识符是否允许任意 Java 对象类型 | `false` |
| `AddProperty` | 是否支持向顶点添加或动态更新属性 | `true` |
| `RemoveProperty` | 是否支持从顶点移除已有属性 | `true` |
| `AddVertices` | 是否支持向图中添加新顶点 | `true` |
| `MultiProperties` | 单个顶点同一属性名下是否支持存储多个值（多值属性） | `true` |
| `DuplicateMultiProperties` | 在启用多值属性时，是否允许存在相同的重复值 | `true` |
| `MetaProperties` | 是否支持在属性上附加元属性（属性的属性） | `false` |
| `RemoveVertices` | 是否支持从图中删除指定顶点 | `true` |
{.wide}

#### 边特性（Edge Features）

| 特性名称 | 含义与说明 | 支持情况 |
|---|---|---|
| `UserSuppliedIds` | 是否允许直接指定边标识符（HugeGraph 边 ID 自动由起点、标签、排序键与终点复合生成） | `false` |
| `NumericIds` | 边内部标识符是否限定为纯数值类型 | `false` |
| `StringIds` | 边内部标识符是否支持字符串类型 | `true` |
| `UuidIds` | 边内部标识符是否限定为 UUID 格式 | `false` |
| `CustomIds` | 边内部标识符是否支持复合自定义对象 | `true` |
| `AnyIds` | 边内部标识符是否允许任意 Java 对象类型 | `false` |
| `AddProperty` | 是否支持向边添加或动态更新属性 | `true` |
| `RemoveProperty` | 是否支持从边移除已有属性 | `true` |
| `AddEdges` | 是否支持在顶点之间建立边 | `true` |
| `RemoveEdges` | 是否支持从图中删除指定边 | `true` |
{.wide}

#### 数据类型支持（Data Type Features）

| 特性名称 | 含义与说明 | 支持情况 |
|---|---|---|
| `BooleanValues` | 布尔类型属性（`boolean`） | `true` |
| `ByteValues` | 单字节整数（`byte`） | `true` |
| `DoubleValues` | 双精度浮点数（`double`） | `true` |
| `FloatValues` | 单精度浮点数（`float`） | `true` |
| `IntegerValues` | 32 位整型（`int`） | `true` |
| `LongValues` | 64 位长整型（`long`） | `true` |
| `MapValues` | 是否支持直接存储嵌套 Map 键值对对象 | `false` |
| `MixedListValues` | 是否支持存储不同类型混合元素的列表 | `false` |
| `BooleanArrayValues` | 布尔数组类型（`boolean[]`） | `false` |
| `ByteArrayValues` | 二进制字节数组（`byte[]`，常用于 Blob 或向量嵌入存储） | `true` |
| `DoubleArrayValues` | 双精度浮点数组（`double[]`） | `false` |
| `FloatArrayValues` | 单精度浮点数组（`float[]`） | `false` |
| `IntegerArrayValues` | 整型数组（`int[]`） | `false` |
| `LongArrayValues` | 长整型数组（`long[]`） | `false` |
| `SerializableValues` | 是否支持直接存储任意 Java 序列化对象 | `false` |
| `StringArrayValues` | 字符串数组（`String[]`） | `false` |
| `StringValues` | 标准文本字符串类型（`text`/`string`） | `true` |
| `UniformListValues` | 存储同类型元素的集合列表（由 Schema 中的 `cardinality()` 与 `valueList()` 机制原生支持） | `false`（由 Schema 支持） |
{.wide}

---

### Gremlin 常用步骤参考

HugeGraph 支持 Gremlin 遍历规范定义的各项步骤。完整说明与高级遍历用法请参阅 [TinkerPop 3.8.1 步骤参考](https://tinkerpop.apache.org/docs/3.8.1/reference/)。

| 步骤 | 说明 | 官方文档 |
|---|---|---|
| `addE` | 在两个顶点之间添加有向边 | [addE step](https://tinkerpop.apache.org/docs/3.8.1/reference/#addedge-step) |
| `addV` | 向图中添加新顶点 | [addV step](https://tinkerpop.apache.org/docs/3.8.1/reference/#addvertex-step) |
| `and` | 确保所有子遍历都产生有效输出 | [and step](https://tinkerpop.apache.org/docs/3.8.1/reference/#and-step) |
| `as` | 为步骤输出分配变量标签的调制器 | [as step](https://tinkerpop.apache.org/docs/3.8.1/reference/#as-step) |
| `by` | 与 `group`、`order` 等步骤配合使用的维度调制器 | [by step](https://tinkerpop.apache.org/docs/3.8.1/reference/#by-step) |
| `coalesce` | 返回首个产生结果的子遍历 | [coalesce step](https://tinkerpop.apache.org/docs/3.8.1/reference/#coalesce-step) |
| `constant` | 生成指定常量值，常与 `coalesce` 配合使用 | [constant step](https://tinkerpop.apache.org/docs/3.8.1/reference/#constant-step) |
| `count` | 统计遍历流中元素的总数量 | [count step](https://tinkerpop.apache.org/docs/3.8.1/reference/#count-step) |
| `datetime` | 构造日期时间对象或取得服务器当前时间（返回 `OffsetDateTime`） | [datetime function](https://tinkerpop.apache.org/docs/3.8.1/reference/#gremlin-groovy-differences) |
| `dedup` | 去除遍历流中的重复元素 | [dedup step](https://tinkerpop.apache.org/docs/3.8.1/reference/#dedup-step) |
| `discard` | 丢弃当前流中的遍历器输出 | [discard step](https://tinkerpop.apache.org/docs/3.8.1/reference/#discard-step) |
| `drop` | 从图中彻底删除对应实体（顶点、边或属性） | [drop step](https://tinkerpop.apache.org/docs/3.8.1/reference/#drop-step) |
| `fold` | 栅栏步骤，将流中所有项汇总折叠为一个 List | [fold step](https://tinkerpop.apache.org/docs/3.8.1/reference/#fold-step) |
| `group` | 根据指定的键与投影调制器对数据进行分组聚合 | [group step](https://tinkerpop.apache.org/docs/3.8.1/reference/#group-step) |
| `has` | 属性与元素过滤，支持 `hasLabel`、`hasId`、`hasNot` 等变体 | [has step](https://tinkerpop.apache.org/docs/3.8.1/reference/#has-step) |
| `inject` | 将外部离散值直接注入当前遍历流中 | [inject step](https://tinkerpop.apache.org/docs/3.8.1/reference/#inject-step) |
| `is` | 针对标量值执行布尔条件匹配与过滤 | [is step](https://tinkerpop.apache.org/docs/3.8.1/reference/#is-step) |
| `limit` | 限制遍历流返回的最大项数 | [limit step](https://tinkerpop.apache.org/docs/3.8.1/reference/#limit-step) |
| `local` | 局部作用域执行子遍历，类似于局部子查询 | [local step](https://tinkerpop.apache.org/docs/3.8.1/reference/#local-step) |
| `not` | 对子遍历匹配结果取反（必须不满足条件） | [not step](https://tinkerpop.apache.org/docs/3.8.1/reference/#not-step) |
| `optional` | 尝试执行子遍历；若有输出则返回，否则保留输入元素 | [optional step](https://tinkerpop.apache.org/docs/3.8.1/reference/#optional-step) |
| `or` | 确保至少有一个子遍历返回有效结果 | [or step](https://tinkerpop.apache.org/docs/3.8.1/reference/#or-step) |
| `order` | 按指定字段或比较规则对元素进行排序 | [order step](https://tinkerpop.apache.org/docs/3.8.1/reference/#order-step) |
| `path` | 收集并返回当前遍历所经过的历史完整路径 | [path step](https://tinkerpop.apache.org/docs/3.8.1/reference/#path-step) |
| `project` | 将多个调制结果投影为结构化 Map 映射 | [project step](https://tinkerpop.apache.org/docs/3.8.1/reference/#project-step) |
| `properties` | 获取指定键的 Property 实体对象 | [properties step](https://tinkerpop.apache.org/docs/3.8.1/reference/#properties-step) |
| `range` | 基于下标范围进行切片截取（起始索引至结束索引） | [range step](https://tinkerpop.apache.org/docs/3.8.1/reference/#range-step) |
| `repeat` | 循环执行指定的子遍历步骤 | [repeat step](https://tinkerpop.apache.org/docs/3.8.1/reference/#repeat-step) |
| `sample` | 从当前流中进行随机抽样 | [sample step](https://tinkerpop.apache.org/docs/3.8.1/reference/#sample-step) |
| `select` | 从历史路径或映射投影中提取特定标签的变量值 | [select step](https://tinkerpop.apache.org/docs/3.8.1/reference/#select-step) |
| `mergeV` | 按属性匹配顶点，存在则更新，不存在则创建（标准 Upsert 步骤） | [mergeV step](https://tinkerpop.apache.org/docs/3.8.1/reference/#mergevertex-step) |
| `mergeE` | 按属性与端点匹配边，存在则更新，不存在则创建（标准 Upsert 步骤） | [mergeE step](https://tinkerpop.apache.org/docs/3.8.1/reference/#mergeedge-step) |
| `tree` | 将遍历路径汇总聚合成树形层级结构 | [tree step](https://tinkerpop.apache.org/docs/3.8.1/reference/#tree-step) |
| `unfold` | 将集合或数组结构展开为连续的流元素 | [unfold step](https://tinkerpop.apache.org/docs/3.8.1/reference/#unfold-step) |
| `union` | 并行执行多个子遍历并合并其输出结果 | [union step](https://tinkerpop.apache.org/docs/3.8.1/reference/#union-step) |
| `V` | 顶点检索与端点跳转基础步骤：`V`、`E`、`out`、`in`、`both`、`outE`、`inE` 等 | [vertex steps](https://tinkerpop.apache.org/docs/3.8.1/reference/#vertex-steps) |
| `where` | 使用表达式或谓词（`eq`、`neq`、`gt` 等）进行条件筛选过滤 | [where step](https://tinkerpop.apache.org/docs/3.8.1/reference/#where-step) |
{.wide .expand}
