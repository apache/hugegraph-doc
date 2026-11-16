---
title: "Configuring the HStore Distributed Backend"
linkTitle: "Config HStore Backend"
weight: 6
search_keywords:
  - hstore
  - pd.peers
  - usePD
  - hstore.partition_count
---

### 1 Overview

`hstore` is the distributed storage backend of HugeGraph. When a graph uses it, HugeGraph-Server keeps no
graph data on its own disk. Two other processes do that work:

- **HugeGraph-PD** (Placement Driver) owns the cluster metadata: the registered store list, the partition
  layout of every graph, the partition to store mapping, the graph schema and the schema id counters.
- **HugeGraph-Store** owns the key value data itself, replicated across store nodes with Raft.

Server links a PD client and a Store client into its own process. For every read and write it asks PD which
partition owns the key and which store node currently leads that partition, then sends the request directly
to that store node.

The server side adapter is the `hugegraph-hstore` module. It registers under the backend name `hstore` and
reports driver version `1.13`.

Selecting `hstore` changes more than where the bytes are written. Server switches these behaviors on the
backend type:

| Area                  | With `hstore`                                                           | With a local backend          |
|-----------------------|-------------------------------------------------------------------------|-------------------------------|
| Schema storage        | Schema is read and written through the PD meta driver                   | Schema lives in the `m` store |
| Schema ids            | Allocated by PD through the PD client                                   | Allocated by the schema store |
| System store          | None, system data goes to the graph store                               | Separate `s` store            |
| Task scheduler        | `distributed`                                                           | `local`                       |
| Auth manager          | `StandardAuthManagerV2`                                                 | `StandardAuthManager`         |
| Backend version check | Reads the graph store                                                   | Reads the system store        |
| `init-store.sh`       | Skips the graph, PD and Store already own the metadata                  | Creates the local store       |

### 2 Prerequisites

`hstore` is not self contained. A PD cluster and at least one Store node must be running before Server opens
an `hstore` graph, and they have to be started in this order:

1. **PD**, so that it can form its Raft group.
2. **Store**, which registers itself with PD over gRPC. A store whose gRPC address is listed in PD's own
   `pd.initial-store-list` goes to state `Up` right away. A store that is not in that list, and that PD has
   never seen `Up` or `Offline` before, registers as `Pending` and has to be activated before it serves data.
3. **Server**, which then reads the store list back out of PD.

Default ports the Server side needs to know about:

| Process | gRPC port | REST port |
|---------|-----------|-----------|
| PD      | 8686      | 8620      |
| Store   | 8500      | 8520      |

`pd.peers` on the Server side points at the PD **gRPC** port, not the REST port.

For installing and configuring the other two processes, see
[Install/Build HugeGraph-PD](/docs/quickstart/hugegraph/hugegraph-pd/) and
[Install/Build HugeGraph-Store](/docs/quickstart/hugegraph/hugegraph-hstore/).

### 3 Selecting the hstore backend

#### 3.1 Graph configuration file

Set the backend in the graph properties file, for example `conf/graphs/hugegraph.properties`:

```ini
backend=hstore
serializer=binary
store=hugegraph
pd.peers=127.0.0.1:8686
```

Notes on those four keys:

- `backend=hstore` selects the adapter. Since 1.7.0 the allowed values are `memory`, `rocksdb`, `hbase` and
  `hstore`. The value is compared case insensitively where the distribution checks it.
- `serializer=binary` is required. Registering the `hstore` backend adds a config space and a store provider
  but no serializer of its own, and the adapter is written against the binary serializer. The built-in default
  of `serializer` is `text`, so this value has to be written out.
- `store=hugegraph` is the namespace part of the name PD sees. Server opens the provider with
  `<graphspace>/<store>` and each backing store appends its own suffix, so PD ends up with one graph entry per
  store: `DEFAULT/hugegraph/g` for graph data and `DEFAULT/hugegraph/m` for the schema store slot.
  `graphspace` defaults to `DEFAULT`, while `g` and `m` are fixed.
- `pd.peers` is the comma separated list of PD gRPC addresses. The adapter reads it from the **graph** config,
  not from `rest-server.properties`, and the graph level metadata connection uses the same value.

If the graph file does not contain `pd.peers`, Server copies the value from `rest-server.properties` into the
graph config while loading the graph, provided that `usePD` is true or the backend is `hstore`. Writing the
key explicitly in the graph file is still the clearer option.

#### 3.2 rest-server.properties

```ini
# use pd
usePD=true
pd.peers=127.0.0.1:8686
```

`usePD=true` makes the Server load its metadata from PD at startup. On that path it connects the meta manager
to PD, creates the built-in admin account and the default graph space, loads the graph spaces and services,
creates the internal system graph (always with `backend=hstore`), and loads the graph configs that PD holds.

