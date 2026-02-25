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

**PS:** 可以参考其他官网的[源码](https://www.docsy.dev/docs/examples), 方便快速了解 docsy 主题结构.

# How to start the website locally (hugo)

Only **3 steps** u can easily to get start~

U should ensure NPM & Hugo binary [download url](https://github.com/gohugoio/hugo/releases) before start, 
hugo binary must end with "**extended**" suffix, and we don't need to install go env, 
just download hugo binary is fine (Note: the Hugo version can't be **too high**, try downgrade if failed)

```bash
# 0. install npm & hugo if you don't have it

# Mac version (0.95 extend)
wget https://github.com/gohugoio/hugo/releases/download/v0.95.0/hugo_extended_0.95.0_macOS-64bit.tar.gz

# Linux version (0.95 extend)
wget https://github.com/gohugoio/hugo/releases/download/v0.95.0/hugo_extended_0.95.0_Linux-64bit.tar.gz

# 解压后 hugo 是单二进制文件, 可直接使用, 或推荐放 /usr/bin 及环境变量下.
sudo install hugo /usr/bin # 如果 mac 提示没有权限, 可以 sudo mv hugo /usr/local/bin

# 1. download website's source code
git clone https://github.com/apache/hugegraph-doc.git website

# (Optional) if download slowly or failed, try the proxy url
git clone https://api.mtr.pub/apache/hugegraph-doc.git website # or https://github.do/https://github.com/apache/hugegraph-doc.git

# 2. install npm dependencies in project root dir
cd website && npm install

# 3. just start server in localhost now (Don't need do anything else)
hugo server

# (optional) if you want modify ip or port, try like this
hugo server -b http://127.0.0.1 -p 80 --bind=0.0.0.0

```

# How to modify the docsy theme (**Important**)

Here we need FE to modify / enhance the css/js/theme config, and we also need to translate doc and website

You can find detailed **theme instructions** in the [Docsy user guide - Content and Customization](https://www.docsy.dev/docs/adding-content/)

1. `config.toml` in the **root dir** is global config
2. `config.toml` in the `./themes/docsy` is theme config
3. `content` dir contains multi-language contents (docs/index-html/blog/about/bg-image), it's the most important dir
    - `content/en` represent english site, we do need to translate the `doc` in it (可先用 Google/GPT 翻译)
    - `content/cn` represent chinese site (需要汉化其中英文部分)

We can see some [example website](https://www.docsy.dev/docs/examples/) & refer to their GitHub **source code** to reduce time to design

<img width="440" alt="image" src="https://user-images.githubusercontent.com/17706099/164688677-c2da2fc6-a88e-4786-a648-07a481cc8f9d.png">


## Troubleshooting

If you run into the following error:

```
➜ hugo server

Error: Error building site: TOCSS: failed to transform "scss/main.scss" (text/x-scss): 
resource "scss/scss/main.scss_9fadf33d895a46083cdd64396b57ef68" not found in file cache
```

This error occurs if you have not installed the extended version of [Hugo](https://github.com/gohugoio/hugo/releases).

[Docsy]: https://github.com/google/docsy
[example.docsy.dev]: https://example.docsy.dev
