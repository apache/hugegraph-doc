---
title: "Task API"
linkTitle: "Task"
weight: 13
description: "Task REST API: Query and manage asynchronous task execution status for long-running operations like index rebuilding and graph traversals."
---

### 7.1 Task

#### 7.1.1 List all async tasks in graph

##### Params

- status: the status of asyncTasks
- limit: the max number of tasks to return

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

##### Response Body

```json
{
    "cancelled": true
}
```

At this point, the number of vertices whose label is man must be less than 10.