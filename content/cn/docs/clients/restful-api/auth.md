---
title: "Authentication API"
linkTitle: "Authentication"
weight: 16
description: "Authentication（认证鉴权）REST 接口:管理用户、角色、权限和访问控制,实现细粒度的图数据安全机制。"
---

> **版本变更说明**:
> - 1.7.0+: Auth API 路径使用 GraphSpace 格式，如 `/graphspaces/DEFAULT/auth/users`，且 group/target 等 id 格式与 name 一致（如 `admin`）
> - 1.5.x 及更早: Auth API 路径包含 graph 名称，group/target 等 id 格式类似 `-69:grant`。参考 [HugeGraph 1.5.x RESTful API](https://github.com/apache/hugegraph-doc/tree/release-1.5.0)

### 10.1 用户认证与权限控制

> 开启权限及相关配置请先参考 [权限配置](/cn/docs/config/config-authentication/) 文档

##### 用户认证与权限控制概述：
HugeGraph 支持多用户认证、以及细粒度的权限访问控制，采用基于“用户 - 用户组 - 操作 - 资源”的 4 层设计，灵活控制用户角色与权限。 
资源描述了图数据库中的数据，比如符合某一类条件的顶点，每一个资源包括 type、label、properties 三个要素，共有 18 种 type、
任意 label、任意 properties 的组合形成的资源，一个资源的内部条件是且关系，多个资源之间的条件是或关系。用户可以属于一个或多个用户组，
每个用户组可以拥有对任意个资源的操作权限，操作类型包括：读、写、删除、执行等种类。HugeGraph 支持动态创建用户、用户组、资源，
支持动态分配或取消权限。初始化数据库时超级管理员用户被创建，后续可通过超级管理员创建各类角色用户，新创建的用户如果被分配足够权限后，可以由其创建或管理更多的用户。

##### 举例说明：
user(name=boss) -belong-> group(name=all) -access(read)-> target(graph=graph1, resource={label: person,
city: Beijing})  
描述：用户'boss'拥有对'graph1'图中北京人的读权限。

##### 接口说明：
用户认证与权限控制接口包括 5 类：UserAPI、GroupAPI、TargetAPI、BelongAPI、AccessAPI。
**注意**: 1.5.0 及之前，group/target 等 id 的格式类似 -69:grant，1.7.0 及之后，id 和 name 一致，如 admin [HugeGraph 1.5.x RESTful API](https://github.com/apache/hugegraph-doc/tree/release-1.5.0)

### 10.2 用户（User）API
用户接口包括：创建用户，删除用户，修改用户，和查询用户相关信息接口。

#### 10.2.1 创建用户

##### Params

- user_name: 用户名称
- user_password: 用户密码
- user_phone: 用户手机号
- user_email: 用户邮箱  

其中 user_name 和 user_password 为必填。

##### Request Body

```json
{
    "user_name": "boss",
    "user_password": "******",
    "user_phone": "182****9088",
    "user_email": "123@xx.com"
}
```


##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/users
```

##### Response Status

```json
201 
```

##### Response Body
返回报文中，密码为加密后的密文
```json
{
    "user_password": "******",
    "user_email": "123@xx.com",
    "user_update": "2020-11-17 14:31:07.833",
    "user_name": "boss",
    "user_creator": "admin",
    "user_phone": "182****9088",
    "id": "boss",
    "user_create": "2020-11-17 14:31:07.833"
}
```

#### 10.2.2 删除用户

##### Params

- id: 需要删除的用户 Id


##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/users/test
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.2.3 修改用户

##### Params

- id: 需要修改的用户 Id

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/users/test
```

##### Request Body
修改 user_name、user_password 和 user_phone
```json
{
    "user_name": "test",
    "user_password": "******",
    "user_phone": "183****9266"
}
```

##### Response Status

```json
200
```

##### Response Body
返回结果是包含修改过的内容在内的整个用户组对象
```json
{
    "user_password": "******",
    "user_update": "2020-11-12 10:29:30.455",
    "user_name": "test",
    "user_creator": "admin",
    "user_phone": "183****9266",
    "id": "test",
    "user_create": "2020-11-12 10:27:13.601"
}
```

#### 10.2.4 查询用户列表

##### Params

- limit: 返回结果条数的上限


##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/users
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "users": [
        {
            "user_password": "******",
            "user_update": "2020-11-11 11:41:12.254",
            "user_name": "admin",
            "user_creator": "system",
          "id": "admin",
            "user_create": "2020-11-11 11:41:12.254"
        }
    ]
}
```

#### 10.2.5 查询某个用户

##### Params

- id: 需要查询的用户 Id

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/users/admin
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "users": [
        {
            "user_password": "******",
            "user_update": "2020-11-11 11:41:12.254",
            "user_name": "admin",
            "user_creator": "system",
          "id": "admin",
            "user_create": "2020-11-11 11:41:12.254"
        }
    ]
}
```

#### 10.2.6 查询某个用户的角色

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/users/boss/role
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "roles": {
        "hugegraph": {
            "READ": [
                {
                    "type": "ALL",
                    "label": "*",
                    "properties": null
                }
            ]
        }
    }
}
```

### 10.3 用户组（Group）API
用户组会赋予相应的资源权限，用户会被分配不同的用户组，即可拥有不同的资源权限。  
用户组接口包括：创建用户组，删除用户组，修改用户组，和查询用户组相关信息接口。

#### 10.3.1 创建用户组

##### Params

- group_name: 用户组名称
- group_description: 用户组描述

##### Request Body

```json
{
    "group_name": "all",
    "group_description": "group can do anything"
}
```


##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/groups
```

