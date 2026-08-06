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
4. Graphspace enables strict authentication by default (default credential: `admin:pa`). Change the password immediately to avoid unauthorized access.

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
| description                  | Yes      | String  |         |                                                                                | Description                                                                       |
| cpu_limit                    | Yes      | Int     |         | > 0                                                                            | CPU cores for the graphspace                                                      |
| memory_limit                 | Yes      | Int     |         | > 0 (GB)                                                                       | Memory quota in GB                                                                |
| storage_limit                | Yes      | Int     |         | > 0                                                                            | Maximum disk usage                                                                |
| compute_cpu_limit            | No       | Int     | 0       | >= 0                                                                           | Extra HugeGraph-Computer CPU cores; falls back to `cpu_limit` if unset or 0       |
| compute_memory_limit         | No       | Int     | 0       | >= 0                                                                           | Extra HugeGraph-Computer memory in GB; falls back to `memory_limit` if unset or 0 |
| oltp_namespace               | Yes      | String  |         |                                                                                | Kubernetes namespace for OLTP HugeGraph-Server                                    |
| olap_namespace               | Yes      | String  |         | Resources are merged when identical to `oltp_namespace`                        | Kubernetes namespace for OLAP / HugeGraph-Computer                                |
| storage_namespace            | Yes      | String  |         |                                                                                | Kubernetes namespace for HugeGraph-Store                                          |
| operator_image_path          | No       | String  |         |                                                                                | HugeGraph-Computer operator image registry                                        |
| internal_algorithm_image_url | No       | String  |         |                                                                                | HugeGraph-Computer algorithm image registry                                       |
| max_graph_number             | Yes      | Int     |         | > 0                                                                            | Maximum number of graphs that can be created inside the graphspace                |
| max_role_number              | Yes      | Int     |         | > 0                                                                            | Maximum number of roles that can be created inside the graphspace                 |
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
  "graph_number_used": 0,
  "role_number_used": 0,
  "auth": true
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
  "graph_number_used": 0,
  "role_number_used": 0,
  "auth": true
}
```

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
| name                         | Yes      | String |                                                         | Graphspace name                                                                   |
| description                  | Yes      | String |                                                         | Description                                                                       |
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
  "graph_number_used": 0,
  "role_number_used": 0,
  "auth": true
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

