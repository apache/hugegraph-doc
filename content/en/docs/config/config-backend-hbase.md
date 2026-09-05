---
title: "Configuring the HBase Backend"
linkTitle: "Config HBase Backend"
weight: 7
---

### Overview

The HBase backend stores graph data in Apache HBase tables. HugeGraph acts as an HBase client only: it connects through the HBase ZooKeeper quorum, creates one HBase namespace per graph, and creates that graph's schema, data and index tables inside it. Counting queries are answered by the HBase `AggregateImplementation` coprocessor, which HugeGraph attaches to every table it creates.

> Note: the HBase backend is deprecated and is planned for removal in HugeGraph 2.0. New deployments should use `hstore` (distributed) or `rocksdb` (embedded, the default), and existing HBase deployments should plan a migration.

Since 1.7.0 the only backends shipped in the distribution are `hstore`, `rocksdb`, `hbase` and `memory`. The backend driver version reported by the HBase provider is `1.12`.

### Supported HBase Versions

The client jars are pinned to HBase `2.6.5` (`hbase-endpoint` plus `hbase-shaded-client`). HBase 2.x is required on the server side: when the detected HBase version is older than `2.0` the scan path rewrites an inclusive stop row into an exclusive one plus a trailing `0` byte, because inclusive stop rows do not work before that release. The CI job and the local Docker image both use HBase 2.6.5, so that is the version the backend is tested against.

### Selecting the Backend

Edit `conf/graphs/hugegraph.properties` of the graph that should use HBase:

```ini
backend=hbase
serializer=hbase

# the namespace name is derived from this value
store=hugegraph

hbase.hosts=localhost
hbase.port=2181
hbase.znode_parent=/hbase
```

> Note: `serializer` must be set to `hbase`, not to `binary`. The HBase serializer is a `BinarySerializer` subclass that drops the id prefix from row keys and writes the pre-split partition prefix that the pre-split vertex and edge tables expect. With `serializer=binary` neither of these applies.

Then initialize the store and start the server:

```bash
./bin/init-store.sh
./bin/start-hugegraph.sh
```

The default distribution is built with the backends `rocksdb, hbase, hstore`, so no extra jar is needed. A distribution built with the `rocksdb-only` Maven profile does not contain the HBase backend, and `backend=hbase` then fails to open with `Not exists BackendStoreProvider: hbase`.

All options below live in the graph properties file (`conf/graphs/hugegraph.properties`), not in `rest-server.properties`. They are registered only when the `hbase` backend is part of the distribution.

### Connection Options

| Option              | Default     | Description                                                                                                                                                 |
|---------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| hbase.hosts         | localhost   | The hostnames or ip addresses of HBase zookeeper, separated with commas. Must not be empty. Maps to `hbase.zookeeper.quorum`.                                |
| hbase.port          | 2181        | The port address of HBase zookeeper, in the range 1 to 65535. Maps to `hbase.zookeeper.property.clientPort`.                                                 |
| hbase.znode_parent  | /hbase      | The znode parent path of HBase zookeeper. Must not be empty. Maps to `zookeeper.znode.parent`.                                                               |
| hbase.zk_retry      | 3           | The recovery retry times of HBase zookeeper, in the range 0 to 1000. Maps to `zookeeper.recovery.retry`.                                                     |
| hbase.threads_max   | 64          | The max threads num of hbase connections, in the range 1 to 1000. Maps to `hbase.hconnection.threads.max`, which HBase itself defaults to 256; the lower value is used to avoid running out of memory. |

### Timeout Options

| Option                    | Default          | Description                                                                                                                                                    |
|---------------------------|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| hbase.truncate_timeout    | 30               | The timeout in seconds of waiting for store truncate. Must be positive. It applies per store, and a graph has three stores, so a truncate can take up to three times this value. |
| hbase.aggregation_timeout | 43200 (12 hours) | The timeout in seconds of waiting for aggregation. Must be positive. Sets `hbase.rpc.timeout` on the aggregation client used by count queries.                  |

### Kerberos and HBase Site Options