##### Response Status

```json
201 
```

##### Response Body

```json
{
    "group_creator": "admin",
    "group_name": "all",
    "group_create": "2020-11-11 15:46:08.791",
    "group_update": "2020-11-11 15:46:08.791",
    "id": "-69:all",
    "group_description": "group can do anything"
}
```

#### 10.3.2 删除用户组

##### Params

- id: 需要删除的用户组 Id


##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/groups/-69:grant
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.3.3 修改用户组

##### Params

- id: 需要修改的用户组 Id

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/groups/-69:grant
```

##### Request Body
修改 group_description
```json
{
    "group_name": "grant",
    "group_description": "grant"
}
```

##### Response Status

```json
200
```

##### Response Body
返回结果是包含修改过的内容在内的整个用户组对象
```json
{
    "group_creator": "admin",
    "group_name": "grant",
    "group_create": "2020-11-12 09:50:58.458",
    "group_update": "2020-11-12 09:57:58.155",
    "id": "-69:grant",
    "group_description": "grant"
}
```

#### 10.3.4 查询用户组列表

##### Params

- limit: 返回结果条数的上限

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/groups
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "groups": [
        {
            "group_creator": "admin",
            "group_name": "all",
            "group_create": "2020-11-11 15:46:08.791",
            "group_update": "2020-11-11 15:46:08.791",
            "id": "-69:all",
            "group_description": "group can do anything"
        }
    ]
}
```

#### 10.3.5 查询某个用户组

##### Params

- id: 需要查询的用户组 Id

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/groups/-69:all
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "group_creator": "admin",
    "group_name": "all",
    "group_create": "2020-11-11 15:46:08.791",
    "group_update": "2020-11-11 15:46:08.791",
    "id": "-69:all",
    "group_description": "group can do anything"
}
```

### 10.4 资源（Target）API
资源描述了图数据库中的数据，比如符合某一类条件的顶点，每一个资源包括 type、label、properties 三个要素，共有 18 种 type、
任意 label、任意 properties 的组合形成的资源，一个资源的内部条件是且关系，多个资源之间的条件是或关系。   
资源接口包括：资源的创建、删除、修改和查询。

#### 10.4.1 创建资源

##### Params
- target_name: 资源名称
- target_graph: 资源图
- target_url: 资源地址
- target_resources: 资源定义 (列表)

target_resources 可以包括多个 target_resource，以列表的形式存储。  
每个 target_resource 包含：
- type：可选值 VERTEX, EDGE 等，可填 ALL，则表示可以是顶点或边；
- label：可选值，⼀个顶点或边类型的名称，可填*，则表示任意类型；
- properties：map 类型，可包含多个属性的键值对，必须匹配所有属性值，属性值⽀持填条件范围（age:
  P.gte(18)），properties 如果为 null 表示任意属性均可，如果属性名和属性值均为‘*ʼ也表示任意属性均可。

如精细资源："target_resources": [{"type":"VERTEX","label":"person","properties":{"city":"Beijing","age":"P.gte(20)"}}]**  
资源定义含义：类型是'person'的顶点，且城市属性是'Beijing'，年龄属性大于等于 20。

##### Request Body

```json
{
    "target_name": "all",
    "target_graph": "hugegraph",
    "target_url": "127.0.0.1:8080",
    "target_resources": [
        {
            "type": "ALL"
        }
    ]
}
```

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/targets
```

