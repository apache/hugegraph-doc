---
title: "HugeGraph Java Client"
linkTitle: "HugeGraph Java Client"
weight: 2
---

本文的代码都是`java`语言写的，但其风格与`gremlin(groovy)`是非常类似的。用户只需要把代码中的变量声明替换成`def`或直接去掉，
就能将`java`代码转变为`groovy`；另外就是每一行语句最后可以不加分号，`groovy`认为一行就是一条语句。

用户在`HugeGraph-Hubble`中编写的`gremlin(groovy)`可以参考本文的`java`代码，下面会举出几个例子。

### 1 HugeGraph-Client

HugeGraph-Client 是操作 graph 的总入口，用户必须先创建出 HugeGraph-Client 对象，与 HugeGraph-Server 建立连接（伪连接）后，才能获取到 schema、graph 以及 gremlin 的操作入口对象。

目前 HugeGraph-Client 只允许连接服务端已存在的图，无法自定义图进行创建。1.7.0 版本后，client 支持 graphSpace 设置，默认为DEFAULT。其创建方法如下：

```java
// HugeGraphServer 地址："http://localhost:8080"
// 图的名称："hugegraph"
HugeClient hugeClient = HugeClient.builder("http://localhost:8080", "hugegraph")
                                //.builder("http://localhost:8080", "graphSpaceName", "hugegraph")
                                  .configTimeout(20) // 默认 20s 超时
                                  .configUser("**", "**") // 默认未开启用户权限
                                  .build();
```

上述创建 HugeClient 的过程如果失败会抛出异常，用户需要 try-catch。如果成功则继续获取 schema、graph 以及 gremlin 的 manager。

在`HugeGraph - Hubble`中通过`gremlin`来操作时，不需要使用`HugeClient`，可以忽略。

### 2 元数据

#### 2.1 SchemaManager

SchemaManager 用于管理 HugeGraph 中的四种元数据，分别是 PropertyKey（属性类型）、VertexLabel（顶点类型）、EdgeLabel（边类型）和 IndexLabel（索引标签）。在定义元数据信息之前必须先创建 SchemaManager 对象。

用户可使用如下方法获得 SchemaManager 对象：

```java
SchemaManager schema = hugeClient.schema()
```

在`HugeGraph-Hubble`中通过`gremlin`创建`schema`对象：

```groovy
schema = graph.schema()
```

下面分别对三种元数据的定义过程进行介绍。

#### 2.2 PropertyKey

##### 2.2.1 接口及参数介绍

PropertyKey 用来规范顶点和边的属性的约束，暂不支持定义属性的属性。

PropertyKey 允许定义的约束信息包括：name、datatype、cardinality、userdata，下面逐一介绍。

- name: 属性的名字，用来区分不同的 PropertyKey，不允许有同名的属性；

| interface                | param | must set |
|--------------------------|-------|----------|
| propertyKey(String name) | name  | y        |

- datatype：属性值类型，必须从下表中选择符合具体业务场景的一项显式设置；

| interface   | Java Class |
|-------------|------------|
| asText()    | String     |
| asInt()     | Integer    |
| asDate()    | Date       |
| asUuid()    | UUID       |
| asBoolean() | Boolean    |
| asByte()    | Byte       |
| asBlob()    | Byte[]     |
| asDouble()  | Double     |
| asFloat()   | Float      |
| asLong()    | Long       |

- cardinality：属性值是单值还是多值，多值的情况下又分为允许有重复值和不允许有重复值，该项默认为 single，如有必要可从下表中选择一项设置；

| interface     | cardinality | description                                 |
|---------------|-------------|---------------------------------------------|
| valueSingle() | single      | single value                                |
| valueList()   | list        | multi-values that allow duplicate value     |
| valueSet()    | set         | multi-values that not allow duplicate value |

- userdata：用户可以自己添加一些约束或额外信息，然后自行检查传入的属性是否满足约束，或者必要的时候提取出额外信息

