---
title: "ToplingDB 开发版集成"
linkTitle: "ToplingDB（开发版）"
weight: 11
description: "从开发源码构建可选 ToplingDB 运行时，隔离数据目录，并了解启动与恢复边界。"
---

> **尚未发布的开发接口。** 本文介绍用于替换 2025 年 ToplingDB 集成的候选实现。
> 需要使用包含该集成及其生命周期、快照恢复前置修改的完整源码。
> 这些修改仍在审查中；已有 HugeGraph 发行版和镜像标签不能证明其支持本文接口。
> 交付状态见[集成提案](https://github.com/hugegraph/hugegraph/pull/264)。

## 确认哪个进程持有数据库

| 部署方式 | 加载 Topling JNI 的进程 | 运行时配置 |
|---|---|---|
| 单机 RocksDB Server | Server | `conf/graphs/hugegraph.properties` 中的 `rocksdb.provider=topling` |
| HStore PD | 每个 PD | `conf/application.yml` 中 `rocksdb` 下的 `provider: topling` |
| HStore Store | 每个 Store | `conf/application-pd.yml` 中 `rocksdb` 下的 `provider: topling` |
| 使用 HStore 的 Server | 无 | 不配置本地 Topling 运行时 |

PD 和 Store 分别选择自己的运行时。使用 HStore 的 Server 是远程客户端，不需要 Topling JAR 或原生库。
运行时在进程启动时选定。同一 Server 进程中的所有本地 RocksDB 图必须使用相同的运行时。

历史文档中的 `rocksdb.option_path` 和 `rocksdb.open_http` 示例属于另一套集成方式。
不要将这些配置复制到本文的开发接口；组件启动脚本负责选择 Easy Migrate YAML 文件。

## 构建可选发行包

在 Linux x86_64 上构建，需要 Java 11+、Maven 3.5+、`rsync`、`unzip` 和 `tar`。
Server 挂载预检查还要求 `PATH` 中有 util-linux 2.37+ 的 `mountpoint`。
此集成不支持在 macOS 原生运行；macOS 用户应使用 Linux x86_64 容器。

从生产方获取兼容的 Topling Easy Migrate JNI JAR，以及对应源码版本、依赖许可证、声明文件和可信 SHA-256。
HugeGraph 源码不包含该二进制文件。校验和只能识别产物，不能证明来源、许可证或运行时兼容性。
分发衍生包或镜像前，核查再分发权限并保留所需许可证和声明文件。

在包含此功能的完整源码目录中执行：

```bash
VERSION=$(mvn help:evaluate -Dexpression=project.version -q -DforceStdout)
mvn clean package \
  -pl hugegraph-server/hugegraph-dist,hugegraph-pd/hg-pd-dist,hugegraph-store/hg-store-dist \
  -am -Dmaven.test.skip=true -Dmaven.javadoc.skip=true -ntp

export TOPLING_JNI_JAR=/absolute/path/to/rocksdbjni-topling.jar
export TOPLING_JNI_SHA256='<trusted 64-character SHA-256>'
install-dist/scripts/build-topling-distribution.sh server "$VERSION"
# 仅在运行 HStore 时生成以下两个组件：
install-dist/scripts/build-topling-distribution.sh pd "$VERSION"
install-dist/scripts/build-topling-distribution.sh store "$VERSION"
```

构建命令先生成标准发行包。生成脚本在其旁边创建独立的 `-topling` 目录及压缩包。
脚本将外部 JAR 复制到私有暂存目录，校验该副本后再准备原生库。
缺少输入、校验和不一致或 JAR 结构不符合要求时，生成过程会停止；脚本不会搜索 Maven 缓存或下载替代文件。
构建成功不等于原生运行时验收通过。

每个 Topling 包包含 `lib/topling/rocksdbjni-topling.jar`、`lib/topling/runtime.properties`、
`library/librocksdbjni-linux64.so` 以及组件的准备和预加载脚本。
更换已安装的 Topling JAR 后，重新运行 `bin/prepare-topling.sh`。

构建容器时，使用同一源码中的 `docker/README.md` 和 `docker/bake.hcl`，并传入相同的外部 JNI 参数。
先在本地完成构建，再使用示例中的 `topling` 标签，本地部署选择 `pull_policy: never`。
使用镜像仓库中的产物前，先核对源码版本、JNI 身份和镜像摘要。标签或容器健康状态本身不能证明实际运行的 JNI。

## 配置独立数据目录

切换运行时不会迁移或转换数据。为 Topling 设置独立目录，保留标准 RocksDB 目录不变。
各组件使用以下配置：

| 组件 | 数据配置 | Topling 根目录示例 |
|---|---|---|
| Server | `rocksdb.data_path` | `/srv/hugegraph/topling/server` |
| PD | `pd.data-path` | `/srv/hugegraph/topling/pd` |
| Store | `app.data-path` | `/srv/hugegraph/topling/store` |

单机 Server 修改生成包中的 `conf/graphs/hugegraph.properties`：

```properties
backend=rocksdb
rocksdb.provider=topling
rocksdb.data_path=/srv/hugegraph/topling/server
```

启动前，挂载或创建实际的 Topling 根目录，不要使用包含符号链接的路径。
挂载父数据根目录，不要单独挂载 `data/g` 等数据库目录，确保所有遵循恢复协议的进程都能看到同级恢复文件。
单机 Server 启动脚本在 Java 启动前拒绝单独挂载的数据库目录，包括 Linux 上同一文件系统的绑定挂载。
启动和恢复期间保持挂载布局不变。

`.hugegraph-rocksdb-provider` 标记用于防止误用目录，不负责数据转换。
标记冲突时停止启动。Topling 也会拒绝没有标记的非空数据目录。
标准 RocksDB 为兼容历史数据而接受已有的无标记目录，但这不意味着可以打开经 Topling 修改的目录。

## 启动、核验和关闭

在单机 Topling 发行包目录中执行：

```bash
bin/init-store.sh
bin/start-hugegraph.sh
curl --fail http://127.0.0.1:8080/versions
# 使用结束后正常关闭：
bin/stop-hugegraph.sh
```

HStore 部署先配置正常的网络地址，再依次启动 PD、Store 和使用 HStore 的 Server。
在各自的发行包目录中使用 `bin/start-hugegraph-pd.sh`、`bin/start-hugegraph-store.sh` 和 `bin/start-hugegraph.sh`。

启动脚本输出 `TOPLINGDB_EASY_MIGRATE_CONF`。核对它指向相应组件的配置文件：

| 组件 | Easy Migrate YAML | 监控绑定地址 |
|---|---|---|
| Server | `conf/toplingdb.yaml` | `127.0.0.1:2011` |
| PD | `conf/rocksdb_pd.yaml` | `127.0.0.1:2012` |
| Store | `conf/rocksdb_store.yaml` | `127.0.0.1:2013` |

示例文件设置 `http.auto_start_http: false`。监控接口没有身份认证，启用时应保留回环地址绑定。
不要使用旧的 `rocksdb.open_http` 开关。

验收部署前，将实际加载的 RocksDB Java 类所属 JAR、进程唯一选中的 JNI、映射的原生库及其 SHA-256 与准备的产物核对。
随后验证 schema 和数据操作、重启后持久化、正常关闭，以及错误运行时或冲突数据目录的拒绝行为。
启动日志、运行时变量和 `/versions` 可用于检查，但不能单独证明正在使用真实 Topling 运行时。

应用仍需主动结束事务。请求清理会释放线程本地事务，但不会提交未完成的工作。
计划关闭时，停止新写入并核对进行中请求的结果；取消操作可能使请求失败。
Store 等待回调和工作线程结束后再关闭数据库。关闭脚本超时时返回失败并保留 PID 文件。
先检查日志和线程转储，不要在工作线程仍运行时强行再次关闭数据库。

## 恢复中断的单机快照恢复操作

此协议适用于本地 RocksDB 适配器的快照恢复，不提供全图原子恢复或 HStore 多分区恢复协议。
替换数据前，恢复过程在同级 `<data-path>.resume-pending` 文件中记录检查点和 WAL 位置。
后续开库会在原生恢复前重试中断的安装。
检查点缺失、元数据不完整或 WAL 配置改变时，开库会停止。

保留检查点、待恢复标记和配置路径。修复访问权限或释放空间后，使用相同运行时和配置重试正常启动。
不要删除待恢复标记或 `<data-path>.resume-lock` 来强行启动。
操作系统锁一直持有到数据库关闭；磁盘上的锁文件本身不能证明存在活跃持有者。
旧程序和其他写入方不遵循此协议，不得并发访问相同目录。

独立 WAL、数据目录内的 WAL，以及 WAL 根目录内的数据目录，都采用原地替换日志的方式。重试时保留 WAL 符号链接配置。
原生开库成功后清除待恢复标记，再尝试清理检查点。
操作中断测试不能证明断电持久性。

## 升级或回到标准 RocksDB

升级标准 RocksDB 依赖前，验证由旧运行时创建的数据。
新建数据库并重启不能证明旧数据兼容性。

从 Topling 回到标准 RocksDB 时，先停止写入并正常关闭组件，保留 Topling 数据，
再使用兼容的标准运行时，将完整的 Topling 切换前备份恢复到一个新的空目录。
恢复服务前验证 schema、读写和重启。不要让标准 RocksDB 打开经 Topling 修改的目录。
