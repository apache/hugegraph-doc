---
title: "HugeGraph-Loader Performance"
linkTitle: "HugeGraph-Loader Performance"
weight: 3
---

> **Note:** 
> 
> The current performance metrics are based on an earlier version. The **latest version** has significant 
> improvements in both performance and functionality. We encourage you to refer to the most recent release featuring 
> **autonomous distributed storage** and **enhanced computational push down capabilities**. Alternatively, 
> you may wait for the community to update the data with these enhancements.

## Use Cases

When the number of graph data to be batch inserted (including vertices and edges) is at the billion level or below, 
or the total data size is less than TB, the [HugeGraph-Loader](/docs/quickstart/toolchain/hugegraph-loader) tool can be used to continuously and quickly import 
graph data.

## Performance

> The test uses the edge data of website.

### RocksDB single-machine performance (Update: multi-raft + rocksdb cluster is supported now)

- When the label index is turned off, 228k edges/s.
- When the label index is turned on, 153k edges/s.

### Cassandra cluster performance

- When label index is turned on by default, 63k edges/s.
