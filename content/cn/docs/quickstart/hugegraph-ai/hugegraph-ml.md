---
title: "HugeGraph-ML"
linkTitle: "HugeGraph-ML"
weight: 2
---

HugeGraph-ML 从 HugeGraph 读取图数据并转换为 DGL 图，供节点嵌入、节点分类、图分类、链接预测和欺诈检测等任务使用。模型实现位于 `hugegraph-ml/src/hugegraph_ml/models/`。

## 环境要求

- Python 3.10 或更高版本
- HugeGraph Server 1.0 或更高版本，推荐 1.5 及以上版本
- `uv` 0.7 或更高版本

所有服务端访问都通过同一仓库中的 `hugegraph-python-client`（即 `pyhugegraph` 包）完成。`HugeGraph2DGL` 使用 Gremlin 接口的 `g.V().hasLabel(...)` 和 `g.E().hasLabel(...)` 拉取点边，数据集导入函数则通过 schema 接口和顶点、边的批量接口写入，每批 500 条。

ML 依赖在仓库根目录的 `[tool.uv] constraint-dependencies` 中固定版本：

| 依赖 | 版本约束 |
|---|---|
| `torch` | `==2.2.0` |
| `dgl` | `~=2.1.0` |
| `ogb` | `~=1.3.6` |
| `torchdata` | `~=0.7.0` |
| `catboost` | `~=1.2.3` |
| `category-encoders` | `~=2.6.3` |
| `numpy` | `~=1.24.4` |
| `pandas` | `~=2.2.3` |

上述约束安装的是 CPU 版本。每个任务都有 `gpu` 参数，默认值 `-1` 表示使用 CPU；只有自行安装 CUDA 版的 `torch` 和 `dgl` 之后，才可以传入设备编号。

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

下列模块均位于 `hugegraph-ml/src/hugegraph_ml/models/`。`models/__init__.py` 不做任何再导出，需要直接从模块文件导入。

