---
title: "HugeGraph 0.12 Release Notes"
linkTitle: "Release-0.12.0"
weight: 11
---

### API & Client

#### 接口更新

- 支持 https + auth 模式连接图服务（hugegraph-client #109  #110）
- 统一 kout/kneighbor 等 OLTP 接口的参数命名及默认值（hugegraph-client #122  #123）
- 支持 RESTful 接口利用 P.textcontains() 进行属性全文检索（hugegraph #1312）
- 增加 graph_read_mode API 接口，以切换 OLTP、OLAP 读模式（hugegraph #1332）
- 支持 list/set 类型的聚合属性 aggregate property（hugegraph #1332）
- 权限接口增加 METRICS 资源类型（hugegraph #1355、hugegraph-client #114）
- 权限接口增加 SCHEMA 资源类型（hugegraph #1362、hugegraph-client #117）
- 增加手动 compact API 接口，支持 rocksdb/cassandra/hbase 后端（hugegraph #1378）
- 权限接口增加 login/logout API，支持颁发或回收 Token（hugegraph #1500、hugegraph-client #125）
- 权限接口增加 project API（hugegraph #1504、hugegraph-client #127）
- 增加 OLAP 回写接口，支持 cassandra/rocksdb 后端（hugegraph #1506、hugegraph-client #129）
- 增加返回一个图的所有 Schema 的 API 接口（hugegraph #1567、hugegraph-client #134）
- 变更 property key 创建与更新 API 的 HTTP 返回码为 202（hugegraph #1584）
- 增强 Text.contains() 支持 3 种格式："word"、"(word)"、"(word1|word2|word3)"（hugegraph #1652）
- 统一了属性中特殊字符的行为（hugegraph #1670 #1684）
- 支持动态创建图实例、克隆图实例、删除图实例（hugegraph-client #135）

#### 其它修改

- 修复在恢复 index label 时 IndexLabelV56 id 丢失的问题（hugegraph-client #118）
- 为 Edge 类增加 name() 方法（hugegraph-client #121）

### Core & Server

#### 功能更新

- 支持动态创建图实例（hugegraph #1065）
- 支持通过 Gremlin 调用 OLTP 算法（hugegraph #1289）
- 支持多集群使用同一个图权限服务，以共享权限信息（hugegraph #1350）
- 支持跨多节点的 Cache 缓存同步（hugegraph #1357）
- 支持 OLTP 算法使用原生集合以降低 GC 压力提升性能（hugegraph #1409）
- 支持对新增的 Raft 节点打快照或恢复快照（hugegraph #1439）
- 支持对集合属性建立二级索引 Secondary Index（hugegraph #1474）
- 支持审计日志，及其压缩、限速等功能（hugegraph #1492 #1493）
- 支持 OLTP 算法使用高性能并行无锁原生集合以提升性能（hugegraph #1552）

#### BUG 修复

