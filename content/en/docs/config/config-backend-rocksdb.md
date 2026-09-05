---
title: "Configuring the RocksDB Backend"
linkTitle: "Config RocksDB Backend"
weight: 5
---

### Overview

RocksDB is an embedded LSM-tree key-value store. With the `rocksdb` backend, HugeGraph-Server keeps all
graph data in RocksDB instances that live inside the server process, so there is no separate storage
service to deploy. This is the backend used by the shipped `conf/graphs/hugegraph.properties`.

Since version 1.7.0 the server accepts only `memory`, `rocksdb`, `hbase` and `hstore` as the backend.
The `rocksdb` backend stores data on the local disks of one server: it does not support shared storage,
so a graph cannot be served by several servers over the same data directory. For a distributed
deployment use the `hstore` backend with PD and Store.

The RocksDB JNI library is pinned to version `8.10.2` by `hugegraph-rocksdb/pom.xml`, so the on-disk
format and the option semantics are those of RocksDB 8.10.

The backend driver version reported by this store is `1.11`, and it is written into the meta table of
the system store when the graph is initialized.

### Selecting the backend

Set the backend and the serializer in the graph properties file (`conf/graphs/<graph>.properties`):

```properties
gremlin.graph=org.apache.hugegraph.HugeFactory

backend=rocksdb
serializer=binary

store=hugegraph

# rocksdb backend config
#rocksdb.data_path=/path/to/disk
#rocksdb.wal_path=/path/to/disk
```

- `backend=rocksdb` selects the RocksDB store provider.
- `serializer=binary` is the serializer the shipped template uses for this backend. The built-in
  serializers are `binary`, `binaryscatter` and `text`.
- `store` is the database namespace of the graph, and it is also part of the graph name that the
  provider passes down to the store.

Run `bin/init-store.sh` once before the first start to create the stores, then start the server. Both
`bin/init-store.sh` and `bin/hugegraph-server.sh` load the RocksDB library, so the data directories are
created on the machine that runs them.

The distribution registers the option space and the store provider for each backend listed in the
packaged `backend.properties`, whose value comes from the `hugegraph.backends` build property. A default
build registers `rocksdb, hbase, hstore`; building with `-Drocksdb-only` activates the `rocksdb-only`
profile and produces a distribution that registers only `rocksdb`. A backend that is not registered
fails at startup with `Not exists BackendStoreProvider`.

The provider registration also adds a second name, `rocksdbsst`, for the store that writes SST files
instead of a live database. That name is not in the list of allowed backends, so `backend=rocksdbsst`
is rejected with `backend is illegal: rocksdbsst`. To load SST files into a normal `rocksdb` graph, use
`rocksdb.sst_path` as described below.

### Data directory layout

Two directories matter: `rocksdb.data_path` (default `rocksdb-data/data`) and `rocksdb.wal_path`
(default `rocksdb-data/wal`). Relative paths resolve against the working directory of the server, which
is the installation directory.

Each graph opens three stores: `m` for schema, `g` for graph data, and `s` for the system store. The
store name is appended to both configured paths, so a default single-graph installation looks like this:

```
rocksdb-data/
  data/
    m/    # schema store: property keys, vertex/edge/index labels, counters
    g/    # graph store: vertices, edges, index tables, olap tables
    s/    # system store: tasks, server info, backend meta (driver version)
  wal/
    m/
    g/
    s/
```

Every backend table becomes a RocksDB column family inside the store it belongs to, named
`<database>+<table>`, where the database is derived from the graph name. Column families of existing
data directories are always reopened, so tables created by an older version stay readable.

Other points to keep in mind:

- Two graphs must not share a data path. When a graph is created by cloning an existing configuration
  through the API, the provider appends `_<newGraph>` to both `rocksdb.data_path` and
  `rocksdb.wal_path`. Deleting such a graph deletes both directories.
