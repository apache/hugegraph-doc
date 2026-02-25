---
title: "HugeGraph-Tools Quick Start"
linkTitle: "使用 HugeGraph-Tools 导出/管理图"
weight: 3
---

### 1 HugeGraph-Tools概述

HugeGraph-Tools 是 HugeGraph 的自动化部署、管理和备份/还原组件。

> **测试指南**：如需在本地运行 Tools 测试，请参考 [工具链本地测试指南](/cn/docs/guides/toolchain-local-test)

### 2 获取 HugeGraph-Tools

有两种方式可以获取 HugeGraph-Tools：(它被包含子 Toolchain 中)

- 下载二进制tar包
- 下载源码编译安装

#### 2.1 下载二进制tar包

下载最新版本的 HugeGraph-Toolchain 包, 然后进入 tools 子目录

```bash
wget https://downloads.apache.org/hugegraph/1.0.0/apache-hugegraph-toolchain-incubating-1.0.0.tar.gz
tar zxf *hugegraph*.tar.gz
```

#### 2.2 下载源码编译安装
源码编译前请确保安装了wget命令

下载最新版本的 HugeGraph-Toolchain 源码包, 然后根目录编译或者单独编译 tool 子模块：

```bash
# 1. get from github
git clone https://github.com/apache/hugegraph-toolchain.git

# 2. get from direct  (e.g. here is 1.0.0, please choose the latest version)
wget https://downloads.apache.org/hugegraph/1.0.0/apache-hugegraph-toolchain-incubating-1.0.0-src.tar.gz
```

编译生成 tar 包:

```bash
cd hugegraph-tools
mvn package -DskipTests
```

生成 tar 包 hugegraph-tools-${version}.tar.gz


### 3 使用

#### 3.1 功能概览

解压后，进入 hugegraph-tools 目录，可以使用`bin/hugegraph`或者`bin/hugegraph help`来查看 usage 信息。主要分为：

- 图管理类，graph-mode-set、graph-mode-get、graph-list、graph-get、graph-clear、graph-create、graph-clone 和 graph-drop
- 异步任务管理类，task-list、task-get、task-delete、task-cancel 和 task-clear
- Gremlin类，gremlin-execute 和 gremlin-schedule
- 备份/恢复类，backup、restore、migrate、schedule-backup 和 dump
- 认证数据备份/恢复类，auth-backup 和 auth-restore
- 安装部署类，deploy、clear、start-all 和 stop-all

```bash
Usage: hugegraph [options] [command] [command options]
```

##### 3.2 [options]-全局变量

`options`是 HugeGraph-Tools 的全局变量，可以在 hugegraph-tools/bin/hugegraph 中配置,包括：

- --graph，HugeGraph-Tools 操作的图的名字，默认值是 hugegraph
- --url，HugeGraph-Server 的服务地址，默认是 http://127.0.0.1:8080
- --user，当 HugeGraph-Server 开启认证时，传递用户名
- --password，当 HugeGraph-Server 开启认证时，传递用户的密码
- --timeout，连接 HugeGraph-Server 时的超时时间，默认是 30s
- --trust-store-file，证书文件的路径，当 --url 使用 https 时，HugeGraph-Client 使用的 truststore 文件，默认为空，代表使用 hugegraph-tools 内置的 truststore 文件 conf/hugegraph.truststore
- --trust-store-password，证书文件的密码，当 --url 使用 https 时，HugeGraph-Client 使用的 truststore 的密码，默认为空，代表使用 hugegraph-tools 内置的 truststore 文件的密码

上述全局变量，也可以通过环境变量来设置。一种方式是在命令行使用 export 设置临时环境变量，在该命令行关闭之前均有效


