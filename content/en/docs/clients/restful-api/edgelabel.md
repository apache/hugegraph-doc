---
title: "EdgeLabel API"
linkTitle: "EdgeLabel"
weight: 4
description: "EdgeLabel REST API: Define edge types and relationship constraints between source and target vertices to construct graph connection rules."
---

### 1.4 EdgeLabel

Assuming PropertyKeys from version 1.2.3 and VertexLabels from version 1.3.3 have already been created.

Params Explanation

- name: Name of the vertex type, required.
- source_label: Name of the source vertex type, required.
- target_label: Name of the target vertex type, required.
- frequency: Whether there can be multiple edges between two points, can have values SINGLE or MULTIPLE, optional (default value: SINGLE).
- properties: Property types associated with the edge type, optional.
- sort_keys: Specifies a list of differentiating key properties when multiple associations are allowed.
- nullable_keys: Nullable properties, optional (default: nullable).
- enable_label_index: Whether to enable type indexing, disabled by default.

#### 1.4.1 Create an EdgeLabel

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

Starting from version 0.11.2 of hugegraph-server, the TTL (Time to Live) feature for edges is supported. The TTL for edges is set through EdgeLabel. For example, if you want the "knows" type of edge to have a lifespan of one day, you need to set the TTL field to 86400000 when creating the "knows" EdgeLabel, where the unit is milliseconds.

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

Additionally, when the edge has a property called "createdTime" and you want to use the "createdTime" property as the starting point for calculating the edge's lifespan, you can set the ttl_start_time field in the EdgeLabel. For example, if the knows EdgeLabel has a property called "createdTime" which is of type Date, and you want the "knows" type of edge to live for one day from the time of creation, the Request Body for creating the knows EdgeLabel would be as follows:

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

#### 1.4.2 Add properties or userdata to an existing EdgeLabel, or remove userdata (removing properties is currently not supported)

##### Params

- action: Indicates whether the current action is to add or remove, with values `append` (add) and `eliminate` (remove).

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

#### 1.4.3 Get all EdgeLabels

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

#### 1.4.4 Get EdgeLabel by name

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

#### 1.4.5 Delete EdgeLabel by name

Deleting an EdgeLabel will result in the deletion of corresponding edges and related index data. This operation will generate an asynchronous task.

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

Note:

> You can query the execution status of an asynchronous task by using `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/1` (where "1" is the task_id). For more information, refer to the [Asynchronous Task RESTful API](./task).
