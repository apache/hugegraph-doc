---
title: "HugeGraph 0.11 Release Notes"
linkTitle: "Release-0.11.2"
draft: true
weight: 13
---

### API & Client

#### 功能更新

- 支持梭形相似度算法（hugegraph #671，hugegraph-client #62）
- 支持创建 Schema 时，记录创建的时间（hugegraph #746，hugegraph-client #69）
- 支持 RESTful API 中基于属性的范围查询顶点/边（hugegraph #782，hugegraph-client #73）
- 支持顶点和边的 TTL （hugegraph #794，hugegraph-client #83）
- 统一 RESTful API Server 和 Gremlin Server 的日期格式为字符串（hugegraph #1014，hugegraph-client #82）
- 支持共同邻居，Jaccard 相似度，全部最短路径，带权最短路径和单源最短路径5种遍历算法（hugegraph #936，hugegraph-client #80）
- 支持用户认证和细粒度权限控制（hugegraph #749，hugegraph #985，hugegraph-client #81）
- 支持遍历 API 的顶点计数功能（hugegraph #995，hugegraph-client #84）
- 支持 HTTPS 协议（hugegrap #1036，hugegraph-client #85）
- 支持创建索引时控制是否重建索引（hugegraph #1106，hugegraph-client #91）
- 支持定制的 kout/kneighbor，多点最短路径，最相似 Jaccard 点和模板路径5种遍历算法（hugegraph #1174，hugegraph-client #100，hugegraph-client #106）

#### 内部修改

- 启动 HugeGraphServer 出现异常时快速失败（hugegraph #748）
- 定义 LOADING 模式来加速导入（hugegraph-client #101）

### Core

#### 功能更新

- 支持多属性顶点/边的分页查询（hugegraph #759）
- 支持聚合运算的性能优化（hugegraph #813）
- 支持堆外缓存（hugegraph #846）
- 支持属性权限管理（hugegraph #971）
- 支持 MySQL 和 Memory 后端分片，并改进 HBase 分片方法（hugegraph #974）
- 支持基于 Raft 的分布式一致性协议（hugegraph #1020）
- 支持元数据拷贝功能（hugegraph #1024）
- 支持集群的异步任务调度功能（hugegraph #1030）
- 支持发生 OOM 时打印堆信息功能（hugegraph #1093）
- 支持 Raft 状态机更新缓存（hugegraph #1119）
- 支持 Raft 节点管理功能（hugegraph #1137）
- 支持限制查询请求速率的功能（hugegraph #1158）
- 支持顶点/边的属性默认值功能（hugegraph #1182）
- 支持插件化查询加速机制 RamTable（hugegraph #1183）
- 支持索引重建失败时设置为 INVALID 状态（hugegraph #1226）
- 支持 HBase 启用 Kerberos 认证（hugegraph #1234）

#### BUG修复

- 修复配置权限时 start-hugegraph.sh 的超时问题（hugegraph #761）
- 修复在 studio 执行 gremlin 时的 MySQL 连接失败问题（hugegraph #765）
- 修复 HBase 后端 truncate 时出现的 TableNotFoundException（hugegraph #771）
- 修复限速配置项值未检查的问题（hugegraph #773）
- 修复唯一索引（Unique Index）的返回的异常信息不准确问题（hugegraph #797）
- 修复 RocksDB 后端执行 g.V().hasLabel().count() 时 OOM 问题 （hugegraph-798）
- 修复 traverseByLabel() 分页设置错误问题（hugegraph #805）
- 修复根据 ID 和 SortKeys 更新边属性时误创建边的问题（hugegraph #819）
- 修复部分存储后端的覆盖写问题（hugegraph #820）
- 修复保存执行失败的异步任务时无法取消的问题（hugegraph #827）
- 修复 MySQL 后端在 SSL 模式下无法打开数据库的问题（hugegraph #842）
- 修复索引查询时 offset 无效问题（hugegraph #866）
- 修复 Gremlin 中绝对路径泄露的安全问题（hugegraph #871）
- 修复 reconnectIfNeeded() 方法的 NPE 问题（hugegraph #874）
- 修复 PostgreSQL 的 JDBC_URL 配置没有"/"前缀的问题（hugegraph #891）
- 修复 RocksDB 内存统计问题（hugegraph #937）
- 修复环路检测的两点成环无法检测的问题（hugegraph #939）
- 修复梭形算法计算结束后没有清理计数的问题（hugegraph #947）
- 修复 gremlin-console 无法工作的问题（hugegraph #1027）
- 修复限制数目的按条件过滤邻接边问题（hugegraph #1057）
- 修复 MySQL 执行 SQL 时的 auto-commit 问题（hugegraph #1064）
- 修复通过两个索引查询时发生超时 80w 限制的问题（hugegraph #1088）
- 修复范围索引检查规则错误（hugegraph #1090）
- 修复删除残留索引的错误（hugegraph #1101）
- 修复当前线程为 task-worker 时关闭事务卡住的问题（hugegraph #1111）
- 修复最短路径查询出现 NoSuchElementException 的问题（hugegraph #1116）
- 修复异步任务有时提交两次的问题（hugegraph #1130）
- 修复值很小的 date 反序列化的问题（hugegraph #1152）
- 修复遍历算法未检查起点或者终点是否存在的问题（hugegraph #1156）
- 修复 bin/start-hugegraph.sh 参数解析错误的问题（hugegraph #1178）
- 修复 gremlin-console 运行时的 log4j 错误信息的问题（hugegraph #1229）

#### 内部修改

