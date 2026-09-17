---
title: "配置 RocksDB 后端"
linkTitle: "配置 RocksDB 后端"
weight: 5
---

### 概述

RocksDB 是一个嵌入式的 LSM-tree 键值存储。使用 `rocksdb` 后端时，HugeGraph-Server 把全部图数据保存在
服务进程内部的 RocksDB 实例中，不需要额外部署存储服务。发布包中的 `conf/graphs/hugegraph.properties`
默认使用的就是这个后端。

从 1.7.0 版本开始，服务端只接受 `memory`、`rocksdb`、`hbase` 和 `hstore` 作为后端。`rocksdb` 后端把
数据写在单台服务器的本地磁盘上，不支持共享存储，因此多个服务无法基于同一个数据目录提供同一个图。
分布式部署请使用 `hstore` 后端，配合 PD 与 Store。

RocksDB 的 JNI 依赖在 `hugegraph-rocksdb/pom.xml` 中固定为 `8.10.2` 版本，因此磁盘格式与各配置项的
语义都以 RocksDB 8.10 为准。

该后端上报的驱动版本是 `1.11`，在初始化图时会写入 system store 的 meta 表中。

### 选择后端

在图配置文件（`conf/graphs/<graph>.properties`）中设置后端与序列化器：

```properties
gremlin.graph=org.apache.hugegraph.HugeFactory

backend=rocksdb
serializer=binary

store=hugegraph

# rocksdb backend config
#rocksdb.data_path=/path/to/disk
#rocksdb.wal_path=/path/to/disk
```

- `backend=rocksdb` 选择 RocksDB 存储实现。
- `serializer=binary` 是发布包模板为该后端使用的序列化器。内置的序列化器为 `binary`、`binaryscatter`
  和 `text`。
- `store` 是该图在后端中的库名，同时也是存储实现拿到的图名的一部分。

首次启动前执行一次 `bin/init-store.sh` 创建各个 store，然后再启动服务。`bin/init-store.sh` 与
`bin/hugegraph-server.sh` 都会加载 RocksDB 库，数据目录在执行这些脚本的机器上创建。

发布包会为打包时 `backend.properties` 中列出的每个后端注册配置项空间和存储实现，该文件的取值来自
`hugegraph.backends` 构建属性。默认构建会注册 `rocksdb, hbase, hstore`；使用 `-Drocksdb-only` 构建会
激活 `rocksdb-only` profile，产出的发布包只注册 `rocksdb`。未注册的后端在启动时会报
`Not exists BackendStoreProvider`。

注册过程还会额外注册一个名字 `rocksdbsst`，它对应的实现写出 SST 文件而不是打开一个可用的数据库。
该名字不在允许的后端列表中，因此 `backend=rocksdbsst` 会被拒绝并报 `backend is illegal: rocksdbsst`。
如果要把 SST 文件导入普通的 `rocksdb` 图，请使用下面介绍的 `rocksdb.sst_path`。

### 数据目录结构

有两个目录需要关注：`rocksdb.data_path`（默认 `rocksdb-data/data`）和 `rocksdb.wal_path`
（默认 `rocksdb-data/wal`）。相对路径基于服务的工作目录解析，也就是安装目录。

每个图会打开三个 store：`m` 存放 schema，`g` 存放图数据，`s` 是 system store。store 名会拼接到上面
两个路径之后，因此一个默认的单图安装目录如下：

```
rocksdb-data/
  data/
    m/    # schema store：属性键、顶点/边/索引标签、计数器
    g/    # graph store：顶点、边、索引表、olap 表
    s/    # system store：任务、服务信息、后端 meta（驱动版本）
  wal/
    m/
    g/
    s/
```

后端的每张表在所属 store 中对应一个 RocksDB 列族，名字形如 `<database>+<table>`，其中 database 由图名
推导得到。已有数据目录中的列族总是会被重新打开，因此旧版本创建的表仍然可读。

还需要注意：

- 两个图不能共用同一个数据路径。通过 API 基于已有配置克隆创建图时，存储实现会在
  `rocksdb.data_path` 和 `rocksdb.wal_path` 后面追加 `_<newGraph>`。删除这样的图会同时删除这两个目录。
