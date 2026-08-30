---
date: 2025-09-30
title: "ToplingDB YAML configuration file"
linkTitle: "ToplingDB YAML configuration file"
---

RocksDB provides a rich set of configuration parameters, but most of them typically require hardcoded setup.

[ToplingDB](https://github.com/topling/toplingdb) introduces a **SidePlugin + YAML** mechanism, making configuration more modular and composable.

This document focuses on the **extended parameters of ToplingDB**, helping readers understand their purpose and usage.

## 0. rocksdb_plus.yaml used in HugeGraph

The following includes only the configuration parameters used in HugeGraph. For the full configuration supported by ToplingDB, refer to the [SidePlugin Wiki](https://github.com/topling/sideplugin-wiki-en/wiki):

```yaml
http: # Web Server related configuration
  # normally parent path of db path
  document_root: /dev/shm/rocksdb_resource # Static resource directory, extracted by `preload_topling.sh` in HugeGraph
  listening_ports: '127.0.0.1:2011' # Web Server listening port for management/monitoring

setenv: # Environment variable settings
  StrSimpleEnvNameNotOverwrite: StringValue
  IntSimpleEnvNameNotOverwrite: 16384
  OverwriteThisEnv:
    #comment: overwrite is default to false
    overwrite: true
    value: force overwrite this env by overwrite true

Cache: # Cache configuration
  lru_cache: # Define an LRU cache instance
    class: LRUCache
    params: 
      capacity: 8G # Cache capacity: 8GB
      num_shard_bits: -1 # Number of shards, -1 means auto
      strict_capacity_limit: false
      high_pri_pool_ratio: 0.5
      use_adaptive_mutex: false
      metadata_charge_policy: kFullChargeCacheMetadata # Metadata also counts toward cache capacity

Statistics: # Sampling configuration
  stat:
    class: default
    params:
      discard_tickers: # Discarded tickers to reduce overhead
        - rocksdb.block.cache
        - rocksdb.block.cachecompressed
        - rocksdb.block
        - rocksdb.memtable.payload.bytes.at.flush
        - rocksdb.memtable.garbage.bytes.at.flush
        - rocksdb.txn
        - rocksdb.blobdb
        - rocksdb.row.cache
        - rocksdb.number.block
        - rocksdb.bloom.filter
        - rocksdb.persistent
        - rocksdb.sim.block.cache
      discard_histograms: # Discarded histogram metrics
        # comment: ....
        - rocksdb.blobdb
        - rocksdb.bytes.compressed
        - rocksdb.bytes.decompressed
        - rocksdb.num.index.and.filter.blocks.read.per.level
        - rocksdb.num.data.blocks.read.per.level
        - rocksdb.compression.times.nanos
        - rocksdb.decompression.times.nanos
        - rocksdb.read.block.get.micros
        - rocksdb.write.raw.block.micros
      # comment end of array
      #stats_level: kAll
      stats_level: kDisableAll  # Disable all statistics

MemTableRepFactory: # MemTable implementation in memory
  cspp: # ToplingDB-specific high-concurrency memory structure
    class: cspp
    params:
      mem_cap: 16G # Preallocate sufficient virtual memory space; may reserve address space without actual allocation
      use_vm: false
      token_use_idle: true
      chunk_size: 16K # Internal allocation granularity
      convert_to_sst: kFileMmap # Convert MemTable directly to SST, skipping flush; options: {kDontConvert, kDumpMem, kFileMmap}
      sync_sst_file: false # Whether to fsync after SST conversion when using kFileMmap

  skiplist: # Default skiplist structure in RocksDB
    class: SkipList
    params:
      lookahead: 0

TableFactory:
  cspp_memtab_sst:
    class: CSPPMemTabTable # TableFactory paired with cspp
    params: # empty params

  bb:
    class: BlockBasedTable # Default block-based table in RocksDB
    params:
      checksum: kCRC32c
      block_size: 4K
      block_restart_interval: 16
      index_block_restart_interval: 1
      metadata_block_size: 4K
      enable_index_compression: true
      block_cache: "${lru_cache}" # Use the LRU cache defined above
      block_cache_compressed:
      persistent_cache:
      filter_policy:

  dispatch:
    class: DispatcherTable
    params:
      default: bb # Default to BlockBasedTable
      readers:
        BlockBasedTable: bb
        CSPPMemTabTable: cspp_memtab_sst
      level_writers: [ bb, bb, bb, bb, bb, bb ] # Custom write strategy per level

CFOptions:
  default:
    max_write_buffer_number: 6
    memtable_factory: "${cspp}" # Reference cspp defined above
    write_buffer_size: 128M
    # set target_file_size_base as small as 512K is to make many SST files,
    # thus key prefix cache can present efficiency
    target_file_size_base: 64M
    target_file_size_multiplier: 1
    table_factory: dispatch # Reference dispatch defined above
    max_bytes_for_level_base: 512M
    max_bytes_for_level_multiplier: 10
    level_compaction_dynamic_level_bytes: false
    level0_slowdown_writes_trigger: 20
    level0_stop_writes_trigger: 36
    level0_file_num_compaction_trigger: 2
    merge_operator: uint64add # support merge
    level_compaction_dynamic_file_size: true
    optimize_filters_for_hits: true
    allow_merge_memtables: true
    min_write_buffer_number_to_merge: 2
    compression_per_level:
      - kNoCompression
      - kNoCompression
      - kSnappyCompression
      - kSnappyCompression
      - kSnappyCompression
      - kSnappyCompression
      - kSnappyCompression

DBOptions:
  dbo:
    create_if_missing: true
    create_missing_column_families: false # this is important, must be false to hugegraph
    max_background_compactions: -1
    max_subcompactions: 4
    max_level1_subcompactions: 0
    inplace_update_support: false
    WAL_size_limit_MB: 0
    statistics: "${stat}"  # Use the statistics config defined above
    max_manifest_file_size: 100M
    max_background_jobs: 8
    compaction_readahead_size: 0
    memtable_as_log_index: true # Combined with convert_to_sst: kFileMmap to enable [omit L0 Flush](https://github.com/topling/toplingdb/wiki/Omit-L0-Flush)
```

**Key points**:

- `listening_ports: '127.0.0.1:2011'` sets the Web Server listening port to 2011 and restricts access to localhost.
- `memtable_as_log_index: true` combined with `convert_to_sst: kFileMmap` enables [omit L0 Flush](https://github.com/topling/toplingdb/wiki/Omit-L0-Flush).
- `memtable_factory: "${cspp}"` specifies the memory structure as `CSPP Memtable`.
- `table_factory: dispatch` sets the TableFactory to the custom `DispatcherTable` defined in YAML.

## 1. Plugin-based configuration and reference mechanism

- **YAML modularization**: The configuration file is organized as objects; each object can be defined independently and referenced elsewhere.
- **Reference syntax**: Objects can be reused across sections via `${lru_cache}`, `${cspp}`, etc.
- **DispatcherTable**: Allows selecting different TableFactories at different levels or scenarios. RocksDB natively supports only a single TableFactory.

ToplingDB YAML Reference and Reuse Diagram:

<div style="text-align: center;">
  <img src="/img/blog/images-server/toplingdb-yaml-ref.png" alt="ToplingDB YAML Reference Diagram" width="800">
</div>

This mechanism makes configuration more flexible and easier to compose in complex scenarios.

## 2. New MemTable implementation: CSPP

ToplingDB provides a MemTable type that RocksDB does not natively have, configured with the following parameters:

### mem_cap

`mem_cap` is the size of the virtual address space reserved for CSPP. This may be just reserved address space without actual physical allocation.
The actual memory usage of `mem_cap` is approximately equal to `write_buffer_size`.

#### Background of mem_cap Design

The underlying algorithm of CSPP adopts a pre-allocation strategy to support high-concurrency writes.
Once the pre-allocated memory is filled, no further writes can proceed.
However, RocksDB itself lacks a mechanism that allows a memtable to actively report
"the pre-allocated memory is full, a new memtable is required".
Due to the complexity of its call chain, it is impractical to refactor RocksDB to add this capability.
Therefore, CSPP adapts to RocksDB’s behavior through parameter design.

#### Core Idea of mem_cap

ToplingDB sets `mem_cap` to be much larger than `write_buffer_size`,
so that RocksDB will not prematurely trigger an "out of memory" error when writing to a memtable.
During CSPP initialization (`New`), the system rechecks the setting.
If `mem_cap` is found to be too small, it will be automatically adjusted to `2 * write_buffer_size` to ensure stability during the write process.

The default value is 2G, and the effective maximum is 16G.

- Small deployments (<16GB RAM): set to 20–30% of system memory
- Medium deployments (16–64GB RAM): set to 8–16G
- Large deployments (>64GB RAM): set to 16G

### use_vm

When allocating memory via `malloc/posix_memalign`, the address space may already be physically allocated (heap space with mapped pages), while CSPP only needs reserved virtual address space.  
When `use_vm` is `true`, allocation is forced to use `mmap`, ensuring reserved address space without occupying physical pages.  
The default is `true`. If physical memory is sufficient, it is recommended to disable this option—establishing mappings from `mmap`’s virtual memory to physical pages can trigger many minor page faults and may affect performance.

### convert_to_sst

`convert_to_sst` supports three enum values:

- `kDontConvert`: Disables the feature (default). Uses the traditional Flush process, offering the best compatibility for stability-focused scenarios.
- `kDumpMem`: During conversion, dumps the entire MemTable memory to an SST file, reducing CPU consumption but not memory usage.
- `kFileMmap`: `mmap`s MemTable content into a file—the key feature—reduces both CPU and memory usage. You can also set `DBOptions.memtable_as_log_index = true` to essentially eliminate MemTable Flush.

These parameters offer more tunable options for the write path, allowing users to choose as needed.

For more design details, see: [cspp-memtable](https://github.com/topling/cspp-memtable/blob/memtable_as_log_index/README_EN.md), [ToplingDB CSPP MemTable Design Essentials](https://zhuanlan.zhihu.com/p/649435555), [CSPP Trie Design Analysis](https://zhuanlan.zhihu.com/p/499138254).

## 3. TableFactory extensions

- **CSPPMemTabTable**: The TableFactory paired with the `cspp` MemTable.
- **DispatcherTable**: Supports specifying different TableFactories per level, for example:
  - Use BlockBasedTable by default.
  - Use CSPPMemTabTable for specific levels.

This level of flexibility is not available in native RocksDB configuration.

## 4. Statistics and observability controls

- **discard_tickers / discard_histograms**: Precisely specify which statistics to discard.
- **stats_level: kDisableAll**: Combined with the above, flexibly control the overhead of statistics.

Compared to RocksDB’s coarse-grained controls, ToplingDB offers finer tuning.

## 5. New DBOptions parameter

- **memtable_as_log_index: true**: Allows using the MemTable as a log index to speed up recovery.

## 6. Security considerations

**Web Server security**:

- The Web Server pages are provided by ToplingDB and do not include authentication.
- By default, `listening_ports: '127.0.0.1:2011'` restricts access to local requests.
- In production, configure firewall rules to allow only intranet access.
- To disable the Web Server, set `rocksdb.open_http=false` in `hugegraph.properties`.

**Shared memory safety**:

- `document_root: /dev/shm/rocksdb_resource` uses a shared memory directory.
- In multi-user environments, ensure proper file permissions to avoid unauthorized access.

## 7. Summary

ToplingDB adds the following capabilities on top of RocksDB:

- Plugin-based configuration and object reuse
- A new MemTable type (cspp) with a paired TableFactory
- DispatcherTable for multi-factory scheduling
- Built-in Web Server
- More flexible statistics and observability controls
- Special DBOptions (such as `memtable_as_log_index`)

These extensions give users more tuning space, particularly suited for scenarios requiring high write performance and flexible operations.

## Related Documentation

- [ToplingDB Quick Start](/blog/2025/10/09/toplingdb-quick-start) – How to enable ToplingDB in HugeGraph
- [RocksDB Official Configuration Guide](https://github.com/facebook/rocksdb/wiki/Setup-Options-and-Basic-Tuning) – Learn the basic configuration options
- [SidePlugin Wiki](https://github.com/topling/sideplugin-wiki-en/wiki) – Complete configuration reference for ToplingDB