- 修复带权最短路径算法（weighted shortest path）NPE 问题（hugegraph #1250）
- 增加 Raft 相关的安全操作白名单（hugegraph #1257）
- 修复 RocksDB 实例未正确关闭的问题（hugegraph #1264）
- 在清空数据 truncate 操作之后，显示的发起写快照 Raft Snapshot（hugegraph #1275）
- 修复 Raft Leader 在收到 Follower 转发请求时未更新缓存的问题（hugegraph #1279）
- 修复带权最短路径算法（weighted shortest path）结果不稳定的问题（hugegraph #1280）
- 修复 rays 算法 limit 参数不生效问题（hugegraph #1284）
- 修复 neighborrank 算法 capacity 参数未检查的问题（hugegraph #1290）
- 修复 PostgreSQL 因为不存在与用户同名的数据库而初始化失败的问题（hugegraph #1293）
- 修复 HBase 后端当启用 Kerberos 时初始化失败的问题（hugegraph #1294）
- 修复 HBase/RocksDB 后端 shard 结束判断错误问题（hugegraph #1306）
- 修复带权最短路径算法（weighted shortest path）未检查目标顶点存在的问题（hugegraph #1307）
- 修复 personalrank/neighborrank 算法中非 String 类型 id  的问题（hugegraph #1310）
- 检查必须是 master 节点才允许调度 gremlin job（hugegraph #1314）
- 修复 g.V().hasLabel().limit(n)  因为索引覆盖导致的部分结果不准确问题（hugegraph #1316）
- 修复 jaccardsimilarity 算法当并集为空时报 NaN 错误的问题（hugegraph #1324）
- 修复 Raft Follower 节点操作 Schema 多节点之间数据不同步问题（hugegraph #1325）
- 修复因为 tx 未关闭导致的 TTL 不生效问题（hugegraph #1330）
- 修复 gremlin job 的执行结果大于 Cassandra 限制但小于任务限制时的异常处理（hugegraph #1334）
- 检查权限接口 auth-delete 和 role-get API 操作时图必须存在（hugegraph #1338）
- 修复异步任务结果中包含 path/tree 时系列化不正常的问题（hugegraph #1351）
- 修复初始化 admin 用户时的 NPE 问题（hugegraph #1360）
- 修复异步任务原子性操作问题，确保 update/get fields 及 re-schedule 的原子性（hugegraph #1361）
- 修复权限 NONE 资源类型的问题（hugegraph #1362）
- 修复启用权限后，truncate 操作报错 SecurityException 及管理员信息丢失问题（hugegraph #1365）
- 修复启用权限后，解析数据忽略了权限异常的问题（hugegraph #1380）
- 修复 AuthManager 在初始化时会尝试连接其它节点的问题（hugegraph #1381）
- 修复特定的 shard 信息导致 base64 解码错误的问题（hugegraph #1383）
- 修复启用权限后，使用 consistent-hash LB 在校验权限时，creator 为空的问题（hugegraph #1385）
- 改进权限中 VAR 资源不再依赖于 VERTEX 资源（hugegraph #1386）
- 规范启用权限后，Schema 操作仅依赖具体的资源（hugegraph #1387）
- 规范启用权限后，部分操作由依赖 STATUS 资源改为依赖 ANY 资源（hugegraph #1391）
- 规范启用权限后，禁止初始化管理员密码为空（hugegraph #1400）
- 检查创建用户时 username/password 不允许为空（hugegraph #1402）
- 修复更新 Label 时，PrimaryKey 或 SortKey 被设置为可空属性的问题（hugegraph #1406）
- 修复 ScyllaDB 丢失分页结果问题（hugegraph #1407）
- 修复带权最短路径算法（weighted shortest path）权重属性强制转换为 double 的问题（hugegraph #1432）
- 统一 OLTP 算法中的 degree 参数命名（hugegraph #1433）
- 修复 fusiformsimilarity 算法当 similars 为空的时候返回所有的顶点问题（hugegraph #1434）
- 改进 paths 算法，当起始点与目标点相同时应该返回空路径（hugegraph #1435）
- 修改 kout/kneighbor 的 limit 参数默认值 10 为 10000000（hugegraph #1436）
- 修复分页信息中的 '+' 被 URL 编码为空格的问题（hugegraph #1437）
- 改进边更新接口的错误提示信息（hugegraph #1443）
- 修复 kout 算法 degree 未在所有 label 范围生效的问题（hugegraph #1459）
- 改进 kneighbor/kout 算法，起始点不允许出现在结果集中（hugegraph #1459 #1463）
- 统一  kout/kneighbor 的 Get 和 Post 版本行为（hugegraph #1470）
- 改进创建边时顶点类型不匹配的错误提示信息（hugegraph #1477）
- 修复 Range Index 的残留索引问题（hugegraph #1498）
- 修复权限操作未失效缓存的问题（hugegraph #1528）
- 修复 sameneighbor 的 limit 参数默认值 10 为 10000000（hugegraph #1530）
- 修复 clear API 不应该所有后端都调用 create snapshot 的问题（hugegraph #1532）
- 修复当 loading 模式时创建 Index Label 阻塞问题（hugegraph #1548）
- 修复增加图到 project 或从 project 移除图的问题（hugegraph #1562）
- 改进权限操作的一些错误提示信息（hugegraph #1563）
- 支持浮点属性设置为 Infinity/NaN 的值（hugegraph #1578)
- 修复 Raft 启用 safe_read 时的 quorum read 问题（hugegraph #1618)
- 修复 token 过期时间配置的单位问题（hugegraph #1625）
- 修复 MySQL Statement 资源泄露问题（hugegraph #1627）
- 修复竞争条件下 Schema.getIndexLabel 获取不到数据的问题（hugegraph #1629）
- 修复 HugeVertex4Insert 无法系列化问题（hugegraph #1630）
- 修复 MySQL count Statement 未关闭问题（hugegraph #1640）
- 修复当删除 Index Label 异常时，导致状态不同步问题（hugegraph #1642）
- 修复 MySQL 执行 gremlin timeout 导致的 statement 未关闭问题（hugegraph #1643）
- 改进 Search Index 以兼容特殊 Unicode 字符：\u0000 to \u0003（hugegraph #1659）
- 修复 #1659 引入的 Char 未转化为 String 的问题（hugegraph #1664）
- 修复 has() + within() 查询时结果异常问题（hugegraph #1680）
- 升级 Log4j 版本到 2.17 以修复安全漏洞（hugegraph #1686 #1698 #1702）
- 修复 HBase 后端 shard scan 中 startkey 包含空串时 NPE 问题（hugegraph #1691）
- 修复 paths 算法在深层环路遍历时性能下降问题（hugegraph #1694）
- 改进 personalrank 算法的参数默认值及错误检查（hugegraph #1695）
- 修复 RESTful 接口 P.within 条件不生效问题（hugegraph #1704）
- 修复启用权限时无法动态创建图的问题（hugegraph #1708）

