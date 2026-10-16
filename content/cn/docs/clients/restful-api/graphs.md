---
title: "Graphs API"
linkTitle: "Graphs"
weight: 12
description: "Graphs（图管理）REST 接口:管理图实例的生命周期,包括创建、查询、克隆、清空和删除图数据库。"
---

### 6.1 Graphs

> [!WARNING]
> 生产环境必须启用 [Server 认证与授权](/cn/docs/config/config-authentication/)，通过 IP 白名单及最小权限控制图管理接口的访问，并保留 `audit-*.log` 审计记录。下文非鉴权配置仅用于隔离的本地测试。

> 本页介绍当前 master 的 Graphs API。历史版本的路径和请求体请切换到对应多版本页面： [1.7 版 Graphs API](https://hugegraph.apache.org/versions/1.7/cn/docs/clients/restful-api/graphs/) 或
> [1.5 版 Graphs API](https://hugegraph.apache.org/versions/1.5/cn/docs/clients/restful-api/graphs/)。

启用鉴权时，创建、克隆、删除、清空、修改图显示名、读取图配置、设置读模式和手动压缩等操作要求图空间管理权限（`space`）；管理员可按权限继承规则满足。创建或恢复快照、设置数据模式允许图空间管理者或该图所有者操作；列表、详情、数据模式读取和读模式读取按图读取权限校验。Raft API 另要求图空间成员权限。

#### 6.1.1 列出图空间中全部的图

##### Params

**路径参数说明：**

- graphspace: 图空间名称

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "graphs": [
        "hugegraph",
        "hugegraph1"
    ]
}
```

#### 6.1.2 查看某个图的信息

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "name": "hugegraph",
    "backend": "rocksdb"
}
```

#### 6.1.3 清空某个图的全部数据，包括 schema、vertex、edge 和 index 等

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

**请求参数说明：**

由于清空图是一个比较危险的操作，为避免用户误调用，我们给 API 添加了用于确认的参数：

- confirm_message: 默认为`I'm sure to delete all data`

##### Method & Url

```text
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/clear?confirm_message=I%27m+sure+to+delete+all+data
```

##### Response Status

```javascript
204
```

#### 6.1.4 克隆一个图

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 要创建的新图名称

**请求参数说明：**

- clone_graph_name: 已有图的名称；从已有的图来克隆，用户可选择传递配置文件，传递时将替换已有图中的配置；

##### Method & Url

```text
POST http://localhost:8080/graphspaces/DEFAULT/graphs/cloneGraph?clone_graph_name=hugegraph
```

##### Request Body (可选)

克隆一个非鉴权模式的图（设置 `Content-Type: application/json`）

```javascript
{
  "gremlin.graph": "org.apache.hugegraph.HugeFactory",
  "backend": "rocksdb",
  "serializer": "binary",
  "store": "cloneGraph",
  "rocksdb.data_path": "./rks-data-xx",
  "rocksdb.wal_path": "./rks-data-xx"
}
```

> Note:
> 1. Rocksdb 存储路径不能与现有图相同（需使用不同的目录）
> 2. 如需开启新图的权限系统，需替换设置 `gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy`

##### Response Status

```javascript
201
```

##### Response Body

```javascript
{
    "name": "cloneGraph",
    "nickname": "cloneGraph",
    "backend": "rocksdb",
    "description": ""
}
```

#### 6.1.5 创建一个图

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

##### Method & Url

```text
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph-xx
```

##### Request Body

创建一个图（设置 `Content-Type: application/json`）

**`gremlin.graph` 配置说明：**
- 鉴权模式：`"gremlin.graph": "org.apache.hugegraph.auth.HugeFactoryAuthProxy"`（生产环境必须使用）
- 非鉴权模式：`"gremlin.graph": "org.apache.hugegraph.HugeFactory"`

**注意**：如果 backend 是 hstore，请确保 HugeGraph-Server 已正确配置 PD，参见 [HStore 配置](/cn/docs/quickstart/hugegraph/hugegraph-server/#511-分布式存储-hstore)。调度器由后端类型决定：hstore 使用分布式调度器，其他后端使用本地调度器。

**选填字段及其默认值：**
- `gremlin.graph` 默认为 `org.apache.hugegraph.HugeFactory`
- `backend` 在 PD 模式下默认为 `hstore`，否则默认为 `rocksdb`
- `serializer` 默认为 `binary`
- `store` 默认为图名称
- `nickname` 设置图的显示名，在图空间内必须唯一
- `schema` 指定初始化该图所用的 [schema 模板](./graphspace)，会被保存为 `schema.init_template`
- `description` 会原样返回在响应中

**RocksDB 示例：**

```javascript
{
  "gremlin.graph": "org.apache.hugegraph.auth.HugeFactoryAuthProxy",
  "backend": "rocksdb",
  "serializer": "binary",
  "store": "hugegraph",
  "rocksdb.data_path": "./rks-data-xx",
  "rocksdb.wal_path": "./rks-data-xx"
}
```

**HStore 示例：**

```javascript
{
  "gremlin.graph": "org.apache.hugegraph.auth.HugeFactoryAuthProxy",
  "backend": "hstore",
  "serializer": "binary",
  "store": "hugegraph2",
  "pd.peers": "127.0.0.1:8686"
}
```

> Note: Rocksdb 存储路径不能与现有图相同（需使用不同的目录）

##### Response Status

```javascript
201
```

##### Response Body

```javascript
{
    "name": "hugegraph2",
    "nickname": "hugegraph2",
    "backend": "rocksdb",
    "description": ""
}
```

#### 6.1.6 删除某个图及其全部数据

启用鉴权时需要图空间管理权限（`space`）。

删图前停止所有使用该图的 Server 的写入和任务，并在失败及重试期间持续保持停止状态。
所有 Server 上的删除完成且经确认前，不得重建同名图。通知送达不构成集群范围的屏障。

执行删除的 Server 会关闭新任务准入，并等待实际执行、取消回调和事务清理结束。
配置的任务等待超时（`task.wait_timeout`，单位秒）时，会在移除数据、配置或元数据前拒绝删除；待执行对象退出后再重试。
因任务未排空而拒绝删除后，任务准入仍保持关闭。若要在破坏性清理前恢复正常用图，保持写入和任务生产者停止，
等待全部已准入任务和取消清理结束后再重启 Server；重启不会恢复已经移除的数据或元数据。
仅关闭调度器时，尚未开始的持久化任务仍保留在存储中。

删图不是事务操作，破坏性清理后的失败不会恢复已移除的数据或元数据。执行对象或原生资源的清理结果不确定时需要人工检查，
不能强制移除调度器，也不能仅凭任务 Future 已完成就恢复写入。
在启用 PD 且 `graph.load_from_local_config=true` 的部署中，若因使用本地配置而拒绝删除，
移除对应配置文件并重启 Server 仅会阻止 Server 继续加载该图，其后端存储数据仍会保留。

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

**请求参数说明：**

由于删除图是一个比较危险的操作，为避免用户误调用，我们给 API 添加了用于确认的参数：

- confirm_message: 默认为`I'm sure to drop the graph`

##### Method & Url

```javascript
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/graphA?confirm_message=I%27m%20sure%20to%20drop%20the%20graph
```

##### Response Status

```javascript
204
```

#### 6.1.7 列出图空间中全部的图及其配置

对当前用户有读权限的每个图返回一条记录，其中包含该图的配置（形如密码、密钥、token、凭证、私钥的配置项会被过滤掉）以及下面这些字段。当前用户的默认图会排在前面。

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求参数说明：**

- prefix: 只返回名称或显示名以该前缀开头的图

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/profile
```

##### Response Status

```javascript
200
```

##### Response Body

`default_update_time` 只在该图是当前用户的默认图时返回，`create_time` 只在该图记录了创建时间时返回。

```javascript
[
  {
    "backend": "rocksdb",
    "serializer": "binary",
    "store": "hugegraph",
    "name": "hugegraph",
    "nickname": "hugegraph",
    "graphspace_nickname": "DEFAULT",
    "default": true,
    "default_update_time": "2024-05-01 12:30:00",
    "create_time": "2024-05-01 12:00:00"
  }
]
```

#### 6.1.8 修改某个图的显示名

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

**请求参数说明：**

- action: 固定为 `update`
- update: 需要修改的字段。`name` 必填且必须与路径中的图名一致，`nickname` 是新的显示名，在图空间内必须唯一。

##### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph
```

##### Request Body

```javascript
{
  "action": "update",
  "update": {
    "name": "hugegraph",
    "nickname": "MyGraph"
  }
}
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "hugegraph": "updated"
}
```

#### 6.1.9 管理当前用户的默认图

默认图是按用户记录的，因此下面的接口都以调用者的身份生效。它们依赖权限系统，未开启权限的单机模式下会返回 `400` 和 `GraphSpace management is not supported in standalone mode`。

##### 设置默认图

##### Method & Url

```text
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/default
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "default_graph": [
    "hugegraph"
  ]
}
```

##### 取消默认图

##### Method & Url

```text
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/default
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "default_graph": []
}
```

##### 查看默认图

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/default
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "default_graph": [
    "hugegraph"
  ]
}
```

#### 6.1.10 重新加载图空间中的图

图配置变化通过重启 Server 应用。热重载恢复尚未实现，不要使用此接口进行配置维护。
当前未启用 PD 的执行路径中，reload 会调用删图流程，可能清空后端数据。重启完成并确认加载了预期图之前，持续停止写入和任务。
下方请求及响应仅说明 API 格式，不代表维护或恢复保障。

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求参数说明：**

- action: 固定为 `reload`

##### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/manage
```

##### Request Body

```javascript
{
  "action": "reload"
}
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "graphs": "reloaded"
}
```

### 6.2 Conf

#### 6.2.1 查看某个图的配置

##### Method & Url

```javascript
GET
http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/conf
```

##### Response Status

```javascript
200
```

##### Response Body

```properties
# gremlin entrence to create graph
gremlin.graph=org.apache.hugegraph.HugeFactory
# cache config
#schema.cache_capacity=1048576
#graph.cache_capacity=10485760
#graph.cache_expire=600

# schema illegal name template
#schema.illegal_name_regex=\s+|~.*

#vertex.default_label=vertex

backend=rocksdb
serializer=binary

store=hugegraph
...=
```

### 6.3 Mode

合法的图模式包括：NONE，RESTORING，MERGING，LOADING

- None 模式（默认），元数据和图数据的写入属于正常状态。特别的：
    - 元数据（schema）创建时不允许指定 ID
    - 图数据（vertex）在 id strategy 为 Automatic 时，不允许指定 ID
- LOADING：批量导入数据时自动启用，特别的：
    - 添加顶点/边时，不会检查必填属性是否传入

Restore 时存在两种不同的模式：Restoring 和 Merging

- Restoring 模式，恢复到一个新图中，特别的：
    - 元数据（schema）创建时允许指定 ID
    - 图数据（vertex）在 id strategy 为 Automatic 时，允许指定 ID
- Merging 模式，合并到一个已存在元数据和图数据的图中，特别的：
    - 元数据（schema）创建时不允许指定 ID
    - 图数据（vertex）在 id strategy 为 Automatic 时，允许指定 ID

正常情况下，图模式为 None，当需要 Restore 图时，需要根据需要临时修改图模式为 Restoring 模式或者 Merging 模式，并在完成 Restore 时，恢复图模式为 None。

#### 6.3.1 查看某个图的模式

启用鉴权时需要图读取权限（`space_member` 或该图的所有者）。

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/mode
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "mode": "NONE"
}
```

> 合法的图模式包括：NONE，RESTORING，MERGING，LOADING

#### 6.3.2 设置某个图的模式

启用鉴权时需要图空间管理权限（`space`）或该图所有者权限；管理员可按权限继承规则满足。

##### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/mode
```

