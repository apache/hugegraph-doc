---
title: "HugeGraph-Tools Quick Start"
linkTitle: "Manage with HugeGraph-Tools"
weight: 3
---

### 1 HugeGraph-Tools Overview

HugeGraph-Tools is an automated deployment, management and backup/restore component of HugeGraph.

> **Testing Guide**: For running HugeGraph-Tools tests locally, please refer to [HugeGraph Toolchain Local Testing Guide](/docs/guides/toolchain-local-test)

### 2 Get HugeGraph-Tools

HugeGraph-Tools is included in the Toolchain distribution. You can download the distribution or build it from source.

- Download the compiled tarball
- Clone source code then compile and install

#### 2.1 Download the compiled archive

Download the latest version of the HugeGraph-Toolchain package:

```bash
export VERSION=1.7.0
export ARCHIVE="apache-hugegraph-toolchain-incubating-${VERSION}"
wget "https://downloads.apache.org/hugegraph/${VERSION}/${ARCHIVE}.tar.gz"
tar zxf "${ARCHIVE}.tar.gz"
# hugegraph-tools ships inside the toolchain package, in a directory
# whose version suffix is the same as the archive's
cd "${ARCHIVE}/apache-hugegraph-tools-incubating-${VERSION}"
```

#### 2.2 Clone source code to compile and install
Please ensure that the wget command is installed before compiling the source code

Download the latest version of the HugeGraph-Tools source package:

```bash
# 1. get from github
git clone https://github.com/apache/hugegraph-toolchain.git

# 2. Download a released source package
export VERSION=1.7.0
export ARCHIVE="apache-hugegraph-toolchain-incubating-${VERSION}"
wget "https://downloads.apache.org/hugegraph/${VERSION}/${ARCHIVE}-src.tar.gz"
```

Compile and generate tar package:

```bash
cd hugegraph-toolchain
mvn package -pl hugegraph-tools -am -DskipTests -ntp
```

The package is generated as `hugegraph-tools/target/apache-hugegraph-tools-${version}.tar.gz`, and the unpacked directory `hugegraph-tools/apache-hugegraph-tools-${version}` (containing `bin/` and `lib/`) is created next to it.


### 3 How to use

#### 3.1 Function overview

After decompression, enter the apache-hugegraph-tools-${version} directory, you can use `bin/hugegraph` or `bin/hugegraph help` to view the usage information, and `bin/hugegraph help <sub-command>` to view the usage of a single sub-command. mainly divided:

- Graph management type, graph-mode-set, graph-mode-get, graph-list, graph-get, graph-clear, graph-create, graph-clone and graph-drop
- Asynchronous task management type, task-list, task-get, task-delete, task-cancel and task-clear
- Gremlin type, gremlin-execute and gremlin-schedule
- Backup/Restore type, backup, restore, migrate, schedule-backup and dump
- Authentication data backup/restore type, auth-backup and auth-restore
- Install deployment type, deploy, clear, start-all and stop-all

```bash
Usage: hugegraph [options] [command] [command options]
```

##### 3.2 [options]-Global Variable

`options` is a global variable of HugeGraph-Tools, which can be configured in hugegraph-tools/bin/hugegraph, including:

- --graph，HugeGraph-Tools The name of the graph to operate on, the default value is hugegraph
- --url，The service address of HugeGraph-Server, the default is http://127.0.0.1:8080
- --user，When HugeGraph-Server opens authentication, pass username
- --password，When HugeGraph-Server opens authentication, pass the user's password
- --timeout，Timeout when connecting to HugeGraph-Server, the default is 30s
- --trust-store-file，The path of the certificate file, when --url uses https, the truststore file used by HugeGraph-Client, the default is empty, which means using the built-in truststore file conf/hugegraph.truststore of hugegraph-tools
- --trust-store-password，The password of the certificate file, when --url uses https, the password of the truststore used by HugeGraph-Client, the default is empty, representing the password of the built-in truststore file of hugegraph-tools
- --throw-mode, whether HugeGraph-Tools throws the exception instead of printing the error message and exiting, the default is false (mainly used by tests)

