---
title: "HugeGraph-ML"
linkTitle: "HugeGraph-ML"
weight: 2
---

HugeGraph-ML reads graph data from HugeGraph and converts it to DGL graphs for tasks such as node embedding, node classification, graph classification, link prediction and fraud detection. Model implementations are under `hugegraph-ml/src/hugegraph_ml/models/`.

## Requirements

- Python 3.10 or later
- HugeGraph Server 1.0 or later; 1.5 or later is recommended
- `uv` 0.7 or later

All server access goes through `hugegraph-python-client` (the `pyhugegraph` package) from the same repository. `HugeGraph2DGL` pulls vertices and edges over the Gremlin endpoint with `g.V().hasLabel(...)` and `g.E().hasLabel(...)`, and the dataset importers write through the schema and batch vertex/edge APIs in batches of 500.

The ML stack is version pinned at the repository root under `[tool.uv] constraint-dependencies`:

| Package | Pin |
|---|---|
| `torch` | `==2.2.0` |
| `dgl` | `~=2.1.0` |
| `ogb` | `~=1.3.6` |
| `torchdata` | `~=0.7.0` |
| `catboost` | `~=1.2.3` |
| `category-encoders` | `~=2.6.3` |
| `numpy` | `~=1.24.4` |
| `pandas` | `~=2.2.3` |

Those pins install CPU builds. Every task accepts a `gpu` argument that defaults to `-1`, meaning CPU; pass a device index only after installing CUDA builds of `torch` and `dgl` yourself.