| interface                          | description                                    |
|------------------------------------|------------------------------------------------|
| userdata(String key, Object value) | The same key, the latter will cover the former |

##### 2.2.2 创建 PropertyKey

```java
schema.propertyKey("name").asText().valueSet().ifNotExist().create()
```

在`HugeGraph-Hubble`中通过`gremlin`创建上述`PropertyKey`对象的语法完全一致，如果用户没有定义出`schema`变量，应该这样写：

```groovy
graph.schema().propertyKey("name").asText().valueSet().ifNotExist().create()
```

以下的示例中，`gremlin`与`java`的语法完全一致，不再赘述。

- ifNotExist()：为 create 添加判断机制，若当前 PropertyKey 已经存在则不再创建，否则创建该属性。若不添加判断，在 properkey 已存在的情况下会抛出异常信息，下同，不再赘述。

##### 2.2.3 删除 PropertyKey

```java
schema.propertyKey("name").remove()
```

##### 2.2.4 查询 PropertyKey

```java
// 获取 PropertyKey 对象
schema.getPropertyKey("name")

// 获取 PropertyKey 属性
schema.getPropertyKey("name").cardinality()
schema.getPropertyKey("name").dataType()
schema.getPropertyKey("name").name()
schema.getPropertyKey("name").userdata()
```

#### 2.3 VertexLabel

##### 2.3.1 接口及参数介绍

VertexLabel 用来定义顶点类型，描述顶点的约束信息：

VertexLabel 允许定义的约束信息包括：name、idStrategy、properties、primaryKeys 和 nullableKeys，下面逐一介绍。

- name: 属性的名字，用来区分不同的 VertexLabel，不允许有同名的属性；

| interface                | param | must set |
|--------------------------|-------|----------|
| vertexLabel(String name) | name  | y        |

- idStrategy: 每一个 VertexLabel 都可以选择自己的 Id 策略，目前有三种策略供选择，即 Automatic（自动生成）、Customize（用户传入）和 PrimaryKey（主属性键）。其中 Automatic 使用 Snowflake 算法生成 Id，Customize 需要用户自行传入字符串或数字类型的 Id，PrimaryKey 则允许用户从 VertexLabel 的属性中选择若干主属性作为区分的依据，HugeGraph 内部会根据主属性的值拼接生成 Id。idStrategy 默认使用 Automatic 的，但如果用户没有显式设置 idStrategy 又调用了 primaryKeys(...) 方法设置了主属性，则 idStrategy 将自动使用 PrimaryKey；

| interface            | idStrategy       | description                                             |
|----------------------|------------------|---------------------------------------------------------|
| useAutomaticId       | AUTOMATIC        | generate id automatically by Snowflake algorithm        |
| useCustomizeStringId | CUSTOMIZE_STRING | passed id by user, must be string type                  |
| useCustomizeNumberId | CUSTOMIZE_NUMBER | passed id by user, must be number type                  |
| usePrimaryKeyId      | PRIMARY_KEY      | choose some important prop as primary key to splice id  |

- properties: 定义顶点的属性，传入的参数是 PropertyKey 的 name

| interface                        | description               |
|----------------------------------|---------------------------|
| properties(String... properties) | allow to pass multi props |

- primaryKeys: 当用户选择了 PrimaryKey 的 Id 策略时，需要从 VertexLabel 的属性中选择若干主属性作为区分的依据；

| interface                   | description                               |
|-----------------------------|-------------------------------------------|
| primaryKeys(String... keys) | allow to choose multi prop as primaryKeys |

需要注意的是，Id 策略的选择与 primaryKeys 的设置有一些相互约束，不能随意调用，约束关系见下表：

|                   | useAutomaticId | useCustomizeStringId | useCustomizeNumberId | usePrimaryKeyId |
|-------------------|----------------|----------------------|----------------------|-----------------|
| unset primaryKeys | AUTOMATIC      | CUSTOMIZE_STRING     | CUSTOMIZE_NUMBER     | ERROR           |
| set primaryKeys   | ERROR          | ERROR                | ERROR                | PRIMARY_KEY     |