- 快照创建在数据目录旁边：数据路径的最后两段会加上前缀重写，因此在默认路径下 graph store 的快照位于
  `rocksdb-data/<prefix>_data/g`。恢复快照时会先关闭实例，删除数据目录，再把快照移动到原位置。
- 设置了 `rocksdb.data_disks` 时，其中列出的表会在指定路径下作为独立的 RocksDB 实例打开，而不再放在
  `rocksdb.data_path` 下。服务最多并发打开 8 个实例，打开最多等待 600 秒，会话关闭最多等待 30 秒。

### 路径与日志配置项

| config option        | default value       | description                                                                                                                                                                                                                                                                                                                                       |
|----------------------|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.data_path    | `rocksdb-data/data` | RocksDB 数据存储路径，不允许为空。                                                                                                                                                                                                                                                                                                                |
| rocksdb.data_disks   | `[]`                | 为部分表指定独立磁盘，每个元素格式为 `STORE/TABLE: /path/disk`。允许的键为 [g/vertex, g/edge_out, g/edge_in, g/vertex_label_index, g/edge_label_index, g/range_int_index, g/range_float_index, g/range_long_index, g/range_double_index, g/secondary_index, g/search_index, g/shard_index, g/unique_index, g/olap]。磁盘路径不能与 `rocksdb.data_path` 相同。 |
| rocksdb.wal_path     | `rocksdb-data/wal`  | RocksDB WAL 存储路径，不允许为空。                                                                                                                                                                                                                                                                                                                |
| rocksdb.sst_path     | （空）              | 待导入 RocksDB 的 SST 文件所在路径，为空表示不导入。                                                                                                                                                                                                                                                                                              |
| rocksdb.log_level    | `INFO`              | RocksDB 的日志级别，可选值：DEBUG、INFO、WARN、ERROR、FATAL、HEADER。                                                                                                                                                                                                                                                                             |

### 压缩与合并配置项

| config option                  | default value                                          | description                                                                                                                            |
|--------------------------------|--------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.num_levels             | `7`                                                    | 数据库的层数，取值范围 1 到 2^31-1。                                                                                                   |
| rocksdb.compaction_style       | `LEVEL`                                                | RocksDB 的 compaction 策略：LEVEL/UNIVERSAL/FIFO。                                                                                     |
| rocksdb.optimize_mode          | `true`                                                 | 针对高负载和大数据量做优化，具体行为见下文的配置项生效方式一节。                                                                         |
| rocksdb.bulkload_mode          | `false`                                                | 切换到批量导入数据的模式。                                                                                                              |
| rocksdb.compression_per_level  | `[none, none, snappy, snappy, snappy, snappy, snappy]` | 各层使用的压缩算法，可选值为 none/snappy/z/bzip2/lz4/lz4hc/xpress/zstd。列表必须为空，或者元素个数正好等于 `rocksdb.num_levels`。         |
| rocksdb.bottommost_compression | `none`                                                 | 最底层使用的压缩算法，可选值为 none/snappy/z/bzip2/lz4/lz4hc/xpress/zstd。                                                               |
| rocksdb.compression            | `snappy`                                               | 压缩数据块使用的压缩算法，可选值为 none/snappy/z/bzip2/lz4/lz4hc/xpress/zstd。                                                           |

### 数据库级配置项

