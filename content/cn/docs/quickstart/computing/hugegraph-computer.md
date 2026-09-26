---
title: "HugeGraph-Computer 快速开始"
linkTitle: "使用 Computer 进行 OLAP 分析"
weight: 2
search_keywords: [HugeGraph Computer, 图计算, OLAP]
search_boost: 1.6
---

## 1. 组件说明

[`HugeGraph-Computer`](https://github.com/apache/hugegraph-computer) 是基于 BSP（Bulk Synchronous Parallel，批量同步并行）模型的 Java 分布式图计算框架，算法按超步迭代运行。它可由 Kubernetes Operator 或 YARN 调度，也可在单机上启动 master 和 worker 进程进行小规模试跑。

它与同一仓库中的 Vermeer 是两套实现：Computer 使用 Java/BSP 运行时，面向分布式计算；Vermeer 是 Go 实现的内存图计算平台，采用 master-worker 结构。两者共享 HugeGraph 数据源，但部署和任务配置不能互换。

Computer 支持从 HugeGraph 或 HDFS 读取图数据，并可将结果写回 HugeGraph 或 HDFS。运行时可把部分数据溢写到磁盘；能否完成任务仍取决于输入规模、资源和配置，不应把溢写能力理解为不受资源限制。

## 2. 前置条件与连接

构建和运行需要 JDK 11 或更高版本。源码构建还需要 Maven 3.5 或更高版本。PageRank 示例要求一个已启动且包含待计算图数据的 HugeGraph-Server，以及可供 master、worker 访问的 etcd。

| 服务 | 示例地址或端口 | 用途 |
|------|----------------|------|
| HugeGraph-Server | `http://127.0.0.1:8080` | 读取图数据并写回算法结果；以 `hugegraph.url` 为准。 |
| etcd | `http://127.0.0.1:2379` | BSP 作业协调；以 `bsp.etcd_endpoints` 为准。 |
| Computer master RPC | TCP `8190` | worker 连接 master；发行配置中的端口。 |
| Computer worker 数据传输 | 本地默认由系统分配；K8s Operator 默认 `8099` | worker 之间传输顶点和消息。跨主机时需保证公告地址和端口可达。 |
| HDFS | 按集群配置 | 仅当输入或输出配置为 HDFS 时需要。 |

Kubernetes 作业中的 `hugegraph.url` 必须是各计算 Pod 都能访问的地址，不能填仅在个人电脑上可用的 `localhost`。如果启用了 HugeGraph 认证，应在配置中填写用户名和密码，并为 REST 查询使用对应凭据。

更多配置项见[Computer 配置参考](/cn/docs/quickstart/computing/hugegraph-computer-config/)。

## 3. 获取源码并构建发行包

Apache 1.7.0 发行目录提供 Computer 源码包 `apache-hugegraph-computer-incubating-1.7.0-src.tar.gz`，不是单独的预编译 Computer 二进制包。下载时同时取得同目录下的 `.sha512` 和 `.asc` 文件。首次验签前还需取得 Apache 项目 [`KEYS`](https://downloads.apache.org/hugegraph/KEYS) 并导入公钥；应先核对密钥指纹来自 Apache 项目发布渠道，再验证签名。后续版本请从 [Apache HugeGraph 下载目录](https://downloads.apache.org/hugegraph/)选择与运行环境匹配的版本。

```bash
curl -fLO https://downloads.apache.org/hugegraph/1.7.0/apache-hugegraph-computer-incubating-1.7.0-src.tar.gz
curl -fLO https://downloads.apache.org/hugegraph/1.7.0/apache-hugegraph-computer-incubating-1.7.0-src.tar.gz.sha512
curl -fLO https://downloads.apache.org/hugegraph/1.7.0/apache-hugegraph-computer-incubating-1.7.0-src.tar.gz.asc
curl -fLO https://downloads.apache.org/hugegraph/KEYS
shasum -a 512 -c apache-hugegraph-computer-incubating-1.7.0-src.tar.gz.sha512
gpg --import KEYS
gpg --verify apache-hugegraph-computer-incubating-1.7.0-src.tar.gz.asc apache-hugegraph-computer-incubating-1.7.0-src.tar.gz
tar -xzf apache-hugegraph-computer-incubating-1.7.0-src.tar.gz
cd apache-hugegraph-computer-incubating-1.7.0-src/computer
mvn clean package -DskipTests
tar -xzf target/apache-hugegraph-computer-1.7.0.tar.gz
cd apache-hugegraph-computer-1.7.0
```

也可以克隆源码后从 Maven 聚合工程目录构建：

```bash
git clone https://github.com/apache/hugegraph-computer.git
cd hugegraph-computer/computer
mvn clean package -DskipTests
tar -xzf target/apache-hugegraph-computer-1.7.0.tar.gz
cd apache-hugegraph-computer-1.7.0
```

发行包由 `computer/computer-dist` 组装，包含 `bin/start-computer.sh`、运行依赖 `lib/`、内置算法 `algorithm/builtin-algorithm.jar` 及默认配置 `conf/computer.properties`、`conf/log4j2.xml`。源码默认配置位于 `computer/computer-dist/src/assembly/static/conf/computer.properties`。在 Maven 聚合工程 `computer/` 中运行 `package` 后，tar 包位于 `computer/target/`，发行目录位于 `computer/apache-hugegraph-computer-1.7.0/`。

## 4. 单机运行 PageRank

先编辑发行目录中的 `conf/computer.properties`，按实际环境修改 HugeGraph 地址、图名和认证信息，并确认 `bsp.etcd_endpoints` 指向可访问的 etcd。默认配置已选择内置 `PageRankParams`；master 和 worker 必须使用同一份配置及相同的 `job.id`。每个并行作业应使用不同的 `job.id`。

在两个终端中都从发行目录启动进程。启动脚本默认读取 `conf/computer.properties`，也可用 `-c` 指定配置文件。

```bash
# 终端一：启动 master
bin/start-computer.sh -d local -r master
```

```bash
# 终端二：启动 worker
bin/start-computer.sh -d local -r worker
```

master 会等待配置要求的 worker 注册后运行作业。查看两个终端输出；默认日志配置也会在当前发行目录的 `logs/` 下写入 master 和 worker 日志。只有进程启动成功并不代表计算完成，应确认 master 日志中输入、超步计算和输出阶段均正常结束。

PageRank 参数类将结果写回 HugeGraph，属性名为 `page_rank`。若图当前读模式不显示 OLAP 写入，可由管理员把读模式设为 `ALL`：

```bash
curl --fail --request PUT \
  --header 'Content-Type: application/json' \
  --data '"ALL"' \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph_read_mode'
```

查询顶点以确认结果属性：

```bash
curl --fail --compressed \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices?limit=3'
```

需要认证时，在 `curl` 命令中添加 `--user "$HG_USER:$HG_PASSWORD"`。读模式接口和权限说明见[图读模式 REST API](/cn/docs/clients/restful-api/graphs/#634-设置某个图的读模式该操作需要管理员权限)。

## 5. 在 Kubernetes 中运行 PageRank

先确保 HugeGraph-Server 对计算 Pod 可达。Computer Operator 清单会部署 Operator 和 etcd；清单配置的 etcd 服务地址会由 Operator 注入作业配置。CRD 和 Operator 清单应使用同一 Computer 发行版本。下面以 1.7.0 的 `v1` CRD 为例：

```bash
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/1.7.0/computer/computer-k8s-operator/manifest/hugegraph-computer-crd.v1.yaml
kubectl apply -f https://raw.githubusercontent.com/apache/hugegraph-computer/1.7.0/computer/computer-k8s-operator/manifest/hugegraph-computer-operator.yaml
kubectl get pods -n hugegraph-computer-operator-system --watch
```

确认 Operator 和 etcd Pod 已就绪后，提交 `HugeGraphComputerJob`。替换镜像为集群可拉取且包含对应版本运行时与内置算法 JAR 的镜像，并把 HugeGraph 地址改成 Pod 可访问的服务地址。分区数必须不小于 worker 数量。

```yaml
apiVersion: operator.hugegraph.apache.org/v1
kind: HugeGraphComputerJob
metadata:
  namespace: hugegraph-computer-operator-system
  name: pagerank-sample
spec:
  jobId: pagerank-sample
  algorithmName: page_rank
  image: registry.example.com/hugegraph-computer:1.7.0
  jarFile: /hugegraph/hugegraph-computer/algorithm/builtin-algorithm.jar
  pullPolicy: IfNotPresent
  workerInstances: 1
  computerConf:
    job.partitions_count: "1"
    algorithm.params_class: org.apache.hugegraph.computer.algorithm.centrality.pagerank.PageRankParams
    hugegraph.url: http://hugegraph-server:8080
    hugegraph.name: hugegraph
```

```bash
kubectl apply -f pagerank-job.yaml
kubectl get hcjob pagerank-sample -n hugegraph-computer-operator-system --watch
```

作业状态为 `SUCCEEDED` 表示运行完成。另开终端在作业运行期间查看 Pod 和日志；若状态为 `FAILED`，应在资源清理前收集诊断信息：

```bash
kubectl get pods -n hugegraph-computer-operator-system
kubectl logs --follow <master-pod-name> -n hugegraph-computer-operator-system
kubectl logs --follow <worker-pod-name> -n hugegraph-computer-operator-system
```

随附 Operator 清单默认启用 `AUTO_DESTROY_POD=true`。Operator 观察到作业结束后会删除作业 CR 及其计算资源，因此应在运行期间观察状态并收集日志。需要保留 CR 和 Pod 以便排查时，在 Operator 部署中将 `AUTO_DESTROY_POD` 设为 `false`；保留后可用 `kubectl get hcjob pagerank-sample -n hugegraph-computer-operator-system -o yaml` 查看最终状态。PageRank 写回 HugeGraph 后按上一节设置读模式并查询。若改用 HDFS 输出，结果位于 `output.hdfs_path_prefix/<job.id>/` 下，文件名和分区布局由作业配置决定。

完整 CRD 字段见[Computer 配置参考中的 CRD 说明](/cn/docs/quickstart/computing/hugegraph-computer-config/#hugegraph-computer-crd)。

## 6. 内置算法与开发入口

当前源码中的内置算法包括：

- 中心性：PageRank、Betweenness Centrality、Closeness Centrality、Degree Centrality。
- 社区与结构：Clustering Coefficient、K-core、LPA、Triangle Count、WCC。
- 路径与采样：环检测、带过滤的环检测、单源最短路径、Random Walk。

算法实现位于 [`computer/computer-algorithm`](https://github.com/apache/hugegraph-computer/tree/1.7.0/computer/computer-algorithm)。自定义算法需要遵循 Computer API 并打包为可加载的 JAR；模块划分和开发入口见[Computer README](https://github.com/apache/hugegraph-computer/blob/1.7.0/computer/README.md)。
