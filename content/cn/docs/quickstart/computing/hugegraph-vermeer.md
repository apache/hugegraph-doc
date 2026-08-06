---
title: "HugeGraph-Vermeer Quick Start"
linkTitle: "Vermeer: 高性能内存图计算框架"
weight: 1
---

## 一、Vermeer 概述

### 1.1 运行架构

Vermeer 是一个 `Go`编写的高性能内存优先的图计算框架 (一次启动，任意执行)，支持 15+ OLAP 图算法的极速计算 (大部分秒~分钟级别完成执行)，包含 master 和 worker 两种角色。master 目前只有一个 (可增加 HA)，worker 可以有多个。

master 是负责通信、转发、汇总的节点，计算量和占用资源量较少。worker 是计算节点，用于存储图数据和运行计算任务，占用大量内存和 cpu。grpc 和 rest 模块分别负责内部通信和外部调用。

该框架的运行配置可以通过命令行参数传入，也可以通过位于 `config/` 目录下的配置文件指定，`--env` 参数可以指定使用哪个配置文件，例如 `--env=master` 指定使用 `master.ini`。需要注意 master 需要指定监听的端口号，worker 需要指定监听端口号和 master 的 `ip:port`。

### 1.2 运行方法

1. **方案一：Docker Compose（推荐）**

确保docker-compose.yaml存在于您的项目根目录中。如果没有，以下是一个示例：

```yaml
services:
  vermeer-master:
    image: hugegraph/vermeer
    container_name: vermeer-master
    volumes:
      - ~/.config:/go/bin/config # Change here to your actual config path
    command: --env=master
    networks:
      vermeer_network:
        ipv4_address: 172.20.0.10 # Assign a static IP for the master

  vermeer-worker:
    image: hugegraph/vermeer
    container_name: vermeer-worker
    volumes:
      - ~/:/go/bin/config # Change here to your actual config path
    command: --env=worker
    networks:
      vermeer_network:
        ipv4_address: 172.20.0.11 # Assign a static IP for the worker

networks:
  vermeer_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24 # Define the subnet for your network
```

修改 docker-compose.yaml
- **Volume**：例如将两处 ~/:/go/bin/config 改为 /home/user/config:/go/bin/config（或您自己的配置目录）。
- **Subnet**：根据实际情况修改子网IP。请注意，每个容器需要访问的端口在config文件中指定，具体请参照项目`config`文件夹下内容。

在项目目录构建镜像并启动（或者先用 docker build 再 docker-compose up）

```shell
# 构建镜像（在项目根 vermeer 目录）
docker build -t hugegraph/vermeer .

# 启动（在 vermeer 根目录）
docker-compose up -d
# 或使用新版 CLI：
# docker compose up -d
```

查看日志 / 停止 / 删除：

```shell
docker-compose logs -f
docker-compose down
```

2. **方案二：通过 docker run 单独启动（手动创建网络并分配静态 IP）**

确保CONFIG_DIR对Docker进程具有适当的读取/执行权限。

构建镜像：

```shell
docker build -t hugegraph/vermeer .
```

创建自定义 bridge 网络（一次性操作）：

```shell
docker network create --driver bridge \
  --subnet 172.20.0.0/24 \
  vermeer_network
```

运行 master（调整 CONFIG_DIR 为您的绝对配置路径，可以根据实际情况调整IP）：

```shell
CONFIG_DIR=/home/user/config

docker run -d \
  --name vermeer-master \
  --network vermeer_network --ip 172.20.0.10 \
  -v ${CONFIG_DIR}:/go/bin/config \
  hugegraph/vermeer \
  --env=master
```

运行 worker：

```shell
docker run -d \
  --name vermeer-worker \
  --network vermeer_network --ip 172.20.0.11 \
  -v ${CONFIG_DIR}:/go/bin/config \
  hugegraph/vermeer \
  --env=worker
```

查看日志 / 停止 / 删除：

```shell
docker logs -f vermeer-master
docker logs -f vermeer-worker

docker stop vermeer-master vermeer-worker
docker rm vermeer-master vermeer-worker

# 删除自定义网络（如果需要）
docker network rm vermeer_network
```

