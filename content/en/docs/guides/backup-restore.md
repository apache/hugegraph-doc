---
title: "Backup and Restore"
linkTitle: "Backup Restore"
weight: 5
---

## Description

Backup exports a graph's schema, vertices, and edges as JSON data. Restore imports that data into a target graph.
These [HugeGraph-Tools](/docs/quickstart/toolchain/hugegraph-tools) commands support migration, recovery after an upgrade, and graph merging.

#### Backup

Backup runs in any graph mode. Pause source writes before exporting so schema, vertices, and edges remain consistent.
The paginated read APIs do not provide a transaction snapshot spanning the entire backup.
`backup -t all` covers graph schema and data, excluding deployment configuration and user permissions.

#### Restore

Choose a restore mode based on the target graph. Use `NONE` for normal operations. `LOADING` cannot be used with `restore`.

| Target | Mode | Schema IDs | Vertex and edge IDs |
|---|---|---|---|
| New graph without schema or data | `RESTORING` | Use IDs from the backup | Use IDs from the backup |
| Existing graph to merge into | `MERGING` | Use target schema IDs, creating schema if needed | Some IDs change with target schema; see below |

In `MERGING`, Tools recomputes `PRIMARY_KEY` vertex IDs using the target label IDs and updates connected edge endpoints and IDs.
It retains `AUTOMATIC` and custom vertex IDs. The merge reuses schema with matching names.
Check that their definitions are compatible and that retained vertex IDs do not conflict.
It does not resolve arbitrary schema or data conflicts. Test on a separate target before merging production data.

## Instructions

Prepare [HugeGraph-Tools](/docs/quickstart/toolchain/hugegraph-tools) compatible with your Server version, then run the commands from the Tools root directory.
This example restores a source graph on port `8080` to an empty target on port `8081`.
Both Servers and the target graph must already exist and be running. Adjust the addresses and graph names for your deployment.

```bash
SOURCE_URL=http://127.0.0.1:8080
TARGET_URL=http://127.0.0.1:8081
SOURCE_GRAPH=hugegraph
TARGET_GRAPH=hugegraph
BACKUP_DIR="$PWD/data/hugegraph-backup"
```

With authentication enabled, add `--user <user> --password <password>` before the subcommand in each Tools command.
The account needs the relevant graph access and graph-mode management permissions.
See the [Tools reference](/docs/quickstart/toolchain/hugegraph-tools) for connection and credential options.

#### Backup

Pause source writes, then export all schema, vertices, and edges.

```bash
bin/hugegraph --url "$SOURCE_URL" --graph "$SOURCE_GRAPH" \
  backup -t all -d "$BACKUP_DIR"
```

An explicit `-d` is the backup directory itself; the graph name is not appended. Use a separate directory for each backup to avoid mixing old files.
Retain the complete directory, including compressed files. Restore reads the JSON backup formats supported by Tools.

#### Restore

This sequence uses `RESTORING`. To merge, use `MERGING` after the compatibility checks above.
Pause application writes to the target during maintenance.


1. <span id="step-1-view-and-set-graph-mode"></span>**Record the original mode, then switch it.**

   ```bash
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" graph-mode-get
   ORIGINAL_MODE=NONE
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" \
     graph-mode-set -m RESTORING
   ```

   A graph in normal use should be in `NONE` mode. Set `ORIGINAL_MODE` to the value returned by the query, such as `NONE` below.
   If another task is using `RESTORING`, `MERGING`, or `LOADING`, coordinate with that task before changing its mode.

1. <span id="step-2-restore-data"></span>**Restore the data.**

   ```bash
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" \
     restore -t all -d "$BACKUP_DIR"
   ```

   Check that the command succeeds and inspect its results for each data type. On failure, retain the backup and logs and inspect partial writes to the target.
   Restore does not roll back completed writes or reset the graph mode automatically. Do not blindly repeat it on a partially restored graph.

1. <span id="step-3-restoring-graph-mode"></span>**Restore the original mode.**

   Reset the mode using `ORIGINAL_MODE`, recorded in the first step.

   ```bash
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" graph-mode-set -m "$ORIGINAL_MODE"
   bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" graph-mode-get
   ```

   Handle the graph mode after either success or failure. After a failure, retain the evidence and reset the mode, but keep application writes paused until the
   target has been checked or prepared again.
{.steps}

After resetting the mode, compare vertex and edge counts on both graphs.

```bash
bin/hugegraph --url "$SOURCE_URL" --graph "$SOURCE_GRAPH" gremlin-execute --script 'g.V().count()'
bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" gremlin-execute --script 'g.V().count()'
bin/hugegraph --url "$SOURCE_URL" --graph "$SOURCE_GRAPH" gremlin-execute --script 'g.E().count()'
bin/hugegraph --url "$TARGET_URL" --graph "$TARGET_GRAPH" gremlin-execute --script 'g.E().count()'
```

Each pair of counts should match. Use the [Schema API](/docs/clients/restful-api/schema/) to compare property keys, vertex labels, edge labels, and indexes.
Also inspect business properties and edge endpoints. Check original IDs for `RESTORING` and the changes in the table for `MERGING`.
Matching counts alone do not prove that the business data is complete.

#### help

See the [Tools reference](/docs/quickstart/toolchain/hugegraph-tools) for compression, concurrency, logs, and selecting data types.
Test backup compatibility with the target version before recovery. Matching command names do not guarantee cross-version compatibility.

## API description for Backup/Restore usage and implementation

#### Backup

Backup exports data through the schema, vertex, and edge list GET APIs.

#### Restore

Restore imports data through the schema, vertex, and edge creation APIs. See the [mode table](#restore) for ID behavior.
`RESTORING` accepts schema IDs; `MERGING` does not. Both accept retained `AUTOMATIC` vertex IDs.
Normal `NONE` mode does not accept these ID settings required for restore.

##### View the mode of a graph

When authentication is enabled, graph read permission is required (`space_member` or the graph owner).

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

Valid graph modes are `NONE`, `RESTORING`, `MERGING`, and `LOADING`.

##### Set the mode of a graph

When authentication is enabled, graph-space management permission (`space`) is required; administrators can satisfy it through permission inheritance.

###### Method & Url

```text
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/mode
```

###### Request Body

```text
"RESTORING"
```

Valid graph modes are `NONE`, `RESTORING`, `MERGING`, and `LOADING`.

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