#### 配置项修改：

- 共享 SSL 相关配置项命名（hugegraph #1260）
- 支持 RocksDB 配置项 rocksdb.level_compaction_dynamic_level_bytes（hugegraph #1262） 
- 去除 RESFful Server 服务协议配置项 restserver.protocol，自动提取 URL 中的 Schema（hugegraph #1272） 
- 增加 PostgreSQL 配置项 jdbc.postgresql.connect_database（hugegraph #1293）
- 增加针对顶点主键是否编码的配置项 vertex.encode_primary_key_number（hugegraph #1323）
- 增加针对聚合查询是否启用索引优化的配置项 query.optimize_aggregate_by_index（hugegraph #1549）
- 修改 cache_type 的默认值 l1 为 l2（hugegraph #1681）
- 增加 JDBC 强制重连配置项 jdbc.forced_auto_reconnect（hugegraph #1710）

#### 其它修改

- 增加默认的 SSL Certificate 文件（hugegraph #1254）
- OLTP 并行请求共享线程池，而非每个请求使用单独的线程池（hugegraph #1258） 
- 修复 Example 的问题（hugegraph #1308）
- 使用 jraft 版本 1.3.5（hugegraph #1313）
- 如果启用了 Raft 模式时，关闭 RocksDB 的 WAL（hugegraph #1318）
- 使用 TarLz4Util 来提升快照 Snapshot 压缩的性能（hugegraph #1336）
- 升级存储的版本号（store version），因为 property key 增加了 read frequency（hugegraph #1341）
- 顶点/边 vertex/edge 的 Get API 使用 queryVertex/queryEdge 方法来替代 iterator 方法（hugegraph #1345）
- 支持 BFS 优化的多度查询（hugegraph #1359)
- 改进 RocksDB deleteRange() 带来的查询性能问题（hugegraph #1375）
- 修复 travis-ci cannot find symbol Namifiable 问题（hugegraph #1376）
- 确保 RocksDB 快照的磁盘与 data path 指定的一致（hugegraph #1392）
- 修复 MacOS 空闲内存 free_memory 计算不准确问题（hugegraph #1396）
- 增加 Raft onBusy 回调来配合限速（hugegraph #1401）
- 升级 netty-all 版本 4.1.13.Final 到 4.1.42.Final（hugegraph #1403）
- 支持 TaskScheduler 暂停当设置为 loading 模式时（hugegraph #1414）
- 修复 raft-tools 脚本的问题（hugegraph #1416）
- 修复 license params 问题（hugegraph #1420）
- 提升写权限日志的性能，通过 batch flush & async write 方式改进（hugegraph #1448）
- 增加 MySQL 连接 URL 的日志记录（hugegraph #1451）
- 提升用户信息校验性能（hugegraph# 1460）
- 修复 TTL 因为起始时间问题导致的错误（hugegraph #1478）
- 支持日志配置的热加载及对审计日志的压缩（hugegraph #1492）
- 支持针对用户级别的审计日志的限速（hugegraph #1493）
- 缓存 RamCache 支持用户自定义的过期时间（hugegraph #1494）
- 在 auth client 端缓存 login role 以避免重复的 RPC 调用（hugegraph #1507）
- 修复 IdSet.contains() 未复写 AbstractCollection.contains() 问题（hugegraph #1511）
- 修复当 commitPartOfEdgeDeletions() 失败时，未回滚 rollback 的问题（hugegraph #1513）
- 提升 Cache metrics 性能（hugegraph #1515）
- 当发生 license 操作错误时，增加打印异常日志（hugegraph #1522）
- 改进 SimilarsMap 实现（hugegraph #1523）
- 使用 tokenless 方式来更新 coverage（hugegraph #1529）
- 改进 project update 接口的代码（hugegraph #1537）
- 允许从 option() 访问 GRAPH_STORE（hugegraph #1546）
- 优化 kout/kneighbor 的 count 查询以避免拷贝集合（hugegraph #1550）
- 优化 shortestpath 遍历方式，以数据量少的一端优先遍历（hugegraph #1569）
- 完善 rocksdb.data_disks 配置项的 allowed keys 提示信息（hugegraph #1585）
- 为 number id 优化 OLTP 遍历中的 id2code 方法性能（hugegraph #1623）
- 优化 HugeElement.getProperties() 返回 Collection\<Property>（hugegraph #1624）
- 增加 APACHE PROPOSAL 文件（hugegraph #1644）
- 改进 close tx 的流程（hugegraph #1655）
- 当 reset() 时为 MySQL close 捕获所有类型异常（hugegraph #1661）
- 改进 OLAP property 模块代码（hugegraph #1675）
- 改进查询模块的执行性能（hugegraph #1711）

