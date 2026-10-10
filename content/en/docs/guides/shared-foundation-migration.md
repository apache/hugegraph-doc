---
title: "1.8.0 shared-foundation migration"
linkTitle: "1.8.0 Java and upgrade migration"
description: "Update Java imports and plugins, then prepare matching Server, PD and Store upgrades for the 1.8.0 shared-foundation changes."
weight: 8
---

The 1.8.0 shared-foundation migration changes Java imports and extension signatures, and requires Server, PD and Store to upgrade together.
Use this guide to identify affected code, rebuild your integrations and check existing data before deployment.

## Find the work that applies to you

| Your integration | What to prepare |
|---|---|
| Java code using Server IDs, schema metadata, queries or indexes | Update imports and affected signatures, then recompile against matching 1.8.0 artifacts. |
| Custom serializers, `HugeGraph` implementations or element subclasses | Adapt the SPI contracts and shared element state below. |
| Custom Gremlin imports or scripts | Replace the old `IdGenerator` class name and test packaged Gremlin startup. |
| Hubble, Java client or Computer integration | Apply the downstream exception changes when matching artifacts are available. |
| HStore deployment | Align the PD namespace, inspect legacy rebuilt indexes and upgrade all writers together. |
| Loader or another REST-only caller | Keep the independent client DTOs; migrate any actual affected Java calls. |

