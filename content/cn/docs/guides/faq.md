---
title: "FAQ"
linkTitle: "FAQ"
weight: 6
---

## 部署与启动 {#deployment}

### 如何选择 RocksDB 或 HStore {#choose-backend}

开发测试或中小规模单机部署推荐选择 **Server + RocksDB**，部署轻便且性能优异。当数据规模较大（如 TB/PB 级）、需要水平扩容或多副本高可用时，推荐部署 **HStore 分布式集群**（PD + Store + Server）。

1.7.0 支持 RocksDB、HStore、HBase 和 Memory。Cassandra、ScyllaDB、MySQL、PostgreSQL 等旧后端需使用低于 1.7.0 的版本。
部署步骤见 [Server 快速开始](/cn/docs/quickstart/hugegraph/hugegraph-server/)。

### 启动时出现 core dumped 怎么查 {#core-dump}

先执行 `java -version` 确认 JDK 版本：**HugeGraph master 分支（以 1.8 为基线）要求 Java 17**，**1.7.0 要求 Java 11**（已不再支持 Java 8）。
若 JDK 版本正确，进一步查看 Server 日志及 JVM 崩溃日志（`hs_err_pid*.log`），排查是否由于系统架构不匹配、依赖的动态库（如 RocksDB JNI）缺失或系统内存不足引起。

### 哪些后端需要 init-store {#initialize-backend}

使用 RocksDB 或 HBase 等本地持久化后端时，**首次启动前必须执行 `bin/init-store.sh`** 进行初始化。Memory（内存后端）和 HStore（分布式后端）无需执行此脚本，HStore 的存储由 PD 和 Store 统一管理。

注意：`backend` 与 `serializer` 必须配套使用（例如 RocksDB 配套 `binary`），不可随意替换。若服务启动后提示无法连接后端，请优先检查是否完成初始化以及后端存储配置是否正确。

### init-store 报 GLIBCXX 版本缺失怎么办 {#native-library}

出现以下报错表示当前系统的 `libstdc++` 版本过低，缺少 RocksDB JNI 本地库所需的符号：

