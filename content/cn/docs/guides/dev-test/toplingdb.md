---
title: "ToplingDB 开发版集成"
linkTitle: "ToplingDB (开发版)"
weight: 2
description: "从开发源码构建可选 ToplingDB 运行时，隔离数据目录，并了解启动与恢复边界。"
aliases:
  - /docs/guides/toplingdb/
---

> **开发版接口**：本文适用于开启可选 ToplingDB 运行时的开发构建版本。
> 已有发行版和镜像标签不代表支持本文接口，采用前须完成运行时验证。

## 确认数据库所属组件

HugeGraph 默认使用标准 RocksDB。对持有本地存储的每个进程分别启用 Topling：

| 组件 | 业务 provider 配置 | 启动命令 |
| --- | --- | --- |
| 独立 RocksDB Server | 每个选用的 graph properties 文件中设置 `rocksdb.provider=topling` | `bin/start-hugegraph.sh` |
| PD | `conf/application.yml` 的 `rocksdb` 下设置 `provider: topling` | `bin/start-hugegraph-pd.sh` |
| Store | `conf/application-pd.yml` 的 `rocksdb` 下设置 `provider: topling` | `bin/start-hugegraph-store.sh` |

独立 Server 保持 `backend=rocksdb`；HStore Server 使用 `backend=hstore`，不需要本地 Topling 运行时。
同一 Server 进程中的本地 RocksDB 图必须使用相同 provider。业务配置必须与启动脚本选择的运行时一致。

## 构建并准备标准发行包

在源码仓库根目录，使用 Java 17 和 Maven 3.6.3 或更新版本构建普通发行包：

```bash
mvn clean package -Dmaven.test.skip=true -Dmaven.javadoc.skip=true
```

从可信制品渠道取得 Topling Easy Migrate JNI JAR 及其 SHA-256。准备环境需要 Java 17 JDK、Linux x86_64、`sha256sum`、`unzip`、`od`、`ldd` 和 GNU `mv`。
还须满足所选 JAR 的 native 依赖，包括其要求的 glibc 和 libaio。

先停止组件，解压一份新的标准发行包，再从该组件目录执行：

```bash
export TOPLING_JNI_JAR=/absolute/path/to/rocksdbjni-topling.jar
export TOPLING_JNI_SHA256='<trusted-64-character-sha256>'
bash bin/prepare-topling.sh
```

脚本校验复制后的 JAR 哈希、Topling Java 标识、唯一的 Linux x86_64 JNI 条目、ELF 架构及 native 依赖。
安装前还会用所选 JNI 打开临时数据库，确认 EasyMigrate 配置实际改变了持久化的写缓冲区大小；类标识和哈希匹配但不支持该配置入口的构建会被拒绝。
包含配置验证修复的构建还会在发布运行时前，以 native 导入检查实际配置。
设置 `TOPLINGDB_EASY_MIGRATE_CONF` 时探测指定文件，否则使用组件的 `conf/toplingdb.yaml`。
缺少插件会在准备阶段失败，避免准备成功后才在 Server 初始化阶段崩溃。
此导入不会按生产 WAL 或日志路径打开数据库。
若显式指定配置，启动组件时也要保留相同的环境变量。
准备与运行时选择都会在启动器切换目录前，按调用方工作目录将相对路径转为绝对路径。
两个步骤应使用同一文件，服务配置优先采用绝对路径以免歧义。
导入检查针对准备时的实际文件；之后更换文件仍可能引入不支持的插件。
重启组件前，应使用所选 JNI 验证替换后的配置。
这些探针不代表已有数据兼容性或所有生产列族均已验证。
校验记录绑定已测试的 JAR 和 native 库，启动时拒绝缺失或失效的记录；从旧准备脚本升级时请重新准备一份新发行包。
默认/标准模式启动时会拒绝继承的 RocksDB JNI 预载库，Topling 模式则拒绝与所选 JNI 竞争的预载库；其他预载库继续保留。
它将 `topling/rocksdbjni.jar`、对应 native 库和可选网页资源放在 `lib` 之外。已有 `topling` 目录时会拒绝准备；更换运行时请使用另一份已停止的新发行包。
按实际部署需要，为 Server、PD 和 Store 分别执行准备步骤。

