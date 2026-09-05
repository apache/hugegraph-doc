---
title: "HugeGraph-Spark-Connector Quick Start"
linkTitle: "使用 Spark Connector 读写图数据"
weight: 4
---

### 1 HugeGraph-Spark-Connector 概述

HugeGraph-Spark-Connector 使用 Spark DataFrame API 将批量数据写入 HugeGraph。当前实现提供顶点和边的写入器。

目前尚未实现从 HugeGraph 读取数据：表只实现了 `SupportsWrite`，因此不支持 `spark.read.format(...)`。连接器支持 `CUSTOMIZE` 和 `PRIMARY_KEY` 两种顶点 id 策略，`AUTOMATIC` 策略会被拒绝。

### 2 环境要求

- Java 8+
- Maven 3.6+
- Spark 3.2.x（模块基于 Spark 3.2.2 编译，依赖范围为 `provided`，因此需要由 Spark 运行环境提供 Spark 的 jar）
- Scala 2.12（基于 Scala 2.12.11 编译）

### 3 编译

#### 3.1 不执行测试的编译

以下命令均在仓库根目录执行。

```bash
git clone https://github.com/apache/hugegraph-toolchain.git
cd hugegraph-toolchain
mvn clean package -pl hugegraph-spark-connector -am -DskipTests -ntp
```

#### 3.2 执行默认测试的编译

```bash
mvn clean package -pl hugegraph-spark-connector -am -ntp
```

两条命令都会在 `hugegraph-spark-connector/target/hugegraph-spark-connector-${revision}-jar-with-dependencies.jar` 生成一个包含依赖的 jar（不包含 Spark 本身）。如果不通过 Maven 管理依赖，可以把它传给 `spark-submit --jars`。

### 4 使用方法

先在 `pom.xml` 中添加依赖，并将 `${revision}` 换成实际使用的发布版本：

```xml
<dependency>
    <groupId>org.apache.hugegraph</groupId>
    <artifactId>hugegraph-spark-connector</artifactId>
    <version>${revision}</version>
</dependency>
```

`format` 必须写完整类名 `org.apache.hugegraph.spark.connector.DataSource`，连接器没有通过 Spark 的 `DataSourceRegister` 服务注册短名称。当 HugeGraphServer 开启鉴权时，需要在下面的示例中加上 `.option("username", ...)` 和 `.option("token", ...)`。

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

#### 4.4 写入 PRIMARY_KEY id 策略的顶点（Scala）

对于使用 `primaryKeys(...)` 的顶点标签，不要设置 `id` 选项：id 由主键列拼接生成。不属于 schema 的列可以通过 `ignored-fields` 丢弃。

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

#### 4.5 写入两端 id 策略不同的边（Scala）

`source-name` 和 `target-name` 各自遵循对应顶点标签的 id 策略。下面的例子中，`person` 使用自定义字符串 id（一列），`software` 使用主键（其 `name` 列）：

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
  .option("source-name", "source") // 自定义 id
  .option("target-name", "name")   // 主键
  .option("batch-size", 2)
  .mode(SaveMode.Overwrite)
  .save()
```

关于保存模式：`SaveMode.Overwrite` 和 `SaveMode.Append` 都只是插入数据，overwrite 路径不会先删除图中已有的数据。

### 5 配置参数

选项名匹配时不区分大小写并会去掉首尾空格。`data-type` 和 `label` 必填；当 `data-type` 为 `edge` 时 `source-name` 和 `target-name` 必填；其余选项都有默认值。

#### 5.1 客户端配置

客户端配置用于配置 hugegraph-client。

| 参数                   | 默认值        | 说明                                                    |
|----------------------|------------|-------------------------------------------------------|
| `host`               | `localhost` | HugeGraphServer 的地址，可以是主机名或 IP，也可以带 `http://` / `https://` 前缀 |
| `port`               | `8080`      | HugeGraphServer 的端口                                  |
| `graph`              | `hugegraph` | 图名称                                                    |
| `protocol`           | `http`      | 向服务器发送请求的协议，可选 `http` 或 `https`                       |
| `username`           | `null`      | 当 HugeGraphServer 开启权限认证时，当前图的用户名。未设置时使用图名称作为用户名        |
| `token`              | `null`      | 当 HugeGraphServer 开启权限认证时，当前图的 token                   |
| `timeout`            | `60`        | 插入结果返回的超时时间（秒）                                        |
| `max-conn`           | `CPUS * 4`  | HugeClient 与 HugeGraphServer 之间的最大 HTTP 连接数            |
| `max-conn-per-route` | `CPUS * 2`  | HugeClient 与 HugeGraphServer 之间每个路由的最大 HTTP 连接数         |
| `trust-store-file`   | `null`      | 当请求协议为 https 时，客户端的证书文件路径。https 下未设置时，连接器会读取 JVM 系统属性 `connector.home.path` 指向目录下的 `conf/hugegraph.truststore`，此时该属性必须设置 |
| `trust-store-token`  | `null`      | 当请求协议为 https 时，客户端的证书密码。https 下未设置时使用 `hugegraph`          |

