---
title: "HugeGraph-Hubble Quick Start"
linkTitle: "使用 Hubble 实现图可视化"
weight: 1
---

### 1 HugeGraph-Hubble 概述

Hubble 已提供登录页面和会话校验。部署时仍应限制网络访问，并为 HugeGraph Server 配置认证；不要把未加固的实例直接暴露在公网。
>
> **测试指南**：如需在本地运行 Hubble 测试，请参考 [工具链本地测试指南](/cn/docs/guides/toolchain-local-test)

HugeGraph-Hubble 是 HugeGraph 的 Web 管理界面，可用于管理图连接和 Schema、导入数据、执行 Gremlin 查询并查看图形化结果。

平台主要包括以下模块：

##### 图管理

图管理用于创建和维护连接，可在多个图之间切换，并执行访问、编辑、删除和查询操作。

##### 元数据建模

元数据建模用于管理 PropertyKey、VertexLabel、EdgeLabel 和 IndexLabel。页面提供列表与图两种视图，也可以在图之间复用元数据。

##### 图分析

图分析页面可以执行 Gremlin 和路径查询，并用图、表格或 JSON 显示结果。页面还保存执行记录和收藏语句，查询结果可以导出为 JSON。

##### 任务管理

任务管理页面用于查看 Gremlin 异步任务、索引创建和重建等后台任务。

##### 数据导入 (BETA)

> 数据导入页面适合小规模试用。大批量或生产导入请使用 [HugeGraph Loader](/cn/docs/quickstart/toolchain/hugegraph-loader)。

数据导入页面按步骤创建任务、上传文件并配置字段映射，可并行运行多个导入任务，也支持断点续传和错误重试。

### 2 部署

有三种方式可以部署`hugegraph-hubble`

- 使用 docker (便于**测试**)
- 下载 toolchain 二进制包
- 源码编译

#### 2.1 使用 Docker (便于**测试**)

> **特别注意**: docker 模式下，若 hubble 和 server 在同一宿主机，hubble 页面中设置 server 的 `hostname` **不能设置**为 `localhost/127.0.0.1`，因这会指向 hubble **容器内部**而非宿主机，导致无法连接到 server.
> 
> 若 hubble 和 server 在同一 docker 网络下，**推荐**直接使用`container_name` (如下例的 `server`) 作为主机名。或者也可以使用 **宿主机 IP** 作为主机名，此时端口号为宿主机给 server 配置的端口