| config option                          | default value        | description                                                                                                     |
|----------------------------------------|----------------------|-----------------------------------------------------------------------------------------------------------------|
| rocksdb.max_background_jobs            | `8`                  | 后台任务（包括 flush 和 compaction）的最大并发数，取值范围 1 到 2^31-1。                                          |
| rocksdb.max_subcompactions             | `4`                  | 单个 compaction 任务使用的最大线程数，取值范围 1 到 2^31-1。                                                     |
| rocksdb.delayed_write_rate             | `16777216`（16 MB/s）| 当 compaction 落后需要降速时，用户写请求的限速值，单位字节每秒。                                                  |
| rocksdb.max_open_files                 | `-1`                 | RocksDB 可缓存的最大打开文件数，-1 表示不限制。                                                                  |
| rocksdb.max_manifest_file_size         | `104857600`（100 MB）| manifest 文件的最大字节数。                                                                                      |
| rocksdb.skip_stats_update_on_db_open   | `false`              | 打开数据库时是否跳过统计信息更新，设为 true 表示不更新统计信息。                                                  |
| rocksdb.skip_check_sst_size_on_db_open | `false`              | 打开数据库时是否跳过检查所有 sst 文件的大小。                                                                    |
| rocksdb.max_file_opening_threads       | `16`                 | 打开文件使用的最大线程数，取值范围 1 到 2^31-1。                                                                 |
| rocksdb.max_total_wal_size             | `0`                  | WAL 文件的总大小上限，单位字节。超过后会强制 flush 相关的列族，0 表示不限制。                                     |
| rocksdb.bytes_per_sync                 | `0`                  | 允许操作系统在后台异步地增量同步正在写入的 SST 文件，每写入这么多字节发起一次请求，0 表示关闭。                    |
| rocksdb.wal_bytes_per_sync             | `0`                  | 同上，作用于 WAL 文件，0 表示关闭。                                                                              |
| rocksdb.strict_bytes_per_sync          | `false`              | 为 true 时保证任意时刻提交回写的 SST/WAL 数据不超过 bytes_per_sync/wal_bytes_per_sync 字节，可用于处理写入速度超过 I/O 速度的场景。 |
| rocksdb.db_write_buffer_size           | `0`                  | 所有列族 write buffer 的总大小上限，单位字节，0 表示不限制。                                                     |
| rocksdb.log_readahead_size             | `0`                  | 读取日志时预取的字节数，0 表示关闭预取。                                                                         |
| rocksdb.compaction_readahead_size      | `0`                  | compaction 时批量读取的字节数。如果 RocksDB 跑在机械盘上，建议至少设为 2MB，0 表示关闭预取。                       |
| rocksdb.row_cache_capacity             | `0`                  | 表级行缓存的全局容量，单位字节，0 表示关闭 row_cache。                                                            |
| rocksdb.delete_obsolete_files_period   | `21600`（6 小时）    | 删除废弃文件的周期，单位秒，0 表示每次都做完整清理。该值传给 RocksDB 前会换算成微秒。                              |

### Memtable 配置项

| config option                               | default value        | description                                                                                                                     |
|---------------------------------------------|----------------------|---------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.write_buffer_size                   | `134217728`（128 MB）| 在内存中累积的数据量，单位字节，最小 1 MB。该值针对单个列族生效。                                                                 |
| rocksdb.max_write_buffer_number             | `6`                  | 内存中累积的 write buffer 的最大个数，取值范围 1 到 2^31-1。                                                                     |
| rocksdb.min_write_buffer_number_to_merge    | `2`                  | 会被合并到一起的 write buffer 的最小个数，取值范围 1 到 2^31-1。                                                                 |
| rocksdb.max_write_buffer_number_to_maintain | `0`                  | 使用事务时，为冲突检查在内存中保留的 write buffer 总数上限。                                                                      |
| rocksdb.memtable_bloom_size_ratio           | `0.0`                | 设置了 prefix-extractor 且该值不为 0，或者 memtable_whole_key_filtering 为 true 时，为 memtable 创建大小为 write_buffer_size * memtable_bloom_size_ratio 的布隆过滤器。大于 0.25 的取值会被收敛为 0.25，取值范围 0.0 到 1.0。 |
| rocksdb.memtable_whole_key_filtering        | `false`              | 在 memtable 中启用全键布隆过滤器，可以降低点查的 CPU 开销。只有 memtable_bloom_size_ratio > 0 时才生效。                          |
| rocksdb.memtable_huge_page_size             | `0`                  | memtable 中布隆过滤器使用的 huge page TLB 的页大小，小于等于 0 时不从 huge page TLB 分配，改用 malloc。                            |
| rocksdb.inplace_update_support              | `false`              | 当写入的键已存在于当前 memtable 且新值更小时，允许线程安全的原地更新。                                                             |

### 层级大小与写入限流配置项

