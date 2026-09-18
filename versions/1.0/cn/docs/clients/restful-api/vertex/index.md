# Vertex API

LLMS 索引： [llms.txt](/versions/1.0/cn/llms.txt)

---

### 2.1 Vertex

顶点类型中的 Id 策略决定了顶点的 Id 类型，其对应关系如下：

| Id_Strategy      | id type |
|------------------|---------|
| AUTOMATIC        | number  |
| PRIMARY_KEY      | string  |
| CUSTOMIZE_STRING | string  |
| CUSTOMIZE_NUMBER | number  |
| CUSTOMIZE_UUID   | uuid    |

顶点的 `GET/PUT/DELETE` API 中 url 的 id 部分传入的应是带有类型信息的 id 值，这个类型信息用 json 串是否带引号表示，也就是说：

- 当 id 类型为 number 时，url 中的 id 不带引号，形如 xxx/vertices/123456
- 当 id 类型为 string 时，url 中的 id 带引号，形如 xxx/vertices/"123456"

-------------------------------------------------------------------

接下来的示例均假设已经创建好了前述的各种 schema 信息

#### 2.1.1 创建一个顶点

##### Method & Url

```
POST http://localhost:8080/graphs/hugegraph/graph/vertices
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
        "name": [
            {
                "id": "1:marko>name",
                "value": "marko"
            }
        ],
        "age": [
            {
                "id": "1:marko>age",
                "value": 29
            }
        ]
    }
}
```

#### 2.1.2 创建多个顶点

##### Method & Url

```
POST http://localhost:8080/graphs/hugegraph/graph/vertices/batch
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

##### Method & Url

```
PUT http://127.0.0.1:8080/graphs/hugegraph/graph/vertices/"1:marko"?action=append
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

> 注意：属性的取值是有三种类别的，分别是single、set和list。如果是single，表示增加或更新属性值；如果是set或list，则表示追加属性值。

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
        "city": [
            {
                "id": "1:marko>city",
                "value": "Beijing"
            }
        ],
        "name": [
            {
                "id": "1:marko>name",
                "value": "marko"
            }
        ],
        "age": [
            {
                "id": "1:marko>age",
                "value": 30
            }
        ]
    }
}
```

#### 2.1.4 批量更新顶点属性

##### 功能说明

批量更新顶点的属性，并支持多种更新策略，包括

- SUM: 数值累加
- BIGGER: 两个数字/日期取更大的
- SMALLER: 两个数字/日期取更小的
- UNION: Set属性取并集
- INTERSECTION: Set属性取交集
- APPEND: List属性追加元素
- ELIMINATE: List/Set属性删除元素
- OVERRIDE: 覆盖已有属性，如果新属性为null，则仍然使用旧属性

假设原顶点及属性为：

```json
{
    "vertices":[
        {
            "id":"2:lop",
            "label":"software",
            "type":"vertex",
            "properties":{
                "name":"lop",
                "lang":"java",
                "price":328
            }
        },
        {
            "id":"1:josh",
            "label":"person",
            "type":"vertex",
            "properties":{
                "name":"josh",
                "age":32,
                "city":"Beijing",
                "weight":0.1,
                "hobby":[
                    "reading",
                    "football"
                ]
            }
        }
    ]
}
```

##### Method & Url

```
PUT http://127.0.0.1:8080/graphs/hugegraph/graph/vertices/batch
```

##### Request Body

```json
{
    "vertices":[
        {
            "label":"software",
            "type":"vertex",
            "properties":{
                "name":"lop",
                "lang":"c++",
                "price":299
            }
        },
        {
            "label":"person",
            "type":"vertex",
            "properties":{
                "name":"josh",
                "city":"Shanghai",
                "weight":0.2,
                "hobby":[
                    "swiming"
                ]
            }
        }
    ],
    "update_strategies":{
        "price":"BIGGER",
        "age":"OVERRIDE",
        "city":"OVERRIDE",
        "weight":"SUM",
        "hobby":"UNION"
    },
    "create_if_not_exist":true
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
                    "swiming",
                    "reading",
                    "football"
                ]
            }
        }
    ]
}
```

结果分析：

- lang 属性未指定更新策略，直接用新值覆盖旧值，无论新值是否为null；
- price 属性指定 BIGGER 的更新策略，旧属性值为328，新属性值为299，所以仍然保留了旧属性值328；
- age 属性指定 OVERRIDE 更新策略，而新属性值中未传入age，相当于age为null，所以仍然保留了原属性值32；
- city 属性也指定了 OVERRIDE 更新策略，且新属性值不为null，所以覆盖了旧值；
- weight 属性指定了 SUM 更新策略，旧属性值为0.1，新属性值为0.2，最后的值为0.3；
- hobby 属性（基数为Set）指定了 UNION 更新策略，所以新值与旧值取了并集；

其他的更新策略使用方式可以类推，不再赘述。

#### 2.1.5 删除顶点属性

##### Method & Url

```
PUT http://127.0.0.1:8080/graphs/hugegraph/graph/vertices/"1:marko"?action=eliminate
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

