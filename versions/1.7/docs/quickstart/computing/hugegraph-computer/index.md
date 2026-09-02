# HugeGraph-Computer Quick Start

LLMS index: [llms.txt](/versions/1.7/llms.txt)

---

## 1 HugeGraph-Computer Overview

The [`HugeGraph-Computer`](https://github.com/apache/incubator-hugegraph-computer) is a distributed graph processing system for HugeGraph (OLAP). It is an implementation of [Pregel](https://kowshik.github.io/JPregel/pregel_paper.pdf). It runs on a Kubernetes(K8s) framework.(It focuses on supporting graph data volumes of hundreds of billions to trillions, using disk for sorting and acceleration, which is one of the biggest differences from Vermeer)

### Features

- Support distributed MPP graph computing, and integrates with HugeGraph as graph input/output storage.
- Based on the BSP (Bulk Synchronous Parallel) model, an algorithm performs computing through multiple parallel iterations; every iteration is a superstep.
- Auto memory management. The framework will never be OOM(Out of Memory) since it will split some data to disk if it doesn't have enough memory to hold all the data.
- The part of edges or the messages of super node can be in memory, so you will never lose it.
- You can load the data from HDFS or HugeGraph, or any other system.
- You can output the results to HDFS or HugeGraph, or any other system.
- Easy to develop a new algorithm. You just need to focus on vertex-only processing just like as in a single server, without worrying about message transfer and memory/storage management.

## 2 Dependency for Building/Running

### 2.1 Install Java 11 (JDK 11)

**Must** use ≥ `Java 11` to run `Computer`, and configure by yourself.

**Be sure to execute the `java -version` command to check the jdk version before reading**

## 3 Get Started

### 3.1 Run PageRank algorithm locally

> To run the algorithm with HugeGraph-Computer, you need to install Java 11 or later versions.
>
> You also need to deploy HugeGraph-Server and [Etcd](https://etcd.io/docs/v3.5/quickstart/).

There are two ways to get HugeGraph-Computer:

- Download the compiled tarball
- Clone source code then compile and package

#### 3.1.1 Download the compiled archive

Download the latest version of the HugeGraph-Computer release package:

```bash
wget https://downloads.apache.org/incubator/hugegraph/${version}/apache-hugegraph-computer-incubating-${version}.tar.gz
tar zxvf apache-hugegraph-computer-incubating-${version}.tar.gz -C hugegraph-computer
```

#### 3.1.2 Clone source code to compile and package

Clone the latest version of HugeGraph-Computer source package:

```bash
$ git clone https://github.com/apache/hugegraph-computer.git
```

Compile and generate tar package:

```bash
cd hugegraph-computer
mvn clean package -DskipTests
```

#### 3.1.3 Start master node

> You can use `-c`  parameter specify the configuration file, more computer config please see:[Computer Config Options](/versions/1.7/docs/config/config-computer#computer-config-options)

```bash
cd hugegraph-computer
bin/start-computer.sh -d local -r master
```

#### 3.1.4 Start worker node

```bash
bin/start-computer.sh -d local -r worker
```

#### 3.1.5 Query algorithm results

3.1.5.1 Enable `OLAP` index query for server

If the OLAP index is not enabled, it needs to be enabled. More reference: [modify-graphs-read-mode](/versions/1.7/docs/clients/restful-api/graphs/#634-modify-graphs-read-mode-this-operation-requires-administrator-privileges)

```http
PUT http://localhost:8080/graphs/hugegraph/graph_read_mode

"ALL"
```

3.1.5.2 Query `page_rank` property value:

```bash
curl "http://localhost:8080/graphs/hugegraph/graph/vertices?page&limit=3" | gunzip
```

### 3.2 Run PageRank algorithm in Kubernetes

> To run an algorithm with HugeGraph-Computer, you need to deploy HugeGraph-Server first

#### 3.2.1 Install HugeGraph-Computer CRD

```bash
# Kubernetes version >= v1.16
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer-k8s-operator/manifest/hugegraph-computer-crd.v1.yaml

# Kubernetes version < v1.16
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer-k8s-operator/manifest/hugegraph-computer-crd.v1beta1.yaml
```

#### 3.2.2 Show CRD

```bash
kubectl get crd

NAME                                        CREATED AT
hugegraphcomputerjobs.hugegraph.apache.org   2021-09-16T08:01:08Z
```

#### 3.2.3 Install hugegraph-computer-operator&etcd-server

```bash
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/master/computer-k8s-operator/manifest/hugegraph-computer-operator.yaml
```

#### 3.2.4 Wait for hugegraph-computer-operator&etcd-server deployment to complete

```bash
kubectl get pod -n hugegraph-computer-operator-system

NAME                                                              READY   STATUS    RESTARTS   AGE
hugegraph-computer-operator-controller-manager-58c5545949-jqvzl   1/1     Running   0          15h
hugegraph-computer-operator-etcd-28lm67jxk5                       1/1     Running   0          15h
```

#### 3.2.5 Submit a job

> More computer crd please see: [Computer CRD](/versions/1.7/docs/config/config-computer#hugegraph-computer-crd)
>
> More computer config please see: [Computer Config Options](/versions/1.7/docs/config/config-computer#computer-config-options)

```yaml
cat <<EOF | kubectl apply --filename -
apiVersion: hugegraph.apache.org/v1
kind: HugeGraphComputerJob
metadata:
  namespace: hugegraph-computer-operator-system
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

#### 3.2.6 Show job

```bash
kubectl get hcjob/pagerank-sample -n hugegraph-computer-operator-system

NAME               JOBID              JOBSTATUS
pagerank-sample    pagerank-sample    RUNNING
```

#### 3.2.7 Show log of nodes

```bash
# Show the master log
kubectl logs -l component=pagerank-sample-master -n hugegraph-computer-operator-system

# Show the worker log
kubectl logs -l component=pagerank-sample-worker -n hugegraph-computer-operator-system

# Show diagnostic log of a job
# NOTE: diagnostic log exist only when the job fails, and it will only be saved for one hour.
kubectl get event --field-selector reason=ComputerJobFailed --field-selector involvedObject.name=pagerank-sample -n hugegraph-computer-operator-system
```

#### 3.2.8 Show success event of a job

> NOTE: it will only be saved for one hour

```bash
kubectl get event --field-selector reason=ComputerJobSucceed --field-selector involvedObject.name=pagerank-sample -n hugegraph-computer-operator-system
```

#### 3.2.9 Query algorithm results

If the output to `Hugegraph-Server` is consistent with Locally, if output to `HDFS`, please check the result file in the directory of `/hugegraph-computer/results/{jobId}` directory.

## 4. Built-In algorithms document

### 4.1 Supported algorithms list:

###### Centrality Algorithm:

* PageRank
* BetweennessCentrality
* ClosenessCentrality
* DegreeCentrality

###### Community Algorithm:

* ClusteringCoefficient
* Kcore
* Lpa
* TriangleCount
* Wcc

###### Path Algorithm:

* RingsDetection
* RingsDetectionWithFilter

More algorithms please see: [Built-In algorithms](https://github.com/apache/hugegraph-computer/tree/master/computer-algorithm/src/main/java/org/apache/hugegraph/computer/algorithm)

### 4.2 Algorithm describe

TODO

## 5 Algorithm development guide

TODO

## 6 Note

- If some classes under computer-k8s cannot be found, you need to execute `mvn compile` in advance to generate corresponding classes.
