---
title: "HugeGraph 1.8.0 Gremlin Migration & Compatibility Guide"
linkTitle: "1.8 Gremlin & TinkerPop Migration"
description: "Comprehensive guide to breaking changes, high-frequency syntax rewrites, configuration migrations, and complete compatibility references from TinkerPop 3.5 to 3.8 in HugeGraph 1.8.0."
weight: 9
---

HugeGraph 1.8.0 upgrades its underlying graph traversal and query framework from Apache TinkerPop 3.5.1 to **TinkerPop 3.8.1**, requires **Java 17** for Server and builds, and updates the script engine to **Groovy 4.0.25**.

This upgrade introduces several language-level breaking changes. The sections below cover the **most frequently affected syntax and behavioral changes** first; less common edge cases and lower-level protocol details are in the [Full Compatibility Reference](#full-compatibility-reference) at the end.

> [!NOTE]
> - This guide applies to upgrades from version 1.7.0 (or earlier) to 1.8.0.
> - The **Groovy script engine** remains supported in 1.8.0; existing multi-line scripts, variable definitions, and Java closures continue to work in most cases.

---

## Top 5 High-Frequency Syntax and Behavioral Changes

The following 5 changes affect the most queries. Changes 1–3 cause immediate execution errors if not rewritten; changes 4–5 do not raise errors but silently alter returned results (dropping elements with missing properties or passing unmatched branches through). Review these first.

### 1. `has(key, traversal)` Overload Removed (High Risk: Execution Error)

* **Impact**:
  In TinkerPop 3.8.0, the `has(String, Traversal)` and `has(T, Traversal)` overloads were removed.
  In the Groovy script engine, legacy syntax falls back to `has(String, Object)`. On HugeGraph 1.8, because the graph engine pushes `has()` predicates down into backend queries and validates values with `TraversalUtil.validPropertyValue()`, **it fails immediately with type mismatch errors**:
  - Property filter `g.V().has('age', __.is(gt(30)))` throws:
    `IllegalArgumentException: Invalid data type of query value '[IsStep(gt(30))]', expect INT for 'age', actual got class org.apache.tinkerpop.gremlin.process.traversal.dsl.graph.DefaultGraphTraversal`
  - Label filter `g.V().has(T.label, __.is('person'))` throws:
    `HugeException: The label type must be number or string, but got 'class org.apache.tinkerpop.gremlin.process.traversal.dsl.graph.DefaultGraphTraversal'`
  *(Note: Pure in-memory TinkerGraph silently returns an empty array `[]`, whereas HugeGraph 1.8 fails strictly).*
* **Legacy Query**:
  ```groovy
  // Broken on HugeGraph 1.8: throws Invalid data type exception
  g.V().has('age', __.is(gt(30)))
  g.V().has(T.label, __.is('person'))
  ```
* **Recommended Rewrite**:
  ```groovy
  // For simple scalar/predicate checks, pass predicates directly
  g.V().has('age', gt(30))
  g.V().hasLabel('person')
  g.V().hasId('v-1')

  // If passing property values into child traversals for complex filtering, use filter()
  g.V().filter(__.values('age').is(gt(30)))
  ```

---

### 2. `store()` Removed & `aggregate()` Scope Overload Removed

* **Impact**:
  - The `store('x')` step, previously used for lazy side-effect collection, has been completely removed (`MissingMethodException: No signature of method: ...store()`).
  - The `aggregate(Scope, 'x')` overload with an explicit `Scope` (both `local` and `global`) has also been removed.
* **Legacy Query**:
  ```groovy
  // Broken: store step removed
  g.V().store('x').by('age').cap('x')

  // Broken: aggregate(Scope, ...) overload removed
  g.V().aggregate(local, 'x')
  g.V().aggregate(global, 'x')
  ```
* **Recommended Rewrite**:
  ```groovy
  // 1. Eager global collection (formerly global aggregate): use aggregate('x') directly
  g.V().aggregate('x').by('age').cap('x')

  // 2. Per-object / lazy collection (formerly store or local aggregate): wrap in local()
  g.V().local(__.aggregate('x').by('age')).cap('x')
  ```

---

### 3. Step `none()` Renamed to `discard()`

* **Impact**:
  In TinkerPop 3.5.1, only the traversal step `g.V().none()` existed (which returned an empty result); anonymous `__.none()` was not supported.
  In 3.8.0, parameterless `none()` was completely renamed to **`discard()`**, while `none(P)` was repurposed as a collection predicate step.
  Calling parameterless `none()` in 3.8.1 (such as `g.V().hasLabel('person').none()`) throws:
  `IllegalArgumentException: Input predicate to none step can't be null.`
* **Recommended Rewrite**:
  ```groovy
  // Legacy (dropped results on 3.5.1, throws predicate can't be null on 3.8.1)
  g.V().hasLabel('person').none()

  // Rewritten: use discard()
  g.V().hasLabel('person').discard()

  // In choose() or branches, discard unhandled and missing-property inputs:
  g.V().choose(__.values('age'))
    .option(gt(30), __.values('name'))
    .option(Pick.none, __.discard())
    .option(Pick.unproductive, __.discard())
  ```

---

### 4. Strict Behavior for Missing Properties in `by()`

* **Impact**:
  TinkerPop 3.6+ unified missing value handling across `by()` modulators (removing previous default-null behaviors). In 3.8.1, when a property referenced by `by()` does not exist:
  1. **Ordering `order().by('age')`**: Vertices missing `age` are **immediately filtered out** (previously they might sort first/last).
  2. **Projection `project('name', 'age').by('name').by('age')`**: If `age` is missing, the returned Map **will not contain the `age` key at all** (previously returned `age: null`).
  3. **Path `path().by('age')`**: If any vertex along the path misses `age`, the **entire path is dropped**.
* **Recommended Rewrite**:
  If your application requires preserving elements with explicit defaults (e.g., `null`), use `coalesce()` inside `by()`:
  ```groovy
  // Retain key 'age' with null when missing
  g.V().project('name', 'age')
    .by('name')
    .by(__.coalesce(__.values('age'), __.constant(null)))

  // Provide a typed default for sorting missing fields
  g.V().order().by(__.coalesce(__.values('age'), __.constant(-1)), desc)
  ```

---

### 5. `choose()` Semantics Alignment

* **Impact**:
  - **Missing Property Handling**: When a choice child traversal evaluated an absent property on an element, TinkerPop 3.5.1 threw:
    `IllegalArgumentException: The provided traverser does not map to a value: v[3]->[PropertiesStep([age],value)]`.
    In 3.8.1, elements missing the target property pass through unchanged without error.
  - **Single Branch Execution**: When multiple `option()` conditions match simultaneously, 3.8.1 **executes only the first matching branch** (legacy versions might execute all matching branches).
  - **Default Pass-Through**: When no `option()` condition matches, 3.8.1 **passes the input element through unchanged** by default (whereas 3.5.1 filtered it out).
* **Recommended Rewrite**:
  - To execute multiple matching branches, rewrite using `union()` combined with `filter()`.
  - To filter out elements when no option matches or property is missing, explicitly supply `Pick.none` and `Pick.unproductive` branches:
  ```groovy
  // Discard unmatched and missing-property inputs
  g.V().choose(__.values('age'))
    .option(gt(30), __.values('name'))
    .option(Pick.none, __.discard())
    .option(Pick.unproductive, __.discard())
  ```

---

## New Steps & Functions in 1.8 (TinkerPop 3.8)

TinkerPop 3.8 introduces native date manipulation functions and steps that were not present in 3.5.1 (HugeGraph 1.7.0):

### Date Steps (`datetime()`, `dateAdd()`, `dateDiff()`)

- **`datetime()`**: Creates a date-time object or retrieves server time.
  In 3.8, it returns **`java.time.OffsetDateTime`** (e.g., `datetime('2026-10-19T00:00:00Z')`).
- **`dateAdd()`**: Performs date arithmetic, adding a duration to a date.
- **`dateDiff()`**: Computes the difference between two date-time objects, returning the difference in **milliseconds**
  (e.g., a 1-day difference yields `86400000` ms).
- **Example**:
  ```groovy
  // Current time as OffsetDateTime
  g.inject(datetime())

  // Compute difference in milliseconds, convert to seconds
  g.inject(datetime('2026-10-19T00:00:00Z')).dateDiff(datetime('2026-10-18T00:00:00Z'))
    .math('_ / 1000').asNumber(GType.LONG)
  ```

---

## Server Configuration and Client Compatibility

### 1. Serializer Configuration in `conf/gremlin-server.yaml`

In TinkerPop 3.8, serializer classes moved from `gremlin-driver` (`org.apache.tinkerpop.gremlin.driver.ser.*`)
to `gremlin-util` (`org.apache.tinkerpop.gremlin.util.ser.*`).

> [!IMPORTANT]
> **Do not simply copy an old `gremlin-server.yaml` from 1.7.0 and edit class names.**
> Always start from the `conf/gremlin-server.yaml` bundled with HugeGraph 1.8.0 and carry over your customizations (ports, host, authenticator).
> HugeGraph requires custom serializer builders and registries: GraphBinary requires `builder: org.apache.hugegraph.io.HugeGraphTypeSerializerRegistryBuilder`
> to serialize HugeGraph `Id`, schema, `Blob`, and enum values (otherwise failing with `IOException: Serializer for type ... not found`);
> untyped GraphSON V1 requires `org.apache.hugegraph.io.HugeGraphSONV1MessageIoRegistry`.

| Legacy Serializer (`driver.ser.*`) | 1.8.0 Serializer (`util.ser.*`) | Required Registries / Builder | Notes |
|---|---|---|---|
| `GraphBinaryMessageSerializerV1` | `org.apache.tinkerpop.gremlin.util.ser.GraphBinaryMessageSerializerV1` | `builder: org.apache.hugegraph.io.HugeGraphTypeSerializerRegistryBuilder`<br>`ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]` | Recommended default binary serializer |
| `GraphSONMessageSerializerV1d0` | `org.apache.tinkerpop.gremlin.util.ser.GraphSONUntypedMessageSerializerV1` | `ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry, org.apache.hugegraph.io.HugeGraphSONV1MessageIoRegistry]` | Untyped GraphSON V1 |
| `GraphSONMessageSerializerV2d0` | `org.apache.tinkerpop.gremlin.util.ser.GraphSONMessageSerializerV2` | `ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]` | Standard Typed GraphSON V2 |
| `GraphSONMessageSerializerV3d0` | `org.apache.tinkerpop.gremlin.util.ser.GraphSONMessageSerializerV3` | `ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]` | Standard Typed GraphSON V3 |
| *(New in 1.8)* | `org.apache.tinkerpop.gremlin.util.ser.GraphSONUntypedMessageSerializerV2` | `ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]` | Untyped GraphSON V2 (`types=false`) |
| *(New in 1.8)* | `org.apache.tinkerpop.gremlin.util.ser.GraphSONUntypedMessageSerializerV3` | `ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]` | Untyped GraphSON V3 (`types=false`) |
{.td-table--wide}

### 2. Can HugeGraph Client 1.5.0 Continue to Work?
* **Verdict**: **Basic CRUD and schema operations continue to work; Gremlin queries and auth management require upgrading or custom aliases**.
* HugeGraph Server 1.8.0 provides backward-compatible adapters, allowing `hugegraph-client:1.5.0` to connect for standard vertex/edge CRUD and schema management.
* **Limitations**:
  - **Gremlin Aliases**: `hugegraph-client:1.5.0` sends legacy graph and traversal aliases (`graph=<graph>` and `g=__g_<graph>`), but Server 1.8.0 only binds GraphSpace-scoped aliases (`DEFAULT-<graph>` and `__g_DEFAULT-<graph>`). Because `/gremlin` passes the body unchanged, Gremlin queries sent via `gremlin().execute()` in Client 1.5.0 fail on unknown aliases. To run Gremlin queries against 1.8.0, upgrade the client or submit queries via the HTTP API with explicit GraphSpace aliases.
  - **Auth Paths**: Server 1.8.0 migrates authentication to GraphSpace scopes (`graphspaces/{graphspace}/auth/users`). The legacy Client 1.5.0 path `graphs/{graph}/auth/...` is not redirected to this new endpoint, so auth operations require upgrading the client.
  - **Gremlin Query Strings**: All Gremlin query strings submitted by the client are evaluated on the server's 3.8.1 engine and must adhere to 3.8 syntax.

---

## Full Compatibility Reference

### Appendix 1: Writes & Upsert (`mergeV` / `mergeE`)
HugeGraph 1.8.0 (introduced upstream in TinkerPop 3.6.0) supports standard `mergeV()` and `mergeE()` steps for graph upserts:
- **M01**: `onCreate` property maps strictly inherit the search match map. Conflicting keys cannot overwrite matched properties.
- **M02**: `mergeE` no longer implicitly binds incoming/outgoing vertices from upstream traversers; specify `Direction.OUT` and `Direction.IN` in the map or use explicit options.
- **M03**: Construction-time validation applies when a static `onCreate` map attempts to override keys defined in the search-criteria match map.
- **M04**: Child traversers in `onMatch` receive the matched Element object rather than the original input Map. Preserve input map references prior to merge with `.as('input')` and reference with `select('input')`.

### Appendix 2: Advanced Traversal Steps & Collections
- **B07 (`local()` unpacks bulk)**: Traversers with bulk counters are expanded into individual items when entering `local()` child traversals. Use `groupCount()` for frequency analysis.
- **B09 (`range(local)` collection unpacking)**: Slicing a single item from a list (e.g., `limit(local, 1)`) consistently returns a Collection wrapper (`[item]`). Append `.unfold()` if a scalar is needed.
- **B11 (`sum()` return type)**: Summing integer streams without overflow may return `Integer` instead of `Long`. Clients should accept `Number`.
- **B14 (`split()` step)**: HugeGraph 1.8 new step. An empty string separator splits the string into individual characters.
- **B15 (`asString()` step)**: HugeGraph 1.8 new step. Throws `IllegalArgumentException` on null inputs.

### Appendix 3: GLV Client Variations
- **Python**: Avoids Python keyword conflicts by appending an underscore to step names (`filter_()`, `id_()`, `range_()`, `max_()`).
- **JavaScript**: Set collections are returned as native ECMAScript `Set` instances (use `.size` and `.has()`). Deprecated `connectOnStartup` option removed; call `await connection.open()`.
- **.NET**: `byte` values serialize strictly as signed bytes (`sbyte`).
- **Go**: BigDecimal/BigInt aligned; always inspect errors on `Next()`.

### Appendix 4: Network Protocols & Serializer Guardrails
- **C03 (OLTP element properties)**: Remote OLTP queries return elements with full properties by default rather than reference tokens only. Use `project()` or `valueMap()` to restrict payload sizes when necessary.
- **C06 (GraphSON payload limits)**: Added guardrails for max number length (10,000), max string length (20,000,000), and max nesting depth (1,000).

### Appendix 5: HugeGraph Feature Capabilities
- **Meta-Properties Unchanged (Unsupported)**: HugeGraph has never supported TinkerPop meta-properties (properties on properties).
  Calling `property()` with key-values on a vertex property throws `VertexProperty.Exceptions.metaPropertiesNotSupported()`
  or `NotSupportException("nested property")`, which remains the unchanged behavior in 1.8.0.
- **GraphComputer Boundaries**: `supportsComputer()` remains `false`. GraphComputer-dependent steps (e.g., `pageRank()`, `peerPressure()`) cannot run directly on the OLTP engine. Use HugeGraph algorithms REST API or Vermeer.
- **Uniform List Features**: `supportsUniformListValues()` returns `false`; property lists remain supported via HugeGraph schema (`valueList()`).
