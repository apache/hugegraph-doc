# v0.5.6 Stand-alone(RocksDB)

LLMS 索引： [llms.txt](/versions/1.0/cn/llms.txt)

---

### 1 测试环境

被压机器信息

CPU                                          | Memory | 网卡        | 磁盘
-------------------------------------------- | ------ | --------- | ------------------
48 Intel(R) Xeon(R) CPU E5-2650 v4 @ 2.20GHz | 128G   | 10000Mbps | 750GB SSD,2.7T HDD

- 起压力机器信息：与被压机器同配置
- 测试工具：apache-Jmeter-2.5.1

注：起压机器和被压机器在同一机房

### 2 测试说明

#### 2.1 名词定义（时间的单位均为ms）

- Samples -- 本次场景中一共完成了多少个线程
- Average -- 平均响应时间
- Median -- 统计意义上面的响应时间的中值
- 90% Line -- 所有线程中90%的线程的响应时间都小于xx
- Min -- 最小响应时间
- Max -- 最大响应时间
- Error -- 出错率
- Throughput -- 吞吐量
- KB/sec -- 以流量做衡量的吞吐量

#### 2.2 底层存储

后端存储使用RocksDB，HugeGraph与RocksDB都在同一机器上启动，server相关的配置文件除主机和端口有修改外，其余均保持默认。

### 3 性能结果总结

1. HugeGraph单条插入顶点和边的速度在每秒1w左右
2. 顶点和边的批量插入速度远大于单条插入速度
3. 按id查询顶点和边的并发度可达到13000以上，且请求的平均延时小于50ms

### 4 测试结果及分析

#### 4.1 batch插入

##### 4.1.1 压力上限测试

###### 测试方法

不断提升并发量，测试server仍能正常提供服务的压力上限

###### 压力参数

持续时间：5min

###### 顶点的最大插入速度：

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/rocksdb/vertex_batch.png" alt="image">
</center>


####### 结论：

- 并发2200，顶点的吞吐量是2026.8，每秒可处理的数据：2026.8*200=405360/s

###### 边的最大插入速度

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/rocksdb/edge_batch.png" alt="image">
</center>

####### 结论：

- 并发900，边的吞吐量是776.9，每秒可处理的数据：776.9*500=388450/s

#### 4.2 single插入

##### 4.2.1 压力上限测试

###### 测试方法

不断提升并发量，测试server仍能正常提供服务的压力上限

###### 压力参数

- 持续时间：5min
- 服务异常标志：错误率大于0.00%

###### 顶点的单条插入

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/rocksdb/vertex_single.png" alt="image">
</center>


####### 结论：

- 并发11500，吞吐量为10730，顶点的单条插入并发能力为11500

###### 边的单条插入

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/rocksdb/edge_single.png" alt="image">
</center>


####### 结论：

- 并发9000，吞吐量是8418，边的单条插入并发能力为9000

#### 4.3 按id查询

##### 4.3.1 压力上限测试

###### 测试方法

不断提升并发量，测试server仍能正常提供服务的压力上限

###### 压力参数

- 持续时间：5min
- 服务异常标志：错误率大于0.00%

###### 顶点的按id查询

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/rocksdb/vertex_id_query.png" alt="image">
</center>

####### 结论：

- 并发14000，吞吐量是12663，顶点的按id查询的并发能力为14000，平均延时为44ms

###### 边的按id查询

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/rocksdb/edge_id_query.png" alt="image">
</center>


####### 结论：

- 并发13000，吞吐量是12225，边的按id查询的并发能力为13000，平均延时为12ms
