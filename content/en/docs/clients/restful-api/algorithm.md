---
title: "Algorithm API"
linkTitle: "Algorithm"
weight: 12.5
description: "Algorithm Job REST API: Submit and monitor asynchronous graph algorithm jobs."
---

## 6.2 Algorithm

The Algorithm API allows you to submit long-running graph algorithms as asynchronous jobs and track their progress.

### 6.2.1 Submit an Algorithm Job

#### Method & Url

```bash
POST http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/jobs/algorithm/{algorithm_name}
```

For legacy setups without graphspaces:

```bash
POST http://localhost:8080/graphs/{graph}/jobs/algorithm/{algorithm_name}
```

#### Request Body

The request body varies by algorithm. Common parameters include:

- `max_iteration`: Maximum number of iterations (used by iterative algorithms like LPA)
- `alpha`: Damping factor for PageRank (default: 0.85)
- `sample_rate`: Sampling rate for algorithms like betweenness_centrality (0-1)
- `direction`: Edge direction for traversal (OUT, IN, or BOTH)

#### Example: Submit a PageRank Job

```json
{
  "alpha": 0.85,
  "max_iteration": 20
}
```

#### Response Status

```json
201
```

#### Response Body

```json
{
  "task_id": 1
}
```

The response contains only the task ID. Use the [Task API](./task) to monitor the job.

### 6.2.2 Monitor Algorithm Job

Use the [Task API](./task) to check the status of an algorithm job:

```bash
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/tasks/{task_id}
```

### 6.2.3 Retrieve Algorithm Results

The response body is algorithm-specific. Some algorithms return JSON directly, while others also write results back to vertex properties.

Examples:

- `page_rank` writes rank values to the `r_rank` vertex property.
- `lpa` and `weak_connected_component` write community labels to the `c_label` vertex property.

These names come from the algorithm job implementation and can differ from property names used by other HugeGraph components.

If a job writes back to vertices, query the graph with the normal vertex API and filter by the property the algorithm updates.

For example, to find vertices with a PageRank value greater than zero, use:

```bash
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/graph/vertices?properties={"r_rank":"P.gt(0)"}
```

### 6.2.4 Supported Algorithms

The server registers the following algorithm names in `AlgorithmPool`:

- `count_vertex`
- `count_edge`
- `degree_centrality`
- `stress_centrality`
- `betweenness_centrality`
- `closeness_centrality`
- `eigenvector_centrality`
- `triangle_count`
- `cluster_coefficient`
- `lpa`
- `louvain`
- `weak_connected_component`
- `fusiform_similarity`
- `rings`
- `k_core`
- `page_rank`
- `subgraph_stat`

### 6.2.5 Performance Considerations

For very large graphs (millions+ vertices/edges), consider using [HugeGraph-Computer](/docs/quickstart/computing/hugegraph-computer) or [HugeGraph-Vermeer](/docs/quickstart/computing/hugegraph-vermeer) for distributed computation instead of the REST API.