> The protocol is taken from the scheme of --url: use `https://...` to connect over https. --trust-store-file and --trust-store-password can only be set when --url uses https, and both --user and --password must be given together or omitted together.

The above global variables can also be set through environment variables. One way is to use export on the command line to set temporary environment variables, which are valid until the command line is closed


| Global Variable                   | Environment Variable           | Example                                            |
|------------------------|--------------------------------|----------------------------------------------------|
| --url                  | HUGEGRAPH_URL                  | export HUGEGRAPH_URL=http://127.0.0.1:8080         |
| --graph                | HUGEGRAPH_GRAPH                | export HUGEGRAPH_GRAPH=hugegraph                   |
| --user                 | HUGEGRAPH_USERNAME             | export HUGEGRAPH_USERNAME=admin                    |
| --password             | HUGEGRAPH_PASSWORD             | export HUGEGRAPH_PASSWORD=test                     |
| --timeout              | HUGEGRAPH_TIMEOUT              | export HUGEGRAPH_TIMEOUT=30                        |
| --trust-store-file     | HUGEGRAPH_TRUST_STORE_FILE     | export HUGEGRAPH_TRUST_STORE_FILE=/tmp/trust-store |
| --trust-store-password | HUGEGRAPH_TRUST_STORE_PASSWORD | export HUGEGRAPH_TRUST_STORE_PASSWORD=xxxx         |

Another way is to set the environment variable in the bin/hugegraph script:

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

`bin/hugegraph` also reads `JAVA_HOME` (a warning is printed when it is not set, and it is needed for https) and `JAVA_OPTIONS` (JVM options; when it is empty the script uses `-Xms512m` plus an `-Xmx` computed from the free memory of the machine).

##### 3.3 Graph Management Type, graph-mode-set, graph-mode-get, graph-list, graph-get, graph-clear, graph-create, graph-clone and graph-drop

- graph-mode-set, set graph restore mode
  - --graph-mode or -m, required, specifies the mode to be set, legal values include [NONE, RESTORING, MERGING, LOADING]
- graph-mode-get, get graph restore mode
- graph-list, list all graphs in a HugeGraph-Server
- graph-get, get a graph and its storage backend type
- graph-clear, clear all schema and data of a graph
  - --confirm-message or -c, required, delete confirmation information, manual input is required, double confirmation to prevent accidental deletion, "I'm sure to delete all data", including double quotes
- graph-create, create a new graph with configuration file
  - --name or -n, optional, the name of the new graph, default is g
  - --file or -f, the path to the graph configuration file, the content of the file is sent to HugeGraph-Server as the config of the new graph
- graph-clone, clone an existing graph
  - --name or -n, optional, the name of the cloned graph, default is g
  - --clone-graph-name, optional, the name of the source graph to clone from, default is hugegraph
- graph-drop, drop a graph (different from graph-clear, this completely removes the graph)
  - --confirm-message or -c, required, confirmation message "I'm sure to drop the graph", including double quotes

> graph-create, graph-clone, graph-clear and graph-drop raise --timeout to at least 300 seconds.

> When you need to restore the backup graph to a new graph, you need to set the graph mode to RESTORING mode; when you need to merge the backup graph into an existing graph, you need to first set the graph mode to MERGING model.

##### 3.4 Asynchronous task management Type，task-list、task-get、task-delete、task-cancel and task-clear

- task-list，List the asynchronous tasks in a graph, which can be filtered according to the status of the tasks
  - --status，Optional, specify the status of the task to view, i.e. filter tasks by status, legal values include [UNKNOWN, NEW, QUEUED, RESTORING, RUNNING, SUCCESS, CANCELLED, FAILED] (case insensitive)
  - --limit，Optional, specify the number of tasks to be obtained, the default is -1, which means to obtain all eligible tasks, a value passed explicitly must be positive
