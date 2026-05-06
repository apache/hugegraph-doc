---
title: "HugeGraph-Computer Quick Start"
linkTitle: "Analysis with HugeGraph-Computer"
weight: 2
---

## 1 HugeGraph-Computer Overview

The [`HugeGraph-Computer`](https://github.com/apache/hugegraph-computer) is a distributed graph processing system for HugeGraph (OLAP). It is an implementation of [Pregel](https://kowshik.github.io/JPregel/pregel_paper.pdf). It runs on a Kubernetes(K8s) framework.(It focuses on supporting graph data volumes of hundreds of billions to trillions, using disk for sorting and acceleration, which is one of the biggest differences from Vermeer)

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
wget https://downloads.apache.org/hugegraph/${version}/apache-hugegraph-computer-incubating-${version}.tar.gz
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

#### 3.1.3 Configure computer.properties

Edit `conf/computer.properties` to configure the connection to HugeGraph-Server and etcd:

```properties
# Job configuration
job.id=local_pagerank_001
job.partitions_count=4

# HugeGraph connection (✅ Correct configuration keys)
hugegraph.url=http://localhost:8080
hugegraph.name=hugegraph
# If authentication is enabled on HugeGraph-Server
hugegraph.username=
hugegraph.password=

# BSP coordination (✅ Correct key: bsp.etcd_endpoints)
bsp.etcd_endpoints=http://localhost:2379
bsp.max_super_step=10

# Algorithm parameters (⚠️ Required)
algorithm.params_class=org.apache.hugegraph.computer.algorithm.centrality.pagerank.PageRankParams
```

> **Important Configuration Notes:**
> - Use `bsp.etcd_endpoints` (NOT `bsp.etcd.url`) for etcd connection
> - `algorithm.params_class` is required for all algorithms
> - For multiple etcd endpoints, use comma-separated list: `http://host1:2379,http://host2:2379`

#### 3.1.4 Start master node

> You can use `-c`  parameter specify the configuration file, more computer config please see:[Computer Config Options](/docs/quickstart/computing/hugegraph-computer-config#computer-config-options)

```bash
cd hugegraph-computer
bin/start-computer.sh -d local -r master
```

#### 3.1.5 Start worker node

```bash
bin/start-computer.sh -d local -r worker
```

#### 3.1.6 Query algorithm results

3.1.6.1 Enable `OLAP` index query for server

If the OLAP index is not enabled, it needs to be enabled. More reference: [modify-graphs-read-mode](/docs/clients/restful-api/graphs/#634-modify-graphs-read-mode-this-operation-requires-administrator-privileges)

```http
PUT http://localhost:8080/graphs/hugegraph/graph_read_mode

"ALL"
```

3.1.6.2 Query `page_rank` property value:

```bash
curl "http://localhost:8080/graphs/hugegraph/graph/vertices?page&limit=3" | gunzip
```

---

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

> More computer crd please see: [Computer CRD](/docs/quickstart/computing/hugegraph-computer-config#hugegraph-computer-crd)
>
> More computer config please see: [Computer Config Options](/docs/quickstart/computing/hugegraph-computer-config#computer-config-options)

**Basic Example:**

```yaml
cat <<EOF | kubectl apply --filename -
apiVersion: hugegraph.apache.org/v1
kind: HugeGraphComputerJob
metadata:
  namespace: hugegraph-computer-operator-system
  name: &jobName pagerank-sample
spec:
  jobId: *jobName
  algorithmName: page_rank  # ✅ Correct: use underscore format (matches algorithm implementation)
  image: hugegraph/hugegraph-computer:latest
  jarFile: /hugegraph/hugegraph-computer/algorithm/builtin-algorithm.jar
  pullPolicy: Always
  workerCpu: "4"
  workerMemory: "4Gi"
  workerInstances: 5
  computerConf:
    job.partitions_count: "20"
    algorithm.params_class: org.apache.hugegraph.computer.algorithm.centrality.pagerank.PageRankParams
    hugegraph.url: http://${hugegraph-server-host}:${hugegraph-server-port}
    hugegraph.name: hugegraph
EOF
```

**Complete Example with Advanced Features:**

```yaml
cat <<EOF | kubectl apply --filename -
apiVersion: hugegraph.apache.org/v1
kind: HugeGraphComputerJob
metadata:
  namespace: hugegraph-computer-operator-system
  name: &jobName pagerank-advanced
spec:
  jobId: *jobName
  algorithmName: page_rank  # ✅ Correct: underscore format
  image: hugegraph/hugegraph-computer:latest
  jarFile: /hugegraph/hugegraph-computer/algorithm/builtin-algorithm.jar
  pullPolicy: Always

  # Resource limits
  masterCpu: "2"
  masterMemory: "2Gi"
  workerCpu: "4"
  workerMemory: "4Gi"
  workerInstances: 5

  # JVM options
  jvmOptions: "-Xmx3g -Xms3g -XX:+UseG1GC"

  # Environment variables (optional)
  envVars:
    - name: REMOTE_JAR_URI
      value: "http://example.com/custom-algorithm.jar"  # Download custom algorithm JAR
    - name: LOG_LEVEL
      value: "INFO"

  # Computer configuration
  computerConf:
    # Job settings
    job.partitions_count: "20"

    # Algorithm parameters (⚠️ Required)
    algorithm.params_class: org.apache.hugegraph.computer.algorithm.centrality.pagerank.PageRankParams
    page_rank.alpha: "0.85"  # PageRank damping factor

    # HugeGraph connection
    hugegraph.url: http://hugegraph-server:8080
    hugegraph.name: hugegraph
    hugegraph.username: ""  # Fill if authentication is enabled
    hugegraph.password: ""

    # BSP configuration (⚠️ System-managed in K8s, do not override)
    # bsp.etcd_endpoints is automatically set by operator
    bsp.max_super_step: "20"
    bsp.log_interval: "30000"

    # Snapshot configuration (optional)
    snapshot.write: "true"       # Enable snapshot writing
    snapshot.load: "false"       # Do not load from snapshot this time
    snapshot.name: "pagerank-snapshot-v1"
    snapshot.minio_endpoint: "http://minio:9000"
    snapshot.minio_access_key: "minioadmin"
    snapshot.minio_secret_key: "minioadmin"
    snapshot.minio_bucket_name: "hugegraph-snapshots"

    # Output configuration
    output.result_name: "page_rank"
    output.batch_size: "500"
    output.with_adjacent_edges: "false"
EOF
```

**Configuration Notes:**

| Configuration Key | ⚠️ Important Notes |
|-------------------|-------------------|
| `algorithmName` | Must use `page_rank` (underscore format), matches the algorithm's `name()` method return value |
| `bsp.etcd_endpoints` | **System-managed in K8s** - automatically set by operator, do not override in `computerConf` |
| `algorithm.params_class` | **Required** - must specify for all algorithms |
| `REMOTE_JAR_URI` | Optional environment variable to download custom algorithm JAR from remote URL |
| `snapshot.*` | Optional - enable snapshots for checkpoint recovery or repeated computations |

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

---

## 3.3 Local Mode vs Kubernetes Mode

Understanding the differences helps you choose the right deployment mode for your use case.

| Feature | Local Mode | Kubernetes Mode |
|---------|------------|-----------------|
| **Configuration** | `conf/computer.properties` file | CRD YAML `computerConf` field |
| **Etcd Management** | Manual deployment of external etcd | Operator auto-deploys etcd StatefulSet |
| **Worker Scaling** | Manual start of multiple processes | CRD `workerInstances` field auto-scales |
| **Resource Isolation** | Shared host resources | Pod-level CPU/Memory limits |
| **Remote JAR** | `JAR_FILE_PATH` environment variable | CRD `remoteJarUri` or `envVars.REMOTE_JAR_URI` |
| **Log Viewing** | Local `logs/` directory | `kubectl logs` command |
| **Fault Recovery** | Manual process restart | K8s auto-restarts failed pods |
| **Use Cases** | Development, testing, small datasets | Production, large-scale data |

**Local Mode Prerequisites:**
- Java 11+
- HugeGraph-Server running on localhost:8080
- Etcd running on localhost:2379

**K8s Mode Prerequisites:**
- Kubernetes cluster (version 1.16+)
- HugeGraph-Server accessible from cluster
- HugeGraph-Computer Operator installed

**Configuration Key Differences:**

```properties
# Local Mode (computer.properties)
bsp.etcd_endpoints=http://localhost:2379  # ✅ User-configured
job.workers_count=4                        # User-configured
```

```yaml
# K8s Mode (CRD)
spec:
  workerInstances: 5  # Overrides job.workers_count
  computerConf:
    # bsp.etcd_endpoints is auto-set by operator, do NOT configure
    job.partitions_count: "20"
```

---

## 3.4 Common Troubleshooting

### 3.4.1 Configuration Errors

**Error: "Failed to connect to etcd"**

**Symptoms:** Master or Worker cannot connect to etcd

**Local Mode Solutions:**
```bash
# Check configuration key name (common mistake)
grep "bsp.etcd_endpoints" conf/computer.properties
# Should output: bsp.etcd_endpoints=http://localhost:2379

# ❌ WRONG: bsp.etcd.url (old/incorrect key)
# ✅ CORRECT: bsp.etcd_endpoints

# Test etcd connectivity
curl http://localhost:2379/version
```

**K8s Mode Solutions:**
```bash
# Check Operator etcd service
kubectl get svc hugegraph-computer-operator-etcd -n hugegraph-computer-operator-system

# Verify etcd pod is running
kubectl get pods -n hugegraph-computer-operator-system -l app=hugegraph-computer-operator-etcd
# Should show: Running status

# Test connectivity from worker pod
kubectl exec -it pagerank-sample-worker-0 -n hugegraph-computer-operator-system -- \
  curl http://hugegraph-computer-operator-etcd:2379/version
```

**Error: "Algorithm class not found"**

**Symptoms:** Cannot find algorithm implementation class

**Cause:** Incorrect `algorithmName` format

```yaml
# ❌ WRONG formats:
algorithmName: pageRank   # Camel case
algorithmName: PageRank   # Title case

# ✅ CORRECT format (matches PageRank.name() return value):
algorithmName: page_rank  # Underscore lowercase
```

**Verification:**
```bash
# Check algorithm implementation in source code
# File: computer-algorithm/.../PageRank.java
# Method: public String name() { return "page_rank"; }
```

**Error: "Required option 'algorithm.params_class' is missing"**

**Solution:**
```yaml
computerConf:
  algorithm.params_class: org.apache.hugegraph.computer.algorithm.centrality.pagerank.PageRankParams  # ⚠️ Required
```

### 3.4.2 K8s Deployment Issues

**Issue: REMOTE_JAR_URI not working**

**Solution:**
```yaml
spec:
  envVars:
    - name: REMOTE_JAR_URI
      value: "http://example.com/my-algorithm.jar"
```

**Issue: Etcd connection timeout in K8s**

**Check Operator etcd:**
```bash
# Verify etcd is running
kubectl get pods -n hugegraph-computer-operator-system -l app=hugegraph-computer-operator-etcd
# Should show: Running

# From worker pod, test etcd connectivity
kubectl exec -it pagerank-sample-worker-0 -n hugegraph-computer-operator-system -- \
  curl http://hugegraph-computer-operator-etcd:2379/version
```

**Issue: Snapshot/MinIO configuration problems**

**Verify MinIO service:**
```bash
# Test MinIO reachability
kubectl run -it --rm debug --image=alpine --restart=Never -- sh
wget -O- http://minio:9000/minio/health/live

# Test bucket permissions (requires MinIO client)
mc config host add myminio http://minio:9000 minioadmin minioadmin
mc ls myminio/hugegraph-snapshots
```

### 3.4.3 Job Status Checks

**Check job overall status:**
```bash
kubectl get hcjob pagerank-sample -n hugegraph-computer-operator-system
# Output example:
# NAME              JOBSTATUS   SUPERSTEP   MAXSUPERSTEP   SUPERSTEPSTAT
# pagerank-sample   Running     5           20             COMPUTING
```

**Check detailed events:**
```bash
kubectl describe hcjob pagerank-sample -n hugegraph-computer-operator-system
```

**Check failure reasons:**
```bash
kubectl get events --field-selector reason=ComputerJobFailed \
  --field-selector involvedObject.name=pagerank-sample \
  -n hugegraph-computer-operator-system
```

**Real-time master logs:**
```bash
kubectl logs -f -l component=pagerank-sample-master -n hugegraph-computer-operator-system
```

**All worker logs:**
```bash
kubectl logs -l component=pagerank-sample-worker -n hugegraph-computer-operator-system --all-containers=true
```

---

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
