---
title: "HugeGraph-Spark Quick Start"
linkTitle: "Analysis with HugeGraph-Spark"
draft: true
weight: 8
---

### 1 HugeGraph-Spark 概述 (Deprecated)

HugeGraph-Spark 是一个连接 HugeGraph 和 Spark GraphX 的工具，能够读取 HugeGraph 中的数据并转换成 Spark GraphX 的 RDD，然后执行 GraphX 中的各种图算法。 (WARNING: Deprecated Now! Use HugeGraph-Computer instead)

### 2 环境依赖

Before using HugeGraph-Spark, you need to deploy HugeGraph-Server and Spark. Please refer to [HugeGraph-Server Quick Start](/docs/quickstart/hugegraph/hugegraph-server) for HugeGraph-Server deployment. Additionally, since HugeGraph-Spark requires Spark GraphX, you also need to download Spark. This example uses apache-spark-2.1.1.

```
wget https://archive.apache.org/dist/spark/spark-2.1.1/spark-2.1.1-bin-hadoop2.7.tgz
tar -zxvf spark-2.1.1-bin-hadoop2.7.tgz
cd spark-2.1.1-bin-hadoop2.7
```

然后将 hugegraph-spark 的 jar 包拷贝到 spark 的 jars 目录下

```
cp {dir}/hugegraph-spark-0.9.0.jar jars
```

### 3 配置

#### 3.1 配置项

可以通过 `spark-default.properties` 或者命令行修改相关配置：

- spark.hugegraph.snapshot.dir: 首次加载 hugegraph 数据生成 RDD 时，会将数据序列化保存到 spark 能访问到的介质上，以便于下次直接从该位置读取数据生成 RDD。默认值为 file:///tmp/hugegraph-snapshot，还可以配置为 HDFS 的路径；
- spark.hugegraph.name: 要访问的图的名字；
- spark.hugegraph.server.url: HugeGraphServer 的地址，默认值为 http://localhost:8080；
- spark.hugegraph.read.timeout: HugeClient 从 HugeGraphServer 获取数据的超时时间，单位为秒，默认值为 120；
- spark.hugegraph.split.size: 从 HugeGraphServer 中获取顶点和边时数据分片的大小，以字节为单位，默认值为 16M；
- spark.hugegraph.shard.page.size: 获取分片数据时，每个分页的大小，默认值为 500 条。

#### 3.2 配置入口

HugeGraph-Spark 提供了两种添加配置项的方法：

1. 修改 conf/spark-defaults.conf

  首次安装的用户需要将 spark-defaults.conf.default 文件拷贝一份，如下：

  ```bash
  cp conf/spark-defaults.conf.default conf/spark-defaults.conf
  ```

  按需设置即可。

2. 在命令行中修改

  ```bash
  bin/spark-shell --conf spark.hugegraph.snapshot.dir=file:///tmp/hugegraph-snapshot2
  ```

### 4 使用

#### 4.1 生成 GraphX Graph RDD

启动 scala shell

```bash
./bin/spark-shell
```

> 这种方式是以 local 模式启动，也支持 --master yarn 的模式运行。 

导入 hugegraph 相关类

```scala
scala> import org.apache.hugegraph.spark._
import org.apache.hugegraph.spark._
```

初始化 graph 对象（GraphX RDD），并创建 snapshot

```scala
scala> val graph = sc.hugeGraph("hugegraph", "http://localhost:8080")
org.apache.spark.graphx.Graph[org.apache.hugegraph.spark.structure.HugeSparkVertex,org.apache.hugegraph.spark.structure.HugeSparkEdge] = org.apache.spark.graphx.impl.GraphImpl@1418a1bd
```

如果已经配置过`spark.hugegraph.server.url`参数，可以省略第二个参数，直接通过`val graph = sc.hugeGraph("hugegraph")`调用即可。

这一步通常很快，因为只是获取了 HugeGraph 数据的分片信息，还没有真正的去执行 action 操作。

#### 4.2 使用 GraphX 进行图分析

数据导入成功后可以对 graph 进行相关操作，示例如下：

##### 获取顶点个数

```scala
graph.vertices.count()
```

注意：第一次执行这一步可能会很耗时，因为这里才真正的读数据并保存。

##### 获取边个数

```scala
graph.edges.count()
```

##### 出度 top 10

```scala
val top10 = graph.outDegrees.top(10)
sc.makeRDD(top10).join(graph.vertices).collect().foreach(println)
```

##### PageRank

PageRank 的结果仍为一个图，包含`vertices` 与 `edges`。

```scala
val ranks = graph.pageRank(0.0001)
```

获取 PageRank 的 top 10 的顶点。

```scala
val top10 = ranks.vertices.top(10)
```

更多 GraphX 的 API 请参考 [spark graphx 官网](http://spark.apache.org/graphx/)。
