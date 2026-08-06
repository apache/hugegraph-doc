---
title: "HugeGraph 0.5 Release Notes"
linkTitle: "Release-0.5.6"
draft: true
weight: 25
---

### API & Java Client

#### 功能更新
- VertexLabel与EdgeLabel增加bool参数enable_label_index表述是否构建label索引（HugeGraph-1085）
- 增加RESTful API来支持高效shortest path，K-out和K-neighbor查询（HugeGraph-944）
- 增加RESTful API支持按id列表批量查询顶点（HugeGraph-1153）
- 支持迭代获取全部的顶点和边，使用分页实现（HugeGraph-1166）
- 顶点id中包含 / % 等 URL 保留字符时通过 VertexAPI 查不出来（HugeGraph-1127）
- 批量插入边时是否检查vertex的RESTful API参数从checkVertex改为check_vertex (HugeGraph-81)
 
#### BUG修复
- hasId()无法正确匹配LongId（HugeGraph-1083）

### Core

#### 功能更新
- RocksDB支持常用配置项（HugeGraph-1068）
- 支持插入、删除、更新等操作的限速（HugeGraph-1071）
- 支持RocksDB导入sst文件方案（HugeGraph-1077）
- 增加MySQL后端存储（HugeGraph-1091）
- 增加Palo后端存储（HugeGraph-1092）
- 增加开关：支持是否构建顶点/边的label index（HugeGraph-1085）
- 支持API分页获取数据（HugeGraph-1105）
- RocksDB配置的数据存放目录如果不存在则自动创建（HugeGraph-1135）
- 增加高级遍历函数shortest path、K-neighbor，K-out和按id列表批量查询顶点（HugeGraph-944）
- init-store.sh增加超时重试机制（HugeGraph-1150）
- 将边表拆分两个表：OUT表、IN表（HugeGraph-1002）
- 限制顶点ID最大长度为128字节（HugeGraph-1168）
- Cassandra通过压缩数据（可配置snappy、lz4）进行优化（HugeGraph-428）
- 支持IN和OR操作（HugeGraph-137）
- 支持RocksDB并行写多个磁盘（HugeGraph-1177）
- MySQL通过批量插入进行性能优化（HugeGraph-1188）

#### BUG修复
- Kryo系列化多线程时异常（HugeGraph-1066）
- RocksDB索引内容中重复写了两次elem-id（HugeGraph-1094）
- SnowflakeIdGenerator.instance在多线程环境下可能会初始化多个实例（HugeGraph-1095）
- 如果查询边的顶点但顶点不存在时，异常信息不够明确（HugeGraph-1101）
- RocksDB配置了多个图时，init-store失败（HugeGraph-1151）
- 无法支持 Date 类型的属性值（HugeGraph-1165）
- 创建了系统内部索引，但无法根据其进行搜索（HugeGraph-1167）
- 拆表后根据label删除边时，edge-in表中的记录未被删除成功（HugeGraph-1182）

### 测试
- 增加配置项：vertex.force_id_string，跑 tinkerpop 测试时打开（HugeGraph-1069）

### 内部修改
- common库OptionChecker增加allowValues()函数用于枚举值（HugeGraph-1075）
- 清理无用、版本老旧的依赖包，减少打包的压缩包的大小（HugeGraph-1078）
- HugeConfig通过文件路径构造时，无法检查多次配置的配置项的值（HugeGraph-1079）
- Server启动时可以支持智能分配最大内存（HugeGraph-1154）
- 修复Mac OS因为不支持free命令导致无法启动server的问题（HugeGraph-1154）
- 修改配置项的注册方式为字符串式，避免直接依赖Backend包（HugeGraph-1171）
- 增加StoreDumper工具以查看后端存储的数据内容（HugeGraph-1172）
- Jenkins把所有与内部服务器有关的构建机器信息都参数化传入（HugeGraph-1179）
- 将RestClient移到common模块，令server和client都依赖common（HugeGraph-1183） 
- 增加配置项dump工具ConfDumper（HugeGraph-1193）