## Installation

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai
uv sync --extra ml
source .venv/bin/activate
cd hugegraph-ml/src
```

HugeGraph-ML is a path dependency of the root project but is not a `uv` workspace member. Select the `ml` extra at the repository root instead of creating another lock file in the subdirectory.

## Implemented Models

Every module below lives in `hugegraph-ml/src/hugegraph_ml/models/`. `models/__init__.py` re-exports nothing, so import from the module file directly.

| Model | Module | Entry class | Used for | Paper |
|---|---|---|---|---|
| AGNN | `agnn.py` | `AGNN` | Node classification | [1803.03735](https://arxiv.org/abs/1803.03735) |
| APPNP | `appnp.py` | `APPNP` | Node classification | [1810.05997](https://arxiv.org/abs/1810.05997) |
| ARMA | `arma.py` | `ARMA4NC` | Node classification | [1901.01343](https://arxiv.org/abs/1901.01343) |
| BGNN | `bgnn.py` | `BGNNPredictor` | Gradient boosting over node features combined with a GNN; the bundled example runs regression | [2101.08543](https://arxiv.org/abs/2101.08543) |
| BGRL | `bgrl.py` | `BGRL` | Self-supervised node embedding | [2102.06514](https://arxiv.org/abs/2102.06514) |
| CARE-GNN | `care_gnn.py` | `CAREGNN` | Fraud detection | [2008.08692](https://arxiv.org/abs/2008.08692) |
| Cluster-GCN | `cluster_gcn.py` | `SAGE` | Node classification with subgraph sampling | [1905.07953](https://arxiv.org/abs/1905.07953) |
| C&S | `correct_and_smooth.py` | `MLP`, `CorrectAndSmooth`, `LabelPropagation` | Correcting and smoothing base predictions | [2010.13993](https://arxiv.org/abs/2010.13993) |
| DAGNN | `dagnn.py` | `DAGNN` | Node classification | [2007.09296](https://arxiv.org/abs/2007.09296) |
| DeeperGCN | `deepergcn.py` | `DeeperGCN` | Node classification with edge features | [2006.07739](https://arxiv.org/abs/2006.07739) |
| DGI | `dgi.py` | `DGI` | Self-supervised node embedding | [1809.10341](https://arxiv.org/abs/1809.10341) |
| DiffPool | `diffpool.py` | `DiffPool` | Graph classification | [1806.08804](https://arxiv.org/abs/1806.08804) |
| GATNE | `gatne.py` | `DGLGATNE` | Heterogeneous network embedding | [1905.01669](https://arxiv.org/abs/1905.01669) |
| GIN | `gin_global_pool.py` | `GIN` | Graph classification | |
| GRACE | `grace.py` | `GRACE` | Self-supervised node embedding | [2006.04131](https://arxiv.org/abs/2006.04131) |
| GRAND | `grand.py` | `GRAND` | Node classification | [2005.11079](https://arxiv.org/abs/2005.11079) |
| JKNet | `jknet.py` | `JKNet` | Node classification | [1806.03536](https://arxiv.org/abs/1806.03536) |
| MLP | `mlp.py` | `MLPClassifier` | Downstream classifier over learned embeddings | |
| P-GNN | `pgnn.py` | `PGNN` | Link prediction | [you19b](http://proceedings.mlr.press/v97/you19b/you19b.pdf) |
| SEAL | `seal.py` | `DGCNN`, `SEALData` | Link prediction | [1802.09691](https://arxiv.org/abs/1802.09691) |

`GIN` accepts `pooling` values `sum` (default), `mean`, `max`, `global_attention` and `set2set`.

## Reading Graph Data

`HugeGraph2DGL` in `hugegraph-ml/src/hugegraph_ml/data/hugegraph2dgl.py` opens a `PyHugeClient` and converts query results into DGL objects:

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

| Method | Returns | Notes |
|---|---|---|
| `convert_graph(vertex_label, edge_label, feat_key="feat", label_key="label", mask_keys=None)` | `dgl.DGLGraph` | `mask_keys` falls back to `["train_mask", "val_mask", "test_mask"]` |
| `convert_hetero_graph(vertex_labels, edge_labels, feat_key="feat", label_key="label", mask_keys=None)` | DGL heterograph | Takes lists of labels |
| `convert_graph_dataset(graph_vertex_label, vertex_label, edge_label, feat_key="feat", label_key="label")` | `HugeGraphDataset` | Fills `info` with `n_graphs`, `max_n_nodes`, `n_feat_dim`, `n_classes` |
| `convert_graph_nx(vertex_label, edge_label)` | `networkx.Graph` | Used by P-GNN |
| `convert_graph_with_edge_feat(vertex_label, edge_label, node_feat_key="feat", edge_feat_key="edge_feat", label_key="label", mask_keys=None)` | `dgl.DGLGraph` | Also fills `edata["feat"]` |
| `convert_graph_ogb(vertex_label, edge_label, split_label)` | `(dgl.DGLGraph, split_edge)` | Used by SEAL |
| `convert_hetero_graph_bgnn(vertex_labels, edge_labels, feat_key="feat", label_key="class", cat_key="cat_features", mask_keys=None)` | DGL heterograph | Used by BGNN |

Node features land in `ndata["feat"]`, labels in `ndata["label"]` and each mask in `ndata[<mask key>]`. `NodeEmbed` requires `feat` only; `NodeClassify`, `NodeClassifyWithEdge` and `NodeClassifyWithSample` require `feat`, `label`, `train_mask`, `val_mask` and `test_mask` and raise `ValueError` when one is missing.

## Importing Sample Datasets

`hugegraph_ml.utils.dgl2hugegraph_utils` writes DGL, OGB and NetworkX datasets into HugeGraph so the conversion layer has something to read. Every function takes the same `url`, `graph`, `user`, `pwd` and `graphspace` arguments as `HugeGraph2DGL`, and most upper-case the dataset name before matching it.

| Function | Accepted datasets | Labels created |
|---|---|---|
| `import_graph_from_dgl` | `CORA`, `CITESEER`, `PUBMED` | `<NAME>_vertex`, `<NAME>_edge` |
| `import_graphs_from_dgl` | `MUTAG`, `COLLAB`, `NCI1`, `PROTEINS`, `PTC`, `ENZYMES`, `DD` | `<NAME>_graph_vertex`, `<NAME>_vertex`, `<NAME>_edge` |
| `import_hetero_graph_from_dgl` | `ACM` | `<NAME>_<ntype>_v`, `<NAME>_<etype>_e` |
| `import_hetero_graph_from_dgl_no_feat` | `AMAZONGATNE` | `<NAME>_<ntype>_v`, `<NAME>_<etype>_e` |
| `import_hetero_graph_from_dgl_bgnn` | `AVAZU` | `<NAME>_<ntype>_v`, `<NAME>_<etype>_e` |
| `import_graph_from_nx` | `CAVEMAN` | `<NAME>_vertex`, `<NAME>_edge` |
| `import_graph_from_dgl_with_edge_feat` | `CORA`, `CITESEER`, `PUBMED` | `<NAME>_edge_feat_vertex`, `<NAME>_edge_feat_edge` |
| `import_graph_from_ogb` | `ogbl-collab`, matched without upper-casing | `<NAME>_vertex`, `<NAME>_edge` |
| `import_split_edge_from_ogb` | `ogbl-collab`, matched without upper-casing | `<NAME>_split_edge` |

Any other name raises `ValueError("dataset not supported")`. `import_split_edge_from_ogb` additionally requires the `idx_to_vertex_id` mapping and a `max_nodes` cap returned by the vertex import.

`clear_all_data()` drops every vertex and edge in the target graph. The test fixture calls it, loads `CORA`, `MUTAG` and `ACM`, and calls it again on teardown.

`AMAZONGATNE` and `AVAZU` are not fetched automatically. Their archive URLs are recorded in comments above `import_hetero_graph_from_dgl_no_feat` and `import_hetero_graph_from_dgl_bgnn`.

## Tasks

Task classes live in `hugegraph-ml/src/hugegraph_ml/tasks/`. Each one takes the converted graph and a model instance.

| Class | Module | Entry points |
|---|---|---|
| `NodeEmbed` | `node_embed.py` | `train_and_embed(add_self_loop=True, lr=1e-3, weight_decay=0, n_epochs=200, patience=inf, gpu=-1)` returns the graph with `ndata["feat"]` replaced by the embedding |
| `NodeClassify` | `node_classify.py` | `train(lr, weight_decay, n_epochs, patience, early_stopping_monitor, gpu)` then `evaluate()`, which returns `{"accuracy": ..., "loss": ...}` |
| `NodeClassifyWithEdge` | `node_classify_with_edge.py` | Same shape, for models that also read `edata["feat"]` |
| `NodeClassifyWithSample` | `node_classify_with_sample.py` | Cluster-GCN style training on `ClusterGCNSampler` partitions; runs on CPU and takes no `gpu` argument |
| `GraphClassify` | `graph_classify.py` | `train(batch_size=20, lr, weight_decay, n_epochs, patience, early_stopping_monitor, clip=2.0, gpu)` over a `HugeGraphDataset`, split 70/20/10 |
| `DetectorCaregnn` | `fraud_detector_caregnn.py` | CARE-GNN training; `evaluate()` reports recall and ROC AUC and reads `ndata["feature"]` rather than `ndata["feat"]` |
| `HeteroSampleEmbedGATNE` | `hetero_sample_embed_gatne.py` | `train_and_embed(lr=1e-3, n_epochs=200, gpu=-1)` |
| `LinkPredictionPGNN` | `link_prediction_pgnn.py` | `train(lr, weight_decay, n_epochs, gpu)` |
| `LinkPredictionSeal` | `link_prediction_seal.py` | The constructor calls `data_prepare()` itself, then `train(lr=1e-3, n_epochs=200, gpu=-1)` |

`patience` defaults to `float("inf")`. `EarlyStopping` in `utils/early_stopping.py` monitors either `loss` or `accuracy`, keeps a copy of the best weights and restores them when training stops.

## Runnable Examples

Scripts sit in `hugegraph-ml/src/hugegraph_ml/examples/`. From `hugegraph-ml/src`, run one with:

```bash
python ./hugegraph_ml/examples/dgi_example.py
```

Each script also exposes a function of the same name, so it can be imported and called with a smaller epoch count.

| Script | Model | Task | Reads |
|---|---|---|---|
| `agnn_example.py` | `AGNN` | `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `appnp_example.py` | `APPNP` | `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `arma_example.py` | `ARMA4NC` | `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `bgnn_example.py` | `BGNNPredictor` | Its own `fit()` | `AVAZU__N_v`, `AVAZU__E_e` |
| `bgrl_example.py` | `BGRL` | `NodeEmbed`, `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `care_gnn_example.py` | `CAREGNN` | `DetectorCaregnn` | `AMAZON_user_v` plus `AMAZON_net_upu_e`, `AMAZON_net_usu_e`, `AMAZON_net_uvu_e` |
| `cluster_gcn_example.py` | `SAGE` | `NodeClassifyWithSample` | `CORA_vertex`, `CORA_edge` |
| `correct_and_smooth_example.py` | `MLP` from `correct_and_smooth` | `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `dagnn_example.py` | `DAGNN` | `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `deepergcn_example.py` | `DeeperGCN` | `NodeClassifyWithEdge` | `CORA_vertex`, `CORA_edge` through `convert_graph_with_edge_feat` |
| `dgi_example.py` | `DGI` | `NodeEmbed`, `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `diffpool_example.py` | `DiffPool` | `GraphClassify` | `MUTAG_graph_vertex`, `MUTAG_vertex`, `MUTAG_edge` |
| `gatne_example.py` | `DGLGATNE` | `HeteroSampleEmbedGATNE` | `AMAZONGATNE__N_v`, `AMAZONGATNE_1_e`, `AMAZONGATNE_2_e` |
| `gin_example.py` | `GIN` | `GraphClassify` | `MUTAG_graph_vertex`, `MUTAG_vertex`, `MUTAG_edge` |
| `grace_example.py` | `GRACE` | `NodeEmbed`, `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `grand_example.py` | `GRAND` | `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `jknet_example.py` | `JKNet` | `NodeClassify` | `CORA_vertex`, `CORA_edge` |
| `pgnn_example.py` | `PGNN` | `LinkPredictionPGNN` | `CAVEMAN_vertex`, `CAVEMAN_edge` |
| `seal_example.py` | `DGCNN` | `LinkPredictionSeal` | `ogbl-collab_vertex`, `ogbl-collab_edge`, `ogbl-collab_split_edge` |

