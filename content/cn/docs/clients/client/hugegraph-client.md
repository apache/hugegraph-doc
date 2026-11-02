---
title: "HugeGraph Java Client"
linkTitle: "Java 客户端"
weight: 1
aliases:
  - /docs/quickstart/client/hugegraph-client/
  - /docs/clients/hugegraph-client/
---

### 1 HugeGraph-Client 概述 {#1-hugegraph-client}

[HugeGraph Java Client](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-client) 将 Java API 转换为 HugeGraph Server 的 REST 请求，支持管理 Schema 和图数据、执行 Gremlin 及调用 Traverser API。本文涵盖 Java 项目的快速接入示例与全量核心 API 参考。

其他语言可使用 [Go Client](/cn/docs/clients/client/hugegraph-client-go/) 或 [Python Client](/cn/docs/clients/client/hugegraph-client-python/)。

### 2 环境要求

- JDK 17，用于本文示例及从 Toolchain `master` 构建 Client `1.8.0`
- Maven 3.6.3+

### 3 使用流程

按下面的顺序接入 HugeGraph-Client。

1. 使用 IntelliJ IDEA 或 Eclipse 新建 Maven 工程。
1. 在 `pom.xml` 中添加 HugeGraph-Client 依赖。
1. 创建客户端、调用 API，并在使用后关闭客户端。
{.steps}

详细操作见下面的完整示例。

### 4 完整示例 {#5-简单示例}

#### 4.1 新建 Maven 工程

使用 Eclipse 或 IntelliJ IDEA 创建 Maven 工程。

