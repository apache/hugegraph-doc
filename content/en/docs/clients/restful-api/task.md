---
title: "Task API"
linkTitle: "Task"
weight: 13
description: "Task REST API: Query and manage asynchronous task execution status for long-running operations like index rebuilding and graph traversals."
---

### 7.1 Task

#### 7.1.1 List all async tasks in graph

##### Params

- status: the status of asyncTasks, one of NEW, SCHEDULING, SCHEDULED, QUEUED, RESTORING, RUNNING, SUCCESS, CANCELLING, CANCELLED, FAILED, HANGING, DELETING, case-insensitive
- ids: task ids to query, can be repeated. It can not be combined with `status` or `page`, and it ignores `limit`.
- limit: the max number of tasks to return, default is 100
- page: page token for pagination. When it is passed, the response carries a `page` field with the token of the next page.

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks?status=success
```

##### Response Status

```json
200
```

##### Response Body

```json
{
	"tasks": [{
		"task_name": "hugegraph.traversal().V()",
		"task_progress": 0,
		"task_create": 1532943976585,
		"task_status": "success",
		"task_update": 1532943976736,
		"task_result": "0",
		"task_retries": 0,
		"id": 2,
		"task_type": "gremlin",
		"task_callable": "org.apache.hugegraph.api.job.GremlinAPI$GremlinJob",
		"task_input": "{\"gremlin\":\"hugegraph.traversal().V()\",\"bindings\":{},\"language\":\"gremlin-groovy\",\"aliases\":{\"hugegraph\":\"graph\"}}"
	}]
}
```

#### 7.1.2 View the details of an async task

##### Params

- with_result: whether to load the result of the task, default is true

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/2
```

##### Response Status

```json
200
```

##### Response Body

```json
{
	"task_name": "hugegraph.traversal().V()",
	"task_progress": 0,
	"task_create": 1532943976585,
	"task_status": "success",
	"task_update": 1532943976736,
	"task_result": "0",
	"task_retries": 0,
	"id": 2,
	"task_type": "gremlin",
	"task_callable": "org.apache.hugegraph.api.job.GremlinAPI$GremlinJob",
	"task_input": "{\"gremlin\":\"hugegraph.traversal().V()\",\"bindings\":{},\"language\":\"gremlin-groovy\",\"aliases\":{\"hugegraph\":\"graph\"}}"
}
```

#### 7.1.3 Delete task information of an async task,**won't delete the task itself**

##### Params

- force: whether to delete the task even when it is still running, default is false

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/2
```

##### Response Status

```json
204
```

#### 7.1.4 Cancel an async task, **the task should be able to be canceled**

If you already created an async task via [Gremlin API](/docs/clients/restful-api/gremlin) as follows:

```groovy
"for (int i = 0; i < 10; i++) {" +
    "hugegraph.addVertex(T.label, 'man');" +
    "hugegraph.tx().commit();" +
    "try {" +
        "sleep(1000);" +
    "} catch (InterruptedException e) {" +
        "break;" +
    "}" +
"}"
```

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/2?action=cancel
```
> cancel it in 10s. if more than 10s, the task may already be finished, then can't be cancelled.

##### Response Status

```json
202
```

Cancelling a task that is already completed or already cancelling returns `400`.

##### Response Body

The whole task object is returned, with `task_status` set to `cancelling` or `cancelled`:

```json
{
	"task_name": "for (int i = 0; i < 10; i++) {...}",
	"task_progress": 0,
	"task_create": 1532943976585,
	"task_status": "cancelling",
	"task_update": 1532943977001,
	"task_retries": 0,
	"id": 2,
	"task_type": "gremlin",
	"task_callable": "org.apache.hugegraph.api.job.GremlinAPI$GremlinJob"
}
```

At this point, the number of vertices whose label is man must be less than 10.

### 7.2 Algorithm Job

Schedules an OLAP algorithm as an asynchronous task inside the server. The task id in the response can be followed with the Task API above.

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name
- name: Algorithm name. The registered algorithms are `count_vertex`, `count_edge`, `degree_centrality`, `stress_centrality`, `betweenness_centrality`, `closeness_centrality`, `eigenvector_centrality`, `triangle_count`, `cluster_coefficient`, `lpa`, `louvain`, `weak_connected_component`, `fusiform_similarity`, `rings`, `k_core`, `page_rank` and `subgraph_stat`. An unknown name returns `404`.

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/algorithm/page_rank
```

##### Request Body

The body is the parameter map of the algorithm, and each algorithm validates its own parameters. Pass `{}` to run with the defaults.

```json
{
    "alpha": 0.15,
    "times": 10
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

### 7.3 Computer Job

Schedules a HugeGraph-Computer job as an asynchronous task. The computer job runs outside the server, see [HugeGraph-Computer](/docs/quickstart/computing/hugegraph-computer).

##### Params

**Path parameters**

- graphspace: Graphspace name
- graph: Graph name
- name: Computer name. The registered computers are `page_rank`, `weak_connected_component`, `lpa`, `triangle_count` and `louvain`. An unknown name returns `404`.

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/computer/page_rank
```

##### Request Body

The body is the parameter map of the computer job. Pass `{}` to run with the defaults.

```json
{}
```

##### Response Status

```json
201
```

##### Response Body

```json
{
    "task_id": 2
}
```
