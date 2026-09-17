---
title: "Graphspace API"
linkTitle: "Graphspace"
weight: 1
description: "Graphspace（图空间）REST 接口：多租户与资源隔离的创建、查看、更新与删除，以及使用前置条件与限制。"
---

### 2.0 Graphspace

在 HugeGraph 中，多租户是通过图空间（graph space）来实现的，资源的分配和隔离可以通过图空间进行。

**重要前置条件**：

1. 目前图空间功能只支持在 hstore 模式下使用。
2. 如果非 hstore 模式，则只能使用默认的图空间 `DEFAULT`，且不支持创建、删除和更新图空间的操作。
3. 注意在 rest-server.properties 中，设置 `usePD=true`，并且 hugegraph.properties 中，设置 `backend=hstore`
4. 图空间功能必须开启鉴权模式，默认账密为 admin:pa（见 `auth.admin_pa` 配置项），请务必修改默认密码，防止未授权访问。
5. 本页所有接口都只在 PD 模式下可用，单机模式下会返回 `400` 和 `GraphSpace management is not supported in standalone mode` 错误信息。

#### 2.0.1 创建一个图空间

##### Method & Url

```
POST http://localhost:8080/graphspaces
```

##### Request Body

注意：目前 cpu，内存，以及 k8s 相关功能暂未开放

| 名称                         | 是否必填 | 类型    | 默认值    | 取值范围                                                        | 说明                                                                                                 |
|------------------------------|----------|---------|-----------|-----------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| name                         | 是       | String  |           | 小写字母、数字和下划线组成，首字符必须是小写字母，长度不超过 48 | 图空间的名字                                                                                         |
| nickname                     | 否       | String  | name 的值 | 在所有图空间中必须唯一                                          | 图空间的显示名                                                                                       |
| description                  | 否       | String  |           |                                                                 | 图空间的描述信息                                                                                     |
| cpu_limit                    | 是       | Int     |           | > 0                                                             | CPU 核数                                                                                             |
| memory_limit                 | 是       | Int     |           | > 0                                                             | 内存大小，单位 GB                                                                                    |
| storage_limit                | 是       | Int     |           | > 0                                                             | 图空间的数据占据的磁盘空间上限                                                                       |
| compute_cpu_limit            | 否       | Int     | 0         | >= 0                                                            | 针对图计算的额外资源配置，单位 cores。当该字段不配置或者配置为 0 时，会由 cpu_limit 字段的值进行覆盖 |
| compute_memory_limit         | 否       | Int     | 0         | >= 0                                                            | 针对图计算的额外内存配置，单位 GB。当该字段不配置或者配置为 0 时，会由 memory_limit 字段的值进行覆盖 |
| oltp_namespace               | 否       | String  | ""        |                                                                 | OLTP 的 k8s 命名空间                                                                                 |
| olap_namespace               | 否       | String  | ""        |                                                                 | OLAP 的 k8s 命名空间。当 olap_namespace 和 oltp_namespace 的值相同时，其配置的资源限额会进行合并     |
| storage_namespace            | 否       | String  | ""        |                                                                 | 存储的 k8s 命名空间                                                                                  |
| operator_image_path          | 否       | String  | ""        |                                                                 | 图计算 operator 的镜像地址：在创建图空间时，允许指定对应的图计算镜像并交由 K8S 进行统一管理          |
| internal_algorithm_image_url | 否       | String  | ""        |                                                                 | 图计算的算法镜像地址：在创建图空间时，允许指定图计算的算法镜像并交由 K8S 进行统一管理                |
| max_graph_number             | 是       | Int     |           | > 0                                                             | 图空间的图数目的上限                                                                                 |
| max_role_number              | 否       | Int     | 0         |                                                                 | 图空间的角色数目的上限                                                                               |
| auth                         | 否       | Boolean | false     | true, false                                                     | 图空间是否支持权限认证                                                                               |
| configs                      | 否       | Map     |           |                                                                 | 其他配置信息                                                                                         |

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

#### 2.0.2 列出系统所有图空间

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

#### 2.0.3 查看某个图空间

##### Params

**路径参数说明：**

- graphspace: 图空间名称

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

> `dp_username` 和 `dp_password` 由图空间名称推导得到，只有该接口会返回这两个字段。

#### 2.0.4 更新某个图空间

> 注意：auth 鉴权配置，在创建图空间的过程一旦确定下来，不允许更新

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求体说明：**

- action: 标记本次操作为 Update 动作，取值固定为 "update"
- update: 即将更新的值，下述参数都应置于 update 中