#### 5.2 图数据配置

图数据配置用于说明 DataFrame 如何映射到顶点或边。

| 参数                | 默认值   | 说明                                                                                                                                                  |
|-------------------|-------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| `data-type`       |       | 必填。图数据类型，必须是 `vertex` 或 `edge`                                                                                                                     |
| `label`           |       | 必填。要导入的顶点/边数据所属的标签                                                                                                                                |
| `id`              |       | 指定某一列作为顶点的 id 列。当顶点 id 策略为 CUSTOMIZE 时，必填；当 id 策略为 PRIMARY_KEY 时，必须为空。不支持 AUTOMATIC id 策略                                                          |
| `source-name`     |       | 当 `data-type` 为 `edge` 时必填。选择输入源的某些列作为源顶点的 id 列。当源顶点的 id 策略为 CUSTOMIZE 时，必须指定某一列作为顶点的 id 列；当源顶点的 id 策略为 PRIMARY_KEY 时，必须指定一列或多列用于拼接生成顶点的 id，即无论使用哪种 id 策略，此项都是必填的。多列之间用 `,` 分隔（`delimiter` 选项对此项不生效） |
| `target-name`     |       | 当 `data-type` 为 `edge` 时必填。指定某些列作为目标顶点的 id 列，与 source-name 类似                                                                                        |
| `selected-fields` |       | 选择某些列进行插入，其他未选择的列不插入，不能与 ignored-fields 同时存在                                                                                                      |
| `ignored-fields`  |       | 忽略某些列使其不参与插入，不能与 selected-fields 同时存在                                                                                                             |
| `batch-size`      | `500` | 导入数据时每批数据的条目数。按 Spark task 生效：每个分区的写入器在缓冲区累积到该数量的顶点/边时向服务端提交一次，commit 时再提交剩余部分                                                                    |

#### 5.3 通用配置

通用配置包含一些常用的配置项。

| 参数          | 默认值 | 说明                                                                 |
|-------------|-----|-------------------------------------------------------------------|
| `delimiter` | `,` | `selected-fields` 和 `ignored-fields` 的分隔符。`source-name` 和 `target-name` 始终按 `,` 拆分 |

### 6 注意事项与限制

- 每个 Spark 写入 task 会创建自己的 HugeClient，写入前把图切换到 `LOADING` 模式，commit 或 abort 时恢复为 `NONE` 模式。
- 顶点 id 长度限制为 128 字节（UTF-8），对自定义字符串 id 和由主键拼接出的 id 都生效。
- 不支持 `AUTOMATIC` 顶点 id 策略，创建写入器时会抛出 `IllegalArgumentException`，写入失败。
- 暂不支持 `SET` 或 `LIST` 基数的属性，只会转换 `SINGLE` 基数的值。
- 日期属性：字符串值必须使用 `yyyy-MM-dd HH:mm:ss` 格式，按 `GMT+8` 时区解析；数值会被当作毫秒时间戳。
- 以字符串形式给出的布尔属性接受 `true`、`1`、`yes`、`y` 和 `false`、`0`、`no`、`n`（不区分大小写）。
- 自定义字符串 id 或任一主键值为空字符串的行会被跳过；为 null 时则会报错。

### 7 许可证

与 HugeGraph 一样，hugegraph-spark-connector 也采用 Apache 2.0 许可证。
