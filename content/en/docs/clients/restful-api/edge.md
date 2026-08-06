---
title: "Edge API"
linkTitle: "Edge"
weight: 8
description: "Edge REST API: Create, query, update, and delete relationship data between vertices with support for batch operations and directional queries."
---

### 2.2 Edge

The modification of the vertex ID format also affects the ID of the edge, as well as the formats of the source vertex and target vertex IDs.

The EdgeId is formed by concatenating `src-vertex-id + direction + label + sort-values + tgt-vertex-id`, but the vertex ID types are not distinguished by quotation marks here. Instead, they are distinguished by prefixes:

- When the ID type is number, the vertex ID in the EdgeId has a prefix `L`, like "L123456>1>>L987654".
- When the ID type is string, the vertex ID in the EdgeId has a prefix `S`, like "S1:peter>1>>S2:lop".

--------------------------------------------------------------------------------

The following example requires creating a graph `schema` based on the following `groovy` script:

```groovy
import org.apache.hugegraph.HugeFactory
import org.apache.tinkerpop.gremlin.structure.T

conf = "conf/graphs/hugegraph.properties"
graph = HugeFactory.open(conf)
schema = graph.schema()

schema.propertyKey("name").asText().ifNotExist().create()
schema.propertyKey("age").asInt().ifNotExist().create()
schema.propertyKey("city").asText().ifNotExist().create()
schema.propertyKey("weight").asDouble().ifNotExist().create()
schema.propertyKey("lang").asText().ifNotExist().create()
schema.propertyKey("date").asText().ifNotExist().create()
schema.propertyKey("price").asInt().ifNotExist().create()

schema.vertexLabel("person").properties("name", "age", "city").primaryKeys("name").ifNotExist().create()
schema.vertexLabel("software").properties("name", "lang", "price").primaryKeys("name").ifNotExist().create()
schema.indexLabel("personByCity").onV("person").by("city").secondary().ifNotExist().create()
schema.indexLabel("personByAgeAndCity").onV("person").by("age", "city").secondary().ifNotExist().create()
schema.indexLabel("softwareByPrice").onV("software").by("price").range().ifNotExist().create()
schema.edgeLabel("knows").sourceLabel("person").targetLabel("person").properties("date", "weight").ifNotExist().create()
schema.edgeLabel("created").sourceLabel("person").targetLabel("software").properties("date", "weight").ifNotExist().create()
schema.indexLabel("createdByDate").onE("created").by("date").secondary().ifNotExist().create()
schema.indexLabel("createdByWeight").onE("created").by("weight").range().ifNotExist().create()
schema.indexLabel("knowsByWeight").onE("knows").by("weight").range().ifNotExist().create()

marko = graph.addVertex(T.label, "person", "name", "marko", "age", 29, "city", "Beijing")
vadas = graph.addVertex(T.label, "person", "name", "vadas", "age", 27, "city", "Hongkong")
lop = graph.addVertex(T.label, "software", "name", "lop", "lang", "java", "price", 328)
josh = graph.addVertex(T.label, "person", "name", "josh", "age", 32, "city", "Beijing")
ripple = graph.addVertex(T.label, "software", "name", "ripple", "lang", "java", "price", 199)
peter = graph.addVertex(T.label, "person", "name", "peter", "age", 35, "city", "Shanghai")

graph.tx().commit()
g = graph.traversal()
```

#### 2.2.1 Creating an Edge

##### Params

**Path Parameter Description:**

- graph: The graph to operate on

**Request Body Description:**

- label: The edge type name (required)
- outV: The source vertex id (required)
- inV: The target vertex id (required)
- outVLabel: The source vertex type (required)
- inVLabel: The target vertex type (required)
- properties: The properties associated with the edge. The internal structure of the object is as follows:
  1. name: The property name
  2. value: The property value

##### Method & Url

```http
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges
```

##### Request Body

```json
{
    "label": "created",
    "outV": "1:marko",
    "inV": "2:lop",
    "outVLabel": "person",
    "inVLabel": "software",
    "properties": {
        "date": "20171210",
        "weight": 0.4
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
    "id": "S1:marko>2>>S2:lop",
    "label": "created",
    "type": "edge",
    "outV": "1:marko",
    "outVLabel": "person",
    "inV": "2:lop",
    "inVLabel": "software",
    "properties": {
        "weight": 0.4,
        "date": "20171210"
    }
}
```

#### 2.2.2 Creating Multiple Edges

##### Params

**Path Parameter Description:**

- graph: The graph to operate on

**Request Parameter Description:**

- check_vertex: Whether to check the existence of vertices (true | false). When set to true, an error will be thrown if the source or target vertices of the edge to be inserted do not exist. Default is true.

**Request Body Description:**

- List of edge information

##### Method & Url

```http
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges/batch
```

##### Request Body