- Snapshots are created beside the data directory: the last two segments of the data path are rewritten
  with a prefix, so with the default paths the snapshot of the graph store goes to
  `rocksdb-data/<prefix>_data/g`. Resuming a snapshot closes the instance, deletes the data directory
  and moves the snapshot into its place.
- With `rocksdb.data_disks` set, the tables named there are opened as separate RocksDB instances under
  the given paths instead of under `rocksdb.data_path`. The server opens up to 8 instances in parallel,
  waits at most 600 seconds for the open to finish and 30 seconds for sessions to close.

### Path and log options

| config option        | default value       | description                                                                                                                                                                                                                                                                                                                                       |
|----------------------|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.data_path    | `rocksdb-data/data` | The path for storing data of RocksDB. Must not be empty.                                                                                                                                                                                                                                                                                          |
| rocksdb.data_disks   | `[]`                | The optimized disks for storing data of RocksDB. The format of each element: `STORE/TABLE: /path/disk`. Allowed keys are [g/vertex, g/edge_out, g/edge_in, g/vertex_label_index, g/edge_label_index, g/range_int_index, g/range_float_index, g/range_long_index, g/range_double_index, g/secondary_index, g/search_index, g/shard_index, g/unique_index, g/olap]. A disk path must differ from `rocksdb.data_path`. |
| rocksdb.wal_path     | `rocksdb-data/wal`  | The path for storing WAL of RocksDB. Must not be empty.                                                                                                                                                                                                                                                                                           |
| rocksdb.sst_path     | (empty)             | The path for ingesting SST file into RocksDB. Empty disables ingestion.                                                                                                                                                                                                                                                                           |
| rocksdb.log_level    | `INFO`              | The info log level of RocksDB. Allowed values: DEBUG, INFO, WARN, ERROR, FATAL, HEADER.                                                                                                                                                                                                                                                            |

### Compaction and compression options

| config option                  | default value                                                                             | description                                                                                                                                                    |
|--------------------------------|-------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.num_levels             | `7`                                                                                       | Set the number of levels for this database. Range: 1 to 2^31-1.                                                                                                |
| rocksdb.compaction_style       | `LEVEL`                                                                                   | Set compaction style for RocksDB: LEVEL/UNIVERSAL/FIFO.                                                                                                        |
| rocksdb.optimize_mode          | `true`                                                                                    | Optimize for heavy workloads and big datasets. See "How the options are applied" below.                                                                          |
| rocksdb.bulkload_mode          | `false`                                                                                   | Switch to the mode to bulk load data into RocksDB.                                                                                                             |
| rocksdb.compression_per_level  | `[none, none, snappy, snappy, snappy, snappy, snappy]`                                    | The compression algorithms for different levels of RocksDB, allowed values are none/snappy/z/bzip2/lz4/lz4hc/xpress/zstd. The list must be empty or hold exactly `rocksdb.num_levels` elements. |
| rocksdb.bottommost_compression | `none`                                                                                    | The compression algorithm for the bottommost level of RocksDB, allowed values are none/snappy/z/bzip2/lz4/lz4hc/xpress/zstd.                                    |
| rocksdb.compression            | `snappy`                                                                                  | The compression algorithm for compressing blocks of RocksDB, allowed values are none/snappy/z/bzip2/lz4/lz4hc/xpress/zstd.                                      |

### Database level options

