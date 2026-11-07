---
title: "HugeGraph Gremlin"
linkTitle: "Gremlin Query Language"
weight: 1
---

### Overview

HugeGraph supports [Gremlin](https://tinkerpop.apache.org/gremlin.html), a graph traversal query language of [Apache TinkerPop3](https://tinkerpop.apache.org).
While SQL is a query language for relational databases, Gremlin is a general-purpose query language for graph databases, enabling entity creation, property
modification, deletion, and traversal queries.

For developers seeking declarative pattern matching (similar to SQL or Neo4j style), HugeGraph also supports [Cypher](/docs/language/hugegraph-cypher/).

> [!NOTE]
> HugeGraph is powered by the TinkerPop **3.8.1** engine (running on Java 17 and Groovy 4.0.25).
> Upgrading from an older version? Review the [Gremlin & TinkerPop Migration Guide](/docs/guides/gremlin-migration-3.8/) for removed legacy syntax
> and behavioral changes.

### TinkerPop Features

HugeGraph implements the TinkerPop framework, but not all TinkerPop features are implemented.

The table below lists the support status of various TinkerPop features in HugeGraph:

### Graph Features

| Name                 | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Support |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| Computer             | Determines if the {@code Graph} implementation supports {@link GraphComputer} based processing                                                                                                                                                                                                                                                                                                                                                                | false   |
| Transactions         | Determines if the {@code Graph} implementations supports transactions.                                                                                                                                                                                                                                                                                                                                                                                        | true    |
| Persistence          | Determines if the {@code Graph} implementation supports persisting it's contents natively to disk.This feature does not refer to every graph's ability to write to disk via the Gremlin IO packages(.e.g. GraphML), unless the graph natively persists to disk via those options somehow. For example,TinkerGraph does not support this feature as it is a pure in-sideEffects graph.                                                                         | Backend-dependent |
| ThreadedTransactions | Determines if the {@code Graph} implementation supports threaded transactions which allow a transaction be executed across multiple threads via {@link Transaction#createThreadedTx()}.                                                                                                                                                                                                                                                                       | false   |
| ConcurrentAccess     | Determines if the {@code Graph} implementation supports more than one connection to the same instance at the same time. For example, Neo4j embedded does not support this feature because concurrent access to the same database files by multiple instances is not possible. However, Neo4j HA could support this feature as each new {@code Graph} instance coordinates with the Neo4j cluster allowing multiple instances to operate on the same database. | false   |
{.wide}

### Vertex Features

| Name                     | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Support |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| UserSuppliedIds          | Determines if an {@link Element} can have a user defined identifier. Implementation that do not support this feature will be expected to auto-generate unique identifiers. In other words, if the {@link Graph} allows {@code graph.addVertex(id,x)} to work and thus set the identifier of the newly added {@link Vertex} to the value of {@code x} then this feature should return true. In this case, {@code x} is assumed to be an identifier data type that the {@link Graph} will accept. | true    |
| NumericIds               | Determines if an {@link Element} has numeric identifiers as their internal representation. In other words,if the value returned from {@link Element#id()} is a numeric value then this method should be return {@code true}. Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite.                                                                                                                                          | false   |
| StringIds                | Determines if an {@link Element} has string identifiers as their internal representation. In other words, if the value returned from {@link Element#id()} is a string value then this method should be return {@code true}. Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite.                                                                                                                                           | true    |
| UuidIds                  | Determines if an {@link Element} has UUID identifiers as their internal representation. In other words,if the value returned from {@link Element#id()} is a {@link UUID} value then this method should be return {@code true}.Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite.                                                                                                                                         | false   |
| CustomIds                | Determines if an {@link Element} has a specific custom object as their internal representation.In other words, if the value returned from {@link Element#id()} is a type defined by the graph implementations, such as OrientDB's {@code Rid}, then this method should be return {@code true}.Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite.                                                                         | true    |
| AnyIds                   | Determines if an {@link Element} any Java object is a suitable identifier. TinkerGraph is a good example of a {@link Graph} that can support this feature, as it can use any {@link Object} as a value for the identifier. Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite. This setting should only return {@code true} if {@link #supportsUserSuppliedIds()} is {@code true}.                                        | false   |
| AddProperty              | Determines if an {@link Element} allows properties to be added. This feature is set independently from supporting "data types" and refers to support of calls to {@link Element#property(String, Object)}.                                                                                                                                                                                                                                                                                      | true    |
| RemoveProperty           | Determines if an {@link Element} allows properties to be removed.                                                                                                                                                                                                                                                                                                                                                                                                                               | true    |
| AddVertices              | Determines if a {@link Vertex} can be added to the {@code Graph}.                                                                                                                                                                                                                                                                                                                                                                                                                               | true    |
| MultiProperties          | Determines if a {@link Vertex} can support multiple properties with the same key.                                                                                                                                                                                                                                                                                                                                                                                                               | true    |
| DuplicateMultiProperties | Determines if a {@link Vertex} can support non-unique values on the same key. For this value to be {@code true}, then {@link #supportsMetaProperties()} must also return true. By default this method, just returns what {@link #supportsMultiProperties()} returns.                                                                                                                                                                                                                            | true    |
| MetaProperties           | Determines if a {@link Vertex} can support properties on vertex properties. It is assumed that a graph will support all the same data types for meta-properties that are supported for regular properties.                                                                                                                                                                                                                                                                                      | false   |
| RemoveVertices           | Determines if a {@link Vertex} can be removed from the {@code Graph}.                                                                                                                                                                                                                                                                                                                                                                                                                           | true    |
{.wide}

### Edge Features

| Name            | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Support |
|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| UserSuppliedIds | Determines if an {@link Element} can have a user defined identifier. Implementation that do not support this feature will be expected to auto-generate unique identifiers. In other words, if the {@link Graph} allows {@code graph.addVertex(id,x)} to work and thus set the identifier of the newly added {@link Vertex} to the value of {@code x} then this feature should return true. In this case, {@code x} is assumed to be an identifier data type that the {@link Graph} will accept. | false   |
| NumericIds      | Determines if an {@link Element} has numeric identifiers as their internal representation. In other words,if the value returned from {@link Element#id()} is a numeric value then this method should be return {@code true}. Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite.                                                                                                                                          | false   |
| StringIds       | Determines if an {@link Element} has string identifiers as their internal representation. In other words, if the value returned from {@link Element#id()} is a string value then this method should be return {@code true}. Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite.                                                                                                                                           | true    |
| UuidIds         | Determines if an {@link Element} has UUID identifiers as their internal representation. In other words,if the value returned from {@link Element#id()} is a {@link UUID} value then this method should be return {@code true}.Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite.                                                                                                                                         | false   |
| CustomIds       | Determines if an {@link Element} has a specific custom object as their internal representation.In other words, if the value returned from {@link Element#id()} is a type defined by the graph implementations, such as OrientDB's {@code Rid}, then this method should be return {@code true}.Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite.                                                                         | true    |
| AnyIds          | Determines if an {@link Element} any Java object is a suitable identifier. TinkerGraph is a good example of a {@link Graph} that can support this feature, as it can use any {@link Object} as a value for the identifier. Note that this feature is most generally used for determining the appropriate tests to execute in the Gremlin Test Suite. This setting should only return {@code true} if {@link #supportsUserSuppliedIds()} is {@code true}.                                        | false   |
| AddProperty     | Determines if an {@link Element} allows properties to be added. This feature is set independently from supporting "data types" and refers to support of calls to {@link Element#property(String, Object)}.                                                                                                                                                                                                                                                                                      | true    |
| RemoveProperty  | Determines if an {@link Element} allows properties to be removed.                                                                                                                                                                                                                                                                                                                                                                                                                               | true    |
| AddEdges        | Determines if an {@link Edge} can be added to a {@code Vertex}.                                                                                                                                                                                                                                                                                                                                                                                                                                 | true    |
| RemoveEdges     | Determines if an {@link Edge} can be removed from a {@code Vertex}.                                                                                                                                                                                                                                                                                                                                                                                                                             | true    |
{.wide}

### Data Type Features

| Name               | Description                                                                                                                                                                                                                                                          | Support |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| BooleanValues      |                                                                                                                                                                                                                                                                      | true    |
| ByteValues         |                                                                                                                                                                                                                                                                      | true    |
| DoubleValues       |                                                                                                                                                                                                                                                                      | true    |
| FloatValues        |                                                                                                                                                                                                                                                                      | true    |
| IntegerValues      |                                                                                                                                                                                                                                                                      | true    |
| LongValues         |                                                                                                                                                                                                                                                                      | true    |
| MapValues          | Supports setting of a {@code Map} value. The assumption is that the {@code Map} can contain arbitrary serializable values that may or may not be defined as a feature itself                                                                                         | false   |
| MixedListValues    | Supports setting of a {@code List} value. The assumption is that the {@code List} can contain arbitrary serializable values that may or may not be defined as a feature itself. As this{@code List} is "mixed" it does not need to contain objects of the same type. | false   |
| BooleanArrayValues |                                                                                                                                                                                                                                                                      | false   |
| ByteArrayValues    |                                                                                                                                                                                                                                                                      | true    |
| DoubleArrayValues  |                                                                                                                                                                                                                                                                      | false   |
| FloatArrayValues   |                                                                                                                                                                                                                                                                      | false   |
| IntegerArrayValues |                                                                                                                                                                                                                                                                      | false   |
| LongArrayValues    |                                                                                                                                                                                                                                                                      | false   |
| SerializableValues |                                                                                                                                                                                                                                                                      | false   |
| StringArrayValues  |                                                                                                                                                                                                                                                                      | false   |
| StringValues       |                                                                                                                                                                                                                                                                      | true    |
| UniformListValues  | Supports setting of a {@code List} value. The assumption is that the {@code List} can contain arbitrary serializable values that may or may not be defined as a feature itself. As this{@code List} is "uniform" it must contain objects of the same type.           | false (supported via Schema valueList()) |
{.wide}

### Gremlin Steps

HugeGraph supports all steps of Gremlin. For complete reference information about Gremlin,
please refer to the [Apache TinkerPop 3.8.1 official documentation](https://tinkerpop.apache.org/docs/3.8.1/reference/).

| Step | Description | Documentation |
|---|---|---|
| `addE` | Add an edge between two vertices. | [addE step](https://tinkerpop.apache.org/docs/3.8.1/reference/#addedge-step) |
| `addV` | Add vertices to graph. | [addV step](https://tinkerpop.apache.org/docs/3.8.1/reference/#addvertex-step) |
| `and` | Make sure all traversals return values. | [and step](https://tinkerpop.apache.org/docs/3.8.1/reference/#and-step) |
| `as` | Step modulator for assigning variables to the step's output. | [as step](https://tinkerpop.apache.org/docs/3.8.1/reference/#as-step) |
| `by` | Step modulators used in conjunction with `group` and `order`. | [by step](https://tinkerpop.apache.org/docs/3.8.1/reference/#by-step) |
| `coalesce` | Returns the first traversal that returns a result. | [coalesce step](https://tinkerpop.apache.org/docs/3.8.1/reference/#coalesce-step) |
| `constant` | Returns a constant value. Used in conjunction with `coalesce`. | [constant step](https://tinkerpop.apache.org/docs/3.8.1/reference/#constant-step) |
| `count` | Returns a count from the traversal. | [count step](https://tinkerpop.apache.org/docs/3.8.1/reference/#count-step) |
| `datetime` | Creates a datetime object or retrieves current server time (returns `OffsetDateTime`). | [datetime function](https://tinkerpop.apache.org/docs/3.8.1/reference/#gremlin-groovy-differences) |
| `dedup` | Returns values with duplicates removed. | [dedup step](https://tinkerpop.apache.org/docs/3.8.1/reference/#dedup-step) |
| `discard` | Discards all current traversers (replaces parameterless `none()`). | [discard step](https://tinkerpop.apache.org/docs/3.8.1/reference/#discard-step) |
| `drop` | Discards a value (vertex/edge). | [drop step](https://tinkerpop.apache.org/docs/3.8.1/reference/#drop-step) |
| `fold` | Acts as a barrier for computing aggregated values from results. | [fold step](https://tinkerpop.apache.org/docs/3.8.1/reference/#fold-step) |
| `group` | Groups values based on specified labels. | [group step](https://tinkerpop.apache.org/docs/3.8.1/reference/#group-step) |
| `has` | Used to filter properties, vertices, and edges. Supports `hasLabel`, `hasId`, `hasNot`, and `has` variants. | [has step](https://tinkerpop.apache.org/docs/3.8.1/reference/#has-step) |
| `inject` | Injects values into the stream. | [inject step](https://tinkerpop.apache.org/docs/3.8.1/reference/#inject-step) |
| `is` | Used to filter by a Boolean expression. | [is step](https://tinkerpop.apache.org/docs/3.8.1/reference/#is-step) |
| `limit` | Used to limit the number of items in a traversal. | [limit step](https://tinkerpop.apache.org/docs/3.8.1/reference/#limit-step) |
| `local` | Locally wraps a part of a traversal, similar to a subquery. | [local step](https://tinkerpop.apache.org/docs/3.8.1/reference/#local-step) |
| `not` | Used to generate the negation result of a filter. | [not step](https://tinkerpop.apache.org/docs/3.8.1/reference/#not-step) |
| `optional` | Returns the result of a specified traversal if it generates any results, otherwise returns the calling element. | [optional step](https://tinkerpop.apache.org/docs/3.8.1/reference/#optional-step) |
| `or` | Ensures that at least one traversal returns a value. | [or step](https://tinkerpop.apache.org/docs/3.8.1/reference/#or-step) |
| `order` | Returns results in the specified order. | [order step](https://tinkerpop.apache.org/docs/3.8.1/reference/#order-step) |
| `path` | Returns the full path of the traversal. | [path step](https://tinkerpop.apache.org/docs/3.8.1/reference/#path-step) |
| `project` | Projects properties as a map. | [project step](https://tinkerpop.apache.org/docs/3.8.1/reference/#project-step) |
| `properties` | Returns properties with specified labels. | [properties step](https://tinkerpop.apache.org/docs/3.8.1/reference/#properties-step) |
| `range` | Filters based on a specified range of values. | [range step](https://tinkerpop.apache.org/docs/3.8.1/reference/#range-step) |
| `repeat` | Repeats a step a specified number of times. Used for looping. | [repeat step](https://tinkerpop.apache.org/docs/3.8.1/reference/#repeat-step) |
| `sample` | Used to sample results returned by the traversal. | [sample step](https://tinkerpop.apache.org/docs/3.8.1/reference/#sample-step) |
| `select` | Used to project the results returned by the traversal. | [select step](https://tinkerpop.apache.org/docs/3.8.1/reference/#select-step) |
| `mergeV` | Matches vertices by property; updates if present, creates if absent (standard upsert). | [mergeV step](https://tinkerpop.apache.org/docs/3.8.1/reference/#mergevertex-step) |
| `mergeE` | Matches edges by property and endpoints; updates if present, creates if absent (standard upsert). | [mergeE step](https://tinkerpop.apache.org/docs/3.8.1/reference/#mergeedge-step) |
| `tree` | Aggregate the paths in vertices into a tree. | [tree step](https://tinkerpop.apache.org/docs/3.8.1/reference/#tree-step) |
| `unfold` | Unfolds an iterator as a step. | [unfold step](https://tinkerpop.apache.org/docs/3.8.1/reference/#unfold-step) |
| `union` | Combines the results of multiple traversals. | [union step](https://tinkerpop.apache.org/docs/3.8.1/reference/#union-step) |
| `V` | Traversal steps between vertices and edges: `V`, `E`, `out`, `in`, `both`, `outE`, `inE`, `bothE`, `outV`, `inV`, `bothV`, and `otherV` | [vertex steps](https://tinkerpop.apache.org/docs/3.8.1/reference/#vertex-steps) |
| `where` | Filters traversal results. Supports `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, and `between` operators. | [where step](https://tinkerpop.apache.org/docs/3.8.1/reference/#where-step) |
{.wide .expand}

### Numeric Literal Coercion in Gremlin-Groovy Predicates

In Gremlin-Groovy, an unsuffixed decimal literal such as `1.0` or `1.5` is parsed as
`java.math.BigDecimal`, and an unsuffixed integer literal such as `1` is parsed as
`java.lang.Integer`. Before executing `has` predicates (`P.eq`, `P.neq`, `P.lt`, `P.lte`,
`P.gt`, `P.gte`, `P.between`, `P.within`, `P.without`), HugeGraph converts predicate values
to the target `PropertyKey` schema type (`TraversalUtil.convAllHasSteps` →
`validPropertyValue` → `DataType.valueToNumber`) and flattens `IN` / `NOT_IN` conditions into
value-compared `EQ` / `NEQ` relations (`ConditionQueryFlatten` / `NumericUtil.compareNumber`):

- **`DOUBLE` and `FLOAT` properties:** Both integer literals (`1`) and decimal literals
  (`1.0`, `1.5`) convert by numeric value via `Double.valueOf(value.toString())` /
  `Float.valueOf(value.toString())`. An unsuffixed predicate such as
  `has('weight', P.within(1.0))` or `has('weight', P.lt(1.5))` matches a stored `DOUBLE`
  `1.0d` when `weight` is indexed.
- **`LONG`, `INT`, and `BYTE` properties:** Integer literals within range convert via
  `Long.valueOf` / `Integer.valueOf` / `Byte.valueOf`, whereas decimal literals such as `1.0`
  (`BigDecimal`) fail integer parsing and throw `IllegalArgumentException`.
- **Index requirement:** Filtering `g.V()` or `g.E()` by a user property requires an index on
  that property key (for example, a `.range()` index on numeric properties); without an index,
  HugeGraph throws `NoIndexException` regardless of literal suffix.

Using explicit Groovy numeric suffixes or casts (`d`/`D` for `DOUBLE`, `f`/`F` for `FLOAT`,
`L` for `LONG`, `(byte)` for `BYTE`) passes the target Java numeric class directly without
intermediate string conversion:

| Schema DataType | Java Runtime Class | Explicit Groovy Literal | Indexed Query Example |
|-----------------|--------------------|-------------------------|-----------------------|
| `DOUBLE` (`asDouble()`) | `java.lang.Double` | `1.0d` / `1.5D` (or `(double) 1.0`) | `g.E().has('weight', P.within(1.0d))` |
| `FLOAT` (`asFloat()`) | `java.lang.Float` | `1.0f` / `1.5F` (or `(float) 1.0`) | `g.V().has('score', P.within(0.5f, 1.0f))` |
| `LONG` (`asLong()`) | `java.lang.Long` | `1L` / `100L` | `g.V().has('timestamp', P.gte(1700000000L))` |
| `INT` (`asInt()`) | `java.lang.Integer` | `1` / `100` | `g.V().has('age', P.within(18, 25))` |
| `BYTE` (`asByte()`) | `java.lang.Byte` | `(byte) 1` | `g.V().has('level', P.within((byte) 1, (byte) 2))` |

```groovy
schema.propertyKey('weight').asDouble().ifNotExist().create()
schema.vertexLabel('DocVertex').useCustomizeStringId().ifNotExist().create()
schema.edgeLabel('DocEdge').sourceLabel('DocVertex').targetLabel('DocVertex').properties('weight').ifNotExist().create()
schema.indexLabel('edgeByWeight').onE('DocEdge').by('weight').range().ifNotExist().create()

// Both unsuffixed BigDecimal (1.0) and explicit Double (1.0d) match by numeric value when indexed
g.E().has('weight', P.within(1.0)).count()
g.E().has('weight', P.lt(1.5d)).count()
```

See also the [Cypher & Gremlin Comparison Matrix](/docs/language/cypher-compatibility/) and [PropertyKey REST API](/docs/clients/restful-api/propertykey/).
