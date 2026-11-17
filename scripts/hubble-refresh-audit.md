# Hubble 文档核对范围

本次维护 latest 中英文基础指南与分布式补充，历史发行分支不变。
源码、镜像身份、截图环境与图片摘要统一见 [截图清单](fixtures/hubble-screenshots.json)。
源码复核入口为 [Hubble](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-hubble)、
[Chart](https://github.com/apache/hugegraph/tree/master/helm/hugegraph) 与
[Vermeer](https://github.com/apache/hugegraph-computer/tree/master/vermeer)。

## 内容与阅读体验

- 核对查询默认限制与预览上限、只读属性、Schema 克隆、任务身份、导入计数、会话、配额继承及 Text2GQL 部署与流式行为。
- 部署、算法与恢复说明分别链接 Helm、Vermeer 指南，避免在 Hubble 页面重复维护。
- 站点已采用 OINK 1.5.1。教程使用原生 Gallery 的响应式布局、延迟加载与原图查看器；
  Expo 的缩略图、相邻原图预加载等能力不属于 Gallery，不能混称。
- 双语标题使用共享 ID 改善 Duo View 同步，中文旧 ID 以无行为空 span 保留；没有新增阅读器或同步脚本。

## 真实环境与截图边界

- 截图来自真实服务与原生语言切换，没有拦截 API、替换 DOM 或调用模型；已独立复核图文与界面状态。
- 基础示例为 8 顶点／6 边。单机 CSV 导入一次后为 10 顶点／6 边；导入与异步任务截图使用这一后续状态。
  实测读取 3 行（含表头）、确认写入 2 顶点／0 边，属性读回正确；独立 Server 异步计数返回 `[10]`。
- 账户截图来自另一个启用鉴权的全新单机卷；昵称留空反映该 Server 的字段支持边界。
- 集群管理图来自真实最小 Helm 环境。Store 的 Kubernetes Ready、生命周期 STARTED 与管理状态未就绪并存；
  PD 成员指标映射 unavailable 也原样保留，详见 [Helm 文档 PR](https://github.com/hugegraph/hugegraph-doc/pull/68)。
- UI、配置与生成入口截图不证明真实 Text2GQL／RAG 推理、全部算法、生产规模或故障恢复已验收。

## 复核入口

- 图片与运行身份：[hubble-screenshots.json](fixtures/hubble-screenshots.json)。
- 阅读体验：`tests/e2e/duo-view.spec.js`、`theme-upgrade.spec.js`、`technical-catalogs.spec.js` 与 `search-ranking.spec.js`。
  重点检查双语旧锚点、双 pane 原图、Escape／焦点恢复、移动端、Print／Markdown 回退与禁用 AI 时的网络行为。
- 截图不能代替后端运行验证；真实导入请求与读回需以各模块端到端测试与真实服务断言为准。
- 源码、构建、链接与浏览器检查使用冻结的内容产物；具体门禁见 [贡献指南](../contribution.md)。
