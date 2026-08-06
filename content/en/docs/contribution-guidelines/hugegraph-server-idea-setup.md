---
title: "Setup Server in IDEA (Dev)"
linkTitle: "Setup Server in IDEA"
weight: 4
---

> NOTE: The following configuration is for reference purposes only, and has been tested on Linux and macOS platforms based on [this version](https://github.com/apache/hugegraph/commit/a946ad1de4e8f922251a5241ffc957c33379677f).

### Background

The [Quick Start](/docs/quickstart/hugegraph/hugegraph-server/) section provides instructions on how to start and stop HugeGraph-Server using **scripts**. In this guide, we will explain how to run and debug HugeGraph-Server on the Linux platform using **IntelliJ IDEA**.

The core steps for local startup are the same as starting with **scripts**:

1. Initialize the database backend by executing the `InitStore` class to initialize the graph.
2. Start HugeGraph-Server by executing the `HugeGraphServer` class to load the initialized graph information and start the server.

Before proceeding with the following process, make sure that you have cloned the source code of HugeGraph
and have configured the development environment, such as `Java 11` & you could config your local environment
with this [config-doc](https://github.com/apache/hugegraph/wiki/The-style-config-for-HugeGraph-in-IDEA)

```bash
git clone https://github.com/apache/hugegraph.git
```

### Steps

#### 1. Copy Configuration Files

To avoid the impact of configuration file changes on Git tracking, it is recommended to copy the required configuration files to a separate folder. Run the following command to copy the files:

```bash
cp -r hugegraph-dist/src/assembly/static/scripts hugegraph-dist/src/assembly/static/conf path-to-your-directory
```

Replace `path-to-your-directory` with the path to the directory where you want to copy the files.

> After introducing ToplingDB, developers need to execute the `preload-topling.sh` script, which automatically extracts the required dynamic libraries and Web Server static resources into the `library` directory located alongside the `bin` directory (the static resources will also be copied to `/dev/shm/rocksdb_resource` ).

#### 2. Configure `InitStore` to initialize the graph

First, you need to configure the database backend in the configuration files. In this example, we will use RocksDB. Open `path-to-your-directory/conf/graphs/hugegraph.properties` and configure it as follows:

```properties
backend=rocksdb
serializer=binary
rocksdb.data_path=.
rocksdb.wal_path=.
```

Next, open the `Run/Debug Configurations` panel in IntelliJ IDEA and create a new Application configuration. Follow these steps for the configuration:

- Select `hugegraph-dist` as the `Use classpath of module`.
- Set the `Main class` to `org.apache.hugegraph.cmd.InitStore`.
- Set the program arguments to `conf/rest-server.properties`. Note that the path here is relative to the working directory, so make sure to set the working directory to `path-to-your-directory`.
- ToplingDB requires preloading dynamic libraries via the `LD_PRELOAD` mechanism. Developers need to set two environment variables: `LD_LIBRARY_PATH` should point to the `library` directory extracted by `preload-topling.sh`, and `LD_PRELOAD` should be set to `libjemalloc.so:librocksdbjni-linux64.so` to ensure the necessary libraries are correctly loaded at runtime.
  - LD_LIBRARY_PATH=/path/to/your/library:$LD_LIBRARY_PATH
  - LD_PRELOAD=libjemalloc.so:librocksdbjni-linux64.so

> If **user authentication** (authenticator) is configured for HugeGraph-Server in the **Java 11** environment, you need to refer to the script [configuration](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/bin/init-store.sh#L52) in the binary package and add the following **VM options**:
>
> ```bash
> --add-exports=java.base/jdk.internal.reflect=ALL-UNNAMED
> ```
>
> Otherwise, an error will occur:
>
> ```java
> java.lang.reflect.InaccessibleObjectException: Unable to make public static synchronized void jdk.internal.reflect.Reflection.registerFieldsToFilter(java.lang.Class,java.lang.String[]) accessible: module java.base does not "exports jdk.internal.reflect" to unnamed module @xxx
> ```

Once the configuration is completed, run it. If the execution is successful, the following runtime logs will be displayed:

```java
2023-06-05 00:43:37 [main] [INFO] o.a.h.u.ConfigUtil - Scanning option 'graphs' directory './conf/graphs'
2023-06-05 00:43:37 [main] [INFO] o.a.h.c.InitStore - Init graph with config file: ./conf/graphs/hugegraph.properties
......
2023-06-05 00:43:39 [main] [INFO] o.a.h.b.s.r.RocksDBStore - Write down the backend version: 1.11
2023-06-05 00:43:39 [main] [INFO] o.a.h.StandardHugeGraph - Graph 'hugegraph' has been initialized
2023-06-05 00:43:39 [main] [INFO] o.a.h.StandardHugeGraph - Close graph standardhugegraph[hugegraph]
2023-06-05 00:43:39 [db-open-1] [INFO] o.a.h.b.s.r.RocksDBStore - Opening RocksDB with data path: ./m
2023-06-05 00:43:39 [db-open-1] [INFO] o.a.h.b.s.r.RocksDBStore - Opening RocksDB with data path: ./s
2023-06-05 00:43:39 [db-open-1] [INFO] o.a.h.b.s.r.RocksDBStore - Opening RocksDB with data path: ./g
2023-06-05 00:43:39 [main] [INFO] o.a.h.HugeFactory - HugeFactory shutdown
2023-06-05 00:43:39 [hugegraph-shutdown] [INFO] o.a.h.HugeFactory - HugeGraph is shutting down
```

#### 3. Running `HugeGraphServer`

Similarly, open the `Run/Debug Configurations` panel in IntelliJ IDEA and create a new `Application` configuration. Follow these steps for the configuration:

- Select `hugegraph-dist` as the `Use classpath of module`.
- Set the `Main class` to `org.apache.hugegraph.dist.HugeGraphServer`.
- Set the program arguments to `conf/gremlin-server.yaml conf/rest-server.properties`. Similarly, note that the path here is relative to the working directory, so make sure to set the working directory to `path-to-your-directory`.

> Similarly, if **user authentication** (authenticator) is configured for HugeGraph-Server in the **Java 11** environment, you need to refer to the script [configuration](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/bin/hugegraph-server.sh#L124) in the binary package and add the following **VM options**:
>
> ```bash
> --add-exports=java.base/jdk.internal.reflect=ALL-UNNAMED --add-modules=jdk.unsupported --add-exports=java.base/sun.nio.ch=ALL-UNNAMED
> ```
> Otherwise, an error will occur:
>
> ```java
> java.lang.reflect.InaccessibleObjectException: Unable to make public static synchronized void jdk.internal.reflect.Reflection.registerFieldsToFilter(java.lang.Class,java.lang.String[]) accessible: module java.base does not "exports jdk.internal.reflect" to unnamed module @xxx
> ```

Once the configuration is completed, run it. If you see the following logs, it means that `HugeGraphServer` has been successfully started:

```java
......
2023-06-05 00:51:56 [gremlin-server-boss-1] [INFO] o.a.t.g.s.GremlinServer - Gremlin Server configured with worker thread pool of 1, gremlin pool of 8 and boss thread pool of 1.
2023-06-05 00:51:56 [gremlin-server-boss-1] [INFO] o.a.t.g.s.GremlinServer - Channel started at port 8182.
```

#### 4. Debugging `HugeGraphServer` (optional)

After completing the above configuration, you can try debugging `HugeGraphServer`. Run `HugeGraphServer` in debug mode and set a breakpoint at the following [location](https://github.com/apache/hugegraph/blob/a946ad1de4e8f922251a5241ffc957c33379677f/hugegraph-api/src/main/java/org/apache/hugegraph/api/graph/VertexAPI.java#L238):

```java
public String list(@Context GraphManager manager,
                   @PathParam("graph") String graph, @QueryParam("label") String label,
                   @QueryParam("properties") String properties, ......) {
    // ignore log
    Map<String, Object> props = parseProperties(properties);
```

Then use the RESTful API to request `HugeGraphServer`:

```bash
curl "http://localhost:8080/graphs/hugegraph/graph/vertices" | gunzip
```

At this point, you can view detailed variable information in the debugger.

#### 5. Log4j2 Configuration

By default, when running `InitStore` and `HugeGraphServer`, the Log4j2 configuration file path read is `hugegraph-dist/src/main/resources/log4j2.xml`, not `path-to-your-directory/conf/log4j2.xml`. This configuration file is read when starting HugeGraph-Server using the **script**.

To avoid maintaining two separate configuration files, you can modify the Log4j2 configuration file path when running and debugging HugeGraph-Server in **IntelliJ IDEA**:

1. Open the previously created `Application` configuration.
2. Click on `Modify options` - `Add VM options`.
3. Set the VM options to `-Dlog4j.configurationFile=conf/log4j2.xml`.

### Possible Issues

#### 1. java: package sun.misc does not exist

The reason may be that cross-compilation is triggered when using Java 11 to compile, causing the symbol of `sun.misc.Unsafe` used in the project to not be found. There are two possible solutions:

1. In IntelliJ IDEA, go to `Preferences/Settings` and find the `Java Compiler` panel. Then, disable the `--release` option (recommended).
2. Set the Project SDK to 8 (Deprecated soon).

#### 2. java: *.store.raft.rpc.RaftRequests does not exist (RPC Generated Files)

The reason is that the source code didn't include the `RPC-generated` files. You could try 2 ways to fix it:
1. [CMD]`mvn clean compile` in the **root** directory (Recommend)
2. [UI] right click on the `hugegraph` repo and select `Maven->Generate Sources and Update Folders`. This will rebuild the repo and correctly generate the required files.

#### 3. Unable to Print Location Information (%l) in Log4j2

This is because Log4j2 uses asynchronous loggers. You can refer to the [official documentation](https://logging.apache.org/log4j/2.x/manual/layouts.html#LocationInformation) for configuration details.

---

### References

1. [HugeGraph-Server Quick Start](/docs/quickstart/hugegraph/hugegraph-server): Instructions for setting up HugeGraph-Server.
2. [Local Debugging Guide for HugeGraph Server (Win/Unix)](https://gist.github.com/imbajin/1661450f000cd62a67e46d4f1abfe82c)
3. ["package sun.misc does not exist" compilation error](https://youtrack.jetbrains.com/issue/IDEA-180033)
4. [Cannot compile: java: package sun.misc does not exist](https://youtrack.jetbrains.com/issue/IDEA-201168)
5. [The code-style config for HugeGraph in IDEA](https://github.com/apache/hugegraph/wiki/The-style-config-for-HugeGraph-in-IDEA)
