---
title: "VertexLabel API"
linkTitle: "VertexLabel"
weight: 3
description: "VertexLabel REST API: Define vertex types, ID strategies, and associated properties that determine vertex structure and constraints."
---

### 1.3 VertexLabel

Assuming that the PropertyKeys listed in 1.1.3 have already been created.

Params Description:

- id: The ID value of the vertex type.
- name: The name of the vertex type, required.
- id_strategy: The ID strategy for the vertex type, including primary key ID, auto-generated, custom string, custom number, custom UUID. The default strategy is primary key ID.
- properties: The property types associated with the vertex type.
- primary_keys: The primary key properties. This field must have a value when the ID strategy is PRIMARY_KEY, and must be empty for other ID strategies.
- enable_label_index: Whether to enable label indexing. It is disabled by default.
- index_names: The indexes created for the vertex type. See details in section 3.4.
- nullable_keys: Nullable properties.
- user_data: Setting the common information of the vertex type, similar to the property type.

#### 1.3.1 Create a VertexLabel

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

Starting from version v0.11.2, hugegraph-server supports Time-to-Live (TTL) functionality for vertices. The TTL for vertices is set through VertexLabel. For example, if you want the vertices of type "person" to have a lifespan of one day, you need to set the TTL field to 86400000 (in milliseconds) when creating the "person" VertexLabel.

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

Additionally, if the vertex has a property called "createdTime" and you want to use it as the starting point for calculating the vertex's lifespan, you can set the ttl_start_time field in the VertexLabel. For example, if the "person" VertexLabel has a property called "createdTime" of type Date, and you want the vertices of type "person" to live for one day starting from the creation time, the Request Body for creating the "person" VertexLabel would be as follows:

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

#### 1.3.2 Add properties or userdata to an existing VertexLabel, or remove userdata (removing properties is currently not supported)

##### Params

- action: Indicates whether the current action is to add or remove. Possible values are `append` (add) and `eliminate` (remove).

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

#### 1.3.3 Get all VertexLabels

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

#### 1.3.4 Get VertexLabel by name

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

#### 1.3.5 Delete VertexLabel by name

Deleting a VertexLabel will result in the removal of corresponding vertices and related index data. This operation will generate an asynchronous task.

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

Note:

> You can use `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/1` (where "1" is the task_id) to query the execution status of the asynchronous task. For more information, refer to the [Asynchronous Task RESTful API](./task).
