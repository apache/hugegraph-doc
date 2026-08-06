---
title: "HugeGraph 0.3.3 Release Notes"
linkTitle: "Release-0.3.3"
draft: true
weight: 29
---

### API & Java Client

#### 功能更新
- 为vertex-label和edge-label增加可空属性集合，允许在create和append时指定（HugeGraph-245）
- 配合core的功能为用户提供tinkerpop variables RESTful API（HugeGraph-396）
- 支持顶点／边属性的更新和删除（HugeGraph-894）
- 支持顶点／边的条件查询（HugeGraph-919）
 
#### BUG修复
- HugeGraph-API接收的RequestBody为null或""时抛出空指针异常（HugeGraph-795）
- 为HugeGraph-API添加输入参数检查，避免抛出空指针异常（HugeGraph-796 ～ HugeGraph-798，HugeGraph-802，HugeGraph-808 ～ HugeGraph-814，HugeGraph-817，HugeGraph-823，HugeGraph-860）
- 创建缺失outV-label 或者 inV-label的实体边，依然能够被创建成功，不符合需求（HugeGraph-835）
- 创建vertex-label和edge-label时可以任意传入index-names（HugeGraph-837）
- 创建index，base-type=“VERTEX”等值（期望VL、EL），返回500（HugeGraph-846）
- 创建index，base-type和base-value不匹配，提示不友好（HugeGraph-848）
- 删除已经不存在的两个实体之间的关系，schema返回204，顶点和边类型的则返回404（期望统一为404）（HugeGraph-853，HugeGraph-854）
- 给vertex-label追加属性，缺失id-strategy，返回信息有误（HugeGraph-861）
- 给edge-label追加属性，name缺失，提示信息有误（HugeGraph-862）
- 给edge-label追加属性，source-label为“null”，提示信息有误（HugeGraph-863）
- 查询时的StringId如果为空字符串应该抛出异常（HugeGraph-868）
- 通Rest API创建两个顶点之间的边，在studio中通过g.V()则刚新创建的边则不显示，g.E()则能够显示新创建的边（HugeGraph-869）
- HugeGraph-Server的内部错误500，不应该将stack trace返回给Client（HugeGraph-879）
- addEdge传入空的id字符串时会抛出非法参数异常（HugeGraph-885）
- HugeGraph-Client 的 Gremlin 查询结果在解析 Path 时，如果不包含Vertex／Edge会反序列化异常（HugeGraph-891）
- 枚举HugeKeys的字符串变成小写字母加下划线，导致API序列化时字段名与类中变量名不一致，进而序列化失败（HugeGraph-896）
- 增加边到不存在的顶点时返回404（期望400）（HugeGraph-922）

### Core

#### 功能更新
- 支持对顶点/边属性（包括索引列）的更新操作（HugeGraph-369）
- 索引field为空或者空字符串的支持（hugegraph-553和hugegraph-288）
- vertex/edge的属性一致性保证推迟到实际要访问属性时（hugegraph-763）
- 增加ScyllaDB后端驱动（HugeGraph-772）
- 支持tinkerpop的hasKey、hasValue查询（HugeGraph-826）
- 支持tinkerpop的variables功能(HugeGraph-396)
- 以“~”为开头的为系统隐藏属性，用户不可以创建(HugeGraph-842)
- 增加Backend Features以兼容不同后端的特性(HugeGraph-844)
- 对mutation的update可能出现的操作不直接抛错，进行细化处理（HugeGraph-887）
- 对append到vertex-label/edge-label的property检查，必须是nullable的（HugeGraph-890）
- 对于按照id查询，当有的id不存在时，返回其余存在的对象，而非直接抛异常（HugeGraph-900）
 
#### BUG修复
- Vertex.edges(Direction.BOTH,...) assert error（HugeGraph-661）
- 无法支持在addVertex函数中对同一property（single）多次赋值（HugeGraph-662）
- 更新属性时不涉及更新的索引列会丢失（HugeGraph-801）
- GraphTransaction中的ConditionQuery需要索引查询时，没有触发commit，导致查询失败（HugeGraph-805）
- Cassandra不支持query offset，查询时limit=offset+limit取回所有记录后过滤（HugeGraph-851）
- 多个插入操作加上一个删除操作，插入操作会覆盖删除操作（HugeGraph-857）
- 查询时的StringId如果为空字符串应该抛出异常（HugeGraph-868）
- 元数据schema方法只返回 hidden 信息（HugeGraph-912） 

### 测试

- tinkerpop的structure和process测试使用不同的keyspace（HugeGraph-763）
- 将tinkerpop测试和unit测试添加到流水线release-after-merge中（HugeGraph-763）
- jenkins脚本分离各阶段子脚本，修改项目中的子脚本即可生效构建（HugeGraph-800）
- 增加clear backends功能，在tinkerpop suite运行完成后清除后端（HugeGraph-852）
- 增加BackendMutation的测试（HugeGraph-801）
- 多线程操作图时可能抛出NoHostAvailableException异常（HugeGraph-883）
 
### 内部修改
- 调整HugeGraphServer和HugeGremlinServer启动时JVM的堆内存初始为256M，最大为2048M（HugeGraph-218）
- 创建Cassandra Table时，使用schemaBuilder代替字符串拼接（hugegraph-773）
- 运行测试用例时如果初始化图失败（比如数据库连接不上），clear()报错（HugeGraph-910）
- Example抛异常 Need to specify a readable config file rather than...（HugeGraph-921）
- HugeGraphServer和HugeGreminServer的缓存保持同步（HugeGraph-569）