## 将持久数据放在发行包之外

更换 provider 不会转换已有数据库。为 Topling 使用独立、初始为空的目录，并保留标准 provider 的数据。
预先创建服务账号可写的持久目录，将其放在源码检出、构建输出和解压后的发行包目录之外。注意：每个图必须使用互不相同的独立数据与 WAL 目录，避免目录冲突：

| 组件 | 配置文件及配置项 | 持久路径示例 |
| --- | --- | --- |
| Server 数据 | Graph properties：`rocksdb.data_path` | `/srv/hugegraph/topling/server/<graph>/data` |
| Server WAL | Graph properties：`rocksdb.wal_path` | `/srv/hugegraph/topling/server/<graph>/wal` |
| PD | `conf/application.yml`：`pd.data-path` | `/srv/hugegraph/topling/pd` |
| Store 数据 | `conf/application.yml`：`app.data-path` | `/srv/hugegraph/topling/store/data` |
| Store Raft | `conf/application.yml`：`app.raft-path` | `/srv/hugegraph/topling/store/raft` |

独立 Server 的每个选用图配置都需修改，例如 `conf/graphs/hugegraph.properties`（若配置多个图，请将路径中的 `hugegraph` 替换为对应图名）：

```properties
backend=rocksdb
rocksdb.provider=topling
rocksdb.data_path=/srv/hugegraph/topling/server/hugegraph/data
rocksdb.wal_path=/srv/hugegraph/topling/server/hugegraph/wal
```

Server 的数据和 WAL 路径**都要设置**，且不同图之间不能共享同一路径。若 WAL 仍使用发行包内的默认路径，重新构建或替换发行包时可能丢失该目录。
运行时或发行包更新时，保留外部数据、WAL 和 Raft 根目录。

PD 和 Store 应在上表对应的 provider 配置文件中修改已有 `rocksdb` 映射，保留其余选项：

```yaml
rocksdb:
  provider: topling
```

持久路径另在 `conf/application.yml` 中配置，同时保留正常的网络地址和集群配置。

准备完成后的 runtime 目录权限为 0755，普通资源文件为 0644，因此使用另一个服务账号也能读取 JNI。该账号还需要组件上级目录的遍历权限；prepare 不会修改上级目录权限。

## 选择运行时并启动验证

在每个持有 Topling 数据库的组件启动终端中，显式选择运行时：

```bash
export TOPLINGDB_ROCKSDB_PROVIDER=topling
# 执行第一张表中该组件对应的启动命令。
```

启动脚本默认使用该组件的 `conf/toplingdb.yaml`，也可用 `TOPLINGDB_EASY_MIGRATE_CONF=/absolute/path/config.yaml` 显式覆盖。
发行包中的 native 配置关闭 HTTP 服务，并保留 Java 写入路径要求的 `memtable_as_log_index=false`。
请按机器条件调整该文件；它与业务 provider、数据目录配置分别生效。

自 Server 1.8.0+（master）起，发行包中的 `conf/toplingdb.yaml` 默认预设基于社区通用 JNI 的 SkipList 内存表与 BlockBasedTable 文件配置，不再依赖 CSPP、CSPPMemTabTable 或 DispatcherTable 插件。
而现有及历史正式发行版本（如 1.7.0）附带的 `conf/toplingdb.yaml` 仍默认配置 `cspp` 内存表与 `DispatcherTable`。
在旧版本上使用缺少 CSPP 插件的社区版 JNI 创建**全新空数据库**时，可将 `conf/toplingdb.yaml` 调整为 SkipList 和 BlockBasedTable，以防止初始化失败。

缓存与写缓冲区参数是单项 native 预算；实际内存还随数据库和列族数量增长。
请检查部署包中的实际配置。自定义 native 配置需要所选 JNI 提供对应插件。
更改默认配置不会转换已有 SST 文件；其他表格式写入的数据仍需要兼容的 reader。