| config option                          | default value        | description                                                                                                                                                                             |
|----------------------------------------|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.max_background_jobs            | `8`                  | Maximum number of concurrent background jobs, including flushes and compactions. Range: 1 to 2^31-1.                                                                                    |
| rocksdb.max_subcompactions             | `4`                  | The value represents the maximum number of threads per compaction job. Range: 1 to 2^31-1.                                                                                              |
| rocksdb.delayed_write_rate             | `16777216` (16 MB/s) | The rate limit in bytes/s of user write requests when need to slow down if the compaction gets behind.                                                                                   |
| rocksdb.max_open_files                 | `-1`                 | The maximum number of open files that can be cached by RocksDB, -1 means no limit.                                                                                                       |
| rocksdb.max_manifest_file_size         | `104857600` (100 MB) | The max size of manifest file in bytes.                                                                                                                                                 |
| rocksdb.skip_stats_update_on_db_open   | `false`              | Whether to skip statistics update when opening the database, setting this flag true allows us to not update statistics.                                                                  |
| rocksdb.skip_check_sst_size_on_db_open | `false`              | Whether to skip checking sizes of all sst files when opening the database.                                                                                                               |
| rocksdb.max_file_opening_threads       | `16`                 | The max number of threads used to open files. Range: 1 to 2^31-1.                                                                                                                       |
| rocksdb.max_total_wal_size             | `0`                  | Total size of WAL files in bytes. Once WALs exceed this size, we will start forcing the flush of column families related, 0 means no limit.                                              |
| rocksdb.bytes_per_sync                 | `0`                  | Allows OS to incrementally sync SST files to disk while they are being written, asynchronously in the background. Issue one request for every bytes_per_sync written. 0 turns it off.     |
| rocksdb.wal_bytes_per_sync             | `0`                  | Same as above for WAL files. 0 turns it off.                                                                                                                                            |
| rocksdb.strict_bytes_per_sync          | `false`              | When true, guarantees SST/WAL files have at most bytes_per_sync/wal_bytes_per_sync bytes submitted for writeback at any given time. This can be used to handle cases where processing speed exceeds I/O speed. |
| rocksdb.db_write_buffer_size           | `0`                  | Total size of write buffers in bytes across all column families, 0 means no limit.                                                                                                       |
| rocksdb.log_readahead_size             | `0`                  | The number of bytes to prefetch when reading the log. 0 means the prefetching is disabled.                                                                                               |
| rocksdb.compaction_readahead_size      | `0`                  | The number of bytes to perform bigger reads when doing compaction. If running RocksDB on spinning disks, you should set this to at least 2MB. 0 means the prefetching is disabled.        |
| rocksdb.row_cache_capacity             | `0`                  | The capacity in bytes of global cache for table-level rows. 0 means the row_cache is disabled.                                                                                           |
| rocksdb.delete_obsolete_files_period   | `21600` (6 hours)    | The periodicity in seconds when obsolete files get deleted, 0 means always do full purge. The value is converted to microseconds before it reaches RocksDB.                              |

### Memtable options

| config option                               | default value        | description                                                                                                                                                                                                                 |
|---------------------------------------------|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.write_buffer_size                   | `134217728` (128 MB) | Amount of data in bytes to build up in memory. Minimum 1 MB. This is per column family.                                                                                                                                     |
| rocksdb.max_write_buffer_number             | `6`                  | The maximum number of write buffers that are built up in memory. Range: 1 to 2^31-1.                                                                                                                                        |
| rocksdb.min_write_buffer_number_to_merge    | `2`                  | The minimum number of write buffers that will be merged together. Range: 1 to 2^31-1.                                                                                                                                       |
| rocksdb.max_write_buffer_number_to_maintain | `0`                  | The total maximum number of write buffers to maintain in memory for conflict checking when transactions are used.                                                                                                            |
| rocksdb.memtable_bloom_size_ratio           | `0.0`                | If prefix-extractor is set and memtable_bloom_size_ratio is not 0, or if memtable_whole_key_filtering is set true, create bloom filter for memtable with the size of write_buffer_size * memtable_bloom_size_ratio. A value larger than 0.25 is reduced to 0.25. Range: 0.0 to 1.0. |
| rocksdb.memtable_whole_key_filtering        | `false`              | Enable whole key bloom filter in memtable, it can potentially reduce CPU usage for point-look-ups. Note this will only take effect if memtable_bloom_size_ratio > 0.                                                          |
| rocksdb.memtable_huge_page_size             | `0`                  | The page size for huge page TLB for bloom in memtable. If <= 0, not allocate from huge page TLB but from malloc.                                                                                                             |
| rocksdb.inplace_update_support              | `false`              | Allows thread-safe inplace updates if a put key exists in current memtable and sizeof new value is smaller.                                                                                                                  |

