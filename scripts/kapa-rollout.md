# Kapa 分阶段启用

本流程跟踪 [#495](https://github.com/apache/hugegraph-doc/issues/495)。
OINK 升级和关闭 AI 的 staging 可以先发布；真实 AI 联调及生产启用需要各自的验收证据。
模拟测试通过不代表远端索引、域名许可或真实服务已通过。

## 当前配置与授权边界

`hugo.yaml` 中的配置入口是 `params.ai_search`：

| 字段 | 含义与启用要求 |
| --- | --- |
| `enabled` | 本 PR 设置为 `true`；合入并发布后启用，回退时设为 `false` |
| `provider` | 当前仅支持 `kapa` |
| `website_id` | 已配置公开站点标识；启用前核对它确实属于 HugeGraph 项目 |
| `source_groups.en` | 真实英文、仅最新文档的 source group ID |
| `source_groups.cn` | 真实中文、仅最新文档的 source group ID；配置键是 `cn`，widget 语言是 `zh` |

两个 source group ID 已从 Kapa 控制台核对并记录在配置中；这不代表索引范围和真实服务已验收。
缺失任一 ID 时，开启状态下模板会拒绝构建。
`tests/e2e/ai-enabled.yaml` 的 `e2e-source-*` 仅用于模拟测试，不能发布为真实配置。
source group 限制必须在 Kapa 管理端核对索引内容，不能只验证 ID 非空。
Kapa 子组会继承 Global 和父组的 sources；必须检查整个继承链，不能将分组过滤误认为语言隔离。
`data-language=zh` 只改变界面文案，不限制检索语料。

EN/CN 组仅保留各自最新文档来源。旧站、历史版本及混合语言来源应从 Global/共同父组
移至与 EN/CN 同级的 `Legacy` 组，不能让 `Legacy` 成为它们的父组。
移动后复查两个组实际可检索的来源及引用；创建空子组本身不产生隔离。
来源可以使用文件上传或限定范围的 HTML 抓取。手动刷新后等待索引完成，并记录文档 SHA、
语言、更新时间和来源范围。当前项目曾显示 demo 自动刷新限制；手动更新可用，不能据此
声称已建立自动同步。索引完成也不等于真实问答验收通过。

HTML 抓取分别从 `/docs/` 与 `/cn/docs/` 开始，用锚定到站点和语言目录的 URL 正则
排除历史路径及其他站点，正文选择器使用 `.td-content`。部署前预览全部页面并核对包含/排除
列表；保持 Global 关闭，只选对应语言组。验证新来源后，将旧上传移入 Legacy 保留回退能力。
记录实际抓取站点和候选 SHA；引用会指向抓取站点，staging 来源不能直接当作生产引用配置。

[ASF FAQ](https://privacy.apache.org/faq/committers.html#can-i-use-kapaai-on-our-website-answer-machine)
确认 Kapa 已签署 DPA，并要求在加载前征得用户同意。本站先展示本地授权弹窗，
用户同意后才加载第三方脚本；`data-consent-required=false` 用于避免 widget 再次弹窗，
不表示跳过本站授权。保留禁用分析 cookie、指纹及反馈的现有配置。

[ASF CSP 文档](https://infra.apache.org/tools/csp.html) 要求新增域名有 VP Data Privacy
批准依据。核对 Kapa 及其 hCaptcha 依赖的具体域名和许可范围，再修改产物根目录的
`.htaccess`，并在注释中注明依据。不要手改后会被构建覆盖的产物，也不要添加未经核对的通配域名。
Kapa 服务获准使用不等于任意附带服务或域名都获准。
**Jira 不是默认前置条件**；只有需要 Infra 协助配置或资源时才请求其处理。

## 当前启用变更

#496 已按维护者要求纳入 `enabled=true` 和既有 staging 验证过的 Kapa/hCaptcha CSP。
这使合入后的正式站具备技术加载条件；修改 PR 不会立即发布正式站。本站授权弹窗仍保留，
第三方资源只在用户同意后加载。CSP 注释记录既有部署依据，不宣称已找到独立批准记录。
用于正式站的 HTML 来源应直接抓取 `https://hugegraph.apache.org/docs/` 与
`https://hugegraph.apache.org/cn/docs/`，使回答引用保持在正式域名。切换来源前核对
线上文档与候选内容及路径一致，索引完成后验证实际回答引用；无需在前端改写链接。
当前索引与问答验收证据统一记录在 #495；开启配置本身不代表验收完成。

## 发布顺序

部署前核对可信 `master` workflow 支持候选分支的主题模块约束。
现有流程通过模块图验证兼容性，不依赖固定的主题版本号。
不要绕过 `--ref master`；也不要为了解除 staging 阻塞而先合并主题升级，
因为 `master` push 会触发正式站发布。

1. **先发布 AI 关闭的 staging。** 使用已审核的 ASF 仓库候选分支，确认其中
   `params.ai_search.enabled=false`。现有 workflow 从 `master` 调度，参数为
   `operation=staging-next`、`scope=latest`、`candidate_branch=<候选分支>`、
   `confirmation=publish asf-staging-oink`，目标是
   <https://hugegraph-oink.staged.apache.org/>。核对运行解析的 SHA、目标分支
   `asf-staging-oink` 和实际部署结果；要验证站内历史页面时使用 `scope=full`。
2. **准备真实配置。** 获取并审核两个 source group、项目 ID、语料范围及域名许可。
   当前 workflow 没有 AI 专用开关，不能把测试 fixture 当作 staging 配置。
   使用单独的 staging 候选分支承载真实配置和经批准的 CSP 生成改动，
   先通过 `staging-next` 验证；生产启用配置在发布 PR 中审核，
   不把 staging 特有的站点地址或发布 profile 带入生产。
3. **真实 staging 验收。** 按下表记录网络、交互和回答证据；存在失败时保留原生搜索，
   修复后重新验证受影响项。只做 latest 部署时，历史版本跳转到生产，不能声称已验收
   staging 历史页面；历史提示需在完整 staging 产物上验证。
4. **生产开启。** 将已验证的 source groups、CSP 和启用配置纳入发布 PR 审核；
   可以与主题升级在同一 PR，但必须先取得 staging 证据，再启用生产。
   链接 staging SHA、部署运行及验收记录。合并前确认生产发布目标及回退版本。
   发布后复查生产响应头、授权前网络和中英文真实回答。

## 真实浏览器验收

在全新浏览器上下文中使用实际远端服务，不拦截替换 Kapa bundle。为桌面及移动端分别验证。

| 场景 | 必须观察到的结果 |
| --- | --- |
| AI 关闭 | 页面、搜索及导航不发送任何第三方 AI 请求 |
| AI 开启但尚未同意 | 页面加载、输入搜索、打开授权弹窗及取消均无 Kapa/hCaptcha 请求；不能仅检查 cookie |
| 同意并提问 | bundle 只在同意后加载，真实请求与回答成功；响应头和控制台没有阻止该流程的 CSP 错误 |
| 中英文 | 英文使用 `.en` group、中文使用 `.cn` group；回答引用来自对应语言的最新文档，不混入历史语料 |
| 继承与引用 | EN/CN 不再继承旧 Global/父组来源；用各语言真实问题检查返回引用，确认 Legacy 内容未泄漏到回答 |
| 历史页面 | 明确显示 AI 使用最新文档的提示，不暗示回答适用于当前历史版本 |
| 取消与焦点 | 取消授权、Escape、重新打开原生搜索不会被过期异步响应再次打开 AI；键盘焦点可继续操作 |
| 超时与失败 | 网络失败有可理解提示，原生搜索仍可用；重试只触发一次新的加载，成功后可继续提问 |
| 回退 | 发布 AI 关闭的已知配置后，新页面访问无第三方 AI 请求，原生搜索保持可用 |

现有 `tests/e2e/ai.spec.js` 验证的是模拟 bundle 的适配行为，
`tests/e2e/platform.spec.js` 覆盖开启状态的授权前零请求，以及独立 disabled fixture
中的中英文关闭状态。CI 和 OINK 升级验证器都会构建对应夹具；保留这些回归，并另附真实服务证据。

## 记录与回退

在 #495 或启用 PR 中记录下列链接及结果，不把账号、凭据、用户问题或未脱敏 HAR 放入仓库：

- 候选 SHA、workflow run、部署地址、产物/部署 SHA 对应关系。
- Kapa 项目归属、EN/CN group 的继承链、Legacy 隔离与索引范围审核结果及复核时间。
- 上传或 HTML 抓取对应的文档 SHA、语言、时间、索引状态；HTML 抓取还需保存 URL 白名单及正文范围。
  本地下载的内容哈希用于追溯站点版本，不能冒充 Kapa 内部解析字节的哈希。
- 具体域名许可依据、部署后 CSP 响应头、脱敏网络记录和浏览器截图。
- 各验收项通过/失败、失败原因、负责方与下一步；未知项明确写“待验证”。

出现问题时先将对应环境的 `enabled` 设回 `false` 并按原发布流程重建部署，
或重新部署已知 AI 关闭的候选提交。不要重置其他人的修改；不要通过删除 CSP 限制绕过失败。
关闭配置影响重新加载后的页面，已经打开的 widget 需要刷新；回退后重新验证关闭状态。

当前 staging 证据及未完成项以 #495 为准。既有 staging 的 CSP 可作为部署先例，
不能冒充单独的组织批准记录。生产启用仍需独立审核，不因 staging 可用而自动开启。