## DGI Node Embedding Example

First import DGL's Cora dataset into HugeGraph. The name is upper-cased before use, so `cora` and `CORA` both produce the `CORA_vertex` and `CORA_edge` labels:

```python
from hugegraph_ml.utils.dgl2hugegraph_utils import import_graph_from_dgl

import_graph_from_dgl("cora")
```

Read the graph and train DGI:

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL
from hugegraph_ml.models.dgi import DGI
from hugegraph_ml.models.mlp import MLPClassifier
from hugegraph_ml.tasks.node_classify import NodeClassify
from hugegraph_ml.tasks.node_embed import NodeEmbed

hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(vertex_label="CORA_vertex", edge_label="CORA_edge")

embed_model = DGI(n_in_feats=graph.ndata["feat"].shape[1])
embed_task = NodeEmbed(graph=graph, model=embed_model)
embedded_graph = embed_task.train_and_embed(
    add_self_loop=True, n_epochs=300, patience=30
)

classifier = MLPClassifier(
    n_in_feat=embedded_graph.ndata["feat"].shape[1],
    n_out_feat=embedded_graph.ndata["label"].unique().shape[0],
)
classify_task = NodeClassify(graph=embedded_graph, model=classifier)
classify_task.train(lr=1e-3, n_epochs=400, patience=40)
print(classify_task.evaluate())
```

`evaluate()` returns a dictionary such as `{'accuracy': 0.82, 'loss': 0.5714246034622192}`. The complete script is `hugegraph-ml/src/hugegraph_ml/examples/dgi_example.py`.

## GRAND Node Classification Example

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL
from hugegraph_ml.models.grand import GRAND
from hugegraph_ml.tasks.node_classify import NodeClassify

hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(vertex_label="CORA_vertex", edge_label="CORA_edge")
model = GRAND(
    n_in_feats=graph.ndata["feat"].shape[1],
    n_out_feats=graph.ndata["label"].unique().shape[0],
)
task = NodeClassify(graph, model)
task.train(lr=1e-2, weight_decay=5e-4, n_epochs=2000, patience=100)
print(task.evaluate())
```

