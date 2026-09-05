---
title: "HugeGraph-Hubble Quick Start"
linkTitle: "使用 Hubble 实现图可视化"
weight: 1
---

### 1 HugeGraph-Hubble 概述

> ⚠️ **安全提醒**：Hubble 监听的是明文 HTTP 端口，请勿将其暴露在公网或不受信任的网络中；应在其前面终结 HTTPS，并使用 IP/端口白名单限制访问。Hubble 自身不保存账号库：当所连接的 HugeGraph Server 开启了鉴权时，Hubble 会显示登录页并把凭据转发给 Server；当 Server 允许匿名访问时，则没有登录环节，账号相关页面也会隐藏。
>
> **版本说明**：本页对应 hugegraph-toolchain `master`。下文标注了依赖较新 Server、PD 或 Store 版本的功能，这些功能在旧版 Server 上不可用。
>
> **测试指南**：如需在本地运行 Hubble 测试，请参考 [工具链本地测试指南](/cn/docs/guides/toolchain-local-test)

HugeGraph-Hubble 是 HugeGraph 的 Web 管理界面。它连接到一个 HugeGraph Server（直连，或在分布式集群中通过 PD 发现），管理图空间（GraphSpace）、图和 Schema，导入数据，执行 Gremlin 与 Cypher 查询以及内置图算法，并将结果图形化展示。

平台主要包括以下模块：

##### 图概览

图概览列出图空间（PD 模式）和图，可以创建、克隆和清空图，加载 Demo 图，打开包含统计信息与 Schema 的图详情页，并跳转到查询工作台。

##### 元数据建模

元数据建模用于管理单个图的 PropertyKey、VertexLabel、EdgeLabel 和 IndexLabel，提供列表与图两种视图。Schema 模板按图空间保存可复用的 Groovy Schema，可在创建图时直接套用。

##### 数据导入

> 数据导入页面适合小规模试用。大批量或生产导入请使用 [HugeGraph Loader](/cn/docs/quickstart/toolchain/hugegraph-loader)。

数据源支持 FILE、HDFS、JDBC 和 KAFKA 四种类型。导入任务分四步配置，可以执行一次、按 cron 周期执行，或对 Kafka 源持续实时执行。

##### 图查询

图查询可以按立即查询或异步任务两种模式执行 Gremlin 与 Cypher 语句，并以图（2D 或 3D）、表格或 JSON 展示结果，同时保存执行记录与收藏语句。

##### 内置图算法

内置图算法为 Server 的 OLTP traverser 接口（交互式探索）以及 OLAP 任务（通过 HugeGraph Computer 或 Vermeer 进行集群批量计算）提供参数表单。

##### 异步任务

异步任务列出后台任务，包括 Gremlin 与 Cypher 任务、算法任务、删除元数据、创建与重建索引、Vermeer 图加载与图计算任务，并支持查看详情、取消和删除。

##### 系统与运维

系统与运维包含个人中心、带图空间权限预设的账号管理，以及 PD 模式下的集群概览与节点详情。

#### 1.1 版本兼容性

Hubble 会自动探测所连接 Server 的鉴权模式与能力，自身没有单独的鉴权开关。支持的组合如下：

| HugeGraph Server / PD | 部署方式 | Hubble 兼容性 | 范围与限制 |
|---|---|---|---|
| Server 1.5.x | 单机，通常不开启鉴权 | 最低兼容 | 仅支持基础的图、Schema、数据和 Gremlin 流程。图空间、账号权限、PD/Store 拓扑、集群运维和较新的算法均不可用。 |
| Server 1.7.x 搭配同版本 PD/Store 1.7.x | 单机或分布式 | 通过兼容适配达到最低可用 | 核心管理与查询流程仍可使用，但旧版 REST/Gremlin 鉴权、权限语义、指标和算法能力的体验会有所降级。 |
| Server、PD 和 Store 1.8.x 及以上 | 推荐分布式部署 | 完整且推荐的体验 | 图空间、账号权限预设、集群运维、异步任务和算法能力处理都是针对这一代设计并验证的。 |

