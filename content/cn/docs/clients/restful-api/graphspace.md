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
4. 生产环境必须启用 Server 认证与授权，并将新建图空间的 `auth` 设为 `true`。生产管理员密码必须替换公开默认值 `pa`（由 `auth.admin_pa` 配置）。
5. 本页所有接口都只在 PD 模式下可用，单机模式下会返回 `400` 和 `GraphSpace management is not supported in standalone mode` 错误信息。

> [!WARNING]
> **限制图空间列表和详情接口的访问**
>
> `GET /graphspaces` 和 `GET /graphspaces/{graphspace}` 均未声明 `@RolesAllowed`；Server 未启用鉴权时可匿名调用，启用鉴权后也没有方法级管理员角色限制。
> 详情响应包含 `dp_username` 和 `dp_password`。
>
> 生产环境设置 `white_ip.status=enable`，并通过 [IP 白名单 API](/cn/docs/clients/restful-api/other/) 维护名单。网关还须按调用者身份或角色，
> 仅允许管理员和可信运维调用方访问这两条路径。只限制来源 IP 仍会让同一网段的普通已认证账号读取 DP 凭据；Server API 端口应仅允许可信网关出口访问，阻断客户端直连。
>
> 在网关记录调用身份、来源和结果。Server `audit-*.log` 记录鉴权授权，不能替代这两条路径的网关访问审计；业务账号按最小权限授权。

#### 2.0.1 创建一个图空间

##### Method & Url

```text
POST http://localhost:8080/graphspaces
```

##### Request Body

`server.use_k8s=true` 时，CPU 与内存限额用于配置 Kubernetes 命名空间配额；其他部署不会据此限制 JVM 或容器资源。
修改这些字段不会自动调整现有 Pod 的资源。

| 名称                         | 是否必填 | 类型    | 默认值    | 取值范围                                                        | 说明                                                                                                 |
|------------------------------|----------|---------|-----------|-----------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| name                         | 是       | String  |           | 小写字母、数字和下划线组成，首字符必须是小写字母，长度不超过 48 | 图空间的名字                                                                                         |
| nickname                     | 否       | String  | name 的值 | 在所有图空间中必须唯一                                          | 图空间的显示名                                                                                       |
| description                  | 否       | String  |           |                                                                 | 图空间的描述信息                                                                                     |
| cpu_limit                    | 否 | Int     | 128 | > 0                                                             | CPU 核数                                                                                             |
| memory_limit                 | 否 | Int     | 128 | > 0                                                             | 内存大小，单位 GB                                                                                    |
| storage_limit                | 否 | Int     | 10240 | > 0                                                             | 图空间的数据占据的磁盘空间上限，单位 GB                                                              |
| compute_cpu_limit            | 否       | Int     | 0         | >= 0                                                            | 计算配额；省略或为 `0` 时持续继承 `cpu_limit` |
| compute_memory_limit         | 否       | Int     | 0         | >= 0                                                            | 计算配额；省略或为 `0` 时持续继承 `memory_limit` |
| oltp_namespace               | 否       | String  | ""        |                                                                 | OLTP 的 k8s 命名空间                                                                                 |
| olap_namespace               | 否       | String  | ""        |                                                                 | OLAP 的 k8s 命名空间。当 olap_namespace 和 oltp_namespace 的值相同时，其配置的资源限额会进行合并     |
| storage_namespace            | 否       | String  | ""        |                                                                 | 存储的 k8s 命名空间                                                                                  |
| operator_image_path          | 否       | String  | ""        |                                                                 | 图计算 operator 的镜像地址：在创建图空间时，允许指定对应的图计算镜像并交由 K8S 进行统一管理          |
| internal_algorithm_image_url | 否       | String  | ""        |                                                                 | 图计算的算法镜像地址：在创建图空间时，允许指定图计算的算法镜像并交由 K8S 进行统一管理                |
| max_graph_number             | 否 | Int     | 100 | > 0                                                             | 图空间的图数目的上限                                                                                 |
| max_role_number              | 否 | Int     | 100 |                                                                 | 图空间的角色数目的上限                                                                               |
| auth                         | 否       | Boolean | false     | true, false                                                     | 图空间是否支持权限认证                                                                               |
| configs                      | 否       | Map     |           |                                                                 | 其他配置信息                                                                                         |
{.td-table--wide}

以上创建默认值自 Server 1.8.0 起生效。在 Server 1.7.0 中，`cpu_limit`、`memory_limit`、`storage_limit` 与 `max_graph_number` 均为必填项（必须 > 0），省略会导致字段取值为 0 并被校验拒绝。已有图空间保留原配额，Hubble 等客户端也可以显式提交其他值。
省略的计算配额保存为 `0`，持续继承对应的 CPU 或内存配额。

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
  "storage_used_kb": 0,
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

```text
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

```text
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
  "storage_used_kb": 0,
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

> 上述 `dp_username` 和 `dp_password` 是文档示例值。实际详情响应会返回对应图空间的 DP 凭据，应按敏感凭据保护。

#### 2.0.4 更新某个图空间

> 注意：auth 鉴权配置，在创建图空间的过程一旦确定下来，不允许更新

