---
title: "Vertex API"
linkTitle: "Vertex"
weight: 7
description: "Vertex REST API: Create, query, update, and delete vertex data in the graph with support for batch operations and conditional filtering."
---

### 2.1 Vertex

In vertex types, the `Id` strategy determines the type of the vertex `Id`, with the corresponding relationships as follows:

| Id_Strategy      | id type |
|------------------|---------|
| AUTOMATIC        | number  |
| PRIMARY_KEY      | string  |
| CUSTOMIZE_STRING | string  |
| CUSTOMIZE_NUMBER | number  |
| CUSTOMIZE_UUID   | uuid    |

For the `GET/PUT/DELETE` API of a vertex, the id part in the URL should be passed as the id value with type information. This type information is indicated by whether the JSON string is enclosed in quotes, meaning:

- When the id type is `number`, the id in the URL is without quotes, for example: `xxx/vertices/123456`.
- When the id type is `string`, the id in the URL is enclosed in quotes, for example: `xxx/vertices/"123456"`.

-------------------------------------------------------------------

The next example requires first creating the graph `schema` from the following `groovy` script

```groovy
schema.propertyKey("name").asText().ifNotExist().create();
schema.propertyKey("age").asInt().ifNotExist().create();
schema.propertyKey("city").asText().ifNotExist().create();
schema.propertyKey("weight").asDouble().ifNotExist().create();
schema.propertyKey("lang").asText().ifNotExist().create();
schema.propertyKey("price").asDouble().ifNotExist().create();
schema.propertyKey("hobby").asText().valueList().ifNotExist().create();

schema.vertexLabel("person").properties("name", "age", "city", "weight", "hobby").primaryKeys("name").nullableKeys("age", "city", "weight", "hobby").ifNotExist().create();
schema.vertexLabel("software").properties("name", "lang", "price").primaryKeys("name").nullableKeys("lang", "price").ifNotExist().create();

schema.indexLabel("personByAge").onV("person").by("age").range().ifNotExist().create();
```

#### 2.1.1 Create a vertex

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices
```

##### Request Body

```json
{
    "label": "person",
    "properties": {
        "name": "marko",
        "age": 29
    }
}
```

##### Response Status

```json
201
```

##### Response Body

```json
{
    "id": "1:marko",
    "label": "person",
    "type": "vertex",
    "properties": {
        "name": "marko",
        "age": 29
    }
}
```

#### 2.1.2 Create multiple vertices

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/batch
```

##### Request Body

```json
[
    {
        "label": "person",
        "properties": {
            "name": "marko",
            "age": 29
        }
    },
    {
        "label": "software",
        "properties": {
            "name": "ripple",
            "lang": "java",
            "price": 199
        }
    }
]
```

##### Response Status

```json
201
```

##### Response Body

```json
[
    "1:marko",
    "2:ripple"
]
```

#### 2.1.3 Update vertex properties

##### Method & Url

```
PUT http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/"1:marko"?action=append
```

##### Request Body

```json
{
    "label": "person",
    "properties": {
        "age": 30,
        "city": "Beijing"
    }
}
```

> Note: There are three categories for property values: single, set, and list. If it is single, it means adding or updating the property value. If it is set or list, it means appending the property value.

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": "1:marko",
    "label": "person",
    "type": "vertex",
    "properties": {
        "name": "marko",
        "age": 30,
        "city": "Beijing"
    }
}
```

#### 2.1.4 Batch Update Vertex Properties

##### Function Description

Batch update properties of vertices and support various update strategies, including:

- SUM: Numeric accumulation
- BIGGER: Take the larger value between two numbers/dates
- SMALLER: Take the smaller value between two numbers/dates
- UNION: Take the union of set properties
- INTERSECTION: Take the intersection of set properties
- APPEND: Append elements to list properties
- ELIMINATE: Remove elements from list/set properties
- OVERRIDE: Override existing properties, if the new property is null, the old property is still used

Assuming the original vertex and properties are:

```json
{
    "vertices": [
        {
            "id": "2:lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "lop",
                "lang": "java",
                "price": 328
            }
        },
        {
            "id": "1:josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "josh",
                "age": 32,
                "city": "Beijing",
                "weight": 0.1,
                "hobby": [
                    "reading",
                    "football"
                ]
            }
        }
    ]
}
```

Add vertices with the following command:

```shell
curl -H "Content-Type: application/json" -d '[{"label":"person","properties":{"name":"josh","age":32,"city":"Beijing","weight":0.1,"hobby":["reading","football"]}},{"label":"software","properties":{"name":"lop","lang":"java","price":328}}]' http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/batch
```

##### Method & Url

```
PUT http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/batch
```

##### Request Body

```json
{
    "vertices": [
        {
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "lop",
                "lang": "c++",
                "price": 299
            }
        },
        {
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "josh",
                "city": "Shanghai",
                "weight": 0.2,
                "hobby": [
                    "swimming"
                ]
            }
        }
    ],
    "update_strategies": {
        "price": "BIGGER",
        "age": "OVERRIDE",
        "city": "OVERRIDE",
        "weight": "SUM",
        "hobby": "UNION"
    },
    "create_if_not_exist": true
}
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "vertices": [
        {
            "id": "2:lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "lop",
                "lang": "c++",
                "price": 328
            }
        },
        {
            "id": "1:josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "josh",
                "age": 32,
                "city": "Shanghai",
                "weight": 0.3,
                "hobby": [
                    "reading",
                    "football",
                    "swimming"
                ]
            }
        }
    ]
}
```

Result Analysis:

- The lang property does not specify an update strategy and is directly overwritten by the new value, regardless of whether the new value is null.
- The price property specifies the BIGGER update strategy. The old property value is 328, and the new property value is 299, so the old property value of 328 is retained.
- The age property specifies the OVERRIDE update strategy, but the new property value does not include age, which is equivalent to age being null. Therefore, the original property value of 32 is still retained.
- The city property also specifies the OVERRIDE update strategy, and the new property value is not null, so it overrides the old value.
- The weight property specifies the SUM update strategy. The old property value is 0.1, and the new property value is 0.2. The final value is 0.3.
- The hobby property (cardinality is Set) specifies the UNION update strategy, so the new value is taken as the union with the old value.

The usage of other update strategies can be inferred in a similar manner and will not be further elaborated.

#### 2.1.5 Delete Vertex Properties

##### Method & Url

```
PUT http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/"1:marko"?action=eliminate
```

##### Request Body

```json
{
    "label": "person",
    "properties": {
        "city": "Beijing"
    }
}
```

> Note: Here, the properties (keys and all values) will be directly deleted, regardless of whether the property values are single, set, or list.

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": "1:marko",
    "label": "person",
    "type": "vertex",
    "properties": {
        "name": "marko",
        "age": 30
    }
}
```