| config option                                | default value           | description                                                                                                                                                                                                        |
|----------------------------------------------|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.level_compaction_dynamic_level_bytes | `false`                 | 是否启用 level_compaction_dynamic_level_bytes。启用后 max_bytes_for_level_multiplier 的优先级高于 max_bytes_for_level_base，基准层的大小是动态的，LSM tree 更可预测，有助于限制最差情况下的空间放大。对已有数据库开关该特性可能造成异常的 LSM tree 结构，因此不推荐改动。 |
| rocksdb.max_bytes_for_level_base             | `536870912`（512 MB）   | level-1 文件总大小的上限，单位字节，最小 1 MB。                                                                                                                                                                    |
| rocksdb.max_bytes_for_level_multiplier       | `10.0`                  | 对所有层 L，第 L+1 层文件总大小与第 L 层文件总大小的比值，最小 1.0。                                                                                                                                               |
| rocksdb.target_file_size_base                | `67108864`（64 MB）     | compaction 的目标文件大小，单位字节，最小 1 MB。                                                                                                                                                                   |
| rocksdb.target_file_size_multiplier          | `1`                     | 第 L 层文件与第 L+1 层文件的大小比值。                                                                                                                                                                             |
| rocksdb.level0_file_num_compaction_trigger   | `2`                     | 触发 level-0 compaction 的文件数。                                                                                                                                                                                 |
| rocksdb.level0_slowdown_writes_trigger       | `20`                    | 触发写入降速的 level-0 文件数软上限。                                                                                                                                                                              |
| rocksdb.level0_stop_writes_trigger           | `36`                    | 触发停写的 level-0 文件数硬上限。                                                                                                                                                                                   |
| rocksdb.soft_pending_compaction_bytes_limit  | `68719476736`（64 GB）  | 待 compaction 数据量的软上限，单位字节，最小 1 GB。                                                                                                                                                                |
| rocksdb.hard_pending_compaction_bytes_limit  | `274877906944`（256 GB）| 待 compaction 数据量的硬上限，单位字节，最小 1 GB。                                                                                                                                                                |

### 文件 I/O 配置项

| config option                                  | default value | description                                                                                          |
|------------------------------------------------|---------------|------------------------------------------------------------------------------------------------------|
| rocksdb.allow_mmap_writes                      | `false`       | 允许操作系统以 mmap 方式写文件。                                                                     |
| rocksdb.allow_mmap_reads                       | `false`       | 允许操作系统以 mmap 方式读取 sst 文件。                                                              |
| rocksdb.use_direct_reads                       | `false`       | 读取 sst 文件时使用直接 I/O。                                                                        |
| rocksdb.use_direct_io_for_flush_and_compaction | `false`       | flush 和 compaction 时使用直接读写。                                                                 |
| rocksdb.use_fsync                              | `false`       | 为 true 时每次持久化都会执行 fsync。                                                                 |
| rocksdb.atomic_flush                           | `false`       | 为 true 时多个列族的 flush 结果会原子地提交到 MANIFEST。WAL 一直开启的情况下不必设置该项。             |

### SST 表格式与块缓存配置项

| config option                            | default value            | description                                                                                                                          |
|------------------------------------------|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.format_version                   | `5`                      | BlockBasedTable 的格式版本，可选值为 0~5。                                                                                            |
| rocksdb.index_type                       | `kBinarySearch`          | sst 文件中数据块之间查找使用的索引类型，可选值为 [kBinarySearch, kHashSearch, kTwoLevelIndexSearch, kBinarySearchWithFirstKey]。        |
| rocksdb.data_block_index_type            | `kDataBlockBinarySearch` | sst 文件数据块内点查使用的查找类型，可选值为 [kDataBlockBinarySearch, kDataBlockBinaryAndHash]。                                        |
| rocksdb.data_block_hash_table_util_ratio | `0.75`                   | 哈希表 entries/buckets 的使用率，仅在 data_block_index_type=kDataBlockBinaryAndHash 时有效，取值范围 0.0 到 1.0。                       |
| rocksdb.block_size                       | `4096`（4 KB）           | 每个块中打包的用户数据的近似大小，注意对应的是未压缩的数据。                                                                            |
| rocksdb.block_size_deviation             | `10`                     | 用于结束一个块的空闲空间百分比，取值范围 0 到 100。                                                                                    |
| rocksdb.block_restart_interval           | `16`                     | 块内增量编码的 restart 间隔。                                                                                                          |
| rocksdb.block_cache_capacity             | `8388608`（8 MB）        | RocksDB 使用的块缓存大小，单位字节，0 表示不使用块缓存。每个列族都会创建一个该大小的独立缓存。                                          |

