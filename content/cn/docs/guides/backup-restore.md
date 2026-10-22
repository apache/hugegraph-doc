---
title: "备份与恢复"
linkTitle: "备份 & 恢复"
weight: 5
---

## 描述

Backup 将一张图的 Schema、顶点和边导出为 JSON 数据，Restore 将这些数据导入目标图。
它们是 [HugeGraph-Tools](/cn/docs/quickstart/toolchain/hugegraph-tools) 的命令，适合图迁移、升级后的恢复及图合并。

#### Backup

备份可在任意图模式下执行。导出前暂停源图写入，让 Schema、顶点和边保持一致；分批读取 API 不提供跨整个备份过程的事务快照。
`backup -t all` 只覆盖图的 Schema 和图数据，不包含部署配置与用户权限备份。

#### Restore

先按目标图状态选择恢复模式。日常读写使用 `NONE`，`LOADING` 不能用于 `restore`。

| 目标 | 模式 | Schema ID | 顶点和边 ID |
|---|---|---|---|
| 恢复到没有 Schema 和数据的新图 | `RESTORING` | 使用备份中的 ID | 使用备份中的 ID |
| 合并到已有图 | `MERGING` | 使用目标图的 Schema ID，必要时新建 | 部分 ID 随目标 Schema 重算，见下文 |

`MERGING` 中，`PRIMARY_KEY` 顶点 ID 按目标 label ID 重新生成，关联边的端点与 ID 随之调整。
`AUTOMATIC` 和自定义顶点 ID 保留。合并会复用同名 Schema，先检查双方的定义是否兼容，以及保留的顶点 ID 是否冲突。
它不提供任意 Schema 冲突或数据冲突的自动解决策略。先在独立目标图验证，再合并正式数据。

## 使用方法

准备与 Server 版本匹配的 [HugeGraph-Tools](/cn/docs/quickstart/toolchain/hugegraph-tools)，在 Tools 根目录执行以下命令。
本例从 `8080` 的源图恢复到 `8081` 的空目标图。两个 Server 和目标图应已创建并启动；可将变量改成实际地址及图名。

```bash
SOURCE_URL=http://127.0.0.1:8080
TARGET_URL=http://127.0.0.1:8081
SOURCE_GRAPH=hugegraph
TARGET_GRAPH=hugegraph
BACKUP_DIR="$PWD/data/hugegraph-backup"
```

启用认证时，在每条 Tools 命令的子命令前加入 `--user <user> --password <password>`，并使用具备对应图读写和模式管理权限的账号。
详细参数及凭据使用方式见 [Tools 参考](/cn/docs/quickstart/toolchain/hugegraph-tools)。

#### Backup

暂停源图写入后，备份全部 Schema、顶点和边。

```bash
bin/hugegraph --url "$SOURCE_URL" --graph "$SOURCE_GRAPH" \
  backup -t all -d "$BACKUP_DIR"
```

显式指定的 `-d` 就是备份目录，不会自动附加图名。为每次备份使用独立目录，避免混入旧文件。
保留完整目录，包括压缩文件；Restore 可读取 Tools 支持的 JSON 备份格式。

#### Restore

以下流程使用 `RESTORING`。合并时改为 `MERGING`，并先完成上面的兼容性检查。
操作期间暂停目标图业务写入。


1. <span id="步骤1查看并设置图模式"></span>**查看并记录原模式，再切换。**

   ```bash
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" graph-mode-get
   ORIGINAL_MODE=NONE
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" \
     graph-mode-set -m RESTORING
   ```

   正常业务图应处于 `NONE`。将查询返回的值填入 `ORIGINAL_MODE`，例如下方的 `NONE`。若另一项维护正在使用 `RESTORING`、`MERGING` 或 `LOADING`，先协调该任务，不要覆盖其模式。

1. <span id="步骤2restore-数据"></span>**恢复数据。**

   ```bash
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" \
     restore -t all -d "$BACKUP_DIR"
   ```

   检查命令是否成功结束及各类型的恢复结果。发生错误时保留备份目录与日志，先检查目标图的部分写入状态。
   Restore 不会回滚已经写入的数据，也不会自动恢复图模式；不要对部分恢复的图盲目重跑。

1. <span id="步骤3恢复图模式"></span>**还原原模式。**

   使用第一步记录的 `ORIGINAL_MODE` 还原模式。

   ```bash
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" graph-mode-set -m "$ORIGINAL_MODE"
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" graph-mode-get
   ```

   无论 Restore 成功还是失败，都要处理图模式。失败时先保留现场，完成模式还原后仍暂停业务写入，待检查或重新准备目标图后再恢复业务。
{.steps}

还原模式后，对比两端的顶点数和边数。

```bash
bin/hugegraph --url "$SOURCE_URL" --graph "$SOURCE_GRAPH" gremlin-execute --script 'g.V().count()'
bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" gremlin-execute --script 'g.V().count()'
bin/hugegraph --url "$SOURCE_URL" --graph "$SOURCE_GRAPH" gremlin-execute --script 'g.E().count()'
bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" gremlin-execute --script 'g.E().count()'
```

两组计数应分别相同。再通过 [Schema API](/cn/docs/clients/restful-api/schema/) 核对属性、顶点类型、边类型和索引，
并抽查业务属性与边的两端。`RESTORING` 还应核对原 ID；`MERGING` 按上表检查 ID 变化。
仅有计数相同不足以证明业务数据完整。

#### 帮助

压缩、并发、日志及分类型备份参数见 [Tools 参考](/cn/docs/quickstart/toolchain/hugegraph-tools)。
恢复前先在目标版本试验备份文件的兼容性，不能仅凭命令名相同推断跨版本可直接恢复。

## Backup/Restore使用和实现的API说明

#### Backup

Backup 使用 Schema、顶点和边的列表 GET API 导出数据。

#### Restore

Restore 使用 Schema、顶点和边的创建 API 导入数据。模式对应的 ID 行为见[前面的选择表](#restore)。
`RESTORING` 允许指定 Schema ID；`MERGING` 不允许指定 Schema ID。两种模式均允许保留 `AUTOMATIC` 顶点 ID。
普通 `NONE` 模式不接受这些恢复操作所需的 ID 设置。

##### 查看某个图的模式

启用鉴权时需要图读取权限（`space_member` 或该图的所有者）。

###### Method & Url

```text
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/mode
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "mode": "NONE"
}
```

合法图模式为 `NONE`、`RESTORING`、`MERGING` 和 `LOADING`。

##### 设置某个图的模式

启用鉴权时需要图空间管理权限（`space`）；管理员可按权限继承规则满足。

###### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/mode
```

###### Request Body

```text
"RESTORING"
```

合法图模式为 `NONE`、`RESTORING`、`MERGING` 和 `LOADING`。

###### Response Status

```json
200
```

###### Response Body

```json
{
    "mode": "RESTORING"
}
```
