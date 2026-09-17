---
title: "Graphspace API"
linkTitle: "Graphspace"
weight: 1
description: "Graphspace REST API: Multi-tenancy and resource isolation for creating, viewing, updating, and deleting graph spaces with prerequisites and constraints."
---

### 2.0 Graphspace

HugeGraph implements multi-tenancy through graph spaces, which isolate compute/storage resources per tenant.

**Prerequisites**

1. Graphspace currently only works in HStore mode.
2. In non-HStore mode you can only use the default graphspace `DEFAULT`; creating/deleting/updating other graphspaces is not supported.
3. Set `usePD=true` in `rest-server.properties` and `backend=hstore` in `hugegraph.properties`.
4. Graphspace enables strict authentication by default (default credential: `admin:pa`, see the `auth.admin_pa` option). Change the password immediately to avoid unauthorized access.
5. Every endpoint on this page requires PD mode. In standalone mode they answer `400` with the message `GraphSpace management is not supported in standalone mode`.

#### 2.0.1 Create a graphspace

##### Method & Url

```
POST http://localhost:8080/graphspaces
```

##### Request Body

Note: CPU/memory and Kubernetes-related capabilities are not publicly available yet.

| Name                         | Required | Type    | Default | Range/Note                                                                     | Description                                                                       |
|------------------------------|----------|---------|---------|--------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| name                         | Yes      | String  |         | Lowercase letters, digits, underscore; must start with a letter; max length 48 | Graphspace name                                                                   |
| nickname                     | No       | String  | name    | Must be unique among graphspaces                                               | Display name of the graphspace                                                    |
| description                  | No       | String  |         |                                                                                | Description                                                                       |
| cpu_limit                    | Yes      | Int     |         | > 0                                                                            | CPU cores for the graphspace                                                      |
| memory_limit                 | Yes      | Int     |         | > 0 (GB)                                                                       | Memory quota in GB                                                                |
| storage_limit                | Yes      | Int     |         | > 0                                                                            | Maximum disk usage                                                                |
| compute_cpu_limit            | No       | Int     | 0       | >= 0                                                                           | Extra HugeGraph-Computer CPU cores; falls back to `cpu_limit` if unset or 0       |
| compute_memory_limit         | No       | Int     | 0       | >= 0                                                                           | Extra HugeGraph-Computer memory in GB; falls back to `memory_limit` if unset or 0 |
| oltp_namespace               | No       | String  | ""      |                                                                                | Kubernetes namespace for OLTP HugeGraph-Server                                    |
| olap_namespace               | No       | String  | ""      | Resources are merged when identical to `oltp_namespace`                        | Kubernetes namespace for OLAP / HugeGraph-Computer                                |
| storage_namespace            | No       | String  | ""      |                                                                                | Kubernetes namespace for HugeGraph-Store                                          |
| operator_image_path          | No       | String  | ""      |                                                                                | HugeGraph-Computer operator image registry                                        |
| internal_algorithm_image_url | No       | String  | ""      |                                                                                | HugeGraph-Computer algorithm image registry                                       |
| max_graph_number             | Yes      | Int     |         | > 0                                                                            | Maximum number of graphs that can be created inside the graphspace                |
| max_role_number              | No       | Int     | 0       |                                                                                | Maximum number of roles that can be created inside the graphspace                 |
| auth                         | No       | Boolean | false   | true / false                                                                   | Whether to enable authentication for the graphspace                               |
| configs                      | No       | Map     |         |                                                                                | Additional configuration                                                          |

```json
{
  "name": "gs1",
  "description": "1st graph space",
  "max_graph_number": 100,
  "cpu_limit": 1000,
  "memory_limit": 8192,
  "storage_limit": 1000000,
  "max_role_number": 10,
  "auth": true,
  "configs": {}
}
```

##### Response Status

```json
201
```

##### Response Body

