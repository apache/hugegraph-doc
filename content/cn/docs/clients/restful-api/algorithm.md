---
title: "算法 API"
linkTitle: "算法"
weight: 12.5
description: "算法任务 REST API：提交和监控异步图算法任务。"
---

## 6.2 算法

算法 API 允许提交长时间运行的图算法作为异步任务并跟踪其进度。

### 6.2.1 提交算法任务

#### 方法与 URL

```bash
POST http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/jobs/algorithm/{algorithm_name}
```

对于旧版没有图空间的设置：

```bash
POST http://localhost:8080/graphs/{graph}/jobs/algorithm/{algorithm_name}
```

#### 请求体

请求体因算法而异。常见参数包括：

- `max_iteration`: 最大迭代次数（用于 LPA 等迭代算法）
- `alpha`: PageRank 的阻尼因子（默认值：0.85）
- `sample_rate`: 采样率，用于 betweenness_centrality 等算法（0-1）
- `direction`: 边遍历方向（OUT、IN 或 BOTH）

#### 示例：提交 PageRank 任务

```json
{
  "alpha": 0.85,
  "max_iteration": 20
}
```

#### 响应状态

```json
201
```

#### 响应体

```json
{
  "task_id": 1
}
```

响应仅包含任务 ID。使用 [任务 API](./task) 监控任务。

### 6.2.2 监控算法任务

使用 [任务 API](./task) 检查算法任务的状态：

```bash
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/tasks/{task_id}
```

### 6.2.3 检索算法结果

响应体是算法相关的。有些算法直接返回 JSON，有些算法还会把结果写回到顶点属性。

示例：

- `page_rank` 会把排名写入 `r_rank` 顶点属性。
- `lpa` 和 `weak_connected_component` 会把社区标签写入 `c_label` 顶点属性。

这些名称来自算法任务实现，可能与 HugeGraph 其他组件使用的属性名不同。

如果某个任务会写回顶点，请使用常规的 Vertex API，并按照算法更新的属性进行查询。

例如，要查找 PageRank 大于 0 的顶点，可以使用：

```bash
GET http://localhost:8080/graphspaces/DEFAULT/graphs/{graph}/graph/vertices?properties={"r_rank":"P.gt(0)"}
```

### 6.2.4 支持的算法

服务端在 `AlgorithmPool` 中注册了以下算法名称：

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

### 6.2.5 性能考虑

对于非常大的图（数百万+个顶点/边），考虑使用 [HugeGraph-Computer](/cn/docs/quickstart/computing/hugegraph-computer) 或 [HugeGraph-Vermeer](/cn/docs/quickstart/computing/hugegraph-vermeer) 进行分布式计算，而不是 REST API。
