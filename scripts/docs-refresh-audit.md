# 文档更新盘点与截图基准

本轮盘点全站当前文档，更新 Hubble 双语指南及会导致照做失败的高影响指引，并完成六组 P2/P3 页面的后续改造。
公开路由、旧锚点、历史版本导航和语言切换保持可用。下表记录本轮处理范围，不代表全站命令均已运行。

## 全站盘点

统计范围为 `content/{en,cn}/docs/**/*.md`：英文 112 篇、中文 123 篇。
多出的 11 篇中文全部为 0.2–0.11.2 的历史 changelog，不属于当前操作指南漏译。
下表为有具体证据的优先项；未列出的页面不代表已经逐条验证所有命令。

| 优先级 | 页面（相对于两语言的 `docs/`） | 问题与处理 |
| --- | --- | --- |
| P1，本轮 | `quickstart/toolchain/hugegraph-hubble.md` 与 `visualization/hugegraph-hubble-hstore.md` | 重拍双语截图，统一数据与步骤；增加任务入口、启动 Steps 和分布式调用关系；修正源码构建要求、模型管理权限及旧元数据说明。 |
| P1，本轮 | `clients/gremlin-console.md` | 旧 GraphSON 类与当前 Server 配置不一致；使用配套 GraphBinary 配置，连接、查询和关闭按顺序呈现，明确 Driver 调用与 Console 远程提交的区别。 |
| P1，本轮 | `quickstart/client/hugegraph-client.md` | 旧 JDK 说明与 master 的 Java 17 目标冲突；区分已发布依赖与源码版，完整示例采用 Tabs，补充保存与运行入口。 |
| P1，本轮 | `quickstart/hugegraph/hugegraph-server.md` | 关联 GraphBinary 示例使用了错误的 HugeGraph registry 包名；与官方配置对齐。 |
| P2，本轮 | `quickstart/toolchain/hugegraph-loader.md` | 靠前增加最短文件导入 Steps，保留映射参考和旧锚点；核实 Java 17、并发保护及 Spark/Flink 版本边界。真实导入 2 点 1 边并查询属性和邻居。 |
| P2，本轮 | `config/config-authentication.md` | 分清 run、Compose 与既有容器三条路径，初始化和重启使用 Steps；发布版与当前源码均验证三条路径的认证状态及原数据保留。 |
| P2，本轮 | `guides/backup-restore.md` | 先给模式选择表，再给备份、设置模式、恢复、还原原模式的闭环；真实对比 RESTORING/MERGING 的 Schema、属性、端点和 ID。 |
| P2，本轮 | `quickstart/hugegraph-ai/quick_start.md` | 重排 GraphRAG 与 Text2Gremlin，补充可复制数据、Schema 和 Prompt；本地模型真实抽取、入库、检索、生成并执行，重拍 8 张两语配对图，写清当前源码限制。 |
| P3，本轮 | `quickstart/toolchain/hugegraph-tools.md` | Git 标签与源码包用 Tabs 提供完整获取和构建路径，两路均实际构建并运行 help；旧 Studio deploy 单独标明版本范围。 |
| P3，本轮 | `guides/faq.md` | 按部署、查询、导入和建模组织可链接的问题标题，修正版本与故障判断；真实验证 gzip 解码和字符串 ID 的 URL 编码查询。 |

## 固定来源