```json
{
  "name": "gs1",
  "nickname": "gs1",
  "description": "1st graph space",
  "cpu_limit": 1000,
  "memory_limit": 8192,
  "storage_limit": 1000000,
  "compute_cpu_limit": 0,
  "compute_memory_limit": 0,
  "oltp_namespace": "hugegraph-server",
  "olap_namespace": "hugegraph-server",
  "storage_namespace": "hugegraph-server",
  "operator_image_path": "127.0.0.1/hugegraph-registry/hugegraph-computer-operator:3.1.1",
  "internal_algorithm_image_url": "127.0.0.1/hugegraph-registry/hugegraph-computer-algorithm:3.1.1",
  "max_graph_number": 100,
  "max_role_number": 10,
  "cpu_used": 0,
  "memory_used": 0,
  "storage_used": 0,
  "storage_percent": 0.0,
  "graph_number_used": 0,
  "role_number_used": 0,
  "auth": true,
  "creator": "admin",
  "create_time": "2024-05-01 12:00:00",
  "update_time": "2024-05-01 12:00:00"
}
```

#### 2.0.2 List all graphspaces

##### Method & Url

```
GET http://localhost:8080/graphspaces
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "graphSpaces": [
    "gs1",
    "DEFAULT"
  ]
}
```

#### 2.0.3 Get graphspace details

##### Params

**Path parameters**

- graphspace: Graphspace name

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "name": "gs1",
  "nickname": "gs1",
  "description": "1st graph space",
  "cpu_limit": 1000,
  "memory_limit": 8192,
  "storage_limit": 1000000,
  "oltp_namespace": "hugegraph-server",
  "olap_namespace": "hugegraph-server",
  "storage_namespace": "hugegraph-server",
  "operator_image_path": "127.0.0.1/hugegraph-registry/hugegraph-computer-operator:3.1.1",
  "internal_algorithm_image_url": "127.0.0.1/hugegraph-registry/hugegraph-computer-algorithm:3.1.1",
  "compute_cpu_limit": 0,
  "compute_memory_limit": 0,
  "max_graph_number": 100,
  "max_role_number": 10,
  "cpu_used": 0,
  "memory_used": 0,
  "storage_used": 0,
  "storage_percent": 0.0,
  "graph_number_used": 0,
  "role_number_used": 0,
  "auth": true,
  "creator": "admin",
  "create_time": "2024-05-01 12:00:00",
  "update_time": "2024-05-01 12:00:00",
  "dp_username": "gs1_dp",
  "dp_password": "a1b2c3d4e5f60718"
}
```

> `dp_username` and `dp_password` are derived from the graphspace name and are only returned by this endpoint.

#### 2.0.4 Update a graphspace

> `auth` cannot be changed once a graphspace is created.

##### Params

**Path parameter**

- graphspace: Graphspace name

**Request parameters**

- action: Must be `"update"`
- update: Container for the actual fields to update (see table below)

| Name                         | Required | Type   | Range/Note                                              | Description                                                                       |
|------------------------------|----------|--------|---------------------------------------------------------|-----------------------------------------------------------------------------------|
| name                         | Yes      | String | Must match the graphspace name in the path              | Graphspace name                                                                   |
| nickname                     | No       | String | Must be unique among graphspaces                        | Display name of the graphspace                                                    |
| description                  | No       | String |                                                         | Description                                                                       |
| cpu_limit                    | Yes      | Int    | > 0                                                     | CPU cores for OLTP HugeGraph-Server                                               |
| memory_limit                 | Yes      | Int    | > 0 (GB)                                                | Memory quota (GB) for OLTP HugeGraph-Server                                       |
| storage_limit                | Yes      | Int    | > 0                                                     | Maximum disk usage                                                                |
| compute_cpu_limit            | No       | Int    | >= 0                                                    | Extra HugeGraph-Computer CPU cores; falls back to `cpu_limit` if unset or 0       |
| compute_memory_limit         | No       | Int    | >= 0                                                    | Extra HugeGraph-Computer memory in GB; falls back to `memory_limit` if unset or 0 |
| oltp_namespace               | Yes      | String |                                                         | Kubernetes namespace for OLTP HugeGraph-Server                                    |
| olap_namespace               | Yes      | String | Resources are merged when identical to `oltp_namespace` | Kubernetes namespace for OLAP                                                     |
| storage_namespace            | Yes      | String |                                                         | Kubernetes namespace for HugeGraph-Store                                          |
| operator_image_path          | No       | String |                                                         | HugeGraph-Computer operator image registry                                        |
| internal_algorithm_image_url | No       | String |                                                         | HugeGraph-Computer algorithm image registry                                       |
| max_graph_number             | Yes      | Int    | > 0                                                     | Maximum number of graphs                                                          |
| max_role_number              | Yes      | Int    | > 0                                                     | Maximum number of roles                                                           |

##### Method & Url

```
PUT http://localhost:8080/graphspaces/gs1
```

##### Request Body

```json
{
  "action": "update",
  "update": {
    "name": "gs1",
    "description": "1st graph space",
    "cpu_limit": 2000,
    "memory_limit": 40960,
    "storage_limit": 2048,
    "oltp_namespace": "hugegraph-server",
    "olap_namespace": "hugegraph-server",
    "operator_image_path": "127.0.0.1/hugegraph-registry/hugegraph-computer-operator:3.1.1",
    "internal_algorithm_image_url": "127.0.0.1/hugegraph-registry/hugegraph-computer-algorithm:3.1.1",
    "max_graph_number": 1000,
    "max_role_number": 100
  }
}
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "name": "gs1",
  "nickname": "gs1",
  "description": "1st graph space",
  "cpu_limit": 2000,
  "memory_limit": 40960,
  "storage_limit": 2048,
  "oltp_namespace": "hugegraph-server",
  "olap_namespace": "hugegraph-server",
  "storage_namespace": "hugegraph-server",
  "operator_image_path": "127.0.0.1/hugegraph-registry/hugegraph-computer-operator:3.1.1",
  "internal_algorithm_image_url": "127.0.0.1/hugegraph-registry/hugegraph-computer-algorithm:3.1.1",
  "compute_cpu_limit": 0,
  "compute_memory_limit": 0,
  "max_graph_number": 1000,
  "max_role_number": 100,
  "cpu_used": 0,
  "memory_used": 0,
  "storage_used": 0,
  "storage_percent": 0.0,
  "graph_number_used": 0,
  "role_number_used": 0,
  "auth": true,
  "creator": "admin",
  "create_time": "2024-05-01 12:00:00",
  "update_time": "2024-05-01 12:30:00"
}
```

#### 2.0.5 Delete a graphspace

##### Params

**Path parameter**

- graphspace: Graphspace name

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/gs1
```

