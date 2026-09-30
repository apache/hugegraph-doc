---
title: "使用 Hubble 实现图可视化：单机快速上手"
description: "用 Docker 启动 RocksDB Server 与 Hubble，从示例图开始理解 Schema、导入 CSV、执行 Gremlin 并查看图结果。"
linkTitle: "Hubble 基础与单机"
weight: 1
search_keywords: [HugeGraph Hubble, 图可视化, 图形化界面, Web 管理界面, RocksDB]
search_boost: 1.6
---

Hubble 是 HugeGraph 的 Web 管理与图可视化界面。你可以在同一个工作台中管理图的 Schema、导入数据、执行查询，
并在图、表格和 JSON 视图之间切换。本文用 **单机 RocksDB Server + Hubble** 走通这些操作，不需要 PD 或 Store。

如果使用 HStore，请先阅读本文的通用操作，再看 [HStore 分布式补充](/cn/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/)。
本文以 Toolchain `master`（当前为 `1.8.0`）为准；Docker `latest` 是可变标签，使用时应核对实际版本。

> [!WARNING]
> **以下组合用于本地试用。** Hubble 提供可修改数据的原生查询入口。生产环境应在可信入口终结 HTTPS，
> 限制 Hubble 与 Server 的网络访问，并在 Server 开启 [认证与授权](/cn/docs/config/config-authentication/)。
> 保留 Server 的 `audit-*.log` 并限制读取权限；`auth.audit_log_rate` 是速率上限，不是审计开关。


本页截图采集于 2026-10-01 的 Docker `latest`：Hubble `/about` 报告 `3.0.0`，Server core 为 `1.7.0`（RocksDB）。
已验证下述示例与导入；部分 master 新功能是否可用仍取决于所连接 Server 的能力。

## 启动单机组合