| 模型 | 模块 | 入口类 | 用途 | 论文 |
|---|---|---|---|---|
| AGNN | `agnn.py` | `AGNN` | 节点分类 | [1803.03735](https://arxiv.org/abs/1803.03735) |
| APPNP | `appnp.py` | `APPNP` | 节点分类 | [1810.05997](https://arxiv.org/abs/1810.05997) |
| ARMA | `arma.py` | `ARMA4NC` | 节点分类 | [1901.01343](https://arxiv.org/abs/1901.01343) |
| BGNN | `bgnn.py` | `BGNNPredictor` | 梯度提升与 GNN 结合处理节点特征，自带示例执行回归任务 | [2101.08543](https://arxiv.org/abs/2101.08543) |
| BGRL | `bgrl.py` | `BGRL` | 自监督节点嵌入 | [2102.06514](https://arxiv.org/abs/2102.06514) |
| CARE-GNN | `care_gnn.py` | `CAREGNN` | 欺诈检测 | [2008.08692](https://arxiv.org/abs/2008.08692) |
| Cluster-GCN | `cluster_gcn.py` | `SAGE` | 基于子图采样的节点分类 | [1905.07953](https://arxiv.org/abs/1905.07953) |
| C&S | `correct_and_smooth.py` | `MLP`、`CorrectAndSmooth`、`LabelPropagation` | 对基础预测结果做校正与平滑 | [2010.13993](https://arxiv.org/abs/2010.13993) |
| DAGNN | `dagnn.py` | `DAGNN` | 节点分类 | [2007.09296](https://arxiv.org/abs/2007.09296) |
| DeeperGCN | `deepergcn.py` | `DeeperGCN` | 带边特征的节点分类 | [2006.07739](https://arxiv.org/abs/2006.07739) |
| DGI | `dgi.py` | `DGI` | 自监督节点嵌入 | [1809.10341](https://arxiv.org/abs/1809.10341) |
| DiffPool | `diffpool.py` | `DiffPool` | 图分类 | [1806.08804](https://arxiv.org/abs/1806.08804) |
| GATNE | `gatne.py` | `DGLGATNE` | 异构网络嵌入 | [1905.01669](https://arxiv.org/abs/1905.01669) |
| GIN | `gin_global_pool.py` | `GIN` | 图分类 | |
| GRACE | `grace.py` | `GRACE` | 自监督节点嵌入 | [2006.04131](https://arxiv.org/abs/2006.04131) |
| GRAND | `grand.py` | `GRAND` | 节点分类 | [2005.11079](https://arxiv.org/abs/2005.11079) |
| JKNet | `jknet.py` | `JKNet` | 节点分类 | [1806.03536](https://arxiv.org/abs/1806.03536) |
| MLP | `mlp.py` | `MLPClassifier` | 基于已学习嵌入的下游分类器 | |
| P-GNN | `pgnn.py` | `PGNN` | 链接预测 | [you19b](http://proceedings.mlr.press/v97/you19b/you19b.pdf) |
| SEAL | `seal.py` | `DGCNN`、`SEALData` | 链接预测 | [1802.09691](https://arxiv.org/abs/1802.09691) |

`GIN` 的 `pooling` 参数可取 `sum`（默认）、`mean`、`max`、`global_attention` 和 `set2set`。

## 读取图数据

`hugegraph-ml/src/hugegraph_ml/data/hugegraph2dgl.py` 中的 `HugeGraph2DGL` 会创建 `PyHugeClient`，并把查询结果转换为 DGL 对象：

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL

hg2d = HugeGraph2DGL(
    url="http://127.0.0.1:8080",
    graph="hugegraph",
    user="",
    pwd="",
    graphspace=None,
)
```

| 方法 | 返回值 | 说明 |
|---|---|---|
| `convert_graph(vertex_label, edge_label, feat_key="feat", label_key="label", mask_keys=None)` | `dgl.DGLGraph` | `mask_keys` 为空时取 `["train_mask", "val_mask", "test_mask"]` |
| `convert_hetero_graph(vertex_labels, edge_labels, feat_key="feat", label_key="label", mask_keys=None)` | DGL 异构图 | 参数为标签列表 |
| `convert_graph_dataset(graph_vertex_label, vertex_label, edge_label, feat_key="feat", label_key="label")` | `HugeGraphDataset` | `info` 中写入 `n_graphs`、`max_n_nodes`、`n_feat_dim`、`n_classes` |
| `convert_graph_nx(vertex_label, edge_label)` | `networkx.Graph` | P-GNN 使用 |
| `convert_graph_with_edge_feat(vertex_label, edge_label, node_feat_key="feat", edge_feat_key="edge_feat", label_key="label", mask_keys=None)` | `dgl.DGLGraph` | 同时填充 `edata["feat"]` |
| `convert_graph_ogb(vertex_label, edge_label, split_label)` | `(dgl.DGLGraph, split_edge)` | SEAL 使用 |
| `convert_hetero_graph_bgnn(vertex_labels, edge_labels, feat_key="feat", label_key="class", cat_key="cat_features", mask_keys=None)` | DGL 异构图 | BGNN 使用 |

节点特征写入 `ndata["feat"]`，标签写入 `ndata["label"]`，各掩码写入 `ndata[<mask key>]`。`NodeEmbed` 只要求 `feat`；`NodeClassify`、`NodeClassifyWithEdge` 和 `NodeClassifyWithSample` 要求 `feat`、`label`、`train_mask`、`val_mask` 和 `test_mask`，缺少任意一项都会抛出 `ValueError`。

## 导入示例数据集

`hugegraph_ml.utils.dgl2hugegraph_utils` 负责把 DGL、OGB 和 NetworkX 数据集写入 HugeGraph，供转换层读取。这些函数都接受与 `HugeGraph2DGL` 相同的 `url`、`graph`、`user`、`pwd` 和 `graphspace` 参数，并且多数会先把数据集名转为大写再匹配。

| 函数 | 支持的数据集 | 创建的标签 |
|---|---|---|
| `import_graph_from_dgl` | `CORA`、`CITESEER`、`PUBMED` | `<NAME>_vertex`、`<NAME>_edge` |
| `import_graphs_from_dgl` | `MUTAG`、`COLLAB`、`NCI1`、`PROTEINS`、`PTC`、`ENZYMES`、`DD` | `<NAME>_graph_vertex`、`<NAME>_vertex`、`<NAME>_edge` |
| `import_hetero_graph_from_dgl` | `ACM` | `<NAME>_<ntype>_v`、`<NAME>_<etype>_e` |
| `import_hetero_graph_from_dgl_no_feat` | `AMAZONGATNE` | `<NAME>_<ntype>_v`、`<NAME>_<etype>_e` |
| `import_hetero_graph_from_dgl_bgnn` | `AVAZU` | `<NAME>_<ntype>_v`、`<NAME>_<etype>_e` |
| `import_graph_from_nx` | `CAVEMAN` | `<NAME>_vertex`、`<NAME>_edge` |
| `import_graph_from_dgl_with_edge_feat` | `CORA`、`CITESEER`、`PUBMED` | `<NAME>_edge_feat_vertex`、`<NAME>_edge_feat_edge` |
| `import_graph_from_ogb` | `ogbl-collab`，不做大写转换 | `<NAME>_vertex`、`<NAME>_edge` |
| `import_split_edge_from_ogb` | `ogbl-collab`，不做大写转换 | `<NAME>_split_edge` |

传入其他名称会抛出 `ValueError("dataset not supported")`。`import_split_edge_from_ogb` 还需要顶点导入返回的 `idx_to_vertex_id` 映射和 `max_nodes` 上限。

`clear_all_data()` 会清空目标图中的全部点和边。测试 fixture 先调用它，再导入 `CORA`、`MUTAG` 和 `ACM`，结束时再次调用。

`AMAZONGATNE` 和 `AVAZU` 不会自动下载，压缩包地址写在 `import_hetero_graph_from_dgl_no_feat` 和 `import_hetero_graph_from_dgl_bgnn` 上方的注释里。

## 任务

任务类位于 `hugegraph-ml/src/hugegraph_ml/tasks/`，均接收转换后的图和模型实例。

| 类 | 模块 | 入口方法 |
|---|---|---|
| `NodeEmbed` | `node_embed.py` | `train_and_embed(add_self_loop=True, lr=1e-3, weight_decay=0, n_epochs=200, patience=inf, gpu=-1)`，返回 `ndata["feat"]` 被替换为嵌入结果的图 |
| `NodeClassify` | `node_classify.py` | 先 `train(lr, weight_decay, n_epochs, patience, early_stopping_monitor, gpu)`，再 `evaluate()` 返回 `{"accuracy": ..., "loss": ...}` |
| `NodeClassifyWithEdge` | `node_classify_with_edge.py` | 结构相同，适用于同时读取 `edata["feat"]` 的模型 |
| `NodeClassifyWithSample` | `node_classify_with_sample.py` | 基于 `ClusterGCNSampler` 分区的训练，仅使用 CPU，没有 `gpu` 参数 |
| `GraphClassify` | `graph_classify.py` | `train(batch_size=20, lr, weight_decay, n_epochs, patience, early_stopping_monitor, clip=2.0, gpu)`，在 `HugeGraphDataset` 上按 70/20/10 划分 |
| `DetectorCaregnn` | `fraud_detector_caregnn.py` | CARE-GNN 训练，`evaluate()` 输出 recall 和 ROC AUC，并读取 `ndata["feature"]` 而非 `ndata["feat"]` |
| `HeteroSampleEmbedGATNE` | `hetero_sample_embed_gatne.py` | `train_and_embed(lr=1e-3, n_epochs=200, gpu=-1)` |
| `LinkPredictionPGNN` | `link_prediction_pgnn.py` | `train(lr, weight_decay, n_epochs, gpu)` |
| `LinkPredictionSeal` | `link_prediction_seal.py` | 构造函数内部已调用 `data_prepare()`，随后执行 `train(lr=1e-3, n_epochs=200, gpu=-1)` |

`patience` 默认值为 `float("inf")`。`utils/early_stopping.py` 中的 `EarlyStopping` 可以监控 `loss` 或 `accuracy`，保存最优权重并在训练结束时恢复。

## 可运行示例

脚本位于 `hugegraph-ml/src/hugegraph_ml/examples/`。在 `hugegraph-ml/src` 目录下执行：

```bash
python ./hugegraph_ml/examples/dgi_example.py
```

每个脚本同时提供同名函数，可以导入后用较小的 epoch 数调用。

| 脚本 | 模型 | 任务 | 读取的标签 |
|---|---|---|---|
| `agnn_example.py` | `AGNN` | `NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `appnp_example.py` | `APPNP` | `NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `arma_example.py` | `ARMA4NC` | `NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `bgnn_example.py` | `BGNNPredictor` | 模型自带的 `fit()` | `AVAZU__N_v`、`AVAZU__E_e` |
| `bgrl_example.py` | `BGRL` | `NodeEmbed`、`NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `care_gnn_example.py` | `CAREGNN` | `DetectorCaregnn` | `AMAZON_user_v` 以及 `AMAZON_net_upu_e`、`AMAZON_net_usu_e`、`AMAZON_net_uvu_e` |
| `cluster_gcn_example.py` | `SAGE` | `NodeClassifyWithSample` | `CORA_vertex`、`CORA_edge` |
| `correct_and_smooth_example.py` | `correct_and_smooth` 中的 `MLP` | `NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `dagnn_example.py` | `DAGNN` | `NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `deepergcn_example.py` | `DeeperGCN` | `NodeClassifyWithEdge` | 通过 `convert_graph_with_edge_feat` 读取 `CORA_vertex`、`CORA_edge` |
| `dgi_example.py` | `DGI` | `NodeEmbed`、`NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `diffpool_example.py` | `DiffPool` | `GraphClassify` | `MUTAG_graph_vertex`、`MUTAG_vertex`、`MUTAG_edge` |
| `gatne_example.py` | `DGLGATNE` | `HeteroSampleEmbedGATNE` | `AMAZONGATNE__N_v`、`AMAZONGATNE_1_e`、`AMAZONGATNE_2_e` |
| `gin_example.py` | `GIN` | `GraphClassify` | `MUTAG_graph_vertex`、`MUTAG_vertex`、`MUTAG_edge` |
| `grace_example.py` | `GRACE` | `NodeEmbed`、`NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `grand_example.py` | `GRAND` | `NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `jknet_example.py` | `JKNet` | `NodeClassify` | `CORA_vertex`、`CORA_edge` |
| `pgnn_example.py` | `PGNN` | `LinkPredictionPGNN` | `CAVEMAN_vertex`、`CAVEMAN_edge` |
| `seal_example.py` | `DGCNN` | `LinkPredictionSeal` | `ogbl-collab_vertex`、`ogbl-collab_edge`、`ogbl-collab_split_edge` |

## DGI 节点嵌入示例

先把 DGL 的 Cora 数据集导入 HugeGraph。数据集名会先转为大写，因此 `cora` 和 `CORA` 都会生成 `CORA_vertex` 和 `CORA_edge` 标签：

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

`evaluate()` 返回类似 `{'accuracy': 0.82, 'loss': 0.5714246034622192}` 的字典。完整脚本是 `hugegraph-ml/src/hugegraph_ml/examples/dgi_example.py`。

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

GRAND 每次增强采样都会返回一组 logits，`NodeClassify` 会对列表中的每个元素分别应用掩码后再计算损失。完整脚本是 `hugegraph-ml/src/hugegraph_ml/examples/grand_example.py`。

## 排查问题

- 连接失败：检查 HugeGraph Server 地址、端口和认证信息。
- Schema 不匹配：示例默认使用 `CORA_vertex` 和 `CORA_edge`，自有数据需要传入实际标签。
- `ValueError: Graph is missing required node attribute ...`：节点分类任务需要 `ndata` 中包含 `feat`、`label`、`train_mask`、`val_mask` 和 `test_mask`。请导入带掩码的数据集，或给 `convert_graph` 传入自定义的 `mask_keys`。
- `ValueError: dataset not supported`：导入函数只接受上表列出的名称，且 `import_graph_from_ogb` 匹配 `ogbl-collab` 时不做大写转换。
- DGL 或 PyTorch 导入失败：回到仓库根目录重新执行 `uv sync --extra ml`，并确认当前 Python 来自根目录 `.venv`。
- `bgrl_example.py` 目前在导入阶段就会失败：它从 `hugegraph_ml.models.bgrl` 导入 `MLP_Predictor`，而该模块中的类名是 `MLPPredictor`。
- `care_gnn_example.py` 读取 `AMAZON_user_v` 和三个 `AMAZON_net_*_e` 边标签，仓库内没有对应的导入函数，需要自行准备该数据集后再运行。