3. **方案三：从源码构建**

构建。具体请参照 [Vermeer Readme](https://github.com/apache/hugegraph-computer/tree/master/vermeer)。

```shell
go build
```

在进入文件夹目录后输入 `./vermeer --env=master` 或 `./vermeer --env=worker01`

## 二、任务创建类 rest api

### 2.1 简介

此类 rest api 提供所有创建任务的功能，包括读取图数据和多种计算功能，提供异步返回和同步返回两种接口。返回的内容均包含所创建任务的信息。使用 vermeer 的整体流程是先创建读取图的任务，待图读取完毕后创建计算任务执行计算。图不会自动被删除，在一个图上运行多个计算任务无需多次重复读取，如需删除可用删除图接口。任务状态可分为读取任务状态和计算任务状态。通常情况下客户端仅需了解创建、任务中、任务结束和任务错误四种状态。图状态是图是否可用的判断依据，若图正在读取中或图状态错误，无法使用该图创建计算任务。图删除接口仅在 loaded 和 error 状态且该图无计算任务时可用。

可以使用的 url 如下：

- 异步返回接口 POST http://master_ip:port/tasks/create 仅返回任务创建是否成功，需通过主动查询任务状态判断是否完成。
- 同步返回接口 POST http://master_ip:port/tasks/create/sync 在任务结束后返回。

### 2.2 加载图数据

具体参数参考 Vermeer 参数列表文档。

vermeer提供三种加载方式：

1. 从本地加载

可以预先获取数据集，例如 twitter-2010 数据集。获取方式：https://snap.stanford.edu/data/twitter-2010.html，第一个 twitter-2010.txt.gz 即可。

**request 示例：**

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "load",
 "graph": "testdb",
 "params": {
  "load.parallel": "50",
  "load.type": "local",
  "load.vertex_files": "{\"localhost\":\"data/twitter-2010.v_[0,99]\"}",
  "load.edge_files": "{\"localhost\":\"data/twitter-2010.e_[0,99]\"}",
  "load.use_out_degree": "1",
  "load.use_outedge": "1"
 }
}
```

2. 从hugegraph加载

**request 示例：**

⚠️ 安全警告：切勿在配置文件或代码中存储真实密码。请改用环境变量或安全的凭据管理系统。

```javascript
POST http://localhost:8688/tasks/create
{
  "task_type": "load",
  "graph": "testdb",
  "params": {
    "load.parallel": "50",
    "load.type": "hugegraph",
    "load.hg_pd_peers": "[\"<your-hugegraph-ip>:8686\"]",
    "load.hugegraph_name": "DEFAULT/hugegraph2/g",
    "load.hugegraph_username": "admin",
    "load.hugegraph_password": "<your-password-here>",
    "load.use_out_degree": "1",
    "load.use_outedge": "1"
  }
}
```

3. 从hdfs加载

**request 示例：**

```javascript
POST http://localhost:8688/tasks/create
{
  "task_type": "load",
  "graph": "testdb",
  "params": {
    "load.parallel": "50",
    "load.type": "hdfs",
    "load.hdfs_namenode": "name_node1:9000",
    "load.hdfs_conf_path": "/path/to/conf",
    "load.krb_realm": "EXAMPLE.COM",
    "load.krb_name": "user@EXAMPLE.COM",
    "load.krb_keytab_path": "/path/to/keytab",
    "load.krb_conf_path": "/path/to/krb5.conf",
    "load.hdfs_use_krb": "1",
    "load.vertex_files": "/data/graph/vertices",
    "load.edge_files": "/data/graph/edges",
    "load.use_out_degree": "1",
    "load.use_outedge": "1"
  }
}
```

### 2.3 输出计算结果

所有的 vermeer 计算任务均支持多种结果输出方式，可自定义输出方式：local、hdfs、afs 或 hugegraph，在发送请求时的 params 参数下加入对应参数，即可生效。指定 output.need_statistics 为 1 时，支持计算结果统计信息输出，结果会写在接口任务信息内。统计模式算子目前支持 "count" 和 "modularity" 。但仅针对社区发现算法适用。

具体参数参考 Vermeer 参数列表文档。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "pagerank",
 "compute.parallel": "10",
 "compute.max_step": "10",
 "output.type": "local",
 "output.parallel": "1",
 "output.file_path": "result/pagerank"
  }
}
```

