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

本页的 HStore 与 HA Compose 操作按当前主线文件编写，必须使用从同一主线源码构建的 PD、Store 和 Server 镜像；不要把这些 Compose 文件与 `1.7.0` 标签的 HStore 组件镜像混用。单机示例单独固定 `hugegraph/hugegraph:1.7.0` 镜像标签。

## 鉴权环境

以下 `.env` 模板对应当前主线 Compose。尖括号内容和 `replace-with-your-password` 都是占位，必须替换为真实值后才能载入或启动；可参考[主线 docker/README.md 的鉴权环境步骤](https://github.com/apache/hugegraph/blob/master/docker/README.md#create-the-authentication-environment)生成 `.env`，并先替换其中的管理员密码占位：

```bash
HUGEGRAPH_ADMIN_PASSWORD='replace-with-your-password'
HUGEGRAPH_AUTH_TOKEN_SECRET='<32 字节随机值，例如 openssl rand -hex 32>'
HG_PD_AUTH_SECRET_KEY='<24 字节随机值，例如 openssl rand -hex 24>'
```

在主线 HStore 和 HA 拓扑中，`HG_PD_AUTH_SECRET_KEY` 是 PD REST Basic 鉴权密码，所有 PD 节点、Server 和 Hubble 都必须使用同一个值。当前主线 PD Docker 镜像要求设置该密钥。Hubble 不会直接读取 `.env`，启动前还要用该值生成拓扑对应的本地配置文件，见下文。不要提交 `.env` 或生成的 `.local.properties`。

`HUGEGRAPH_ADMIN_PASSWORD` 非空时会以 `PASSWORD` 启用 Server 鉴权，Hubble 通过 Server API 自动识别该模式；该密码只在首次初始化内置 `admin` 账号。不设置或设为空值则关闭鉴权，这只适用于可信的本地环境。

当前主线 Compose 会把 `HUGEGRAPH_AUTH_TOKEN_SECRET` 传给 `HG_SERVER_AUTH_TOKEN_SECRET`。同一密钥可让主线多 Server 副本验证相同 token，并在容器重建后继续验证已签发 token；HA Compose 还要求显式提供该密钥。`hugegraph/hugegraph:1.7.0` 单机镜像的 Docker 入口脚本只根据 `PASSWORD` 开启鉴权，不读取 `HG_SERVER_AUTH_TOKEN_SECRET`，因此不要把 `.env` 中该变量视为该镜像的固定 JWT 配置。若在 1.7.0 中需要固定 JWT secret，请在其认证图配置 `conf/graphs/hugegraph.properties` 中显式设置 `auth.token_secret`，并确保该配置随容器替换保留；认证图路径及密钥生成说明见[鉴权配置指南](/cn/docs/config/config-authentication/)。

之后修改 `HUGEGRAPH_ADMIN_PASSWORD` 不会轮换已有密码，请使用用户 API 修改。

> [!WARNING]
> **生产环境的组件访问控制**
>
> 生产环境必须按 [Server 认证与授权配置](/cn/docs/config/config-authentication/) 为图 API 启用 Server Auth，启用并维护 Server IP 白名单、按最小权限授权，并保留、限制读取 Server `audit-*.log`。PD 的 REST 凭据与 PD/Store 的 gRPC、Raft、REST 网络边界独立配置；Server Auth 不会保护这些端口。仅向集群节点和受信运维入口开放 PD/Store 端口。

## 单节点快速启动

本节固定使用 `hugegraph/hugegraph:1.7.0` 单机镜像标签；HStore/HA 示例使用当前主线构建镜像，不能照搬本节的版本号。

```bash
cd "$(git rev-parse --show-toplevel)/docker"
# 单机 RocksDB Server 镜像示例
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose.yml up -d --wait
```

验证：
```bash
curl -fsS http://localhost:8080/versions
curl -fsS http://localhost:8088/about        # Hubble
```

Hubble 默认只发布在宿主机回环地址（`127.0.0.1:8088`）。只有在 HTTPS 反向代理和可信网络管控之后才应设置 `HUBBLE_PUBLISH_HOST`。

## 最小 HStore 快速启动（当前主线镜像）

从 HugeGraph Server 主线仓库根目录构建 PD、Store 和 HStore Server 镜像：

```bash
cd "$(git rev-parse --show-toplevel)"
docker build -f hugegraph-pd/Dockerfile -t hugegraph/pd:local .
docker build -f hugegraph-store/Dockerfile -t hugegraph/store:local .
docker build -f hugegraph-server/Dockerfile-hstore -t hugegraph/server:local .
```

从仓库根目录执行以下命令进入 `docker/`，载入 `.env` 并生成最小拓扑所需的 Hubble 配置。缺少 `hstore.local.properties` 时，Compose 不会为只读 bind mount 自动创建有效配置；先生成文件再启动：

```bash
cd "$(git rev-parse --show-toplevel)/docker"
set -a; . ./.env; set +a
./set-hubble-pd-password.sh hstore
HUGEGRAPH_VERSION=local HUGEGRAPH_PULL_POLICY=never \
  docker compose -f docker-compose-hstore.yml up -d --wait
```

验证：
```bash
set -a; . ./.env; set +a
curl -fsS http://localhost:8620/v1/health    # PD
curl -fsS http://localhost:8520/v1/health    # Store
curl -fsS http://localhost:8080/versions     # Server
curl -fsS http://localhost:8088/about        # Hubble
curl -fsS -u "hg:${HG_PD_AUTH_SECRET_KEY:?请先载入 .env}" \
  http://localhost:8620/v1/stores       # PD REST 认证后查看 Store 注册状态
```

若要从本地源码构建该拓扑而不是拉取镜像，可加上开发覆盖文件，并在后续所有生命周期命令中同时带上这两个文件：

```bash
cd "$(git rev-parse --show-toplevel)/docker"
set -a; . ./.env; set +a
./set-hubble-pd-password.sh hstore
docker compose -f docker-compose-hstore.yml -f docker-compose.dev.yml up -d --build --wait
```

覆盖文件为本地构建生成 `dev` 标签的镜像；如果已经按上文构建 `local` 标签镜像，则使用基础 Compose 文件和 `HUGEGRAPH_VERSION=local` 启动，不要同时混用两个版本标签。

## 3 节点集群快速启动（当前主线镜像）

HA Compose 文件不包含源码构建覆盖层。先按最小 HStore 一节从同一主线源码构建 `hugegraph/pd:local`、`hugegraph/store:local` 和 `hugegraph/server:local`，然后在 `docker/` 目录载入 `.env`，生成 HA Hubble 配置并启动：

```bash
cd "$(git rev-parse --show-toplevel)/docker"
set -a; . ./.env; set +a
./set-hubble-pd-password.sh hstore-ha
HUGEGRAPH_VERSION=local \
  docker compose -f docker-compose-3pd-3store-3server.yml up -d --wait
```

HA Hubble bind-mount `conf/hubble/hstore-ha.local.properties`；必须在启动前生成。该文件与最小 HStore 使用的 `hstore.local.properties` 分开生成，但两者从同一 `.env` 读取同一个 `HG_PD_AUTH_SECRET_KEY`。

默认内置的启动顺序：
1. PD (节点)最先启动，且必须通过 `/v1/health` 健康检查
2. Store (节点)在所有 PD 健康后再启动
3. Server (节点)在所有 Store + PD 健康后最后启动

验证集群正常：PD 的 `/v1/health` 和 `/v1/ready` 是无需认证的探针；查询 Store 注册和分区数据属于受保护的 PD REST 管理接口，需用用户名 `hg` 和 `.env` 中的 `HG_PD_AUTH_SECRET_KEY` 进行 Basic 认证。

```bash
set -a; . ./.env; set +a
curl -fsS http://localhost:8620/v1/health      # PD 健康检查
curl -fsS http://localhost:8520/v1/health      # Store 健康检查
curl -fsS http://localhost:8080/versions        # Server
for port in 8620 8621 8622; do
  curl -fsS "http://localhost:${port}/v1/ready" | grep -q '"ready":true' || exit 1
done
curl -fsS -u "hg:${HG_PD_AUTH_SECRET_KEY:?请先载入 .env}" \
  http://localhost:8620/v1/stores          # 认证后查看已注册的 Store
curl -fsS -u "hg:${HG_PD_AUTH_SECRET_KEY:?请先载入 .env}" \
  http://localhost:8620/v1/partitions      # 认证后查看分区分配
curl -fsS http://localhost:8088/about           # Hubble
```

开启鉴权后，图列表接口应拒绝匿名请求并接受管理员：

```bash
set -a; . ./.env; set +a
curl -o /dev/null -w '%{http_code}\n' \
  http://localhost:8080/graphspaces/DEFAULT/graphs                      # 期望 401
curl -o /dev/null -w '%{http_code}\n' -u "admin:${HUGEGRAPH_ADMIN_PASSWORD}" \
  http://localhost:8080/graphspaces/DEFAULT/graphs                      # 期望 200
```

另外两个 Server 分别在 `8081` 和 `8082` 上提供服务，其余 PD 和 Store 节点分别在 `8621`/`8622` 和 `8521`/`8522`。

## 环境变量参考

以下 PD、Store、Server 和 Compose 变量表描述当前主线镜像入口及 Compose 文件，不是 `hugegraph/hugegraph:1.7.0` 单机镜像的环境变量契约。PD 和 Store 的入口脚本会把各自的变量拼成 `SPRING_APPLICATION_JSON`，并在启动时打印部分非敏感配置摘要；PD 密钥不会打印在该摘要中。`docker logs` 可用于核对日志列出的配置项，但不要以日志中未显示密钥来判断是否生效。Server 的入口脚本则直接改写 `conf/graphs/hugegraph.properties` 和 `conf/rest-server.properties` 中的键。

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
| `HG_PD_AUTH_SECRET_KEY` | 是（当前主线 Docker） | 无 | `auth.secret-key`；PD REST Basic 密码，也供 Server 与 Hubble 使用 |

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
| `HG_SERVER_URLS_TO_PD` | `http://0.0.0.0:8080` | `server.urls_to_pd`：本 Server 注册到 PD 的地址列表（逗号分隔），代替 `restserver.url`；仅在 `server.deploy_in_k8s` 为 `true` 时生效；每个地址都要自带 `http://` 前缀，系统只会给第一个地址补上；其中的空白字符会被去除 |
| `HG_SERVER_DEPLOY_IN_K8S` | `false` | `rest-server.properties` 中的 `server.deploy_in_k8s` |
| `HG_SERVER_MIN_FREE_MEMORY` | `64`（MB） | `restserver.min_free_memory` |
| `HG_SERVER_INIT_STORE_ENABLED` | `true` | `init_store.enabled`；元数据由存储侧管理的 PD/HStore 部署应设为 `false` |
| `HG_SERVER_AUTH_TOKEN_SECRET` | 设置了 `PASSWORD` 时自动生成 | 两个配置文件中的 `auth.token_secret`，至少 32 字节 |
| `HG_SERVER_REQUIRE_AUTH_TOKEN_SECRET` | `false` | 为 `true` 时，只设置 `PASSWORD` 而未设置 `HG_SERVER_AUTH_TOKEN_SECRET` 则拒绝启动 |
| `PASSWORD` | （无） | `auth.admin_pa`，并执行 `bin/enable-auth.sh` 开启鉴权模式 |
| `PRELOAD` | （无） | 为 `true` 时从 `scripts/example.groovy` 预加载示例图 |
| `JAVA_OPTS` | 镜像中已设置 | 传给 `bin/start-hugegraph.sh -j` |
| `HG_SERVER_STARTUP_TIMEOUT_S` | `120`（秒） | 传给 `bin/start-hugegraph.sh -t`，允许范围为 `1`–`86400`；详见下文的 Server 启动等待超时 |
| `STORE_REST` | `store:8520` | `wait-partition.sh` 轮询的 Store REST 地址，仅 hstore 后端使用 |
| `HG_SERVER_PD_REST_ENDPOINT` | 由 `pd.peers` 把 `:8686` 改写为 `:8620` 得到 | `wait-storage.sh` 轮询的 PD REST 地址 |
| `PD_AUTH_USER` | `store` | `wait-storage.sh` 访问 PD REST API 的 Basic 用户名 |
| `PD_AUTH_PASSWORD` | 空 | PD REST Basic 密码；启用 PD REST 鉴权时须与 `HG_PD_AUTH_SECRET_KEY` 相同 |
| `WAIT_PARTITION_TIMEOUT_S` | `120` | 分区轮询超时；包含下文修复的构建还会限制最终诊断 |

包含鉴权属性修复的 master 镜像会保留显式签名密钥中的空格、反斜杠和 Unicode，各 Server 副本应使用同一密钥。
如果旧镜像曾错误读取这类密钥，升级时应重新显式提供原本想使用的 `HG_SERVER_AUTH_TOKEN_SECRET`；仅复用旧配置仍会保留错误读取后的密钥。
若实际生效的密钥改变，须重新登录获取 token。上文所述 1.7.0 镜像限制仍适用。

旧镜像在初始化程序继承 C locale 时，可能错误初始化 Unicode 管理员密码。升级或再次设置 `PASSWORD` 不会修复已有账号存储的密码，
须由仍可登录的管理员通过[用户 API](/cn/docs/clients/restful-api/auth/)修改。若已无可用管理员身份，本修复不提供自动恢复；应保留现有数据，安排账号恢复后再升级。

> **已弃用的别名**：`BACKEND` → `HG_SERVER_BACKEND`、`PD_PEERS` → `HG_SERVER_PD_PEERS`

`wait-storage.sh` 最多等待 300 秒直到出现状态为 `Up` 的 Store。该时长写死在脚本中，无法通过环境变量调整。

在当前 master Server 构建中，HStore 启动时，分区轮询和最终
`/v1/partitions` 诊断分别使用独立的 `WAIT_PARTITION_TIMEOUT_S` 预算。旧构建仅限制轮询时间，最终诊断请求没有超时。
使用默认配置时，最终响应停滞会在 120 秒后超时；设为 `0` 会禁用 GNU timeout 的时限。
入口脚本在等待 Java 进程前会先等待 `wait-partition.sh`。若 Java 进程在分区轮询阶段提前退出，轮询仍可能消耗完整超时预算后入口脚本才感知到退出；
若轮询成功，后续的最终诊断也可能再次消耗完整的超时预算。信号触发的关闭仍可正常中断检查。

`HG_SERVER_INIT_STORE_ENABLED` 和 `HG_SERVER_DEPLOY_IN_K8S` 只接受 `HugeConfig` 能识别的写法（忽略大小写）：`y`、`t`、`yes`、`on`、`true`、`n`、`f`、`no`、`off`、`false`。其他取值（包括 `0` 和 `1`）都会让入口脚本终止。

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
| `HUGEGRAPH_AUTH_TOKEN_SECRET` | （无） | 当前主线 Compose 以 `HG_SERVER_AUTH_TOKEN_SECRET` 传给 Server；1.7.0 镜像不读取该变量 |
| `HG_PD_AUTH_SECRET_KEY` | （无） | HStore 拓扑 PD REST Basic 密码；由 Compose 传给 PD 和 Server，并用于生成 Hubble 本地配置 |

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

3. **分区分配未完成**：在 `docker/` 目录先载入 `.env`，再用 PD REST Basic 认证检查 Store：

   ```bash
   set -a; . ./.env; set +a
   curl -fsS -u "hg:${HG_PD_AUTH_SECRET_KEY:?请先载入 .env}" http://localhost:8620/v1/stores
   ```

   3 个 Store 都显示 `"state":"Up"` 后，PD 才能为集群完成分区分配。

4. **连接被拒**：确保 `HG_*` 环境变量使用容器主机名（`pd0`、`store0`），而非 `127.0.0.1`

5. **数据在意料之外地保留了下来**：`docker compose down` 会保留命名卷。要同时删除该拓扑的数据，请使用 `docker compose down -v`

**查看运行时日志**：使用 `docker logs <container-name>`（如 `docker logs hg-pd0`）可直接查看日志，无需进入容器。基于当前 master 构建的 PD、Store 以及两个 Server 镜像（`hugegraph/hugegraph` 和 HStore 的
`hugegraph/server`）都设置了 `STDOUT_MODE=true`，服务日志会输出到容器 stdout。对 Server 而言，Hadoop、ZooKeeper、SOFA、Netty 和 Commons 的 WARN 及以上日志也会输出到 stdout；Hadoop、Netty 和 Commons 的
INFO 日志以及审计日志、慢查询日志仍只写入文件，ZooKeeper 和 SOFA 不输出 WARN 以下的日志。`/hugegraph-server/logs` 中包含 `hugegraph-server.log`、JVM
崩溃日志（`hs_err_pid*.log`）和内存溢出时的堆转储（`heapdump_*/java_pid*.hprof`，每次启动一个目录，Server 及其启动的 JVM 分别写入各自的文件，除非某个 JVM 复用了同一次启动中先前的 PID；如果无法创建该目录，转储会直接写入
`/hugegraph-server/logs`）。两个镜像都声明了 `VOLUME /hugegraph-server`，因此 `docker restart` 和 Compose 重新创建容器都会保留这些文件；`docker compose down` 会留下这个匿名卷，下一次 `up` 不会再挂载它，之后执行
`down -v` 也不会删除它（请在 `down` 之前用 `docker inspect` 记下卷名，再用 `docker volume rm <name>` 删除；`docker volume prune` 会同时删除 Docker
主机上所有其他未使用的匿名卷），所以请使用具名卷或绑定挂载来保留这些文件。Kubernetes 每次重启都会新建容器，因此需要在 `/hugegraph-server/logs` 挂载 `emptyDir` 或 PersistentVolumeClaim。请为每个 Pod 使用单独的卷，或在共享 PVC 上为每个
Pod 使用单独的目录（`subPathExpr: $(POD_NAME)`，并通过 Downward API 从 `metadata.name` 传入 `POD_NAME`；Helm Chart 两者都没有设置）：崩溃文件的名字各不相同，但日志文件本身的名字是固定的。只有当存储支持多个节点同时读写挂载（通常是
`ReadWriteMany`）时，不同节点上的 Pod 才能共享同一个 PVC；`ReadWriteOnce` 的 PVC 只能被一个节点读写挂载，否则请为每个 Pod 使用单独的 PVC。Helm Chart 目前还不会挂载日志卷。堆转储可能和 JVM 堆一样大，而且每次启动都会使用新目录，因此反复内存溢出的
Server 会把卷写满；请按需要保留的转储数量规划卷大小，并确保不超过 `ephemeral-storage` 限制或 `emptyDir` 的 `sizeLimit`（被驱逐时 `emptyDir` 会连同转储一起删除），也不要使用 `medium: Memory`。存活探针失败后，容器最早可能在转储开始后约
`(failureThreshold - 1) × periodSeconds + timeoutSeconds` 被重启，kubelet 最多再等待 `terminationGracePeriodSeconds`
就会终止它；请让这段时间长于写入一次堆转储所需的时间，否则在写转储的过程中重启会留下不完整的文件。启动脚本从不删除转储或 `heapdump_*` 目录，因为 computer 任务的 JVM 可能在 Server 退出后仍在使用它；每次启动到 Java 阶段都会留下一个目录，除非发生内存溢出否则为空。在该次启动的
HugeGraph JVM 都已退出后可以删除旧目录，但不要动正在运行的 Server 最新的那个目录。要对所有 JVM 关闭堆转储，请在容器的环境变量中设置 `JAVA_TOOL_OPTIONS=-XX:-HeapDumpOnOutOfMemoryError`（可以使用 `docker run -e`，或在
Compose 中 Server 服务的 `environment:` 里添加，自带的 Compose 文件没有设置它，或在 Kubernetes 中使用 `env`；只在宿主机 shell 中导出不会生效），这样会保留镜像默认的 `JAVA_OPTS`；把该参数加到 `JAVA_OPTS` 中只对 Server
自身的 JVM 生效，而且会替换镜像默认值（`-XX:+UseContainerSupport -XX:MaxRAMPercentage=50 ...`），需要把这些参数一并写上。

> **版本范围**：上文描述的是基于当前 master 构建的镜像。1.7.0 及更早的镜像都没有设置 `STDOUT_MODE`，包括上文使用的单机镜像 `hugegraph/hugegraph:1.7.0`：`docker logs`
> 只能看到入口脚本的输出，服务日志仍在容器内的 `logs/` 中（Server 为 `logs/hugegraph-server.log`）。

## 容器监控与健康检查

> **版本说明**：本节描述当前主线 Docker 镜像的行为，**不包含在 `1.7.0` 镜像中**。可使用上文从主线构建并标记为 `local` 的镜像，或包含这些改动的 `latest` 镜像。

### 进程监控模型

此前，三个 Docker 入口脚本均以 `tail -f /dev/null` 结尾，即使 Java 进程崩溃，容器仍会保持运行状态。由于容器从未退出，Docker 的 `restart: unless-stopped` 策略也不会触发。

现在，入口脚本直接监控 Java 进程：

- **PD 和 Store 容器**：入口脚本向启动脚本传入 `-d false` 参数，启动脚本通过 `exec` 直接替换为 Java 进程。容器进程即为 Java 进程，当 Java 退出（崩溃或正常关闭）时，容器立即退出，Docker 的重启策略随即触发。
- **Server 容器**：入口脚本持有前台 launcher 并等待 Java。服务就绪后保留 Java 的实际退出码，包括 `0`、`42` 和 `SIGKILL` 对应的 `137`。
  `SIGTERM` 和 `SIGINT` 请求协作关闭、回收持有的就绪/分区检查进程，并在关闭后分别返回 `143` 和 `130`。
- 所有镜像中的 PID 1 均为 `dumb-init`，负责将 Docker 信号转发给入口脚本进程。

### Server 启动等待超时

`HG_SERVER_STARTUP_TIMEOUT_S` 设置 Docker 入口脚本等待 REST 就绪的期限，未设置时默认 **120 秒**。取值必须是不带前导零的十进制整数，范围为 **1–86400 秒**。空字符串、`0`、负数、小数和超出范围的值都会使入口脚本记录错误并以退出码 `1` 退出。

入口脚本也通过 `bin/start-hugegraph.sh -t` 传入该值；前台 launcher 本身等待 Java，不轮询 REST。
启动期限失败、或 Java 在就绪前以 `0` 退出时，入口脚本返回 `1`；提前以非零码退出则保留该退出码。
此时长不包括此前的存储初始化或等待后端就绪的时间。关闭时可以中断就绪和分区检查；启动期限失败会请求终止 Java 并返回，不增加无限等待。
未响应终止请求的 Java 进程仍依靠容器终止完成最终清理。

例如，在 HugeGraph 仓库的 `docker/` 目录下，将单机 Server 的启动等待时间增加到 300 秒（Compose 文件会将该变量传入容器）：

```bash
HG_SERVER_STARTUP_TIMEOUT_S=300 HUGEGRAPH_VERSION=latest \
  docker compose -f docker-compose.yml up -d --wait
```

该设置与 Docker 健康检查的 `start_period`、`interval`、`timeout` 和 `retries` 相互独立。健康检查参数决定何时将容器标记为 `unhealthy`；仅增加健康检查的等待时间，不会延长 Server 启动脚本的等待期限。调整此变量也不会自动修改健康检查参数，启动较慢时应分别检查这两组设置。

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
