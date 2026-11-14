# Apache HugeGraph

> A full-stack graph database ecosystem for OLTP, OLAP, and graph AI.

LLMS index: [llms.txt](/llms.txt)

## Full-stack graph platform

Query relationships in real time, analyze whole graphs offline, and use Graph AI to build LLM memory and ontology graphs

[Get Started](/docs/quickstart/)

[GitHub](https://github.com/apache/hugegraph)

## HugeGraph, from one stack to every scale

### Graph Database

server/pd/store

Server handles graph queries. In a distributed deployment, PD manages partitions and Store keeps replicas

**Start with one vertex**

Follow an edge to a neighboring vertex. Use embedded storage on a single machine or Raft replication for highly available distributed storage

```gremlin
g.V().has('name', 'marko').out('knows')
```

[Explore database deployment](/docs/quickstart/hugegraph/)

### Graph Toolchain

loader/hubble/tools

Import vertices and edges with Loader, explore them in Hubble, and back up or migrate data with Tools

**Follow an edge**

Load vertices and edges with Loader, then explore the query results in Hubble, one relationship at a time

[Explore the graph toolchain](/docs/quickstart/toolchain/)

### Graph Computing

vermeer/computer

OLAP over the whole graph, in memory or on a BSP cluster

**Analyze the whole graph to discover communities**

Graph computing runs OLAP over the whole dataset, with Vermeer in memory and Computer on a BSP cluster

[Explore graph computing](/docs/quickstart/computing/)

### Graph AI

llm/sdk/rag

GraphRAG and ontology graph construction with LLMs

**Explore graphs with AI**

Our graph extraction SDK, Memory, and ontology platform are evolving quickly. Join us in building Graph AI

[Explore Graph AI](/docs/quickstart/hugegraph-ai/)

## A full-stack graph system that carries your data from **storage** and **real-time querying** to **offline analysis** and **AI**

- **100s of billions** — vertices and edges

- **Milliseconds** — multi-hop query latency

- **30+** — built-in graph algorithms

- **First** — Apache top‑level graph system

## Key features

- [**Efficient**](/docs/quickstart/toolchain/hugegraph-loader/) — Batch import for massive datasets, millisecond-level retrieval and concurrent online operations for thousands of users

- [**AI\-Ready**](/docs/quickstart/hugegraph-ai/) — GraphRAG, automated knowledge graph construction and 20+ built-in graph machine learning algorithms

- [**Convenient**](/docs/quickstart/toolchain/) — Gremlin, Cypher and a RESTful API, plus a complete toolchain for import, visualization and operations

- [**Adaptable**](/docs/quickstart/computing/) — Property graph modeling on Apache TinkerPop, covering OLTP and OLAP, with Hadoop and Spark integration

- [**Scalable**](/docs/quickstart/hugegraph/hugegraph-hstore/) — Horizontal scaling and distributed deployment, from a standalone server to PB-level clusters

- [**Open Ecosystem**](/docs/clients/client/hugegraph-client/) — TinkerPop standards, multi-language clients and an active, evolving Apache community

## Works seamlessly with your existing stack

Apache Spark, Apache Flink, Apache Hadoop, Docker, Kubernetes, Helm, RocksDB, Python, Go, OpenJDK

## ALL IN ONE

Deploy the database on one node or across a cluster. Add tools, graph computing and AI as needed

### Graph Database

- [**Server \(Start here\)**](/docs/quickstart/hugegraph/hugegraph-server/) — Core graph engine with REST API, Gremlin and Cypher

- [**PD**](/docs/quickstart/hugegraph/hugegraph-pd/) — Placement Driver for metadata, partitions and cluster scheduling

- [**Store**](/docs/quickstart/hugegraph/hugegraph-hstore/) — Distributed storage with Raft consensus

### Toolchain

- [**Hubble**](/docs/quickstart/toolchain/hugegraph-hubble/) — Web platform for graph visualization

- [**Loader**](/docs/quickstart/toolchain/hugegraph-loader/) — Data import tool for bulk loading

- [**Tools**](/docs/quickstart/toolchain/hugegraph-tools/) — Command-line utilities for backup, restore and migration

### Computing and AI

- [**Vermeer**](/docs/quickstart/computing/hugegraph-vermeer/) — In-memory graph algorithms for PageRank and community detection

- [**AI**](/docs/quickstart/hugegraph-ai/) — GraphRAG and knowledge graph construction with LLMs

## Quick start

Docker starts HugeGraph Server in standalone mode by default on port 8080 of localhost. Standalone mode supports in-memory or disk storage

```bash
docker run -d -p 127.0.0.1:8080:8080 hugegraph/hugegraph
```

Check the startup logs, then verify the service is ready

```bash
curl -fsS http://127.0.0.1:8080/versions
```

[Other install options](/docs/download/download/)

[Verify setup and run your first query](/docs/quickstart/hugegraph/hugegraph-server/)

## Welcome to the HugeGraph open source community

New users and contributors are always welcome

- [**GitHub**](https://github.com/apache/hugegraph) — Contributions go through pull requests on GitHub

- [**ASF Slack**](https://the-asf.slack.com/archives/C059UU2FJ23) — Join the HugeGraph channel for community discussions

- [**Discord**](https://discord.gg/bT7GtKEnJK) — Join the HugeGraph community on Discord

- **Twitter** — On the way

---

Section pages:

- [Documentation](/docs/)

- [About Apache HugeGraph](/about/)

- [Blog](/blog/)

- [Community](/community/)

- [Search Results](/search/)
