---
title: "HugeGraph-PD Quick Start"
linkTitle: "Install/Build HugeGraph-PD"
weight: 2
---

### 1 HugeGraph-PD Overview

HugeGraph-PD (Placement Driver) is the metadata management component of HugeGraph's distributed version, responsible for managing the distribution of graph data and coordinating storage nodes. It plays a central role in distributed HugeGraph, maintaining cluster status and coordinating HugeGraph-Store storage nodes.

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
# Replace {version} with the latest version number, e.g., 1.5.0
wget https://downloads.apache.org/hugegraph/{version}/apache-hugegraph-incubating-{version}.tar.gz  
tar zxf apache-hugegraph-incubating-{version}.tar.gz
cd apache-hugegraph-incubating-{version}/apache-hugegraph-pd-incubating-{version}
```

#### 3.2 Compile from source

```bash
# 1. Clone the source code
git clone https://github.com/apache/hugegraph.git

# 2. Build the project
cd hugegraph
mvn clean install -DskipTests=true

# 3. After successful compilation, the PD module build artifacts will be located at
#    apache-hugegraph-incubating-{version}/apache-hugegraph-pd-incubating-{version}
#    target/apache-hugegraph-incubating-{version}.tar.gz
```

#### 3.3 Docker Deployment

The HugeGraph-PD Docker image is available on Docker Hub as `hugegraph/pd`.

> **Note**: The following steps assume you have already cloned or pulled the HugeGraph main repository locally, or at least have its `docker/` directory available.

Use the `docker compose` setup to deploy the complete 3-node cluster (PD + Store + Server):

```bash
cd hugegraph/docker
# Keep the version aligned with the latest release, for example 1.x.0
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-3pd-3store-3server.yml up -d
```

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

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HG_PD_GRPC_HOST` | Yes | — | This node's hostname/IP for gRPC (e.g. `pd0` in Docker, `192.168.1.10` on bare metal) |
| `HG_PD_RAFT_ADDRESS` | Yes | — | This node's Raft address (e.g. `pd0:8610`) |
| `HG_PD_RAFT_PEERS_LIST` | Yes | — | All PD peers (e.g. `pd0:8610,pd1:8610,pd2:8610`) |
| `HG_PD_INITIAL_STORE_LIST` | Yes | — | Expected store gRPC addresses (e.g. `store0:8500,store1:8500,store2:8500`) |
| `HG_PD_GRPC_PORT` | No | `8686` | gRPC server port |
| `HG_PD_REST_PORT` | No | `8620` | REST API port |
| `HG_PD_DATA_PATH` | No | `/hugegraph-pd/pd_data` | Metadata storage path |
| `HG_PD_INITIAL_STORE_COUNT` | No | `1` | Minimum stores required for cluster availability |

> **Note**: In Docker bridge networking, use container hostnames (e.g. `pd0`) for `HG_PD_GRPC_HOST` and `HG_PD_RAFT_ADDRESS` instead of IP addresses.

> **Deprecated aliases**: `GRPC_HOST`, `RAFT_ADDRESS`, `RAFT_PEERS`, `PD_INITIAL_STORE_LIST` still work but log a deprecation warning. Use the `HG_PD_*` names for new deployments.

To view runtime logs for a running PD container use `docker logs <container-name>` (e.g. `docker logs hg-pd0`).

See [docker/README.md](https://github.com/apache/hugegraph/blob/master/docker/README.md) for the full cluster setup guide.

### 4 Configuration

The main configuration file for PD is `conf/application.yml`. Here are the key configuration items:

```yaml
spring:
  application:
    name: hugegraph-pd

grpc:
  # gRPC port for cluster mode
  port: 8686
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
  # Cluster mode
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
  initial-store-count: 1

partition:
  # Default number of replicas per partition
  default-shard-count: 1
  # Default maximum number of replicas per machine
  store-max-shard-count: 12
```

For multi-node deployment, you need to modify the port and address configurations for each node to ensure proper communication between nodes.

### 5 Start and Stop

#### 5.1 Start PD

In the PD installation directory, execute:

```bash
./bin/start-hugegraph-pd.sh
```

After successful startup, you can see logs similar to the following in `logs/hugegraph-pd-stdout.log`:

```
YYYY-mm-dd xx:xx:xx [main] [INFO] o.a.h.p.b.HugePDServer - Started HugePDServer in x.xxx seconds (JVM running for x.xxx)
```

#### 5.2 Stop PD

In the PD installation directory, execute:

```bash
./bin/stop-hugegraph-pd.sh
```

### 6 Verification

Confirm that the PD service is running properly:

```bash
curl http://localhost:8620/actuator/health
```

If it returns `{"status":"UP"}`, it indicates that the PD service has been successfully started.

Additionally, you can verify Store node status through the PD API:

```bash
curl http://localhost:8620/v1/stores
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
