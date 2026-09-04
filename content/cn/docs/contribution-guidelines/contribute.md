---
title: "参与 HugeGraph 社区"
linkTitle: "贡献流程"
weight: 1
---

## 选择贡献方式

可以通过 [GitHub Issues](https://github.com/apache/hugegraph/issues) 报告问题，也可以提交代码、测试或文档。准备较大的改动前，建议先创建 Issue 并说明范围，避免重复工作。

下面以 `apache/hugegraph` 为例。其他 HugeGraph 仓库的流程相同，但构建和测试命令应以各仓库的 `README.md`、`AGENTS.md` 和 CI 配置为准。

## 准备仓库

![在 GitHub 上 Fork HugeGraph 仓库](/images/docs/contribution/github-fork.png)
{width="884" height="462"}

先在 GitHub 上 fork [apache/hugegraph](https://github.com/apache/hugegraph)，再克隆自己的 fork：

```bash
git clone https://github.com/<your-name>/hugegraph.git
cd hugegraph
git remote add upstream https://github.com/apache/hugegraph.git
git fetch upstream master
```

不要直接在 `master` 上开发。每项改动使用单独分支：

```bash
git switch master
git merge --ff-only upstream/master
git switch -c fix/<short-description>
```

## 修改和验证

HugeGraph Server 的代码位于 `hugegraph-server/`。例如，核心模块路径是：

```text
hugegraph-server/hugegraph-core/src/main/java/org/apache/hugegraph/
```

先运行与改动直接相关的测试。Server 常用测试入口如下：

```bash
# Core 测试，使用内存后端
mvn test -pl hugegraph-server/hugegraph-test -am -P core-test,memory

# API 测试，使用 RocksDB 后端
mvn test -pl hugegraph-server/hugegraph-test -am -P api-test,rocksdb

# 格式化并检查编译
mvn editorconfig:format
mvn clean compile -Dmaven.javadoc.skip=true
```

Note that since GitHub requires submitting code through `username + token` (instead of using `username + password` directly), you need to create a GitHub token from https://github.com/settings/tokens:

![使用个人访问令牌认证 Git 推送](/images/docs/contribution/github-authentication.png)
{width="1280" height="422"}

提交第三方依赖时，还要同步发行包中的许可证信息：

1. 把依赖的许可证文件放入 `hugegraph-server/hugegraph-dist/release-docs/licenses/`。
2. 更新 `hugegraph-server/hugegraph-dist/release-docs/LICENSE`；依赖包含 NOTICE 时，同时更新 `NOTICE`。
3. 运行 `hugegraph-server/hugegraph-dist/scripts/dependency/regenerate_known_dependencies.sh`，更新已知依赖清单。

## 提交 Pull Request

Note: please make sure the email address you used to submit the code is bound to the GitHub account. For how to bind the email address, please refer to https://github.com/settings/emails:

![在 GitHub 中验证提交邮箱](/images/docs/contribution/github-email.png)
{width="1280" height="592"}

提交信息使用 `type(module): message` 格式，例如：

```bash
git add <changed-files>
git commit -m "fix(core): handle empty vertex query"
git push -u origin fix/<short-description>
```

然后从 fork 分支向 `apache/hugegraph:master` 创建 Pull Request。说明问题、修改方法和实际运行的验证命令；界面变化应附截图。

## 处理 Review

CI 失败或 reviewer 要求修改时，在原分支继续提交并推送。需要同步上游时，可以 rebase：

```bash
git fetch upstream master
git rebase upstream/master
git push --force-with-lease
```

不要使用普通 `--force` 覆盖远端分支。完成所有 CI 和 review 要求后，由项目 maintainer 合并 Pull Request。

Contributor Agreement 使用 ASF 官方流程，见[贡献者协议](/cn/docs/CLA/)。
