# HugeGraph-Hubble Quick Start

LLMS index: [llms.txt](/versions/1.0/llms.txt)

---

### 1 HugeGraph-Hubble Overview

HugeGraph is an analysis-oriented graph database system that supports batch operations, which fully supports [Apache TinkerPop3](https://tinkerpop.apache.org) framework and [Gremlin](https://tinkerpop.apache.org/gremlin.html) graph query language. It provides a complete tool chain ecology such as export, backup, and recovery, and effectively solve the storage, query and correlation analysis needs of massive graph data. HugeGraph is widely used in the fields of risk control, insurance claims, recommendation search, public security crime crackdown, knowledge graph, network security, IT operation and maintenance of bank securities companies, and is committed to allowing more industries, organizations and users to enjoy a wider range of data comprehensive value.

**HugeGraph-Hubble** is HugeGraph's one-stop visual analysis platform. The platform covers the whole process from data modeling, to efficient data import, to real-time and offline analysis of data, and unified management of graphs, realizing the whole process wizard of graph application. It is designed to improve the user's use fluency, lower the user's use threshold, and provide a more efficient and easy-to-use user experience.

The platform mainly includes the following modules:

##### Graph Management

The graph management module realizes the unified management of multiple graphs and graph access, editing, deletion, and query by creating graph and connecting the platform and graph data.

##### Metadata Modeling

The metadata modeling module realizes the construction and management of graph models by creating attribute libraries, vertex types, edge types, and index types. The platform provides two modes, list mode and graph mode, which can display the metadata model in real time, which is more intuitive. At the same time, it also provides a metadata reuse function across graphs, which saves the tedious and repetitive creation process of the same metadata, greatly improves modeling efficiency and enhances ease of use.

##### Data Import

Data import is to convert the user's business data into the vertices and edges of the graph and insert it into the graph database. The platform provides a wizard-style visual import module. By creating import tasks, the management of import tasks and the parallel operation of multiple import tasks are realized. Improve import performance. After entering the import task, you only need to follow the platform step prompts, upload files as needed, and fill in the content to easily implement the import process of graph data. At the same time, it supports breakpoint resuming, error retry mechanism, etc., which reduces import costs and improves efficiency.

##### Graph Analysis

By inputting the graph traversal language Gremlin, high-performance general analysis of graph data can be realized, and functions such as customized multidimensional path query of vertices can be provided, and three kinds of graph result display methods are provided, including: graph form, table form, Json form, and multidimensional display. The data form meets the needs of various scenarios used by users. It provides functions such as running records and collection of common statements, realizing the traceability of graph operations, and the reuse and sharing of query input, which is fast and efficient. It supports the export of graph data, and the export format is Json format.

##### Task Management

For Gremlin tasks that need to traverse the whole graph, index creation and reconstruction and other time-consuming asynchronous tasks, the platform provides corresponding task management functions to achieve unified management and result viewing of asynchronous tasks.

### 2	Platform Workflow

The module usage process of the platform is as follows:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/2平台使用流程.png" alt="image">
</center>


### 3	Platform Instructions
#### 3.1	Graph Management
##### 3.1.1	Graph creation
Under the graph management module, click [Create graph], and realize the connection of multiple graphs by filling in the graph ID, graph name, host name, port number, username, and password information.

<center>
  <img src="/versions/1.0/docs/images/images-hubble/311图创建.png" alt="image">
</center>


Create graph by filling in the content as follows:：

<center>
  <img src="/versions/1.0/docs/images/images-hubble/311图创建2.png" alt="image">
</center>


##### 3.1.2	Graph Access
Realize the information access of the graph space. After entering, you can perform operations such as multidimensional query analysis, metadata management, data import, and algorithm analysis of the graph.

<center>
  <img src="/versions/1.0/docs/images/images-hubble/312图访问.png" alt="image">
</center>


##### 3.1.3	Graph management
1. Users can achieve unified management of graphs through overview, search, and information editing and deletion of single graphs.
2. Search range: You can search for the graph name and ID.

<center>
  <img src="/versions/1.0/docs/images/images-hubble/313图管理.png" alt="image">
</center>


#### 3.2	Metadata Modeling (list + graph mode)
##### 3.2.1	Module entry
Left navigation:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/321元数据入口.png" alt="image">
</center>


##### 3.2.2	Property type
###### 3.2.2.1	Create type
1. Fill in or select the attribute name, data type, and cardinality to complete the creation of the attribute.
2. Created attributes can be used as attributes of vertex type and edge type.

List mode：

<center>
  <img src="/versions/1.0/docs/images/images-hubble/3221属性创建.png" alt="image">
</center>


Graph mode：

<center>
  <img src="/versions/1.0/docs/images/images-hubble/3221属性创建2.png" alt="image">
</center>


###### 3.2.2.2	Reuse
1. The platform provides the [Reuse] function, which can directly reuse the metadata of other graphs.
2. Select the graph ID that needs to be reused, and continue to select the attributes that need to be reused. After that, the platform will check whether there is a conflict. After passing, the metadata can be reused.

Select reuse items:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/3222属性复用.png" alt="image">
</center>


Check reuse items:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/3222属性复用2.png" alt="image">
</center>


###### 3.2.2.3	Management
1. You can delete a single item or delete it in batches in the attribute list.

##### 3.2.3	Vertex type
###### 3.2.3.1	Create type
1. Fill in or select the vertex type name, ID strategy, association attribute, primary key attribute, vertex style, content displayed below the vertex in the query result, and index information: including whether to create a type index, and the specific content of the attribute index, complete the vertex Type creation.

List mode:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/3231顶点创建.png" alt="image">
</center>


Graph mode:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/3231顶点创建2.png" alt="image">
</center>

###### 3.2.3.2 Reuse
1. The multiplexing of vertex types will reuse the attributes and attribute indexes associated with this type together.
2. The reuse method is similar to the property reuse, see 3.2.2.2.

###### 3.2.3.3 Administration
1. Editing operations are available. The vertex style, association type, vertex display content, and attribute index can be edited, and the rest cannot be edited.

2. You can delete a single item or delete it in batches.

<center>
  <img src="/versions/1.0/docs/images/images-hubble/3233顶点删除.png" alt="image">
</center>


##### 3.2.4 Edge Types
###### 3.2.4.1 Create
1. Fill in or select the edge type name, start point type, end point type, associated attributes, whether to allow multiple connections, edge style, content displayed below the edge in the query result, and index information: including whether to create a type index, and attribute index The specific content, complete the creation of the edge type.

List mode:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/3241边创建.png" alt="image">
</center>


Graph mode：

<center>
  <img src="/versions/1.0/docs/images/images-hubble/3241边创建2.png" alt="image">
</center>


###### 3.2.4.2 Reuse
1. The reuse of the edge type will reuse the start point type, end point type, associated attribute and attribute index of this type.
2. The reuse method is similar to the property reuse, see 3.2.2.2.


###### 3.2.4.3 Administration
1. Editing operations are available. Edge styles, associated attributes, edge display content, and attribute indexes can be edited, and the rest cannot be edited, the same as the vertex type.
2. You can delete a single item or delete it in batches.

##### 3.2.5 Index Types
Displays vertex and edge indices for vertex types and edge types.

#### 3.3 Data Import
The usage process of data import is as follows:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/33导入流程.png" alt="image">
</center>


##### 3.3.1	Module entrance
Left navigation:
<center>
  <img src="/versions/1.0/docs/images/images-hubble/331导入入口.png" alt="image">
</center>


##### 3.3.2 Create task
1. Fill in the task name and remarks (optional) to create an import task.
2. Multiple import tasks can be created and imported in parallel.

<center>
  <img src="/versions/1.0/docs/images/images-hubble/332创建任务.png" alt="image">
</center>


##### 3.3.3 Uploading files
1. Upload the file that needs to be composed. The currently supported format is CSV, which will be updated continuously in the future.
2. Multiple files can be uploaded at the same time.

<center>
  <img src="/versions/1.0/docs/images/images-hubble/333上传文件.png" alt="image">
</center>


##### 3.3.4 Setting up data mapping
1. Set up data mapping for uploaded files, including file settings and type settings
2. File settings: Check or fill in whether to include the header, separator, encoding format and other settings of the file itself, all set the default values, no need to fill in manually
3. Type setting:

     1. Vertex map and edge map:

        【Vertex Type】: Select the vertex type, and upload the column data in the file for its ID mapping;

        【Edge Type】: Select the edge type and map the column data of the uploaded file to the ID column of its start point type and end point type;
     2. Mapping settings: upload the column data in the file for the attribute mapping of the selected vertex type. Here, if the attribute name is the same as the header name of the file, the mapping attribute can be automatically matched, and there is no need to manually fill in the selection.
     3. After completing the setting, the setting list will be displayed before proceeding to the next step. It supports the operations of adding, editing and deleting mappings.

Fill in the settings map:

  <center>
      <img src="/versions/1.0/docs/images/images-hubble/334设置映射.png" alt="image">
  </center>


Mapping list：

  <center>
    <img src="/versions/1.0/docs/images/images-hubble/334设置映射2.png" alt="image">
  </center>


##### 3.3.5 Import data
Before importing, you need to fill in the import setting parameters. After filling in, you can start importing data into the gallery.
1. Import settings
- The import setting parameter items are as shown in the figure below, all set the default value, no need to fill in manually

<center>
  <img src="/versions/1.0/docs/images/images-hubble/335导入设置.png" alt="image">
</center>


2. Import details
- Click Start Import to start the file import task
- The import details provide the mapping type, import speed, import progress, time-consuming and the specific status of the current task set for each uploaded file, and can pause, resume, stop and other operations for each task
- If the import fails, you can view the specific reason

<center>
  <img src="/versions/1.0/docs/images/images-hubble/335导入详情.png" alt="image">
</center>


#### 3.4 Data Analysis
##### 3.4.1 Module entry
Left navigation:
<center>
  <img src="/versions/1.0/docs/images/images-hubble/341分析入口.png" alt="image">
</center>


##### 3.4.2 Multi-image switching
By switching the entrance on the left, flexibly switch the operation space of multiple graphs
<center>
  <img src="/versions/1.0/docs/images/images-hubble/342多图切换.png" alt="image">
</center>


##### 3.4.3 Graph Analysis and Processing
HugeGraph supports Gremlin, a graph traversal query language of Apache TinkerPop3. Gremlin is a general graph database query language. By entering Gremlin statements and clicking execute, you can perform query and analysis operations on graph data, and create and delete vertices/edges. , vertex/edge attribute modification, etc.

After Gremlin query, below is the graph result display area, which provides 3 kinds of graph result display modes: [Graph Mode], [Table Mode], [Json Mode].

Support zoom, center, full screen, export and other operations.

【Picture Mode】
<center>
  <img src="/versions/1.0/docs/images/images-hubble/343图分析-图.png" alt="image">
</center>


【Table mode】
<center>
  <img src="/versions/1.0/docs/images/images-hubble/343图分析-表格.png" alt="image">
</center>


【Json mode】
<center>
  <img src="/versions/1.0/docs/images/images-hubble/343图分析-json.png" alt="image">
</center>


##### 3.4.4 Data Details
Click the vertex/edge entity to view the data details of the vertex/edge, including: vertex/edge type, vertex ID, attribute and corresponding value, expand the information display dimension of the graph, and improve the usability.


##### 3.4.5 Multidimensional Path Query of Graph Results
In addition to the global query, in-depth customized query and hidden operations can be performed for the vertices in the query result to realize customized mining of graph results.

Right-click a vertex, and the menu entry of the vertex appears, which can be displayed, inquired, hidden, etc.
- Expand: Click to display the vertices associated with the selected point.
- Query: By selecting the edge type and edge direction associated with the selected point, and then selecting its attributes and corresponding filtering rules under this condition, a customized path display can be realized.
- Hide: When clicked, hides the selected point and its associated edges.

Double-clicking a vertex also displays the vertex associated with the selected point.

<center>
  <img src="/versions/1.0/docs/images/images-hubble/345定制路径查询.png" alt="image">
</center>


##### 3.4.6 Add vertex/edge
###### 3.4.6.1 Added vertex
In the graph area, two entries can be used to dynamically add vertices, as follows:
1. Click on the graph area panel, the Add Vertex entry appears
2. Click the first icon in the action bar in the upper right corner

Complete the addition of vertices by selecting or filling in the vertex type, ID value, and attribute information.

The entry is as follows:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/346新增顶点.png" alt="image">
</center>


Add the vertex content as follows:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/346新增顶点2.png" alt="image">
</center>


###### 3.4.6.2 Add edge
Right-click a vertex in the graph result to add the outgoing or incoming edge of that point.


##### 3.4.7 Execute the query of records and favorites
1. Record each query record at the bottom of the graph area, including: query time, execution type, content, status, time-consuming, as well as [collection] and [load] operations, to achieve a comprehensive record of graph execution, with traces to follow, and Can quickly load and reuse execution content
2. Provides the function of collecting sentences, which can be used to collect frequently used sentences, which is convenient for fast calling of high-frequency sentences.

<center>
  <img src="/versions/1.0/docs/images/images-hubble/347收藏.png" alt="image">
</center>


#### 3.5 Task Management
##### 3.5.1 Module entry
Left navigation:
<center>
   <img src="/versions/1.0/docs/images/images-hubble/351任务管理入口.png" alt="image">
</center>


##### 3.5.2 Task Management
1. Provide unified management and result viewing of asynchronous tasks. There are 4 types of asynchronous tasks, namely:
- gremlin: Gremlin tasks
- algorithm: OLAP algorithm task
- remove_schema: remove metadata
- rebuild_index: rebuild the index
2. The list displays the asynchronous task information of the current graph, including: task ID, task name, task type, creation time, time-consuming, status, operation, and realizes the management of asynchronous tasks.
3. Support filtering by task type and status
4. Support searching for task ID and task name
5. Asynchronous tasks can be deleted or deleted in batches

<center>
  <img src="/versions/1.0/docs/images/images-hubble/352任务列表.png" alt="image">
</center>


##### 3.5.3 Gremlin asynchronous tasks
1. Create a task

- The data analysis module currently supports two Gremlin operations, Gremlin query and Gremlin task; if the user switches to the Gremlin task, after clicking execute, an asynchronous task will be created in the asynchronous task center;
2. Task submission
- After the task is submitted successfully, the graph area returns the submission result and task ID
3. Mission details
- Provide [View] entry, you can jump to the task details to view the specific execution of the current task After jumping to the task center, the currently executing task line will be displayed directly

<center>
  <img src="/versions/1.0/docs/images/images-hubble/353gremlin任务.png" alt="image">
</center>


Click to view the entry to jump to the task management list, as follows:

<center>
  <img src="/versions/1.0/docs/images/images-hubble/353gremlin任务2.png" alt="image">
</center>


4. View the results
- The results are displayed in the form of json


##### 3.5.4 OLAP algorithm tasks
There is no visual OLAP algorithm execution on Hubble. You can call the RESTful API to perform OLAP algorithm tasks, find the corresponding tasks by ID in the task management, and view the progress and results.

##### 3.5.5 Delete metadata, rebuild index
1. Create a task
- In the metadata modeling module, when deleting metadata, an asynchronous task for deleting metadata can be created

<center>
  <img src="/versions/1.0/docs/images/images-hubble/355删除元数据.png" alt="image">
</center>


- When editing an existing vertex/edge type operation, when adding an index, an asynchronous task of creating an index can be created
<center>
  <img src="/versions/1.0/docs/images/images-hubble/355构建索引.png" alt="image">
</center>


2. Task details
- After confirming/saving, you can jump to the task center to view the details of the current task

<center>
  <img src="/versions/1.0/docs/images/images-hubble/355任务详情.png" alt="image">
</center>
