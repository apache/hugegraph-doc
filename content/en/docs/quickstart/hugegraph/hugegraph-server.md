---
title: "HugeGraph-Server Quick Start"
linkTitle: "Install/Build HugeGraph-Server"
weight: 1
---

### 1 HugeGraph-Server Overview

`HugeGraph-Server` is the core part of the HugeGraph Project, contains submodules such as graph-core, backend, API.

The Core Module is an implementation of the Tinkerpop interface; The Backend module is used to save the graph data to the data store. For version 1.7.0+, supported backends include: RocksDB (standalone default), HStore (distributed), HBase, and Memory. The API Module provides HTTP Server, which converts Client's HTTP request into a call to Core Module.

> ⚠️ **Important Change**: Starting from version 1.7.0, legacy backends such as MySQL, PostgreSQL, Cassandra, and ScyllaDB have been removed. If you need to use these backends, please use version 1.5.x or earlier.

> There will be two spellings HugeGraph-Server and HugeGraphServer in the document, and other 
> modules are similar. There is no big difference in the meaning of these two ways, 
> which can be distinguished as follows: `HugeGraph-Server` represents the code of server-related 
> components, `HugeGraphServer` represents the service process.

### 2 Dependency for Building/Running

#### 2.1 Install Java 11 (JDK 11)

You need to use Java 11 to run `HugeGraph-Server` (compatible with Java 8 before 1.5.0, but not recommended to use), 
and configure by yourself.

**Be sure to execute the `java -version` command to check the jdk version before reading**

> Note: Using Java8 will lose some security guarantees, we recommend using Java11 in production

### 3 Deploy

There are four ways to deploy HugeGraph-Server components:

- Method 1: Use Docker container (Convenient for Test/Dev)
- Method 2: Download the binary tarball
- Method 3: Source code compilation
- Method 4: One-click deployment

**Note:** If it's exposed to the public network, **must enable** [Auth authentication](/docs/config/config-authentication/) to ensure safety (so as the legacy version).

#### 3.1 Use Docker container (Convenient for Test/Dev)

<!-- 3.1 is linked by another place. if change 3.1's title, please check -->
You can refer to the [Docker deployment guide](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/docker/README.md).

We can use `docker run -itd --name=server -p 8080:8080 -e PASSWORD=xxx hugegraph/hugegraph:1.7.0` to quickly start a `HugeGraph Server` with a built-in `RocksDB` backend.

