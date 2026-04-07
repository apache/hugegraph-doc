---
title: "HugeGraph Docker Cluster Guide"
linkTitle: "Docker Cluster"
weight: 6
---

## Overview

HugeGraph can quickly run a full distributed deployment (PD + Store + Server) with Docker Compose. This works on Linux and Mac.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop 4.x+
- Docker Compose v2
- For a 3-node cluster on Mac: allocate at least **12 GB** memory (Settings → Resources → Memory). Adjust this on other platforms as needed.

> **Tested environments**: Linux (native Docker) and macOS (Docker Desktop with ARM M4).

## Compose Files

Three compose files are available in the [`docker/`](https://github.com/apache/hugegraph/tree/master/docker) directory of the HugeGraph main repository:

| File | Description |
|------|-------------|
| `docker-compose.yml` | Quickstart for a single-host deployment using pre-built images |
| `docker-compose.dev.yml` | Development mode for a single-host deployment built from source |
| `docker-compose-3pd-3store-3server.yml` | Distributed cluster with 3 PD, 3 Store, and 3 Server processes |

> **Note**: The following steps assume you have already cloned or pulled the HugeGraph main repository locally, or at least have its `docker/` directory available.

## Single-Node Quickstart

```bash
cd hugegraph/docker
# Keep the version aligned with the latest release, for example 1.x.0
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

Built-in startup ordering:
1. PD nodes start first and must pass the `/v1/health` check
2. Store nodes start only after all PD nodes are healthy
3. Server nodes start last, after all PD and Store nodes are healthy

Verify that the cluster is healthy:
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

> **Deprecated aliases**: `GRPC_HOST` → `HG_PD_GRPC_HOST`, `RAFT_ADDRESS` → `HG_PD_RAFT_ADDRESS`, `RAFT_PEERS` → `HG_PD_RAFT_PEERS_LIST`

### Store Variables

| Variable | Required | Default | Maps To |
|----------|----------|---------|---------|
| `HG_STORE_PD_ADDRESS` | Yes | — | `pdserver.address` |
| `HG_STORE_GRPC_HOST` | Yes | — | `grpc.host` |
| `HG_STORE_RAFT_ADDRESS` | Yes | — | `raft.address` |
| `HG_STORE_GRPC_PORT` | No | `8500` | `grpc.port` |
| `HG_STORE_REST_PORT` | No | `8520` | `server.port` |
| `HG_STORE_DATA_PATH` | No | `/hugegraph-store/storage` | `app.data-path` |

> **Deprecated aliases**: `PD_ADDRESS` → `HG_STORE_PD_ADDRESS`, `GRPC_HOST` → `HG_STORE_GRPC_HOST`, `RAFT_ADDRESS` → `HG_STORE_RAFT_ADDRESS`

### Server Variables

| Variable | Required | Default | Maps To |
|----------|----------|---------|---------|
| `HG_SERVER_BACKEND` | Yes | — | `backend` in `hugegraph.properties` |
| `HG_SERVER_PD_PEERS` | Yes | — | `pd.peers` |
| `STORE_REST` | No | — | used by `wait-partition.sh` |
| `PASSWORD` | No | — | enables auth mode |

> **Deprecated aliases**: `BACKEND` → `HG_SERVER_BACKEND`, `PD_PEERS` → `HG_SERVER_PD_PEERS`

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

1. **Containers exit due to OOM (`exit code 137`)**: Increase Docker Desktop memory to at least 12 GB, or reduce the JVM heap settings for the process that is being killed.

2. **Raft leader election timeout**: Check that `HG_PD_RAFT_PEERS_LIST` is identical on all PD nodes. Verify connectivity with `docker exec hg-pd0 ping pd1`.

3. **Partition assignment does not complete**: Check `curl http://localhost:8620/v1/stores` and confirm that all 3 stores show `"state":"Up"` before partition assignment can finish.

4. **Connection refused**: Ensure `HG_*` environment variables use container hostnames (`pd0`, `store0`) instead of `127.0.0.1`.

**Viewing runtime logs**: Use `docker logs <container-name>` (e.g. `docker logs hg-pd0`) to view logs directly without exec-ing into the container.
