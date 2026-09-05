---
title: "HugeGraph-Store Quick Start"
linkTitle: "Install/Build HugeGraph-Store"
weight: 3
search_keywords:
  - server.port
  - REST port
  - Store REST port
search_boost: 1.5
---

### 1 HugeGraph-Store Overview

HugeGraph-Store is the storage node component of HugeGraph's distributed version, responsible for actually storing and managing graph data. It works in conjunction with HugeGraph-PD to form HugeGraph's distributed storage engine, providing high availability and horizontal scalability.

Each Store node keeps graph data in RocksDB and replicates it with Raft (JRaft): every partition is a separate Raft group, so a partition survives the loss of a minority of its replicas. Store nodes do not know about each other directly. They register with PD, receive their partition assignment from PD, and report state back over a heartbeat. HugeGraph-Server reaches Store over gRPC after looking up partition locations in PD.

### 2 Prerequisites

#### 2.1 Requirements

- Operating System: Linux or macOS (Windows has not been fully tested)
- Java version: ≥ 11 (enforced by the build and re-checked by `bin/start-hugegraph-store.sh`)
- Maven version: ≥ 3.5.0
- Deploy HugeGraph-PD first for multi-node deployment

### 3 Deployment

There are two ways to deploy the HugeGraph-Store component:

- Method 1: Download the tar package
- Method 2: Compile from source

#### 3.1 Download the tar package

Download the latest version of HugeGraph-Store from the Apache HugeGraph official download page:

```bash
# 1.7.0 is a historical release from the incubation period, so its file and directory names still include "incubating"
wget https://downloads.apache.org/hugegraph/1.7.0/apache-hugegraph-incubating-1.7.0.tar.gz
tar zxf apache-hugegraph-incubating-1.7.0.tar.gz
cd apache-hugegraph-incubating-1.7.0/apache-hugegraph-store-incubating-1.7.0
```

#### 3.2 Compile from source

```bash
# 1. Clone the source code
git clone https://github.com/apache/hugegraph.git

# 2. Build the project
cd hugegraph
mvn clean install -DskipTests=true

# 3. After a successful build, the Store directory and complete distribution package are located at
#    hugegraph-store/apache-hugegraph-store-{version}
#    target/apache-hugegraph-{version}.tar.gz
```

To build Store alone instead of the whole repository, build `hugegraph-struct` first, because Store depends on it:

```bash
mvn install -pl hugegraph-struct -am -DskipTests
mvn clean package -pl hugegraph-store/hg-store-dist -am -DskipTests
```

The assembled directory contains only `bin/`, `conf/` and `lib/hg-store-node-{version}.jar`.

#### 3.3 Docker Deployment

The HugeGraph-Store Docker image is available on Docker Hub as `hugegraph/store`.

> **Note**: The following steps assume you have already cloned or pulled the HugeGraph main repository locally, or at least have its `docker/` directory available.

Two compose files include Store:

| Compose file | Topology | Use |
|--------------|----------|-----|
| `docker-compose-hstore.yml` | 1 PD + 1 Store + 1 Server + 1 Hubble | Smallest distributed setup |
| `docker-compose-3pd-3store-3server.yml` | 3 PD + 3 Store + 3 Server + 1 Hubble | Multi-node reference |

```bash
cd hugegraph/docker
# Keep the version aligned with the latest release, for example 1.x.0

# Minimal distributed deployment
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-hstore.yml up -d --wait

# Or the multi-node cluster
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-3pd-3store-3server.yml up -d
```

To run a single Store node via `docker run`:

```bash
docker run -d \
  -p 8520:8520 \
  -p 8500:8500 \
  -p 8510:8510 \
  -e HG_STORE_PD_ADDRESS=<pd-ip>:8686 \
  -e HG_STORE_GRPC_HOST=<your-ip> \
  -e HG_STORE_RAFT_ADDRESS=<your-ip>:8510 \
  -v /path/to/storage:/hugegraph-store/storage \
  --name hugegraph-store \
  hugegraph/store:1.7.0
```

**Environment variable reference:**