Optional:
1. use `docker exec -it graph bash` to enter the container to do some operations.
2. use `docker run -itd --name=graph -p 8080:8080 -e PRELOAD="true" hugegraph/hugegraph:1.7.0` to start with a **built-in** example graph. We can use `RESTful API` to verify the result. The detailed step can refer to [5.1.8](#518-create-an-example-graph-when-startup)
3. use `-e PASSWORD=xxx` to enable auth mode and set the password for admin. You can find more details from [Config Authentication](/docs/config/config-authentication#use-docker-to-enable-authentication-mode)

If you use docker desktop, you can set the option like: 
<div style="text-align: center;">
    <img src="/docs/images/images-server/31docker-option.jpg" alt="image" style="width:33%;">
</div>

Also, if we want to manage the other Hugegraph related instances in one file, we can use `docker-compose` to deploy, with the command `docker-compose up -d` (you can config only `server`). Here is an example `docker-compose.yml`:

```yaml
version: '3'
services:
  server:
    image: hugegraph/hugegraph:1.7.0
    container_name: server
    environment:
     - PASSWORD=xxx
    # PASSWORD is an option to enable auth mode with the password you set.
    #  - PRELOAD=true
    # PRELOAD is a option to preload a build-in sample graph when initializing.
    ports:
      - 8080:8080
```

> Note: 
>
> 1. The docker image of the hugegraph is a convenient release to start it quickly, but not **official distribution** artifacts. You can find more details from [ASF Release Distribution Policy](https://infra.apache.org/release-distribution.html#dockerhub).
>
> 2. Recommend to use `release tag` (like `1.7.0`/`1.x.0`) for the stable version. Use `latest` tag to experience the newest functions in development.

#### 3.2 Download the binary tar tarball

You could download the binary tarball from the download page of the ASF site like this:
```bash
# use the latest version, here is 1.7.0 for example
wget https://downloads.apache.org/hugegraph/{version}/apache-hugegraph-incubating-{version}.tar.gz
tar zxf *hugegraph*.tar.gz

# (Optional) verify the integrity with SHA512 (recommended)
shasum -a 512 apache-hugegraph-incubating-{version}.tar.gz
curl https://downloads.apache.org/hugegraph/{version}/apache-hugegraph-incubating-{version}.tar.gz.sha512
```

#### 3.3 Source code compilation

Please ensure that the wget/curl commands are installed before compiling the source code

Download HugeGraph **source code** in either of the following 2 ways (so as the other HugeGraph repos/modules):
- download the stable/release version from the ASF site
- clone the unstable/latest version by GitBox(ASF) or GitHub

```bash
# Way 1. download release package from the ASF site
wget https://downloads.apache.org/hugegraph/{version}/apache-hugegraph-incubating-src-{version}.tar.gz
tar zxf *hugegraph*.tar.gz

# (Optional) verify the integrity with SHA512 (recommended)
shasum -a 512 apache-hugegraph-incubating-src-{version}.tar.gz
curl https://downloads.apache.org/hugegraph/{version}/apache-hugegraph-incubating-{version}-src.tar.gz.sha512

# Way2 : clone the latest code by git way (e.g GitHub)
git clone https://github.com/apache/hugegraph.git
```

Compile and generate tarball

```bash
cd *hugegraph
# (Optional) use "-P stage" param if you build failed with the latest code(during pre-release period)
mvn package -DskipTests -ntp
```

The execution log is as follows:

```bash
......
[INFO] Reactor Summary for hugegraph 1.5.0:
[INFO] 
[INFO] hugegraph .......................................... SUCCESS [  2.405 s]
[INFO] hugegraph-core ..................................... SUCCESS [ 13.405 s]
[INFO] hugegraph-api ...................................... SUCCESS [ 25.943 s]
[INFO] hugegraph-cassandra ................................ SUCCESS [ 54.270 s]
[INFO] hugegraph-scylladb ................................. SUCCESS [  1.032 s]
[INFO] hugegraph-rocksdb .................................. SUCCESS [ 34.752 s]
[INFO] hugegraph-mysql .................................... SUCCESS [  1.778 s]
[INFO] hugegraph-palo ..................................... SUCCESS [  1.070 s]
[INFO] hugegraph-hbase .................................... SUCCESS [ 32.124 s]
[INFO] hugegraph-postgresql ............................... SUCCESS [  1.823 s]
[INFO] hugegraph-dist ..................................... SUCCESS [ 17.426 s]
[INFO] hugegraph-example .................................. SUCCESS [  1.941 s]
[INFO] hugegraph-test ..................................... SUCCESS [01:01 min]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
......
```

After successful execution, `*hugegraph-*.tar.gz` files will be generated in the hugegraph directory, which is the tarball generated by compilation.

<details>
<summary> Outdated tools</summary>
#### 3.4 One-click deployment (Outdated)

`HugeGraph-Tools` provides a command-line tool for one-click deployment, users can use this tool to quickly download, decompress, configure and start `HugeGraphServer` and `HugeGraph-Hubble` with one click.

Of course, you should download the tarball of `HugeGraph-Toolchain` first.

```bash
# download toolchain binary package, it includes loader + tool + hubble
# please check the latest version (e.g. here is 1.7.0)
wget https://downloads.apache.org/hugegraph/1.7.0/apache-hugegraph-toolchain-incubating-1.7.0.tar.gz
tar zxf *hugegraph-*.tar.gz

# enter the tool's package
cd *hugegraph*/*tool* 
```

> note: `${version}` is the version, The latest version can refer to [Download Page](/docs/download/download), or click the link to download directly from the Download page

The general entry script for HugeGraph-Tools is `bin/hugegraph`, Users can use the `help` command to view its usage, here only the commands for one-click deployment are introduced.

```bash
bin/hugegraph deploy -v {hugegraph-version} -p {install-path} [-u {download-path-prefix}]
```

`{hugegraph-version}` indicates the version of HugeGraphServer and HugeGraphStudio to be deployed, users can view the `conf/version-mapping.yaml` file for version information, `{install-path}` specify the installation directory of HugeGraphServer and HugeGraphStudio, `{download-path-prefix}` optional, specify the download address of HugeGraphServer and HugeGraphStudio tarball, use default download URL if not provided, for example, to start HugeGraph-Server and HugeGraphStudio version 0.6, write the above command as `bin/hugegraph deploy -v 0.6 -p services`.
</details>

### 4 Config

If you need to quickly start HugeGraph just for testing, then you only need to modify a few configuration items (see next section).
For detailed configuration introduction, please refer to [configuration document](/docs/config/config-guide) and [introduction to configuration items](/docs/config/config-option)

### 5 Startup

#### 5.1 Use a startup script to startup

The startup is divided into "first startup" and "non-first startup." This distinction is because the back-end database needs to be initialized before the first startup, and then the service is started.
after the service is stopped artificially, or when the service needs to be started again for other reasons, because the backend database is persistent, you can start the service directly.

When HugeGraphServer starts, it will connect to the backend storage and try to check the version number of the backend storage. If the backend is not initialized or the backend has been initialized but the version does not match (old version data), HugeGraphServer will fail to start and give an error message.

If you need to access HugeGraphServer externally, please modify the `restserver.url` configuration item of `rest-server.properties`
（default is `http://127.0.0.1:8080`）, change to machine name or IP address.

Since the configuration (hugegraph.properties) and startup steps required by various backends are slightly different, the following will introduce the configuration and startup of each backend one by one.

**Note:** Configure [Server Authentication](/docs/config/config-authentication/) before starting HugeGraphServer if you need Auth mode (especially for production or public network environments).

##### 5.1.1 Distributed Storage (HStore)

<details>
<summary>Click to expand/collapse Distributed Storage configuration and startup method</summary>

> Distributed storage is a new feature introduced after HugeGraph 1.5.0, which implements distributed data storage and computation based on HugeGraph-PD and HugeGraph-Store components.

To use the distributed storage engine, you need to deploy HugeGraph-PD and HugeGraph-Store first. See [HugeGraph-PD Quick Start](/docs/quickstart/hugegraph/hugegraph-pd/) and [HugeGraph-Store Quick Start](/docs/quickstart/hugegraph/hugegraph-hstore/).

After ensuring that both PD and Store services are started, modify the `hugegraph.properties` configuration of HugeGraph-Server:

```properties
backend=hstore
serializer=binary
task.scheduler_type=distributed

# PD service address, multiple PD addresses are separated by commas, configure PD's RPC port
pd.peers=127.0.0.1:8686,127.0.0.1:8687,127.0.0.1:8688
```

```properties
# Simple example (with authentication)
gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy

# Specify storage backend hstore
backend=hstore
serializer=binary
store=hugegraph

# Specify the task scheduler (for versions 1.7.0 and earlier, hstore storage is required)
task.scheduler_type=distributed

# pd config
pd.peers=127.0.0.1:8686
```

Then enable PD discovery in `rest-server.properties` (required for every HugeGraph-Server node):

```properties
usePD=true

# notice: must have this conf in 1.7.0
pd.peers=127.0.0.1:8686,127.0.0.1:8687,127.0.0.1:8688
# If auth is needed
# auth.authenticator=org.apache.hugegraph.auth.StandardAuthenticator
```

If configuring multiple HugeGraph-Server nodes, you need to modify the `rest-server.properties` configuration file for each node, for example:

Node 1 (Master node):
```properties
usePD=true
restserver.url=http://127.0.0.1:8081
gremlinserver.url=http://127.0.0.1:8181
pd.peers=127.0.0.1:8686

rpc.server_host=127.0.0.1
rpc.server_port=8091

server.id=server-1
server.role=master
```

Node 2 (Worker node):
```properties
usePD=true
restserver.url=http://127.0.0.1:8082
gremlinserver.url=http://127.0.0.1:8182
pd.peers=127.0.0.1:8686

rpc.server_host=127.0.0.1
rpc.server_port=8092

server.id=server-2
server.role=worker
```

Also, you need to modify the port configuration in `gremlin-server.yaml` for each node:

Node 1:
```yaml
host: 127.0.0.1
port: 8181
```

Node 2:
```yaml
host: 127.0.0.1
port: 8182
```

Initialize the database:

```bash
cd *hugegraph-${version}
bin/init-store.sh
```

Start the Server:

```bash
bin/start-hugegraph.sh
```

The startup sequence for using the distributed storage engine is:
1. Start HugeGraph-PD
2. Start HugeGraph-Store
3. Initialize the database (only for the first time)
4. Start HugeGraph-Server

Verify that the service is started properly:

```bash
curl http://localhost:8081/graphs
# Should return: {"graphs":["hugegraph"]}
```

The sequence to stop the services should be the reverse of the startup sequence:
1. Stop HugeGraph-Server
2. Stop HugeGraph-Store
3. Stop HugeGraph-PD

```bash
bin/stop-hugegraph.sh
```
</details>

##### 5.1.2 Memory

<details>
<summary>Click to expand/collapse Memory configuration and startup methods</summary>

Update hugegraph.properties

```properties
backend=memory
serializer=text
```

> The data of the Memory backend is stored in memory and cannot be persisted. It does not need to initialize the backend. This is the only backend that does not require initialization.

Start server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

The prompted url is the same as the restserver.url configured in rest-server.properties

</details>

##### 5.1.3 RocksDB / ToplingDB

<details>
<summary>Click to expand/collapse RocksDB configuration and startup methods</summary>

> RocksDB is an embedded database that does not require manual installation and deployment. GCC version >= 4.3.0 (GLIBCXX_3.4.10) is required. If not, GCC needs to be upgraded in advance

Update hugegraph.properties

```properties
backend=rocksdb
serializer=binary
rocksdb.data_path=.
rocksdb.wal_path=.
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

**ToplingDB (Beta)**: As a high-performance alternative to RocksDB, please refer to the configuration guide: [ToplingDB Quick Start]({{< ref path="/blog/hugegraph/toplingdb/toplingdb-quick-start.md" lang="en">}})

</details>

##### 5.1.4 Cassandra

> ⚠️ **Deprecated**: This backend has been removed starting from HugeGraph 1.7.0. If you need to use it, please refer to version 1.5.x documentation.

<details>
<summary>Click to expand/collapse Cassandra configuration and startup methods</summary>

> users need to install Cassandra by themselves, requiring version 3.0 or above, [download link](http://cassandra.apache.org/download/)

Update hugegraph.properties

```properties
backend=cassandra
serializer=cassandra

# cassandra backend config
cassandra.host=localhost
cassandra.port=9042
cassandra.username=
cassandra.password=
#cassandra.connect_timeout=5
#cassandra.read_timeout=20

#cassandra.keyspace.strategy=SimpleStrategy
#cassandra.keyspace.replication=3
```

Initialize the database (required on the first startup, or a new configuration was manually added under 'conf/graphs/')


```bash
cd *hugegraph-${version}
bin/init-store.sh
Initing HugeGraph Store...
2017-12-01 11:26:51 1424  [main] [INFO ] org.apache.hugegraph.HugeGraph [] - Opening backend store: 'cassandra'
2017-12-01 11:26:52 2389  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph, try init keyspace later
2017-12-01 11:26:52 2472  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph, try init keyspace later
2017-12-01 11:26:52 2557  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph, try init keyspace later
2017-12-01 11:26:53 2797  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_graph
2017-12-01 11:26:53 2945  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_schema
2017-12-01 11:26:53 3044  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_index
2017-12-01 11:26:53 3046  [pool-3-thread-1] [INFO ] org.apache.hugegraph.backend.Transaction [] - Clear cache on event 'store.init'
2017-12-01 11:26:59 9720  [main] [INFO ] org.apache.hugegraph.HugeGraph [] - Opening backend store: 'cassandra'
2017-12-01 11:27:00 9805  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph1, try init keyspace later
2017-12-01 11:27:00 9886  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph1, try init keyspace later
2017-12-01 11:27:00 9955  [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Failed to connect keyspace: hugegraph1, try init keyspace later
2017-12-01 11:27:00 10175 [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_graph
2017-12-01 11:27:00 10321 [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_schema
2017-12-01 11:27:00 10413 [main] [INFO ] org.apache.hugegraph.backend.store.cassandra.CassandraStore [] - Store initialized: huge_index
2017-12-01 11:27:00 10413 [pool-3-thread-1] [INFO ] org.apache.hugegraph.backend.Transaction [] - Clear cache on event 'store.init'
```

Start server

```bash
bin/start-hugegraph.sh
Starting HugeGraphServer...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)....OK
```

</details>

##### 5.1.5 ScyllaDB

> ⚠️ **Deprecated**: This backend has been removed starting from HugeGraph 1.7.0. If you need to use it, please refer to version 1.5.x documentation.

<details>
<summary>Click to expand/collapse ScyllaDB configuration and startup methods</summary>

> users need to install ScyllaDB by themselves, version 2.1 or above is recommended, [download link](https://docs.scylladb.com/getting-started/)

Update hugegraph.properties

```properties
backend=scylladb
serializer=scylladb

# cassandra backend config
cassandra.host=localhost
cassandra.port=9042
cassandra.username=
cassandra.password=
#cassandra.connect_timeout=5
#cassandra.read_timeout=20

#cassandra.keyspace.strategy=SimpleStrategy
#cassandra.keyspace.replication=3
```

Since the scylladb database itself is an "optimized version" based on cassandra, if the user does not have scylladb installed, they can also use cassandra as the backend storage directly. They only need to change the backend and serializer to scylladb, and the host and post point to the seeds and port of the cassandra cluster. Yes, but it is not recommended to do so, it will not take advantage of scylladb itself.

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

</details>

##### 5.1.6 HBase

<details>
<summary>Click to expand/collapse HBase configuration and startup methods</summary>

> users need to install HBase by themselves, requiring version 2.0 or above,[download link](https://hbase.apache.org/downloads.html)

Update hugegraph.properties

```properties
backend=hbase
serializer=hbase

# hbase backend config
hbase.hosts=localhost
hbase.port=2181
# Note: recommend to modify the HBase partition number by the actual/env data amount & RS amount before init store
# it may influence the loading speed a lot
#hbase.enable_partition=true
#hbase.vertex_partitions=10
#hbase.edge_partitions=30
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

> for more other backend configurations, please refer to[introduction to configuration options](/docs/config/config-option)

</details>

##### 5.1.7 MySQL

> ⚠️ **Deprecated**: This backend has been removed starting from HugeGraph 1.7.0. If you need to use it, please refer to version 1.5.x documentation.

<details>
<summary>Click to expand/collapse MySQL configuration and startup methods</summary>

> Because MySQL is licensed under the GPL and incompatible with the Apache License, users must install MySQL themselves, [download link](https://dev.mysql.com/downloads/mysql/)

Download the MySQL [driver package](https://repo1.maven.org/maven2/mysql/mysql-connector-java/), such as `mysql-connector-java-8.0.30.jar`, and place it in the `lib` directory of HugeGraph-Server.

Update `hugegraph.properties` to configure the database URL, username, and password.
`store` is the database name; it will be created automatically if it doesn't exist.

```properties
backend=mysql
serializer=mysql

store=hugegraph

# mysql backend config
jdbc.driver=com.mysql.cj.jdbc.Driver
jdbc.url=jdbc:mysql://127.0.0.1:3306
jdbc.username=
jdbc.password=
jdbc.reconnect_max_times=3
jdbc.reconnect_interval=3
jdbc.ssl_mode=false
```

Initialize the database (required for first startup or when manually adding new configurations to `conf/graphs/`)

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

</details>

##### 5.1.8 Create an example graph when startup

Carry the `-p true` arguments when starting the script, which indicates `preload`, to create a sample graph.

```
bin/start-hugegraph.sh -p true
Starting HugeGraphServer in daemon mode...
Connecting to HugeGraphServer (http://127.0.0.1:8080/graphs)......OK
```

And use the RESTful API to request `HugeGraphServer` and get the following result:

```javascript
> curl "http://localhost:8080/graphs/hugegraph/graph/vertices" | gunzip

{"vertices":[{"id":"2:lop","label":"software","type":"vertex","properties":{"name":"lop","lang":"java","price":328}},{"id":"1:josh","label":"person","type":"vertex","properties":{"name":"josh","age":32,"city":"Beijing"}},{"id":"1:marko","label":"person","type":"vertex","properties":{"name":"marko","age":29,"city":"Beijing"}},{"id":"1:peter","label":"person","type":"vertex","properties":{"name":"peter","age":35,"city":"Shanghai"}},{"id":"1:vadas","label":"person","type":"vertex","properties":{"name":"vadas","age":27,"city":"Hongkong"}},{"id":"2:ripple","label":"software","type":"vertex","properties":{"name":"ripple","lang":"java","price":199}}]}
```

This indicates the successful creation of the sample graph.


#### 5.2 Use Docker to startup

In [3.1 Use Docker container](#31-use-docker-container-convenient-for-testdev), we have introduced how to use docker to deploy `hugegraph-server`. `server` can also preload an example graph by setting the parameter.

##### 5.2.1 Uses Cassandra as storage

> ⚠️ **Deprecated**: Cassandra backend has been removed starting from HugeGraph 1.7.0. If you need to use it, please refer to version 1.5.x documentation.

<details>
<summary> Click to expand/collapse Cassandra configuration and startup methods</summary>

When using Docker, we can use Cassandra as the backend storage. We highly recommend using docker-compose directly to manage both the server and Cassandra.

The sample `docker-compose.yml` can be obtained on [GitHub](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/docker/example/docker-compose-cassandra.yml), and you can start it with `docker-compose up -d`. (If using Cassandra 4.0 as the backend storage, it takes approximately two minutes to initialize. Please be patient.)

```yaml
version: "3"

services:
  graph:
    image: hugegraph/hugegraph
    container_name: cas-server
    ports:
      - 8080:8080
    environment:
      hugegraph.backend: cassandra
      hugegraph.serializer: cassandra
      hugegraph.cassandra.host: cas-cassandra
      hugegraph.cassandra.port: 9042
    networks:
      - ca-network
    depends_on:
      - cassandra
    healthcheck:
      test: ["CMD", "bin/gremlin-console.sh", "--" ,"-e", "scripts/remote-connect.groovy"]
      interval: 10s
      timeout: 30s
      retries: 3

  cassandra:
    image: cassandra:4
    container_name: cas-cassandra
    ports:
      - 7000:7000
      - 9042:9042
    security_opt:
      - seccomp:unconfined
    networks:
      - ca-network
    healthcheck:
      test: ["CMD", "cqlsh", "--execute", "describe keyspaces;"]
      interval: 10s
      timeout: 30s
      retries: 5

networks:
  ca-network:

volumes:
  hugegraph-data:
```

In this YAML file, configuration parameters related to Cassandra need to be passed as environment variables in the format of `hugegraph.<parameter_name>`.

Specifically, in the configuration file `hugegraph.properties` , there are settings like `backend=xxx` and `cassandra.host=xxx`. To configure these settings during the process of passing environment variables, we need to prepend `hugegraph.` to these configurations, like `hugegraph.backend` and `hugegraph.cassandra.host`.

The rest of the configurations can be referenced under [4 config](#4-config)

</details>

##### 5.2.2 Create an example graph when starting a server

Set the environment variable `PRELOAD=true` when starting Docker to load data during the execution of the startup script.

1. Use `docker run`

    Use `docker run -itd --name=server -p 8080:8080 -e PRELOAD=true hugegraph/hugegraph:1.7.0`

2. Use `docker-compose`

    Create `docker-compose.yml` as following. We should set the environment variable `PRELOAD=true`. [`example.groovy`](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/scripts/example.groovy) is a predefined script to preload the sample data. If needed, we can mount a new `example.groovy` to change the preload data.

    ```yaml
    version: '3'
      services:
        server:
          image: hugegraph/hugegraph:1.7.0
          container_name: server
          environment:
            - PRELOAD=true
            - PASSWORD=xxx
          ports:
            - 8080:8080
    ```

    Use `docker-compose up -d` to start the container

And use the RESTful API to request `HugeGraphServer` and get the following result:

```javascript
> curl "http://localhost:8080/graphs/hugegraph/graph/vertices" | gunzip

{"vertices":[{"id":"2:lop","label":"software","type":"vertex","properties":{"name":"lop","lang":"java","price":328}},{"id":"1:josh","label":"person","type":"vertex","properties":{"name":"josh","age":32,"city":"Beijing"}},{"id":"1:marko","label":"person","type":"vertex","properties":{"name":"marko","age":29,"city":"Beijing"}},{"id":"1:peter","label":"person","type":"vertex","properties":{"name":"peter","age":35,"city":"Shanghai"}},{"id":"1:vadas","label":"person","type":"vertex","properties":{"name":"vadas","age":27,"city":"Hongkong"}},{"id":"2:ripple","label":"software","type":"vertex","properties":{"name":"ripple","lang":"java","price":199}}]}
```

This indicates the successful creation of the sample graph.


### 6. Access server

#### 6.1 Service startup status check

Use `jps` to see a service process

```bash
jps
6475 HugeGraphServer
```

`curl` request `RESTfulAPI`

```bash
echo `curl -o /dev/null -s -w %{http_code} "http://localhost:8080/graphs/hugegraph/graph/vertices"`
```

Return 200, which means the server starts normally.

#### 6.2 Request Server

The RESTful API of HugeGraphServer includes various types of resources, typically including graph, schema, gremlin, traverser and task.

- `graph` contains `vertices`、`edges`
- `schema`  contains `vertexlabels`、 `propertykeys`、 `edgelabels`、`indexlabels`
- `gremlin` contains various `Gremlin` statements, such as `g.v()`, which can be executed synchronously or asynchronously
- `traverser` contains various advanced queries including shortest paths, intersections, N-step reachable neighbors, etc.
- `task` contains query and delete with asynchronous tasks

##### 6.2.1 Get vertices and its related properties in `hugegraph`

```bash
curl http://localhost:8080/graphs/hugegraph/graph/vertices 
```

_explanation_

1. Since there are many vertices and edges in the graph, for list-type requests, such as getting all vertices, getting all edges, etc., the server will compress the data and return it, so when use curl, you get a bunch of garbled characters, you can redirect to gunzip for decompression. It is recommended to use the Chrome browser + Restlet plugin to send HTTP requests for testing.

    ```
    curl "http://localhost:8080/graphs/hugegraph/graph/vertices" | gunzip
    ```

2. The current default configuration of HugeGraphServer can only be accessed locally, and the configuration can be modified so that it can be accessed on other machines.

    ```
    vim conf/rest-server.properties
    
    restserver.url=http://0.0.0.0:8080
    ```

response body:

```javasript
{
    "vertices": [
        {
            "id": "2lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "price": [
                    {
                        "id": "price",
                        "value": 328
                    }
                ],
                "name": [
                    {
                        "id": "name",
                        "value": "lop"
                    }
                ],
                "lang": [
                    {
                        "id": "lang",
                        "value": "java"
                    }
                ]
            }
        },
        {
            "id": "1josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": [
                    {
                        "id": "name",
                        "value": "josh"
                    }
                ],
                "age": [
                    {
                        "id": "age",
                        "value": 32
                    }
                ]
            }
        },
        ...
    ]
}
```

<p id="swaggerui-example"></p>

For the detailed API, please refer to [RESTful-API](/docs/clients/restful-api)

You can also visit `localhost:8080/swagger-ui/index.html` to check the API.

<div style="text-align: center;">
  <img src="/docs/images/images-server/swagger-ui.png" alt="image">
</div>

When using Swagger UI to debug the API provided by HugeGraph, if HugeGraph Server turns on authentication mode, you can enter authentication information on the Swagger page.

<div style="text-align: center;">
  <img src="/docs/images/images-server/swagger-ui-where-set-auth-example.png" alt="image">
</div>

Currently, HugeGraph supports setting authentication information in two forms: Basic and Bearer.

<div style="text-align: center;">
  <img src="/docs/images/images-server/swagger-ui-set-auth-example.png" alt="image">
</div>

### 7 Stop Server

```bash
$cd *hugegraph-${version}
$bin/stop-hugegraph.sh
```

### 8 Debug Server with IntelliJ IDEA

Please refer to [Setup Server in IDEA](/docs/contribution-guidelines/hugegraph-server-idea-setup)