##### Request Body

```text
"RESTORING"
```

> 合法的图模式包括：NONE，RESTORING，MERGING，LOADING

存在活跃的 loading owner 时，此枚举 PUT 会拒绝所有模式修改，包括 `"LOADING"`。请先停止导入 worker，再释放其 owner。

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "mode": "RESTORING"
}
```

#### 6.3.3 查看某个图的读模式

启用鉴权时需要图读取权限（`space_member` 或该图的所有者）。

##### Params

- name: 图的名称

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph_read_mode
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "graph_read_mode": "ALL"
}
```

#### 6.3.4 设置某个图的读模式

启用鉴权时需要图空间管理权限（`space`）；管理员可按权限继承规则满足。

##### Params

- name: 图的名称

##### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph_read_mode
```

##### Request Body

```text
"OLTP_ONLY"
```

> 合法的读模式包括：ALL，OLTP_ONLY。传入 OLAP_ONLY 时接口会报错 `Graph-read-mode could be ALL or OLTP_ONLY`。

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "graph_read_mode": "OLTP_ONLY"
}
```

#### 6.3.5 LOADING owner 管理 {#loading-ownership}

自 HugeGraph 1.8.0 起提供 owner 协议 1 接口（需配合返回 `protocol: 1` 的新版 Server 与对应 Loader；当前 `master` 分支暂未包含该协议）；
Loader 需使用配套的 1.8.0 及以上版本客户端。旧版本发行包、早期 1.8 构建以及当前 `master` 分支均不包含该协议；仅支持 `LOADING` 枚举不能说明支持这些接口。
启用鉴权时，两个接口沿用模式设置接口的权限要求，即图空间管理权限（`space`）或该图所有者权限，并校验 STATUS 写权限。
Server 将句柄绑定到实际鉴权用户；token 本身不赋予权限。申请、释放和重试必须保持相同身份。

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/mode/owners
```

`200` 能力响应包含图实例 UUID、当前非负 epoch 及状态 revision：

```json
{
    "protocol": 1,
    "instance": "<instance UUID>",
    "epoch": 0,
    "revision": 0
}
```

每轮导入生成一个新的小写连字符 UUID（lowercase hyphenated UUID）作为 `token`，保留返回的 `instance` 和 `epoch`，通过以下请求申请，并设置 `Content-Type: application/json`：

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/mode/owners
```

