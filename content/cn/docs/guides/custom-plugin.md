---
title: "HugeGraph Plugin 机制及插件扩展流程"
linkTitle: "HugeGraph Plugin"
weight: 3
---

### 背景

1. HugeGraph 不仅开源开放，而且要做到简单易用，一般用户无需更改源码也能轻松增加插件扩展功能。
2. HugeGraph 支持多种内置存储后端，也允许用户无需更改现有源码的情况下扩展自定义后端。
3. HugeGraph 支持全文检索，全文检索功能涉及到各语言分词，目前已内置 7 种分词器（ansj、hanlp、smartcn、jieba、jcseg、mmseg4j、ikanalyzer），也允许用户无需更改现有源码的情况下扩展自定义分词器。

### 可扩展维度

目前插件方式提供如下几个维度的扩展项：

- 后端存储
- 序列化器
- 自定义配置项
- 分词器

### 插件实现机制

1. HugeGraph 提供插件接口 HugeGraphPlugin，通过 Java SPI 机制支持插件化
2. HugeGraph 在 HugeGraphPlugin 接口上以静态方法提供了 4 个扩展项注册函数：`registerOptions()`、`registerBackend()`、`registerSerializer()`、`registerAnalyzer()`
3. 插件实现者实现相应的 Options、Backend、Serializer 或 Analyzer 的接口
4. 插件实现者实现 HugeGraphPlugin 接口的`register()`方法，在该方法中注册上述第 3 点所列的具体实现类，并打成 jar 包
5. 插件使用者将 jar 包放在 HugeGraph Server 安装目录的`plugins`目录下，修改相关配置项为插件自定义值，重启即可生效

### 插件实现流程实例

#### 1 新建一个 maven 项目

##### 1.1 项目名称取名：hugegraph-plugin-demo

##### 1.2 添加`hugegraph-core` Jar 包依赖

maven pom.xml 详细内容如下：

```xml
<?xml version="1.0" encoding="UTF-8"?>

<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modelVersion>4.0.0</modelVersion>
    <groupId>org.apache.hugegraph</groupId>
    <artifactId>hugegraph-plugin-demo</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <name>hugegraph-plugin-demo</name>

    <dependencies>
        <dependency>
            <groupId>org.apache.hugegraph</groupId>
            <artifactId>hugegraph-core</artifactId>
            <version>${project.version}</version>
        </dependency>
    </dependencies>
</project>

```
 
#### 2 实现扩展功能

##### 2.1 扩展自定义后端

###### 2.1.1 实现接口 BackendStoreProvider

- 可实现接口：`org.apache.hugegraph.backend.store.BackendStoreProvider`
- 或者继承抽象类：`org.apache.hugegraph.backend.store.AbstractBackendStoreProvider`
 
以 RocksDB 后端 RocksDBStoreProvider 为例：

```java
public class RocksDBStoreProvider extends AbstractBackendStoreProvider {

    protected String database() {
        return this.graph().toLowerCase();
    }

    @Override
    protected BackendStore newSchemaStore(HugeConfig config, String store) {
        return new RocksDBStore.RocksDBSchemaStore(this, this.database(), store);
    }

    @Override
    protected BackendStore newGraphStore(HugeConfig config, String store) {
        return new RocksDBStore.RocksDBGraphStore(this, this.database(), store);
    }

    @Override
    protected BackendStore newSystemStore(HugeConfig config, String store) {
        return new RocksDBStore.RocksDBSystemStore(this, this.database(), store);
    }

    @Override
    public String type() {
        return "rocksdb";
    }

    @Override
    public String driverVersion() {
        return "1.11";
    }
}
```

###### 2.1.2 实现接口 BackendStore

BackendStore 接口定义如下：

```java
public interface BackendStore {
    // Store name
    String store();

    // Stored version
    String storedVersion();

    // Database name
    String database();

    // Get the parent provider
    BackendStoreProvider provider();

    // Get the system schema store
    SystemSchemaStore systemSchemaStore();

    // Whether it is the storage of schema
    boolean isSchemaStore();

    // Open/close database
    void open(HugeConfig config);
    void close();
    boolean opened();

    // Initialize/clear database
    void init();
    void clear(boolean clearSpace);
    boolean initialized();

    // Delete all data of database (keep table structure)
    void truncate();

    // Add/delete data
    void mutate(BackendMutation mutation);

    // Query data
    Iterator<BackendEntry> query(Query query);
    Number queryNumber(Query query);

    // Transaction
    void beginTx();
    void commitTx();
    void rollbackTx();

    // Get metadata by key
    <R> R metadata(HugeType type, String meta, Object[] args);

    // Backend features
    BackendFeatures features();

    // Increase next id for specific type
    void increaseCounter(HugeType type, long increment);

    // Get current counter for a specific type
    long getCounter(HugeType type);
}
```
 
###### 2.1.3 扩展自定义序列化器

序列化器必须继承抽象类：`org.apache.hugegraph.backend.serializer.AbstractSerializer`(`implements GraphSerializer, SchemaSerializer`)
主要接口的定义如下：

