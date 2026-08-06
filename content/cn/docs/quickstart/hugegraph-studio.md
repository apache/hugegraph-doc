---
title: "HugeGraph-Studio Quick Start"
linkTitle: "(Deprecated) Display with HugeGraph-Studio"
draft: true
weight: 5
---

> Note: Studio 已经停止维护, 不再更新, 请转向使用 hubble, 感谢理解

### 1 HugeGraph-Studio概述 (Deprecated)

HugeGraph-Studio是HugeGraph的前端展示工具，是基于Web的图形化IDE环境。
通过HugeGraph-Studio，用户可以执行Gremlin语句，并及时获得图形化的展示结果。
功能包括：

- 图数据的输入
- 图数据的展示
- 图数据的分析

> 注意：HugeGraph-Studio需要依赖HugeGraph-Server，在安装和使用HugeGraph-Studio之前，请通过jps命令检查HugeGraphServer服务是否已经启动，如果没有启动，请参考[HugeGraph-Server安装配置](/docs/quickstart/hugegraph/hugegraph-server)启动HugeGraphServer。

### 2 安装和运行HugeGraph-Studio

有两种方式可以获取HugeGraph-Studio：

- 下载源码包编译安装
- 下载二进制tar包

#### 2.1 下载源码编译生成tar包

下载HugeGraph-Studio源码包

```bash
$ git clone https://github.com/hugegraph/hugegraph-studio.git
```

编译生成tar包:

```bash
$ cd hugegraph-studio
$ mvn package -DskipTests
```

执行结果如下：

```bash
[INFO] ------------------------------------------------------------------------
[INFO] Reactor Summary:
[INFO]
[INFO] hugegraph-studio ................................... SUCCESS [  0.735 s]
[INFO] studio-server: Embed tomcat server ................. SUCCESS [  3.825 s]
[INFO] studio-api: RESTful api for hugegraph-studio ....... SUCCESS [  5.918 s]
[INFO] studio-dist: Tar and Distribute Archives ........... SUCCESS [ 48.349 s]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 59.055 s
[INFO] Finished at: 2017-07-27T17:23:05+08:00
[INFO] Final Memory: 57M/794M
[INFO] ------------------------------------------------------------------------
```

执行成功后,在hugegraph-studio目录下生成hugegraph-studio-${version}文件夹以及hugegraph-studio-${version}.tar.gz文件，即为编译生成的tar包。

#### 2.2 下载二进制tar包

可以从以下地址下载:

```bash
wget https://github.com/hugegraph/hugegraph-studio/releases/download/v${version}/hugegraph-studio-${version}.tar.gz
```

下载完成后解压缩：

```bash
$ tar zxvf hugegraph-studio-${version}.tar.gz
```

### 3 启动HugeGraph-Studio

修改配置文件：

```bash
$ cd hugegraph-studio-${version}
$ vim conf/hugegraph-studio.properties
```

- 将配置项`studio.server.host`的值`localhost`修改成机器名或 IP，这是 HugeGraphStudio 对外提供服务的`host`，如果只需要本地访问则保持不变即可；
- 将配置项`studio.server.port`的值`8088`修改成想要的端口，这是 HugeGraphStudio 对外提供服务的`port`；
- 将配置项`graph.server.host`的值`localhost`修改成 HugeGraphServer 的`host`，HugeGraphStudio 通过此项和`graph.server.port`与 HugeGraphServer 建立连接；
- 将配置项`graph.server.port`的值`8080`修改成 HugeGraphServer 的`port`，HugeGraphStudio 通过`graph.server.host`和此项与 HugeGraphServer 建立连接；
- 将配置项`graph.name`的值`hugegraph`修改成要连接的 HugeGraphServer 的图名，目前只允许连接一个图。

修改完上述配置后，即可启动 HugeGraphStudio:

```bash
$ cd hugegraph-studio-${version}
$ bin/hugegraph-studio.sh
```

启动成功结果如下：

