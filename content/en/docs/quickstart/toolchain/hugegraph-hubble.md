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
> Do not expose Hubble or Server directly to the public network. In production, use HTTPS, containers,
> [authentication and authorization](/docs/config/config-authentication/), and an access allowlist.


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
The algorithm and account screenshots use Hubble built from Toolchain `1.8.0` with Server `1.7.0`. Hubble currently returns the static value
`3.0.0` from `/about`, which does not identify the build version. This pairing describes those screenshots, not a fixed meaning of `latest`.
Available controls depend on Server capabilities.
Compose's `server-data` and `hubble-data` retain graph data and Hubble metadata respectively. For further persistence and production settings,
see the [Server deployment guide](/docs/quickstart/hugegraph/hugegraph-server/).

## Home: find the right starting point

Home groups the workspace into graph overview, data preparation, and graph queries. Use it to understand the workflow,
then return to any section through the sidebar. The top graph selector determines the target of queries, schema operations, and async tasks;
check the current graph after changing pages. Standalone mode has only the `DEFAULT` GraphSpace and needs no PD configuration.

| Section | Purpose |
|---|---|
| Graph Overview and details | Select a graph, load samples, inspect its size, then model or query it |
| Schema configuration | Define properties, vertex/edge labels, and indexes |
| GQL Traversal | Write queries and explore graph, table, and JSON results |
| Built-in Algorithms | Explore neighbors, paths, and similarity with parameter forms |
| Async Tasks | Track background queries, schema changes, and index operations |
| Data Source Management | Upload files or configure external readers |
| Data Import | Map source fields to the graph model and run or schedule ingestion |
| Profile and Account Management | Update personal details/passwords and manage accounts or space members according to permissions |
| Operations | Inspect Server nodes; PD mode also includes cluster overview and PD/Store nodes |

## Graph Overview and details: get to know a graph

Select the default graph `hugegraph` in **Graph Overview**. The overview provides graph entry points and action menus.
Graph details show schema and data statistics, with routes to modeling, data preparation, and queries.
Statistics describe overall size; update them after importing or modifying data.

Load the **People & Software Demo Graph** from the graph's **More actions** menu. Samples add their schema and missing elements
without clearing existing data. Start with an empty graph to avoid conflicting schema names.
The remaining examples explore the people and software in this graph.

![Graph overview with the person/software sample](/docs/images/hubble/overview.jpg)

Graph creation depends on Server capabilities. Its form accepts a name, optional alias, and schema or sample;
it does not configure a Server host or account per graph. The connection comes from Hubble configuration.
User-defined schema templates require PD mode; see the [distributed supplement](/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/).

## Schema modeling: define the shape of your data

Schema determines valid properties and relationships, vertex ID generation, and query indexes.
Open the graph's schema configuration. List view is useful for maintaining definitions; graph view helps explain how labels connect.

| Definition | What to decide |
|---|---|
| Properties | Data type and cardinality; distinguish numbers from text |
| Vertex labels | Properties, nullable properties, ID strategy, and primary keys |
| Edge labels | Source/target labels, properties, frequency, and sort keys |
| Vertex / edge indexes | Index type and fields that match filtering and range queries |

In the person/software sample, `person` generates IDs from the primary key `name`, with nullable `age` and `city`.
`software` has custom numeric IDs, and `created` connects people to software. This matches the
[Loader example](/docs/quickstart/toolchain/hugegraph-loader/).

![Vertex labels with primary-key and numeric ID strategies](/docs/images/hubble/schema.jpg)

For a new model, define properties, vertex labels, edge labels, then indexes. Associated-property and index information help inspect dependencies.
Schema deletion and index creation/rebuild may submit background tasks. Acceptance of an operation is only the first step;
confirm its final status in **Async Tasks**.

## GQL workspace: query and explore relationships

Open **GQL Traversal** and confirm `hugegraph` is selected. The workspace puts the editor and results together,
with immediate or async execution, query favorites, and reusable execution history. Start with this Gremlin query:

```groovy
g.V().hasLabel('person').valueMap()
```

