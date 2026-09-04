---
title: "HugeGraph-Spark Quick Start"
linkTitle: "Analysis with HugeGraph-Spark"
draft: true
weight: 8
---

> HugeGraph-Spark is no longer maintained. Use [HugeGraph-Computer](/docs/quickstart/computing/hugegraph-computer) for new graph computing workloads. This page is retained only as a reference for older versions.

### 1 HugeGraph-Spark Overview (Deprecated)

HugeGraph-Spark connects HugeGraph with Spark GraphX. It reads data from HugeGraph, converts it into Spark GraphX RDDs, and then runs GraphX graph algorithms. (Warning: this component is deprecated; use HugeGraph-Computer instead.)

### 2 Requirements

HugeGraph-Spark depends on HugeGraph Server; see [HugeGraph Server Quick Start](/docs/quickstart/hugegraph/hugegraph-server) for installation. It also depends on Spark GraphX. The legacy example retained below uses Apache Spark 2.1.1.

```
wget https://archive.apache.org/dist/spark/spark-2.1.1/spark-2.1.1-bin-hadoop2.7.tgz
tar -zxvf spark-2.1.1-bin-hadoop2.7.tgz
cd spark-2.1.1-bin-hadoop2.7
```

Then copy the HugeGraph-Spark JAR into Spark's `jars` directory:

```
cp {dir}/hugegraph-spark-0.9.0.jar jars
```

### 3 Configuration

#### 3.1 Configuration Options

The following options can be set in `spark-default.properties` or on the command line:

- `spark.hugegraph.snapshot.dir`: When HugeGraph data is first loaded to create an RDD, the data is serialized to storage accessible to Spark so that subsequent runs can create an RDD directly from that location. The default is `file:///tmp/hugegraph-snapshot`; an HDFS path can also be used.
- `spark.hugegraph.name`: The name of the graph to access.
- `spark.hugegraph.server.url`: The HugeGraph Server URL. The default is `http://localhost:8080`.
- `spark.hugegraph.read.timeout`: The timeout, in seconds, for HugeClient to retrieve data from HugeGraph Server. The default is 120.
- `spark.hugegraph.split.size`: The data split size, in bytes, used when retrieving vertices and edges from HugeGraph Server. The default is 16 MB.
- `spark.hugegraph.shard.page.size`: The page size used when retrieving split data. The default is 500 records.

#### 3.2 Where to Configure Options

HugeGraph-Spark provides two ways to add configuration options:

1. Edit `conf/spark-defaults.conf`.

   For a new installation, first copy `spark-defaults.conf.default`:

   ```bash
   cp conf/spark-defaults.conf.default conf/spark-defaults.conf
   ```

   Then set the required options.

2. Set options on the command line.

   ```bash
   bin/spark-shell --conf spark.hugegraph.snapshot.dir=file:///tmp/hugegraph-snapshot2
   ```

### 4 Usage

#### 4.1 Create a GraphX Graph RDD

Start the Scala shell:

```bash
./bin/spark-shell
```

> This command starts Spark in local mode. You can also run it with `--master yarn`.

Import the HugeGraph classes:

```scala
scala> import org.apache.hugegraph.spark._
import org.apache.hugegraph.spark._
```

Initialize the graph object (a GraphX RDD) and create a snapshot:

```scala
scala> val graph = sc.hugeGraph("hugegraph", "http://localhost:8080")
org.apache.spark.graphx.Graph[org.apache.hugegraph.spark.structure.HugeSparkVertex,org.apache.hugegraph.spark.structure.HugeSparkEdge] = org.apache.spark.graphx.impl.GraphImpl@1418a1bd
```

If `spark.hugegraph.server.url` is already configured, omit the second argument and call `val graph = sc.hugeGraph("hugegraph")` directly.

This step is usually fast because it retrieves only the split metadata for HugeGraph data. No action has run yet.

#### 4.2 Analyze the Graph with GraphX

After the data is imported, run operations on the graph as shown below.

##### Count Vertices

```scala
graph.vertices.count()
```

The first execution may take a long time because this is when the data is actually read and saved.

##### Count Edges

```scala
graph.edges.count()
```

##### Top 10 by Out-Degree

```scala
val top10 = graph.outDegrees.top(10)
sc.makeRDD(top10).join(graph.vertices).collect().foreach(println)
```

##### PageRank

The PageRank result is also a graph containing `vertices` and `edges`.

```scala
val ranks = graph.pageRank(0.0001)
```

Get the top 10 PageRank vertices:

```scala
val top10 = ranks.vertices.top(10)
```

For more GraphX APIs, see the [Spark GraphX documentation](http://spark.apache.org/graphx/).
