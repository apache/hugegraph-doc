---
title: "HugeGraph-PD Quick Start"
linkTitle: "Install/Build HugeGraph-PD"
weight: 2
---

### 1 HugeGraph-PD Overview

HugeGraph-PD (Placement Driver) is the metadata management component of HugeGraph's distributed version, responsible for managing the distribution of graph data and coordinating storage nodes. It plays a central role in distributed HugeGraph, maintaining cluster status and coordinating HugeGraph-Store storage nodes.

PD keeps cluster metadata in an embedded RocksDB store under `pd.data-path` and replicates it across PD nodes with Raft, so a 3-node or 5-node PD cluster keeps serving while a minority of nodes is down. On top of that it registers and activates Store nodes, allocates and rebalances partitions, tracks Store heartbeats, and answers service discovery queries from Store and Server.

PD listens on three ports:

| Port | Default | Configured by | Used by |
|------|---------|---------------|---------|
| gRPC | `8686` | `grpc.port` | Store and Server clients |
| REST | `8620` | `server.port` | Management, health checks, metrics |
| Raft | `8610` | `raft.address` | The other PD nodes only |

### 2 Prerequisites

#### 2.1 Requirements

- Operating System: Linux or macOS (Windows has not been fully tested)
- Java version: ≥ 11
- Maven version: ≥ 3.5.0

### 3 Deployment

There are two ways to deploy the HugeGraph-PD component:

- Method 1: Download the tar package
- Method 2: Compile from source

#### 3.1 Download the tar package

Download the latest version of HugeGraph-PD from the Apache HugeGraph official download page:

```bash
# 1.7.0 is a historical release from the incubation period, so its file and directory names still include "incubating"
wget https://downloads.apache.org/hugegraph/1.7.0/apache-hugegraph-incubating-1.7.0.tar.gz
tar zxf apache-hugegraph-incubating-1.7.0.tar.gz
cd apache-hugegraph-incubating-1.7.0/apache-hugegraph-pd-incubating-1.7.0
```

#### 3.2 Compile from source

```bash
# 1. Clone the source code
git clone https://github.com/apache/hugegraph.git

# 2. Build the project
cd hugegraph
mvn clean install -DskipTests=true

# 3. After a successful build, the PD directory and packages are located at
#    hugegraph-pd/apache-hugegraph-pd-{version}          (unpacked PD distribution)
#    hugegraph-pd/apache-hugegraph-pd-{version}.tar.gz   (PD only package, Linux build hosts only)
#    target/apache-hugegraph-{version}.tar.gz            (PD + Store + Server package)
```

To build only the PD distribution and the modules it depends on:

```bash
mvn clean package -pl hugegraph-pd/hg-pd-dist -am -DskipTests
```

The unpacked distribution contains just three directories: `bin` (start and stop scripts), `conf` (`application.yml`, `application.yml.template`, `log4j2.xml`, `verify-license.json`) and `lib` (the `hg-pd-service` jar).

#### 3.3 Docker Deployment

The HugeGraph-PD Docker image is available on Docker Hub as `hugegraph/pd`.

> **Note**: The following steps assume you have already cloned or pulled the HugeGraph main repository locally, or at least have its `docker/` directory available.

Use the `docker compose` setup to deploy the complete 3-node cluster (PD + Store + Server):

```bash
cd hugegraph/docker
# Keep the version aligned with the latest release, for example 1.x.0
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-3pd-3store-3server.yml up -d
```

A single PD plus a single Store and Server is also available as `docker-compose-hstore.yml`.

To run a single PD node via `docker run`, configuration is provided via environment variables:

```bash
docker run -d \
  -p 8620:8620 \
  -p 8686:8686 \
  -p 8610:8610 \
  -e HG_PD_GRPC_HOST=<your-ip> \
  -e HG_PD_RAFT_ADDRESS=<your-ip>:8610 \
  -e HG_PD_RAFT_PEERS_LIST=<your-ip>:8610 \
  -e HG_PD_INITIAL_STORE_LIST=<store-ip>:8500 \
  -v /path/to/data:/hugegraph-pd/pd_data \
  --name hugegraph-pd \
  hugegraph/pd:1.7.0
```

