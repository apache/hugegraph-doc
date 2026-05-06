---
title: "HugeGraph Java Client"
linkTitle: "HugeGraph Java Client"
weight: 2
---

The code in this document is written in `java`, but its style is very similar to `gremlin(groovy)`. The user only needs to replace the variable declaration in the code with `def` or remove it directly,
You can convert `java` code into `groovy`; in addition, each line of statement can be without a semicolon at the end, `groovy` considers a line to be a statement.
The `gremlin(groovy)` written by the user in `HugeGraph-Studio` can refer to the `java` code in this document, and some examples will be given below.

### 1 HugeGraph-Client

HugeGraph-Client is the general entry for operating graph. Users must first create a HugeGraph-Client object and establish a connection (pseudo connection) with HugeGraph-Server before they can obtain the operation entry objects of schema, graph and gremlin.

Currently, HugeGraph-Client only allows connections to existing graphs on the server, and cannot create custom graphs. After version 1.7.0, client has supported setting graphSpace, the default value for graphSpace is DEFAULT. Its creation method is as follows:

```java
// HugeGraphServer address: "http://localhost:8080"
// Graph Name: "hugegraph"
HugeClient hugeClient = HugeClient.builder("http://localhost:8080", "hugegraph")
                                //.builder("http://localhost:8080", "graphSpaceName", "hugegraph")
                                  .configTimeout(20) // 20s timeout
                                  .configUser("**", "**") // enable auth
                                  .build();
```

If the above process of creating HugeClient fails, an exception will be thrown, and the user needs to use try-catch. If successful, continue to get schema, graph and gremlin manager.

When operating through `gremlin` in `HugeGraph-Hubble`(or `HugeGraph-Studio`), `HugeClient` is not required and can be ignored.

### 2 Schema

#### 2.1 SchemaManager

SchemaManager is used to manage four kinds of schema in HugeGraph, namely PropertyKey (property type), VertexLabel (vertex type), EdgeLabel (edge type) and IndexLabel (index label). A SchemaManager object can be created for schema information definition.

The user can obtain the SchemaManager object using the following methods:

```java
SchemaManager schema = hugeClient.schema()
```

Create a `schema` object via `gremlin` in `HugeGraph-Hubble`:

```groovy
schema = graph.schema()
```

The definition process of the 4 kinds of schema is described below.

#### 2.2 PropertyKey

##### 2.2.1 Interface and parameter introduction

PropertyKey is used to standardize the property constraints of vertices and edges, and properties of properties are not currently supported.

The constraint information that PropertyKey allows to define includes: name, datatype, cardinality, and userdata, which are introduced one by one below.

- name: The name of the property, used to distinguish different PropertyKeys, PropertyKeys with the same name are not allowed.

| interface                | param | must set |
|--------------------------|-------|----------|
| propertyKey(String name) | name  | y        |

- datatype: property value type, you must select an explicit setting from the following table that conforms to the specific business scenario:

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

- cardinality: Whether the property value is single-valued or multivalued, in the case of multivalued, it is divided into allowing-duplicate values and not-allowing-duplicate values. This item is single by default. If necessary, you can select a setting from the following table:

| interface     | cardinality | description                                 |
|---------------|-------------|---------------------------------------------|
| valueSingle() | single      | single value                                |
| valueList()   | list        | multi-values that allow duplicate value     |
| valueSet()    | set         | multi-values that not allow duplicate value |

- userdata: Users can add some constraints or additional information by themselves, and then check whether the incoming properties satisfy the constraints, or extract additional information when necessary:

| interface                          | description                                    |
|------------------------------------|------------------------------------------------|
| userdata(String key, Object value) | The same key, the latter will cover the former |

##### 2.2.2 Create PropertyKey

```java
schema.propertyKey("name").asText().valueSet().ifNotExist().create()
```

The syntax of creating the above `PropertyKey` object through `gremlin` in `HugeGraph-Hubble` is exactly the same. If the user does not define the `schema` variable, it should be written like this:

```groovy
graph.schema().propertyKey("name").asText().valueSet().ifNotExist().create()
```

In the following examples, the syntax of `gremlin` and `java` is exactly the same, so we won't repeat them.

- ifNotExist(): Add a judgment mechanism for create, if the current PropertyKey already exists, it will not be created, otherwise the property will be created. If no ifNotExist() is added, an exception will be thrown if a property-key with the same name already exists. The same as below, and will not be repeated there.

##### 2.2.3 Delete PropertyKey

```java
schema.propertyKey("name").remove()
```