It is a separate switch from the graph level `backend=hstore`: a graph can use `hstore` with `usePD` left at
its default of `false`, and Server then never opens the PD backed metadata path. The distribution's own test
startup script sets it whenever the backend is `hstore`.

#### 3.3 The shipped template

The distribution ships a ready made graph file for this backend at
`conf/graphs/hstore.properties.template`. It matches `hugegraph.properties` except that it sets
`backend=hstore`, leaves `pd.peers=127.0.0.1:8686` uncommented, and carries no memory management block.

The hstore Docker image applies that template for you: it deletes `conf/graphs/hugegraph.properties` and
renames the template over it, so a container starts with the `hstore` backend already selected.

A locally built distribution has the `hstore` provider compiled in by default. The `rocksdb-only` Maven
profile narrows the compiled backend list to `rocksdb`, and a distribution built that way rejects
`backend=hstore` with `Not exists BackendStoreProvider: hstore` after the provider factory check.

### 4 hstore config options

These are the only keys in the `hstore` config space. They belong in the graph properties file.

| config option          | default value | description                                                   |
|------------------------|---------------|---------------------------------------------------------------|
| hstore.partition_count | 0             | Number of partitions, which PD controls partitions based on.   |
| hstore.shard_count     | 0             | Number of copies, which PD controls partition copies based on. |
{.td-table--wide}

#### 4.1 hstore.partition_count

Server sends this number to PD once per graph store, the first time the store is opened, together with the
graph name. A negative value is rejected at that point with
`The value of hstore.partition_count cannot be less than 0.`

How PD reads the number:

- `0`, the default, means let PD decide. For a graph data store PD uses its own cluster wide partition total,
  which it derives from the number of entries in `pd.initial-store-list`, `partition.store-max-shard-count`
  and `partition.default-shard-count`. For the `/m` and `/s` stores it uses a fixed count of `1`.
- A value between `1` and that total is used as is.
- A value above that total is clamped down to it.

The number is applied when the store is first registered with PD, so changing it later in the properties file
does not repartition an existing graph.

#### 4.2 hstore.shard_count

`hstore.shard_count` is declared in the `hstore` config space and is accepted in the properties file, but no
code on the Server side reads it in this release: `hstore.partition_count` is the only one of the two the
adapter reads. The replica count in effect is the one PD is configured with,
`partition.default-shard-count` in PD's `application.yml`.

### 5 Other options that only apply in hstore mode

These keys live in the shared `rest-server.properties` and graph properties files, but only take effect, or
only change behavior, when PD and the `hstore` backend are in use. The source column gives the file and line
in the checked Server master commit `2f827d6` where the option is declared.

| config option                | file                   | default        | why it matters with hstore                                                                   | source                       |
|------------------------------|------------------------|----------------|----------------------------------------------------------------------------------------------|------------------------------|
| pd.peers                     | rest-server.properties | 127.0.0.1:8686 | PD addresses used for metadata, service discovery and the system graph                        | `ServerOptions.java:195-201` |
| pd.peers                     | {graph}.properties     | 127.0.0.1:8686 | PD addresses used by the backend adapter itself                                               | `CoreOptions.java:649-654`   |
| usePD                        | rest-server.properties | false          | Whether Server loads its metadata from PD at startup                                          | `ServerOptions.java:401-407` |
| cluster                      | rest-server.properties | hg-test        | Cluster name used as the prefix of every PD metadata key                                      | `ServerOptions.java:187-193` |
| init_store.enabled           | rest-server.properties | true           | Set it to `false` in a PD/Store deployment, where the storage side already owns the metadata  | `ServerOptions.java:382-390` |
| graph.load_from_local_config | rest-server.properties | false | Controls constructor preloading. Application initialization still scans and attempts to load local configurations, so `false` does not block local loading. Restart Server to apply graph configuration changes. | `ServerOptions.java:366-372` |
| auth.graph_store             | rest-server.properties | hugegraph      | The graph that holds auth data, checked against the `hstore` backend when init-store is off   | `ServerOptions.java:602-609` |
| graphspace                   | {graph}.properties     | DEFAULT        | First segment of the graph name PD sees                                                       | `CoreOptions.java:679-685`   |
{.td-table--wide}

`init-store.sh` never initializes an `hstore` graph. On the enabled path it scans `conf/graphs` and skips
every graph whose backend is `hstore`. If you turn the whole step off with `init_store.enabled=false`, it
validates instead that the admin account can still be created on the PD startup path: `usePD` has to be true,
the auth graph has to exist locally with backend `hstore`, and `auth.admin_pa` has to be set to an explicit
non-empty value. Otherwise startup fails rather than handing out the public default password.

### 6 How the Server finds the stores

The adapter builds its clients once per process, on the first `hstore` graph it opens:

1. A PD client config from `pd.peers`, with the PD authority credentials and the client side partition cache
   enabled.