### Level sizing and write stall options

| config option                               | default value             | description                                                                                                                                                                                                                                            |
|---------------------------------------------|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.level_compaction_dynamic_level_bytes | `false`                  | Whether to enable level_compaction_dynamic_level_bytes, if it's enabled we give max_bytes_for_level_multiplier a priority against max_bytes_for_level_base, the bytes of base level is dynamic for a more predictable LSM tree, it is useful to limit worse case space amplification. Turning this feature on/off for an existing DB can cause unexpected LSM tree structure so it's not recommended. |
| rocksdb.max_bytes_for_level_base            | `536870912` (512 MB)      | The upper-bound of the total size of level-1 files in bytes. Minimum 1 MB.                                                                                                                                                                             |
| rocksdb.max_bytes_for_level_multiplier      | `10.0`                    | The ratio between the total size of level (L+1) files and the total size of level L files for all L. Minimum 1.0.                                                                                                                                       |
| rocksdb.target_file_size_base               | `67108864` (64 MB)        | The target file size for compaction in bytes. Minimum 1 MB.                                                                                                                                                                                             |
| rocksdb.target_file_size_multiplier         | `1`                       | The size ratio between a level L file and a level (L+1) file.                                                                                                                                                                                           |
| rocksdb.level0_file_num_compaction_trigger  | `2`                       | Number of files to trigger level-0 compaction.                                                                                                                                                                                                         |
| rocksdb.level0_slowdown_writes_trigger      | `20`                      | Soft limit on number of level-0 files for slowing down writes.                                                                                                                                                                                          |
| rocksdb.level0_stop_writes_trigger          | `36`                      | Hard limit on number of level-0 files for stopping writes.                                                                                                                                                                                             |
| rocksdb.soft_pending_compaction_bytes_limit | `68719476736` (64 GB)     | The soft limit to impose on pending compaction in bytes. Minimum 1 GB.                                                                                                                                                                                  |
| rocksdb.hard_pending_compaction_bytes_limit | `274877906944` (256 GB)   | The hard limit to impose on pending compaction in bytes. Minimum 1 GB.                                                                                                                                                                                  |

### File I/O options

| config option                                  | default value | description                                                                                                                                                     |
|------------------------------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.allow_mmap_writes                      | `false`       | Allow the OS to mmap file for writing.                                                                                                                          |
| rocksdb.allow_mmap_reads                       | `false`       | Allow the OS to mmap file for reading sst tables.                                                                                                                |
| rocksdb.use_direct_reads                       | `false`       | Enable the OS to use direct I/O for reading sst tables.                                                                                                          |
| rocksdb.use_direct_io_for_flush_and_compaction | `false`       | Enable the OS to use direct read/writes in flush and compaction.                                                                                                 |
| rocksdb.use_fsync                              | `false`       | If true, then every store to stable storage will issue a fsync.                                                                                                 |
| rocksdb.atomic_flush                           | `false`       | If true, flushing multiple column families and committing their results atomically to MANIFEST. Note that it's not necessary to set atomic_flush=true if WAL is always enabled. |

### SST table format and block cache options

| config option                            | default value          | description                                                                                                                                                                          |
|------------------------------------------|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.format_version                   | `5`                    | The format version of BlockBasedTable, allowed values are 0~5.                                                                                                                        |
| rocksdb.index_type                       | `kBinarySearch`        | The index type used to lookup between data blocks with the sst table, allowed values are [kBinarySearch, kHashSearch, kTwoLevelIndexSearch, kBinarySearchWithFirstKey].                |
| rocksdb.data_block_index_type            | `kDataBlockBinarySearch` | The search type used to point lookup in data block with the sst table, allowed values are [kDataBlockBinarySearch, kDataBlockBinaryAndHash].                                        |
| rocksdb.data_block_hash_table_util_ratio | `0.75`                 | The hash table utilization ratio value of entries/buckets. It is valid only when data_block_index_type=kDataBlockBinaryAndHash. Range: 0.0 to 1.0.                                    |
| rocksdb.block_size                       | `4096` (4 KB)          | Approximate size of user data packed per block, Note that it corresponds to uncompressed data.                                                                                        |
| rocksdb.block_size_deviation             | `10`                   | The percentage of free space used to close a block. Range: 0 to 100.                                                                                                                  |
| rocksdb.block_restart_interval           | `16`                   | The block restart interval for delta encoding in blocks.                                                                                                                              |
| rocksdb.block_cache_capacity             | `8388608` (8 MB)       | The amount of block cache in bytes that will be used by RocksDB, 0 means no block cache. A separate cache of this size is created for each column family.                              |

