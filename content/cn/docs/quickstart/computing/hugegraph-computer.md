---
title: "HugeGraph-Computer 快速入门"
linkTitle: "使用 Computer 进行 OLAP 分析"
weight: 2
---

HugeGraph-Computer 是实现 Pregel/BSP 模型的分布式图处理框架，可运行在 Kubernetes、YARN 或本地进程中。它从 HugeGraph 或 Loader 数据读取图，计算过程中可把超出内存阈值的数据落盘，结果可写回 HugeGraph 或 HDFS。

## 环境要求

- JDK 11 或更高版本
- Maven 3.5 或更高版本
- HugeGraph Server
- etcd，用于 BSP 节点协调

集成测试还依赖 HDFS、Kubernetes 和 HugeGraph；普通源码编译不需要启动整套测试环境。

## 从源码构建

```bash
git clone https://github.com/apache/hugegraph-computer.git
cd hugegraph-computer/computer

# 编译
mvn clean compile -Dmaven.javadoc.skip=true

# 生成分发包
mvn clean package -DskipTests
```

分发内容由 `computer-dist` 模块生成，包含 `bin/start-computer.sh`、`conf/computer.properties`、依赖库和内置算法 JAR。

## 本地运行 PageRank

> 您可以使用 `-c` 参数指定配置文件，更多 computer 配置请看：[Computer Config Options](/cn/docs/quickstart/computing/hugegraph-computer-config#computer-配置选项)

先启动 HugeGraph Server 和 etcd。然后在分发目录编辑 `conf/computer.properties`：

```properties
job.id=local_001
job.workers_count=1

transport.server_host=127.0.0.1
transport.server_port=0
rpc.server_host=127.0.0.1
rpc.server_port=8190

bsp.etcd_endpoints=http://127.0.0.1:2379
bsp.max_super_step=20

hugegraph.url=http://127.0.0.1:8080
hugegraph.name=hugegraph
hugegraph.username=
hugegraph.password=

algorithm.params_class=org.apache.hugegraph.computer.algorithm.centrality.pagerank.PageRankParams
```

分别在两个终端启动 master 和 worker。启动脚本以前台进程运行，第一条命令不会自行返回：

```bash
bin/start-computer.sh -d local -r master
bin/start-computer.sh -d local -r worker
```

脚本还支持：

- `-c, --conf`：指定 properties 文件。
- `-a, --algorithm`：加入自定义算法 JAR。
- `-l, --log4`：指定 Log4j2 配置。
- `-d, --drive`：选择 `local`、`k8s` 或 `yarn`。
- `-r, --role`：选择 `master` 或 `worker`。

如果没有启用 OLAP 索引，则需要启用，更多参考：[modify-graphs-read-mode](/cn/docs/clients/restful-api/graphs/#634-设置某个图的读模式该操作需要管理员权限)

计算结果写回 HugeGraph OLAP 属性后，需要让 Server 的图读取模式包含 OLAP 数据，再查询对应属性。具体写回类和属性名由算法参数及 `output.*` 配置决定。

## 在 Kubernetes 中提交作业

仓库提供 v1 和 v1beta1 两份 CRD。Kubernetes 1.16 及以上版本使用 v1：

```bash
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer/computer-k8s-operator/manifest/hugegraph-computer-crd.v1.yaml
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer/computer-k8s-operator/manifest/hugegraph-computer-operator.yaml
```

### 3.2 在 Kubernetes 中运行 PageRank 算法

> 要使用 HugeGraph-Computer 运行算法，您需要先部署 HugeGraph-Server

#### 3.2.1 安装 HugeGraph-Computer CRD

```bash
# Kubernetes version >= v1.16
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer-k8s-operator/manifest/hugegraph-computer-crd.v1.yaml

# Kubernetes version < v1.16
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer-k8s-operator/manifest/hugegraph-computer-crd.v1beta1.yaml
```

#### 3.2.2 显示 CRD

```bash
kubectl get crd

NAME                                        CREATED AT
hugegraphcomputerjobs.hugegraph.apache.org   2021-09-16T08:01:08Z
```

#### 3.2.3 安装 hugegraph-computer-operator&etcd-server

```bash
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer-k8s-operator/manifest/hugegraph-computer-operator.yaml
```

#### 3.2.4 等待 hugegraph-computer-operator&etcd-server 部署完成

```bash
kubectl get pod -n hugegraph-computer-operator-system

NAME                                                              READY   STATUS    RESTARTS   AGE
hugegraph-computer-operator-controller-manager-58c5545949-jqvzl   1/1     Running   0          15h
hugegraph-computer-operator-etcd-28lm67jxk5                       1/1     Running   0          15h
```

#### 3.2.5 提交作业

> 更多 computer crd spec 请看：[Computer CRD](/docs/quickstart/computing/hugegraph-computer-config#hugegraph-computer-crd)
>
> 更多 Computer 配置请看：[Computer Config Options](/cn/docs/quickstart/computing/hugegraph-computer-config#computer-配置选项)

提交 PageRank 示例：

```yaml
apiVersion: hugegraph.apache.org/v1
kind: HugeGraphComputerJob
metadata:
  namespace: hugegraph-computer-operator-system
  name: pagerank-sample
spec:
  jobId: pagerank-sample
  algorithmName: page_rank
  image: hugegraph/hugegraph-computer:latest
  jarFile: /hugegraph/hugegraph-computer/algorithm/builtin-algorithm.jar
  pullPolicy: Always
  workerCpu: "4"
  workerMemory: "4Gi"
  workerInstances: 5
  computerConf:
    job.partitions_count: "20"
    algorithm.params_class: org.apache.hugegraph.computer.algorithm.centrality.pagerank.PageRankParams
    hugegraph.url: http://hugegraph-server:8080
    hugegraph.name: hugegraph
```

查看作业和日志：

```bash
kubectl get hcjob/pagerank-sample -n hugegraph-computer-operator-system
kubectl logs -l component=pagerank-sample-master \
  -n hugegraph-computer-operator-system
kubectl logs -l component=pagerank-sample-worker \
  -n hugegraph-computer-operator-system
```

## 内置算法

`computer-algorithm` 当前包含：

- 中心性：PageRank、Betweenness Centrality、Closeness Centrality、Degree Centrality。
- 社区与结构：Clustering Coefficient、K-core、LPA、Triangle Count、WCC。
- 路径与采样：Rings Detection、带过滤的 Rings Detection、Single Source Shortest Path、Random Walk。

完整类清单以 [`computer-algorithm`](https://github.com/apache/hugegraph-computer/tree/master/computer/computer-algorithm/src/main/java/org/apache/hugegraph/computer/algorithm) 为准。

## 开发和测试

```bash
cd hugegraph-computer/computer
mvn test -P unit-test
mvn apache-rat:check
```

K8s 模块依赖 operator 生成的 CRD 类。相关类不存在时，先在 `computer-k8s-operator` 模块执行 `mvn clean install`，而不是只运行 `mvn compile`。

所有配置键及代码默认值见 [Computer 配置参考](./hugegraph-computer-config.md)。