GRAND returns a list of logits per augmentation sample, and `NodeClassify` masks each element of that list before computing the loss. The complete script is `hugegraph-ml/src/hugegraph_ml/examples/grand_example.py`.

## Troubleshooting

- Connection failures: check the HugeGraph Server address, port, and credentials.
- Schema mismatches: the examples use `CORA_vertex` and `CORA_edge`; pass the actual labels for your own data.
- `ValueError: Graph is missing required node attribute ...`: the node classification tasks need `feat`, `label`, `train_mask`, `val_mask` and `test_mask` in `ndata`. Import a dataset that carries masks, or pass your own `mask_keys` to `convert_graph`.
- `ValueError: dataset not supported`: the importer only accepts the names in the table above, and `import_graph_from_ogb` matches `ogbl-collab` without upper-casing.
- DGL or PyTorch import failures: rerun `uv sync --extra ml` from the repository root and confirm that Python comes from the root `.venv`.
- `bgrl_example.py` currently fails on import: it asks for `MLP_Predictor` from `hugegraph_ml.models.bgrl`, but that module defines the class as `MLPPredictor`.
- `care_gnn_example.py` reads `AMAZON_user_v` and the three `AMAZON_net_*_e` edge labels. No bundled importer creates them, so load that dataset yourself before running the script.