- nullableKeys: 对于通过 properties(...) 方法设置过的属性，默认全都是不可为空的，也就是在创建顶点时该属性必须赋值，这样可能对用户数据提出了太过严格的完整性要求。为避免这样的强约束，用户可以通过
本方法设置若干属性为可空的，这样添加顶点时该属性可以不赋值。

| interface                          | description               |
|------------------------------------|---------------------------|
| nullableKeys(String... properties) | allow to pass multi props |

注意：primaryKeys 和 nullableKeys 不能有交集，因为一个属性不能既作为主属性，又是可空的。

- enableLabelIndex：用户可以指定是否需要为 label 创建索引。不创建则无法全局搜索指定 label 的顶点和边，创建则可以全局搜索，做类似于`g.V().hasLabel('person'), g.E().has('label', 'person')`这样的查询，
但是插入数据时性能上会更加慢，并且需要占用更多的存储空间。此项默认为 true。

| interface                        | description                     |
|----------------------------------|---------------------------------|
| enableLabelIndex(boolean enable) | Whether to create a label index |

- userdata：用户可以自己添加一些约束或额外信息，然后自行检查传入的属性是否满足约束，或者必要的时候提取出额外信息

| interface                          | description                                    |
|------------------------------------|------------------------------------------------|
| userdata(String key, Object value) | The same key, the latter will cover the former |

##### 2.3.2 创建 VertexLabel

```java
// 使用 Automatic 的 Id 策略
schema.vertexLabel("person").properties("name", "age").ifNotExist().create();
schema.vertexLabel("person").useAutomaticId().properties("name", "age").ifNotExist().create();

// 使用 Customize_String 的 Id 策略
schema.vertexLabel("person").useCustomizeStringId().properties("name", "age").ifNotExist().create();
// 使用 Customize_Number 的 Id 策略
schema.vertexLabel("person").useCustomizeNumberId().properties("name", "age").ifNotExist().create();

// 使用 PrimaryKey 的 Id 策略
schema.vertexLabel("person").properties("name", "age").primaryKeys("name").ifNotExist().create();
schema.vertexLabel("person").usePrimaryKeyId().properties("name", "age").primaryKeys("name").ifNotExist().create();
```

##### 2.3.3 追加 VertexLabel

VertexLabel 是可以追加约束的，不过仅限 properties 和 nullableKeys，而且追加的属性也必须添加到 nullableKeys 集合中。

```java
schema.vertexLabel("person").properties("price").nullableKeys("price").append();
```

##### 2.3.4 删除 VertexLabel

```java
schema.vertexLabel("person").remove();
```

##### 2.3.5 查询 VertexLabel

```java
// 获取 VertexLabel 对象
schema.getVertexLabel("name")

// 获取 property key 属性
schema.getVertexLabel("person").idStrategy()
schema.getVertexLabel("person").primaryKeys()
schema.getVertexLabel("person").name()
schema.getVertexLabel("person").properties()
schema.getVertexLabel("person").nullableKeys()
schema.getVertexLabel("person").userdata()
```

#### 2.4 EdgeLabel

##### 2.4.1 接口及参数介绍

EdgeLabel 用来定义边类型，描述边的约束信息。

EdgeLabel 允许定义的约束信息包括：name、sourceLabel、targetLabel、frequency、properties、sortKeys 和 nullableKeys，下面逐一介绍。

- name: 属性的名字，用来区分不同的 EdgeLabel，不允许有同名的属性；

| interface              | param | must set |
|------------------------|-------|----------|
| edgeLabel(String name) | name  | y        |

- sourceLabel: 边连接的源顶点类型名，只允许设置一个；

- targetLabel: 边连接的目标顶点类型名，只允许设置一个；

| interface                 | param | must set |
|---------------------------|-------|----------|
| sourceLabel(String label) | label | y        |
| targetLabel(String label) | label | y        |

