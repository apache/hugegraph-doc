---
title: "在 IDEA 中配置 Server 开发环境"
linkTitle: "在 IDEA 中配置 Server 开发环境"
weight: 4
---

> 注意：下述配置仅供参考，基于[这个版本](https://github.com/apache/hugegraph/commit/a946ad1de4e8f922251a5241ffc957c33379677f)，在 Linux 和 macOS 平台下进行了测试。

### 背景

在 [Quick Start](/docs/quickstart/hugegraph/hugegraph-server/) 部分已经介绍了使用**脚本**启停 HugeGraph-Server 的流程。下面以 Linux 平台为例，
介绍使用 **IntelliJ IDEA** 运行与调试 HugeGraph-Server 的流程。

本地启动的核心与**脚本启动**是一样的：

1. 初始化数据库后端，执行 `InitStore` 类初始化图
2. 启动 HugeGraph-Server，执行 `HugeGraphServer` 类加载初始化的图信息启动

在执行下述流程之前，请确保已经克隆了 HugeGraph 的源代码，并且已经配置了 Java 11 环境 & 可以参考这个
[配置文档](https://github.com/apache/hugegraph/wiki/The-style-config-for-HugeGraph-in-IDEA)

```bash
git clone https://github.com/apache/hugegraph.git
```

### 步骤

#### 1. 配置文件拷贝

为了避免配置文件的更改影响 Git 的追踪，建议将所需的配置文件拷贝到一个单独的文件夹中：

```bash
cp -r hugegraph-dist/src/assembly/static/scripts hugegraph-dist/src/assembly/static/conf path-to-your-directory
```

将 `path-to-your-directory` 替换为你创建的文件夹的路径。

> 在引入 ToplingDB 后，开发者需执行 `preload-topling.sh` 脚本，该脚本会将相关动态库和 Web Server 所需的静态资源自动解压至与 `bin` 同级的 `library` 目录中 (静态资源会同时拷贝到 `/dev/shm/rocksdb_resource` 中)。

#### 2. `InitStore` 类初始化图

首先，需要在配置文件中配置数据库后端。以 RocksDB 为例，在 `path-to-your-directory/conf/graphs/hugegraph.properties` 文件中进行以下配置：

```properties
backend=rocksdb
serializer=binary
rocksdb.data_path=.
rocksdb.wal_path=.
```

然后，打开 IntelliJ IDEA 的 `Run/Debug Configurations` 面板，创建一个新的 Application 配置，按照以下步骤进行配置：

- 在 `Use classpath of module` 中选择 `hugegraph-dist`
- 将 `Main class` 设置为 `org.apache.hugegraph.cmd.InitStore`
- 设置运行参数为 `conf/rest-server.properties`，这里的路径是相对于工作路径的，需要将工作路径设置为 `path-to-your-directory`
- (可选) ToplingDB 需要通过 `LD_PRELOAD` 机制预加载动态库，开发者需设置两个环境变量：`LD_LIBRARY_PATH` 指向 `preload-topling.sh` 解压出的 `library` 目录，`LD_PRELOAD` 设置为 `libjemalloc.so:librocksdbjni-linux64.so`，以确保相关库在运行时被正确加载
  - LD_LIBRARY_PATH=/path/to/your/library:$LD_LIBRARY_PATH
  - LD_PRELOAD=libjemalloc.so:librocksdbjni-linux64.so

> 若在 **Java 11** 环境下为 HugeGraph-Server 配置了**用户认证** (authenticator)，需要参考二进制包的脚本[配置](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/bin/init-store.sh#L52)，添加下述 **VM options**:
>
> ```bash
> --add-exports=java.base/jdk.internal.reflect=ALL-UNNAMED
> ```
>
> 否则会报错：
>
> ```java
> java.lang.reflect.InaccessibleObjectException: Unable to make public static synchronized void jdk.internal.reflect.Reflection.registerFieldsToFilter(java.lang.Class,java.lang.String[]) accessible: module java.base does not "exports jdk.internal.reflect" to unnamed module @xxx
> ```

配置完成后运行，如果运行成功，将会输出以下类似运行日志：

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

#### 3. 运行 `HugeGraphServer`

类似地，打开 IntelliJ IDEA 的 `Run/Debug Configurations` 面板，创建一个新的 `Application` 配置，按照以下步骤进行配置：

- 在 `Use classpath of module` 中选择 `hugegraph-dist`
- 将 `Main class` 设置为 `org.apache.hugegraph.dist.HugeGraphServer`
- 设置运行参数为 `conf/gremlin-server.yaml conf/rest-server.properties`，同样地，这里的路径是相对于工作路径的，需要将工作路径设置为 `path-to-your-directory`

> 类似的，若在 **Java 11** 环境下为 HugeGraph-Server 配置了**用户认证** (authenticator)，同样需要参考二进制包的脚本[配置](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/bin/hugegraph-server.sh#L124)，添加下述 **VM options**:
>
> ```bash
> --add-exports=java.base/jdk.internal.reflect=ALL-UNNAMED --add-modules=jdk.unsupported --add-exports=java.base/sun.nio.ch=ALL-UNNAMED
> ```
>
> 否则会报错：
>
> ```java
> java.lang.reflect.InaccessibleObjectException: Unable to make public static synchronized void jdk.internal.reflect.Reflection.registerFieldsToFilter(java.lang.Class,java.lang.String[]) accessible: module java.base does not "exports jdk.internal.reflect" to unnamed module @xxx
> ```

配置完成后运行，如果看到以下类似日志，表示 `HugeGraphServer` 已经成功启动：

```java
......
2023-06-05 00:51:56 [gremlin-server-boss-1] [INFO] o.a.t.g.s.GremlinServer - Gremlin Server configured with worker thread pool of 1, gremlin pool of 8 and boss thread pool of 1.
2023-06-05 00:51:56 [gremlin-server-boss-1] [INFO] o.a.t.g.s.GremlinServer - Channel started at port 8182.
```

#### 4. 调试 `HugeGraphServer` (可选)

在完成上述配置后，可以尝试对 `HugeGraphServer` 进行调试。在调试模式下运行 `HugeGraphServer`，并在以下[位置](https://github.com/apache/hugegraph/blob/a946ad1de4e8f922251a5241ffc957c33379677f/hugegraph-api/src/main/java/org/apache/hugegraph/api/graph/VertexAPI.java#L238)设置断点：

```java
public String list(@Context GraphManager manager,
                   @PathParam("graph") String graph, @QueryParam("label") String label,
                   @QueryParam("properties") String properties, ......) {
    // ignore log
    Map<String, Object> props = parseProperties(properties);
```

然后，使用 RESTful API 请求 `HugeGraphServer`：

```bash
curl "http://localhost:8080/graphs/hugegraph/graph/vertices" | gunzip
```

此时，可以在调试器中查看详细的变量信息。

#### 5. Log4j2 日志配置

默认情况下，运行 `InitStore` 和 `HugeGraphServer` 时，读取的 Log4j2 配置文件路径为 `hugegraph-dist/src/main/resources/log4j2.xml`，而不是 `path-to-your-directory/conf/log4j2.xml`，这个配置文件是使用**脚本**启动 HugeGraph-Server 时读取的。

为了避免同时维护两份配置文件，可以考虑在 **IntelliJ IDEA** 运行与调试 HugeGraph-Server 时，修改读取的 Log4j2 配置文件路径：

1. 打开之前创建的 `Application` 配置
2. 点击 `Modify options` - `Add VM options`
3. 设置 VM options 为 `-Dlog4j.configurationFile=conf/log4j2.xml`

### 可能遇到的问题

#### 1. java: package sun.misc does not exist

原因可能是在使用 **Java 11** 编译时触发了交叉编译，导致项目中使用的 `sun.misc.Unsafe` 找不到符号。有两种解决方案可供选择：

1. 在 IntelliJ IDEA 的 `Preferences/Settings` 中找到 `Java Compiler` 面板，然后关闭 `--release` 选项 (推荐)
2. 或者将项目的 SDK 版本设置为 8 (Deprecated soon)

#### 2. java: *.store.raft.rpc.RaftRequests does not exist (RPC Generated Files)

原因是源代码没有包含 `RPC-generated` 文件。可以尝试两种方法来解决：
1. [命令] 在根目录下运行 `mvn clean compile -DskipTests` (**推荐**)
2. [UI] 在 IDEA 中，右键点击 `hugegraph` 模块，选择 `Manve -> Generate Sources and Update Folders`


#### 3. Log4j2 日志无法打印 %l 等位置信息

这是因为 Log4j2 中使用了 asynchronous loggers，可以参考[官方文档](https://logging.apache.org/log4j/2.x/manual/layouts.html#LocationInformation)进行配置

---

##### 参考

1. [HugeGraph-Server Quick Start](/docs/quickstart/hugegraph/hugegraph-server/)
2. [hugegraph-server 本地调试文档 (Win/Unix)](https://gist.github.com/imbajin/1661450f000cd62a67e46d4f1abfe82c)
3. ["package sun.misc does not exist" compilation error](https://youtrack.jetbrains.com/issue/IDEA-180033)
4. [Cannot compile: java: package sun.misc does not exist](https://youtrack.jetbrains.com/issue/IDEA-201168)
5. [The code-style config for HugeGraph in IDEA](https://github.com/apache/hugegraph/wiki/The-style-config-for-HugeGraph-in-IDEA)