```json
{
    "action": "acquire",
    "instance": "<instance UUID>",
    "epoch": 0,
    "token": "<import UUID>"
}
```

只有响应中包含 `state: "active"` 时才表示申请成功；此时返回 `200` 并回显 `protocol`、`instance`、`epoch`、`token` 以及 `mode: "LOADING"`。
若返回 `200` 但 `state: "released"`，说明该句柄已失效或已被提前取消，此时并未获得 owner 保护；必须先停止并排空该次导入尝试，然后再通过 GET 获取新的 `instance` 和 `epoch` 并使用新 token 重新发起尝试。
释放时将 `action` 设置为 `release`，句柄保持不变；响应中包含 `state: "released"` 和当前实际模式。未申请前直接调用释放会被记录，并导致后续使用该句柄的申请直接返回 `released`。
重试保留同一句柄；Server 校验其鉴权身份、instance 和 epoch。已释放句柄不能再次申请。

当异常中断（如 `kill -9`）导致句柄残留时，管理员可发起强制恢复请求：

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/mode/owners
```

```json
{
    "action": "recover",
    "instance": "<instance UUID>",
    "epoch": 0,
    "revision": 0,
    "confirm": "I'm sure all imports have stopped"
}
```

管理员恢复需要全局管理员权限（`admin`）。调用方必须传入从 `GET /mode/owners` 获取的当前 `revision`、`instance` 和 `epoch`，
以及确认文案 `confirm: "I'm sure all imports have stopped"`。
若传入的 `revision` 与服务端当前状态不一致，请求将被拒绝并返回 HTTP `409 Conflict`。
恢复成功后服务端清除所有残留 owner，将图模式重置为 `NONE` 并递增 epoch，返回 HTTP `200`（含 `state: "recovered"` 和 `mode: "NONE"`）。

首个 owner 要求 `NONE`；其他 owner 共享由 owner 管理的 `LOADING`，最后一个释放后恢复 `NONE`。
手动设置的 `LOADING`、`RESTORING` 和 `MERGING` 不会被接管；owner 活跃时，旧枚举 PUT 会拒绝模式修改。

该协议保护同一 Server 上实际运行的图实例中的普通导入，句柄绑定到实际鉴权身份、instance 和 epoch。
它不提供跨 Server 协调、数据写入隔离或自动过期。请使用固定的 Server 直连地址，在导入停止后释放。
升级后的 Loader 仅在 owner 探测返回接口路由不受支持的 `404` 时回退到旧行为；其他错误仍失败。
图数据源和恢复导入保留原有枚举模式行为，参见 [Loader 兼容与恢复说明](/cn/docs/quickstart/toolchain/hugegraph-loader/#loading-ownership)。

### 6.4 Snapshot

#### 6.4.1 创建快照

启用鉴权时需要图空间管理权限（`space`）或该图所有者权限；管理员可按权限继承规则满足。

##### Params

- name: 图的名称

##### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/snapshot_create
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "hugegraph": "snapshot_created"
}
```