##### Response Status

```json
201 
```

##### Response Body

```json
{
    "target_creator": "admin",
    "target_name": "all",
    "target_url": "127.0.0.1:8080",
    "target_graph": "hugegraph",
    "target_create": "2020-11-11 15:32:01.192",
    "target_resources": [
        {
            "type": "ALL",
            "label": "*",
            "properties": null
        }
    ],
    "id": "-77:all",
    "target_update": "2020-11-11 15:32:01.192"
}
```

#### 10.4.2 删除资源

##### Params

- id: 需要删除的资源 Id


##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/targets/-77:gremlin
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.4.3 修改资源

##### Params

- id: 需要修改的资源 Id


##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/targets/-77:gremlin
```

##### Request Body
修改资源定义中的 type
```json
{
    "target_name": "gremlin",
    "target_graph": "hugegraph",
    "target_url": "127.0.0.1:8080",
    "target_resources": [
        {
            "type": "NONE"
        }
    ]
}
```

##### Response Status

```json
200
```

##### Response Body
返回结果是包含修改过的内容在内的整个用户组对象
```json
{
    "target_creator": "admin",
    "target_name": "gremlin",
    "target_url": "127.0.0.1:8080",
    "target_graph": "hugegraph",
    "target_create": "2020-11-12 09:34:13.848",
    "target_resources": [
        {
            "type": "NONE",
            "label": "*",
            "properties": null
        }
    ],
    "id": "-77:gremlin",
    "target_update": "2020-11-12 09:37:12.780"
}
```

#### 10.4.4 查询资源列表

##### Params

- limit: 返回结果条数的上限

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/targets
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "targets": [
        {
            "target_creator": "admin",
            "target_name": "all",
            "target_url": "127.0.0.1:8080",
            "target_graph": "hugegraph",
            "target_create": "2020-11-11 15:32:01.192",
            "target_resources": [
                {
                    "type": "ALL",
                    "label": "*",
                    "properties": null
                }
            ],
            "id": "-77:all",
            "target_update": "2020-11-11 15:32:01.192"
        },
        {
            "target_creator": "admin",
            "target_name": "grant",
            "target_url": "127.0.0.1:8080",
            "target_graph": "hugegraph",
            "target_create": "2020-11-11 15:43:24.841",
            "target_resources": [
                {
                    "type": "GRANT",
                    "label": "*",
                    "properties": null
                }
            ],
            "id": "-77:grant",
            "target_update": "2020-11-11 15:43:24.841"
        }
    ]
}
```

#### 10.4.5 查询某个资源

##### Params

- id: 需要查询的资源 Id

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/targets/-77:grant
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "target_creator": "admin",
    "target_name": "grant",
    "target_url": "127.0.0.1:8080",
    "target_graph": "hugegraph",
    "target_create": "2020-11-11 15:43:24.841",
    "target_resources": [
        {
            "type": "GRANT",
            "label": "*",
            "properties": null
        }
    ],
    "id": "-77:grant",
    "target_update": "2020-11-11 15:43:24.841"
}
```

### 10.5 关联角色（Belong）API
关联用户和用户组的关系，一个用户可以关联一个或者多个用户组。用户组拥有相关资源的权限，不同用户组的资源权限可以理解为不同的角色。即给用户关联角色。  
关联角色接口包括：用户关联角色的创建、删除、修改和查询。

#### 10.5.1 创建用户的关联角色

##### Params

- user: 用户 Id
- group: 用户组 Id
- belong_description: 描述

##### Request Body

```json
{
  "user": "boss",
    "group": "-69:all"
}
```


##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/belongs
```

