# Rebuild API

LLMS 索引： [llms.txt](/versions/1.5/cn/llms.txt)

---

### 1.6 Rebuild

#### 1.6.1 重建IndexLabel

##### Method & Url

```
PUT http://localhost:8080/graphs/hugegraph/jobs/rebuild/indexlabels/personByCity
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

> 可以通过`GET http://localhost:8080/graphs/hugegraph/tasks/1`（其中"1"是task_id）来查询异步任务的执行状态，更多[异步任务RESTful API](../task)

#### 1.6.2 VertexLabel对应的全部索引重建

##### Method & Url

```
PUT http://localhost:8080/graphs/hugegraph/jobs/rebuild/vertexlabels/person
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

> 可以通过`GET http://localhost:8080/graphs/hugegraph/tasks/2`（其中"2"是task_id）来查询异步任务的执行状态，更多[异步任务RESTful API](../task)

#### 1.6.3 EdgeLabel对应的全部索引重建

##### Method & Url

```
PUT http://localhost:8080/graphs/hugegraph/jobs/rebuild/edgelabels/created
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

> 可以通过`GET http://localhost:8080/graphs/hugegraph/tasks/3`（其中"3"是task_id）来查询异步任务的执行状态，更多[异步任务RESTful API](../task)
