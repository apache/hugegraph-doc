---
title: "Graph Visualization with Hubble: Standalone Quick Start"
description: "Visualize graph data with Hubble and RocksDB Server: start with Docker, explore schema, import CSV, and run Gremlin queries."
linkTitle: "Hubble Basics and Standalone"
weight: 1
search_keywords: [HugeGraph Hubble, graph visualization, Web management interface, RocksDB]
search_boost: 1.6
---

Hubble is the HugeGraph Web management and graph visualization interface. Use one workspace to manage schema, import data, run queries,
and switch between graph, table, and JSON results. This guide uses **standalone RocksDB Server + Hubble**, without PD or Store.

For HStore, read the shared operations here first, then follow the [distributed supplement](/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/).
This guide follows Toolchain `master` (currently `1.8.0`); Docker `latest` is mutable, so check the actual running versions.

> [!WARNING]
> **The deployment below is for a local trial.** Hubble accepts native queries that can modify data. In production,
> terminate HTTPS at a trusted entry point, restrict network access to Hubble and Server, and enable
> [Server authentication and authorization](/docs/config/config-authentication/).
> Retain Server's `audit-*.log` with restricted access; `auth.audit_log_rate` is a rate limit, not an audit switch.


Screenshots were captured on 2026-10-01 with Docker `latest`: Hubble `/about` reports `3.0.0` and Server core is `1.7.0` (RocksDB).
The sample and import below were exercised; availability of newer master features still depends on Server capabilities.

## Start the standalone pair

