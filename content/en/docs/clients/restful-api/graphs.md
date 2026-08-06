---
title: "Graphs API"
linkTitle: "Graphs"
weight: 12
description: "Graphs REST API: Manage graph instance lifecycle including creating, querying, cloning, clearing, and deleting graph databases."
---

### 6.1 Graphs

**Important Reminder**: Since HugeGraph 1.7.0, dynamic graph creation must enable authentication mode. For non-authentication mode, please refer to [Graph Configuration File](https://hugegraph.apache.org/docs/config/config-guide/#4-hugegraphproperties) to statically create graphs through configuration files.

#### 6.1.1 List all graphs in the graphspace

##### Params

**Path parameters**

- graphspace: Graphspace name

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

#### 6.1.2 Get details of the graph

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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
  "backend": "cassandra"
}
```

#### 6.1.3 Clear all data of a graph, include: schema, vertex, edge and index, **This operation requires administrator privileges**

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

**Query parameters**

Since emptying the graph is a dangerous operation, we have added parameters for confirmation to the API to avoid false calls by users:

- confirm_message: default by `I'm sure to delete all data`

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/clear?confirm_message=I%27m+sure+to+delete+all+data
```

##### Response Status

```javascript
204
```

#### 6.1.4 Clone graph, **this operation requires administrator privileges**

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Name of the new graph to create

**Query parameters**

- clone_graph_name: name of an existed graph. To clone from an existing graph, the user can choose to transfer the configuration file, which will replace the configuration in the existing graph

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/cloneGraph?clone_graph_name=hugegraph
```

##### Request Body [Optional]

Clone a `non-auth` mode graph (set `Content-Type: application/json`)

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
> 1. The data/wal_path can't be the same as the existing graph (use separate directories)
> 2. Replace "gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy" to enable auth mode

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
    "name": "cloneGraph",
    "backend": "rocksdb"
}
```

#### 6.1.5 Create graph, **this operation requires administrator privileges**

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph2
```

##### Request Body

Create a graph (set `Content-Type: application/json`)

**`gremlin.graph` Configuration:**
- Auth mode: `"gremlin.graph": "org.apache.hugegraph.auth.HugeFactoryAuthProxy"` (Recommended)
- Non-auth mode: `"gremlin.graph": "org.apache.hugegraph.HugeFactory"`

**Note**!!
1. In version 1.7.0, dynamic graph creation would cause a NPE. This issue has been fixed in [PR#2912](https://github.com/apache/hugegraph/pull/2912). The current master version and versions after 1.7.0 do not have this problem.
2. For version 1.7.0 and earlier, if the backend is hstore, you must add "task.scheduler_type": "distributed" in the request body. Also ensure HugeGraph-Server is properly configured with PD, see [HStore Configuration](/docs/quickstart/hugegraph/hugegraph-server/#511-distributed-storage-hstore).

**RocksDB Example:**

```javascript
{
  "gremlin.graph": "org.apache.hugegraph.auth.HugeFactoryAuthProxy",
  "backend": "rocksdb",
  "serializer": "binary",
  "store": "hugegraph2",
  "rocksdb.data_path": "./rks-data-xx",
  "rocksdb.wal_path": "./rks-data-xx"
}
```

**HStore Example (for version 1.7.0 and earlier):**

```javascript
{
  "gremlin.graph": "org.apache.hugegraph.auth.HugeFactoryAuthProxy",
  "backend": "hstore",
  "serializer": "binary",
  "store": "hugegraph2",
  "task.scheduler_type": "distributed",
  "pd.peers": "127.0.0.1:8686"
}
```

> Note: The data/wal_path can't be the same as the existing graph (use separate directories)

##### Response Status

```javascript
200
```

##### Response Body

```javascript
{
  "name": "hugegraph2",
  "backend": "rocksdb"
}
```

#### 6.1.6 Delete graph and its data

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

**Query parameters**

Since deleting a graph is a dangerous operation, we have added parameters for confirmation to the API to avoid false calls by users:

- confirm_message: default by `I'm sure to drop the graph`

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/graphA?confirm_message=I%27m%20sure%20to%20drop%20the%20graph
```

##### Response Status

```javascript
204
```

> Note: For HugeGraph 1.5.0 and earlier versions, if you need to create or drop a graph, please still use the legacy `text/plain` (properties) style request body instead of JSON.

### 6.2 Conf

#### 6.2.1 Get configuration for a graph, **This operation requires administrator privileges**

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

##### Method & Url

```javascript
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/conf
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

backend=cassandra
serializer=cassandra

store=hugegraph
...=
```

### 6.3 Mode

Allowed graph mode values are: NONE, RESTORING, MERGING, LOADING

- None mode is regular mode
    - Not allowed to create schema with specified id
    - Not support creating vertex with id for AUTOMATIC id strategy
- LOADING mode used to load data via hugegraph-loader.
    - When adding vertices / edges, it is not checked whether the required attributes are passed in

Restore has two different modes: Restoring and Merging

- Restoring mode is used to restore schema and graph data to a new graph.
    - Support create schema with specified id
    - Support create vertex with id for AUTOMATIC id strategy
- Merging mode is used to merge schema and graph data to an existing graph.
    - Not allowed to create schema with specified id
    - Support create vertex with id for AUTOMATIC id strategy

Under normal circumstances, the graph mode is None. When you need to restore the graph,
you need to temporarily modify the graph mode to Restoring or Merging as needed.
When you complete the restore, change the graph mode to None.

#### 6.3.1 Get graph mode

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

> Allowed graph mode values are: NONE, RESTORING, MERGING

#### 6.3.2 Modify graph mode. **This operation requires administrator privileges**

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/mode
```

##### Request Body

```
"RESTORING"
```

> Allowed graph mode values are: NONE, RESTORING, MERGING

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

#### 6.3.3 Get graph's read mode

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

#### 6.3.4 Modify graph's read mode. **This operation requires administrator privileges**

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph_read_mode
```

##### Request Body

```
"OLTP_ONLY"
```

> Allowed read mode values are: ALL, OLTP_ONLY, OLAP_ONLY

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

#### 6.4.1 Create a snapshot

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

#### 6.4.2 Resume a snapshot

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

#### 6.5.1 Manually compact graph, **This operation requires administrator privileges**

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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