##### 2.2.4 Query PropertyKey

```java
// Get PropertyKey
schema.getPropertyKey("name")

// Get attributes of PropertyKey
schema.getPropertyKey("name").cardinality()
schema.getPropertyKey("name").dataType()
schema.getPropertyKey("name").name()
schema.getPropertyKey("name").userdata()
```

#### 2.3 VertexLabel

##### 2.3.1 Interface and parameter introduction

VertexLabel is used to define the vertex type and describe the constraint information of the vertex.

The constraint information that VertexLabel allows to define include: name, idStrategy, properties, primaryKeys and nullableKeys, which are introduced one by one below.

- name: The name of the VertexLabel, used to distinguish different VertexLabels, VertexLabels with the same name are not allowed.

| interface                | param | must set |
|--------------------------|-------|----------|
| vertexLabel(String name) | name  | y        |

- idStrategy: Each VertexLabel can choose its own ID strategy. There are currently three strategies to choose from, namely Automatic (automatically generated), Customize (user input) and PrimaryKey (primary attribute key). Among them, Automatic uses the Snowflake algorithm to generate ID, Customize requires the user to pass in the ID of string or number type, and PrimaryKey allows the user to select several properties of VertexLabel as the basis for differentiation. HugeGraph will be spliced and generated ID according to the value of the primary properties. idStrategy uses Automatic by default, but if the user does not explicitly set idStrategy and calls the primaryKeys(...) method to set the primary property, then idStrategy will automatically use PrimaryKey.

| interface            | idStrategy       | description                                             |
|----------------------|------------------|---------------------------------------------------------|
| useAutomaticId       | AUTOMATIC        | generate id automatically by Snowflake algorithm        |
| useCustomizeStringId | CUSTOMIZE_STRING | passed id by user, must be string type                  |
| useCustomizeNumberId | CUSTOMIZE_NUMBER | passed id by user, must be number type                  |
| usePrimaryKeyId      | PRIMARY_KEY      | choose some important prop as primary key to splice id  |

- properties: define the properties of the vertex, the incoming parameter is the name of the PropertyKey.

| interface                        | description                    |
|----------------------------------|--------------------------------|
| properties(String... properties) | allow to pass multi properties |

- primaryKeys: When the user selects the ID strategy of PrimaryKey, several primary properties need to be selected from the properties of VertexLabel as the basis for differentiation;

| interface                   | description                               |
|-----------------------------|-------------------------------------------|
| primaryKeys(String... keys) | allow to choose multi prop as primaryKeys |

Note that the selection of the ID strategy and the setting of primaryKeys have some mutual constraints, which cannot be called at will. The constraints are shown in the following table:

|                   | useAutomaticId | useCustomizeStringId | useCustomizeNumberId | usePrimaryKeyId |
|-------------------|----------------|----------------------|----------------------|-----------------|
| unset primaryKeys | AUTOMATIC      | CUSTOMIZE_STRING     | CUSTOMIZE_NUMBER     | ERROR           |
| set primaryKeys   | ERROR          | ERROR                | ERROR                | PRIMARY_KEY     |

- nullableKeys: For properties set by the properties(...) method, all of them are non-nullable by default, that is, the property must be assigned a value when creating a vertex, which may impose too strict integrity requirements on user data. In order to avoid such strong constraints, the user can set some properties to be nullable through this method, so that the properties can be unassigned when adding vertices.

| interface                          | description               |
|------------------------------------|---------------------------|
| nullableKeys(String... properties) | allow to pass multi props |

Note: primaryKeys and nullableKeys cannot intersect, because a property cannot be both primary and nullable.

- enableLabelIndex: The user can specify whether to create an index for the label. If you don't create it, you can't globally search for the vertices and edges of the specified label. If you create it, you can search globally, like `g.V().hasLabel('person'), g.E().has('label', 'person')` query, but the performance will be slower when inserting data, and it will take up more storage space. This defaults to true.

| interface                        | description                     |
|----------------------------------|---------------------------------|
| enableLabelIndex(boolean enable) | Whether to create a label index |

- userdata: Users can add some constraints or additional information by themselves, and then check whether the incoming properties meet the constraints, or extract additional information when necessary.

| interface                          | description                                    |
|------------------------------------|------------------------------------------------|
| userdata(String key, Object value) | The same key, the latter will cover the former |

##### 2.3.2 Create VertexLabel

