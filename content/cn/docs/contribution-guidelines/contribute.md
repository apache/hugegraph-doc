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

当前主仓库根目录的 Maven 模块如下；Server 的存储适配器 `hugegraph-server/hugegraph-hstore/` 与独立的存储节点项目 `hugegraph-store/` 是不同模块。

| 路径 | 子模块 |
|---|---|
| `hugegraph-server/` | `hugegraph-core/`、`hugegraph-api/`、`hugegraph-example/`、`hugegraph-dist/`、`hugegraph-test/`、`hugegraph-rocksdb/`、`hugegraph-hbase/`、`hugegraph-hstore/` |
| `hugegraph-pd/` | `hg-pd-common/`、`hg-pd-client/`、`hg-pd-core/`、`hg-pd-service/`、`hg-pd-dist/`、`hg-pd-cli/`、`hg-pd-grpc/`、`hg-pd-test/` |
| `hugegraph-store/` | `hg-store-common/`、`hg-store-client/`、`hg-store-core/`、`hg-store-node/`、`hg-store-dist/`、`hg-store-cli/`、`hg-store-grpc/`、`hg-store-rocksdb/`、`hg-store-test/` |
| `hugegraph-commons/` | `hugegraph-common/`、`hugegraph-rpc/` |
| `hugegraph-cluster-test/` | `hugegraph-clustertest-minicluster/`、`hugegraph-clustertest-dist/`、`hugegraph-clustertest-test/` |
| 独立根模块 | `hugegraph-struct/`、`install-dist/` |

上述名称来自根 `pom.xml` 及各子项目 `pom.xml`；代码结构以正在使用的分支为准。

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

GitHub 已不支持通过用户名和密码直接推送代码。需要使用个人访问令牌时，请在[令牌设置页](https://github.com/settings/tokens)创建并按需授权：

![使用个人访问令牌认证 Git 推送](/images/docs/contribution/github-authentication.png)
{width="1280" height="422"}

提交第三方依赖时，还要同步发行包中的许可证信息：

1. 把依赖的许可证文件放入 `hugegraph-server/hugegraph-dist/release-docs/licenses/`。
2. 更新 `hugegraph-server/hugegraph-dist/release-docs/LICENSE`；依赖包含 NOTICE 时，同时更新 `NOTICE`。
3. 运行 `hugegraph-server/hugegraph-dist/scripts/dependency/regenerate_known_dependencies.sh`，更新已知依赖清单。

## 提交 Pull Request

提交代码所用的邮箱需要绑定到 GitHub 账号。请在[邮箱设置页](https://github.com/settings/emails)完成绑定：

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

Contributor Agreement 使用 ASF 官方流程，见[贡献者协议]({{< ref path="/docs/CLA.md" lang="cn" >}})。
