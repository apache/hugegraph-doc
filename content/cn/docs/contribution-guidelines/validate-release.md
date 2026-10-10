---
title: "验证 Apache 发版"
linkTitle: "验证 Apache 发版"
weight: 3
---

> Note: 这篇文档会持续更新。
> HugeGraph 1.8.0 的源码构建与发行包运行验证统一使用 Java 17。
>
> 毕业说明：Apache HugeGraph 已于 2026 年 1 月毕业。正式发版投票现由 HugeGraph 社区内部完成（`dev@hugegraph.apache.org` 上的 PMC binding 投票），不再需要 Incubator `general@incubator.apache.org` 审批。

## 自动化发版验证

Workflow 与 `dist/validate-release.sh` 共用 Java 17 校验逻辑。发行版本与 SVN RC 路径分别指定，
Maven staging repository 使用投票邮件中的地址。Server/Toolchain 四个源码和二进制包是必需项，
同一候选目录也可包含 AI、Computer 源码包。每个包均须附带 SHA512 与 GPG 签名；未知包名和版本不符会阻断验证。
所有包均检查完整性、内容和许可证，Computer 源码另执行 Maven 构建；AI、Computer 产品运行验证需另行完成。

```bash
bash dist/validate-release.sh --svn-path 1.8.0/RC1 \
  --staging-repository https://repository.apache.org/content/repositories/<staging-id>/ 1.8.0 pengjunzhi
# 原有本地包位置参数接口保留：
bash dist/validate-release.sh 1.8.0 pengjunzhi /path/to/rc 17
```