| Variable | Required | Default | Maps to | Description |
|----------|----------|---------|---------|-------------|
| `HG_STORE_PD_ADDRESS` | Yes | n/a | `pdserver.address` | PD gRPC addresses (e.g. `pd0:8686,pd1:8686,pd2:8686`) |
| `HG_STORE_GRPC_HOST` | Yes | n/a | `grpc.host` | This node's hostname/IP for gRPC (e.g. `store0`) |
| `HG_STORE_RAFT_ADDRESS` | Yes | n/a | `raft.address` | This node's Raft address (e.g. `store0:8510`) |
| `HG_STORE_GRPC_PORT` | No | `8500` | `grpc.port` | gRPC server port |
| `HG_STORE_REST_PORT` | No | `8520` | `server.port` | REST API port |
| `HG_STORE_DATA_PATH` | No | `/hugegraph-store/storage` | `app.data-path` | Data storage path |

The entrypoint turns these into a `SPRING_APPLICATION_JSON` overlay on top of `conf/application.yml`, then runs `bin/start-hugegraph-store.sh -d false -j "$JAVA_OPTS"`. Any key not covered by the table above still has to be edited in `conf/application.yml`, or supplied through your own `SPRING_APPLICATION_JSON`.

Image details:

- `JAVA_OPTS` defaults to `-XX:+UnlockExperimentalVMOptions -XX:+UseContainerSupport -XX:MaxRAMPercentage=50 -XshowSettings:vm`
- `STDOUT_MODE=true`, so Java logs go to the container stdout instead of `logs/hugegraph-store-server.log`
- `HEALTHCHECK` calls `GET http://localhost:8520/v1/health` every 15s after a 90s start period
- The image declares `EXPOSE 8520`; publish 8500 and 8510 yourself when Server or other Store nodes need to reach the container from outside the Docker network

> **Note**: In Docker bridge networking, use container hostnames (e.g. `store0`) for `HG_STORE_GRPC_HOST` instead of IP addresses.

> **Deprecated aliases**: `PD_ADDRESS`, `GRPC_HOST`, `RAFT_ADDRESS` still work but log a deprecation warning. Use the `HG_STORE_*` names for new deployments.

### 4 Configuration

Store reads two files from `conf/`:

- `application.yml`, the main configuration file (PD address, ports, Raft, data path)
- `application-pd.yml`, pulled in by `spring.profiles.include: pd` in `application.yml`, holding the RocksDB memory settings and the Actuator exposure

#### 4.1 application.yml

This is the file shipped in the distribution package:

```yaml
pdserver:
  # PD service address, multiple PD addresses separated by commas
  address: localhost:8686

management:
  metrics:
    export:
      prometheus:
        enabled: true
  endpoints:
    web:
      exposure:
        include: "*"

grpc:
  # grpc service address
  host: 127.0.0.1
  port: 8500
  netty-server:
    max-inbound-message-size: 1000MB
raft:
  # raft cache queue size
  disruptorBufferSize: 1024
  address: 127.0.0.1:8510
  max-log-file-size: 600000000000
  # Snapshot generation interval, in seconds
  snapshotInterval: 1800
server:
  # rest service address
  port: 8520

app:
  # Storage path, support multiple paths, separated by commas
  data-path: ./storage
  #raft-path: ./storage

spring:
  application:
    name: store-node-grpc-server
  profiles:
    active: default
    include: pd

logging:
  config: 'file:./conf/log4j2.xml'
  level:
    root: info
```

#### 4.2 application-pd.yml

```yaml
management:
  metrics:
    export:
      prometheus:
        enabled: true
  endpoints:
    web:
      exposure:
        include: "*"

rocksdb:
  # rocksdb total memory usage, force flush to disk when reaching this value
  total_memory_size: 32000000000
  # memtable size used by rocksdb
  write_buffer_size: 32000000
  # For each rocksdb, the number of memtables reaches this value for writing to disk.
  min_write_buffer_number_to_merge: 16
```

#### 4.3 Configuration reference

"Shipped" is the value in the two files above. "Code default" is what the node falls back to when the key is absent, and is the value to rely on for keys the template does not list.

**Core**

| Key | Shipped | Code default | Meaning |
|-----|---------|--------------|---------|
| `pdserver.address` | `localhost:8686` | required | PD gRPC endpoints, comma separated. Store registers itself here and receives its partition assignment. Must be PD's `grpc.port`, not its REST port. |
| `grpc.host` | `127.0.0.1` | required | Address this node advertises for its own gRPC service. Set it to a routable IP or hostname, `127.0.0.1` is only usable for a single-machine setup. |
| `grpc.port` | `8500` | required | gRPC port. Server and the Store client connect here. |
| `grpc.netty-server.max-inbound-message-size` | `1000MB` | gRPC default | Maximum size of a single inbound gRPC message. Bound by the `grpc-spring-boot-starter` Netty server. |
| `grpc.server.wait-time` | not set | `3600` | Seconds a scan stream waits for the client to consume a page before the server aborts it. |
| `server.port` | `8520` | required | REST and Actuator port. Also reported to PD as the `rest.port` label. |