```bash
19:05:12.779 [localhost-startStop-1] INFO  org.springframework.web.context.ContextLoader ID:  TS: - Root WebApplicationContext: initialization started
19:05:12.910 [localhost-startStop-1] INFO  org.springframework.web.context.support.XmlWebApplicationContext ID:  TS: - Refreshing Root WebApplicationContext: startup date [Thu Jul 27 19:05:12 CST 2017]; root of context hierarchy
19:05:12.973 [localhost-startStop-1] INFO  org.springframework.beans.factory.xml.XmlBeanDefinitionReader ID:  TS: - Loading XML bean definitions from class path resource [applicationContext.xml]
19:05:13.402 [localhost-startStop-1] INFO  org.springframework.beans.factory.annotation.AutowiredAnnotationBeanPostProcessor ID:  TS: - JSR-330 'javax.inject.Inject' annotation found and supported for autowiring
19:05:13.710 [localhost-startStop-1] WARN  com.baidu.hugegraph.config.HugeConfig ID:  TS: - The option: 'studio.server.port' is redundant
19:05:13.711 [localhost-startStop-1] WARN  com.baidu.hugegraph.config.HugeConfig ID:  TS: - The option: 'studio.server.host' is redundant
19:05:13.712 [localhost-startStop-1] WARN  com.baidu.hugegraph.config.HugeConfig ID:  TS: - The option: 'studio.server.ui' is redundant
19:05:13.712 [localhost-startStop-1] WARN  com.baidu.hugegraph.config.HugeConfig ID:  TS: - The option: 'studio.server.api.war' is redundant
····
19:05:14.873 [main] INFO   com.baidu.hugegraph.studio.HugeGraphStudio ID:  TS: - HugeGraphStudio is now running on: http://localhost:8088
```

接下来，打开浏览器访问 <http://localhost:8088> 即可使用HugeGraph-Studio，首页如下图：

<center>
  <img src="/images/images-studio/home-page.png" alt="image">
</center>

这里以"一些人与相关软件关系图"为例子，内容包括元数据（Schema）和数据（Vertex/Edge）两部分。

### 4 HugeGraph-Studio 操作指南

#### 4.1 使用Gremlin语言创建一个图

##### 4.1.1 创建Schema

这个例子涉及的Schema有三类，分别是：PropertyKey，VertexLabel和EdgeLabel。下面依次创建这些Schema。

###### 4.1.1.1 创建属性类型（PropertyKey）

将下面的语句输入到 Studio 的输入框中：

```groovy
graph.schema().propertyKey("name").asText().ifNotExist().create()
graph.schema().propertyKey("age").asInt().ifNotExist().create()
graph.schema().propertyKey("city").asText().ifNotExist().create()
graph.schema().propertyKey("lang").asText().ifNotExist().create()
graph.schema().propertyKey("date").asText().ifNotExist().create()
graph.schema().propertyKey("price").asInt().ifNotExist().create()
```

**在这里有几点需要说明**

