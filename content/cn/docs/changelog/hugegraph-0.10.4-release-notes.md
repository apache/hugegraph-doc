---
title: "HugeGraph 0.10 Release Notes"
linkTitle: "Release-0.10.4"
draft: true
weight: 15
---

### API & Client

#### 功能更新

- 支持 HugeGraphServer 服务端内存紧张时返回错误拒绝请求 （hugegraph #476）
- 支持 API 白名单和 HugeGraphServer GC 频率控制功能 （hugegraph #522）
- 支持 Rings API 的 source_in_ring 参数 （hugegraph #528，hugegraph-client #48）
- 支持批量按策略更新属性接口 （hugegraph #493，hugegraph-client #46）
- 支持 Shard Index 前缀与范围检索索引 （hugegraph #574，hugegraph-client #56）
- 支持顶点的 UUID ID 类型 （hugegraph #618，hugegraph-client #59）
- 支持唯一性约束索引（Unique Index） （hugegraph #636，hugegraph-client #60）
- 支持 API 请求超时功能 （hugegraph #674）
- 支持根据名称列表查询 schema （hugegraph #686，hugegraph-client #63）
- 支持按分页方式获取异步任务 （hugegraph #720）

#### 内部修改

- 保持 traverser 的参数与 server 端一致 （hugegraph-client #44）
- 支持在 Shard 内使用分页方式遍历顶点或者边的方法 （hugegraph-client #47）
- 支持 Gremlin 查询结果持有 GraphManager （hugegraph-client #49）
- 改进 RestClient 的连接参数 （hugegraph-client #52）
- 增加 Date 类型属性的测试 （hugegraph-client #55）
- 适配 HugeGremlinException 异常 （hugegraph-client #57）
- 增加新功能的版本匹配检查 （hugegraph-client #66）
- 适配 UUID 的序列化 （hugegraph-client #67）

### Core

#### 功能更新

- 支持 PostgreSQL 和 CockroachDB 存储后端 （hugegraph #484）
- 支持负数索引 （hugegraph #513）
- 支持边的 Vertex + SortKeys 的前缀范围查询 （hugegraph #574）
- 支持顶点的邻接边按分页方式查询 （hugegraph #659）
- 禁止通过 Gremlin 进行敏感操作 （hugegraph #176）
- 支持 Lic 校验功能 （hugegraph #645）
- 支持 Search Index 查询结果按匹配度排序的功能 （hugegraph #653）
- 升级 tinkerpop 至版本 3.4.3 （hugegraph #648）

#### BUG修复

- 修复按分页方式查询边时剩余数目（remaining count）错误 （hugegraph #515）
- 修复清空后端时边缓存未清空的问题 （hugegraph #488）
- 修复无法插入 List<Date> 类型的属性问题 （hugegraph #534）
- 修复 PostgreSQL 后端的 existDatabase(), clearBackend() 和 rollback()功能 （hugegraph #531）
- 修复程序关闭时 HugeGraphServer 和 GremlinServer 残留问题 （hugegraph #554）
- 修复在 LockTable 中重复抓锁的问题 （hugegraph #566）
- 修复从 Edge 中获取的 Vertex 没有属性的问题 （hugegraph #604）
- 修复交叉关闭 RocksDB 的连接池问题 （hugegraph #598）
- 修复在超级点查询时 limit 失效问题 （hugegraph #607）
- 修复使用 Equal 条件和分页的情况下查询 Range Index 只返回第一页的问题 （hugegraph #614）
- 修复查询 limit 在删除部分数据后失效的问题 （hugegraph #610）
- 修复 Example1 的查询错误 （hugegraph #638）
- 修复 HBase 的批量提交部分错误问题 （hugegraph #634）
- 修复索引搜索时 compareNumber() 方法的空指针问题 （hugegraph #629）
- 修复更新属性值为已经删除的顶点或边的属性时失败问题 （hugegraph #679）
- 修复 system 类型残留索引无法清除问题 （hugegraph #675）
- 修复 HBase 在 Metrics 信息中的单位问题 （hugegraph #713）
- 修复存储后端未初始化问题 （hugegraph #708）
- 修复按 Label 删除边时导致的 IN 边残留问题 （hugegraph #727）
- 修复 init-store 会生成多份 backend_info 问题 （hugegraph #723）

