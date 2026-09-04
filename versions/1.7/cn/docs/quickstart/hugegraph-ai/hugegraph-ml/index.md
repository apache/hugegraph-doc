# HugeGraph-ML

LLMS 索引： [llms.txt](/versions/1.7/cn/llms.txt)

---

HugeGraph-ML 从 HugeGraph 读取图数据并转换为 DGL 图，供节点嵌入、节点分类和图分类等任务使用。模型实现位于 `hugegraph-ml/src/hugegraph_ml/models/`。

## 环境要求

- Python 3.10 或更高版本
- HugeGraph Server 1.0 或更高版本，推荐 1.5 及以上版本
- `uv` 0.7 或更高版本

## 安装

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra ml
source .venv/bin/activate
cd hugegraph-ml/src
```

HugeGraph-ML 是根项目的路径依赖，但不属于 `uv` workspace members。应在仓库根目录选择 `ml` extra，不要在子目录建立另一套锁文件。

## 已实现模型

当前 README 列出的模型如下：

| 模型 | 主要用途 |
|---|---|
| AGNN、APPNP、ARMA、Cluster-GCN、DAGNN、DeeperGCN、GRAND、JKNet | 节点分类 |
| BGNN、CARE-GNN | 欺诈检测 |
| BGRL、DGI、GRACE | 表示学习 |
| DiffPool | 图分类 |
| GATNE、P-GNN、SEAL | 链接预测或网络嵌入 |
| C&S | 预测结果校正与平滑 |

源码中还包含 `GIN` 图分类实现和供下游分类使用的 `MLPClassifier`。模型数量会随版本变化，以 `src/hugegraph_ml/models/` 为准。

## DGI 节点嵌入示例

先把 DGL 的 Cora 数据集导入 HugeGraph：

```python
from hugegraph_ml.utils.dgl2hugegraph_utils import import_graph_from_dgl

import_graph_from_dgl("cora")
```

读取图并训练 DGI：

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL
from hugegraph_ml.models.dgi import DGI
from hugegraph_ml.models.mlp import MLPClassifier
from hugegraph_ml.tasks.node_classify import NodeClassify
from hugegraph_ml.tasks.node_embed import NodeEmbed

hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(
    vertex_label="CORA_vertex",
    edge_label="CORA_edge",
)

embed_model = DGI(n_in_feats=graph.ndata["feat"].shape[1])
embed_task = NodeEmbed(graph=graph, model=embed_model)
embedded_graph = embed_task.train_and_embed(
    add_self_loop=True,
    n_epochs=300,
    patience=30,
)

classifier = MLPClassifier(
    n_in_feat=embedded_graph.ndata["feat"].shape[1],
    n_out_feat=embedded_graph.ndata["label"].unique().shape[0],
)
classify_task = NodeClassify(graph=embedded_graph, model=classifier)
classify_task.train(lr=1e-3, n_epochs=400, patience=40)
print(classify_task.evaluate())
```

完整脚本是 `hugegraph-ml/src/hugegraph_ml/examples/dgi_example.py`。

## GRAND 节点分类示例

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL
from hugegraph_ml.models.grand import GRAND
from hugegraph_ml.tasks.node_classify import NodeClassify

hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(
    vertex_label="CORA_vertex",
    edge_label="CORA_edge",
)
model = GRAND(
    n_in_feats=graph.ndata["feat"].shape[1],
    n_out_feats=graph.ndata["label"].unique().shape[0],
)
task = NodeClassify(graph, model)
task.train(lr=1e-2, weight_decay=5e-4, n_epochs=2000, patience=100)
print(task.evaluate())
```

完整脚本是 `hugegraph-ml/src/hugegraph_ml/examples/grand_example.py`。

## 排查问题

- 连接失败：检查 HugeGraph Server 地址、端口和认证信息。
- Schema 不匹配：示例默认使用 `CORA_vertex` 和 `CORA_edge`，自有数据需要传入实际标签。
- DGL 或 PyTorch 导入失败：回到仓库根目录重新执行 `uv sync --extra ml`，并确认当前 Python 来自根目录 `.venv`。
