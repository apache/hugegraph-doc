---
title: "Import and Migrate Graph Data with SeaTunnel"
linkTitle: "SeaTunnel Data Integration"
weight: 5
---

SeaTunnel connects data sources such as databases and Kafka to HugeGraph. It can also migrate vertices and edges between two HugeGraph graphs. The connector has two parts: **Source reads data and Sink writes data**, with SeaTunnel transform components available between them.

> **Version requirement: This guide targets SeaTunnel [3.0+](https://github.com/apache/seatunnel/tree/3.0.0-release).** All examples use `mappings`.

[![Loader imports data directly with graph mappings; SeaTunnel 3.0+ combines Source, Transform, and Sink, and both support JDBC, Kafka, and graph data](/docs/images/seatunnel/seatunnel-vs-loader-en.png)](/docs/images/seatunnel/seatunnel-vs-loader-en.png)

Click a diagram to view the original size.

## 1 Loader vs SeaTunnel and version requirements

[HugeGraph-Loader](/docs/quickstart/toolchain/hugegraph-loader/) is designed for graph data imports. Its input sources and graph mappings describe which records become vertices or edges. SeaTunnel organizes a job as **Source → Transform → Sink**, so you can reuse existing connectors, transforms, and data pipelines.

| Comparison | HugeGraph-Loader | SeaTunnel |
| --- | --- | --- |
| Job configuration | JSON mapping file describing the source, vertices, and edges | [HOCON job file](https://seatunnel.apache.org/docs/introduction/concepts/config/) combining Source, Transform, and Sink |
| Best for | Directly importing data into HugeGraph when field and value mappings are enough | Connecting HugeGraph to an existing SeaTunnel pipeline or reusing its connectors and transforms |
| Runtime setup | Use Loader; Spark Loader and Flink CDC integrations are also available | Prepare matching engine and connector versions; this guide uses Zeta in local mode |

**Choose by the work you need to complete, not only by the data source or batch/stream mode.** Both tools support JDBC, Kafka, and graph data. Loader also provides field/value mappings and Spark or Flink CDC integrations. Use Loader for a direct graph import; if a SeaTunnel job already exists, adding HugeGraph to that pipeline is usually simpler.

For new SeaTunnel jobs, use [3.0+](https://github.com/apache/seatunnel/tree/3.0.0-release) and `mappings`. Recheck the connector configuration when using another version.

## 2 Prepare the environment

### 2.1 Get SeaTunnel 3.0+

The SeaTunnel 3.0+ setup guide lists JDK 8 and JDK 11 as supported. This guide uses JDK 11 and sets `JAVA_HOME`. Clone the [SeaTunnel 3.0+](https://github.com/apache/seatunnel/tree/3.0.0-release) branch and build a distribution by following the upstream [development setup guide](https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/developer/setup.md):

```bash
git clone --branch 3.0.0-release https://github.com/apache/seatunnel.git
cd seatunnel
./mvnw clean package -pl seatunnel-dist -am -Dmaven.test.skip=true
```

Extract the binary package from `seatunnel-dist/target/`. Run the remaining commands from the extracted SeaTunnel installation directory. When updating the feature set, switch to another version as needed. Keep the engine and connector plugins from the same build, and do not mix different plugin versions.

This guide uses the bundled **Zeta engine in local mode**. Check that `connectors/` contains HugeGraph and the JDBC or Kafka connector required by each example. If a custom build does not include them, add the plugins produced by that same build. The JDBC examples also require the MySQL driver JAR in `lib/`, with driver class `com.mysql.cj.jdbc.Driver`.

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

If the relation table has only numeric foreign keys while the graph uses names as primary keys, join the names in SQL before passing the records to the Sink. See [MySQL CDC Source](https://seatunnel.apache.org/docs/connectors/source/MySQL-CDC/) for MySQL CDC integration.

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

## 5 Migrate a HugeGraph graph (graph2graph)

The following example migrates `person` vertices and `knows` edges from a source graph. Use a separate target graph. This section uses `CUSTOMIZE_STRING` to preserve vertex IDs. Do not reuse the `person` label created earlier with `PRIMARY_KEY`.

These two jobs migrate only the selected labels and properties. They do not copy every source schema setting, such as indexes and TTLs. Pause writes to the source graph during the migration so both jobs read a consistent point in time. Afterward, compare vertex and edge counts and sample properties.

[![Regenerating a primary key can change 1:marko to 2:marko; CUSTOMIZE_STRING preserves the original ID so edge endpoints still resolve](/docs/images/seatunnel/seatunnel-preserve-ids-en.png)](/docs/images/seatunnel/seatunnel-preserve-ids-en.png)

### 5.1 Migrate vertices first

Source adds a `~id` column for the original ID, and Sink stores it as a string. Do not declare `~id` in `schema.fields`; manually declaring this reserved column is rejected.

<details>
<summary>Expand the configuration and save it as config/graph2graph-person.conf</summary>

```hocon
env {
  job.mode = "BATCH"
}

source {
  HugeGraph {
    host = "source-hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
    label = "person"
    label_type = "VERTEX"
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
    host = "target-hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
    batch_failure_fallback = false
    mappings = [
      {
        type = "VERTEX"
        label = "person"
        idStrategy = "CUSTOMIZE_STRING"
        idFields = ["~id"]
        properties = ["name", "age"]
      }
    ]
  }
}
```

</details>

```bash
./bin/seatunnel.sh --config ./config/graph2graph-person.conf -m local
```

### 5.2 Migrate edges second

After the vertex job succeeds, use the `~source_id` and `~target_id` columns added by Source to locate endpoints. Because the previous job preserved the original IDs, these columns can refer directly to vertices in the target graph.

<details>
<summary>Expand the configuration and save it as config/graph2graph-knows.conf</summary>

```hocon
env {
  job.mode = "BATCH"
}

source {
  HugeGraph {
    host = "source-hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
    label = "knows"
    label_type = "EDGE"
    schema = {
      fields = {
        since = "int"
      }
    }
  }
}

sink {
  HugeGraph {
    host = "target-hugegraph"
    port = 8080
    graph_name = "hugegraph"
    graph_space = "DEFAULT"
    check_vertex = true
    batch_failure_fallback = false
    mappings = [
      {
        type = "EDGE"
        label = "knows"
        sourceConfig = {
          label = "person"
          idFields = ["~source_id"]
        }
        targetConfig = {
          label = "person"
          idFields = ["~target_id"]
        }
        properties = ["since"]
      }
    ]
  }
}
```

</details>

```bash
./bin/seatunnel.sh --config ./config/graph2graph-knows.conf -m local
```

This example checks endpoints and makes write errors fail the job. The default `check_vertex = false` does not guarantee a consistent result: a missing endpoint can create a dangling edge, so a successful job is not a substitute for checking the migrated graph.

> **Why preserve IDs?** A HugeGraph `PRIMARY_KEY` ID contains the internal ID of the vertex label, and that internal ID can differ between graphs. For example, a source vertex can be `1:marko`, while regenerating the primary key in the target graph can produce `2:marko`. Reusing the source edge endpoints after regenerating vertex IDs can connect edges to the wrong vertices. This example stores the original ID as a string, which changes the target graph's ID strategy.

When Source reads every label, omit `label` to read all labels of `label_type` (default `VERTEX`). It produces one output table per label. Bind each Sink mapping to its table with `sourceTable`, for example `sourceTable = "default.person"`; use the full table name shown in the Writer log for the exact value. Do not reuse the single-label configuration from this section. See the [HugeGraph Source documentation](https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/source/HugeGraph.md) for other limitations.

## 6 Common configuration and troubleshooting

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
| `batch_failure_fallback` | Default `false`, so a batch failure fails the job; set `true` to retry records one by one and allow failed records to be skipped |

Use these checks when a job fails:

- **`mappings` is unknown or HugeGraph Source is missing:** Check that the engine and HugeGraph connector come from the same SeaTunnel 3.0+ build.
- **Connection failure:** Check the host, port, graph space, authentication details, and whether the SeaTunnel runtime can reach the service.
- **Schema incompatibility:** Check the ID strategy, property types, and edge endpoints. Automatic creation does not change an existing `PRIMARY_KEY` label into `CUSTOMIZE_STRING`.
- **Small Kafka batches do not appear promptly:** Confirm that the job uses Zeta and set `sink.flush.interval` in `env`. In this version, `batch_interval_ms` is retained only for compatibility and cannot replace it.

## 7 Choosing a tool

Choose a tool based on the work to complete. Use [Tools](/docs/quickstart/toolchain/hugegraph-tools/) for graph management, Gremlin, backup, or cloning. Use [Loader](/docs/quickstart/toolchain/hugegraph-loader/) for a direct graph import. Choose SeaTunnel when you need to reuse a Source, Transform, and Sink pipeline. For SeaTunnel graph reads and migrations, prepare the environment using the SeaTunnel 3.0+ version used by this guide.

[![Choosing a tool: Tools for graph management, Loader for direct imports, and SeaTunnel for reusable data pipelines](/docs/images/seatunnel/seatunnel-tool-choice-en.png)](/docs/images/seatunnel/seatunnel-tool-choice-en.png)

## 8 References

- [HugeGraph Sink](https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/sink/HugeGraph.md)
- [HugeGraph Source](https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/source/HugeGraph.md)
- [JDBC Source](https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/source/Jdbc.md)
- [Kafka Source](https://github.com/apache/seatunnel/blob/3.0.0-release/docs/en/connectors/source/Kafka.md)
- [SeaTunnel local deployment](https://seatunnel.apache.org/docs/getting-started/locally/deployment/)

## 9 Legacy version note

This guide targets SeaTunnel 3.0+. Its Source, `mappings`, and graph migration examples do not apply to 2.3.13. That legacy version provides only the HugeGraph Sink, uses `schema_config`, and requires the graph schema to be created in advance. If you must use 2.3.13, follow the [official Sink documentation](https://github.com/apache/seatunnel/blob/2.3.13/docs/en/connectors/sink/HugeGraph.md) instead of copying this guide's configuration.
