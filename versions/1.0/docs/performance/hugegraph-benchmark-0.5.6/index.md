# HugeGraph BenchMark Performance

LLMS index: [llms.txt](/versions/1.0/llms.txt)

---

### 1 测试环境

#### 1.1 硬件信息

| CPU                                          | Memory | 网卡        | 磁盘        |
|----------------------------------------------|--------|-----------|-----------|
| 48 Intel(R) Xeon(R) CPU E5-2650 v4 @ 2.20GHz | 128G   | 10000Mbps | 750GB SSD |

#### 1.2 软件信息

##### 1.2.1 测试用例

测试使用[graphdb-benchmark](https://github.com/socialsensor/graphdb-benchmarks)，一个图数据库测试集。该测试集主要包含4类测试：

- Massive Insertion，批量插入顶点和边，一定数量的顶点或边一次性提交
- Single Insertion，单条插入，每个顶点或者每条边立即提交
- Query，主要是图数据库的基本查询操作：

  - Find Neighbors，查询所有顶点的邻居
  - Find Adjacent Nodes，查询所有边的邻接顶点
  - Find Shortest Path，查询第一个顶点到100个随机顶点的最短路径

- Clustering，基于Louvain Method的社区发现算法

##### 1.2.2 测试数据集

测试使用人造数据和真实数据

- MIW、SIW和QW使用SNAP数据集

  - [Enron Dataset](http://snap.stanford.edu/data/email-Enron.html)

  - [Amazon dataset](http://snap.stanford.edu/data/amazon0601.html)

  - [Youtube dataset](http://snap.stanford.edu/data/com-Youtube.html)

  - [LiveJournal dataset](http://snap.stanford.edu/data/com-LiveJournal.html)

- CW使用[LFR-Benchmark generator](https://sites.google.com/site/andrealancichinetti/files)生成的人造数据

###### 本测试用到的数据集规模

| 名称                      | vertex数目  | edge数目    | 文件大小   |
|-------------------------|-----------|-----------|--------|
| email-enron.txt         | 36,691    | 367,661   | 4MB    |
| com-youtube.ungraph.txt | 1,157,806 | 2,987,624 | 38.7MB |
| amazon0601.txt          | 403,393   | 3,387,388 | 47.9MB |
| com-lj.ungraph.txt      | 3997961   | 34681189  | 479MB  |

#### 1.3 服务配置

- HugeGraph版本：0.5.6，RestServer和Gremlin Server和backends都在同一台服务器上

  - RocksDB版本：rocksdbjni-5.8.6

- Titan版本：0.5.4, 使用thrift+Cassandra模式

  - Cassandra版本：cassandra-3.10，commit-log 和 data 共用SSD

- Neo4j版本：2.0.1

> graphdb-benchmark适配的Titan版本为0.5.4

### 2 测试结果

#### 2.1 Batch插入性能

| Backend   | email-enron(30w) | amazon0601(300w) | com-youtube.ungraph(300w) | com-lj.ungraph(3000w) |
|-----------|------------------|------------------|---------------------------|-----------------------|
| HugeGraph | 0.629            | 5.711            | 5.243                     | 67.033                |
| Titan     | 10.15            | 108.569          | 150.266                   | 1217.944              |
| Neo4j     | 3.884            | 18.938           | 24.890                    | 281.537               |

_说明_

- 表头"（）"中数据是数据规模，以边为单位
- 表中数据是批量插入的时间，单位是s
- 例如，HugeGraph使用RocksDB插入amazon0601数据集的300w条边，花费5.711s

##### 结论

- 批量插入性能 HugeGraph(RocksDB) > Neo4j > Titan(thrift+Cassandra)

#### 2.2 遍历性能

##### 2.2.1 术语说明

- FN(Find Neighbor), 遍历所有vertex, 根据vertex查邻接edge, 通过edge和vertex查other vertex
- FA(Find Adjacent), 遍历所有edge，根据edge获得source vertex和target vertex

##### 2.2.2 FN性能

| Backend   | email-enron(3.6w) | amazon0601(40w) | com-youtube.ungraph(120w) | com-lj.ungraph(400w) |
|-----------|-------------------|-----------------|---------------------------|----------------------|
| HugeGraph | 4.072             | 45.118          | 66.006                    | 609.083              |
| Titan     | 8.084             | 92.507          | 184.543                   | 1099.371             |
| Neo4j     | 2.424             | 10.537          | 11.609                    | 106.919              |

_说明_

- 表头"（）"中数据是数据规模，以顶点为单位
- 表中数据是遍历顶点花费的时间，单位是s
- 例如，HugeGraph使用RocksDB后端遍历amazon0601的所有顶点，并查找邻接边和另一顶点，总共耗时45.118s

##### 2.2.3 FA性能

| Backend   | email-enron(30w) | amazon0601(300w) | com-youtube.ungraph(300w) | com-lj.ungraph(3000w) |
|-----------|------------------|------------------|---------------------------|-----------------------|
| HugeGraph | 1.540            | 10.764           | 11.243                    | 151.271               |
| Titan     | 7.361            | 93.344           | 169.218                   | 1085.235              |
| Neo4j     | 1.673            | 4.775            | 4.284                     | 40.507                |

_说明_

- 表头"（）"中数据是数据规模，以边为单位
- 表中数据是遍历边花费的时间，单位是s
- 例如，HugeGraph使用RocksDB后端遍历amazon0601的所有边，并查询每条边的两个顶点，总共耗时10.764s

###### 结论

- 遍历性能 Neo4j > HugeGraph(RocksDB) > Titan(thrift+Cassandra)

#### 2.3 HugeGraph-图常用分析方法性能

##### 术语说明

- FS(Find Shortest Path), 寻找最短路径
- K-neighbor，从起始vertex出发，通过K跳边能够到达的所有顶点, 包括1, 2, 3...(K-1), K跳边可达vertex
- K-out, 从起始vertex出发，恰好经过K跳out边能够到达的顶点

##### FS性能

| Backend   | email-enron(30w) | amazon0601(300w) | com-youtube.ungraph(300w) | com-lj.ungraph(3000w) |
|-----------|------------------|------------------|---------------------------|-----------------------|
| HugeGraph | 0.494            | 0.103            | 3.364                     | 8.155                 |
| Titan     | 11.818           | 0.239            | 377.709                   | 575.678               |
| Neo4j     | 1.719            | 1.800            | 1.956                     | 8.530                 |

_说明_

- 表头"（）"中数据是数据规模，以边为单位
- 表中数据是找到**从第一个顶点出发到达随机选择的100个顶点的最短路径**的时间，单位是s
- 例如，HugeGraph使用RocksDB后端在图amazon0601中查找第一个顶点到100个随机顶点的最短路径，总共耗时0.103s

###### 结论

- 在数据规模小或者顶点关联关系少的场景下，HugeGraph性能优于Neo4j和Titan
- 随着数据规模增大且顶点的关联度增高，HugeGraph与Neo4j性能趋近，都远高于Titan

##### K-neighbor性能

顶点    | 深度 | 一度     | 二度     | 三度     | 四度     | 五度     | 六度
----- | -- | ------ | ------ | ------ | ------ | ------ | ---
v1    | 时间 | 0.031s | 0.033s | 0.048s | 0.500s | 11.27s | OOM
v111  | 时间 | 0.027s | 0.034s | 0.115  | 1.36s  | OOM    | --
v1111 | 时间 | 0.039s | 0.027s | 0.052s | 0.511s | 10.96s | OOM

_说明_

- HugeGraph-Server的JVM内存设置为32GB，数据量过大时会出现OOM

##### K-out性能

顶点    | 深度 | 一度     | 二度     | 三度     | 四度     | 五度        | 六度
----- | -- | ------ | ------ | ------ | ------ | --------- | ---
v1    | 时间 | 0.054s | 0.057s | 0.109s | 0.526s | 3.77s     | OOM
      | 度  | 10     | 133    | 2453   | 50,830 | 1,128,688 |
v111  | 时间 | 0.032s | 0.042s | 0.136s | 1.25s  | 20.62s    | OOM
      | 度  | 10     | 211    | 4944   | 113150 | 2,629,970 |
v1111 | 时间 | 0.039s | 0.045s | 0.053s | 1.10s  | 2.92s     | OOM
      | 度  | 10     | 140    | 2555   | 50825  | 1,070,230 |

_说明_

- HugeGraph-Server的JVM内存设置为32GB，数据量过大时会出现OOM

###### 结论

- FS场景，HugeGraph性能优于Neo4j和Titan
- K-neighbor和K-out场景，HugeGraph能够实现在5度范围内秒级返回结果

#### 2.4 图综合性能测试-CW

| 数据库             | 规模1000 | 规模5000  | 规模10000  | 规模20000  |
|-----------------|--------|---------|----------|----------|
| HugeGraph(core) | 20.804 | 242.099 | 744.780  | 1700.547 |
| Titan           | 45.790 | 820.633 | 2652.235 | 9568.623 |
| Neo4j           | 5.913  | 50.267  | 142.354  | 460.880  |

_说明_

- "规模"以顶点为单位
- 表中数据是社区发现完成需要的时间，单位是s，例如HugeGraph使用RocksDB后端在规模10000的数据集，社区聚合不再变化，需要耗时744.780s
- CW测试是CRUD的综合评估
- 该测试中HugeGraph跟Titan一样，没有通过client，直接对core操作

##### 结论

- 社区聚类算法性能 Neo4j > HugeGraph > Titan
