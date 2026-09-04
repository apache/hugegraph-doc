---
title: "HugeGraph-Vermeer Quick Start"
linkTitle: "Vermeer: 高性能内存图计算框架"
weight: 1
---

## 一、Vermeer 概述

### 1.1 运行架构

Vermeer 是 Go 编写的内存图计算平台，采用 master-worker 架构。master 负责调度，worker 保存图数据并执行计算；当前源码注册了 19 个算法。

节点间使用 gRPC，外部请求使用 REST API。默认 master HTTP/gRPC 端口为 `6688`/`6689`，worker 为 `6788`/`6789`。通过 `--env=master` 或 `--env=worker` 读取 `config/master.ini` 或 `config/worker.ini`。

### 1.2 运行方法

1. **方案一：Docker Compose**

仓库 `vermeer/docker-compose.yaml` 已提供 master 和 worker 示例。修改挂载目录和 worker 的 `master_peer` 后启动即可。不要把整个主目录挂进容器；只挂载包含 `master.ini`、`worker.ini` 的配置目录。

```yaml
services:
  vermeer-master:
    image: hugegraph/vermeer
    container_name: vermeer-master
    volumes:
      - /home/user/vermeer-config:/go/bin/config
    command: --env=master
    networks:
      vermeer_network:
        ipv4_address: 172.20.0.10 # Assign a static IP for the master

  vermeer-worker:
    image: hugegraph/vermeer
    container_name: vermeer-worker
    volumes:
      - /home/user/vermeer-config:/go/bin/config
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

修改 `docker-compose.yaml` 中的挂载目录和子网，并把 `worker.ini` 的 `master_peer` 指向 master 的 `6689` 端口。监听地址以 `config/master.ini` 和 `config/worker.ini` 为准。

在 `vermeer` 目录构建镜像并启动：

```shell
# 构建镜像（在项目根 vermeer 目录）
docker build -t hugegraph/vermeer .

# 启动（在 vermeer 根目录）
docker compose up -d
```

查看日志 / 停止 / 删除：

```shell
docker compose logs -f
docker compose down
```

2. **方案二：通过 docker run 单独启动（手动创建网络并分配静态 IP）**

`CONFIG_DIR` 需要包含 Vermeer 配置文件，并允许 Docker 读取。

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
  -p 6688:6688 -p 6689:6689 \
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
make init
make
```

`make init` 首次执行时下载 supervisord、protoc 和 Web UI 资源。构建完成后运行 `./vermeer --env=master` 和 `./vermeer --env=worker`；`--env` 对应 `config/` 下的 INI 文件名。

## 二、任务创建类 rest api

### 2.1 简介

先创建 load 任务读取图，再创建 compute 任务。异步接口只返回创建结果，客户端需查询状态；同步接口等待任务结束。已加载的图可复用于多个计算任务。只有图处于 `loaded` 或 `error` 且没有计算任务时才能删除。

可以使用的 url 如下：

- 异步返回接口 POST http://master_ip:port/tasks/create 仅返回任务创建是否成功，需通过主动查询任务状态判断是否完成。
- 同步返回接口 POST http://master_ip:port/tasks/create/sync 在任务结束后返回。

### 2.2 加载图数据

参数定义见 [`vermeer/apps/options`](https://github.com/apache/hugegraph-computer/tree/master/vermeer/apps/options) 和各数据源在 [`vermeer/apps/graphio`](https://github.com/apache/hugegraph-computer/tree/master/vermeer/apps/graphio) 中的实现。

Vermeer 提供三种加载方式：

1. 从本地加载

可以预先获取数据集，例如 twitter-2010 数据集。获取方式：https://snap.stanford.edu/data/twitter-2010.html，第一个 twitter-2010.txt.gz 即可。

**request 示例：**

```javascript
POST http://localhost:6688/tasks/create
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

示例中的密码是占位值。不要把真实密码提交到配置文件或代码仓库。

```javascript
POST http://localhost:6688/tasks/create
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
POST http://localhost:6688/tasks/create
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

Vermeer 当前注册了 `local`、`hdfs` 和 `hugegraph` 输出方式。把对应参数放入请求的 `params`。设置 `output.need_statistics=1` 后，任务信息会包含统计结果；`count` 和 `modularity` 统计用于相应的社区发现算法。

输出参数定义见 [`vermeer/apps/options`](https://github.com/apache/hugegraph-computer/tree/master/vermeer/apps/options)，实现见 [`vermeer/apps/graphio`](https://github.com/apache/hugegraph-computer/tree/master/vermeer/apps/graphio)。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

当前注册的算法名为：`pagerank`、`ppr`、`betweenness_centrality`、`closeness_centrality`、`degree`、`louvain`、`louvain_weighted`、`lpa`、`slpa`、`wcc`、`scc`、`sssp`、`triangle_count`、`kcore`、`kout`、`clustering_coefficient`、`cycle_detection`、`jaccard` 和 `depth`。下面列出常用请求；未展开的参数以对应 `vermeer/algorithms/*.go` 实现为准。

### 3.1 PageRank

PageRank 根据节点之间的链接迭代计算分数。入边数量和来源节点的分数都会影响结果，可用于网页排序或图中的节点影响力分析。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

弱连通分量把忽略边方向后相互可达的顶点划入同一组，并输出每个顶点所属的分量 ID。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

标签传播通过相邻顶点间传播标签来划分社区。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

度中心性统计节点连接的边数。无向图返回度数；有向图可按边方向统计入度或出度。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

紧密中心性根据节点到其他可达节点的最短距离计算。值越大，节点越接近所在连通区域的中心。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

中介中心性（Betweenness Centrality）统计节点位于其他节点最短路径上的程度。值较高的节点往往连接图中的不同区域。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

三角形计数返回每个顶点参与的三角形数量。该实现按无向图处理，忽略边的方向。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

K-Core 反复移除当前度数小于 K 的顶点，得到每个剩余顶点度数至少为 K 的子图。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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
POST http://localhost:6688/tasks/create
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
POST http://localhost:6688/tasks/create
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

Louvain 根据模块度增量移动顶点，再将已形成的社区压缩为新顶点，重复计算直到模块度不再提升。

Vermeer 的 Louvain 实现受节点遍历顺序和并行调度影响。同一数据重复执行时，社区划分可能不同。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

Jaccard 相似系数根据两个邻居集合的交集与并集计算相似度。这里以给定源点为基准，计算它与其他顶点的系数。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

个性化 PageRank 从指定源点开始随机游走：以 `1-d` 的概率返回源点，以 `d` 的概率沿出边继续。运行前需在加载任务中设置 `load.use_out_degree=1`。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

### 3.14 集聚系数 clustering coefficient

局部聚类系数衡量一个顶点的邻居彼此连接的程度。

request 示例：

```javascript
POST http://localhost:6688/tasks/create
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

### 3.15 SCC（强连通分量）

强连通分量是有向图中任意两点相互可达的最大顶点集合。

```javascript
POST http://localhost:6688/tasks/create
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

其余算法可使用相同的计算任务结构，把 `compute.algorithm` 换成上方列出的注册名，并按实现提供所需参数。