1、上述语句是`groovy`语言形式（类似但不是`java`）的`gremlin`语句，这些`gremlin`语句会被发送到`HugeGraphServer`上执行。
关于`gremlin`本身可以参考[Gremlin Query Language](../language/hugegraph-gremlin)或[Tinkerpop官网](http://tinkerpop.apache.org/)；

2、上述语句是通过`graph.schema()`获取到`SchemaManager`对象后操作元数据，通过`gremlin`语句操作Schema可参考文档[HugeGraph-Client](/docs/clients/hugegraph-client)，
需要注意的是`HugeGraph-Client`是`java`语法，大体上与`gremlin`风格是一致的，具体的差异见文档`HugeGraph-Client`中的说明。

3、在`HugeGraph-Studio`的输入框中，用户可以直接使用两个变量`graph`和`g`，其中`graph`就是当前连接的图对象，可使用该对象对图做各种增删改查操作;
`g`是用于遍历图的一个对象，其本质就是`graph.traversal()`，用户可以使用该对象做各种遍历操作；

4、`HugeGraph-Studio`作为一个展示图的工具，主要用于做查询或遍历，而不宜做太多增删改的操作。

执行完成后，可以得到返回的数据，表明执行成功。如图所示

<center>
  <img src="/docs/images/images-studio/add-schema.png" alt="image">
</center>


###### 4.1.1.2 创建顶点类型（VertexLabel）

```groovy
person = graph.schema().vertexLabel("person").properties("name", "age", "city").primaryKeys("name").ifNotExist().create()
software = graph.schema().vertexLabel("software").properties("name", "lang", "price").primaryKeys("name").ifNotExist().create()
```

###### 4.1.1.2 创建边类型（EdgeLabel）

```groovy
knows = graph.schema().edgeLabel("knows").sourceLabel("person").targetLabel("person").properties("date").ifNotExist().create()
created = graph.schema().edgeLabel("created").sourceLabel("person").targetLabel("software").properties("date", "city").ifNotExist().create()
```

##### 4.1.2 创建顶点（Vertex）和边（Edge）

有了Schema后，就可以根据Schema创建特定的顶点和边了，这里我们定义两个person类型的顶点实例：marko 和 vadas，再定义两者之间的关系knows：

```groovy
marko = graph.addVertex(T.label, "person", "name", "marko", "age", 29, "city", "Beijing")
vadas = graph.addVertex(T.label, "person", "name", "vadas", "age", 27, "city", "Hongkong")
marko.addEdge("knows", vadas, "date", "20160110")
```

在页面中输入语句，这样我们就创建了两个顶点一条边，点击执行，结果如下图所示

<center>
  <img src="/docs/images/images-studio/example-2V-1E.png" alt="image">
</center>


##### 4.1.3 添加更多数据到图中

```groovy
marko = graph.addVertex(T.label, "person", "name", "marko", "age", 29, "city", "Beijing")
vadas = graph.addVertex(T.label, "person", "name", "vadas", "age", 27, "city", "Hongkong")
lop = graph.addVertex(T.label, "software", "name", "lop", "lang", "java", "price", 328)
josh = graph.addVertex(T.label, "person", "name", "josh", "age", 32, "city", "Beijing")
ripple = graph.addVertex(T.label, "software", "name", "ripple", "lang", "java", "price", 199)
peter = graph.addVertex(T.label, "person","name", "peter", "age", 29, "city", "Shanghai")

marko.addEdge("knows", vadas, "date", "20160110")
marko.addEdge("knows", josh, "date", "20130220")
marko.addEdge("created", lop, "date", "20171210", "city", "Shanghai")
josh.addEdge("created", ripple, "date", "20151010", "city", "Beijing")
josh.addEdge("created", lop, "date", "20171210", "city", "Beijing")
peter.addEdge("created", lop, "date", "20171210", "city", "Beijing")
```

##### 4.1.4 展示图

```groovy
g.V()
```

如下图所示

<center>
  <img src="/docs/images/images-studio/show-graph.png" alt="image">
</center>


HugeGraph-Studio不仅支持通过graph的方式展示数据，还支持表格和Json两种数据展示形式

**表格展示形式**

<center>
  <img src="/docs/images/images-studio/show-table.png" alt="image">
</center>


**Json展示形式**

<center>
  <img src="/docs/images/images-studio/show-json.png" alt="image">
</center>


#### 4.4 HugeGraph-Studio 样式自定义

##### 4.4.1 自定义VertexLabel 样式

| 属性                         | 默认值       | 类型     | 说明                                                                                                              |
|:---------------------------|:----------|:-------|:----------------------------------------------------------------------------------------------------------------|
| `vis.size`                 | `25`      | number | 顶点大小                                                                                                            |
| `vis.scaling.min`          | `10`      | number | 根据标签内容调整节点大小，优先级比vis.size高                                                                                      |
| `vis.scaling.max`          | `30`      | number | 根据标签内容调整节点大小，优先级比vis.size高                                                                                      |
| `vis.shape`                | dot       | string | 形状，包括ellipse, circle, database, box, text，diamond, dot, star, triangle, triangleDown, hexagon, square and icon. |
| `vis.border`               | #00ccff   | string | 顶点边框颜色                                                                                                          |
| `vis.background`           | #00ccff   | string | 顶点背景颜色                                                                                                          |
| `vis.hover.border`         | #00ccff   | string | 鼠标悬浮时，顶点边框颜色                                                                                                    |
| `vis.hover.background`     | #ec3112   | string | 鼠标悬浮时，顶点背景颜色                                                                                                    |
| `vis.highlight.border`     | #fb6a02   | string | 选中时，顶点边框颜色                                                                                                      |
| `vis.highlight.background` | #fb6a02   | string | 选中时，顶点背景颜色                                                                                                      |
| `vis.font.color`           | #343434   | string | 顶点类型字体颜色                                                                                                        |
| `vis.font.size`            | `12`      | string | 顶点类型字体大小                                                                                                        |
| `vis.icon.code`            | `\uf111`  | string | FontAwesome 图标编码，目前支持4.7.5版本的图标                                                                                 |
| `vis.icon.color`           | `#2B7CE9` | string | 图标颜色，优先级比vis.background高                                                                                        |
| `vis.icon.size`            | 50        | string | icon大小，优先级比vis.size高                                                                                            |

示例：

```groovy
graph.schema().vertexLabel("software")
     .userdata("vis.size",25)
     .userdata("vis.scaling.min",1)
     .userdata("vis.scaling.max",10)
     .userdata("vis.shape","icon")
     .userdata("vis.border","#66ff33")
     .userdata("vis.background","#3366ff")
     .userdata("vis.hover.background","#FFB90F")
     .userdata("vis.hover.border","#00EE00")
     .userdata("vis.highlight.background","#7A67EE")
     .userdata("vis.highlight.border","#4F4F4F")
     .userdata("vis.font.color","#1C86EE")
     .userdata("vis.font.size",12)
     .userdata("vis.icon.code","\uf1b9")
     .userdata("vis.icon.color","#8EE5EE")
     .userdata("vis.icon.size",25)
     .append()
```

<div align="center">

颜色代码示例：
<table style="BORDER-COLLAPSE: collapse" bordercolor="#111111" cellpadding="2" width="740" border="0">
<tbody><tr><td align="middle" width="10%" bgcolor="#fffff" height="16"><font face="MS Sans Serif" size="2" color="#000000">#ffffff </font></td><td align="middle" width="10%" bgcolor="#ffffcc" height="16"><font face="MS Sans Serif" size="2" color="#000000">#ffffcc </font></td><td align="middle" width="10%" bgcolor="#cccccc" height="16"><font face="MS Sans Serif" size="2" color="#000000">#cccccc </font></td><td align="middle" width="10%" bgcolor="#999999" height="16"><font face="MS Sans Serif" size="2" color="#000000">#999999 </font></td><td align="middle" width="10%" bgcolor="#000000" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#000000 </font></td><td align="middle" width="10%" bgcolor="#fc363b" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#fc363b </font></td><td align="middle" width="10%" bgcolor="#fb157e" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#fb157e </font></td><td align="middle" width="10%" bgcolor="#fec96e" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#fec96e </font></td><td align="middle" width="10%" bgcolor="#b80711" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#b80711</font></td><td align="middle" width="10%" bgcolor="#e981f2" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#e981f2 </font></td></tr><tr><td align="middle" width="10%" bgcolor="#fb6120" height="16"><font face="MS Sans Serif" size="2" color="#000000">#fb6120 </font></td><td align="middle" width="10%" bgcolor="#9b9dfa" height="16"><font face="MS Sans Serif" size="2" color="#000000">#9b9dfa </font></td><td align="middle" width="10%" bgcolor="#98c2f9" height="16"><font face="MS Sans Serif" size="2" color="#000000">#98c2f9 </font></td><td align="middle" width="10%" bgcolor="#3e71ef" height="16"><font face="MS Sans Serif" size="2" color="#000000">#3e71ef </font></td><td align="middle" width="10%" bgcolor="#fecec8" height="16"><font face="MS Sans Serif" color="#00000" size="2">#fecec8 </font></td><td align="middle" width="10%" bgcolor="#77d46f" height="16"><font face="MS Sans Serif" color="#00000" size="2">#77d46f </font></td><td align="middle" width="10%" bgcolor="#fefc38" height="16"><font face="MS Sans Serif" color="#00000" size="2">#fefc38 </font></td><td align="middle" width="10%" bgcolor="#7ede4d" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#7ede4d </font></td><td align="middle" width="10%" bgcolor="#c3f9be" height="16"><font face="MS Sans Serif" color="#00000" size="2">#c3f9be</font></td><td align="middle" width="10%" bgcolor="#f95c79" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#f95c79 </font></td></tr></tbody>
</table>
</div>
