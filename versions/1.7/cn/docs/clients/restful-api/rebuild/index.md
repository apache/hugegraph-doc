# Rebuild API

LLMS 索引： [llms.txt](/versions/1.7/cn/llms.txt)

---

### 1.6 Rebuild

#### 1.6.1 重建 IndexLabel

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

注：

> 可以通过`GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/1`（其中"1"是 task_id）来查询异步任务的执行状态，更多[异步任务 RESTful API](../task)

#### 1.6.2 VertexLabel 对应的全部索引重建

##### Method & Url

```http request
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

注：

> 可以通过`GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/2`（其中"2"是 task_id）来查询异步任务的执行状态，更多[异步任务 RESTful API](../task)

#### 1.6.3 EdgeLabel 对应的全部索引重建

##### Method & Url

```http request
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

注：

> 可以通过`GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/tasks/3`（其中"3"是 task_id）来查询异步任务的执行状态，更多[异步任务 RESTful API](../task)