| 全局变量                   | 环境变量                           | 示例                                                 |
|------------------------|--------------------------------|----------------------------------------------------|
| --url                  | HUGEGRAPH_URL                  | export HUGEGRAPH_URL=http://127.0.0.1:8080         |
| --graph                | HUGEGRAPH_GRAPH                | export HUGEGRAPH_GRAPH=hugegraph                   |
| --user                 | HUGEGRAPH_USERNAME             | export HUGEGRAPH_USERNAME=admin                    |
| --password             | HUGEGRAPH_PASSWORD             | export HUGEGRAPH_PASSWORD=test                     |
| --timeout              | HUGEGRAPH_TIMEOUT              | export HUGEGRAPH_TIMEOUT=30                        |
| --trust-store-file     | HUGEGRAPH_TRUST_STORE_FILE     | export HUGEGRAPH_TRUST_STORE_FILE=/tmp/trust-store |
| --trust-store-password | HUGEGRAPH_TRUST_STORE_PASSWORD | export HUGEGRAPH_TRUST_STORE_PASSWORD=xxxx         |

另一种方式是在 bin/hugegraph 脚本中设置环境变量：

```
#!/bin/bash

# Set environment here if needed
#export HUGEGRAPH_URL=
#export HUGEGRAPH_GRAPH=
#export HUGEGRAPH_USERNAME=
#export HUGEGRAPH_PASSWORD=
#export HUGEGRAPH_TIMEOUT=
#export HUGEGRAPH_TRUST_STORE_FILE=
#export HUGEGRAPH_TRUST_STORE_PASSWORD=
```

##### 3.3 图管理类，graph-mode-set、graph-mode-get、graph-list、graph-get、graph-clear、graph-create、graph-clone和graph-drop

- graph-mode-set，设置图的 restore mode
    - --graph-mode 或者 -m，必填项，指定将要设置的模式，合法值包括 [NONE, RESTORING, MERGING, LOADING]
- graph-mode-get，获取图的 restore mode
- graph-list，列出某个 HugeGraph-Server 中全部的图
- graph-get，获取某个图及其存储后端类型
- graph-clear，清除某个图的全部 schema 和 data
    - --confirm-message 或者 -c，必填项，删除确认信息，需要手动输入，二次确认防止误删，"I'm sure to delete all data"，包括双引号
- graph-create，使用配置文件创建新图
    - --name 或者 -n，选填项，新图的名称，默认为 hugegraph
    - --file 或者 -f，必填项，图配置文件的路径
- graph-clone，克隆已存在的图
    - --name 或者 -n，选填项，新克隆图的名称，默认为 hugegraph
    - --clone-graph-name，选填项，要克隆的源图名称，默认为 hugegraph
- graph-drop，删除图（不同于 graph-clear，这会完全删除图）
    - --confirm-message 或者 -c，必填项，确认消息 "I'm sure to drop the graph"，包括双引号

> 当需要把备份的图原样恢复到一个新的图中的时候，需要先将图模式设置为 RESTORING 模式；当需要将备份的图合并到已存在的图中时，需要先将图模式设置为 MERGING 模式。

##### 3.4 异步任务管理类，task-list、task-get和task-delete

- task-list，列出某个图中的异步任务，可以根据任务的状态过滤
    - --status，选填项，指定要查看的任务的状态，即按状态过滤任务
    - --limit，选填项，指定要获取的任务的数目，默认为 -1，意思为获取全部符合条件的任务
- task-get，获取某个异步任务的详细信息
    - --task-id，必填项，指定异步任务的 ID
- task-delete，删除某个异步任务的信息
    - --task-id，必填项，指定异步任务的 ID
- task-cancel，取消某个异步任务的执行
    - --task-id，要取消的异步任务的 ID
- task-clear，清理完成的异步任务
    - --force，选填项，设置时，表示清理全部异步任务，未执行完成的先取消，然后清除所有异步任务。默认只清理已完成的异步任务

##### 3.5 Gremlin类，gremlin-execute和gremlin-schedule

- gremlin-execute，发送 Gremlin 语句到 HugeGraph-Server 来执行查询或修改操作，同步执行，结束后返回结果
    - --file 或者 -f，指定要执行的脚本文件，UTF-8编码，与 --script 互斥
    - --script 或者 -s，指定要执行的脚本字符串，与 --file 互斥
    - --aliases 或者 -a，Gremlin 别名设置，格式为：key1=value1,key2=value2,...
    - --bindings 或者 -b，Gremlin 绑定设置，格式为：key1=value1,key2=value2,...
    - --language 或者 -l，Gremlin 脚本的语言，默认为 gremlin-groovy
    > --file 和 --script 二者互斥，必须设置其中之一