## 三、支持的算法

### 3.1 PageRank

PageRank 算法又称网页排名算法，是一种由搜索引擎根据网页（节点）之间相互的超链接进行计算的技

术，用来体现网页（节点）的相关性和重要性。

- 如果一个网页被很多其他网页链接到，说明这个网页比较重要，也就是其 PageRank 值会相对较高。
- 如果一个 PageRank 值很高的网页链接到其他网页，那么被链接到的网页的 PageRank 值会相应地提高。

PageRank 算法适用于网页排序、社交网络重点人物发掘等场景。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "pagerank",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/pagerank",
 "compute.max_step":"10"
 }
}
```

### 3.2 WCC（弱连通分量）

弱连通分量，计算无向图中所有联通的子图，输出各顶点所属的弱联通子图 id，表明各个点之间的连通性，区分不同的连通社区。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "wcc",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/wcc",
 "compute.max_step":"10"
 }
}
```

### 3.3 LPA（标签传播）

标签传递算法，是一种图聚类算法，常用在社交网络中，用于发现潜在的社区。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "lpa",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/lpa",
 "compute.max_step":"10"
 }
}
```

### 3.4 Degree Centrality（度中心性）

度中心性算法，算法用于计算图中每个节点的度中心性值，支持无向图和有向图。度中心性是衡量节点重要性的重要指标，节点与其它节点的边越多，则节点的度中心性值越大，节点在图中的重要性也就越高。在无向图中，度中心性的计算是基于边信息统计节点出现次数，得出节点的度中心性的值，在有向图中则基于边的方向进行筛选，基于输入边或输出边信息统计节点出现次数，得到节点的入度值或出度值。它表明各个点的重要性，一般越重要的点度数越高。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "degree",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/degree",
 "degree.direction":"both"
 }
}
```

### 3.5 Closeness Centrality（紧密中心性）

紧密中心性（Closeness Centrality）用于计算一个节点到所有其他可达节点的最短距离的倒数，进行累积后归一化的值。紧密中心度可以用来衡量信息从该节点传输到其他节点的时间长短。节点的“Closeness Centrality”越大，其在所在图中的位置越靠近中心，适用于社交网络中关键节点发掘等场景。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "closeness_centrality",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/closeness_centrality",
 "closeness_centrality.sample_rate":"0.01"
 }
}
```

### 3.6 Betweenness Centrality（中介中心性算法）

中介中心性算法（Betweeness Centrality）判断一个节点具有"桥梁"节点的值，值越大说明它作为图中两点间必经路径的可能性越大，典型的例子包括社交网络中的共同关注的人。适用于衡量社群围绕某个节点的聚集程度。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "betweenness_centrality",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/betweenness_centrality",
 "betweenness_centrality.sample_rate":"0.01"
 }
}
```

### 3.7 Triangle Count（三角形计数）

三角形计数算法，用于计算通过每个顶点的三角形个数，适用于计算用户之间的关系，关联性是不是成三角形。三角形越多，代表图中节点关联程度越高，组织关系越严密。社交网络中的三角形表示存在有凝聚力的社区，识别三角形有助于理解网络中个人或群体的聚类和相互联系。在金融网络或交易网络中，三角形的存在可能表示存在可疑或欺诈活动，三角形计数可以帮助识别可能需要进一步调查的交易模式。

输出的结果为 每个顶点对应一个 Triangle Count，即为每个顶点所在三角形的个数。

注：该算法为无向图算法，忽略边的方向。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "triangle_count",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/triangle_count"
 }
}
```

### 3.8 K-Core

K-Core 算法，标记所有度数为 K 的顶点，适用于图的剪枝，查找图的核心部分。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "kcore",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/kcore",
 "kcore.degree_k":"5"
 }
}
```

### 3.9 SSSP（单元最短路径）