- task-get，Get detailed information about an asynchronous task
  - --task-id，Required, specifies the ID of the asynchronous task
- task-delete，Delete information about an asynchronous task
  - --task-id，Required, specifies the ID of the asynchronous task
- task-cancel，Cancel the execution of an asynchronous task
  - --task-id，Required, the ID of the asynchronous task to cancel
- task-clear，Clean up completed asynchronous tasks
  - --force，Optional. When set, it means to clean up all asynchronous tasks. Unfinished ones are canceled first, and then all asynchronous tasks are cleared. By default, only completed asynchronous tasks are cleaned up

##### 3.5 Gremlin Type，gremlin-execute and gremlin-schedule

> ⚠️ **SEC Reminder**: The execution of Gremlin depends on the actual logic of the statements, which may involve scenarios such as large-scale data modification and high-risk system calls with potential implicit hazards. Please use this tool **only in secure and trusted network environments**. It is imperative to configure and secure **HugeGraph-Server** with the **[Authentication System (Auth)](/docs/config/config-authentication/)** and an **IP Whitelist** to restrict execution requests on the server side. Never hand over the tool or expose the execution entry to unauthorized personnel.

- gremlin-execute, send Gremlin statements to HugeGraph-Server to execute query or modification operations, execute synchronously, and return results after completion
  - --file or -f, specify the script file to execute, UTF-8 encoding, mutually exclusive with --script
  - --script or -s, specifies the script string to execute, mutually exclusive with --file
  - --aliases or -a, Gremlin alias settings, the format is: key1=value1,key2=value2,...
  - --bindings or -b, Gremlin binding settings, the format is: key1=value1,key2=value2,...
  - --language or -l, the language of the Gremlin script, the default is gremlin-groovy
  > --file and --script are mutually exclusive, one of them must be set
- gremlin-schedule, send Gremlin statements to HugeGraph-Server to perform query or modification operations, asynchronous execution, and return the asynchronous task id immediately after the task is submitted
  - --file or -f, specify the script file to execute, UTF-8 encoding, mutually exclusive with --script
  - --script or -s, specifies the script string to execute, mutually exclusive with --file
  - --bindings or -b, Gremlin binding settings, the format is: key1=value1,key2=value2,...
  - --language or -l, the language of the Gremlin script, the default is gremlin-groovy
  > --file and --script are mutually exclusive, one of them must be set

##### 3.6 Backup/Restore Type

- backup, back up the schema or data in a certain graph out of the HugeGraph system, and store it on the local disk or HDFS in the form of JSON
  - --format, the backup format, optional values include [json, text], the default is json
  - --all-properties, whether to back up all properties of vertices/edges, only valid when --format is text, default false
  - --label, the vertex label or edge label to be backed up, only applied when --format is text; when it is set, --huge-types must name exactly one type and that type must be vertex or edge, otherwise the command fails
  - --properties, properties of vertices/edges to be backed up, separated by commas, only valid when --format is text, valid only when backing up vertices or edges
  - --compress, whether to compress data during backup, the default is true
  - --directory or -d, the directory to store schema or data, the default is './{graphName}' for local directory, and '{fs.default.name}/{graphName}' for HDFS
  - --huge-types or -t, the data types to be backed up, separated by commas, the optional value is 'all' or a combination of one or more [vertex, edge, vertex_label, edge_label, property_key, index_label], 'all' Represents all 6 types, namely vertices, edges and all schemas, 'schema' represents the 4 schema types [vertex_label, edge_label, property_key, index_label]
  - --log or -l, specify the log directory, the default is ./logs
  - --retry, specify the number of failed retries, the default is 3
  - --thread-num or -T, the number of threads to use, default is Math.min(10, Math.max(4, CPUs / 2))
  - --split-size or -s, specifies the size of splitting vertices or edges when backing up, the default is 1048576, and it must be at least 1048576 (1M)
  - -D, use the mode of -Dkey=value to specify dynamic parameters, and specify HDFS configuration items when backing up data to HDFS, for example: -Dfs.default.name=hdfs://localhost:9000
  > If --timeout is less than 120 seconds, backup (and the backup step of migrate) uses 120 seconds
