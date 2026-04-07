---
title: "HugeGraph Docker 集群部署指南"
linkTitle: "Docker 集群"
weight: 6
---

## 概述

HugeGraph 通过 Docker-Compose 可快速运行完整的分布式集群版（PD + Store + Server）。该方式适用于 Linux 和 Mac。

## 前置条件

- Docker Engine 20.10+ 或 Docker Desktop 4.x+
- Docker Compose v2
- Mac 运行 3 节点集群时，建议分配至少 **12 GB** 内存（设置 → 资源 → 内存）。[其他平台根据实际情况调整]

> **已测试环境**：Linux（原生 Docker）和 macOS（Docker Desktop with ARM M4）

## Compose 文件

在 HugeGraph 主仓库 [`docker/`](https://github.com/apache/hugegraph/tree/master/docker) 目录下提供了三个 compose 文件：

| 文件 | 描述 |
|------|------|
| `docker-compose.yml` | 使用预构建镜像的** 1x3 单进程(节点)**快速启动 |
| `docker-compose.dev.yml` | 从源码构建的单节点**开发模式** |
| `docker-compose-3pd-3store-3server.yml` | ** 3x3 进程**(模拟节点)分布式集群 |

> 注: 后续步骤皆为假设你本地**已拉取** `hugegraph` 主仓库代码 (至少是 docker 目录)

## 单节点快速启动

```bash
cd hugegraph/docker
 # 注意版本号请随时保持更新 → 1.x.0 
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

默认内置的启动顺序：
1. PD (节点)最先启动，且必须通过 `/v1/health` 健康检查
2. Store (节点)在所有 PD 健康后再启动
3. Server (节点)在所有 Store + PD 健康后最后启动

验证集群正常：(重要)
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

> **已弃用的别名**：`GRPC_HOST` → `HG_PD_GRPC_HOST`、`RAFT_ADDRESS` → `HG_PD_RAFT_ADDRESS`、`RAFT_PEERS` → `HG_PD_RAFT_PEERS_LIST`

### Store 变量

| 变量 | 必填 | 默认值 | 映射配置 |
|------|------|--------|----------|
| `HG_STORE_PD_ADDRESS` | 是 | — | `pdserver.address` |
| `HG_STORE_GRPC_HOST` | 是 | — | `grpc.host` |
| `HG_STORE_RAFT_ADDRESS` | 是 | — | `raft.address` |
| `HG_STORE_GRPC_PORT` | 否 | `8500` | `grpc.port` |
| `HG_STORE_REST_PORT` | 否 | `8520` | `server.port` |
| `HG_STORE_DATA_PATH` | 否 | `/hugegraph-store/storage` | `app.data-path` |

> **已弃用的别名**：`PD_ADDRESS` → `HG_STORE_PD_ADDRESS`、`GRPC_HOST` → `HG_STORE_GRPC_HOST`、`RAFT_ADDRESS` → `HG_STORE_RAFT_ADDRESS`

### Server 变量

| 变量 | 必填 | 默认值 | 映射配置 |
|------|------|--------|----------|
| `HG_SERVER_BACKEND` | 是 | — | `hugegraph.properties` 中的 `backend` |
| `HG_SERVER_PD_PEERS` | 是 | — | `pd.peers` |
| `STORE_REST` | 否 | — | `wait-partition.sh` 使用 |
| `PASSWORD` | 否 | — | 启用鉴权模式 |

> **已弃用的别名**：`BACKEND` → `HG_SERVER_BACKEND`、`PD_PEERS` → `HG_SERVER_PD_PEERS`

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

1. **容器 OOM 退出（exit code 137）**：将 Docker Desktop 内存增加到 12 GB 以上 (或调整被 kill 的启动 jvm 内存设置)

2. **Raft 选举超时**：检查所有 PD 节点的 `HG_PD_RAFT_PEERS_LIST` 是否一致。验证连通性：`docker exec hg-pd0 ping pd1`

3. **分区分配未完成**：检查 `curl http://localhost:8620/v1/stores` — 3 个 Store 必须都显示 `"state":"Up"` 才能完成分区分配

4. **连接被拒**：确保 `HG_*` 环境变量使用容器主机名（`pd0`、`store0`），而非 `127.0.0.1`
