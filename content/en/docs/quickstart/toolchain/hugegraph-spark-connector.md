---
title: "HugeGraph-Spark-Connector Quick Start"
linkTitle: "Read/Write Graph Data with Spark Connector"
weight: 4
---

### 1 HugeGraph-Spark-Connector Overview

HugeGraph-Spark-Connector uses the Spark DataFrame API to write bulk data to HugeGraph. The current implementation provides vertex and edge writers.

Reading from HugeGraph is not implemented yet: the table only implements `SupportsWrite`, so `spark.read.format(...)` is not supported. The connector supports the `CUSTOMIZE` and `PRIMARY_KEY` vertex id strategies; the `AUTOMATIC` strategy is rejected.

### 2 Environment Requirements

- Java 8+
- Maven 3.6+
- Spark 3.2.x (the module is built against Spark 3.2.2 with `provided` scope, so your Spark runtime must supply the Spark jars)
- Scala 2.12 (built with Scala 2.12.11)

### 3 Building

#### 3.1 Build without executing tests

```bash
git clone https://github.com/apache/hugegraph-toolchain.git
cd hugegraph-toolchain
mvn clean package -pl hugegraph-spark-connector -am -DskipTests -ntp
```

#### 3.2 Build with default tests

```bash
mvn clean package -pl hugegraph-spark-connector -am -ntp
```

Both commands produce a fat jar at `hugegraph-spark-connector/target/hugegraph-spark-connector-${revision}-jar-with-dependencies.jar` (Spark itself is not bundled). Pass it to `spark-submit --jars` when you do not manage the dependency through Maven.

### 4 Usage

Add the dependency to `pom.xml`, replacing `${revision}` with the release version you use:

```xml
<dependency>
    <groupId>org.apache.hugegraph</groupId>
    <artifactId>hugegraph-spark-connector</artifactId>
    <version>${revision}</version>
</dependency>
```

The `format` string must be the full class name `org.apache.hugegraph.spark.connector.DataSource`; the connector does not register a short name with Spark's `DataSourceRegister` service loader. When HugeGraphServer has authentication enabled, add `.option("username", ...)` and `.option("token", ...)` to the examples below.

#### 4.1 Schema Definition Example

If we have a graph, the schema is defined as follows:

```groovy
schema.propertyKey("name").asText().ifNotExist().create()
schema.propertyKey("age").asInt().ifNotExist().create()
schema.propertyKey("city").asText().ifNotExist().create()
schema.propertyKey("weight").asDouble().ifNotExist().create()
schema.propertyKey("lang").asText().ifNotExist().create()
schema.propertyKey("date").asText().ifNotExist().create()
schema.propertyKey("price").asDouble().ifNotExist().create()

schema.vertexLabel("person")
        .properties("name", "age", "city")
        .useCustomizeStringId()
        .nullableKeys("age", "city")
        .ifNotExist()
        .create()

schema.vertexLabel("software")
        .properties("name", "lang", "price")
        .primaryKeys("name")
        .ifNotExist()
        .create()

schema.edgeLabel("knows")
        .sourceLabel("person")
        .targetLabel("person")
        .properties("date", "weight")
        .ifNotExist()
        .create()

schema.edgeLabel("created")
        .sourceLabel("person")
        .targetLabel("software")
        .properties("date", "weight")
        .ifNotExist()
        .create()
```

#### 4.2 Vertex Sink (Scala)

```scala
val df = sparkSession.createDataFrame(Seq(
  Tuple3("marko", 29, "Beijing"),
  Tuple3("vadas", 27, "HongKong"),
  Tuple3("Josh", 32, "Beijing"),
  Tuple3("peter", 35, "ShangHai"),
  Tuple3("li,nary", 26, "Wu,han"),
  Tuple3("Bob", 18, "HangZhou"),
)) toDF("name", "age", "city")

df.show()

df.write
  .format("org.apache.hugegraph.spark.connector.DataSource")
  .option("host", "127.0.0.1")
  .option("port", "8080")
  .option("graph", "hugegraph")
  .option("data-type", "vertex")
  .option("label", "person")
  .option("id", "name")
  .option("batch-size", 2)
  .mode(SaveMode.Overwrite)
  .save()
```