##### Response Status

```json
201 
```

##### Response Body

```json
{
    "belong_create": "2020-11-11 16:19:35.422",
    "belong_creator": "admin",
    "belong_update": "2020-11-11 16:19:35.422",
  "id": "Sboss>-82>>S-69:all",
  "user": "boss",
    "group": "-69:all"
}
```

#### 10.5.2 删除关联角色

##### Params

- id: 需要删除的关联角色 Id

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/belongs/Sboss>-82>>S-69:grant
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.5.3 修改关联角色
关联角色只能修改描述，不能修改 user 和 group 属性，如果需要修改关联角色，需要删除原来关联关系，新增关联角色。

##### Params

- id: 需要修改的关联角色 Id

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/belongs/Sboss>-82>>S-69:grant
```

##### Request Body
修改 belong_description
```json
{
    "belong_description": "update test"
}
```

##### Response Status

```json
200
```

##### Response Body
返回结果是包含修改过的内容在内的整个用户组对象
```json
{
    "belong_description": "update test",
    "belong_create": "2020-11-12 10:40:21.720",
    "belong_creator": "admin",
    "belong_update": "2020-11-12 10:42:47.265",
  "id": "Sboss>-82>>S-69:grant",
  "user": "boss",
    "group": "-69:grant"
}
```

#### 10.5.4 查询关联角色列表

##### Params

- limit: 返回结果条数的上限


##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/belongs
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "belongs": [
        {
            "belong_create": "2020-11-11 16:19:35.422",
            "belong_creator": "admin",
            "belong_update": "2020-11-11 16:19:35.422",
          "id": "Sboss>-82>>S-69:all",
          "user": "boss",
            "group": "-69:all"
        }
    ]
}
```

#### 10.5.5 查看某个关联角色

##### Params

- id: 需要查询的关联角色 Id

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/belongs/Sboss>-82>>S-69:all
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "belong_create": "2020-11-11 16:19:35.422",
    "belong_creator": "admin",
    "belong_update": "2020-11-11 16:19:35.422",
  "id": "Sboss>-82>>S-69:all",
  "user": "boss",
    "group": "-69:all"
}
```

### 10.6 赋权（Access）API
给用户组赋予资源的权限，主要包含：读操作 (READ)、写操作 (WRITE)、删除操作 (DELETE)、执行操作 (EXECUTE) 等。  
赋权接口包括：赋权的创建、删除、修改和查询。

#### 10.6.1 创建赋权 (用户组赋予资源的权限)

##### Params

- group: 用户组 Id
- target: 资源 Id
- access_permission: 权限许可  
- access_description: 赋权描述

access_permission：
- READ：读操作，所有的查询，包括查询 Schema、查顶点/边，查询顶点和边的数量 VERTEX_AGGR/EDGE_AGGR，也包括读图的状态 STATUS、变量 VAR、任务 TASK 等；
- WRITE：写操作，所有的创建、更新操作，包括给 Schema 增加 property key，给顶点增加或更新属性等；
- DELETE：删除操作，包括删除元数据、删除顶点/边；
- EXECUTE：执⾏操作，包括执⾏ Gremlin 语句、执⾏ Task、执⾏ metadata 函数；

##### Request Body

```json
{
    "group": "-69:all",
    "target": "-77:all",
    "access_permission": "READ"
}
```

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/accesses
```

##### Response Status

```json
201 
```

##### Response Body

```json
{
    "access_permission": "READ",
    "access_create": "2020-11-11 15:54:54.008",
    "id": "S-69:all>-88>11>S-77:all",
    "access_update": "2020-11-11 15:54:54.008",
    "access_creator": "admin",
    "group": "-69:all",
    "target": "-77:all"
}
```

#### 10.6.2 删除赋权

##### Params

- id: 需要删除的赋权 Id


