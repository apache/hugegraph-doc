---
title: "HugeGraph-Hubble Quick Start"
linkTitle: "Visual with HugeGraph-Hubble"
weight: 1
---

### 1 HugeGraph-Hubble Overview

> ⚠️ **Security notice**: Hubble listens on plain HTTP. Do not expose it to the public Internet or untrusted networks; terminate HTTPS in front of it and restrict access with IP/port allowlists. Hubble keeps no account database of its own: when the connected HugeGraph Server has authentication enabled, Hubble shows a sign-in page and forwards the credentials to the Server; when the Server allows anonymous access, there is no sign-in and the account pages are hidden.

> **Version note**: This page follows hugegraph-toolchain `master`. Features that depend on newer Server, PD or Store versions are marked below and are unavailable on older Servers.

> **Testing Guide**: For running HugeGraph-Hubble tests locally, please refer to [HugeGraph Toolchain Local Testing Guide](/docs/guides/toolchain-local-test)

HugeGraph-Hubble is HugeGraph's web management interface. It connects to one HugeGraph Server, either directly or through PD in a distributed cluster, manages GraphSpaces, graphs and schemas, imports data, runs Gremlin and Cypher queries and built-in graph algorithms, and visualizes the results.

The platform mainly includes the following modules:

##### Graph Overview

Graph Overview lists GraphSpaces (in PD mode) and graphs. It creates, clones and clears graphs, loads demo graphs, opens the graph detail page with statistics and schema, and jumps to the query workbench.

##### Metadata Modeling

Metadata Modeling manages PropertyKeys, VertexLabels, EdgeLabels and IndexLabels of one graph, in list and graph views. Schema Templates keep reusable Groovy schemas per GraphSpace that can be applied when a graph is created.

##### Data Import

> The data import page is intended for small-scale trials. For bulk or production imports, use [HugeGraph Loader](/docs/quickstart/toolchain/hugegraph-loader).

Data Sources register FILE, HDFS, JDBC and KAFKA sources. Import tasks are configured in four steps and can run once, on a cron schedule, or continuously for Kafka.

##### Graph Query

Graph Query runs Gremlin and Cypher statements in immediate or asynchronous mode and displays results as a graph (2D or 3D), a table, or JSON. It keeps execution records and favorite statements.

##### Built-in Graph Algorithms

Built-in Graph Algorithms provides forms for the Server's OLTP traverser APIs (interactive exploration) and for OLAP jobs (cluster batch computation through HugeGraph Computer or Vermeer).

##### Async Tasks

Async Tasks lists background tasks such as Gremlin and Cypher tasks, algorithm tasks, metadata removal, index creation and rebuild, and Vermeer load or compute tasks, with detail, cancel and delete actions.

##### System and Operations

System and Operations covers the personal profile, account management with GraphSpace permission presets, and, in PD mode, the cluster overview and node details.

#### 1.1 Compatibility

Hubble detects the authentication mode and the capabilities of the connected Server; there is no separate authentication switch in Hubble. The supported combinations are:

| HugeGraph Server / PD | Deployment | Hubble compatibility | Scope and limitations |
|---|---|---|---|
| Server 1.5.x | Standalone, normally without authentication | Minimum compatibility | Basic graph, schema, data and Gremlin workflows only. GraphSpace, account permissions, PD/Store topology, cluster operations and newer algorithms are unavailable. |
| Server 1.7.x with matching PD/Store 1.7.x | Standalone or distributed | Minimum compatibility through legacy adapters | Core management and query workflows stay usable, but legacy REST/Gremlin authentication, permission semantics, metrics and algorithm capabilities give a reduced experience. |
| Server, PD and Store 1.8.x or later | Distributed deployment recommended | Full and recommended experience | GraphSpace, account permission presets, cluster operations, async tasks and algorithm capability handling are designed and validated against this generation. |

Use matching Server, PD and Store minor versions in a distributed cluster.

### 2 Deploy

There are three ways to deploy `hugegraph-hubble`

- Use Docker (Convenient for Test/Dev)
- Download the Toolchain binary package
- Source code compilation

