---
title: "HugeGraph Examples"
linkTitle: "HugeGraph Examples"
weight: 2
---

### 1 Overview

This example uses the [TitanDB Getting Started](http://s3.thinkaurelius.com/docs/titan/1.0.0/getting-started.html) guide as a template to demonstrate how to use HugeGraph. By comparing HugeGraph and TitanDB, you can understand the differences between them.

#### 1.1 Similarities and Differences between HugeGraph and TitanDB

Both HugeGraph and TitanDB are graph databases based on the [Apache TinkerPop3](https://tinkerpop.apache.org) framework. They both support the [Gremlin](https://tinkerpop.apache.org/gremlin.html) graph query language and share many similarities in terms of usage and interfaces. However, HugeGraph is a completely new design and development, characterized by its clear code structure, richer features, and more user-friendly interfaces.

Compared to TitanDB, HugeGraph's main features are as follows:

- HugeGraph currently offers a comprehensive suite of tools, including HugeGraph-API, HugeGraph-Client, HugeGraph-Loader, HugeGraph-Studio, and HugeGraph-Spark. These components facilitate system integration, data loading, visual graph querying, Spark connectivity, and other functionalities.
- HugeGraph incorporates the concepts of Server and Client, allowing third-party systems to connect via multiple methods such as JAR references, clients, and APIs. In contrast, TitanDB only supports connections via JAR references.
- HugeGraph requires explicit schema definition, and all insertions and queries must pass strict schema validation. Implicit schema creation is not supported at the moment.
- HugeGraph makes full use of the characteristics of the underlying storage system to achieve efficient data access, whereas TitanDB ignores the differences of the backend with a unified Kv structure.
- HugeGraph's update operations can be performed on-demand (e.g., updating a specific attribute), offering better performance. TitanDB uses a read-and-update approach for updates.
- Both VertexId and EdgeId in HugeGraph support concatenation, allowing for automatic deduplication and better query performance. In TitanDB, all IDs are auto-generated and require indexing for queries.

#### 1.2 Character Relationship Graph

This example uses the Property Graph Model to describe the relationships between characters in Greek mythology, also known as the character relationship graph. The specific relationships are shown in the diagram below.

<div style="text-align: center;">
  <img src="/img/docs/graph-of-gods.png" alt="image">
</div>


In the diagram, circular nodes represent entities (Vertices), arrows represent relationships (Edges), and the content in the boxes represents attributes.

There are two types of vertices in this graph: characters and locations, as shown in the table below:

| Name        | Type     | Attributes            |
|-----------|--------|---------------|
| character | vertex | name,age,type |
| location  | vertex | name          |

There are six types of relationships: father, mother, brother, battled, lives, and pet. The details of these relationships are as follows:

| Name      | Type   | Source Vertex Label | Target Vertex Label | Attributes     |
|---------|------|---------------------|---------------------|--------|
| father  | edge | character           | character           | -      |
| mother  | edge | character           | character           | -      |
| brother | edge | character           | character           | -      |
| pet     | edge | character           | character           | -      |
| lives   | edge | character           | location            | reason |

In HugeGraph, each edge label can only act on one pair of source and target vertex labels. In other words, if a relationship called "father" is defined in the graph to connect character to character, then "father" cannot be used to connect to other vertex labels.

Therefore, in this example, the original TitanDB's monster, god, human, and demigod are all represented using the same `vertex label: character` in HugeGraph, with an additional `type` attribute to indicate the type of character. The `edge labels` remain consistent with the original TitanDB. Of course, to satisfy the `edge label` constraints, adjustments can be made to the `name` of the `edge label`.

### 2 Graph Schema and Data Ingest Examples

HugeGraph requires explicit schema creation, which involves creating PropertyKeys, VertexLabels, and EdgeLabels in sequence. If indexing is needed, IndexLabels must also be created.

#### 2.1 Graph Schema

```groovy
schema = hugegraph.schema()

schema.propertyKey("name").asText().ifNotExist().create()
schema.propertyKey("age").asInt().ifNotExist().create()
schema.propertyKey("time").asInt().ifNotExist().create()
schema.propertyKey("reason").asText().ifNotExist().create()
schema.propertyKey("type").asText().ifNotExist().create()

schema.vertexLabel("character").properties("name", "age", "type").primaryKeys("name").nullableKeys("age").ifNotExist().create()
schema.vertexLabel("location").properties("name").primaryKeys("name").ifNotExist().create()

schema.edgeLabel("father").link("character", "character").ifNotExist().create()
schema.edgeLabel("mother").link("character", "character").ifNotExist().create()
schema.edgeLabel("battled").link("character", "character").properties("time").ifNotExist().create()
schema.edgeLabel("lives").link("character", "location").properties("reason").nullableKeys("reason").ifNotExist().create()
schema.edgeLabel("pet").link("character", "character").ifNotExist().create()
schema.edgeLabel("brother").link("character", "character").ifNotExist().create()
```

#### 2.2 Graph Data

```groovy
// add vertices
Vertex saturn = graph.addVertex(T.label, "character", "name", "saturn", "age", 10000, "type", "titan")
Vertex sky = graph.addVertex(T.label, "location", "name", "sky")
Vertex sea = graph.addVertex(T.label, "location", "name", "sea")
Vertex jupiter = graph.addVertex(T.label, "character", "name", "jupiter", "age", 5000, "type", "god")
Vertex neptune = graph.addVertex(T.label, "character", "name", "neptune", "age", 4500, "type", "god")
Vertex hercules = graph.addVertex(T.label, "character", "name", "hercules", "age", 30, "type", "demigod")
Vertex alcmene = graph.addVertex(T.label, "character", "name", "alcmene", "age", 45, "type", "human")
Vertex pluto = graph.addVertex(T.label, "character", "name", "pluto", "age", 4000, "type", "god")
Vertex nemean = graph.addVertex(T.label, "character", "name", "nemean", "type", "monster")
Vertex hydra = graph.addVertex(T.label, "character", "name", "hydra", "type", "monster")
Vertex cerberus = graph.addVertex(T.label, "character", "name", "cerberus", "type", "monster")
Vertex tartarus = graph.addVertex(T.label, "location", "name", "tartarus")

// add edges
jupiter.addEdge("father", saturn)
jupiter.addEdge("lives", sky, "reason", "loves fresh breezes")
jupiter.addEdge("brother", neptune)
jupiter.addEdge("brother", pluto)
neptune.addEdge("lives", sea, "reason", "loves waves")
neptune.addEdge("brother", jupiter)
neptune.addEdge("brother", pluto)
hercules.addEdge("father", jupiter)
hercules.addEdge("mother", alcmene)
hercules.addEdge("battled", nemean, "time", 1)
hercules.addEdge("battled", hydra, "time", 2)
hercules.addEdge("battled", cerberus, "time", 12)
pluto.addEdge("brother", jupiter)
pluto.addEdge("brother", neptune)
pluto.addEdge("lives", tartarus, "reason", "no fear of death")
pluto.addEdge("pet", cerberus)
cerberus.addEdge("lives", tartarus)
```

#### 2.3 Indices

HugeGraph by default automatically generates IDs. However, if a user specifies the `primaryKeys` field list for a `VertexLabel` through `primaryKeys`, the ID strategy for that `VertexLabel` will automatically switch to the `primaryKeys` strategy. Once the `primaryKeys` strategy is enabled, HugeGraph generates `VertexId` by concatenating `vertexLabel+primaryKeys`, which allows for automatic deduplication. Additionally, there is no need to create extra indexes to use the properties in `primaryKeys` for fast querying. For example, both "character" and "location" have the `primaryKeys("name")` attribute, so without creating additional indexes, vertices can be queried using `g.V().hasLabel('character') .has('name','hercules')`.

### 3 Graph Traversal Examples

#### 3.1 Traversal Query

**1\. Find the grandfather of hercules**

```groovy
g.V().hasLabel('character').has('name','hercules').out('father').out('father')
```

It can also be done using the `repeat` method:

```groovy
g.V().hasLabel('character').has('name','hercules').repeat(__.out('father')).times(2)
```

**2\. Find the name of Hercules's father**

```groovy
g.V().hasLabel('character').has('name','hercules').out('father').value('name')
```

**3\. Find the characters with age > 100**

```groovy
g.V().hasLabel('character').has('age',gt(100))
```

**4\. Find who are pluto's cohabitants**

```groovy
g.V().hasLabel('character').has('name','pluto').out('lives').in('lives').values('name')
```

**5\. Find pluto can't be his own cohabitant**

```groovy
pluto = g.V().hasLabel('character').has('name', 'pluto')
g.V(pluto).out('lives').in('lives').where(is(neq(pluto)).values('name')

// use 'as'
g.V().hasLabel('character').has('name', 'pluto').as('x').out('lives').in('lives').where(neq('x')).values('name')
```

**6\. Pluto's Brothers**

```groovy
pluto = g.V().hasLabel('character').has('name', 'pluto').next()
// where do pluto's brothers live?
g.V(pluto).out('brother').out('lives').values('name')

// which brother lives in which place?
g.V(pluto).out('brother').as('god').out('lives').as('place').select('god','place')

// what is the name of the brother and the name of the place?
g.V(pluto).out('brother').as('god').out('lives').as('place').select('god','place').by('name')
```

It is recommended to use [HugeGraph-Hubble](/docs/quickstart/toolchain/hugegraph-hubble) to execute the above code visually. Additionally, the code can be executed through various other methods such as HugeGraph-Client, HugeGraph-Api, GremlinConsole, and GremlinDriver.

#### 3.2 Summary

HugeGraph currently supports `Gremlin` syntax, and users can implement various query requirements through `Gremlin / REST-API`.
