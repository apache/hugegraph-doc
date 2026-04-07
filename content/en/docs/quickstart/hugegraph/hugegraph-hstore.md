---
title: "HugeGraph-Store Quick Start"
linkTitle: "Install/Build HugeGraph-Store"
weight: 3
---

### 1 HugeGraph-Store Overview

HugeGraph-Store is the storage node component of HugeGraph's distributed version, responsible for actually storing and managing graph data. It works in conjunction with HugeGraph-PD to form HugeGraph's distributed storage engine, providing high availability and horizontal scalability.

### 2 Prerequisites

#### 2.1 Requirements

- Operating System: Linux or macOS (Windows has not been fully tested)
- Java version: ≥ 11
- Maven version: ≥ 3.5.0
- Deploy HugeGraph-PD first for multi-node deployment

### 3 Deployment

There are two ways to deploy the HugeGraph-Store component:

- Method 1: Download the tar package
- Method 2: Compile from source

#### 3.1 Download the tar package

Download the latest version of HugeGraph-Store from the Apache HugeGraph official download page:

```bash
# Replace {version} with the latest version number, e.g., 1.5.0
wget https://downloads.apache.org/hugegraph/{version}/apache-hugegraph-incubating-{version}.tar.gz  
tar zxf apache-hugegraph-incubating-{version}.tar.gz
cd apache-hugegraph-incubating-{version}/apache-hugegraph-hstore-incubating-{version}
```

#### 3.2 Compile from source

```bash
# 1. Clone the source code
git clone https://github.com/apache/hugegraph.git

# 2. Build the project
cd hugegraph
mvn clean install -DskipTests=true

# 3. After successful compilation, the Store module build artifacts will be located at
#    apache-hugegraph-incubating-{version}/apache-hugegraph-hstore-incubating-{version}
#    target/apache-hugegraph-incubating-{version}.tar.gz
```

#### 3.3 Docker Deployment

The HugeGraph-Store Docker image is available on Docker Hub as `hugegraph/store`.

> **Note**: The following steps assume you have already cloned or pulled the HugeGraph main repository locally, or at least have its `docker/` directory available.

Use the compose file to deploy the complete 3-node cluster (PD + Store + Server):

```bash
cd hugegraph/docker
# Keep the version aligned with the latest release, for example 1.x.0
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

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HG_STORE_PD_ADDRESS` | Yes | — | PD gRPC addresses (e.g. `pd0:8686,pd1:8686,pd2:8686`) |
| `HG_STORE_GRPC_HOST` | Yes | — | This node's hostname/IP for gRPC (e.g. `store0`) |
| `HG_STORE_RAFT_ADDRESS` | Yes | — | This node's Raft address (e.g. `store0:8510`) |
| `HG_STORE_GRPC_PORT` | No | `8500` | gRPC server port |
| `HG_STORE_REST_PORT` | No | `8520` | REST API port |
| `HG_STORE_DATA_PATH` | No | `/hugegraph-store/storage` | Data storage path |

> **Note**: In Docker bridge networking, use container hostnames (e.g. `store0`) for `HG_STORE_GRPC_HOST` instead of IP addresses.

> **Deprecated aliases**: `PD_ADDRESS`, `GRPC_HOST`, `RAFT_ADDRESS` still work but log a deprecation warning. Use the `HG_STORE_*` names for new deployments.

### 4 Configuration

The main configuration file for Store is `conf/application.yml`. Here are the key configuration items:

```yaml
pdserver:
  # PD service address, multiple PD addresses are separated by commas (configure PD's gRPC port)
  address: 127.0.0.1:8686

grpc:
  # gRPC service address
  host: 127.0.0.1
  port: 8500
  netty-server:
    max-inbound-message-size: 1000MB

raft:
  # raft cache queue size
  disruptorBufferSize: 1024
  address: 127.0.0.1:8510
  max-log-file-size: 600000000000
  # Snapshot generation time interval, in seconds
  snapshotInterval: 1800

server:
  # REST service address
  port: 8520

app:
  # Storage path, supports multiple paths separated by commas
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

For multi-node deployment, you need to modify the following configurations for each Store node:

1. `grpc.port` (RPC port) for each node
2. `raft.address` (Raft protocol port) for each node
3. `server.port` (REST port) for each node
4. `app.data-path` (data storage path) for each node

### 5 Start and Stop

#### 5.1 Start Store

Ensure that the PD service is already started, then in the Store installation directory, execute:

```bash
./bin/start-hugegraph-store.sh
```

After successful startup, you can see logs similar to the following in `logs/hugegraph-store-server.log`:

```
YYYY-mm-dd xx:xx:xx [main] [INFO] o.a.h.s.n.StoreNodeApplication - Started StoreNodeApplication in x.xxx seconds (JVM running for x.xxx)
```

#### 5.2 Stop Store

In the Store installation directory, execute:

```bash
./bin/stop-hugegraph-store.sh
```

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

#### 6.3 Docker Distributed Cluster Configuration

The distributed Store cluster definition is included in `docker/docker-compose-3pd-3store-3server.yml`. Each Store node gets its own hostname and environment variables:

```yaml
# store0
HG_STORE_PD_ADDRESS: pd0:8686,pd1:8686,pd2:8686
HG_STORE_GRPC_HOST: store0
HG_STORE_GRPC_PORT: "8500"
HG_STORE_REST_PORT: "8520"
HG_STORE_RAFT_ADDRESS: store0:8510
HG_STORE_DATA_PATH: /hugegraph-store/storage

# store1
HG_STORE_PD_ADDRESS: pd0:8686,pd1:8686,pd2:8686
HG_STORE_GRPC_HOST: store1
HG_STORE_RAFT_ADDRESS: store1:8510

# store2
HG_STORE_PD_ADDRESS: pd0:8686,pd1:8686,pd2:8686
HG_STORE_GRPC_HOST: store2
HG_STORE_RAFT_ADDRESS: store2:8510
```

Store nodes start only after all PD nodes pass healthchecks (`/v1/health`), enforced via `depends_on: condition: service_healthy`.

To view runtime logs for a running Store container use `docker logs <container-name>` (e.g. `docker logs hg-store0`).

See [docker/README.md](https://github.com/apache/hugegraph/blob/master/docker/README.md) for the full setup guide.

### 7 Verify Store Service

Confirm that the Store service is running properly:

```bash
curl http://localhost:8520/actuator/health
```

If it returns `{"status":"UP"}`, it indicates that the Store service has been successfully started.

Additionally, you can check the status of Store nodes in the cluster through the PD API:

```bash
curl http://localhost:8620/v1/stores
```

If Store is configured successfully, the response should include status information for the current node, and `state: "Up"` means the node is running normally.

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
        "deployPath": "/Users/{your_user_name}/hugegraph/apache-hugegraph-incubating-1.5.0/apache-hugegraph-store-incubating-1.5.0/lib/hg-store-node-1.5.0.jar",
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