- gremlin-schedule，发送 Gremlin 语句到 HugeGraph-Server 来执行查询或修改操作，异步执行，任务提交后立刻返回异步任务id
    - --file 或者 -f，指定要执行的脚本文件，UTF-8编码，与 --script 互斥
    - --script 或者 -s，指定要执行的脚本字符串，与 --file 互斥
    - --bindings 或者 -b，Gremlin 绑定设置，格式为：key1=value1,key2=value2,...
    - --language 或者 -l，Gremlin 脚本的语言，默认为 gremlin-groovy
    > --file 和 --script 二者互斥，必须设置其中之一

##### 3.6 备份/恢复类

- backup，将某张图中的 schema 或者 data 备份到 HugeGraph 系统之外，以 JSON 形式存在本地磁盘或者 HDFS
    - --format，备份的格式，可选值包括 [json, text]，默认为 json
    - --all-properties，是否备份顶点/边全部的属性，仅在 --format 为 text 是有效，默认 false
    - --label，要备份的顶点/边的类型，仅在 --format 为 text 是有效，只有备份顶点或者边的时候有效
    - --properties，要备份的顶点/边的属性，逗号分隔，仅在 --format 为 text 是有效，只有备份顶点或者边的时候有效
    - --compress，备份时是否压缩数据，默认为 true
    - --directory 或者 -d，存储 schema 或者 data 的目录，本地目录时，默认为'./{graphName}'，HDFS 时，默认为 '{fs.default.name}/{graphName}'
    - --huge-types 或者 -t，要备份的数据类型，逗号分隔，可选值为 'all' 或者 一个或多个 [vertex,edge,vertex_label,edge_label,property_key,index_label] 的组合，'all' 代表全部6种类型，即顶点、边和所有schema
    - --log 或者 -l，指定日志目录，默认为当前目录
    - --retry，指定失败重试次数，默认为 3
    - --thread-num 或者 -T，使用的线程数，默认为 Math.min(10, Math.max(4, CPUs / 2))
    - --split-size 或者 -s，指定在备份时对顶点或者边分块的大小，默认为 1048576
    - -D，用 -Dkey=value 的模式指定动态参数，用来备份数据到 HDFS 时，指定 HDFS 的配置项，例如：-Dfs.default.name=hdfs://localhost:9000 
- restore，将 JSON 格式存储的 schema 或者 data 恢复到一个新图中（RESTORING 模式）或者合并到已存在的图中（MERGING 模式）
    - --directory 或者 -d，存储 schema 或者 data 的目录，本地目录时，默认为'./{graphName}'，HDFS 时，默认为 '{fs.default.name}/{graphName}'
    - --clean，是否在恢复图完成后删除 --directory 指定的目录，默认为 false
    - --huge-types 或者 -t，要恢复的数据类型，逗号分隔，可选值为 'all' 或者 一个或多个 [vertex,edge,vertex_label,edge_label,property_key,index_label] 的组合，'all' 代表全部6种类型，即顶点、边和所有schema
    - --log 或者 -l，指定日志目录，默认为当前目录
    - --retry，指定失败重试次数，默认为 3
    - --thread-num 或者 -T，使用的线程数，默认为 Math.min(10, Math.max(4, CPUs / 2))
    - -D，用 -Dkey=value 的模式指定动态参数，用来从 HDFS 恢复图时，指定 HDFS 的配置项，例如：-Dfs.default.name=hdfs://localhost:9000
    > 只有当 --format 为 json 执行 backup 时，才可以使用 restore 命令恢复
