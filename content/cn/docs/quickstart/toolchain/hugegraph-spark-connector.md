---
title: "HugeGraph-Spark-Connector Quick Start"
linkTitle: "使用 Spark Connector 读写图数据"
weight: 4
---

### 1 HugeGraph-Spark-Connector 概述

HugeGraph-Spark-Connector 是一个用于在 Spark 中以标准格式读写 HugeGraph 数据的连接器应用程序。

### 2 环境要求

- Java 8+
- Maven 3.6+
- Spark 3.x
- Scala 2.12

### 3 编译

#### 3.1 不执行测试的编译

```bash
mvn clean package -DskipTests
```

#### 3.2 执行默认测试的编译

```bash
mvn clean package
```

### 4 使用方法

首先在你的 pom.xml 中添加依赖：

```xml
<dependency>
    <groupId>org.apache.hugegraph</groupId>
    <artifactId>hugegraph-spark-connector</artifactId>
    <version>${revision}</version>
</dependency>
```

#### 4.1 Schema 定义示例

假设我们有一个图，其 schema 定义如下：

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

#### 4.2 写入顶点数据（Scala）

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

#### 4.3 写入边数据（Scala）

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

### 5 配置参数

#### 5.1 客户端配置

客户端配置用于配置 hugegraph-client。

| 参数                   | 默认值        | 说明                                                    |
|----------------------|------------|-------------------------------------------------------|
| `host`               | `localhost` | HugeGraphServer 的地址                                  |
| `port`               | `8080`      | HugeGraphServer 的端口                                  |
| `graph`              | `hugegraph` | 图空间名称                                                 |
| `protocol`           | `http`      | 向服务器发送请求的协议，可选 `http` 或 `https`                       |
| `username`           | `null`      | 当 HugeGraphServer 开启权限认证时，当前图的用户名                      |
| `token`              | `null`      | 当 HugeGraphServer 开启权限认证时，当前图的 token                   |
| `timeout`            | `60`        | 插入结果返回的超时时间（秒）                                        |
| `max-conn`           | `CPUS * 4`  | HugeClient 与 HugeGraphServer 之间的最大 HTTP 连接数            |
| `max-conn-per-route` | `CPUS * 2`  | HugeClient 与 HugeGraphServer 之间每个路由的最大 HTTP 连接数         |
| `trust-store-file`   | `null`      | 当请求协议为 https 时，客户端的证书文件路径                             |
| `trust-store-token`  | `null`      | 当请求协议为 https 时，客户端的证书密码                               |

#### 5.2 图数据配置

图数据配置用于设置图空间的配置。

| 参数                | 默认值   | 说明                                                                                                                                                  |
|-------------------|-------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| `data-type`       |       | 图数据类型，必须是 `vertex` 或 `edge`                                                                                                                        |
| `label`           |       | 要导入的顶点/边数据所属的标签                                                                                                                                   |
| `id`              |       | 指定某一列作为顶点的 id 列。当顶点 id 策略为 CUSTOMIZE 时，必填；当 id 策略为 PRIMARY_KEY 时，必须为空                                                                            |
| `source-name`     |       | 选择输入源的某些列作为源顶点的 id 列。当源顶点的 id 策略为 CUSTOMIZE 时，必须指定某一列作为顶点的 id 列；当源顶点的 id 策略为 PRIMARY_KEY 时，必须指定一列或多列用于拼接生成顶点的 id，即无论使用哪种 id 策略，此项都是必填的        |
| `target-name`     |       | 指定某些列作为目标顶点的 id 列，与 source-name 类似                                                                                                                 |
| `selected-fields` |       | 选择某些列进行插入，其他未选择的列不插入，不能与 ignored-fields 同时存在                                                                                                      |
| `ignored-fields`  |       | 忽略某些列使其不参与插入，不能与 selected-fields 同时存在                                                                                                             |
| `batch-size`      | `500` | 导入数据时每批数据的条目数                                                                                                                                      |

#### 5.3 通用配置

通用配置包含一些常用的配置项。

| 参数          | 默认值 | 说明                                                                 |
|-------------|-----|-------------------------------------------------------------------|
| `delimiter` | `,` | `source-name`、`target-name`、`selected-fields` 或 `ignored-fields` 的分隔符 |

### 6 许可证

与 HugeGraph 一样，hugegraph-spark-connector 也采用 Apache 2.0 许可证。