Inspect person properties in table or JSON view. To visualize the people-to-software relationships, run:

```groovy
g.V().hasLabel('person').outE('created').inV().path()
```

![Gremlin path query and graph result](/docs/images/hubble/query.jpg)

Graph results support 2D / 3D. Click a vertex or edge to inspect its ID, label, and properties; double-click a vertex to expand its neighbors.
Layout, styling, and filtering help highlight relevant relationships, while export helps share results.
Use **New** to create elements, or edit existing data when authorized. Layout, colors, and display limits only change presentation;
adding/editing elements and Gremlin writes change Server data.

Use `Ctrl` / `Command` + `Enter` to execute. Immediate mode suits small explorations; submit long queries asynchronously
and avoid returning an entire large graph. Cypher is available only when Server supports it.
Text2GQL is currently a UI preview with no model or query service connected; it cannot generate executable queries.

## Built-in algorithms: explore with parameter forms

Use **Built-in Algorithms** when you prefer a form to writing traversal code. Search for an algorithm and supply its parameters.
Neighbor exploration answers what surrounds a vertex, path algorithms connect two vertices, and similarity/ranking algorithms compare or select vertices.
Start with a known vertex ID and limit direction, edge labels, depth, and result size before attempting broader computation.

Forms provide parameter guidance and documentation links, and restore common parameters when navigating away and back.
Results use graph or algorithm-specific panels. Consult the help and documentation links beside the algorithm title for definitions and parameters.
While the parameter form is focused, `Ctrl` / `Command` + `Enter` runs the current algorithm.

OLAP batch algorithms require external compute services such as Computer or Vermeer.
The two containers in this example provide online graph operations, not those compute services.

For example, select K-neighbor (GET) with `source=1:marko`, `max_depth=1`, and `limit=20`.
After parameter validation, use the run button on the card or the form shortcut to explore one-hop neighbors.

![Built-in neighbor algorithm parameters and graph result](/docs/images/hubble/algorithms.jpg)

## Async Tasks: confirm background results

**Async Tasks** lists background work for the current graph, including async queries and some schema/index operations.
Filter by task type and status, inspect IDs, creation times, and execution states, open successful query results, or expand failure information.
Completed task records can be deleted where the interface permits. These tasks are separate from import execution history.

For example, submit `g.V().count()` asynchronously, confirm success in the list, then inspect the returned count.
A successful submission means the request was accepted, not that computation or indexing has finished.
Use task errors and Server logs together when diagnosing failures.

## Data Source Management: prepare the input

A data source defines where data comes from and how to parse it, and can be referenced by import tasks.
Hubble supports FILE, HDFS, JDBC, and Kafka, each with its own path, connection, or subscription settings.
FILE is an easy starting point: upload a file, configure its format, delimiter, encoding, and header, and check column names before mapping.
Hubble configuration controls upload limits and permitted extensions.

Save this UTF-8 file as `people.csv` for the person example:

```csv
name,age,city
docs_alice,28,Beijing
docs_bob,32,Shanghai
```

Create a FILE data source and upload it. Select CSV (comma separation and UTF-8 by default), with column names `name,age,city`.
Header, delimiter, and encoding belong to the data source, not mapping settings. The source fields must match the file.

## Data Import: turn fields into a queryable graph

**Data Import** converts source rows into vertices and edges. Its four configuration sections identify the target, select fields,
map them to the graph, and choose execution timing. Use the preceding data source to create a person import into `DEFAULT` / `hugegraph`:

| Section | Settings for this example |
|---|---|
| Basic Information | Target graph, new data source, and a recognizable task name |
| Source Fields | Select `name`, `age`, and `city`, moving them to the selected field list |
| Mapping Fields | Add a `person` vertex mapping; use **Auto Match** for same-name properties, then verify types |
| Schedule | Choose one-time execution; confirmation submits the task immediately |

`person` uses PRIMARY_KEY, so do not select a separate ID column. Custom ID strategies require an ID column;
AUTOMATIC lets Server generate IDs, while PRIMARY_KEY derives them from mapped primary-key properties.
Edge mappings need source/target fields that follow the corresponding vertex ID rules.

