---
title: "Backup Restore"
linkTitle: "备份 & 恢复"
weight: 5
---

## 描述

Backup 和 Restore 是备份图和恢复图的功能。备份和恢复的数据包括元数据（schema）和图数据（vertex 和 edge）。

#### Backup

将 HugeGraph 系统中的一张图的元数据和图数据以 JSON 格式导出。

#### Restore

将 Backup 导出的JSON格式的数据，重新导入到 HugeGraph 系统中的一个图中。

Restore 有两种模式：

- Restoring 模式，将 Backup 导出的元数据和图数据原封不动的恢复到 HugeGraph 系统中。可用于图的备份和恢复，一般目标图是新图（没有元数据和图数据）。比如：
    - 系统升级，先备份图，然后升级系统，最后将图恢复到新的系统中
    - 图迁移，从一个 HugeGraph 系统中，使用 Backup 功能将图导出，然后使用 Restore 功能将图导入另一个 HugeGraph 系统中
- Merging 模式，将 Backup 导出的元数据和图数据导入到另一个已经存在元数据或者图数据的图中，过程中元数据的 ID 可能发生改变，顶点和边的 ID 也会发生相应变化。
    - 可用于合并图

## 使用方法

可以使用[hugegraph-tools](/cn/docs/quickstart/toolchain/hugegraph-tools)进行图的备份和恢复。

#### Backup

```bash
bin/hugegraph backup -t all -d data
```

该命令将 http://127.0.0.1 的 hugegraph 图的全部元数据和图数据备份到data目录下。

> Backup 在三种图模式下都可以正常工作

#### Restore

Restore 有两种模式： RESTORING 和 MERGING，备份之前首先要根据需要设置图模式。

##### 步骤1：查看并设置图模式

```bash
bin/hugegraph graph-mode-get
```
该命令用于查看当前图模式，包括：NONE、RESTORING、MERGING。

```bash
bin/hugegraph graph-mode-set -m RESTORING
```
该命令用于设置图模式，Restore 之前可以设置成 RESTORING 或者 MERGING 模式，例子中设置成 RESTORING。

##### 步骤2：Restore 数据

```bash
bin/hugegraph restore -t all -d data
```
该命令将data目录下的全部元数据和图数据重新导入到 http://127.0.0.1 的 hugegraph 图中。

##### 步骤3：恢复图模式

```bash
bin/hugegraph graph-mode-set -m NONE
```
该命令用于恢复图模式为 NONE。

至此，一次完整的图备份和图恢复流程结束。

#### 帮助

备份和恢复命令的详细使用方式可以参考[hugegraph-tools文档](/cn/docs/quickstart/toolchain/hugegraph-tools)。

## Backup/Restore使用和实现的API说明

#### Backup

Backup 使用`元数据`和`图数据`的相应的 list(GET) API 导出，并未增加新的 API。

#### Restore

Restore 使用`元数据`和`图数据`的相应的 create(POST) API 导入，并未增加新的 API。

Restore 时存在两种不同的模式： Restoring 和 Merging，另外，还有常规模式 NONE(默认)，区别如下：

- None 模式，元数据和图数据的写入属于正常状态，可参见功能说明。特别的：
    - 元数据（schema）创建时不允许指定 ID
    - 图数据（vertex）在 id strategy 为 Automatic 时，不允许指定 ID
- Restoring 模式，恢复到一个新图中，特别的：
    - 元数据（schema）创建时允许指定 ID
    - 图数据（vertex）在 id strategy 为 Automatic 时，允许指定 ID
- Merging 模式，合并到一个已存在元数据和图数据的图中，特别的：
    - 元数据（schema）创建时不允许指定 ID
    - 图数据（vertex）在 id strategy 为 Automatic 时，允许指定 ID

正常情况下，图模式为 None，当需要 Restore 图时，需要根据需要临时修改图模式为 Restoring 模式或者 Merging 模式，并在完成 Restore 时，恢复图模式为 None。

实现的设置图模式的 RESTful API 如下：

##### 查看某个图的模式. **该操作需要管理员权限**

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/mode
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

> 合法的图模式包括：NONE，RESTORING，MERGING

##### 设置某个图的模式. **该操作需要管理员权限**

###### Method & Url

```
PUT http://localhost:8080/graphs/{graph}/mode
```

###### Request Body

```
"RESTORING"
```

> 合法的图模式包括：NONE，RESTORING，MERGING

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
