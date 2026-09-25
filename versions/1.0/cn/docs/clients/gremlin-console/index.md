# Gremlin-Console

LLMS 索引： [llms.txt](/versions/1.0/cn/llms.txt)

---

Gremlin-Console是由Tinkerpop自己开发的一个交互式客户端，用户可以使用该客户端对Graph做各种操作，主要有两种使用模式：

- 单机离线调用模式；
- Client/Server请求模式；

### 1 单机离线调用模式

由于lib目录下已经包含了HugeCore的jar包，且HugeGraph已经作为插件注册到Console中，用户可以直接写groovy脚本调用HugeGraph-Core的代码，然后交由Gremlin-Console内的解析引擎执行，就能在不启动Server的情况下操作图。

这种模式便于用户快速上手体验，但是不适合大量数据插入和查询的场景。下面给一个示例：

在script目录下有一个示例脚本：example.groovy

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

其实这一段groovy脚本几乎就是Java代码，不同之处仅在于变量的定义可以不写类型声明，以及每一行末尾的分号可以去掉。

> g.V() 是获取所有的顶点，g.E() 是获取所有的边，toList() 是把结果存到一个 List 中，参考[TinkerPop Terminal Steps](http://tinkerpop.apache.org/docs/current/reference/#terminal-steps)。

下面进入gremlin-console，并传入该脚本令其执行：

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

可以看到，插入了6个顶点、6条边，并查询出来了。进入console之后，还可继续输入groovy语句对图做操作：

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

更多的Gremlin语句请参考[Tinkerpop官网](http://tinkerpop.apache.org/docs/current/reference/)

### 2 Client/Server请求模式

因为Gremlin-Console只能通过WebSocket连接HugeGraph-Server，默认HugeGraph-Server是对外提供HTTP连接的，所以先修改gremlin-server的配置。

*注意：将连接方式修改为WebSocket后，HugeGraph-Client、HugeGraph-Loader、HugeGraph-Studio等配套工具都不能使用了。*

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

将`channelizer: org.apache.tinkerpop.gremlin.server.channel.HttpChannelizer`修改成`channelizer: org.apache.tinkerpop.gremlin.server.channel.WebSocketChannelizer`或直接注释，然后按照步骤启动Server。

然后进入gremlin-console

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

连接server，需在配置文件中指定连接参数，在conf目录下有一个默认的remote.yaml

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

连接成功之后，在console的上下文中能使用的变量只有hugegraph和hugegraph1两个图对象（在gremlin-server.yaml中配置），如果想拥有更多的变量，可以在`scripts/empty-sample.groovy`中添加，如:

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

这样在console中便可以直接使用schema和g这两个对象，做元数据的管理和图的查询了。

不定义了也没关系，因为所有的对象都可以通过graph获得，例如：

```groovy
gremlin> :> hugegraph.traversal().V()
==>v[2:ripple]
==>v[1:vadas]
==>v[1:peter]
==>v[1:josh]
==>v[1:marko]
==>v[2:lop]
```

在Client/Server模式下，所有跟Server有关的操作都要加上`:> `，如果不加，表示在console本地操作。

还可以把多条语句放在一个字符串变量中，然后一次性发给server：

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

更多关于gremlin-console的使用，请参考[Tinkerpop官网](http://tinkerpop.apache.org/docs/current/reference/)
