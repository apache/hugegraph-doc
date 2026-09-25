# v0.5.6 Cluster(Cassandra)

LLMS 索引： [llms.txt](/versions/1.0/cn/llms.txt)

---

### 1 测试环境

被压机器信息

CPU                                          | Memory | 网卡      | 磁盘
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

后端存储使用15节点Cassandra集群，HugeGraph与Cassandra集群位于不同的服务器，server相关的配置文件除主机和端口有修改外，其余均保持默认。

### 3 性能结果总结

1. HugeGraph单条插入顶点和边的速度分别为9000和4500
2. 顶点和边的批量插入速度分别为5w/s和15w/s，远大于单条插入速度
3. 按id查询顶点和边的并发度可达到12000以上，且请求的平均延时小于70ms

### 4 测试结果及分析

#### 4.1 batch插入

##### 4.1.1 压力上限测试

###### 测试方法

不断提升并发量，测试server仍能正常提供服务的压力上限

###### 压力参数

持续时间：5min

###### 顶点的最大插入速度：

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/cassandra/vertex_batch.png" alt="image">
</center>


####### 结论：

- 并发3500，顶点的吞吐量是261，每秒可处理的数据：261*200=52200/s

###### 边的最大插入速度

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/cassandra/edge_batch.png" alt="image">
</center>


####### 结论：

- 并发1000，边的吞吐量是323，每秒可处理的数据：323*500=161500/s

#### 4.2 single插入

##### 4.2.1 压力上限测试

###### 测试方法

不断提升并发量，测试server仍能正常提供服务的压力上限

###### 压力参数

- 持续时间：5min
- 服务异常标志：错误率大于0.00%

###### 顶点的单条插入

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/cassandra/vertex_single.png" alt="image">
</center>


####### 结论：

- 并发9000，吞吐量为8400，顶点的单条插入并发能力为9000

###### 边的单条插入

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/cassandra/edge_single.png" alt="image">
</center>


####### 结论：

- 并发4500，吞吐量是4160，边的单条插入并发能力为4500

#### 4.3 按id查询

##### 4.3.1 压力上限测试

###### 测试方法

不断提升并发量，测试server仍能正常提供服务的压力上限

###### 压力参数

- 持续时间：5min
- 服务异常标志：错误率大于0.00%

###### 顶点的按id查询

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/cassandra/vertex_id_query.png" alt="image">
</center>


####### 结论：

- 并发14500，吞吐量是13576，顶点的按id查询的并发能力为14500，平均延时为11ms

###### 边的按id查询

<center>
  <img src="/versions/1.0/docs/images/API-perf/v0.5.6/cassandra/edge_id_query.png" alt="image">
</center>

####### 结论：

- 并发12000，吞吐量是10688，边的按id查询的并发能力为12000，平均延时为63ms
