---
title: "Graph Query Languages"
linkTitle: "Graph Query Languages"
weight: 7
---

HugeGraph supports two mainstream graph query languages: **Gremlin** (imperative traversal language) and **Cypher** (declarative pattern matching language).

- **Gremlin**: The core graph traversal language of Apache TinkerPop, offering rich traversal primitives and fine control over complex topological paths.
- **Cypher**: The declarative query language standardized by openCypher, featuring intuitive SQL-like patterns (`MATCH ... WHERE ... RETURN`) for Neo4j parity.

## Language Guides & References

- [HugeGraph-Gremlin](/docs/language/hugegraph-gremlin/)

  Gremlin traversal fundamentals, CRUD query examples, TinkerPop feature support, and 1.8 upgrade changes.
- [HugeGraph Cypher](/docs/language/hugegraph-cypher/)

  Cypher language support via cypher-for-gremlin, read/write statement examples, execution mechanics, and constraints.
- [Cypher Compatibility](/docs/language/cypher-compatibility/)

  Coverage matrix for Cypher clauses and functions, known behavior differences, and workarounds for unsupported features.
- [Migrate from Neo4j](/docs/language/migrate-from-neo4j/)

  Core differences between Neo4j and HugeGraph in graph modeling, ID strategies, multiple labels, and query translation.
- [Sample Graph Data](/docs/language/hugegraph-example/)

  The classic 6-vertex 6-edge TinkerPop sample graph dataset used across query examples.
{.cards}

## Related Tools & Entry Points

Ways to interact with and execute graph queries across HugeGraph components:

- **CLI Shell**: Use [Gremlin Console](/docs/clients/gremlin-console/) to debug queries offline or connect directly to Server over WebSocket.
- **Web Visualization**: Use [HugeGraph-Hubble](/docs/quickstart/toolchain/hugegraph-hubble/)
  to run Gremlin / Cypher queries with visual graph exploration and Text2GQL.
- **HTTP REST APIs**: Submit queries programmatically via HTTP using
  the [Gremlin REST API](/docs/clients/restful-api/gremlin/) and [Cypher REST API](/docs/clients/restful-api/cypher/).
- **Version Migration**: Upgrading to 1.8.0? Review the
  [1.8 Gremlin & TinkerPop Migration Guide](/docs/guides/gremlin-migration-3.8/) for TinkerPop 3.8 syntax removals.