#### 4.3 Edge Sink (Scala)

```scala
val df = sparkSession.createDataFrame(Seq(
  Tuple4("marko", "vadas", "20160110", 0.5),
  Tuple4("peter", "Josh", "20230801", 1.0),
  Tuple4("peter", "li,nary", "20130220", 2.0)
)).toDF("source", "target", "date", "weight")

df.show()

df.write
  .format("org.apache.hugegraph.spark.connector.DataSource")
  .option("host", "127.0.0.1")
  .option("port", "8080")
  .option("graph", "hugegraph")
  .option("data-type", "edge")
  .option("label", "knows")
  .option("source-name", "source")
  .option("target-name", "target")
  .option("batch-size", 2)
  .mode(SaveMode.Overwrite)
  .save()
```

#### 4.4 Vertex Sink with PRIMARY_KEY id strategy (Scala)

For a vertex label that uses `primaryKeys(...)`, do not set the `id` option: the id is spliced from the primary key columns. Columns that are not part of the schema can be dropped with `ignored-fields`.

```scala
val df = sparkSession.createDataFrame(Seq(
  Tuple4("lop", "java", 328L, "ISBN978-7-107-18618-5"),
  Tuple4("ripple", "python", 199L, "ISBN978-7-100-13678-5"),
)).toDF("name", "lang", "price", "ISBN")

df.write
  .format("org.apache.hugegraph.spark.connector.DataSource")
  .option("host", "127.0.0.1")
  .option("port", "8080")
  .option("graph", "hugegraph")
  .option("data-type", "vertex")
  .option("label", "software")
  .option("ignored-fields", "ISBN")
  .option("batch-size", 2)
  .mode(SaveMode.Overwrite)
  .save()
```

#### 4.5 Edge Sink with mixed id strategies (Scala)

`source-name` and `target-name` follow the id strategy of their own vertex label. Below, `person` uses a customized string id (one column) while `software` uses a primary key (its `name` column):

```scala
val df = sparkSession.createDataFrame(Seq(
  Tuple4("marko", "lop", "20171210", 0.5),
  Tuple4("Josh", "lop", "20091111", 0.4),
  Tuple4("peter", "ripple", "20171210", 1.0),
  Tuple4("vadas", "lop", "20171210", 0.2)
)).toDF("source", "name", "date", "weight")

df.write
  .format("org.apache.hugegraph.spark.connector.DataSource")
  .option("host", "127.0.0.1")
  .option("port", "8080")
  .option("graph", "hugegraph")
  .option("data-type", "edge")
  .option("label", "created")
  .option("source-name", "source") // customize id
  .option("target-name", "name")   // primary key
  .option("batch-size", 2)
  .mode(SaveMode.Overwrite)
  .save()
```

Note on save modes: `SaveMode.Overwrite` and `SaveMode.Append` both insert the rows. The overwrite path does not delete existing data from the graph first.

### 5 Configuration Parameters

Option keys are matched case-insensitively and trimmed. `data-type` and `label` are always required; `source-name` and `target-name` are required when `data-type` is `edge`; all other options have defaults.

#### 5.1 Client Configs

Client Configs are used to configure hugegraph-client.

| Parameter            | Default Value | Description                                                                                  |
|----------------------|---------------|----------------------------------------------------------------------------------------------|
| `host`               | `localhost`   | Address of HugeGraphServer. A bare host name or IP, or a full `http://` / `https://` prefix   |
| `port`               | `8080`        | Port of HugeGraphServer                                                                      |
| `graph`              | `hugegraph`   | Graph name                                                                                   |
| `protocol`           | `http`        | Protocol for sending requests to the server, optional `http` or `https`                      |
| `username`           | `null`        | Username of the current graph when HugeGraphServer enables permission authentication. When unset, the graph name is used as the username |
| `token`              | `null`        | Token of the current graph when HugeGraphServer has enabled authorization authentication     |
| `timeout`            | `60`          | Timeout (seconds) for inserting results to return                                            |
| `max-conn`           | `CPUS * 4`    | The maximum number of HTTP connections between HugeClient and HugeGraphServer                |
| `max-conn-per-route` | `CPUS * 2`    | The maximum number of HTTP connections for each route between HugeClient and HugeGraphServer |
| `trust-store-file`   | `null`        | The client's certificate file path when the request protocol is https. When unset under https, the connector reads `conf/hugegraph.truststore` under the directory given by the JVM system property `connector.home.path`, which must then be set |
| `trust-store-token`  | `null`        | The client's certificate password when the request protocol is https. When unset under https, `hugegraph` is used                         |

