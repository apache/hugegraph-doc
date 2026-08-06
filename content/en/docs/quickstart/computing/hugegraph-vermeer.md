---
title: "HugeGraph-Vermeer Quick Start"
linkTitle: "Vermeer: Memory-First Computing Framework"
weight: 1
---

## 1. Overview of Vermeer

### 1.1 Architecture

Vermeer is a high-performance, memory-first graph computing framework written in `Go` (start once, execute any task), supporting ultra-fast computation of 15+ OLAP graph algorithms (most tasks complete in seconds to minutes), with master and worker roles. Currently, there is only one master (HA can be added), and there can be multiple workers.

The master is responsible for communication, forwarding, and aggregation, with minimal computation and resource usage. Workers are computation nodes used to store graph data and run computation tasks, consuming a large amount of memory and CPU. The grpc and rest modules handle internal communication and external calls, respectively.

The framework's runtime configuration can be passed via command-line parameters or specified in configuration files located in the `config/` directory. The `--env` parameter can specify which configuration file to use, e.g., `--env=master` specifies using `master.ini`. Note that the master needs to specify the listening port, and the worker needs to specify the listening port and the master's `ip:port`.

### 1.2 Running Method

1.  **Option 1: Docker Compose (Recommended)**

Please ensure that `docker-compose.yaml` exists in your project root directory. If it doesn't, here is an example:

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

Modify `docker-compose.yaml`

- **Volume**: For example, change both instances of `~/:/go/bin/config` to `/home/user/config:/go/bin/config` (or your own configuration directory).
- **Subnet**: Modify the subnet IP based on your actual situation. Note that the ports each container needs to access are specified in the config file. Please refer to the contents of the project's `config` folder for details.

Build the Image and Start in the Project Directory (or `docker build` first, then `docker-compose up`)

```shell
# Build the image (in the project root vermeer directory)
docker build -t hugegraph/vermeer .

# Start the services (in the vermeer root directory)
docker-compose up -d
# Or use the new CLI:
# docker compose up -d
```

View Logs / Stop / Remove

```shell
docker-compose logs -f
docker-compose down
```

2.  **Option 2: Start individually via `docker run` (Manually create network and assign static IP)**

Ensure the CONFIG_DIR has proper read/execute permissions for the Docker process.

Build the image:

```shell
docker build -t hugegraph/vermeer .
```

Create a custom bridge network (one-time operation):

```shell
docker network create --driver bridge \
  --subnet 172.20.0.0/24 \
  vermeer_network
```

Run master (adjust `CONFIG_DIR` to your **absolute** configuration path, and you can adjust the IP as needed based on your actual situation).

```shell
CONFIG_DIR=/home/user/config

docker run -d \
  --name vermeer-master \
  --network vermeer_network --ip 172.20.0.10 \
  -v ${CONFIG_DIR}:/go/bin/config \
  hugegraph/vermeer \
  --env=master
```

Run worker:

```shell
docker run -d \
  --name vermeer-worker \
  --network vermeer_network --ip 172.20.0.11 \
  -v ${CONFIG_DIR}:/go/bin/config \
  hugegraph/vermeer \
  --env=worker
```

View logs / Stop / Remove:

```shell
docker logs -f vermeer-master
docker logs -f vermeer-worker

docker stop vermeer-master vermeer-worker
docker rm vermeer-master vermeer-worker

# Remove the custom network (if needed)
docker network rm vermeer_network
```

3.  **Option 3: Build from Source**

