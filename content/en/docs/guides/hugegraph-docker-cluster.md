---
title: "HugeGraph Docker Cluster Guide"
linkTitle: "Docker Cluster"
weight: 6
---

## Overview

Docker Compose provides a quick way to run a complete HugeGraph distributed cluster (PD + Store + Server) on Linux or macOS.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop 4.x+
- Docker Compose v2
- For a three-node cluster on macOS, allocate at least **12 GB** of memory (Settings → Resources → Memory). Adjust resources to suit other platforms.

> **Tested environments**: Linux (native Docker) and macOS (Docker Desktop on ARM M4).

## Compose Files

The HugeGraph repository provides four Compose files in [`docker/`](https://github.com/apache/hugegraph/tree/master/docker):

| File | Services | Use case |
|------|------|----------|
| `docker-compose.yml` | 1 RocksDB Server + 1 Hubble | Default standalone Quick Start; recommended starting point |
| `docker-compose-hstore.yml` | 1 PD + 1 Store + 1 Server + 1 Hubble | Local distributed development |
| `docker-compose-3pd-3store-3server.yml` | 3 PD + 3 Store + 3 Server + 1 Hubble | HA reference and evaluation |
| `docker-compose.dev.yml` | Override only | Source-build override for the minimal HStore topology; always combine with `docker-compose-hstore.yml` |

Standalone uses `hugegraph/hugegraph:${HUGEGRAPH_VERSION:-latest}`; HStore uses matching `hugegraph/pd`, `hugegraph/store`, and `hugegraph/server` tags. Hubble is selected separately by `${HUBBLE_IMAGE:-hugegraph/hubble:latest}`.

> The following steps assume you have cloned the `hugegraph` repository, or at least its `docker/` directory.

HStore and HA instructions use current master Compose files and require PD, Store, and Server images built from the same master source. Do not combine these files with HStore component images tagged `1.7.0`. The standalone example separately pins `hugegraph/hugegraph:1.7.0`.

## Authentication Environment

This `.env` template applies to current master Compose. Angle-bracket values and `replace-with-your-password` are placeholders: replace them before loading the file or starting services. Follow the [master authentication environment instructions](https://github.com/apache/hugegraph/blob/master/docker/README.md#create-the-authentication-environment) to generate `.env`, then replace the administrator password placeholder:

```bash
HUGEGRAPH_ADMIN_PASSWORD='replace-with-your-password'
HUGEGRAPH_AUTH_TOKEN_SECRET='<32 random bytes, e.g. openssl rand -hex 32>'
HG_PD_AUTH_SECRET_KEY='<24 random bytes, e.g. openssl rand -hex 24>'
```

For master HStore and HA topologies, `HG_PD_AUTH_SECRET_KEY` is the PD REST Basic password, shared by all PD nodes, Server, and Hubble. Current master PD Docker images require it. Hubble does not read `.env` directly: generate the local configuration for its topology using this value before startup, as described below. Do not commit `.env` or generated `.local.properties` files.

A nonempty `HUGEGRAPH_ADMIN_PASSWORD` enables Server authentication through `PASSWORD`; Hubble detects this mode through the Server API. It initializes the built-in `admin` password only on first initialization. An unset or empty value disables authentication and is suitable only for trusted local environments.

Current master Compose passes `HUGEGRAPH_AUTH_TOKEN_SECRET` as `HG_SERVER_AUTH_TOKEN_SECRET`. A shared secret lets master Server replicas verify the same tokens and retain token validity after container recreation; HA Compose requires an explicit secret. The standalone `hugegraph/hugegraph:1.7.0` entrypoint enables authentication through `PASSWORD` but ignores `HG_SERVER_AUTH_TOKEN_SECRET`, so this `.env` variable does not fix its JWT secret. For a stable JWT secret in 1.7.0, explicitly set `auth.token_secret` in its authentication graph configuration, `conf/graphs/hugegraph.properties`, and persist that file across container replacement. See the [authentication guide](/docs/config/config-authentication/) for graph paths and secret generation.

Changing `HUGEGRAPH_ADMIN_PASSWORD` later does not rotate an existing password; use the user API.

> [!WARNING]
> **Production component access controls**
>
> In production, enable [Server authentication and authorization](/docs/config/config-authentication/) for graph APIs, maintain the Server IP allowlist, grant minimum permissions, and retain Server `audit-*.log` with restricted read access. Configure PD REST credentials and PD/Store gRPC, Raft, and REST network boundaries separately; Server Auth does not protect those ports. Expose PD/Store only to cluster nodes and trusted operations networks.

## Standalone Quick Start

This section pins the standalone image `hugegraph/hugegraph:1.7.0`. HStore/HA examples use master-built images; do not reuse this version for them.

```bash
cd "$(git rev-parse --show-toplevel)/docker"
# Standalone RocksDB Server image example
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose.yml up -d --wait
```

Verify:
```bash
curl -fsS http://localhost:8080/versions
curl -fsS http://localhost:8088/about        # Hubble
```

Hubble binds only to host loopback (`127.0.0.1:8088`) by default. Set `HUBBLE_PUBLISH_HOST` only behind an HTTPS reverse proxy and trusted network controls.

## Minimal HStore Quick Start (Current Master Images)

Build PD, Store, and HStore Server images from the HugeGraph Server master repository root:

```bash
cd "$(git rev-parse --show-toplevel)"
docker build -f hugegraph-pd/Dockerfile -t hugegraph/pd:local .
docker build -f hugegraph-store/Dockerfile -t hugegraph/store:local .
docker build -f hugegraph-server/Dockerfile-hstore -t hugegraph/server:local .
```

From the repository root, enter `docker/`, load `.env`, and generate Hubble configuration for the minimal topology. A read-only bind mount cannot create a valid missing `hstore.local.properties`; generate it before startup:

```bash
cd "$(git rev-parse --show-toplevel)/docker"
set -a; . ./.env; set +a
./set-hubble-pd-password.sh hstore
HUGEGRAPH_VERSION=local HUGEGRAPH_PULL_POLICY=never \
  docker compose -f docker-compose-hstore.yml up -d --wait
```

Verify:
```bash
set -a; . ./.env; set +a
curl -fsS http://localhost:8620/v1/health    # PD
curl -fsS http://localhost:8520/v1/health    # Store
curl -fsS http://localhost:8080/versions     # Server
curl -fsS http://localhost:8088/about        # Hubble
curl -fsS -u "hg:${HG_PD_AUTH_SECRET_KEY:?Load .env first}" \
  http://localhost:8620/v1/stores       # Check registered Stores with PD REST authentication
```

To build this topology from local source instead of pulling images, add the development override and keep both files in all subsequent lifecycle commands:

```bash
cd "$(git rev-parse --show-toplevel)/docker"
set -a; . ./.env; set +a
./set-hubble-pd-password.sh hstore
docker compose -f docker-compose-hstore.yml -f docker-compose.dev.yml up -d --build --wait
```

The override builds images tagged `dev`. If you already built `local` images above, start with the base Compose file and `HUGEGRAPH_VERSION=local`; keep the tag choices consistent.

## Three-Node Cluster Quick Start (Current Master Images)

HA Compose has no source-build override. First build `hugegraph/pd:local`, `hugegraph/store:local`, and `hugegraph/server:local` from the same master source as in the minimal HStore section, then load `.env` in `docker/`, generate HA Hubble configuration, and start:

```bash
cd "$(git rev-parse --show-toplevel)/docker"
set -a; . ./.env; set +a
./set-hubble-pd-password.sh hstore-ha
HUGEGRAPH_VERSION=local \
  docker compose -f docker-compose-3pd-3store-3server.yml up -d --wait
```

HA Hubble bind-mounts `conf/hubble/hstore-ha.local.properties`; generate this before startup. It is separate from the minimal topology's `hstore.local.properties`, but both use the same `HG_PD_AUTH_SECRET_KEY` from `.env`.

The default startup order is:
1. PD nodes start first and must pass `/v1/health` checks.
2. Store nodes start after all PD nodes are healthy.
3. Server nodes start after all Store and PD nodes are healthy.

Verify the cluster: PD `/v1/health` and `/v1/ready` probes require no authentication. Store registration and partition queries are protected PD REST management APIs: use Basic username `hg` and `HG_PD_AUTH_SECRET_KEY` from `.env`.

```bash
set -a; . ./.env; set +a
curl -fsS http://localhost:8620/v1/health      # PD health check
curl -fsS http://localhost:8520/v1/health      # Store health check
curl -fsS http://localhost:8080/versions        # Server
for port in 8620 8621 8622; do
  curl -fsS "http://localhost:${port}/v1/ready" | grep -q '"ready":true' || exit 1
done
curl -fsS -u "hg:${HG_PD_AUTH_SECRET_KEY:?Load .env first}" \
  http://localhost:8620/v1/stores          # Authenticated Store registration query
curl -fsS -u "hg:${HG_PD_AUTH_SECRET_KEY:?Load .env first}" \
  http://localhost:8620/v1/partitions      # Authenticated partition query
curl -fsS http://localhost:8088/about           # Hubble
```

With authentication enabled, graph listing should reject anonymous access and accept the administrator:

```bash
set -a; . ./.env; set +a
curl -o /dev/null -w '%{http_code}\n' \
  http://localhost:8080/graphspaces/DEFAULT/graphs                      # Expect 401
curl -o /dev/null -w '%{http_code}\n' -u "admin:${HUGEGRAPH_ADMIN_PASSWORD}" \
  http://localhost:8080/graphspaces/DEFAULT/graphs                      # Expect 200
```

The other Server nodes listen on `8081` and `8082`; the remaining PD and Store nodes use `8621`/`8622` and `8521`/`8522`.

## Environment Variable Reference

The following tables describe current master entrypoints and Compose files, not the standalone `hugegraph/hugegraph:1.7.0` environment-variable contract. PD and Store build `SPRING_APPLICATION_JSON` from their variables and log selected nonsensitive settings at startup. PD secrets are excluded from that summary. Use `docker logs` to check listed settings; an absent secret in the logs does not establish whether it was applied. Server instead rewrites keys in `conf/graphs/hugegraph.properties` and `conf/rest-server.properties`.

### PD Variables

| Variable | Required | Default | Configuration mapping |
|------|------|--------|----------|
| `HG_PD_GRPC_HOST` | Yes | None | `grpc.host` |
| `HG_PD_RAFT_ADDRESS` | Yes | None | `raft.address` |
| `HG_PD_RAFT_PEERS_LIST` | Yes | None | `raft.peers-list` |
| `HG_PD_INITIAL_STORE_LIST` | Yes | None | `pd.initial-store-list` |
| `HG_PD_GRPC_PORT` | No | `8686` | `grpc.port` |
| `HG_PD_REST_PORT` | No | `8620` | `server.port` |
| `HG_PD_DATA_PATH` | No | `/hugegraph-pd/pd_data` | `pd.data-path` |
| `HG_PD_INITIAL_STORE_COUNT` | No | `1` | `pd.initial-store-count` |
| `HG_PD_AUTH_SECRET_KEY` | Yes (current master Docker) | None | `auth.secret-key`; PD REST Basic password, also used by Server and Hubble |

> **Deprecated aliases**: `GRPC_HOST` → `HG_PD_GRPC_HOST`, `RAFT_ADDRESS` → `HG_PD_RAFT_ADDRESS`, `RAFT_PEERS` → `HG_PD_RAFT_PEERS_LIST`, `PD_INITIAL_STORE_LIST` → `HG_PD_INITIAL_STORE_LIST`. Old names are mapped only when new names are unset, with a warning. Missing required variables cause the entrypoint to exit with code 2.

### Store Variables

| Variable | Required | Default | Configuration mapping |
|------|------|--------|----------|
| `HG_STORE_PD_ADDRESS` | Yes | None | `pdserver.address` |
| `HG_STORE_GRPC_HOST` | Yes | None | `grpc.host` |
| `HG_STORE_RAFT_ADDRESS` | Yes | None | `raft.address` |
| `HG_STORE_GRPC_PORT` | No | `8500` | `grpc.port` |
| `HG_STORE_REST_PORT` | No | `8520` | `server.port` |
| `HG_STORE_DATA_PATH` | No | `/hugegraph-store/storage` | `app.data-path` |

> **Deprecated aliases**: `PD_ADDRESS` → `HG_STORE_PD_ADDRESS`, `GRPC_HOST` → `HG_STORE_GRPC_HOST`, `RAFT_ADDRESS` → `HG_STORE_RAFT_ADDRESS`.

### Server Variables

Unlike PD and Store, Server has no mandatory entrypoint variables: only set values are written to configuration. Distributed deployment nevertheless requires at least `HG_SERVER_BACKEND` and `HG_SERVER_PD_PEERS`.

| Variable | Default | Configuration mapping |
|------|--------|----------|
| `HG_SERVER_BACKEND` | Template value (`rocksdb`, or `hstore` in `hugegraph/server`) | `backend` in `conf/graphs/hugegraph.properties` |
| `HG_SERVER_PD_PEERS` | None | `pd.peers` in `hugegraph.properties` and `rest-server.properties` |
| `HG_SERVER_USE_PD` | `false` | `usePD` in `rest-server.properties` |
| `HG_SERVER_CLUSTER` | `hg-test` | `cluster` in `rest-server.properties` |
| `HG_SERVER_REST_URL` | `http://0.0.0.0:8080` (set in the image) | `restserver.url` |
| `HG_SERVER_MIN_FREE_MEMORY` | `64`（MB） | `restserver.min_free_memory` |
| `HG_SERVER_INIT_STORE_ENABLED` | `true` | `init_store.enabled`; set `false` for PD/HStore deployments whose metadata is managed by storage |
| `HG_SERVER_AUTH_TOKEN_SECRET` | Generated when `PASSWORD` is set | `auth.token_secret` in both configuration files; at least 32 bytes |
| `HG_SERVER_REQUIRE_AUTH_TOKEN_SECRET` | `false` | When `true`, refuse startup if `PASSWORD` is set without `HG_SERVER_AUTH_TOKEN_SECRET` |
| `PASSWORD` | None | `auth.admin_pa`; runs `bin/enable-auth.sh` to enable authentication |
| `PRELOAD` | None | When `true`, preload the example graph from `scripts/example.groovy` |
| `JAVA_OPTS` | Set in the image | Passed to `bin/start-hugegraph.sh -j` |
| `HG_SERVER_STARTUP_TIMEOUT_S` | `120` seconds | Passed to `bin/start-hugegraph.sh -t`, range `1`–`86400`; see Server startup timeout below |
| `STORE_REST` | `store:8520` | Store REST address polled by `wait-partition.sh`, for HStore only |
| `HG_SERVER_PD_REST_ENDPOINT` | Derived from `pd.peers` by replacing `:8686` with `:8620` | PD REST address polled by `wait-storage.sh` |
| `PD_AUTH_USER` | `store` | Basic username for PD REST calls from `wait-storage.sh` |
| `PD_AUTH_PASSWORD` | Empty | PD REST Basic password; must match `HG_PD_AUTH_SECRET_KEY` when PD REST authentication is enabled |
| `WAIT_PARTITION_TIMEOUT_S` | `120` | Partition allocation wait time in `wait-partition.sh` |

> **Deprecated aliases**: `BACKEND` → `HG_SERVER_BACKEND`, `PD_PEERS` → `HG_SERVER_PD_PEERS`.

`wait-storage.sh` waits up to 300 seconds for an `Up` Store. This duration is hardcoded and cannot be changed through environment variables.

`HG_SERVER_INIT_STORE_ENABLED` accepts only the case-insensitive boolean values recognized by `HugeConfig`: `y`, `t`, `yes`, `on`, `true`, `n`, `f`, `no`, `off`, `false`. Other values, including `0` and `1`, terminate the entrypoint.

After successful initialization, the entrypoint writes `docker/init_complete`; later starts skip reinitialization but still invoke `bin/init-store.sh` to revalidate configuration each time initialization is disabled.

### Compose Variables

Compose files, rather than entrypoints, read these variables:

| Variable | Default | Purpose |
|------|--------|------|
| `HUGEGRAPH_VERSION` | `latest` | Server, PD, and Store image tag |
| `HUGEGRAPH_PULL_POLICY` | `missing` | Image `pull_policy`; use `never` to retain locally built images |
| `HUBBLE_IMAGE` | `hugegraph/hubble:latest` | Hubble image, selected independently of `HUGEGRAPH_VERSION` |
| `HUBBLE_PULL_POLICY` | `missing` | Hubble image `pull_policy` |
| `HUBBLE_PUBLISH_HOST` | `127.0.0.1` | Host interface for publishing Hubble port `8088` |
| `HUGEGRAPH_ADMIN_PASSWORD` | None | Passed to Server as `PASSWORD` |
| `HUGEGRAPH_AUTH_TOKEN_SECRET` | None | Master Compose passes this to Server as `HG_SERVER_AUTH_TOKEN_SECRET`; the 1.7.0 image ignores it |
| `HG_PD_AUTH_SECRET_KEY` | None | HStore PD REST Basic password; Compose supplies it to PD and Server and uses it to generate local Hubble configuration |

## Port Reference

Published ports in the three-node cluster:

| Service | Host port | Container port | Purpose |
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
| hubble | 8088 | 8088 | Hubble UI, bound to `127.0.0.1` by default |

Standalone publishes only `8080` and `8088`; minimal HStore publishes `8620` (PD REST), `8520` (Store REST), `8080`, and `8088`. PD Raft uses internal port `8610`, unpublished in all topologies.

## Troubleshooting

1. **Container OOM exit (code 137)**: Increase Docker Desktop memory beyond 12 GB or adjust JVM memory for the killed process.

2. **Raft election timeout**: Verify every PD node has the same `HG_PD_RAFT_PEERS_LIST`. Check connectivity with `docker exec hg-pd0 ping pd1`.

3. **Partition allocation incomplete**: Load `.env` in `docker/`, then check Store registration with PD REST Basic authentication:

   ```bash
   set -a; . ./.env; set +a
   curl -fsS -u "hg:${HG_PD_AUTH_SECRET_KEY:?Load .env first}" http://localhost:8620/v1/stores
   ```

   PD can complete partition allocation once all three Stores report `"state":"Up"`.

4. **Connection refused**: Use container hostnames (`pd0`, `store0`) in `HG_*` variables rather than `127.0.0.1`.

5. **Unexpected retained data**: `docker compose down` keeps named volumes. To delete topology data too, use `docker compose down -v`.

**Runtime logs**: `docker logs <container-name>` (for example, `docker logs hg-pd0`) shows logs without entering containers. In images built from current
master, the PD, Store and both Server images (`hugegraph/hugegraph` and the HStore `hugegraph/server`) set `STDOUT_MODE=true` and send service logs to stdout.
For the Server, WARN and above from Hadoop, ZooKeeper, SOFA, Netty and Commons also reaches stdout; their INFO output and the audit and slow-query logs stay in
files. The full `hugegraph-server.log`, JVM crash logs (`hs_err_pid*.log`) and out-of-memory heap dumps (`java_pid*.hprof`) are in `/hugegraph-server/logs`.
`docker restart` keeps them, but Kubernetes starts a new container on every restart, so mount an `emptyDir` or a PersistentVolumeClaim at
`/hugegraph-server/logs` to keep them. A heap dump can be as large as the JVM heap, and every launch writes to a new file, so a Server that keeps running out of
memory adds one heap-sized dump per restart until the volume is full. The launcher never removes old dumps, whether the volume is an `emptyDir` (which also
survives container restarts) or a PVC. Size the volume for the number of dumps you want to keep plus the logs, move or delete old `java_pid*.hprof` files after
each incident, or turn dumps off with `-XX:-HeapDumpOnOutOfMemoryError`.

> **Version scope**: the paragraph above describes current master images ([apache/hugegraph#2980](https://github.com/apache/hugegraph/pull/2980) for PD, Store
> and the standalone Server, [apache/hugegraph#3258](https://github.com/apache/hugegraph/pull/3258) for the HStore Server). No 1.7.0 or older image sets
> `STDOUT_MODE`, including the standalone `hugegraph/hugegraph:1.7.0` used above: `docker logs` shows only entrypoint output, and service logs stay in `logs/`
> inside the container (`logs/hugegraph-server.log` for the Server).

## Container Monitoring and Health Checks

> **Version scope**: This section describes current master Docker images; these behaviors **are not included in 1.7.0 images**. Use the master-built `local` images above or a `latest` image containing these changes.

### Process Monitoring

Previously, all three entrypoints ended with `tail -f /dev/null`, keeping containers alive even after Java crashed. Because containers never exited, Docker's `restart: unless-stopped` policy did not trigger.

Entrypoints now monitor Java directly:

- **PD and Store**: The entrypoint passes `-d false` to the startup script, which replaces itself with Java using `exec`. When Java exits, the container exits immediately and Docker's restart policy applies.
- **Server**: The entrypoint waits with `tail --pid=$PID -f /dev/null`. `SIGTERM`/`SIGINT` traps forward Docker stop signals to Java and wait for graceful shutdown (exit 0). If Java crashes, the entrypoint exits with code 1, triggering the restart policy.
- PID 1 in every image is `dumb-init`, which forwards Docker signals to the entrypoint.

### Server Startup Timeout

`HG_SERVER_STARTUP_TIMEOUT_S` controls how long the Server startup script waits for a REST response; the default is **120 seconds**. Values must be decimal integers without leading zeros, from **1 to 86400 seconds**. Empty strings, `0`, negative numbers, fractions, and out-of-range values log an error and exit with code `1`.

The entrypoint passes this value to `bin/start-hugegraph.sh -t`. If Server does not become ready within the deadline or exits early, startup fails and the container exits with code `1`; its restart policy may restart it. This duration excludes earlier storage initialization and backend readiness waits.

For example, from the HugeGraph repository's `docker/` directory, extend the standalone Server wait to 300 seconds (Compose passes this variable to the container):

```bash
HG_SERVER_STARTUP_TIMEOUT_S=300 HUGEGRAPH_VERSION=latest \
  docker compose -f docker-compose.yml up -d --wait
```

This setting is independent of Docker health-check `start_period`, `interval`, `timeout`, and `retries`. Those determine when a container becomes `unhealthy`; extending health-check grace periods does not extend the startup script deadline. Adjusting this variable does not update health-check settings, so check both for slow startup.

### Health-Check Endpoints

All four master Docker images include `HEALTHCHECK`. `docker ps` displays health status. Failures during the 90-second startup grace period do not count; three consecutive failures afterward mark a container `unhealthy`.

| Image | Health-check endpoint | Port | Parameters |
|------|-------------|------|------|
| `hugegraph/hugegraph` (standalone RocksDB Server) | `GET /versions` | 8080 | `--interval=15s --timeout=10s --start-period=90s --retries=3` |
| `hugegraph/server` (HStore Server) | `GET /versions` | 8080 | Same as above |
| `hugegraph/pd` | `GET /v1/health` | 8620 | Same as above |
| `hugegraph/store` | `GET /v1/health` | 8520 | Same as above |

Compose defines additional health checks, so `--wait` and `depends_on: condition: service_healthy` do not depend on image-level checks. Compose uses shorter startup periods (30–120 seconds depending on service and topology) and more retries.

> **Note**: The cron-based `-m true` monitoring option in `start-hugegraph.sh` is for VM/bare-metal deployments. Docker images neither install nor use it; use built-in `HEALTHCHECK` and Docker restart policies.