**Raft**

| Key | Shipped | Code default | Meaning |
|-----|---------|--------------|---------|
| `raft.address` | `127.0.0.1:8510` | required | Raft service address of this node, `host:port`. Must be reachable from every other Store node. There is no peer list to configure: PD tells each node which peers belong to a partition's Raft group. |
| `raft.disruptorBufferSize` | `1024` | `0` | Raft task queue size. `0` derives it from `rocksdb.total_memory_size`, by rounding that size in GB to the nearest power of two and multiplying by 32. |
| `raft.max-log-file-size` | `600000000000` | `50000000000` | Maximum byte size of Raft logs. |
| `raft.snapshotInterval` | `1800` | `300` | Seconds between Raft snapshots. |
| `raft.snapshotLogIndexMargin` | not set | `0` | Minimum applied-index distance since the last snapshot before a snapshot is actually written. `0` disables the distance check. |
| `raft.rpc-timeout` | not set | `10000` | Raft RPC timeout in milliseconds. |
| `raft.metrics` | not set | `true` | Collect JRaft node metrics, readable at `/metrics/raft`. |
| `raft.useRocksDBSegmentLogStorage` | not set | `true` | Store Raft logs in the RocksDB segment log storage. |
| `raft.maxSegmentFileSize` | not set | `67108864` | Segment log file size in bytes (64 MB). |
| `raft.maxReplicatorInflightMsgs` | not set | `256` | Maximum in-flight replication requests per follower. |
| `raft.maxEntriesSize` | not set | `256` | Maximum number of entries in one `AppendEntries` request. |
| `raft.maxBodySize` | not set | `524288` | Maximum byte size of one `AppendEntries` request. |
| `ave-logEntry-size-ratio` | not set | `0.95` | Smoothing ratio used to estimate the average log entry size. Note that this key sits at the top level, not under `raft`. |

**Storage and labels**

| Key | Shipped | Code default | Meaning |
|-----|---------|--------------|---------|
| `app.data-path` | `./storage` | `store` | RocksDB data directory. Multiple paths separated by commas spread partitions over several disks. |
| `app.raft-path` | commented out | empty | Directory for Raft logs and snapshots. Falls back to `app.data-path` when empty. |
| `app.fake-pd` | not set | `false` | Built-in PD mode for standalone testing. Do not use it in production. |
| `app.placeholder-size` | not set | `10` | Size in GB of a `placeholder` file created in each data path at startup, so space can be freed in an emergency. `0` disables it. |
| `app.label.<name>` | not set | none | Arbitrary key/value labels sent to PD in the store heartbeat. The node adds `rest.port` on its own. |

**RocksDB**

| Key | Shipped | Code default | Meaning |
|-----|---------|--------------|---------|
| `rocksdb.total_memory_size` | `32000000000` | `51539607552` | Memory budget shared by all RocksDB instances on this node. When absent or `0`, the node uses the JVM max heap instead. |
| `rocksdb.write_buffer_size` | `32000000` | `33554432` | Memtable size in bytes. When absent or `0`, the node uses `total_memory_size / 1000`. |
| `rocksdb.min_write_buffer_number_to_merge` | `16` | `16` | Number of memtables merged together before a flush. |
| `rocksdb.write_buffer_ratio` | not set | `0.66` | Share of `total_memory_size` given to the write cache. The rest becomes the block cache. |

Any other option defined in `org/apache/hugegraph/rocksdb/access/RocksDBOptions.java` can be added under the same `rocksdb:` block, for example `rocksdb.max_background_jobs`, `rocksdb.level0_file_num_compaction_trigger` or `rocksdb.bloom_filter_bits_per_key`.

**Thread pools**

| Key | Code default | Meaning |
|-----|--------------|---------|
| `thread.pool.grpc.core` | `600` | Core threads serving gRPC requests. |
| `thread.pool.grpc.max` | `1000` | Maximum gRPC threads. |
| `thread.pool.grpc.queue` | `2147483647` | gRPC task queue capacity. |
| `thread.pool.scan.core` | `128` | Core threads serving scans. `0` means 4 times the CPU count. |
| `thread.pool.scan.max` | `1000` | Maximum scan threads. |
| `thread.pool.scan.queue` | `0` | Scan task queue capacity. |

