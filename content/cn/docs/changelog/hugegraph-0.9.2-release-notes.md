---
title: "HugeGraph 0.9 Release Notes"
linkTitle: "Release-0.9.2"
draft: true
weight: 17
---

### API & Client

#### 功能更新

- 增加 personal rank API 和 neighbor rank API （hugegraph #274）
- Shortest path API 增加 skip_degree 参数跳过超级点（hugegraph #433，hugegraph-client #42）
- vertex/edge 的 scan API 支持分页机制 （hugegraph #428，hugegraph-client #35）
- VertexAPI 使用简化的属性序列化器 （hugegraph #332，hugegraph-client #37）
- 增加 customized paths API 和 customized crosspoints API （hugegraph #306，hugegraph-client #40）
- 在 server 端所有线程忙时返回503错误 （hugegraph #343）
- 保持 API 的 depth 和 degree 参数一致 （hugegraph #252，hugegraph-client #30）

#### BUG修复

- 增加属性的时候验证 Date 而非 Timestamp 的值 （hugegraph-client #26）

#### 内部修改

- RestClient 支持重用连接 （hugegraph-client #33）
- 使用 JsonUtil 替换冗余的 ObjectMapper （hugegraph-client #41）
- Edge 直接引用 Vertex 使得批量插入更友好 （hugegraph-client #29）
- 使用 JaCoCo 替换 Cobertura 统计代码覆盖率 （hugegraph-client #39）
- 改进 Shard 反序列化机制 （hugegraph-client #34）

### Core

#### 功能更新

- 支持 Cassandra 的 NetworkTopologyStrategy （hugegraph #448）
- 元数据删除和索引重建使用分页机制 (hugegraph #417)
- 支持将 HugeGraphServer 作为系统服务 （hugegraph #170)
- 单一索引查询支持分页机制 （hugegraph #328）
- 在初始化图库时支持定制化插件 （hugegraph #364）
- 为HBase后端增加 hbase.zookeeper.znode.parent 配置项 （hugegraph #333）
- 支持异步 Gremlin 任务的进度更新 （hugegraph #325）
- 使用异步任务的方式删除残留索引 （hugegraph #285）
- 支持按 sortKeys 范围查找功能 （hugegraph #271）

#### BUG修复

- 修复二级索引删除时 Cassandra 后端的 batch 超过65535限制的问题 （hugegraph #386）
- 修复 RocksDB 磁盘利用率的 metrics 不正确问题 （hugegraph #326）
- 修复异步索引删除错误修复 （hugegraph #336）
- 修复 BackendSessionPool.close() 的竞争条件问题 （hugegraph #330）
- 修复保留的系统 ID 不工作问题 （hugegraph #315）
- 修复 cache 的 metrics 信息丢失问题 （hugegraph #321）
- 修复使用 hasId() 按 id 查询顶点时不支持数字 id 问题 （hugegraph #302）
- 修复重建索引时的 80w 限制问题和 Cassandra 后端的 batch 65535问题 （hugegraph #292）
- 修复残留索引删除无法处理未展开（none-flatten）查询的问题 （hugegraph #281）

#### 内部修改

- 迭代器变量统一命名为 'iter'（hugegraph #438）
- 增加 PageState.page() 方法统一获取分页信息接口 （hugegraph #429）
- 为基于 mapdb 的内存版后端调整代码结构，增加测试用例 （hugegraph #357）
- 支持代码覆盖率统计 （hugegraph #376）
- 设置 tx capacity 的下限为 COMMIT_BATCH（默认为500） （hugegraph #379）
- 增加 shutdown hook 来自动关闭线程池 （hugegraph #355）
- PerfExample 的统计时间排除环境初始化时间 （hugegraph #329）
- 改进 BinarySerializer 中的 schema 序列化 （hugegraph #316）
- 避免对 primary key 的属性创建多余的索引 （hugegraph #317）
- 限制 Gremlin 异步任务的名字小于256字节 （hugegraph #313）
- 使用 multi-get 优化 HBase 后端的按 id 查询 （hugegraph #279）
- 支持更多的日期数据类型 （hugegraph #274）
- 修改 Cassandra 和 HBase 的 port 范围为（1，65535） （hugegraph #263）

#### 其它

- 增加 travis API 测试 （hugegraph #299）
- 删除 rest-server.properties 中的 GremlinServer 相关的默认配置项 （hugegraph #290）

### Loader

#### 功能更新

- 支持从 HDFS 和 关系型数据库导入数据 （hugegraph-loader #14）
- 支持传递权限 token 参数（hugegraph-loader #46）
- 支持通过 regex 指定要跳过的行 （hugegraph-loader #43）
- 支持导入 TEXT 文件时的 List/Set 属性（hugegraph-loader #38）
- 支持自定义的日期格式 （hugegraph-loader #28）
- 支持从指定目录导入数据 （hugegraph-loader #33）
- 支持忽略最后多余的列或者 null 值的列 （hugegraph-loader #23）

#### BUG修复

- 修复 Example 问题（hugegraph-loader #57）
- 修复当 vertex 是 customized ID 策略时边解析问题（hugegraph-loader #24）

#### 内部修改

- URL regex 改进 （hugegraph-loader #47）

### Tools

#### 功能更新

- 支持海量数据备份和恢复到本地和 HDFS，并支持压缩 （hugegraph-tools #21）
- 支持异步任务取消和清理功能 （hugegraph-tools #20）
- 改进 graph-clear 命令的提示信息 （hugegraph-tools #23）

#### BUG修复

- 修复 restore 命令总是使用 'hugegraph' 作为目标图的问题，支持指定图 （hugegraph-tools #26）