#### 5.2 Graph Data Configs

Graph Data Configs describe how DataFrame columns map to vertices or edges.

| Parameter         | Default Value | Description                                                                                                                                                                                                                                                                                                                                                                                                                |
|-------------------|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `data-type`       |               | Required. Graph data type, must be `vertex` or `edge`                                                                                                                                                                                                                                                                                                                                                                      |
| `label`           |               | Required. Label to which the vertex/edge data to be imported belongs                                                                                                                                                                                                                                                                                                                                                       |
| `id`              |               | Specify a column as the id column of the vertex. When the vertex id policy is CUSTOMIZE, it is required; when the id policy is PRIMARY_KEY, it must be empty. The AUTOMATIC id policy is not supported                                                                                                                                                                                                                       |
| `source-name`     |               | Required when `data-type` is `edge`. Select certain columns of the input source as the id column of source vertex. When the id policy of the source vertex is CUSTOMIZE, a certain column must be specified as the id column of the vertex; when the id policy of the source vertex is PRIMARY_KEY, one or more columns must be specified for splicing the id of the generated vertex, that is, no matter which id strategy is used, this item is required. Multiple columns are separated by `,` (the `delimiter` option does not apply here) |
| `target-name`     |               | Required when `data-type` is `edge`. Specify certain columns as the id columns of target vertex, similar to source-name                                                                                                                                                                                                                                                                                                    |
| `selected-fields` |               | Select some columns to insert, other unselected ones are not inserted, cannot exist at the same time as ignored-fields                                                                                                                                                                                                                                                                                                     |
| `ignored-fields`  |               | Ignore some columns so that they do not participate in insertion, cannot exist at the same time as selected-fields                                                                                                                                                                                                                                                                                                         |
| `batch-size`      | `500`         | The number of data items in each batch when importing data. Applied per Spark task: each partition writer flushes its buffer to the server once it holds this many vertices/edges, and again at commit for the remainder                                                                                                                                                                                                   |

#### 5.3 Common Configs

Common Configs contains some common configurations.

| Parameter   | Default Value | Description                                                                     |
|-------------|---------------|---------------------------------------------------------------------------------|
| `delimiter` | `,`           | Separator of `selected-fields` and `ignored-fields`. `source-name` and `target-name` are always split on `,` |

### 6 Notes and Limitations

- Each Spark write task opens its own HugeClient, switches the graph to `LOADING` mode before writing and sets it back to `NONE` at commit or abort.
- Vertex ids are limited to 128 bytes (UTF-8). This applies to customized string ids and to ids spliced from primary keys.
- The `AUTOMATIC` vertex id strategy is not supported; the write fails with an `IllegalArgumentException` when the writer is created.
- Properties with `SET` or `LIST` cardinality are not supported yet; only `SINGLE` cardinality values are converted.
- Date properties: string values must use the format `yyyy-MM-dd HH:mm:ss` and are parsed in the `GMT+8` time zone; numeric values are treated as epoch milliseconds.
- Boolean properties given as strings accept `true`, `1`, `yes`, `y` and `false`, `0`, `no`, `n` (case-insensitive).
- Rows whose customized string id, or any primary key value, is an empty string are skipped. A null id or primary key value raises an error instead.

### 7 License

The same as HugeGraph, hugegraph-spark-connector is also licensed under Apache 2.0 License.