Hubble runs on Java 11: the backend is compiled with `java.version=11` and the Docker image is based on `eclipse-temurin:11-jre`. `bin/start-hubble.sh` only checks that a `java` binary is on the `PATH`, so make sure the right JDK is selected.

#### 2.1 Use docker (Convenient for Test/Dev)

> **Special Note**: Hubble no longer asks for the Server host and port on the web page. The Server address comes from `conf/hugegraph-hubble.properties`: `server.direct_url` when `pd.enabled=false`, or PD discovery through `pd.peers` when `pd.enabled=true`. Inside the container `127.0.0.1` refers to the `hubble` container itself, so the packaged default `server.direct_url=http://127.0.0.1:8080` does not reach a Server running in another container.
>
> If `hubble` and `server` are in the same docker network, we **recommend** using the `container_name` (in our example, it is `server`) as the hostname, and `8080` as the port. Or you can use the **host IP** as the hostname, and the port is configured by the host for the server.

The image copies the packaged distribution to `/hubble`, rewrites `server.host=0.0.0.0` and clears `dashboard.address` in `/hubble/conf/hugegraph-hubble.properties`, exposes port `8088` and runs `./bin/start-hubble.sh -f` in the foreground.

Prepare a `hugegraph-hubble.properties` that points at your Server and keeps the container listening on all interfaces:

```properties
server.host=0.0.0.0
server.port=8088
pd.enabled=false
server.direct_url=http://server:8080
```

