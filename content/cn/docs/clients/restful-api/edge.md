---
title: "Edge API"
linkTitle: "Edge"
weight: 8
description: "Edge（边）REST 接口:创建、查询、更新和删除顶点之间的关系数据,支持批量操作和方向查询。"
---

### 2.2 Edge

顶点 id 格式的修改也影响到了边的 id 以及源顶点和目标顶点 id 的格式

EdgeId 是由 `src-vertex-id + direction + label + sort-values + tgt-vertex-id` 拼接而成，但是这里的顶点 id 类型不是通过引号区分的，而是根据前缀区分：

- 当 id 类型为 number 时，EdgeId 的顶点 id 前有一个前缀 `L` ，形如 "L123456>1>>L987654"
- 当 id 类型为 string 时，EdgeId 的顶点 id 前有一个前缀 `S` ，形如 "S1:peter>1>>S2:lop"

--------------------------------------------------------------------------------

接下来的示例需要先根据以下 `groovy` 脚本创建图 `schema`

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

#### 2.2.1 创建一条边

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph：待操作的图

**请求体说明：**

- label：边类型名称，必填
- outV：源顶点 id，必填
- inV：目标顶点 id，必填
- outVLabel：源顶点类型，必填
- inVLabel：目标顶点类型，必填
- properties: 边关联的属性，对象内部结构为：
  1. name：属性名称
  2. value：属性值

##### Method & Url

```bash
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

#### 2.2.2 创建多条边

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph：待操作的图

**请求参数说明：**

- check_vertex：是否检查顶点存在 (true | false)，当设置为 true 而待插入边的源顶点或目标顶点不存在时会报错，默认为 true

**请求体说明：**

- 边信息的列表

##### Method & Url

```bash
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

#### 2.2.3 更新边属性

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph：待操作的图
- id：待操作的边 id

**请求参数说明：**

- action：append 操作

**请求体说明：**

- 边信息

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

> 注意：属性的取值是有三种类别的，分别是 single、set 和 list。如果是 single，表示增加或更新属性值；如果是 set 或 list，则表示追加属性值

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

#### 2.2.4 批量更新边属性

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph：待操作的图

**请求体说明：**

- edges：边信息的列表
- update_strategies：对于每个属性，可以单独设置其更新策略，包括：
  - SUM：仅支持 number 类型
  - BIGGER/SMALLER：仅支持 date/number 类型
  - UNION/INTERSECTION：仅支持 set 类型
  - APPEND/ELIMINATE：仅支持 collection 类型
  - OVERRIDE
- check_vertex：是否检查顶点存在 (true | false)，当设置为 true 而待插入边的源顶点或目标顶点不存在时会报错，默认为 true
- create_if_not_exist：目前只支持设定为 true

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

#### 2.2.5 删除边属性

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph：待操作的图
- id：待操作的边 id

**请求参数说明：**

- action：eliminate 操作

**请求体说明：**

- 边信息

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

> 注意：这里会直接删除属性（删除 key 和所有 value），无论其属性的取值是 single、set 或 list

##### Response Status

```json
400
```

##### Response Body

无法删除未设置为 nullable 的属性

```json
{
    "exception": "class java.lang.IllegalArgumentException",
    "message": "Can't remove non-null edge property 'p[weight->1.0]'",
    "cause": ""
}
```

#### 2.2.6 获取符合条件的边

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph：待操作的图

**请求参数说明：**

- vertex_id: 顶点 id
- direction: 边的方向 (OUT | IN | BOTH)，默认为 BOTH
- label: 边的标签
- properties: 属性键值对 (根据属性查询的前提是预先建立了索引)
- keep_start_p: 默认为 false，当设置为 true 后，不会自动转义范围匹配输入的表达式，例如此时 `properties={"age":"P.gt(0.8)"}` 会被理解为精确匹配，即 age 属性等于 "P.gt(0.8)"
- offset：偏移，默认为 0
- limit: 查询数目，默认为 100
- page: 页号

属性键值对由 JSON 格式的属性名称和属性值组成，允许多个属性键值对作为查询条件，属性值支持精确匹配和范围匹配，精确匹配时形如 `properties={"weight":0.8}`，范围匹配时形如 `properties={"age":"P.gt(0.8)"}`，范围匹配支持的表达式如下：

| 表达式                                | 说明                               |
|------------------------------------|----------------------------------|
| P.eq(number)                       | 属性值等于 number 的边                  |
| P.neq(number)                      | 属性值不等于 number 的边                 |
| P.lt(number)                       | 属性值小于 number 的边                  |
| P.lte(number)                      | 属性值小于等于 number 的边                |
| P.gt(number)                       | 属性值大于 number 的边                  |
| P.gte(number)                      | 属性值大于等于 number 的边                |
| P.between(number1,number2)         | 属性值大于等于 number1 且小于 number2 的边   |
| P.inside(number1,number2)          | 属性值大于 number1 且小于 number2 的边     |
| P.outside(number1,number2)         | 属性值小于 number1 且大于 number2 的边     |
| P.within(value1,value2,value3,...) | 属性值等于任何一个给定 value 的边             |
| P.textcontains(value)              | 属性值包含给定 value 的边 (string 类型)     |
| P.contains(value)                  | 属性值包含给定 value 的边 (collection 类型) |

**查询与顶点 person:marko(vertex_id="1:marko") 相连且 label 为 knows 的且 date 属性等于 "20160111" 的边**

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

**分页查询所有边，获取第一页（page 不带参数值），限定 2 条**

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

返回的 body 里面是带有下一页的页号信息的，`"page": "EoYxOm1hcmtvgggCAIQyOmxvcAAAAAAAAAAC"`，在查询下一页的时候将该值赋给 page 参数

**分页查询所有边，获取下一页（page 带上上一页返回的 page 值），限定 2 条**

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

此时 `"page": null` 表示已经没有下一页了

> 注：后端为 Cassandra 时，为了性能考虑，返回页恰好为最后一页时，返回 `page` 值可能非空，通过该 `page` 再请求下一页数据时则返回 `空数据` 及 `page = null`，其他情况类似

#### 2.2.7 根据 id 获取边

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph：待操作的图
- id：待操作的边 id

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

#### 2.2.8 根据 id 删除边

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph：待操作的图
- id：待操作的边 id

**请求参数说明：**

- label: 边的标签

**仅根据 id 删除边**

##### Method & Url

```http
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges/S1:marko>2>>S2:lop
```

##### Response Status

```json
204
```

**根据 label + id 删除边**

通过指定 label 参数和 id 来删除边时，一般来说其性能比仅根据 id 删除会更好

##### Method & Url

```http
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/edges/S1:marko>1>>S1:vadas?label=knows
```

##### Response Status

```json
204
```