- frequency: 字面意思是频率，表示在两个具体的顶点间某个关系出现的次数，可以是单次（single）或多次（frequency），默认为 single；

| interface    | frequency | description                         |
|--------------|-----------|-------------------------------------|
| singleTime() | single    | a relationship can only occur once  |
| multiTimes() | multiple  | a relationship can occur many times |

- properties: 定义边的属性

| interface                        | description               |
|----------------------------------|---------------------------|
| properties(String... properties) | allow to pass multi props |

- sortKeys: 当 EdgeLabel 的 frequency 为 multiple 时，需要某些属性来区分这多次的关系，故引入了 sortKeys（排序键）；

| interface                | description                            |
|--------------------------|----------------------------------------|
| sortKeys(String... keys) | allow to choose multi prop as sortKeys |

- nullableKeys: 与顶点中的 nullableKeys 概念一致，不再赘述

注意：sortKeys 和 nullableKeys 也不能有交集。

- enableLabelIndex：与顶点中的 enableLabelIndex 概念一致，不再赘述

- userdata：用户可以自己添加一些约束或额外信息，然后自行检查传入的属性是否满足约束，或者必要的时候提取出额外信息

| interface                          | description                                    |
|------------------------------------|------------------------------------------------|
| userdata(String key, Object value) | The same key, the latter will cover the former |

##### 2.4.2 创建 EdgeLabel

```java
schema.edgeLabel("knows").link("person", "person").properties("date").ifNotExist().create();
schema.edgeLabel("created").multiTimes().link("person", "software").properties("date").sortKeys("date").ifNotExist().create();
```

##### 2.4.3 追加 EdgeLabel

```java
schema.edgeLabel("knows").properties("price").nullableKeys("price").append();
```

##### 2.4.4 删除 EdgeLabel

```java
schema.edgeLabel("knows").remove();
```

##### 2.4.5 查询 EdgeLabel

```java
// 获取 EdgeLabel 对象
schema.getEdgeLabel("knows")

// 获取 property key 属性
schema.getEdgeLabel("knows").frequency()
schema.getEdgeLabel("knows").sourceLabel()
schema.getEdgeLabel("knows").targetLabel()
schema.getEdgeLabel("knows").sortKeys()
schema.getEdgeLabel("knows").name()
schema.getEdgeLabel("knows").properties()
schema.getEdgeLabel("knows").nullableKeys()
schema.getEdgeLabel("knows").userdata()
```

#### 2.5 IndexLabel

##### 2.5.1 接口及参数介绍

IndexLabel 用来定义索引类型，描述索引的约束信息，主要是为了方便查询。

IndexLabel 允许定义的约束信息包括：name、baseType、baseValue、indexFields、indexType，下面逐一介绍。

- name: 属性的名字，用来区分不同的 IndexLabel，不允许有同名的属性；

| interface               | param | must set |
|-------------------------|-------|----------|
| indexLabel(String name) | name  | y        |

- baseType: 表示要为 VertexLabel 还是 EdgeLabel 建立索引, 与下面的 baseValue 配合使用；

- baseValue: 指定要建立索引的 VertexLabel 或 EdgeLabel 的名称；

| interface             | param     | description                              |
|-----------------------|-----------|------------------------------------------|
| onV(String baseValue) | baseValue | build index for VertexLabel: 'baseValue' |
| onE(String baseValue) | baseValue | build index for EdgeLabel: 'baseValue'   |

- indexFields: 要在哪些属性上建立索引，可以是为多列建立联合索引；

| interface            | param | description                                               |
|----------------------|-------|-----------------------------------------------------------|
| by(String... fields) | files | allow to build index for multi fields for secondary index |

