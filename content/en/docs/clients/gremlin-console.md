---
title: "Gremlin-Console"
linkTitle: "Gremlin Console"
weight: 3
---

Gremlin-Console is an interactive client developed by TinkerPop. Users can use this client to perform various operations on Graph. There are two main usage modes:

- Stand-alone offline mode
- Client/Server mode

**Note: Gremlin-Console is only for users to quickly get started and experience, it is not recommended for use in production environments.**

### 1 Stand-alone offline mode

Since the lib directory already contains the HugeCore jar package, and HugeGraph-Server has been registered in the Console as a plug-in, the users can write a groovy script directly to call the code of HugeGraph-Core, and then hand it over to the parsing engine in Gremlin-Console for execution. As a result, the users can operate the graph **without** starting the Server.

Here is an example, first modify the `hugegraph.properties` configuration to use the Memory backend (using other backends may encounter some initialization issues):

```properties
backend=memory
serializer=text
```

Then enter the following command:

```bash
> ./bin/gremlin-console.sh -- -i scripts/example.groovy

         \,,,/
         (o o)
-----oOOo-(3)-oOOo-----
plugin activated: HugeGraph
plugin activated: tinkerpop.server
plugin activated: tinkerpop.utilities
plugin activated: tinkerpop.tinkergraph
main dict load finished, time elapsed 644 ms
model load finished, time elapsed 35 ms.
>>>> query all vertices: size=6
>>>> query all edges: size=6
gremlin> 
```

> The `--` here will be parsed by getopts as the last option, allowing the subsequent options to be passed to Gremlin-Console for processing. `-i` represents `Execute the specified script and leave the console open on completion`. For more options, you can refer to the [source code](https://github.com/apache/tinkerpop/blob/3.5.1/gremlin-console/src/main/groovy/org/apache/tinkerpop/gremlin/console/Console.groovy#L483) of Gremlin-Console.

[`example.groovy`](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/scripts/example.groovy) is an example script under the `scripts` directory. This script inserts some data and queries the number of vertices and edges in the graph at the end.

You can continue to enter Gremlin statements to operate on the graph:

```groovy
gremlin> g.V()
==>v[2:lop]
==>v[1:josh]
==>v[1:marko]
==>v[1:peter]
==>v[1:vadas]
==>v[2:ripple]
gremlin> g.E()
==>e[S1:josh>2>>S2:lop][1:josh-created->2:lop]
==>e[S1:josh>2>>S2:ripple][1:josh-created->2:ripple]
==>e[S1:marko>1>>S1:josh][1:marko-knows->1:josh]
==>e[S1:marko>1>>S1:vadas][1:marko-knows->1:vadas]
==>e[S1:marko>2>>S2:lop][1:marko-created->2:lop]
==>e[S1:peter>2>>S2:lop][1:peter-created->2:lop]
gremlin> 
```

For more Gremlin statements, please refer to [Tinkerpop Official Website](http://tinkerpop.apache.org/docs/current/reference/)

### 2 Client/Server mode

Because Gremlin-Console can only connect to HugeGraph-Server through WebSocket, HugeGraph-Server provides HTTP connections by default, so modify the configuration of gremlin-server first.

**NOTE: After changing the connection method to WebSocket, HugeGraph-Client, HugeGraph-Loader, HugeGraph-Hubble and other supporting tools cannot be used.**

```yaml
# vim conf/gremlin-server.yaml
# ......
# If you want to start gremlin-server for gremlin-console (web-socket),
# please change `HttpChannelizer` to `WebSocketChannelizer` or comment this line.
channelizer: org.apache.tinkerpop.gremlin.server.channel.HttpChannelizer
# ......
```

Modify `channelizer: org.apache.tinkerpop.gremlin.server.channel.HttpChannelizer` to `channelizer: org.apache.tinkerpop.gremlin.server.channel.WebSocketChannelizer` or comment directly, and then follow the [steps](/docs/quickstart/hugegraph/hugegraph-server) to start the Server.

Then enter Gremlin-Console:

```bash
> ./bin/gremlin-console.sh

         \,,,/
         (o o)
-----oOOo-(3)-oOOo-----
plugin activated: HugeGraph
plugin activated: tinkerpop.server
plugin activated: tinkerpop.utilities
plugin activated: tinkerpop.tinkergraph
```

To connect to the server, you need to specify the connection parameters in the configuration file, and there is a default `remote.yaml` file in the conf directory

```yaml
# cat conf/remote.yaml
hosts: [localhost]
port: 8182
serializer: {
  className: org.apache.tinkerpop.gremlin.driver.ser.GraphSONMessageSerializerV1d0,
  config: {
    serializeResultToString: false,
    ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]
  }
}
```

```groovy
gremlin> :remote connect tinkerpop.server conf/remote.yaml
==>Configured localhost/127.0.0.1:8182
```

After a successful connection, if the sample graph `example.groovy` is imported during the startup of HugeGraph-Server, you can directly perform queries in the console.

```groovy
gremlin> :> hugegraph.traversal().V()
==>[id:2:lop,label:software,type:vertex,properties:[name:lop,lang:java,price:328]]
==>[id:1:josh,label:person,type:vertex,properties:[name:josh,age:32,city:Beijing]]
==>[id:1:marko,label:person,type:vertex,properties:[name:marko,age:29,city:Beijing]]
==>[id:1:peter,label:person,type:vertex,properties:[name:peter,age:35,city:Shanghai]]
==>[id:1:vadas,label:person,type:vertex,properties:[name:vadas,age:27,city:Hongkong]]
==>[id:2:ripple,label:software,type:vertex,properties:[name:ripple,lang:java,price:199]]
```

> NOTE: In Client/Server mode, all operations related to the Server should be prefixed with `:> `. If not added, it indicates local console operations.

You can also put multiple statements in a single string variable and send them to the Server at once:

```groovy
gremlin> script = """
......1> graph = hugegraph;
......2> g = graph.traversal();
......3> g.V().toList().size();
......4> """
==>
graph = hugegraph;
g = graph.traversal();
g.V().toList().size();

gremlin> :> @script
==>6
gremlin> 
```

For more information on the use of Gremlin-Console, please refer to [Tinkerpop Official Website](http://tinkerpop.apache.org/docs/current/reference/)
