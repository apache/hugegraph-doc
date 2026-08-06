---
title: "HugeGraph 0.2.4 Release Notes"
linkTitle: "Release-0.2.4"
draft: true
weight: 31
---

### API & Java Client

#### 功能更新
### 元数据（Schema）相关
 
#### BUG修复
- Vertex Label为非primary-key id策略应该允许属性为空（HugeGraph-651）
- Gremlin-Server 序列化的 EdgeLabel 仅有一个directed 属性，应该打印完整的schema描述（HugeGraph-680）
- 创建IndexLabel时使用不存在的属性抛出空指针异常，应该抛非法参数异常（HugeGraph-682）
- 创建schema如果已经存在并指定了ifNotExist时，结果应该返回原来的对象（HugeGraph-694）
- 由于EdgeLabel的Frequency默认为null以及不允许修改特性，导致Append操作传递null值在API层反序列化失败（HugeGraph-729）
- 增加对schema名称的正则检查配置项，默认不允许为全空白字符（HugeGraph-727）
- 中文名的schema在前端显示为乱码（HugeGraph-711）

### 图数据（Vertex、Edge）相关

#### 功能更新
- DataType支持Array，并且List类型除了一个一个添加object，也需要支持直接赋值List对象（HugeGraph-719）
- 自动生成的顶点id由十进制改为十六进制（字符串存储时）（HugeGraph-785）
 
#### BUG修复
- HugeGraph-API的VertexLabel/EdgeLabel API未提供eliminate接口（HugeGraph-614）
- 增加非primary-key id策略的顶点时，如果属性为空无法插入到数据库中（HugeGraph-652）
- 使用HugeGraph-Client的gremlin发送无返回值groovy请求时，由于gremlin-server将无返回值序列化为null，导致前端迭代结果集时出现空指针异常（HugeGraph-664） 
- RESTful API在没有找到对应id的vertex/edge时返回500（HugeGraph-734）
- HugeElement/HugeProperty的equals()与tinkerpop不兼容（HugeGraph-653）
- HugeEdgeProperty的property的equals函数与tinkerpop兼容 （HugeGraph-740）
- HugeElement/HugeVertexProperty的hashcode函数与tinkerpop不兼容（HugeGraph-728）
- HugeVertex/HugeEdge的toString函数与tinkerpop不兼容（HugeGraph-665）
- 与tinkerpop的异常不兼容，包括IllegalArgumentsException和UnsupportedOperationException（HugeGraph-667）
- 通过id无法找到element时，抛出的异常类型与tinkerpop不兼容（HugeGraph-689）
- vertex.addEdge没有检查properties的数目是否为2的倍数（HugeGraph-716）
- vertex.addEdge()时，assignId调用时机太晚，导致vertex的Set<Edge>中有重复的edge（HugeGraph-666）
- 查询时包含大于等于三层逻辑嵌套时，会抛出ClassCastException，现改成抛出非法参数异常（HugeGraph-481）
- 边查询如果同时包含source-vertex/direction和property作为条件，查询结果错误（HugeGraph-749）
- HugeGraph-Server 在运行时如果 cassandra 宕掉，插入或查询操作时会抛出DataStax的异常以及详细的调用栈（HugeGraph-771）
- 删除不存在的 indexLabel 时会抛出异常，而删除其他三种元数据（不存在的）则不会（HugeGraph-782）
- 当传给EdgeApi的源顶点或目标顶点的id非法时，会因为查询不到该顶点向客户端返回404状态码（HugeGraph-784）
- 提供内部使用获取元数据的接口，使SchemaManager仅为外部使用，当获取不存在的schema时抛出NotFoundException异常（HugeGraph-743）
- HugeGraph-Client 创建／添加／移除 元数据都应该返回来自服务端的结果（HugeGraph-760）
- 创建HugeGraph-Client时如果输入了错误的主机会导致进程阻塞，无法响应（HugeGraph-718） 
 
### 查询、索引、缓存相关

#### 功能更新
- 缓存更新更加高效的锁方案（HugeGraph-555）
- 索引查询增加支持只有一个元素的IN语句（原来仅支持EQ）（HugeGraph-739）

#### BUG修复
- 防止请求数据量过大时服务本身hang住（HugeGraph-777）

### 其它

#### 功能更新
- 使Init-Store仅用于初始化数据库，清空后端由独立脚本实现（HugeGraph-650）
 
#### BUG修复
- 单元测试跑完后在测试机上遗留了临时的keyspace（HugeGraph-611）
- Cassandra的info日志信息过多，将大部分修改为debug级别（HugeGraph-722）
- EventHub.containsListener(String event)判断逻辑有遗漏（HugeGraph-732）
- EventHub.listeners/unlisten(String event)当没有对应event的listener时会抛空指针异常（HugeGraph-733）

 
### 测试
#### Tinkerpop合规测试
- 增加自定义ignore机制，规避掉暂时不需要加入持续集成的测试用例（HugeGraph-647）
- 为TestGraph注册GraphSon和Kryo序列化器，实现 IdGenerator$StringId 的 graphson-v1、graphson-v2 和 Kryo的序列化与反序列化（HugeGraph-660）
- 增加了可配置的测试用例过滤器，使得tinkerpop测试可以用在开发分支和发布分支的回归测试中
- 将tinkerpop测试通过配置文件，加入到回归测试中
 
#### 单元测试
- 增加Cache及Event的单元测试（HugeGraph-659）
- HugeGraph-Client 增加API的测试（99个）
- HugeGraph-Client 增加单元测试，包括RestResult反序列化的单测（12个）
 
### 内部修改
 
- 改进LOG变量方面代码（HugeGraph-623/HugeGraph-631）
- License格式调整（HugeGraph-625）
- 将序列化器中持有的graph抽离，要用到graph的函数通过传参数实现 （HugeGraph-750）
