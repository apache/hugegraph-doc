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
4. 图空间功能必须开启鉴权模式，默认账密为 admin:pa，请务必修改默认密码，防止未授权访问。

#### 2.0.1 创建一个图空间

##### Method & Url

```
POST http://localhost:8080/graphspaces
```

##### Request Body

注意：目前 cpu，内存，以及 k8s 相关功能暂未开放

| 名称                           | 是否必填 | 类型      | 默认值   | 取值范围                              | 说明                                                                    |
|------------------------------|------|---------|-------|-----------------------------------|-----------------------------------------------------------------------|
| name                         | 是    | String  |       | 小写字母、数字和下划线组成，首字符必须是小写字母，长度不超过 48 | 图空间的名字                                                                |
| description                  | 是    | String  |       |                                   | 图空间的描述信息                                                              |
| cpu_limit                    | 是    | Int     |       | > 0                               | CPU 核数                                                                |
| memory_limit                 | 是    | Int     |       | > 0                               | 内存大小，单位 GB                                                            |
| storage_limit                | 是    | Int     |       | > 0                               | 图空间的数据占据的磁盘空间上限                                                       |
| compute_cpu_limit            | 否    | Int     | 0     | >= 0                              | 针对图计算的额外资源配置，单位 cores。当该字段不配置或者配置为 0 时，会由 cpu_limit 字段的值进行覆盖          |
| compute_memory_limit         | 否    | Int     | 0     | >= 0                              | 针对图计算的额外内存配置，单位 GB。当该字段不配置或者配置为 0 时，会由 memory_limit 字段的值进行覆盖          |
| oltp_namespace               | 是    | String  |       |                                   | OLTP 的 k8s 命名空间                                                       |
| olap_namespace               | 是    | String  |       |                                   | OLAP 的 k8s 命名空间。当 olap_namespace 和 oltp_namespace 的值相同时，其配置的资源限额会进行合并 |
| storage_namespace            | 是    | String  |       |                                   | 存储的 k8s 命名空间                                                          |
| operator_image_path          | 否    | String  |       |                                   | 图计算 operator 的镜像地址：在创建图空间时，允许指定对应的图计算镜像并交由 K8S 进行统一管理                 |
| internal_algorithm_image_url | 否    | String  |       |                                   | 图计算的算法镜像地址：在创建图空间时，允许指定图计算的算法镜像并交由 K8S 进行统一管理                         |
| max_graph_number             | 是    | Int     |       | > 0                               | 图空间的图数目的上限                                                            |
| max_role_number              | 是    | Int     |       | > 0                               | 图空间的角色数目的上限                                                           |
| auth                         | 否    | Boolean | false | true, false                       | 图空间是否支持权限认证                                                           |
| configs                      | 否    | Map     |       |                                   | 其他配置信息                                                                |

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

#### 2.0.4 更新某个图空间

> 注意：auth 鉴权配置，在创建图空间的过程一旦确定下来，不允许更新

##### Params

**路径参数说明：**

- graphspace: 图空间名称

**请求体说明：**

- action: 标记本次操作为 Update 动作，取值固定为 "update"
- update: 即将更新的值，下述参数都应置于 update 中

| 名称                           | 是否必填 | 类型     | 默认值 | 取值范围 | 说明                                                                    |
|------------------------------|------|--------|-----|------|-----------------------------------------------------------------------|
| name                         | 是    | String |     |      | 图空间名称                                                                 |
| description                  | 是    | String |     |      | 图空间的描述信息                                                              |
| cpu_limit                    | 是    | Int    |     | > 0  | OLTP HugeGraphServer 的 CPU 核数                                         |
| memory_limit                 | 是    | Int    |     | > 0  | OLTP HugeGraphServer 的内存大小，单位 GB                                      |
| storage_limit                | 是    | Int    |     | > 0  | 图空间的数据占据的磁盘空间上限                                                       |
| compute_cpu_limit            | 否    | Int    | 0   | >= 0 | 针对图计算的额外资源配置，单位 cores。当该字段不配置或者配置为 0 时，会由 cpu_limit 字段的值进行覆盖          |
| compute_memory_limit         | 否    | Int    | 0   | >= 0 | 针对图计算的额外内存配置，单位 GB。当该字段不配置或者配置为 0 时，会由 memory_limit 字段的值进行覆盖          |
| oltp_namespace               | 是    | String |     |      | OLTP 的 k8s 命名空间                                                       |
| olap_namespace               | 是    | String |     |      | OLAP 的 k8s 命名空间。当 olap_namespace 和 oltp_namespace 的值相同时，其配置的资源限额会进行合并 |
| storage_namespace            | 是    | String |     |      | 存储的 k8s 命名空间                                                          |
| operator_image_path          | 否    | String |     |      | 图计算 operator 的镜像地址：在更新图空间时，允许指定对应的图计算镜像并交由 K8S 进行统一管理                 |
| internal_algorithm_image_url | 否    | String |     |      | 图计算的算法镜像地址：在更新图空间时，允许指定图计算的算法镜像并交由 K8S 进行统一管理                         |
| max_graph_number             | 是    | Int    |     | > 0  | 图空间的图数目的上限                                                            |
| max_role_number              | 是    | Int    |     | > 0  | 图空间的角色数目的上限                                                           |

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
