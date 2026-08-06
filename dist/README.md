# Apache HugeGraph 发版验证脚本

Apache HugeGraph 发布包的自动化验证脚本。

## 概述

`validate-release.sh` 脚本对 Apache HugeGraph 发布包进行全面验证，自动执行 [Apache 发布政策](https://www.apache.org/legal/release-policy.html) 的核心要求。

## 功能特性

- ✅ **自动依赖检查** - 验证所有必需工具（svn、gpg、java、maven 等）
- ✅ **SHA512 和 GPG 签名验证** - 确保包的完整性和真实性
- ✅ **许可证合规性验证** - 检查禁止的 ASF Category X 和需要文档化的 Category B 许可证
- ✅ **详细的许可证错误报告** - 对 Category X 违规显示文件路径、许可证名称和上下文
- ✅ **包内容验证** - 强校验 `LICENSE`、`NOTICE`
- ✅ **ASF 许可证头检查** - 验证所有源文件中的许可证头，支持第三方代码文档化
- ✅ **版本一致性验证** - 验证 Maven `<revision>` 属性与预期发布版本匹配
- ✅ **多语言项目支持** - 自动跳过 Python 项目（hugegraph-ai）的 Maven 版本检查
- ✅ **源码包编译** - 编译源码包以验证构建正确性
- ✅ **运行时测试** - 测试服务器和工具链（loader、tool、hubble）功能
- ✅ **智能进度跟踪** - 显示实时进度、步骤指示器和执行时间
- ✅ **上下文化错误报告** - 错误和警告包含步骤、包名和索引编号
- ✅ **详细日志记录** - 将所有输出保存到带时间戳的日志文件
- ✅ **全面的错误摘要** - 收集所有错误并在最后显示格式化摘要

## 环境要求

- Java 11（HugeGraph 1.5.0+ 必需）
- Maven 3.x
- svn（Subversion 客户端）
- gpg（用于签名验证的 GnuPG）
- wget 或 curl
- 标准 Unix 工具（bash、find、grep、awk、perl 等）

脚本会自动检查所有依赖项，如果缺少任何内容会提供安装说明。

## 使用方法

### 基本用法

```bash
# 查看帮助信息
./validate-release.sh --help

# 从 Apache SVN 验证（自动下载发布文件）
./validate-release.sh <版本号> <apache-用户名>

# 示例
./validate-release.sh 1.7.0 pengjunzhi
```

### 高级用法

```bash
# 从本地目录验证（如果已经下载了文件）
./validate-release.sh <版本号> <apache-用户名> <本地路径>

# 示例
./validate-release.sh 1.7.0 pengjunzhi /path/to/downloaded/dist

# 指定 Java 版本（默认：11）
./validate-release.sh <版本号> <apache-用户名> <本地路径> <java-版本>

# 示例 - 使用 Java 11
./validate-release.sh 1.7.0 pengjunzhi /path/to/dist 11

# 示例 - SVN 模式使用 Java 11
./validate-release.sh 1.7.0 pengjunzhi "" 11

# 非交互模式（用于 CI/CD）
./validate-release.sh --non-interactive 1.7.0 pengjunzhi

```

### 命令行选项

- `--help`, `-h` - 显示帮助信息并退出
- `--version`, `-v` - 显示脚本版本并退出
- `--non-interactive` - 无提示运行（用于 CI/CD 管道）

### `deploy-release.sh`（本地快速拉起）

该脚本用于从 `downloads.apache.org/hugegraph` 下载对应版本并快速启动 server/hubble。

```bash
./deploy-release.sh 1.7.0
```

## 验证步骤

脚本执行以下 9 个验证步骤：

1. **检查依赖项** - 验证所有必需工具已安装并显示版本信息
2. **准备发布文件** - 从 Apache SVN 下载或使用本地目录
3. **导入并信任 GPG 密钥** - 导入 KEYS 文件并信任所有公钥
4. **验证 SHA512 和 GPG 签名** - 验证所有包的校验和和签名
5. **验证源码包** - 对源码包进行全面检查：
   - 包命名（必须符合 `apache-hugegraph-<ver>*`）
   - 必需文件（`LICENSE`、`NOTICE`）
   - 许可证合规性（禁止 Category X，记录 Category B）
   - 详细的许可证违规报告（文件路径、许可证名称、上下文）
   - 无空文件或目录
   - 文件大小限制（无文件 > 800KB）
   - 二进制文件文档化（在 LICENSE 中声明）
   - 所有源文件的许可证头（支持第三方代码文档化）
   - Maven `<revision>` 属性版本一致性（跳过 Python 项目）
   - NOTICE 文件版权年份
   - 源码编译测试
6. **测试编译的服务器** - 初始化并启动编译的 HugeGraph 服务器
7. **测试编译的工具链** - 从编译包测试 loader、tool 和 hubble
8. **验证二进制包** - 检查二进制包的必需文件、licenses 目录和许可证合规性
9. **测试二进制包** - 从二进制包测试服务器和工具链功能

## 输出结果

### 进度指示器

脚本提供实时进度信息：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Apache HugeGraph Release Validation v2.2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Version:   1.7.0
  User:      pengjunzhi
  Java:      11
  Mode:      SVN Download
  Log:       logs/validate-1.7.0-20251115-021742.log

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step [1/9]: Check Dependencies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ svn: version 1.14.1
✓ gpg: gpg (GnuPG) 2.2.41
✓ java: 11.0.21
✓ mvn: Apache Maven 3.9.5
...
```

### 彩色结果

- ✓ **绿色** - 成功的检查
- ✗ **红色** - 需要修复的错误
- ⚠ **黄色** - 需要审查的警告
- **蓝色** - 步骤标题和进度信息

### 日志文件

所有输出都保存到 `logs/validate-<version>-<timestamp>.log` 以供后续查看。

### 最终摘要

验证结束时，会显示一个全面的摘要，包含执行时间和详细的错误/警告信息：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    VALIDATION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Execution Time: 6m 34s
Total Checks:   139
Passed:         134
Failed:         3
Warnings:       2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        ERRORS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[E1] [Step 8: Validate Binary Packages] [xxxx] contains 1 prohibited ASF Category X license(s):
xxxxx

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                       WARNINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
xxxx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VALIDATION FAILED
Log file: logs/validate-1.7.0-20251115-021742.log
```

## 许可证检查说明

### Category X 许可证（禁止使用）

脚本会严格检查以下 ASF Category X 许可证，发现后会报错并提供详细信息：

- GPL, LGPL 系列
- Sleepycat License
- BSD-4-Clause
- BCL (Binary Code License)
- JSR-275
- Amazon Software License
- RSAL (Reciprocal Public License)
- QPL (Q Public License)
- SSPL (Server Side Public License)
- CPOL (Code Project Open License)
- NPL1 (Netscape Public License)
- Creative Commons Non-Commercial
- **JSON.org** (JSON License)

**错误报告格式：**
```
Package 'xxx.tar.gz' contains 1 prohibited ASF Category X license(s):
    - File: licenses/LICENSE-json.txt
      License: JSON.org
      Context: Copyright (c) 2002 JSON.org
```

### Category B 许可证（需要文档化）

以下许可证会触发警告，提醒检查是否在 LICENSE 文件中正确记录：

- CDDL1, CPL, EPL, IPL, MPL, SPL
- OSL-3.0
- UnRAR License
- Erlang Public License
- OFL (SIL Open Font License)
- Ubuntu Font License Version 1.0
- IPA Font License Agreement v1.0
- EPL2.0
- CC-BY (Creative Commons Attribution)

**警告报告格式（简洁）：**
```
Package 'xxx.tar.gz' contains 2 ASF Category B license(s) - please verify documentation
```

### 许可证头检查

脚本会检查所有源代码文件（Java、Shell、Python、Go、JavaScript、TypeScript、C/C++、Scala、Groovy、Rust、Kotlin、Proto 等）是否包含 ASF 许可证头。

**第三方代码处理：**
- 如果源文件没有 ASF 许可证头，脚本会检查该文件是否在 LICENSE 文件中被文档化
- 支持通过文件名或相对路径匹配
- 已文档化的第三方代码会被标记为合法并单独统计
- 只有未文档化且缺少 ASF 头的文件才会报错

## 错误处理

脚本使用**"继续并报告"**方式：

- 不会在第一个错误时退出
- 收集所有验证错误和警告
- 在最后显示全面摘要，包含：
  - 执行总时间
  - 检查统计（总数、通过、失败、警告）
  - 带编号和上下文的错误列表
  - 带编号和上下文的警告列表
- 退出码 0 = 所有检查通过
- 退出码 1 = 一个或多个检查失败

每个错误和警告都包含：
- 编号索引（[E1], [E2], [W1], [W2] 等）
- 步骤上下文（哪个验证步骤）
- 包名上下文（哪个包）
- 详细的错误描述

这允许你一次看到所有问题，并能快速定位到具体的失败点。

## 特殊处理

### Python 项目（hugegraph-ai）

- 自动跳过编译步骤
- 自动跳过 Maven `<revision>` 版本检查
- 仍然执行其他所有验证（许可证、文件结构等）

### Computer 模块

- 在特殊目录结构下编译（`cd computer && mvn package`）
- 支持 Java 8 和 Java 11

## 故障排除

### Java 版本不匹配

如果看到 Java 版本错误：

```bash
# 检查你的 Java 版本
java -version

# 使用 JAVA_HOME 指定 Java 11
export JAVA_HOME=/path/to/java11
export PATH=$JAVA_HOME/bin:$PATH
```

### GPG 密钥问题

如果 GPG 密钥导入失败：

```bash
# 手动下载并导入 KEYS
curl https://downloads.apache.org/hugegraph/KEYS > KEYS
gpg --import KEYS

# 信任特定密钥
gpg --edit-key <user-email>
# 在 GPG 提示符中，输入: trust, 然后 5, 然后 y, 然后 quit

# 或者信任所有导入的密钥
for key in $(gpg --no-tty --list-keys --with-colons | awk -F: '/^pub/ {print $5}'); do
    echo -e "5\ny\n" | gpg --batch --command-fd 0 --edit-key "$key" trust
done
```

### 权限被拒绝

确保脚本可执行：

```bash
chmod +x validate-release.sh
```

### 许可证检查误报

如果合法的第三方代码被标记为缺少许可证头：

1. 确保在根目录的 `LICENSE` 文件中记录了该文件
2. 记录格式可以是文件名或相对路径
3. 重新运行验证脚本

示例 LICENSE 文件条目：
```
This product bundles ThirdParty.java from XYZ project,
which is available under a "MIT License".
For details, see licenses/LICENSE-mit.txt
```

### 查看详细日志

如果需要更多调试信息：

```bash
# 查看完整日志
cat logs/validate-<version>-<timestamp>.log

# 搜索特定错误
grep "ERROR" logs/validate-*.log

# 查看特定步骤
grep "Step \[5/9\]" logs/validate-*.log
```

## 参考文档

- [Apache 发布政策](https://www.apache.org/legal/release-policy.html)
- [Apache 许可证分类](https://www.apache.org/legal/resolved.html)
- [HugeGraph 验证发布指南](../content/cn/docs/contribution-guidelines/validate-release.md)

## 贡献

如果发现问题或有改进建议，请：

1. 查看现有问题：https://github.com/apache/hugegraph-doc/issues
2. 提交新问题或 pull request
