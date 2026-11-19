---
title: "Tools Quick Start"
linkTitle: "Manage with Tools"
weight: 3
---

### 1 HugeGraph-Tools Overview

HugeGraph-Tools manages graphs and tasks and provides backup and restore commands. It also retains deployment commands for legacy Server/Studio versions.

> **Testing Guide**: For running HugeGraph-Tools tests locally, please refer to [HugeGraph Toolchain Local Testing Guide](/docs/guides/dev-test/toolchain-local-test/)

### 2 Get HugeGraph-Tools

HugeGraph-Tools is included in the Toolchain distribution. You can obtain it via:

- [Download compiled archive](#21-download-the-compiled-archive) — Download the official released Toolchain tarball.
- [Compile released 1.7.0 from source](#22-clone-source-code-to-compile-and-install) — Build release 1.7.0 using Git tag or source archive with JDK 11.
- [Build current master source](#build-current-source) — Build latest master Tools with JDK 17.
{.cards}

#### 2.1 Download the compiled archive

The following example uses the released HugeGraph-Toolchain `1.7.0` package. Check the [download page](/docs/download/download/) for releases.

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

Choose one source below. Both build the released `1.7.0` Tools; install Maven and JDK 11 first. The archive route also requires `wget`.
Each example ends in the generated Tools directory, where `bin/hugegraph help` lists the available commands.

```bash {tab="Git tag"}
git clone --branch 1.7.0 --single-branch https://github.com/apache/hugegraph-toolchain.git
cd hugegraph-toolchain
mvn package -pl hugegraph-tools -am -DskipTests -ntp
cd hugegraph-tools/apache-hugegraph-tools-incubating-1.7.0
bin/hugegraph help
```

```bash {tab="Source archive"}
export VERSION=1.7.0
export ARCHIVE="apache-hugegraph-toolchain-incubating-${VERSION}"
wget "https://downloads.apache.org/hugegraph/${VERSION}/${ARCHIVE}-src.tar.gz"
tar zxf "${ARCHIVE}-src.tar.gz"
cd "${ARCHIVE}-src"
mvn package -pl hugegraph-tools -am -DskipTests -ntp
cd "hugegraph-tools/apache-hugegraph-tools-incubating-${VERSION}"
bin/hugegraph help
```

The build also writes `hugegraph-tools/target/apache-hugegraph-tools-incubating-1.7.0.tar.gz` relative to the source root.

#### 2.3 Build current source {#build-current-source}

Building current Toolchain source requires **JDK 17, Maven 3.6.3+, and Python 3.9+**.
Set `JAVA_HOME` to your JDK 17 installation. Prepare the matching Server SDK before building Tools, Client or Loader.
Use the same terminal and isolated Maven repository for these steps.

1. **Clone Toolchain source**

   ```bash
   git clone --branch master --single-branch https://github.com/apache/hugegraph-toolchain.git
   cd hugegraph-toolchain
   ```

1. <span id="prepare-server-sdk"></span>**Prepare the matching Server SDK.**

   Run the script below to download Server source and install the SDK into an isolated Maven repository:

   ```bash
   java -version
   mvn -version
   server_commit=$(python3 - <<'PY'
   import runpy
   print(runpy.run_path(
       "hugegraph-client/assembly/travis/verify_candidate_image_sdk.py"
   )["COMMIT"])
   PY
   )
   candidate_dir=$(mktemp -d)
   mkdir -p "$candidate_dir/m2"
   bash hugegraph-client/assembly/travis/install-candidate-sdk.sh \
     "$server_commit" "$candidate_dir/server" "$candidate_dir/m2"
   ```

   Both version checks must report JDK 17. The helper requires the full Server source identity selected by Toolchain;
   passing `master` is rejected. This keeps the installed SDK and package verification consistent.
   Keep `candidate_dir` for the following commands. See the
   [Java 17 migration guide](https://github.com/apache/hugegraph-toolchain/blob/master/docs/java17-migration.md) for other build modes.

1. **Package Tools**

   ```bash
   mvn -Dmaven.repo.local="$candidate_dir/m2" \
     -Dhugegraph.version=1.8.0 -Dsdk.validation.mode=candidate \
     package -pl hugegraph-tools -am -DskipTests -Dmaven.javadoc.skip=true -ntp
   cd hugegraph-tools/apache-hugegraph-tools-*
   bin/hugegraph help
   ```
{.steps}

These are development packages, not an ASF release. Keep the isolated SDK repository while building other Toolchain modules or applications using them.
The master build directory does not contain `incubating`.

### 3 How to use

#### 3.1 Function overview

From the extracted or generated Tools directory, run `bin/hugegraph help` for the command list,
or `bin/hugegraph help <sub-command>` for one command. The commands cover these tasks.

- Graph management type, graph-mode-set, graph-mode-get, graph-list, graph-get, graph-clear, graph-create, graph-clone and graph-drop
- Asynchronous task management type, task-list, task-get, task-delete, task-cancel and task-clear
- Gremlin type, gremlin-execute and gremlin-schedule
- Backup/Restore type, backup, restore, migrate, schedule-backup and dump
- Authentication data backup/restore type, auth-backup and auth-restore
- Legacy Server/Studio deployment, deploy, clear, start-all and stop-all

```bash
Usage: hugegraph [options] [command] [command options]
```

##### 3.2 [options]-Global Variable

Set these global connection options on the command line or through the environment variables below.

- `--graph` selects the graph, default `hugegraph`.
- `--url` sets the Server address, default `http://127.0.0.1:8080`.
- `--user` supplies the username when Server authentication is enabled.
- `--password` supplies that user's password.
- `--timeout` sets the connection timeout, default 30 seconds.
- `--trust-store-file` selects the HTTPS truststore. An empty value uses the built-in `conf/hugegraph.truststore`.
- `--trust-store-password` supplies its password. An empty value uses the built-in truststore password.
- `--throw-mode` defaults to `false`, which prints errors and exits. Set it to `true` to throw exceptions, mainly for tests.

> The scheme in `--url` selects the protocol. Use `https://...` for HTTPS and set truststore options only with that scheme.
> Supply both `--user` and `--password`, or omit both.

Use `export` to set an option for the current shell and the commands launched from it.


| Global Variable                   | Environment Variable           | Example                                            |
|------------------------|--------------------------------|----------------------------------------------------|
| --url                  | HUGEGRAPH_URL                  | export HUGEGRAPH_URL=http://127.0.0.1:8080         |
| --graph                | HUGEGRAPH_GRAPH                | export HUGEGRAPH_GRAPH=hugegraph                   |
| --user                 | HUGEGRAPH_USERNAME             | export HUGEGRAPH_USERNAME=admin                    |
| --password             | HUGEGRAPH_PASSWORD             | export HUGEGRAPH_PASSWORD=test                     |
| --timeout              | HUGEGRAPH_TIMEOUT              | export HUGEGRAPH_TIMEOUT=30                        |
| --trust-store-file     | HUGEGRAPH_TRUST_STORE_FILE     | export HUGEGRAPH_TRUST_STORE_FILE=/tmp/trust-store |
| --trust-store-password | HUGEGRAPH_TRUST_STORE_PASSWORD | export HUGEGRAPH_TRUST_STORE_PASSWORD=xxxx         |
{.td-table--wide .expand}

Both forms below count vertices in the same graph; choose either form. The example uses a local Server without authentication.
For an authenticated Server, also provide the username and password described above.

```bash {tab="CLI flags"}
./bin/hugegraph --url http://127.0.0.1:8080 --graph hugegraph gremlin-execute --script 'g.V().count()'
```

```bash {tab="Environment variables"}
export HUGEGRAPH_URL=http://127.0.0.1:8080
export HUGEGRAPH_GRAPH=hugegraph
./bin/hugegraph gremlin-execute --script 'g.V().count()'
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
- graph-clone, create a graph using an existing graph’s configuration; Schema and data are not copied
  - --name or -n, optional, the name of the cloned graph, default is g
  - --clone-graph-name, optional, the name of the source graph to clone from, default is hugegraph
- graph-drop, drop a graph (different from graph-clear, this completely removes the graph)
  - --confirm-message or -c, required, confirmation message "I'm sure to drop the graph", including double quotes

> graph-create, graph-clone, graph-clear and graph-drop raise --timeout to at least 300 seconds.

> Before restoring into a new graph, set its mode to `RESTORING`. To merge into an existing graph, use `MERGING`.

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
  > `restore` accepts backups made with `--format json`.
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
  > [!WARNING]
  > **Backup & Migration Failures**: If any vertex or edge data page fails after configured retries, the backup halts immediately with an error, and `migrate`
  > does not proceed to restore the target graph. Partial backup files and shard diagnostics (files ending in `_shards`, such as `vertex_failed_shards` or
  > `edge_timeout_shards`) are preserved in `./logs` for root-cause diagnosis.
  > The backup directory (`--directory`) and log directory (`--log`, default `./logs`) are independent. Note that task initialization automatically clears
  > files ending in `_shards` from the selected log directory. Before retrying, copy diagnostic files elsewhere or select a new `--log` directory as well as
  > a clean `--directory`.
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

Note: These deployment commands only apply to legacy versions (Server 0.6.1~0.10.4 and Studio 0.6.1~0.10.0),
and do not support current HugeGraph Server or Hubble.
For modern deployments, follow [Server Quick Start](/docs/quickstart/hugegraph/hugegraph-server/)
and [Hubble Quick Start](/docs/quickstart/toolchain/hugegraph-hubble/).
The options below are retained only for maintaining legacy environments.

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

> `deploy -u` overrides the download URL and saves it in `~/hugegraph-download-url-prefix`.
> Later runs without `-u` reuse the saved URL. Without either setting, the script uses `https://github.com/hugegraph`.

##### 3.9 Specific command parameters

Use the help shipped with your installed version to check supported commands and defaults:

```bash
./bin/hugegraph help
./bin/hugegraph help backup
./bin/hugegraph help graph-clone
```

Place global options such as `--url` and `--graph` before the command, and its own options after it.
For example, use `./bin/hugegraph --graph hugegraph backup --directory ./backup`.

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

> [!NOTE]
> If a data page fails during the backup phase of migration, `migrate` terminates immediately and leaves the target graph untouched.
> Inspect shard diagnostic files in `./logs/` (`*_shards`) and ensure a clean directory is provided before retrying.
