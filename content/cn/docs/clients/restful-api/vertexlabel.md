---
title: "VertexLabel API"
linkTitle: "VertexLabel"
weight: 3
description: "VertexLabel（顶点标签）REST 接口:定义顶点类型、ID策略及关联的属性,决定顶点的结构和约束规则。"
---

### 1.3 VertexLabel

假设已经创建好了 1.1.3 中列出来的 PropertyKeys

Params 说明

- id：顶点类型 id 值
- name：顶点类型名称，必填
- id_strategy: 顶点类型的 ID 策略，主键 ID、自动生成、自定义字符串、自定义数字、自定义 UUID，默认主键 ID
- properties: 顶点类型关联的属性类型
- primary_keys: 主键属性，当 ID 策略为 PRIMARY_KEY 时必须有值，其他 ID 策略时必须为空；
- enable_label_index：是否开启类型索引，默认关闭
- index_names：顶点类型创建的索引，详情见 3.4
- nullable_keys：可为空的属性
- user_data：设置顶点类型的通用信息，作用同属性类型

#### 1.3.1 创建一个 VertexLabel

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
```

##### Request Body

```json
{
    "name": "person",
    "id_strategy": "DEFAULT",
    "properties": [
        "name",
        "age"
    ],
    "primary_keys": [
        "name"
    ],
    "nullable_keys": [],
    "enable_label_index": true
}
```

##### Response Status

```json
201
```

##### Response Body

```json
{
    "id": 1,
    "primary_keys": [
        "name"
    ],
    "id_strategy": "PRIMARY_KEY",
    "name": "person2",
    "index_names": [
    ],
    "properties": [
        "name",
        "age"
    ],
    "nullable_keys": [
    ],
    "enable_label_index": true,
    "user_data": {}
}
```

从 hugegraph-server v0.11.2 版本开始支持顶点的 TTL 功能。顶点的 TTL 是通过 VertexLabel 来设置的。比如希望 person 类型的顶点存活时间为一天，需要在创建 person VertexLabel 的时候将 TTL 字段设置为 86400000，即单位为毫秒。

```json
{
    "name": "person",
    "id_strategy": "DEFAULT",
    "properties": [
        "name",
        "age"
    ],
    "primary_keys": [
        "name"
    ],
    "nullable_keys": [],
    "ttl": 86400000,
    "enable_label_index": true
}
```

另外，当顶点中带有"创建时间"的属性且希望以"创建时间"属性作为计算顶点存活时间的起点时，可以设置 VertexLabel 中的 ttl_start_time 字段。比如 person VertexLabel 有 createdTime 属性，且 createdTime 是 Date 类型的参数，希望 person 类型的顶点从创建开始存活一天的时间，那么创建 person VertexLabel 的 Request Body 如下：

```json
{
    "name": "person",
    "id_strategy": "DEFAULT",
    "properties": [
        "name",
        "age",
        "createdTime"
    ],
    "primary_keys": [
        "name"
    ],
    "nullable_keys": [],
    "ttl": 86400000,
    "ttl_start_time": "createdTime",
    "enable_label_index": true
}
```

#### 1.3.2 为已存在的 VertexLabel 添加 properties 或 userdata，或者移除 userdata（目前不支持移除 properties）

##### Params

- action: 表示当前行为是添加还是移除，取值为`append`（添加）和`eliminate`（移除）

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels/person?action=append
```

##### Request Body

```json
{
    "name": "person",
    "properties": [
        "city"
    ],
    "nullable_keys": ["city"],
    "user_data": {
        "super": "animal"
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
    "id": 1,
    "primary_keys": [
        "name"
    ],
    "id_strategy": "PRIMARY_KEY",
    "name": "person",
    "index_names": [
    ],
    "properties": [
        "city",
        "name",
        "age"
    ],
    "nullable_keys": [
        "city"
    ],
    "enable_label_index": true,
    "user_data": {
        "super": "animal"
    }
}
```

#### 1.3.3 获取所有的 VertexLabel

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "vertexlabels": [
        {
            "id": 1,
            "primary_keys": [
                "name"
            ],
            "id_strategy": "PRIMARY_KEY",
            "name": "person",
            "index_names": [
            ],
            "properties": [
                "city",
                "name",
                "age"
            ],
            "nullable_keys": [
                "city"
            ],
            "enable_label_index": true,
            "user_data": {
                "super": "animal"
            }
        },
        {
            "id": 2,
            "primary_keys": [
                "name"
            ],
            "id_strategy": "PRIMARY_KEY",
            "name": "software",
            "index_names": [
            ],
            "properties": [
                "price",
                "name",
                "lang"
            ],
            "nullable_keys": [
                "price"
            ],
            "enable_label_index": false,
            "user_data": {}
        }
    ]
}
```

#### 1.3.4 根据 name 获取 VertexLabel

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels/person
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": 1,
    "primary_keys": [
        "name"
    ],
    "id_strategy": "PRIMARY_KEY",
    "name": "person",
    "index_names": [
    ],
    "properties": [
        "city",
        "name",
        "age"
    ],
    "nullable_keys": [
        "city"
    ],
    "enable_label_index": true,
    "user_data": {
        "super": "animal"
    }
}
```

#### 1.3.5 根据 name 删除 VertexLabel

删除 VertexLabel 会导致删除对应的顶点以及相关的索引数据，会产生一个异步任务

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels/person
```

##### Response Status

```json
202
```

##### Response Body

```json
{
    "task_id": 1
}
```

注：

> 可以通过`GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/1`（其中"1"是 task_id）来查询异步任务的执行状态，更多[异步任务 RESTful API](./task)