**Query pushdown**

| Key | Code default | Meaning |
|-----|--------------|---------|
| `query.push-down.threads` | `1500` | Thread pool size for pushed-down queries. |
| `query.push-down.fetch_batch` | `20000` | Rows fetched per request. |
| `query.push-down.fetch_timeout` | `300000` | Fetch timeout in milliseconds. |
| `query.push-down.memory_limit_count` | `50000` | Row limit for in-memory operations such as sorting. |
| `query.push-down.index_size_limit_count` | `50000` | Index sst file size limit in kB. |

**Background jobs**

| Key | Code default | Meaning |
|-----|--------------|---------|
| `job.interruptableThreadPool.core` | `128` | Core threads of the TTL cleaner pool. `0` means the CPU count. |
| `job.interruptableThreadPool.max` | `256` | Maximum threads of the TTL cleaner pool. `0` means 4 times the CPU count. |
| `job.interruptableThreadPool.queue` | `2147483647` | Queue capacity of the TTL cleaner pool. |
| `job.uninterruptibleThreadPool.core` | `0` | Core threads of the engine's uninterruptible job pool. `0` means the CPU count. |
| `job.uninterruptibleThreadPool.max` | `256` | Maximum threads of the uninterruptible job pool. |
| `job.uninterruptibleThreadPool.queue` | `2147483647` | Queue capacity of the uninterruptible job pool. |
| `job.cleaner.batch.size` | `10000` | Keys deleted per batch by the TTL cleaner. |
| `job.start-time` | `0` | Hour of day (0 to 23) at which the daily TTL cleanup runs. Values outside that range fall back to 19. |

**Built-in PD mode**

Only for single-node development and debugging, activated by `app.fake-pd: true`. The node then plays PD's role itself and ignores `pdserver.address`.

| Key | Code default | Meaning |
|-----|--------------|---------|
| `fake-pd.store-list` | `''` | gRPC addresses of the Store nodes in the fake cluster. |
| `fake-pd.peers-list` | `''` | Raft addresses of the same nodes. |
| `fake-pd.partition-count` | `3` | Number of partitions. |
| `fake-pd.shard-count` | `3` | Replicas per partition. |

**Diagnostics**

| Key | Code default | Meaning |
|-----|--------------|---------|
| `arthas.telnetPort` | `8566` | Arthas telnet port, used when `/v1/arthasstart` is called. |
| `arthas.httpPort` | `8565` | Arthas HTTP port. |
| `arthas.ip` | `0.0.0.0` | Arthas bind address. |
| `arthas.disabledCommands` | `jad` | Arthas commands to disable. |

#### 4.4 Per-node changes

For multi-node deployment, you need to modify the following configurations for each Store node:

1. `grpc.host` and `grpc.port` (the address other components dial)
2. `raft.address` (Raft protocol address)
3. `server.port` (REST port)
4. `app.data-path` (data storage path)

`pdserver.address` is the same on every node, it lists the whole PD cluster.

### 5 Start and Stop

#### 5.1 Start Store

Ensure that the PD service is already started, then in the Store installation directory, execute:

```bash
./bin/start-hugegraph-store.sh
```

The script accepts four flags:

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `-d` | `true`, `false` | `true` | Daemon mode. See below. |
| `-g` | `ZGC`, `zgc` | not set | Garbage collector. Omit the flag for G1, which is the default. Any value other than `ZGC` or `zgc` aborts the start, including `g1`, even though the script's own usage line suggests it. |
| `-j` | JVM options string | empty | Extra JVM options, for example `-j "-Xmx16g -Xms8g"`. |
| `-y` | `true`, `false` | `false` | Attach the OpenTelemetry Java agent, downloading it into `plugins/` on first use, and export traces to `127.0.0.1:4317`. |

Daemon mode:

- `-d true` (default): run as a background daemon. The script returns immediately and writes the Java pid to `bin/pid`.
- `-d false`: run in the foreground. The script `exec`s Java, so the container or supervisor process is Java itself. Use this under Docker or a process supervisor (systemd, supervisord) so crashes are detected and the service is restarted automatically.

JVM memory, unless you set `JAVA_OPTIONS` yourself: `-Xms512m`, and `-Xmx` set to half the free memory, clamped to the 512 MB to 2048 MB range. The script also adds `-XX:MetaspaceSize=256M`, a heap dump on out-of-memory into `logs/`, and a rolling GC log at `logs/gc.log`. Production nodes normally need a much larger heap, so pass one explicitly, for example `-j "-Xmx32g -Xms32g"`.