The implementation has merged into Server `master` through [apache/hugegraph#3270](https://github.com/apache/hugegraph/pull/3270), targeting 1.8.0.
Use matching Server, PD, Store and downstream artifacts when upgrading.
See the [source migration guide](https://github.com/apache/hugegraph/blob/master/docs/shared-foundation-migration.md)
for Java mappings and compatibility fixtures.

## Where shared code now lives

Server core and struct previously carried separate implementations of several IDs, schema types, queries, elements and codecs.
The migration gives these shared types one owner so Server and Store can use the same implementation.
`hugegraph-core` continues to run the graph engine, `hugegraph-struct` supplies shared models and codecs, and `hugegraph-common` supplies utilities.

![Core and struct once duplicated shared code; core and Store now use struct, while struct and PD use common](/images/shared-foundation/ownership.png)

*Core retains graph execution and adapters, Store retains storage and schema lifecycle, and struct/common own the shared implementations.
The arrows show shared ownership, not the full dependency tree.*

| Owner | Responsibilities |
|---|---|
| struct | IDs, schema metadata, type codes, queries, base elements, property/byte codecs, index construction and analyzers |
| core | Transactions, traversal, tasks, schema mutation, backend adapters and index update orchestration |
| Store | PD-backed schema access, listeners and cache lifecycle through `SchemaGraph`/`SchemaDriver` |
| common | JWT signing/verification, shared auth constants and RPC configuration interfaces |

The Server HStore adapter still needs PD and Store clients. Store retains its network, PD client and storage libraries.
PD and Store must not depend on core, and struct must not depend on core or PD clients.

Core and Store implement `HugeGraphSupplier` to provide schema, configuration and clock access.
Shared base elements hold state and adjacency. `HugeVertex` and `HugeEdge` retain engine behavior and wrapper identity over that same state;
property mutation, cloning, removal, expiration and loading state must propagate through it.
Core serializers retain backend adapters and delegate shared encoding.
Shared index and OLAP selection receive schema candidates and result sinks from their callers; core keeps transaction writes and backend capability checks.

## Update Java source and SPI implementations

Start with the types your code imports. This ID construction call keeps the same string value while its imports move.

**Before, using the 1.7.0 core API**

```java
import org.apache.hugegraph.backend.id.Id;
import org.apache.hugegraph.backend.id.IdGenerator;

Id vertexId = IdGenerator.of("vertex-1");
```

**After, using the shared API**

```java
import org.apache.hugegraph.id.Id;
import org.apache.hugegraph.id.IdGenerator;

Id vertexId = IdGenerator.of("vertex-1");
```

Recompile the application and its plugins after adapting source. Relocated types also change method descriptors,
so editing imports cannot make an old compiled jar binary-compatible. Removed core classes have no general compatibility package.
The [plugin examples](/docs/guides/custom-plugin/) still describe 1.7.0; apply the following mappings when targeting the migrated API.

| Previous Java entry | Use in the migrated API |
|---|---|
| Shared types listed below in `org.apache.hugegraph.backend.id` | `org.apache.hugegraph.id.*` |
| `org.apache.hugegraph.schema.*` metadata | `org.apache.hugegraph.struct.schema.*` |
| Shared types listed below in `org.apache.hugegraph.backend.query` | `org.apache.hugegraph.query.*` |
| `org.apache.hugegraph.backend.query.serializer.*` | `org.apache.hugegraph.query.serializer.*` |
| `org.apache.hugegraph.backend.store.Shard` | `org.apache.hugegraph.backend.Shard` |
| `org.apache.hugegraph.backend.store.BackendEntry.BackendColumn` | `org.apache.hugegraph.backend.BackendColumn` |
| `org.apache.hugegraph.structure.HugeIndex` | `org.apache.hugegraph.structure.Index` |
| Shared byte/encoding code in backend serializers | `org.apache.hugegraph.serializer.*` |
| Core `HugeException` | `org.apache.hugegraph.exception.HugeException` |
| `org.apache.hugegraph.SchemaGraph`/`SchemaDriver` | `org.apache.hugegraph.store.schema.*` |

Only `Id`, `IdGenerator`, `EdgeId`, `IdUtil` and `SplicingIdGenerator` move from the ID package.
`SnowflakeIdGenerator` remains in core under `org.apache.hugegraph.backend.id`; retain its existing import.
The moved query types are `Query`, `ConditionQuery`, `Condition`, `IdQuery`, `IdPrefixQuery`, `IdRangeQuery`, `BatchConditionQuery` and `Aggregate`.
`QueryResults`, `ConditionQueryFlatten`, `EdgesQueryIterator`, `QueryBatch` and `QueryResultContext` remain in core under
`org.apache.hugegraph.backend.query`; retain their existing imports.

`SchemaManager`, schema mutation builders and backend-specific serializers remain in core, so apply these mappings only to affected types.
Client REST DTOs remain independent, including Toolchain's `org.apache.hugegraph.structure.graph.Shard`.

| Extension point | Change in your implementation |
|---|---|
| `HugeGraph.sameAs(HugeGraph)` | Override `sameAs(org.apache.hugegraph.HugeGraphSupplier)`. There is no old-signature overload. |
| `GraphSerializer.writeIndex`/`readIndex` | Accept/return shared `org.apache.hugegraph.structure.Index`; update callers too. |
| Custom `HugeElement` subclass | Expose shared `BaseElement` through `element()` and adapt properties through `wrapProperty`. |

Keep element adapters on the shared state; do not restore removed engine state fields or add a second adjacency collection.
For Gremlin `classImports` and scripts, replace `org.apache.hugegraph.backend.id.IdGenerator` with `org.apache.hugegraph.id.IdGenerator`.
Configuration-only class names need a packaged Gremlin startup check; Java compilation does not exercise them.

The RPC interfaces `org.apache.hugegraph.rpc.RpcServiceConfig4Client` and `RpcServiceConfig4Server` now have one owner in common.
Their names and signatures stay the same, so this move requires no RPC import or configuration change.
`org.apache.hugegraph.auth.TokenGenerator` also belongs to common. Callers supply the signing secret and map JWT failures to their service responses.
Common's JWT dependencies are optional; direct JWT consumers must declare their required libraries.

### Adapt downstream exceptions when matching artifacts are available

| Previous downstream entry | Replacement |
|---|---|
| Hubble `org.apache.hugegraph.exception.HugeException` | `org.apache.hugegraph.exception.HubbleException` |
| Java client `org.apache.hugegraph.exception.NotSupportException` | `org.apache.hugegraph.exception.ClientNotSupportException` |
| Hubble's copy of `org.apache.hugegraph.license.MachineInfo` | Keep the import and use the common implementation. |

Update constructors and catch clauses along with imports. `HubbleException` keeps its `RuntimeException` parent and string constructor.
`ClientNotSupportException` keeps its `ClientException` parent and message/cause and message/arguments constructors.
Computer's `HgkvDirImpl` is one affected client-exception caller. Struct's similarly named exceptions have different contracts.
Loader's REST boundary and independent client DTOs do not need an overall conversion to struct.

The Toolchain and Computer changes are still unpublished downstream handoffs. They need matching publication, builds and packaged-classpath checks.
Inspect the built jars as well as the source tree for stale or transitive copies of the same class.

## Prepare a coordinated service upgrade

Upgrade Server, PD and Store together to matching release artifacts. This migration does not support mixed-version rolling upgrades.
The sequence below applies once those matching artifacts are available.

![Back up data, adapt Java code, upgrade matching services and verify; OLAP rows use property and vertex keys](/images/shared-foundation/migration.png)

*Back up data/configuration and check affected indexes, update imports/SPI and recompile, then upgrade matching services and align the PD namespace.
Verify packaged services and graph reads/writes. OLAP keys change from one row per vertex to one row per property and vertex;
matching legacy rows remain readable, overwritten values cannot be recovered, and mixed-version rolling upgrades are unsupported.*

1. Back up graph data with the existing [backup and restore procedure](/docs/guides/backup-restore/) and preserve deployment configuration.
2. Prepare matching Server, PD and Store artifacts, plus rebuilt plugins and any required downstream integrations.
3. Align the metadata namespace using the settings below; preserve existing backend graph names.
4. Rehearse in a validation environment. Start the packaged services, read historical data and exercise affected queries and writes.
5. Pause writes for the coordinated deployment upgrade. Resume only after all Server and Store writers use matching artifacts and checks pass.

The consolidation does not automatically rewrite graph data, rebuild indexes or recover historical entries.
Review the compatibility cases below during the rehearsal.

### Match the PD metadata namespace

Store's `pd.cluster` defaults to `hg`. Set it in Store `application.yml` as follows.

```yaml
pd:
  cluster: hg
```

The equivalent environment variable is `PD_CLUSTER`.

| Server mode | Value that must match Store's `pd.cluster` |
|---|---|
| `usePD=true` | Server's `cluster` |
| `usePD=false` | The graph's `pd.cluster` |

This namespace covers schema, graph configuration, cache watches and TTL-cleaner metadata.
All HStore graphs in one Server process must use the same metadata namespace.
With `usePD=false`, the first HStore graph opened binds the process-wide `MetaManager` to its `pd.cluster`.
A later graph's explicit conflicting `pd.cluster` is logged and ignored; it does not create an independent namespace.
One Store process cannot share a schema driver across conflicting namespaces.
Preserve backend `graphspace/store/table` names such as `DEFAULT/hugegraph/g`; the REST identity `DEFAULT-hugegraph` is not a metadata key.

## Check data compatibility

| Data or behavior | What the migration preserves or changes |
|---|---|
| Stored IDs and properties | Existing type codes and ID/property bytes are preserved, along with configuration defaults. |
| String ID comparison | Java UTF-16 order is used consistently, including IDs loaded from UTF-8 bytes. Stored ID bytes stay the same. |
| Query JSON and supported Kryo values | Historical Java names still need legacy decoding after relocation. |
| Schema maps | Wire fields and ID identity stay the same. Primary-key and edge sort-key lists keep order and duplicates. |
| Schema endpoints | Matching redundant metadata and legacy endpoint-only maps remain readable; conflicting or malformed endpoints are rejected. |
| Ordinary schema indexes | Server-created keys keep their key/name-TTL layout. |
| Store SYSTEM-label indexes with positive expiry | Stable keys and the old 13-byte value envelope remain; the label reader recognizes that bounded envelope. |

The core SYSTEM-label writer keeps its existing bytes. This migration adds no TTL suffix to those keys and does not change prefix deletion.
Previously unsupported index-only element reconstruction remains unsupported.

Element classification also keeps the producer context through `BaseVertex.TypeContext`.

| Context | Existing system-vertex classification |
|---|---|
| `STORAGE` | `~variables` is task data. |
| `ENGINE` | `~server` and `~role_data` are server data; `~variables` is ordinary vertex data. |
| Both | `~task` and `~taskresult` are task data. |

Engine wrappers select `ENGINE`; standalone storage elements retain `STORAGE` so table routing follows the existing behavior.

### Rebuild affected legacy long-text indexes

The previous Store-side `IndexBuilder` shortened long text values to 20 characters. Server queries used the full value and its hash.
The shared builder now follows the Server contract. An old shortened row can still be decoded, but it does not automatically match a full-value query.

If your deployment used Store-side index rebuilding, identify affected indexes and rebuild them from graph data where necessary.
The migration performs no automatic rebuild and cannot recover missing historical entries. Ordinary Server-created index keys retain their existing contract.

### Verify HStore OLAP reads and deletes

New OLAP rows use `[property ID][vertex ID]` keys, allowing several OLAP properties on one vertex to coexist.
Legacy rows used only the vertex ID; their values remain readable without a rewrite.

| Operation | Behavior with compound and legacy keys |
|---|---|
| Read a property | Prefer its compound key. Fall back to a vertex-only row only when its value contains the requested property ID. |
| Delete a property | Remove its compound row and a matching legacy row; preserve other properties. |
| Read a property already overwritten by the old writer | The lost value cannot be recovered by this repair. |

Upgrade all Server and Store writers before resuming writes. An old writer can update a legacy row while a new reader prefers an existing compound row.
Mixed-version OLAP writes are outside the supported upgrade contract.

## Verify packaged services and integrations

Run affected Java/SPI tests, then exercise RocksDB and HStore queries, authentication, Store schema/filter behavior and shared element state propagation.
Include historical ID, schema, property and index samples, pagination, TTL and OLAP cases.
Inspect resolved dependencies and shipped jars for forbidden module dependencies or duplicate HugeGraph classes,
and start the actual packaged services without classpath-ordering workarounds.
The [contribution guide](/docs/contribution-guidelines/contribute/) describes build and dependency-inventory prerequisites.

The implementation, website documentation and downstream artifacts need coordinated publication.
Use matching artifacts and their runtime results to decide when to adopt the migration; compiling source or skipping tests is insufficient.
