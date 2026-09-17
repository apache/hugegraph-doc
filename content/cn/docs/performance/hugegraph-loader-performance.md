---
title: "HugeGraph-Loader Performance"
linkTitle: "HugeGraph-Loader 性能"
weight: 3
---

> **Note:** 
> 
> 当前的性能指标测试基于很早期的版本。**最新版本**在性能和功能上都有显著的改进。我们鼓励您参考最新的发布版本，
> 该版本具有**自主分布式存储**和**增强的计算推下能力**。或者，您可以等待社区更新相关测试数据 (也欢迎反馈共建)。

## 使用场景

当要批量插入的图数据（包括顶点和边）条数为 billion 级别及以下，或者总数据量小于 TB 时，
可以采用 [HugeGraph-Loader](/cn/docs/quickstart/toolchain/hugegraph-loader) 工具持续、高速导入图数据

## 性能

> 测试均采用网址数据的边数据

### RocksDB 单机性能

- 关闭 label index，22.8w edges/s
- 开启 label index，15.3w edges/s

### Cassandra 集群性能

- 默认开启 label index，6.3w edges/s
