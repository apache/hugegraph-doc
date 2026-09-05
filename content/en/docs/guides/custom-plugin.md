---
title: "HugeGraph Plugin mechanism and plug-in extension process"
linkTitle: "HugeGraph Plugin"
weight: 3
---

### Background

1. HugeGraph is not only open source and open, but also simple and easy to use. General users can easily add plug-in extension functions without changing the source code.
2. HugeGraph supports a variety of built-in storage backends, and also allows users to extend custom backends without changing the existing source code.
3. HugeGraph supports full-text search. The full-text search function involves word segmentation in various languages. Currently, there are 7 built-in word 
breakers (ansj, hanlp, smartcn, jieba, jcseg, mmseg4j, ikanalyzer), and it also allows users to expand custom word breakers without changing the existing source code.

### Scalable dimension

Currently, the plug-in method provides extensions in the following dimensions:

- backend storage
- serializer
- Custom configuration items
- tokenizer

### Plug-in implementation mechanism

1. HugeGraph provides a plug-in interface HugeGraphPlugin, which supports plug-in through the Java SPI mechanism
2. HugeGraph provides four extension registration functions as static methods on HugeGraphPlugin: registerOptions(), registerBackend(), registerSerializer(), registerAnalyzer()
3. The plug-in implementer implements the corresponding Options, Backend, Serializer or Analyzer interface
4. The plug-in implementer implements register()the method of the HugeGraphPlugin interface, registers the specific 
implementation class listed in the above point 3 in this method, and packs it into a jar package
5. The plug-in user puts the jar package in the HugeGraph Server installation directory plugins, modifies the relevant 
configuration items to the plug-in custom value, and restarts to take effect

### Plug-in implementation process example

#### 1 Create a new maven project

##### 1.1 Name the project name: hugegraph-plugin-demo

##### 1.2 Add `hugegraph-core` Jar package dependencies

The details of maven pom.xml are as follows:

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
 
#### 2 Realize extended functions

##### 2.1 Extending a custom backend

###### 2.1.1  Implement the interface BackendStoreProvider

- Realizable interfaces: `org.apache.hugegraph.backend.store.BackendStoreProvider`
- Or inherit an abstract class:`org.apache.hugegraph.backend.store.AbstractBackendStoreProvider`
 
Take the RocksDB backend RocksDBStoreProvider as an example:

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

###### 2.1.2 Implement interface BackendStore

The BackendStore interface is defined as follows:

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
 
###### 2.1.3 Extending custom serializers

The serializer must inherit the abstract class: `org.apache.hugegraph.backend.serializer.AbstractSerializer` 
( `implements GraphSerializer, SchemaSerializer`) The main interface is defined as follows:

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

###### 2.1.4 Extend custom configuration items

When adding a custom backend, it may be necessary to add new configuration items. The implementation process mainly includes:

- Add a configuration item container class and implement the interface `org.apache.hugegraph.config.OptionHolder`
- Provide a singleton method `public static OptionHolder instance()`, and call the method when the object is initialized `OptionHolder.registerOptions()`
- Add configuration item declaration, single-value configuration item type is `ConfigOption`, multi-value configuration item type is `ConfigListOption`
 
Take the RocksDB configuration item definition as an example:

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

##### 2.2 Extend custom tokenizer

The tokenizer needs to implement the interface `org.apache.hugegraph.analyzer.Analyzer`, take implementing a SpaceAnalyzer space tokenizer as an example.

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
 
#### 3. Implement the plug-in interface and register it

The plug-in registration entry is `HugeGraphPlugin.register()`, the custom plug-in must implement this interface method, and register the extension 
items defined above inside it. The interface `org.apache.hugegraph.plugin.HugeGraphPlugin` is defined as follows:

```java
public interface HugeGraphPlugin {

    String name();

    void register();

    String supportsMinVersion();

    String supportsMaxVersion();
}
```
 
And HugeGraphPlugin provides 4 static methods for registering extensions:

- registerOptions(String name, String classPath): register configuration items
- registerBackend(String name, String classPath): register backend (BackendStoreProvider)
- registerSerializer(String name, String classPath): register serializer
- registerAnalyzer(String name, String classPath): register tokenizer
 
 
The following is an example of registering the SpaceAnalyzer tokenizer:

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

#### 4. Configure SPI entry

1. Make sure the services directory exists: hugegraph-plugin-demo/resources/META-INF/services
2. Create a text file in the services directory: org.apache.hugegraph.plugin.HugeGraphPlugin
3. The content of the file is as follows: org.apache.hugegraph.plugin.DemoPlugin

#### 5. Make Jar package

Through maven packaging, execute the command in the project directory mvn package, and a Jar package file will be generated in the 
target directory. Copy the Jar package to the `plugins` directory when using it, and restart the service to take effect.