The script refuses to start if `ulimit -n` or `ulimit -u` is below 1024, and it preloads jemalloc on x86_64 and arm64 when the shared object can be downloaded and verified.

After successful startup, you can see logs similar to the following in `logs/hugegraph-store-server.log`:

```
YYYY-mm-dd xx:xx:xx [main] [INFO] o.a.h.s.n.StoreNodeApplication - Started StoreNodeApplication in x.xxx seconds (JVM running for x.xxx)
```

#### 5.2 Stop Store

In the Store installation directory, execute:

```bash
./bin/stop-hugegraph-store.sh
```

The script reads `bin/pid`, signals that process, and waits up to 30 seconds for it to exit before removing the pid file. If `bin/pid` is missing it exits without doing anything.

#### 5.3 Restart Store

```bash
./bin/restart-hugegraph-store.sh
```

It sources the stop script and then the start script, and forwards the flags from section 5.1.

#### 5.4 Startup order

1. **PD** first. Each Store's `grpc.host:grpc.port` should appear in PD's `pd.initial-store-list`, otherwise PD registers the node in `Pending` state instead of bringing it to `Up`, and partition assignment never finishes.
2. **Store** next. A Store started before PD is reachable is not fatal: the heartbeat thread keeps retrying registration and logs `store heartbeat error: PD UNREACHABLE` until PD answers.
3. **HugeGraph-Server** last, once every Store node reports `state: "Up"`. Server needs the partitions in place before it can initialize or open a graph.

The compose files encode the same order with `depends_on: condition: service_healthy`: Store waits for every PD healthcheck, and Server waits for every Store healthcheck.

### 6 Multi-Node Deployment Example

Below is a configuration example for a three-node deployment:

#### 6.1 Three-Node Configuration Reference

- 3 PD nodes
  - raft ports: 8610, 8611, 8612
  - rpc ports: 8686, 8687, 8688
  - rest ports: 8620, 8621, 8622
- 3 Store nodes
  - raft ports: 8510, 8511, 8512
  - rpc ports: 8500, 8501, 8502
  - rest ports: 8520, 8521, 8522

#### 6.2 Store Node Configuration

For the three Store nodes, the main configuration differences are as follows:

Node A:
```yaml
grpc:
  port: 8500
raft:
  address: 127.0.0.1:8510
server:
  port: 8520
app:
  data-path: ./storage-a
```

Node B:
```yaml
grpc:
  port: 8501
raft:
  address: 127.0.0.1:8511
server:
  port: 8521
app:
  data-path: ./storage-b
```

Node C:
```yaml
grpc:
  port: 8502
raft:
  address: 127.0.0.1:8512
server:
  port: 8522
app:
  data-path: ./storage-c
```

All nodes should point to the same PD cluster:
```yaml
pdserver:
  address: 127.0.0.1:8686,127.0.0.1:8687,127.0.0.1:8688
```

And every PD node should list all three Store gRPC addresses:
```yaml
pd:
  initial-store-list: 127.0.0.1:8500,127.0.0.1:8501,127.0.0.1:8502
```

#### 6.3 Docker Distributed Cluster Configuration

The distributed Store cluster definition is included in `docker/docker-compose-3pd-3store-3server.yml`. Each Store node gets its own hostname and environment variables:

```yaml
# store0, published as 8500 (gRPC), 8510 (Raft), 8520 (REST)
HG_STORE_PD_ADDRESS: pd0:8686,pd1:8686,pd2:8686
HG_STORE_GRPC_HOST: store0
HG_STORE_GRPC_PORT: "8500"
HG_STORE_REST_PORT: "8520"
HG_STORE_RAFT_ADDRESS: store0:8510
HG_STORE_DATA_PATH: /hugegraph-store/storage

# store1, published as 8501, 8511, 8521
HG_STORE_GRPC_HOST: store1
HG_STORE_RAFT_ADDRESS: store1:8510

# store2, published as 8502, 8512, 8522
HG_STORE_GRPC_HOST: store2
HG_STORE_RAFT_ADDRESS: store2:8510
```

The container ports stay 8500/8510/8520 on every node, only the published host ports differ. The PD nodes set `HG_PD_INITIAL_STORE_LIST: store0:8500,store1:8500,store2:8500` to match.