分布式集群中请使用版本号一致的 Server、PD 和 Store。

### 2 部署

有三种方式可以部署`hugegraph-hubble`

- 使用 docker (便于**测试**)
- 下载 toolchain 二进制包
- 源码编译

Hubble 运行在 Java 11 上：后端以 `java.version=11` 编译，Docker 镜像基于 `eclipse-temurin:11-jre`。`bin/start-hubble.sh` 只检查 `PATH` 中是否存在 `java`，因此请自行确认选用的是正确的 JDK。

#### 2.1 使用 Docker (便于**测试**)

> **特别注意**：Hubble 已不再在页面上填写 Server 的主机名和端口。Server 地址来自 `conf/hugegraph-hubble.properties`：`pd.enabled=false` 时使用 `server.direct_url`，`pd.enabled=true` 时通过 `pd.peers` 由 PD 发现。容器内的 `127.0.0.1` 指向 hubble 容器自身，因此打包默认值 `server.direct_url=http://127.0.0.1:8080` 无法访问到另一个容器里的 Server。
>
> 若 hubble 和 server 在同一 docker 网络下，**推荐**直接使用`container_name` (如下例的 `server`) 作为主机名。或者也可以使用 **宿主机 IP** 作为主机名，此时端口号为宿主机给 server 配置的端口

镜像会把打包产物复制到 `/hubble`，把 `/hubble/conf/hugegraph-hubble.properties` 中的 `server.host` 改写为 `0.0.0.0`、清空 `dashboard.address`，暴露 `8088` 端口，并以 `./bin/start-hubble.sh -f` 前台方式启动。

先准备一份指向你的 Server、并让容器监听所有网卡的 `hugegraph-hubble.properties`：

```properties
server.host=0.0.0.0
server.port=8088
pd.enabled=false
server.direct_url=http://server:8080
```

