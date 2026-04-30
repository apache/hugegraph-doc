---
title: "Algorithm API"
linkTitle: "Algorithm"
weight: 11
description: "Algorithm Job REST API: Submit and monitor asynchronous graph algorithm jobs."
---

### 6.1 Algorithm

The Algorithm API allows you to submit long-running graph algorithms as asynchronous jobs and track their progress.

#### 6.1.1 Submit an Algorithm Job

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/jobs/algorithm/{algorithm_name}
```

For legacy setups without graphspaces:
```
POST http://localhost:8080/graphs/{graph}/jobs/algorithm/{algorithm_name}
```

##### Request Body

The request body varies by algorithm. Common parameters include:

- `max_iteration`: Maximum number of iterations (used by iterative algorithms like LPA)
- `alpha`: Damping factor for PageRank (default: 0.85)
- `sample_rate`: Sampling rate for algorithms like betweenness_centrality (0-1)
- `direction`: Edge direction for traversal (OUT, IN, or BOTH)

##### Example: Submit a PageRank Job

```json
{
  "alpha": 0.85,
  "max_iteration": 20
}
```

##### Response Status

```json
201
```

##### Response Body

```json
{
  "task_id": 1
}
```

The response contains only the task ID. Use the [Task API](/docs/clients/restful-api/task) to monitor the job.

#### 6.1.2 Monitor Algorithm Job

Use the [Task API](/docs/clients/restful-api/task) to check the status of an algorithm job:

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/tasks/{task_id}
```

#### 6.1.3 Retrieve Algorithm Results

Once the job completes (task_status = "success"), algorithm results are stored as vertex properties. Query vertices to access the results:

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/graph/vertices?filter=properties.{property_name}
```

Common result property names by algorithm:

| Algorithm | Result Property |
|-----------|-----------------|
| pagerank | `page_rank` |
| lpa | `community` |
| wcc | `component` |
| degree_centrality | `degree` |
| closeness_centrality | `closeness` |
| betweenness_centrality | `betweenness` |
| triangle_count | `triangles` |

#### 6.1.4 Supported Algorithms

- `pagerank`: Compute vertex importance scores
- `lpa`: Label Propagation Algorithm for community detection
- `wcc`: Weakly Connected Components
- `degree_centrality`: Vertex connectivity measure
- `closeness_centrality`: Average distance to other vertices
- `betweenness_centrality`: Vertex importance based on shortest paths
- `triangle_count`: Count triangles in the graph

#### 6.1.5 Performance Considerations

For very large graphs (millions+ vertices/edges), consider using [HugeGraph-Computer](/docs/quickstart/computing/hugegraph-computer) or [HugeGraph-Vermeer](/docs/quickstart/computing/hugegraph-vermeer) for distributed computation instead of the REST API.
