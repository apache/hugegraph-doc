---
title: "HugeGraph-Computer Quick Start"
linkTitle: "Analysis with HugeGraph-Computer"
weight: 2
search_keywords: [HugeGraph Computer, graph computing, OLAP]
search_boost: 1.6
---

## 1. Component Overview

[`HugeGraph-Computer`](https://github.com/apache/hugegraph-computer) is a Java distributed graph computing framework based on BSP (Bulk Synchronous Parallel), with algorithms running in iterative supersteps. Kubernetes Operator or YARN can schedule jobs; master and worker processes can also run on one machine for small trial jobs.

Computer and Vermeer, in the same repository, are separate implementations: Computer uses a Java/BSP runtime for distributed computing, while Vermeer is a Go in-memory graph computing platform with a master-worker architecture. They share HugeGraph data sources, but their deployment and job configurations are not interchangeable.

Computer reads graph data from HugeGraph or HDFS and writes results to either system. The runtime can spill some data to disk; whether a job completes still depends on input size, resources, and configuration. Disk spilling does not remove resource limits.

## 2. Prerequisites and Connections

Building and running require JDK 11 or later; source builds also require Maven 3.5 or later. The PageRank example needs a running HugeGraph-Server with graph data, plus etcd reachable by the master and workers.

| Service | Example address or port | Purpose |
|------|----------------|------|
| HugeGraph-Server | `http://127.0.0.1:8080` | Read graph data and write algorithm results; configured by `hugegraph.url`. |
| etcd | `http://127.0.0.1:2379` | BSP job coordination; configured by `bsp.etcd_endpoints`. |
| Computer master RPC | TCP `8190` | Workers connect to master; port in the distribution configuration. |
| Computer worker data transfer | OS-assigned locally; K8s Operator defaults to `8099` | Transfer vertices and messages between workers. Advertised addresses and ports must be reachable across hosts. |
| MinIO (K8s manifests) | HTTP `9000` | Input partition snapshots. Computer 1.7.0 manifests incorrectly map Service port `9000` to MinIO Console port `9090`; change `targetPort` to `9000` before enabling snapshots. Defaults are `snapshot.write=false` and `snapshot.load=false`, so MinIO access is unnecessary when snapshots are disabled. |
| cert-manager (K8s) | In-cluster service | Operator manifests use `cert-manager.io/v1` `Certificate`, `Issuer`, and CA injection. Install a compatible version before deploying the Operator. |
| HDFS | Cluster-specific | Required only when input or output uses HDFS. |

For Kubernetes jobs, `hugegraph.url` must be reachable from all computing Pods; do not use a `localhost` address available only on your computer. If HugeGraph authentication is enabled, configure the username and password and supply matching credentials for REST queries.

> [!WARNING]
> In production, enable [Server authentication and authorization](/docs/config/config-authentication/), retain Server audit logs (normally `audit-*.log`), give Computer a dedicated account with only the read/write permissions required by its jobs, and configure a source IP allowlist for Server. `hugegraph.username` and `hugegraph.password` are credentials for connecting to Server, not a replacement for Server authentication.

See the [Computer configuration reference](/docs/quickstart/computing/hugegraph-computer-config/) for more options.

## 3. Obtain Source and Build a Distribution

The Apache HugeGraph download directory provides versioned Computer source archives, without separate precompiled Computer binaries. This example uses `VERSION=1.7.0`, whose source archive and build output names include `-incubating-`. For other versions, use the actual filenames in the download directory.

```bash
VERSION=1.7.0 # Replace with the release to download
ARCHIVE="apache-hugegraph-computer-incubating-${VERSION}-src.tar.gz"
DOWNLOAD_BASE="https://downloads.apache.org/hugegraph/${VERSION}"
curl -fLO "${DOWNLOAD_BASE}/${ARCHIVE}"
curl -fLO "${DOWNLOAD_BASE}/${ARCHIVE}.sha512"
curl -fLO "${DOWNLOAD_BASE}/${ARCHIVE}.asc"
curl -fLO https://downloads.apache.org/hugegraph/KEYS
shasum -a 512 -c "${ARCHIVE}.sha512"
gpg --import KEYS
gpg --verify "${ARCHIVE}.asc" "${ARCHIVE}"
tar -xzf "${ARCHIVE}"
cd "apache-hugegraph-computer-incubating-${VERSION}-src/computer"
mvn clean package -DskipTests
tar -xzf "target/apache-hugegraph-computer-incubating-${VERSION}.tar.gz"
cd "apache-hugegraph-computer-incubating-${VERSION}"
```

To build current master, clone and package the source:

```bash
git clone https://github.com/apache/hugegraph-computer.git
cd hugegraph-computer/computer
mvn clean package -DskipTests
```

The `computer/computer-dist` module assembles the distribution, including `bin/start-computer.sh`, runtime dependencies in `lib/`, built-in algorithms in `algorithm/builtin-algorithm.jar`, and default `conf/computer.properties` and `conf/log4j2.xml`. The source configuration is `computer/computer-dist/src/assembly/static/conf/computer.properties`. Release 1.7.0 build output includes `-incubating-`; current master omits it and takes its version from the POM. Use archive names matching the source you built.

## 4. Run PageRank Locally

Edit `conf/computer.properties` in the distribution directory with your HugeGraph URL, graph name, and credentials; point `bsp.etcd_endpoints` to reachable etcd. The default configuration selects built-in `PageRankParams`. Master and workers must use the same configuration and `job.id`; concurrent jobs need distinct job IDs.

Start processes from the distribution directory in two terminals. The script reads `conf/computer.properties` by default; use `-c` to select another file.

```bash
# Terminal 1: start master
bin/start-computer.sh -d local -r master
```

```bash
# Terminal 2: start worker
bin/start-computer.sh -d local -r worker
```

Master waits for the configured workers to register before running the job. Check both terminal outputs; the default logging configuration also writes master and worker logs under the distribution directory's `logs/`. Process startup alone does not confirm completion: verify that input, superstep computation, and output all finish normally in the master log.

PageRank writes results to HugeGraph under `page_rank`. First ensure every target vertex label allows this property. Computer creates a `DOUBLE`, `OLAP_COMMON` property key but does not add it to vertex labels. If absent, create it:

```bash
curl --fail --request POST \
  --header 'Content-Type: application/json' \
  --data '{"name":"page_rank","data_type":"DOUBLE","cardinality":"SINGLE","write_type":"OLAP_COMMON"}' \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/propertykeys'
```

If the property key already exists, verify its type is `DOUBLE` and `write_type` is `OLAP_COMMON`. List vertex labels, then add nullable `page_rank` to every label being computed; replace `person` with the actual label:

```bash
curl --fail --compressed \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels'

curl --fail --request PUT \
  --header 'Content-Type: application/json' \
  --data '{"name":"person","properties":["page_rank"],"nullable_keys":["page_rank"]}' \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels/person?action=append'
```

If the current read mode hides OLAP writes, an administrator can set it to `ALL`:

```bash
curl --fail --request PUT \
  --header 'Content-Type: application/json' \
  --data '"ALL"' \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph_read_mode'
```

Query vertices to verify the result property:

```bash
curl --fail --compressed \
  'http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/graph/vertices?limit=3'
```

When authentication is required, add `--user "$HG_USER:$HG_PASSWORD"` to curl. See the [graph read-mode REST API](/docs/clients/restful-api/graphs/#634-modify-graphs-read-mode) for the endpoint and permissions.

## 5. Run PageRank on Kubernetes

Ensure computing Pods can reach HugeGraph-Server, then install a cluster-compatible cert-manager using its [official installation guide](https://cert-manager.io/docs/installation/). The Computer Operator manifests deploy the Operator, etcd, and MinIO. Use the same Computer release for the CRD and Operator manifests; this example uses 1.7.0:

```bash
VERSION=1.7.0 # Use the same release for CRD and Operator manifests
kubectl apply -f "https://raw.githubusercontent.com/apache/hugegraph-computer/${VERSION}/computer/computer-k8s-operator/manifest/hugegraph-computer-crd.v1.yaml"
kubectl apply -f "https://raw.githubusercontent.com/apache/hugegraph-computer/${VERSION}/computer/computer-k8s-operator/manifest/hugegraph-computer-operator.yaml"
kubectl rollout status deployment/hugegraph-computer-operator-controller-manager \
  -n hugegraph-computer-operator-system --timeout=120s
```

> [!DETAILS]- Optional: enable MinIO snapshots (1.7.0)
>
> The 1.7.0 MinIO Service maps S3 API port `9000` to Console port `9090`. Fix this mapping before enabling snapshots and set `snapshot.minio_endpoint` to `http://hugegraph-computer-operator-minio.hugegraph-computer-operator-system.svc:9000`. Skip this when snapshots remain disabled.
>
> ```bash
> kubectl patch service hugegraph-computer-operator-minio \
>   -n hugegraph-computer-operator-system \
>   --type=json \
>   -p='[{"op":"replace","path":"/spec/ports/0/targetPort","value":9000}]'
> ```

Replace the HugeGraph URL with a service address reachable by computing Pods, then submit a `HugeGraphComputerJob`. This example uses the official Docker Hub image `hugegraph/hugegraph-computer:latest` and its built-in PageRank JAR. Custom algorithm JARs can be bundled in the image and selected with `jarFile`, or downloaded from HTTP(S) with `remoteJarUri`. The partition count must be at least the worker count.

Save the following YAML as `pagerank-job.yaml`, then apply it:

```yaml
apiVersion: operator.hugegraph.apache.org/v1
kind: HugeGraphComputerJob
metadata:
  namespace: hugegraph-computer-operator-system
  name: pagerank-sample
spec:
  jobId: pagerank-sample
  algorithmName: page_rank
  image: hugegraph/hugegraph-computer:latest # Official Docker Hub image
  jarFile: /hugegraph/hugegraph-computer/algorithm/builtin-algorithm.jar
  pullPolicy: IfNotPresent
  workerInstances: 1
  masterCpu: 500m
  workerCpu: 500m
  masterMemory: 1Gi
  workerMemory: 2Gi
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

`SUCCEEDED` means the job completed. By default, the Operator deletes the CR and computing resources after completion. Expand the following instructions when you need to retain state or investigate a failed job.

> [!DETAILS]- Optional: retain job state, inspect logs, or clean up resources
>
> The Operator defaults to `AUTO_DESTROY_POD=true`, so short jobs may lose their CR and Pods before inspection. Disable this before submitting the job, wait for the replacement Controller Pod to become ready, then submit. Change this setting in the Java Operator's `controller` container:
>
> ```bash
> kubectl set env deployment/hugegraph-computer-operator-controller-manager \
>   -n hugegraph-computer-operator-system \
>   --containers=controller AUTO_DESTROY_POD=false
> kubectl rollout status deployment/hugegraph-computer-operator-controller-manager \
>   -n hugegraph-computer-operator-system --timeout=120s
> ```
>
> Inspect runtime information or failure logs:
>
> ```bash
> kubectl logs --follow <master-pod-name> -n hugegraph-computer-operator-system
> kubectl logs --follow <worker-pod-name> -n hugegraph-computer-operator-system
> ```
>
> After checking results, delete the CR to clean up associated resources and restore the default policy:
>
> ```bash
> kubectl delete hcjob pagerank-sample -n hugegraph-computer-operator-system
> kubectl set env deployment/hugegraph-computer-operator-controller-manager \
>   -n hugegraph-computer-operator-system \
>   --containers=controller AUTO_DESTROY_POD=true
> ```

After PageRank writes to HugeGraph, set the read mode and query as in the previous section. For HDFS output, results are under `output.hdfs_path_prefix/<job.id>/`; filenames and partition layout depend on job configuration.

See the [CRD configuration reference](/docs/quickstart/computing/hugegraph-computer-config/#hugegraph-computer-crd) for all fields.

## 6. Built-in Algorithms and Development

Current built-in algorithms include:

- Centrality: PageRank, Betweenness Centrality, Closeness Centrality, Degree Centrality.
- Communities and structure: Clustering Coefficient, K-core, LPA, Triangle Count, WCC.
- Paths and sampling: ring detection, filtered ring detection, single-source shortest path, Random Walk.

Implementations are in [`computer/computer-algorithm`](https://github.com/apache/hugegraph-computer/tree/master/computer/computer-algorithm). Custom algorithms must follow the Computer API and be packaged as loadable JARs; see the [Computer README](https://github.com/apache/hugegraph-computer/blob/master/computer/README.md) for modules and development entry points.
