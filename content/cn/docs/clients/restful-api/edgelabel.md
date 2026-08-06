---
title: "EdgeLabel API"
linkTitle: "EdgeLabel"
weight: 4
description: "EdgeLabel（边标签）REST 接口:定义边类型、源顶点和目标顶点的关系约束,构建图的连接规则。"
---

### 1.4 EdgeLabel

假设已经创建好了 1.2.3 中的 PropertyKeys 和 1.3.3 中的 VertexLabels

Params 说明

- name：顶点类型名称，必填
- source_label: 源顶点类型的名称，必填
- target_label: 目标顶点类型的名称，必填
- frequency：两个点之间是否可以有多条边，可以取值 SINGLE 和 MULTIPLE，非必填，默认值 SINGLE
- properties: 边类型关联的属性类型，选填
- sort_keys: 当允许关联多次时，指定区分键属性列表
- nullable_keys：可为空的属性，选填，默认可为空
- enable_label_index：是否开启类型索引，默认关闭

#### 1.4.1 创建一个 EdgeLabel

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/edgelabels
```

##### Request Body

```json
{
    "name": "created",
    "source_label": "person",
    "target_label": "software",
    "frequency": "SINGLE",
    "properties": [
        "date"
    ],
    "sort_keys": [],
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
    "sort_keys": [
    ],
    "source_label": "person",
    "name": "created",
    "index_names": [
    ],
    "properties": [
        "date"
    ],
    "target_label": "software",
    "frequency": "SINGLE",
    "nullable_keys": [
    ],
    "enable_label_index": true,
    "user_data": {}
}
```

从 hugegraph-server v0.11.2 版本开始支持边的 TTL 功能。边的 TTL 是通过 EdgeLabel 来设置的。比如希望 knows 类型的边存活时间为一天，需要在创建 knows EdgeLabel 的时候将 TTL 字段设置为 86400000，即单位为毫秒。

```json
{
    "id": 1,
    "sort_keys": [
    ],
    "source_label": "person",
    "name": "knows",
    "index_names": [
    ],
    "properties": [
        "date",
        "createdTime"
    ],
    "target_label": "person",
    "frequency": "SINGLE",
    "nullable_keys": [
    ],
    "enable_label_index": true,
    "ttl": 86400000,
    "user_data": {}
}
```

另外，当边中带有"创建时间"的属性且希望以"创建时间"属性作为计算边存活时间的起点时，可以设置 EdgeLabel 中的 ttl_start_time 字段。比如 knows EdgeLabel 有 createdTime 属性，且 createdTime 是 Date 类型的参数，希望 knows 类型的边从创建开始存活一天的时间，那么创建 knows EdgeLabel 的 Request Body 如下：

```json
{
    "id": 1,
    "sort_keys": [
    ],
    "source_label": "person",
    "name": "knows",
    "index_names": [
    ],
    "properties": [
        "date",
        "createdTime"
    ],
    "target_label": "person",
    "frequency": "SINGLE",
    "nullable_keys": [
    ],
    "enable_label_index": true,
    "ttl": 86400000,
    "ttl_start_time": "createdTime",
    "user_data": {}
}
```

#### 1.4.2 为已存在的 EdgeLabel 添加 properties 或 userdata，或者移除 userdata（目前不支持移除 properties）

##### Params

- action: 表示当前行为是添加还是移除，取值为`append`（添加）和`eliminate`（移除）

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/edgelabels/created?action=append
```

##### Request Body

```json
{
    "name": "created",
    "properties": [
        "weight"
    ],
    "nullable_keys": [
        "weight"
    ]
}
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": 2,
    "sort_keys": [
    ],
    "source_label": "person",
    "name": "created",
    "index_names": [
    ],
    "properties": [
        "date",
        "weight"
    ],
    "target_label": "software",
    "frequency": "SINGLE",
    "nullable_keys": [
        "weight"
    ],
    "enable_label_index": true,
    "user_data": {}
}
```

#### 1.4.3 获取所有的 EdgeLabel

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/edgelabels
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "edgelabels": [
        {
            "id": 1,
            "sort_keys": [
            ],
            "source_label": "person",
            "name": "created",
            "index_names": [
            ],
            "properties": [
                "date",
                "weight"
            ],
            "target_label": "software",
            "frequency": "SINGLE",
            "nullable_keys": [
                "weight"
            ],
            "enable_label_index": true,
            "user_data": {}
        },
        {
            "id": 2,
            "sort_keys": [
            ],
            "source_label": "person",
            "name": "knows",
            "index_names": [
            ],
            "properties": [
                "date",
                "weight"
            ],
            "target_label": "person",
            "frequency": "SINGLE",
            "nullable_keys": [
            ],
            "enable_label_index": false,
            "user_data": {}
        }
    ]
}
```

#### 1.4.4 根据 name 获取 EdgeLabel

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/edgelabels/created
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": 1,
    "sort_keys": [
    ],
    "source_label": "person",
    "name": "created",
    "index_names": [
    ],
    "properties": [
        "date",
        "city",
        "weight"
    ],
    "target_label": "software",
    "frequency": "SINGLE",
    "nullable_keys": [
        "city",
        "weight"
    ],
    "enable_label_index": true,
    "user_data": {}
}
```

#### 1.4.5 根据 name 删除 EdgeLabel

删除 EdgeLabel 会导致删除对应的边以及相关的索引数据，会产生一个异步任务

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/edgelabels/created
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