| Option                   | Default                        | Description                                                                                             |
|--------------------------|--------------------------------|---------------------------------------------------------------------------------------------------------|
| hbase.kerberos_enable    | false                          | Is Kerberos authentication enabled for HBase.                                                           |
| hbase.krb5_conf          | /etc/krb5.conf                 | Kerberos configuration file, including KDC IP, default realm, etc. Applied as the `java.security.krb5.conf` system property. |
| hbase.hbase_site         | /etc/hbase/conf/hbase-site.xml | The HBase's configuration file. It is added as a configuration resource on every connection, whether or not Kerberos is enabled. |
| hbase.kerberos_principal | (empty)                        | The HBase's principal for kerberos authentication.                                                      |
| hbase.kerberos_keytab    | (empty)                        | The HBase's key tab file for kerberos authentication.                                                   |

When `hbase.kerberos_enable=true`, HugeGraph sets `hadoop.security.authentication` and `hbase.security.authentication` to `kerberos` on the connection, then logs in from the keytab with the configured principal before opening the connection. A Kerberos setup therefore needs all four of `hbase.krb5_conf`, `hbase.hbase_site`, `hbase.kerberos_principal` and `hbase.kerberos_keytab` to be valid:

```ini
hbase.kerberos_enable=true
hbase.krb5_conf=/etc/krb5.conf
hbase.hbase_site=/etc/hbase/conf/hbase-site.xml
hbase.kerberos_principal=hugegraph/host@EXAMPLE.COM
hbase.kerberos_keytab=/etc/security/keytabs/hugegraph.keytab
```

`hbase.hbase_site` is read even with Kerberos disabled, so a path that does not exist is simply an empty resource. Point it at the cluster's own `hbase-site.xml` when HBase settings beyond the options above are needed.

### Pre-split Partition Options

| Option                  | Default | Description                                                                        |
|-------------------------|---------|------------------------------------------------------------------------------------|
| hbase.enable_partition  | true    | Is pre-split partitions enabled for HBase. Also decides whether the backend reports support for key-prefix and key-range scans. |
| hbase.vertex_partitions | 10      | The number of partitions of the HBase vertex table. Must not be negative.          |
| hbase.edge_partitions   | 30      | The number of partitions of the HBase edge table. Must not be negative.            |

With pre-split enabled, the vertex table is created with `hbase.vertex_partitions` regions and each of the two edge tables with `hbase.edge_partitions` regions, and the serializer prefixes row keys with the partition the id hashes to.

> Note: set the partition counts to match the actual data volume and the number of region servers before the store is initialized. They change the load speed considerably, and they are only applied at table creation time.

Turning `hbase.enable_partition` off restores plain, unprefixed row keys. In exchange the backend then reports support for key-prefix scans and key-range scans, which pre-split row keys cannot serve.

### Namespace and Table Layout

Each graph maps to one HBase namespace named `<graphspace>/<store>`, lowercased, with `/` replaced by `_` because an HBase namespace name may only contain alphanumeric characters and the `_` character. With the defaults `graphspace=DEFAULT` and `store=hugegraph`, the namespace is `default_hugegraph`.

Inside that namespace a graph keeps three stores, the schema store `m`, the graph store `g` and the system store `s`:

| Store        | Tables                                                                     |
|--------------|----------------------------------------------------------------------------|
| schema (`m`) | `VL`, `EL`, `PK`, `IL`, `C`, `m_si`                                        |
| graph (`g`)  | `g_v`, `g_oe`, `g_ie`, `g_si`, `g_vi`, `g_ei`, `g_ii`, `g_fi`, `g_li`, `g_di`, `g_ai`, `g_hi`, `g_ui` |
| system (`s`) | `s_v`, `s_oe`, `s_ie`, `s_si`, `s_vi`, `s_ei`, `s_ii`, `s_fi`, `s_li`, `s_di`, `s_ai`, `s_hi`, `s_ui`, `M` |

