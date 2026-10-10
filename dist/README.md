# Apache HugeGraph 发版验证

`validate-release.sh` 与 `.github/workflows/validate-release.yml` 共用校验逻辑。HugeGraph 1.8.0 使用 Java 17，
新源码包和二进制包不含 `incubating`。验证只读取发行文件，不执行发布或 Maven staging 的 release/promote。

## 环境

需要 Java 17（含 `javac`）、Maven、Python 3.9+、GPG、curl、tar、shasum、Perl 和标准 Unix 工具。
SVN 下载模式还需要 Subversion；源码预构建需要 Git 和 Linux 的 `libgomp1`。Hubble 的 Maven 构建自动下载其固定的 Node/Yarn。
macOS 需要 coreutils，供发行项目的打包脚本使用。

## 严格 RC 验证

```bash
# 默认候选路径为 dev/hugegraph/1.8.0
bash dist/validate-release.sh 1.8.0 pengjunzhi

# SVN 候选目录与发行版本分开指定
bash dist/validate-release.sh --svn-path 1.8.0/RC1 \
  --staging-repository https://repository.apache.org/content/repositories/<staging-id>/ \
  1.8.0 pengjunzhi

# 已下载的本地发行文件；原有位置参数接口保留，Java 默认 17
bash dist/validate-release.sh --staging-repository https://repository.apache.org/content/repositories/<staging-id>/ \
  1.8.0 pengjunzhi /path/to/rc 17
```

以下四个包是必需项，每个包均须有 `.sha512` 和 `.asc`：

- `apache-hugegraph-1.8.0-src.tar.gz`
- `apache-hugegraph-1.8.0.tar.gz`
- `apache-hugegraph-toolchain-1.8.0-src.tar.gz`
- `apache-hugegraph-toolchain-1.8.0.tar.gz`

同一目录可另含 `apache-hugegraph-computer-1.8.0-src.tar.gz`、`apache-hugegraph-ai-1.8.0-src.tar.gz`。
所有归档均验证签名、SHA512、内容和许可证；Computer 源码另执行 Maven 构建。未知归档或版本不符均失败，不能跳过签名。
AI、Computer 产品运行验证需另行完成；本脚本的完整业务链路仅覆盖 Server/Toolchain。

签名使用项目 KEYS 中由 `gpg-user` 选定的公钥验证，其他签名者的有效签名也会被拒绝；不修改用户的 GPG 信任设置。仍需按投票邮件核对签名者指纹。
校验通过后才解压构建；Server 与 Toolchain 使用独立、全新的 Maven 仓库，严格 RC 模式不预装本地 Server SDK。
应指定投票邮件中的 staging repository；默认值为 Apache staging group。

源码检查保留 LICENSE、NOTICE、许可证分类、空文件、源码头和 Maven 版本检查。
大于 800KB 的源码文件列为人工复核提示，大小本身不是 ASF 发布禁止条件。
源码构建产物与下载的二进制包分别验证，不能用一次启动替代两者。

## 许可证复核边界

二进制包的 LICENSE/NOTICE/licenses 关键词命中带上下文列为人工复核提示；它可能描述未打包资源或许可替代项，不能据此断言依赖违规。
脚本读取实际 JAR 内嵌 Maven POM 的许可声明，明确无替代项/例外的 Category-X-only 声明仍失败；
多许可、例外、Category B、缺少声明或继承信息写入 `license-review-*.txt`，需对照实际组件源码和发布资料复核。
源包原有 Category X 检查保留。CI 成功表示自动检查通过，不表示许可复核已完成或发布已获批准。
许可选择及 ClasspathException 条件遵循 [ASF 第三方许可政策](https://www.apache.org/legal/resolved.html) 中的相应规则。

## 无真实 RC 时的源码预验证

```bash
# 输出目录必须不存在；使用两个完整 commit SHA，以便恢复同一构建
bash dist/prepare-release.sh 1.8.0 <server-commit-sha> <toolchain-commit-sha> /path/to/prevalidation
bash dist/validate-release.sh --source-prevalidation --sdk-repository /path/to/prevalidation/m2 \
  1.8.0 unused /path/to/prevalidation/packages
```

此模式实际构建 `git archive` 导出的源码，使用同源 Server 安装的 SDK，再生成二进制包和 SHA512。
验证报告明确标注它没有验证真实 RC 下载、签名或远端 staging 依赖来源，不可将其作为正式 RC 验证结论。

## 核心链路与证据

每组包均在独立目录中运行 RocksDB Server，等待 API 和 Gremlin 可用后执行以下检查：

- Client 创建 schema、写入顶点/边、查询并清理。
- 普通 Loader 导入自带 file 示例，并断言数据数量。
- Tools 执行 Gremlin、task-list 和 backup，检查实际非空备份文件。
- Hubble 检查 `/about` 业务状态，登录、读取 graphspace 和 Server schema，再检查停止结果。

脚本只修改自己的解压目录，保留失败日志并清理本次启动的服务。任一关键检查失败返回非零。
每次运行创建新的 `dist/validation/<version>.<run-id>/`，`--work-dir` 可指定父目录。
目录包含 `validation.log`、源码和二进制运行日志、隔离 Maven 仓库及 Tools 备份；不要将该目录提交到 Git。

CI 的 `rc` 模式保留四个 Linux/macOS 平台，全部 Java 17；`source-prevalidation` 默认 Ubuntu，
可通过 `all_platforms` 扩大。失败时上传验证日志。源码模式必须提供两个完整 commit SHA。

## 本地检查

```bash
bash -n dist/validate-release.sh dist/prepare-release.sh
shellcheck dist/validate-release.sh dist/prepare-release.sh
actionlint .github/workflows/validate-release.yml
python3 -m unittest discover -s dist/tests
```

参见 [英文验证指南](../content/en/docs/contribution-guidelines/validate-release.md)、
[中文验证指南](../content/cn/docs/contribution-guidelines/validate-release.md) 和
[ASF 发布策略](https://www.apache.org/legal/release-policy.html)。

控制台和 GitHub Job Summary 汇总结果、失败阶段、复核提示及日志位置；源码预验证不会显示为 RC 验收通过。