**Environment variable reference:**

| Variable | Required | Default | Maps to | Description |
|----------|----------|---------|---------|-------------|
| `HG_PD_GRPC_HOST` | Yes | n/a | `grpc.host` | This node's hostname/IP for gRPC (e.g. `pd0` in Docker, `192.168.1.10` on bare metal) |
| `HG_PD_RAFT_ADDRESS` | Yes | n/a | `raft.address` | This node's Raft address (e.g. `pd0:8610`) |
| `HG_PD_RAFT_PEERS_LIST` | Yes | n/a | `raft.peers-list` | All PD peers (e.g. `pd0:8610,pd1:8610,pd2:8610`) |
| `HG_PD_INITIAL_STORE_LIST` | Yes | n/a | `pd.initial-store-list` | Expected store gRPC addresses (e.g. `store0:8500,store1:8500,store2:8500`) |
| `HG_PD_GRPC_PORT` | No | `8686` | `grpc.port` | gRPC server port |
| `HG_PD_REST_PORT` | No | `8620` | `server.port` | REST API port |
| `HG_PD_DATA_PATH` | No | `/hugegraph-pd/pd_data` | `pd.data-path` | Metadata storage path |
| `HG_PD_INITIAL_STORE_COUNT` | No | `1` | `pd.initial-store-count` | Minimum stores required for cluster availability |

The entrypoint refuses to start if any of the four required variables is missing, and it turns the values above into a `SPRING_APPLICATION_JSON` override, so the packaged `conf/application.yml` does not need editing. Any key not covered by an `HG_PD_*` variable keeps the value from that file. `JAVA_OPTS` is passed through to the JVM.

> **Note**: In Docker bridge networking, use container hostnames (e.g. `pd0`) for `HG_PD_GRPC_HOST` and `HG_PD_RAFT_ADDRESS` instead of IP addresses.

> **Deprecated aliases**: `GRPC_HOST`, `RAFT_ADDRESS`, `RAFT_PEERS`, `PD_INITIAL_STORE_LIST` still work but log a deprecation warning. Use the `HG_PD_*` names for new deployments.

The image ships a `HEALTHCHECK` that polls `GET /v1/health` on port `8620` every 15 seconds, with a 90 second start period and 3 retries, so `docker ps` reports real PD health. The entrypoint runs the start script with `-d false`, so the container process is Java itself and Docker's restart policy fires when it dies. The image also sets `STDOUT_MODE=true`, so `docker logs <container-name>` (e.g. `docker logs hg-pd0`) shows the PD log without exec-ing into the container.