- restore, restore schema or data stored in JSON format to a new graph (RESTORING mode) or merge into an existing graph (MERGING mode)
  - --directory or -d, the directory to store schema or data, the default is './{graphName}' for local directory, and '{fs.default.name}/{graphName}' for HDFS
  - --clean, whether to delete the directory specified by --directory after the recovery map is completed, the default is false
  - --huge-types or -t, data types to restore, separated by commas, optional value is 'all' or a combination of one or more [vertex, edge, vertex_label, edge_label, property_key, index_label], 'all' Represents all 6 types, namely vertices, edges and all schemas, 'schema' represents the 4 schema types [vertex_label, edge_label, property_key, index_label]
  - --log or -l, specify the log directory, the default is ./logs
  - --retry, specify the number of failed retries, the default is 3
  - --thread-num or -T, the number of threads to use, default is Math.min(10, Math.max(4, CPUs / 2))
  - -D, use the mode of -Dkey=value to specify dynamic parameters, which are used to specify HDFS configuration items when restoring graphs from HDFS, for example: -Dfs.default.name=hdfs://localhost:9000
  > restore command can be used only if --format is executed as backup for json
  > restore requires the graph to be in RESTORING or MERGING mode (set it with graph-mode-set first), otherwise the command fails
- migrate, migrate the currently connected graph to another HugeGraphServer
  - --target-graph, the name of the target graph, the default is hugegraph
  - --target-url, the HugeGraphServer where the target graph is located, the default is http://127.0.0.1:8081
  - --target-user, the username used to access the target graph
  - --target-password, the password to access the target map
  - --target-timeout, the timeout for accessing the target map
  - --target-trust-store-file, access the truststore file used by the target graph
  - --target-trust-store-password, the password to access the truststore used by the target map
  - --directory or -d, during the migration process, the directory where the schema or data of the source graph is stored. For a local directory, the default is './{graphName}'; for HDFS, the default is '{fs.default.name}/ {graphName}'
  - --huge-types or -t, the data types to be migrated, separated by commas, the optional value is 'all' or a combination of one or more [vertex, edge, vertex_label, edge_label, property_key, index_label], 'all' Represents all 6 types, namely vertices, edges and all schemas, 'schema' represents the 4 schema types [vertex_label, edge_label, property_key, index_label]
  - --log or -l, specify the log directory, the default is ./logs
  - --retry, specify the number of failed retries, the default is 3
  - --thread-num or -T, the number of threads to use, default is Math.min(10, Math.max(4, CPUs / 2))
  - --split-size or -s, specify the size of the vertex or edge block when backing up the source graph during the migration process, the default is 1048576, and it must be at least 1048576 (1M)
  - -D, use the mode of -Dkey=value to specify dynamic parameters, which are used to specify HDFS configuration items when the data needs to be backed up to HDFS during the migration process, for example: -Dfs.default.name=hdfs://localhost: 9000
  - --graph-mode or -m, the mode to set the target graph when restoring the source graph to the target graph, legal values include [RESTORING, MERGING], the default is RESTORING. The target graph is switched to this mode during the migration and switched back to its original mode afterwards
  - --keep-local-data, whether to keep the backup of the source map generated in the process of migrating the map, the default is false, that is, the backup of the source map is not kept after the default migration map ends
- schedule-backup, periodically back up the graph and keep a certain number of the latest backups (currently only supports local file systems)
  - --directory or -d, required, specifies the directory of the backup data
  - --backup-num, optional, specifies the number of latest backups to save, defaults to 3
  - --interval, an optional item, specifies the backup cycle, the format is the same as the Linux crontab format, the default is "0 0 * * *" (every day at 00:00)
  > schedule-backup adds a crontab entry that runs `backup -t all` into `{directory}/{graph}/hugegraph-backup-{yyMMddHHmm}/` and keeps only the latest --backup-num backups. A relative --directory is resolved against the hugegraph-tools home directory, and `{directory}/{graph}` must not exist yet
