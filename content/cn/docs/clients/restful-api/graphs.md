---
title: "Graphs API"
linkTitle: "Graphs"
weight: 12
description: "Graphs（图管理）REST 接口:管理图实例的生命周期,包括创建、查询、克隆、清空和删除图数据库。"
---

### 6.1 Graphs

**重要提醒**：1.7.0 及之后，动态创建图必须开启鉴权模式。非鉴权模式请参考[图配置文件](https://hugegraph.apache.org/cn/docs/config/config-guide/#4-hugegraphproperties)，通过配置文件静态创建图。

#### 6.1.1 列出图空间中全部的图

##### Params

**路径参数说明：**

- graphspace: 图空间名称

##### Method & Url

```
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

```
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

#### 6.1.3 清空某个图的全部数据，包括 schema、vertex、edge 和 index 等，**该操作需要管理员权限**

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

**请求参数说明：**

由于清空图是一个比较危险的操作，为避免用户误调用，我们给 API 添加了用于确认的参数：

- confirm_message: 默认为`I'm sure to delete all data`

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/clear?confirm_message=I%27m+sure+to+delete+all+data
```

##### Response Status

```javascript
204
```

#### 6.1.4 克隆一个图 (**管理员权限**)

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 要创建的新图名称

**请求参数说明：**

- clone_graph_name: 已有图的名称；从已有的图来克隆，用户可选择传递配置文件，传递时将替换已有图中的配置；

##### Method & Url

```
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

#### 6.1.5 创建一个图，**该操作需要管理员权限**

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph-xx
```

##### Request Body

创建一个图（设置 `Content-Type: application/json`）

**`gremlin.graph` 配置说明：**
- 鉴权模式：`"gremlin.graph": "org.apache.hugegraph.auth.HugeFactoryAuthProxy"`（推荐）
- 非鉴权模式：`"gremlin.graph": "org.apache.hugegraph.HugeFactory"`

**注意**！！
1. 在 1.7.0 版本中，动态创建图会导致 NPE 错误。该问题已在 [PR#2912](https://github.com/apache/hugegraph/pull/2912) 中修复。当前 master 版本和 1.7.0 之前的版本不受此问题影响。
2. 如果 backend 是 hstore，请确保 HugeGraph-Server 已正确配置 PD，参见 [HStore 配置](/cn/docs/quickstart/hugegraph/hugegraph-server/#511-分布式存储-hstore)。1.7.0 及之前版本还需要在请求体中设置 `"task.scheduler_type": "distributed"`，该配置项现已废弃并被忽略：调度器由后端类型决定，hstore 使用分布式调度器，其他后端使用本地调度器。

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

> 注意：对于 HugeGraph 1.5.0 及之前版本，如需创建或删除图，请继续使用旧的 `text/plain`（properties）格式请求体，而不是 JSON。

#### 6.1.7 列出图空间中全部的图及其配置

对当前用户有读权限的每个图返回一条记录，其中包含该图的配置（形如密码、密钥、token、凭证、私钥的配置项会被过滤掉）以及下面这些字段。当前用户的默认图会排在前面。

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求参数说明：**

- prefix: 只返回名称或显示名以该前缀开头的图

##### Method & Url

```
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

#### 6.1.8 修改某个图的显示名，**该操作需要管理员权限**

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

**请求参数说明：**

- action: 固定为 `update`
- update: 需要修改的字段。`name` 必填且必须与路径中的图名一致，`nickname` 是新的显示名，在图空间内必须唯一。

##### Method & Url

```
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

```
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

```
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

```
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

重新加载服务中的图，适用于图配置在服务外部被改动之后。

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求参数说明：**

- action: 固定为 `reload`

##### Method & Url

```
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

#### 6.2.1 查看某个图的配置，**该操作需要管理员权限**

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

正常情况下，图模式为 None，当需要 Restore 图时，需要根据需要临时修改图模式为 Restoring 模式或者 Merging
模式，并在完成 Restore 时，恢复图模式为 None。

#### 6.3.1 查看某个图的模式。

##### Method & Url

```
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

#### 6.3.2 设置某个图的模式。**该操作需要管理员权限**

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/mode
```

##### Request Body

```
"RESTORING"
```

> 合法的图模式包括：NONE，RESTORING，MERGING，LOADING

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

#### 6.3.3 查看某个图的读模式。

##### Params

- name: 图的名称

##### Method & Url

```
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

#### 6.3.4 设置某个图的读模式。**该操作需要管理员权限**

##### Params

- name: 图的名称

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph_read_mode
```

##### Request Body

```
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

### 6.4 Snapshot

#### 6.4.1 创建快照

##### Params

- name: 图的名称

##### Method & Url

```
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

##### Params

- name: 图的名称

##### Method & Url

```
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

#### 6.5.1 手动压缩图，**该操作需要管理员权限**

##### Params

- name: 图的名称

##### Method & Url

```
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

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

**请求参数说明：**

- group: raft 组名称，默认为 `default`
- endpoint: 节点地址，形如 `host:port`。`transfer_leader`、`set_leader`、`add_peer` 和 `remove_peer` 必填。

#### 6.6.1 查看 raft 组的成员列表

##### Method & Url

```
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

```
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

```
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

```
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

```
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

```
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
