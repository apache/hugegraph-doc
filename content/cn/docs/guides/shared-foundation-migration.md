---
title: "1.8.0 共享基础模块迁移指南"
linkTitle: "1.8.0 Java 与升级迁移"
description: "调整 Java import 和插件实现，并准备 1.8.0 共享基础模块迁移所需的 Server、PD、Store 同步升级。"
weight: 8
---

1.8.0 共享基础模块迁移会改变 Java import 和扩展接口的签名，Server、PD、Store 也需要一起升级。
先根据集成方式找出受影响代码，再重新构建应用，并在部署前检查已有数据。

## 先确定需要调整的部分

| 你的集成方式 | 需要准备什么 |
|---|---|
| Java 代码使用 Server 的 ID、schema 元数据、查询或索引 | 调整 import 和受影响签名，使用配套的 1.8.0 依赖包重新编译。 |
| 自定义序列化器、`HugeGraph` 实现或元素子类 | 按下方说明修改 SPI 契约和共享元素状态的适配。 |
| 自定义 Gremlin import 或脚本 | 替换旧 `IdGenerator` 类名，并验证发行包中的 Gremlin 服务启动。 |
| Hubble、Java client 或 Computer 集成 | 配套依赖包可用后，应用对应的异常类调整。 |
| HStore 部署 | 对齐 PD 命名空间，检查旧的 Store 重建索引，同步升级所有写入端。 |
| Loader 或其他仅通过 REST 调用的集成 | 保留独立 client DTO，按实际使用情况迁移受影响的 Java 调用。 |

