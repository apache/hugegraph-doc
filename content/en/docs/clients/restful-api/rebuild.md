---
title: "Rebuild API"
linkTitle: "Rebuild"
weight: 6
description: "Rebuild REST API: Rebuild graph schema indexes to ensure consistency between index data and graph data."
---

### 1.6 Rebuild

#### 1.6.1 Rebuild IndexLabel

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/rebuild/indexlabels/personByCity
```

##### Response Status

```json
202
```

##### Response Body

```json
{
    "task_id": 1
}
```
Note:

> You can get the asynchronous job status by `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/${task_id}` (the task_id here should be 1). See More [AsyncJob RESTfull API](./task)

#### 1.6.2 Rebulid all Indexs of VertexLabel

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/rebuild/vertexlabels/person
```

##### Response Status

```json
202
```

##### Response Body

```json
{
    "task_id": 2
}
```

Note:

> You can get the asynchronous job status by `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/${task_id}` (the task_id here should be 2). See More [AsyncJob RESTfull API](./task)

#### 1.6.3 Rebulid all Indexs of EdgeLabel

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/jobs/rebuild/edgelabels/created
```

##### Response Status

```json
202
```

##### Response Body

```json
{
    "task_id": 3
}
```

Note:

> You can get the asynchronous job status by `GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/${task_id}` (the task_id here should be 3). See More [AsyncJob RESTfull API](./task)