- 延迟检查非空属性（hugegraph #756）
- 为存储后端增加查看集群节点信息的功能 （hugegraph #821）
- 为 RocksDB 后端增加 compaction 高级配置项（hugegraph #825）
- 增加 vertex.check_adjacent_vertex_exist 配置项（hugegraph #837）
- 检查主键属性不允许为空（hugegraph #847）
- 增加图名字的合法性检查（hugegraph #854）
- 增加对非预期的 SysProp 的查询（hugegraph #862）
- 使用 disableTableAsync 加速 HBase 后端的数据清除（hugegraph #868）
- 允许 Gremlin 环境触发系统异步任务（hugegraph #892）
- 编码字符类型索引中的类型 ID（hugegraph #894）
- 安全模块允许 Cassandra 在执行 CQL 时按需创建线程（hugegraph #896）
- 将 GremlinServer 的默认通道设置为 WsAndHttpChannelizer（hugegraph #903）
- 将 Direction 和遍历算法的类导出到 Gremlin 环境（hugegraph #904）
- 增加顶点属性缓存限制（hugegraph #941，hugegraph #942）
- 优化列表属性的读（hugegraph #943）
- 增加缓存的 L1 和 L2 配置（hugegraph #945）
- 优化 EdgeId.asString() 方法（hugegraph #946）
- 优化当顶点没有属性时跳过后端存储查询（hugegraph #951）
- 创建名字相同但属性不同的元数据时抛出 ExistedException（hugegraph #1009）
- 查询顶点和边后按需关闭事务（hugegraph #1039）
- 当图关闭时清空缓存（hugegraph #1078）
- 关闭图时加锁避免竞争问题（hugegraph #1104）
- 优化顶点和边的删除效率，当提供 Label+ID 删除时免去查询（hugegraph #1150）
- 使用 IntObjectMap 优化元数据缓存效率（hugegraph #1185）
- 使用单个 Raft 节点管理目前的三个 store（hugegraph #1187）
- 在重建索引时提前释放索引删除的锁（hugegraph #1193）
- 在压缩和解压缩异步任务的结果时，使用 LZ4 替代 Gzip（hugegraph #1198）
- 实现 RocksDB 删除 CF 操作的排他性来避免竞争（hugegraph #1202）
- 修改 CSV reporter 的输出目录，并默认设置为不输出（hugegraph #1233）

#### 其它

- cherry-pick 0.10.4 版本的 bug 修复代码（hugegraph #785，hugegraph #1047）
- Jackson 升级到 2.10.2 版本（hugegraph #859）
- Thanks 信息中增加对 Titan 的感谢（hugegraph #906）
- 适配 TinkerPop 测试（hugegraph #1048）
- 修改允许输出的日志最低等级为 TRACE（hugegraph #1050）
- 增加 IDEA 的格式配置文件（hugegraph #1060）
- 修复 Travis CI 太多错误信息的问题（hugegraph #1098）

### Loader

#### 功能更新

- 支持读取 Hadoop 配置文件（hugegraph-loader #105）
- 支持指定 Date 属性的时区（hugegraph-loader #107）
- 支持从 ORC 压缩文件导入数据（hugegraph-loader #113）
- 支持单条边插入时设置是否检查顶点（hugegraph-loader #117）
- 支持从 Snappy-raw 压缩文件导入数据（hugegraph-loader #119）
- 支持导入映射文件 2.0 版本（hugegraph-loader #121）
- 增加一个将 utf8-bom 转换为 utf8 的命令行工具（hugegraph-loader #128）
- 支持导入任务开始前清理元数据信息的功能（hugegraph-loader #140）
- 支持 id 列作为属性存储（hugegraph-loader #143）
- 支持导入任务配置 username（hugegraph-loader #146）
- 支持从 Parquet 文件导入数据（hugegraph-loader #153）
- 支持指定读取文件的最大行数（hugegraph-loader #159）
- 支持 HTTPS 协议（hugegraph-loader #161）
- 支持时间戳作为日期格式（hugegraph-loader #164）

#### BUG修复

- 修复行的 retainAll() 方法没有修改 names 和 values 数组（hugegraph-loader #110）
- 修复 JSON 文件重新加载时的 NPE 问题（hugegraph-loader #112）

#### 内部修改

- 只打印一次插入错误信息，以避免过多的错误信息（hugegraph-loader #118）
- 拆分批量插入和单条插入的线程（hugegraph-loader #120）
- CSV 的解析器改为 SimpleFlatMapper（hugegraph-loader #124）
- 编码主键中的数字和日期字段（hugegraph-loader #136）
- 确保主键列合法或者存在映射（hugegraph-loader #141）
- 跳过主键属性全部为空的顶点（hugegraph-loader #166）
- 在导入任务开始前设置为 LOADING 模式，并在导入完成后恢复原来模式（hugegraph-loader #169）
- 改进停止导入任务的实现（hugegraph-loader #170）

### Tools

#### 功能更新

- 支持 Memory 后端的备份功能 （hugegraph-tools #53）
- 支持 HTTPS 协议（hugegraph-tools #58）
- 支持 migrate 子命令配置用户名和密码（hugegraph-tools #61）
- 支持备份顶点和边时指定类型和过滤属性信息（hugegraph-tools #63）

#### BUG修复

- 修复 dump 命令的 NPE 问题（hugegraph-tools #49）

#### 内部修改

- 在 backup/dump 之前清除分片文件（hugegraph-tools #53）
- 改进 HugeGraph-tools 的报错信息（hugegraph-tools #67）
- 改进 migrate 子命令，删除掉不支持的子配置（hugegraph-tools #68）