```text
java.lang.UnsatisfiedLinkError: .../librocksdbjni....so:
.../libstdc++.so.6: version `GLIBCXX_3.4.10' not found
```

解决方法：核对发行包支持的系统架构，升级系统的 `libstdc++`（或安装较新的 GCC 运行库），或者直接使用官方提供的 Docker 镜像运行。

### 应该使用哪个 Server 启动脚本 {#start-script}

当前发行包统一使用 `bin/start-hugegraph.sh`，GremlinServer 与 REST Server 会在同一个进程中启动。旧版本文档中的 `start-restserver.sh` 和 `start-gremlinserver.sh` 已废弃。

### 启动脚本会加载哪些图 {#load-graphs}

脚本名称与加载的图无关。Server 默认会扫描并加载 `conf/graphs` 目录下的所有图配置（可在 `conf/rest-server.properties` 中的 `graphs` 修改该目录）。每张本地图使用独立的配置文件，修改配置后需重启 Server。

注：`graph.load_from_local_config` 默认为 `false`（控制构造阶段预加载），不能用来禁止启动时加载本地图。详见[服务端配置说明](/cn/docs/config/config-guide/)。

## 连接与查询 {#queries}

### curl 返回乱码怎么办 {#compressed-response}

批量顶点和边接口默认会返回 gzip 压缩数据。使用 curl 请求时加上 `--compressed` 参数即可自动解压：

```bash
curl --compressed \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices?limit=10'
```

若开启了认证，需同时传入凭据。若返回内容仍不符合预期，请检查 HTTP 状态码、`Content-Type` 与 `Content-Encoding`，不要把 JSON 报错直接管道传给 `gunzip`。

### 按顶点 ID 查询却找不到顶点 {#vertex-id}

先从已有查询结果中确认 `id` 的实际格式和类型：**字符串 ID 需要 JSON 双引号，数值 ID 不需要**。例如字符串 ID `1:marko` 的 JSON 格式应为 `"1:marko"`。

在把 ID 放入 URL 路径时，必须对包含双引号在内的完整字符串进行 URL 编码。若 ID 含有特殊字符，不能仅补双引号而遗漏编码：

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

当某个标签下的数据量很大时，全量扫描很容易耗尽资源导致超时。建议优化方式：
1. 加上 `limit()` 限制返回记录数；
2. 使用分页机制分批读取；
3. 配合具体属性过滤，并确保对应属性已建立索引，避免全表扫描。

### REST 请求正常，Gremlin 返回 500 {#gremlin-connection}

REST 接口正常仅说明 HTTP 入口可用，Gremlin 执行返回 500 通常有以下原因：
1. **Gremlin Server 连接异常**：检查 `conf/rest-server.properties` 中的 `gremlinserver.url` 是否指向可达的 Gremlin 端口（默认 `8182`，对应 `conf/gremlin-server.yaml`）；
2. **语句语法或逻辑错误**：例如未加索引导致遍历被拦截；
3. **认证凭据缺失或过期**。

建议查看 `logs/hugegraph-server.log` 中的异常堆栈定位具体报错。

### REST 请求返回 HTTP 415 {#content-type}

发送带请求体的 POST/PUT 请求时，需在请求头中指定 `Content-Type: application/json`，并确保请求体是合法的 JSON 格式。

## 导入与数据维护 {#data-management}

### Loader 出现 Socket Timeout {#loader-timeout}

导入超时通常由于单批次写入过大或并发压力过高导致。建议：
1. 适当调小 `--batch-size`（如由 500 降为 200）；
2. 适当降低并发线程数；
3. 调大 `--timeout` 并配置重试机制。参数说明见 [Loader 指南](/cn/docs/quickstart/toolchain/hugegraph-loader/)。

### 如何清空一张图 {#clear-graph}

管理员可调用以下接口清空指定图的 Schema、顶点、边和索引（执行前请务必确认目标图并做好备份）：

```text
DELETE /graphspaces/{graphspace}/graphs/{graph}/clear
```

请求需携带 `confirm_message` 查询参数，值必须严格等于 `I'm sure to delete all data`（需进行 URL 编码）。完整调用方式见 [Graph API](/cn/docs/clients/restful-api/graphs/)。

### 清理底层存储后，为什么仍提示 Schema 已存在 {#schema-cache}

Server 在内存中维护了 Schema 缓存。如果直接绕过 Server 清理底层存储（如清空 RocksDB 目录或 HBase 表），Server 缓存与实际存储将出现不一致。
若已手动清理底层，必须**重启 Server**。日常清理建议使用官方提供的 [Clear 图 API](/cn/docs/clients/restful-api/graphs/#clear-graph)。

## 建模与 ID {#modeling}

### 顶点或边 ID 超过长度限制 {#id-length}

为保证底层存储与索引性能，HugeGraph 对 ID 长度作了如下限制（按编码后的字节数计算）：
- **顶点 ID**：最长 16384 字节（16 KB）；
- **边 ID**：最长 65536 字节（64 KB）。

建议使用简洁的业务唯一标识作为主键，避免在 ID 中拼接大段文本。注：属性索引值超过 32 字节时会自动转为哈希存储，不会报错超长。

### 是否支持嵌套属性 {#nested-properties}

目前不支持嵌套属性（复杂对象或嵌套 Map）。如果需要表达多层级关系，建议将嵌套对象拆分成独立的顶点，通过边与主体顶点相连。

### 一个边类型能连接多组顶点类型吗 {#edge-links}

支持。创建 `EdgeLabel` 时，对每一组起点和终点类型分别调用一次 `link(sourceLabel, targetLabel)` 即可。
例如“投资”关系可以同时连接“个人 → 企业”和“企业 → 企业”。旧版 `sourceLabel()` 与 `targetLabel()` 只支持单一配对，现已废弃。

其他问题可搜索 [Server issues](https://github.com/apache/hugegraph/issues) 或 [Toolchain issues](https://github.com/apache/hugegraph-toolchain/issues)。
