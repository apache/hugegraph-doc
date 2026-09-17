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
`backend=hstore` with `Unsupported backend type`.

### 4 hstore config options

These are the only keys in the `hstore` config space. They belong in the graph properties file.

| config option          | default value | description                                                   |
|------------------------|---------------|---------------------------------------------------------------|
| hstore.partition_count | 0             | Number of partitions, which PD controls partitions based on.   |
| hstore.shard_count     | 0             | Number of copies, which PD controls partition copies based on. |

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
on the HugeGraph master branch where the option is declared.

| config option                | file                   | default        | why it matters with hstore                                                                   | source                       |
|------------------------------|------------------------|----------------|----------------------------------------------------------------------------------------------|------------------------------|
| pd.peers                     | rest-server.properties | 127.0.0.1:8686 | PD addresses used for metadata, service discovery and the system graph                        | `ServerOptions.java:195-201` |
| pd.peers                     | {graph}.properties     | 127.0.0.1:8686 | PD addresses used by the backend adapter itself                                               | `CoreOptions.java:649-654`   |
| usePD                        | rest-server.properties | false          | Whether Server loads its metadata from PD at startup                                          | `ServerOptions.java:390-396` |
| cluster                      | rest-server.properties | hg-test        | Cluster name used as the prefix of every PD metadata key                                      | `ServerOptions.java:187-193` |
| init_store.enabled           | rest-server.properties | true           | Set it to `false` in a PD/Store deployment, where the storage side already owns the metadata  | `ServerOptions.java:371-380` |
| graph.load_from_local_config | rest-server.properties | false          | Whether `conf/graphs` is scanned at startup in addition to the graph configs held in PD       | `ServerOptions.java:355-361` |
| auth.graph_store             | rest-server.properties | hugegraph      | The graph that holds auth data, checked against the `hstore` backend when init-store is off   | `ServerOptions.java:591-598` |
| graphspace                   | {graph}.properties     | DEFAULT        | First segment of the graph name PD sees                                                       | `CoreOptions.java:679-685`   |

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
