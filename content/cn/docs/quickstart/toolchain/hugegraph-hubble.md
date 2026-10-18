---
title: "使用 Hubble 实现图可视化：单机快速上手"
description: "用 Docker 启动 RocksDB Server 与 Hubble，从示例图开始建模、导入 CSV，并用 Gremlin、Cypher 或 Text2GQL 查询图数据。"
linkTitle: "Hubble 基础与单机"
weight: 1
search_keywords: [HugeGraph Hubble, 图可视化, 图形化界面, Web 管理界面, RocksDB, Text2GQL, 自然语言查询, Prompt]
search_boost: 1.6
---

Hubble 是 HugeGraph 的 Web 管理与图可视化界面。你可以在同一个工作台中管理图的 Schema、导入数据、执行查询，
并在图、表格和 JSON 视图之间自由切换。本文以 **单机 RocksDB Server + Hubble** 为例走通完整操作，无需预先部署 PD 或 Store。

如需搭配 HStore 分布式集群使用，可先了解本文的基础操作，再参考 [HStore 分布式补充](/cn/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/)。
文档内容以 Toolchain 与 Server 的 `master` 分支（当前版本均为 `1.8.0`）为准；Docker `latest` 为动态标签，实际部署建议使用固定版本。

> [!WARNING]
> 请勿将未配置防护的 Hubble 或 Server 直接暴露在公网上。生产环境请务必开启 HTTPS、容器网络隔离、
> [认证与授权](/cn/docs/config/config-authentication/)及访问白名单。

## 启动单机组合