- dump, export all vertices and edges in the graph, using the `vertex vertex-edge1 vertex-edge2...` JSON format by default.
  To customize the format, implement a `Formatter` subclass such as `CustomFormatter` under `hugegraph-tools/src/main/java/org/apache/hugegraph/formatter`, then select it when running the command:
  `bin/hugegraph dump -f CustomFormatter`
  - --formatter or -f, specify the formatter to use, the default is JsonFormatter
  - --directory or -d, the directory where schema or data is stored, the default is './{graphName}' for local directory, and '{fs.default.name}/{graphName}' for HDFS
  - --log or -l, specify the log directory, the default is ./logs
  - --retry, specify the number of failed retries, the default is 3
  - --thread-num or -T, the number of threads to use, default is Math.min(10, Math.max(4, CPUs / 2))
  - --split-size or -s, specifies the size of splitting vertices or edges when backing up, the default is 1048576, and it must be at least 1048576 (1M)
  - -D, use the mode of -Dkey=value to specify dynamic parameters, and specify HDFS configuration items when backing up data to HDFS, for example: -Dfs.default.name=hdfs://localhost:9000

##### 3.7 Authentication data backup/restore type

- auth-backup, backup authentication data to a specified directory
  - --types or -t, types of authentication data to back up, separated by commas, optional value is 'all' or a combination of one or more [user, group, target, belong, access], 'all' represents all 5 types; 'belong' requires 'user' and 'group' to be included, 'access' requires 'group' and 'target' to be included
  - --directory, directory to store backup data, the default is './auth-backup-restore' for local directory, and '{fs.default.name}/auth-backup-restore' for HDFS (this option has no -d short form)
  - --retry, specify the number of failed retries, the default is 3
  - -D, use the mode of -Dkey=value to specify dynamic parameters, and specify HDFS configuration items when backing up data to HDFS, for example: -Dfs.default.name=hdfs://localhost:9000
- auth-restore, restore authentication data from a specified directory
  - --types or -t, types of authentication data to restore, separated by commas, optional value is 'all' or a combination of one or more [user, group, target, belong, access], 'all' represents all 5 types; 'belong' requires 'user' and 'group' to be included, 'access' requires 'group' and 'target' to be included
  - --directory, directory where backup data is stored, the default is './auth-backup-restore' for local directory, and '{fs.default.name}/auth-backup-restore' for HDFS (this option has no -d short form)
  - --retry, specify the number of failed retries, the default is 3
  - --strategy, conflict handling strategy, optional values are [stop, ignore], default is stop. stop means stop restoring when encountering conflicts, ignore means ignore conflicts and continue restoring
  - --init-password, initial password to set when restoring users, required when --types includes user
  - -D, use the mode of -Dkey=value to specify dynamic parameters, which are used to specify HDFS configuration items when restoring data from HDFS, for example: -Dfs.default.name=hdfs://localhost:9000

##### 3.8 Install the deployment type

- deploy, one-click download, install and start HugeGraph-Server and HugeGraph-Studio
  - -v, required, specifies the HugeGraph-Server and HugeGraph-Studio version to install, must be one of the versions listed in bin/version-map.yaml (0.6, 0.7, 0.8, 0.9, 0.10), which maps it to the matching server and studio release versions
  - -p, required, specifies the installed HugeGraph-Server and HugeGraph-Studio directories
  - -u, optional, specifies the link to download the HugeGraph-Server and HugeGraph-Studio compressed packages
- clear, clean up HugeGraph-Server and HugeGraph-Studio directories and tarballs (refuses to run while a matching server or studio process is still alive, and prompts before each removal)
  - -p, required, specifies the directory of HugeGraph-Server and HugeGraph-Studio to be cleaned
