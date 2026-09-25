# HugeGraph-Computer Quick Start

LLMS 索引： [llms.txt](/versions/1.0/cn/llms.txt)

---

## 1 HugeGraph-Computer 概述

[`HugeGraph-Computer`](https://github.com/apache/incubator-hugegraph-computer) 是分布式图处理系统 (OLAP). 它是 [Pregel](https://kowshik.github.io/JPregel/pregel_paper.pdf) 的一个实现. 它可以运行在 Kubernetes 上。

### 特性

- 支持分布式MPP图计算，集成HugeGraph作为图输入输出存储。
- 算法基于BSP(Bulk Synchronous Parallel)模型，通过多次并行迭代进行计算，每一次迭代都是一次超步。
- 自动内存管理。该框架永远不会出现 OOM（内存不足），因为如果它没有足够的内存来容纳所有数据，它会将一些数据拆分到磁盘。
- 边的部分或超级节点的消息可以在内存中，所以你永远不会丢失它。
- 您可以从 HDFS 或 HugeGraph 或任何其他系统加载数据。
- 您可以将结果输出到 HDFS 或 HugeGraph，或任何其他系统。
- 易于开发新算法。您只需要像在单个服务器中一样专注于仅顶点处理，而不必担心消息传输和内存存储管理。

## 2 开始

### 2.1 在本地运行 PageRank 算法

> 要使用 HugeGraph-Computer 运行算法，您需要安装 64 位 JREJDK 11 或更高版本。
>
> 还需要首先部署 HugeGraph-Server 和 [Etcd](https://etcd.io/docs/v3.5/quickstart/).

有两种方式可以获取 HugeGraph-Computer：

- 下载已编译的压缩包
- 克隆源码编译打包

#### 2.1 Download the compiled archive

下载最新版本的 HugeGraph-Computer release 包：

```bash
wget https://github.com/apache/hugegraph-computer/releases/download/v${version}/hugegraph-loader-${version}.tar.gz
tar zxvf hugegraph-computer-${version}.tar.gz
```

#### 2.2 Clone source code to compile and package

克隆最新版本的 HugeGraph-Computer 源码包：

```bash
$ git clone https://github.com/apache/hugegraph-computer.git
```

编译生成tar包:

```bash
cd hugegraph-computer
mvn clean package -DskipTests
```

#### 2.3 启动 master 节点

> 您可以使用 `-c` 参数指定配置文件, 更多computer 配置请看: [Computer Config Options](/versions/1.0/docs/config/config-computer#computer-config-options)

```bash
cd hugegraph-computer-${version}
bin/start-computer.sh -d local -r master
```

#### 2.4 启动 worker 节点

```
bin/start-computer.sh -d local -r worker
```

#### 2.5 查询算法结果

2.5.1 为 server 启用 `OLAP` 索引查询

如果没有启用OLAP索引，则需要启用, 更多参考: [modify-graphs-read-mode](/versions/1.0/docs/clients/restful-api/graphs/#634-modify-graphs-read-mode-this-operation-requires-administrator-privileges)

```http
PUT http://localhost:8080/graphs/hugegraph/graph_read_mode

"ALL"
```

2.5.2 查询 `page_rank` 属性值:

```bash
curl "http://localhost:8080/graphs/hugegraph/graph/vertices?page&limit=3" | gunzip
```

### 2.2 在 Kubernetes 中运行 PageRank 算法

> 要使用 HugeGraph-Computer 运行算法，您需要先部署 HugeGraph-Server

#### 2.2.1 安装 HugeGraph-Computer CRD

```bash
# Kubernetes version >= v1.16
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer-k8s-operator/manifest/hugegraph-computer-crd.v1.yaml

# Kubernetes version < v1.16
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer-k8s-operator/manifest/hugegraph-computer-crd.v1beta1.yaml
```

#### 2.2.2 显示 CRD

```bash
kubectl get crd

NAME                                        CREATED AT
hugegraphcomputerjobs.hugegraph.apache.org   2021-09-16T08:01:08Z
```

#### 2.2.3 安装 hugegraph-computer-operator&etcd-server

```bash
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer-k8s-operator/manifest/hugegraph-computer-operator.yaml
```

#### 2.2.4 等待 hugegraph-computer-operator&etcd-server 部署完成

```bash
kubectl get pod -n hugegraph-computer-operator-system

NAME                                                              READY   STATUS    RESTARTS   AGE
hugegraph-computer-operator-controller-manager-58c5545949-jqvzl   1/1     Running   0          15h
hugegraph-computer-operator-etcd-28lm67jxk5                       1/1     Running   0          15h
```

#### 2.2.5 提交作业

> 更多 computer crd spec 请看: [Computer CRD](/versions/1.0/docs/config/config-computer#hugegraph-computer-crd)
>
> 更多 Computer 配置请看: [Computer Config Options](/versions/1.0/docs/config/config-computer#computer-config-options)

```yaml
cat <<EOF | kubectl apply --filename -
apiVersion: hugegraph.apache.org/v1
kind: HugeGraphComputerJob
metadata:
  namespace: hugegraph-computer-system
  name: &jobName pagerank-sample
spec:
  jobId: *jobName
  algorithmName: page_rank
  image: hugegraph/hugegraph-computer:latest # algorithm image url
  jarFile: /hugegraph/hugegraph-computer/algorithm/builtin-algorithm.jar # algorithm jar path
  pullPolicy: Always
  workerCpu: "4"
  workerMemory: "4Gi"
  workerInstances: 5
  computerConf:
    job.partitions_count: "20"
    algorithm.params_class: org.apache.hugegraph.computer.algorithm.centrality.pagerank.PageRankParams
    hugegraph.url: http://${hugegraph-server-host}:${hugegraph-server-port} # hugegraph server url
    hugegraph.name: hugegraph # hugegraph graph name
EOF
```

#### 2.2.6 显示作业

```bash
kubectl get hcjob/pagerank-sample -n hugegraph-computer-system

NAME               JOBID              JOBSTATUS
pagerank-sample    pagerank-sample    RUNNING
```

#### 2.2.7 显示节点日志

```bash
# Show the master log
kubectl logs -l component=pagerank-sample-master -n hugegraph-computer-system

# Show the worker log
kubectl logs -l component=pagerank-sample-worker -n hugegraph-computer-system

# Show diagnostic log of a job
# 注意: 诊断日志仅在作业失败时存在，并且只会保存一小时。
kubectl get event --field-selector reason=ComputerJobFailed --field-selector involvedObject.name=pagerank-sample -n hugegraph-computer-system
```

#### 2.2.8 显示作业的成功事件

> NOTE: it will only be saved for one hour

```bash
kubectl get event --field-selector reason=ComputerJobSucceed --field-selector involvedObject.name=pagerank-sample -n hugegraph-computer-system
```

#### 2.2.9 查询算法结果

如果输出到 `Hugegraph-Server` 则与 Locally 模式一致，如果输出到 `HDFS` ，请检查 `hugegraph-computerresults{jobId}`目录下的结果文件。

## 3 内置算法文档

### 3.1 支持的算法列表:

###### 中心性算法:

* PageRank
* BetweennessCentrality
* ClosenessCentrality
* DegreeCentrality

###### 社区算法:

* ClusteringCoefficient
* Kcore
* Lpa
* TriangleCount
* Wcc

###### 路径算法:

* RingsDetection
* RingsDetectionWithFilter

更多算法请看: [Built-In algorithms](https://github.com/apache/hugegraph-computer/tree/master/computer-algorithm/src/main/java/org/apache/hugegraph/computer/algorithm)

### 3.2 算法描述

TODO

## 4 算法开发指南

TODO
