---
title: "验证 Apache 发版"
linkTitle: "验证 Apache 发版"
weight: 3
---

Apache HugeGraph 已毕业为顶级项目。候选版本在 `dev@hugegraph.apache.org` 投票，不再提交 Incubator `general@incubator.apache.org` 审批。当前发布包名称必须以 `apache-hugegraph` 开头，不能包含 `incubating`；旧版本归档中的名称不受此规则影响。

## 准备环境

验证脚本需要 Bash、Subversion、GnuPG、Java 和 Maven。运行功能测试时使用 Java 11；不同组件的额外依赖以候选版本说明为准。

先从投票邮件确认版本号和发布经理的 Apache ID，然后在 `hugegraph-doc` 根目录运行：

```bash
# 从 ASF development distribution 下载并验证
./dist/validate-release.sh <version> <apache-id>

# 验证已经下载到本地的候选包
./dist/validate-release.sh <version> <apache-id> /path/to/release-files 11
```

脚本会检查 SHA-512、GPG 签名、包名、LICENSE、NOTICE、许可证类别、空文件、未声明的二进制文件，并尝试编译源码包和启动主要服务。完整参数见：

```bash
./dist/validate-release.sh --help
```

GitHub Actions 中的 `Validate Apache Release` workflow 使用同一发布目录，并在 Ubuntu 和 macOS 上执行对应检查。自动化结果不能替代人工检查。

## 人工检查

### 发布来源

- 候选包来自 `https://dist.apache.org/repos/dist/dev/hugegraph/<version>/`。
- KEYS 文件来自 `https://downloads.apache.org/hugegraph/KEYS`。
- 投票邮件中的 Git tag、commit 和下载目录相互对应。

### 源码包

- 根目录包含 LICENSE 和 NOTICE，内容与打包依赖一致。
- 源文件带有适用的 ASF License 头；没有未声明的二进制文件。
- Maven、Python、Go 等模块版本与候选版本一致。
- 按各仓库 README 和 CI 配置编译源码，并记录操作系统、Java/Python/Go 版本和执行命令。

### 二进制包

- 解压后的目录名和文件版本正确。
- Server、Loader、Hubble 等实际包含在候选版本中的程序可以启动或执行基本命令。
- LICENSE 和 NOTICE 覆盖随包分发的第三方文件。

历史 incubating 制品还需要检查 DISCLAIMER；毕业后的新制品不应包含 `incubating` 名称，也不把 DISCLAIMER 当作必需文件。

## 回复投票

回复必须列出实际完成的检查，不要只写结论。普通开发者使用 `non-binding`，PMC 成员使用 `binding`：

```text
+1 (binding 或 non-binding)

I checked:
- Download URL, tag and commit match
- SHA-512 checksums and GPG signatures pass
- LICENSE and NOTICE are present and consistent with package contents
- Source package builds on <OS> with <runtime versions>
- <services or commands actually tested>
```

如果投反对票，应附上可以复现的问题和对应文件。发现发布阻断问题后，停止当前候选版本并重新生成制品，不要在已投票的压缩包上直接替换文件。

参考资料：

- [ASF Release Policy](https://www.apache.org/legal/release-policy.html)
- [HugeGraph KEYS](https://downloads.apache.org/hugegraph/KEYS)