- indexType: 建立的索引类型，目前支持五种，即 Secondary、Range、Search、Shard 和 Unique。
    - Secondary 支持精确匹配的二级索引，允许建立联合索引，联合索引支持索引前缀搜索
        - 单个属性，支持相等查询，比如：person 顶点的 city 属性的二级索引，可以用`g.V().has("city", "北京")
        `查询"city 属性值是北京"的全部顶点
        - 联合索引，支持前缀查询和相等查询，比如：person 顶点的 city 和 street 属性的联合索引，可以用`g.V().has
        ("city", "北京").has('street', '中关村街道')
        `查询"city属性值是北京且street属性值是中关村"的全部顶点，或者`g.V()
        .has("city", "北京")`查询"city 属性值是北京"的全部顶点
        > secondary index 的查询都是基于"是"或者"相等"的查询条件，不支持"部分匹配"
    - Range 支持数值类型的范围查询
        - 必须是单个数字或者日期属性，比如：person 顶点的 age 属性的范围索引，可以用`g.V().has("age", P.gt(18))
        `查询"age属性值大于18"的顶点。除了`P.gt()`以外，还支持`P.gte()`, `P.lte()`, `P.lt()`,
        `P.eq()`, `P.between()`, `P.inside()`和`P.outside()`等
    - Search 支持全文检索的索引
        - 必须是单个文本属性，比如：person 顶点的 address 属性的全文索引，可以用`g.V().has("address", Text
        .contains('大厦')`查询"address 属性中包含大厦"的全部顶点
        > search index 的查询是基于"是"或者"包含"的查询条件
    - Shard 支持前缀匹配 + 数字范围查询的索引
        - N 个属性的分片索引，支持前缀相等情况下的范围查询，比如：person 顶点的 city 和 age 属性的分片索引，可以用`g.V().has
        ("city", "北京").has("age", P.between(18, 30))
        `查询"city 属性是北京且年龄大于等于 18 小于 30"的全部顶点
        - shard index N 个属性全是文本属性时，等价于 secondary index
        - shard index 只有单个数字或者日期属性时，等价于 range index
        > shard index 可以有任意数字或者日期属性，但是查询时最多只能提供一个范围查找条件，且该范围查找条件的属性的前缀属性都是相等查询条件
    - Unique 支持属性值唯一性约束，即可以限定属性的值不重复，允许联合索引，但不支持查询
        - 单个或者多个属性的唯一性索引，不可用来查询，只可对属性的值进行限定，当出现重复值时将报错

| interface   | indexType | description                                         |
|-------------|-----------|-----------------------------------------------------|
| secondary() | Secondary | support prefix search                               |
| range()     | Range     | support range(numeric or date type) search          |
| search()    | Search    | support full text search                            |
| shard()     | Shard     | support prefix + range(numeric or date type) search |
| unique()    | Unique    | support unique props value, not support search      |

##### 2.5.2 创建 IndexLabel

```java
schema.indexLabel("personByAge").onV("person").by("age").range().ifNotExist().create();
schema.indexLabel("createdByDate").onE("created").by("date").secondary().ifNotExist().create();
schema.indexLabel("personByLived").onE("person").by("lived").search().ifNotExist().create();
schema.indexLabel("personByCityAndAge").onV("person").by("city", "age").shard().ifNotExist().create();
schema.indexLabel("personById").onV("person").by("id").unique().ifNotExist().create();
```

##### 2.5.3 删除 IndexLabel

```java
schema.indexLabel("personByAge").remove()
```

##### 2.5.4 查询 IndexLabel

```java
// 获取 IndexLabel 对象
schema.getIndexLabel("personByAge")

// 获取 property key 属性
schema.getIndexLabel("personByAge").baseType()
schema.getIndexLabel("personByAge").baseValue()
schema.getIndexLabel("personByAge").indexFields()
schema.getIndexLabel("personByAge").indexType()
schema.getIndexLabel("personByAge").name()
```

### 3 图数据

#### 3.1 Vertex

顶点是构成图的最基本元素，一个图中可以有非常多的顶点。下面给出一个添加顶点的例子：

```java
Vertex marko = graph.addVertex(T.label, "person", "name", "marko", "age", 29);
Vertex lop = graph.addVertex(T.label, "software", "name", "lop", "lang", "java", "price", 328);
```

