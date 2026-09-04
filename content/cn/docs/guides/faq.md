---
title: "FAQ"
linkTitle: "FAQ"
weight: 6
---

- 如何选择后端存储? 选 RocksDB 还是分布式存储?

  HugeGraph 支持多种部署模式，根据数据规模和场景选择：
  - **单机模式**：Server + RocksDB，适合开发测试和小于 1 TB 的数据
  - **分布式模式**：HugeGraph-PD + HugeGraph-Store（HStore），用于需要水平扩展和多副本的部署

  1.7.0 支持 RocksDB、HStore、HBase 和 Memory。Cassandra、ScyllaDB、MySQL、PostgreSQL 等旧后端需使用 1.5.x 或更早版本。

- 启动服务时提示：`xxx (core dumped) xxx`

  请先确认 JDK 版本不低于 Java 11。HugeGraph 1.7.0 不再支持 Java 8。

- 启动服务成功了，但是操作图时有类似于"无法连接到后端或连接未打开"的提示

  RocksDB、HBase 等本地持久化后端首次启动前需要使用 `init-store` 初始化。HStore 由 PD、Store 管理，不执行该脚本。

- 所有的后端在使用前都需要执行`init-store`吗，序列化的选择可以随意填写么?
  
  Memory 和 HStore 不执行 `init-store`；RocksDB、HBase 等本地持久化后端首次使用前需要初始化。序列化器必须与后端匹配，例如 RocksDB 使用 `binary`。

- 执行`init-store`报错：```Exception in thread "main" java.lang.UnsatisfiedLinkError: /tmp/librocksdbjni3226083071221514754.so: /usr/lib64/libstdc++.so.6: version `GLIBCXX_3.4.10' not found (required by /tmp/librocksdbjni3226083071221514754.so)```

  RocksDB需要 gcc 4.3.0 (GLIBCXX_3.4.10) 及以上版本

- `bin`目录下包含`start-hugegraph.sh`、`start-restserver.sh`和`start-gremlinserver.sh`三个似乎与启动有关的脚本，到底该使用哪个

  当前发布包只保留 `start-hugegraph.sh` 作为 Server 启动脚本。GremlinServer 和 REST Server 由同一进程启动。

- 配置了两个图，名字是`hugegraph`和`hugegraph1`，而启动服务的命令是`start-hugegraph.sh`，是只打开了`hugegraph`这个图吗

  脚本名称与图名无关。需要从 `graphs` 目录加载多个本地图时，在 `rest-server.properties` 中设置 `graph.load_from_local_config=true`；该选项的源码默认值是 `false`。

- 服务启动成功后，使用`curl`查询所有顶点时返回乱码

  服务端返回的批量顶点/边是压缩（gzip）过的，可以使用管道重定向至 `gunzip` 进行解压（`curl http://example | gunzip`），也可以用`Firefox`的`postman`或者`Chrome`浏览器的`restlet`插件发请求，会自动解压缩响应数据。

- 使用顶点Id通过`RESTful API`查询顶点时返回空，但是顶点确实是存在的

  检查顶点Id的类型，如果是字符串类型，`API`的`url`中的id部分需要加上双引号，数字类型则不用加。

- 已经根据需要给顶点Id加上了双引号，但是通过`RESTful API`查询顶点时仍然返回空
  
  检查顶点id中是否包含`+`、`空格`、`/`、`?`、`%`、`&`和`=`这些URL的保留字符，如果存在则需要进行编码。下表给出了编码值：
  
  ```
  特殊字符 | 编码值
  --------| ----
  +       | %2B
  空格     | %20
  /       | %2F
  ?       | %3F
  %       | %25
  #       | %23
  &       | %26
  =       | %3D
  ```
  
- 查询某一类别的顶点或边（`query by label`）时提示超时

  由于属于某一label的数据量可能比较多，请加上limit限制。

- 通过`RESTful API`操作图是可以的，但是发送`Gremlin`语句就报错：`Request Failed(500)`

  可能是`GremlinServer`的配置有误，检查`gremlin-server.yaml`的`host`、`port`是否与`rest-server.properties`的`gremlinserver.url`匹配，如不匹配则修改，然后重启服务。

- 使用`Loader`导数据出现`Socket Timeout`异常，然后导致`Loader`中断

  持续地导入数据会使`Server`的压力过大，然后导致有些请求超时。可以通过调整`Loader`的参数来适当缓解`Server`压力（如：重试次数，重试间隔，错误容忍数等），降低该问题出现频率。

- 如何删除图中的全部数据

  管理员可调用 `DELETE /graphspaces/{graphspace}/graphs/{graph}/clear`。请求必须携带源码要求的 `confirm_message`，具体格式见 [Graph API](../clients/restful-api/graphs)。该操作会清除 schema、顶点、边和索引。

- 清空了数据库，并且执行了`init-store`，但是添加`schema`时提示"xxx has existed"

  `HugeGraphServer`内是有缓存的，清空数据库的同时是需要重启`Server`的，否则残留的缓存会产生不一致。

- 插入顶点或边的过程中报错：`Id max length is 128, but got xxx {yyy}` 或 `Big id max length is 32768, but got xxx`

  为了保证查询性能，目前的后端存储对id列的长度做了限制，顶点id不能超过128字节，边id长度不能超过32768字节，索引id不能超过128字节。

- 是否支持嵌套属性，如果不支持，是否有什么替代方案

  嵌套属性目前暂不支持。替代方案：可以把嵌套属性作为单独的顶点拿出来，然后用边连接起来。

- 一个`EdgeLabel`是否可以连接多对`VertexLabel`，比如"投资"关系，可以是"个人"投资"企业"，也可以是"企业"投资"企业"

  一个`EdgeLabel`不支持连接多对`VertexLabel`，需要用户将`EdgeLabel`拆分得更细一点，如："个人投资"，"企业投资"。

- 通过`RestAPI`发送请求时提示`HTTP 415 Unsupported Media Type`

  请求头中需要指定`Content-Type:application/json`

其他问题可以在对应项目的 issue 区搜索，例如 [Server-Issues](https://github.com/apache/hugegraph/issues) / [Loader Issues](https://github.com/apache/hugegraph-toolchain/issues)
