---
title: "Gremlin-Console"
linkTitle: "Gremlin Console"
weight: 3
---

Gremlin-Console 是由 Tinkerpop 自己开发的一个交互式客户端，用户可以使用该客户端对 Graph 做各种操作，主要有两种使用模式：

- 单机离线调用模式
- Client/Server 请求模式

**注：Gremlin-Console 只是便于用户快速上手体验，不建议在生产环境中使用。**

### 1 单机离线调用模式

由于 lib 目录下已经包含了 HugeCore 的 jar 包，且 HugeGraph-Server 已经作为插件注册到 Gremlin-Console 中，用户可以直接写 Groovy 脚本调用 HugeGraph-Core 的代码，然后交由 Gremlin-Console 内的解析引擎执行，就能在**不启动** Server 的情况下操作图。

这里提供一个示例，首先修改 `hugegraph.properties` 配置使用 Memory 后端 (使用其他后端可能会出现一些初始化问题)：

```properties
backend=memory
serializer=text
```

然后输入下述命令：

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

> 这里的 `--` 会被 getopts 解析为最后一个 option，这样后面的 options 就可以传入 Gremlin-Console 进行处理了。`-i` 代表 `Execute the specified script and leave the console open on completion`，更多的选项可以参考 Gremlin-Console 的[源代码](https://github.com/apache/tinkerpop/blob/3.5.1/gremlin-console/src/main/groovy/org/apache/tinkerpop/gremlin/console/Console.groovy#L483)。

其中 [`example.groovy`](https://github.com/apache/hugegraph/blob/master/hugegraph-server/hugegraph-dist/src/assembly/static/scripts/example.groovy) 是 scripts 目录下的一个示例脚本，该脚本插入了一些数据，并在最后查询图中顶点和边的数量。

此时还可以继续输入 Gremlin 语句对图进行操作：

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

更多的 Gremlin 语句请参考 [Tinkerpop 官网](http://tinkerpop.apache.org/docs/current/reference/)。

### 2 Client/Server 请求模式

因为 Gremlin-Console 只能通过 WebSocket 连接 HugeGraph-Server，默认 HugeGraph-Server 是对外提供 HTTP 连接的，所以先修改 gremlin-server 的配置。

**注意：将连接方式修改为 WebSocket 后，HugeGraph-Client、HugeGraph-Loader、HugeGraph-Hubble 等配套工具都不能使用了。**

```yaml
# vim conf/gremlin-server.yaml
# ......
# If you want to start gremlin-server for gremlin-console (web-socket),
# please change `HttpChannelizer` to `WebSocketChannelizer` or comment this line.
channelizer: org.apache.tinkerpop.gremlin.server.channel.HttpChannelizer
# ......
```

将 `channelizer: org.apache.tinkerpop.gremlin.server.channel.HttpChannelizer` 修改成 `channelizer: org.apache.tinkerpop.gremlin.server.channel.WebSocketChannelizer` 或直接注释，然后按照[步骤](/cn/docs/quickstart/hugegraph/hugegraph-server/)启动 HugeGraph-Server。

下面进入 Gremlin-Console：

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

连接 Server，需在配置文件中指定连接参数，在 conf 目录下有一个默认的 `remote.yaml`：

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

连接成功之后，如果在启动 HugeGraph-Server 的过程中导入了示例图，就可以在 Gremlin-Console 中直接进行查询：

```groovy
gremlin> :> hugegraph.traversal().V()
==>[id:2:lop,label:software,type:vertex,properties:[name:lop,lang:java,price:328]]
==>[id:1:josh,label:person,type:vertex,properties:[name:josh,age:32,city:Beijing]]
==>[id:1:marko,label:person,type:vertex,properties:[name:marko,age:29,city:Beijing]]
==>[id:1:peter,label:person,type:vertex,properties:[name:peter,age:35,city:Shanghai]]
==>[id:1:vadas,label:person,type:vertex,properties:[name:vadas,age:27,city:Hongkong]]
==>[id:2:ripple,label:software,type:vertex,properties:[name:ripple,lang:java,price:199]]
```

> 注意：在 Client/Server 模式下，所有和 Server 有关的操作都要加上 `:> `，如果不加，表示在 console 本地操作。

还可以把多条语句放在一个字符串变量中，然后一次性发给 Server：

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

更多关于 Gremlin-Console 的使用，请参考 [Tinkerpop 官网](http://tinkerpop.apache.org/docs/current/reference/)。
