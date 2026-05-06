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
├── src/data/versions.json      # 🏷️  Documentation version metadata
├── scripts/                    # 🔧 Content validation and version preparation
├── docusaurus.config.js        # ⚙️  Site configuration
├── sidebars*.js                # 🧭 Documentation sidebar configuration
└── package.json                # 📦 Node.js dependencies
```

## Documentation Versions

The source tree keeps only current documentation and version metadata. Docusaurus release snapshots are generated before `npm run start` and `npm run build` from the configured Git source refs. A version entry may set `sourceRef` to read from a Git branch or tag; when it is omitted, the current working tree is used.

Version semantics:

| Version | Route | Meaning |
|---------|-------|---------|
| `stable` | `/docs/`, `/cn/docs/` | Latest stable release documentation and the default navbar target |
| `current` / `next` | `/docs/next/`, `/cn/docs/next/` | Unreleased development documentation with an unreleased banner |

Release-branch mapping is explicit:

| Source branch | Docusaurus version / route segment | UI label |
|---------------|------------------------------------|----------|
| `release-1.5.0` | `docusaurus-1.5.0` | `1.5.0` |
| `release-1.3.0` | `docusaurus-1.3.0` | `1.3.0` |
| `release-1.2.0` | `docusaurus-1.2.0` | `1.2.0` |
| `release-1.0.0` | `docusaurus-1.0.0` | `1.0.0` |
| `release-0.11` | `docusaurus-0.11` | `0.11` |
| `release-0.10` | `docusaurus-0.10` | `0.10` |

The source branch prefix is never shown in the UI. The archived release branches listed above were authored before this Docusaurus migration, so any import repair for those snapshots is isolated under `legacyCompatibility` in `src/data/versions.json`. That compatibility layer is only for adapting those historical branches to a previewable Docusaurus build; it is not part of the normal documentation authoring or version generation pipeline. Future Docusaurus-native release branches should keep the standard `content/{en,cn}/docs` layout and should not require those adapters.

In the mapping table, `docusaurus-*` is a Docusaurus version name and route segment, not necessarily a Git branch. The actual content source is always the configured `sourceRef`. For example, `1.5.0` currently reads from the Git branch `release-1.5.0` and is published under the Docusaurus route segment `docusaurus-1.5.0`.

Generate the Docusaurus version files locally:

```bash
npm run docs:versions:prepare
```

This writes `versioned_docs/`, `versioned_sidebars/`, `versions.json`, `docs-cn_versioned_docs/`, `docs-cn_versioned_sidebars/`, and `docs-cn_versions.json` from the configured source refs. These files are generated build inputs and are intentionally ignored by Git.

List configured versions:

```bash
npm run docs:versions:list
```

To update a release source:

1. Update the entry in `src/data/versions.json`, especially `label`, `docusaurusVersion`, `path`, `cnPath`, `githubTagUrl`, and `sourceRef`.
2. Make sure the source ref is fetched locally. CI uses `fetch-depth: 0`, so tags and release branches are available there.
3. Run `npm run docs:versions:prepare`, then `npm run build`.

Only archived pre-Docusaurus branches should use `legacyCompatibility` fields such as `sourcePaths`, `sourceIncludes`, `sourceOverlays`, `indexFrom`, or Markdown normalization. These fields document deliberate compatibility work for old snapshots, not guidance for new documentation.

Do not use `latest` ambiguously in docs navigation. Use `stable` for the latest released documentation and `next` for unreleased documentation.

## Team and User Data

The Team page is available at `/team/` and `/cn/team/`. It is data-driven from `src/data/team.js`, currently based on public ASF roster data. Update that file when PMC or committer information changes, and include the public source used for the update.

The user showcase is available at `/users/` and `/cn/users/`. It is data-driven from `src/data/users.js` and uses public submissions from [apache/hugegraph#1651](https://github.com/apache/hugegraph/issues/1651). Do not add company names, logos, quotes, or deployment details unless they are already public and approved. If no approved logo exists in the repository, leave the logo empty and let the page render the fallback initials.

## Content Visibility

The site supports these publishing states:

| State | Front matter | Production behavior |
|-------|--------------|---------------------|
| Public | default | Appears in navigation and generated outputs |
| Draft | `draft: true` | Excluded from production builds by Docusaurus |
| Unlisted | `unlisted: true` | Built for direct URL access but hidden from navigation, listings, feeds, and indexed discovery; Docusaurus adds noindex/nofollow metadata |
| Placeholder | `placeholder: true`, `unlisted: true`, `noindex: true` | Reserves a URL with only a short safe placeholder message |
| Private | `private: true` | Fails production builds unless `ALLOW_PRIVATE_CONTENT=true` is explicitly set for a non-public preview |

Private content is not access control. Do not put sensitive material in Markdown, MDX, static assets, generated HTML, JavaScript bundles, source maps, or JSON that will be published. Real private access must be enforced by the hosting platform, reverse proxy, authentication gateway, or a non-public preview environment.

Production builds run:

```bash
npm run check:content-visibility
```

Use this placeholder pattern when reserving a route:

```markdown
---
title: Upcoming Case Study
unlisted: true
noindex: true
placeholder: true
---

