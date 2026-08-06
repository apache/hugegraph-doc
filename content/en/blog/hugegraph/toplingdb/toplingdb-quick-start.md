---
date: 2025-10-09
title: "ToplingDB Quick Start"
linkTitle: "ToplingDB Quick Start"
---

> [ToplingDB](https://github.com/topling/toplingdb) is a configurable and observable extension of RocksDB. It supports dynamic tuning via YAML files and enables real-time monitoring through a built-in Web Server.

Update hugegraph.properties

```properties
backend=rocksdb
serializer=binary
rocksdb.data_path=.
rocksdb.wal_path=.
# Path to YAML configuration file
#  For security reasons, HG only allows YAML files to be located under the `conf/graphs` directory
rocksdb.option_path=./conf/graphs/rocksdb_plus.yaml
# Enable Web Server
rocksdb.open_http=true
```

Initialize the database (required on the first startup, or a new configuration was manually added under 'conf/graphs/')

```bash
cd *hugegraph-${version}
bin/init-store.sh
```

Start server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

## Verify ToplingDB Is Working Properly

### Prerequisite: Ensure Core Parameters Are Correctly Configured

Check that `hugegraph.properties` includes:

```properties
# Configuration file path
rocksdb.option_path=./conf/graphs/rocksdb_plus.yaml
# Enable Web Server
rocksdb.open_http=true
```

### Method 1: Access the Web Monitoring Interface

Visualize the Web monitoring page. Example screenshot:

<div style="text-align: center;">
  <img src="/blog/images/images-server/toplingdb-web-server.png" alt="image" width="400">
</div>

Verify via terminal:

```bash
# Access http://localhost:2011 (port depends on listening_ports in YAML config)
curl http://localhost:2011 | grep topling
```

The following output indicates the page is working:

```html
<p><a href="https://topling.cn">Topling Inc.</a>This is <strong>Engine Inspector</strong>, for metrics, see <a href='javascript:grafana()'>Grafana</a>!</p>
```

### Method 2: Check ToplingDB Initialization Info in Logs

```bash
tail -f logs/hugegraph-server.log | grep -i topling
```

Similar output indicates ToplingDB is the storage engine:

```java
2025-10-14 08:56:25 [db-open-1] [INFO] o.a.h.b.s.r.RocksDBStdSessions - SidePluginRepo found. Will attempt to open multi CFs RocksDB using Topling plugin.
2025-10-14 08:56:25 [db-open-1] [INFO] o.a.h.b.s.r.RocksDBStdSessions - Topling HTTP Server has been started according to the listening_ports specified in ./conf/graphs/rocksdb_plus.yaml
```

## Common Troubleshooting

### Issue 1: Startup Failure Due to YAML Format Error

Sample log during startup:

```java
2025-10-15 01:55:50 [db-open-1] [INFO] o.a.h.b.s.r.RocksDBStdSessions - SidePluginRepo found. Will attempt to open multi CFs RocksDB using Topling plugin.
21:1: (891B):ERROR: 
sideplugin/rockside/3rdparty/rapidyaml/src/c4/yml/parse.cpp:3310: ERROR parsing yml: parse error: incorrect indentation?
```

**Solutions**:

1. Check YAML indentation (must use spaces, not tabs)
2. Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('conf/graphs/rocksdb_plus.yaml'))"`
3. Review specific error messages in logs

### Issue 2: Web Server Port Conflict

Sample log during startup:

```java
2025-10-15 01:57:34 [db-open-1] [INFO] o.a.h.b.s.r.RocksDBStdSessions - SidePluginRepo found. Will attempt to open multi CFs RocksDB using Topling plugin.
2025-10-15 01:57:34 [db-open-1] [ERROR] o.a.h.b.s.r.RocksDBStore - Failed to open RocksDB 'rocksdb-data/data/g'
org.rocksdb.RocksDBException: rocksdb::Status rocksdb::SidePluginRepo::StartHttpServer(): null context when constructing CivetServer. Possible problem binding to port.
    at org.rocksdb.SidePluginRepo.startHttpServer(Native Method) ~[rocksdbjni-8.10.2-20250804.074027-4.jar:?]
```

**Solutions**:

1. Check if the port is occupied: `lsof -i :2011`
2. Modify `listening_ports` in the YAML file
3. Restart HugeGraph Server

### Issue 3: Database Initialization Failure

Sample output indicating lock acquisition failure, possibly due to write permission issues or another process locking the DB:

```java
Caused by: org.rocksdb.RocksDBException: While lock file: rocksdb-data/data/m/LOCK: Resource temporarily unavailable
        at org.rocksdb.SidePluginRepo.nativeOpenDBMultiCF(Native Method)
        at org.rocksdb.SidePluginRepo.openDB(SidePluginRepo.java:22)
```

**Solutions**:

1. Confirm correct config path: `rocksdb.option_path=./conf/graphs/rocksdb_plus.yaml`
2. Check data directory permissions: ensure read/write access for the running user
3. Review detailed logs: `bin/init-store.sh 2>&1 | tee init.log`

## Related Documentation

- [ToplingDB YAML Configuration Explained](/blog/2025/09/30/toplingdb-yaml-configuration-file/) – Understand each parameter in the config file
- [HugeGraph Configuration Guide](/docs/config/config-option) – Reference for core HugeGraph settings
- [ToplingDB GitHub Repository](https://github.com/topling/toplingdb) – Official docs and latest updates
