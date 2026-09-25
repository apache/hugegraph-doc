# Gremlin-Console

LLMS index: [llms.txt](/versions/1.0/llms.txt)

---

Gremlin-Console is an interactive client developed by TinkerPop. Users can use this client to perform various operations on Graph. There are two main usage modes:

- Stand-alone offline mode;
- Client/Server mode;

### 1 Stand-alone offline mode

Since the lib directory already contains the HugeCore jar package, and HugeGraph has been registered in the Console as a plug-in, the users can write a groovy script directly to call the code of HugeGraph-Core, and then hand it over to the parsing engine in Gremlin-Console for execution. As a result, the users can operate the graph without starting the Server.

This mode is convenient for users to get started quickly, but it is not suitable for scenarios where a large amount of data is inserted and queried. Here is an example:

There is a sample script in the script directory：example.groovy

```groovy
import com.baidu.hugegraph.HugeFactory
import com.baidu.hugegraph.dist.RegisterUtil
import org.apache.tinkerpop.gremlin.structure.T

RegisterUtil.registerCassandra();
RegisterUtil.registerScyllaDB();

conf = "conf/hugegraph.properties"
graph = HugeFactory.open(conf);
schema = graph.schema();

schema.propertyKey("name").asText().ifNotExist().create();
schema.propertyKey("age").asInt().ifNotExist().create();
schema.propertyKey("city").asText().ifNotExist().create();
schema.propertyKey("weight").asDouble().ifNotExist().create();
schema.propertyKey("lang").asText().ifNotExist().create();
schema.propertyKey("date").asText().ifNotExist().create();
schema.propertyKey("price").asInt().ifNotExist().create();

schema.vertexLabel("person").properties("name", "age", "city").primaryKeys("name").ifNotExist().create();
schema.vertexLabel("software").properties("name", "lang", "price").primaryKeys("name").ifNotExist().create();
schema.indexLabel("personByName").onV("person").by("name").secondary().ifNotExist().create();
schema.indexLabel("personByCity").onV("person").by("city").secondary().ifNotExist().create();
schema.indexLabel("personByAgeAndCity").onV("person").by("age", "city").secondary().ifNotExist().create();
schema.indexLabel("softwareByPrice").onV("software").by("price").range().ifNotExist().create();
schema.edgeLabel("knows").sourceLabel("person").targetLabel("person").properties("date", "weight").ifNotExist().create();
schema.edgeLabel("created").sourceLabel("person").targetLabel("software").properties("date", "weight").ifNotExist().create();
schema.indexLabel("createdByDate").onE("created").by("date").secondary().ifNotExist().create();
schema.indexLabel("createdByWeight").onE("created").by("weight").range().ifNotExist().create();
schema.indexLabel("knowsByWeight").onE("knows").by("weight").range().ifNotExist().create();

marko = graph.addVertex(T.label, "person", "name", "marko", "age", 29, "city", "Beijing");
vadas = graph.addVertex(T.label, "person", "name", "vadas", "age", 27, "city", "Hongkong");
lop = graph.addVertex(T.label, "software", "name", "lop", "lang", "java", "price", 328);
josh = graph.addVertex(T.label, "person", "name", "josh", "age", 32, "city", "Beijing");
ripple = graph.addVertex(T.label, "software", "name", "ripple", "lang", "java", "price", 199);
peter = graph.addVertex(T.label, "person", "name", "peter", "age", 35, "city", "Shanghai");

marko.addEdge("knows", vadas, "date", "20160110", "weight", 0.5);
marko.addEdge("knows", josh, "date", "20130220", "weight", 1.0);
marko.addEdge("created", lop, "date", "20171210", "weight", 0.4);
josh.addEdge("created", lop, "date", "20091111", "weight", 0.4);
josh.addEdge("created", ripple, "date", "20171210", "weight", 1.0);
peter.addEdge("created", lop, "date", "20170324", "weight", 0.2);

graph.tx().commit();

g = graph.traversal();

System.out.println(">>>> query all vertices: size=" + g.V().toList().size());
System.out.println(">>>> query all edges: size=" + g.E().toList().size());
```

In fact, this groovy script is almost Java code, the only difference is that the variable definition can be written without the type declaration, and the semicolon at the end of each line can be removed.