### 布隆过滤器配置项

只有 `rocksdb.bloom_filter_bits_per_key` 大于等于 0 时，本组的配置项才会被读取。默认值 -1 表示不启用
布隆过滤器，此时本表中其他配置项都不生效，包括索引和过滤块的缓存相关项。

| config option                                   | default value | description                                                                                                                                     |
|-------------------------------------------------|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| rocksdb.bloom_filter_bits_per_key               | `-1`          | 布隆过滤器中每个键占用的位数，10 是一个不错的取值，对应约 1% 的误判率。大于 0 表示启用布隆过滤器，-1 表示不启用（0~0.5 向下取整为不启用）。        |
| rocksdb.bloom_filter_block_based_mode           | `false`       | 启用布隆过滤器时，设为 true 表示使用 block based filter 而不是 full filter。                                                                      |
| rocksdb.bloom_filter_whole_key_filtering        | `true`        | 启用布隆过滤器时，设为 true 表示把完整的键放入布隆过滤器，否则在设置了 prefix-extractor 时放入键的前缀。                                          |
| rocksdb.cache_index_and_filter_blocks           | `true`        | 设为 true 表示把索引块和过滤块放入块缓存。                                                                                                        |
| rocksdb.pin_l0_filter_and_index_blocks_in_cache | `true`        | 设为 true 表示把 L0 的索引块和过滤块固定在块缓存中。                                                                                              |
| rocksdb.optimize_filters_for_hits               | `true`        | 启用布隆过滤器时，该开关允许不为最后一层存储过滤器，设为 true 表示主要针对命中的场景优化过滤器，而不是同时优化未命中的场景。该项在过滤器关闭时也会生效。 |
| rocksdb.partition_filters_and_indexes           | `false`       | 启用布隆过滤器时，设为 true 表示每个 sst 文件使用分区的 full filter 和索引。该项与 block based filter 不兼容。开启后索引类型会被强制为 kTwoLevelIndexSearch，元数据块大小取 `rocksdb.block_size`。 |
| rocksdb.pin_top_level_index_and_filter          | `true`        | 当 partition_filters_and_indexes 为 true 时，设为 true 表示把分区过滤块和索引块的顶层索引固定在块缓存中。                                          |
| rocksdb.prefix_extractor_n_bytes                | `0`           | prefix-extractor 取键的前 N 个字节作为前缀，键长度小于 N 时使用完整键，0 表示不设置 prefix-extractor。                                             |

### 配置项的生效方式

服务为每个 store 和每个列族构建一次 RocksDB 的选项对象，因此上面任何配置项的修改都在下次启动服务时
生效。

- `rocksdb.optimize_mode=true` 会在应用上表中的取值之前先套用一组预设：数据库层面把并行度提高到可用
  处理器数的一半（至少 1），允许 memtable 并发写入，并开启写线程自适应让出；列族层面调用 RocksDB 的
  level-style 和 universal-style compaction 预设。显式配置项在之后应用，因此配置文件中写明的取值会覆盖
  预设。
- `rocksdb.bulkload_mode=true` 会关闭自动 compaction，把三个 level-0 触发阈值提高到 int 最大值，把两个
  待 compaction 上限提高到 long 最大值。导入结束后要关闭它并重启，否则 compaction 不会运行。
- `rocksdb.block_cache_capacity=0` 表示彻底关闭块缓存，而不是不限制大小。
- `rocksdb.prefix_extractor_n_bytes` 大于 0 时会安装一个该长度的 capped prefix extractor。
- 所有列族都使用 `uint64add` merge 操作符，计数器表依赖它。
- 数据库不存在时会自动创建，`avoid_unnecessary_blocking_io` 和 `write_dbid_to_manifest` 始终开启。

