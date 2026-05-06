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

#### 1.3 服务配置

- HugeGraph版本：0.4.4，RestServer和Gremlin Server和backends都在同一台服务器上
- Cassandra版本：cassandra-3.10，commit-log 和data共用SSD
- RocksDB版本：rocksdbjni-5.8.6
- Titan版本：0.5.4, 使用thrift+Cassandra模式

> graphdb-benchmark适配的Titan版本为0.5.4

### 2 测试结果

#### 2.1 Batch插入性能

| Backend   | email-enron(30w) | amazon0601(300w) | com-youtube.ungraph(300w) |
|-----------|------------------|------------------|---------------------------|
| Titan     | 9.516            | 88.123           | 111.586                   |
| RocksDB   | 2.345            | 14.076           | 16.636                    |
| Cassandra | 11.930           | 108.709          | 101.959                   |
| Memory    | 3.077            | 15.204           | 13.841                    |

_说明_

- 表头"（）"中数据是数据规模，以边为单位
- 表中数据是批量插入的时间，单位是s
- 例如，HugeGraph使用RocksDB插入amazon0601数据集的300w条边，花费14.076s，速度约为21w edges/s

##### 结论

- RocksDB和Memory后端插入性能优于Cassandra
- HugeGraph和Titan同样使用Cassandra作为后端的情况下，插入性能接近

#### 2.2 遍历性能

##### 2.2.1 术语说明

- FN(Find Neighbor), 遍历所有vertex, 根据vertex查邻接edge, 通过edge和vertex查other vertex
- FA(Find Adjacent), 遍历所有edge，根据edge获得source vertex和target vertex

##### 2.2.2 FN性能

| Backend   | email-enron(3.6w) | amazon0601(40w) | com-youtube.ungraph(120w) |
|-----------|-------------------|-----------------|---------------------------|
| Titan     | 7.724             | 70.935          | 128.884                   |
| RocksDB   | 8.876             | 65.852          | 63.388                    |
| Cassandra | 13.125            | 126.959         | 102.580                   |
| Memory    | 22.309            | 207.411         | 165.609                   |

_说明_

- 表头"（）"中数据是数据规模，以顶点为单位
- 表中数据是遍历顶点花费的时间，单位是s
- 例如，HugeGraph使用RocksDB后端遍历amazon0601的所有顶点，并查找邻接边和另一顶点，总共耗时65.852s

##### 2.2.3 FA性能

| Backend   | email-enron(30w) | amazon0601(300w) | com-youtube.ungraph(300w) |
|-----------|------------------|------------------|---------------------------|
| Titan     | 7.119            | 63.353           | 115.633                   |
| RocksDB   | 6.032            | 64.526           | 52.721                    |
| Cassandra | 9.410            | 102.766          | 94.197                    |
| Memory    | 12.340           | 195.444          | 140.89                    |

_说明_

- 表头"（）"中数据是数据规模，以边为单位
- 表中数据是遍历边花费的时间，单位是s
- 例如，HugeGraph使用RocksDB后端遍历amazon0601的所有边，并查询每条边的两个顶点，总共耗时64.526s

###### 结论

- HugeGraph RocksDB > Titan thrift+Cassandra > HugeGraph Cassandra > HugeGraph Memory

#### 2.3 HugeGraph-图常用分析方法性能

##### 术语说明

- FS(Find Shortest Path), 寻找最短路径
- K-neighbor，从起始vertex出发，通过K跳边能够到达的所有顶点, 包括1, 2, 3...(K-1), K跳边可达vertex
- K-out, 从起始vertex出发，恰好经过K跳out边能够到达的顶点

##### FS性能

| Backend   | email-enron(30w) | amazon0601(300w) | com-youtube.ungraph(300w) |
|-----------|------------------|------------------|---------------------------|
| Titan     | 11.333           | 0.313            | 376.06                    |
| RocksDB   | 44.391           | 2.221            | 268.792                   |
| Cassandra | 39.845           | 3.337            | 331.113                   |
| Memory    | 35.638           | 2.059            | 388.987                   |

_说明_

- 表头"（）"中数据是数据规模，以边为单位
- 表中数据是找到**从第一个顶点出发到达随机选择的100个顶点的最短路径**的时间，单位是s
- 例如，HugeGraph使用RocksDB查找第一个顶点到100个随机顶点的最短路径，总共耗时2.059s

###### 结论

- 在数据规模小或者顶点关联关系少的场景下，Titan最短路径性能优于HugeGraph
- 随着数据规模增大且顶点的关联度增高，HugeGraph最短路径性能优于Titan

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

- FS场景，HugeGraph性能优于Titan
- K-neighbor和K-out场景，HugeGraph能够实现在5度范围内秒级返回结果

#### 2.4 图综合性能测试-CW

| 数据库             | 规模1000 | 规模5000   | 规模10000  | 规模20000  |
|-----------------|--------|----------|----------|----------|
| Titan           | 45.943 | 849.168  | 2737.117 | 9791.46  |
| Memory(core)    | 41.077 | 1825.905 | *        | *        |
| Cassandra（core） | 39.783 | 862.744  | 2423.136 | 6564.191 |
| RocksDB（core）   | 33.383 | 199.894  | 763.869  | 1677.813 |

_说明_

- "规模"以顶点为单位
- 表中数据是社区发现完成需要的时间，单位是s，例如HugeGraph使用RocksDB后端在规模10000的数据集，社区聚合不再变化，需要耗时763.869s
- "*"表示超过10000s未完成
- CW测试是CRUD的综合评估
- 后三者分别是HugeGraph的不同后端，该测试中HugeGraph跟Titan一样，没有通过client，直接对core操作

##### 结论

- HugeGraph在使用Cassandra后端时，性能略优于Titan，随着数据规模的增大，优势越来越明显，数据规模20000时，比Titan快30%
- HugeGraph在使用RocksDB后端时，性能远高于Titan和HugeGraph的Cassandra后端，分别比两者快了6倍和4倍