```java
// Use Automatic Id strategy
schema.vertexLabel("person").properties("name", "age").ifNotExist().create();
schema.vertexLabel("person").useAutomaticId().properties("name", "age").ifNotExist().create();

// Use Customize_String Id strategy
schema.vertexLabel("person").useCustomizeStringId().properties("name", "age").ifNotExist().create();
// Use Customize_Number Id strategy
schema.vertexLabel("person").useCustomizeNumberId().properties("name", "age").ifNotExist().create();

// Use PrimaryKey Id strategy
schema.vertexLabel("person").properties("name", "age").primaryKeys("name").ifNotExist().create();
schema.vertexLabel("person").usePrimaryKeyId().properties("name", "age").primaryKeys("name").ifNotExist().create();
```

##### 2.3.3 Update VertexLabel

VertexLabel can append constraints, but only properties and nullableKeys, and the appended properties must also be added to the nullableKeys collection.

```java
schema.vertexLabel("person").properties("price").nullableKeys("price").append();
```

##### 2.3.4 Delete VertexLabel

```java
schema.vertexLabel("person").remove();
```

##### 2.3.5 Query VertexLabel

```java
// Get VertexLabel
schema.getVertexLabel("name")

// Get attributes of VertexLabel
schema.getVertexLabel("person").idStrategy()
schema.getVertexLabel("person").primaryKeys()
schema.getVertexLabel("person").name()
schema.getVertexLabel("person").properties()
schema.getVertexLabel("person").nullableKeys()
schema.getVertexLabel("person").userdata()
```

#### 2.4 EdgeLabel

##### 2.4.1 Interface and parameter introduction

EdgeLabel is used to define the edge type and describe the constraint information of the edge.

The constraint information that EdgeLabel allows to define include: name, sourceLabel, targetLabel, frequency, properties, sortKeys and nullableKeys, which are introduced one by one below.

- name: The name of the EdgeLabel, used to distinguish different EdgeLabels, EdgeLabels with the same name are not allowed.

| interface              | param | must set |
|------------------------|-------|----------|
| edgeLabel(String name) | name  | y        |

- sourceLabel: The name of the source vertex type of the edge link, only one is allowed;

- targetLabel: The name of the target vertex type of the edge link, only one is allowed;

| interface                 | param | must set |
|---------------------------|-------|----------|
| sourceLabel(String label) | label | y        |
| targetLabel(String label) | label | y        |

- frequency: Indicating the number of times a relationship occurs between two specific vertices, which can be single (single) or multiple (frequency), the default is single.

| interface    | frequency | description                         |
|--------------|-----------|-------------------------------------|
| singleTime() | single    | a relationship can only occur once  |
| multiTimes() | multiple  | a relationship can occur many times |

- properties: Define the properties of the edge.

| interface                        | description               |
|----------------------------------|---------------------------|
| properties(String... properties) | allow to pass multi props |

- sortKeys: When the frequency of EdgeLabel is multiple, some properties are needed to distinguish the multiple relationships, so sortKeys (sorted keys) is introduced;

| interface                | description                            |
|--------------------------|----------------------------------------|
| sortKeys(String... keys) | allow to choose multi prop as sortKeys |

- nullableKeys: Consistent with the concept of nullableKeys in vertices.

Note: sortKeys and nullableKeys also cannot intersect.

- enableLabelIndex: It is consistent with the concept of enableLabelIndex in the vertex.

- userdata: Users can add some constraints or additional information by themselves, and then check whether the incoming properties meet the constraints, or extract additional information when necessary.

| interface                          | description                                    |
|------------------------------------|------------------------------------------------|
| userdata(String key, Object value) | The same key, the latter will cover the former |

##### 2.4.2 Create EdgeLabel

```java
schema.edgeLabel("knows").link("person", "person").properties("date").ifNotExist().create();
schema.edgeLabel("created").multiTimes().link("person", "software").properties("date").sortKeys("date").ifNotExist().create();
```

##### 2.4.3 Update EdgeLabel

```java
schema.edgeLabel("knows").properties("price").nullableKeys("price").append();
```

##### 2.4.4 Delete EdgeLabel

```java
schema.edgeLabel("knows").remove();
```

##### 2.4.5 Query EdgeLabel