#### 内部修改

- 抑制因 PostgreSQL 后端 database 不存在时的报警信息 （hugegraph #527）
- 删除 PostgreSQL 后端的无用配置项 （hugegraph #533）
- 改进错误信息中的 HugeType 为易读字符串 （hugegraph #546）
- 增加 jdbc.storage_engine 配置项指定存储引擎 （hugegraph #555）
- 增加使用后端链接时按需重连功能 （hugegraph #562）
- 避免打印空的查询条件 （hugegraph #583）
- 缩减 Variable 的字符串长度 （hugegraph #581）
- 增加 RocksDB 后端的 cache 配置项 （hugegraph #567）
- 改进异步任务的异常信息 （hugegraph #596）
- 将 Range Index 拆分成 INT，LONG，FLOAT，DOUBLE 四个表存储 （hugegraph #574）
- 改进顶点和边 API 的 Metrics 名字 （hugegraph #631）
- 增加 G1GC 和 GC Log 的配置项 （hugegraph #616）
- 拆分顶点和边的 Label Index 表 （hugegraph #635）
- 减少顶点和边的属性存储空间 （hugegraph #650）
- 支持对 Secondary Index 和 Primary Key 中的数字进行编码 （hugegraph #676）
- 减少顶点和边的 ID 存储空间 （hugegraph #661）
- 支持 Cassandra 后端存储的二进制序列化存储 （hugegraph #680）
- 放松对最小内存的限制 （hugegraph #689）
- 修复 RocksDB 后端批量写时的 Invalid column family 问题 （hugegraph #701）
- 更新异步任务状态时删除残留索引 （hugegraph #719）
- 删除 ScyllaDB 的 Label Index 表 （hugegraph #717）
- 启动时使用多线程方式打开 RocksDB 后端存储多个数据目录 （hugegraph #721）
- RocksDB 版本从 v5.17.2 升级至 v6.3.6 （hugegraph #722）

#### 其它

- 增加 API tests 到 codecov 统计中 （hugegraph #711）
- 改进配置文件的默认配置项 （hugegraph #575）
- 改进 README 中的致谢信息 （hugegraph #548）

### Loader

#### 功能更新

- 支持 JSON 数据源的 selected 字段 （hugegraph-loader #62）
- 支持定制化 List 元素之间的分隔符 （hugegraph-loader #66）
- 支持值映射 （hugegraph-loader #67）
- 支持通过文件后缀过滤文件 （hugegraph-loader #82）
- 支持对导入进度进行记录和断点续传 （hugegraph-loader #70，hugegraph-loader #87）
- 支持从不同的关系型数据库中读取 Header 信息 （hugegraph-loader #79）
- 支持属性为 Unsigned Long 类型值 （hugegraph-loader #91）
- 支持顶点的 UUID ID 类型 （hugegraph-loader #98）
- 支持按照策略批量更新属性 （hugegraph-loader #97）

#### BUG修复

- 修复 nullable key 在 mapping field 不工作的问题 （hugegraph-loader #64）
- 修复 Parse Exception 无法捕获的问题 （hugegraph-loader #74）
- 修复在等待异步任务完成时获取信号量数目错误的问题 （hugegraph-loader #86）
- 修复空表时 hasNext() 返回 true 的问题 （hugegraph-loader #90）
- 修复布尔值解析错误问题 （hugegraph-loader #92）

#### 内部修改

- 增加 HTTP 连接参数 （hugegraph-loader #81）
- 改进导入完成的总结信息 （hugegraph-loader #80）
- 改进一行数据缺少列或者有多余列的处理逻辑 （hugegraph-loader #93）

### Tools

#### 功能更新

- 支持 0.8 版本 server 备份的数据恢复至 0.9 版本的 server 中 （hugegraph-tools #34）
- 增加 timeout 全局参数 （hugegraph-tools #44）
- 增加 migrate 子命令支持迁移图 （hugegraph-tools #45）

#### BUG修复

- 修复 dump 命令不支持 split size 参数的问题 （hugegraph-tools #32）

#### 内部修改

- 删除 Hadoop 对 Jersey 1.19的依赖 （hugegraph-tools #31）
- 优化子命令在 help 信息中的排序 （hugegraph-tools #37）
- 使用 log4j2 清除 log4j 的警告信息 （hugegraph-tools #39）