The task list manages configuration and execution entry points; execution history in task details shows each instance's state, count, and errors.
Periodic schedules and real-time Kafka tasks are also available; choose an execution mode compatible with the source.
After completion, verify the result in the GQL workspace:

```groovy
g.V().hasLabel('person').has('name', within('docs_alice', 'docs_bob')).valueMap()
```

The result should include both new people. Import counts are not necessarily counts of newly created vertices:
reruns may update existing elements, and header processing can affect reader counts.
If the import fails, check source fields, numeric types, nullable properties, and target schema.
Use Hubble for small trials and [HugeGraph Loader](/docs/quickstart/toolchain/hugegraph-loader/) for production bulk ingestion.

## Profile and account permissions

Hubble uses Server authentication and accounts, with no separate user database. Anonymous mode hides **Profile** and **Account Management**.
After authentication is enabled, Profile shows the current account's details and permissions and allows changing your password.
Editing details such as a nickname requires Server support for the personal-profile API. Changing a password ends the current session;
sign in again with the new password.

### Standalone account management

In standalone mode, the administrator can create, inspect, edit, delete, and batch-create accounts.
Ordinary standalone accounts created through Hubble receive read, write, delete, and execute permissions across all graphs;
they are not read-only or isolated to one graph. Configure finer resource permissions through
[Server authentication and authorization](/docs/config/config-authentication/) rather than relying on GraphSpace presets.

### GraphSpace permissions in PD mode

With a Server supporting default-role APIs, global accounts and space access can be managed separately.
The administrator manages global accounts; a space administrator manages members only within authorized spaces.
Ordinary members do not receive account-management or operations entry points.
The following presets are for PD mode, and are not universally editable on older or standalone Servers:

| Preset | Scope and purpose |
|---|---|
| `SUPER_ADMIN` | Global account, GraphSpace, and operations management; grant or revoke super-administrator access |
| `GS_ADMIN` | Manage authorized spaces and their members, without granting other-space or global super-administrator access |
| `GS_READ_WRITE` | Read and write graph data within authorized spaces, without managing global accounts |
| `GS_READ_ONLY` | Read graph data within authorized spaces, without writes |

An account may have different permissions in different spaces. Select a space before adding an existing account or changing member permissions.
Before replacing custom permissions with a preset, inspect the grants that need to be retained; complex permissions may not match a single preset.
After changes, refresh permission context or sign in again and verify menus and space selection. Server still validates every request.
Older Servers may hide or disable unsupported operations; a visible button alone does not establish resource authorization.
See the [distributed supplement](/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/) for space management.

![Authenticated account list in PD mode](/docs/images/hubble/accounts.jpg)

## Operations: inspect the standalone Server

Standalone **Operations** provides **Node Information** for Server only, with no PD/Store nodes or cluster overview.
Search nodes, filter health status, and open node details to inspect available version, system, JVM, and Server-backend metrics.
When metrics are unavailable or stale, use collection state and the last successful observation time;
a missing value is neither zero nor proof of health.

Anonymous mode can read operations information. With authentication enabled, operations are available only to administrators with the capability.
This is an observation and diagnosis interface, not a start/stop or scaling console.
The distributed supplement covers cluster overview and the PD/Store node hierarchy.

## Keyboard shortcuts and graph interactions

Use the topbar shortcut-help button to see key bindings. Their scope differs: typing `?` in an input does not trigger global help.

| Action | Key or gesture | Scope |
|---|---|---|
| Open / close shortcut help | `?` | Outside inputs and editors |
| Execute query | `Ctrl` / `Command` + `Enter` | Query editor |
| Run current algorithm | `Ctrl` / `Command` + `Enter` | Algorithm parameter form |
| Toggle graph fullscreen | `F` | Click to focus the graph canvas first; not a global binding |
| Inspect element details | Click a vertex or edge | Graph result |
| Expand neighboring relationships | Double-click a vertex | Graph result |

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