- [Eclipse 新建 Maven 工程](http://www.vogella.com/tutorials/EclipseMaven/article.html)
- [Intellij Idea 创建 maven 工程](https://vaadin.com/docs/-/part/framework/getting-started/getting-started-idea.html)

#### 4.2 添加 hugegraph-client 依赖

在 `pom.xml` 中添加依赖。

```xml

<dependencies>
    <dependency>
        <groupId>org.apache.hugegraph</groupId>
        <artifactId>hugegraph-client</artifactId>
        <!-- 以下完整示例可使用已发布的 1.7.0 -->
        <version>1.7.0</version>
    </dependency>
</dependencies>
```

先根据用途选择客户端版本。

| 用途 | 客户端版本 | Java 编译目标 |
| --- | --- | --- |
| 运行下方完整示例 | 已发布的 `1.7.0`，使用上面的依赖即可 | 发布版 POM 为 Java 8；本文统一使用 JDK 17 |
| 使用能力探测等 master 新接口 | Toolchain `master`（以 1.8 为基线） | Java 17 |

示例使用的 Schema、Graph、Gremlin 和资源关闭接口在 Client `1.7.0` 中可用，也与 Toolchain `master` 兼容。
发布版的 Java 编译目标不代表所有传递依赖的运行环境要求。

若需要使用 master 分支未发布的新接口，可从源码编译安装 Client（需配合 Toolchain 源码，详见 [Tools 源码构建指引](/cn/docs/quickstart/toolchain/hugegraph-tools/#build-current-source)）：

```bash
java -version
mvn -version
mvn -Dmaven.repo.local="${candidate_dir:?Run the candidate SDK setup first}/m2" \
  -Dsdk.validation.mode=candidate \
  install -pl hugegraph-client -am -DskipTests -Dmaven.javadoc.skip=true -ntp
```

两条版本检查都应显示 JDK 17。使用 master 分支 Client 的项目运行 Maven 命令时，也需添加 `-Dmaven.repo.local="$candidate_dir/m2"`。
Client 与 Server 的版本不必相同；升级前核对所需 API 及兼容范围。

#### 4.3 Example

选择单条操作或批量操作示例，将完整代码保存为 Maven 工程中的 `src/main/java/SingleExample.java` 或
`src/main/java/BatchExample.java`。复制按钮会包含已折叠的代码行。

{{< tabs group="java-client-example" default="single" label="Java 客户端示例" >}}
{{< tab label="SingleExample" value="single" >}}

##### 4.3.1 SingleExample

```java {collapse=30}
import java.io.IOException;
import java.util.Iterator;
import java.util.List;

import org.apache.hugegraph.driver.GraphManager;
import org.apache.hugegraph.driver.GremlinManager;
import org.apache.hugegraph.driver.HugeClient;
import org.apache.hugegraph.driver.SchemaManager;
import org.apache.hugegraph.structure.constant.T;
import org.apache.hugegraph.structure.graph.Edge;
import org.apache.hugegraph.structure.graph.Path;
import org.apache.hugegraph.structure.graph.Vertex;
import org.apache.hugegraph.structure.gremlin.Result;
import org.apache.hugegraph.structure.gremlin.ResultSet;

public class SingleExample {

    public static void main(String[] args) throws IOException {
        // If connect failed will throw a exception.
        HugeClient hugeClient = HugeClient.builder("http://localhost:8080",
                                                   "DEFAULT",
                                                   "hugegraph")
                                          .configUser("username", "password")
                                          // 这是示例,生产环境需要使用安全的凭证
                                          .build();

        SchemaManager schema = hugeClient.schema();

        schema.propertyKey("name").asText().ifNotExist().create();
        schema.propertyKey("age").asInt().ifNotExist().create();
        schema.propertyKey("city").asText().ifNotExist().create();
        schema.propertyKey("weight").asDouble().ifNotExist().create();
        schema.propertyKey("lang").asText().ifNotExist().create();
        schema.propertyKey("date").asDate().ifNotExist().create();
        schema.propertyKey("price").asInt().ifNotExist().create();

        schema.vertexLabel("person")
              .properties("name", "age", "city")
              .primaryKeys("name")
              .ifNotExist()
              .create();

        schema.vertexLabel("software")
              .properties("name", "lang", "price")
              .primaryKeys("name")
              .ifNotExist()
              .create();

        schema.indexLabel("personByCity")
              .onV("person")
              .by("city")
              .secondary()
              .ifNotExist()
              .create();

        schema.indexLabel("personByAgeAndCity")
              .onV("person")
              .by("age", "city")
              .secondary()
              .ifNotExist()
              .create();

        schema.indexLabel("softwareByPrice")
              .onV("software")
              .by("price")
              .range()
              .ifNotExist()
              .create();

        schema.edgeLabel("knows")
              .sourceLabel("person")
              .targetLabel("person")
              .properties("date", "weight")
              .ifNotExist()
              .create();

        schema.edgeLabel("created")
              .sourceLabel("person").targetLabel("software")
              .properties("date", "weight")
              .ifNotExist()
              .create();

        schema.indexLabel("createdByDate")
              .onE("created")
              .by("date")
              .secondary()
              .ifNotExist()
              .create();

        schema.indexLabel("createdByWeight")
              .onE("created")
              .by("weight")
              .range()
              .ifNotExist()
              .create();

        schema.indexLabel("knowsByWeight")
              .onE("knows")
              .by("weight")
              .range()
              .ifNotExist()
              .create();

        GraphManager graph = hugeClient.graph();
        Vertex marko = graph.addVertex(T.LABEL, "person", "name", "marko",
                                       "age", 29, "city", "Beijing");
        Vertex vadas = graph.addVertex(T.LABEL, "person", "name", "vadas",
                                       "age", 27, "city", "Hongkong");
        Vertex lop = graph.addVertex(T.LABEL, "software", "name", "lop",
                                     "lang", "java", "price", 328);
        Vertex josh = graph.addVertex(T.LABEL, "person", "name", "josh",
                                      "age", 32, "city", "Beijing");
        Vertex ripple = graph.addVertex(T.LABEL, "software", "name", "ripple",
                                        "lang", "java", "price", 199);
        Vertex peter = graph.addVertex(T.LABEL, "person", "name", "peter",
                                       "age", 35, "city", "Shanghai");

        marko.addEdge("knows", vadas, "date", "2016-01-10", "weight", 0.5);
        marko.addEdge("knows", josh, "date", "2013-02-20", "weight", 1.0);
        marko.addEdge("created", lop, "date", "2017-12-10", "weight", 0.4);
        josh.addEdge("created", lop, "date", "2009-11-11", "weight", 0.4);
        josh.addEdge("created", ripple, "date", "2017-12-10", "weight", 1.0);
        peter.addEdge("created", lop, "date", "2017-03-24", "weight", 0.2);

        GremlinManager gremlin = hugeClient.gremlin();
        System.out.println("==== Path ====");
        ResultSet resultSet = gremlin.gremlin("g.V().outE().path()").execute();
        Iterator<Result> results = resultSet.iterator();
        results.forEachRemaining(result -> {
            System.out.println(result.getObject().getClass());
            Object object = result.getObject();
            if (object instanceof Vertex) {
                System.out.println(((Vertex) object).id());
            } else if (object instanceof Edge) {
                System.out.println(((Edge) object).id());
            } else if (object instanceof Path) {
                List<Object> elements = ((Path) object).objects();
                elements.forEach(element -> {
                    System.out.println(element.getClass());
                    System.out.println(element);
                });
            } else {
                System.out.println(object);
            }
        });

        hugeClient.close();
    }
}
```

{{< /tab >}}
{{< tab label="BatchExample" value="batch" >}}

##### 4.3.2 BatchExample

```java {collapse=30}
import java.util.ArrayList;
import java.util.List;

import org.apache.hugegraph.driver.GraphManager;
import org.apache.hugegraph.driver.HugeClient;
import org.apache.hugegraph.driver.SchemaManager;
import org.apache.hugegraph.structure.graph.Edge;
import org.apache.hugegraph.structure.graph.Vertex;

public class BatchExample {

    public static void main(String[] args) {
        // If connect failed will throw a exception.
        HugeClient hugeClient = HugeClient.builder("http://localhost:8080",
                                                "DEFAULT",
                                                "hugegraph")
                                          .configUser("username", "password")
                                          // 这是示例,生产环境需要使用安全的凭证
                                          .build();

        SchemaManager schema = hugeClient.schema();

        schema.propertyKey("name").asText().ifNotExist().create();
        schema.propertyKey("age").asInt().ifNotExist().create();
        schema.propertyKey("lang").asText().ifNotExist().create();
        schema.propertyKey("date").asDate().ifNotExist().create();
        schema.propertyKey("price").asInt().ifNotExist().create();

        schema.vertexLabel("person")
              .properties("name", "age")
              .primaryKeys("name")
              .ifNotExist()
              .create();

        schema.vertexLabel("person")
              .properties("price")
              .nullableKeys("price")
              .append();

        schema.vertexLabel("software")
              .properties("name", "lang", "price")
              .primaryKeys("name")
              .ifNotExist()
              .create();

        schema.indexLabel("softwareByPrice")
              .onV("software").by("price")
              .range()
              .ifNotExist()
              .create();

        schema.edgeLabel("knows")
              .link("person", "person")
              .properties("date")
              .ifNotExist()
              .create();

        schema.edgeLabel("created")
              .link("person", "software")
              .properties("date")
              .ifNotExist()
              .create();

        schema.indexLabel("createdByDate")
              .onE("created").by("date")
              .secondary()
              .ifNotExist()
              .create();

        // get schema object by name
        System.out.println(schema.getPropertyKey("name"));
        System.out.println(schema.getVertexLabel("person"));
        System.out.println(schema.getEdgeLabel("knows"));
        System.out.println(schema.getIndexLabel("createdByDate"));

        // list all schema objects
        System.out.println(schema.getPropertyKeys());
        System.out.println(schema.getVertexLabels());
        System.out.println(schema.getEdgeLabels());
        System.out.println(schema.getIndexLabels());

        GraphManager graph = hugeClient.graph();

        Vertex marko = new Vertex("person").property("name", "marko")
                                           .property("age", 29);
        Vertex vadas = new Vertex("person").property("name", "vadas")
                                           .property("age", 27);
        Vertex lop = new Vertex("software").property("name", "lop")
                                           .property("lang", "java")
                                           .property("price", 328);
        Vertex josh = new Vertex("person").property("name", "josh")
                                          .property("age", 32);
        Vertex ripple = new Vertex("software").property("name", "ripple")
                                              .property("lang", "java")
                                              .property("price", 199);
        Vertex peter = new Vertex("person").property("name", "peter")
                                           .property("age", 35);

        Edge markoKnowsVadas = new Edge("knows").source(marko).target(vadas)
                                                .property("date", "2016-01-10");
        Edge markoKnowsJosh = new Edge("knows").source(marko).target(josh)
                                               .property("date", "2013-02-20");
        Edge markoCreateLop = new Edge("created").source(marko).target(lop)
                                                 .property("date",
                                                           "2017-12-10");
        Edge joshCreateRipple = new Edge("created").source(josh).target(ripple)
                                                   .property("date",
                                                             "2017-12-10");
        Edge joshCreateLop = new Edge("created").source(josh).target(lop)
                                                .property("date", "2009-11-11");
        Edge peterCreateLop = new Edge("created").source(peter).target(lop)
                                                 .property("date",
                                                           "2017-03-24");

        List<Vertex> vertices = new ArrayList<>();
        vertices.add(marko);
        vertices.add(vadas);
        vertices.add(lop);
        vertices.add(josh);
        vertices.add(ripple);
        vertices.add(peter);

        List<Edge> edges = new ArrayList<>();
        edges.add(markoKnowsVadas);
        edges.add(markoKnowsJosh);
        edges.add(markoCreateLop);
        edges.add(joshCreateRipple);
        edges.add(joshCreateLop);
        edges.add(peterCreateLop);

        vertices = graph.addVertices(vertices);
        vertices.forEach(vertex -> System.out.println(vertex));

        edges = graph.addEdges(edges, false);
        edges.forEach(edge -> System.out.println(edge));

        hugeClient.close();
    }
}
```

{{< /tab >}}
{{< /tabs >}}

#### 4.4 运行 Example

1. [启动 HugeGraph Server](/cn/docs/quickstart/hugegraph/hugegraph-server)，在图空间 `DEFAULT` 中准备名为 `hugegraph` 的测试图。
1. 将 Maven 工程的 JDK 设为 17，把所选示例中 `HugeClient.builder(...)` 和 `configUser(...)` 的 Server 地址、图空间、图名和凭据改为实际配置。
   Server 未开启鉴权时，省略 `configUser(...)`。
1. 在 IDE 中运行 `SingleExample.main()` 或 `BatchExample.main()`。两个示例都会创建 Schema 和图数据、打印结果并关闭客户端。
   请使用测试图，已有 Schema 或数据可能影响重复运行。
{.steps}

本文的代码都是`java`语言写的，但其风格与`gremlin(groovy)`是非常类似的。用户只需要把代码中的变量声明替换成`def`或直接去掉，
就能将`java`代码转变为`groovy`；另外就是每一行语句最后可以不加分号，`groovy`认为一行就是一条语句。

用户在`HugeGraph-Hubble`中编写的`gremlin(groovy)`可以参考本文的`java`代码，下面会举出几个例子。

本文以 Toolchain `master`（Client `1.8.0`）为准。请先按上方快速入门准备对应依赖；
能力探测等新增接口不能直接用于旧版 Client。

### 5 HugeClient 构造与操作入口

HugeGraph-Client 是操作 graph 的总入口，用户必须先创建出 HugeGraph-Client 对象，与 HugeGraph-Server 建立连接（伪连接）后，才能获取到 schema、graph 以及 gremlin 的操作入口对象。

HugeGraph-Client 连接服务端已有的图。构造器支持传入 GraphSpace；使用双参数构造器或传入空值时，GraphSpace 默认为 `DEFAULT`。

```java
// HugeGraphServer 地址："http://localhost:8080"
// 图的名称："hugegraph"
HugeClient hugeClient = HugeClient.builder("http://localhost:8080", "hugegraph")
                                //.builder("http://localhost:8080", "graphSpaceName", "hugegraph")
                                  .configTimeout(20) // 默认 20s 超时
                                  // .configUser("username", "password") // 服务端启用认证时配置
                                  .build();
```

上述创建 HugeClient 的过程如果失败会抛出异常，用户需要 try-catch。如果成功则继续获取 schema、graph 以及 gremlin 的 manager。

在`HugeGraph - Hubble`中通过`gremlin`来操作时，不需要使用`HugeClient`，可以忽略。

#### 5.1 构造器选项 {#11-构造器选项}

构造器支持下列选项。所有超时参数的单位都是秒，内部会转换为毫秒。

| interface                                                    | description                                        | default            |
|--------------------------------------------------------------|----------------------------------------------------|--------------------|
| `configUrl(String url)`                                       | 服务端地址，通常已经通过 `builder(...)` 传入        | 必填               |
| `configGraph(String graph)`                                   | 图名称，通常已经通过 `builder(...)` 传入            | 必填               |
| `configGraphSpace(String graphSpace)`                         | GraphSpace 名称，传入 null 或空值时回退为 `DEFAULT` | `DEFAULT`          |
| `configUser(String username, String password)`                | 服务端用户名和密码，传入 null 时按空字符串处理      | 空，不开启认证     |
| `configToken(String token)`                                   | 使用 Token 代替用户名和密码                         | 空                 |
| `configTimeout(int seconds)`                                  | 请求超时，建议使用正数秒值                     | 20                 |
| `configConnectTimeout(Integer seconds)`                       | 连接超时，不设置时沿用 `configTimeout`              | 未设置             |
| `configReadTimeout(Integer seconds)`                          | 读取超时，不设置时沿用 `configTimeout`              | 未设置             |
| `configPool(int maxConns, int maxConnsPerRoute)`              | 连接池大小，任意一项传入 `0` 时恢复其默认值         | 4 x CPU 数，2 x CPU 数 |
| `configIdleTime(int seconds)`                                 | 空闲连接保持时间，必须大于 0                        | 30                 |
| `configSSL(String trustStoreFile, String trustStorePassword)` | HTTPS 连接使用的信任库                              | 空                 |
| `configHttpBuilder(Consumer<OkHttpClient.Builder> consumer)`  | 回调，用于进一步定制底层的 OkHttp 客户端            | 无                 |
| `graphRequired(boolean graphRequired)`                        | `build()` 是否拒绝空的 url 或图名称                 | true               |

当前 master 的 `configTimeout(0)` 存在单位换算缺陷，会得到 20,000 秒而非默认的 20 秒。
保持默认值时省略该调用，或显式使用 `configTimeout(20)`；不要用 `0` 恢复默认值。

调用 `build()` 时，客户端会读取服务端的 API 版本，超出 `[0.38, 0.81)` 范围时报错。

#### 5.2 操作入口 {#12-操作入口}

除 schema、graph 和 gremlin 外，HugeClient 还提供下列入口。图级别的入口只有在指定了图名称时才可用；如果创建客户端时图名称为空，这些入口会返回 null，直到调用 `assignGraph(graphSpace, graph)` 为止。

| interface             | returns                | scope      | description                                                |
|-----------------------|------------------------|------------|------------------------------------------------------------|
| `schema()`            | `SchemaManager`        | graph      | 管理 PropertyKey、VertexLabel、EdgeLabel 和 IndexLabel      |
| `graph()`             | `GraphManager`         | graph      | 单条或批量地增删改查顶点和边                                |
| `gremlin()`           | `GremlinManager`       | graph      | 同步执行 Gremlin 语句，或作为异步任务提交                    |
| `cypher()`            | `CypherManager`        | graph      | 同步执行 Cypher 语句，或作为异步任务提交                     |
| `traverser()`         | `TraverserManager`     | graph      | RESTful 遍历，如最短路径、k-out、k-neighbor、交叉点等         |
| `variables()`         | `VariablesManager`     | graph      | 获取、设置、列出和删除图变量                                 |
| `job()`               | `JobManager`           | graph      | 重建 VertexLabel、EdgeLabel 或 IndexLabel 的索引             |
| `task()`              | `TaskManager`          | graph      | 列出、获取、取消、删除异步任务，或等待其完成                  |
| `computer()`          | `ComputerManager`      | graph      | 创建、取消、列出和获取 computer 任务                         |
| `graphs()`            | `GraphsManager`        | graphspace | 创建、克隆、列出、重载、清空和删除图，读取和设置图的模式      |
| `graphSpace()`        | `GraphSpaceManager`    | server     | 管理 GraphSpace，详见第 8 节                                 |
| `auth()`              | `AuthManager`          | server     | 管理 user、group、target、belong 和 access                   |
| `metrics()`           | `MetricsManager`       | server     | 读取后端、系统和统计指标                                     |
| `versionManager()`    | `VersionManager`       | server     | 读取服务端的 core、gremlin 和 API 版本                        |

客户端还会报告所连服务端支持的能力，调用方可以据此判断，而不必解析版本号：`supportsGraphSpace()`、`supportsCypher()`、`supportsGraphCreate()`、`supportsDefaultRole()` 和 `isServerAuthEnabled()`。

### 6 元数据管理 (SchemaManager) {#2-元数据}

#### 6.1 SchemaManager {#21-schemamanager}

SchemaManager 用于管理 HugeGraph 中的四种元数据，分别是 PropertyKey（属性类型）、VertexLabel（顶点类型）、EdgeLabel（边类型）和 IndexLabel（索引标签）。在定义元数据信息之前必须先创建 SchemaManager 对象。

用户可使用如下方法获得 SchemaManager 对象：

```java
SchemaManager schema = hugeClient.schema()
```

在`HugeGraph-Hubble`中通过`gremlin`创建`schema`对象：

```groovy
schema = graph.schema()
```

下面分别介绍四种元数据的定义过程。

#### 6.2 PropertyKey {#22-propertykey}

##### 6.2.1 接口及参数介绍 {#221-接口及参数介绍}

PropertyKey 用来规范顶点和边的属性的约束，暂不支持定义属性的属性。

PropertyKey 允许定义的约束信息包括：name、datatype、cardinality、aggregateType、writeType、userdata，下面逐一介绍。

- name: 属性的名字，用来区分不同的 PropertyKey，不允许有同名的属性；

| interface                | param | must set |
|--------------------------|-------|----------|
| propertyKey(String name) | name  | y        |

- datatype：属性值类型，必须从下表中选择符合具体业务场景的一项显式设置；

| interface   | Java Class |
|-------------|------------|
| asText()    | String     |
| asInt()     | Integer    |
| asDate()    | Date       |
| asUUID()    | UUID       |
| asBoolean() | Boolean    |
| asByte()    | Byte       |
| asBlob()    | Byte[]     |
| asDouble()  | Double     |
| asFloat()   | Float      |
| asLong()    | Long       |

- cardinality：属性值是单值还是多值，多值的情况下又分为允许有重复值和不允许有重复值，该项默认为 single，如有必要可从下表中选择一项设置；

| interface     | cardinality | description                                 |
|---------------|-------------|---------------------------------------------|
| valueSingle() | single      | single value                                |
| valueList()   | list        | multi-values that allow duplicate value     |
| valueSet()    | set         | multi-values that not allow duplicate value |

- aggregateType：同一属性被重复写入时的合并方式，默认为 none，即保留最后写入的值。数值类的选项要求属性为数字类型；

| interface   | aggregateType | description        |
|-------------|---------------|--------------------|
| calcSum()   | sum           | 对写入的值累加      |
| calcMax()   | max           | 保留最大值          |
| calcMin()   | min           | 保留最小值          |
| calcOld()   | old           | 保留首次写入的值，忽略后续更新 |

`aggregateType(AggregateType type)` 可以直接设置该项，传入 `AggregateType.NONE` 即恢复默认。

- writeType：属性属于 OLTP 图数据还是 OLAP 计算结果，对于 OLAP 还区分是否带索引，默认为 oltp；

| writeType      | description            |
|----------------|------------------------|
| OLTP           | 普通图属性              |
| OLAP_COMMON    | 不带索引的 OLAP 属性     |
| OLAP_SECONDARY | 带二级索引的 OLAP 属性   |
| OLAP_RANGE     | 带范围索引的 OLAP 属性   |

| interface                        | description            |
|----------------------------------|------------------------|
| writeType(WriteType writeType)   | 使用枚举值设置写入类型  |
| writeType(String name)           | 使用枚举名设置写入类型  |

- userdata：用户可以自己添加一些约束或额外信息，然后自行检查传入的属性是否满足约束，或者必要的时候提取出额外信息

| interface                          | description                                    |
|------------------------------------|------------------------------------------------|
| userdata(String key, Object value) | The same key, the latter will cover the former |

##### 6.2.2 创建 PropertyKey {#222-创建-propertykey}

```java
schema.propertyKey("name").asText().valueSet().ifNotExist().create()
```

在`HugeGraph-Hubble`中通过`gremlin`创建上述`PropertyKey`对象的语法完全一致，如果用户没有定义出`schema`变量，应该这样写：

```groovy
graph.schema().propertyKey("name").asText().valueSet().ifNotExist().create()
```

以下的示例中，`gremlin`与`java`的语法完全一致，不再赘述。

- ifNotExist()：为 create 添加判断机制，若当前 PropertyKey 已经存在则不再创建，否则创建该属性。若不添加判断，在 properkey 已存在的情况下会抛出异常信息，下同，不再赘述。

##### 6.2.3 删除 PropertyKey {#223-删除-propertykey}

```java
schema.propertyKey("name").remove()
```

##### 6.2.4 查询 PropertyKey {#224-查询-propertykey}

```java
// 获取 PropertyKey 对象
schema.getPropertyKey("name")

// 获取 PropertyKey 属性
schema.getPropertyKey("name").cardinality()
schema.getPropertyKey("name").dataType()
schema.getPropertyKey("name").name()
schema.getPropertyKey("name").userdata()
```

#### 6.3 VertexLabel {#23-vertexlabel}

##### 6.3.1 接口及参数介绍 {#231-接口及参数介绍}

VertexLabel 用来定义顶点类型，描述顶点的约束信息：

VertexLabel 允许定义的约束信息包括：name、idStrategy、properties、primaryKeys、nullableKeys 和 ttl，下面逐一介绍。

- name: 属性的名字，用来区分不同的 VertexLabel，不允许有同名的属性；

| interface                | param | must set |
|--------------------------|-------|----------|
| vertexLabel(String name) | name  | y        |

- idStrategy: 每一个 VertexLabel 都可以选择自己的 Id 策略，目前有三种策略供选择，即 Automatic（自动生成）、Customize（用户传入）和 PrimaryKey（主属性键）。其中 Automatic 使用 Snowflake 算法生成 Id，Customize 需要用户自行传入字符串或数字类型的 Id，PrimaryKey 则允许用户从 VertexLabel 的属性中选择若干主属性作为区分的依据，HugeGraph 内部会根据主属性的值拼接生成 Id。idStrategy 默认使用 Automatic 的，但如果用户没有显式设置 idStrategy 又调用了 primaryKeys(...) 方法设置了主属性，则 idStrategy 将自动使用 PrimaryKey；

| interface            | idStrategy       | description                                             |
|----------------------|------------------|---------------------------------------------------------|
| useAutomaticId       | AUTOMATIC        | generate id automatically by Snowflake algorithm        |
| useCustomizeStringId | CUSTOMIZE_STRING | passed id by user, must be string type                  |
| useCustomizeNumberId | CUSTOMIZE_NUMBER | passed id by user, must be number type                  |
| useCustomizeUuidId   | CUSTOMIZE_UUID   | passed id by user, must be UUID type                    |
| usePrimaryKeyId      | PRIMARY_KEY      | choose some important prop as primary key to splice id  |

- properties: 定义顶点的属性，传入的参数是 PropertyKey 的 name

| interface                        | description               |
|----------------------------------|---------------------------|
| properties(String... properties) | allow to pass multi props |

- primaryKeys: 当用户选择了 PrimaryKey 的 Id 策略时，需要从 VertexLabel 的属性中选择若干主属性作为区分的依据；

| interface                   | description                               |
|-----------------------------|-------------------------------------------|
| primaryKeys(String... keys) | allow to choose multi prop as primaryKeys |

需要注意的是，Id 策略的选择与 primaryKeys 的设置有一些相互约束，不能随意调用，约束关系见下表：

|                   | useAutomaticId | useCustomizeStringId | useCustomizeNumberId | usePrimaryKeyId |
|-------------------|----------------|----------------------|----------------------|-----------------|
| unset primaryKeys | AUTOMATIC      | CUSTOMIZE_STRING     | CUSTOMIZE_NUMBER     | ERROR           |
| set primaryKeys   | ERROR          | ERROR                | ERROR                | PRIMARY_KEY     |

客户端自身只校验 Id 策略是否被重复设置，因此在同一个构造器上调用两个上述方法会在本地报错。上表中的组合由服务端校验。

- nullableKeys: 对于通过 properties(...) 方法设置过的属性，默认全都是不可为空的，也就是在创建顶点时该属性必须赋值，这样可能对用户数据提出了太过严格的完整性要求。为避免这样的强约束，用户可以通过
本方法设置若干属性为可空的，这样添加顶点时该属性可以不赋值。

| interface                          | description               |
|------------------------------------|---------------------------|
| nullableKeys(String... properties) | allow to pass multi props |

注意：primaryKeys 和 nullableKeys 不能有交集，因为一个属性不能既作为主属性，又是可空的。

- ttl：该类型顶点的存活时间，默认为 0，即永不过期。客户端会拒绝负值。默认从顶点写入的时刻开始计时；设置 ttlStartTime 后，改为从该 label 的某个日期属性开始计时。

| interface                        | description                     |
|----------------------------------|---------------------------------|
| ttl(long ttl)                    | 设置存活时间，0 表示不过期       |
| ttlStartTime(String property)    | 指定计时起点所用的日期属性       |

- enableLabelIndex：用户可以指定是否需要为 label 创建索引。不创建则无法全局搜索指定 label 的顶点和边，创建则可以全局搜索，做类似于`g.V().hasLabel('person'), g.E().has('label', 'person')`这样的查询，
但是插入数据时性能上会更加慢，并且需要占用更多的存储空间。此项默认为 true。

| interface                        | description                     |
|----------------------------------|---------------------------------|
| enableLabelIndex(boolean enable) | Whether to create a label index |

- userdata：用户可以自己添加一些约束或额外信息，然后自行检查传入的属性是否满足约束，或者必要的时候提取出额外信息

| interface                          | description                                    |
|------------------------------------|------------------------------------------------|
| userdata(String key, Object value) | The same key, the latter will cover the former |

##### 6.3.2 创建 VertexLabel {#232-创建-vertexlabel}

```java
// 使用 Automatic 的 Id 策略
schema.vertexLabel("person").properties("name", "age").ifNotExist().create();
schema.vertexLabel("person").useAutomaticId().properties("name", "age").ifNotExist().create();

// 使用 Customize_String 的 Id 策略
schema.vertexLabel("person").useCustomizeStringId().properties("name", "age").ifNotExist().create();
// 使用 Customize_Number 的 Id 策略
schema.vertexLabel("person").useCustomizeNumberId().properties("name", "age").ifNotExist().create();
// 使用 Customize_Uuid 的 Id 策略
schema.vertexLabel("person").useCustomizeUuidId().properties("name", "age").ifNotExist().create();

// 使用 PrimaryKey 的 Id 策略
schema.vertexLabel("person").properties("name", "age").primaryKeys("name").ifNotExist().create();
schema.vertexLabel("person").usePrimaryKeyId().properties("name", "age").primaryKeys("name").ifNotExist().create();
```

##### 6.3.3 追加 VertexLabel {#233-追加-vertexlabel}

VertexLabel 是可以追加约束的，不过仅限 properties 和 nullableKeys，而且追加的属性也必须添加到 nullableKeys 集合中。

```java
schema.vertexLabel("person").properties("price").nullableKeys("price").append();
```

##### 6.3.4 删除 VertexLabel {#234-删除-vertexlabel}

```java
schema.vertexLabel("person").remove();
```

##### 6.3.5 查询 VertexLabel {#235-查询-vertexlabel}

```java
// 获取 VertexLabel 对象
schema.getVertexLabel("name")

// 获取 property key 属性
schema.getVertexLabel("person").idStrategy()
schema.getVertexLabel("person").primaryKeys()
schema.getVertexLabel("person").name()
schema.getVertexLabel("person").properties()
schema.getVertexLabel("person").nullableKeys()
schema.getVertexLabel("person").userdata()
schema.getVertexLabel("person").ttl()
schema.getVertexLabel("person").ttlStartTime()
```

#### 6.4 EdgeLabel {#24-edgelabel}

##### 6.4.1 接口及参数介绍 {#241-接口及参数介绍}

EdgeLabel 用来定义边类型，描述边的约束信息。

EdgeLabel 允许定义的约束信息包括：name、sourceLabel、targetLabel、frequency、properties、sortKeys、nullableKeys 和 ttl，下面逐一介绍。

- name: 属性的名字，用来区分不同的 EdgeLabel，不允许有同名的属性；

| interface              | param | must set |
|------------------------|-------|----------|
| edgeLabel(String name) | name  | y        |

- sourceLabel 和 targetLabel: 边连接的源顶点类型名和目标顶点类型名，两者都设置等同于声明一组连接。

- link: EdgeLabel 内部保存的是一组源顶点和目标顶点的组合，因此 `link(...)` 可以多次调用，让同一种边连接多组顶点类型。一旦通过这种方式添加过组合，`sourceLabel(...)` 和 `targetLabel(...)` 就会被拒绝；同时 `sourceLabel()` 和 `targetLabel()` 这两个取值方法只在恰好有一组组合时可用，需要读取全部组合时请使用 `links()`。

| interface                                    | param                    | must set                |
|----------------------------------------------|--------------------------|-------------------------|
| link(String sourceLabel, String targetLabel) | sourceLabel, targetLabel | y，或设置下面两项        |
| sourceLabel(String label)                    | label                    | y，除非已使用 link()     |
| targetLabel(String label)                    | label                    | y，除非已使用 link()     |

- frequency: 字面意思是频率，表示在两个具体的顶点间某个关系出现的次数，可以是单次（single）或多次（frequency），默认为 single；

| interface    | frequency | description                         |
|--------------|-----------|-------------------------------------|
| singleTime() | single    | a relationship can only occur once  |
| multiTimes() | multiple  | a relationship can occur many times |

- properties: 定义边的属性

| interface                        | description               |
|----------------------------------|---------------------------|
| properties(String... properties) | allow to pass multi props |

- sortKeys: 当 EdgeLabel 的 frequency 为 multiple 时，需要某些属性来区分这多次的关系，故引入了 sortKeys（排序键）；

| interface                | description                            |
|--------------------------|----------------------------------------|
| sortKeys(String... keys) | allow to choose multi prop as sortKeys |

- nullableKeys: 与顶点中的 nullableKeys 概念一致，不再赘述

注意：sortKeys 和 nullableKeys 也不能有交集。

- ttl：与顶点中的 ttl 概念一致，同样提供 `ttl(long ttl)` 和 `ttlStartTime(String property)` 方法，默认值同样为 0。

- edge label type：EdgeLabel 默认为普通类型，也可以声明为一族边类型的父类型、某个父类型的子类型，或者通用类型：

| interface                     | edgeLabelType | description                    |
|-------------------------------|---------------|--------------------------------|
| asBase()                      | PARENT        | 将该 label 声明为父类型         |
| withBase(String parentLabel)  | SUB           | 将该 label 声明为 parentLabel 的子类型 |
| asGeneral()                   | GENERAL       | 将该 label 声明为通用类型       |

- enableLabelIndex：与顶点中的 enableLabelIndex 概念一致，不再赘述

- userdata：用户可以自己添加一些约束或额外信息，然后自行检查传入的属性是否满足约束，或者必要的时候提取出额外信息

| interface                          | description                                    |
|------------------------------------|------------------------------------------------|
| userdata(String key, Object value) | The same key, the latter will cover the former |

##### 6.4.2 创建 EdgeLabel {#242-创建-edgelabel}

```java
schema.edgeLabel("knows").link("person", "person").properties("date").ifNotExist().create();
schema.edgeLabel("created").multiTimes().link("person", "software").properties("date").sortKeys("date").ifNotExist().create();
```

##### 6.4.3 追加 EdgeLabel {#243-追加-edgelabel}

```java
schema.edgeLabel("knows").properties("price").nullableKeys("price").append();
```

##### 6.4.4 删除 EdgeLabel {#244-删除-edgelabel}

```java
schema.edgeLabel("knows").remove();
```

##### 6.4.5 查询 EdgeLabel {#245-查询-edgelabel}

```java
// 获取 EdgeLabel 对象
schema.getEdgeLabel("knows")

// 获取 property key 属性
schema.getEdgeLabel("knows").frequency()
schema.getEdgeLabel("knows").sourceLabel()
schema.getEdgeLabel("knows").targetLabel()
schema.getEdgeLabel("knows").sortKeys()
schema.getEdgeLabel("knows").name()
schema.getEdgeLabel("knows").properties()
schema.getEdgeLabel("knows").nullableKeys()
schema.getEdgeLabel("knows").userdata()
schema.getEdgeLabel("knows").ttl()
schema.getEdgeLabel("knows").ttlStartTime()
schema.getEdgeLabel("knows").edgeLabelType()
// 全部的源顶点和目标顶点组合，存在多组时也可安全调用
schema.getEdgeLabel("knows").links()
```

#### 6.5 IndexLabel {#25-indexlabel}

##### 6.5.1 接口及参数介绍 {#251-接口及参数介绍}

IndexLabel 用来定义索引类型，描述索引的约束信息，主要是为了方便查询。

IndexLabel 允许定义的约束信息包括：name、baseType、baseValue、indexFields、indexType，下面逐一介绍。

- name: 属性的名字，用来区分不同的 IndexLabel，不允许有同名的属性；

| interface               | param | must set |
|-------------------------|-------|----------|
| indexLabel(String name) | name  | y        |

- baseType: 表示要为 VertexLabel 还是 EdgeLabel 建立索引, 与下面的 baseValue 配合使用；

- baseValue: 指定要建立索引的 VertexLabel 或 EdgeLabel 的名称；

| interface             | param     | description                              |
|-----------------------|-----------|------------------------------------------|
| onV(String baseValue) | baseValue | build index for VertexLabel: 'baseValue' |
| onE(String baseValue) | baseValue | build index for EdgeLabel: 'baseValue'   |

- indexFields: 要在哪些属性上建立索引，可以是为多列建立联合索引；

| interface            | param | description                                               |
|----------------------|-------|-----------------------------------------------------------|
| by(String... fields) | files | allow to build index for multi fields for secondary index |

- indexType: 建立的索引类型，目前支持五种，即 Secondary、Range、Search、Shard 和 Unique。
    - Secondary 支持精确匹配的二级索引，允许建立联合索引，联合索引支持索引前缀搜索
        - 单个属性，支持相等查询，比如：person 顶点的 city 属性的二级索引，可以用`g.V().has("city", "北京")
        `查询"city 属性值是北京"的全部顶点
        - 联合索引，支持前缀查询和相等查询，比如：person 顶点的 city 和 street 属性的联合索引，可以用`g.V().has
        ("city", "北京").has('street', '中关村街道')
        `查询"city属性值是北京且street属性值是中关村"的全部顶点，或者`g.V()
        .has("city", "北京")`查询"city 属性值是北京"的全部顶点
        > secondary index 的查询都是基于"是"或者"相等"的查询条件，不支持"部分匹配"
    - Range 支持数值类型的范围查询
        - 必须是单个数字或者日期属性，比如：person 顶点的 age 属性的范围索引，可以用`g.V().has("age", P.gt(18))
        `查询"age属性值大于18"的顶点。除了`P.gt()`以外，还支持`P.gte()`, `P.lte()`, `P.lt()`,
        `P.eq()`, `P.between()`, `P.inside()`和`P.outside()`等
    - Search 支持全文检索的索引
        - 必须是单个文本属性，比如：person 顶点的 address 属性的全文索引，可以用`g.V().has("address", Text
        .contains('大厦')`查询"address 属性中包含大厦"的全部顶点
        > search index 的查询是基于"是"或者"包含"的查询条件
    - Shard 支持前缀匹配 + 数字范围查询的索引
        - N 个属性的分片索引，支持前缀相等情况下的范围查询，比如：person 顶点的 city 和 age 属性的分片索引，可以用`g.V().has
        ("city", "北京").has("age", P.between(18, 30))
        `查询"city 属性是北京且年龄大于等于 18 小于 30"的全部顶点
        - shard index N 个属性全是文本属性时，等价于 secondary index
        - shard index 只有单个数字或者日期属性时，等价于 range index
        > shard index 可以有任意数字或者日期属性，但是查询时最多只能提供一个范围查找条件，且该范围查找条件的属性的前缀属性都是相等查询条件
    - Unique 支持属性值唯一性约束，即可以限定属性的值不重复，允许联合索引，但不支持查询
        - 单个或者多个属性的唯一性索引，不可用来查询，只可对属性的值进行限定，当出现重复值时将报错

| interface   | indexType | description                                         |
|-------------|-----------|-----------------------------------------------------|
| secondary() | Secondary | support prefix search                               |
| range()     | Range     | support range(numeric or date type) search          |
| search()    | Search    | support full text search                            |
| shard()     | Shard     | support prefix + range(numeric or date type) search |
| unique()    | Unique    | support unique props value, not support search      |

##### 6.5.2 创建 IndexLabel {#252-创建-indexlabel}

以下示例假定已创建带 `name`、`age` 的 `person` 顶点类型，以及带 `date` 的 `created` 边类型。
先补充索引所需属性；`id` 是业务属性，与顶点的内部 ID 不同。

```java
schema.propertyKey("lived").asText().ifNotExist().create();
schema.propertyKey("city").asText().ifNotExist().create();
schema.propertyKey("id").asInt().ifNotExist().create();
schema.vertexLabel("person").properties("lived", "city", "id")
      .nullableKeys("lived", "city", "id").append();

schema.indexLabel("personByAge").onV("person").by("age").range().ifNotExist().create();
schema.indexLabel("createdByDate").onE("created").by("date").secondary().ifNotExist().create();
schema.indexLabel("personByLived").onV("person").by("lived").search().ifNotExist().create();
schema.indexLabel("personByCityAndAge").onV("person").by("city", "age").shard().ifNotExist().create();
schema.indexLabel("personById").onV("person").by("id").unique().ifNotExist().create();
```

##### 6.5.3 删除 IndexLabel {#253-删除-indexlabel}

```java
schema.indexLabel("personByAge").remove()
```

##### 6.5.4 查询 IndexLabel {#254-查询-indexlabel}

```java
// 获取 IndexLabel 对象
schema.getIndexLabel("personByAge")

// 获取 property key 属性
schema.getIndexLabel("personByAge").baseType()
schema.getIndexLabel("personByAge").baseValue()
schema.getIndexLabel("personByAge").indexFields()
schema.getIndexLabel("personByAge").indexType()
schema.getIndexLabel("personByAge").name()
```

### 7 图数据操作 (GraphManager) {#3-图数据}

#### 7.1 Vertex {#31-vertex}

顶点是构成图的最基本元素，一个图中可以有非常多的顶点。下面给出一个添加顶点的例子：

```java
Vertex marko = graph.addVertex(T.LABEL, "person", "name", "marko", "age", 29);
Vertex lop = graph.addVertex(T.LABEL, "software", "name", "lop", "lang", "java", "price", 328);
```

- 添加顶点的关键是顶点属性，添加顶点函数的参数个数必须为偶数，且满足`key1 -> val1, key2 -> val2 ···`的顺序排列，键值对之间的顺序是自由的。
- 参数中必须包含一对特殊的键值对，就是`T.LABEL -> "val"`，用来定义该顶点的类别，以便于程序从缓存或后端获取到该 VertexLabel 的 schema 定义，然后做后续的约束检查。例子中的 label 定义为 person。`T.LABEL` 就是常量 `"label"`，直接传入该字符串效果相同。
- 如果顶点类型的 Id 策略为 `AUTOMATIC`，则不允许用户传入 id 键值对。
- 如果顶点类型的 Id 策略为 `CUSTOMIZE_STRING`，则用户需要自己传入 String 类型 id 的值，键值对形如：`T.ID, "123456"`。
- 如果顶点类型的 Id 策略为 `CUSTOMIZE_NUMBER`，则用户需要自己传入 Number 类型 id 的值，键值对形如：`T.ID, 123456`。
- 如果顶点类型的 Id 策略为 `PRIMARY_KEY`，参数还必须全部包含该`primaryKeys`对应属性的名和值，如果不设置会抛出异常。比如之前`person`的`primaryKeys`是`name`，例子中就设置了`name`的值为`marko`。
- 对于非 nullableKeys 的属性，必须要赋值。
- 剩下的参数就是顶点其他属性的设置，但并非必须。
- 调用`addVertex`方法后，顶点会立刻被插入到后端存储系统中。

#### 7.2 Edge {#32-edge}

有了点，还需要边才能构成完整的图。下面给出一个添加边的例子：

```java
Edge knows1 = marko.addEdge("knows", vadas, "city", "Beijing");
```

- 由（源）顶点来调用添加边的函数，函数第一个参数为边的 label，第二个参数是目标顶点，这两个参数的位置和顺序是固定的。后续的参数就是`key1 -> val1, key2 -> val2 ···`的顺序排列，设置边的属性，键值对顺序自由。
- 源顶点和目标顶点必须符合 EdgeLabel 中 source-label 和 target-label 的定义，不能随意添加。
- 对于非 nullableKeys 的属性，必须要赋值。


**注意：当 frequency 为 multiple 时必须要设置 sortKeys 对应属性类型的值。**

### 8 图空间管理 (GraphSpace) {#4-图管理}
Client 支持管理一个物理部署中的多个 GraphSpace，每个 GraphSpace 可以包含多个图。不指定 GraphSpace 时使用 `DEFAULT`。

GraphSpace 需要服务端 core 版本不低于 1.7.0。连接更早的服务端时，客户端会退回到 legacy 模式，此时 `hugeClient.supportsGraphSpace()` 返回 false。

#### 8.1 创建GraphSpace {#41-创建graphspace}

```java
GraphSpaceManager spaceManager = hugeClient.graphSpace();

// 定义 GraphSpace 配置
GraphSpace graphSpace = new GraphSpace();
graphSpace.setName("myGraphSpace");
graphSpace.setDescription("Business data graph space");
graphSpace.setMaxGraphNumber(10);  // 最大图数量
graphSpace.setMaxRoleNumber(100);  // 最大角色数量

// 创建 GraphSpace
spaceManager.createGraphSpace(graphSpace);
```
#### 8.2 GraphSpace 接口汇总 {#42-graphspace-接口汇总}

| 类别 | 接口 | 描述 |
|------|------|------|
| Manager - 查询 | listGraphSpace() | 获取所有 GraphSpace 名称 |
| | listProfile() / listProfile(String prefix) | 获取 GraphSpace 概要 |
| | getGraphSpace(String name) | 获取指定 GraphSpace |
| | getDefault() | 获取默认 GraphSpace |
| Manager - 创建/更新 | createGraphSpace(GraphSpace) | 创建 GraphSpace |
| | updateGraphSpace(GraphSpace) | 更新配置 |
| | setDefault(String name) | 设置默认 GraphSpace |
| Manager - 删除 | deleteGraphSpace(String name) | 删除指定 GraphSpace |
| Manager - 默认角色 | setDefaultRole(String name, String user, String role) | 授予默认角色，可用第四个参数限定到某个图 |
| | checkDefaultRole(String name, String user, String role) | 检查默认角色，可用第四个参数限定到某个图 |
| | deleteDefaultRole(String name, String user, String role) | 撤销默认角色，可用第四个参数限定到某个图 |
| GraphSpace - 属性 | getName() / getNickname() / getDescription() | 获取名称/昵称/描述 |
| | getGraphNumberUsed() / getRoleNumberUsed() | 获取已使用的图数量/角色数量 |
| | getCpuUsed() / getMemoryUsed() / getStorageUsed() | 获取已使用的资源 |
| | getCreateTime() / getUpdateTime() | 获取创建时间/更新时间 |
| GraphSpace - 配置 | setDescription(String) / setNickname(String) | 设置描述/昵称 |
| | setMaxGraphNumber(int) / setMaxRoleNumber(int) | 设置最大图数量/角色数量 |
| | setCpuLimit(int) / setMemoryLimit(int) / setStorageLimit(int) | 设置资源配额 |
| | setConfigs(Map&lt;String, Object&gt;) | 设置额外的配置项 |
