---
title: "Backup and Restore"
linkTitle: "Backup Restore"
weight: 5
---

## Description

Backup and Restore are functions of backup map and restore map. The data backed up and restored includes metadata (schema) and graph data (vertex and edge).

#### Backup

Export the metadata and graph data of a graph in the HugeGraph system in JSON format.

#### Restore

Re-import the data in JSON format exported by Backup to a graph in the HugeGraph system.

Restore has two modes:

- In Restoring mode, the metadata and graph data exported by Backup are restored to the HugeGraph system intact. It can be used for graph backup and recovery, and the general target graph is a new graph (without metadata and graph data). for example:
  - System upgrade, first back up the map, then upgrade the system, and finally restore the map to the new system
  - Graph migration, from a HugeGraph system, use the Backup function to export the graph, and then use the Restore function to import the graph into another HugeGraph system
- In the Merging mode, the metadata and graph data exported by Backup are imported into another graph that already has metadata or graph data. During the process, the ID of the metadata may change, and the IDs of vertices and edges will also change accordingly.
  - Can be used to merge graphs

## Instructions

You can use [hugegraph-tools](/docs/quickstart/toolchain/hugegraph-tools) to backup and restore the graph.

#### Backup

```bash
bin/hugegraph backup -t all -d data
```

This command backs up all the metadata and graph data of the hugegraph graph of http://127.0.0.1 to the data directory.

> Backup works fine in all three graph modes

#### Restore

Restore has two modes: RESTORING and MERGING. Before backup, you must first set the graph mode according to your needs.

##### Step 1: View and set graph mode

```bash
bin/hugegraph graph-mode-get
```
This command is used to view the current graph mode, including: NONE, RESTORING, MERGING.

```bash
bin/hugegraph graph-mode-set -m RESTORING
```

This command is used to set the graph mode. Before Restore, it can be set to RESTORING or MERGING mode. In the example, it is set to RESTORING.

##### Step 2: Restore data

```bash
bin/hugegraph restore -t all -d data
```
This command re-imports all metadata and graph data in the data directory to the hugegraph graph at http://127.0.0.1.

##### Step 3: Restoring Graph Mode

```bash
bin/hugegraph graph-mode-set -m NONE
```
This command is used to restore the graph mode to NONE.

So far, a complete graph backup and graph recovery process is over.

#### help

For detailed usage of backup and restore commands, please refer to the [hugegraph-tools documentation](/docs/quickstart/toolchain/hugegraph-tools).

## API description for Backup/Restore usage and implementation

#### Backup

Backup uses the corresponding list(GET) API export of metadata and graph data, and no new API is added.

#### Restore

Restore uses the corresponding create(POST) API imports for metadata and graph data, and does not add new APIs.

There are two different modes for Restore: Restoring and Merging. In addition, there is a regular mode of NONE (default), the differences are as follows:

- In None mode, the writing of metadata and graph data is normal, please refer to the function description. special:
    - ID is not allowed when metadata (schema) is created
    - Graph data (vertex) is not allowed to specify an ID when the id strategy is Automatic
- Restoring mode, restoring to a new graph, in particular:
    - ID is allowed to be specified when metadata (schema) is created
    - Graph data (vertex) allows specifying an ID when the id strategy is Automatic
- Merging mode, merging into a graph with existing metadata and graph data, in particular:
    - ID is not allowed when metadata (schema) is created
    - Graph data (vertex) allows specifying an ID when the id strategy is Automatic


Normally, the graph mode is None. When you need to restore the graph, you need to temporarily change the graph mode to Restoring mode or
Merging mode as needed, and when the Restore is completed, restore the graph mode to None.

The implemented RESTful API for setting graph mode is as follows:

##### View the schema of a graph. **This operation requires administrator privileges**

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

> Legal graph modes include: NONE, RESTORING, MERGING

##### Set the mode of a graph. ""This operation requires administrator privileges**

###### Method & Url

```
PUT http://localhost:8080/graphs/{graph}/mode
```

###### Request Body

```
"RESTORING"
```

> Legal graph modes include: NONE, RESTORING, MERGING

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
