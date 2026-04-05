---
title: "HugeGraph Docker 集群部署指南"
linkTitle: "Docker 集群"
weight: 5
---

## 概述

HugeGraph 支持通过 Docker 桥接网络运行完整的分布式集群（PD + Store + Server）。该方式适用于 Linux 和 Mac（Docker Desktop）。

早期版本使用 `network_mode: host`，仅在 Linux 上可用。集群现在使用 Docker 桥接网络（`hg-net`），服务通过容器主机名而非 `127.0.0.1` 进行通信。

## 前置条件

- Docker Engine 20.10+ 或 Docker Desktop 4.x+
- Docker Compose v2
- Mac（Docker Desktop）运行 3 节点集群时，需分配至少 **12 GB** 内存（设置 → 资源 → 内存）。Linux 上 Docker 直接使用宿主机内存，无需额外分配

> **已测试平台**：Linux（原生 Docker）和 macOS（Docker Desktop，已在 Apple M4 上测试）。Windows Docker Desktop 未经测试。

## Compose 文件

[`docker/`](https://github.com/apache/hugegraph/tree/master/docker) 目录下提供了三个 compose 文件：

| 文件 | 描述 |
|------|------|
| `docker-compose.yml` | 使用预构建镜像的单节点快速启动 |
| `docker-compose.dev.yml` | 从源码构建的单节点开发模式 |
| `docker-compose-3pd-3store-3server.yml` | 3 节点分布式集群 |

## 单节点快速启动

```bash
cd hugegraph/docker
HUGEGRAPH_VERSION=1.7.0 docker compose up -d
```

验证：
```bash
curl http://localhost:8080/versions
```

## 3 节点集群快速启动

```bash
cd hugegraph/docker
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-3pd-3store-3server.yml up -d
```

启动顺序自动强制执行：
1. PD 节点首先启动，必须通过 `/v1/health` 健康检查
2. Store 节点在所有 PD 节点健康后启动
3. Server 节点在所有 Store 节点健康后启动

验证集群：
```bash
curl http://localhost:8620/v1/health      # PD 健康检查
curl http://localhost:8520/v1/health      # Store 健康检查
curl http://localhost:8080/versions        # Server
curl http://localhost:8620/v1/stores       # 已注册的 Store
curl http://localhost:8620/v1/partitions   # 分区分配
```

## 环境变量参考

### PD 变量

| 变量 | 必填 | 默认值 | 映射配置 |
|------|------|--------|----------|
| `HG_PD_GRPC_HOST` | 是 | — | `grpc.host` |
| `HG_PD_RAFT_ADDRESS` | 是 | — | `raft.address` |
| `HG_PD_RAFT_PEERS_LIST` | 是 | — | `raft.peers-list` |
| `HG_PD_INITIAL_STORE_LIST` | 是 | — | `pd.initial-store-list` |
| `HG_PD_GRPC_PORT` | 否 | `8686` | `grpc.port` |
| `HG_PD_REST_PORT` | 否 | `8620` | `server.port` |
| `HG_PD_DATA_PATH` | 否 | `/hugegraph-pd/pd_data` | `pd.data-path` |
| `HG_PD_INITIAL_STORE_COUNT` | 否 | `1` | `pd.initial-store-count` |

**已弃用的别名**：`GRPC_HOST` → `HG_PD_GRPC_HOST`、`RAFT_ADDRESS` → `HG_PD_RAFT_ADDRESS`、`RAFT_PEERS` → `HG_PD_RAFT_PEERS_LIST`

### Store 变量

| 变量 | 必填 | 默认值 | 映射配置 |
|------|------|--------|----------|
| `HG_STORE_PD_ADDRESS` | 是 | — | `pdserver.address` |
| `HG_STORE_GRPC_HOST` | 是 | — | `grpc.host` |
| `HG_STORE_RAFT_ADDRESS` | 是 | — | `raft.address` |
| `HG_STORE_GRPC_PORT` | 否 | `8500` | `grpc.port` |
| `HG_STORE_REST_PORT` | 否 | `8520` | `server.port` |
| `HG_STORE_DATA_PATH` | 否 | `/hugegraph-store/storage` | `app.data-path` |

**已弃用的别名**：`PD_ADDRESS` → `HG_STORE_PD_ADDRESS`、`GRPC_HOST` → `HG_STORE_GRPC_HOST`、`RAFT_ADDRESS` → `HG_STORE_RAFT_ADDRESS`

### Server 变量

| 变量 | 必填 | 默认值 | 映射配置 |
|------|------|--------|----------|
| `HG_SERVER_BACKEND` | 是 | — | `hugegraph.properties` 中的 `backend` |
| `HG_SERVER_PD_PEERS` | 是 | — | `pd.peers` |
| `STORE_REST` | 否 | — | `wait-partition.sh` 使用 |
| `PASSWORD` | 否 | — | 启用鉴权模式 |

**已弃用的别名**：`BACKEND` → `HG_SERVER_BACKEND`、`PD_PEERS` → `HG_SERVER_PD_PEERS`

## 端口参考

| 服务 | 宿主机端口 | 用途 |
|------|-----------|------|
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

## 故障排查

**容器 OOM 被杀（退出码 137）**：将 Docker Desktop 内存增加到 12 GB 以上。

**Raft 选举超时**：检查所有 PD 节点的 `HG_PD_RAFT_PEERS_LIST` 是否一致。验证连通性：`docker exec hg-pd0 ping pd1`

**分区分配未完成**：检查 `curl http://localhost:8620/v1/stores` — 所有 3 个 Store 必须显示 `"state":"Up"` 才能完成分区分配。

**连接被拒**：确保 `HG_*` 环境变量使用容器主机名（`pd0`、`store0`），而非 `127.0.0.1`。