#### 2.1.6 Get Vertices that Meet the Criteria

##### Params

- label: Vertex type
- properties: Property key-value pairs (precondition: indexes are created for property queries)
- limit: Maximum number of results
- page: Page number

All of the above parameters are optional. If the `page` parameter is provided, the `limit` parameter must also be provided, and no other parameters are allowed. `label, properties`, and `limit` can be combined in any way.

Property key-value pairs consist of the property name and value in JSON format. Multiple property key-value pairs are allowed as query conditions. The property value supports exact matching, range matching, and fuzzy matching. For exact matching, use the format `properties={"age":29}`, for range matching, use the format `properties={"age":"P.gt(29)"}`, and for fuzzy matching, use the format `properties={"city": "P.textcontains("ChengDu China")}`. The following expressions are supported for range matching:

| Expression                        | Explanation                                    |
|------------------------------------|---------------------------------------------|
| P.eq(number)                       | Vertices with property value equal to `number`         |
| P.neq(number)                      | Vertices with property value not equal to `number`     |
| P.lt(number)                       | Vertices with property value less than `number`         |
| P.lte(number)                      | Vertices with property value less than or equal to `number`   |
| P.gt(number)                       | Vertices with property value greater than `number`         |
| P.gte(number)                      | Vertices with property value greater than or equal to `number`   |
| P.between(number1,number2)         | Vertices with property value greater than or equal to `number1` and less than `number2`  |
| P.inside(number1,number2)          | Vertices with property value greater than `number1` and less than `number2`    |
| P.outside(number1,number2)         | Vertices with property value less than `number1` and greater than `number2`    |
| P.within(value1,value2,value3,...) | Vertices with property value equal to any of the given `values`     |

**Query all vertices with age 29 and label person**

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices?label=person&properties={"age":29}&limit=1
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "vertices": [
        {
            "id": "1:marko",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "marko",
                "age": 30
            }
        }
    ]
}
```

**Paginate through all vertices, retrieve the first page (page without parameter value), limited to 3 records**

Add vertices with the following command:

```shell
curl -H "Content-Type: application/json" -d '[{"label":"person","properties":{"name":"peter","age":29,"city":"Shanghai"}},{"label":"person","properties":{"name":"vadas","age":27,"city":"Hongkong"}}]' http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/batch
```

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices?page&limit=3
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "vertices": [
        {
            "id": "2:lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "lop",
                "lang": "c++",
                "price": 328
            }
        },
        {
            "id": "1:josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "josh",
                "age": 32,
                "city": "Shanghai",
                "weight": 0.3,
                "hobby": [
                    "reading",
                    "football",
                    "swimming"
                ]
            }
        },
        {
            "id": "1:marko",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "marko",
                "age": 30
            }
        }
    ],
    "page": "CIYxOnBldGVyAAAAAAAAAAM="
}
```

The returned `body` contains information about the page number of the next `page`, `"page": "CIYxOnBldGVyAAAAAAAAAAM"`. When querying the next page, assign this value to the `page` parameter.

**Paginate and retrieve all vertices, including the next page (passing the `page` value returned from the previous page), limited to 3 items.**

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices?page=CIYxOnBldGVyAAAAAAAAAAM=&limit=3
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "vertices": [
        {
            "id": "1:peter",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "peter",
                "age": 29,
                "city": "Shanghai"
            }
        },
        {
            "id": "1:vadas",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "vadas",
                "age": 27,
                "city": "Hongkong"
            }
        },
        {
            "id": "2:ripple",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "ripple",
                "lang": "java",
                "price": 199
            }
        }
    ],
    "page": null
}
```

At this point, `"page": null` indicates that there are no more pages available. (Note: When using Cassandra as the backend for performance reasons, if the returned page happens to be the last page, the `page` value may not be empty. When requesting the next page using that `page` value, it will return `empty data` and `page = null`. The same applies to other similar situations.)

#### 2.1.7 Retrieve Vertex by ID

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/"1:marko"
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": "1:marko",
    "label": "person",
    "type": "vertex",
    "properties": {
        "name": "marko",
        "age": 30
    }
}
```

#### 2.1.8 Delete Vertex by ID

##### Params

- label: Vertex type, optional parameter

**Delete the vertex based on ID only.**

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/"1:marko"
```

##### Response Status

```json
204
```

**Delete Vertex by Label+ID**

When deleting a vertex by specifying both the Label parameter and the ID, it generally offers better performance compared to deleting by ID alone.

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/"1:marko"?label=person
```

##### Response Status

```json
204
```