### Loader

- 支持导入 Parquet 格式文件（hugegraph-loader #174）
- 支持 HDFS Kerberos 权限验证（hugegraph-loader #176）
- 支持 HTTPS 协议连接到服务端导入数据（hugegraph-loader #183）
- 修复 trust store file 路径问题（hugegraph-loader #186）
- 处理 loading mode 重置的异常（hugegraph-loader #187）
- 增加在插入数据时对非空属性的检查（hugegraph-loader #190）
- 修复客户端与服务端时区不同导致的时间判断问题（hugegraph-loader #192）
- 优化数据解析性能（hugegraph-loader #194）
- 当用户指定了文件头时，检查其必须不为空（hugegraph-loader #195）
- 修复示例程序中 MySQL struct.json 格式问题（hugegraph-loader #198）
- 修复顶点边导入速度不精确的问题（hugegraph-loader #200 #205）
- 当导入启用 check-vertex 时，确保先导入顶点再导入边（hugegraph-loader #206）
- 修复边 Json 数据导入格式不统一时数组溢出的问题（hugegraph-loader #211）
- 修复因边 mapping 文件不存在导致的 NPE 问题（hugegraph-loader #213）
- 修复读取时间可能出现负数的问题（hugegraph-loader #215)
- 改进目录文件的日志打印（hugegraph-loader #223)
- 改进 loader 的的 Schema 处理流程（hugegraph-loader #230)

### Tools

- 支持 HTTPS 协议（hugegraph-tools #71）
- 移除 --protocol 参数，直接从 URL 中自动提取（hugegraph-tools #72）
- 支持将数据 dump 到 HDFS 文件系统（hugegraph-tools #73）
- 修复 trust store file 路径问题（hugegraph-tools #75）
- 支持权限信息的备份恢复（hugegraph-tools #76）
- 支持无参数的 Printer 打印（hugegraph-tools #79）
- 修复 MacOS free_memory 计算问题（hugegraph-tools #82）
- 支持备份恢复时指定线程数 hugegraph-tools #83）
- 支持动态创建图、克隆图、删除图等命令（hugegraph-tools #95)