##### Response Status

```json
204
```

> Warning: deleting a graphspace releases all resources that belong to it.

#### 2.0.6 List all graphspaces with their details

##### Params

**Query parameters**

- prefix: Return only the graphspaces whose name or nickname starts with this prefix

##### Method & Url

```
GET http://localhost:8080/graphspaces/profile
```

##### Response Status

```json
200
```

##### Response Body

Each entry carries the same fields as `GET /graphspaces/{graphspace}` plus `authed`, `default`, `create_time` and `update_time`. `authed` says whether the current user may enter the graphspace: it is `false` when the graphspace has authentication on and the user is neither an administrator, nor a manager, nor a member of it. `default` is always `false` for now, the default-graphspace feature is not implemented yet.

```json
[
  {
    "name": "gs1",
    "nickname": "gs1",
    "description": "1st graph space",
    "cpu_limit": 1000,
    "memory_limit": 8192,
    "storage_limit": 1000000,
    "compute_cpu_limit": 0,
    "compute_memory_limit": 0,
    "oltp_namespace": "hugegraph-server",
    "olap_namespace": "hugegraph-server",
    "storage_namespace": "hugegraph-server",
    "max_graph_number": 100,
    "max_role_number": 10,
    "cpu_used": 0,
    "memory_used": 0,
    "storage_used": 0,
    "storage_percent": 0.0,
    "graph_number_used": 0,
    "role_number_used": 0,
    "auth": true,
    "creator": "admin",
    "authed": true,
    "default": false,
    "create_time": "2024-05-01 12:00:00",
    "update_time": "2024-05-01 12:30:00"
  }
]
```

