---
title: "ToplingDB development integration"
linkTitle: "ToplingDB (development)"
weight: 11
description: "Build the optional ToplingDB runtime from development source, isolate its data, and understand startup and recovery boundaries."
---

> **Unreleased development interface.** This guide follows the [three-component runtime integration](https://github.com/apache/hugegraph/pull/3275).
> Use source containing that change. Existing releases and image tags do not establish support, and runtime acceptance remains a deployment prerequisite.

## Choose the database owner

HugeGraph defaults to standard RocksDB. Enable Topling separately for each process that owns local storage:

| Component | Business provider setting | Start command |
| --- | --- | --- |
| Standalone RocksDB Server | `rocksdb.provider=topling` in each selected graph properties file | `bin/start-hugegraph.sh` |
| PD | `provider: topling` under `rocksdb` in `conf/application.yml` | `bin/start-hugegraph-pd.sh` |
| Store | `provider: topling` under `rocksdb` in `conf/application-pd.yml` | `bin/start-hugegraph-store.sh` |

A standalone Server keeps `backend=rocksdb`; an HStore-backed Server uses `backend=hstore` and needs no local Topling runtime.
All local RocksDB graphs in one Server process must use the same provider. The business setting must match the runtime selected by its launcher.

## Build and prepare a standard distribution

Build the normal distributions from the source repository root using Java 17 and Maven 3.6.3 or later:

```bash
mvn clean package -Dmaven.test.skip=true -Dmaven.javadoc.skip=true
```

Obtain a trusted Topling Easy Migrate JNI JAR and its SHA-256 through your artifact channel. Preparation requires a Java 17 JDK, Linux x86_64,
`sha256sum`, `unzip`, `od`, `ldd`, and GNU `mv`. The selected JAR's native dependencies, including its glibc and libaio requirements, must be installed.

Stop the component, unpack a fresh standard distribution, and run from that component directory:

```bash
export TOPLING_JNI_JAR=/absolute/path/to/rocksdbjni-topling.jar
export TOPLING_JNI_SHA256='<trusted-64-character-sha256>'
bash bin/prepare-topling.sh
```

The script verifies the copied JAR's hash, Topling Java marker, one Linux x86_64 JNI entry, ELF architecture and native dependencies.
Before installation, a disposable database verifies that the selected JNI actually applies EasyMigrate configuration to its persisted write-buffer size.
Unsupported builds are rejected even when their marker and hash match. The probe does not certify existing-data compatibility or every production setting.
A checksum receipt binds this verification to the installed JAR and native library; launchers reject missing or changed receipts. Use a fresh distribution
when upgrading from an older preparation script. Launch rejects inherited RocksDB JNI preloads in default/standard mode and competing JNI in Topling mode, while preserving unrelated preloads.
It installs `topling/rocksdbjni.jar`, its native library and optional web resources outside `lib`. Preparation refuses an existing `topling` directory;
replace a runtime by preparing another stopped, fresh distribution. Repeat preparation separately for Server, PD and Store as applicable.

## Keep data outside the distribution

Changing providers does not convert an existing database. Use separate, initially empty Topling directories and retain the standard-provider data.
Create persistent directories writable by the service account, outside source checkouts, build outputs and unpacked distribution directories:

| Component | Configuration file and key | Example persistent path |
| --- | --- | --- |
| Server data | Graph properties: `rocksdb.data_path` | `/srv/hugegraph/topling/server/data` |
| Server WAL | Graph properties: `rocksdb.wal_path` | `/srv/hugegraph/topling/server/wal` |
| PD | `conf/application.yml`: `pd.data-path` | `/srv/hugegraph/topling/pd` |
| Store data | `conf/application.yml`: `app.data-path` | `/srv/hugegraph/topling/store/data` |
| Store Raft | `conf/application.yml`: `app.raft-path` | `/srv/hugegraph/topling/store/raft` |

For a standalone Server, edit every selected graph configuration, for example `conf/graphs/hugegraph.properties`:

```properties
backend=rocksdb
rocksdb.provider=topling
rocksdb.data_path=/srv/hugegraph/topling/server/data
rocksdb.wal_path=/srv/hugegraph/topling/server/wal
```

Set **both** Server data and WAL paths. Leaving WAL at its package-local default risks losing it when a build or package replacement removes that directory.
Keep the external data, WAL and Raft roots across runtime/package changes.

For PD and Store, edit the existing `rocksdb` mapping in the provider configuration file listed above, retaining its other options:

```yaml
rocksdb:
  provider: topling
```

Set their persistent paths separately in `conf/application.yml`; keep the normal network addresses and cluster configuration.

The published runtime directories use 0755 and regular files use 0644, so a service account different from the preparer can read the JNI. The service account also needs traversal permission on the component's parent directories; preparation does not change those parents.

## Select, start and verify

In the startup shell of each component that owns a Topling database, explicitly select the runtime:

```bash
export TOPLINGDB_ROCKSDB_PROVIDER=topling
# Run this component's start command from the first table.
```

The launcher uses that component's `conf/toplingdb.yaml`. Set `TOPLINGDB_EASY_MIGRATE_CONF=/absolute/path/config.yaml` for an explicit override.
The shipped native profile disables its HTTP server and keeps `memtable_as_log_index=false`, which the Java write path requires.
Tune that profile for the host; it is separate from the business provider and data-path configuration.

For a fresh standalone Server graph, initialize its store once before the first startup:

```bash
bash bin/init-store.sh
bash bin/start-hugegraph.sh
```

`bin/init-store.sh` and `bin/dump-store.sh` use the same explicit runtime selection as `bin/start-hugegraph.sh`.
For HStore, start PD, then Store. Before starting the HStore-backed Server from the same shell, run `unset TOPLINGDB_ROCKSDB_PROVIDER`
(or `export TOPLINGDB_ROCKSDB_PROVIDER=rocksdb`); do not enable local Topling on that Server.
A configured provider/runtime mismatch fails before the component opens its database.

Before adoption, verify the actual RocksDB Java classes and mapped JNI library belong to the prepared runtime. Use dedicated data directories to test real
writes, reads, normal stop and restart; for HStore, include a Server graph operation through PD and Store. A successful build, startup or standard-JNI unit test
alone does not establish Topling runtime acceptance.

## Stop or switch back

Stop incoming work, then use the normal stop scripts. For HStore, stop Server with `bin/stop-hugegraph.sh`, Store with `bin/stop-hugegraph-store.sh`,
and PD with `bin/stop-hugegraph-pd.sh`, waiting for each process to exit before stopping its dependency. A forced kill is not proof of normal native cleanup.

To use standard RocksDB again, stop the component, unset `TOPLINGDB_ROCKSDB_PROVIDER`, and restore its business provider to `rocksdb`.
Select the corresponding standard-provider data and WAL paths; do not point it at a database modified by Topling.

Dedicated Topling distributions, Docker/Compose packaging, general lifecycle changes and retryable snapshot recovery are separate follow-ups.
This guide covers the normal distribution launch scripts; custom IDE and embedded launchers require their own runtime setup and validation.
