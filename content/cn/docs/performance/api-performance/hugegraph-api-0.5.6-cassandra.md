---
title: "v0.5.6 Cluster(Cassandra)"
linkTitle: "v0.5.6 Cluster(Cassandra)"
weight: 2
---

> **Note:** 
> 
> 当前的性能指标测试基于很早期的版本。**最新版本**在性能和功能上都有显著的改进。我们鼓励您参考最新的发布版本，
> 该版本具有**自主分布式存储**和**增强的计算推下能力**。或者，您可以等待社区更新相关测试数据 (也欢迎反馈共建)。

### 1 测试环境

被压机器信息

| CPU                                          | Memory | 网卡        | 磁盘                 |
|----------------------------------------------|--------|-----------|--------------------|
| 48 Intel(R) Xeon(R) CPU E5-2650 v4 @ 2.20GHz | 128G   | 10000Mbps | 750GB SSD,2.7T HDD |

- 起压力机器信息：与被压机器同配置
- 测试工具：apache-Jmeter-2.5.1

注：起压机器和被压机器在同一机房

### 2 测试说明

#### 2.1 名词定义（时间的单位均为 ms）

- Samples -- 本次场景中一共完成了多少个线程
- Average -- 平均响应时间
- Median -- 统计意义上面的响应时间的中值
- 90% Line -- 所有线程中 90% 的线程的响应时间都小于 xx
- Min -- 最小响应时间
- Max -- 最大响应时间
- Error -- 出错率
- Throughput -- 吞吐量
- KB/sec -- 以流量做衡量的吞吐量

#### 2.2 底层存储

后端存储使用 15 节点 Cassandra 集群，HugeGraph 与 Cassandra 集群位于不同的服务器，server 相关的配置文件除主机和端口有修改外，其余均保持默认。

### 3 性能结果总结

1. HugeGraph 单条插入顶点和边的速度分别为 9000 和 4500
2. 顶点和边的批量插入速度分别为5w/s和15w/s，远大于单条插入速度
3. 按 id 查询顶点和边的并发度可达到 12000 以上，且请求的平均延时小于 70ms

### 4 测试结果及分析

#### 4.1 batch 插入

##### 4.1.1 压力上限测试

###### 测试方法

不断提升并发量，测试 server 仍能正常提供服务的压力上限

###### 压力参数

持续时间：5min

###### 顶点的最大插入速度：

<div style="text-align: center;">
  <img src="/docs/images/API-perf/v0.5.6/cassandra/vertex_batch.png" alt="image">
</div>


###### 结论：

- 并发 3500，顶点的吞吐量是 261，每秒可处理的数据：261*200=52200/s

###### 边的最大插入速度

<div style="text-align: center;">
  <img src="/docs/images/API-perf/v0.5.6/cassandra/edge_batch.png" alt="image">
</div>


###### 结论：

- 并发 1000，边的吞吐量是 323，每秒可处理的数据：323*500=161500/s

#### 4.2 single 插入

##### 4.2.1 压力上限测试

###### 测试方法

不断提升并发量，测试 server 仍能正常提供服务的压力上限

###### 压力参数

- 持续时间：5min
- 服务异常标志：错误率大于 0.00%

###### 顶点的单条插入

<div style="text-align: center;">
  <img src="/docs/images/API-perf/v0.5.6/cassandra/vertex_single.png" alt="image">
</div>


###### 结论：

- 并发 9000，吞吐量为 8400，顶点的单条插入并发能力为 9000

###### 边的单条插入

<div style="text-align: center;">
  <img src="/docs/images/API-perf/v0.5.6/cassandra/edge_single.png" alt="image">
</div>


###### 结论：

- 并发 4500，吞吐量是 4160，边的单条插入并发能力为 4500

#### 4.3 按 id 查询

##### 4.3.1 压力上限测试

###### 测试方法

不断提升并发量，测试 server 仍能正常提供服务的压力上限

###### 压力参数

- 持续时间：5min
- 服务异常标志：错误率大于 0.00%

###### 顶点的按 id 查询

<div style="text-align: center;">
  <img src="/docs/images/API-perf/v0.5.6/cassandra/vertex_id_query.png" alt="image">
</div>


###### 结论：

- 并发 14500，吞吐量是 13576，顶点的按 id 查询的并发能力为 14500，平均延时为 11ms

###### 边的按 id 查询

<div style="text-align: center;">
  <img src="/docs/images/API-perf/v0.5.6/cassandra/edge_id_query.png" alt="image">
</div>

###### 结论：

- 并发 12000，吞吐量是 10688，边的按 id 查询的并发能力为 12000，平均延时为 63ms
