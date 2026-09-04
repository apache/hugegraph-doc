# Apache HugeGraph Documentation Website

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/apache/hugegraph-doc)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Hugo](https://img.shields.io/badge/Hugo-Extended-ff4088?logo=hugo)](https://gohugo.io/)

---

[中文](#中文版) | **English**

This is the **source code repository** for the [HugeGraph documentation website](https://hugegraph.apache.org/docs/).

For the HugeGraph database project, visit [apache/hugegraph](https://github.com/apache/hugegraph).

## Quick Start

Only **3 steps** are needed to run the documentation website locally.

**Prerequisites:** Go 1.27+ and [Hugo Extended](https://github.com/gohugoio/hugo/releases) 0.165.0. OINK does not require Node.js, npm, PostCSS, or a vendored theme checkout.

```bash
# 1. Clone repository
git clone https://github.com/apache/hugegraph-doc.git
cd hugegraph-doc

# 2. Verify the pinned theme module
hugo mod graph

# 3. Start the development server (auto-reload)
hugo server
```

Open http://localhost:1313 to preview.

The module graph must resolve `github.com/pgsty/oink@v1.0.0`. For a production-equivalent check, run the strict build command shown below.

## Repository Structure

```
hugegraph-doc/
├── content/                    # 📄 Documentation content (Markdown)
│   ├── cn/                     # 🇨🇳 Chinese documentation
│   │   ├── docs/               #    Main documentation
│   │   │   ├── quickstart/     #    Quick start guides
│   │   │   ├── config/         #    Configuration docs
│   │   │   ├── clients/        #    Client docs
│   │   │   ├── guides/         #    User guides
│   │   │   └── ...
│   │   ├── blog/               #    Blog posts
│   │   └── community/          #    Community pages
│   └── en/                     # 🇺🇸 English documentation (mirrors cn/ structure)
│
├── data/                       # 🧭 Landing-page and footer data
├── i18n/cn.yaml                # 🌐 OINK interface strings for the /cn/ locale
├── assets/                     # 🖼️  Project brand assets
├── layouts/                    # 📐 Hugo template overrides
├── static/                     # 📁 Static files
├── go.mod / go.sum             # 📌 Pinned OINK module
└── hugo.yaml                   # ⚙️  Site configuration
```

## Contributing

### Contribution Workflow

1. **Fork** this repository
2. Create a **new branch** from `master`
3. Make your changes
4. Submit a **Pull Request** with screenshots

### Requirements

| Requirement | Description |
|-------------|-------------|
| **Bilingual Updates** | Update **BOTH** `content/cn/` and `content/en/` |
| **PR Screenshots** | Include **before/after screenshots** in PR |
| **Markdown** | Use Markdown with Hugo front matter |

### Detailed Guide

See [contribution.md](./contribution.md) for the pinned toolchain, strict build, OINK customization, and translation rules.

## Commands

| Command | Description |
|---------|-------------|
| `hugo server` | Start dev server (hot reload) |
| `hugo --cleanDestinationDir --gc --minify --environment production --printPathWarnings --printI18nWarnings --panicOnWarning` | Strict production build to `./public/` |
| `hugo server -p 8080` | Custom port |

---

## 中文版

这是 [HugeGraph 官方文档网站](https://hugegraph.apache.org/docs/) 的**源代码仓库**。

如果你想查找 HugeGraph 数据库本身，请访问 [apache/hugegraph](https://github.com/apache/hugegraph)。

### 快速开始

只需 **3 步**即可在本地启动文档网站。

**前置条件：** Go 1.27+ 和 [Hugo Extended](https://github.com/gohugoio/hugo/releases) 0.165.0。OINK 不需要 Node.js、npm、PostCSS 或检出到仓库内的主题副本。

```bash
# 1. 克隆仓库
git clone https://github.com/apache/hugegraph-doc.git
cd hugegraph-doc

# 2. 检查固定的主题模块
hugo mod graph

# 3. 启动开发服务器（支持热重载）
hugo server
```

打开 http://localhost:1313 预览网站。

模块图必须解析为 `github.com/pgsty/oink@v1.0.0`。需要执行与生产一致的检查时，请运行下方的严格构建命令。

### 仓库结构

```
hugegraph-doc/
├── content/                    # 📄 文档内容 (Markdown)
│   ├── cn/                     # 🇨🇳 中文文档
│   │   ├── docs/               #    主要文档目录
│   │   │   ├── quickstart/     #    快速开始指南
│   │   │   ├── config/         #    配置文档
│   │   │   ├── clients/        #    客户端文档
│   │   │   ├── guides/         #    使用指南
│   │   │   └── ...
│   │   ├── blog/               #    博客文章
│   │   └── community/          #    社区页面
│   └── en/                     # 🇺🇸 英文文档（与 cn/ 结构一致）
│
├── data/                       # 🧭 首页与页尾数据
├── i18n/cn.yaml                # 🌐 /cn/ 语言的 OINK 界面文案
├── assets/                     # 🖼️  项目品牌资源
├── layouts/                    # 📐 Hugo 模板覆盖
├── static/                     # 📁 静态文件
├── go.mod / go.sum             # 📌 固定的 OINK 模块
└── hugo.yaml                   # ⚙️  站点配置
```

### 如何贡献

#### 贡献流程

1. **Fork** 本仓库
2. 基于 `master` 创建**新分支**
3. 修改文档内容
4. 提交 **Pull Request**（附截图）

#### 重要说明

| 要求 | 说明 |
|------|------|
| **双语更新** | 修改内容时需**同时更新** `content/cn/` 和 `content/en/` |
| **PR 截图** | 提交 PR 时需附上修改**前后对比截图** |
| **Markdown** | 文档使用 Markdown 格式，带 Hugo front matter |

#### 详细指南

查看 [contribution.md](./contribution.md) 了解固定工具链、严格构建、OINK 定制和翻译要求。

### 常用命令

| 命令 | 说明 |
|------|------|
| `hugo server` | 启动开发服务器（热重载） |
| `hugo --cleanDestinationDir --gc --minify --environment production --printPathWarnings --printI18nWarnings --panicOnWarning` | 严格构建生产版本到 `./public/` |
| `hugo server -p 8080` | 指定端口 |

---

## Contact & Community

- **Issues:** [GitHub Issues](https://github.com/apache/hugegraph-doc/issues)
- **Mailing List:** [dev@hugegraph.apache.org](mailto:dev@hugegraph.apache.org) ([subscribe first](https://hugegraph.apache.org/docs/contribution-guidelines/subscribe/))
- **Slack:** [ASF Slack](https://the-asf.slack.com/archives/C059UU2FJ23)

<img src="./assets/images/wechat.png" alt="WeChat QR Code" width="350"/>

## Contributors

Thanks to all contributors to the HugeGraph documentation!

[![contributors](https://contrib.rocks/image?repo=apache/hugegraph-doc)](https://github.com/apache/hugegraph-doc/graphs/contributors)

---

## License

[Apache License 2.0](LICENSE)
