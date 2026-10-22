---
title: "FAQ"
linkTitle: "FAQ"
weight: 6
---

## 部署与启动 {#deployment}

### 如何选择 RocksDB 或 HStore {#choose-backend}

开发测试或单机部署可从 Server + RocksDB 开始。需要多节点扩展和多副本时，再部署 PD + Store + Server 的 HStore 集群。
容量和性能取决于图结构、查询方式及硬件，应使用自己的数据测试后决定。

1.7.0 支持 RocksDB、HStore、HBase 和 Memory。Cassandra、ScyllaDB、MySQL、PostgreSQL 等旧后端需使用低于 1.7.0 的版本。
部署步骤见 [Server 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-server/)。

### 启动时出现 core dumped 怎么查 {#core-dump}

先用 `java -version` 检查 JVM。HugeGraph 1.8.0 使用 Java 17，1.7.0 使用 Java 11。
再查看 Server 日志及 JVM 生成的 `hs_err_pid*.log`，核对崩溃位置、系统架构和本地库版本。
`core dumped` 也可能来自本地库或内存问题，不能只凭这条提示判断原因。

### 哪些后端需要 init-store {#initialize-backend}

RocksDB、HBase 首次使用前需要执行 `bin/init-store.sh`。Memory 和 HStore 不执行该脚本，HStore 的存储由 PD 和 Store 管理。
`backend` 与 `serializer` 必须配套，例如 RocksDB 使用 `binary`，不能随意替换序列化器。

服务已启动却提示后端未连接时，先检查初始化是否成功，再检查后端配置和服务连通性。

### init-store 报 GLIBCXX 版本缺失怎么办 {#native-library}

下面的错误表示加载 RocksDB 本地库时，系统的 `libstdc++` 没有提供所需符号。

```text
java.lang.UnsatisfiedLinkError: .../librocksdbjni....so:
.../libstdc++.so.6: version `GLIBCXX_3.4.10' not found
```

核对发行包支持的平台与系统架构，并检查实际加载的 `libstdc++`。使用兼容的运行环境或对应版本的官方容器镜像。
升级 C++ 运行库时按错误中缺少的符号核实兼容性，不能仅凭一个 GCC 版本号判断所有发行包是否可用。

### 应该使用哪个 Server 启动脚本 {#start-script}

当前发行包使用 `bin/start-hugegraph.sh`。GremlinServer 和 REST Server 在同一个进程中启动。
旧文档里的 `start-restserver.sh`、`start-gremlinserver.sh` 不适用于当前发行包。

### 启动脚本会加载哪些图 {#load-graphs}

脚本名与图名无关。Server 默认从 `conf/graphs` 加载本地图配置，可通过 `conf/rest-server.properties` 的 `graphs` 修改目录。
每张本地图使用独立配置文件，修改后重启 Server。

`graph.load_from_local_config` 默认 `false`，控制构造阶段的预加载，不能用它禁止启动时加载本地图。
详见[服务端配置说明](/cn/docs/config/config-guide/)。

## 连接与查询 {#queries}

### curl 返回乱码怎么办 {#compressed-response}

批量顶点和边接口会返回 gzip 压缩结果。让 curl 按响应头自动解压即可。

```bash
curl --compressed \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices?limit=10'
```

开启认证时还需提供账号。若返回的内容仍不符合预期，检查 HTTP 状态、`Content-Type` 和 `Content-Encoding`。
不要将 JSON 错误响应直接交给 `gunzip`。

### 按顶点 ID 查询却找不到顶点 {#vertex-id}

先从已有查询结果中复制 `id`，保留它的类型。字符串 ID 需要 JSON 双引号，数值 ID 不需要。
例如字符串 ID `1:marko` 的 JSON 写法是 `"1:marko"`。

将这个 JSON ID 放进 URL 路径时，对它整体做 URL 编码。ID 含特殊字符时，不能只补双引号而忽略编码。

| 字符 | URL 编码 |
| --- | --- |
| `+` | `%2B` |
| 空格 | `%20` |
| `/` | `%2F` |
| `?` | `%3F` |
| `%` | `%25` |
| `#` | `%23` |
| `&` | `%26` |
| `=` | `%3D` |
| `"` | `%22` |

### 按类型查询顶点或边时超时 {#label-timeout}

先加较小的 `limit`，确认条件和返回结果。某个标签的数据量很大时，继续使用分页或更具体的过滤条件。
涉及属性过滤时，检查查询所需的索引，避免直接返回该类型的全部数据。

### REST 请求正常，Gremlin 返回 500 {#gremlin-connection}

先查看错误正文和 Server 日志。检查 `gremlin-server.yaml` 的 `host`、`port`，以及 `rest-server.properties` 的 `gremlinserver.url`。
这些配置必须指向同一个可达的 Gremlin 服务。修改配置后重启 Server。

REST 接口可达只说明 HTTP 入口正常，语句错误、权限和 Gremlin 服务连接仍需分别检查。

### REST 请求返回 HTTP 415 {#content-type}

发送 JSON 请求体时，设置请求头 `Content-Type: application/json`，并检查请求体确实是合法 JSON。

## 导入与数据维护 {#data-management}

### Loader 出现 Socket Timeout {#loader-timeout}

先检查 Server 的负载、日志和网络。导入并发过高时，降低批次大小或请求并发，再按实际耗时调整超时与重试参数。
错误容忍数决定是否继续处理错误记录，不能替代失败原因排查。参数说明见 [Loader 指南](/cn/docs/quickstart/toolchain/hugegraph-loader/)。

### 如何清空一张图 {#clear-graph}

管理员可调用以下接口。它会删除这张图的 Schema、顶点、边和索引，执行前先确认目标图和备份。

```text
DELETE /graphspaces/{graphspace}/graphs/{graph}/clear
```

请求需携带 `confirm_message` 查询参数，值必须严格等于 `I'm sure to delete all data`，并做 URL 编码。
完整调用方式见 [Graph API](/cn/docs/clients/restful-api/graphs/)。

### 清理底层存储后，为什么仍提示 Schema 已存在 {#schema-cache}

运行中的 Server 保留了图和 Schema 缓存。直接清理底层存储会造成缓存与数据不一致，需要重启 Server。
维护时优先使用受支持的图管理接口；确需操作底层存储时，先停止对应服务并备份数据。

## 建模与 ID {#modeling}

### 顶点或边 ID 超过长度限制 {#id-length}

当前二进制存储中，顶点 ID 最长 16384 字节，边 ID 最长 65536 字节。限制按编码后的字节数计算。
使用较短的业务标识作主键，避免把大段文本拼进 ID。

索引 ID 超过 32 字节时会使用哈希存储，该处理与顶点、边 ID 超长报错不同。

### 是否支持嵌套属性 {#nested-properties}

目前不支持嵌套属性。需要保留对象之间的关系时，可以将嵌套对象建成顶点，再用边连接。

### 一个边类型能连接多组顶点类型吗 {#edge-links}

可以。创建 `EdgeLabel` 时，对每一组顶点类型调用一次 `link(sourceLabel, targetLabel)`。
例如同一个“投资”边类型可以连接“个人 → 企业”和“企业 → 企业”。
旧的 `sourceLabel()`、`targetLabel()` 构建方式只表达一组配对，已废弃。

其他问题可搜索 [Server issues](https://github.com/apache/hugegraph/issues) 或
[Toolchain issues](https://github.com/apache/hugegraph-toolchain/issues)。
