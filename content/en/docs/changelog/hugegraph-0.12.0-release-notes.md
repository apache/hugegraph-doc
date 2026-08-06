---
title: "HugeGraph 0.12 Release Notes"
linkTitle: "Release-0.12.0"
draft: true
weight: 11
---

### API & Client

#### Interface Updates

- Support https + auth mode to connect to graph service (hugegraph-client #109 #110)
- Unified the parameter naming and default values of OLTP interfaces such as kout/kneighbor (hugegraph-client #122 #123)
- Support RESTful interface for attribute full-text search using P.textcontains() (hugegraph #1312)
- Added graph_read_mode API interface to switch between OLTP and OLAP read modes (hugegraph #1332)
- Support aggregate properties of list/set types (hugegraph #1332)
- Permission interface added METRICS resource type (hugegraph #1355, hugegraph-client #114)
- Permission interface added SCHEMA resource type (hugegraph #1362, hugegraph-client #117)
- Added manual compact API interface, supports rocksdb/cassandra/hbase backend (hugegraph #1378)
- Permission interface added login/logout API, supports issuing or revoking tokens (hugegraph #1500, hugegraph-client #125)
- Permission interface added project API (hugegraph #1504, hugegraph-client #127)
- Added OLAP write-back interface, supports cassandra/rocksdb backend (hugegraph #1506, hugegraph-client #129)
- Added API interface to return all Schema of a graph (hugegraph #1567, hugegraph-client #134)
- Changed the HTTP return code of property key creation and update API to 202 (hugegraph #1584)
- Enhanced Text.contains() to support 3 formats: "word", "(word)", "(word1|word2|word3)" (hugegraph #1652)
- Unified the behavior of special characters in properties (hugegraph #1670 #1684)
- Support dynamic creation of graph instances, cloning of graph instances, and deletion of graph instances (hugegraph-client #135)

#### Other modifications

- Fixed the problem of IndexLabelV56 id loss when restoring index label (hugegraph-client #118)
- Added name() method to Edge class (hugegraph-client #121)

### Core & Server

#### Functionality Updates

- Support dynamic creation of graph instances (hugegraph #1065)
- Support calling OLTP algorithms through Gremlin (hugegraph #1289)
- Support multiple clusters using the same graph permission service to share permission information (hugegraph #1350)
- Support Cache synchronization across multiple nodes (hugegraph #1357)
- Support OLTP algorithms to use native collections to reduce GC pressure and improve performance (hugegraph #1409)
- Support snapshotting and restoring snapshots for newly added Raft nodes (hugegraph #1439)
- Support secondary index for collection properties (hugegraph #1474)
- Support audit logs, compression, rate limiting, and other features (hugegraph #1492 #1493)
- Support OLTP algorithms to use high-performance parallel lock-free native collections to improve performance (hugegraph #1552)

### BUG Fixes

The following are the bug fixes made in the context of computer science:

- Fixed an NPE issue with weighted shortest path algorithm (HugeGraph #1250)
- Added security operation whitelist for Raft (HugeGraph #1257)
- Fixed the issue where RocksDB instances were not properly closed (HugeGraph #1264)
- After the truncate operation clears data, the displayed Raft snapshot will show the initiated write snapshot (HugeGraph #1275)
- Fixed the caching problem of Raft Leader when receiving forwarded requests from Follower (HugeGraph #1279)
- Fixed the instability issue with results of the weighted shortest path algorithm (HugeGraph #1280)
- Fixed the issue where the limit parameter of rays algorithm was not effective (HugeGraph #1284)
- Fixed the unchecked capacity parameter in neighborrank algorithm (HugeGraph #1290)
- Fixed the initialization failure issue of PostgreSQL due to the absence of a database with the same name as the user (HugeGraph #1293)
- Fixed the initialization failure issue of HBase backend when Kerberos is enabled (HugeGraph #1294)
- Fixed the error in determining the end of shard for HBase/RocksDB backend (HugeGraph #1306)
- Fixed the issue where the weighted shortest path algorithm did not check for the existence of the target vertex (HugeGraph #1307)
- Fixed the issue with non-String type id in personalrank/neighborrank algorithm (HugeGraph #1310)
- Checked that only the master node is allowed to schedule a gremlin job (HugeGraph #1314)
- Fixed the inaccurate results issue caused by index coverage when using `g.V().hasLabel().limit(n)` (HugeGraph #1316)
- Fixed the NaN error issue with jaccardsimilarity algorithm when the union is empty (HugeGraph #1324)
- Fixed the data synchronization problem between multiple nodes when Follower node operates Schema in Raft (HugeGraph #1325)
- Fixed the issue where TTL was not effective due to unclosed transactions (HugeGraph #1330)
- Fixed the exception handling issue when the execution result of a gremlin job is greater than the Cassandra limit but less than the task limit (HugeGraph #1334)
- Checked that the graph must exist when performing operations with auth-delete and role-get APIs (HugeGraph #1338)
- Fixed the serialization problem with asynchronous task results containing path/tree (HugeGraph #1351)
- Fixed the NPE issue when initializing admin user (HugeGraph #1360)
- Ensured the atomicity of update/get fields and re-schedule operations for asynchronous tasks (HugeGraph #1361)
- Fixed the problem with the NONE resource type (HugeGraph #1362)
- Fixed the SecurityException error and administrator information loss issue when performing truncate operation with enabled permissions (HugeGraph #1365)
- Fixed the issue where permission exceptions were ignored during data parsing with enabled permissions (HugeGraph #1380)
- Fixed the issue with AuthManager attempting to connect to other nodes during initialization (HugeGraph #1381)
- Fixed the issue with base64 decoding error caused by specific shard information (HugeGraph #1383)
- Fixed the issue where creator was empty when using consistent-hash LB for permission verification with enabled permissions (HugeGraph #1385)
- Improved the VAR resource in permissions to no longer depend on the VERTEX resource (HugeGraph #1386)
- Standardized the Schema operations to depend only on specific resources after enabling permissions (HugeGraph #1387)
- Standardized certain operations to depend on the ANY resource instead of the STATUS resource after enabling permissions (HugeGraph #1391)
- After enabling permissions, it is now prohibited to initialize the administrator password as empty (HugeGraph #1400)
- Checked that the username/password cannot be empty when creating a user (HugeGraph #1402)
- Fixed the issue where PrimaryKey or SortKey were set as nullable attributes when updating Label (HugeGraph #1406)
- Fixed the issue of missing pagination results in ScyllaDB (HugeGraph #1407)
- Fixed the issue of weight property being forcibly converted to double in the weighted shortest path algorithm (HugeGraph #1432)
- Unified the naming of the degree parameter in OLTP algorithms (HugeGraph #1433)
- Fixed the issue where fusiformsimilarity algorithm returned all vertices when similars were empty (HugeGraph #1434)
- Improved the paths algorithm to return an empty path when the starting point is the same as the target point (HugeGraph #1435)
- Changed the default value of the limit parameter for kout/kneighbor from 10 to 10000000 (HugeGraph #1436)
- Fixed the issue of '+' being URL-encoded as a space in pagination information (HugeGraph #1437)
- Improved the error message for the edge update interface (HugeGraph #1443)
- Fixed the issue where degree parameter in kout algorithm did not take effect for all labels (HugeGraph #1459)
- Improved the kneighbor/kout algorithms to disallow the starting point from appearing in the result set (HugeGraph #1459 #1463)
- Unified the behavior of Get and Post versions for kout/kneighbor (HugeGraph #1470)
- Improved the error message for mismatched vertex types when creating edges (HugeGraph #1477)
- Fixed the issue of residual indexes in Range Index (HugeGraph #1498)
- Fixed the problem of invalidating cache for permission operations (HugeGraph #1528)
- Fixed the default value of the limit parameter for sameneighbor from 10 to 10000000 (HugeGraph #1530)
- Fixed the issue where the clear API should not call create snapshot for all backends (HugeGraph #1532)
- Fixed the blocking issue when creating Index Label in loading mode (HugeGraph #1548)
- Fixed the problem of adding a graph to a project or removing a graph from a project (HugeGraph #1562)
- Improved the error message for certain permission operations (HugeGraph #1563)
- Support setting floating point attributes to Infinity/NaN values (hugegraph #1578)
- Fix quorum read issue when Raft is enabled for safe_read (hugegraph #1618)
- Fix unit issue with token expiration time configuration (hugegraph #1625)
- Fix resource leak issue with MySQL Statement (hugegraph #1627)
- Fix issue with Schema.getIndexLabel not being able to retrieve data under race conditions (hugegraph #1629)
- Fix issue with HugeVertex4Insert serialization (hugegraph #1630)
- Fix issue with MySQL count Statement not being closed (hugegraph #1640)
- Fix issue with out-of-sync status caused by deleting Index Label exception (hugegraph #1642)
- Fix issue with MySQL executing gremlin timeout causing unclosed statements (hugegraph #1643)
- Improve Search Index to support special Unicode characters: \u0000 to \u0003 (hugegraph #1659)
- Fix issue introduced by #1659 where Char was not converted to String (hugegraph #1664)
- Fix issue with abnormal results when using has() + within() queries (hugegraph #1680)
- Upgrade Log4j version to 2.17 to fix security vulnerabilities (hugegraph #1686 #1698 #1702)
- Fix NPE issue with shard scan in HBase backend when startkey contains empty string (hugegraph #1691)
- Improve performance of paths algorithm in deep loop traversal (hugegraph #1694)
- Improve default values and error checking for personalrank algorithm (hugegraph #1695)
- Fix issue with P.within condition not working for RESTful API (hugegraph #1704)
- Fix issue with dynamic graph creation when permissions are enabled (hugegraph #1708)

#### Configuration changes:

- Rename shared SSL related configuration items (hugegraph #1260).
- Support RocksDB configuration item `rocksdb.level_compaction_dynamic_level_bytes` (hugegraph #1262).
- Remove RESTful Server service protocol configuration item `restserver.protocol` and automatically extract schema from the URL (hugegraph #1272).
- Add PostgreSQL configuration item `jdbc.postgresql.connect_database` (hugegraph #1293).
- Add configuration item `vertex.encode_primary_key_number` for specifying whether vertex primary keys should be encoded (hugegraph #1323).
- Add configuration item `query.optimize_aggregate_by_index` for enabling index optimization in aggregate queries (hugegraph #1549).
- Change the default value of `cache_type` from `l1` to `l2` (hugegraph #1681).
- Add JDBC forced auto-reconnect configuration item `jdbc.forced_auto_reconnect` (hugegraph #1710).

#### Other Changes

- Added default SSL Certificate file (hugegraph #1254)
- OLTP parallel requests share thread pool instead of using separate thread pools for each request (hugegraph #1258)
- Fixed issues with Examples (hugegraph #1308)
- Upgraded to jraft version 1.3.5 (hugegraph #1313)
- Disable RocksDB WAL when Raft mode is enabled (hugegraph #1318)
- Use TarLz4Util to improve the performance of Snapshot compression (hugegraph #1336)
- Upgraded storage version as property key read frequency has been added (hugegraph #1341)
- Replaced iterator methods with queryVertex/queryEdge methods in Get API for vertex/edge (hugegraph #1345)
- Supported multi-degree queries optimized for BFS (hugegraph #1359)
- Improved query performance issue caused by RocksDB deleteRange() (hugegraph #1375)
- Fixed "cannot find symbol Namifiable" issue in travis-ci (hugegraph #1376)
- Ensured consistency between the disk of RocksDB snapshots and the data path specified (hugegraph #1392)
- Fixed inaccurate calculation of free_memory on MacOS (hugegraph #1396)
- Added Raft onBusy callback to cooperate with rate limiting (hugegraph #1401)
- Upgraded netty-all version from 4.1.13.Final to 4.1.42.Final (hugegraph #1403)
- Supported pausing TaskScheduler when set to loading mode (hugegraph #1414)
- Fixed issues with raft-tools scripts (hugegraph #1416)
- Fixed license params issues (hugegraph #1420)
- Improved the performance of write permission logs by using batch flush and async write methods (hugegraph #1448)
- Added logging of MySQL connection URL (hugegraph #1451)
- Improved user information verification performance (hugegraph #1460)
- Fixed error caused by TTL due to start time issue (hugegraph #1478)
- Supported hot reloading of log configuration and compression of audit logs (hugegraph #1492)
- Supported rate limiting for user-level audit logs (hugegraph #1493)
- RamCache now supports user-defined expiration time (hugegraph #1494)
- Cached login role in auth client to avoid duplicate RPC calls (hugegraph #1507)
- Overrode IdSet.contains() to fix issue with AbstractCollection.contains() (hugegraph #1511)
- Fixed issue where rollback was not performed when commitPartOfEdgeDeletions() fails (hugegraph #1513)
- Improved performance of Cache metrics (hugegraph #1515)
- Added exception logging when license operation error occurs (hugegraph #1522)
- Improved implementation of SimilarsMap (hugegraph #1523)
- Updated coverage using tokenless approach (hugegraph #1529)
- Refactored code for project update interface (hugegraph #1537)
- Allowed access to GRAPH_STORE from option() (hugegraph #1546)
- Optimized count queries for kout/kneighbor to avoid collection copying (hugegraph #1550)
- Optimized shortestpath traversal by prioritizing the side with less data (hugegraph #1569)
- Enhanced prompt messages for allowed keys in rocksdb.data_disks configuration (hugegraph #1585)
- Optimized id2code method performance for number IDs in OLTP traversal (hugegraph #1623)
- Improved HugeElement.getProperties() to return Collection\<Property> (hugegraph #1624)
- Added APACHE PROPOSAL file (hugegraph #1644)
- Improved close transaction flow (hugegraph #1655)
- Captured all types of exceptions when resetting and closing MySQL (hugegraph #1661)
- Improved code for OLAP property module (hugegraph #1675)
- Improved execution performance of query module (hugegraph #1711)

### Loader

- Supports importing files in Parquet format (hugegraph-loader #174)
- Supports HDFS Kerberos authentication (hugegraph-loader #176)
- Supports importing data by connecting to the server using HTTPS protocol (hugegraph-loader #183)
- Fixes trust store file path issue (hugegraph-loader #186)
- Handles exceptions caused by resetting loading mode (hugegraph-loader #187)
- Adds checking of non-empty attributes during data insertion (hugegraph-loader #190)
- Fixes time comparison issue caused by different time zones between client and server (hugegraph-loader #192)
- Improves data parsing performance (hugegraph-loader #194)
- Checks that the user-specified file header is not empty when inserting data (hugegraph-loader #195)
- Fixes format issue with MySQL struct.json in the example program (hugegraph-loader #198)
- Fixes inaccurate vertex-edge import speed issue (hugegraph-loader #200 #205)
- When check-vertex is enabled during import, ensures that vertices are imported before edges (hugegraph-loader #206)
- Fixes array overflow issue caused by inconsistent edge Json data import format (hugegraph-loader #211)
- Fixes NPE issue caused by missing edge mapping file (hugegraph-loader #213)
- Fixes issue where negative time values may be read (hugegraph-loader #215)
- Improves logging for directory files (hugegraph-loader #223)
- Improves Schema processing in the loader (hugegraph-loader #230)

### Tools

- Support HTTPS protocol (hugegraph-tools #71)
- Remove --protocol parameter and automatically extract from the URL (hugegraph-tools #72)
- Support dumping data to HDFS file system (hugegraph-tools #73)
- Fix trust store file path issue (hugegraph-tools #75)
- Support backup and restore of permission information (hugegraph-tools #76)
- Support Printer printing without parameters (hugegraph-tools #79)
- Fix macOS free_memory calculation issue (hugegraph-tools #82)
- Support specifying the number of threads during backup and restore (hugegraph-tools #83)
- Support commands for dynamically creating graphs, cloning graphs, deleting graphs, etc. (hugegraph-tools #95)