- migrate, 将当前连接的图迁移至另一个 HugeGraphServer 中
    - --target-graph，目标图的名字，默认为 hugegraph
    - --target-url，目标图所在的 HugeGraphServer，默认为 http://127.0.0.1:8081
    - --target-username，访问目标图的用户名
    - --target-password，访问目标图的密码
    - --target-timeout，访问目标图的超时时间
    - --target-trust-store-file，访问目标图使用的 truststore 文件
    - --target-trust-store-password，访问目标图使用的 truststore 的密码
    - --directory 或者 -d，迁移过程中，存储源图的 schema 或者 data 的目录，本地目录时，默认为'./{graphName}'，HDFS 时，默认为 '{fs.default.name}/{graphName}'
    - --huge-types 或者 -t，要迁移的数据类型，逗号分隔，可选值为 'all' 或者 一个或多个 [vertex,edge,vertex_label,edge_label,property_key,index_label] 的组合，'all' 代表全部6种类型，即顶点、边和所有schema
    - --log 或者 -l，指定日志目录，默认为当前目录
    - --retry，指定失败重试次数，默认为 3
    - --split-size 或者 -s，指定迁移过程中对源图进行备份时顶点或者边分块的大小，默认为 1048576
    - -D，用 -Dkey=value 的模式指定动态参数，用来在迁移图过程中需要备份数据到 HDFS 时，指定 HDFS 的配置项，例如：-Dfs.default.name=hdfs://localhost:9000
    - --graph-mode 或者 -m，将源图恢复到目标图时将目标图设置的模式，合法值包括 [RESTORING, MERGING]
    - --keep-local-data，是否保留在迁移图的过程中产生的源图的备份，默认为 false，即默认迁移图结束后不保留产生的源图备份
- schedule-backup，周期性对图执行备份操作，并保留一定数目的最新备份（目前仅支持本地文件系统）
    - --directory 或者 -d，必填项，指定备份数据的目录
    - --backup-num，选填项，指定保存的最新的备份的数目，默认为 3
    - --interval，选填项，指定进行备份的周期，格式同 Linux crontab 格式
- dump，把整张图的顶点和边全部导出，默认以`vertex vertex-edge1 vertex-edge2...`JSON格式存储。
用户也可以自定义存储格式，只需要在`hugegraph-tools/src/main/java/com/baidu/hugegraph/formatter`
目录下实现一个继承自`Formatter`的类，例如`CustomFormatter`，使用时指定该类为formatter即可，例如
`bin/hugegraph dump -f CustomFormatter`
    - --formatter 或者 -f，指定使用的 formatter，默认为 JsonFormatter
    - --directory 或者 -d，存储 schema 或者 data 的目录，默认为当前目录
    - --log 或者 -l，指定日志目录，默认为当前目录
    - --retry，指定失败重试次数，默认为 3
    - --split-size 或者 -s，指定在备份时对顶点或者边分块的大小，默认为 1048576
    - -D，用 -Dkey=value 的模式指定动态参数，用来备份数据到 HDFS 时，指定 HDFS 的配置项，例如：-Dfs.default.name=hdfs://localhost:9000

##### 3.7 认证数据备份/恢复类

- auth-backup，备份认证数据到指定目录
    - --types 或者 -t，要备份的认证数据类型，逗号分隔，可选值为 'all' 或者一个或多个 [user, group, target, belong, access] 的组合，'all' 代表全部5种类型
    - --directory 或者 -d，备份数据存储目录，默认为当前目录
    - --log 或者 -l，指定日志目录，默认为当前目录
    - --retry，指定失败重试次数，默认为 3
    - --thread-num 或者 -T，使用的线程数，默认为 Math.min(10, Math.max(4, CPUs / 2))
    - -D，用 -Dkey=value 的模式指定动态参数，用来备份数据到 HDFS 时，指定 HDFS 的配置项，例如：-Dfs.default.name=hdfs://localhost:9000
- auth-restore，从指定目录恢复认证数据
    - --types 或者 -t，要恢复的认证数据类型，逗号分隔，可选值为 'all' 或者一个或多个 [user, group, target, belong, access] 的组合，'all' 代表全部5种类型
    - --directory 或者 -d，备份数据存储目录，默认为当前目录
    - --log 或者 -l，指定日志目录，默认为当前目录
    - --retry，指定失败重试次数，默认为 3
    - --thread-num 或者 -T，使用的线程数，默认为 Math.min(10, Math.max(4, CPUs / 2))
    - --strategy，冲突处理策略，可选值为 [stop, ignore]，默认为 stop。stop 表示遇到冲突时停止恢复，ignore 表示忽略冲突继续恢复
    - --init-password，恢复用户时设置的初始密码，恢复用户数据时必填
    - -D，用 -Dkey=value 的模式指定动态参数，用来从 HDFS 恢复数据时，指定 HDFS 的配置项，例如：-Dfs.default.name=hdfs://localhost:9000

