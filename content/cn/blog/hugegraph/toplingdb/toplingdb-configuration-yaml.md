---
date: 2025-09-30
title: "ToplingDB YAML configuration file"
linkTitle: "ToplingDB的YAML配置文件"
---

RocksDB 提供了丰富的参数配置，但大多数情况下，这些配置需要通过硬编码完成。

[ToplingDB](https://github.com/topling/toplingdb) 在此基础上引入了 **SidePlugin + YAML** 的方式，使得配置更加模块化和可组合。

本文重点介绍 **ToplingDB 扩展参数** 的部分，帮助读者理解这些配置的意义。

## 术语说明

- **MemTable**: LSM-Tree 在内存中的可写数据结构，接收新写入的数据
- **SST (Sorted String Table)**: Memtable 持久化到磁盘后生成的有序键值对文件
- **Flush**: 将 MemTable 数据写入磁盘生成 SST 的过程
- **Compaction**: 合并多个 SST 文件以优化存储和查询性能的过程
- **L0, L1, ... L6**: LSM-Tree 的不同层级，数字越大层级越深

## 0. HugeGraph 中提供的rocksdb_plus.yaml

下文只包括HugeGraph中所使用的配置参数，ToplingDB支持的完整配置请参考：[SidePlugin Wiki](https://github.com/topling/sideplugin-wiki-en/wiki)

```yaml
http: # Web Server 相关配置
  # normally parent path of db path
  document_root: /dev/shm/rocksdb_resource # 静态资源目录, HugeGraph中通过`preload_topling.sh`进行静态资源提取
  listening_ports: '127.0.0.1:2011' # Web Server监听端口，用于管理/监控 如端口被占用，请改为其他端口，例如 2012 或 2013
setenv: # 环境变量设置
  StrSimpleEnvNameNotOverwrite: StringValue
  IntSimpleEnvNameNotOverwrite: 16384
  OverwriteThisEnv:
    #comment: overwrite is default to false
    overwrite: true
    value: force overwrite this env by overwrite true
Cache: # Cache 相关配置
  lru_cache: # 定义一个 LRU 缓存实例
    class: LRUCache
    params: 
      capacity: 8G # 缓存容量 8GB
      num_shard_bits: -1 # 分片数量，-1 表示自动
      strict_capacity_limit: false
      high_pri_pool_ratio: 0.5
      use_adaptive_mutex: false
      metadata_charge_policy: kFullChargeCacheMetadata # 元数据也计入缓存容量
Statistics: # 数据采样配置
  stat:
    class: default
    params:
      discard_tickers: # 丢弃的统计计数器，减少开销
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
      discard_histograms: # 丢弃的直方图统计项
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
      stats_level: kDisableAll  # 禁用所有统计
MemTableRepFactory: # 内存中 memtable 的实现
  cspp: # ToplingDB 独有的高并发内存结构
    class: cspp
    params:
      mem_cap: 16G # 预分配足够的单块内存地址空间，这些内存可以只是保留地址空间，但并未实际分配 对物理内存并无要求，只是为CSPP保留虚拟内存空间
      use_vm: false
      token_use_idle: true
      chunk_size: 16K # 内部分配粒度
      convert_to_sst: kFileMmap # 直接将 MemTable 转化为 SST，省去 Flush，可选值：{kDontConvert, kDumpMem, kFileMmap}
      sync_sst_file: false # convert_to_sst 为 kFileMmap 时，SST 转化完成后是否执行 fsync
  skiplist: # RocksDB 默认的跳表结构
    class: SkipList
    params:
      lookahead: 0
TableFactory:
  cspp_memtab_sst:
    class: CSPPMemTabTable # 与 cspp 配套的 TableFactory
    params: # empty params
  bb:
    class: BlockBasedTable # RocksDB 默认的块表
    params:
      checksum: kCRC32c
      block_size: 4K
      block_restart_interval: 16
      index_block_restart_interval: 1
      metadata_block_size: 4K
      enable_index_compression: true
      block_cache: "${lru_cache}" # 使用上面定义的 LRU 缓存
      block_cache_compressed:
      persistent_cache:
      filter_policy:
  dispatch:
    class: DispatcherTable
    params:
      default: bb # 默认使用 BlockBasedTable
      readers:
        BlockBasedTable: bb
        CSPPMemTabTable: cspp_memtab_sst
      level_writers: [ bb, bb, bb, bb, bb, bb ] # 支持自定义各层写入策略
CFOptions:
  default:
    max_write_buffer_number: 6
    memtable_factory: "${cspp}" # 引用上方定义的cspp，使用 cspp 作为 MemTable
    write_buffer_size: 128M
    # set target_file_size_base as small as 512K is to make many SST files,
    # thus key prefix cache can present efficiency
    target_file_size_base: 64M
    target_file_size_multiplier: 1
    table_factory: dispatch # 引用上方定义的 dispatch, 使用 DispatcherTable Class
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
    statistics: "${stat}"  # 使用上面定义的统计配置
    max_manifest_file_size: 100M
    max_background_jobs: 8 # 设置flush和compaction线程总数 建议设置为 (cpu核数 / 2)
    compaction_readahead_size: 0
    memtable_as_log_index: true # 此配置结合 convert_to_sst: kFileMmap 可实现[omit L0 Flush](https://github.com/topling/toplingdb/wiki/Omit-L0-Flush)

```

**关键要点**:

- `listening_ports: '127.0.0.1:2011'` 指定Web Server监听端口为2011，并且仅允许本地访问
- `memtable_as_log_index: true` 与 `convert_to_sst: kFileMmap` 结合实现[omit L0 Flush](https://github.com/topling/toplingdb/wiki/Omit-L0-Flush)
- `memtable_factory: "${cspp}"` 指定了内存结构采用`CSPP Memtable`
- `table_factory: dispatch` 指定了TableFactory使用YAML中自定义的`DispatcherTable`结构

## 1. 插件化配置与引用机制

- **YAML 插件化**：配置文件以对象形式组织，每个对象可以单独定义并在其他地方引用。
- **引用语法**：通过 `${lru_cache}`、`${cspp}` 等方式在不同段落复用对象。
- **DispatcherTable**：允许在不同层级或场景下选择不同的 TableFactory。RocksDB 原生只能指定单一 TableFactory。

ToplingDB YAML 引用与复用图示:

<div style="text-align: center;">
  <img src="/img/blog/images-server/toplingdb-yaml-ref.png" alt="image" width="800">
</div>

这种机制使得配置更灵活，便于在复杂场景下组合不同组件。

## 2. 新的 MemTable 实现：CSPP

ToplingDB 提供了一个 RocksDB 原生没有的 MemTable 类型，通过以下参数配置：

### mem_cap

`mem_cap` 是指在内存地址空间中，为 CSPP 预留的空间大小，这些内存可以只是**保留地址空间，并未实际分配的**。
`mem_cap` 真正占用的内存大小约为 `write_buffer_size` 。

#### mem_cap 设计背景

CSPP 的底层算法为了支持高并发写入，采用了预分配内存的策略。
当预分配的内存被写满时，新的写入操作将无法继续。
然而，RocksDB 本身缺乏一种机制，使得 memtable 能够主动反馈 '预分配内存已满，需要切换到新的 memtable' 。
由于其函数调用链路复杂，难以通过重构来实现这一机制，因此 `CSPP` 只能通过参数设计来适配 RocksDB 的行为。

#### mem_cap 核心思路

ToplingDB 将 `mem_cap` 设置为远大于 `write_buffer_size`，从而避免 RocksDB 在向 Memtable 写入时过早触发“内存已满”的错误。
在 CSPP 初始化（New）时，会再次检查，如果发现 `mem_cap` 设置过小，则会自动调整为 `2 * write_buffer_size`，以确保写入过程的稳定性。

`mem_cap` 默认值为 2G，有效最大值为 16G。

- 小型部署（< 16GB 内存）: 建议设置为系统内存的 20-30%
- 中型部署（16-64GB 内存）: 建议设置为 8-16G
- 大型部署（> 64GB 内存）: 建议设置为 16G

### use_vm

在使用 malloc/posix_memalign 分配内存时，地址空间可能是已经实际分配的（位于堆空间中，已有对应的物理页面），而 CSPP 在分配时只需要获得保留的地址空间。
`use_vm` 选项为 `true` 时会强制使用 `mmap` 分配内存，从而保证分配的一定时是保留地址空间，但并不实际占用物理页面。
`use_vm` 默认值为 `true`。如果用户物理内存空间充足，建议关闭此选项，`mmap` 分配的虚拟内存空间在建立对物理地址的映射时会触发大量minor page fault，可能会影响性能。

### convert_to_sst

`convert_to_sst` 支持以下三种枚举值:

- `kDontConvert`: 禁用该功能，为默认值。使用传统的 Flush 流程，兼容性最好，适合对稳定性要求高的场景
- `kDumpMem`: 转化时将 MemTable 的整块内存写入 SST 文件，避免 CPU 消耗，但未降低内存消耗
- `kFileMmap`: 将 MemTable 内容 mmap 到文件，这是关键功能，同时降低 CPU 和内存消耗，可同时将 DBOptions.memtable_as_log_index 设为 true 从本质上消除 MemTable Flush

这些参数为数据写入路径提供了更多可调节空间，用户可按需选择。

更多设计细节请参考 ToplingDB 作者的撰写的相关博客：[cspp-memtable](https://github.com/topling/cspp-memtable/blob/memtable_as_log_index/README_EN.md), [ToplingDB CSPP MemTable Design Essentials](https://zhuanlan.zhihu.com/p/649435555), [CSPP Trie Design Analysis](https://zhuanlan.zhihu.com/p/499138254)

## 3. TableFactory 扩展

- **CSPPMemTabTable**：与 `cspp` MemTable 配套的 TableFactory。
- **DispatcherTable**：支持为不同层级指定不同的 TableFactory，例如：
  - 默认使用 BlockBasedTable。
  - 特定层级可以使用 CSPPMemTabTable。

这类灵活性在 RocksDB 原生配置中并不存在。

## 4. 统计与观测控制

- **discard_tickers / discard_histograms**：可以精确指定哪些统计项需要丢弃。
- **stats_level: kDisableAll**：结合上述配置，可以灵活控制统计开销。

相比 RocksDB 的粗粒度控制，ToplingDB 提供了更细的调节方式。

## 5. DBOptions 新增参数

- **memtable_as_log_index: true**：允许使用 MemTable 作为日志索引，加快恢复速度。

## 6. 安全注意事项

**Web Server 安全配置**:

- Web Server 页面由ToplingDB提供，不包含权限认证功能
- 默认设置 `listening_ports: '127.0.0.1:2011'` 仅限本地访问
- 生产环境建议配置防火墙规则，仅允许内网访问
- 如需禁用 Web Server，在 `hugegraph.properties` 中设置 `rocksdb.open_http=false`

**共享内存安全**:

- `document_root: /dev/shm/rocksdb_resource` 使用共享内存目录
- 多用户环境需要注意文件权限设置，避免未授权访问

## 7. 总结

ToplingDB 在 RocksDB 的基础上增加了以下能力：

- 插件化配置与对象复用
- 新的 MemTable 类型（cspp）及配套 TableFactory
- DispatcherTable 支持多工厂调度
- 内置 Web Server
- 更灵活的统计与观测控制
- 特殊 DBOptions（如 memtable_as_log_index）

这些扩展为用户提供了更多的可调节空间，尤其适合需要高写入性能和灵活运维的场景。

## 相关文档

- [ToplingDB 快速开始](/cn/blog/2025/10/09/toplingdb-quick-start/) – 如何在 HugeGraph 中启用 ToplingDB
- [RocksDB 官方配置文档](https://github.com/facebook/rocksdb/wiki/Setup-Options-and-Basic-Tuning) – 了解基础配置项
- [SidePlugin Wiki](https://github.com/topling/sideplugin-wiki-en/wiki) – ToplingDB 完整配置参考
