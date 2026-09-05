---
title: "Task API"
linkTitle: "Task"
weight: 13
description: "Task（任务管理）REST 接口:查询和管理异步任务的执行状态,如索引重建、图遍历等长时任务。"
---

### 7.1 Task

#### 7.1.1 列出某个图中全部的异步任务

##### Params

- status: 异步任务的状态，取值为 NEW、SCHEDULING、SCHEDULED、QUEUED、RESTORING、RUNNING、SUCCESS、CANCELLING、CANCELLED、FAILED、HANGING、DELETING 之一，不区分大小写
- ids: 需要查询的任务 id，可以重复传多个。不能与 `status` 或 `page` 同时使用，并且会忽略 `limit`
- limit：返回异步任务数目上限，默认为 100
- page: 分页的页标记，传该参数时响应中会带上下一页的 `page` 字段

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

#### 7.1.2 查看某个异步任务的信息

##### Params

- with_result: 是否加载任务的结果，默认为 true

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

#### 7.1.3 删除某个异步任务信息，**不删除异步任务本身**

##### Params

- force: 任务仍在运行时是否强制删除，默认为 false

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/2
```

##### Response Status

```json
204
```

#### 7.1.4 取消某个异步任务，**该异步任务必须具有处理中断的能力**

假设已经通过[Gremlin API](/cn/docs/clients/restful-api/gremlin)创建了一个异步任务如下：

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

> 请保证在 10 秒内发送该请求，如果超过 10 秒发送，任务可能已经执行完成，无法取消。

##### Response Status

```json
202
```

对已经完成或者正在取消中的任务发起取消会返回 `400`。

##### Response Body

返回整个任务对象，其中 `task_status` 为 `cancelling` 或 `cancelled`：

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

此时查询 label 为 man 的顶点数目，一定是小于 10 的。

### 7.2 Algorithm Job

在服务内部以异步任务的方式调度一个 OLAP 算法，返回的 task id 可以用上面的 Task API 跟踪。

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称
- name: 算法名称，已注册的算法有 `count_vertex`、`count_edge`、`degree_centrality`、`stress_centrality`、`betweenness_centrality`、`closeness_centrality`、`eigenvector_centrality`、`triangle_count`、`cluster_coefficient`、`lpa`、`louvain`、`weak_connected_component`、`fusiform_similarity`、`rings`、`k_core`、`page_rank` 和 `subgraph_stat`。名称不存在时返回 `404`。

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/algorithm/page_rank
```

##### Request Body

请求体是算法的参数集合，每个算法各自校验自己的参数。传 `{}` 表示全部使用默认值。

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

以异步任务的方式调度一个 HugeGraph-Computer 作业。该作业在服务外部执行，参见 [HugeGraph-Computer](/cn/docs/quickstart/computing/hugegraph-computer)。

##### Params

**路径参数说明：**

- graphspace: 图空间名称
- graph: 图名称
- name: 算法名称，已注册的有 `page_rank`、`weak_connected_component`、`lpa`、`triangle_count` 和 `louvain`。名称不存在时返回 `404`。

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/computer/page_rank
```

##### Request Body

请求体是作业的参数集合，传 `{}` 表示全部使用默认值。

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
