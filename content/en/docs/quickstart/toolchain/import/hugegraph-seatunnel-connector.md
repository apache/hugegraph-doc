---
title: "Import Graph Data with SeaTunnel Sink"
linkTitle: "Import graph data with SeaTunnel Sink"
weight: 2
aliases:
  - /docs/quickstart/toolchain/hugegraph-seatunnel-connector/
---

SeaTunnel connects data sources such as databases and Kafka to HugeGraph. The connector has two parts: **Source reads data and Sink writes data**<sup>[1][2]</sup>, with SeaTunnel transform components available between them. To export or migrate data from HugeGraph, see the [SeaTunnel Source export and migration guide](/docs/quickstart/toolchain/export-migration/hugegraph-seatunnel-source/).

> **Version requirement: This guide targets SeaTunnel [3.0+](https://github.com/apache/seatunnel/tree/3.0.0-release).** All examples use `mappings`

[![Loader imports data directly with graph mappings; SeaTunnel 3.0+ combines Source, Transform, and Sink, and both support JDBC, Kafka, and graph data](/docs/images/seatunnel/seatunnel-vs-loader-en.png)](/docs/images/seatunnel/seatunnel-vs-loader-en.png)

Click a diagram to view the original size.

## 1 Loader, Tools, and SeaTunnel

[HugeGraph-Loader](/docs/quickstart/toolchain/hugegraph-loader/) is suited to direct imports from common data sources. [HugeGraph-Tools](/docs/quickstart/toolchain/hugegraph-tools/) focuses on standalone graph management, backup, and export. SeaTunnel organizes a job as **Source → Transform → Sink**, so you can reuse existing connectors, transforms, and data pipelines.

> **Table legend**
>
> ✅ Supported natively; ⚠️ conditional support or requires an extra component/external platform; ❌ not provided

| Comparison | Loader | Tools | SeaTunnel |
| --- | --- | --- | --- |
| Task coverage | ✅ Direct graph imports | ✅ Backup, restore, and export | ✅ Import, export, and migration with composable Source, Transform, and Sink stages |
| Job configuration | JSON mapping file describing the source, vertices, and edges | Command-line options and operations | [HOCON job file](https://seatunnel.apache.org/docs/introduction/concepts/config/)<sup>[3]</sup> combining Source, Transform, and Sink |
| Default deployment | ✅ Standalone CLI; ⚠️ Spark Loader can extend it | ✅ Standalone CLI | ✅ Standalone; ✅ distributed |
| Execution engine | ⚠️ Mainly CLI; Spark Loader is a separate extension | ❌ Does not provide a Spark/Flink execution engine | ✅ HugeGraph Source and Sink support Zeta, Spark, and Flink<sup>[1][2][7][8][9][10]</sup> |
| Frontend and observability | ❌ No built-in frontend; inspect CLI logs | ❌ No built-in frontend; inspect CLI logs | ✅ Built-in Web UI job panel for task status and runtime information |
| Input and output | ⚠️ Focused on graph imports and common files, JDBC, Kafka, and similar sources | ⚠️ Focused on graph data and backup files in common storage | ✅ Dozens of connectors, including JDBC, Kafka, and SQL-CDC |
| Scheduling and resource management | ❌ No unified cross-task scheduling or resource allocation | ❌ No unified cross-task scheduling or resource allocation | ⚠️ Can integrate with DolphinScheduler for scheduling and task management |
| Simplicity | ✅ Focused and simple; a future binary CLI will make quick use easier | ✅ Direct commands for standalone operations | ⚠️ More runtime components, suited to long-lived data pipelines |
| High-throughput import | ✅ Supports bypass-server and other optimizations; measured peaks can reach 1-2 million records/s with specific backends and hardware, so benchmark the actual setup | ⚠️ Focuses on backup and export rather than bulk-import throughput | ✅ Scales throughput through parallelism, distributed engines, and connectors |

SeaTunnel covers Loader's graph-import and Tools' export and migration scenarios in one expandable pipeline, and it also supports SQL-CDC and dozens of input and output types. Loader and Tools normally run on one machine, while SeaTunnel supports both standalone and distributed deployments and scales with data and task volume. Tools' `schedule-backup` can create a crontab entry, but it does not provide unified workflow orchestration and resource management.

> **Existing Spark/Flink daily jobs**
>
> Both HugeGraph Source and Sink list SeaTunnel Engine (Zeta), Spark, and Flink as supported engines in SeaTunnel 3.0.0-release. If you express the daily job as a SeaTunnel job and submit it to that engine, records can move directly from Source to Transform to Sink without an intermediate file. If you keep the existing Spark/Flink DAG, SeaTunnel does not automatically take over its in-memory DataFrame or stream. Adapt it into a SeaTunnel job or expose the data through a Source connector

Loader and Tools are focused, direct, and quick to start. Use Loader for a direct graph import; use Tools for backup, restore, export, or daily operations. If a SeaTunnel job already exists, adding HugeGraph to that pipeline is usually simpler. For higher import throughput, Loader's bypass-server path and other import optimizations are a better fit; measured peaks of 1-2 million records/s require a specific backend, data set, and hardware configuration and are not a general performance guarantee. For new SeaTunnel jobs, use [3.0+](https://github.com/apache/seatunnel/tree/3.0.0-release) and `mappings`. Recheck the connector configuration when using another version.

## 2 Prepare the environment

### 2.1 Get SeaTunnel 3.0+

The SeaTunnel 3.0+ setup guide lists JDK 8 and JDK 11 as supported. This guide uses JDK 11 and sets `JAVA_HOME`. Clone the [SeaTunnel 3.0+](https://github.com/apache/seatunnel/tree/3.0.0-release)<sup>[4]</sup> branch and build a distribution by following the upstream [development setup guide](https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/developer/setup.md)<sup>[5]</sup>:

```bash
git clone --branch 3.0.0-release https://github.com/apache/seatunnel.git
cd seatunnel
./mvnw clean package -pl seatunnel-dist -am -Dmaven.test.skip=true
```

Extract the binary package from `seatunnel-dist/target/`. Run the remaining commands from the extracted SeaTunnel installation directory. When updating the feature set, switch to another version as needed. Keep the engine and connector plugins from the same build, and do not mix different plugin versions.

This guide uses the bundled **Zeta engine in local mode**<sup>[6][7]</sup>. Check that `connectors/` contains HugeGraph and the JDBC or Kafka connector required by each example<sup>[11][12]</sup>. If a custom build does not include them, add the plugins produced by that same build. The JDBC examples also require the MySQL driver JAR in `lib/`, with driver class `com.mysql.cj.jdbc.Driver`.

### 2.2 Prepare HugeGraph and data sources

Start [HugeGraph Server](/docs/quickstart/hugegraph/hugegraph-server/) and create a graph for testing. The examples use the `hugegraph` graph in the `DEFAULT` graph space. Adjust these names to match the server configuration; graph space names are case-sensitive. If authentication is enabled, provide `username` and `password` in the HugeGraph Source and Sink configurations.

The following graph model is shared by the JDBC and Kafka examples. `mappings` creates missing PropertyKey, VertexLabel, and EdgeLabel definitions by default; existing schema definitions must be compatible.

| Graph element | Name and properties |
| --- | --- |
| Properties | `name` is Text; `age` and `since` are Int |
| Vertex | `person`, primary key `name`, properties `name` and `age` |
| Edge | `knows`, from `person` to `person`, property `since` |

The `mysql`, `kafka`, and `hugegraph` host names in the examples are placeholders. Replace them with addresses reachable from the SeaTunnel runtime. Inside a container, `127.0.0.1` points to that container; services on the same Docker network can use their service names. Set `host` to a host name or IP address, and set the port separately.

## 3 Import from a relational database (sql2graph)

Use two jobs for this import: write the `person` table as vertices first, then write the `knows` table as edges. Both edge endpoints will already exist when the edge job runs.

[![The person table creates marko and vadas vertices; the knows table creates a directed edge with since 2010 through endpoint fields](/docs/images/seatunnel/seatunnel-records-to-graph-en.png)](/docs/images/seatunnel/seatunnel-records-to-graph-en.png)

### 3.1 Import vertices

Prepare the sample data in the MySQL `demo` database and grant the configured account read access:

```sql
CREATE TABLE person (
  name VARCHAR(64) PRIMARY KEY,
  age INT NOT NULL
);
INSERT INTO person VALUES ('marko', 29), ('vadas', 27);
```

Save the following as `config/sql2graph-person.conf` and replace the database user name and password:

```hocon
env {
  job.mode = "BATCH"
}

source {
  Jdbc {
    url = "jdbc:mysql://mysql:3306/demo?useSSL=false&serverTimezone=UTC"
    driver = "com.mysql.cj.jdbc.Driver"
    username = "seatunnel"
    password = "change_me"
    query = "SELECT name, age FROM person ORDER BY name"
  }
}

sink {
  HugeGraph {
    host = "hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
    batch_failure_fallback = false
    mappings = [
      {
        type = "VERTEX"
        label = "person"
        idStrategy = "PRIMARY_KEY"
        idFields = ["name"]
        properties = ["name", "age"]
      }
    ]
  }
}
```

```bash
./bin/seatunnel.sh --config ./config/sql2graph-person.conf -m local
```

Check the result in Hubble or Gremlin. You should find `marko` and `vadas` with their ages:

```groovy
g.V().hasLabel('person').valueMap('name', 'age')
```

`idFields = ["name"]` uses the name to generate the primary key. Importing the same `name` again writes to the same vertex. `properties` lists the source fields to write.

### 3.2 Import edges

Prepare the relation table. Its two endpoint fields correspond to `person.name` from the vertex job:

```sql
CREATE TABLE knows (
  source_name VARCHAR(64) NOT NULL,
  target_name VARCHAR(64) NOT NULL,
  since INT NOT NULL
);
INSERT INTO knows VALUES ('marko', 'vadas', 2010);
```

<details>
<summary>Expand the configuration and save it as config/sql2graph-knows.conf</summary>

```hocon
env {
  job.mode = "BATCH"
}

source {
  Jdbc {
    url = "jdbc:mysql://mysql:3306/demo?useSSL=false&serverTimezone=UTC"
    driver = "com.mysql.cj.jdbc.Driver"
    username = "seatunnel"
    password = "change_me"
    query = "SELECT source_name, target_name, since FROM knows ORDER BY source_name, target_name"
  }
}

sink {
  HugeGraph {
    host = "hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
    batch_failure_fallback = false
    check_vertex = true
    mappings = [
      {
        type = "EDGE"
        label = "knows"
        sourceConfig = {
          label = "person"
          idFields = ["source_name"]
        }
        targetConfig = {
          label = "person"
          idFields = ["target_name"]
        }
        fieldMapping = {
          source_name = "name"
          target_name = "name"
        }
        properties = ["since"]
      }
    ]
  }
}
```

</details>

After the vertex job succeeds, run the edge job:

```bash
./bin/seatunnel.sh --config ./config/sql2graph-knows.conf -m local
```

The following query should return a `knows` edge from `marko` to `vadas` with `since` set to `2010`:

```groovy
g.V().has('person', 'name', 'marko').outE('knows').where(inV().has('name', 'vadas')).valueMap()
```

`sourceConfig` and `targetConfig` identify the endpoint fields. `fieldMapping` maps them to the vertex primary key `name`, and `properties = ["since"]` writes only the edge property. The example enables `check_vertex = true` and disables per-record fallback after a batch failure (`batch_failure_fallback = false`), so a missing endpoint or write failure causes the job to fail.

If the relation table has only numeric foreign keys while the graph uses names as primary keys, join the names in SQL before passing the records to the Sink. See [MySQL CDC Source](https://seatunnel.apache.org/docs/connectors/source/MySQL-CDC/)<sup>[13]</sup> for MySQL CDC integration.

## 4 Import from Kafka (kafka2graph)

Kafka is useful for a continuous stream of events. Create the `user-events` topic and publish the following JSON message. Each message becomes one `person` vertex:

```json
{"name":"marko","age":29}
```

Save the following as `config/kafka2graph.conf`:

```hocon
env {
  job.mode = "STREAMING"
  checkpoint.interval = 10000
  sink.flush.interval = 5000
}

source {
  Kafka {
    bootstrap.servers = "kafka:9092"
    topic = "user-events"
    consumer.group = "hugegraph-import"
    start_mode = "earliest"
    format = "json"
    schema = {
      fields = {
        name = "string"
        age = "int"
      }
    }
  }
}

sink {
  HugeGraph {
    host = "hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
    batch_failure_fallback = false
    mappings = [
      {
        type = "VERTEX"
        label = "person"
        idStrategy = "PRIMARY_KEY"
        idFields = ["name"]
        properties = ["name", "age"]
      }
    ]
  }
}
```

```bash
./bin/seatunnel.sh --config ./config/kafka2graph.conf -m local
```

Use the Gremlin query from section 3.1 to check the data. The streaming job keeps running. `checkpoint.interval` saves job state every 10 seconds, while `sink.flush.interval` asks Zeta to flush every 5 seconds so a small number of messages does not wait for a full batch.

HugeGraph Sink writes with **at-least-once** semantics, so recovery can replay records. `PRIMARY_KEY` sends the same `name` to the same vertex, but it does not make every update exactly-once. Scheduled flushing is provided by Zeta and does not apply to Spark or Flink engines.

## 5 Common configuration and troubleshooting

The following table applies to the SeaTunnel 3.0+ version used by this guide:

| Configuration | Purpose |
| --- | --- |
| `host`, `port` | Set the HugeGraph host and port |
| `graph_name`, `graph_space` | Select an existing graph and graph space |
| `mappings` | Define how input fields become vertices or edges |
| `properties` | List the source fields written by each mapping |
| `schema_save_mode` | `mappings` creates missing schema by default; existing schema must still be compatible |
| `batch_size` | Number of records per batch; default 500 |
| `env.sink.flush.interval` | Zeta scheduled flush interval in milliseconds |
| `check_vertex` | Check edge endpoints; the edge job in this guide sets it to `true` |
| [`batch_failure_fallback`](https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/sink/HugeGraph.md)<sup>[2]</sup> | Defaults to `true`, so a failed batch falls back to record-by-record retries, capped by `max_insert_errors`; the examples explicitly set `false` so a batch failure stops the job |
| `max_insert_errors` | Number of failed records that record-by-record fallback may skip; default `500`, `-1` for unlimited, and only applies when `batch_failure_fallback` is enabled |

Use these checks when a job fails:

- **`mappings` is unknown or HugeGraph Source is missing:** Check that the engine and HugeGraph connector come from the same SeaTunnel 3.0+ build.
- **Connection failure:** Check the host, port, graph space, authentication details, and whether the SeaTunnel runtime can reach the service.
- **Schema incompatibility:** Check the ID strategy, property types, and edge endpoints. Automatic creation does not change an existing `PRIMARY_KEY` label into `CUSTOMIZE_STRING`.
- **Small Kafka batches do not appear promptly:** Confirm that the job uses Zeta and set `sink.flush.interval` in `env`. In this version, `batch_interval_ms` is retained only for compatibility and cannot replace it.

## 6 Choosing a tool

Choose a tool based on the work to complete. Use [Tools](/docs/quickstart/toolchain/hugegraph-tools/) for graph management, Gremlin, backup, or cloning. Use [Loader](/docs/quickstart/toolchain/hugegraph-loader/) for a direct graph import. Choose SeaTunnel when you need to reuse a Source, Transform, and Sink pipeline. For SeaTunnel graph reads and migrations, prepare the environment using the SeaTunnel 3.0+ version used by this guide.

[![Choosing a tool: Tools for graph management, Loader for direct imports, and SeaTunnel for reusable data pipelines](/docs/images/seatunnel/seatunnel-tool-choice-en.png)](/docs/images/seatunnel/seatunnel-tool-choice-en.png)

## 7 References

**HugeGraph connectors**

<p><sup>[1]</sup> <a href="https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/source/HugeGraph.md">HugeGraph Source</a><br>
<sup>[2]</sup> <a href="https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/sink/HugeGraph.md">HugeGraph Sink</a></p>

**Configuration and deployment**

<p><sup>[3]</sup> <a href="https://seatunnel.apache.org/docs/introduction/concepts/config/">HOCON job configuration</a><br>
<sup>[4]</sup> <a href="https://github.com/apache/seatunnel/tree/3.0.0-release">SeaTunnel 3.0.0-release branch</a><br>
<sup>[5]</sup> <a href="https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/developer/setup.md">SeaTunnel development setup</a><br>
<sup>[6]</sup> <a href="https://seatunnel.apache.org/docs/getting-started/locally/deployment/">SeaTunnel local deployment</a></p>

**Execution engines**

<p><sup>[7]</sup> <a href="https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/engines/overview.md">SeaTunnel Engine Overview</a><br>
<sup>[8]</sup> <a href="https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/engines/spark.md">SeaTunnel Spark Engine</a><br>
<sup>[9]</sup> <a href="https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/engines/flink.md">SeaTunnel Flink Engine</a><br>
<sup>[10]</sup> <a href="https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/introduction/concepts/connector-v2-features.md">Connector V2 multi-engine support</a></p>

**Data source connectors**

<p><sup>[11]</sup> <a href="https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/source/Jdbc.md">JDBC Source</a><br>
<sup>[12]</sup> <a href="https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/source/Kafka.md">Kafka Source</a><br>
<sup>[13]</sup> <a href="https://seatunnel.apache.org/docs/connectors/source/MySQL-CDC/">MySQL CDC Source</a></p>

**Legacy compatibility**

<p><sup>[14]</sup> <a href="https://github.com/apache/seatunnel/blob/2.3.13/docs/en/connectors/sink/HugeGraph.md">SeaTunnel 2.3.13 HugeGraph Sink</a></p>

> **Legacy version note**
>
> This guide targets SeaTunnel 3.0+. Its Source, `mappings`, and graph migration examples do not apply to 2.3.13. That legacy version provides only the HugeGraph Sink, uses `schema_config`, and requires the graph schema to be created in advance. If you must use 2.3.13, follow the [official Sink documentation](https://github.com/apache/seatunnel/blob/2.3.13/docs/en/connectors/sink/HugeGraph.md)<sup>[14]</sup> instead of copying this guide's configuration