### Bloom filter options

The options in this group are read only when `rocksdb.bloom_filter_bits_per_key` is 0 or greater. With
the default value of -1 there is no bloom filter and none of the other options in this table take
effect, including the index and filter block caching ones.

| config option                                   | default value | description                                                                                                                                                                                                       |
|-------------------------------------------------|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.bloom_filter_bits_per_key               | `-1`          | The bits per key in bloom filter, a good value is 10, which yields a filter with ~ 1% false positive rate. Set bloom_filter_bits_per_key > 0 to enable bloom filter, -1 means no bloom filter (0~0.5 round down to no filter). |
| rocksdb.bloom_filter_block_based_mode           | `false`       | If bloom filter is enabled, set this option true to use block based filter rather than full filter.                                                                                                                |
| rocksdb.bloom_filter_whole_key_filtering        | `true`        | If bloom filter is enabled, set this option true to place whole keys in the bloom filter, else place the prefix of keys when prefix-extractor is set.                                                               |
| rocksdb.cache_index_and_filter_blocks           | `true`        | Set this option true if we'd put index/filter blocks to the block cache.                                                                                                                                          |
| rocksdb.pin_l0_filter_and_index_blocks_in_cache | `true`        | Set this option true if we'd pin L0 index/filter blocks to the block cache.                                                                                                                                       |
| rocksdb.optimize_filters_for_hits               | `true`        | If bloom filter is enabled, this flag allows us to not store filters for the last level. set this option true to optimize the filters mainly for cases where keys are found rather than also optimize for keys missed. This one is applied even when the filter is disabled. |
| rocksdb.partition_filters_and_indexes           | `false`       | If bloom filter is enabled, set this option true to use partitioned full filters and indexes for each sst file. This option is incompatible with block-based filters. Enabling it also forces the index type to kTwoLevelIndexSearch and sets the metadata block size to `rocksdb.block_size`. |
| rocksdb.pin_top_level_index_and_filter          | `true`        | If partition_filters_and_indexes is set true, set this option true if we'd pin top-level index of partitioned filter and index blocks to the block cache.                                                          |
| rocksdb.prefix_extractor_n_bytes                | `0`           | The prefix-extractor uses the first N bytes of a key as its prefix, it will use the full key when a key is shorter than the N. 0 means unset prefix-extractor.                                                       |

### How the options are applied

The server builds the RocksDB option objects once per store and per column family, so a change to any
of the options above takes effect on the next server start.

- `rocksdb.optimize_mode=true` applies presets before the values in the tables above: at the database
  level it raises parallelism to half of the available processors (at least one), allows concurrent
  memtable writes and enables the write thread adaptive yield; at the column family level it calls the
  RocksDB level-style and universal-style compaction presets. The explicit options are applied
  afterwards, so any value you set in the properties file wins over the preset.
- `rocksdb.bulkload_mode=true` disables automatic compaction, raises the three level-0 triggers to the
  maximum integer and the two pending compaction limits to the maximum long value. Turn it off and
  restart after the load, otherwise compaction never runs.
