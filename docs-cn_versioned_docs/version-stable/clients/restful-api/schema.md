---
title: "Schema API"
linkTitle: "Schema"
weight: 1
description: "Schema（图模式）REST 接口:查询图的完整模式定义,包括属性键、顶点标签、边标签和索引标签的统一视图。"
---

### 1.1 Schema

HugeGraph 提供单一接口获取某个图的全部 Schema 信息，包括：PropertyKey、VertexLabel、EdgeLabel 和 IndexLabel。

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph_name}/schema

e.g: GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema
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
            "id": 7,
            "name": "price",
            "data_type": "DOUBLE",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.316"
            }
        },
        {
            "id": 6,
            "name": "date",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.309"
            }
        },
        {
            "id": 3,
            "name": "city",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.287"
            }
        },
        {
            "id": 2,
            "name": "age",
            "data_type": "INT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.280"
            }
        },
        {
            "id": 5,
            "name": "lang",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.301"
            }
        },
        {
            "id": 4,
            "name": "weight",
            "data_type": "DOUBLE",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.294"
            }
        },
        {
            "id": 1,
            "name": "name",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.250"
            }
        }
    ],
    "vertexlabels": [
        {
            "id": 1,
            "name": "person",
            "id_strategy": "PRIMARY_KEY",
            "primary_keys": [
                "name"
            ],
            "nullable_keys": [
                "age",
                "city"
            ],
            "index_labels": [
                "personByAge",
                "personByCity",
                "personByAgeAndCity"
            ],
            "properties": [
                "name",
                "age",
                "city"
            ],
            "status": "CREATED",
            "ttl": 0,
            "enable_label_index": true,
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.336"
            }
        },
        {
            "id": 2,
            "name": "software",
            "id_strategy": "CUSTOMIZE_NUMBER",
            "primary_keys": [],
            "nullable_keys": [],
            "index_labels": [
                "softwareByPrice"
            ],
            "properties": [
                "name",
                "lang",
                "price"
            ],
            "status": "CREATED",
            "ttl": 0,
            "enable_label_index": true,
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.347"
            }
        }
    ],
    "edgelabels": [
        {
            "id": 1,
            "name": "knows",
            "source_label": "person",
            "target_label": "person",
            "frequency": "SINGLE",
            "sort_keys": [],
            "nullable_keys": [],
            "index_labels": [
                "knowsByWeight"
            ],
            "properties": [
                "weight",
                "date"
            ],
            "status": "CREATED",
            "ttl": 0,
            "enable_label_index": true,
            "user_data": {
                "~create_time": "2023-05-08 17:49:08.437"
            }
        },
        {
            "id": 2,
            "name": "created",
            "source_label": "person",
            "target_label": "software",
            "frequency": "SINGLE",
            "sort_keys": [],
            "nullable_keys": [],
            "index_labels": [
                "createdByDate",
                "createdByWeight"
            ],
            "properties": [
                "weight",
                "date"
            ],
            "status": "CREATED",
            "ttl": 0,
            "enable_label_index": true,
            "user_data": {
                "~create_time": "2023-05-08 17:49:08.446"
            }
        }
    ],
    "indexlabels": [
        {
            "id": 1,
            "name": "personByAge",
            "base_type": "VERTEX_LABEL",
            "base_value": "person",
            "index_type": "RANGE_INT",
            "fields": [
                "age"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:05.375"
            }
        },
        {
            "id": 2,
            "name": "personByCity",
            "base_type": "VERTEX_LABEL",
            "base_value": "person",
            "index_type": "SECONDARY",
            "fields": [
                "city"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:06.898"
            }
        },
        {
            "id": 3,
            "name": "personByAgeAndCity",
            "base_type": "VERTEX_LABEL",
            "base_value": "person",
            "index_type": "SECONDARY",
            "fields": [
                "age",
                "city"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:07.407"
            }
        },
        {
            "id": 4,
            "name": "softwareByPrice",
            "base_type": "VERTEX_LABEL",
            "base_value": "software",
            "index_type": "RANGE_DOUBLE",
            "fields": [
                "price"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:07.916"
            }
        },
        {
            "id": 5,
            "name": "createdByDate",
            "base_type": "EDGE_LABEL",
            "base_value": "created",
            "index_type": "SECONDARY",
            "fields": [
                "date"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:08.454"
            }
        },
        {
            "id": 6,
            "name": "createdByWeight",
            "base_type": "EDGE_LABEL",
            "base_value": "created",
            "index_type": "RANGE_DOUBLE",
            "fields": [
                "weight"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:08.963"
            }
        },
        {
            "id": 7,
            "name": "knowsByWeight",
            "base_type": "EDGE_LABEL",
            "base_value": "knows",
            "index_type": "RANGE_DOUBLE",
            "fields": [
                "weight"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2023-05-08 17:49:09.473"
            }
        }
    ]
}
```
