---
title: "ToplingDB development integration"
linkTitle: "ToplingDB (development)"
weight: 11
description: "Build the optional ToplingDB runtime from development source, isolate its data, and understand startup and recovery boundaries."
---

> **Unreleased development interface.** This guide describes the proposed replacement for the 2025 ToplingDB integration.
> It requires a complete source checkout containing the integration and its lifecycle and snapshot-recovery prerequisites.
> These changes are under review; existing HugeGraph releases and registry tags do not establish support for this interface.
> Follow the [integration proposal](https://github.com/hugegraph/hugegraph/pull/264) for its delivery status.

## Choose the process that owns the database

| Deployment | Process that loads Topling JNI | Provider setting |
|---|---|---|
| Standalone RocksDB Server | Server | `rocksdb.provider=topling` in `conf/graphs/hugegraph.properties` |
| HStore PD | Each PD | `provider: topling` under `rocksdb` in `conf/application.yml` |
| HStore Store | Each Store | `provider: topling` under `rocksdb` in `conf/application-pd.yml` |
| HStore-backed Server | None | No local Topling setting |

PD and Store select their providers independently. The HStore-backed Server is a remote client and does not need a Topling JAR or native library.
Provider selection happens at process startup. All local RocksDB graphs within one Server process must agree on the provider.

The historical `rocksdb.option_path` and `rocksdb.open_http` examples describe a different integration.
Do not copy that configuration into this development interface. The component's launch scripts select the Easy Migrate YAML file.

## Build an optional distribution

Build on Linux x86_64 with Java 11+, Maven 3.5+, `rsync`, `unzip`, and `tar`.
The Server mount preflight additionally requires util-linux 2.37+ `mountpoint` on `PATH`.
Native macOS execution is outside this integration's support matrix; use a Linux x86_64 container when working on macOS.

Obtain a compatible Topling Easy Migrate JNI JAR from its producer, together with its source revision, dependency licenses, notices, and trusted SHA-256.
The HugeGraph source tree does not include this binary. A checksum identifies an artifact; it does not establish its origin, license, or runtime compatibility.
Verify redistribution rights and retain the required license and notice files before distributing a derived package or image.

From the complete source checkout containing this feature:

```bash
VERSION=$(mvn help:evaluate -Dexpression=project.version -q -DforceStdout)
mvn clean package \
  -pl hugegraph-server/hugegraph-dist,hugegraph-pd/hg-pd-dist,hugegraph-store/hg-store-dist \
  -am -Dmaven.test.skip=true -Dmaven.javadoc.skip=true -ntp

export TOPLING_JNI_JAR=/absolute/path/to/rocksdbjni-topling.jar
export TOPLING_JNI_SHA256='<trusted 64-character SHA-256>'
install-dist/scripts/build-topling-distribution.sh server "$VERSION"
# Generate these only when running HStore:
install-dist/scripts/build-topling-distribution.sh pd "$VERSION"
install-dist/scripts/build-topling-distribution.sh store "$VERSION"
```

The Maven build creates standard packages. The generator creates separate `-topling` directories and archives beside them.
It copies the external JAR into private staging, verifies that copy, and prepares the native library.
Missing inputs, a checksum mismatch, or incompatible JAR structure stop generation; the generator does not search a Maven cache or download a substitute.
Build success is not a native runtime acceptance test.

Each Topling package contains `lib/topling/rocksdbjni-topling.jar`, `lib/topling/runtime.properties`,
`library/librocksdbjni-linux64.so`, and the component's preparation and preload scripts.
Run `bin/prepare-topling.sh` again after replacing the installed Topling JAR.

For container builds, use the matching checkout's `docker/README.md` and `docker/bake.hcl` with the same external JNI inputs.
Build locally before using the example `topling` tags and select `pull_policy: never` for that local deployment.
For registry images, verify the source revision, JNI identity, and digest first. A tag or a healthy container alone does not prove which JNI is running.

## Configure isolated data

Changing the provider does not migrate or convert data. Give Topling a separate data directory and keep the standard RocksDB directory unchanged.
Use these component-specific settings:

| Component | Data setting | Example Topling root |
|---|---|---|
| Server | `rocksdb.data_path` | `/srv/hugegraph/topling/server` |
| PD | `pd.data-path` | `/srv/hugegraph/topling/pd` |
| Store | `app.data-path` | `/srv/hugegraph/topling/store` |

For a standalone Server, edit the generated distribution's `conf/graphs/hugegraph.properties`:

```properties
backend=rocksdb
rocksdb.provider=topling
rocksdb.data_path=/srv/hugegraph/topling/server
```

Mount or create the configured Topling root as a real directory before startup. Do not use symlinked path components.
Mount the parent data root, not an individual store directory such as `data/g`; sibling recovery files must remain visible to all cooperating processes.
The standalone Server launcher rejects individual store mounts before starting Java, including same-filesystem bind mounts on Linux.
Keep the mount layout unchanged throughout startup and recovery.

The `.hugegraph-rocksdb-provider` marker guards against accidental directory reuse; it is not a converter.
A conflicting marker stops startup. Topling also rejects an unmarked, non-empty data directory.
Standard RocksDB retains compatibility with existing unmarked data, but that is not permission to open a directory modified by Topling.

## Start, verify, and stop

Run from the standalone Topling distribution:

```bash
bin/init-store.sh
bin/start-hugegraph.sh
curl --fail http://127.0.0.1:8080/versions
# Stop cleanly when finished:
bin/stop-hugegraph.sh
```

For HStore, configure the normal network addresses and start PD, then Store, then the HStore-backed Server.
Use `bin/start-hugegraph-pd.sh`, `bin/start-hugegraph-store.sh`, and `bin/start-hugegraph.sh` in their respective distributions.

The launcher reports `TOPLINGDB_EASY_MIGRATE_CONF`. Check that it names the intended component file:

| Component | Easy Migrate YAML | Monitor binding |
|---|---|---|
| Server | `conf/toplingdb.yaml` | `127.0.0.1:2011` |
| PD | `conf/rocksdb_pd.yaml` | `127.0.0.1:2012` |
| Store | `conf/rocksdb_store.yaml` | `127.0.0.1:2013` |

The sample files set `http.auto_start_http: false`. The monitor has no authentication; keep its loopback binding if you enable it.
Do not use the old `rocksdb.open_http` switch.

Before accepting a deployment, verify the loaded RocksDB Java class's JAR origin, the unique JNI selected for that process,
and the mapped native library and their SHA-256 values against the prepared artifact.
Then verify schema and data operations, persistence after restart, clean shutdown, and rejection of invalid provider or conflicting data directories.
Startup logs, a provider variable, and `/versions` are useful checks but do not by themselves prove a real Topling runtime.

Finish application transactions explicitly. Request cleanup releases thread-local transactions but does not commit unfinished work.
During planned shutdown, stop new writes and check in-flight outcomes; cancellation can fail requests.
Store waits for callbacks and workers before closing its databases. If its stop script times out, it returns a failure and retains the PID file.
Inspect logs and thread dumps; do not force a second database close underneath active workers.

## Recover an interrupted standalone snapshot restore

This protocol applies to local RocksDB adapter snapshot restore. It does not provide atomic whole-graph restore or an HStore multi-partition protocol.
Before replacing data, restore records its checkpoint and WAL location in a sibling `<data-path>.resume-pending` file.
A subsequent open retries the interrupted installation before native recovery.
Missing checkpoints, incomplete metadata, or a changed WAL configuration stop opening.

Keep the checkpoint, pending marker, and configured paths. Restore access or free space, then retry normal startup with the same runtime and configuration.
Do not delete the pending marker or `<data-path>.resume-lock` to force startup.
The operating-system lock remains held until the database closes; the retained lock file alone does not indicate an active owner.
Older binaries and unrelated writers do not honor this protocol and must not access the same directories concurrently.

Independent WAL, WAL inside data, and data inside a WAL root use in-place log replacement. Preserve WAL symlink configuration across retries.
Successful native reopening clears the pending marker and then attempts checkpoint cleanup.
Interrupted-operation tests do not establish power-cut durability.

## Upgrade or return to standard RocksDB

Validate old data created with the previous runtime before a standard RocksDB dependency upgrade.
Creating a new database and restarting it does not test old-data compatibility.

To return from Topling to standard RocksDB, stop writers and stop the component cleanly, preserve the Topling data,
and restore a full pre-Topling backup into a new, empty directory using its compatible standard runtime.
Validate schema, reads, writes, and restart before serving traffic. Do not point standard RocksDB at a directory Topling has modified.