- start-all, start HugeGraph-Server and HugeGraph-Studio with one click
  - -v, required, specifies the installed HugeGraph-Server and HugeGraph-Studio version to start, same values as deploy
  - -p, required, specifies the directory where HugeGraph-Server and HugeGraph-Studio are installed
- stop-all, close HugeGraph-Server and HugeGraph-Studio with one click

> deploy, start-all, clear and stop-all are handed by `bin/hugegraph` straight to the shell scripts `bin/deploy.sh`, `bin/start-all.sh`, `bin/clear.sh` and `bin/stop-all.sh`, so the global options and environment variables in 3.2 do not apply to them.

> There is an optional parameter -u in the deploy command. When provided, the specified download address will be used instead of the default download address to download the tar package, and the address will be written into the `~/hugegraph-download-url-prefix` file; if no address is specified later When -u and `~/hugegraph-download-url-prefix` are not specified, the tar package will be downloaded from the address specified by `~/hugegraph-download-url-prefix`; if there is neither -u nor `~/hugegraph-download-url-prefix`, it will be downloaded from the default download address `https://github.com/hugegraph`

##### 3.9 Specific command parameters

The specific parameters of each subcommand are as follows:

```bash
Usage: hugegraph [options] [command] [command options]
  Options:
    --graph
      Name of graph
      Default: hugegraph
    --password
      Password of user
    --throw-mode
      Whether the hugegraph-tools work to throw an exception
      Default: false
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
    graph-create      Create graph with config
      Usage: graph-create [options]
        Options:
          --file, -f
            Creating graph config file
          --name, -n
            The name of new created graph, default is g
            Default: g

    graph-clone      Clone graph
      Usage: graph-clone [options]
        Options:
          --clone-graph-name
            The name of cloned graph, default is hugegraph
            Default: hugegraph
          --name, -n
            The name of new created graph, default is g
            Default: g

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

    graph-drop      Drop graph
      Usage: graph-drop [options]
        Options:
        * --confirm-message, -c
            Confirm message of graph clear is "I'm sure to drop the graph". 
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
            set HDFS params. For example: 
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
            Type of schema/data. Concat with ',' if more than one. Other types 
            include 'all' and 'schema'. 'all' means all vertices, edges and 
            schema. In other words, 'all' equals with 'vertex, edge, 
            vertex_label, edge_label, property_key, index_label'. 'schema' 
            equals with 'vertex_label, edge_label, property_key, index_label'.
            Default: [PROPERTY_KEY, VERTEX_LABEL, EDGE_LABEL, INDEX_LABEL, VERTEX, EDGE]
          --label
            Vertex label or edge label, only valid when type is vertex or edge
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
          --thread-num, -T
            Threads number to use, default is Math.min(10, Math.max(4, CPUs / 
            2)) 
            Default: 0
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
          --thread-num, -T
            Threads number to use, default is Math.min(10, Math.max(4, CPUs / 
            2)) 
            Default: 0
          -D
            HDFS config parameters
            Syntax: -Dkey=value
            Default: {}

    restore      Restore graph schema/data. If directory is on HDFS, use -D to 
            set HDFS params if needed. For 
            example:-Dfs.default.name=hdfs://localhost:9000 
      Usage: restore [options]
        Options:
          --clean
            Whether to remove the directory of graph data after restored
            Default: false
          --directory, -d
            Directory of graph schema/data, default is './{graphname}' in 
            local file system or '{fs.default.name}/{graphname}' in HDFS
          --huge-types, -t
            Type of schema/data. Concat with ',' if more than one. Other types 
            include 'all' and 'schema'. 'all' means all vertices, edges and 
            schema. In other words, 'all' equals with 'vertex, edge, 
            vertex_label, edge_label, property_key, index_label'. 'schema' 
            equals with 'vertex_label, edge_label, property_key, index_label'.
            Default: [PROPERTY_KEY, VERTEX_LABEL, EDGE_LABEL, INDEX_LABEL, VERTEX, EDGE]
          --log, -l
            Directory of log
            Default: ./logs
          --retry
            Retry times, default is 3
            Default: 3
          --thread-num, -T
            Threads number to use, default is Math.min(10, Math.max(4, CPUs / 
            2)) 
            Default: 0
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
            Type of schema/data. Concat with ',' if more than one. Other types 
            include 'all' and 'schema'. 'all' means all vertices, edges and 
            schema. In other words, 'all' equals with 'vertex, edge, 
            vertex_label, edge_label, property_key, index_label'. 'schema' 
            equals with 'vertex_label, edge_label, property_key, index_label'.
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
          --thread-num, -T
            Threads number to use, default is Math.min(10, Math.max(4, CPUs / 
            2)) 
            Default: 0
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

    auth-backup      null
      Usage: auth-backup [options]
        Options:
          --directory
            Directory of auth information, default is 
            './{auth-backup-restore}' in local file system or 
            '{fs.default.name}/{auth-backup-restore}' in HDFS
          --retry
            Retry times, default is 3
            Default: 3
          --types, -t
            Type of auth data to restore and backup, concat with ',' if more 
            than one. 'all' means all auth information. In other words, 'all' 
            equals with 'user, group, target, belong, access'. In addition, 
            'belong' or 'access' can not backup or restore alone, if type 
            contains 'belong' then should contains 'user' and 'group'. If type 
            contains 'access' then should contains 'group' and 'target'.
            Default: [TARGET, GROUP, USER, ACCESS, BELONG]
          -D
            HDFS config parameters
            Syntax: -Dkey=value
            Default: {}

    auth-restore      null
      Usage: auth-restore [options]
        Options:
          --directory
            Directory of auth information, default is 
            './{auth-backup-restore}' in local file system or 
            '{fs.default.name}/{auth-backup-restore}' in HDFS
          --init-password
            Init user password, if restore type include 'user', please specify 
            the init-password of users.
            Default: <empty string>
          --retry
            Retry times, default is 3
            Default: 3
          --strategy
            The strategy needs to be chosen in the event of a conflict when 
            restoring. Valid strategies include 'stop' and 'ignore', default 
            is 'stop'. 'stop' means if there a conflict, stop restore. 
            'ignore' means if there a conflict, ignore and continue to 
            restore. 
            Default: STOP
            Possible Values: [STOP, IGNORE]
          --types, -t
            Type of auth data to restore and backup, concat with ',' if more 
            than one. 'all' means all auth information. In other words, 'all' 
            equals with 'user, group, target, belong, access'. In addition, 
            'belong' or 'access' can not backup or restore alone, if type 
            contains 'belong' then should contains 'user' and 'group'. If type 
            contains 'access' then should contains 'group' and 'target'.
            Default: [TARGET, GROUP, USER, ACCESS, BELONG]
          -D
            HDFS config parameters
            Syntax: -Dkey=value
            Default: {}

    help      Print usage
      Usage: help
```

##### 3.10 Specific command example

###### 1. gremlin statement

```bash
# Execute gremlin synchronously
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph gremlin-execute --script 'g.V().count()'

# Execute gremlin asynchronously
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph gremlin-schedule --script 'g.V().count()'
```

###### 2. Show task status

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph task-list

./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph task-list --limit 5

./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph task-list --status success
```

###### 3. Set and show graph mode

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-mode-set -m RESTORING

./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-mode-get

./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-list
```

###### 4. Cleanup Graph

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-clear -c "I'm sure to delete all data"
```

###### 5. Backup Graph

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph backup -t all --directory ./backup-test
```

###### 6. Periodic Backup Graph

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph schedule-backup -d ./backup --interval "*/2 * * * *"
```

###### 7. Recovery Graph

```bash
# set graph mode
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-mode-set -m RESTORING

# recovery graph
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph restore -t all --directory ./backup-test

# restore graph mode
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph graph-mode-set -m NONE
```

###### 8. Graph Migration

```bash
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph migrate --target-url http://127.0.0.1:8090 --target-graph hugegraph
```
