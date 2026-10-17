---
title: "HugeGraph-Studio Quick Start"
linkTitle: "(Deprecated) Display with HugeGraph-Studio"
draft: true
weight: 5
---

> Note: Studio is no longer maintained. Use [Hubble](/docs/quickstart/toolchain/hugegraph-hubble/) instead.

### 1 HugeGraph-Studio Overview (Deprecated)

HugeGraph-Studio is a web-based graphical IDE for HugeGraph. It executes Gremlin statements and displays their results graphically. Features include:

- Graph data input
- Graph visualization
- Graph analysis

> HugeGraph-Studio depends on HugeGraph-Server. Before installing or using Studio, check with `jps` that HugeGraphServer is running. If needed, follow the [Server installation guide](/docs/quickstart/hugegraph/hugegraph-server/).

### 2 Install and Run HugeGraph-Studio

Two installation methods are available:

- Build a source archive
- Download a binary archive

#### 2.1 Build from Source

Download HugeGraph-Studio source:

```bash
$ git clone https://github.com/hugegraph/hugegraph-studio.git
```

Build the archive:

```bash
$ cd hugegraph-studio
$ mvn package -DskipTests
```

Example output:

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

The build creates `hugegraph-studio-${version}/` and `hugegraph-studio-${version}.tar.gz` under the source directory.

#### 2.2 Download a Binary Archive

Download from:

```bash
wget https://github.com/hugegraph/hugegraph-studio/releases/download/v${version}/hugegraph-studio-${version}.tar.gz
```

Extract the archive:

```bash
$ tar zxvf hugegraph-studio-${version}.tar.gz
```

### 3 Start HugeGraph-Studio

Edit configuration:

```bash
$ cd hugegraph-studio-${version}
$ vim conf/hugegraph-studio.properties
```

- `studio.server.host`: Change `localhost` to the Studio hostname or IP for external access; retain it for local access.
- `studio.server.port`: Change `8088` to the desired Studio service port.
- `graph.server.host`: HugeGraphServer hostname used with `graph.server.port` to connect to Server.
- `graph.server.port`: HugeGraphServer port, default `8080`, used with `graph.server.host`.
- `graph.name`: Graph to connect to, default `hugegraph`. Studio supports one graph at a time.

After editing configuration, start Studio:

```bash
$ cd hugegraph-studio-${version}
$ bin/hugegraph-studio.sh
```

Successful startup output:

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

Open <http://localhost:8088> in a browser; the homepage is shown below.

<center>
  <img src="/images/images-studio/home-page.png" alt="image">
</center>

The following example models relationships between people and software, with schema and vertex/edge data.

### 4 HugeGraph-Studio User Guide

#### 4.1 Create a Graph with Gremlin

##### 4.1.1 Create Schema

The example uses PropertyKey, VertexLabel, and EdgeLabel schema. Create them in the following order.

###### 4.1.1.1 Create Property Keys

Enter the following statements in Studio:

```groovy
graph.schema().propertyKey("name").asText().ifNotExist().create()
graph.schema().propertyKey("age").asInt().ifNotExist().create()
graph.schema().propertyKey("city").asText().ifNotExist().create()
graph.schema().propertyKey("lang").asText().ifNotExist().create()
graph.schema().propertyKey("date").asText().ifNotExist().create()
graph.schema().propertyKey("price").asInt().ifNotExist().create()
```

**Notes**