##### 3.8 安装部署类

- deploy，一键下载、安装和启动 HugeGraph-Server 和 HugeGraph-Studio
    - -v，必填项，指明安装的 HugeGraph-Server 和 HugeGraph-Studio 的版本号，最新的是 0.9
    - -p，必填项，指定安装的 HugeGraph-Server 和 HugeGraph-Studio 目录
    - -u，选填项，指定下载 HugeGraph-Server 和 HugeGraph-Studio 压缩包的链接
- clear，清理 HugeGraph-Server 和 HugeGraph-Studio 目录和tar包
    - -p，必填项，指定要清理的 HugeGraph-Server 和 HugeGraph-Studio 的目录
- start-all，一键启动 HugeGraph-Server 和 HugeGraph-Studio，并启动监控，服务死掉时自动拉起服务
    - -v，必填项，指明要启动的 HugeGraph-Server 和 HugeGraph-Studio 的版本号，最新的是 0.9
    - -p，必填项，指定安装了 HugeGraph-Server 和 HugeGraph-Studio 的目录
- stop-all，一键关闭 HugeGraph-Server 和 HugeGraph-Studio

> deploy命令中有可选参数 -u，提供时会使用指定的下载地址替代默认下载地址下载 tar 包，并且将地址写入`~/hugegraph-download-url-prefix`文件中；之后如果不指定地址时，会优先从`~/hugegraph-download-url-prefix`指定的地址下载 tar 包；如果 -u 和`~/hugegraph-download-url-prefix`都没有时，会从默认下载地址进行下载

##### 3.9 具体命令参数

各子命令的具体参数如下：