```java
public interface GraphSerializer {
    BackendEntry writeVertex(HugeVertex vertex);
    BackendEntry writeOlapVertex(HugeVertex vertex);
    BackendEntry writeVertexProperty(HugeVertexProperty<?> prop);
    HugeVertex readVertex(HugeGraph graph, BackendEntry entry);
    BackendEntry writeEdge(HugeEdge edge);
    BackendEntry writeEdgeProperty(HugeEdgeProperty<?> prop);
    HugeEdge readEdge(HugeGraph graph, BackendEntry entry);
    CIter<Edge> readEdges(HugeGraph graph, BackendEntry bytesEntry);
    BackendEntry writeIndex(HugeIndex index);
    HugeIndex readIndex(HugeGraph graph, ConditionQuery query, BackendEntry entry);
    BackendEntry writeId(HugeType type, Id id);
    Query writeQuery(Query query);
}

public interface SchemaSerializer {
    BackendEntry writeVertexLabel(VertexLabel vertexLabel);
    VertexLabel readVertexLabel(HugeGraph graph, BackendEntry entry);
    BackendEntry writeEdgeLabel(EdgeLabel edgeLabel);
    EdgeLabel readEdgeLabel(HugeGraph graph, BackendEntry entry);
    BackendEntry writePropertyKey(PropertyKey propertyKey);
    PropertyKey readPropertyKey(HugeGraph graph, BackendEntry entry);
    BackendEntry writeIndexLabel(IndexLabel indexLabel);
    IndexLabel readIndexLabel(HugeGraph graph, BackendEntry entry);
}
```

###### 2.1.4 扩展自定义配置项

增加自定义后端时，可能需要增加新的配置项，实现流程主要包括：

- 增加配置项容器类，并实现接口`org.apache.hugegraph.config.OptionHolder`
- 提供单例方法`public static OptionHolder instance()`，并在对象初始化时调用方法`OptionHolder.registerOptions()`
- 增加配置项声明，单值配置项类型为`ConfigOption`、多值配置项类型为`ConfigListOption`
 
以 RocksDB 配置项定义为例：

```java
public class RocksDBOptions extends OptionHolder {

    private RocksDBOptions() {
        super();
    }

    private static volatile RocksDBOptions instance;

    public static synchronized RocksDBOptions instance() {
        if (instance == null) {
            instance = new RocksDBOptions();
            instance.registerOptions();
        }
        return instance;
    }

    public static final ConfigOption<String> DATA_PATH =
            new ConfigOption<>(
                    "rocksdb.data_path",
                    "The path for storing data of RocksDB.",
                    disallowEmpty(),
                    "rocksdb-data/data"
            );

    public static final ConfigOption<String> WAL_PATH =
            new ConfigOption<>(
                    "rocksdb.wal_path",
                    "The path for storing WAL of RocksDB.",
                    disallowEmpty(),
                    "rocksdb-data/wal"
            );

    public static final ConfigListOption<String> DATA_DISKS =
            new ConfigListOption<>(
                    "rocksdb.data_disks",
                    false,
                    "The optimized disks for storing data of RocksDB. " +
                    "The format of each element: `STORE/TABLE: /path/disk`." +
                    "Allowed keys are [g/vertex, g/edge_out, g/edge_in, " +
                    "g/vertex_label_index, g/edge_label_index, " +
                    "g/range_int_index, g/range_float_index, " +
                    "g/range_long_index, g/range_double_index, " +
                    "g/secondary_index, g/search_index, g/shard_index, " +
                    "g/unique_index, g/olap]",
                    null,
                    String.class,
                    ImmutableList.of()
            );
}
```

##### 2.2 扩展自定义分词器

分词器需要实现接口`org.apache.hugegraph.analyzer.Analyzer`，以实现一个 SpaceAnalyzer 空格分词器为例。

```java
package org.apache.hugegraph.plugin;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import org.apache.hugegraph.analyzer.Analyzer;

public class SpaceAnalyzer implements Analyzer {

    @Override
    public Set<String> segment(String text) {
        return new HashSet<>(Arrays.asList(text.split(" ")));
    }
}
```
 
#### 3. 实现插件接口，并进行注册

插件注册入口为`HugeGraphPlugin.register()`，自定义插件必须实现该接口方法，在其内部注册上述定义好的扩展项。
接口`org.apache.hugegraph.plugin.HugeGraphPlugin`定义如下：

```java
public interface HugeGraphPlugin {

    String name();

    void register();

    String supportsMinVersion();

    String supportsMaxVersion();
}
```
 
并且 HugeGraphPlugin 提供了 4 个静态方法用于注册扩展项：

- registerOptions(String name, String classPath)：注册配置项
- registerBackend(String name, String classPath)：注册后端（BackendStoreProvider）
- registerSerializer(String name, String classPath)：注册序列化器
- registerAnalyzer(String name, String classPath)：注册分词器
 
 
下面以注册 SpaceAnalyzer 分词器为例：

```java
package org.apache.hugegraph.plugin;

public class DemoPlugin implements HugeGraphPlugin {

    @Override
    public String name() {
        return "demo";
    }

    @Override
    public void register() {
        HugeGraphPlugin.registerAnalyzer("demo", SpaceAnalyzer.class.getName());
    }

    @Override
    public String supportsMinVersion() {
        return "1.7.0";
    }

    @Override
    public String supportsMaxVersion() {
        return "1.8.0";
    }
}
```

#### 4. 配置 SPI 入口

1. 确保 services 目录存在：hugegraph-plugin-demo/resources/META-INF/services
2. 在 services 目录下建立文本文件：org.apache.hugegraph.plugin.HugeGraphPlugin
3. 文件内容如下：org.apache.hugegraph.plugin.DemoPlugin
 
#### 5. 打 Jar 包

通过 maven 打包，在项目目录下执行命令`mvn package`，在 target 目录下会生成 Jar 包文件。
使用时将该 Jar 包拷到`plugins`目录，重启服务即可生效。