- Hubble：[官方 Toolchain master 快照](https://github.com/apache/hugegraph-toolchain/tree/d655b0372dfe189ebeff51ea885b3386a1bc4a2c/hugegraph-hubble)。
- Server / PD / Store：[官方 Server master 快照](https://github.com/apache/hugegraph/tree/ebb8f4e17f0bf826cb50745c590d8bc54b45c6b6)。
- Hubble 编译 SDK 使用仓库锁定的 [Java 17 candidate 基准](https://github.com/apache/hugegraph/tree/86c05ef9c5d417bd37eab21d4ecd5af82bab17ef)，
  与运行版本分别记录。两次 Server 提交间仅启动、容器脚本及其说明/测试有变化；运行的 Java 源码相同，启动脚本使用 master 版本。
- HugeGraph-AI：[官方 main 快照](https://github.com/apache/hugegraph-ai/tree/da11249745180471420890fd5a44aee93bc33bae)。
- Tools 获取路径使用已发布的 `1.7.0` 标签和官方源码包，当前源码能力另按 Toolchain 固定版本说明。
- OINK：`go.mod` 固定的 `v1.3.1`，仅使用公开的 Cards、Steps、Tabs、Gallery、Mermaid 和代码折叠能力。

构建要求来自固定源码的实际脚本，不由旧版包或 `latest` 标签推断。
Hubble 当前源码需要 JDK 17、Maven 3.9+、Python 3.9+、稳定 Node 24（至少 24.22.0）与 pnpm 12.14.0，
并使用同一独立 Maven 仓库构建配套 SDK、Client、Loader 和 Hubble。

## 双语截图约定

使用真实后端与生产前端构建，不拦截 API 返回模拟数据。采用相同视口、图、查询和页面状态，
通过 Hubble 自带语言切换分别截取 `zh-CN`、`en-US`，保留已有图片路径。
图片来源、尺寸与 SHA-256 见 [截图清单](fixtures/hubble-screenshots.json)。
普通截图为 1600 × 1000；Store 详情使用 1600 × 1200，以完整显示 Raft 与分区指标。

| 图片文件 | 真实状态与操作 |
| --- | --- |
| `overview.jpg` | `DEFAULT/hugegraph`，加载人物与软件示例后查看图卡。 |
| `schema.jpg` | 同一图的顶点类型，展示 `person` 主键与 `software` 数值 ID 策略。 |
| `query.jpg` | 执行 `g.V().hasLabel('person').outE('created').inV().path()`，展示实际图结果。 |
| `algorithms.jpg` | K-neighbor（GET），`source=1:marko`、`max_depth=1`、`limit=20`。 |
| `text2gql.jpg` | 模型未配置的真实工作台；图结果来自手写 Gremlin，不宣称自然语言生成成功。 |
| `text2gql-settings.jpg` | 模型尚未配置的设置页，不填入凭据或虚构可用模型。 |
| `text2gql-prompt.jpg` | 打开默认 Gremlin / Cypher Prompt 编辑界面，不调用外部模型。 |
| `accounts.jpg` | 已启用 Server 认证的单机账号管理。 |
| `graphspace.jpg` | PD 模式创建图空间的实际表单，显示高级资源入口。 |
| `members.jpg` | PD 模式下真实账号与图空间成员权限。 |
| `cluster-overview.jpg` | 实际 PD、Store、Server 的集群拓扑与采集状态。 |
| `store-node.jpg` | 同一 Store 的系统、磁盘、Raft 与分区指标。 |

示例图为内置 `loader` 数据集，8 个顶点、6 条边。查询与算法截图应在额外导入 CSV 前完成，
使双语图规模一致。单机与分布式图数据目录独立，截图不混用两个模式的导航或权限入口。

更新时保留旧发行版图片，不能仅凭当前页面未引用就删除：历史版本可能仍需要它们。
教程内的截图使用 Gallery；只有以图片为主体的独立相册才使用 Expo。

## 运行时发现的后续问题

Hubble 已有算法结果时切换界面语言，结果面板可能误显示“任务已提交”，且 Task ID 为空。
本轮已实际复现；在目标语言重新执行相同算法后，能正常显示 4 个节点、3 条边的同步结果。
截图采用重新执行后的真实状态。该问题属于 Toolchain 的结果状态判定，本轮仅更新文档，未修改 Hubble 产品代码。

## Hubble 等 P1 页面的验证

- 使用 CI 同版本的 Python 3.13、Hugo Extended 0.168.0、Dart Sass 1.105.2，以及本机 WebP 工具执行源码测试。
  下载页生成结果测试在新构建产物上另行执行，避免其默认跳过。
- 新鲜 latest 产物的严格构建与逐版本安全检查通过。构建使用 staging URL，历史版本指向已发布站点；未发布到远端。
- `bash dist/validate-links.sh` 与 `tests/e2e/search-ranking.spec.js` 通过。
- 两语 320 / 390 / 1440 像素布局、Cards 锚点、Steps、Tabs 键盘操作和旧示例深链接通过浏览器检查。
- 全部 24 张图片均已实际加载，并逐张检查原图查看器、Escape 关闭和焦点恢复；Mermaid 已实际渲染。
- Java 完整示例复制包含折叠内容，打印包含两个 Tab，Markdown 导出保留完整示例及图片链接。
- Console 的 GraphBinary 与 traversal alias 已对真实 HStore Server 执行，两条计数查询均返回示例图的 8 个顶点。
  中英文四份 Java 示例已使用真实发布版 `1.7.0` 依赖编译；未执行会修改图数据的完整 Java 示例。
- 独立审查覆盖文字变更与 24 张截图；算法图重拍后复查通过。保留了桌面与移动端的改前、改后页面截图。

本轮没有修改共享主题样式或历史发布分支，未重新组装历史版本，也未执行完整历史聚合发布门禁。

## 六组后续页面的验证

- 从固定源码构建配套 Server、Client、Loader 和 Tools，使用独立图与数据验证操作。Loader 导入 2 个顶点和 1 条边，姓名、年龄和邻居查询均匹配。
- 认证覆盖固定 1.7.0 镜像和当前源码构建，各自验证 run、Compose、既有容器离线启用三条路径。匿名或错误密码返回 401，正确密码返回 200；既有图的顶点 ID、类型和属性保留。
- 备份源包含 PRIMARY_KEY 人物、AUTOMATIC 顶点及带属性的边。RESTORING 保留 Schema 和元素 ID，MERGING 按目标 Schema 重算主键 ID、保留 AUTOMATIC ID，边端点随之更新；两路均还原原图模式。
- Tools 的 Git 标签与官方源码包分别真实构建，生成目录和 `bin/hugegraph help` 均正确。Loader 页的 Spark/Flink 说明核对了固定源码，未把它们写成已完成分布式作业验收。
- FAQ 的 `curl --compressed` 真实接收 gzip 并解码 JSON；对返回的字符串 ID 进行完整 JSON 编码后，可以查询到原顶点。
- HugeGraph-AI 使用本地 Ollama `qwen2.5:3b`、`mxbai-embed-large` 和 Faiss。两语使用同一份 Sarah / James 数据，真实抽取并写入 2 点 1 边。Text2Gremlin 的生成语句经 Server 执行，返回 Sarah 的年龄和职业，没有手改生成结果。
- 中文按 writing-human 的教程规则复查动作、条件和可见结果，英文同步精简重复解释。旧锚点通过显式 ID 保留，技术字段和命令保持准确。
- 最终新鲜产物通过 CI 对应工具链的源码检查、严格构建、安全检查、内部链接与搜索排名；浏览器覆盖六组双语、P1 回归、移动端导航、完整复制及 Print/Markdown 回退。
- 独立只读审查提出的版本、仓库参数、模式还原和表格模板问题均已修复并复审。AI 六列表格经两语页面实际下载、上传和预览，未把输入模板当作批量生成成功。

AI 截图的来源、模型、输入、状态和 SHA-256 见[截图清单](fixtures/ai-screenshots.json)。
AI 的 `LANGUAGE` 切换提示词和示例，控件仍为英文；配图保留实际界面，未翻译图片像素。旧图片保留供历史内容使用。

## AI 源码限制与后续项

- 固定源码缺少 `questions_template.xlsx` 时，Web 页面无法启动。教程提供创建真实输入模板的步骤，未改产品代码。
- Text2Gremlin 的自动示例召回在本轮未通过，`Similar Template (TopN)` 为空。教程使用可复制 Prompt 直接提供参考示例，配图展示真实生成和执行，不宣称自动召回成功。
- 小模型会生成错误 ID、改变大小写或产生不满足索引条件的查询。教程保留检查结果的步骤，不承诺每次生成正确。
- Graph-only 的中文流曾出现空输出。复现主流程采用两语均验证的 Graph-Vector 范围；四种范围表说明控件用途，不代表四条路径均已通过。