直接使用主仓库提供的 [docker/docker-compose.yml](https://github.com/apache/hugegraph/blob/master/docker/docker-compose.yml) 即可，
无需自行编写 Compose 配置文件。该文件已内置编排了 RocksDB Server 与 Hubble，并配置好网络、健康检查及持久化数据卷；
完整部署说明见同目录的 [README](https://github.com/apache/hugegraph/blob/master/docker/README.md)。

```bash
git clone --branch master --single-branch --depth 1 https://github.com/apache/hugegraph.git
cd hugegraph/docker
```

若本地已有主仓库，直接进入其 `docker/` 目录即可。Compose 会自动挂载该目录下的
[`conf/hubble/standalone.properties`](https://github.com/apache/hugegraph/blob/master/docker/conf/hubble/standalone.properties)，
已预设 `pd.enabled=false` 与 `server.direct_url=http://server:8080`。两项服务处于同一 Docker 网络中通信，
无需为每个图单独配置 Server 地址。请直接在 `docker/` 目录下启动，以确保相对配置路径有效。

Hubble 默认只在宿主机回环地址开放 `8088`（由 `HUBBLE_PUBLISH_HOST` 环境变量控制，默认为 `127.0.0.1`）；
Server 默认对外发布 `8080`。若仅供本机试用，可将 Compose 中 Server 的 `ports` 改为 `127.0.0.1:8080:8080`，避免匿名端口暴露到外部网络。

为本次试用指定一个独立的项目名，后续命令在同一终端中沿用这些环境变量；另起终端时请重新设置：

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

服务启动完成后，在浏览器访问 <http://127.0.0.1:8088>。若未在 `.env` 中配置 `HUGEGRAPH_ADMIN_PASSWORD`，Server 默认允许匿名访问，
Hubble 会直接进入首页。若已启用认证，请根据 Docker README 在 `.env` 中配置管理员密码与 JWT 密钥，并使用 Server 账号登录（Hubble 无独立用户库）。
个人中心与账号管理入口仅在开启认证且具备相应权限时展示。

`latest` 镜像便于快速体验最新功能，生产环境建议指定发布版本号或镜像 digest。正式发布包可前往 [下载页](/cn/docs/download/download/) 获取。

> [!DETAILS]- 核实部署版本
>
> 文档截图用于定位界面元素，实际版本以部署镜像的 digest 及构建信息为准。

Compose 中的 `server-data` 与 `hubble-data` 卷分别持久化保存图数据与 Hubble 元数据；更多生产配置参见
[Server 部署指南](/cn/docs/quickstart/hugegraph/hugegraph-server/)。

## 首页：找到当前任务的入口

首页按“图概览 → 图导入 → 图查询”组织核心工作流。左侧导航栏可随时切换各功能模块；
顶部的图选择器用于切换当前操作的目标图，所有查询、Schema 操作和异步任务均作用于当前选中的图。
单机模式下仅包含默认的 `DEFAULT` 图空间，无需配置 PD。

| 栏目 | 主要用途 |
|---|---|
| 图概览与图详情 | 选择图、加载示例、查看数据规模，再进入建模或查询 |
| Schema / 元数据配置 | 定义属性、顶点类型、边类型及索引 |
| GQL 图遍历 | 编写查询，在图、表格和 JSON 中探索结果 |
| 内置图算法 | 用参数表单探索邻居、路径和相似关系 |
| 异步任务 | 跟踪后台查询、Schema 和索引操作 |
| 数据源管理 | 上传文件或配置外部数据的读取方式 |
| 数据导入 | 将源端字段映射到图模型，执行或调度导入 |
| 个人中心与账号管理 | 查看个人资料、修改密码，按权限管理账号及空间成员 |
| 系统运维 | 查看 Server 节点；PD 模式还提供集群概览和 Store / PD 节点 |

### 界面速览

图概览、Schema 和查询工作区如下，点击任一截图可查看原图。

```gallery
![人物与软件示例的图概览](/cn/docs/images/hubble/overview.jpg) # 图概览：选择图并查看示例数据
![顶点类型列表中的主键与数值 ID 策略](/cn/docs/images/hubble/schema.jpg) # Schema：查看顶点类型、主键与 ID 策略
![Gremlin 路径查询与图结果](/cn/docs/images/hubble/query.jpg) # 图查询：执行 Gremlin 并探索图结果
```

## 图概览与图详情：先认识一张图

在【图概览】中选择默认图 `hugegraph`。点击图卡片或详情，可查看该图的 Schema 结构与数据统计，并快速跳转到建模、数据导入或查询页面。

在图卡片的【更多操作】菜单中点击【加载人物与软件 Demo 图】。该示例会自动创建预设 Schema 并导入示例数据（不会清空已有数据）。
初次体验建议在空图上加载，避免与已有同名 Schema 冲突。后续章节均基于该示例图演示。

若需新建图，可在页面点击新建按钮，填写图名称、可选别名并选择 Schema 模板或示例数据。连接信息由 Hubble 后端统一配置，
无需重复填写 Server 主机与账号。用户自定义 Schema 模板属于 PD 模式功能，详见 [分布式补充](/cn/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/)。

## Schema 建模：定义数据的形状

Schema 规定了图中允许存储的属性、顶点与边类型，并决定顶点 ID 的生成策略与索引规则。
在【元数据配置】中，可以通过列表视图维护定义，或通过图关系视图直观查看顶点与边的拓扑结构。

| 定义 | 建模时关注什么 |
|---|---|
| 属性 | 数据类型、单值或多值，避免把数值读成文本 |
| 顶点类型 | 属性、可空属性、ID 策略与主键 |
| 边类型 | 起点和终点类型、属性、边的频次及排序键 |
| 顶点索引 / 边索引 | 索引类型与字段，匹配实际过滤和范围查询 |

在人物与软件示例中：`person` 以 `name` 为主键生成 ID，`age` 与 `city` 允许为空；
`software` 采用自定义数值 ID；边类型 `created` 连接人物与软件。模型定义与 [Loader 示例](/cn/docs/quickstart/toolchain/hugegraph-loader/) 保持一致。

自主建模时，建议遵循 **属性 → 顶点类型 → 边类型 → 索引** 的顺序依次创建。
删除类型或创建/重建索引操作通常会提交为后台异步任务，操作提交后可在【异步任务】中查看最终执行结果。

## GQL 工作台：查询与探索人物关系

进入【GQL 图遍历】，确认当前图为 `hugegraph`。工作台将查询编辑器与图展示区集成在一起，
支持即时执行与异步执行、常用语句收藏，并可随时从执行历史中重载语句。先在 Gremlin 编辑器中执行人物属性查询：

```groovy
g.V().hasLabel('person').valueMap()
```

这条查询适合在表格或 JSON 视图核对属性。要观察人物与软件的关系，执行：

```groovy
g.V().hasLabel('person').outE('created').inV().path()
```

图结果支持 2D / 3D 展示。点击顶点或边查看 ID、类型和属性，双击顶点展开邻居；
布局、样式和筛选工具帮助突出重点，导出功能便于分享结果。【新增】用于创建元素，有权限时也可以编辑已有数据。
调整布局、颜色或显示范围仅影响前端画布；通过界面新增、编辑元素或执行 Gremlin 写入语句才会真正修改 Server 中的图数据。

快捷键 `Ctrl` / `Command` + `Enter` 可快速执行查询。普通即时执行适合小规模交互探索；大数据量或耗时查询建议提交为后台异步任务。
Cypher 查询仅在 Server 后端支持时提供。快捷键会作用于当前获得焦点的输入框（在自然语言框中生成查询，在语句框中执行已有语句）。

### Text2GQL 自然语言查询 {#text2gql}

> [!NOTE]
> Text2GQL 后端能力（包括模型设置、内置/临时模型管理与 Prompt 模板）依赖包含
> [apache/hugegraph-toolchain#824](https://github.com/apache/hugegraph-toolchain/pull/824) 的 Hubble 构建或后续发布版本；未合入该特性的旧版本仅提供预览占位，不包含模型设置页面。

在【自然语言】输入框中用自然语言描述查询需求，Text2GQL 会结合当前图的 Schema 自动生成只读 Gremlin 或 Cypher 语句并执行查询。
生成的语句支持二次编辑（执行前同样会进行只读安全校验）。切换至【异步】模式时，生成的查询与手写查询均可提交为后台异步任务。
输入框会自动恢复当前图最近一次的查询输入（不会自动触发执行），执行记录中也会完整保留原始自然语言问题。

```gallery
![Text2GQL 查询与图结果](/cn/docs/images/hubble/text2gql.jpg) # 查询工作台
![内置模型设置](/cn/docs/images/hubble/text2gql-settings.jpg) # 模型设置
![Gremlin 与 Cypher Prompt 模板](/cn/docs/images/hubble/text2gql-prompt.jpg) # Text2GQL Prompt
```

| 模型来源 | 配置与保存方式 |
| --- | --- |
| 使用内置模型 | 在【系统与运维 → 模型设置】统一配置，Key 加密存入 H2，不回传浏览器 |
| 使用临时模型 | 在查询页填写 API 类别、Base URL、模型名称和临时 API Key；Key 只保留在前端内存中，刷新后清除 |

使用 OpenAI、DeepSeek、GLM 等模型时选择【OpenAI 兼容接口】；使用本地运行的 Ollama 时选择【Ollama（本地）】（无认证时 Key 可留空）。
注意：Base URL 必须能被 Hubble 后端服务正常访问（若 Hubble 运行在容器中，`localhost` 指向容器本身而非宿主机）。公网端点必须使用 HTTPS，HTTP 仅允许用于
本地回环或私网模型；在【模型设置】中修改 Base URL 时，必须重新填写 Key 或清空已保存的 Key。
全局内置模型仅由 `admin` 账号（PD 模式下为超级管理员）统一配置；未开启 Server 认证时，任何访问者均可配置。

在模型设置页面右上角打开 **Text2GQL Prompt**，可分别定制 Gremlin 与 Cypher 的生成规则及 Few-shot 示例。
点击【应用】后需保存模型设置，模板将持久化存入 H2 数据库供内置模型与临时模型共享，生成时会自动附加当前图的 Schema。

> [!DETAILS]- API Key 存储与隐私说明
>
> 备份 Hubble H2 数据库时，请一并备份主密钥文件（默认路径 `data/text2gql-master.key`），该文件丢失将导致无法解密已保存的 Key。
> 生成查询时仅向模型接口发送用户问题、当前 Schema 及纠错提示，绝不会发送图数据查询结果。
> 浏览器可选择记住常用的 Base URL 与模型名称，但临时 API Key 仅保留在前端内存中，刷新页面即自动清除。

页脚分别显示模型生成耗时与查询请求耗时；异步提交耗时仅代表任务入队耗时，不代表后台任务实际运行时间。

## 内置图算法：用表单探索关系

不想从头编写遍历语句时，可以进入【内置图算法】，搜索算法并填写参数。
邻居探索用于回答“这个点附近有什么”，路径算法用于寻找两个点的连接，相似度和排序算法用于比较或筛选顶点。
从一个已知顶点 ID 开始，先限定方向、边类型、深度与返回规模，再观察结果，会比直接运行大范围计算更容易理解。

算法表单提供参数说明及文档入口；常用参数可以在页面间往返时恢复。
运行结果按算法显示为图或相应的结果面板；需要理解具体定义和参数时，使用算法标题旁的说明与文档链接。
表单聚焦时也可用 `Ctrl` / `Command` + `Enter` 运行当前算法。

OLAP 批量算法需要 Computer 或 Vermeer 等外部计算环境。本例的两个容器用于在线图操作，不包含这些计算服务。

例如选择 K-neighbor（GET），设置 `source=1:marko`、`max_depth=1`、`limit=20`，
参数校验通过后点击卡片右侧运行按钮，或在参数表单内使用快捷键，即可观察一跳邻居。

![内置邻居算法的参数与图结果](/cn/docs/images/hubble/algorithms.jpg)
{width="2033" height="977"}

## 异步任务：确认后台操作的最终结果

【异步任务】集中显示当前图的后台任务，包括异步查询及部分 Schema、索引操作。
可以按任务类型和状态筛选，查看任务 ID、创建时间与执行状态；成功查询可打开结果，失败任务可展开错误信息。
已结束的任务可按界面提供的操作删除记录，任务列表与导入任务的执行历史是两个不同入口。

例如把 `g.V().count()` 以异步方式提交后，先在列表确认成功，再查看返回的数量。
“提交成功”只表示请求被接受，不表示计算或索引已完成。排查失败时，结合任务错误和 Server 日志定位原因。

## 数据源管理：把原始数据准备好

数据源负责“从哪里读、怎样解析”，可以被导入任务引用。Hubble 支持 FILE、HDFS、JDBC 和 Kafka；
不同来源需要对应的路径、连接或订阅配置。FILE 最适合先体验：上传文件后，配置格式、分隔符、编码和表头，
检查读取的列名，再进入映射。上传限制和允许的扩展名由 Hubble 配置决定。

为人物示例保存一个 UTF-8 文件 `people.csv`：

```csv
name,age,city
docs_alice,28,Beijing
docs_bob,32,Shanghai
```

创建 FILE 数据源并上传它，选择 CSV（逗号分隔、默认 UTF-8），列名为 `name,age,city`。
表头、分隔符和编码属于数据源配置，不在后面的映射步骤设置；源字段应与文件内容一致。

## 数据导入：从字段映射到可查询的图

【数据导入】把数据源中的行转换为顶点和边。任务创建采用四段配置，先明确目标，再选择字段和映射，最后决定执行时机。
沿用上面的数据源，在 `DEFAULT` / `hugegraph` 中创建人物导入任务：

1. **基础信息** 选择目标图与刚创建的数据源，填写任务名。
1. **源端字段** 选择 `name`、`age`、`city`，移到已选字段列表。
1. **映射字段** 添加 `person` 顶点映射，用【自动匹配】关联同名属性后核对类型。
1. **调度信息** 选择执行一次，确认后提交任务。
{.steps}

`person` 使用 PRIMARY_KEY，不设置独立 ID 列。自定义 ID 策略需要指定 ID 列；
AUTOMATIC 由 Server 生成 ID，PRIMARY_KEY 根据映射的主键属性生成 ID。边映射还需指定起点、终点字段并匹配对应顶点的 ID 规则。

任务列表用于管理配置和执行入口，详情中的执行历史用于查看每次实例的状态、导入量与错误。
Hubble 还提供周期调度和 Kafka 实时执行，调度方式需与数据源类型匹配。
完成后返回 GQL 工作台验证：

```groovy
g.V().hasLabel('person').has('name', within('docs_alice', 'docs_bob')).valueMap()
```

结果应包含两条新人物记录。导入量统计不应直接当作新增顶点数；重跑可能更新已有元素，表头处理也会影响读取统计。
失败时先检查源字段、数值类型、可空属性及目标 Schema。Hubble 导入适合小规模体验，
大批量正式导入请使用 [HugeGraph Loader](/cn/docs/quickstart/toolchain/hugegraph-loader/)。

## 个人中心与账号权限

Hubble 使用 Server 的认证和账号，没有独立用户库。匿名访问时不显示【个人中心】与【账号管理】；
开启认证后，个人中心展示当前账号资料与权限信息，可修改自己的密码。昵称等资料编辑依赖 Server 对个人资料接口的支持。
修改密码后会退出当前会话，需要重新登录。

### 单机账号管理

单机模式由管理员管理账号，可创建、查看、编辑或删除账号，并支持批量创建。
通过 Hubble 新建的普通单机账号会获得覆盖所有图的读、写、删除和执行权限，不能把它当作只读账号或单图隔离账号。
需要更细的资源权限时，应按 [Server 认证与授权](/cn/docs/config/config-authentication/)配置，而不是依赖空间预设。

### PD 模式的空间权限

连接支持默认角色接口的 Server 后，账号与空间访问可以分别管理。管理员管理全局账号，
空间管理员只管理已授权空间的成员；普通成员不会获得账号管理或运维入口。
以下四种预设属于 PD 模式，不表示旧版本或单机 Server 都提供同样的权限编辑能力：

| 预设 | 范围与用途 |
|---|---|
| `SUPER_ADMIN` | 全局管理账号、图空间和运维；可授予或撤销超级管理员 |
| `GS_ADMIN` | 管理已授权图空间及其成员，不授予其他空间或全局超级管理员权限 |
| `GS_READ_WRITE` | 在已授权空间执行图数据读写操作，不管理全局账号 |
| `GS_READ_ONLY` | 在已授权空间读取图数据，不进行写入 |

同一账号在不同空间可以有不同权限。成员管理先选择空间，再添加已有账号或调整权限；
把已有自定义权限替换为预设前，先核对需要保留的授权，避免把复杂权限误认为单一预设。
权限变更后刷新权限上下文或重新登录，确认菜单和目标空间已更新；最终请求仍由 Server 校验。
旧 Server 未提供相应接口时，页面按能力隐藏或禁用操作，不应只凭按钮是否可见推断资源权限。
更完整的空间管理见 [分布式补充](/cn/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/)。

![认证模式下的账号列表（PD 模式示例）](/cn/docs/images/hubble/accounts.jpg)
{width="2033" height="977"}

## 系统运维：检查单机 Server

单机模式的【系统运维】提供【节点信息】，只显示 Server，不显示 PD / Store 节点或集群概览。
节点列表可搜索、筛选健康状态并进入详情；详情用于查看可用的版本、系统、JVM、Server 后端等指标。
指标缺失或标记过期时，应结合采集状态与最近成功时间判断，不能把空值当作零或健康。

匿名模式可以查看运维信息；开启认证后，运维入口仅对有运维权限的管理员显示。
此处用于观测和排查，不是启动、停止或扩缩容控制台。PD 模式的集群概览与节点层级见分布式补充。

## 快捷键与画布操作

顶部的快捷键帮助入口随时可查看按键说明。以下快捷键有不同的作用范围，输入框中不会触发全局 `?` 帮助。

| 操作 | 按键或动作 | 生效位置 |
|---|---|---|
| 打开 / 关闭快捷键说明 | {{< kbd "?" >}} | 输入框和编辑器之外 |
| 执行查询 | {{< kbd "Ctrl" "Enter" >}} / {{< kbd "Command" "Enter" >}} | 查询编辑器 |
| 运行当前算法 | {{< kbd "Ctrl" "Enter" >}} / {{< kbd "Command" "Enter" >}} | 算法参数表单 |
| 切换图全屏 | {{< kbd "F" >}} | 先点击聚焦图画布；不是全局按键 |
| 查看元素详情 | 单击顶点或边 | 图结果 |
| 展开相邻关系 | 双击顶点 | 图结果 |

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

需要与 master 精确一致的产物时，使用 JDK 17 和 Maven 从 Toolchain 构建。
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
