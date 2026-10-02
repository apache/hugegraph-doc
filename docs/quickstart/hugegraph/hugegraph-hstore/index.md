# HugeGraph-Store Quick Start

LLMS index: [llms.txt](/llms.txt)

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

Apache downloads currently provide the complete 1.7.0 binary bundle containing PD, Store, and Server, without a separate Store binary. Verify version, signatures, and SHA512 on the [official download page](https://hugegraph.apache.org/docs/download/download/). This historical incubating release retains `incubating` in archive and directory names:

```bash
# Historical release 1.7.0 retains incubating in filenames and directories
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

`HG_STORE_*` mappings are current master features, absent from Server tag `1.7.0`. These Docker examples require PD, Store, and HStore Server images built from the same current master source with matching local tags:

```bash
# Run from the HugeGraph repository root
docker build -f hugegraph-pd/Dockerfile -t hugegraph/pd:local .
docker build -f hugegraph-store/Dockerfile -t hugegraph/store:local .
docker build -f hugegraph-server/Dockerfile-hstore -t hugegraph/server:local .
```

Before first startup, create `.env` in `docker/` following the [authentication environment instructions](https://github.com/apache/hugegraph/blob/master/docker/README.md#create-the-authentication-environment).
The procedure uses `umask 077` and refuses to overwrite existing files. Keep an existing `.env` and add missing entries. Never regenerate `HG_PD_AUTH_SECRET_KEY` for initialized data directories. Although `.gitignore` excludes this file, do not commit it.
In every new shell, load the same file from `docker/` before Compose or PD REST commands:

```bash
# Run from the HugeGraph repository root
cd docker
set -a; . ./.env; set +a
: "${HG_PD_AUTH_SECRET_KEY:?Set HG_PD_AUTH_SECRET_KEY in .env}"
# Start PD, Store, and Server without optional Hubble
HUGEGRAPH_VERSION=local HUGEGRAPH_PULL_POLICY=never \
  docker compose -f docker-compose-hstore.yml \
  up -d --wait pd store server
```

Load the same secret before subsequent restarts or PD REST calls; do not regenerate it for initialized directories. Explicitly include `HUGEGRAPH_VERSION=local` and `HUGEGRAPH_PULL_POLICY=never` in every Compose lifecycle command.

To start Hubble, use the topology-specific untracked configuration: minimal `docker-compose-hstore.yml` mounts `conf/hubble/hstore.local.properties`;
HA `docker-compose-3pd-3store-3server.yml` mounts `conf/hubble/hstore-ha.local.properties`.
The README initialization creates both files with the shared PD secret. If missing or requiring updates, load existing `.env` from `docker/` and run:

```bash
set -a; . ./.env; set +a
./set-hubble-pd-password.sh hstore      # Minimal topology
./set-hubble-pd-password.sh hstore-ha  # HA topology
```

Multi-node service names are `pd0`–`pd2`, `store0`–`store2`, and `server0`–`server2`. This master Compose file also requires matching locally built images; do not mix `HUGEGRAPH_VERSION=1.7.0` release images with master Compose.

To run master-built Store alone, replace example addresses with actual routable Store and PD addresses:

```bash
docker run -d \
  -p 8520:8520 -p 8500:8500 -p 8510:8510 \
  -e HG_STORE_PD_ADDRESS=192.168.1.10:8686 \
  -e HG_STORE_GRPC_HOST=192.168.1.20 \
  -e HG_STORE_RAFT_ADDRESS=192.168.1.20:8510 \
  -v /path/to/storage:/hugegraph-store/storage \
  --name hugegraph-store \
  hugegraph/store:local
```

**Current Master Docker Environment Variables:**

| Variable | Required | Default | Configuration key | Description |
|------|------|--------|------------|------|
| `HG_STORE_PD_ADDRESS` | Yes | None | `pdserver.address` | Comma-separated PD gRPC addresses. |
| `HG_STORE_GRPC_HOST` | Yes | None | `grpc.host` | Advertised hostname/IP; use a container hostname within a container network. |
| `HG_STORE_RAFT_ADDRESS` | Yes | None | `raft.address` | This node's Raft address. |
| `HG_STORE_GRPC_PORT` | No | `8500` | `grpc.port` | gRPC service port. |
| `HG_STORE_REST_PORT` | No | `8520` | `server.port` | REST API port. |
| `HG_STORE_DATA_PATH` | No | `/hugegraph-store/storage` | `app.data-path` | Data path. |

The master entrypoint writes these values into `SPRING_APPLICATION_JSON`, overriding image `conf/application.yml`. Other options still come from that file and `application-pd.yml`; Java runs in the foreground. Deprecated `PD_ADDRESS`, `GRPC_HOST`, and `RAFT_ADDRESS` remain supported with warnings.

PD and Store Docker `HEALTHCHECK` use `/v1/health`, confirming only local REST responses. Compose `depends_on` uses the same startup gate; separately verify PD `/v1/ready` and `Up` Store state in `/v1/stores`. Store defaults to `STDOUT_MODE=true`; its Dockerfile declares only `EXPOSE 8520`, so publish gRPC `8500` and Raft `8510` separately if needed outside the Docker network.

### 4 Configuration

Store reads two files under `conf/`. Release 1.7.0 sources: [application.yml](https://github.com/apache/hugegraph/blob/1.7.0/hugegraph-store/hg-store-dist/src/assembly/static/conf/application.yml), [application-pd.yml](https://github.com/apache/hugegraph/blob/1.7.0/hugegraph-store/hg-store-dist/src/assembly/static/conf/application-pd.yml). Master sources: [application.yml](https://github.com/apache/hugegraph/blob/master/hugegraph-store/hg-store-dist/src/assembly/static/conf/application.yml), [application-pd.yml](https://github.com/apache/hugegraph/blob/master/hugegraph-store/hg-store-dist/src/assembly/static/conf/application-pd.yml). Master places RocksDB settings in the second file, included through `spring.profiles.include: pd`; startup selects `application.yml`.

- `application.yml`: Main PD address, ports, Raft, and data path settings.
- `application-pd.yml`: Included through `spring.profiles.include: pd`; RocksDB memory and Actuator exposure.

#### 4.1 application.yml

The following tables were checked against distribution values and Java defaults at Server master commit `2f827d6e8c9c62ae858f2fc122b3a192d015e2f4`. Use tagged configuration for release 1.7.0 without replacing it with another version's files.

#### 4.2 application-pd.yml

This file contains only `rocksdb` and Actuator exposure settings.

> [!WARNING]
> **Protect Server and Store ports separately in production**
>
> Enable [Server authentication and authorization](/docs/config/config-authentication/), an IP allowlist, and minimum graph API permissions; retain and protect Server `audit-*.log`. These settings do not protect Store: master exposes all Actuator endpoints without PD-style Basic authentication. Restrict Store REST, gRPC, and Raft to cluster nodes and trusted operations networks.


#### 4.3 Configuration reference

"Master distribution value" comes from the two master files above. "Code default" is the fallback when a key is absent; rely on code defaults for options omitted from the distribution files.

**Core**

| Key | Master distribution value | Code default | Meaning |
|-----|---------|--------------|---------|
| `pdserver.address` | `localhost:8686` | required | PD gRPC endpoints, comma separated. Store registers itself here and receives its partition assignment. Must be PD's `grpc.port`, not its REST port. |
| `grpc.host` | `127.0.0.1` | required | Address this node advertises for its own gRPC service. Set it to a routable IP or hostname, `127.0.0.1` is only usable for a single-machine setup. |
| `grpc.port` | `8500` | required | gRPC port. Server and the Store client connect here. |
| `grpc.netty-server.max-inbound-message-size` | `1000MB` | gRPC default | Maximum size of a single inbound gRPC message. Bound by the `grpc-spring-boot-starter` Netty server. |
| `grpc.server.wait-time` | not set | `3600` | Seconds a scan stream waits for the client to consume a page before the server aborts it. |
| `server.port` | `8520` | required | REST and Actuator port. Also reported to PD as the `rest.port` label. |

**Raft**

| Key | Master distribution value | Code default | Meaning |
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

| Key | Master distribution value | Code default | Meaning |
|-----|---------|--------------|---------|
| `app.data-path` | `./storage` | `store` | RocksDB data directory. Multiple paths separated by commas spread partitions over several disks. |
| `app.raft-path` | commented out | empty | Directory for Raft logs and snapshots. Falls back to `app.data-path` when empty. |
| `app.fake-pd` | not set | `false` | Built-in PD mode for standalone testing. Do not use it in production. |
| `app.placeholder-size` | not set | `10` | Size in GB of a `placeholder` file created in each data path at startup, so space can be freed in an emergency. `0` disables it. |
| `app.label.<name>` | not set | none | Arbitrary key/value labels sent to PD in the store heartbeat. The node adds `rest.port` on its own. |

**RocksDB**

| Key | Master distribution value | Code default | Meaning |
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

1. **All PD nodes first.** Each Store's `grpc.host:grpc.port` must appear in PD `pd.initial-store-list`, or the node remains `Pending` instead of `Up`, blocking partition allocation. On master, verify HTTP `200` with `ready:true` from every PD `/v1/ready` first; `/v1/health` is liveness only.
2. **Store next.** Registration retries while PD is unreachable, logging `store heartbeat error: PD UNREACHABLE`.
3. **Server last.** Every Store should report `Up`; partitions must be ready before opening or initializing graphs.

Master Compose uses `depends_on: condition: service_healthy` for local liveness, but PD and Store Docker checks only call `/v1/health`; they do not confirm Raft quorum or Store registration. Server waits for PD to report at least one `Up` Store. Operators should still check PD `/v1/ready` and `/v1/stores`.

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

Actuator `{"status":"UP"}` confirms local Store application health, without proving registration as `Up` in PD.

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
| GET | `/-/state` | Operator-set `STARTING`, `ONLINE`, or `STOPPING` flag; distinct from PD registration state |
| GET | `/-/echo?name=<text>` | Echo check |
| GET | `/-/scan` | State of the running scan streams |
| GET | `/v1/partitions` | All Raft groups on this node with per-partition metrics. Add `?flags=accurate` for exact key counts, which is slower. |
| GET | `/v1/partition/{id}` | One Raft group by partition id, including role, leader, peers and committed index |
| GET | `/metrics/system` | Host CPU and memory metrics |
| GET | `/metrics/drive` | Disk metrics for the data paths |
| GET | `/metrics/raft` | JRaft node metrics, needs `raft.metrics: true` |

Master Store configuration exposes all Actuator endpoints with `management.endpoints.web.exposure.include: "*"` and enables Prometheus. These endpoints lack PD REST Basic protection; restrict Store REST network access.

The node also serves maintenance endpoints that change state or run heavy work: `PUT /-/state`, `GET /-/cleaner`, `GET /v1/partition/dump/{id}`, `GET /v1/partition/clean/{id}`, `POST /v1/compat?id=<partition>`, `GET /v1/arthasstart`, `POST /raft/options`, and the `/fix/*` and `/test/*` groups. Use them only for troubleshooting, and keep the REST port off untrusted networks.

#### 7.2 Check registration from PD

You can also check Store node status through the PD API:

```bash
curl -u "store:${HG_PD_AUTH_SECRET_KEY:?Set the PD deployment secret first}" \
  http://localhost:8620/v1/stores
```

For master builds, PD REST usernames must be `hg`, `store`, `hubble`, or `vermeer`, and the password must equal PD `auth.secret-key`. `HG_PD_AUTH_SECRET_KEY` configures PD and Server in Compose. `/v1/health`, `/v1/ready`, `/actuator/*`, and `/v1/prom/targets/*` require no authentication. Release 1.7.0 checks only usernames, without comparing passwords; do not use that old behavior for master builds.

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

#### 7.3 Minimal Graph Read/Write Verification

After Store appears as `Up` in PD, start an HStore-backed Server connected to the same PD cluster. See the [Server Quick Start](./hugegraph-server.md). Once `GET /versions` responds and the default `hugegraph` graph is loaded, create a property key, vertex label, and vertex, then read it:

```bash
SERVER_URL=http://localhost:8080
GRAPH_URL="$SERVER_URL/graphspaces/DEFAULT/graphs/hugegraph"

# Names must be unique within the graphspace; choose new names if they already exist
curl -fsS -X POST "$GRAPH_URL/schema/propertykeys" \
  -H 'Content-Type: application/json' \
  -d '{"name":"pd_store_demo_name","data_type":"TEXT","cardinality":"SINGLE","properties":[]}'

curl -fsS -X POST "$GRAPH_URL/schema/vertexlabels" \
  -H 'Content-Type: application/json' \
  -d '{"name":"pd_store_demo_vertex","id_strategy":"CUSTOMIZE_STRING","properties":["pd_store_demo_name"],"primary_keys":[],"nullable_keys":[]}'

curl -fsS -X POST "$GRAPH_URL/graph/vertices" \
  -H 'Content-Type: application/json' \
  -d '{"id":"pd-store-demo-1","label":"pd_store_demo_vertex","properties":{"pd_store_demo_name":"stored in HStore"}}'

curl -fsS "$GRAPH_URL/graph/vertices/%22pd-store-demo-1%22"
```

The final response should contain vertex ID `pd-store-demo-1` and property `pd_store_demo_name`. If Server authentication is enabled, add credentials to each request.

---

Backlinks:

- [Config HStore Backend](/docs/config/config-backend-hstore/)
- [Design Concepts (legacy)](/docs/guides/desgin-concept/)
- [System Introduction](/docs/introduction/)
- [HugeGraph (OLTP)](/docs/quickstart/hugegraph/)
- [Install/Build HugeGraph-PD](/docs/quickstart/hugegraph/hugegraph-pd/)
- [Install/Build HugeGraph Server](/docs/quickstart/hugegraph/hugegraph-server/)
- [Hubble with HStore](/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/)
