---
title: "Vertex API"
linkTitle: "Vertex"
weight: 7
description: "Vertex（顶点）REST 接口:创建、查询、更新和删除图中的顶点数据,支持批量操作和条件过滤。"
---

### 2.1 Vertex

顶点类型中的 `Id` 策略决定了顶点的 `Id` 类型，其对应的 `id` 类型如下：

| Id_Strategy      | id type |
|------------------|---------|
| AUTOMATIC        | number  |
| PRIMARY_KEY      | string  |
| CUSTOMIZE_STRING | string  |
| CUSTOMIZE_NUMBER | number  |
| CUSTOMIZE_UUID   | uuid    |

顶点的 `GET/PUT/DELETE` API 中 url 的 id 部分应该传入带有类型信息的 id 值，这个类型信息通过 json 串是否带引号来表示，也就是说：

- 当 id 类型为 `number` 时，url 中的 id 不带引号，例如 `xxx/vertices/123456`
- 当 id 类型为 `string` 时，url 中的 id 带引号，例如 `xxx/vertices/"123456"`

-------------------------------------------------------------------

接下来的示例需要先根据以下 `groovy` 脚本创建图 `schema`

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

#### 2.1.1 创建一个顶点

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

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

#### 2.1.2 创建多个顶点

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

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

#### 2.1.3 更新顶点属性

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称
- id: 顶点 id，需要包含引号，例如"1:marko"

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

> 注意：属性的取值有三种类别，分别为 single、set 和 list。single 表示增加或更新属性值，set 或 list 表示追加属性值。

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

#### 2.1.4 批量更新顶点属性

##### 功能说明

批量更新顶点的属性时，可以选择多种更新策略，如下：

- SUM: 数值累加
- BIGGER: 原值和新值 (数字、日期) 取更大的
- SMALLER: 原值和新值 (数字、日期) 取更小的
- UNION: Set 属性取并集
- INTERSECTION: Set 属性取交集
- APPEND: List 属性追加元素
- ELIMINATE: List/Set属性删除元素
- OVERRIDE: 覆盖已有属性，如果新属性为 null，则仍然使用旧属性

假设原顶点的属性如下：

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

通过以下命令新增顶点：

```shell
curl -H "Content-Type: application/json" -d '[{"label":"person","properties":{"name":"josh","age":32,"city":"Beijing","weight":0.1,"hobby":["reading","football"]}},{"label":"software","properties":{"name":"lop","lang":"java","price":328}}]' http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/batch
```

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

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

结果分析如下：

- lang 属性未指定更新策略，直接用新值覆盖旧值，无论新值是否为 null；
- price 属性指定 BIGGER 的更新策略，旧属性值为 328，新属性值为 299，所以仍然保留了旧属性值 328；
- age 属性指定 OVERRIDE 更新策略，而新属性值中未传入 age，相当于 age 为 null，所以仍然保留了原属性值 32；
- city 属性也指定了 OVERRIDE 更新策略，且新属性值不为 null，所以覆盖了旧值；
- weight 属性指定了 SUM 更新策略，旧属性值为 0.1，新属性值为 0.2，最后的值为 0.3；
- hobby 属性（基数为 Set）指定了 UNION 更新策略，所以新值与旧值取了并集；

其他更新策略的使用方式与此类似，此处不再详述。

#### 2.1.5 删除顶点属性

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称
- id: 顶点 id，需要包含引号，例如"1:marko"

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

> 注意：这里会直接删除属性（删除 key 和所有 value），无论其属性的取值是 single、set 或 list。

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

#### 2.1.6 获取符合条件的顶点

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称

**请求参数说明：**

- label: 顶点的类型
- properties: 属性键值对（查询属性的前提是该属性已经建立了索引）
- limit: 查询结果的最大数目
- page: 分页的页号

以上参数都是可选的，但如果提供了 page 参数，就必须同时提供 limit 参数，并且不能再提供其他参数。`label, properties`和`limit`之间可以任意组合。

属性键值对由属性名称和属性值组成 JSON 格式的对象，可以使用多个属性键值对作为查询条件，属性值支持精确匹配和范围匹配，精确匹配的形式如`properties={"age":29}`，范围匹配的形式如`properties={"age":"P.gt(29)"}`，范围匹配支持以下表达式：

| 表达式                                | 说明                              |
|------------------------------------|---------------------------------|
| P.eq(number)                       | 属性值等于 number 的顶点                |
| P.neq(number)                      | 属性值不等于 number 的顶点               |
| P.lt(number)                       | 属性值小于 number 的顶点                |
| P.lte(number)                      | 属性值小于等于 number 的顶点              |
| P.gt(number)                       | 属性值大于 number 的顶点                |
| P.gte(number)                      | 属性值大于等于 number 的顶点              |
| P.between(number1,number2)         | 属性值大于等于 number1 且小于 number2 的顶点 |
| P.inside(number1,number2)          | 属性值大于 number1 且小于 number2 的顶点   |
| P.outside(number1,number2)         | 属性值小于 number1 且大于 number2 的顶点   |
| P.within(value1,value2,value3,...) | 属性值等于任何一个给定 value 的顶点           |

**查询所有 age 为 29 且 label 为 person 的顶点**

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

**分页查询所有顶点，获取第一页（page 不带参数值），限定 3 条**

通过以下命令新增顶点：

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

返回的 `body` 里面是带有下一页的页号信息的，`"page": "CIYxOnBldGVyAAAAAAAAAAM="`，在查询下一页的时候将该值赋给 `page` 参数。

**分页查询所有顶点，获取下一页（page 带上上一页返回的 page 值），限定 3 条**

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

当`"page": null`时，表示已经没有下一页了（注：如果后端使用的是 Cassandra，为了提高性能，当返回的页数刚好是最后一页时，返回的 `page` 值可能不为空，但是如果用这个 `page` 值再请求下一页数据时，就会返回 `空数据` 和 `page = null`，其他情况也类似）

#### 2.1.7 根据 Id 获取顶点

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称
- id: 顶点 id，需要包含引号，例如"1:marko"

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

#### 2.1.8 根据 Id 删除顶点

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称
- id: 顶点 id，需要包含引号，例如"1:marko"

**请求参数说明：**

- label: 顶点类型，可选参数

**仅根据 Id 删除顶点**

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/"1:marko"
```

##### Response Status

```json
204
```

**根据 Label+Id 删除顶点**

通过指定 Label 参数和 Id 来删除顶点时，一般来说其性能比仅根据 Id 删除会更好。

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices/"1:marko"?label=person
```

##### Response Status

```json
204
```