```java
// Get EdgeLabel
schema.getEdgeLabel("knows")

// Get attributes of EdgeLabel
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

##### 2.5.1 Interface and parameter introduction

IndexLabel is used to define the index type and describe the constraint information of the index, mainly for the convenience of query.

The constraint information that IndexLabel allows to define include: name, baseType, baseValue, indexFields, indexType, which are introduced one by one below.

- name: The name of the IndexLabel, used to distinguish different IndexLabels, IndexLabels with the same name are not allowed.

| interface               | param | must set |
|-------------------------|-------|----------|
| indexLabel(String name) | name  | y        |

- baseType: Indicates whether to index VertexLabel or EdgeLabel, used in conjunction with the baseValue below.

- baseValue: Specifies the name of the VertexLabel or EdgeLabel to be indexed.

| interface             | param     | description                              |
|-----------------------|-----------|------------------------------------------|
| onV(String baseValue) | baseValue | build index for VertexLabel: 'baseValue' |
| onE(String baseValue) | baseValue | build index for EdgeLabel: 'baseValue'   |

- indexFields: on which fields to index, it can be a joint index for multiple columns.

| interface            | param | description                                               |
|----------------------|-------|-----------------------------------------------------------|
| by(String... fields) | files | allow to build index for multi fields for secondary index |

- indexType: There are currently five types of indexes established, namely Secondary, Range, Search, Shard and Unique.
    - Secondary Index supports exact matching secondary index, allow to build joint index, joint index supports index prefix search
        - Single Property Secondary Index, support equality query, for example: the secondary index of the city property of the person vertex, you can use `g.V().has("city", "Beijing")` to query all the vertices with "city attribute value is Beijing"
        - Joint Secondary Index, supports prefix query and equality query, such as: joint index of city and street properties of person vertex, you can use `g.V().has("city", "Beijing").has('street', 'Zhongguancun street ')` to query all vertices of "city property value is Beijing and street property value is ZhongGuanCun", or `g.V().has("city", "Beijing")` to query all vertices of "city property value is Beijing".
        > The query of Secondary Index is based on the query condition of "yes" or "equal", and does not support "partial matching".
    - Range Index supports for range queries of numeric types
        - Must be a single number or date attribute, for example: the range index of the age property of the person vertex, you can use `g.V().has("age", P.gt(18))` to query the vertices with "age property value greater than 18" . In addition to `P.gt()`, also supports `P.gte()`, `P.lte()`, `P.lt()`, `P.eq()`, `P.between() `, `P.inside()` and `P.outside()` etc.
    - Search Index supports full-text search
        - It must be a single text property, such as: full-text index of the address property of the person vertex, you can use `g.V().has("address", Text.contains('building')` to query all vertices whose "address property contains a 'building'"
        > The query of the Search Index is based on the query condition of "is" or "contains".
    - Shard Index supports prefix matching + numeric range query
        - The shard index of N properties supports range queries with equal prefixes. For example, the shard index of the city and age properties of the person vertex can use `g.V().has("city", "Beijing").has ("age", P.between(18, 30))`Query "city property is Beijing and all vertices whose age is greater than or equal to 18 and less than 30".
        - When all N properties are text properties in a Shard Index, it is equivalent to Secondary Index.
        - When there is only one single number or date property in a Shard Index, it is equivalent to the Range Index.
        > Shard Index can have any number or date property, but at most one range search condition can be provided when querying, and the prefix properties of the Shard Search conditions must be "equals".
    - Unique Index supports properties uniqueness constraints, that is, the value of properties can be limited to not repeat, and joint indexing is allowed, but querying is not supported now
        - The unique index of single or multiple properties cannot be used for query, only the value of the property can be limited, and an error will be reported when there is a duplicate value.

| interface   | indexType | description                                         |
|-------------|-----------|-----------------------------------------------------|
| secondary() | Secondary | support prefix search                               |
| range()     | Range     | support range(numeric or date type) search          |
| search()    | Search    | support full text search                            |
| shard()     | Shard     | support prefix + range(numeric or date type) search |
| unique()    | Unique    | support unique props value, not support search      |

##### 2.5.2 Create IndexLabel

```java
schema.indexLabel("personByAge").onV("person").by("age").range().ifNotExist().create();
schema.indexLabel("createdByDate").onE("created").by("date").secondary().ifNotExist().create();
schema.indexLabel("personByLived").onE("person").by("lived").search().ifNotExist().create();
schema.indexLabel("personByCityAndAge").onV("person").by("city", "age").shard().ifNotExist().create();
schema.indexLabel("personById").onV("person").by("id").unique().ifNotExist().create();
```

##### 2.5.3 Delete IndexLabel

```java
schema.indexLabel("personByAge").remove()
```

##### 2.5.4 Query IndexLabel

```java
// Get IndexLabel
schema.getIndexLabel("personByAge")

// Get attributes of IndexLabel
schema.getIndexLabel("personByAge").baseType()
schema.getIndexLabel("personByAge").baseValue()
schema.getIndexLabel("personByAge").indexFields()
schema.getIndexLabel("personByAge").indexType()
schema.getIndexLabel("personByAge").name()
```

### 3 Graph

#### 3.1 Vertex

Vertices are the most basic elements of a graph, and there can be many vertices in a graph. Here is an example of adding vertices:

```java
Vertex marko = graph.addVertex(T.label, "person", "name", "marko", "age", 29);
Vertex lop = graph.addVertex(T.label, "software", "name", "lop", "lang", "java", "price", 328);
```

- The key to adding vertices is the vertex properties. The number of parameters of the vertex adding function must be an even number and satisfy the order of `key1 -> val1, key2 -> val2 ...`, and the order between key-value pairs is free .
- The parameter must contain a special key-value pair, namely `T.label -> "val"`, which is used to define the category of the vertex, so that the program can obtain the schema definition of the VertexLabel from the cache or backend, and then do subsequent constraint checks. The label in the example is defined as person.
- If the vertex type's ID policy is `AUTOMATIC`, users are not allowed to pass in id key-value pairs.
- If the ID policy of the vertex type is `CUSTOMIZE_STRING`, the user needs to pass in the value of the id of the String type. The key-value pair is like: `"T.id", "123456"`.
- If the ID policy of the vertex type is `CUSTOMIZE_NUMBER`, the user needs to pass in the value of the id of the Number type. The key-value pair is like: `"T.id", 123456`.
- If the ID policy of the vertex type is `PRIMARY_KEY`, the parameters must also contain the name and value of the properties corresponding to the `primaryKeys`, if not set an exception will be thrown. For example, the `primaryKeys` of `person` is `name`, in the example, the value of `name` is set to `marko`.
- For properties that are not nullableKeys, a value must be assigned.
- The remaining parameters are the settings of other properties of the vertex, but they are not required.
- After calling the `addVertex` method, the vertices are inserted into the backend storage system immediately.

#### 3.2 Edge

After added vertices, edges are also needed to form a complete graph. Here is an example of adding edges:

```java
Edge knows1 = marko.addEdge("knows", vadas, "city", "Beijing");
```

- The function `addEdge()` of the (source) vertex is to add an edge(relationship) between itself and another vertex. The first parameter of the function is the label of the edge, and the second parameter is the target vertex. The position and order of these two parameters are fixed. The subsequent parameters are the order of `key1 -> val1, key2 -> val2 ...`, set the properties of the edge, and the key-value pair order is free.
- The source and target vertices must conform to the definitions of source-label and target label in EdgeLabel, and cannot be added arbitrarily.
- For properties that are not nullableKeys, a value must be assigned.


**Note: When frequency is multiple, the value of the property type corresponding to sortKeys must be set.**

### 4 GraphSpace
The client supports multiple GraphSpaces in one physical deployment, and each GraphSpace can contain multiple graphs.
- Compatibility: When no GraphSpace is specified, the "DEFAULT" space is used by default.

#### 4.1 Create GraphSpace

```java
GraphSpaceManager spaceManager = hugeClient.graphSpace();

// Define GraphSpace configuration
GraphSpace graphSpace = new GraphSpace();
graphSpace.setName("myGraphSpace");
graphSpace.setDescription("Business data graph space");
graphSpace.setMaxGraphNumber(10);  // Maximum number of graphs
graphSpace.setMaxRoleNumber(100);  // Maximum number of roles

// Create GraphSpace
spaceManager.createGraphSpace(graphSpace);
```

#### 4.2 GraphSpace Interface Summary

| Category | Interface | Description |
|----------|-----------|-------------|
| Manager - Query | listGraphSpace() | Get the list of all GraphSpaces |
|           | getGraphSpace(String name) | Get the specified GraphSpace |
| Manager - Create/Update | createGraphSpace(GraphSpace) | Create a GraphSpace |
|           | updateGraphSpace(String, GraphSpace) | Update configuration |
| Manager - Delete | removeGraphSpace(String) | Delete the specified GraphSpace |
| GraphSpace - Properties | getName() / getDescription() | Get name / description |
|           | getGraphNumber() | Get the number of graphs |
| GraphSpace - Configuration | setDescription(String) | Set description |
|           | setMaxGraphNumber(int) | Set the maximum number of graphs |

### 5 Simple Example

Simple examples can reference [HugeGraph-Client](/docs/quickstart/client/hugegraph-client)
