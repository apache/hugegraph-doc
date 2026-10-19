---
title: "HugeGraph 1.8.0 Gremlin Migration & Compatibility Guide"
linkTitle: "1.8 Gremlin & TinkerPop Migration"
description: "Comprehensive guide to breaking changes, high-frequency syntax rewrites, configuration migrations, and complete compatibility references from TinkerPop 3.5 to 3.8 in HugeGraph 1.8.0."
weight: 9
---

HugeGraph 1.8.0 upgrades its underlying graph traversal and query framework from Apache TinkerPop 3.5.1 to **TinkerPop 3.8.1**, requires **Java 17** for Server and builds, and updates the script engine to **Groovy 4.0.25**.

While bringing substantial performance optimizations and specification alignments, this upgrade introduces several language-level breaking changes. This guide highlights the **most critical and frequently used syntax changes** with recommended rewrites to ensure seamless migration. Edge cases and lower-level protocol details are organized in the [Full Compatibility Reference](#full-compatibility-reference) at the end.

> [!NOTE]
> - This guide applies to upgrades from version 1.7.0 (or earlier) to 1.8.0.
> - The **Groovy script engine** remains supported in 1.8.0, allowing existing multi-line scripts, variable definitions, and Java closures to continue functioning as expected.

---

## Top 6 High-Frequency Syntax and Behavioral Changes

Among existing query scripts, the following 6 changes are the most common. **Failure to update these may cause query errors or silently return empty results.**

### 1. `has(key, traversal)` Overload Removed (High Risk: Silent Empty Results)

* **Impact**:
  In TinkerPop 3.8.0, the `has(String, Traversal)` and `has(T, Traversal)` overloads were removed.
  In the Groovy script engine, legacy code will not throw a compilation error; instead, it **silently falls back to `has(String, Object)`**, comparing the anonymous traversal object itself against vertex/edge properties. In practice, this **silently yields 0 results / empty sets**!
* **Legacy Query**:
  ```groovy
  // Broken in 3.8: will not throw an error, but silently returns 0 results
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
  - The `store('x')` step, previously used for lazy side-effect collection, has been completely removed (`No signature of method: store()`).
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
  The parameterless `none()` step was originally used to discard all incoming traversers (e.g., at the end of `choose()` or `coalesce()` branches). In 3.8.0, this step is renamed to **`discard()`**.
  Meanwhile, 3.8 introduces a new collection predicate step `none(P)` (checking if no elements in a collection match predicate P). Calling parameterless `none()` in 3.8 triggers argument errors.
* **Recommended Rewrite**:
  ```groovy
  // Legacy:
  g.V().choose(__.values('age')).option(gt(30), __.values('name')).option(Pick.none, __.none()) // Error

  // Rewritten: use discard()
  g.V().choose(__.values('age')).option(gt(30), __.values('name')).option(Pick.none, __.discard())
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
  - **Single Branch Execution**: When multiple `option()` conditions match simultaneously, 3.8 **executes only the first matching branch** (legacy versions might execute all matching branches).
  - **Default Pass-Through**: If the choice child traversal yields no values (e.g., property missing) or no `option()` matches, 3.8 **passes the input element through unchanged** by default (legacy versions often filtered it out).
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

### 6. Date Types and Time Difference Units

* **Impact**:
  - **Return Type**: Date steps such as `datetime()` and `dateAdd()` now return **`java.time.OffsetDateTime`** instead of `java.util.Date`.
  - **Unit Change in `dateDiff()`**: The difference between two dates is now returned in **milliseconds** instead of seconds (e.g., 1 day difference is `86400000` ms instead of `86400` s).
* **Recommended Rewrite**:
  - Update Java clients to expect `OffsetDateTime`; convert to `java.util.Date` via `Date.from(offsetDateTime.toInstant())` only if strictly required.
  - Review all TTL checks and date comparisons that use `dateDiff()`. Adjust multipliers or divide by 1000:
  ```groovy
  // Convert dateDiff milliseconds to seconds
  g.inject(datetime('2026-10-19T00:00:00Z')).dateDiff(datetime('2026-10-18T00:00:00Z'))
    .math('_ / 1000').asNumber(GType.LONG)
  ```

---

## Server Configuration and Client Compatibility

### 1. Serializer Class Names and Package Migration
In `conf/gremlin-server.yaml`, serializer classes moved from `gremlin-driver` to `gremlin-util`. **You must update serializer package names in the configuration, as legacy class names will cause ClassNotFoundException**:

| Legacy Class (`driver.ser.*`) | 1.8.0 Class (`util.ser.*`) | Notes |
|---|---|---|
| `GraphBinaryMessageSerializerV1` | `org.apache.tinkerpop.gremlin.util.ser.GraphBinaryMessageSerializerV1` | Recommended default binary serializer |
| `GraphSONMessageSerializerV1d0` | `org.apache.tinkerpop.gremlin.util.ser.GraphSONUntypedMessageSerializerV1` | Retains untyped JSON (do not just remove `d0`, which becomes typed) |
| `GraphSONMessageSerializerV3d0` | `org.apache.tinkerpop.gremlin.util.ser.GraphSONMessageSerializerV3` | Standard Typed GraphSON V3 |
{.td-table--wide}

### 2. Can HugeGraph Client 1.5.0 Continue to Work?
* **Verdict**: **Yes**.
* HugeGraph Server 1.8.0 provides backward-compatible adapters (graph alias mapping and legacy auth path redirection). Applications using `hugegraph-client:1.5.0` can continue standard CRUD, schema management, and REST operations without forced SDK upgrades.
* **Important Note**: Although Client 1.5.0 connects successfully, **all submitted Gremlin script strings are executed on the 3.8.1 server engine**. Therefore, Gremlin queries constructed in your code must comply with the 3.8 rules described above.

---

## Full Compatibility Reference

### Appendix 1: Writes & Upsert (`mergeV` / `mergeE`)
- **M01**: `onCreate` property maps strictly inherit the search match map. Conflicting keys cannot overwrite matched properties.
- **M02**: `mergeE` no longer implicitly binds incoming/outgoing vertices from upstream traversers; specify `Direction.OUT` and `Direction.IN` in the map or use explicit options.
- **M03**: Conflicting `onCreate` / `onMatch` maps are validated during construction rather than deferred to runtime execution.
- **M04**: In 3.8, child traversers in `onMatch` receive the matched Element object rather than the original input Map. Preserve input map references prior to merge with `.as('input')` and reference with `select('input')`.

### Appendix 2: Advanced Traversal Steps & Collections
- **B07 (`local()` unpacks bulk)**: Traversers with bulk counters are expanded into individual items when entering `local()` child traversals. Use `groupCount()` for frequency analysis.
- **B09 (`range(local)` collection unpacking)**: Slicing a single item from a list (e.g., `limit(local, 1)`) consistently returns a Collection wrapper (`[item]`). Append `.unfold()` if a scalar is needed.
- **B11 (`sum()` return type)**: Summing integer streams without overflow may return `Integer` instead of `Long`. Clients should accept `Number`.
- **B14 (`split('')`)**: Splitting with an empty separator returns a list of individual characters.
- **B15 (`asString()` on null)**: `asString()` throws an `IllegalArgumentException` on null inputs.

### Appendix 3: GLV Client Variations
- **Python**: Avoids Python keyword conflicts by appending an underscore to step names (`filter_()`, `id_()`, `range_()`, `max_()`).
- **JavaScript**: Set collections are returned as native ECMAScript `Set` instances (use `.size` and `.has()`). Deprecated `connectOnStartup` option removed; call `await connection.open()`.
- **.NET**: `byte` values serialize strictly as signed bytes (`sbyte`).
- **Go**: BigDecimal/BigInt aligned; always inspect errors on `Next()`.

### Appendix 4: Network Protocols & Serializer Guardrails
- **C03 (OLTP element properties)**: Remote OLTP queries return elements with full properties by default rather than reference tokens only. Use `project()` or `valueMap()` to restrict payload sizes when necessary.
- **C06 (GraphSON payload limits)**: Added guardrails for max number length (10,000), max string length (20,000,000), and max nesting depth (1,000).

### Appendix 5: HugeGraph Feature Capabilities
- **Meta-Properties Unsupported**: HugeGraph strictly follows its native schema design and does not support TinkerPop meta-properties (properties on properties). Writing property metadata in 1.8.0 will be **explicitly rejected**.
- **GraphComputer Boundaries**: `supportsComputer()` remains `false`. GraphComputer-dependent steps (e.g., `pageRank()`, `peerPressure()`) cannot run directly on the OLTP engine. Use HugeGraph algorithms REST API or Vermeer.
- **Uniform List Features**: `supportsUniformListValues()` returns `false`; property lists remain supported via HugeGraph schema (`valueList()`).