```json
[
    {
        "label": "knows",
        "outV": "1:marko",
        "inV": "1:vadas",
        "outVLabel": "person",
        "inVLabel": "person",
        "properties": {
            "date": "20160110",
            "weight": 0.5
        }
    },
    {
        "label": "knows",
        "outV": "1:marko",
        "inV": "1:josh",
        "outVLabel": "person",
        "inVLabel": "person",
        "properties": {
            "date": "20130220",
            "weight": 1.0
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
    "S1:marko>1>>S1:vadas",
    "S1:marko>1>>S1:josh"
]
```

#### 2.2.3 Updating Edge Properties

##### Params

**Path Parameter Description:**

- graph: The graph to operate on
- id: The ID of the edge to be operated on

**Request Parameter Description:**

- action: The append action

**Request Body Description:**

- Edge information

##### Method & Url

```http
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges/S1:marko>2>>S2:lop?action=append
```

##### Request Body

```json
{
    "properties": {
        "weight": 1.0
    }
}
```

> NOTE: There are three categories of property values: single, set, and list. If it is single, it means adding or updating the property value. If it is set or list, it means appending the property value.

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": "S1:marko>2>>S2:lop",
    "label": "created",
    "type": "edge",
    "outV": "1:marko",
    "outVLabel": "person",
    "inV": "2:lop",
    "inVLabel": "software",
    "properties": {
        "weight": 1.0,
        "date": "20171210"
    }
}
```

#### 2.2.4 Batch Updating Edge Properties

##### Params

**Path Parameter Description:**

- graph: The graph to operate on

**Request Body Description:**

- edges: List of edge information
- update_strategies: For each property, you can set its update strategy individually, including:
  - SUM: Only supports number type
  - BIGGER/SMALLER: Only supports date/number type
  - UNION/INTERSECTION: Only supports set type
  - APPEND/ELIMINATE: Only supports collection type
  - OVERRIDE
- check_vertex: Whether to check the existence of vertices (true | false). When set to true, an error will be thrown if the source or target vertices of the edge to be inserted do not exist. Default is true.
- create_if_not_exist: Currently only supports setting to true

##### Method & Url

```http
PUT http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges/batch
```

##### Request Body

```json
{
    "edges": [
        {
            "label": "knows",
            "outV": "1:marko",
            "inV": "1:vadas",
            "outVLabel": "person",
            "inVLabel": "person",
            "properties": {
                "date": "20160111",
                "weight": 1.0
            }
        },
        {
            "label": "knows",
            "outV": "1:marko",
            "inV": "1:josh",
            "outVLabel": "person",
            "inVLabel": "person",
            "properties": {
                "date": "20130221",
                "weight": 0.5
            }
        }
    ],
    "update_strategies": {
        "weight": "SUM",
        "date": "OVERRIDE"
    },
    "check_vertex": false,
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
    "edges": [
        {
            "id": "S1:marko>1>>S1:vadas",
            "label": "knows",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "1:vadas",
            "inVLabel": "person",
            "properties": {
                "weight": 1.5,
                "date": "20160111"
            }
        },
        {
            "id": "S1:marko>1>>S1:josh",
            "label": "knows",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "1:josh",
            "inVLabel": "person",
            "properties": {
                "weight": 1.5,
                "date": "20130221"
            }
        }
    ]
}
```

#### 2.2.5 Deleting Edge Properties

##### Params

**Path Parameter Description:**

- graph: The graph to operate on
- id: The ID of the edge to be operated on

**Request Parameter Description:**

- action: The eliminate action

**Request Body Description:**

- Edge information

##### Method & Url

```http
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges/S1:marko>2>>S2:lop?action=eliminate
```

##### Request Body

```json
{
    "properties": {
        "weight": 1.0
    }
}
```

> NOTE: This will directly delete the properties (removing the key and all values), regardless of whether the property values are single, set, or list.

##### Response Status

```json
400
```

##### Response Body

It is not possible to delete an attribute that is not set as nullable.

```json
{
    "exception": "class java.lang.IllegalArgumentException",
    "message": "Can't remove non-null edge property 'p[weight->1.0]'",
    "cause": ""
}
```

#### 2.2.6 Fetching Edges that Match the Criteria

##### Params

**Path Parameter:**

- graph: The graph to operate on

**Request Parameters:**

- vertex_id: Vertex ID
- direction: Edge direction (OUT | IN | BOTH), default is BOTH
- label: Edge label
- properties: Key-value pairs of properties (requires pre-built indexes for property queries)
- keep_start_p: Default is false. When set to true, the range matching input expression will not be automatically escaped. For example, `properties={"age":"P.gt(0.8)"}` will be interpreted as an exact match, i.e., the age property is equal to "P.gt(0.8)"
- offset: Offset, default is 0
- limit: Number of queries, default is 100
- page: Page number

Key-value pairs of properties consist of the property name and value in JSON format. Multiple key-value pairs are allowed as query conditions. Property values support exact matching and range matching. For exact matching, it is in the form `properties={"weight":0.8}`. For range matching, it is in the form `properties={"age":"P.gt(0.8)"}`. The expressions supported by range matching are as follows:

| Expression                         | Description                                                                      |
|------------------------------------|----------------------------------------------------------------------------------|
| P.eq(number)                       | Edges with property value equal to number                                        |
| P.neq(number)                      | Edges with property value not equal to number                                    |
| P.lt(number)                       | Edges with property value less than number                                       |
| P.lte(number)                      | Edges with property value less than or equal to number                           |
| P.gt(number)                       | Edges with property value greater than number                                    |
| P.gte(number)                      | Edges with property value greater than or equal to number                        |
| P.between(number1,number2)         | Edges with property value greater than or equal to number1 and less than number2 |
| P.inside(number1,number2)          | Edges with property value greater than number1 and less than number2             |
| P.outside(number1,number2)         | Edges with property value less than number1 and greater than number2             |
| P.within(value1,value2,value3,...) | Edges with property value equal to any of the given values                       |
| P.textcontains(value)              | Edges with property value containing the given value (string type)               |
| P.contains(value)                  | Edges with property value containing the given value (collection type)           |

**Edges connected to the vertex person:marko(vertex_id="1:marko") with label knows and date property equal to "20160111"**

##### Method & Url

```http
GET http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges?vertex_id="1:marko"&label=knows&properties={"date":"P.within(\"20160111\")"}
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "edges": [
        {
            "id": "S1:marko>1>>S1:vadas",
            "label": "knows",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "1:vadas",
            "inVLabel": "person",
            "properties": {
                "weight": 1.5,
                "date": "20160111"
            }
        }
    ]
}
```

**Paginate and retrieve all edges, get the first page (page without parameter value), limit to 2 entries**

##### Method & Url

```http
GET http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges?page&limit=2
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "edges": [
        {
            "id": "S1:marko>1>>S1:josh",
            "label": "knows",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "1:josh",
            "inVLabel": "person",
            "properties": {
                "weight": 1.5,
                "date": "20130221"
            }
        },
        {
            "id": "S1:marko>1>>S1:vadas",
            "label": "knows",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "1:vadas",
            "inVLabel": "person",
            "properties": {
                "weight": 1.5,
                "date": "20160111"
            }
        }
    ],
    "page": "EoYxOm1hcmtvgggCAIQyOmxvcAAAAAAAAAAC"
}
```

The returned body contains the page number information for the next page, `"page": "EoYxOm1hcmtvgggCAIQyOmxvcAAAAAAAAAAC"`. When querying the next page, assign this value to the page parameter.

**Paginate and retrieve all edges, get the next page (include the page value returned from the previous page), limit to 2 entries**

##### Method & Url

```http
GET http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges?page=EoYxOm1hcmtvgggCAIQyOmxvcAAAAAAAAAAC&limit=2
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "edges": [
        {
            "id": "S1:marko>2>>S2:lop",
            "label": "created",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "2:lop",
            "inVLabel": "software",
            "properties": {
                "weight": 1.0,
                "date": "20171210"
            }
        }
    ],
    "page": null
}
```

When `"page": null` is returned, it indicates that there are no more pages available.

> NOTE: When the backend is Cassandra, for performance considerations, if the returned page happens to be the last page, the `page` value may not be empty. When requesting the next page data using that `page` value, it will return `empty data` and `page = null`. Similar situations apply for other cases.

#### 2.2.7 Fetching Edge by ID

##### Params

**Path parameter description:**

- graph: The graph to be operated on.
- id: The ID of the edge to be operated on.

##### Method & Url

```http
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges/S1:marko>2>>S2:lop
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "id": "S1:marko>2>>S2:lop",
    "label": "created",
    "type": "edge",
    "outV": "1:marko",
    "outVLabel": "person",
    "inV": "2:lop",
    "inVLabel": "software",
    "properties": {
        "weight": 1.0,
        "date": "20171210"
    }
}
```

#### 2.2.8 Deleting Edge by ID

##### Params

**Path parameter description:**

- graph: The graph to be operated on.
- id: The ID of the edge to be operated on.

**Request parameter description:**

- label: The label of the edge.

**Deleting Edge by ID only**

##### Method & Url

```http
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges/S1:marko>2>>S2:lop
```

##### Response Status

```json
204
```

**Deleting Edge by Label + ID**

In general, specifying the Label parameter along with the ID to delete an edge will provide better performance compared to deleting by ID only.

##### Method & Url

```http
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges/S1:marko>1>>S1:vadas?label=knows
```

##### Response Status

```json
204
```
