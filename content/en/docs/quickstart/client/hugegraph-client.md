---
title: "HugeGraph-Java-Client"
linkTitle: "Java-Client"
weight: 1
---

### 1 Overview

[HugeGraph Java Client](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-client) translates Java APIs into REST requests to HugeGraph Server. It supports managing schemas and graph data, executing Gremlin queries, and calling Traverser APIs. See the [Client API](/docs/clients/hugegraph-client) for detailed interfaces; this page shows how to use the client in a Java project.

For other languages, use the [Go Client](/docs/quickstart/client/hugegraph-client-go) or the [Python Client](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-python-client) maintained in the HugeGraph-AI repository.

### 2 What You Need

- JDK 17 for this walkthrough and for building Client `1.8.0` from Toolchain `master`
- Maven 3.6.3+

### 3 How To Use

The basic steps to use HugeGraph-Client are as follows:

1. Create a Maven project in IntelliJ IDEA or Eclipse.
1. Add the HugeGraph-Client dependency to `pom.xml`.
1. Create a client, call its APIs, and close it after use.
{.steps}

See the complete example in the following section for the detail.

### 4 Complete Example 

#### 4.1 Build New Maven Project

Using IDEA or Eclipse to create the project:

- [Build by Eclipse](http://www.vogella.com/tutorials/EclipseMaven/article.html)
- [Build by IntelliJ IDEA](https://vaadin.com/docs/-/part/framework/getting-started/getting-started-idea.html)

#### 4.2 Add Hugegraph-Client Dependency In POM

```xml
<dependencies>
    <dependency>
        <groupId>org.apache.hugegraph</groupId>
        <artifactId>hugegraph-client</artifactId>
        <!-- The complete examples below work with the published 1.7.0 client -->
        <version>1.7.0</version>
    </dependency>    
</dependencies>
```

Choose the client version before building:

| Use case | Client version | Java build target |
| --- | --- | --- |
| Run the complete examples below | Published `1.7.0`; use the dependency above | Java 8 in the release POM; this walkthrough uses JDK 17 |
| Use new master APIs, such as capability detection | Toolchain `master` (based on 1.8) | Java 17 |

The examples use Schema, Graph, Gremlin and resource-cleanup APIs available in Client `1.7.0` and compatible with Toolchain `master`.
The release's Java build target does not describe the runtime requirements of every transitive dependency.

To use unreleased features from the master branch, build Client from source (see [Tools source build instructions](/docs/quickstart/toolchain/hugegraph-tools/#build-current-source)):

```bash
java -version
mvn -version
mvn -Dmaven.repo.local="${candidate_dir:?Run the candidate SDK setup first}/m2" \
  -Dsdk.validation.mode=candidate \
  install -pl hugegraph-client -am -DskipTests -Dmaven.javadoc.skip=true -ntp
```

Both version checks must report JDK 17. Also pass `-Dmaven.repo.local="$candidate_dir/m2"` to Maven commands in projects using Client from master.
Client and Server versions need not be identical; check the required APIs and compatibility before upgrading.

#### 4.3 Example

Choose a single-record or batch example. Save the complete code as `src/main/java/SingleExample.java` or
`src/main/java/BatchExample.java` in your Maven project. The copy button includes the folded lines.

{{< tabs group="java-client-example" default="single" label="Java client example" >}}
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
                                          // This is an example. In a production environment, secure credentials should be used.
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
        HugeClient hugeClient = HugeClient.builder("http://localhost:8080",
                                                   "DEFAULT",
                                                   "hugegraph")
                                          .configUser("username", "password")
                                          // This is an example. In a production environment, secure credentials should be used.
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

#### 4.4 Run The Example

1. [Start HugeGraph Server](/docs/quickstart/hugegraph/hugegraph-server) and prepare a test graph named `hugegraph` in graphspace `DEFAULT`.
1. Set the Maven project's JDK to 17. In the selected example, replace the Server URL, graphspace, graph and credentials in `HugeClient.builder(...)`
   and `configUser(...)` with your settings. Omit `configUser(...)` if Server does not require authentication.
1. Run `SingleExample.main()` or `BatchExample.main()` in your IDE. Both examples create schema and graph data, print the results, and close the client.
   Use a test graph: existing schema or data can affect repeated runs.
{.steps}

#### 4.5 More Information About Client-API

See[Introduce basic API of HugeGraph-Client](/docs/clients/hugegraph-client).