- `rocksdb.block_cache_capacity=0` turns the block cache off completely rather than making it unbounded.
- `rocksdb.prefix_extractor_n_bytes` greater than 0 installs a capped prefix extractor of that length.
- Every column family uses the `uint64add` merge operator, which is what the counter table relies on.
- The database is created if it is missing, and `avoid_unnecessary_blocking_io` and
  `write_dbid_to_manifest` are always on.

### Memory notes

The caches and write buffers of RocksDB are native allocations, so they are not part of the JVM heap
sizing in `bin/hugegraph-server.sh`. The `GET /metrics/backend` endpoint reports what the store uses:
the memory number is the sum of the block cache usage, the pinned block cache usage, the estimated
table reader memory (index and filter blocks) and the size of all memtables, taken from the RocksDB
properties of every open column family.

Two option values multiply with the number of column families:

- `rocksdb.block_cache_capacity` creates one cache instance per column family, so the total block cache
  of a server is roughly this value times the number of open tables across the `m`, `g` and `s` stores
  of every graph, plus the instances opened for `rocksdb.data_disks`.
- `rocksdb.write_buffer_size` times `rocksdb.max_write_buffer_number` bounds the memtable memory of one
  column family. `rocksdb.db_write_buffer_size` caps the total across all column families of one store,
  and its default of 0 means there is no such cap.

`rocksdb.row_cache_capacity` is different: it is one cache per store, and 0 disables it.

### Ingesting SST files

Setting `rocksdb.sst_path` turns on ingestion. When a store is opened, and again whenever tables are
created, the server walks `<sst_path>/<column family>/`, collects every non-empty `*.sst` file below it
and ingests those files into the matching column family. The files are moved rather than copied, so the
source directory is consumed by the ingestion.

### Raft mode

The RocksDB backend can still run behind the raft state machine: with `raft.mode=true` the store
provider of any local backend is wrapped by the raft provider. The wrapper rejects backends with shared
storage, so `rocksdb` is accepted while `hbase` is not. Under raft mode a RocksDB session writes with
the WAL disabled and without sync, because the state machine can restore from a snapshot plus the raft
log, and snapshots are supported by this backend.

Notes for anyone using it:

- `bin/init-store.sh` forces `raft.mode=false` while it initializes the backend, so initialization never
  goes through raft.
- The shipped `conf/graphs/hugegraph.properties` marks the raft options as deprecated. Distributed
  deployments of 1.7.0 and later use the `hstore` backend with PD and Store instead.
- The raft peer endpoints are served under `graphspaces/{graphspace}/graphs/{graph}/raft/`, with
  `list_peers`, `get_leader`, `set_leader`, `transfer_leader`, `add_peer` and `remove_peer`.
  `bin/raft-tools.sh` wraps the same operations, but it still builds URLs without the graphspace
  segment, so the path has to be adjusted for a 1.7.0 server.
- The remaining `raft.*` options are listed in the
  [Server Complete Configuration Manual](config-option).

### Backend capabilities

The feature flags of this backend affect what the server can push down to the store:

- Scans by key prefix and by key range, paged queries, range conditions and order-by are supported.
- There is no index inside RocksDB, so querying schema by name, querying by label and deleting edges by
  label are done by the server instead of the store.
- Transactions are supported through RocksDB write batches.
- Snapshots are supported, which is what raft mode and backup rely on.
- Shared storage is not supported, so one data directory belongs to one server.
- Olap properties are supported, and their tables are created as extra column families.
- The store does not expire data by itself, so the server filters out elements whose TTL has passed when
  it reads them.
- `in`, `contains` and `contains_key` conditions, aggregate properties and vertex or edge property
  updates in place are not supported at the store level.

### Platform note for riscv64

On Linux riscv64 the RocksDB JNI library needs `libatomic.so.1`. `bin/util.sh` looks for it and adds it
to `LD_PRELOAD` before `bin/hugegraph-server.sh`, `bin/init-store.sh` and `bin/dump-store.sh` start the
JVM. If it is missing, those scripts stop with
`RISC-V RocksDB requires libatomic.so.1; install libatomic1`, and installing the `libatomic1` package
fixes it.