See [docker/README.md](https://github.com/apache/hugegraph/blob/master/docker/README.md) for the full cluster setup guide.

### 4 Configuration

The main configuration file for PD is `conf/application.yml`. This is the file the distribution ships:

```yaml
spring:
  application:
    name: hugegraph-pd

management:
  metrics:
    export:
      prometheus:
        enabled: true
  endpoints:
    web:
      exposure:
        include: "*"

logging:
  config: 'file:./conf/log4j2.xml'

license:
  verify-path: ./conf/verify-license.json
  license-path: ./conf/hugegraph.license

grpc:
  # gRPC port for cluster mode
  port: 8686
  # Change to the actual local IPv4 address when deploying
  host: 127.0.0.1

server:
  # REST service port
  port: 8620

pd:
  # Storage path
  data-path: ./pd_data
  # Auto-expansion check cycle (seconds)
  patrol-interval: 1800
  # Minimum number of Store nodes required for cluster availability
  initial-store-count: 1
  # Store configuration information, format is IP:gRPC port
  initial-store-list: 127.0.0.1:8500

raft:
  # Raft address of this node
  address: 127.0.0.1:8610
  # Raft addresses of all PD nodes in the cluster
  peers-list: 127.0.0.1:8610

store:
  # Store offline time (seconds). After this time, the store is considered permanently unavailable
  max-down-time: 172800
  # Whether to enable store monitoring data storage
  monitor_data_enabled: true
  # Monitoring data interval
  monitor_data_interval: 1 minute
  # Monitoring data retention time
  monitor_data_retention: 1 day

partition:
  # Default number of replicas per partition
  default-shard-count: 1
  # Default maximum number of replicas per machine
  store-max-shard-count: 12
```

`conf/application.yml.template` is a second, unused copy with placeholders (`$GRPC_PORT$`, `$RAFT_ADDRESS$` and so on) for deployment tooling that generates the file. PD always reads `conf/application.yml`, which the start script passes as `-Dspring.config.location`.

#### 4.1 Configuration reference

Keys not present in `conf/application.yml` fall back to the built-in default listed below. Keys with no built-in default must be present, otherwise PD fails to start.

**gRPC and REST**

| Key | Shipped value | Built-in default | Description |
|-----|---------------|------------------|-------------|
| `grpc.host` | `127.0.0.1` | none, required | Address this PD advertises for gRPC. Store and Server connect here, so set it to a reachable IPv4 address or hostname, never `127.0.0.1` or `0.0.0.0`, in a distributed deployment. |
| `grpc.port` | `8686` | none, required | gRPC port. |
| `server.port` | `8620` | none, required | REST API port. Also the port reported in Raft member information. |

`application.yml.template` also carries `grpc.netty-server.max-inbound-message-size: 100MB`, but PD sets the gRPC server's inbound message limit to 1 GB in code, so that key has no effect.

**Raft**

| Key | Shipped value | Built-in default | Description |
|-----|---------------|------------------|-------------|
| `raft.address` | `127.0.0.1:8610` | none, required | Raft address of this node as `host:port`. Must be unique per node and must appear in `raft.peers-list`. |
| `raft.peers-list` | `127.0.0.1:8610` | none, required | Comma separated Raft addresses of every PD node, including this one. Must be identical on all nodes. |
| `raft.enable` | not set | `true` | When true, metadata writes go through the Raft state machine. When false, PD writes straight to its local store with no replication. |
| `raft.ip-whitelist.enabled` | not set | `true` | When true, the Raft RPC port accepts connections only from the addresses resolved from `raft.peers-list`; other clients are dropped and logged as `Blocked connection from <ip>`. The allowlist is re-resolved when the peer list changes, but a peer that keeps its hostname and changes IP (a restarted container, for example) needs a PD restart. |
| `raft.snapshotInterval` | not set | `300` | Seconds between Raft snapshots. |
| `raft.rpc-timeout` | not set | `10000` | Raft RPC connect, request and install-snapshot timeout, in milliseconds. |

**PD core**

| Key | Shipped value | Built-in default | Description |
|-----|---------------|------------------|-------------|
| `pd.data-path` | `./pd_data` | none, required | Metadata directory. Holds the RocksDB store in `rocksdb/` and the Raft log, metadata and snapshots in `pd_raft/`. |
| `pd.patrol-interval` | `1800` | `300` | Seconds between patrol runs, which check partition health across stores and rebalance partition counts. |
| `pd.initial-store-count` | `1` | `3` | Minimum number of active Store nodes. Below this the cluster state becomes `Cluster_Not_Ready` and the cluster is treated as unavailable. Set it to the number of stores you deploy. |
| `pd.initial-store-list` | `127.0.0.1:8500` | empty | Comma separated Store gRPC addresses (`ip:port`) that are activated automatically when they register. An entry may also carry a group id as `store_address/group_id`. |
| `pd.cluster_id` | not set | `1` | Cluster id, used to keep separate PD clusters apart. |

**Store management**

| Key | Shipped value | Built-in default | Description |
|-----|---------------|------------------|-------------|
| `store.keepAlive-timeout` | not set | `300` | Seconds without a heartbeat after which a Store is treated as temporarily unavailable and its partition leaders move to other replicas. |
| `store.max-down-time` | `172800` | `1800` | Seconds after which a Store is treated as permanently unavailable and its replicas are reallocated to other machines. |
| `store.monitor_data_enabled` | `true` | `false` | Whether to persist Store monitoring samples. |
| `store.monitor_data_interval` | `1 minute` | `1 minute` | Sampling interval, written as `<number> <unit>` with unit one of `second`, `minute`, `hour`, `day`, `month`, `year`. The number defaults to 1 when omitted. |
| `store.monitor_data_retention` | `1 day` | `1 day` | How long monitoring samples are kept, same format as above. |

**Partitions**

| Key | Shipped value | Built-in default | Description |
|-----|---------------|------------------|-------------|
| `partition.default-shard-count` | `1` | `3` | Number of replicas per partition. Use `3` for a production cluster. |
| `partition.store-max-shard-count` | `12` | `24` | Maximum number of partition replicas one Store holds. |

The initial partition count is derived from these two values and the size of `pd.initial-store-list`:

```text
initial partitions = store count * partition.store-max-shard-count / partition.default-shard-count
```

**Discovery, license and metrics**

| Key | Shipped value | Built-in default | Description |
|-----|---------------|------------------|-------------|
| `discovery.heartbeat-try-count` | not set | `3` | Number of missed heartbeats after which a registered client's discovery entry is deleted. |
| `license.verify-path` | `./conf/verify-license.json` | none, required | Path to the license verification descriptor. Read by the `/v1/license` endpoints. |
| `license.license-path` | `./conf/hugegraph.license` | none, required | Path to the license file. The distribution ships `verify-license.json` but no license file, so the license endpoints report an error until one is supplied. |
| `auth.secret-key` | not set | built-in constant | HS256 secret used to sign the PD tokens handed back to internal clients. |
| `management.metrics.export.prometheus.enabled` | `true` | Spring Boot default | Exposes `/actuator/prometheus`. |
| `management.endpoints.web.exposure.include` | `"*"` | Spring Boot default | Actuator endpoints to expose. |
| `logging.config` | `file:./conf/log4j2.xml` | none | Log4j2 configuration. Writes `logs/hugegraph-pd.log`, `logs/hugegraph-pd_raft.log` and `logs/audit-hugegraph-pd.log`. |

**Thread pools**

| Key | Built-in default | Description |
|-----|------------------|-------------|
| `thread.pool.grpc.core` | `600` | Core size of the pool that serves gRPC calls. |
| `thread.pool.grpc.max` | `1000` | Maximum size of that pool. |
| `thread.pool.grpc.queue` | unbounded | Queue capacity of that pool. |
| `job.uninterruptibleThreadPool.core` | `0` | Core size of the background metadata job pool. A value of 0 or less means half the available processors. |
| `job.uninterruptibleThreadPool.max` | `256` | Maximum size of that pool. |
| `job.uninterruptibleThreadPool.queue` | unbounded | Queue capacity of that pool. |

#### 4.2 Single-node configuration

The shipped `conf/application.yml` already is a working single-node configuration. It is meant for development and testing: one PD node has no Raft quorum to lose, and `partition.default-shard-count: 1` keeps a single replica per partition.

```yaml
grpc:
  host: 127.0.0.1
  port: 8686
server:
  port: 8620
raft:
  address: 127.0.0.1:8610
  peers-list: 127.0.0.1:8610
pd:
  data-path: ./pd_data
  initial-store-count: 1
  initial-store-list: 127.0.0.1:8500
partition:
  default-shard-count: 1
```

#### 4.3 Three-node cluster configuration

For a production cluster run 3 or 5 PD nodes, an odd number so Raft always has a quorum. A 3-node cluster tolerates one node failure. `raft.peers-list` must list every node and must be byte-for-byte identical on all of them, while `grpc.host` and `raft.address` differ per node.

Node 1 (`192.168.1.10`):

```yaml
grpc:
  host: 192.168.1.10
  port: 8686
server:
  port: 8620
raft:
  address: 192.168.1.10:8610
  peers-list: 192.168.1.10:8610,192.168.1.11:8610,192.168.1.12:8610
pd:
  data-path: /data/pd
  initial-store-count: 3
  initial-store-list: 192.168.1.20:8500,192.168.1.21:8500,192.168.1.22:8500
partition:
  default-shard-count: 3
```

Node 2 (`192.168.1.11`) and node 3 (`192.168.1.12`) use the same file with `grpc.host` and `raft.address` changed to their own address:

```yaml
# node 2
grpc:
  host: 192.168.1.11
raft:
  address: 192.168.1.11:8610
  peers-list: 192.168.1.10:8610,192.168.1.11:8610,192.168.1.12:8610

# node 3
grpc:
  host: 192.168.1.12
raft:
  address: 192.168.1.12:8610
  peers-list: 192.168.1.10:8610,192.168.1.11:8610,192.168.1.12:8610
```

To put all three PD nodes on one machine for testing, give each node its own `pd.data-path` and its own ports, for example raft `8610/8611/8612`, gRPC `8686/8687/8688` and REST `8620/8621/8622`.

In Docker bridge networking the same configuration comes from environment variables and uses container hostnames instead of IP addresses:

```yaml
# pd0
HG_PD_GRPC_HOST: pd0
HG_PD_RAFT_ADDRESS: pd0:8610
HG_PD_RAFT_PEERS_LIST: pd0:8610,pd1:8610,pd2:8610
HG_PD_INITIAL_STORE_LIST: store0:8500,store1:8500,store2:8500
HG_PD_INITIAL_STORE_COUNT: 3

# pd1
HG_PD_GRPC_HOST: pd1
HG_PD_RAFT_ADDRESS: pd1:8610
HG_PD_RAFT_PEERS_LIST: pd0:8610,pd1:8610,pd2:8610

# pd2
HG_PD_GRPC_HOST: pd2
HG_PD_RAFT_ADDRESS: pd2:8610
HG_PD_RAFT_PEERS_LIST: pd0:8610,pd1:8610,pd2:8610
```

### 5 Start and Stop

#### 5.1 Start PD

In the PD installation directory, execute:

```bash
./bin/start-hugegraph-pd.sh
```

The script requires a JDK of at least version 11 on `PATH` or in `JAVA_HOME`, and it exits without doing anything if it finds a Java process already using this installation's `conf` directory.

Supported flags:

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `-d` | `true`, `false` | `true` | Daemon mode. See the note below. |
| `-g` | `zgc`, `ZGC` | not set | Garbage collector. Leave the flag off for the default G1GC. Any other value, `g1` included, aborts the start. |
| `-j` | JVM options | empty | Extra JVM options, for example `-j "-Xmx8g -Xms8g"`. |
| `-y` | `true`, `false` | `false` | Attach the OpenTelemetry Java agent. The agent is downloaded into `plugins/` on first use, its MD5 is verified, and traces are exported over gRPC to `http://127.0.0.1:4317`. |

The `-d` flag controls daemon mode:

- `-d true` (default): run as a background daemon; the script returns immediately.
- `-d false`: run in foreground. The script `exec`s Java, so the container or supervisor process IS Java. Use this when running under Docker or a process supervisor (systemd, supervisord) so crashes are detected and the service is restarted automatically.

Each flag also has an environment variable equivalent: `DAEMON`, `GC_OPTION`, `USER_OPTION` and `OPEN_TELEMETRY`. Setting `JAVA_OPTIONS` replaces the computed heap settings entirely; otherwise the script sizes the heap between 512 MB and 32 GB from available memory. Setting `STDOUT_MODE=true` leaves the JVM output on stdout instead of redirecting it to `logs/hugegraph-pd-stdout.log`, which is what the Docker image does.

After successful startup, you can see logs similar to the following in `logs/hugegraph-pd-stdout.log`:

```
YYYY-mm-dd xx:xx:xx [main] [INFO] o.a.h.p.b.HugePDServer - Started HugePDServer in x.xxx seconds (JVM running for x.xxx)
```

The process id is written to `bin/pid`.

#### 5.2 Stop PD

In the PD installation directory, execute:

```bash
./bin/stop-hugegraph-pd.sh
```

The script reads `bin/pid`, sends the process a termination signal, waits up to 30 seconds for it to exit, and removes the pid file. If `bin/pid` is missing it reports that and exits successfully.

### 6 Startup Order in a Distributed Cluster

Start the components in this order:

1. **All PD nodes.** They form the Raft group and elect a leader. Wait until every node answers `GET /v1/health`.
2. **All Store nodes.** Each Store registers with PD over gRPC, and PD activates the ones listed in `pd.initial-store-list`. Wait until `GET /v1/stores` reports `"state": "Up"` for every Store.
3. **All Server nodes.** A Server reads `pd.peers` and depends on PD reporting at least one live Store before partitions can be assigned.

The Docker Compose topologies enforce exactly this. Store containers wait on PD's `/v1/health` healthcheck through `depends_on` with `condition: service_healthy`, Server containers wait the same way on the Store healthcheck, and the Server entrypoint then polls PD's `/v1/stores` until a Store reports `Up` before it starts HugeGraph.

PD is also the last component to stop: shut down Server, then Store, then PD.

### 7 Verification

#### 7.1 REST API authentication

Except for `/actuator/*`, `/v1/health` and `/v1/prom/targets/*`, every PD REST path requires an HTTP Basic `Authorization` header whose user name is one of the internal service names `hg`, `store`, `hubble` or `vermeer`. A request without the header is answered with:

```json
{"status": -1, "error": "Unauthorized!"}
```

The password is not validated yet, so any value works. The Server's own `bin/wait-storage.sh` uses `store:admin` and lets you override it with `PD_AUTH_USER` and `PD_AUTH_PASSWORD`, so the examples below use the same credentials:

```bash
curl -u store:admin http://localhost:8620/v1/stores
```

> **Warning**: This check is only meant to separate HugeGraph's own components from other traffic. Do not expose the PD REST or gRPC ports to an untrusted network. Restrict them with firewall rules or security groups, and keep `raft.ip-whitelist.enabled` on so the Raft port only accepts the configured peers.

#### 7.2 Health check

`GET /v1/health` needs no credentials and is what the Docker healthcheck uses. It answers `200` with an empty body:

```bash
curl -i http://localhost:8620/v1/health
```

The Spring Boot actuator endpoint also works and is more readable:

```bash
curl http://localhost:8620/actuator/health
```

If it returns `{"status":"UP"}`, it indicates that the PD service has been successfully started.

#### 7.3 Cluster and member status

Check the PD members and which node is the Raft leader:

```bash
curl -u store:admin http://localhost:8620/v1/members
```

The response carries `pdList`, the elected `pdLeader`, `numOfService`, `numOfNormalService` and a `stateCountMap`. In a healthy 3-node PD cluster `numOfService` and `numOfNormalService` are both `3` and exactly one member has `role: "Leader"`.

`GET /v1/cluster` returns the same member list together with the Store list, graph list and overall cluster state, and `GET /` returns a short summary (leader address, cluster state, member count, store count, graph count, partition count).

#### 7.4 Store status

You can also verify Store node status through the PD API:

```bash
curl -u store:admin http://localhost:8620/v1/stores
```

If the response shows `state` as `Up`, the corresponding Store node is running normally. The example below shows a single Store node. In a healthy 3-node deployment, the `storeId` list should contain three IDs, and `stateCountMap.Up`, `numOfService`, and `numOfNormalService` should all be `3`.

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
        "deployPath": "/Users/{your_user_name}/hugegraph/apache-hugegraph-incubating-1.7.0/apache-hugegraph-store-incubating-1.7.0/lib/hg-store-node-1.7.0.jar",
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

#### 7.5 Other REST endpoints

All paths below are relative to `http://<pd-host>:8620` and need the Basic header from section 7.1 unless noted.

| Method and path | Description |
|-----------------|-------------|
| `GET /` | Brief cluster statistics: leader, state, member count, store count, graph count, partition count |
| `GET /v1/health` | Health check, no authentication required |
| `GET /v1/cluster` | Full cluster statistics: PD members, stores, graphs, partitions |
| `GET /v1/members` | PD member list with roles and the elected leader |
| `POST /v1/members/change` | Change the Raft peer list, body `{"peerList": "..."}` |
| `GET /v1/stores` | Registered Store nodes with state and per-store statistics |
| `GET /v1/store/{storeId}` | One Store node |
| `POST /v1/store/{storeId}` | Update a Store's state, body `{"storeState": "..."}` |
| `DELETE /v1/store/{storeId}` | Remove a Store from the cluster |
| `POST /v1/store/log` | Store state change log, body `{"startTime": "...", "endTime": "..."}` |
| `GET /v1/storesAndStats` | Raw Store metadata, for debugging |
| `GET /v1/store_monitor/{storeId}` | Store monitoring samples as text |
| `GET /v1/store_monitor/json/{storeId}` | Store monitoring samples as JSON |
| `GET /v1/shards` | Every shard of every partition, with store id, role, state and progress |
| `GET /v1/shardGroups` | Shard groups |
| `GET /v1/shardGroupsCache` | Shard groups from PD's in-memory cache |
| `GET /v1/shardLeaders` | Partition leaders grouped by Store raft address |
| `GET /v1/balanceLeaders` | Rebalance partition leaders across Stores |
| `GET /v1/partitions` | Partition list with state and statistics |
| `GET /v1/highLevelPartitions` | Partitions with per-graph key counts and data sizes |
| `GET /v1/partitionsAndStats` | Raw partition metadata, for debugging |
| `POST /v1/partitions/log` | Partition change log, body `{"startTime": "...", "endTime": "..."}` |
| `GET /v1/resetPartitionState` | Reset the state of every partition |
| `GET /v1/graphs` | Graph list |
| `GET /v1/graph/**` | One graph by name |
| `POST /v1/graph/**` | Update a graph's partition count, body `{"partitionCount": N}` |
| `GET /v1/graph/partitionSizeRange` | Minimum and maximum partition count the cluster accepts |
| `GET /v1/graph-spaces` | Graph space list |
| `GET /v1/graph-spaces/**` | One graph space |
| `POST /v1/graph-spaces/**` | Update a graph space |
| `POST /v1/registry` | Register a service instance for discovery |
| `POST /v1/registryInfo` | Query registered instances |
| `GET /v1/allInfo` | All registered instances |
| `GET /v1/license` | License context |
| `GET /v1/license/machineInfo` | IP and MAC addresses seen by the license check |
| `GET /v1/task/patrolStores` | Run the store patrol task now |
| `GET /v1/task/patrolPartitions` | Run the partition patrol task now |
| `GET /v1/task/balancePartitions` | Rebalance partitions across Stores |
| `GET /v1/task/splitPartitions` | Run automatic partition splitting now |
| `GET /v1/task/balanceLeaders` | Rebalance partition leaders |
| `GET /v1/task/compact` | Instruct Store nodes to compact the RocksDB files of their partitions |
| `GET /v1/prom/targets/{appName}` | Prometheus service discovery targets, no authentication required |
| `GET /v1/prom/targets-all` | Prometheus targets for all app types |
| `GET /v1/prom/sd_config` | Prometheus HTTP service discovery config |
| `GET /actuator/health` | Spring Boot health, no authentication required |
| `GET /actuator/metrics` | Spring Boot metrics, no authentication required |
| `GET /actuator/prometheus` | Prometheus scrape endpoint, no authentication required |

The two `log` endpoints take a time range as `{"startTime": "...", "endTime": "..."}`; `yyyy-MM-dd HH:mm:ss` and `yyyy-MM-dd` are among the accepted formats.

PD registers its own meters under the `hg` prefix, so `/actuator/prometheus` exposes `hg_up`, `hg_graphs`, `hg_stores` and `hg_terms` alongside the standard JVM metrics, plus per-graph partition and size meters once graphs exist.