我们可以使用 `docker run -itd --name=hubble -p 8088:8088 hugegraph/hubble:1.5.0` 快速启动 [hubble](https://hub.docker.com/r/hugegraph/hubble).

或者使用 docker-compose 启动 hubble，另外如果 hubble 和 server 在同一个 docker 网络下，可以使用 server 的 contain_name 进行访问，而不需要宿主机的 ip

使用`docker-compose up -d`，`docker-compose.yml`如下：

```yaml
version: '3'
services:
  server:
    image: hugegraph/hugegraph:1.5.0
    container_name: server
    environment:
      - PASSWORD=xxx
    ports:
      - 8080:8080

  hubble:
    image: hugegraph/hubble:1.5.0
    container_name: hubble
    ports:
      - 8088:8088
```

> 注意：
>
> 1. `hugegraph-hubble` 的 docker 镜像是一个便捷发布版本，用于快速测试试用 hubble，并非**ASF 官方发布物料包的方式**。你可以从 [ASF Release Distribution Policy](https://infra.apache.org/release-distribution.html#dockerhub) 中得到更多细节。
>
> 2. **生产环境**推荐使用 `release tag`(如 `1.5.0`) 稳定版。使用 `latest` tag 默认对应 master 最新代码。

#### 2.2 下载 toolchain 二进制包

`hubble`项目在`toolchain`项目中，首先下载`toolchain`的 tar 包

```bash
export VERSION=1.7.0
export ARCHIVE="apache-hugegraph-toolchain-incubating-${VERSION}"
wget "https://downloads.apache.org/hugegraph/${VERSION}/${ARCHIVE}.tar.gz"
tar -xvf "${ARCHIVE}.tar.gz"
cd "${ARCHIVE}/apache-hugegraph-hubble-incubating-${VERSION}"
```

运行`hubble`

```bash
bin/start-hubble.sh
```

启动完成后访问 `http://<host>:8088`。停止服务时执行 `bin/stop-hubble.sh`。

#### 2.3 源码编译

Hubble 的构建由 `hugegraph-hubble/hubble-dist/pom.xml` 中的 `frontend-maven-plugin` 安装 Node.js 18.20.8 和 Yarn 1.22.21，无需预先安装这两个工具。

下载 toolchain 源码包

```shell
git clone https://github.com/apache/hugegraph-toolchain.git
```

编译`hubble`, 它依赖 loader 和 client, 编译时需提前构建这些依赖 (后续可跳)

```shell
cd hugegraph-toolchain
python -m pip install -r hugegraph-hubble/hubble-dist/assembly/travis/requirements.txt
mvn install -pl hugegraph-client,hugegraph-loader -am -Dmaven.javadoc.skip=true -DskipTests -ntp

cd hugegraph-hubble
mvn -e package -Dmaven.javadoc.skip=true -Dmaven.test.skip=true -ntp
cd apache-hugegraph-hubble-*
```

启动`hubble`

```bash
bin/start-hubble.sh -d
```


### 3	平台使用流程

平台的模块使用流程如下：

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/2平台使用流程.png" alt="image">
</div>


### 4	平台使用说明
#### 4.1	图管理
##### 4.1.1	图创建
图管理模块下，点击【创建图】，通过填写图 ID、图名称、主机名、端口号、用户名、密码的信息，实现多图的连接。

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/311图创建.png" alt="image">
</div>


创建图填写内容如下：

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/311图创建2.png" alt="image">
</div>

> **注意**：如果使用 docker 启动 `hubble`，且 `server` 和 `hubble` 位于同一宿主机，不能直接使用 `localhost/127.0.0.1` 作为主机名。如果 `hubble` 和 `server` 在同一 docker 网络下，则可以直接使用 container_name 作为主机名，端口则为 8080。或者也可以使用宿主机 ip 作为主机名，此时端口为宿主机为 server 配置的端口

##### 4.1.2	图访问
实现图空间的信息访问，进入后，可进行图的多维查询分析、元数据管理、数据导入、算法分析等操作。

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/312图访问.png" alt="image">
</div>


##### 4.1.3	图管理
1. 用户通过对图的概览、搜索以及单图的信息编辑与删除，实现图的统一管理。
2. 搜索范围：可对图名称和 ID 进行搜索。

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/313图管理.png" alt="image">
</div>


#### 4.2	元数据建模（列表 + 图模式）
##### 4.2.1	模块入口
左侧导航处：

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/321元数据入口.png" alt="image">
</div>


##### 4.2.2	属性类型
###### 4.2.2.1	创建
1.	填写或选择属性名称、数据类型、基数，完成属性的创建。
2.	创建的属性可作为顶点类型和边类型的属性。

列表模式：

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/3221属性创建.png" alt="image">
</div>


图模式：

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/3221属性创建2.png" alt="image">
</div>


###### 4.2.2.2	复用
1.	平台提供【复用】功能，可直接复用其他图的元数据。
2.  选择需要复用的图 ID，继续选择需要复用的属性，之后平台会进行是否冲突的校验，通过后，可实现元数据的复用。

选择复用项：

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/3222属性复用.png" alt="image">
</div>


校验复用项：

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/3222属性复用2.png" alt="image">
</div>


###### 4.2.2.3	管理
1.	在属性列表中可进行单条删除或批量删除操作。

##### 4.2.3	顶点类型
###### 4.2.3.1	创建
1.  填写或选择顶点类型名称、ID 策略、关联属性、主键属性，顶点样式、查询结果中顶点下方展示的内容，以及索引的信息：包括是否创建类型索引，及属性索引的具体内容，完成顶点类型的创建。

列表模式：

<center>
  <img src="/docs/images/images-hubble/3231顶点创建.png" alt="image">
</center>


图模式：

<center>
  <img src="/docs/images/images-hubble/3231顶点创建2.png" alt="image">
</center>


###### 4.2.3.2	复用
1.	顶点类型的复用，会将此类型关联的属性和属性索引一并复用。
2.	复用功能使用方法类似属性的复用，见 3.2.2.2。

###### 4.2.3.3	管理
1.	可进行编辑操作，顶点样式、关联类型、顶点展示内容、属性索引可编辑，其余不可编辑。


2.	可进行单条删除或批量删除操作。

<center>
  <img src="/docs/images/images-hubble/3233顶点删除.png" alt="image">
</center>


##### 4.2.4	边类型
###### 4.2.4.1	创建
1.	填写或选择边类型名称、起点类型、终点类型、关联属性、是否允许多次连接、边样式、查询结果中边下方展示的内容，以及索引的信息：包括是否创建类型索引，及属性索引的具体内容，完成边类型的创建。

列表模式：

<center>
  <img src="/docs/images/images-hubble/3241边创建.png" alt="image">
</center>


图模式：

<center>
  <img src="/docs/images/images-hubble/3241边创建2.png" alt="image">
</center>


###### 4.2.4.2	复用
1.	边类型的复用，会将此类型的起点类型、终点类型、关联的属性和属性索引一并复用。
2.	复用功能使用方法类似属性的复用，见 3.2.2.2。


###### 4.2.4.3	管理
1.	可进行编辑操作，边样式、关联属性、边展示内容、属性索引可编辑，其余不可编辑，同顶点类型。
2.	可进行单条删除或批量删除操作。

##### 4.2.5	索引类型
展示顶点类型和边类型的顶点索引和边索引。

#### 4.3	数据导入

> **注意**：目前推荐使用 [hugegraph-loader](/cn/docs/quickstart/toolchain/hugegraph-loader) 进行正式数据导入，hubble 内置的导入用来做**测试**和**简单上手**

数据导入的使用流程如下：

<center>
  <img src="/docs/images/images-hubble/33导入流程.png" alt="image">
</center>


##### 4.3.1	模块入口
左侧导航处：
<center>
  <img src="/docs/images/images-hubble/331导入入口.png" alt="image">
</center>


##### 4.3.2	创建任务
1.	填写任务名称和备注（非必填），可以创建导入任务。
2.	可创建多个导入任务，并行导入。

<center>
  <img src="/docs/images/images-hubble/332创建任务.png" alt="image">
</center>


##### 4.3.3	上传文件
1.	上传需要构图的文件，目前支持的格式为 CSV，后续会不断更新。
2.	可同时上传多个文件。

<center>
  <img src="/docs/images/images-hubble/333上传文件.png" alt="image">
</center>


##### 4.3.4	设置数据映射
1. 对上传的文件分别设置数据映射，包括文件设置和类型设置
2. 文件设置：勾选或填写是否包含表头、分隔符、编码格式等文件本身的设置内容，均设置默认值，无需手动填写
3. 类型设置：

    1.	顶点映射和边映射：

       【顶点类型】 ：选择顶点类型，并为其 ID 映射上传文件中列数据；

       【边类型】：选择边类型，为其起点类型和终点类型的 ID 列映射上传文件的列数据；
    2.	映射设置：为选定的顶点类型的属性映射上传文件中的列数据，此处，若属性名称与文件的表头名称一致，可自动匹配映射属性，无需手动填选
    3.	完成设置后，显示设置列表，方可进行下一步操作，支持映射的新增、编辑、删除操作

设置映射的填写内容：

  <center>
      <img src="/docs/images/images-hubble/334设置映射.png" alt="image">
  </center>


映射列表：

  <center>
    <img src="/docs/images/images-hubble/334设置映射2.png" alt="image">
  </center>


##### 4.3.5	导入数据
导入前需要填写导入设置参数，填写完成后，可开始向图库中导入数据
1.	导入设置
- 导入设置参数项如下图所示，均设置默认值，无需手动填写

<center>
  <img src="/docs/images/images-hubble/335导入设置.png" alt="image">
</center>


2.	导入详情
- 点击开始导入，开始文件的导入任务
- 导入详情中提供每个上传文件设置的映射类型、导入速度、导入的进度、耗时以及当前任务的具体状态，并可对每个任务进行暂停、继续、停止等操作
- 若导入失败，可查看具体原因

<center>
  <img src="/docs/images/images-hubble/335导入详情.png" alt="image">
</center>


#### 4.4	数据分析
##### 4.4.1	模块入口
左侧导航处：
<center>
  <img src="/docs/images/images-hubble/341分析入口.png" alt="image">
</center>


##### 4.4.2	多图切换
通过左侧切换入口，灵活切换多图的操作空间
<center>
  <img src="/docs/images/images-hubble/342多图切换.png" alt="image">
</center>


##### 4.4.3	图分析与处理
HugeGraph 支持 Apache TinkerPop3 的图遍历查询语言 Gremlin，Gremlin 是一种通用的图数据库查询语言，通过输入 Gremlin 语句，点击执行，即可执行图数据的查询分析操作，并可实现顶点/边的创建及删除、顶点/边的属性修改等。

Gremlin 查询后，下方为图结果展示区域，提供 3 种图结果展示方式，分别为：【图模式】、【表格模式】、【Json 模式】。

> ⚠️ **SEC 提醒**：Hubble 允许在网页端直接输入并执行 Gremlin 原生查询语句，这赋予了使用者较高的操作权限。**请避免将 Hubble 服务暴露在公网环境**，建议在使用时确保图数据库服务端已开启 **[鉴权体系 (Auth)](/cn/docs/config/config-authentication/)** 并配合 **IP 白名单**进行严格的权限控制，防止未授权访问或恶意代码执行风险。

支持缩放、居中、全屏、导出等操作。

【图模式】

<center>
  <img src="/docs/images/images-hubble/343图分析-图.png" alt="image">
</center>


【表格模式】
<center>
  <img src="/docs/images/images-hubble/343图分析-表格.png" alt="image">
</center>


【Json 模式】
<center>
  <img src="/docs/images/images-hubble/343图分析-json.png" alt="image">
</center>


##### 4.4.4	数据详情
点击顶点/边实体，可查看顶点/边的数据详情，包括：顶点/边类型，顶点 ID，属性及对应值，拓展图的信息展示维度，提高易用性。


##### 4.4.5	图结果的多维路径查询
除了全局的查询外，可针对查询结果中的顶点进行深度定制化查询以及隐藏操作，实现图结果的定制化挖掘。

右击顶点，出现顶点的菜单入口，可进行展示、查询、隐藏等操作。
-	展开：点击后，展示与选中点关联的顶点。
-	查询：通过选择与选中点关联的边类型及边方向，在此条件下，再选择其属性及相应筛选规则，可实现定制化的路径展示。
-	隐藏：点击后，隐藏选中点及与之关联的边。

双击顶点，也可展示与选中点关联的顶点。

<center>
  <img src="/docs/images/images-hubble/345定制路径查询.png" alt="image">
</center>


##### 4.4.6	新增顶点/边
###### 4.4.6.1	新增顶点
在图区可通过两个入口，动态新增顶点，如下：
1.	点击图区面板，出现添加顶点入口
2.	点击右上角的操作栏中的首个图标

通过选择或填写顶点类型、ID 值、属性信息，完成顶点的增加。

入口如下：

<center>
  <img src="/docs/images/images-hubble/346新增顶点.png" alt="image">
</center>


添加顶点内容如下：

<center>
  <img src="/docs/images/images-hubble/346新增顶点2.png" alt="image">
</center>


###### 4.4.6.2	新增边
右击图结果中的顶点，可增加该点的出边或者入边。


##### 4.4.7	执行记录与收藏的查询
1.	图区下方记载每次查询记录，包括：查询时间、执行类型、内容、状态、耗时、以及【收藏】和【加载】操作，实现图执行的全方位记录，有迹可循，并可对执行内容快速加载复用
2.	提供语句的收藏功能，可对常用语句进行收藏操作，方便高频语句快速调用

<center>
  <img src="/docs/images/images-hubble/347收藏.png" alt="image">
</center>


#### 4.5	任务管理
##### 4.5.1	模块入口
左侧导航处：
<center>
  <img src="/docs/images/images-hubble/351任务管理入口.png" alt="image">
</center>


##### 4.5.2	任务管理
1.  提供异步任务的统一的管理与结果查看，异步任务包括 4 类，分别为：
-   gremlin：Gremlin 任务务
-   algorithm：OLAP 算法任务务
- 	remove_schema：删除元数据
- 	rebuild_index：重建索引
2.	列表显示当前图的异步任务信息，包括：任务 ID，任务名称，任务类型，创建时间，耗时，状态，操作，实现对异步任务的管理。
3.	支持对任务类型和状态进行筛选
4.	支持搜索任务 ID 和任务名称
5.	可对异步任务进行删除或批量删除操作

<center>
  <img src="/docs/images/images-hubble/352任务列表.png" alt="image">
</center>


##### 4.5.3	Gremlin 异步任务
1.创建任务

- 数据分析模块，目前支持两种 Gremlin 操作，Gremlin 查询和 Gremlin 任务；若用户切换到 Gremlin 任务，点击执行后，在异步任务中心会建立一条异步任务；
2.任务提交
- 任务提交成功后，图区部分返回提交结果和任务 ID
3.任务详情
- 提供【查看】入口，可跳转到任务详情查看当前任务具体执行情况跳转到任务中心后，直接显示当前执行的任务行

<center>
  <img src="/docs/images/images-hubble/353gremlin任务.png" alt="image">
</center>


点击查看入口，跳转到任务管理列表，如下：

<center>
  <img src="/docs/images/images-hubble/353gremlin任务2.png" alt="image">
</center>


4.查看结果
- 结果通过 json 形式展示


##### 4.5.4	OLAP 算法任务
Hubble 上暂未提供可视化的 OLAP 算法执行，可调用 RESTful API 进行 OLAP 类算法任务，在任务管理中通过 ID 找到相应任务，查看进度与结果等。

##### 4.5.5	删除元数据、重建索引
1.创建任务
- 在元数据建模模块中，删除元数据时，可建立删除元数据的异步任务

<center>
  <img src="/docs/images/images-hubble/355删除元数据.png" alt="image">
</center>


- 在编辑已有的顶点/边类型操作中，新增索引时，可建立创建索引的异步任务

<center>
  <img src="/docs/images/images-hubble/355构建索引.png" alt="image">
</center>


2.任务详情
- 确认/保存后，可跳转到任务中心查看当前任务的详情

<center>
  <img src="/docs/images/images-hubble/355任务详情.png" alt="image">
</center>


### 5 配置说明

HugeGraph-Hubble 可以通过 `conf/hugegraph-hubble.properties` 文件进行配置。

#### 5.1 服务器配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `hubble.host` | `0.0.0.0` | Hubble 服务绑定的地址 |
| `hubble.port` | `8088` | Hubble 服务监听的端口 |

#### 5.2 Server 与 PD

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `pd.enabled` | `false` | 是否通过 PD 发现服务；单机 Server 保持为 `false` |
| `server.direct_url` | `http://127.0.0.1:8080` | `pd.enabled=false` 时连接的 Server 地址 |
| `pd.peers` | `127.0.0.1:8686` | PD 节点地址 |
| `pd.server` | `127.0.0.1:8620` | PD 服务地址 |
| `route.type` | `NODE_PORT` | 服务路由方式，可选 `NODE_PORT`、`DDS` 或 `BOTH` |

#### 5.3 Gremlin 查询限制

这些设置控制查询结果限制，防止内存问题：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `gremlin.suffix_limit` | `250` | 查询后缀最大长度 |
| `gremlin.vertex_degree_limit` | `100` | 显示的最大顶点度数 |
| `gremlin.edges_total_limit` | `500` | 返回的最大边数 |
| `gremlin.batch_query_ids` | `100` | ID 批量查询大小 |