#### 6.4.2 快照恢复

启用鉴权时需要图空间管理权限（`space`）或该图所有者权限；管理员可按权限继承规则满足。

##### Params

- name: 图的名称

##### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/snapshot_resume
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "hugegraph": "snapshot_resumed"
}
```

### 6.5 Compact

#### 6.5.1 手动压缩图

启用鉴权时需要图空间管理权限（`space`）；管理员可按权限继承规则满足。

##### Params

- name: 图的名称

##### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/compact
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "nodes": 1,
    "cluster_id": "local",
    "servers": {
        "local": "OK"
    }
}
```

### 6.6 Raft

以下接口只在图运行于 raft 模式时可用，参见 [配置项](/cn/docs/config/config-option/) 中的 `raft.mode`。未开启 raft 模式的图会返回 `400` 和 `Allowed <operation> operation only when working on raft mode`。

启用鉴权时需要图空间成员权限（`space_member`）；管理员可按权限继承规则满足。

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

**请求参数说明：**

- group: raft 组名称，默认为 `default`
- endpoint: 节点地址，形如 `host:port`。`transfer_leader`、`set_leader`、`add_peer` 和 `remove_peer` 必填。

#### 6.6.1 查看 raft 组的成员列表

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/raft/list_peers
```

##### Response Status

```javascript
200
```

##### Response Body

返回对象的 key 是 raft 组名称。

```javascript
{
  "default": [
    "127.0.0.1:8281",
    "127.0.0.1:8282",
    "127.0.0.1:8283"
  ]
}
```

#### 6.6.2 查看 raft 组的 leader

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/raft/get_leader
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "default": "127.0.0.1:8281"
}
```

#### 6.6.3 转移 raft 组的 leader

##### Method & Url

```text
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/raft/transfer_leader?endpoint=127.0.0.1:8282
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "default": "127.0.0.1:8282"
}
```

#### 6.6.4 指定 raft 组的 leader

##### Method & Url

```text
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/raft/set_leader?endpoint=127.0.0.1:8282
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "default": "127.0.0.1:8282"
}
```

#### 6.6.5 向 raft 组添加成员

该操作会创建一个异步任务，参见 [Task API](./task)。

##### Method & Url

```text
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/raft/add_peer?endpoint=127.0.0.1:8284
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "task_id": 1
}
```

#### 6.6.6 从 raft 组移除成员

该操作会创建一个异步任务，参见 [Task API](./task)。

##### Method & Url

```text
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/raft/remove_peer?endpoint=127.0.0.1:8284
```

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "task_id": 2
}
```