| 名称                         | 是否必填 | 类型   | 默认值 | 取值范围                   | 说明                                                                                                 |
|------------------------------|----------|--------|--------|----------------------------|------------------------------------------------------------------------------------------------------|
| name                         | 是       | String |        | 必须与路径中的图空间名一致 | 图空间名称                                                                                           |
| nickname                     | 否       | String |        | 在所有图空间中必须唯一     | 图空间的显示名                                                                                       |
| description                  | 否       | String |        |                            | 图空间的描述信息                                                                                     |
| cpu_limit                    | 是       | Int    |        | > 0                        | OLTP HugeGraphServer 的 CPU 核数                                                                     |
| memory_limit                 | 是       | Int    |        | > 0                        | OLTP HugeGraphServer 的内存大小，单位 GB                                                             |
| storage_limit                | 是       | Int    |        | > 0                        | 图空间的数据占据的磁盘空间上限                                                                       |
| compute_cpu_limit            | 否       | Int    | 0      | >= 0                       | 针对图计算的额外资源配置，单位 cores。当该字段不配置或者配置为 0 时，会由 cpu_limit 字段的值进行覆盖 |
| compute_memory_limit         | 否       | Int    | 0      | >= 0                       | 针对图计算的额外内存配置，单位 GB。当该字段不配置或者配置为 0 时，会由 memory_limit 字段的值进行覆盖 |
| oltp_namespace               | 否       | String |        |                            | OLTP 的 k8s 命名空间                                                                                 |
| olap_namespace               | 否       | String |        |                            | OLAP 的 k8s 命名空间。当 olap_namespace 和 oltp_namespace 的值相同时，其配置的资源限额会进行合并     |
| storage_namespace            | 否       | String |        |                            | 存储的 k8s 命名空间                                                                                  |
| operator_image_path          | 否       | String |        |                            | 图计算 operator 的镜像地址：在更新图空间时，允许指定对应的图计算镜像并交由 K8S 进行统一管理          |
| internal_algorithm_image_url | 否       | String |        |                            | 图计算的算法镜像地址：在更新图空间时，允许指定图计算的算法镜像并交由 K8S 进行统一管理                |
| max_graph_number             | 是       | Int    |        | > 0                        | 图空间的图数目的上限                                                                                 |
| max_role_number              | 否       | Int    |        |                            | 图空间的角色数目的上限                                                                               |

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

#### 2.0.5 删除某个图空间

##### Params

**路径参数说明：**

- graphspace: 图空间名称

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/gs1
```

##### Response Status

```json
204
```

> 注意：删除图空间，会导致图空间的全部资源被释放。

#### 2.0.6 列出系统所有图空间及其详情

##### Params

**请求参数说明：**

- prefix: 只返回名称或显示名以该前缀开头的图空间

##### Method & Url

```
GET http://localhost:8080/graphspaces/profile
```

##### Response Status

```json
200
```

##### Response Body

每条记录包含与 `GET /graphspaces/{graphspace}` 相同的字段，并额外带上 `authed`、`default`、`create_time` 和 `update_time`。`authed` 表示当前用户是否可以进入该图空间：当图空间开启了鉴权，而当前用户既不是管理员、也不是该空间的管理员或成员时为 `false`。`default` 目前恒为 `false`，默认图空间功能尚未实现。

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

**默认角色**

每个图空间内置四种默认角色，可以一次性把一整组权限赋给某个用户或角色：

- `space`：图空间管理员，只有管理员可以授予
- `space_member`：图空间成员
- `analyst`：图空间分析师
- `observer`：只读角色，传入 `graph` 时可以收窄到单个图

`user` 既可以是用户名，也可以是角色名。当前用户是否具备某个默认角色也可以通过 `GET /graphspaces/{graphspace}/auth/managers/default` 查询，参见 [Authentication API](./auth)。

#### 2.0.7 授予默认角色

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求体说明：**

- user: 用户名或角色名，必填
- role: 取值为 `space`、`space_member`、`analyst`、`observer` 之一，必填
- graph: 图名称，选填，只在 `role=observer` 时生效

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

只有在单个图上授予角色时才会回显 `graph`。

```json
{
  "user": "boss",
  "role": "analyst",
  "graphSpace": "gs1"
}
```

#### 2.0.8 查询默认角色

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求参数说明：**

- user: 用户名或角色名，必填
- role: 默认角色名称，必填
- graph: 图名称，选填，只在 `role=observer` 时生效

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

#### 2.0.9 回收默认角色

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求参数说明：**

- user: 用户名或角色名，必填
- role: 默认角色名称，必填
- graph: 图名称，选填，只在 `role=observer` 时生效

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/gs1/role?user=boss&role=analyst
```

##### Response Status

```json
204
```

**Schema 模板**

Schema 模板把一段 Gremlin schema 脚本以名称保存下来，创建图时通过 `schema` 字段引用它来初始化图，参见 [Graphs API](./graphs)。模板可以由它的创建者、图空间管理员或系统管理员修改和删除。

#### 2.0.10 创建 schema 模板

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求体说明：**

- name: 模板名称，必填
- schema: Gremlin schema 脚本，必填

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

#### 2.0.11 列出图空间的全部 schema 模板

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

#### 2.0.12 查看某个 schema 模板

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/schematemplates/template1
```

##### Response Status

```json
200
```

#### 2.0.13 修改某个 schema 模板

只能修改 `schema`，模板名称不可修改。

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

#### 2.0.14 删除某个 schema 模板

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/gs1/schematemplates/template1
```

##### Response Status

```json
204
```
