# Validate Apache Release

LLMS index: [llms.txt](/versions/1.0/llms.txt)

---

> TODO: Translate this article to English!

## 验证阶段

当内部的临时发布和打包工作完成后, 其他的社区开发者(尤其是 PMC)需要参与到[验证环节](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist)确保某个人发布版本的"正确性 + 完整性", 这里需要**每个人**都尽量参与, 然后后序**邮件回复**的时候说明自己**已检查**了哪些项. (下面是核心项)

#### 1. 检查 hash 值

首先需要检查 `source + binary` 包的文件完整性, 通过 `shasum` 进行校验, 确保和发布到 apache/github 上的 hash 值一致 (一般是 sha512), 这里同0x02的最后一步检验.

#### 2. 检查 gpg 签名

这个就是为了确保发布的包是由**可信赖**的人上传的, 假设 tom 签名后上传, 其他人应该下载 A 的**公钥**然后进行**签名确认**, 相关命令:

```bash
# 1. 下载项目可信赖公钥到本地 (首次需要)
curl xxx >> PK
gpg --import PK
# 1.2 等待响应后输入 trust 表示信任 tom 的公钥 (其他人名类似)
gpg -edit-key tom 

# 2. 检查签名 (可用 0x03 章节的第 ⑧ 步的 for 循环脚本批量遍历)
gpg --verify xx.asc xxx-source.tar.gz
gpg --verify xx.asc xxx-binary.tar.gz # 注: 我们目前没有 binary 后缀
```

先确认了整体的完整性/一致性, 然后接下来确认具体的内容 (**关键**)

#### 3. 检查压缩包内容

这里分源码包 + 二进制包两个方面, 源码包更为严格, 挑核心的部分说 (完整的列表参考官方 [Wiki](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist), 比较长)

首先我们需要从 apache 官方的 `release-candidate` 地址下载包到本地 (地址: `dist.apache.org/repos/dist/dev/hugegraph/`)

##### A. 源码包

解压 `xxx-hugegraph-source.tar.gz`后, 进行如下检查:

1. 文件夹都带有 `incubating`, 且不存在**空的**文件/文件夹
2. 存在`DISCLAIMER`文件
3. 存在 `LICENSE` + `NOTICE` 文件并且内容正常
4. **不存在**任何二进制文件
5. 源码文件都包含标准 `ASF License` 头 (这个用插件跑一下为主)
6. 检查每个父/子模块的 `pom.xml` 版本号是否一致 (且符合期望)
7. 检查前 3 ~ 5 个 commit 提交, 点进去看看是否修改处和源码文件一致
8. 最后, 确保源码可以正常/正确编译 (然后看看测试和规范)

```bash
# 同时也可以检查一下代码风格是否符合规范, 不符合的可以放下一次调整
mvn clean test -Dcheckstyle.skip=false
```

##### B. 二进制包

解压 `xxx-hugegraph.tar.gz`后, 进行如下检查:

1. 文件夹都带有 `incubating`
2. 存在 `LICENSE` + `NOTICE` 文件并且内容正常
3. 通过 gpg 命令确认每个文件的签名正常

**注:** 如果二进制包里面引入了第三方依赖, 则需要更新 LICENSE, 加入第三方依赖的 LICENSE; 若第三方依赖 LICENSE 是 Apache 2.0, 且对应的项目中包含了 NOTICE, 则还需要更新我们的 NOTICE 文件

#### 4. 检查官网以及 github 等页面

1. 确保官网至少满足 [apache website check](https://whimsy.apache.org/pods/project/hugegraph), 以及没有死链等
2. 更新**下载链接**以及版本更新说明
3. ...