> `g.V()` is to get all the vertices, `g.E()` is to get all the edges, `toList()` is to store the result in a List, refer to[TinkerPop Terminal Steps](http://tinkerpop.apache.org/docs/current/reference/#terminal-steps)。

Enter the gremlin-console below and pass in the script to execute it:

```bash
bin/gremlin-console.sh scripts/example.groovy
objc[5038]: Class JavaLaunchHelper is implemented in both /Library/Java/JavaVirtualMachines/jdk1.8.0_121.jdk/Contents/Home/bin/java (0x10137a4c0) and /Library/Java/JavaVirtualMachines/jdk1.8.0_121.jdk/Contents/Home/jre/lib/libinstrument.dylib (0x102bbb4e0). One of the two will be used. Which one is undefined.

         \,,,/
         (o o)
-----oOOo-(3)-oOOo-----
plugin activated: com.baidu.hugegraph
plugin activated: tinkerpop.server
plugin activated: tinkerpop.utilities
plugin activated: tinkerpop.tinkergraph
2018-01-15 14:36:19 7516  [main] [WARN ] com.baidu.hugegraph.config.HugeConfig [] - The config option 'rocksdb.data_path' is redundant, please ensure it has been registered
2018-01-15 14:36:19 7523  [main] [WARN ] com.baidu.hugegraph.config.HugeConfig [] - The config option 'rocksdb.wal_path' is redundant, please ensure it has been registered
2018-01-15 14:36:19 7604  [main] [INFO ] com.baidu.hugegraph.HugeGraph [] - Opening backend store 'cassandra' for graph 'hugegraph'
>>>> query all vertices: size=6
>>>> query all edges: size=6
```

As you can see, 6 vertices and 6 edges are inserted and queried. After entering the console, you can continue to enter groovy statements to operate on the graph:

```groovy
gremlin> g.V()
==>v[2:ripple]
==>v[1:vadas]
==>v[1:peter]
==>v[1:josh]
==>v[1:marko]
==>v[2:lop]
gremlin> g.E()
==>e[S1:josh>2>>S2:ripple][1:josh-created->2:ripple]
==>e[S1:marko>1>20160110>S1:vadas][1:marko-knows->1:vadas]
==>e[S1:peter>2>>S2:lop][1:peter-created->2:lop]
==>e[S1:josh>2>>S2:lop][1:josh-created->2:lop]
==>e[S1:marko>1>20130220>S1:josh][1:marko-knows->1:josh]
==>e[S1:marko>2>>S2:lop][1:marko-created->2:lop]
```

For more Gremlin statements, please refer to [Tinkerpop Official Website](http://tinkerpop.apache.org/docs/current/reference/)

### 2 Client/Server mode

Because Gremlin-Console can only connect to HugeGraph-Server through WebSocket, HugeGraph-Server provides HTTP connections by default, so modify the configuration of gremlin-server first.

*Note: After changing the connection method to WebSocket, HugeGraph-Client, HugeGraph-Loader, HugeGraph-Studio and other supporting tools cannot be used.*

```yaml
# vim conf/gremlin-server.yaml
host: 127.0.0.1
port: 8182
scriptEvaluationTimeout: 30000
# If you want to start gremlin-server for gremlin-console(web-socket),
# please change `HttpChannelizer` to `WebSocketChannelizer` or comment this line.
channelizer: org.apache.tinkerpop.gremlin.server.channel.HttpChannelizer
graphs: {
  hugegraph: conf/hugegraph.properties,
  hugegraph1: conf/hugegraph1.properties
}
plugins:
  - com.baidu.hugegraph
scriptEngines: {
  gremlin-groovy: {
    imports: [java.lang.Math],
    staticImports: [java.lang.Math.PI],
    scripts: [scripts/empty-sample.groovy]
  }
}
serializers:
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GryoLiteMessageSerializerV1d0,
      config: {
        serializeResultToString: false,
        ioRegistries: [com.baidu.hugegraph.io.HugeGraphIoRegistry]
      }
    }
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GryoMessageSerializerV1d0,
      config: {
        serializeResultToString: true,
        ioRegistries: [com.baidu.hugegraph.io.HugeGraphIoRegistry]
      }
    }
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphSONMessageSerializerGremlinV1d0,
      config: {
        serializeResultToString: false,
        ioRegistries: [com.baidu.hugegraph.io.HugeGraphIoRegistry]
      }
    }
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphSONMessageSerializerGremlinV2d0,
      config: {
        serializeResultToString: false,
        ioRegistries: [com.baidu.hugegraph.io.HugeGraphIoRegistry]
      }
    }
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphSONMessageSerializerV1d0,
      config: {
        serializeResultToString: false,
        ioRegistries: [com.baidu.hugegraph.io.HugeGraphIoRegistry]
      }
    }
metrics: {
  consoleReporter: {enabled: false, interval: 180000},
  csvReporter: {enabled: true, interval: 180000, fileName: /tmp/gremlin-server-metrics.csv},
  jmxReporter: {enabled: false},
  slf4jReporter: {enabled: false, interval: 180000},
  gangliaReporter: {enabled: false, interval: 180000, addressingMode: MULTICAST},
  graphiteReporter: {enabled: false, interval: 180000}
}
maxInitialLineLength: 4096
maxHeaderSize: 8192
maxChunkSize: 8192
maxContentLength: 65536
maxAccumulationBufferComponents: 1024
resultIterationBatchSize: 64
writeBufferLowWaterMark: 32768
writeBufferHighWaterMark: 65536
ssl: {
  enabled: false
}
```

Modify `channelizer: org.apache.tinkerpop.gremlin.server.channel.HttpChannelizer` to `channelizer: org.apache.tinkerpop.gremlin.server.channel.WebSocketChannelizer` or comment directly, and then follow the steps to start the Server.

Then enter gremlin-console

```bash
bin/gremlin-console.sh 
objc[5761]: Class JavaLaunchHelper is implemented in both /Library/Java/JavaVirtualMachines/jdk1.8.0_121.jdk/Contents/Home/bin/java (0x10ec584c0) and /Library/Java/JavaVirtualMachines/jdk1.8.0_121.jdk/Contents/Home/jre/lib/libinstrument.dylib (0x10ecdc4e0). One of the two will be used. Which one is undefined.

         \,,,/
         (o o)
-----oOOo-(3)-oOOo-----
plugin activated: com.baidu.hugegraph
plugin activated: tinkerpop.server
plugin activated: tinkerpop.utilities
plugin activated: tinkerpop.tinkergraph
```

To connect to the server, you need to specify the connection parameters in the configuration file, and there is a default remote.yaml file in the conf directory

```yaml
# cat conf/remote.yaml
hosts: [localhost]
port: 8182
serializer: {
  className: org.apache.tinkerpop.gremlin.driver.ser.GryoMessageSerializerV1d0,
  config: {
    serializeResultToString: true,
    ioRegistries: [com.baidu.hugegraph.io.HugeGraphIoRegistry]
  }
}
```

```groovy
gremlin> :remote connect tinkerpop.server conf/remote.yaml
2018-01-15 15:30:31 11528 [main] [INFO ] org.apache.tinkerpop.gremlin.driver.Connection [] - Created new connection for ws://localhost:8182/gremlin
2018-01-15 15:30:31 11538 [main] [INFO ] org.apache.tinkerpop.gremlin.driver.Connection [] - Created new connection for ws://localhost:8182/gremlin
2018-01-15 15:30:31 11538 [main] [INFO ] org.apache.tinkerpop.gremlin.driver.ConnectionPool [] - Opening connection pool on Host{address=localhost/127.0.0.1:8182, hostUri=ws://localhost:8182/gremlin} with core size of 2
==>Configured localhost/127.0.0.1:8182
```

After the connection is successful, the only variables that can be used in the context of the console are two graph objects, hugegraph and hugegraph1 (configured in gremlin-server.yaml), and if you want to have more variables, you can add them in `scripts/empty-sample.groovy`, such as:

```groovy
import org.apache.tinkerpop.gremlin.server.util.LifeCycleHook

// an init script that returns a Map allows explicit setting of global bindings.
def globals = [:]

// defines a sample LifeCycleHook that prints some output to the Gremlin Server console.
// note that the name of the key in the "global" map is unimportant.
globals << [hook: [
        onStartUp : { ctx ->
            ctx.logger.info("Executed once at startup of Gremlin Server.")
        },
        onShutDown: { ctx ->
            ctx.logger.info("Executed once at shutdown of Gremlin Server.")
        }
] as LifeCycleHook]

// define schema manger for hugegraph
schema = hugegraph.schema()
// define the default TraversalSource to bind queries to - this one will be named "g".
g = hugegraph.traversal()
```

In this way, the two objects `schema` and `g` can be directly used in the console for metadata management and graph query.

It doesn't matter if it is not defined, because all objects are available through the graph, for example:

```groovy
gremlin> :> hugegraph.traversal().V()
==>v[2:ripple]
==>v[1:vadas]
==>v[1:peter]
==>v[1:josh]
==>v[1:marko]
==>v[2:lop]
```

In Client/Server mode, all operations related to Server must be added with `:> `, if not, it means local operation in the console.

You can also put multiple statements in a string variable and send them to the server at once:

```groovy
gremlin> script = """
graph = hugegraph;
marko = graph.addVertex(T.label, "person", "name", "marko", "age", 29, "city", "Beijing");
vadas = graph.addVertex(T.label, "person", "name", "vadas", "age", 27, "city", "Hongkong");
lop = graph.addVertex(T.label, "software", "name", "lop", "lang", "java", "price", 328);
josh = graph.addVertex(T.label, "person", "name", "josh", "age", 32, "city", "Beijing");
ripple = graph.addVertex(T.label, "software", "name", "ripple", "lang", "java", "price", 199);
peter = graph.addVertex(T.label, "person", "name", "peter", "age", 35, "city", "Shanghai");

marko.addEdge("knows", vadas, "date", "20160110", "weight", 0.5);
marko.addEdge("knows", josh, "date", "20130220", "weight", 1.0);
marko.addEdge("created", lop, "date", "20171210", "weight", 0.4);
josh.addEdge("created", lop, "date", "20091111", "weight", 0.4);
josh.addEdge("created", ripple, "date", "20171210", "weight", 1.0);
peter.addEdge("created", lop, "date", "20170324", "weight", 0.2);

graph.tx().commit();

g = graph.traversal();
g.V().toList().size();
"""

gremlin> :> @script
==>6
```

For more information on the use of gremlin-console, please refer to [Tinkerpop Official Website](http://tinkerpop.apache.org/docs/current/reference/)
