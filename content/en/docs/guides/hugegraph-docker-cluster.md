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

Four compose files are available in the [`docker/`](https://github.com/apache/hugegraph/tree/master/docker) directory of the HugeGraph main repository:

| File | Services | When to use it |
|------|----------|----------------|
| `docker-compose.yml` | 1 RocksDB Server + 1 Hubble | Default standalone quickstart, start here |
| `docker-compose-hstore.yml` | 1 PD + 1 Store + 1 Server + 1 Hubble | Distributed local development |
| `docker-compose-3pd-3store-3server.yml` | 3 PD + 3 Store + 3 Server + 1 Hubble | HA reference and evaluation |
| `docker-compose.dev.yml` | (override only) | Source build overlay for the minimal HStore topology, always used together with `docker-compose-hstore.yml` |

The standalone topology uses `hugegraph/hugegraph:${HUGEGRAPH_VERSION:-latest}`. The HStore topologies use the matching `hugegraph/pd`, `hugegraph/store`, and `hugegraph/server` tags. Hubble is selected independently with `${HUBBLE_IMAGE:-hugegraph/hubble:latest}`.

> **Note**: The following steps assume you have already cloned or pulled the HugeGraph main repository locally, or at least have its `docker/` directory available.

## Authentication Environment

All topologies read the administrator password and the shared JWT secret from the Compose environment, normally a `docker/.env` file:

```bash
HUGEGRAPH_ADMIN_PASSWORD='replace-with-your-password'
HUGEGRAPH_AUTH_TOKEN_SECRET='<32 random bytes, for example openssl rand -hex 32>'
```

A non-empty `HUGEGRAPH_ADMIN_PASSWORD` enables Server authentication, and Hubble detects that mode through the Server API. Omitting it, or setting it to an empty value, disables authentication, which is only suitable for a trusted local environment. Keeping the same JWT secret preserves tokens when containers are recreated, and every Server replica in a multi-Server topology receives the same secret. The HA topology sets `HG_SERVER_REQUIRE_AUTH_TOKEN_SECRET: "true"`, so it fails fast when a password is supplied without the shared secret. Do not commit `.env`.

`HUGEGRAPH_ADMIN_PASSWORD` initializes the built-in `admin` account on the first authenticated startup. Changing it later does not rotate an existing password, use the user API for that.

## Single-Node Quickstart

```bash
cd hugegraph/docker
# Keep the version aligned with the latest release, for example 1.x.0
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose.yml up -d --wait
```

Verify:
```bash
curl http://localhost:8080/versions
curl http://localhost:8088/about        # Hubble
```

Hubble is published on host loopback (`127.0.0.1:8088`) by default. Set `HUBBLE_PUBLISH_HOST` only behind an HTTPS reverse proxy and trusted network controls.

## Minimal HStore Quickstart

```bash
cd hugegraph/docker
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-hstore.yml up -d --wait
```

Verify:
```bash
curl http://localhost:8620/v1/health    # PD
curl http://localhost:8520/v1/health    # Store
curl http://localhost:8080/versions     # Server
curl http://localhost:8088/about        # Hubble
```

To build this topology from local source instead of pulling images, add the development overlay and keep both files on every later lifecycle command:

```bash
docker compose -f docker-compose-hstore.yml -f docker-compose.dev.yml up -d --build --wait
```

## 3-Node Cluster Quickstart

```bash
cd hugegraph/docker
HUGEGRAPH_VERSION=1.7.0 docker compose -f docker-compose-3pd-3store-3server.yml up -d --wait
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

With authentication on, a graph listing must reject an anonymous request and accept the administrator:

```bash
curl -o /dev/null -w '%{http_code}\n' \
  http://localhost:8080/graphspaces/DEFAULT/graphs                      # expect 401
curl -o /dev/null -w '%{http_code}\n' -u "admin:${HUGEGRAPH_ADMIN_PASSWORD}" \
  http://localhost:8080/graphspaces/DEFAULT/graphs                      # expect 200
```

The other two Servers answer on `8081` and `8082`, and the other PD and Store nodes on `8621`/`8622` and `8521`/`8522`.

## Environment Variable Reference

The PD and Store entrypoints turn their variables into a `SPRING_APPLICATION_JSON` document and log the effective values at startup, so `docker logs` shows exactly what a container resolved. The Server entrypoint instead rewrites keys in `conf/graphs/hugegraph.properties` and `conf/rest-server.properties`.

### PD Variables

| Variable | Required | Default | Maps To |
|----------|----------|---------|---------|
| `HG_PD_GRPC_HOST` | Yes | (none) | `grpc.host` |
| `HG_PD_RAFT_ADDRESS` | Yes | (none) | `raft.address` |
| `HG_PD_RAFT_PEERS_LIST` | Yes | (none) | `raft.peers-list` |
| `HG_PD_INITIAL_STORE_LIST` | Yes | (none) | `pd.initial-store-list` |
| `HG_PD_GRPC_PORT` | No | `8686` | `grpc.port` |
| `HG_PD_REST_PORT` | No | `8620` | `server.port` |
| `HG_PD_DATA_PATH` | No | `/hugegraph-pd/pd_data` | `pd.data-path` |
| `HG_PD_INITIAL_STORE_COUNT` | No | `1` | `pd.initial-store-count` |

> **Deprecated aliases**: `GRPC_HOST` → `HG_PD_GRPC_HOST`, `RAFT_ADDRESS` → `HG_PD_RAFT_ADDRESS`, `RAFT_PEERS` → `HG_PD_RAFT_PEERS_LIST`, `PD_INITIAL_STORE_LIST` → `HG_PD_INITIAL_STORE_LIST`. A deprecated name is mapped to the new one only when the new one is unset, and the entrypoint logs a warning. The entrypoint exits with code 2 when any required variable is missing.

### Store Variables

| Variable | Required | Default | Maps To |
|----------|----------|---------|---------|
| `HG_STORE_PD_ADDRESS` | Yes | (none) | `pdserver.address` |
| `HG_STORE_GRPC_HOST` | Yes | (none) | `grpc.host` |
| `HG_STORE_RAFT_ADDRESS` | Yes | (none) | `raft.address` |
| `HG_STORE_GRPC_PORT` | No | `8500` | `grpc.port` |
| `HG_STORE_REST_PORT` | No | `8520` | `server.port` |
| `HG_STORE_DATA_PATH` | No | `/hugegraph-store/storage` | `app.data-path` |

> **Deprecated aliases**: `PD_ADDRESS` → `HG_STORE_PD_ADDRESS`, `GRPC_HOST` → `HG_STORE_GRPC_HOST`, `RAFT_ADDRESS` → `HG_STORE_RAFT_ADDRESS`

### Server Variables

Unlike PD and Store, the Server entrypoint requires nothing: every variable below is optional and only the ones that are set are written into the config files. A distributed deployment still needs at least `HG_SERVER_BACKEND` and `HG_SERVER_PD_PEERS`.

| Variable | Default | Maps To |
|----------|---------|---------|
| `HG_SERVER_BACKEND` | template value (`rocksdb`, or `hstore` in the `hugegraph/server` image) | `backend` in `conf/graphs/hugegraph.properties` |
| `HG_SERVER_PD_PEERS` | (none) | `pd.peers` in both `hugegraph.properties` and `rest-server.properties` |
| `HG_SERVER_USE_PD` | `false` | `usePD` in `rest-server.properties` |
| `HG_SERVER_CLUSTER` | `hg-test` | `cluster` in `rest-server.properties` |
| `HG_SERVER_REST_URL` | `http://0.0.0.0:8080` (set in the image) | `restserver.url` |
| `HG_SERVER_MIN_FREE_MEMORY` | `64` (MB) | `restserver.min_free_memory` |
| `HG_SERVER_INIT_STORE_ENABLED` | `true` | `init_store.enabled`, set `false` for PD/HStore deployments where the storage side owns the metadata |
| `HG_SERVER_AUTH_TOKEN_SECRET` | generated when `PASSWORD` is set | `auth.token_secret` in both files, must be at least 32 bytes |
| `HG_SERVER_REQUIRE_AUTH_TOKEN_SECRET` | `false` | when `true`, refuses to start if `PASSWORD` is set without `HG_SERVER_AUTH_TOKEN_SECRET` |
| `PASSWORD` | (none) | `auth.admin_pa`, and runs `bin/enable-auth.sh` to turn auth mode on |
| `PRELOAD` | (none) | `true` preloads the sample graph from `scripts/example.groovy` |
| `JAVA_OPTS` | set in the image | passed to `bin/start-hugegraph.sh -j` |
| `STORE_REST` | `store:8520` | Store REST endpoint that `wait-partition.sh` polls, hstore backend only |
| `HG_SERVER_PD_REST_ENDPOINT` | derived by rewriting `:8686` to `:8620` in `pd.peers` | PD REST peers that `wait-storage.sh` polls |
| `PD_AUTH_USER` / `PD_AUTH_PASSWORD` | `store` / `admin` | credentials `wait-storage.sh` uses against the PD REST API |
| `WAIT_PARTITION_TIMEOUT_S` | `120` | how long `wait-partition.sh` waits for partition assignment |

`wait-storage.sh` waits up to 300 seconds for a store in state `Up`. That budget is fixed in the script and cannot be raised from the environment.

> **Deprecated aliases**: `BACKEND` → `HG_SERVER_BACKEND`, `PD_PEERS` → `HG_SERVER_PD_PEERS`

`HG_SERVER_INIT_STORE_ENABLED` accepts only the spellings `HugeConfig` accepts, case-insensitively: `y`, `t`, `yes`, `on`, `true`, `n`, `f`, `no`, `off`, `false`. Anything else, `0` and `1` included, aborts the entrypoint.

The entrypoint writes `docker/init_complete` after a successful initialization and skips re-initialization on later startups, but still re-runs `bin/init-store.sh` so a disabled one revalidates its configuration on every start.

### Compose Variables

These are read by the Compose files rather than by the entrypoints:

| Variable | Default | Purpose |
|----------|---------|---------|
| `HUGEGRAPH_VERSION` | `latest` | Image tag for Server, PD, and Store |
| `HUGEGRAPH_PULL_POLICY` | `missing` | `pull_policy` for those images, use `never` to keep locally built ones |
| `HUBBLE_IMAGE` | `hugegraph/hubble:latest` | Hubble image, selected independently of `HUGEGRAPH_VERSION` |
| `HUBBLE_PULL_POLICY` | `missing` | `pull_policy` for the Hubble image |
| `HUBBLE_PUBLISH_HOST` | `127.0.0.1` | Host interface Hubble's `8088` is published on |
| `HUGEGRAPH_ADMIN_PASSWORD` | (none) | Passed to the Server as `PASSWORD` |
| `HUGEGRAPH_AUTH_TOKEN_SECRET` | (none) | Passed to the Server as `HG_SERVER_AUTH_TOKEN_SECRET` |

## Port Reference

Ports published by the 3-node cluster:

| Service | Host Port | Container Port | Purpose |
|---------|-----------|----------------|---------|
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

The standalone topology publishes only `8080` and `8088`. The minimal HStore topology publishes `8620` (PD REST), `8520` (Store REST), `8080`, and `8088`. PD Raft uses `8610` inside the network and is not published by any topology.

## Troubleshooting

1. **Containers exit due to OOM (`exit code 137`)**: Increase Docker Desktop memory to at least 12 GB, or reduce the JVM heap settings for the process that is being killed.

2. **Raft leader election timeout**: Check that `HG_PD_RAFT_PEERS_LIST` is identical on all PD nodes. Verify connectivity with `docker exec hg-pd0 ping pd1`.

3. **Partition assignment does not complete**: Check `curl http://localhost:8620/v1/stores` and confirm that all 3 stores show `"state":"Up"` before partition assignment can finish.

4. **Connection refused**: Ensure `HG_*` environment variables use container hostnames (`pd0`, `store0`) instead of `127.0.0.1`.

5. **Data survives a restart when you did not expect it to**: `docker compose down` keeps the named volumes. Use `docker compose down -v` to delete the topology's data as well.

**Viewing runtime logs**: Use `docker logs <container-name>` (e.g. `docker logs hg-pd0`) to view logs directly without exec-ing into the container. The standalone `hugegraph/hugegraph` image sets `STDOUT_MODE=true`, so its server log goes to the container stdout. The `hugegraph/server` (HStore) image does not, so `docker logs` on a Server of an HStore topology shows only the entrypoint output; read `logs/hugegraph-server.log` inside the container for the rest.

## Container Supervision & Health Checks

> **Version note**: This behavior is **not present in the `1.7.0` images**. Use `HUGEGRAPH_VERSION=latest` or wait for the next release tag.

### Process Supervision Model

Previously, all three Docker entrypoints ended with `tail -f /dev/null`, which kept the container running even if the Java process crashed. Docker's `restart: unless-stopped` policy never fired because the container never exited.

The entrypoints now supervise Java directly:

- **PD and Store containers**: the entrypoint passes `-d false` to the startup script, which `exec`s Java directly. The container process IS the Java process: when Java exits (crash or clean shutdown), the container exits immediately and Docker's restart policy fires.
- **Server container**: the entrypoint uses `tail --pid=$PID -f /dev/null` to block until Java exits. A `SIGTERM`/`SIGINT` trap forwards `docker stop` signals to Java and waits for clean shutdown (exits 0). If Java crashes, the entrypoint exits 1 so the restart policy fires.
- `dumb-init` (PID 1 in all images) forwards signals from Docker to the entrypoint process.

### Health Check Endpoints

All four Docker images now include a `HEALTHCHECK` instruction. `docker ps` shows real health status. During the 90-second start period, failed checks do not count. After that, three consecutive failures mark the container as `unhealthy`.

| Image | Health endpoint | Port | Parameters |
|-------|-----------------|------|------------|
| `hugegraph/hugegraph` (standalone RocksDB Server) | `GET /versions` | 8080 | `--interval=15s --timeout=10s --start-period=90s --retries=3` |
| `hugegraph/server` (HStore Server) | `GET /versions` | 8080 | same |
| `hugegraph/pd` | `GET /v1/health` | 8620 | same |
| `hugegraph/store` | `GET /v1/health` | 8520 | same |

The Compose files define their own health checks on top of these, so `--wait` and `depends_on: condition: service_healthy` work without relying on the image defaults. Those Compose checks use a shorter start period (30 to 120 seconds depending on the service and topology) and more retries.

> **Note**: The `-m true` flag (cron-based monitor) in `start-hugegraph.sh` is for VM/bare-metal deployments only. It is not installed or used in Docker images. Docker users should rely on the built-in `HEALTHCHECK` and Docker's restart policy instead.