### 内存说明

RocksDB 的缓存和 write buffer 都是本地内存分配，不属于 `bin/hugegraph-server.sh` 中设置的 JVM 堆。
`GET /metrics/backend` 接口会返回存储的使用量：内存数值是所有已打开列族的块缓存用量、固定在块缓存中的
用量、预估的 table reader 内存（索引块和过滤块）以及全部 memtable 大小之和，取自 RocksDB 的属性。

有两个配置项的实际占用会随列族数量成倍增长：

- `rocksdb.block_cache_capacity` 为每个列族创建一个缓存实例，因此一台服务的块缓存总量大致等于该值乘以
  所有图的 `m`、`g`、`s` 三个 store 中已打开表的数量，再加上 `rocksdb.data_disks` 额外打开的实例。
- `rocksdb.write_buffer_size` 乘以 `rocksdb.max_write_buffer_number` 限定的是单个列族的 memtable 内存。
  `rocksdb.db_write_buffer_size` 限制一个 store 内所有列族的总量，默认值 0 表示没有这个限制。

`rocksdb.row_cache_capacity` 不同：它是每个 store 一个缓存，0 表示关闭。

### 导入 SST 文件

设置 `rocksdb.sst_path` 即开启导入。打开 store 时以及每次创建表时，服务会遍历
`<sst_path>/<column family>/` 目录，收集其中所有非空的 `*.sst` 文件，导入到对应的列族。导入采用移动
文件的方式而不是复制，因此源目录会被导入过程消耗掉。

### raft 模式

RocksDB 后端仍然可以运行在 raft 状态机之后：`raft.mode=true` 时，本地后端的存储实现会被 raft 实现包装。
包装层会拒绝共享存储的后端，因此 `rocksdb` 可用而 `hbase` 不可用。raft 模式下 RocksDB 会话写入时关闭
WAL 且不做 sync，因为状态机可以通过快照加 raft 日志恢复，而该后端支持快照。

使用时需要注意：

- `bin/init-store.sh` 在初始化后端时会强制把 `raft.mode` 置为 false，因此初始化过程不会走 raft。
- 发布包中的 `conf/graphs/hugegraph.properties` 已把 raft 相关配置标记为废弃。1.7.0 及之后版本的分布式
  部署改用 `hstore` 后端，配合 PD 与 Store。
- raft 成员管理接口位于 `graphspaces/{graphspace}/graphs/{graph}/raft/` 之下，包括 `list_peers`、
  `get_leader`、`set_leader`、`transfer_leader`、`add_peer` 和 `remove_peer`。`bin/raft-tools.sh` 封装了
  同样的操作，但它拼接的 URL 中仍然没有 graphspace 段，在 1.7.0 的服务上需要调整路径才能使用。
- 其余 `raft.*` 配置项见 [Server 配置选项](config-option)。

### 后端能力

该后端的特性开关决定了哪些操作可以下推给存储：

- 支持按键前缀扫描、按键范围扫描、分页查询、范围条件和 order-by。
- RocksDB 内部没有索引，因此按名字查询 schema、按标签查询以及按标签删除边由服务端完成，而不是由存储
  完成。
- 通过 RocksDB 的 write batch 支持事务。
- 支持快照，raft 模式和备份依赖该能力。
- 不支持共享存储，一个数据目录属于一台服务。
- 支持 olap 属性，对应的表会作为额外的列族创建。
- 存储本身不会让数据过期，因此服务端在读取时过滤掉 TTL 已到期的元素。
- 存储层不支持 `in`、`contains`、`contains_key` 条件，不支持聚合属性，也不支持原地更新顶点或边的属性。

### riscv64 平台说明

在 Linux riscv64 上，RocksDB 的 JNI 库需要 `libatomic.so.1`。`bin/util.sh` 会查找该库并在
`bin/hugegraph-server.sh`、`bin/init-store.sh` 和 `bin/dump-store.sh` 启动 JVM 之前把它加入
`LD_PRELOAD`。如果找不到，这些脚本会以
`RISC-V RocksDB requires libatomic.so.1; install libatomic1` 退出，安装 `libatomic1` 包即可解决。