This page is reserved for an upcoming Apache HugeGraph case study.
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
| `npm run check:content-visibility` | Fail production-unsafe private content |
| `npm run docs:versions:prepare` | Generate Docusaurus version files from configured Git refs |
| `npm run docs:versions:list` | Print configured docs versions |
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
├── src/data/versions.json      # 🏷️  文档版本元数据
├── scripts/                    # 🔧 内容校验和版本准备脚本
├── docusaurus.config.js        # ⚙️  站点配置
├── sidebars*.js                # 🧭 文档侧边栏配置
└── package.json                # 📦 Node.js 依赖
```

### 文档版本

源码分支只保留当前文档和版本元数据。Docusaurus 需要的版本快照会在 `npm run start` 和 `npm run build` 前，从配置的 Git source ref 生成。版本条目可以通过 `sourceRef` 指向 Git 分支或标签；未设置时使用当前工作区文档。

| 版本 | 路由 | 含义 |
|------|------|------|
| `stable` | `/docs/`, `/cn/docs/` | 最新稳定版本文档，也是导航栏默认入口 |
| `current` / `next` | `/docs/next/`, `/cn/docs/next/` | 未发布开发中文档，并展示 unreleased 提示 |

发布分支映射规则是显式配置的：

| 源分支 | Docusaurus 版本 / 路由段 | UI 展示 |
|--------|--------------------------|---------|
| `release-1.5.0` | `docusaurus-1.5.0` | `1.5.0` |
| `release-1.3.0` | `docusaurus-1.3.0` | `1.3.0` |
| `release-1.2.0` | `docusaurus-1.2.0` | `1.2.0` |
| `release-1.0.0` | `docusaurus-1.0.0` | `1.0.0` |
| `release-0.11` | `docusaurus-0.11` | `0.11` |
| `release-0.10` | `docusaurus-0.10` | `0.10` |

UI 不展示源分支的 `release-` 前缀。上表中的归档 release 分支是在这次 Docusaurus 迁移之前编写的，所以为了让这些历史快照可以被 Docusaurus 预览，相关导入修补都被限制在 `src/data/versions.json` 的 `legacyCompatibility` 下。这一层只用于适配这些旧分支，不属于正常的文档编写或版本生成流水线。未来 Docusaurus 原生的发布分支应保持标准的 `content/{en,cn}/docs` 目录，不应依赖这些适配项。

上表里的 `docusaurus-*` 是 Docusaurus 版本名和路由段，不一定是 Git 分支名。实际内容来源始终由配置中的 `sourceRef` 决定。例如 `1.5.0` 当前从 Git 分支 `release-1.5.0` 读取内容，并发布到 Docusaurus 路由段 `docusaurus-1.5.0`。

本地生成 Docusaurus 版本文件：

```bash
npm run docs:versions:prepare
```

该命令会生成 `versioned_docs/`、`versioned_sidebars/`、`versions.json`、`docs-cn_versioned_docs/`、`docs-cn_versioned_sidebars/` 和 `docs-cn_versions.json`。这些是构建输入，不作为源码提交。

更新发布版本时，请修改 `src/data/versions.json` 中的 `label`、`docusaurusVersion`、`path`、`cnPath`、`githubTagUrl` 和 `sourceRef`。该 ref 需要已经 fetch 到本地，然后运行 `npm run docs:versions:prepare` 和 `npm run build`。

只有归档的 pre-Docusaurus 分支才应该使用 `legacyCompatibility` 下的 `sourcePaths`、`sourceIncludes`、`sourceOverlays`、`indexFrom` 或 Markdown normalization。这些字段用于记录旧快照的兼容目的，不是新文档的开发规范。

不要在导航中模糊使用 `latest`：`stable` 表示最新已发布版本，`next` 表示未发布开发中文档。

### 团队和用户数据

Team 页面位于 `/team/` 与 `/cn/team/`，数据来自 `src/data/team.js`，当前基于 ASF 公开 roster。PMC 或 committer 变化时请更新该数据文件，并保留公开来源。

用户案例页面位于 `/users/` 与 `/cn/users/`，数据来自 `src/data/users.js`，当前基于 [apache/hugegraph#1651](https://github.com/apache/hugegraph/issues/1651) 的公开提交。不要加入未经公开授权的公司名、Logo、引用或部署细节；如果仓库中没有已授权 Logo，则保持为空，页面会展示缩写占位。

### 内容可见性

| 状态 | Front matter | 生产行为 |
|------|--------------|----------|
| Public | 默认 | 正常出现在导航和生成内容中 |
| Draft | `draft: true` | Docusaurus 在生产构建中排除 |
| Unlisted | `unlisted: true` | 可通过直链访问，但不进入导航、列表、feed 和索引发现；Docusaurus 会添加 noindex/nofollow |
| Placeholder | `placeholder: true`, `unlisted: true`, `noindex: true` | 只保留短占位内容，用于预留 URL |
| Private | `private: true` | 生产构建失败，除非在非公开预览环境显式设置 `ALLOW_PRIVATE_CONTENT=true` |

静态站点前端不提供真正的加密或访问控制。不要把敏感内容放进会发布的 Markdown、MDX、静态资源、HTML、JS bundle、source map 或 JSON 中；真正的私有访问必须由托管平台、反向代理、认证网关或非公开预览环境实现。

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
| `npm run check:content-visibility` | 检查并阻断生产不安全的私有内容 |
| `npm run docs:versions:prepare` | 从配置的 Git ref 生成 Docusaurus 版本文件 |
| `npm run docs:versions:list` | 输出当前配置的文档版本 |
| `npm run validate` | 构建、检查内容清单并运行无头 UI 校验 |

---

## Contact & Community

- **Issues:** [GitHub Issues](https://github.com/apache/hugegraph-doc/issues)
- **Mailing List:** [dev@hugegraph.apache.org](mailto:dev@hugegraph.apache.org) ([subscribe first](https://hugegraph.apache.org/community/contribution-guidelines/subscribe/))
- **Slack:** [ASF Slack](https://the-asf.slack.com/archives/C059UU2FJ23)

<img src="./assets/images/wechat.png" alt="WeChat QR Code" width="350"/>

## Contributors

Thanks to all contributors to the HugeGraph documentation!

[![contributors](https://contrib.rocks/image?repo=apache/hugegraph-doc)](https://github.com/apache/hugegraph-doc/graphs/contributors)

---

## License

[Apache License 2.0](LICENSE)
