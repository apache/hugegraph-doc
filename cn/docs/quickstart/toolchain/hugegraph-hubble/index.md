# 使用 Hubble 实现图可视化：单机快速上手

> 用 Docker 启动 RocksDB Server 与 Hubble，从示例图开始理解 Schema、导入 CSV、执行 Gremlin 并查看图结果。

---

LLMS 索引： [llms.txt](/cn/llms.txt)

---

Hubble 是 HugeGraph 的 Web 管理与图可视化界面。你可以在同一个工作台中管理图的 Schema、导入数据、执行查询，
并在图、表格和 JSON 视图之间切换。本文用 **单机 RocksDB Server + Hubble** 走通这些操作，不需要 PD 或 Store。

如果使用 HStore，请先阅读本文的通用操作，再看 [HStore 分布式补充](/cn/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/)。
本文以 Toolchain `master`（当前为 `1.8.0`）为准；Docker `latest` 是可变标签，使用时应核对实际版本。

> [!WARNING]
> 不要直接对外暴露 Hubble 或 Server。生产环境使用 HTTPS、容器部署、
> [认证与授权](/cn/docs/config/config-authentication/)和访问白名单。


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
算法与账号配图使用 Toolchain `1.8.0` 构建的 Hubble 与 Server `1.7.0`。Hubble 的 `/about` 当前返回静态值 `3.0.0`，
不能据此判断构建版本；此组合只说明这些配图的运行环境，不保证 `latest` 始终对应这些版本。界面入口仍取决于 Server 提供的能力。
Compose 的 `server-data` 和 `hubble-data` 分别保存图数据与 Hubble 元数据；更多持久化与生产配置见
[Server 部署指南](/cn/docs/quickstart/hugegraph/hugegraph-server/)。

## 首页：找到当前任务的入口

首页按“图概览 → 图导入 → 图查询”组织工作入口，适合第一次使用时了解整体流程。
左侧导航可随时返回各栏目；顶部的图选择器决定查询、Schema 和异步任务的操作对象，切换页面后也要留意当前图。
单机模式只有 `DEFAULT` 图空间，不需要额外配置 PD。

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

## 图概览与图详情：先认识一张图

从【图概览】选择默认图 `hugegraph`。图概览提供图的入口与操作菜单；进入详情后，
可以查看 Schema 和数据统计，并跳转到建模、数据准备或查询。统计提供整体规模信息，导入或修改数据后可重新更新。

在图的【更多操作】菜单中加载【人物与软件 Demo 图】。示例会补齐对应 Schema 和缺失的数据，不清空已有图；
初次体验请使用空图，避免同名 Schema 与示例定义冲突。本文后续都使用这张图，探索人物和软件之间的关系。

![人物与软件示例的图概览](/cn/docs/images/hubble/overview.jpg)

新建图入口取决于 Server 的建图能力。表单填写图名称、可选别名及模板或示例数据，不填写每图 Server 主机与账号；
Server 连接统一来自 Hubble 配置。用户自建 Schema 模板属于 PD 模式，见 [分布式补充](/cn/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/)。

## Schema 建模：定义数据的形状

Schema 决定哪些属性和关系可以写入图，以及顶点 ID 和查询索引如何生成。
从【元数据配置】进入，列表视图方便维护定义，图视图帮助理解顶点与边的结构。

| 定义 | 建模时关注什么 |
|---|---|
| 属性 | 数据类型、单值或多值，避免把数值读成文本 |
| 顶点类型 | 属性、可空属性、ID 策略与主键 |
| 边类型 | 起点和终点类型、属性、边的频次及排序键 |
| 顶点索引 / 边索引 | 索引类型与字段，匹配实际过滤和范围查询 |

在人物与软件示例中，`person` 通过 `name` 主键生成 ID，`age` 与 `city` 可以为空；
`software` 使用自定义数值 ID，`created` 连接人物与软件。它们对应 [Loader 完整示例](/cn/docs/quickstart/toolchain/hugegraph-loader/)。

![顶点类型列表中的主键与数值 ID 策略](/cn/docs/images/hubble/schema.jpg)

建立自己的模型时，按“属性 → 顶点类型 → 边类型 → 索引”准备。关联属性和索引信息可以帮助检查类型的依赖关系。
删除类型和创建、重建索引可能提交后台任务；操作被接受后，还需到【异步任务】确认最终状态。

## GQL 工作台：查询与探索人物关系

进入【GQL 图遍历】，确认当前图为 `hugegraph`。工作台将查询编辑器与结果区放在一起，
可选择立即执行或异步执行，收藏常用语句，也可以从执行记录加载查询。
先在 Gremlin 编辑器执行人物属性查询：

```groovy
g.V().hasLabel('person').valueMap()
```

这条查询适合在表格或 JSON 视图核对属性。要观察人物与软件的关系，执行：

```groovy
g.V().hasLabel('person').outE('created').inV().path()
```

![Gremlin 路径查询与图结果](/cn/docs/images/hubble/query.jpg)

图结果支持 2D / 3D 展示。点击顶点或边查看 ID、类型和属性，双击顶点展开邻居；
布局、样式和筛选工具帮助突出重点，导出功能便于分享结果。【新增】用于创建元素，有权限时也可以编辑已有数据。
调整布局、颜色或显示范围只改变画布；新增、编辑和 Gremlin 写入才会改变 Server 中的数据。

`Ctrl` / `Command` + `Enter` 执行查询。立即执行适合小规模探索；长查询可交给后台任务，避免一次返回整张大图。
Cypher 页签只在 Server 支持时提供。Text2GQL 当前是界面预览，未连接模型或查询服务，不能直接生成可执行查询。

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

| 配置 | 本例如何填写 |
|---|---|
| 基础信息 | 选择目标图与刚创建的数据源，填写可识别的任务名 |
| 源端字段 | 选择 `name`、`age`、`city`，移到已选字段列表 |
| 映射字段 | 添加 `person` 顶点映射，用【自动匹配】关联同名属性后核对类型 |
| 调度信息 | 选择执行一次；确认后任务随即提交执行 |

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
| 打开 / 关闭快捷键说明 | `?` | 输入框和编辑器之外 |
| 执行查询 | `Ctrl` / `Command` + `Enter` | 查询编辑器 |
| 运行当前算法 | `Ctrl` / `Command` + `Enter` | 算法参数表单 |
| 切换图全屏 | `F` | 先点击聚焦图画布；不是全局按键 |
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

---

反链：

- [Documentation](/cn/docs/)
- [架构概览](/cn/docs/guides/architectural/)
- [系统介绍](/cn/docs/introduction/)
- [HugeGraph Examples](/cn/docs/language/hugegraph-example/)
- [HugeGraph 工具链](/cn/docs/quickstart/toolchain/)
- [图可视化](/cn/docs/quickstart/toolchain/visualization/)
- [Hubble 分布式补充](/cn/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/)