实现已通过 [apache/hugegraph#3270](https://github.com/apache/hugegraph/pull/3270) 合入 Server 的 `master`，目标版本为 1.8.0。
升级时使用配套的 Server、PD、Store 发行包和下游依赖。
Java 映射和兼容性样本见[源码迁移指南](https://github.com/apache/hugegraph/blob/master/docs/shared-foundation-migration.md)。

## 共享代码现在由谁维护

此前 Server core 和 struct 分别维护了部分 ID、schema 类型、查询、元素和编解码实现。
迁移后，这些共享类型统一由一个模块维护，Server 和 Store 使用同一份实现。
`hugegraph-core` 继续运行图引擎，`hugegraph-struct` 提供共享模型和编解码，`hugegraph-common` 提供通用工具。

![迁移前 core 和 struct 分别维护共享实现，迁移后 core 与 Store 使用 struct，struct 使用 common，PD 使用 common](/images/shared-foundation/ownership.png)

*Core 保留图执行和适配器，Store 保留存储和 schema 生命周期，struct、common 统一维护共享实现。
箭头描述共享职责，不包含完整依赖树。*

| 维护模块 | 职责 |
|---|---|
| struct | ID、schema 元数据、类型码、查询、基础元素、属性和字节编解码、索引构建及分词器 |
| core | 事务、遍历、任务、schema 修改、后端适配器及索引更新编排 |
| Store | 通过 `SchemaGraph`/`SchemaDriver` 管理基于 PD 的 schema 访问、监听器和缓存生命周期 |
| common | JWT 签名与校验、共享认证常量和 RPC 配置接口 |

Server 的 HStore 适配器仍需要 PD、Store 客户端，Store 保留网络、PD 客户端及存储库。
PD、Store 不应依赖 core，struct 不应依赖 core 或 PD 客户端。

Core、Store 实现 `HugeGraphSupplier`，提供 schema、配置和时钟访问能力。
共享基础元素持有状态和邻接关系，`HugeVertex`、`HugeEdge` 保留引擎行为及基于同一状态的包装对象身份。
属性修改、克隆、删除、过期和加载状态都应通过这份共享状态传递。
Core 序列化器保留后端适配逻辑，委托共享代码完成编解码。
共享索引和 OLAP 选择接收调用方提供的 schema 候选及结果接收器，事务写入和后端能力检查仍由 core 执行。

## 调整 Java 源码和 SPI 实现

先检查代码实际使用的类型。以下 ID 构造调用保留相同的字符串值，只需要迁移 import。

**调整前，使用 1.7.0 core API**

```java
import org.apache.hugegraph.backend.id.Id;
import org.apache.hugegraph.backend.id.IdGenerator;

Id vertexId = IdGenerator.of("vertex-1");
```

**调整后，使用共享 API**

```java
import org.apache.hugegraph.id.Id;
import org.apache.hugegraph.id.IdGenerator;

Id vertexId = IdGenerator.of("vertex-1");
```

调整源码后，重新编译应用和插件。迁移后的类型同时改变了方法描述符，仅修改 import 不能让旧的已编译 jar 具备二进制兼容性。
被移除的 core 类没有通用兼容包。[插件示例](/cn/docs/guides/custom-plugin/)仍描述 1.7.0 API，接入迁移后的 API 时按下表调整。

| 原 Java 入口 | 迁移后的入口 |
|---|---|
| `org.apache.hugegraph.backend.id` 中下方列出的共享类型 | `org.apache.hugegraph.id.*` |
| `org.apache.hugegraph.schema.*` 元数据 | `org.apache.hugegraph.struct.schema.*` |
| `org.apache.hugegraph.backend.query` 中下方列出的共享类型 | `org.apache.hugegraph.query.*` |
| `org.apache.hugegraph.backend.query.serializer.*` | `org.apache.hugegraph.query.serializer.*` |
| `org.apache.hugegraph.backend.store.Shard` | `org.apache.hugegraph.backend.Shard` |
| `org.apache.hugegraph.backend.store.BackendEntry.BackendColumn` | `org.apache.hugegraph.backend.BackendColumn` |
| `org.apache.hugegraph.structure.HugeIndex` | `org.apache.hugegraph.structure.Index` |
| 后端序列化器中的共享字节与编码逻辑 | `org.apache.hugegraph.serializer.*` |
| Core `HugeException` | `org.apache.hugegraph.exception.HugeException` |
| `org.apache.hugegraph.SchemaGraph`/`SchemaDriver` | `org.apache.hugegraph.store.schema.*` |

ID 包只迁移 `Id`、`IdGenerator`、`EdgeId`、`IdUtil`、`SplicingIdGenerator`。
`SnowflakeIdGenerator` 保留在 core 的 `org.apache.hugegraph.backend.id`，继续使用原 import。
查询包迁移 `Query`、`ConditionQuery`、`Condition`、`IdQuery`、`IdPrefixQuery`、`IdRangeQuery`、`BatchConditionQuery`、`Aggregate`。
`QueryResults`、`ConditionQueryFlatten`、`EdgesQueryIterator`、`QueryBatch`、`QueryResultContext` 保留在 core 的
`org.apache.hugegraph.backend.query`，继续使用原 import。

`SchemaManager`、Schema 修改 builder 和后端专用序列化器仍在 core，需按实际受影响类型应用表中的映射。
客户端 REST DTO 保持独立，包括 Toolchain 的 `org.apache.hugegraph.structure.graph.Shard`。

| 扩展点 | 实现需要怎样调整 |
|---|---|
| `HugeGraph.sameAs(HugeGraph)` | Override 改为 `sameAs(org.apache.hugegraph.HugeGraphSupplier)`，没有旧签名的重载。 |
| `GraphSerializer.writeIndex`/`readIndex` | 接收或返回共享 `org.apache.hugegraph.structure.Index`，并调整调用方。 |
| 自定义 `HugeElement` 子类 | 通过 `element()` 提供共享 `BaseElement`，通过 `wrapProperty` 适配属性。 |

元素适配器继续使用共享状态，不要恢复已移除的引擎状态字段，也不要新增一套邻接集合。
Gremlin `classImports` 和脚本需将 `org.apache.hugegraph.backend.id.IdGenerator` 改为 `org.apache.hugegraph.id.IdGenerator`。
启动发行包中的 Gremlin 服务，验证仅存在于配置中的类名引用；Java 编译不会检查这些引用。

RPC 接口 `org.apache.hugegraph.rpc.RpcServiceConfig4Client` 和 `RpcServiceConfig4Server` 统一由 common 维护。
类名和签名保持不变，无需因这项迁移调整 RPC import 或配置。
`org.apache.hugegraph.auth.TokenGenerator` 也由 common 维护，调用方提供签名密钥，并将 JWT 失败转换为各服务的响应。
Common 的 JWT 依赖为 optional，直接使用 JWT 的模块需声明所需库。

### 使用配套依赖包时调整下游异常

| 原下游入口 | 替换为 |
|---|---|
| Hubble `org.apache.hugegraph.exception.HugeException` | `org.apache.hugegraph.exception.HubbleException` |
| Java client `org.apache.hugegraph.exception.NotSupportException` | `org.apache.hugegraph.exception.ClientNotSupportException` |
| Hubble 自带的 `org.apache.hugegraph.license.MachineInfo` | 保留 import，使用 common 的实现。 |

与 import 一起修改构造调用和 catch。`HubbleException` 保留 `RuntimeException` 父类和字符串构造器。
`ClientNotSupportException` 保留 `ClientException` 父类及 message/cause、message/arguments 构造器。
Computer 的 `HgkvDirImpl` 是受影响的 client 异常调用方。Struct 中名称相近的异常具有不同契约。
Loader 的 REST 边界和独立 client DTO 无需整体改为 struct。

Toolchain、Computer 调整仍是未发布的下游交接内容，需要配套发布、构建和发行包类路径检查。
检查构建后的 jar 以及源码，排除残留或传递依赖引入的同名类副本。

## 准备同步升级服务

将 Server、PD、Store 一起升级到配套发行包，本次迁移不支持混合版本滚动升级。
以下步骤适用于配套发行包已可用的部署。

![迁移流程包括备份和索引检查、修改 Java 代码、同步升级 Server PD Store、验证服务和数据，OLAP key 改为属性加顶点](/images/shared-foundation/migration.png)

*先备份数据和配置、检查受影响索引，再修改 import、SPI 并重新编译，随后同步升级配套服务、对齐 PD 命名空间。
最后验证发行包服务及图数据读写。OLAP 从每个顶点一行改为每个属性和顶点一行；匹配的旧行仍可读取，覆盖丢失的值不能恢复，不支持混合版本滚动升级。*

1. 按已有[备份恢复流程](/cn/docs/guides/backup-restore/)备份图数据，并保留部署配置。
2. 准备配套的 Server、PD、Store 发行包，以及重新构建的插件和实际需要的下游集成。
3. 按下方配置对齐元数据命名空间，保留既有底层图名称。
4. 在验证环境演练，启动发行包中的服务，读取历史数据，执行受影响查询和写入。
5. 暂停写入后同步升级部署。所有 Server、Store 写入端使用配套发行包且检查通过后，再恢复写入。

本次整合不会自动重写图数据、重建索引或恢复历史项。演练时需检查下方兼容性场景。

### 对齐 PD 元数据命名空间

Store 的 `pd.cluster` 默认值为 `hg`，在 Store `application.yml` 中按以下方式设置。

```yaml
pd:
  cluster: hg
```

对应环境变量为 `PD_CLUSTER`。

| Server 模式 | 必须与 Store `pd.cluster` 一致的配置 |
|---|---|
| `usePD=true` | Server 的 `cluster` |
| `usePD=false` | 图配置的 `pd.cluster` |

命名空间用于 schema、图配置、缓存监听和 TTL 清理器元数据。
同一个 Server 进程内的所有 HStore 图必须使用同一元数据命名空间。
`usePD=false` 时，首先打开的 HStore 图会用自身的 `pd.cluster` 绑定进程级 `MetaManager`。
后续图显式配置的冲突 `pd.cluster` 会记录警告并被忽略，不会建立独立命名空间。
同一个 Store 进程不能在冲突命名空间之间共享 schema driver。
保留 backend `graphspace/store/table` 名称，例如 `DEFAULT/hugegraph/g`；REST 标识 `DEFAULT-hugegraph` 不是元数据 key。

## 检查数据兼容性

| 数据或行为 | 保留或调整的行为 |
|---|---|
| 已存储的 ID 和属性 | 保留既有类型码、ID 与属性字节，以及配置默认值。 |
| 字符串 ID 比较 | 统一采用 Java UTF-16 顺序，包括从 UTF-8 字节加载的 ID；存储字节不变。 |
| 查询 JSON 和受支持的 Kryo 数据 | 类型迁移后仍需兼容解码历史 Java 类名。 |
| Schema map | 保留 wire 字段和 ID 身份；主键及 edge sort-key 列表保留顺序和重复项。 |
| Schema 端点 | 可读取匹配的冗余元数据和旧版仅含端点字段的 map；拒绝冲突或格式错误的端点。 |
| 普通 schema 索引 | Server 创建的 key 保留 key/name-TTL 布局。 |
| 带正过期时间的 Store SYSTEM-label 索引 | 保留稳定 key 和旧版 13 字节 value 封装，label 读取端识别这个有明确边界的封装。 |

Core SYSTEM-label 写入端保留原有字节。这次迁移不为这些 key 添加 TTL 后缀，也不改变前缀删除行为。
原本不支持的仅凭索引重建元素功能仍不支持。

元素分类通过 `BaseVertex.TypeContext` 保留生产方上下文。

| 上下文 | 既有系统顶点分类 |
|---|---|
| `STORAGE` | `~variables` 是任务数据。 |
| `ENGINE` | `~server`、`~role_data` 是服务端数据，`~variables` 是普通顶点数据。 |
| 两者 | `~task`、`~taskresult` 都是任务数据。 |

引擎 wrapper 选择 `ENGINE`，独立 storage 元素保留 `STORAGE`，使表路由沿用既有行为。

### 重建受影响的旧长文本索引

旧 Store `IndexBuilder` 将长文本值截短为 20 个字符，Server 查询使用完整值及其 hash。
共享 builder 现在采用 Server 契约。旧的截短索引行仍可解码，但不会自动匹配完整值查询。

若部署曾通过 Store 重建索引，应找出受影响索引，必要时从图数据重新构建。
本次迁移不自动重建索引，也不能恢复缺失的历史项。普通 Server 创建的索引 key 沿用原有契约。

### 验证 HStore OLAP 读取和删除

新 OLAP 行使用 `[property ID][vertex ID]` key，让同一顶点的多个 OLAP 属性可以共存。
旧行只以 vertex ID 作为 key，其 value 无需重写仍可读取。

| 操作 | 组合 key 与旧 key 的处理方式 |
|---|---|
| 读取某个属性 | 优先读取其组合 key；旧 vertex-only 行的 value 包含请求的 property ID 时，才回退读取。 |
| 删除某个属性 | 移除其组合行和匹配的旧行，保留其他属性。 |
| 读取旧写入端已经覆盖丢失的属性 | 本次修复无法恢复丢失的值。 |

恢复写入前，升级全部 Server、Store 写入端。旧写入端可能更新旧行，新读取端仍优先读取已经存在的组合行。
混合版本 OLAP 写入不在支持的升级契约内。

## 验证发行包服务和集成

运行受影响的 Java/SPI 测试，再检查 RocksDB、HStore 查询、认证、Store schema 与过滤行为，以及共享元素状态传播。
覆盖历史 ID、schema、属性和索引样本、分页、TTL、OLAP 场景。
核查解析后的依赖和发行 jar，排除禁止的模块依赖或重复 HugeGraph 类，并启动实际发行包中的服务，不依赖类路径顺序规避冲突。
构建和依赖清单的前置条件见[贡献指南](/cn/docs/contribution-guidelines/contribute/)。

实现、网站文档和下游依赖包仍需配套发布。
根据配套发行包、依赖包和运行结果决定采用迁移的时间；只编译源码或跳过测试的构建不足以确认可用性。