`g_v` is the vertex table, `g_oe` and `g_ie` are the out-edge and in-edge tables, and the remaining `g_*` tables are the secondary, vertex-label, edge-label, range (int, float, long, double), search, shard and unique index tables. Every table has a single column family named `f`, and every table is created with the `org.apache.hadoop.hbase.coprocessor.AggregateImplementation` coprocessor attached. Only `g_v`, `g_oe` and `g_ie` are pre-split; the system store's copies of those tables are created with a single region.

The `M` table in the system store holds the backend version written by `init-store.sh`. It is excluded when a graph is truncated, because losing it makes the version check fail on the next startup. Clearing a graph drops the tables; clearing it with the storage space included drops the whole namespace.

`GET /metrics/backend` reports the HBase cluster state: `cluster_id`, `master_name`, `average_load`, `hbase_version`, `region_count`, `leaving_servers`, `nodes`, `region_servers`, and a `servers` map with heap, disk, request and per region details for each region server. `PUT /graphspaces/{graphspace}/graphs/{name}/compact` asks HBase to compact every table of the graph.

### Local Testing with Docker

`docker/hbase` in the server repository builds a standalone HBase 2.6.5 image (`hugegraph/hbase:2.6.5`, container name `hg-hbase-test`) for local development and tests. Run these from the repository root.

Start HBase for a HugeGraph server running on the host:

```bash
docker compose -p hg-hbase -f docker/hbase/docker-compose.hbase.yml build --no-cache hbase
HBASE_MASTER_HOSTNAME=localhost HBASE_REGIONSERVER_HOSTNAME=localhost \
docker compose -p hg-hbase -f docker/hbase/docker-compose.hbase.yml up -d
until docker exec hg-hbase-test nc -z localhost 2181 >/dev/null 2>&1; do sleep 2; done
```

Start HBase for a HugeGraph server running in a container on the same Docker network:

```bash
HBASE_HOSTNAME=hbase docker compose -p hg-hbase -f docker/hbase/docker-compose.hbase.yml up -d
```

The advertised hostnames matter: the container writes `HBASE_MASTER_HOSTNAME` and `HBASE_REGIONSERVER_HOSTNAME` into its `hbase-site.xml` on startup, falling back to `HBASE_HOSTNAME` (default `hbase`). A client that cannot resolve the advertised name fails with `UnknownHostException: hbase:16000` even though ZooKeeper answers.

Ports published to the host:

| Port  | Service                                              |
|-------|------------------------------------------------------|
| 2181  | ZooKeeper, matches the `hbase.port` default          |
| 16000 | HBase Master RPC                                     |
| 16010 | HBase Master web UI, `http://localhost:16010`        |
| 16020 | HBase RegionServer RPC                               |
| 16030 | HBase RegionServer web UI, `http://localhost:16030`  |

Run the backend test suite against it:

```bash
mvn test -pl hugegraph-server/hugegraph-test -am -P core-test,hbase
```

Stop it and remove its volumes:

```bash
docker compose -p hg-hbase -f docker/hbase/docker-compose.hbase.yml down -v
```

The image starts ZooKeeper, the master and the region server as separate daemons and waits for the master to report a live server before it starts tailing the logs, so the first startup can take a while. Give Docker at least 4 GB of memory. The compose health check has a 90 second start period for the same reason.

### Limitations

The HBase backend does not support these features:

- Transactions. A rollback only discards the batch that has not been committed yet, and a commit writes one table at a time, so it is not atomic across tables.
- Updating a single vertex or edge property in place, and merging vertex properties. Properties are stored in one cell, so the whole property column is rewritten.
- Querying schema by name, and querying vertices or edges by label alone. Both would need an HBase secondary index.
- Deleting edges by label.
- Queries with an `in` condition, a `contains` condition or a `contains_key` condition.
- Aggregate properties and OLAP properties.
- Native number types (the `supportsNumberType` backend feature is off).
- Scan tokens.
- Key-prefix scans and key-range scans while `hbase.enable_partition` is `true`.
- Aggregation other than `count`. Any other aggregate function is rejected.
- Snapshots. Creating or resuming a backend snapshot throws `UnsupportedOperationException`.

Supported features include TTL on vertices and edges, paged queries, order-by queries, range conditions, and sorting by input ids.
