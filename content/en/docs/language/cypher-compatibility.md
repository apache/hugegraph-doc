---
title: "Cypher Compatibility"
linkTitle: "Cypher Compatibility"
weight: 3
---

### Scope and Overview

HugeGraph supports declarative openCypher 9 queries on top of the TinkerPop engine.
This page summarizes supported request forms, parameter binding rules, syntax coverage, and behavioral boundaries.

The endpoint is `/graphspaces/{graphspace}/graphs/{graph}/cypher`. For query examples and Gremlin equivalents, see the
[HugeGraph Cypher Guide](/docs/language/hugegraph-cypher/).

### Request Forms and Parameter Bindings

| Request Form | Content-Type | Description |
|---|---|---|
| `POST` (Recommended) | `application/json` | JSON body `{"cypher": "...", "parameters": {...}}`, supports parameter bindings |
| `POST` | `application/json` | Raw Cypher text string body (for unparameterized raw statements) |
| `GET` | — | Query parameter `?cypher=<URL-encoded statement>`, suitable for simple read queries |
{.wide}

Example JSON parameterized request:

```json
{
  "cypher": "MATCH (n:person) WHERE n.name = $name RETURN n.name",
  "parameters": {"name": "marko"}
}
```

#### Parameter Binding Rules

- **Parameter Format**: The `cypher` field must be a non-empty string; `parameters`, if provided, must be a JSON object (omitted means an empty map).
- **Parameter Count**: The top-level `parameters` object accepts at most 16 keys. For more properties, group them into a nested Map and reference fields
  explicitly in the statement (e.g. `$props.name`).
- **Unbound Variables**: Referencing an undeclared `$param` raises an execution error and is rejected (explicit `null` is supported).
- **Reserved Marker**: The exact string `"  cypher.null"` (two leading spaces) is reserved by the engine as an internal sentinel and is rejected in
  parameter values.
- **Error Response**: On validation or execution errors, the server returns HTTP 400 (or `status.code` 400 with null result), with structured details
  (`code`, `message`, `hint`) in `status.attributes.errors`.

### Syntax and Feature Support Matrix

| Category | Supported Features | Notes |
|---|---|---|
| Reads & Patterns | Label scans, equality and range predicates, boolean logic (AND/OR/NOT), directed 1-hop and multi-hop patterns, regex matching (`=~` full match) | Range comparisons require corresponding indexes |
| Results & Projection | Node and scalar projections, aliases (`AS`), property access, nested structures, relationship IDs, path expressions, null handling | Results are mapped to standard JSON structures |
| Aggregation & Ordering | `count`, `sum`, `min`, `max`, `avg`, `DISTINCT`, `ORDER BY`, `SKIP`, `LIMIT` | Mapped to underlying graph traversal steps |
| Data Writes | Vertex and edge `CREATE`, property `SET` / `REMOVE`, edge and vertex `DELETE` / `DETACH DELETE` | Create vertices with required properties before creating connecting edges |
{.wide}

### Write Constraints and Considerations

On schemas with non-nullable properties or `PRIMARY_KEY` strategy, the shorthand `CREATE (a)-[:knows]->(b)` fails
due to non-null property validation (`checkNonnullProperty`) or missing primary keys.
Execute vertex and edge creations separately, ensuring required vertex attributes are fully specified.

### Unsupported Features

The following advanced features are currently unsupported; use Gremlin or the respective REST APIs:
- **Complex Clauses**: `MERGE`, `OPTIONAL MATCH`, `WITH`, `UNWIND`, `UNION`, variable-length paths (`*1..3`);
- **Procedures**: `CALL dbms.*` / `CALL algo.*` (use the [Traverser REST API](/docs/clients/restful-api/traverser/));
- **Schema Management**: Cypher Schema DDL (use the [Schema REST API](/docs/clients/restful-api/schema/));
- **Protocols & Drivers**: Bolt protocol and drivers (use the HTTP REST API or [HugeGraph Client](/docs/clients/hugegraph-client/)).