严格 RC 模式使用全新、相互隔离的 Maven 仓库，不预装本地 Server SDK。
源码构建产物和下载的二进制包分别执行 Server、Client、普通 Loader、Tools 与 Hubble 业务断言，失败后保留日志。
Workflow 的 `source-prevalidation` 模式使用明确的 Server/Toolchain commit SHA 和无签名源码归档，
它不证明真实 RC 签名、下载及远端 staging 依赖解析已通过。
`license-review-*.txt` 中的许可选择和例外仍需人工复核，明确的 Category-X-only 依赖会阻断验证；自动成功不等于发布批准。
本地预验证和证据目录说明见[验证脚本指南](https://github.com/apache/hugegraph-doc/blob/master/dist/README.md)。

控制台和 GitHub Job Summary 汇总结果、失败阶段、复核提示及日志位置；源码预验证不会显示为 RC 验收通过。

## 验证阶段

当内部的临时发布和打包工作完成后，其他的社区开发者 (尤其是 PMC)
需要按 ASF 发版规范参与验证，可参考：
- [ASF 发布策略](https://www.apache.org/legal/release-policy.html)
- [Incubator 检查清单（历史参考）](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist)
确保某个人发布版本的"正确性 + 完整性", 这里需要**每个人**都尽量参与，然后后序**邮件回复**的时候说明自己
**已检查**了哪些项。(下面是核心项)

#### 1. 准备工作

如果本地没有 svn 或 gpg 或 wget 环境，建议先安装一下 (windows 推荐使用 WSL2 环境，
或者至少是 `git-bash`), 同时确保安装 Java 17 和 maven 软件。

```bash
# 1. 安装svn
# ubuntu/debian
sudo apt install subversion -y
# MacOS
brew install subversion
# 验证安装是否成功, 执行以下命令:
svn --version

# 2. 安装gpg
# ubuntu/debian
sudo apt-get install gnupg -y
# MacOS
brew install gnupg
# 验证安装是否成功, 执行以下命令:
gpg --version

# 3. 安装wget
# ubuntu/debian
sudo apt-get install wget -y
# MacOS
brew install wget

# 4. 下载 hugegraph-svn 目录 (版本号注意填写此次验证版本)
svn co https://dist.apache.org/repos/dist/dev/hugegraph/1.x.x/
# (注) 如果出现 svn 下载某个文件速度很慢的情况, 可以考虑 wget 单个文件下载, 如下 (或考虑使用 VPN / 代理)
wget https://dist.apache.org/repos/dist/dev/hugegraph/1.x.x/apache-hugegraph-toolchain-1.x.x.tar.gz
```

#### 2. 检查 hash 值

首先需要检查 `source + binary` 包的文件完整性，通过 `shasum` 进行校验，确保和发布到 apache/github 上的
hash 值一致 (一般是 sha512)

```bash
执行命令:
for i in *.tar.gz; do echo $i; shasum -a 512 --check  $i.sha512; done
```

#### 3. 检查 gpg 签名

这个就是为了确保发布的包是由**可信赖**的人上传的，假设 tom 签名后上传，其他人应该下载 A 的**公钥**
然后进行**签名确认**, 相关命令：

```bash
# 1. 下载项目可信赖公钥到本地 (首次需要) & 导入
curl  https://downloads.apache.org/hugegraph/KEYS > KEYS
gpg --import KEYS

# 导入后可以看到如下输出, 这代表导入了 x 个用户公钥
gpg: /home/ubuntu/.gnupg/trustdb.gpg: trustdb created
gpg: key BA7E78F8A81A885E: public key "imbajin (apache mail) <jin@apache.org>" imported
gpg: key 818108E7924549CC: public key "vaughn <vaughn@apache.org>" imported
gpg: key 28DCAED849C4180E: public key "coderzc (CODE SIGNING KEY) <zhaocong@apache.org>" imported
....
gpg: Total number processed: x
gpg:               imported: x

# 2. 将完整主密钥指纹与发版投票邮件中的签名者指纹对照
release_signer_fingerprint='<signer-full-fingerprint>'
gpg --fingerprint -- "$release_signer_fingerprint"

# 3. 在子 shell 中验证，失败时停止检查但不退出交互终端
(
  for archive in *.tar.gz; do
    gpg --status-fd 1 --verify -- "$archive.asc" "$archive" > "$archive.status" || {
      status=$?
      printf 'Signature verification failed: %s\n' "$archive" >&2
      cat "$archive.status"
      exit "$status"
    }
    cat "$archive.status"
    if grep -Eq '^\[GNUPG:\] (REVKEYSIG|EXPKEYSIG|EXPSIG)( |$)' "$archive.status"; then
      printf 'Expired or revoked signature: %s\n' "$archive" >&2
      exit 1
    fi
    grep -q '^\[GNUPG:\] VALIDSIG ' "$archive.status" || {
      printf 'Missing valid signature: %s\n' "$archive" >&2
      exit 1
    }
  done
)
```

必须同时确认验证退出码为零，且 `VALIDSIG` 中的指纹对应投票邮件的签名者；使用签名子密钥时，核对其报告的主密钥指纹。
密钥信任警告本身不表示签名无效，也不能只凭本地化的 `Good signature` 文本判断成功。
即使同时出现 `VALIDSIG` 或退出码为零，遇到 `REVKEYSIG`、`EXPKEYSIG`、`EXPSIG` 仍须停止，交由发版负责人复核或更新候选包。
格式见 [GnuPG 状态说明](https://github.com/gpg/gnupg/blob/master/doc/DETAILS)。

先确认了整体的"完整性 + 一致性", 然后接下来确认具体的内容 (**关键**)

#### 4. 检查压缩包内容

这里检查准备工作下载的压缩包内容。分源码包 + 二进制包两个方面，源码包更为严格，挑核心的部分说 
(完整的列表可参考官方 [Wiki](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist), 比较长)

##### A. 源码包

解压 `*hugegraph*src.tar.gz`后，进行如下检查：

1. 包名/目录名应符合当前发版命名（历史版本可能仍包含 `incubating`），且不存在**空的**文件/文件夹
2. 存在 `LICENSE` + `NOTICE` 且内容正常；历史版本若在项目孵化期发布，还需检查 `DISCLAIMER`
3. **不存在** 缺乏 License 的二进制文件
4. 源码文件都包含标准 `ASF License` 头 (这个用插件跑一下为主)
5. 检查每个父 / 子模块的 `pom.xml` 版本号是否一致 (且符合期望)
6. 最后，确保源码可以正常 / 正确编译 (然后看看测试和规范)

PMC 同学请特别注意认真检查 `LICENSE` + `NOTICE` 文件，确保文件严格遵循了 ASF 的发版要求， 
大部分的发版问题都与之相关

```bash
# 请优先使用/切换到 `java 17` 版本进行后序的编译和运行操作 (注:`Computer` 仅支持 `java >= 11`)
# java --version

# 尝试在 Unix 环境下编译测试是否正常
mvn -s /path/to/staging-settings.xml -Dmaven.repo.local=/path/to/fresh-m2 \
  clean install -Papache-release -DskipTests -Dgpg.skip=true
```

手动 Maven 命令的 settings 必须指向投票邮件中的 staging repository，并使用全新的本地仓库。
不要预装本地 Server SDK 来掩盖 staging 缺少依赖；自动化验证脚本会生成这些设置。

##### B. 二进制包

解压 `xxx-hugegraph.tar.gz`后，进行如下检查：

1. 包名/目录名应符合当前发版命名（历史版本可能仍包含 `incubating`）
2. 存在 `LICENSE` + `NOTICE` 且内容正常（历史版本若在项目孵化期发布，还需检查 `DISCLAIMER`）
3. 服务启动

```bash
# hugegraph-server
bin/start-hugegraph.sh

# hugegraph-loader
bin/hugegraph-loader.sh -g hugegraph -f example/file/struct.json -s example/file/schema.groovy

# hugegraph-hubble
bin/start-hubble.sh

更多参考官网: https://hugegraph.apache.org/cn/docs/quickstart
```

**注:** 如果二进制包里面引入了第三方依赖, 则需要更新 LICENSE, 加入第三方依赖的 LICENSE; 若第三方依赖
LICENSE 是 Apache 2.0, 且对应的项目中包含了 NOTICE, 则还需要更新我们的 NOTICE 文件

#### 5. 检查官网以及 github 等页面

1. 确保官网至少满足 [apache website check](https://whimsy.apache.org/pods/project/hugegraph),
   以及没有死链等
2. 更新**下载链接**存在，以及版本更新说明页面更新
3. ...

## 邮件模板

检查完成后，你应该按不同角色回复邮件：(普通开发者 & PMC 成员)

```markdown
[] +1 approve

[] +0 no opinion

[] -1 disapprove with the reason
```

```markdown
+1 (non-binding)
I checked:
1. Download link/tag in mail are valid
2. Checksum and GPG signatures are OK
3. LICENSE & NOTICE exist
4. Build successfully on XX OS version XXX
5. No unexpected binary files
6. Date is right in the NOTICE file
7. Compile from source is fine under JavaX
8. No empty file & directory found
9. Test running xxx service OK
10. ....
```

特别注意 PMC 成员必须使用 `binding` 标记回复邮件，这对于统计有效投票很重要;

```markdown
+1 (binding)
I checked:
1. Download link/tag in mail are valid
2. Checksum and GPG signatures are OK
3. LICENSE & NOTICE exist
4. Build successfully on XX OS Version XX
5. No unexpected binary files
6. Date is right in the NOTICE file
7. Compile from source is fine under JavaXX
8. No empty file & directory found
9. Test running XXX service OK
10. ....
```