2. The process wide PD client.
3. The process wide store client, created from that PD client.

Creating the store client installs a PD backed partitioner as the node provider, partitioner and notifier of
the store client's node manager. That partitioner is the whole of the routing logic:

- **Point and prefix requests** ask PD for the partition that owns the key, take the leader shard of that
  partition and send the request to that store id.
- **Code range scans** walk the partitions by code until the range is covered, producing one target store per
  partition.
- **Whole graph scans** ask PD for the active stores of the graph and fan out to every one of them.
- **Store address lookup** resolves a store id to a host and port through PD.
- **Cache invalidation**: when a store answers that a partition leader moved, the notifier updates the
  partition leader in PD's client cache and invalidates the stale partition entry, so later requests follow
  the new leader.

Because the store list comes from PD rather than from configuration, a store node is added or removed by
starting or stopping it against the same PD cluster. No Server side config change is needed.

### 7 Backend capabilities

`hstore` does not support every query form the local backends do. The differences visible to a user:

| Feature                    | Supported |
|----------------------------|-----------|
| Scan by key prefix         | yes       |
| Scan by key range          | yes       |
| Query with range condition | yes       |
| Query with order by        | yes       |
| Query by page              | yes       |
| OLAP properties            | yes       |
| Task and server vertex     | yes       |
| Scan token                 | no        |
| Query schema by name       | no        |
| Query by label             | no        |
| Query with `in` condition  | no        |
| Query with `contains`      | no        |
| Query with `contains key`  | no        |
| Sort results by input ids  | no        |
| Delete edge by label       | no        |
| Update vertex property     | no        |
| Update edge property       | no        |
| Transaction                | no        |
| Number type                | no        |
| Aggregate property         | no        |
| TTL                        | no        |

Sorting by input ids is off because multi node batch scans group the input keys by store and lose the global
order. Vertex and edge property updates are off because the properties are stored in a single cell.

### 8 Verification

Once the Server is up, the backend metrics endpoint reports the number of stores that PD currently considers
active:

```bash
curl http://localhost:8080/metrics/backend
```

The `nodes` value in the response is the count of active stores PD returns. A `nodes` value of `0` means the
Server reached PD but PD has no store in state `Up`, which usually means the Store nodes have not registered
yet, or registered as `Pending` because they are not in PD's `pd.initial-store-list`.

### 9 Legacy GraphID upgrade preflight

Some 1.7 Store batch writes use the reserved `FFFE` prefix when a graph has no ID mapping. Allocating a real GraphID does not move those rows,
so newer reads can miss old data; Raft replay can also trigger allocation. This does not affect every 1.7 database.

