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

在 HugeGraph 主仓库 [`docker/`](https://github.com/apache/hugegraph/tree/master/docker) 目录下提供了四个 compose 文件：

| 文件 | 服务 | 适用场景 |
|------|------|----------|
| `docker-compose.yml` | 1 个 RocksDB Server + 1 个 Hubble | 默认的单机快速启动，推荐从这里开始 |
| `docker-compose-hstore.yml` | 1 PD + 1 Store + 1 Server + 1 Hubble | 分布式本地开发 |
| `docker-compose-3pd-3store-3server.yml` | 3 PD + 3 Store + 3 Server + 1 Hubble | HA 参考与评估 |
| `docker-compose.dev.yml` | （仅覆盖文件） | 最小 HStore 拓扑的源码构建覆盖，始终与 `docker-compose-hstore.yml` 一起使用 |

单机拓扑使用 `hugegraph/hugegraph:${HUGEGRAPH_VERSION:-latest}`；HStore 拓扑使用对应的 `hugegraph/pd`、`hugegraph/store` 和 `hugegraph/server` tag。Hubble 由 `${HUBBLE_IMAGE:-hugegraph/hubble:latest}` 单独选择。

> 注: 后续步骤皆为假设你本地**已拉取** `hugegraph` 主仓库代码 (至少是 docker 目录)

## 鉴权环境

所有拓扑都从 Compose 环境读取管理员密码和共享 JWT 密钥，通常放在 `docker/.env` 文件中：

```bash
HUGEGRAPH_ADMIN_PASSWORD='replace-with-your-password'
HUGEGRAPH_AUTH_TOKEN_SECRET='<32 字节随机值，例如 openssl rand -hex 32>'
```

`HUGEGRAPH_ADMIN_PASSWORD` 非空即开启 Server 鉴权，Hubble 通过 Server API 自动识别该模式。不设置或设为空值则关闭鉴权，这只适用于可信的本地环境。保持同一个 JWT 密钥可以在容器重建后继续使用已签发的 token，多 Server 拓扑中的每个副本都会收到同一个密钥。HA 拓扑设置了 `HG_SERVER_REQUIRE_AUTH_TOKEN_SECRET: "true"`，因此只提供密码而没有共享密钥时会快速失败。请不要提交 `.env`。

`HUGEGRAPH_ADMIN_PASSWORD` 只在第一次以鉴权模式启动时初始化内置的 `admin` 账号。之后修改它不会轮换已有密码，请使用用户 API 修改。

## 单节点快速启动

```bash
cd hugegraph/docker
 # 注意版本号请随时保持更新 → 1.x.0 
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose.yml up -d --wait
```

验证：
```bash
curl http://localhost:8080/versions
curl http://localhost:8088/about        # Hubble
```

Hubble 默认只发布在宿主机回环地址（`127.0.0.1:8088`）。只有在 HTTPS 反向代理和可信网络管控之后才应设置 `HUBBLE_PUBLISH_HOST`。

## 最小 HStore 快速启动

```bash
cd hugegraph/docker
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-hstore.yml up -d --wait
```

验证：
```bash
curl http://localhost:8620/v1/health    # PD
curl http://localhost:8520/v1/health    # Store
curl http://localhost:8080/versions     # Server
curl http://localhost:8088/about        # Hubble
```

若要从本地源码构建该拓扑而不是拉取镜像，可加上开发覆盖文件，并在后续所有生命周期命令中同时带上这两个文件：

```bash
docker compose -f docker-compose-hstore.yml -f docker-compose.dev.yml up -d --build --wait
```

## 3 节点集群快速启动

```bash
cd hugegraph/docker
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-3pd-3store-3server.yml up -d --wait
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

开启鉴权后，图列表接口应拒绝匿名请求并接受管理员：

```bash
curl -o /dev/null -w '%{http_code}\n' \
  http://localhost:8080/graphspaces/DEFAULT/graphs                      # 期望 401
curl -o /dev/null -w '%{http_code}\n' -u "admin:${HUGEGRAPH_ADMIN_PASSWORD}" \
  http://localhost:8080/graphspaces/DEFAULT/graphs                      # 期望 200
```

另外两个 Server 分别在 `8081` 和 `8082` 上提供服务，其余 PD 和 Store 节点分别在 `8621`/`8622` 和 `8521`/`8522`。

## 环境变量参考

PD 和 Store 的入口脚本会把各自的变量拼成 `SPRING_APPLICATION_JSON`，并在启动时打印生效值，因此 `docker logs` 中能看到容器实际解析出的配置。Server 的入口脚本则直接改写 `conf/graphs/hugegraph.properties` 和 `conf/rest-server.properties` 中的键。

### PD 变量

| 变量 | 必填 | 默认值 | 映射配置 |
|------|------|--------|----------|
| `HG_PD_GRPC_HOST` | 是 | （无） | `grpc.host` |
| `HG_PD_RAFT_ADDRESS` | 是 | （无） | `raft.address` |
| `HG_PD_RAFT_PEERS_LIST` | 是 | （无） | `raft.peers-list` |
| `HG_PD_INITIAL_STORE_LIST` | 是 | （无） | `pd.initial-store-list` |
| `HG_PD_GRPC_PORT` | 否 | `8686` | `grpc.port` |
| `HG_PD_REST_PORT` | 否 | `8620` | `server.port` |
| `HG_PD_DATA_PATH` | 否 | `/hugegraph-pd/pd_data` | `pd.data-path` |
| `HG_PD_INITIAL_STORE_COUNT` | 否 | `1` | `pd.initial-store-count` |

> **已弃用的别名**：`GRPC_HOST` → `HG_PD_GRPC_HOST`、`RAFT_ADDRESS` → `HG_PD_RAFT_ADDRESS`、`RAFT_PEERS` → `HG_PD_RAFT_PEERS_LIST`、`PD_INITIAL_STORE_LIST` → `HG_PD_INITIAL_STORE_LIST`。只有当新名称未设置时才会把旧名称映射过去，并打印一条警告日志。任一必填变量缺失时，入口脚本以退出码 2 退出。

### Store 变量

| 变量 | 必填 | 默认值 | 映射配置 |
|------|------|--------|----------|
| `HG_STORE_PD_ADDRESS` | 是 | （无） | `pdserver.address` |
| `HG_STORE_GRPC_HOST` | 是 | （无） | `grpc.host` |
| `HG_STORE_RAFT_ADDRESS` | 是 | （无） | `raft.address` |
| `HG_STORE_GRPC_PORT` | 否 | `8500` | `grpc.port` |
| `HG_STORE_REST_PORT` | 否 | `8520` | `server.port` |
| `HG_STORE_DATA_PATH` | 否 | `/hugegraph-store/storage` | `app.data-path` |

> **已弃用的别名**：`PD_ADDRESS` → `HG_STORE_PD_ADDRESS`、`GRPC_HOST` → `HG_STORE_GRPC_HOST`、`RAFT_ADDRESS` → `HG_STORE_RAFT_ADDRESS`

### Server 变量

与 PD、Store 不同，Server 入口脚本没有必填变量：只有实际设置了的变量才会被写入配置文件。但分布式部署至少需要 `HG_SERVER_BACKEND` 和 `HG_SERVER_PD_PEERS`。

| 变量 | 默认值 | 映射配置 |
|------|--------|----------|
| `HG_SERVER_BACKEND` | 模板取值（`rocksdb`，在 `hugegraph/server` 镜像中为 `hstore`） | `conf/graphs/hugegraph.properties` 中的 `backend` |
| `HG_SERVER_PD_PEERS` | （无） | `hugegraph.properties` 和 `rest-server.properties` 中的 `pd.peers` |
| `HG_SERVER_USE_PD` | `false` | `rest-server.properties` 中的 `usePD` |
| `HG_SERVER_CLUSTER` | `hg-test` | `rest-server.properties` 中的 `cluster` |
| `HG_SERVER_REST_URL` | `http://0.0.0.0:8080`（镜像中已设置） | `restserver.url` |
| `HG_SERVER_MIN_FREE_MEMORY` | `64`（MB） | `restserver.min_free_memory` |
| `HG_SERVER_INIT_STORE_ENABLED` | `true` | `init_store.enabled`；元数据由存储侧管理的 PD/HStore 部署应设为 `false` |
| `HG_SERVER_AUTH_TOKEN_SECRET` | 设置了 `PASSWORD` 时自动生成 | 两个配置文件中的 `auth.token_secret`，至少 32 字节 |
| `HG_SERVER_REQUIRE_AUTH_TOKEN_SECRET` | `false` | 为 `true` 时，只设置 `PASSWORD` 而未设置 `HG_SERVER_AUTH_TOKEN_SECRET` 则拒绝启动 |
| `PASSWORD` | （无） | `auth.admin_pa`，并执行 `bin/enable-auth.sh` 开启鉴权模式 |
| `PRELOAD` | （无） | 为 `true` 时从 `scripts/example.groovy` 预加载示例图 |
| `JAVA_OPTS` | 镜像中已设置 | 传给 `bin/start-hugegraph.sh -j` |
| `STORE_REST` | `store:8520` | `wait-partition.sh` 轮询的 Store REST 地址，仅 hstore 后端使用 |
| `HG_SERVER_PD_REST_ENDPOINT` | 由 `pd.peers` 把 `:8686` 改写为 `:8620` 得到 | `wait-storage.sh` 轮询的 PD REST 地址 |
| `PD_AUTH_USER` / `PD_AUTH_PASSWORD` | `store` / `admin` | `wait-storage.sh` 访问 PD REST API 使用的凭据 |
| `WAIT_PARTITION_TIMEOUT_S` | `120` | `wait-partition.sh` 等待分区分配的时长 |

> **已弃用的别名**：`BACKEND` → `HG_SERVER_BACKEND`、`PD_PEERS` → `HG_SERVER_PD_PEERS`

`wait-storage.sh` 最多等待 300 秒直到出现状态为 `Up` 的 Store。该时长写死在脚本中，无法通过环境变量调整。

`HG_SERVER_INIT_STORE_ENABLED` 只接受 `HugeConfig` 能识别的写法（忽略大小写）：`y`、`t`、`yes`、`on`、`true`、`n`、`f`、`no`、`off`、`false`。其他取值（包括 `0` 和 `1`）都会让入口脚本终止。

入口脚本在初始化成功后写入 `docker/init_complete`，后续启动会跳过重新初始化，但仍会再执行一次 `bin/init-store.sh`，以便关闭状态下每次启动都重新校验配置。

### Compose 变量

以下变量由 Compose 文件读取，而非入口脚本：

| 变量 | 默认值 | 用途 |
|------|--------|------|
| `HUGEGRAPH_VERSION` | `latest` | Server、PD 和 Store 的镜像 tag |
| `HUGEGRAPH_PULL_POLICY` | `missing` | 上述镜像的 `pull_policy`，使用 `never` 可保留本地构建的镜像 |
| `HUBBLE_IMAGE` | `hugegraph/hubble:latest` | Hubble 镜像，与 `HUGEGRAPH_VERSION` 独立选择 |
| `HUBBLE_PULL_POLICY` | `missing` | Hubble 镜像的 `pull_policy` |
| `HUBBLE_PUBLISH_HOST` | `127.0.0.1` | Hubble `8088` 端口发布到的宿主机网卡 |
| `HUGEGRAPH_ADMIN_PASSWORD` | （无） | 以 `PASSWORD` 传给 Server |
| `HUGEGRAPH_AUTH_TOKEN_SECRET` | （无） | 以 `HG_SERVER_AUTH_TOKEN_SECRET` 传给 Server |

## 端口参考

3 节点集群发布的端口：

| 服务 | 宿主机端口 | 容器端口 | 用途 |
|------|-----------|----------|------|
| pd0 | 8620 | 8620 | REST API |
| pd0 | 8686 | 8686 | gRPC |
| pd1 | 8621 | 8620 | REST API |
| pd1 | 8687 | 8686 | gRPC |
| pd2 | 8622 | 8620 | REST API |
| pd2 | 8688 | 8686 | gRPC |
| store0 | 8500 | 8500 | gRPC |
| store0 | 8510 | 8510 | Raft |
| store0 | 8520 | 8520 | REST API |
| store1 | 8501 | 8500 | gRPC |
| store1 | 8511 | 8510 | Raft |
| store1 | 8521 | 8520 | REST API |
| store2 | 8502 | 8500 | gRPC |
| store2 | 8512 | 8510 | Raft |
| store2 | 8522 | 8520 | REST API |
| server0 | 8080 | 8080 | Graph API |
| server1 | 8081 | 8080 | Graph API |
| server2 | 8082 | 8080 | Graph API |
| hubble | 8088 | 8088 | Hubble 界面，默认绑定 `127.0.0.1` |

单机拓扑只发布 `8080` 和 `8088`；最小 HStore 拓扑发布 `8620`（PD REST）、`8520`（Store REST）、`8080` 和 `8088`。PD Raft 使用网络内的 `8610`，所有拓扑都不对外发布。

## 故障排查

1. **容器 OOM 退出（exit code 137）**：将 Docker Desktop 内存增加到 12 GB 以上 (或调整被 kill 的启动 jvm 内存设置)

2. **Raft 选举超时**：检查所有 PD 节点的 `HG_PD_RAFT_PEERS_LIST` 是否一致。验证连通性：`docker exec hg-pd0 ping pd1`

3. **分区分配未完成**：检查 `curl http://localhost:8620/v1/stores`，3 个 Store 必须都显示 `"state":"Up"` 才能完成分区分配

4. **连接被拒**：确保 `HG_*` 环境变量使用容器主机名（`pd0`、`store0`），而非 `127.0.0.1`

5. **数据在意料之外地保留了下来**：`docker compose down` 会保留命名卷。要同时删除该拓扑的数据，请使用 `docker compose down -v`

**查看运行时日志**：使用 `docker logs <container-name>`（如 `docker logs hg-pd0`）可直接查看日志，无需进入容器。单机镜像 `hugegraph/hugegraph` 设置了 `STDOUT_MODE=true`，其服务日志会输出到容器 stdout。`hugegraph/server`（HStore）镜像没有设置该变量，因此对 HStore 拓扑的 Server 执行 `docker logs` 只能看到入口脚本的输出，其余内容需在容器内查看 `logs/hugegraph-server.log`。

## 容器监控与健康检查

> **版本说明**：本节描述的行为**不包含在 `1.7.0` 镜像中**。请使用 `HUGEGRAPH_VERSION=latest` 或等待下一个发布版本。

### 进程监控模型

此前，三个 Docker 入口脚本均以 `tail -f /dev/null` 结尾，即使 Java 进程崩溃，容器仍会保持运行状态。由于容器从未退出，Docker 的 `restart: unless-stopped` 策略也不会触发。

现在，入口脚本直接监控 Java 进程：

- **PD 和 Store 容器**：入口脚本向启动脚本传入 `-d false` 参数，启动脚本通过 `exec` 直接替换为 Java 进程。容器进程即为 Java 进程，当 Java 退出（崩溃或正常关闭）时，容器立即退出，Docker 的重启策略随即触发。
- **Server 容器**：入口脚本使用 `tail --pid=$PID -f /dev/null` 阻塞，直到 Java 退出。`SIGTERM`/`SIGINT` 信号陷阱会将 `docker stop` 信号转发给 Java 并等待其正常关闭（退出码 0）。若 Java 崩溃，入口脚本以退出码 1 退出，从而触发重启策略。
- 所有镜像中的 PID 1 均为 `dumb-init`，负责将 Docker 信号转发给入口脚本进程。

### 健康检查端点

所有四个 Docker 镜像现已内置 `HEALTHCHECK` 指令。`docker ps` 将显示真实的健康状态。在 90 秒的启动期内，检查失败不计入统计；此后，连续三次失败将把容器标记为 `unhealthy`。

| 镜像 | 健康检查端点 | 端口 | 参数 |
|------|-------------|------|------|
| `hugegraph/hugegraph`（单机 RocksDB Server） | `GET /versions` | 8080 | `--interval=15s --timeout=10s --start-period=90s --retries=3` |
| `hugegraph/server`（HStore Server） | `GET /versions` | 8080 | 同上 |
| `hugegraph/pd` | `GET /v1/health` | 8620 | 同上 |
| `hugegraph/store` | `GET /v1/health` | 8520 | 同上 |

Compose 文件在此之上还定义了自己的健康检查，因此 `--wait` 和 `depends_on: condition: service_healthy` 不依赖镜像内置的检查。Compose 中的检查使用更短的启动期（视服务和拓扑为 30 到 120 秒）和更多的重试次数。

> **注意**：`start-hugegraph.sh` 中的 `-m true` 标志（基于 cron 的监控）仅适用于虚拟机/裸机部署，Docker 镜像中未安装也不使用该功能。Docker 用户应依赖内置的 `HEALTHCHECK` 和 Docker 重启策略。