直接使用主仓库 [docker/docker-compose.yml](https://github.com/apache/hugegraph/blob/master/docker/docker-compose.yml)，
无需另外编写一份 Compose。文件已经组合了 RocksDB Server 与 Hubble，并配置网络、健康检查和数据卷；
部署细节见同目录的 [README](https://github.com/apache/hugegraph/blob/master/docker/README.md)。

```bash
git clone --branch master --single-branch --depth 1 https://github.com/apache/hugegraph.git
cd hugegraph/docker
```

如果已有主仓库，直接进入它的 `docker/` 目录。Compose 挂载该目录下的
[`conf/hubble/standalone.properties`](https://github.com/apache/hugegraph/blob/master/docker/conf/hubble/standalone.properties)，
其中 `pd.enabled=false`、`server.direct_url=http://server:8080`：两个服务在同一 Docker 网络中通信，不需要填写每图 Server 地址。
不要只下载 YAML 后从其他目录启动，否则相对配置文件路径可能不存在。

Hubble 默认只在宿主机回环地址开放 `8088`；Server 默认发布 `8080`。仅本机试用时，将 Compose 中 Server 的
`ports` 改为 `127.0.0.1:8080:8080`，避免对其他机器开放匿名接口。

为本次试用选一个未被使用的项目名，后续命令在同一终端沿用这些变量；另开终端时恢复本次项目名。

```bash
export HUGEGRAPH_VERSION=latest
export HUBBLE_IMAGE=hugegraph/hubble:latest
export HUBBLE_DEMO_PROJECT="hubble-demo-$(date +%Y%m%d-%H%M%S)"
docker compose ls
docker compose -p "$HUBBLE_DEMO_PROJECT" -f docker-compose.yml pull
docker compose -p "$HUBBLE_DEMO_PROJECT" -f docker-compose.yml up -d --wait
docker compose -p "$HUBBLE_DEMO_PROJECT" -f docker-compose.yml ps
curl -fsS http://127.0.0.1:8080/versions
```

服务健康后，打开 <http://127.0.0.1:8088>。全新目录未配置 `HUGEGRAPH_ADMIN_PASSWORD` 时，Server 允许匿名访问，
Hubble 直接进入首页。需要认证时，按 Docker README 配置 `.env` 中的管理员密码与 JWT 密钥，使用 Server 账号登录；
Hubble 没有独立账号库。个人中心与账号管理只在相应认证和权限条件下显示，不要覆盖已有 `.env`。

`latest` 便于体验当前功能，正式部署应固定镜像版本或 digest。镜像是便捷分发物，正式发布包见 [下载页](/cn/docs/download/download/)。
Compose 的 `server-data` 和 `hubble-data` 分别保存图数据与 Hubble 元数据；更多持久化与生产配置见
[Server 部署指南](/cn/docs/quickstart/hugegraph/hugegraph-server/)。

## 先用一张示例图认识工作台

从【图概览】选择默认图 `hugegraph`。单机模式只有 `DEFAULT` 图空间，通常不需要手动选择空间。
顶部的图选择器决定当前操作对象；查询前、切换页面后，都留意当前图。

在图的【更多操作】菜单中加载【人物与软件 Demo 图】。示例会补齐对应 Schema 和缺失的数据，不清空已有图；
初次体验请使用空图，避免同名 Schema 与示例定义冲突。图名、别名或类型不同，会影响后续查询结果。

![人物与软件示例的图概览](/cn/docs/images/hubble/overview.jpg)

| 想做的事 | 从哪里开始 |
|---|---|
| 查看图、加载示例、了解数据规模 | 图概览与图详情 |
| 定义属性、顶点类型、边类型及索引 | 图的【元数据配置】 |
| 执行 Gremlin / Cypher，探索查询结果 | 【GQL 图遍历】 |
| 上传文件、设置读取方式 | 【数据源管理】 |
| 配置映射、执行或调度导入 | 【数据导入】 |
| 查看后台查询、索引等任务 | 【异步任务】 |

新建图入口取决于 Server 的建图能力。表单填写图名称、可选别名及模板或示例数据，不填写每图 Server 主机与账号；
Server 连接统一来自 Hubble 配置。加载示例之后，可以先查询再回头查看 Schema，更容易理解数据与模型的关系。

## 查询与探索人物关系

进入【GQL 图遍历】，确认当前图为 `hugegraph`，在 Gremlin 编辑器输入以下语句并选择立即执行：

```groovy
g.V().hasLabel('person').valueMap()
```

这条查询返回人物属性，适合在表格或 JSON 视图查看。要看到人物与软件之间的关系，执行：

```groovy
g.V().hasLabel('person').outE('created').inV().path()
```

图视图中点击顶点或边可查看 ID、类型和属性；双击顶点可展开邻居。画布工具栏提供布局、样式、筛选、导出及【新增】等操作。
调整画布展示不等于修改图数据；通过新增、编辑或 Gremlin 写入的操作才会改变 Server 中的数据。

![Gremlin 路径查询与图结果](/cn/docs/images/hubble/query.jpg)

`Ctrl` / `Command` + `Enter` 可执行语句。常用查询可以收藏，执行记录可以加载后再次运行。
较长的查询可选择异步执行，再到【异步任务】查看状态与结果。立即查询适合小规模探索，避免一次返回整张大图。

Cypher 页签只在 Server 支持时提供；Text2GQL 当前只是界面预览，没有接入模型或查询服务。
图画布支持 2D/3D，表格与 JSON 适合核对原始结果。内置图算法提供探索邻居、路径、相似度等表单；
OLAP 批量算法还需要 Computer 或 Vermeer 等外部计算环境，并非启动本例两个容器就能使用。

## 看懂 Schema，再添加自己的数据

从图概览打开【元数据配置】。Schema 描述哪些类型和属性可以写入图，并决定顶点 ID 与索引方式。
页面提供列表和图两种视图；列表将属性、顶点类型、边类型、顶点索引、边索引分开显示。

在人物与软件示例中，`person` 通过 `name` 主键生成 ID，`age` 与 `city` 可以为空；
`software` 使用自定义数值 ID，`created` 连接人物与软件。它们对应 [Loader 完整示例](/cn/docs/quickstart/toolchain/hugegraph-loader/)。

![顶点类型列表中的主键与数值 ID 策略](/cn/docs/images/hubble/schema.jpg)

自己建模时，按“属性 → 顶点类型 → 边类型 → 索引”的顺序准备。选择数据类型时留意数字与文本，
明确哪些属性允许为空，再决定主键或自定义 ID。边需要指向已存在的顶点类型；索引应匹配实际查询条件。
删除类型和创建、重建索引可能提交后台任务，可在【异步任务】核查完成状态。

### 用 CSV 增加两个人物

保存一个 UTF-8 文件 `people.csv`：

```csv
name,age,city
docs_alice,28,Beijing
docs_bob,32,Shanghai
```

先到【数据源管理】新建 FILE 数据源并上传文件，选择 CSV（逗号分隔、默认 UTF-8），列名为 `name,age,city`。
表头、分隔符和编码属于数据源配置，不在后面的映射步骤设置。

接着到【数据导入】创建任务，依次完成四项：

1. **基础信息**：选择 `DEFAULT` / `hugegraph` 和刚才的数据源。
2. **源端字段**：选中识别出的 `name`、`age`、`city`，移到右侧已选字段。
3. **映射字段**：添加 `person` 顶点映射，点击【自动匹配】，核对三个同名字段与对应属性。
4. **调度信息**：选择执行一次并确认，任务随即提交执行；回到列表查看状态。

`person` 使用 PRIMARY_KEY，不设置独立 ID 列。只有自定义 ID 策略需要指定 ID 列；
AUTOMATIC 由 Server 生成 ID，PRIMARY_KEY 根据映射的主键属性生成 ID。边映射还需指定起点、终点字段。


在执行历史中查看本次实例的状态、导入量和错误消息，再返回查询工作台验证：

```groovy
g.V().hasLabel('person').has('name', within('docs_alice', 'docs_bob')).valueMap()
```

结果应包含两条新人物记录。运行失败时，先检查源字段、数值类型、可空属性及目标 Schema，而不是重复创建任务。
Hubble 也支持 HDFS、JDBC 和 Kafka 数据源，以及周期调度、Kafka 实时执行。
Hubble 导入适合小规模体验，大批量正式导入请使用 [HugeGraph Loader](/cn/docs/quickstart/toolchain/hugegraph-loader/)。

## 排查连接与结果问题

| 现象 | 先检查 |
|---|---|
| Hubble 页面打不开 | 检查容器状态及 `docker compose -p "$HUBBLE_DEMO_PROJECT" -f docker-compose.yml logs hubble` |
| 页面打开但无法访问图 | Server 是否健康，`server.direct_url` 是否能从 Hubble 容器访问，两个容器是否在同一网络 |
| 出现登录页或没有写操作入口 | Server 的认证模式和当前账号权限；Hubble 不单独开启认证 |
| 查询没有预期数据 | 顶部当前图、示例是否加载成功、标签和属性是否一致；区分画布展示与 Server 数据 |
| 没有集群概览 | 本例没有 PD；集群功能见分布式补充 |

查询显示规模受配置影响。`gremlin.suffix_limit` 默认 `250`，用于对适用的 Gremlin 查询追加 `.limit(N)`，
不是所有查询的硬上限；`gremlin.vertex_degree_limit`（`100`）与 `gremlin.edges_total_limit`（`500`）限制展开规模。
FILE 上传默认允许 `csv,txt`，单文件 1 GB、总量 10 GB；需要覆盖时修改 `upload_file.*` 配置。

## 停止试用环境或从源码构建

不再需要示例时，在主仓库的 `docker/` 目录执行：

```bash
docker compose -p "${HUBBLE_DEMO_PROJECT:?}" -f docker-compose.yml down --volumes
```

这会删除该项目的容器、网络、命名卷与匿名卷，示例图和 Hubble 导入任务也会丢失。
若想保留数据，下线时省略 `--volumes`，以后用同一项目名启动。

需要与 master 精确一致的产物时，使用 JDK 11 和 Maven 从 Toolchain 构建。
Maven 插件会安装所需的 Node/Yarn，无需预先安装；以下命令不执行测试：

```bash
git clone --branch master --single-branch https://github.com/apache/hugegraph-toolchain.git
cd hugegraph-toolchain
mvn install -pl hugegraph-client,hugegraph-loader -am -Dmaven.javadoc.skip=true -DskipTests -ntp
cd hugegraph-hubble
mvn package -Dmaven.javadoc.skip=true -DskipTests -ntp
cd apache-hugegraph-hubble-*
# 编辑 conf/hugegraph-hubble.properties，设置正确的 Server URL
bin/start-hubble.sh
```

打包配置默认绑定本机 `localhost:8088`。`bin/stop-hubble.sh` 会先请求正常停机，超时后才强制终止。
需要开发与测试说明时，参考 [Toolchain 本地测试指南](/cn/docs/guides/toolchain-local-test/)。
