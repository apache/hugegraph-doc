---
title: "Task API"
linkTitle: "Task"
weight: 13
description: "Task（任务管理）REST 接口:查询和管理异步任务的执行状态,如索引重建、图遍历等长时任务。"
---

### 7.1 Task

#### 7.1.1 列出某个图中全部的异步任务

##### Params

- status: 异步任务的状态
- limit：返回异步任务数目上限

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

##### Response Body

```json
{
    "cancelled": true
}
```

此时查询 label 为 man 的顶点数目，一定是小于 10 的。
