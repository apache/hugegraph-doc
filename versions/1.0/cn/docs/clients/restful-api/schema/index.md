# Schema API

LLMS 索引： [llms.txt](/versions/1.0/cn/llms.txt)

---

### 1.1 Schema

HugeGraph 提供单一接口获取某个图的全部 Schema 信息，包括：PropertyKey、VertexLabel、EdgeLabel 和 IndexLabel。

##### Method & Url

```
GET http://localhost:8080/graphs/hugegraph/schema
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
            "data_type": "INT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:40.741"
            }
        },
        {
            "id": 6,
            "name": "date",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:40.729"
            }
        },
        {
            "id": 3,
            "name": "city",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:40.691"
            }
        },
        {
            "id": 2,
            "name": "age",
            "data_type": "INT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:40.678"
            }
        },
        {
            "id": 5,
            "name": "lang",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:40.718"
            }
        },
        {
            "id": 4,
            "name": "weight",
            "data_type": "DOUBLE",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:40.707"
            }
        },
        {
            "id": 1,
            "name": "name",
            "data_type": "TEXT",
            "cardinality": "SINGLE",
            "aggregate_type": "NONE",
            "write_type": "OLTP",
            "properties": [
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:40.609"
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
                "age"
            ],
            "index_labels": [
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
                "~create_time": "2021-09-03 15:13:40.783"
            }
        },
        {
            "id": 2,
            "name": "software",
            "id_strategy": "PRIMARY_KEY",
            "primary_keys": [
                "name"
            ],
            "nullable_keys": [
                "price"
            ],
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
                "~create_time": "2021-09-03 15:13:40.840"
            }
        }
    ],
    "edgelabels": [
        {
            "id": 1,
            "name": "knows",
            "source_label": "person",
            "target_label": "person",
            "frequency": "MULTIPLE",
            "sort_keys": [
                "date"
            ],
            "nullable_keys": [
                "weight"
            ],
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
                "~create_time": "2021-09-03 15:13:41.840"
            }
        },
        {
            "id": 2,
            "name": "created",
            "source_label": "person",
            "target_label": "software",
            "frequency": "SINGLE",
            "sort_keys": [
            ],
            "nullable_keys": [
                "weight"
            ],
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
                "~create_time": "2021-09-03 15:13:41.868"
            }
        }
    ],
    "indexlabels": [
        {
            "id": 1,
            "name": "personByCity",
            "base_type": "VERTEX_LABEL",
            "base_value": "person",
            "index_type": "SECONDARY",
            "fields": [
                "city"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:40.886"
            }
        },
        {
            "id": 4,
            "name": "createdByDate",
            "base_type": "EDGE_LABEL",
            "base_value": "created",
            "index_type": "SECONDARY",
            "fields": [
                "date"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:41.878"
            }
        },
        {
            "id": 5,
            "name": "createdByWeight",
            "base_type": "EDGE_LABEL",
            "base_value": "created",
            "index_type": "RANGE_DOUBLE",
            "fields": [
                "weight"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:42.117"
            }
        },
        {
            "id": 2,
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
                "~create_time": "2021-09-03 15:13:41.351"
            }
        },
        {
            "id": 3,
            "name": "softwareByPrice",
            "base_type": "VERTEX_LABEL",
            "base_value": "software",
            "index_type": "RANGE_INT",
            "fields": [
                "price"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:41.587"
            }
        },
        {
            "id": 6,
            "name": "knowsByWeight",
            "base_type": "EDGE_LABEL",
            "base_value": "knows",
            "index_type": "RANGE_DOUBLE",
            "fields": [
                "weight"
            ],
            "status": "CREATED",
            "user_data": {
                "~create_time": "2021-09-03 15:13:42.376"
            }
        }
    ]
}
```
