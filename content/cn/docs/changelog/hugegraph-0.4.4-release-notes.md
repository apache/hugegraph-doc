---
title: "HugeGraph 0.4.4 Release Notes"
linkTitle: "Release-0.4.4"
draft: true
weight: 27
---

### API & Java Client

#### 功能更新
- HugeGraph-Server支持WebSocket，能用Gremlin-Console连接使用；并支持直接编写groovy脚本调用Core的代码（HugeGraph-977）
- 适配Schema-id（HugeGraph-1038）
 
#### BUG修复
- hugegraph-0.3.3：删除vertex的属性，body中properties=null，返回500，空指针（HugeGraph-950）
- hugegraph-0.3.3： graph.schema().getVertexLabel()  空指针（HugeGraph-955）
- HugeGraph-Client 中顶点和边的属性集合不是线程安全的（HugeGraph-1013）
- 批量操作的异常信息无法打印（HugeGraph-1013）
- 异常message提示可读性太差，都是用propertyKey的id显示，对于用户来说无法立即识别（HugeGraph-1055） 
- 批量新增vertex实体，有一个body体为null，返回500，空指针（HugeGraph-1056）
- 追加属性body体中只包含properties，功能出现回退，抛出异常The label of vertex can't be null（HugeGraph-1057）
- HugeGraph-Client适配：PropertyKey的DateType中Timestamp替换成Date（HugeGraph-1059）
- 创建IndexLabel时baseValue为空会报出500错误（HugeGraph-1061）
 
### Core

#### 功能更新
- 实现上层独立事务管理，并兼容tinkerpop事务规范（HugeGraph-918、HugeGraph-941）
- 完善memory backend，可以通过API正确访问，且适配了tinkerpop事务（HugeGraph-41）
- 增加RocksDB后端存储驱动框架（HugeGraph-929）
- RocksDB数字索引range-query实现（HugeGraph-963）
- 为所有的schema增加了id，并将各表原依赖name的列也换成id（HugeGraph-589）
- 填充query key-value条件时，value的类型如果不匹配key定义的类型时需要转换为该类型（HugeGraph-964）
- 统一各后端的offset、limit实现（HugeGraph-995）
- 查询顶点、边时，Core支持迭代方式返回结果，而非一次性载入内存（HugeGraph-203）
- memory backend支持range query（HugeGraph-967）
- memory backend的secondary的支持方式从遍历改为IdQuery（HugeGraph-996）
- 联合索引支持复杂的（只要逻辑上可以查都支持）多种索引组合查询（HugeGraph-903）
- Schema中增加存储用户数据的域（map）（HugeGraph-902）
- 统一ID的解析及系列化（包括API及Backend）（HugeGraph-965）
- RocksDB没有keyspace概念，需要完善对多图实例的支持（HugeGraph-973）
- 支持Cassandra设置连接用户名密码（HugeGraph-999）
- Schema缓存支持缓存所有元数据（get-all-schema）（HugeGraph-1037）
- 目前依然保持schema对外暴露name，暂不直接使用schema id（HugeGraph-1032）
- 用户传入ID的策略的修改为支持String和Number（HugeGraph-956）
 
#### BUG修复
- 删除旧的前缀indexLabel时数据库中的schemaLabel对象还有残留（HugeGraph-969）
- HugeConfig解析时共用了公共的Option，导致不同graph的配置项有覆盖（HugeGraph-984）
- 数据库数据不兼容时，提示更加友好的异常信息（HugeGraph-998）
- 支持Cassandra设置连接用户名密码（HugeGraph-999）
- RocksDB deleteRange end溢出后触发RocksDB assert错误（HugeGraph-971）
- 允许根据null值id进行查询顶点/边，返回结果为空集合（HugeGraph-1045）
- 内存中存在部分更新数据未提交时，搜索结果不对（HugeGraph-1046）
- g.V().hasLabel(XX)传入不存在的label时报错： Internal Server Error and Undefined property key: '~label'（HugeGraph-1048）
- gremlin获取的的schema只剩下名称字符串（HugeGraph-1049）
- 大量数据情况下无法进行count操作（HugeGraph-1051）
- RocksDB持续插入6~8千万条边时卡住（HugeGraph-1053）
- 整理属性类型的支持，并在BinarySerializer中使用二进制格式系列化属性值（HugeGraph-1062）
 
### 测试
- 增加tinkerpop的performance测试（HugeGraph-987）
 
### 内部修改
- HugeFactory打开同一个图（name相同者）时，共用HugeGraph对象即可（HugeGraph-983）
- 规范索引类型命名secondary、range、search（HugeGraph-991）
- 数据库数据不兼容时，提示更加友好的异常信息（HugeGraph-998）
- IO部分的 gryo 和 graphson 的module分开（HugeGraph-1041）
- 增加query性能测试到PerfExample中（HugeGraph-1044）
- 关闭gremlin-server的metric日志（HugeGraph-1050）