> [!NOTE]
> **动态配额更新与资源约束**：
> - **动态配额更新**：管理员可通过 `PUT /graphspaces/{name}` 并携带 `{"action":"update","update":{...}}` 动态调整配额（包括 `max_graph_number`、
>   `max_role_number`、`cpu_limit`、`memory_limit`、`storage_limit`）。更新前建议先通过 `GET /graphspaces/{name}` 读取当前配置，并保留未修改字段的原值。
> - **计算资源配额继承**：当 `compute_cpu_limit: 0` 或 `compute_memory_limit: 0`（或创建时缺省）时，表示持续继承主图空间的 `cpu_limit` 和 `memory_limit`。
>   数值 0 代表继承，既非无限制也非分配 0 资源。
>   在 Server 1.8.0+ 中，更新时省略计算配额字段会保留原设置，显式传入 0 恢复继承；而在 Server 1.7.0 中，更新处理会忽略 0，保留之前的配额而不会恢复继承。响应保留这个原始 0 标记。
> - **配额超限约束**：图数量达到 `max_graph_number` 时，新建图请求将被拒绝并返回 `reach graph limit`；存储占用超过 `storage_limit` 时，PD 会将该图空间内的图标记为
>   `ReadOnly`（只读），待后续巡检检测到占用降至配额以下后自动恢复 `ReadWrite`。
> - **高精度存储指标**：响应体在保留以 GB 为单位的整数 `storage_used` 字段外，新增了 `storage_used_kb` 字段以支持 1GB 以下的高精度用量展示，`storage_percent`
>   比率直接基于该 KB 精度值计算得出。

客户端必须保留“省略字段”与“显式传入 0”的区别。旧客户端可能把未设置的计算配额序列化为 0，意外恢复继承。
使用这类客户端时，先读取图空间，再显式传入需要保留的原计算配额。

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
| storage_limit                | 是       | Int    |        | > 0                        | 图空间的数据占据的磁盘空间上限，单位 GB                                                              |
| compute_cpu_limit            | 否       | Int    | 保留原值 | >= 0                       | 省略时保留当前设置；`0` 恢复继承 `cpu_limit` |
| compute_memory_limit         | 否       | Int    | 保留原值 | >= 0                       | 省略时保留当前设置；`0` 恢复继承 `memory_limit` |
| oltp_namespace               | 否       | String |        |                            | OLTP 的 k8s 命名空间                                                                                 |
| olap_namespace               | 否       | String |        |                            | OLAP 的 k8s 命名空间。当 olap_namespace 和 oltp_namespace 的值相同时，其配置的资源限额会进行合并     |
| storage_namespace            | 否       | String |        |                            | 存储的 k8s 命名空间                                                                                  |
| operator_image_path          | 否       | String |        |                            | 图计算 operator 的镜像地址：在更新图空间时，允许指定对应的图计算镜像并交由 K8S 进行统一管理          |
| internal_algorithm_image_url | 否       | String |        |                            | 图计算的算法镜像地址：在更新图空间时，允许指定图计算的算法镜像并交由 K8S 进行统一管理                |
| max_graph_number             | 是       | Int    |        | > 0                        | 图空间的图数目的上限                                                                                 |
| max_role_number              | 是 | Int    |        |                            | 图空间的角色数目的上限                                                                               |
{.td-table--wide}

##### Method & Url

```text
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
  "storage_used_kb": 0,
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

```text
DELETE http://localhost:8080/graphspaces/gs1
```

##### Response Status

```json
204
```

> [!WARNING]
> 升级到支持图空间统计清理的 Server 前，先升级**全部 PD 节点**。旧 PD 会返回 `UNIMPLEMENTED`，但此时 Server 已清理图、
> 图空间权限、Schema 模板和服务，只保留图空间配置与列表项并报告删除失败。该操作不是事务，失败响应不会恢复已经清理的资源。

删除期间停止在该空间新建图。成功删除还会移除该空间的 PD 配额与用量记录，但不会清理旧版本删除操作留下的历史孤儿记录。
PD 清理失败时，应修正原因再重试，不能假设失败后的图空间仍保留原有图。

若 PD 报告仍有图元数据，通过 PD 已鉴权的 `GET /v1/partitionsAndStats` 核查完整图标识，包含数据 `/g` 与 Schema `/m` 记录，
即使记录下已无分区也会列出；仅查询 `GET /v1/graphs` 不足以完成排查。确认所有权和需要保留的数据后，通过正常 Server 图接口处理
确认废弃的图。若 Server 已缺少该图配置，使用原图空间、图名和后端重建配置，再正常删除图并重试删除图空间。
其他 Server 管理的图应通过其所有者处理；不要直接删除 PD 记录，也不要擅自重建其他 Server 管理的图。

#### 2.0.6 列出系统所有图空间及其详情

##### Params

**请求参数说明：**

- prefix: 只返回名称或显示名以该前缀开头的图空间

##### Method & Url

```text
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
    "storage_used_kb": 0,
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

```text
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

```text
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

```text
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

```text
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

```text
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

```text
GET http://localhost:8080/graphspaces/gs1/schematemplates/template1
```

##### Response Status

```json
200
```

#### 2.0.13 修改某个 schema 模板

只能修改 `schema`，模板名称不可修改。

##### Method & Url

```text
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

```text
DELETE http://localhost:8080/graphspaces/gs1/schematemplates/template1
```

##### Response Status

```json
204
```
