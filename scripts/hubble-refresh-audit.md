# Hubble 文档更新基线

本次只更新 latest 中英文 Hubble 基础指南与分布式补充，不修改历史发行分支。
Vermeer 与 Helm 的详细部署、算法目录和恢复步骤在对应指南维护，Hubble 页面提供操作入口与关联说明。

## 源码依据

| 组件 | 核对版本 | 主要核对位置 |
| --- | --- | --- |
| Toolchain / Hubble | `20807295eed25d8c135bb1d10ab456d4f4523ecb` | Hubble README、`DirectVermeerService`、`AsyncTaskService`、Text2GQL 服务与前端文案 |
| Server / Helm | `8828d8238ad578f0d8ac25010c3dd6d4b3ba0e07` | Chart values、Hubble 配置、Vermeer 与运维指南 |
| Vermeer | `cc990987d2932fe269948e197a82d73da6869494` | 原生引擎 README 与算法实现；Hubble 支持范围仍以其直连适配器为准 |
| 文档站 | `7ea15624d9ad4796b2110ad71c157359b0ba36c7` | 已合并的 [OINK 1.5.1 / Duo View 更新 #565](https://github.com/apache/hugegraph-doc/pull/565) |

核心修正包括 300 行默认查询限制与 1,000 行／顶点预览上限、部分属性只读、Schema 克隆边界、Server／Vermeer 任务身份、导入计数含义，
以及个人会话、GraphSpace 配额与继承、Text2GQL 流式生成和部署默认模型。分布式补充串联 Helm、Hubble 加载图、Vermeer 计算及集群诊断。
截图来源、语言、尺寸和摘要以 [截图清单](fixtures/hubble-screenshots.json) 为准；不能把界面截图当作完整计算或恢复验证。

## 多图与双语阅读

OINK 最新发布版已是站点采用的 `v1.5.1`，无需重复提交主题升级。
教程仍使用原生 Gallery：响应式网格、延迟加载、异步解码与原图查看器。
Gallery 在本次主题版本中没有新增缩略图压缩、相邻原图预加载或轮播；Expo 的这些相册能力不能套用于教程 Gallery。

Hubble 主篇的 30 个标题与分布式补充的 9 个标题采用对应的双语 heading ID，改善 Duo View 的同步滚动。
英文原有 ID 保留；中文旧 ID 通过标题前的无行为空 `span` 保留，既有目录外深链接与任务卡片仍可使用。
这是内容级锚点兼容，不新增标题渲染器、相册脚本或同步控制器。

## 验证记录

- Hugo Extended `0.168.0`、Go `1.27.3`、Python `3.13`、WebP `1.5.0`：严格构建通过，仅保留允许的 LibSass 弃用警告。
- 最新文档基线源码测试：294 项，293 通过；下载页渲染检查因未设置 `DOWNLOAD_PUBLIC_DIR` 跳过，随后对新鲜 latest 产物单独执行并通过。
- 新增 Hubble Duo View 回归：中英文分别在 1440 和 390 像素通过，共 4 项。
  覆盖双语标题对应、旧中文任务卡片深链接、两个 pane 中原图加载、Escape 仅关闭图片、图片焦点恢复及阅读器退出。
- 同源 latest 预览上的 Duo View 与搜索排序：46 项通过；历史版本未组装，对应 8 项明确跳过。
- 全部截图及五组指南标题完成后的浏览器回归：99 项通过、8 项历史用例按 `EXPECTED_VERSIONS=latest` 明确跳过；
  覆盖搜索排序、Duo View、FileTree 全注释及技术表格的桌面／移动端行为。
- Hubble 原图查看器与改后截图：12 项通过；另保留 10 组对应的改前浏览器截图。
- 渲染后的 HTML 安全检查通过，覆盖 372 个 HTML 文件。
- 对比改前和改后生成 HTML：四页的旧 ID 全部保留，未产生重复 ID。
- 独立源码审查确认主要行为与双语对应；已修正“复制任务身份携带图上下文”及“整个生成操作限时 60 秒”的易误解措辞。

本篇的 28 张截图经独立视觉审查，尺寸与 SHA-256 均已核验。生产 origin 的联合 latest 产物校验通过：
369 个 canonical 页面、332 个动作清单、105322 个内部 URL、24 条路由契约及 372 个 HTML 安全检查。
源码链接检查通过；浏览器使用相同内容的同源本地预览。浏览器页面检查不代替真实后端算法、集群健康或 Kubernetes 生命周期验收。

## 单机 CSV 导入与异步计数的真实闭环

2026-11-15 06:50:34（Asia/Singapore；UTC 为 2026-11-14 22:50:34）在单机匿名 Hubble 中通过原生 UI 执行一次导入。
该操作在基础示例截图完成后进行，基础截图仍对应 8 顶点／6 边，导入和异步任务截图对应 10 顶点／6 边。

- 原生【本地上传】创建 `docs_people_csv`，上传文档中的带表头 UTF-8 `people.csv`；【列名】留空，字段预览自动识别 `name`、`age`、`city`。
- 在导入向导选择 `DEFAULT/hugegraph`、三个源字段、`person` 顶点类型，使用自动匹配，不设置主键策略的独立 ID 列，并选择单次执行。
- 仅提交一次 `docs_people_import`。导入任务及执行实例均为 `1`，状态成功；输入读取 `3`（含表头）、确认顶点写入 `2`、确认边写入 `0`。
- 通过原生 GQL UI 执行文档中的 `valueMap()` 查询，实际返回 `docs_alice`（28、Beijing）及 `docs_bob`（32、Shanghai）。
- 切换 UI 的异步模式，提交一次 `g.V().count()`，使用提交结果中的【查看任务进度】进入列表。
  `Server #1` 成功后展开结果，真实值为 `[10]`。该 Server 任务 ID 与导入实例 ID 并非同一任务。
- `import-task.jpg` 与 `async-tasks.jpg` 的两语截图均为 1600 × 1000、JPEG quality 88，通过 Hubble 自带语言按钮切换，
  展示同一导入执行实例和同一 Server 任务。未拦截 API、未替换 DOM、未重复导入或删除数据来恢复旧数量。
- 实际请求、响应、验证属性及截图文本保留在本次工作产物 `hubble-import-live/`；截图摘要由统一清单记录。

单机运行环境中，entrypoint 使用 `0.0.0.0` 探测 REST 就绪时曾被继承代理返回 403，而 localhost 健康检查和真实查询成功。
在运行用 Compose 中同时为 `NO_PROXY` / `no_proxy` 加入该本地地址后重建 Server，保留原卷及数据；未修改产品代码或放宽验证。
