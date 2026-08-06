---
title: "IndexLabel API"
linkTitle: "IndexLabel"
weight: 5
description: "IndexLabel REST API: Create indexes on vertex and edge properties to accelerate property-based queries and filtering operations."
---

### 1.5 IndexLabel

Assuming PropertyKeys from version 1.1.3, VertexLabels from version 1.2.3, and EdgeLabels from version 1.3.3 have already been created.

#### 1.5.1 Create an IndexLabel

##### Method & Url

```
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

#### 1.5.2 Get all IndexLabels

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

#### 1.5.3 Get IndexLabel by name

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

#### 1.5.4 Delete IndexLabel by name

Deleting an IndexLabel will result in the deletion of related index data. This operation will generate an asynchronous task.

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

Note:

> You can query the execution status of an asynchronous task by using `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/1` (where "1" is the task_id). For more information, refer to the [Asynchronous Task RESTful API](./task).
