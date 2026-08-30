# Contribution Guide - Detailed Reference

> **快速开始请看 [README.md](./README.md)**，这里是详细的参考文档。

## PR 检查清单

提交 Pull Request 前请确认：

- [ ] 本地构建并验证了修改效果
- [ ] 同时更新了中文 (`content/cn/`) 和英文 (`content/en/`) 版本
- [ ] PR 描述中包含修改前后的截图对比
- [ ] 如有相关 Issue，已在 PR 中关联

---

## How to help us (如何参与)

1. 在本地 3 步快速构建官网环境，启动起来看下目前效果 (Auto reload)
2. 先 fork 仓库，然后基于 `master` 创建一个**新的**分支，修改完成后提交 PR ✅ (请在 PR 内**截图**对比一下修改**前后**的效果 & 简要说明，感谢)
3. 新增/修改网站/文档 (提供**中/英文**页面翻译，基本为 `markdown` 格式)

Refer: 不熟悉 **github-pr** 流程的同学, 可参考[贡献流程](https://github.com/apache/hugegraph/blob/master/CONTRIBUTING.md)文档, 推荐使用 [github desktop](https://desktop.github.com/) 应用, 会简单方便许多~

**PS:** 站点基于 [Docusaurus](https://docusaurus.io/) 构建，可参考 [Docusaurus 官方文档](https://docusaurus.io/docs) 了解更多。

# How to start the website locally (Docusaurus)

仅需 Node.js v18+，**3 步**即可启动：

```bash
# 1. 下载源码
git clone https://github.com/apache/hugegraph-doc.git website
cd website

# 2. 安装依赖
npm install

# 3. 启动开发服务器 (支持热重载)
npm run start
```

打开 http://localhost:3000 预览。

### 项目结构

```
content/          # 文档内容 (Markdown)
  cn/             # 中文文档
  en/             # 英文文档
src/              # Docusaurus 页面、CSS、组件
static/           # 静态资源
docusaurus.config.js  # 站点配置
sidebars*.js      # 侧边栏配置
scripts/          # 构建与验证脚本
```

详细的仓库结构请参考 [README.md](./README.md)。

## Troubleshooting

如果遇到构建错误，请确保：

- **Node.js >= v18**
- 执行 `npm install` 安装依赖
- 版本化文档已准备：`npm run docs:versions:prepare`