##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/accesses/S-69:all>-88>12>S-77:all
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.6.3 修改赋权
赋权只能修改描述，不能修改用户组、资源和权限许可，如果需要修改赋权的关系，可以删除原来的赋权关系，新增赋权。

##### Params

- id: 需要修改的赋权 Id

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/accesses/S-69:all>-88>12>S-77:all
```

##### Request Body
修改 access_description
```json
{
    "access_description": "test"
}
```

##### Response Status

```json
200
```

##### Response Body
返回结果是包含修改过的内容在内的整个用户组对象
```json
{
    "access_description": "test",
    "access_permission": "WRITE",
    "access_create": "2020-11-12 10:12:03.074",
    "id": "S-69:all>-88>12>S-77:all",
    "access_update": "2020-11-12 10:16:18.637",
    "access_creator": "admin",
    "group": "-69:all",
    "target": "-77:all"
}
```

#### 10.6.4 查询赋权列表

##### Params

- limit: 返回结果条数的上限

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/accesses
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "accesses": [
        {
            "access_permission": "READ",
            "access_create": "2020-11-11 15:54:54.008",
            "id": "S-69:all>-88>11>S-77:all",
            "access_update": "2020-11-11 15:54:54.008",
            "access_creator": "admin",
            "group": "-69:all",
            "target": "-77:all"
        }
    ]
}
```

#### 10.6.5 查询某个赋权

##### Params

- id: 需要查询的赋权 Id

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/accesses/S-69:all>-88>11>S-77:all
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "access_permission": "READ",
    "access_create": "2020-11-11 15:54:54.008",
    "id": "S-69:all>-88>11>S-77:all",
    "access_update": "2020-11-11 15:54:54.008",
    "access_creator": "admin",
    "group": "-69:all",
    "target": "-77:all"
}
```

### 10.7 图空间管理员（Manager）API

**重要提示**：在使用以下 API 之前，需要先创建图空间（graphspace）。请参考 [Graphspace API](./graphspace) 创建名为 `gs1` 的图空间。文档中的示例均假设已存在名为 `gs1` 的图空间

1. 图空间管理员 API 用于在 graphspace 维度给用户授予/回收管理员角色，并查询当前用户或其他用户在该 graphspace 下的角色信息。角色类型可取 `SPACE`、`SPACE_MEMBER`、`ADMIN` 。

#### 10.7.1 检查当前登录用户是否拥有某个角色

##### Params

- type: 需要校验的角色类型，可选

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/auth/managers/check?type=WRITE
```

##### Response Status

```json
200
```

##### Response Body

```json
"true"
```

返回 `true/false` 字符串表示是否拥有对应角色。

#### 10.7.2 查询图空间管理员列表

##### Params

- type: 角色类型，可选，按角色过滤

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/auth/managers?type=SPACE
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "managers": [
    {
      "user": "admin",
      "type": "SPACE",
      "create_time": "2024-01-10 09:30:00"
    }
  ]
}
```

#### 10.7.3 授权/创建图空间管理员

- 下面在 gs1 下，将用户 boss 授权为 SPACE_MEMBER 角色

##### Request Body

```json
{
  "user": "boss",
  "type": "SPACE_MEMBER"
}
```

##### Method & Url

```
POST http://localhost:8080/graphspaces/gs1/auth/managers
```

##### Response Status

```json
201
```

##### Response Body

```json
{
  "user": "boss",
  "type": "SPACE_MEMBER",
  "manager_creator": "admin",
  "manager_create": "2024-01-10 09:45:12"
}
```

#### 10.7.4 取消图空间管理员权限

- 下面在 gs1 下，将用户 boss 的 SPACE_MEMBER 角色删除

##### Params

- user: 需要删除的用户 Id
- type: 需要删除的角色类型

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/gs1/auth/managers?user=boss&type=SPACE_MEMBER
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.7.5 查询指定用户在图空间中的角色

##### Params

- user: 用户 Id

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/auth/managers/role?user=boss
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "roles": {
    "boss": [
      "READ",
      "SPACE_MEMBER"
    ]
  }
}
```
