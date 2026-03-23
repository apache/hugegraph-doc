---
title: "HugeGraph Docker Cluster Guide"
linkTitle: "Docker Cluster"
weight: 5
---

## Overview

HugeGraph supports running a full distributed cluster (PD + Store + Server) via Docker using bridge networking. This works on Linux and Mac (Docker Desktop).

Previous versions used `network_mode: host` which only worked on Linux. The cluster now uses a Docker bridge network (`hg-net`) where services communicate via container hostnames instead of `127.0.0.1`.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop 4.x+
- Docker Compose v2
- For the 3-node cluster: at least **12 GB** memory allocated to Docker Desktop (Settings → Resources → Memory)

> **Tested platforms**: Linux (native Docker) and macOS (Docker Desktop, tested on Apple M4). Windows Docker Desktop is untested.

## Compose Files

Three compose files are available in the [`docker/`](https://github.com/apache/hugegraph/tree/master/docker) directory:

| File | Description |
|------|-------------|
| `docker-compose.yml` | Single-node quickstart using pre-built images |
| `docker-compose-dev.yml` | Single-node dev build from source |
| `docker-compose-3pd-3store-3server.yml` | 3-node distributed cluster |

## Single-Node Quickstart

```bash
cd hugegraph/docker
HUGEGRAPH_VERSION=1.7.0 docker compose up -d
```

Verify:
```bash
curl http://localhost:8080/versions
```

## 3-Node Cluster Quickstart

```bash
cd hugegraph/docker
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-3pd-3store-3server.yml up -d
```

Startup ordering is enforced automatically:
1. PD nodes start first and must pass `/v1/health`
2. Store nodes start after all PD nodes are healthy
3. Server nodes start after all Store nodes are healthy

Verify the cluster:
```bash
curl http://localhost:8620/v1/health      # PD health
curl http://localhost:8520/v1/health      # Store health
curl http://localhost:8080/versions        # Server
curl http://localhost:8620/v1/stores       # Registered stores
curl http://localhost:8620/v1/partitions   # Partition assignment
```

## Environment Variable Reference

### PD Variables

| Variable | Required | Default | Maps To |
|----------|----------|---------|---------|
| `HG_PD_GRPC_HOST` | Yes | — | `grpc.host` |
| `HG_PD_RAFT_ADDRESS` | Yes | — | `raft.address` |
| `HG_PD_RAFT_PEERS_LIST` | Yes | — | `raft.peers-list` |
| `HG_PD_INITIAL_STORE_LIST` | Yes | — | `pd.initial-store-list` |
| `HG_PD_GRPC_PORT` | No | `8686` | `grpc.port` |
| `HG_PD_REST_PORT` | No | `8620` | `server.port` |
| `HG_PD_DATA_PATH` | No | `/hugegraph-pd/pd_data` | `pd.data-path` |
| `HG_PD_INITIAL_STORE_COUNT` | No | `1` | `pd.initial-store-count` |

**Deprecated aliases**: `GRPC_HOST` → `HG_PD_GRPC_HOST`, `RAFT_ADDRESS` → `HG_PD_RAFT_ADDRESS`, `RAFT_PEERS` → `HG_PD_RAFT_PEERS_LIST`

### Store Variables

| Variable | Required | Default | Maps To |
|----------|----------|---------|---------|
| `HG_STORE_PD_ADDRESS` | Yes | — | `pdserver.address` |
| `HG_STORE_GRPC_HOST` | Yes | — | `grpc.host` |
| `HG_STORE_RAFT_ADDRESS` | Yes | — | `raft.address` |
| `HG_STORE_GRPC_PORT` | No | `8500` | `grpc.port` |
| `HG_STORE_REST_PORT` | No | `8520` | `server.port` |
| `HG_STORE_DATA_PATH` | No | `/hugegraph-store/storage` | `app.data-path` |

**Deprecated aliases**: `PD_ADDRESS` → `HG_STORE_PD_ADDRESS`, `GRPC_HOST` → `HG_STORE_GRPC_HOST`, `RAFT_ADDRESS` → `HG_STORE_RAFT_ADDRESS`

### Server Variables

| Variable | Required | Default | Maps To |
|----------|----------|---------|---------|
| `HG_SERVER_BACKEND` | Yes | — | `backend` in `hugegraph.properties` |
| `HG_SERVER_PD_PEERS` | Yes | — | `pd.peers` |
| `STORE_REST` | No | — | used by `wait-partition.sh` |
| `PASSWORD` | No | — | enables auth mode |

**Deprecated aliases**: `BACKEND` → `HG_SERVER_BACKEND`, `PD_PEERS` → `HG_SERVER_PD_PEERS`

## Port Reference

| Service | Host Port | Purpose |
|---------|-----------|---------|
| pd0 | 8620 | REST API |
| pd0 | 8686 | gRPC |
| pd1 | 8621 | REST API |
| pd1 | 8687 | gRPC |
| pd2 | 8622 | REST API |
| pd2 | 8688 | gRPC |
| store0 | 8500 | gRPC |
| store0 | 8520 | REST API |
| store1 | 8501 | gRPC |
| store1 | 8521 | REST API |
| store2 | 8502 | gRPC |
| store2 | 8522 | REST API |
| server0 | 8080 | Graph API |
| server1 | 8081 | Graph API |
| server2 | 8082 | Graph API |

## Troubleshooting

**Containers OOM killed (exit code 137)**: Increase Docker Desktop memory to 12 GB+.

**Raft leader election timeout**: Check `HG_PD_RAFT_PEERS_LIST` is identical on all PD nodes. Verify connectivity: `docker exec hg-pd0 ping pd1`

**Partition assignment not completing**: Check `curl http://localhost:8620/v1/stores` — all 3 stores must show `"state":"Up"` before partitions are assigned.

**Connection refused**: Ensure `HG_*` env vars use container hostnames (`pd0`, `store0`), not `127.0.0.1`.
