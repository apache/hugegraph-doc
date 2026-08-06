---
title: "IndexLabel API"
linkTitle: "IndexLabel"
weight: 5
description: "IndexLabel（索引标签）REST 接口:为顶点和边的属性创建索引,加速基于属性的查询和过滤操作。"
---

### 1.5 IndexLabel

假设已经创建好了 1.1.3 中的 PropertyKeys、1.2.3 中的 VertexLabels 以及 1.3.3 中的 EdgeLabels

#### 1.5.1 创建一个 IndexLabel

##### Method & Url

```bash
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/indexlabels
```

##### Request Body

```json
{
    "name": "personByCity",
    "base_type": "VERTEX_LABEL",
    "base_value": "person",
    "index_type": "SECONDARY",
    "fields": [
        "city"
    ]
}
```

##### Response Status

```json
202
```

##### Response Body

```json
{
    "index_label": {
        "id": 1,
        "base_type": "VERTEX_LABEL",
        "base_value": "person",
        "name": "personByCity",
        "fields": [
            "city"
        ],
        "index_type": "SECONDARY"
    },
    "task_id": 2
}
```

#### 1.5.2 获取所有的 IndexLabel

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/indexlabels
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "indexlabels": [
        {
            "id": 3,
            "base_type": "VERTEX_LABEL",
            "base_value": "software",
            "name": "softwareByPrice",
            "fields": [
                "price"
            ],
            "index_type": "RANGE"
        },
        {
            "id": 4,
            "base_type": "EDGE_LABEL",
            "base_value": "created",
            "name": "createdByDate",
            "fields": [
                "date"
            ],
            "index_type": "SECONDARY"
        },
        {
            "id": 1,
            "base_type": "VERTEX_LABEL",
            "base_value": "person",
            "name": "personByCity",
            "fields": [
                "city"
            ],
            "index_type": "SECONDARY"
        },
        {
            "id": 3,
            "base_type": "VERTEX_LABEL",
            "base_value": "person",
            "name": "personByAgeAndCity",
            "fields": [
                "age",
                "city"
            ],
            "index_type": "SECONDARY"
        }
    ]
}
```

#### 1.5.3 根据 name 获取 IndexLabel

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/indexlabels/personByCity
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": 1,
    "base_type": "VERTEX_LABEL",
    "base_value": "person",
    "name": "personByCity",
    "fields": [
        "city"
    ],
    "index_type": "SECONDARY"
}
```

#### 1.5.4 根据 name 删除 IndexLabel

删除 IndexLabel 会导致删除相关的索引数据，会产生一个异步任务

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/indexlabels/personByCity
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
