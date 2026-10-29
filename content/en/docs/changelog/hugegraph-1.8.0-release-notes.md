---
title: "HugeGraph 1.8.0 Release Notes"
linkTitle: "Release-1.8.0"
weight: 1
---

> WIP: This doc is under construction, please wait for the final version (BETA)

### Runtime & Version Requirements

- **Java Environment**: **1.8.0** HugeGraph components (Server, PD, Store) require **Java 17** for runtime and source builds (1.7.0 is the last release supporting Java 11).
- **Query & Script Engine**: Graph traversal framework upgraded to **Apache TinkerPop 3.8.1**, script engine upgraded to **Groovy 4.0.25**.

### Key Breaking Changes & Compatibility

#### 1. Critical Gremlin Traversal Breaking Changes
- **Removed `has(key, traversal)` overload**: In Groovy on HugeGraph 1.8, legacy syntax fails immediately with an `Invalid data type of query value` exception due to strong type checks (pure TinkerGraph returns empty results). Use `has('age', gt(30))` for simple conditions, or `filter(__.values('age').is(gt(30)))` for child traversals.
- **Removed `store()` & scoped `aggregate()`**: Use `aggregate('x')` for global eager collection; use `local(__.aggregate('x'))` for lazy or per-object collection.
- **Step `none()` renamed to `discard()`**: Discarding incoming traversers must now use `discard()` (avoids collision with new collection predicate `none(P)`).
- **Strict `by()` behavior on missing properties**: Vertices missing properties are dropped in `order().by()`; keys are omitted from maps in `project().by()`; paths are discarded in `path().by()`. Wrap with `coalesce()` to provide explicit defaults if preservation is needed.
- **`choose()` semantics alignment**: Executes only the first matching branch when conditions overlap; passes elements through unchanged by default when no branch matches or values are absent.

> For comprehensive query comparison examples and the full migration checklist, see the [HugeGraph 1.8.0 Gremlin Migration & Compatibility Guide](../guides/gremlin-migration-3.8).

#### 2. Server Configuration & Client Compatibility
- **Serializer class names**: Serializer packages in `conf/gremlin-server.yaml` moved from `org.apache.tinkerpop.gremlin.driver.ser.*` to `org.apache.tinkerpop.gremlin.util.ser.*`.
- **HugeGraph Client 1.5.0**: Basic CRUD and schema operations are backward-compatible on Server 1.8.0; however, Gremlin queries fail due to missing GraphSpace aliases, and auth paths require upgrading the client or using HTTP endpoints.
- **GPL word analyzer no longer bundled**: `word-1.3.jar` is no longer bundled by default due to license compliance.
  Graphs configured with `search.text_analyzer=word` remain supported once `word-1.3.jar` is placed in Server's `lib/` directory.
  Alternatively, switch to IK or SmartCN (note that switching analyzers requires rebuilding search indexes).

---

### hugegraph

#### API Changes
- **BREAKING CHANGE**: Upgrade TinkerPop to 3.8.1 and require Java 17 runtime
- **BREAKING CHANGE**: Shared foundation module migration (`hugegraph-struct`)

#### Feature Changes
- Support TinkerPop 3.8 steps including `discard()`, `mergeV()`, `mergeE()`, and date steps (`datetime()`, `dateAdd()`, `dateDiff()`)
- Adapt HugeSecurityManager and Groovy 4.0.25 on Java 17
- Improve count query visibility inside uncommitted transactions