- 添加顶点的关键是顶点属性，添加顶点函数的参数个数必须为偶数，且满足`key1 -> val1, key2 -> val2 ···`的顺序排列，键值对之间的顺序是自由的。
- 参数中必须包含一对特殊的键值对，就是`T.label -> "val"`，用来定义该顶点的类别，以便于程序从缓存或后端获取到该 VertexLabel 的 schema 定义，然后做后续的约束检查。例子中的 label 定义为 person。
- 如果顶点类型的 Id 策略为 `AUTOMATIC`，则不允许用户传入 id 键值对。
- 如果顶点类型的 Id 策略为 `CUSTOMIZE_STRING`，则用户需要自己传入 String 类型 id 的值，键值对形如：`"T.id", "123456"`。
- 如果顶点类型的 Id 策略为 `CUSTOMIZE_NUMBER`，则用户需要自己传入 Number 类型 id 的值，键值对形如：`"T.id", 123456`。
- 如果顶点类型的 Id 策略为 `PRIMARY_KEY`，参数还必须全部包含该`primaryKeys`对应属性的名和值，如果不设置会抛出异常。比如之前`person`的`primaryKeys`是`name`，例子中就设置了`name`的值为`marko`。
- 对于非 nullableKeys 的属性，必须要赋值。
- 剩下的参数就是顶点其他属性的设置，但并非必须。
- 调用`addVertex`方法后，顶点会立刻被插入到后端存储系统中。

#### 3.2 Edge

有了点，还需要边才能构成完整的图。下面给出一个添加边的例子：

```java
Edge knows1 = marko.addEdge("knows", vadas, "city", "Beijing");
```

- 由（源）顶点来调用添加边的函数，函数第一个参数为边的 label，第二个参数是目标顶点，这两个参数的位置和顺序是固定的。后续的参数就是`key1 -> val1, key2 -> val2 ···`的顺序排列，设置边的属性，键值对顺序自由。
- 源顶点和目标顶点必须符合 EdgeLabel 中 source-label 和 target-label 的定义，不能随意添加。
- 对于非 nullableKeys 的属性，必须要赋值。

**注意：当 frequency 为 multiple 时必须要设置 sortKeys 对应属性类型的值。**

### 4 图管理
client支持一个物理部署中多个 GraphSpace，每个 GraphSpace 下可以含多个图（graph）。
- 兼容：不指定 GraphSpace 时，默认使用 "DEFAULT" 空间

#### 4.1 创建GraphSpace

```java
GraphSpaceManager spaceManager = hugeClient.graphSpace();

// 定义 GraphSpace 配置
GraphSpace graphSpace = new GraphSpace();
graphSpace.setName("myGraphSpace");
graphSpace.setDescription("Business data graph space");
graphSpace.setMaxGraphNumber(10);  // 最大图数量
graphSpace.setMaxRoleNumber(100);  // 最大角色数量

// 创建 GraphSpace
spaceManager.createGraphSpace(graphSpace);
```
#### 4.2 GraphSpace 接口汇总

| 类别 | 接口 | 描述 |
|------|------|------|
| Manager - 查询 | listGraphSpace() | 获取所有 GraphSpace 列表 |
| | getGraphSpace(String name) | 获取指定 GraphSpace |
| Manager - 创建/更新 | createGraphSpace(GraphSpace) | 创建 GraphSpace |
| | updateGraphSpace(String, GraphSpace) | 更新配置 |
| Manager - 删除 | removeGraphSpace(String) | 删除指定 GraphSpace |
| GraphSpace - 属性 | getName() / getDescription() | 获取名称/描述 |
| | getGraphNumber() | 获取图数量 |
| GraphSpace - 配置 | setDescription(String) | 设置描述 |
| | setMaxGraphNumber(int) | 设置最大图数量 |


### 5 简单示例

简单示例见[HugeGraph-Client](/cn/docs/quickstart/client/hugegraph-client)
