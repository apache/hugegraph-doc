# HugeGraph Architecture Overview

LLMS index: [llms.txt](/versions/1.7/llms.txt)

---

### 1 Overview

As a general-purpose graph database product, HugeGraph needs to possess basic graph database functionality. HugeGraph supports two types of graph computation: OLTP and OLAP. For OLTP, it implements the [Apache TinkerPop3](https://tinkerpop.apache.org) framework and supports the [Gremlin](https://tinkerpop.apache.org/gremlin.html) and [Cypher](https://en.wikipedia.org/wiki/Cypher) query languages. It comes with a complete application toolchain and provides a plugin-based backend storage driver framework.

Below is the overall architecture diagram of HugeGraph:

<div style="text-align: center;">
  <img src="/versions/1.7/docs/images/design/architectural-revised.png" alt="image">
</div>

HugeGraph consists of three layers of functionality: the application layer, the graph engine layer, and the storage layer.

- Application Layer:
  - [Hubble](/versions/1.7/docs/quickstart/toolchain/hugegraph-hubble): A one-stop visual analysis platform that covers the entire process from data modeling to rapid data import, online and offline analysis, and unified graph management, realizing wizard-style operations for the entire graph application process.
  - [Loader](/versions/1.7/docs/quickstart/toolchain/hugegraph-loader): A data import component that can transform data from multiple data sources into graph vertices and edges and batch import them into the graph database.
  - [Tools](/versions/1.7/docs/quickstart/toolchain/hugegraph-tools): Command-line tools for deploying, managing, and backing up/restoring data in HugeGraph.
  - [Computer](/versions/1.7/docs/quickstart/computing/hugegraph-computer): A distributed graph processing system (OLAP), which is an implementation of [Pregel](https://kowshik.github.io/JPregel/pregel_paper.pdf) and can run on Kubernetes.
  - [Client](/versions/1.7/docs/quickstart/client/hugegraph-client): A HugeGraph client written in Java. Users can use the Client to write Java code to operate HugeGraph. Python, Go, C++ and other language support will be provided in the future as needed.
- [Graph Engine Layer](/versions/1.7/docs/quickstart/hugegraph/hugegraph-server/):
  - REST Server: Provides a RESTful API for querying graph/schema information, supports the [Gremlin](https://tinkerpop.apache.org/gremlin.html) and [Cypher](https://en.wikipedia.org/wiki/Cypher) query languages, and offers APIs for service monitoring and operations.
  - Graph Engine: Supports both OLTP and OLAP graph computation types, with OLTP implementing the [Apache TinkerPop3](https://tinkerpop.apache.org) framework.
  - Backend Interface: Implements the storage of graph data to the backend.
- Storage Layer:
  - Storage Backend: Supports multiple built-in storage backends (RocksDB/MySQL/HBase/...) and allows users to extend custom backends without modifying the existing source code.