**Default roles**

Every graphspace carries four built-in roles, so that a user or a group can be given a whole set of permissions at once:

- `space`: manager of the graphspace, only an administrator may grant it
- `space_member`: member of the graphspace
- `analyst`: analyst of the graphspace
- `observer`: read-only role, it can be narrowed to a single graph by passing `graph`

`user` accepts either a user name or a group name. Whether the current user holds a default role can also be checked with `GET /graphspaces/{graphspace}/auth/managers/default`, see [Authentication API](./auth).

#### 2.0.7 Grant a default role

##### Params

**Path parameter**

- graphspace: Graphspace name

**Request parameters**

- user: User or group name, required
- role: One of `space`, `space_member`, `analyst`, `observer`, required
- graph: Graph name, optional, only taken into account with `role=observer`

##### Method & Url

```
POST http://localhost:8080/graphspaces/gs1/role
```

##### Request Body

```json
{
  "user": "boss",
  "role": "analyst"
}
```

##### Response Status

```json
201
```

##### Response Body

`graph` is echoed back only when the role was granted on a single graph.

```json
{
  "user": "boss",
  "role": "analyst",
  "graphSpace": "gs1"
}
```

#### 2.0.8 Check a default role

##### Params

**Path parameter**

- graphspace: Graphspace name

**Query parameters**

- user: User or group name, required
- role: Default role name, required
- graph: Graph name, optional, only taken into account with `role=observer`

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/role?user=boss&role=analyst
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "check": true
}
```

#### 2.0.9 Revoke a default role

##### Params

**Path parameter**

- graphspace: Graphspace name

**Query parameters**

- user: User or group name, required
- role: Default role name, required
- graph: Graph name, optional, only taken into account with `role=observer`

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/gs1/role?user=boss&role=analyst
```

##### Response Status

```json
204
```

**Schema templates**

A schema template stores a Gremlin schema script under a name, so that a new graph can be initialized with it by passing `schema` when the graph is created, see [Graphs API](./graphs). A template can be updated or deleted by its creator, by a manager of the graphspace, or by an administrator.

#### 2.0.10 Create a schema template

##### Params

**Path parameter**

- graphspace: Graphspace name

**Request parameters**

- name: Template name, required
- schema: Gremlin schema script, required

##### Method & Url

```
POST http://localhost:8080/graphspaces/gs1/schematemplates
```

##### Request Body

```json
{
  "name": "template1",
  "schema": "schema.propertyKey('name').asText().ifNotExist().create();"
}
```

##### Response Status

```json
201
```

##### Response Body

```json
{
  "name": "template1",
  "schema": "schema.propertyKey('name').asText().ifNotExist().create();",
  "creator": "admin",
  "create": "2024-05-01 12:00:00.000",
  "create_time": "2024-05-01 12:00:00.000",
  "update": "2024-05-01 12:00:00.000",
  "update_time": "2024-05-01 12:00:00.000"
}
```

#### 2.0.11 List the schema templates of a graphspace

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/schematemplates
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "schema_templates": [
    "template1"
  ]
}
```

#### 2.0.12 Get a schema template

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/schematemplates/template1
```

##### Response Status

```json
200
```

#### 2.0.13 Update a schema template

Only `schema` can be updated, the name of a template is fixed.

##### Method & Url

```
PUT http://localhost:8080/graphspaces/gs1/schematemplates/template1
```

##### Request Body

```json
{
  "schema": "schema.propertyKey('age').asInt().ifNotExist().create();"
}
```

##### Response Status

```json
200
```

#### 2.0.14 Delete a schema template

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/gs1/schematemplates/template1
```

##### Response Status

```json
204
```
