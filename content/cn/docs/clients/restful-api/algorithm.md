---
title: "算法 API"
linkTitle: "算法"
weight: 11
description: "算法任务 REST API：提交和监控异步图算法任务。"
---

### 6.1 算法

算法 API 允许提交长时间运行的图算法作为异步任务并跟踪其进度。

#### 6.1.1 提交算法任务

##### 方法与 URL

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/jobs/algorithm/{algorithm_name}
```

对于旧版没有图空间的设置：
```
POST http://localhost:8080/graphs/{graph}/jobs/algorithm/{algorithm_name}
```

##### 请求体

请求体因算法而异。常见参数包括：

- `max_iteration`: 最大迭代次数（用于 LPA 等迭代算法）
- `alpha`: PageRank 的阻尼因子（默认值：0.85）
- `sample_rate`: 采样率，用于 betweenness_centrality 等算法（0-1）
- `direction`: 边遍历方向（OUT、IN 或 BOTH）

##### 示例：提交 PageRank 任务

```json
{
  "alpha": 0.85,
  "max_iteration": 20
}
```

##### 响应状态

```json
201
```

##### 响应体

```json
{
  "task_id": 1
}
```

响应仅包含任务 ID。使用 [任务 API](/docs/clients/restful-api/task) 监控任务。

#### 6.1.2 监控算法任务

使用 [任务 API](/docs/clients/restful-api/task) 检查算法任务的状态：

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/tasks/{task_id}
```

#### 6.1.3 检索算法结果

任务完成后（task_status = "success"），算法结果作为顶点属性存储。查询顶点以访问结果：

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/graph/vertices?filter=properties.{property_name}
```

按算法的常见结果属性名称：

| 算法 | 结果属性 |
|------|----------|
| pagerank | `page_rank` |
| lpa | `community` |
| wcc | `component` |
| degree_centrality | `degree` |
| closeness_centrality | `closeness` |
| betweenness_centrality | `betweenness` |
| triangle_count | `triangles` |

#### 6.1.4 支持的算法

- `pagerank`: 计算顶点重要性分数
- `lpa`: 用于社区检测的标签传播算法
- `wcc`: 弱连通分量
- `degree_centrality`: 顶点连通性度量
- `closeness_centrality`: 到其他顶点的平均距离
- `betweenness_centrality`: 基于最短路径的顶点重要性
- `triangle_count`: 计算图中的三角形

#### 6.1.5 性能考虑

对于非常大的图（数百万+个顶点/边），考虑使用 [HugeGraph-Computer](/docs/quickstart/computing/hugegraph-computer) 或 [HugeGraph-Vermeer](/docs/quickstart/computing/hugegraph-vermeer) 进行分布式计算，而不是 REST API。
