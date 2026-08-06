---
title: "PropertyKey API"
linkTitle: "PropertyKey"
weight: 2
description: "PropertyKey REST API: Define data types and cardinality constraints for all properties in the graph, serving as fundamental schema elements."
---

### 1.2 PropertyKey

Params Description:

- name: The name of the property type, required.
- data_type: The data type of the property type, including: bool, byte, int, long, float, double, text, blob, date, uuid. The default data type is `text` (Represent a `string` type)
- cardinality: The cardinality of the property type, including: single, list, set. The default cardinality is `single`.

Request Body Field Description:

- id: The ID value of the property type.
- properties: The properties of the property type. For properties, this field is empty.
- user_data: Setting the common information of the property type, such as setting the value range of the age property from 0 to 100. Currently, no validation is performed on this field, and it is only a reserved entry for future expansion.

#### 1.2.1 Create a PropertyKey

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/propertykeys
```

##### Request Body

```json
{
    "name": "age",
    "data_type": "INT",
    "cardinality": "SINGLE"
}
```

##### Response Status

```json
202
```

##### Response Body

```json
{
    "property_key": {
        "id": 1,
        "name": "age",
        "data_type": "INT",
        "cardinality": "SINGLE",
        "aggregate_type": "NONE",
        "write_type": "OLTP",
        "properties": [],
        "status": "CREATED",
        "user_data": {
            "~create_time": "2022-05-13 13:47:23.745"
        }
    },
    "task_id": 0
}
```

#### 1.2.2 Add or Remove userdata for an existing PropertyKey

##### Params

- action: Indicates whether the current action is to add or remove userdata. Possible values are `append` (add) and `eliminate` (remove).

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/propertykeys/age?action=append
```

##### Request Body

```json
{
    "name": "age",
    "user_data": {
        "min": 0,
        "max": 100
    }
}
```

##### Response Status

```json
202
```

##### Response Body

```json
{
    "property_key": {
        "id": 1,
        "name": "age",
        "data_type": "INT",
        "cardinality": "SINGLE",
        "aggregate_type": "NONE",
        "write_type": "OLTP",
        "properties": [],
        "status": "CREATED",
        "user_data": {
            "min": 0,
            "max": 100,
            "~create_time": "2022-05-13 13:47:23.745"
        }
    },
    "task_id": 0
}
```

#### 1.2.3 Get all PropertyKeys

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/propertykeys
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "propertykeys": [
        {
            "id": 3,
            "name": "city",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "properties": [],
            "user_data": {}
        },
        {
            "id": 2,
            "name": "age",
            "data_type": "INT",
            "cardinality": "SINGLE",
            "properties": [],
            "user_data": {}
        },
        {
            "id": 5,
            "name": "lang",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "properties": [],
            "user_data": {}
        },
        {
            "id": 4,
            "name": "weight",
            "data_type": "DOUBLE",
            "cardinality": "SINGLE",
            "properties": [],
            "user_data": {}
        },
        {
            "id": 6,
            "name": "date",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "properties": [],
            "user_data": {}
        },
        {
            "id": 1,
            "name": "name",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "properties": [],
            "user_data": {}
        },
        {
            "id": 7,
            "name": "price",
            "data_type": "INT",
            "cardinality": "SINGLE",
            "properties": [],
            "user_data": {}
        }
    ]
}
```

#### 1.2.4 Get PropertyKey according to name

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/propertykeys/age
```

Where `age` is the name of the PropertyKey to be retrieved.

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": 1,
    "name": "age",
    "data_type": "INT",
    "cardinality": "SINGLE",
    "aggregate_type": "NONE",
    "write_type": "OLTP",
    "properties": [],
    "status": "CREATED",
    "user_data": {
        "min": 0,
        "max": 100,
        "~create_time": "2022-05-13 13:47:23.745"
    }
}
```

#### 1.2.5 Delete PropertyKey according to name

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/propertykeys/age
```

Where `age` is the name of the PropertyKey to be deleted.

##### Response Status

```json
202
```

##### Response Body

```json
{
    "task_id" : 0
}
```
