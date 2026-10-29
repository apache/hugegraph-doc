---
title: "Gremlin-Console"
linkTitle: "Gremlin Console"
weight: 3
---

Gremlin-Console 是 TinkerPop 的交互式客户端，支持离线操作图，也可以连接 Server 提交查询。

- 单机离线调用模式
- Client/Server 请求模式

Gremlin-Console 适合学习和调试。生产应用建议使用对应语言的客户端。

### 1 单机离线调用模式

Server 发行包内的 Console 已包含 HugeGraph-Core JAR 和插件，可以直接执行 Groovy 脚本操作图，无需启动 Server。

先在 `hugegraph.properties` 中配置 Memory 后端。其他后端可能需要额外初始化。

```properties
backend=memory
serializer=text
```

然后运行示例脚本。

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

脚本执行后，可以继续输入 Gremlin 语句。

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

Gremlin-Console 通过 WebSocket 连接 HugeGraph-Server。使用与 Server 同版本发行包中的 Console 和 `conf/remote.yaml`，
保留文件中的序列化器配置，只修改地址，以及启用鉴权时需要的凭据。旧版配置可能引用已经不存在的序列化器类。

1. 准备连接配置并启动 Server。

   检查 `conf/gremlin-server.yaml` 中的 `host`、`port`。默认的 `WsAndHttpChannelizer` 同时处理 WebSocket 和 HTTP 请求，无需修改。
   `conf/remote.yaml` 中的 `hosts` 应填写 Console 能访问的 Server 地址，`port` 应与 Gremlin 端口一致（默认为 `8182`，不是 REST 端口 `8080`）。
   按照[快速上手](/cn/docs/quickstart/hugegraph/hugegraph-server/)启动 Server。

   当前 master 配置使用 GraphBinary V1 和 HugeGraph 类型注册器。

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

   如果 Server 开启了鉴权，在同一个文件中填写实际凭据。

   ```yaml
   username: admin
   password: "replace-with-your-password"
   ```

   随包的 `remote-objects.yaml` 和 `gremlin-driver-settings.yaml` 使用相同的序列化器配置；使用这些文件时也要保持一致。

1. 从 Server 发行包目录启动 Console，并创建带 traversal 别名的客户端。

   ```bash
   ./bin/gremlin-console.sh
   ```

   Server 端将默认图空间下的图绑定为 `DEFAULT-hugegraph`，其 traversal source 绑定为 `__g_DEFAULT-hugegraph`。
   由于连字符 `-` 在 Groovy 中不能直接用作变量名，通过 Java Driver 连接时，使用 `.alias(['g': '__g_DEFAULT-hugegraph'])` 将其映射为 `g`。

   ```groovy
   import org.apache.tinkerpop.gremlin.driver.Cluster
   cluster = Cluster.open('conf/remote.yaml')
   client = cluster.connect().alias(['g': '__g_DEFAULT-hugegraph'])
   ```

1. 通过客户端提交查询。

   ```groovy
   client.submit('g.V().count()').all().get()[0].object
   client.submit('g.V().toList().size()').all().get()[0].object
   ```

   若启动 Server 时预加载了示例图，两条查询均返回 `6`（其他图返回其实际顶点数）。
   通过 Driver 的 `client.submit()` 提交脚本时，无需在语句前加 `:>` 前缀。

1. 使用结束后关闭客户端和集群连接。

   ```groovy
   client.close()
   cluster.close()
   ```
{.steps}

此外，也可以使用 Gremlin Console 内置的 `:remote` 命令连接：

```groovy
:remote connect tinkerpop.server conf/remote.yaml
// 通过 Console 远程连接提交脚本时，前缀使用 :>
:remote close
```

使用 `:remote` 连接时，以 `:>` 开头的语句会被发送至远端 Server 执行，普通语句则在 Console 本地执行。

更多用法见 [TinkerPop Gremlin Console 参考](https://tinkerpop.apache.org/docs/current/reference/#gremlin-console)。