升级已有 CSPP 部署前，先停止组件并保留匹配的 JNI、之前调优的配置与可恢复的数据备份。
包含兼容配置修复的 Server、PD、Store 发行包会提供 `conf/toplingdb-legacy-cspp.yaml`，完整保留旧配置。
准备和启动时，通过绝对路径 `TOPLINGDB_EASY_MIGRATE_CONF` 选择该文件或部署原有的配置。
用于验证的社区 JNI 缺少 CSPP reader；旧 CSPP SST 的兼容性仍需要匹配 JNI 与真实旧格式数据验证。
不能用社区配置替换已有 CSPP 部署的 native 设置。

新默认值还调整了资源参数：缓存 8 GiB → 64 MiB、写缓冲 128 MiB → 16 MiB、最多缓冲数 6 → 3、后台任务 8 → 2。
部分原有压缩整理调优也已移除。这些变化可能影响性能，不是透明的格式迁移。
实测社区 JNI 中，Java 先设置 128 MiB 与六个缓冲，EasyMigrate 在打开数据库时实际应用 16 MiB、三个缓冲及 64 MiB 缓存。
其他 JNI 构建应检查持久化 OPTIONS 与 `rocksdb.block-cache-capacity`，不能仅凭打开前的 Java getter 判断最终 native 值。

标准 Server 容器包含 Java 17 JDK；包含准备工具修复的构建还提供 `unzip`。
该镜像不捆绑或下载可选 JNI，制品的 glibc、libaio 与 CPU 要求仍须匹配基础镜像或宿主机。
单机与 HStore 镜像的区别见 [Server 部署指南](/cn/docs/quickstart/hugegraph/hugegraph-server/)。

Linux 上可在启动后检查单机 Server 实际映射的 JNI：

```bash
# 在 Server 发行包目录中，以服务账号执行。
server_pid=$(cat bin/pid)
grep -F 'topling/librocksdbjni-linux64.so' "/proc/$server_pid/maps"
```

API 请求成功本身不能证明选择了 Topling。
应同时检查实际映射库与真实图写入、读取结果；这些运行态检查与 Helm 变体渲染测试分别验收。

独立 Server 使用全新图时，首次启动前先初始化一次存储：

```bash
bash bin/init-store.sh
bash bin/start-hugegraph.sh
```

`bin/init-store.sh`、`bin/dump-store.sh` 与 `bin/start-hugegraph.sh` 使用同一显式运行时选择。
HStore 按 PD、Store、Server 的顺序启动。在同一 shell 中启动 HStore Server 前，执行 `unset TOPLINGDB_ROCKSDB_PROVIDER`
（或 `export TOPLINGDB_ROCKSDB_PROVIDER=rocksdb`）；不要在该 Server 上启用本地 Topling。
业务 provider 与实际运行时不一致时，组件会在开库前拒绝启动。

采用前须确认实际 RocksDB Java 类和进程加载的 JNI 库来自准备好的运行时。在专用数据目录中验证真实写入、读取、正常停止和重启；
HStore 还需通过 Server 执行图操作，覆盖 PD 和 Store 链路。仅构建成功、启动成功或通过标准 JNI 单元测试，不能证明 Topling 运行时已验收。

## 停止或切回标准 RocksDB

先停止新业务，再使用正常停止脚本。HStore 依次执行 Server 的 `bin/stop-hugegraph.sh`、Store 的 `bin/stop-hugegraph-store.sh`、
PD 的 `bin/stop-hugegraph-pd.sh`，等待前一个进程退出后再停止其依赖。强制终止进程不能作为正常 native 资源清理的证明。

切回标准 RocksDB 前先停止组件，取消 `TOPLINGDB_ROCKSDB_PROVIDER`，并把业务 provider 改回 `rocksdb`。
使用对应的标准 provider 数据和 WAL 路径，不要指向已被 Topling 修改的数据库。

专用 Topling 发行包、Docker/Compose 打包、通用生命周期改造及可重试快照恢复分别后续交付。
本文覆盖普通发行包的启动脚本；自定义 IDE 和嵌入式入口需要自行准备运行时并完成验证。