Build. You can refer [Vermeer Readme](https://github.com/apache/hugegraph-computer/tree/master/vermeer).

```shell
go build
```

Enter the directory and input `./vermeer --env=master` or `./vermeer --env=worker01`.

## 2. Task Creation REST API

### 2.1 Introduction

This REST API provides all task creation functions, including reading graph data and various computation functions, offering both asynchronous and synchronous return interfaces. The returned content includes information about the created tasks. The overall process of using Vermeer is to first create a task to read the graph data, and after the graph is read, create a computation task to execute the computation. The graph will not be automatically deleted; multiple computation tasks can be run on one graph without repeated reading. If deletion is needed, the delete graph interface can be used. Task statuses can be divided into graph reading task status and computation task status. Generally, the client only needs to know four statuses: created, in progress, completed, and error. The graph status is the basis for determining whether the graph is available. If the graph is being read or the graph status is erroneous, the graph cannot be used to create computation tasks. The delete graph interface is only available when the graph is in the loaded or error status and has no computation tasks.

Available URLs are as follows:

- Asynchronous return interface: POST http://master_ip:port/tasks/create returns only whether the task creation is successful, and the task status needs to be actively queried to determine completion.
- Synchronous return interface: POST http://master_ip:port/tasks/create/sync returns after the task is completed.

### 2.2 Loading Graph Data

Refer to the Vermeer parameter list document for specific parameters.

Vermeer provides three ways to load data:

1. Load from Local Files

You can obtain the dataset in advance, such as the Twitter-2010 dataset. Acquisition method: https://snap.stanford.edu/data/twitter-2010.html The first Twitter-2010.text.gz is sufficient.

**Request Example:**

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

2. Load from HugeGraph

**Request Example:**

⚠️ Security Warning: Never store real passwords in configuration files or code. Use environment variables or a secure credential management system instead.

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

3. Load from HDFS

**Request Example:**

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

### 2.3 Output Computation Results

All Vermeer computation tasks support multiple result output methods, which can be customized: local, hdfs, afs, or hugegraph. Add the corresponding parameters under the params parameter when sending the request to take effect. When output.need_statistics is set to 1, it supports outputting statistical information of the computation results, which will be written in the interface task information. The statistical mode operators currently support "count" and "modularity," but only for community detection algorithms.

Refer to the Vermeer parameter list document for specific parameters.

Request example:

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

## 3. Supported Algorithms

### 3.1 PageRank

The PageRank algorithm, also known as the web ranking algorithm, is a technique used by search engines to calculate the relevance and importance of web pages (nodes) based on their mutual hyperlinks.

- If a web page is linked to by many other web pages, it indicates that the web page is relatively important, and its PageRank value will be relatively high.
- If a web page with a high PageRank value links to other web pages, the PageRank value of the linked web pages will also increase accordingly.

The PageRank algorithm is suitable for scenarios such as web page ranking and identifying key figures in social networks.

Request example:

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

### 3.2 WCC (Weakly Connected Components)

The weakly connected components algorithm calculates all connected subgraphs in an undirected graph and outputs the weakly connected subgraph ID to which each vertex belongs, indicating the connectivity between points and distinguishing different connected communities.

Request example:

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

### 3.3 LPA (Label Propagation Algorithm)

The label propagation algorithm is a graph clustering algorithm commonly used in social networks to discover potential communities.

Request example:

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

### 3.4 Degree Centrality

The degree centrality algorithm calculates the degree centrality value of each node in the graph, supporting both undirected and directed graphs. Degree centrality is an important indicator of node importance; the more edges a node has with other nodes, the higher its degree centrality value, and the more important the node is in the graph. In an undirected graph, degree centrality is calculated based on edge information to count the number of times a node appears, resulting in the degree centrality value of the node. In a directed graph, it is based on the direction of the edges, filtering based on input or output-edge information to count the number of times a node appears, resulting in the in-degree or out-degree value of the node. It indicates the importance of each point, with more important points having higher degrees.

Request example:

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

### 3.5 Closeness Centrality

Closeness centrality is used to calculate the inverse of the shortest distance from a node to all other reachable nodes, accumulating and normalizing the value. Closeness centrality can be used to measure the time it takes for information to be transmitted from the node to other nodes. The larger the closeness centrality of a node, the closer its position in the graph is to the center, suitable for scenarios such as identifying key nodes in social networks.

Request example:

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

### 3.6 Betweenness Centrality

The betweenness centrality algorithm determines the value of a node as a "bridge" node; the larger the value, the more likely it is to be a necessary path between two points in the graph. Typical examples include mutual followers in social networks. It is suitable for measuring the degree of aggregation around a node in a community.

Request example:

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

### 3.7 Triangle Count

The triangle count algorithm calculates the number of triangles passing through each vertex, suitable for calculating the relationships between users and whether the associations form triangles. The more triangles, the higher the degree of association between nodes in the graph, and the tighter the organizational relationship. In social networks, triangles indicate cohesive communities, and identifying triangles helps understand clustering and interconnections among individuals or groups in the network. In financial or transaction networks, the presence of triangles may indicate suspicious or fraudulent activities, and triangle counting can help identify transaction patterns that may require further investigation.

The output result is the Triangle Count corresponding to each vertex, i.e., the number of triangles the vertex is part of.

Note: This algorithm is for undirected graphs and ignores edge directions.

Request example:

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

The K-Core algorithm marks all vertices with a degree of K, suitable for graph pruning and finding the core part of the graph.

Request example:

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

### 3.9 SSSP (Single Source Shortest Path)

The single source the shortest path algorithm calculates the shortest distance from one point to all other points.

Request example:

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

Starting from a point, get the k-layer nodes of this point.

Request example:

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

The Louvain algorithm is a community detection algorithm based on modularity. The basic idea is that nodes in the network try to traverse all neighbor community labels and choose the community label that maximizes the modularity increment. After maximizing modularity, each community is regarded as a new node, and the process is repeated until the modularity no longer increases.

The distributed Louvain algorithm implemented on Vermeer is affected by factors such as node order and parallel computation. Due to the random traversal order of the Louvain algorithm, community compression also has a certain randomness, leading to different results in multiple executions. However, the overall trend will not change significantly.

Request example:

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

### 3.12 Jaccard Similarity Coefficient

The Jaccard index, also known as the Jaccard similarity coefficient, is used to compare the similarity and diversity between finite sample sets. The larger the Jaccard coefficient value, the higher the similarity of the samples. It is used to calculate the Jaccard similarity coefficient between a given source point and all other points in the graph.

Request example:

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

The goal of personalized PageRank is to calculate the relevance of all nodes relative to user u. Starting from the node corresponding to user u, at each node, there is a probability of 1-d to stop walking and start again from u, or a probability of d to continue walking, randomly selecting a node from the nodes pointed to by the current node to walk down. It is used to calculate the personalized PageRank score starting from a given starting point, suitable for scenarios such as social recommendations.

Since the calculation requires using out-degree, load.use_out_degree needs to be set to 1 when reading the graph.

Request example:

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

### 3.14 Global Kout

Calculate the k-degree neighbors of all nodes in the graph (excluding themselves and 1~k-1 degree neighbors). Due to the severe memory expansion of the global kout algorithm, k is currently limited to 1 and 2. Additionally, the global kout algorithm supports filtering functions (parameters such as "compute.filter":"risk_level==1"), and the filtering condition is judged when calculating the k-degree. The final result set includes those that meet the filtering condition. The algorithm's final output is the number of neighbors that meet the condition.

Request example:

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
 "compute.max_step":"2",
 "compute.filter":"risk_level==1"
 }
}
```

### 3.15 Clustering Coefficient

The clustering coefficient represents the coefficient of the clustering degree of nodes in a graph. In real networks, especially in specific networks, nodes tend to establish a tightly organized relationship due to relatively high-density connection points. The clustering coefficient algorithm (Cluster Coefficient) is used to calculate the clustering degree of nodes in the graph. This algorithm is for local clustering coefficients. The local clustering coefficient can measure the clustering degree around each node in the graph.

Request example:

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

### 3.16 SCC (Strongly Connected Components)

In the mathematical theory of directed graphs, if every vertex of a graph can be reached from any other point in the graph, the graph is said to be strongly connected. The parts of any directed graph that can achieve strong connectivity are called strongly connected components. It indicates the connectivity between points and distinguishes different connected communities.

Request example:

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

> 🚧, further updates and improvements will be made at any time. Suggestions and feedback are welcome.
```
