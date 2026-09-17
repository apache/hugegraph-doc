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

Gremlin Console connects to HugeGraph Server through WebSocket. The default configuration uses `WsAndHttpChannelizer`, which handles both WebSocket and HTTP requests, so there is no need to switch the Channelizer.

```yaml
# vim conf/gremlin-server.yaml
# ......
channelizer: org.apache.tinkerpop.gremlin.server.channel.WsAndHttpChannelizer
# ......
```

Confirm that `host` and `port` match the settings in `remote.yaml`, and then follow the [steps](/docs/quickstart/hugegraph/hugegraph-server) to start HugeGraph Server.

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

If the Server runs in auth mode, add the credentials to the same file:

```yaml
username: admin
password: pa
```

The `conf` directory also ships `remote-objects.yaml` and `gremlin-driver-settings.yaml`, which carry the same host, port, and serializer settings.

```groovy
gremlin> :remote connect tinkerpop.server conf/remote.yaml
==>Configured localhost/127.0.0.1:8182
```

Server-side graphs are bound under a graphspace-qualified name, so the graph `hugegraph` in graphspace `DEFAULT` is bound as `DEFAULT-hugegraph` and its traversal source as `__g_DEFAULT-hugegraph`. A bare `hugegraph` does not resolve on the Server, and `DEFAULT-hugegraph` is not a valid Groovy identifier, so a remote script reaches the traversal source through an alias. If the sample graph was preloaded when HugeGraph-Server started, a query looks like this:

```groovy
gremlin> import org.apache.tinkerpop.gremlin.driver.Cluster
gremlin> cluster = Cluster.open('conf/remote.yaml')
gremlin> client = cluster.connect().alias(['g': '__g_DEFAULT-hugegraph'])
gremlin> client.submit('g.V().count()').all().get()[0].object
==>6
gremlin> client.submit('g.V().toList().size()').all().get()[0].object
==>6
gremlin> client.close(); cluster.close()
```

> NOTE: In Client/Server mode, all operations related to the Server should be prefixed with `:> `. If not added, it indicates local console operations. A `:> ` script carries no alias, so it can only use names the Server itself has bound.

For more information on the use of Gremlin-Console, please refer to [Tinkerpop Official Website](http://tinkerpop.apache.org/docs/current/reference/)
