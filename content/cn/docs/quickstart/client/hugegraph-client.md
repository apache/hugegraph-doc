---
title: "HugeGraph-Java-Client"
linkTitle: "Java 客户端"
weight: 1
---

### 1 HugeGraph-Client 概述

[HugeGraph Java Client](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-client) 将 Java API 转换为 HugeGraph Server 的 REST 请求，支持管理 Schema 和图数据、执行 Gremlin 及调用 Traverser API。详细接口见 [Client API](/cn/docs/clients/hugegraph-client)，本文给出 Java 项目的接入示例。

其他语言可使用 [Go Client](/cn/docs/quickstart/client/hugegraph-client-go) 或 HugeGraph-AI 仓库中的 [Python Client](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-python-client)。

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

### 4 完整示例

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

#### 4.5 详细 API 说明

示例说明见[HugeGraph-Client 基本 API 介绍](/cn/docs/clients/hugegraph-client)