> [!NOTE]
> Released 1.7.0 does not include this protection. Before relying on it, ensure the Store build contains the
> [GraphID preflight patch](https://github.com/apache/hugegraph/pull/3330).

These builds inspect all retained valid local partition DB versions before Store registration, heartbeats or Raft startup.
Each graph-data column family is checked by an ordered seek to `FFFE`, without a full scan. Legacy rows, a DB that cannot be safely inspected,
a nonempty DB directory without `CURRENT`, or an incomplete selected version that would hide a valid older version cause startup to fail.
Errors identify the stage, partition and path,
and the column family when a legacy row is found. This startup does not register the Store as `Up`; a prior registration can remain until its heartbeat expires.

The check does not create, prune or rewrite partition DBs, or change the persisted ID format. The same protection remains before missing-ID allocation,
cold DB opens, Raft initialization and staged snapshot activation. Cached primary sessions are checked directly to include unflushed writes with WAL disabled.
A GraphID preflight failure during later local recovery requests a nonzero exit. Rejected snapshots retain the active DB and committed index,
incoming snapshot and staged copy. The entire application startup is not read-only: configuration loading can already have contacted PD,
and later bootstrap stages can have changed Store/Raft location metadata.

#### Offline check before startup

> [!NOTE]
> These commands additionally require a Store build containing the [offline checker change](https://github.com/apache/hugegraph/pull/3399).
> Availability depends on that runtime change being merged and included in your distribution; this guide does not establish that a released tag has the script.
> The registration guard and offline command are separate entry points. A build with only the registration guard need not include this command.

Stop writers, retain matching PD, Store data and Raft backups, and complete the original version's snapshot and Store shutdown procedure.
Using Java 17, selected through `JAVA_HOME` or `PATH`, run from the Store distribution containing the change:

```bash
bin/hugegraph-store-check.sh --check
```

`--config` selects a local configuration directory, defaulting to the distribution's `conf`. Use `--data-path` for the effective data roots.
Separate multiple roots with commas in one argument. Do not repeat `--data-path`: duplicate options are rejected rather than accumulated.

```bash
bin/hugegraph-store-check.sh --check \
  --config /srv/hugegraph-store/conf \
  --data-path /srv/store-data-a,/srv/store-data-b
```

Replace these example paths with deployment values. Relative paths resolve from the Store distribution.
The command reads `application.yml` followed by `application-pd.yml` when present.
It starts no Spring context, PD, Server or Raft node and creates no inspected DB.
It does not automatically apply Spring environment, JSON or profile overrides. For example, pass a container's `HG_STORE_DATA_PATH` explicitly through
`--data-path`; the entrypoint's `SPRING_APPLICATION_JSON` is not applied. Configuration files must also contain the resolved effective RocksDB settings.

For Topling, prepare the verified runtime assets first, set `TOPLINGDB_ROCKSDB_PROVIDER=topling`,
and retain `rocksdb.provider=topling` in effective configuration.
The checker shares the Store launcher's runtime selector, and the selected JNI JAR precedes the bundled standard RocksDB classes.
Missing or unverified assets fail the check; do not switch providers to treat that failure as a pass.

Check every stopped Store. Active DB locks cause refusal; a separate read-only process also cannot see a running Store's unflushed memtables.
The scope includes configured data roots, retained DB versions, each partition's latest local snapshot and other recorded storage locations.
It seeks `FFFE` per column family and validates GraphID metadata instead of scanning every business row
or invoking the normal opener that can prune old versions.

| Result | Meaning and action |
| --- | --- |
| Exit 0 | No incompatible prefix or invalid mapping was found in the inspected persisted DBs and latest snapshots; retain backups and continue normal upgrade acceptance |
| Exit 2 | Legacy data, invalid mappings, active locks, configuration or I/O problems; resolve the path-specific diagnosis and recheck before upgrading |
| Other nonzero exit | The launcher, JVM or check did not succeed; refuse the upgrade instead of treating this as clean |

Exit 0 does not establish historical ownership, backup completeness or acceptance of the whole upgrade, and never authorizes merging prefixes.
On refusal, follow the trusted-source recovery boundaries below. See the
[runtime upgrade guide](https://github.com/hugegraph/hugegraph/blob/fix/graphid-upgrade-guard/docs/graphid-upgrade.md) for the command contract.

#### Upgrade and migration

Stop application writes and back up the original cluster's data, metadata and Raft state. Data that passes the GraphID guard needs no migration for this issue;
complete the usual upgrade validation before resuming writes.

If startup reports `FFFE`, stop the upgrade and preserve the original DBs, WAL, metadata and snapshots. Prefer logical migration from a complete, trusted
1.7 source to a fresh 1.8 cluster with existing HugeGraph-Tools. Target data then uses the normal GraphID and Raft write paths.
Restore an isolated 1.7 source from a pre-upgrade backup when necessary. Confirm source completeness and graph ownership before exporting;
a current single-graph configuration does not prove historical ownership of every `FFFE` row.

For a graph in the `DEFAULT` graph space, use an empty target graph and a Tools build containing the
[backup data-page failure fix](https://github.com/hugegraph/hugegraph-toolchain/pull/96), so a failed export stops migration before target restore:

```bash
bin/hugegraph --url http://old-1.7:8080 --graph hugegraph \
  migrate --target-url http://new-1.8:8080 --target-graph hugegraph \
  --graph-mode RESTORING --directory /safe-backup/hugegraph \
  --huge-types all --keep-local-data
```

Keep application writes stopped throughout the process; export does not provide a snapshot across all requests.
`RESTORING` preserves schema IDs on the empty target,
and `--keep-local-data` retains the logical backup.
The current command uses the default graph space; do not apply this example directly to another graph space.
Do not switch traffic after an export or restore error. Retain the backup and retry against a fresh empty target;
a failed restore can leave partial data and `RESTORING` mode. Successful exit and matching counts alone do not establish completeness: compare vertex/edge IDs,
endpoints, properties, schema, indexes and application queries against a known baseline. Repeat queries after a target snapshot and restart,
and verify follower rebuilds in replicated deployments. Switch traffic after acceptance and retain the source and backup;
new target writes are absent from the old backup.

If a previous upgrade allocated new IDs, the source view can be incomplete; remapping to `FFFE` can instead hide newer rows. Prefer a pre-upgrade backup;
replacing the JAR alone does not undo a persisted mapping. Multiple graphs may share the old prefix, physical keys do not prove ownership,
and overwritten or deleted values cannot be reconstructed without another source. Do not automatically merge old and new prefixes,
assign all legacy rows to one graph, or edit each replica's RocksDB independently. Recover these cases from backup and write-history evidence first.
The guard detects and refuses unsafe operations; it does not migrate data automatically or enable in-place rolling upgrades of affected data.

See the
[Store GraphID upgrade guide](https://github.com/hugegraph/hugegraph/blob/fix/store-legacy-graph-prefix-preflight/docs/store-graphid-upgrade.md)
for details.
