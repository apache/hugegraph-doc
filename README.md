# Apache HugeGraph Documentation Website

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/apache/hugegraph-doc)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Docusaurus](https://img.shields.io/badge/Docusaurus-3.x-2e8555?logo=docusaurus)](https://docusaurus.io/)

---

[中文](#中文版) | **English**

This is the **source code repository** for the [HugeGraph documentation website](https://hugegraph.apache.org/docs/).

For the HugeGraph database project, visit [apache/hugegraph](https://github.com/apache/hugegraph).

## Quick Start

Only **3 steps** to run the documentation website locally:

**Prerequisites:** Node.js v18+

```bash
# 1. Clone repository
git clone https://github.com/apache/hugegraph-doc.git
cd hugegraph-doc

# 2. Install dependencies
npm install

# 3. Start development server (auto-reload)
npm run start
```

Open http://localhost:3000 to preview.

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
├── src/                        # 🎨 Docusaurus pages, CSS, and helpers
├── static/                     # 📁 Static files served from site root
├── docusaurus.config.js        # ⚙️  Site configuration
├── sidebars*.js                # 🧭 Documentation sidebar configuration
└── package.json                # 📦 Node.js dependencies
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
| **Markdown** | Use Markdown with front matter |

### Detailed Guide

See [contribution.md](./contribution.md) for:
- Local development setup
- Docusaurus theme customization
- Translation tips

## Commands

| Command | Description |
|---------|-------------|
| `npm run start` | Start dev server (hot reload) |
| `npm run build` | Build production site to `./build/` |
| `npm run serve` | Serve the production build locally |
| `npm run validate` | Build, check content inventory, and run headless UI validation |

---

## 中文版

这是 [HugeGraph 官方文档网站](https://hugegraph.apache.org/docs/) 的**源代码仓库**。

如果你想查找 HugeGraph 数据库本身，请访问 [apache/hugegraph](https://github.com/apache/hugegraph)。

### 快速开始

只需 **3 步**即可在本地启动文档网站：

**前置条件：** Node.js v18+

```bash
# 1. 克隆仓库
git clone https://github.com/apache/hugegraph-doc.git
cd hugegraph-doc

# 2. 安装依赖
npm install

# 3. 启动开发服务器（支持热重载）
npm run start
```

打开 http://localhost:3000 预览网站。

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
├── src/                        # 🎨 Docusaurus 页面、样式和辅助脚本
├── static/                     # 📁 站点根路径静态文件
├── docusaurus.config.js        # ⚙️  站点配置
├── sidebars*.js                # 🧭 文档侧边栏配置
└── package.json                # 📦 Node.js 依赖
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
| **Markdown** | 文档使用 Markdown 格式，带 front matter |

#### 详细指南

查看 [contribution.md](./contribution.md) 了解：
- 本地开发环境配置
- Docusaurus 主题定制
- 翻译技巧

### 常用命令

| 命令 | 说明 |
|------|------|
| `npm run start` | 启动开发服务器（热重载） |
| `npm run build` | 构建生产版本到 `./build/` |
| `npm run serve` | 本地预览生产构建 |
| `npm run validate` | 构建、检查内容清单并运行无头 UI 校验 |

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
