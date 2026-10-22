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

Gremlin Console connects to HugeGraph Server through WebSocket. Use the Console and `conf/remote.yaml` bundled with the same Server version.
Keep the serializer settings from that file; change only the address and, if authentication is enabled, credentials.
Older configuration files may reference serializer classes that no longer exist.

1. Prepare the connection configuration and start Server.

   Check the `host` and `port` in `conf/gremlin-server.yaml`. The default `WsAndHttpChannelizer` handles both WebSocket and HTTP requests;
   it does not need to be changed. In `conf/remote.yaml`, `hosts` must contain the Server address reachable from the Console,
   and `port` must match the Gremlin port (default `8182`, not the REST port `8080`).
   Start Server following the [quick start](/docs/quickstart/hugegraph/hugegraph-server).

   The current master configuration uses GraphBinary V1 with HugeGraph's type registry:

   ```yaml
   hosts: [localhost]
   port: 8182
   serializer:
     className: org.apache.tinkerpop.gremlin.util.ser.GraphBinaryMessageSerializerV1
     config:
       serializeResultToString: false
       builder: org.apache.hugegraph.io.HugeGraphTypeSerializerRegistryBuilder
       ioRegistries: [org.apache.hugegraph.io.HugeGraphIoRegistry]
   ```

   If Server requires authentication, add your actual credentials to the same file:

   ```yaml
   username: admin
   password: "replace-with-your-password"
   ```

   The bundled `remote-objects.yaml` and `gremlin-driver-settings.yaml` use the same serializer settings. Keep them aligned if you use them.

1. Start Console from the Server distribution directory and create a client with a traversal alias.

   ```bash
   ./bin/gremlin-console.sh
   ```

   Server binds the graph `hugegraph` in graphspace `DEFAULT` as `DEFAULT-hugegraph`, and its traversal source as `__g_DEFAULT-hugegraph`.
   Because hyphens are invalid in Groovy variable names, use `.alias(['g': '__g_DEFAULT-hugegraph'])` to map it to `g` when creating the driver client:

   ```groovy
   import org.apache.tinkerpop.gremlin.driver.Cluster
   cluster = Cluster.open('conf/remote.yaml')
   client = cluster.connect().alias(['g': '__g_DEFAULT-hugegraph'])
   ```

1. Submit queries through the client.

   ```groovy
   client.submit('g.V().count()').all().get()[0].object
   client.submit('g.V().toList().size()').all().get()[0].object
   ```

   Both return `6` if the sample graph was preloaded at Server startup (other graphs return their actual vertex count).
   When submitting scripts via `client.submit()`, no `:>` prefix is needed.

1. Close the client and cluster when finished.

   ```groovy
   client.close()
   cluster.close()
   ```
{.steps}

Alternatively, you can connect using Gremlin Console's built-in `:remote` command:

```groovy
:remote connect tinkerpop.server conf/remote.yaml
// Use :> as a prefix when submitting scripts through the Console remote connection.
:remote close
```

When connected with `:remote`, expressions prefixed with `:>` are sent to the remote Server, while normal expressions execute locally in Console.

For more information, see the [TinkerPop Gremlin Console reference](https://tinkerpop.apache.org/docs/current/reference/#gremlin-console).
