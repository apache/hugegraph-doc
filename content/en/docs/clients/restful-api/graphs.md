---
title: "Graphs API"
linkTitle: "Graphs"
weight: 12
description: "Graphs REST API: Manage graph instance lifecycle including creating, querying, cloning, clearing, and deleting graph databases."
---

### 6.1 Graphs

> [!WARNING]
> In production, enable [Server authentication and authorization](/docs/config/config-authentication/), restrict graph management with an IP allowlist and minimum permissions, and retain `audit-*.log` audit records. Unauthenticated settings below are only for isolated local tests.

> This page documents the Graphs API on current master. For historical paths and request bodies, use the [1.7 Graphs API](https://hugegraph.apache.org/versions/1.7/docs/clients/restful-api/graphs/) or
> [1.5 Graphs API](https://hugegraph.apache.org/versions/1.5/docs/clients/restful-api/graphs/).

With authentication enabled, creation, cloning, deletion, clearing, display-name changes, graph-configuration reads, read-mode changes, and manual compaction require graph-space management permission (`space`); administrators can satisfy it through permission inheritance. Snapshot creation/restoration and data-mode changes allow graph-space managers or the graph owner. Listing, details, and data/read-mode queries use graph read permissions. Raft APIs additionally require graph-space membership.

#### 6.1.1 List all graphs in the graphspace

##### Params

**Path parameters**

- graphspace: Graphspace name

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

#### 6.1.2 Get details of the graph

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

#### 6.1.3 Clear all data of a graph, include: schema, vertex, edge and index

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

**Query parameters**

Since emptying the graph is a dangerous operation, we have added parameters for confirmation to the API to avoid false calls by users:

- confirm_message: default by `I'm sure to delete all data`

##### Method & Url

```text
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/clear?confirm_message=I%27m+sure+to+delete+all+data
```

##### Response Status

```javascript
204
```

#### 6.1.4 Clone graph

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Name of the new graph to create

**Query parameters**

- clone_graph_name: name of an existed graph. To clone from an existing graph, the user can choose to transfer the configuration file, which will replace the configuration in the existing graph

##### Method & Url

```text
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

#### 6.1.5 Create graph

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

##### Method & Url

```text
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph-xx
```

##### Request Body

Create a graph (set `Content-Type: application/json`)

**`gremlin.graph` Configuration:**
- Auth mode: `"gremlin.graph": "org.apache.hugegraph.auth.HugeFactoryAuthProxy"` (required in production)
- Non-auth mode: `"gremlin.graph": "org.apache.hugegraph.HugeFactory"`

**Note**: For HStore, configure PD correctly in HugeGraph Server; see [HStore configuration](/docs/quickstart/hugegraph/hugegraph-server/#511-distributed-storage-hstore). The backend selects the scheduler: HStore uses the distributed scheduler; other backends use the local scheduler.

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

#### 6.1.6 Delete graph and its data

Graph-space management permission (`space`) is required when authentication is enabled.

Stop writes and tasks on every Server that uses the graph before deletion, and keep them stopped during failures and retries.
Do not recreate the same graph name until deletion has completed and been confirmed on every Server. Notifications are not a cluster-wide barrier.

On the deleting Server, scheduler shutdown fences new task admission and waits for actual executions, cancellation callbacks and transaction cleanup.
If the configured task-drain wait times out (`task.wait_timeout`, seconds), deletion is refused before data, configuration or metadata removal; retry after
the owners exit. Task admission stays closed after this refusal.
To resume ordinary graph use before destructive cleanup, keep writes and task producers stopped;
wait for all admitted tasks and cancellation cleanup to finish, then restart Server. A restart does not restore data or metadata already removed.
Closing the scheduler alone retains persistent work that has not started.

Deletion is not transactional. A failure after destructive cleanup does not restore removed data or metadata. An uncertain owner or native-resource cleanup
needs manual inspection; do not force-remove the scheduler or resume writes just because a task Future is done.
In PD deployments with `graph.load_from_local_config=true`, if deletion is refused because the graph uses local configuration,
removing its configuration file and restarting Server stops Server from loading the graph, but leaves its backend data in place.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

**Query parameters**

Since deleting a graph is a dangerous operation, we have added parameters for confirmation to the API to avoid false calls by users:

- confirm_message: default by `I'm sure to drop the graph`

##### Method & Url

```javascript
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/graphA?confirm_message=I%27m%20sure%20to%20drop%20the%20graph
```

##### Response Status

```javascript
204
```


#### 6.1.7 List the graphs of the graphspace with their configuration

Returns one entry per graph the current user can read, each carrying the graph configuration (keys that look like passwords, secrets, tokens, credentials or private keys are left out) plus the fields below. Graphs marked as default for the current user come first.

##### Params

**Path parameters**

- graphspace: Graphspace name

**Query parameters**

- prefix: Return only the graphs whose name or nickname starts with this prefix

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/profile
```

##### Response Status

```javascript
200
```

##### Response Body

`default_update_time` is only present when the graph is a default graph of the current user, and `create_time` only when the graph records one.

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

#### 6.1.8 Update the nickname of a graph

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

**Request parameters**

- action: Must be `update`
- update: Container for the fields to update. `name` is required and must match the graph name in the path, `nickname` is the new display name and must be unique inside the graphspace.

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

#### 6.1.9 Manage the default graphs of the current user

A default graph is recorded per user, so the endpoints below act on behalf of the calling user. They need the authentication system, a server started in standalone mode without it answers `400` with `GraphSpace management is not supported in standalone mode`.

##### Set a graph as default

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

##### Unset a default graph

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

##### Get the default graphs

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

#### 6.1.10 Reload the graphs of the graphspace

Apply graph configuration changes by restarting Server. Hot-reload recovery is deferred; do not use this endpoint for configuration maintenance.
In the current non-PD path, reload invokes graph deletion and can clear backend data. Keep writes and tasks stopped until Server has restarted and the
intended graphs have been verified. The request and response below document the API shape, not a maintenance or recovery guarantee.

##### Params

**Path parameters**

- graphspace: Graphspace name

**Request parameters**

- action: Must be `reload`

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

#### 6.2.1 Get configuration for a graph

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

Graph read permission (`space_member` or the graph owner) is required when authentication is enabled.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

> Allowed graph mode values are: NONE, RESTORING, MERGING, LOADING

#### 6.3.2 Modify graph mode.

Graph-space management permission (`space`) or graph ownership is required when authentication is enabled; administrators can satisfy it through permission inheritance.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

##### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/mode
```

##### Request Body

```text
"RESTORING"
```

> Allowed graph mode values are: NONE, RESTORING, MERGING, LOADING

While loading owners are active, this enum PUT rejects all mode changes, including `"LOADING"`. Release the owners after their import workers stop.

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

Graph read permission (`space_member` or the graph owner) is required when authentication is enabled.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

#### 6.3.4 Modify graph's read mode.

Graph-space management permission (`space`) is required when authentication is enabled; administrators can satisfy it through permission inheritance.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

##### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph_read_mode
```

##### Request Body

```text
"OLTP_ONLY"
```

> Allowed read mode values are: ALL, OLTP_ONLY. The API rejects OLAP_ONLY with `Graph-read-mode could be ALL or OLTP_ONLY`.

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

#### 6.3.5 LOADING ownership {#loading-ownership}

Starting with HugeGraph 1.8.0, the Server provides the protocol 1 endpoints for LOADING ownership
(requires a Server whose `GET .../mode/owners` returns `protocol: 1` and a matching Loader; current `master` does not include it yet);
Loader integration requires a matching 1.8.0 or newer client.
Released packages, earlier 1.8 builds, and current `master` builds lack this protocol. Support for the `LOADING` enum alone does not imply support for it.
With authentication enabled, both endpoints use the mode setter's permissions: graph-space management (`space`) or graph ownership, with STATUS write
authorization. Server binds the handle to the authenticated principal; a token grants no permission. Keep the same identity for acquire, release and retries.

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/mode/owners
```

The `200` capability response contains the graph-instance UUID, current nonnegative epoch, and state revision:

```json
{
    "protocol": 1,
    "instance": "<instance UUID>",
    "epoch": 0,
    "revision": 0
}
```

Generate a new lowercase hyphenated UUID `token` for each import, retain the returned `instance` and `epoch`,
and acquire with `Content-Type: application/json`:

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

An acquire succeeded only when the response returns `200` with `state: "active"`, echoing `protocol`, `instance`, `epoch`, `token`, and `mode: "LOADING"`.
A `200` response with `state: "released"` means the handle is finished or was preemptively released; it does not grant ownership. In that case, stop and drain
that import attempt, then start a new attempt with a fresh GET for `instance` and `epoch` and generate a new token.
Release with `action: "release"` and the same handle; its response has `state: "released"` and the effective graph mode. Calling release before acquire is
recorded and causes a subsequent acquire with that handle to return `released`.
Keep one handle for retries; Server checks its principal, instance and epoch. A released handle cannot acquire again.

To clear orphaned handles after an abnormal exit (e.g. `kill -9`), an administrator can execute an explicit recovery request:

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

Administrator recovery requires the global administrator role (`admin`). Callers must supply the current `revision`, `instance`, and `epoch`
obtained from `GET /mode/owners`, plus the confirmation string `confirm: "I'm sure all imports have stopped"`.
If the provided `revision` does not match the Server's current state, the request is rejected with HTTP `409 Conflict`.
On success, the Server clears all active owners, resets graph mode to `NONE`, and increments the epoch, returning HTTP `200` with
`state: "recovered"` and `mode: "NONE"`.

The first owner requires `NONE`. Other owners share owner-managed `LOADING`; the last release restores `NONE`.
Manually set `LOADING`, `RESTORING` and `MERGING` are not adopted. While owners are active, the legacy enum PUT rejects mode changes.

This protects ordinary imports on one live Server graph instance, with the handle bound to its authenticated principal, instance and epoch.
It provides no cross-Server coordination, data-write isolation or automatic expiry. Use a fixed direct Server endpoint and release after the import stops.
The upgraded Loader falls back to old behavior only for an unsupported-route `404` from its ownership probe; other errors remain failures.
Graph-source and restore imports retain their original enum-mode behavior. See
[Loader compatibility and recovery](/docs/quickstart/toolchain/hugegraph-loader/#loading-ownership).

### 6.4 Snapshot

#### 6.4.1 Create a snapshot

Graph-space management permission (`space`) or graph ownership is required when authentication is enabled; administrators can satisfy it through permission inheritance.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

#### 6.4.2 Resume a snapshot

Graph-space management permission (`space`) or graph ownership is required when authentication is enabled; administrators can satisfy it through permission inheritance.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

#### 6.5.1 Manually compact graph

Graph-space management permission (`space`) is required when authentication is enabled; administrators can satisfy it through permission inheritance.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

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

These endpoints only work when the graph runs in raft mode, see the `raft.mode` option in [Config Options](/docs/config/config-option/). On a graph that does not, they answer `400` with `Allowed <operation> operation only when working on raft mode`.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name

**Query parameters**

- group: Raft group name, default is `default`
- endpoint: Address of the peer, in the `host:port` form. Required by `transfer_leader`, `set_leader`, `add_peer` and `remove_peer`.

#### 6.6.1 List the peers of a raft group

Graph-space membership (`space_member`) is required when authentication is enabled; administrators can satisfy it through permission inheritance.

##### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/raft/list_peers
```

##### Response Status

```javascript
200
```

##### Response Body

The key of the returned object is the raft group name.

```javascript
{
  "default": [
    "127.0.0.1:8281",
    "127.0.0.1:8282",
    "127.0.0.1:8283"
  ]
}
```

#### 6.6.2 Get the leader of a raft group

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

#### 6.6.3 Transfer the leadership of a raft group

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

#### 6.6.4 Set the leader of a raft group

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

#### 6.6.5 Add a peer to a raft group

This schedules an asynchronous task, see [Task API](./task).

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

#### 6.6.6 Remove a peer from a raft group

This schedules an asynchronous task, see [Task API](./task).

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