Then start [hubble](https://hub.docker.com/r/hugegraph/hubble) with that file mounted over the packaged configuration:

```bash
docker run -itd --name=hubble -p 8088:8088 \
  -v "$PWD/hugegraph-hubble.properties:/hubble/conf/hugegraph-hubble.properties" \
  hugegraph/hubble:1.7.0
```

Alternatively, you can use Docker Compose to start `hubble`. Additionally, if `hubble` and the graph is in the same Docker network, you can access the graph using the container name of the graph, eliminating the need for the host machine's IP address.

Use `docker-compose up -d`, `docker-compose.yml` is following:

```yaml
version: '3'
services:
  server:
    image: hugegraph/hugegraph:1.7.0
    container_name: server
    environment:
      - PASSWORD=xxx
    ports:
      - 8080:8080

  hubble:
    image: hugegraph/hubble:1.7.0
    container_name: hubble
    ports:
      - 8088:8088
    volumes:
      - ./hugegraph-hubble.properties:/hubble/conf/hugegraph-hubble.properties
```

> Note:
>
> 1. The docker image of hugegraph-hubble is a convenience release to start hugegraph-hubble quickly, but not **official distribution** artifacts. You can find more details from [ASF Release Distribution Policy](https://infra.apache.org/release-distribution.html#dockerhub).
>
> 2. Recommend to use `release tag` (like `1.7.0`) for the stable version. Use `latest` tag to experience the newest functions in development.

#### 2.2 Download the Toolchain binary package

`hubble` is in the `toolchain` project. First, download the binary tar tarball

```bash
export VERSION=1.7.0
export ARCHIVE="apache-hugegraph-toolchain-incubating-${VERSION}"
wget "https://downloads.apache.org/hugegraph/${VERSION}/${ARCHIVE}.tar.gz"
tar -xvf "${ARCHIVE}.tar.gz"
cd "${ARCHIVE}/apache-hugegraph-hubble-incubating-${VERSION}"
```

Edit `conf/hugegraph-hubble.properties` so that the Server address is correct, then run `hubble`

```bash
bin/start-hubble.sh
```

`start-hubble.sh` accepts the following options:

| Option | Description |
|--------|-------------|
| `-f`, `--foreground [true\|false]` | Run in the foreground instead of as a daemon; the Docker image uses `-f` |
| `-d`, `--debug` | Enable the JDWP debugger on port `8787` (`server=y,suspend=n`) |

The script starts the JVM with `-Xms512m -Dfile.encoding=UTF-8 -Dhubble.home.path=<install dir>`, writes the PID to `bin/pid`, logs to `logs/hugegraph-hubble.log` and waits up to 30 seconds for `http://<server.host>:<server.port>/about` to answer before it returns.

The packaged default is `server.host=localhost`, so the service only accepts loopback connections until you change it. After startup, open `http://<host>:8088`.

Run `bin/stop-hubble.sh` to stop the service. It sends `SIGTERM` first so that the shutdown hooks pause running load tasks and close the embedded H2 database cleanly, and only escalates to `SIGKILL` if the process is still alive after `STOP_TIMEOUT` seconds (environment variable, default `30`).

#### 2.3 Source code compilation

Hubble's build uses `frontend-maven-plugin` in `hugegraph-hubble/hubble-dist/pom.xml` to install Node.js v18.20.8 and Yarn v1.22.21, so neither tool needs to be installed beforehand. JDK 11 and Maven are required.

Download the toolchain source code.

```shell
git clone https://github.com/apache/hugegraph-toolchain.git
```

Compile `hubble`. It depends on the loader and client, so you need to build these dependencies in advance during the compilation process (you can skip this step later).

```shell
cd hugegraph-toolchain
python -m pip install -r hugegraph-hubble/hubble-dist/assembly/travis/requirements.txt
mvn install -pl hugegraph-client,hugegraph-loader -am -Dmaven.javadoc.skip=true -DskipTests -ntp
cd hugegraph-hubble
mvn -e compile package -Dmaven.javadoc.skip=true -Dmaven.test.skip=true -ntp
cd apache-hugegraph-hubble-*
```

Run `hubble`

```bash
bin/start-hubble.sh -d
```

For frontend work, run `yarn dev` inside `hubble-fe`. The backend POM does not configure `spring-boot:run`, so run `org.apache.hugegraph.HugeGraphHubble` from `hubble-be/target/classes` with `-Dhubble.home.path` pointing at a writable directory instead.

### 3	Platform Workflows

The home page groups the modules into three journeys: Graph Overview, Graph Import and Graph Query. It also shows whether Hubble runs in PD / cluster mode or in non-PD standalone mode. The module usage process of the platform is as follows:

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/2平台使用流程.png" alt="image">
</div>


### 4	Platform Instructions
#### 4.1	Graph Management
In PD mode, [Graph Space Management] lists all GraphSpaces of the cluster and can create or edit one, including its alias, optional Kubernetes namespace and compute task, and resource limits. In non-PD standalone mode there is exactly one GraphSpace named `DEFAULT` and the GraphSpace list is skipped.

##### 4.1.1	Graph creation
Under the graph management module, click [New Graph] and fill in the graph name, an optional alias, an optional schema template and optional sample data. The graph name is unique inside its GraphSpace and cannot be changed after creation.

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/311图创建.png" alt="image">
</div>


Create graph by filling in the content as follows:

<center>
  <img src="/docs/images/images-hubble/311图创建2.png" alt="image">
</center>

> **Special Note**: The Server connection is not configured on this page. It comes from `conf/hugegraph-hubble.properties`, through `server.direct_url` or PD discovery; see section 2.1 for the Docker hostname rules. Graph creation is only offered when the connected Server exposes it (REST API 0.67 or later); on older Servers the graph list is read-only.

##### 4.1.2	Graph Access
Realize the information access to the graph space. After entering, you can perform operations such as multidimensional query analysis, metadata management, data import, and algorithm analysis of the graph. [Open Graph Studio] opens the query workbench, [Metadata Config] opens the schema pages, and the graph detail page shows vertex and edge statistics together with the schema.

<center>
  <img src="/docs/images/images-hubble/312图访问.png" alt="image">
</center>


##### 4.1.3	Graph management
1. The graph list has a card view and a list view. Search matches the graph name.
2. Per-graph actions are View Schema (with [Export Groovy Schema]), Metadata Config, Clone Graph (schema only, or schema and data), Clear Schema and Data, Delete, and, in PD mode, Set Default.
3. [Sample data and resources] builds a demo graph inside the current graph: the Red Chamber demo graph, the People & Software demo graph, or the Tiny Movie Rank demo. These demos add missing schema and elements only and never clear existing data.

<center>
  <img src="/docs/images/images-hubble/313图管理.png" alt="image">
</center>


#### 4.2	Metadata Modeling (list + graph mode)
##### 4.2.1	Module entry
Open [Metadata Config] from the graph list, or the metadata page of a graph at `/graphspace/<graphspace>/graph/<graph>/meta`. The page has five tabs, Property, Vertex Type, Edge Type, Vertex Index and Edge Index, and a switch between list view and graph view.

<center>
  <img src="/docs/images/images-hubble/321元数据入口.png" alt="image">
</center>


##### 4.2.2	Property type
###### 4.2.2.1	Create type
1. Fill in or select the property name, data type, and cardinality to complete the creation of the property.
2. Created properties can be used as properties of vertex type and edge type.

List mode:

<center>
  <img src="/docs/images/images-hubble/3221属性创建.png" alt="image">
</center>


Graph mode:

<center>
  <img src="/docs/images/images-hubble/3221属性创建2.png" alt="image">
</center>


###### 4.2.2.2	Management
1. You can delete a single item or delete it in batches in the property list. A property that is still used by a vertex or edge type cannot be deleted.
2. Deleting metadata runs as an asynchronous task; check Async Tasks for its progress.

##### 4.2.3	Vertex type
###### 4.2.3.1	Create type
1. Fill in or select the vertex type name, ID strategy, associated properties, primary key properties, vertex style, content displayed below the vertex in the query result, and index information: including whether to create a type index, and the specific content of the property index, complete the vertex type creation.

List mode:

<center>
  <img src="/docs/images/images-hubble/3231顶点创建.png" alt="image">
</center>


Graph mode:

<center>
  <img src="/docs/images/images-hubble/3231顶点创建2.png" alt="image">
</center>

###### 4.2.3.2 Administration
1. Editing operations are available. The vertex style, associated properties, vertex display content, and property index can be edited, and the rest cannot be edited. In graph mode, double-click a vertex type to edit it.

2. You can delete a single item or delete it in batches.

<center>
  <img src="/docs/images/images-hubble/3233顶点删除.png" alt="image">
</center>


##### 4.2.4 Edge Types
###### 4.2.4.1 Create
1. Fill in or select the edge type name, the type (Normal, Parent or Sub, for edge type hierarchies), start point type, end point type, associated properties, whether to allow multiple connections, edge style, content displayed below the edge in the query result, and index information: including whether to create a type index, and the specific content of the property index, complete the creation of the edge type.

List mode:

<center>
  <img src="/docs/images/images-hubble/3241边创建.png" alt="image">
</center>


Graph mode:

<center>
  <img src="/docs/images/images-hubble/3241边创建2.png" alt="image">
</center>


###### 4.2.4.2 Administration
1. Editing operations are available. Edge styles, associated properties, edge display content, and property indexes can be edited, and the rest cannot be edited, the same as the vertex type.
2. You can delete a single item or delete it in batches.

##### 4.2.5 Index Types
Displays vertex and edge indexes for vertex types and edge types. Secondary, range, search and unique indexes are supported.

##### 4.2.6 Schema Templates
[Schema templates] at `/graphspace/<graphspace>/schema` keeps a reusable template library for the current GraphSpace. Example templates ship with Hubble and can be used, removed or restored; they are not stored on the Server until you save one. User templates hold Groovy schema on the Server and can be created, edited and deleted. When you create a graph, an existing template can be selected so that its schema is applied right away.

#### 4.3 Data Import

> **Note**: currently, we recommend to use [hugegraph-loader](/docs/quickstart/toolchain/hugegraph-loader) to import data formally. The built-in import of `hubble` is used for **testing** and **getting started**.

The usage process of data import is as follows:

<center>
  <img src="/docs/images/images-hubble/33导入流程.png" alt="image">
</center>


##### 4.3.1	Module entrance
Left navigation, under Graph Import: [Data Sources] and [Data Import].
<center>
  <img src="/docs/images/images-hubble/331导入入口.png" alt="image">
</center>


##### 4.3.2 Data sources
1. [Data Sources] registers where an import task reads from. Four source types are supported: FILE (local upload), HDFS, Kafka and JDBC.
2. For a FILE source, upload the files that need to be composed. The accepted formats come from `upload_file.format_list`, which defaults to `csv` and `txt`.
3. The single file and total size limits default to 1 GB and 10 GB, and unfinished uploads are discarded after `upload_file.max_uploading_time`, which defaults to 12 hours.

<center>
  <img src="/docs/images/images-hubble/333上传文件.png" alt="image">
</center>


##### 4.3.3 Create task
1. [Data Import] > [Create Task] configures an import in four steps: Basic Information, Select Source Fields, Select Mapping Fields and Schedule.
2. Basic Information takes the task name (1 to 48 Chinese characters, letters, digits or `_`), the target GraphSpace and graph, the source type and the data source.
3. Multiple import tasks can be created and imported in parallel.

<center>
  <img src="/docs/images/images-hubble/332创建任务.png" alt="image">
</center>


##### 4.3.4 Setting up data mapping
1. Set up data mapping for the selected source, including file settings and type settings
2. File settings: check or fill in whether to include the header, separator, encoding format and other settings of the source itself, all set the default values, no need to fill in manually
3. Type setting:

     1. Vertex map and edge map:

        【Vertex Type】: Select the vertex type, and map the column data of the source for its ID;

        【Edge Type】: Select the edge type and map the column data of the source to the ID column of its start point type and end point type;
     2. Mapping settings: map the column data of the source to the properties of the selected vertex type. Here, if the property name is the same as the header name of the file, the mapping property can be automatically matched, and there is no need to manually fill in the selection.
     3. After completing the setting, the setting list will be displayed before proceeding to the next step. It supports the operations of adding, editing and deleting mappings.

Fill in the settings map:

  <center>
      <img src="/docs/images/images-hubble/334设置映射.png" alt="image">
  </center>


Mapping list:

  <center>
    <img src="/docs/images/images-hubble/334设置映射2.png" alt="image">
  </center>


##### 4.3.5 Import data
The last step chooses when the task runs: Run Once for a one-off import, Scheduled with a Quartz cron expression such as `0 0/5 * * * ?`, or Realtime for a Kafka source.
1. Import settings
- The import setting parameter items are as shown in the figure below, all set the default value, no need to fill in manually

<center>
  <img src="/docs/images/images-hubble/335导入设置.png" alt="image">
</center>


2. Import details
- Run a task from the task list to start the import, and pause, edit or delete it from the same list
- The execution history of a task provides the execution instance ID, the number of imported records, the average rate in records per second, the import duration and the status of each run
- If the import fails, you can view the specific reason

<center>
  <img src="/docs/images/images-hubble/335导入详情.png" alt="image">
</center>


#### 4.4 Graph Query
##### 4.4.1 Module entry
Left navigation, under Graph Query: [GQL Traversal].
<center>
  <img src="/docs/images/images-hubble/341分析入口.png" alt="image">
</center>


##### 4.4.2 Multi-graphs switching
The top bar carries the current GraphSpace and graph, so you can flexibly switch the operation space of multiple graphs without leaving the page.
<center>
  <img src="/docs/images/images-hubble/342多图切换.png" alt="image">
</center>


##### 4.4.3 Graph Analysis and Processing
HugeGraph supports Gremlin, a graph traversal query language of Apache TinkerPop3. Gremlin is a general graph database query language. By entering Gremlin statements and clicking execute, you can perform query and analysis operations on graph data, and create and delete vertices/edges, modify vertex/edge properties, etc. When the connected Server supports Cypher, a Cypher tab is offered next to Gremlin. A Text2GQL tab is present as a user interface preview only: it is not connected to a model or a query service, and nothing entered there is sent or executed.

Each statement can run in one of two modes. Immediate returns the result inline and suits analyses that finish within about 30 seconds; Async submits a task instead, and its progress and result appear under Async Tasks. `Ctrl`/`Command` + `Enter` runs the current statement.

After the query, below is the graph result display area, which provides 3 kinds of graph result display modes: [Graph Mode], [Table Mode], [Json Mode]. The graph canvas can be rendered in 2D or 3D.

> ⚠️ **SEC Reminder**: Hubble allows the direct input and execution of native Gremlin query statements on the web interface, which grants users relatively high operational privileges. **Please avoid exposing the Hubble service to public network environments**. It is recommended to ensure that the graph database server has enabled the **[Authentication System (Auth)](/docs/config/config-authentication/)** combined with an **IP Whitelist** for strict permission control when in use, preventing unauthorized access or malware execution risks.

Support zoom, center, full screen, layout and style configuration, legend, minimap, undo and redo, and export operations. The canvas can be exported as JSON, CSV or an image, and a previously exported canvas can be imported again.

【Picture Mode】
<center>
  <img src="/docs/images/images-hubble/343图分析-图.png" alt="image">
</center>


【Table mode】
<center>
  <img src="/docs/images/images-hubble/343图分析-表格.png" alt="image">
</center>


【Json mode】
<center>
  <img src="/docs/images/images-hubble/343图分析-json.png" alt="image">
</center>


##### 4.4.4 Data Details
Click the vertex/edge entity to view the data details of the vertex/edge, including vertex/edge type, vertex ID, attribute and corresponding value, expand the information display dimension of the graph, and improve the usability.


##### 4.4.5 Multidimensional Path Query of Graph Results
In addition to the global query, an in-depth customized query and hidden operations can be performed for the vertices in the query result to realize customized mining of graph results.

Right-click a vertex, and the menu entry of the vertex appears, which can be displayed, inquired, hidden, etc.
- Expand: Click to display the vertices associated with the selected point.
- Query: By selecting the edge type and edge direction associated with the selected point, and then selecting its attributes and corresponding filtering rules under this condition, a customized path display can be realized.
- Hide: When clicked, hides the selected point and its associated edges.

Double-clicking a vertex also displays the vertex associated with the selected point.

<center>
  <img src="/docs/images/images-hubble/345定制路径查询.png" alt="image">
</center>


##### 4.4.6 Add vertex/edge
###### 4.4.6.1 Added vertex
In the graph area, two entries can be used to dynamically add vertices, as follows:
1. Click on the graph area panel, the Add Vertex entry appears
2. Click the first icon in the action bar in the upper right corner

Complete the addition of vertices by selecting or filling in the vertex type, ID value, and attribute information.

The entry is as follows:

<center>
  <img src="/docs/images/images-hubble/346新增顶点.png" alt="image">
</center>


Add the vertex content as follows:

<center>
  <img src="/docs/images/images-hubble/346新增顶点2.png" alt="image">
</center>


###### 4.4.6.2 Add edge
Right-click a vertex in the graph result to add the outgoing or incoming edge of that point.


##### 4.4.7 Execute the query of records and favorites
1. Record each query record at the bottom of the graph area, including: query time, execution type, content, status, time-consuming, as well as [collection] and [load] operations, to achieve a comprehensive record of graph execution, with traces to follow, and Can quickly load and reuse execution content
2. Provides the function of collecting sentences, which can be used to collect frequently used sentences, which is convenient for fast calling of high-frequency sentences.

<center>
  <img src="/docs/images/images-hubble/347收藏.png" alt="image">
</center>


#### 4.5 Async Tasks
##### 4.5.1 Module entry
Left navigation, under Graph Query: [Async Tasks].
<center>
   <img src="/docs/images/images-hubble/351任务管理入口.png" alt="image">
</center>


##### 4.5.2 Task Management
1. Provide unified management and result viewing of asynchronous tasks. The task types are:
- gremlin: Gremlin tasks
- cypher: Cypher tasks
- computer-dis: algorithm tasks
- remove_schema: remove metadata
- create_index: create an index
- rebuild_index: rebuild the index
- vermeer-task:load: Vermeer graph load tasks
- vermeer-task:compute: Vermeer graph compute tasks
2. The list displays the asynchronous task information of the current graph, including task ID, task name, task type, creation time, time-consuming, status, operation, and realizes the management of asynchronous tasks. The list refreshes every 5 seconds.
3. Support filtering by task type and status
4. Support searching for task ID and task name
5. A running task can be cancelled, and asynchronous tasks can be deleted one by one or in batches

<center>
  <img src="/docs/images/images-hubble/352任务列表.png" alt="image">
</center>


##### 4.5.3 Gremlin asynchronous tasks
1. Create a task

- The graph query module supports two execution modes, immediate query and asynchronous task; if the user switches to the asynchronous mode, after clicking execute, an asynchronous task will be created in the asynchronous task center. A Cypher statement creates a Cypher task in the same way;
2. Task submission
- After the task is submitted successfully, the graph area returns the submission result and task ID
3. Mission details
- Provide [View] entry, you can jump to the task details to view the specific execution of the current task After jumping to the task center, the currently executing task line will be displayed directly

<center>
  <img src="/docs/images/images-hubble/353gremlin任务.png" alt="image">
</center>


Click to view the entry to jump to the task management list, as follows:

<center>
  <img src="/docs/images/images-hubble/353gremlin任务2.png" alt="image">
</center>


4. View the results
- The results are displayed in the form of JSON, and a compact result can be expanded inline


##### 4.5.4 Algorithm tasks
Batch algorithms submitted from [Built-in Graph Algorithms] land here as algorithm tasks, and so do Vermeer graph load and compute tasks. Find a task by ID in the list and open it to follow its progress and result. See section 4.6 for the algorithm forms themselves.

##### 4.5.5 Delete metadata, rebuild index
1. Create a task
- In the metadata modeling module, when deleting metadata, an asynchronous task for deleting metadata can be created

<center>
  <img src="/docs/images/images-hubble/355删除元数据.png" alt="image">
</center>


- When editing an existing vertex/edge type operation, when adding an index, an asynchronous task of creating an index can be created
<center>
  <img src="/docs/images/images-hubble/355构建索引.png" alt="image">
</center>


2. Task details
- After confirming/saving, you can jump to the task center to view the details of the current task

<center>
  <img src="/docs/images/images-hubble/355任务详情.png" alt="image">
</center>


#### 4.6 Built-in Graph Algorithms

[Built-in Graph Algorithms] under Graph Query provides parameter forms for the algorithms the Server exposes, grouped by intent: explore neighborhoods, find paths and connections, compare and rank, measure importance, find communities, and analyze graph structure. Each algorithm links to its official API documentation.

Two execution modes are offered:

- Interactive exploration runs the Server's OLTP traverser APIs and returns results directly. It covers K-out and K-neighbor, shortest path in its single source, weighted, and multi-node forms, paths and all paths, customized and template paths, rings and rays, crosspoints and customized crosspoints, same neighbors, Jaccard similarity, fusiform similarity, Adamic-Adar, resource allocation, egonet, and the rank and neighbor rank APIs.
- Cluster batch computation submits an asynchronous job over the whole graph and reports the result under Async Tasks. It covers PageRank and personal PageRank, degree, closeness and betweenness centrality, K-core, weakly connected components, label propagation, Louvain, triangle count, cluster coefficient, rings detection, subgraph matching and links, with Vermeer variants where the deployment provides Vermeer.

Batch algorithms need a HugeGraph Computer environment, including Kubernetes when the deployment requires it. When Computer cannot be reached, the page says so instead of submitting the task.

#### 4.7 Sign-in and account management

When the connected Server has authentication enabled, Hubble opens the sign-in page at `/login`. Sign in with a HugeGraph Server account: Hubble forwards the credentials to the Server and keeps the returned token for the browser session, and it stores no accounts of its own. Login attempts are throttled, so after the first three failures for the same account and address, further attempts back off starting at 5 seconds and doubling up to 600 seconds. When the Server allows anonymous access, `/login` redirects to the home page and the profile and account pages are hidden.

[My Profile] shows the account details and changes the password. [Account Management] is available to accounts that may manage accounts or GraphSpace members. It creates accounts and assigns one of four access presets: Super Administrator, GraphSpace Read-only, GraphSpace Read-write and GraphSpace Administrator. Low-level role, target, access and belong records are not exposed in the interface.

#### 4.8 Cluster operations

In PD mode, [System & Operations] adds [Cluster Overview] and [Node details] for accounts with the matching capabilities. Cluster Overview shows the topology, per-tier node status and cluster facts such as stores online, PD leader, capacity, data size, graphs, partitions and replicas. Node details lists every discovered node with filters for type and status, and opens a node profile with its metrics, leader role and Raft shards. Node details is also available in standalone mode; Cluster Overview needs PD.

An optional external dashboard can be linked from the navigation page through `dashboard.address`. It is a separate monitoring entry, and leaving it unconfigured does not affect Cluster Overview or Node details.

### 5 Configuration

HugeGraph-Hubble can be configured through the `conf/hugegraph-hubble.properties` file.

#### 5.1 Service Configuration

| Configuration Item | Default Value | Description |
|-------------------|---------------|-------------|
| `server.host` | `localhost` | The address that Hubble binds to. The Docker image rewrites it to `0.0.0.0` |
| `server.port` | `8088` | The port that Hubble listens on |
| `server.protocol` | `http` | Protocol used to reach HugeGraphServer, `http` or `https` |
| `ssl.client_truststore_file` | `conf/hugegraph.truststore` | Client truststore path, used when `server.protocol=https` |
| `ssl.client_truststore_password` | `hugegraph` | Client truststore password, used when `server.protocol=https` |

#### 5.2 Server and PD

| Configuration | Default | Description |
|---------------|---------|-------------|
| `pd.enabled` | `false` | Whether to discover services through PD; keep `false` for a standalone Server |
| `server.direct_url` | `http://127.0.0.1:8080` | Server address used when `pd.enabled=false` |
| `pd.peers` | `127.0.0.1:8686` | PD node address |
| `pd.server` | `127.0.0.1:8620` | PD service address |
| `cluster` | `hg` | Name of the cluster Hubble connects to |
| `route.type` | `NODE_PORT` | Service routing mode: `NODE_PORT`, `DDS`, or `BOTH` |
| `client.request_timeout` | `60` | Request timeout in seconds for the HugeGraph client |
| `client.url_cache_max_entries` | `1024` | Discovered URL scopes retained for stale fallback |

#### 5.3 Gremlin Query Limits

These settings control query result limits to prevent memory issues:

| Configuration Item | Default Value | Description |
|-------------------|---------------|-------------|
| `gremlin.suffix_limit` | `250` | Maximum query suffix length |
| `gremlin.vertex_degree_limit` | `100` | Maximum vertex degree to display |
| `gremlin.edges_total_limit` | `500` | Maximum number of edges returned |
| `gremlin.batch_query_ids` | `100` | ID batch query size |
| `execute-history.show_limit` | `500` | Number of execution records kept for display |

#### 5.4 File Upload

These keys are not written into the packaged file; add them to override the defaults.

| Configuration Item | Default Value | Description |
|-------------------|---------------|-------------|
| `upload_file.location` | `upload-files` | Directory that holds uploaded files |
| `upload_file.format_list` | `csv,txt` | Accepted upload formats |
| `upload_file.single_file_size_limit` | 1 GB | Size limit for one uploaded file |
| `upload_file.total_file_size_limit` | 10 GB | Total size limit for uploaded files |
| `upload_file.max_uploading_time` | `43200` | Seconds before unfinished upload parts are cleared |

#### 5.5 Cluster Operations

These keys drive the Cluster Overview and Node details pages.

| Configuration Item | Default Value | Description |
|-------------------|---------------|-------------|
| `operations.connect_timeout_ms` | `1500` | Connection timeout for each operations upstream |
| `operations.read_timeout_ms` | `2500` | Read timeout for each operations upstream |
| `operations.max_response_bytes` | `1048576` | Maximum accepted body size from an operations upstream |
| `operations.cache_ttl_seconds` | `5` | Lifetime of a fresh operations snapshot |
| `operations.cache_max_entries` | `1024` | Operations snapshots retained across credentials |
| `operations.store_threads` | `16` | Concurrent Store metric collection tasks |
| `operations.store_deadline_ms` | `5000` | Deadline for one Store metric collection pass |
| `operations.store.allowed_targets` | `[http://127.0.0.1:8520,http://[::1]:8520]` | Exact Store metric origins Hubble may contact |
| `operations.pd.username` / `operations.pd.password` | `hubble` / empty | PD service identity used by the backend only |
| `operations.store.username` / `operations.store.password` | `hubble` / empty | Store service identity used by the backend only |
| `dashboard.address` | `127.0.0.1:8092` | Optional external dashboard; empty hides the entry |

> The `operations.store.allowed_targets` default covers local testing only. A production deployment must list every trusted Store scheme, host and port explicitly, because discovery never adds an origin to this allowlist. HTTPS origins keep their configured hostname for TLS SNI and certificate verification. Supply the PD and Store passwords through a protected deployment configuration rather than the packaged file.