Use the main repository's [docker/docker-compose.yml](https://github.com/apache/hugegraph/blob/master/docker/docker-compose.yml)
instead of writing another Compose file. It already combines RocksDB Server and Hubble, with networking, health checks, and data volumes.
See the adjacent [README](https://github.com/apache/hugegraph/blob/master/docker/README.md) for deployment details.

```bash
git clone --branch master --single-branch --depth 1 https://github.com/apache/hugegraph.git
cd hugegraph/docker
```

If you already have the main repository, enter its `docker/` directory. Compose mounts
[`conf/hubble/standalone.properties`](https://github.com/apache/hugegraph/blob/master/docker/conf/hubble/standalone.properties)
from that directory. It sets `pd.enabled=false` and `server.direct_url=http://server:8080`;
both services communicate over one Docker network, without a Server address configured per graph.
Do not download only the YAML and start it from another directory: relative configuration files may be missing.

Hubble defaults to host loopback port `8088`; Server publishes `8080`. For a trial on your machine only, change Server's
`ports` entry to `127.0.0.1:8080:8080` to avoid exposing the anonymous API to other machines.

Choose an unused project name for this trial and keep these variables in the same terminal.
Restore this project name if you use another terminal.

```bash
export HUGEGRAPH_VERSION=latest
export HUBBLE_IMAGE=hugegraph/hubble:latest
export HUBBLE_DEMO_PROJECT="hubble-demo-$(date +%Y%m%d-%H%M%S)"
docker compose ls
docker compose -p "$HUBBLE_DEMO_PROJECT" -f docker-compose.yml pull
docker compose -p "$HUBBLE_DEMO_PROJECT" -f docker-compose.yml up -d --wait
docker compose -p "$HUBBLE_DEMO_PROJECT" -f docker-compose.yml ps
curl -fsS http://127.0.0.1:8080/versions
```

Once services are healthy, open <http://127.0.0.1:8088>. In a fresh directory without `HUGEGRAPH_ADMIN_PASSWORD`,
Server allows anonymous access and Hubble opens the home page directly. For authentication, follow the Docker README to configure
an administrator password and JWT secret in `.env`, then sign in with a Server account. Hubble has no separate account database.
Personal and account-management pages depend on the authentication mode and your permissions. Do not overwrite an existing `.env`.

Use `latest` to try current features, and pin a published image version or digest for production.
Images are convenience distributions; official release archives are on the [download page](/docs/download/download/).
Compose's `server-data` and `hubble-data` retain graph data and Hubble metadata respectively. For further persistence and production settings,
see the [Server deployment guide](/docs/quickstart/hugegraph/hugegraph-server/).

## Learn the workspace with a sample graph

Open **Graph Overview** and select the default graph `hugegraph`. Standalone mode has only the `DEFAULT` GraphSpace,
so you usually do not need to select a space. The top graph selector determines which graph each operation affects;
check it before a query and after switching pages.

In the graph's **More actions** menu, load the **People & Software Demo Graph**. Samples add their schema and missing elements without clearing existing data.
Use an empty graph for your first run to avoid conflicting schema names. Graph names, aliases, and labels affect the queries that follow.

![Graph overview with the person/software sample](/docs/images/hubble/overview.jpg)

| Task | Starting point |
|---|---|
| View graphs, load a sample, inspect data size | Graph Overview and graph details |
| Define properties, vertex/edge labels, and indexes | The graph's schema configuration |
| Run Gremlin / Cypher and explore results | GQL Traversal |
| Upload a file and configure its reader | Data Source Management |
| Configure mappings, run or schedule imports | Data Import |
| Track background queries and index tasks | Async Tasks |

Graph creation is available only when Server exposes that capability. The form accepts a name, optional alias, and schema or sample;
it does not configure a Server host or account per graph. The connection comes from Hubble's configuration.
Query the sample first, then inspect its schema to understand how the model relates to the data.

## Query and explore relationships

Open **GQL Traversal**, confirm `hugegraph` is selected, and run this Gremlin query in immediate mode:

```groovy
g.V().hasLabel('person').valueMap()
```

It returns person properties, best inspected in the table or JSON view. To visualize person-to-software relationships, run:

```groovy
g.V().hasLabel('person').outE('created').inV().path()
```

Click a vertex or edge in the graph to inspect its ID, label, and properties; double-click a vertex to expand its neighbors.
The canvas toolbar provides layout, styling, filtering, exporting, and **New** actions.
Changing the presentation does not modify stored data; adding/editing elements or executing Gremlin writes does.

![Gremlin path query and graph result](/docs/images/hubble/query.jpg)

Use `Ctrl` / `Command` + `Enter` to execute. Save frequently used queries as favorites, or load them from execution history.
For longer queries, choose asynchronous execution and inspect status/results in **Async Tasks**.
Immediate queries are suitable for small explorations; avoid returning an entire large graph at once.

The Cypher tab is available only when Server supports it. Text2GQL is currently a UI preview with no model or query service connected.
The canvas supports 2D/3D, while table and JSON views help verify raw results.
Built-in algorithm forms cover neighbor exploration, paths, and similarity; OLAP batch algorithms additionally require Computer or Vermeer,
so starting the two containers in this example does not provide those external compute environments.

## Understand the schema before adding data

Open the graph's schema configuration from Graph Overview. Schema defines the labels/properties that can be written,
vertex ID strategies, and indexes. Switch between list and graph views; the list separates properties, vertex labels,
edge labels, vertex indexes, and edge indexes.

In the person/software sample, `person` generates its ID from the primary key `name`, with nullable `age` and `city`.
`software` has custom numeric IDs, and `created` links people to software. This matches
the [Loader example](/docs/quickstart/toolchain/hugegraph-loader/).

![Vertex labels with primary-key and numeric ID strategies](/docs/images/hubble/schema.jpg)

For your own model, define properties, then vertex labels, edge labels, and indexes. Distinguish numeric and text values,
declare nullable properties, and choose primary-key or custom IDs. Edges must reference existing vertex labels;
indexes should match your queries. Schema deletion and index creation/rebuild may submit background tasks,
whose completion is visible in **Async Tasks**.

### Add two people from CSV

Save a UTF-8 file named `people.csv`:

```csv
name,age,city
docs_alice,28,Beijing
docs_bob,32,Shanghai
```

Create a FILE data source in **Data Sources** and upload the file. Select CSV (comma separation and UTF-8 by default),
and the column names `name,age,city`. Header, delimiter, and encoding are data source settings, not mapping settings.

Create an import task in **Data Import**, completing these four sections:

1. **Basic Information**: choose `DEFAULT` / `hugegraph` and the new data source.
2. **Source Fields**: select the detected `name`, `age`, and `city` fields and move them to the selected list on the right.
3. **Mapping Fields**: add a `person` vertex mapping and use **Auto Match**, then verify the three matching fields and properties.
4. **Schedule**: choose one-time execution and confirm; the task is submitted immediately. Check its status in the list.

`person` uses PRIMARY_KEY, so do not select a separate ID column. Custom ID strategies require an ID column;
AUTOMATIC lets Server generate IDs, and PRIMARY_KEY derives IDs from mapped primary-key properties.
Edge mappings also require source and target fields.


Inspect the execution instance's status, imported count, and error message in execution history, then verify in the query workspace:

```groovy
g.V().hasLabel('person').has('name', within('docs_alice', 'docs_bob')).valueMap()
```

The result should include both new people. If the import fails, check source fields, numeric types, nullable properties,
and target schema before creating another task. Hubble also supports HDFS, JDBC, Kafka, periodic schedules,
and real-time Kafka tasks. Use Hubble imports for small trials; use [HugeGraph Loader](/docs/quickstart/toolchain/hugegraph-loader/)
for production bulk ingestion.

## Diagnose connection and result issues

| Symptom | Check first |
|---|---|
| The Hubble page does not open | Check container status and `docker compose -p "$HUBBLE_DEMO_PROJECT" -f docker-compose.yml logs hubble` |
| The page opens but graphs are unavailable | Server health, a `server.direct_url` reachable from Hubble, and a shared network |
| Login appears or write actions are missing | Server authentication and account permissions; Hubble has no independent authentication switch |
| Expected data is missing | Current graph, sample load result, matching labels/properties; distinguish canvas display from stored data |
| No cluster overview | This example has no PD; see the distributed supplement |

Configuration can affect displayed query size. `gremlin.suffix_limit` defaults to `250` and supplies `.limit(N)` appended to applicable Gremlin queries;
it is not a universal hard limit. `gremlin.vertex_degree_limit` (`100`) and `gremlin.edges_total_limit` (`500`) constrain expansion.
FILE uploads allow `csv,txt` by default, with 1 GB per file and 10 GB total. Override `upload_file.*` settings when needed.

## Stop the trial or build from source

When finished, run this in the main repository's `docker/` directory:

```bash
docker compose -p "${HUBBLE_DEMO_PROJECT:?}" -f docker-compose.yml down --volumes
```

This removes the project's containers, network, named volumes, and anonymous volume, losing the sample data and Hubble import tasks.
To retain data, omit `--volumes` when taking the deployment down and reuse the same project name when starting it again.

To obtain an exact master build, use JDK 11 and Maven. The Maven plugin installs the required Node/Yarn;
you do not need to install them separately. These commands skip tests:

```bash
git clone --branch master --single-branch https://github.com/apache/hugegraph-toolchain.git
cd hugegraph-toolchain
mvn install -pl hugegraph-client,hugegraph-loader -am -Dmaven.javadoc.skip=true -DskipTests -ntp
cd hugegraph-hubble
mvn package -Dmaven.javadoc.skip=true -DskipTests -ntp
cd apache-hugegraph-hubble-*
# Edit conf/hugegraph-hubble.properties with the correct Server URL
bin/start-hubble.sh
```

The bundled configuration binds to `localhost:8088`. `bin/stop-hubble.sh` requests graceful shutdown before forcing termination on timeout.
For development and testing, see the [Toolchain local test guide](/docs/guides/toolchain-local-test/).
