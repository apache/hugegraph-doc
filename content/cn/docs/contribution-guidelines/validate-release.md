---
title: "验证 Apache 发版"
linkTitle: "验证 Apache 发版"
weight: 3
---

> Note: 这篇文档会持续更新。
> 你需要使用 Java11 验证测试 (如果希望测试功能/运行时)，从 1.5.0 版本开始 (除 client 外) 不再支持 Java8
>
> 毕业说明：Apache HugeGraph 已于 2026 年 1 月毕业。正式发版投票现由 HugeGraph 社区内部完成（`dev@hugegraph.apache.org` 上的 PMC binding 投票），不再需要 Incubator `general@incubator.apache.org` 审批。

## 验证阶段

当内部的临时发布和打包工作完成后，其他的社区开发者 (尤其是 PMC)
需要按 ASF 发版规范参与验证，可参考：
- [ASF 发布策略](https://www.apache.org/legal/release-policy.html)
- [Incubator 检查清单（历史参考）](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist)
确保某个人发布版本的"正确性 + 完整性", 这里需要**每个人**都尽量参与，然后后序**邮件回复**的时候说明自己
**已检查**了哪些项。(下面是核心项)

#### 1. 准备工作

如果本地没有 svn 或 gpg 或 wget 环境，建议先安装一下 (windows 推荐使用 WSL2 环境，
或者至少是 `git-bash`), 同时确保安装 Java(推荐 11) 和 maven 软件。

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
wget https://dist.apache.org/repos/dist/dev/hugegraph/1.x.x/apache-hugegraph-toolchain-incubating-1.x.x.tar.gz
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

# 2. 信任发版用户 (你需要信任 n 个邮件里提到的 gpg 用户名, ＞1则依次执行相同操作)
gpg --edit-key $USER # 这里填写具体用户名或者公钥串, 回车进入交互模式
gpg> trust
...输出选项..
Your decision? 5 # 选择5
Do you really want to set this key to ultimate trust? (y/N) y # 选择y, 然后 q 退出信任下一个用户

# (可选) 你也可以直接使用非交互模式的如下命令:
echo -e "5\ny\n" | gpg --batch --command-fd 0 --edit-key $USER trust
# 或者是信任所有当前导入过的 gpg 公钥 (请小心检查)
for key in $(gpg --no-tty --list-keys --with-colons | awk -F: '/^pub/ {print $5}'); do
  echo -e "5\ny\n" | gpg --batch --command-fd 0 --edit-key "$key" trust
done

# 3. 检查签名(确保没有 Warning 输出, 每一个 source/binary 文件都提示 Good Signature)
#单个文件验证
gpg --verify xx.asc xxx-src.tar.gz
gpg --verify xx.asc xxx.tar.gz # 注：目前没有  bin/binary  后缀

# 一行脚本快速验证所有包 (推荐使用，请确保所有 gpg 公钥已经信任)
for i in *.tar.gz; do echo $i; gpg --verify $i.asc $i ; done
```

先确认了整体的"完整性 + 一致性", 然后接下来确认具体的内容 (**关键**)

#### 4. 检查压缩包内容

这里检查准备工作下载的压缩包内容。分源码包 + 二进制包两个方面，源码包更为严格，挑核心的部分说 
(完整的列表可参考官方 [Wiki](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist), 比较长)

##### A. 源码包

解压 `*hugegraph*src.tar.gz`后，进行如下检查：

1. 包名/目录名应符合当前发版命名（历史版本可能仍包含 `incubating`），且不存在**空的**文件/文件夹
2. 存在 `LICENSE` + `NOTICE` 且内容正常；历史 incubating 制品需检查 `DISCLAIMER`
3. **不存在** 缺乏 License 的二进制文件
4. 源码文件都包含标准 `ASF License` 头 (这个用插件跑一下为主)
5. 检查每个父 / 子模块的 `pom.xml` 版本号是否一致 (且符合期望)
6. 最后，确保源码可以正常 / 正确编译 (然后看看测试和规范)

PMC 同学请特别注意认真检查 `LICENSE` + `NOTICE` 文件，确保文件严格遵循了 ASF 的发版要求， 
大部分的发版问题都与之相关

```bash
# 请优先使用/切换到 `java 11` 版本进行后序的编译和运行操作 (注:`Computer` 仅支持 `java >= 11`) 
# java --version

# 尝试在 Unix 环境下编译测试是否正常
mvn clean package -DskipTests -Dcheckstyle.skip=true -P stage
```

##### B. 二进制包

解压 `xxx-hugegraph.tar.gz`后，进行如下检查：

1. 包名/目录名应符合当前发版命名（历史版本可能仍包含 `incubating`）
2. 存在 `LICENSE` + `NOTICE` 且内容正常（历史 incubating 制品需检查 `DISCLAIMER`）
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
3. LICENSE & NOTICE & DISCLAIMER are exist
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
3. LICENSE & NOTICE & DISCLAIMER are exist
4. Build successfully on XX OS Version XX
5. No unexpected binary files
6. Date is right in the NOTICE file
7. Compile from source is fine under JavaXX
8. No empty file & directory found
9. Test running XXX service OK
10. ....
```