单源最短路径算法，求一个点到其他所有点的最短距离。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "sssp",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/degree",
 "sssp.source":"tom"
 }
}
```

### 3.10 KOUT

以一个点为起点，获取这个点的 k 层的节点。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "kout",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/kout",
 "kout.source":"tom",
 "compute.max_step":"6"
 }
}
```

### 3.11 Louvain

Louvain 算法是一种基于模块度的社区发现算法。其基本思想是网络中节点尝试遍历所有邻居的社区标签，并选择最大化模块度增量的社区标签。在最大化模块度之后，每个社区看成一个新的节点，重复直到模块度不再增大。

Vermeer 上实现的分布式 Louvain 算法受节点顺序、并行计算等因素影响，并且由于 Louvain 算法由于其遍历顺序的随机导致社区压缩也具有一定的随机性，导致重复多次执行可能存在不同的结果。但整体趋势不会有大的变化。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "louvain",
 "compute.parallel":"10",
 "compute.max_step":"1000",
 "louvain.threshold":"0.0000001",
 "louvain.resolution":"1.0",
 "louvain.step":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/louvain"
  }
 }
```

### 3.12 Jaccard 相似度系数

Jaccard index , 又称为 Jaccard 相似系数（Jaccard similarity coefficient）用于比较有限样本集之间的相似性与差异性。Jaccard 系数值越大，样本相似度越高。用于计算一个给定的源点，与图中其他所有点的 Jaccard 相似系数。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "jaccard",
 "compute.parallel":"10",
 "compute.max_step":"2",
 "jaccard.source":"123",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/jaccard"
 }
}
```

### 3.13 Personalized PageRank

个性化的 pagerank 的目标是要计算所有节点相对于用户 u 的相关度。从用户 u 对应的节点开始游走，每到一个节点都以 1-d 的概率停止游走并从 u 重新开始，或者以 d 的概率继续游走，从当前节点指向的节点中按照均匀分布随机选择一个节点往下游走。用于给定一个起点，计算此起点开始游走的个性化 pagerank 得分。适用于社交推荐等场景。

由于计算需要使用出度，需要在读取图时需要设置 load.use_out_degree 为 1。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "ppr",
 "compute.parallel":"100",
 "compute.max_step":"10",
 "ppr.source":"123",
 "ppr.damping":"0.85",
 "ppr.diff_threshold":"0.00001",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/ppr"
 }
}
```

### 3.14 全图 Kout

计算图的所有节点的k度邻居（不包含自己以及1～k-1度的邻居），由于全图kout算法内存膨胀比较厉害，目前k限制在1和2，另外，全局kout算法支持过滤功能( 参数如："compute.filter":"risk_level==1"),在计算第k度的是时候进行过滤条件的判断，符合过滤条件的进入最终结果集，算法最终输出是符合条件的邻居个数。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "kout_all",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"10",
 "output.file_path":"result/kout",
 "compute.max_step":"2"，
 "compute.filter":"risk_level==1"
 }
}
```

### 3.15 集聚系数 clustering coefficient

集聚系数表示一个图中节点聚集程度的系数。在现实的网络中，尤其是在特定的网络中，由于相对高密度连接点的关系，节点总是趋向于建立一组严密的组织关系。集聚系数算法（Cluster Coefficient）用于计算图中节点的聚集程度。本算法为局部集聚系数。局部集聚系数可以测量图中每一个结点附近的集聚程度。

request 示例：

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "clustering_coefficient",
 "compute.parallel":"100",
 "compute.max_step":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/cc"
 }
}
```

### 3.16 SCC（强连通分量）

在有向图的数学理论中，如果一个图的每一个顶点都可从该图其他任意一点到达，则称该图是强连通的。在任意有向图中能够实现强连通的部分我们称其为强连通分量。它表明各个点之间的连通性，区分不同的连通社区。

```javascript
POST http://localhost:8688/tasks/create
{
 "task_type": "compute",
 "graph": "testdb",
 "params": {
 "compute.algorithm": "scc",
 "compute.parallel":"10",
 "output.type":"local",
 "output.parallel":"1",
 "output.file_path":"result/scc",
 "compute.max_step":"200"
 }
}
```

> 🚧, 后续随时更新完善，欢迎随时提出建议和意见。