1. These Gremlin statements use Groovy syntax and are sent to HugeGraphServer for execution.
See [Gremlin Query Language](../language/hugegraph-gremlin) or the [TinkerPop website](http://tinkerpop.apache.org/) for Gremlin details.

2. `graph.schema()` returns a `SchemaManager` for schema operations. See [HugeGraph-Client](/docs/clients/hugegraph-client/) for examples.
The Java client uses Java syntax, broadly similar to Gremlin; see its documentation for differences.

3. Studio exposes `graph`, the connected graph object for data operations, and `g`, its traversal object (`graph.traversal()`).

4. Studio primarily supports queries and visualization; avoid extensive data modification through this interface.

Execution returns data confirming success, as shown below.

<center>
  <img src="/docs/images/images-studio/add-schema.png" alt="image">
</center>


###### 4.1.1.2 Create Vertex Labels

```groovy
person = graph.schema().vertexLabel("person").properties("name", "age", "city").primaryKeys("name").ifNotExist().create()
software = graph.schema().vertexLabel("software").properties("name", "lang", "price").primaryKeys("name").ifNotExist().create()
```

###### 4.1.1.3 Create Edge Labels

```groovy
knows = graph.schema().edgeLabel("knows").sourceLabel("person").targetLabel("person").properties("date").ifNotExist().create()
created = graph.schema().edgeLabel("created").sourceLabel("person").targetLabel("software").properties("date", "city").ifNotExist().create()
```

##### 4.1.2 Create Vertices and Edges

With schema created, add `person` vertices `marko` and `vadas`, and a `knows` edge between them:

```groovy
marko = graph.addVertex(T.label, "person", "name", "marko", "age", 29, "city", "Beijing")
vadas = graph.addVertex(T.label, "person", "name", "vadas", "age", 27, "city", "Hongkong")
marko.addEdge("knows", vadas, "date", "20160110")
```

Enter and execute the statements to create two vertices and one edge; the result is shown below.

<center>
  <img src="/docs/images/images-studio/example-2V-1E.png" alt="image">
</center>


##### 4.1.3 Add More Data

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

##### 4.1.4 Display the Graph

```groovy
g.V()
```

Example visualization:

<center>
  <img src="/docs/images/images-studio/show-graph.png" alt="image">
</center>


Studio supports graph, table, and JSON views.

**Table view**

<center>
  <img src="/docs/images/images-studio/show-table.png" alt="image">
</center>


**JSON view**

<center>
  <img src="/docs/images/images-studio/show-json.png" alt="image">
</center>


#### 4.4 Customize Studio Styles

##### 4.4.1 Customize VertexLabel Styles

| Property | Default | Type | Description |
|:---------------------------|:----------|:-------|:----------------------------------------------------------------------------------------------------------------|
| `vis.size` | `25` | number | Vertex size |
| `vis.scaling.min` | `10` | number | Scale vertices according to label content; takes precedence over `vis.size` |
| `vis.scaling.max` | `30` | number | Scale vertices according to label content; takes precedence over `vis.size` |
| `vis.shape` | dot | string | Shape: ellipse, circle, database, box, text, diamond, dot, star, triangle, triangleDown, hexagon, square, or icon |
| `vis.border` | #00ccff | string | Vertex border color |
| `vis.background` | #00ccff | string | Vertex background color |
| `vis.hover.border` | #00ccff | string | Border color on hover |
| `vis.hover.background` | #ec3112 | string | Background color on hover |
| `vis.highlight.border` | #fb6a02 | string | Selected vertex border color |
| `vis.highlight.background` | #fb6a02 | string | Selected vertex background color |
| `vis.font.color` | #343434 | string | Vertex label font color |
| `vis.font.size` | `12` | string | Vertex label font size |
| `vis.icon.code` | `\uf111` | string | FontAwesome icon code, currently supporting version 4.7.5 |
| `vis.icon.color` | `#2B7CE9` | string | Icon color; takes precedence over `vis.background` |
| `vis.icon.size` | 50 | string | Icon size; takes precedence over `vis.size` |

Example:

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

Color code examples:
<table style="BORDER-COLLAPSE: collapse" bordercolor="#111111" cellpadding="2" width="740" border="0">
<tbody><tr><td align="middle" width="10%" bgcolor="#fffff" height="16"><font face="MS Sans Serif" size="2" color="#000000">#ffffff </font></td><td align="middle" width="10%" bgcolor="#ffffcc" height="16"><font face="MS Sans Serif" size="2" color="#000000">#ffffcc </font></td><td align="middle" width="10%" bgcolor="#cccccc" height="16"><font face="MS Sans Serif" size="2" color="#000000">#cccccc </font></td><td align="middle" width="10%" bgcolor="#999999" height="16"><font face="MS Sans Serif" size="2" color="#000000">#999999 </font></td><td align="middle" width="10%" bgcolor="#000000" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#000000 </font></td><td align="middle" width="10%" bgcolor="#fc363b" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#fc363b </font></td><td align="middle" width="10%" bgcolor="#fb157e" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#fb157e </font></td><td align="middle" width="10%" bgcolor="#fec96e" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#fec96e </font></td><td align="middle" width="10%" bgcolor="#b80711" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#b80711</font></td><td align="middle" width="10%" bgcolor="#e981f2" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#e981f2 </font></td></tr><tr><td align="middle" width="10%" bgcolor="#fb6120" height="16"><font face="MS Sans Serif" size="2" color="#000000">#fb6120 </font></td><td align="middle" width="10%" bgcolor="#9b9dfa" height="16"><font face="MS Sans Serif" size="2" color="#000000">#9b9dfa </font></td><td align="middle" width="10%" bgcolor="#98c2f9" height="16"><font face="MS Sans Serif" size="2" color="#000000">#98c2f9 </font></td><td align="middle" width="10%" bgcolor="#3e71ef" height="16"><font face="MS Sans Serif" size="2" color="#000000">#3e71ef </font></td><td align="middle" width="10%" bgcolor="#fecec8" height="16"><font face="MS Sans Serif" color="#00000" size="2">#fecec8 </font></td><td align="middle" width="10%" bgcolor="#77d46f" height="16"><font face="MS Sans Serif" color="#00000" size="2">#77d46f </font></td><td align="middle" width="10%" bgcolor="#fefc38" height="16"><font face="MS Sans Serif" color="#00000" size="2">#fefc38 </font></td><td align="middle" width="10%" bgcolor="#7ede4d" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#7ede4d </font></td><td align="middle" width="10%" bgcolor="#c3f9be" height="16"><font face="MS Sans Serif" color="#00000" size="2">#c3f9be</font></td><td align="middle" width="10%" bgcolor="#f95c79" height="16"><font face="MS Sans Serif" color="#ffffff" size="2">#f95c79 </font></td></tr></tbody>
</table>
</div>