然后把该文件挂载覆盖打包配置来启动 [hubble](https://hub.docker.com/r/hugegraph/hubble)：

```bash
docker run -itd --name=hubble -p 8088:8088 \
  -v "$PWD/hugegraph-hubble.properties:/hubble/conf/hugegraph-hubble.properties" \
  hugegraph/hubble:1.7.0
```

或者使用 docker-compose 启动 hubble，另外如果 hubble 和 server 在同一个 docker 网络下，可以使用 server 的 container_name 进行访问，而不需要宿主机的 ip

使用`docker-compose up -d`，`docker-compose.yml`如下：

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

> 注意：
>
> 1. `hugegraph-hubble` 的 docker 镜像是一个便捷发布版本，用于快速测试试用 hubble，并非**ASF 官方发布物料包的方式**。你可以从 [ASF Release Distribution Policy](https://infra.apache.org/release-distribution.html#dockerhub) 中得到更多细节。
>
> 2. **生产环境**推荐使用 `release tag`(如 `1.7.0`) 稳定版。使用 `latest` tag 默认对应 master 最新代码。

#### 2.2 下载 toolchain 二进制包

`hubble`项目在`toolchain`项目中，首先下载`toolchain`的 tar 包

```bash
export VERSION=1.7.0
export ARCHIVE="apache-hugegraph-toolchain-incubating-${VERSION}"
wget "https://downloads.apache.org/hugegraph/${VERSION}/${ARCHIVE}.tar.gz"
tar -xvf "${ARCHIVE}.tar.gz"
cd "${ARCHIVE}/apache-hugegraph-hubble-incubating-${VERSION}"
```

先修改 `conf/hugegraph-hubble.properties`，把 Server 地址配置正确，然后运行`hubble`

```bash
bin/start-hubble.sh
```

`start-hubble.sh` 支持以下参数：

| 参数 | 说明 |
|------|------|
| `-f`、`--foreground [true\|false]` | 前台运行而不是以守护进程方式运行，Docker 镜像使用 `-f` |
| `-d`、`--debug` | 在 `8787` 端口开启 JDWP 调试（`server=y,suspend=n`） |

脚本以 `-Xms512m -Dfile.encoding=UTF-8 -Dhubble.home.path=<安装目录>` 启动 JVM，把 PID 写入 `bin/pid`，日志输出到 `logs/hugegraph-hubble.log`，并最多等待 30 秒直到 `http://<server.host>:<server.port>/about` 有响应后才返回。

打包默认值为 `server.host=localhost`，即在修改之前只接受本机回环访问。启动完成后访问 `http://<host>:8088`。

停止服务时执行 `bin/stop-hubble.sh`：它先发送 `SIGTERM`，让关闭钩子暂停正在运行的导入任务并干净地关闭内置 H2 数据库；只有在 `STOP_TIMEOUT` 秒（环境变量，默认 `30`）后进程仍然存活时，才会升级为 `SIGKILL`。

#### 2.3 源码编译

Hubble 的构建由 `hugegraph-hubble/hubble-dist/pom.xml` 中的 `frontend-maven-plugin` 安装 Node.js v18.20.8 和 Yarn v1.22.21，无需预先安装这两个工具。此外需要 JDK 11 和 Maven。

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

前端开发时可在 `hubble-fe` 目录下执行 `yarn dev`。后端 POM 未配置 `spring-boot:run`，请改为从 `hubble-be/target/classes` 启动 `org.apache.hugegraph.HugeGraphHubble`，并用 `-Dhubble.home.path` 指向一个可写目录。


### 3	平台使用流程

首页把各模块归纳为三条主线：图概览、图导入和图查询，同时显示当前运行在 PD / 集群模式还是 non-PD 单机模式。平台的模块使用流程如下：

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/2平台使用流程.png" alt="image">
</div>


### 4	平台使用说明
#### 4.1	图管理
在 PD 模式下，【图空间管理】列出集群中的所有图空间，并可创建或编辑图空间，包括别名、可选的 Kubernetes 命名空间与计算任务，以及资源上限。在 non-PD 单机模式下只有一个名为 `DEFAULT` 的图空间，图空间列表会被跳过。

##### 4.1.1	图创建
图管理模块下，点击【新建图】，填写图名称、可选的别名、可选的 Schema 模板和示例数据。图名称在其所属图空间内唯一，创建后不可修改。

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/311图创建.png" alt="image">
</div>


创建图填写内容如下：

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/311图创建2.png" alt="image">
</div>

> **注意**：Server 连接不在此页面配置，而是来自 `conf/hugegraph-hubble.properties`，通过 `server.direct_url` 或 PD 发现获得，Docker 下的主机名规则见 2.1 节。只有当所连接的 Server 提供建图能力（REST API 0.67 及以上）时才会显示新建图入口，旧版 Server 上图列表为只读。

##### 4.1.2	图访问
实现图空间的信息访问，进入后，可进行图的多维查询分析、元数据管理、数据导入、算法分析等操作。【进入图分析平台】打开查询工作台，【元数据配置】打开 Schema 页面，图详情页展示顶点/边统计信息和 Schema。

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/312图访问.png" alt="image">
</div>


##### 4.1.3	图管理
1. 图列表提供卡片视图和列表视图，搜索按图名称匹配。
2. 单图操作包括：查看 schema（可【导出 Groovy Schema】）、元数据配置、克隆图（仅 Schema，或 Schema 与数据）、清空 Schema 与数据、删除，以及 PD 模式下的设为默认。
3. 【示例数据与资源】可在当前图中构建 Demo 图：红楼梦 Demo 图、人物与软件 Demo 图、迷你电影 Rank Demo。这些 Demo 只补齐缺失的 Schema 和元素，不会清空已有数据。

<div style="text-align: center;">
  <img src="/docs/images/images-hubble/313图管理.png" alt="image">
</div>


#### 4.2	元数据建模（列表 + 图模式）
##### 4.2.1	模块入口
从图列表进入【元数据配置】，或直接访问图的元数据页面 `/graphspace/<graphspace>/graph/<graph>/meta`。页面包含属性、顶点类型、边类型、顶点索引、边索引五个标签页，并可在列表视图和图视图之间切换。

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


###### 4.2.2.2	管理
1.	在属性列表中可进行单条删除或批量删除操作，已被顶点类型或边类型使用的属性无法删除。
2.	删除元数据会以异步任务方式执行，可在异步任务中查看进度。

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


###### 4.2.3.2	管理
1.	可进行编辑操作，顶点样式、关联属性、顶点展示内容、属性索引可编辑，其余不可编辑。图模式下双击顶点类型即可编辑。


2.	可进行单条删除或批量删除操作。

<center>
  <img src="/docs/images/images-hubble/3233顶点删除.png" alt="image">
</center>


##### 4.2.4	边类型
###### 4.2.4.1	创建
1.	填写或选择边类型名称、类型（普通类型、父边类型或子边类型，用于边类型的层级关系）、起点类型、终点类型、关联属性、是否允许多次连接、边样式、查询结果中边下方展示的内容，以及索引的信息：包括是否创建类型索引，及属性索引的具体内容，完成边类型的创建。

列表模式：

<center>
  <img src="/docs/images/images-hubble/3241边创建.png" alt="image">
</center>


图模式：

<center>
  <img src="/docs/images/images-hubble/3241边创建2.png" alt="image">
</center>


###### 4.2.4.2	管理
1.	可进行编辑操作，边样式、关联属性、边展示内容、属性索引可编辑，其余不可编辑，同顶点类型。
2.	可进行单条删除或批量删除操作。

##### 4.2.5	索引类型
展示顶点类型和边类型的顶点索引和边索引，支持二级索引、范围索引、全文索引和唯一索引。

##### 4.2.6	Schema 模板
【Schema 模板】（`/graphspace/<graphspace>/schema`）按图空间维护一份可复用的模板库。示例模板由 Hubble 内置，可以使用、移除和恢复，在保存之前不会写入 Server；用户模板以 Groovy Schema 形式保存在 Server 上，可以创建、编辑和删除。创建图时可以选择已有模板，使其 Schema 立即生效。

#### 4.3	数据导入

> **注意**：目前推荐使用 [hugegraph-loader](/cn/docs/quickstart/toolchain/hugegraph-loader) 进行正式数据导入，hubble 内置的导入用来做**测试**和**简单上手**

数据导入的使用流程如下：

<center>
  <img src="/docs/images/images-hubble/33导入流程.png" alt="image">
</center>


##### 4.3.1	模块入口
左侧导航「图导入」下的【数据源管理】和【数据导入】：
<center>
  <img src="/docs/images/images-hubble/331导入入口.png" alt="image">
</center>


##### 4.3.2	数据源
1.	【数据源管理】用于登记导入任务的读取来源，支持四种类型：FILE（本地上传）、HDFS、Kafka 和 JDBC。
2.	FILE 类型需要上传需要构图的文件，可接受的格式由 `upload_file.format_list` 决定，默认为 `csv` 和 `txt`。
3.	单文件与总大小上限默认分别为 1 GB 和 10 GB，未完成的上传分片会在 `upload_file.max_uploading_time`（默认 12 小时）后被清理。

<center>
  <img src="/docs/images/images-hubble/333上传文件.png" alt="image">
</center>


##### 4.3.3	创建任务
1.	【数据导入】>【创建任务】分四步配置：输入基础信息、选择源端字段、选择映射字段、输入调度信息。
2.	基础信息包括任务名称（1 到 48 个中文、字母、数字或 `_`）、目标图空间与图、源端类型和数据源。
3.	可创建多个导入任务，并行导入。

<center>
  <img src="/docs/images/images-hubble/332创建任务.png" alt="image">
</center>


##### 4.3.4	设置数据映射
1. 对选定的数据源设置数据映射，包括文件设置和类型设置
2. 文件设置：勾选或填写是否包含表头、分隔符、编码格式等源端本身的设置内容，均设置默认值，无需手动填写
3. 类型设置：

    1.	顶点映射和边映射：

       【顶点类型】 ：选择顶点类型，并为其 ID 映射源端中的列数据；

       【边类型】：选择边类型，为其起点类型和终点类型的 ID 列映射源端的列数据；
    2.	映射设置：为选定的顶点类型的属性映射源端中的列数据，此处，若属性名称与文件的表头名称一致，可自动匹配映射属性，无需手动填选
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
最后一步选择任务的执行方式：执行一次表示一次性导入，周期执行使用 Quartz cron 表达式（例如 `0 0/5 * * * ?`），实时执行用于 Kafka 数据源。
1.	导入设置
- 导入设置参数项如下图所示，均设置默认值，无需手动填写

<center>
  <img src="/docs/images/images-hubble/335导入设置.png" alt="image">
</center>


2.	导入详情
- 在任务列表中运行任务即可开始导入，也可在同一列表中暂停、编辑或删除任务
- 任务的执行历史提供每次执行的执行实例 ID、导入记录数、平均速率（条/秒）、导入耗时和状态
- 若导入失败，可查看具体原因

<center>
  <img src="/docs/images/images-hubble/335导入详情.png" alt="image">
</center>


#### 4.4	图查询
##### 4.4.1	模块入口
左侧导航「图查询」下的【GQL 图遍历】：
<center>
  <img src="/docs/images/images-hubble/341分析入口.png" alt="image">
</center>


##### 4.4.2	多图切换
顶部栏承载当前图空间和图，可在不离开页面的情况下灵活切换多图的操作空间
<center>
  <img src="/docs/images/images-hubble/342多图切换.png" alt="image">
</center>


##### 4.4.3	图分析与处理
HugeGraph 支持 Apache TinkerPop3 的图遍历查询语言 Gremlin，Gremlin 是一种通用的图数据库查询语言，通过输入 Gremlin 语句，点击执行，即可执行图数据的查询分析操作，并可实现顶点/边的创建及删除、顶点/边的属性修改等。当所连接的 Server 支持 Cypher 时，Gremlin 旁边会出现 Cypher 页签。Text2GQL 页签仅为界面预览，并未接入任何模型或查询服务，其中输入的内容不会被发送或执行。

每条语句可以按两种模式执行：立即查询直接返回结果，适合 30 秒内可完成的小规模分析；异步执行则提交一个任务，进度和结果在异步任务中查看。`Ctrl`/`Command` + `Enter` 可执行当前语句。

查询后，下方为图结果展示区域，提供 3 种图结果展示方式，分别为：【图模式】、【表格模式】、【Json 模式】。图画布支持 2D 与 3D 渲染。

> ⚠️ **SEC 提醒**：Hubble 允许在网页端直接输入并执行 Gremlin 原生查询语句，这赋予了使用者较高的操作权限。**请避免将 Hubble 服务暴露在公网环境**，建议在使用时确保图数据库服务端已开启 **[鉴权体系 (Auth)](/cn/docs/config/config-authentication/)** 并配合 **IP 白名单**进行严格的权限控制，防止未授权访问或恶意代码执行风险。

支持缩放、居中、全屏、布局与样式配置、图例、缩略图、撤销与重做、导出等操作。画布可导出为 JSON、CSV 或图片，导出的画布也可以再次导入。

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


#### 4.5	异步任务
##### 4.5.1	模块入口
左侧导航「图查询」下的【异步任务】：
<center>
  <img src="/docs/images/images-hubble/351任务管理入口.png" alt="image">
</center>


##### 4.5.2	任务管理
1.  提供异步任务的统一的管理与结果查看，任务类型包括：
-   gremlin：Gremlin 任务
-   cypher：Cypher 任务
-   computer-dis：算法任务
- 	remove_schema：删除元数据
- 	create_index：创建索引
- 	rebuild_index：重建索引
- 	vermeer-task:load：Vermeer 图加载任务
- 	vermeer-task:compute：Vermeer 图计算任务
2.	列表显示当前图的异步任务信息，包括：任务 ID，任务名称，任务类型，创建时间，耗时，状态，操作，实现对异步任务的管理。列表每 5 秒自动刷新一次。
3.	支持对任务类型和状态进行筛选
4.	支持搜索任务 ID 和任务名称
5.	运行中的任务可以取消，异步任务可进行删除或批量删除操作

<center>
  <img src="/docs/images/images-hubble/352任务列表.png" alt="image">
</center>


##### 4.5.3	Gremlin 异步任务
1.创建任务

- 图查询模块支持两种执行方式：立即查询和异步任务；若用户切换到异步方式，点击执行后，在异步任务中心会建立一条异步任务；Cypher 语句同理会建立一条 Cypher 任务；
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
- 结果通过 json 形式展示，较长的结果可以就地展开


##### 4.5.4	算法任务
从【内置图算法】提交的批量算法会在这里以算法任务的形式出现，Vermeer 的图加载与图计算任务同理。可在列表中通过 ID 找到相应任务，打开后查看进度与结果等。算法表单本身见 4.6 节。

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


#### 4.6	内置图算法

「图查询」下的【内置图算法】为 Server 提供的算法给出参数表单，并按用途分组：探索邻居、寻找路径与连接、比较与排序、度量重要性、发现社区、分析图结构。每个算法都提供指向官方 API 文档的链接。

支持两种执行方式：

- 交互式探索调用 Server 的 OLTP traverser 接口并直接返回结果，覆盖 K-out 与 K-neighbor，单源、带权和多点形式的最短路径，路径与全部路径，定制化路径与模板路径，环与射线，交点与定制化交点，共同邻居，Jaccard 相似度，Fusiform 相似度，Adamic-Adar，资源分配，Egonet，以及 rank 与 neighbor rank 接口。
- 集群批量计算提交一个覆盖全图的异步任务，结果在异步任务中查看，覆盖 PageRank 与个性化 PageRank，度中心性、接近中心性与介数中心性，K-core，弱连通分量，标签传播，Louvain，三角形计数，聚类系数，环检测，子图匹配与 Links；在提供 Vermeer 的部署中还有对应的 Vermeer 版本。

批量算法需要 HugeGraph Computer 环境，部署要求时还包括 Kubernetes。当无法访问 Computer 时，页面会直接提示而不会提交任务。

#### 4.7	登录与账号管理

当所连接的 Server 开启了鉴权时，Hubble 会打开 `/login` 登录页。请使用 HugeGraph Server 账号登录：Hubble 会把凭据转发给 Server，并在浏览器会话中保存返回的 token，自身不存储任何账号。登录尝试受限流保护，同一账号与地址连续失败三次之后，后续尝试会开始退避，初始 5 秒并逐次翻倍，最长 600 秒。当 Server 允许匿名访问时，`/login` 会重定向到首页，个人中心和账号管理页面也会隐藏。

【个人中心】展示账号信息并可修改密码。【账号管理】面向具备账号管理或图空间成员管理能力的账号，可创建账号并分配四种权限预设之一：超级管理员、GraphSpace 只读、GraphSpace 读写、GraphSpace 管理员。界面上不再暴露底层的 role、target、access、belong 记录。

#### 4.8	集群运维

在 PD 模式下，【系统与运维】会为具备相应能力的账号提供【集群概览】和【节点详情】。集群概览展示拓扑、各层级的节点状态，以及在线 Store 数、PD Leader、容量、数据量、图数、分区数、副本数等集群概况。节点详情列出所有发现到的节点，支持按类型和状态筛选，并可打开单个节点查看指标、Leader 角色和 Raft 分片。节点详情在单机模式下同样可用，集群概览则需要 PD。

导航页还可以通过 `dashboard.address` 链接一个可选的外部监控面板。它是独立的监控入口，不配置也不会影响集群概览和节点详情。

### 5 配置说明

HugeGraph-Hubble 可以通过 `conf/hugegraph-hubble.properties` 文件进行配置。

#### 5.1 服务配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `server.host` | `localhost` | Hubble 服务绑定的地址，Docker 镜像会改写为 `0.0.0.0` |
| `server.port` | `8088` | Hubble 服务监听的端口 |
| `server.protocol` | `http` | 访问 HugeGraphServer 使用的协议，可选 `http` 或 `https` |
| `ssl.client_truststore_file` | `conf/hugegraph.truststore` | 客户端 truststore 路径，`server.protocol=https` 时使用 |
| `ssl.client_truststore_password` | `hugegraph` | 客户端 truststore 密码，`server.protocol=https` 时使用 |

#### 5.2 Server 与 PD

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `pd.enabled` | `false` | 是否通过 PD 发现服务；单机 Server 保持为 `false` |
| `server.direct_url` | `http://127.0.0.1:8080` | `pd.enabled=false` 时连接的 Server 地址 |
| `pd.peers` | `127.0.0.1:8686` | PD 节点地址 |
| `pd.server` | `127.0.0.1:8620` | PD 服务地址 |
| `cluster` | `hg` | Hubble 连接的集群名称 |
| `route.type` | `NODE_PORT` | 服务路由方式，可选 `NODE_PORT`、`DDS` 或 `BOTH` |
| `client.request_timeout` | `60` | HugeGraph 客户端请求超时时间（秒） |
| `client.url_cache_max_entries` | `1024` | 保留用于回退的已发现 URL 数量上限 |

#### 5.3 Gremlin 查询限制

这些设置控制查询结果限制，防止内存问题：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `gremlin.suffix_limit` | `250` | 查询后缀最大长度 |
| `gremlin.vertex_degree_limit` | `100` | 显示的最大顶点度数 |
| `gremlin.edges_total_limit` | `500` | 返回的最大边数 |
| `gremlin.batch_query_ids` | `100` | ID 批量查询大小 |
| `execute-history.show_limit` | `500` | 展示的执行记录条数上限 |

#### 5.4 文件上传

以下配置项不在打包的配置文件中，如需覆盖默认值请自行添加。

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `upload_file.location` | `upload-files` | 存放上传文件的目录 |
| `upload_file.format_list` | `csv,txt` | 允许上传的文件格式 |
| `upload_file.single_file_size_limit` | 1 GB | 单个上传文件的大小上限 |
| `upload_file.total_file_size_limit` | 10 GB | 上传文件的总大小上限 |
| `upload_file.max_uploading_time` | `43200` | 超过该秒数后清理未完成的上传分片 |

#### 5.5 集群运维

以下配置项用于集群概览和节点详情页面。

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `operations.connect_timeout_ms` | `1500` | 每个运维上游的连接超时 |
| `operations.read_timeout_ms` | `2500` | 每个运维上游的读取超时 |
| `operations.max_response_bytes` | `1048576` | 接受的运维上游响应体大小上限 |
| `operations.cache_ttl_seconds` | `5` | 运维快照缓存的有效期 |
| `operations.cache_max_entries` | `1024` | 跨凭据保留的运维快照数量 |
| `operations.store_threads` | `16` | Store 指标采集的并发任务数 |
| `operations.store_deadline_ms` | `5000` | 一轮 Store 指标采集的截止时间 |
| `operations.store.allowed_targets` | `[http://127.0.0.1:8520,http://[::1]:8520]` | Hubble 允许访问的 Store 指标来源（精确匹配） |
| `operations.pd.username` / `operations.pd.password` | `hubble` / 空 | 仅后端使用的 PD 服务身份 |
| `operations.store.username` / `operations.store.password` | `hubble` / 空 | 仅后端使用的 Store 服务身份 |
| `dashboard.address` | `127.0.0.1:8092` | 可选的外部监控面板地址，留空则隐藏入口 |

> `operations.store.allowed_targets` 的默认值仅适用于本地测试。生产部署必须显式列出每一个受信任的 Store 协议、主机和端口，服务发现不会向该白名单追加来源。HTTPS 来源会保留其配置的主机名用于 TLS SNI 与证书校验。PD 和 Store 的密码请通过受保护的部署配置提供，不要写入打包的配置文件。