Store nodes start only after all PD nodes pass healthchecks (`/v1/health`), enforced via `depends_on: condition: service_healthy`.

To view runtime logs for a running Store container use `docker logs <container-name>` (e.g. `docker logs hg-store0`).

See [docker/README.md](https://github.com/apache/hugegraph/blob/master/docker/README.md) for the full setup guide.

### 7 Verify Store Service

Confirm that the Store service is running properly:

```bash
curl http://localhost:8520/actuator/health
```

If it returns `{"status":"UP"}`, it indicates that the Store service has been successfully started.

`GET /v1/health` is the lighter check used by the Docker image and the compose files. It answers HTTP 200 with an empty body, so use `curl -fsS` and check the exit code rather than the output:

```bash
curl -fsS http://localhost:8520/v1/health && echo OK
```

#### 7.1 Store REST endpoints

The Store node exposes these read-only endpoints on `server.port`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/health` | Liveness probe, HTTP 200 with an empty body |
| GET | `/actuator/health` | Spring Boot Actuator health, `{"status":"UP"}` |
| GET | `/actuator/prometheus` | Prometheus scrape endpoint |
| GET | `/` | Node summary, `leaderCount` and `partitionCount` |
| GET | `/-/state` | Node state, one of `STARTING`, `ONLINE`, `STOPPING` |
| GET | `/-/echo?name=<text>` | Echo check |
| GET | `/-/scan` | State of the running scan streams |
| GET | `/v1/partitions` | All Raft groups on this node with per-partition metrics. Add `?flags=accurate` for exact key counts, which is slower. |
| GET | `/v1/partition/{id}` | One Raft group by partition id, including role, leader, peers and committed index |
| GET | `/metrics/system` | Host CPU and memory metrics |
| GET | `/metrics/drive` | Disk metrics for the data paths |
| GET | `/metrics/raft` | JRaft node metrics, needs `raft.metrics: true` |

Actuator and Prometheus are reachable because the shipped configuration sets `management.endpoints.web.exposure.include: "*"` and `management.metrics.export.prometheus.enabled: true`.

The node also serves maintenance endpoints that change state or run heavy work: `PUT /-/state`, `GET /-/cleaner`, `GET /v1/partition/dump/{id}`, `GET /v1/partition/clean/{id}`, `POST /v1/compat?id=<partition>`, `GET /v1/arthasstart`, `POST /raft/options`, and the `/fix/*` and `/test/*` groups. Use them only for troubleshooting, and keep the REST port off untrusted networks.

#### 7.2 Check registration from PD

You can also check Store node status through the PD API:

```bash
curl -u store:admin http://localhost:8620/v1/stores
```

PD requires basic auth on its REST port. The user name must be one of `hg`, `store`, `hubble`, `vermeer`, and the password is not validated yet. A call with no credentials returns `{"status":-1,"error":"Unauthorized!"}`. Only `/v1/health`, `/actuator/*` and `/v1/prom/targets/*` are exempt.

If Store is configured successfully, the response should include status information for the current node, and `state: "Up"` means the node is running normally. A node stuck at `Pending` is usually missing from PD's `pd.initial-store-list`.

The example below shows a single Store node. If all three nodes are configured correctly and running, the `storeId` list should contain three IDs, and `stateCountMap.Up`, `numOfService`, and `numOfNormalService` should all be `3`.

```javascript
{
  "message": "OK",
  "data": {
    "stores": [
      {
        "storeId": 8319292642220586694,
        "address": "127.0.0.1:8500",
        "raftAddress": "127.0.0.1:8510",
        "version": "",
        "state": "Up",
        "deployPath": "/Users/{your_user_name}/hugegraph/hugegraph-store/apache-hugegraph-store-{version}/lib/hg-store-node-{version}.jar",
        "dataPath": "./storage",
        "startTimeStamp": 1754027127969,
        "registedTimeStamp": 1754027127969,
        "lastHeartBeat": 1754027909444,
        "capacity": 494384795648,
        "available": 346535829504,
        "partitionCount": 0,
        "graphSize": 0,
        "keyCount": 0,
        "leaderCount": 0,
        "serviceName": "127.0.0.1:8500-store",
        "serviceVersion": "",
        "serviceCreatedTimeStamp": 1754027127000,
        "partitions": []
      }
    ],
    "stateCountMap": {
      "Up": 1
    },
    "numOfService": 1,
    "numOfNormalService": 1
  },
  "status": 0
}
```