```bash
Usage: hugegraph [options] [command] [command options]
  Options:
    --graph
      Name of graph
      Default: hugegraph
    --password
      Password of user
    --timeout
      Connection timeout
      Default: 30
    --trust-store-file
      The path of client truststore file used when https protocol is enabled
    --trust-store-password
      The password of the client truststore file used when the https protocol 
      is enabled
    --url
      The URL of HugeGraph-Server
      Default: http://127.0.0.1:8080
    --user
      Name of user
  Commands:
    graph-list      List all graphs
      Usage: graph-list

    graph-get      Get graph info
      Usage: graph-get

    graph-clear      Clear graph schema and data
      Usage: graph-clear [options]
        Options:
        * --confirm-message, -c
            Confirm message of graph clear is "I'm sure to delete all data". 
            (Note: include "")

    graph-mode-set      Set graph mode
      Usage: graph-mode-set [options]
        Options:
        * --graph-mode, -m
            Graph mode, include: [NONE, RESTORING, MERGING]
            Possible Values: [NONE, RESTORING, MERGING, LOADING]

    graph-mode-get      Get graph mode
      Usage: graph-mode-get

    task-list      List tasks
      Usage: task-list [options]
        Options:
          --limit
            Limit number, no limit if not provided
            Default: -1
          --status
            Status of task

    task-get      Get task info
      Usage: task-get [options]
        Options:
        * --task-id
            Task id
            Default: 0

    task-delete      Delete task
      Usage: task-delete [options]
        Options:
        * --task-id
            Task id
            Default: 0

    task-cancel      Cancel task
      Usage: task-cancel [options]
        Options:
        * --task-id
            Task id
            Default: 0

    task-clear      Clear completed tasks
      Usage: task-clear [options]
        Options:
          --force
            Force to clear all tasks, cancel all uncompleted tasks firstly, 
            and delete all completed tasks
            Default: false

    gremlin-execute      Execute Gremlin statements
      Usage: gremlin-execute [options]
        Options:
          --aliases, -a
            Gremlin aliases, valid format is: 'key1=value1,key2=value2...'
            Default: {}
          --bindings, -b
            Gremlin bindings, valid format is: 'key1=value1,key2=value2...'
            Default: {}
          --file, -f
            Gremlin Script file to be executed, UTF-8 encoded, exclusive to 
            --script 
          --language, -l
            Gremlin script language
            Default: gremlin-groovy
          --script, -s
            Gremlin script to be executed, exclusive to --file

    gremlin-schedule      Execute Gremlin statements as asynchronous job
      Usage: gremlin-schedule [options]
        Options:
          --bindings, -b
            Gremlin bindings, valid format is: 'key1=value1,key2=value2...'
            Default: {}
          --file, -f
            Gremlin Script file to be executed, UTF-8 encoded, exclusive to 
            --script 
          --language, -l
            Gremlin script language
            Default: gremlin-groovy
          --script, -s
            Gremlin script to be executed, exclusive to --file

    backup      Backup graph schema/data. If directory is on HDFS, use -D to 
            set HDFS params. For exmaple:
            -Dfs.default.name=hdfs://localhost:9000 
      Usage: backup [options]
        Options:
          --all-properties
            All properties to be backup flag
            Default: false
          --compress
            compress flag
            Default: true
          --directory, -d
            Directory of graph schema/data, default is './{graphname}' in 
            local file system or '{fs.default.name}/{graphname}' in HDFS
          --format
            File format, valid is [json, text]
            Default: json
          --huge-types, -t
            Type of schema/data. Concat with ',' if more than one. 'all' means 
            all vertices, edges and schema, in other words, 'all' equals with 
            'vertex,edge,vertex_label,edge_label,property_key,index_label' 
            Default: [PROPERTY_KEY, VERTEX_LABEL, EDGE_LABEL, INDEX_LABEL, VERTEX, EDGE]
          --label
            Vertex or edge label, only valid when type is vertex or edge
          --log, -l
            Directory of log
            Default: ./logs
          --properties
            Vertex or edge properties to backup, only valid when type is
            vertex or edge
            Default: []
          --retry
            Retry times, default is 3
            Default: 3
          --split-size, -s
            Split size of shard
            Default: 1048576
          -D
            HDFS config parameters
            Syntax: -Dkey=value
            Default: {}

    schedule-backup      Schedule backup task
      Usage: schedule-backup [options]
        Options:
          --backup-num
            The number of latest backups to keep
            Default: 3
        * --directory, -d
            The directory of backups stored
          --interval
            The interval of backup, format is: "a b c d e". 'a' means minute 
            (0 - 59), 'b' means hour (0 - 23), 'c' means day of month (1 - 
            31), 'd' means month (1 - 12), 'e' means day of week (0 - 6) 
            (Sunday=0), "*" means all
            Default: "0 0 * * *"

    dump      Dump graph to files
      Usage: dump [options]
        Options:
          --directory, -d
            Directory of graph schema/data, default is './{graphname}' in 
            local file system or '{fs.default.name}/{graphname}' in HDFS
          --formatter, -f
            Formatter to customize format of vertex/edge
            Default: JsonFormatter
          --log, -l
            Directory of log
            Default: ./logs
          --retry
            Retry times, default is 3
            Default: 3
          --split-size, -s
            Split size of shard
            Default: 1048576
          -D
            HDFS config parameters
            Syntax: -Dkey=value
            Default: {}

    restore      Restore graph schema/data. If directory is on HDFS, use -D to 
            set HDFS params if needed. For 
            exmaple:-Dfs.default.name=hdfs://localhost:9000 
      Usage: restore [options]
        Options:
          --clean
            Whether to remove the directory of graph data after restored
            Default: false
          --directory, -d
            Directory of graph schema/data, default is './{graphname}' in 
            local file system or '{fs.default.name}/{graphname}' in HDFS
          --huge-types, -t
            Type of schema/data. Concat with ',' if more than one. 'all' means 
            all vertices, edges and schema, in other words, 'all' equals with 
            'vertex,edge,vertex_label,edge_label,property_key,index_label' 
            Default: [PROPERTY_KEY, VERTEX_LABEL, EDGE_LABEL, INDEX_LABEL, VERTEX, EDGE]
          --log, -l
            Directory of log
            Default: ./logs
          --retry
            Retry times, default is 3
            Default: 3
          -D
            HDFS config parameters
            Syntax: -Dkey=value
            Default: {}

    migrate      Migrate graph
      Usage: migrate [options]
        Options:
          --directory, -d
            Directory of graph schema/data, default is './{graphname}' in 
            local file system or '{fs.default.name}/{graphname}' in HDFS
          --graph-mode, -m
            Mode used when migrating to target graph, include: [RESTORING, 
            MERGING] 
            Default: RESTORING
            Possible Values: [NONE, RESTORING, MERGING, LOADING]
          --huge-types, -t
            Type of schema/data. Concat with ',' if more than one. 'all' means 
            all vertices, edges and schema, in other words, 'all' equals with 
            'vertex,edge,vertex_label,edge_label,property_key,index_label' 
            Default: [PROPERTY_KEY, VERTEX_LABEL, EDGE_LABEL, INDEX_LABEL, VERTEX, EDGE]
          --keep-local-data
            Whether to keep the local directory of graph data after restored
            Default: false
          --log, -l
            Directory of log
            Default: ./logs
          --retry
            Retry times, default is 3
            Default: 3
          --split-size, -s
            Split size of shard
            Default: 1048576
          --target-graph
            The name of target graph to migrate
            Default: hugegraph
          --target-password
            The password of target graph to migrate
          --target-timeout
            The timeout to connect target graph to migrate
            Default: 0
          --target-trust-store-file
            The trust store file of target graph to migrate
          --target-trust-store-password
            The trust store password of target graph to migrate
          --target-url
            The url of target graph to migrate
            Default: http://127.0.0.1:8081
          --target-user
            The username of target graph to migrate
          -D
            HDFS config parameters
            Syntax: -Dkey=value
            Default: {}

    deploy      Install HugeGraph-Server and HugeGraph-Studio
      Usage: deploy [options]
        Options:
        * -p
            Install path of HugeGraph-Server and HugeGraph-Studio
          -u
            Download url prefix path of HugeGraph-Server and HugeGraph-Studio
        * -v
            Version of HugeGraph-Server and HugeGraph-Studio

    start-all      Start HugeGraph-Server and HugeGraph-Studio
      Usage: start-all [options]
        Options:
        * -p
            Install path of HugeGraph-Server and HugeGraph-Studio
        * -v
            Version of HugeGraph-Server and HugeGraph-Studio

    clear      Clear HugeGraph-Server and HugeGraph-Studio
      Usage: clear [options]
        Options:
        * -p
            Install path of HugeGraph-Server and HugeGraph-Studio

    stop-all      Stop HugeGraph-Server and HugeGraph-Studio
      Usage: stop-all

    help      Print usage
      Usage: help

```

##### 3.10 具体命令示例

###### 1. gremlin语句

```bash
# 同步执行gremlin
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph gremlin-execute --script 'g.V().count()'

# 异步执行gremlin
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph gremlin-schedule --script 'g.V().count()'
```

###### 2. 查看task情况

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph task-list

./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph task-list --limit 5

./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph task-list --status success
```

###### 3. 图模式查看和设置

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-mode-set -m RESTORING MERGING NONE

./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-mode-set -m RESTORING

./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-mode-get

./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-list
```

###### 4. 清理图

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-clear -c "I'm sure to delete all data"
```

###### 5. 图备份

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph backup -t all --directory ./backup-test
```

###### 6. 周期性的备份

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph --interval */2 * * * * schedule-backup -d ./backup-0.10.2
```

###### 7. 图恢复

```bash
# 设置图模式
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-mode-set -m RESTORING

# 恢复图
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph restore -t all --directory ./backup-test

# 恢复图模式
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-mode-set -m NONE
```

###### 8. 图迁移

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph migrate --target-url http://127.0.0.1:8090 --target-graph hugegraph
```