> 注意：这里会直接删除属性（删除key和所有value），无论其属性的取值是single、set或list。

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
        "name": [
            {
                "id": "1:marko>name",
                "value": "marko"
            }
        ],
        "age": [
            {
                "id": "1:marko>age",
                "value": 30
            }
        ]
    }
}
```

#### 2.1.6 获取符合条件的顶点

##### Params

- label: 顶点类型
- properties: 属性键值对(根据属性查询的前提是预先建立了索引)
- limit: 查询最大数目
- page: 页号

以上参数都是可选的，如果提供page参数，必须提供limit参数，不允许带其他参数。`label, properties`和`limit`可以任意组合。

属性键值对由JSON格式的属性名称和属性值组成，允许多个属性键值对作为查询条件，属性值支持精确匹配和范围匹配，精确匹配时形如`properties={"age":29}`，范围匹配时形如`properties={"age":"P.gt(29)"}`,范围匹配支持的表达式如下：

| 表达式                                | 说明                          |
|------------------------------------|-----------------------------|
| P.eq(number)                       | 属性值等于number的顶点              |
| P.neq(number)                      | 属性值不等于number的顶点             |
| P.lt(number)                       | 属性值小于number的顶点              |
| P.lte(number)                      | 属性值小于等于number的顶点            |
| P.gt(number)                       | 属性值大于number的顶点              |
| P.gte(number)                      | 属性值大于等于number的顶点            |
| P.between(number1,number2)         | 属性值大于等于number1且小于number2的顶点 |
| P.inside(number1,number2)          | 属性值大于number1且小于number2的顶点   |
| P.outside(number1,number2)         | 属性值小于number1且大于number2的顶点   |
| P.within(value1,value2,value3,...) | 属性值等于任何一个给定value的顶点         |

**查询所有 age 为 20 且 label 为 person 的顶点**

##### Method & Url

```
GET http://localhost:8080/graphs/hugegraph/graph/vertices?label=person&properties={"age":29}&limit=1
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
                "city": [
                    {
                        "id": "1:marko>city",
                        "value": "Beijing"
                    }
                ],
                "name": [
                    {
                        "id": "1:marko>name",
                        "value": "marko"
                    }
                ],
                "age": [
                    {
                        "id": "1:marko>age",
                        "value": 29
                    }
                ]
            }
        }
    ]
}
```

**分页查询所有顶点，获取第一页（page不带参数值），限定3条**

##### Method & Url

```
GET http://localhost:8080/graphs/hugegraph/graph/vertices?page&limit=3
```

##### Response Status

```json
200
```

##### Response Body

```json
{
	"vertices": [{
			"id": "2:ripple",
			"label": "software",
			"type": "vertex",
			"properties": {
				"price": [{
					"id": "2:ripple>price",
					"value": 199
				}],
				"name": [{
					"id": "2:ripple>name",
					"value": "ripple"
				}],
				"lang": [{
					"id": "2:ripple>lang",
					"value": "java"
				}]
			}
		},
		{
			"id": "1:vadas",
			"label": "person",
			"type": "vertex",
			"properties": {
				"city": [{
					"id": "1:vadas>city",
					"value": "Hongkong"
				}],
				"name": [{
					"id": "1:vadas>name",
					"value": "vadas"
				}],
				"age": [{
					"id": "1:vadas>age",
					"value": 27
				}]
			}
		},
		{
			"id": "1:peter",
			"label": "person",
			"type": "vertex",
			"properties": {
				"city": [{
					"id": "1:peter>city",
					"value": "Shanghai"
				}],
				"name": [{
					"id": "1:peter>name",
					"value": "peter"
				}],
				"age": [{
					"id": "1:peter>age",
					"value": 35
				}]
			}
		}
	],
	"page": "001000100853313a706574657200f07ffffffc00e797c6349be736fffc8699e8a502efe10004"
}
```

返回的body里面是带有下一页的页号信息的，`"page": "001000100853313a706574657200f07ffffffc00e797c6349be736fffc8699e8a502efe10004"`，
在查询下一页的时候将该值赋给page参数。

**分页查询所有顶点，获取下一页（page带上上一页返回的page值），限定3条**

##### Method & Url

```
GET http://localhost:8080/graphs/hugegraph/graph/vertices?page=001000100853313a706574657200f07ffffffc00e797c6349be736fffc8699e8a502efe10004&limit=3
```

##### Response Status

```json
200
```

##### Response Body

```json
{
	"vertices": [{
			"id": "1:josh",
			"label": "person",
			"type": "vertex",
			"properties": {
				"city": [{
					"id": "1:josh>city",
					"value": "Beijing"
				}],
				"name": [{
					"id": "1:josh>name",
					"value": "josh"
				}],
				"age": [{
					"id": "1:josh>age",
					"value": 32
				}]
			}
		},
		{
			"id": "1:marko",
			"label": "person",
			"type": "vertex",
			"properties": {
				"city": [{
					"id": "1:marko>city",
					"value": "Beijing"
				}],
				"name": [{
					"id": "1:marko>name",
					"value": "marko"
				}],
				"age": [{
					"id": "1:marko>age",
					"value": 29
				}]
			}
		},
		{
			"id": "2:lop",
			"label": "software",
			"type": "vertex",
			"properties": {
				"price": [{
					"id": "2:lop>price",
					"value": 328
				}],
				"name": [{
					"id": "2:lop>name",
					"value": "lop"
				}],
				"lang": [{
					"id": "2:lop>lang",
					"value": "java"
				}]
			}
		}
	],
	"page": null
}
```

此时`"page": null`表示已经没有下一页了 (注: 后端为 Cassandra 时，为了性能考虑，返回页恰好为最后一页时，返回 `page` 值可能非空，通过该 `page` 再请求下一页数据时则返回 `空数据` 及 `page = null`，其他情况类似)

#### 2.1.7 根据Id获取顶点

##### Method & Url

```
GET http://localhost:8080/graphs/hugegraph/graph/vertices/"1:marko"
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
        "name": [
            {
                "id": "1:marko>name",
                "value": "marko"
            }
        ],
        "age": [
            {
                "id": "1:marko>age",
                "value": 29
            }
        ]
    }
}
```

#### 2.1.8 根据Id删除顶点

##### Params

- label: 顶点类型，可选参数

**仅根据Id删除顶点**

##### Method & Url

```
DELETE http://localhost:8080/graphs/hugegraph/graph/vertices/"1:marko"
```

##### Response Status

```json
204
```

**根据Label+Id删除顶点**

通过指定Label参数和Id来删除顶点时，一般来说其性能比仅根据Id删除会更好。

##### Method & Url

```
DELETE http://localhost:8080/graphs/hugegraph/graph/vertices/"1:marko"?label=person
```

##### Response Status
```json
204
```
