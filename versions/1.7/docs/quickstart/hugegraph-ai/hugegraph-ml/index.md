# HugeGraph-ML

LLMS index: [llms.txt](/versions/1.7/llms.txt)

---

HugeGraph-ML reads graph data from HugeGraph and converts it to DGL graphs for tasks such as node embedding, node classification, and graph classification. Model implementations are under `hugegraph-ml/src/hugegraph_ml/models/`.

## Requirements

- Python 3.10 or later
- HugeGraph Server 1.0 or later; 1.5 or later is recommended
- `uv` 0.7 or later

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

The current README lists these models:

| Models | Main purpose |
|---|---|
| AGNN, APPNP, ARMA, Cluster-GCN, DAGNN, DeeperGCN, GRAND, JKNet | Node classification |
| BGNN, CARE-GNN | Fraud detection |
| BGRL, DGI, GRACE | Representation learning |
| DiffPool | Graph classification |
| GATNE, P-GNN, SEAL | Link prediction or network embedding |
| C&S | Correction and smoothing of predictions |

The source also includes `GIN` for graph classification and `MLPClassifier` for downstream classification. The model count changes between versions; use `src/hugegraph_ml/models/` as the authoritative list.

## DGI Node Embedding Example

First import DGL's Cora dataset into HugeGraph:

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

The complete script is `hugegraph-ml/src/hugegraph_ml/examples/dgi_example.py`.

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

The complete script is `hugegraph-ml/src/hugegraph_ml/examples/grand_example.py`.

## Troubleshooting

- Connection failures: check the HugeGraph Server address, port, and credentials.
- Schema mismatches: the examples use `CORA_vertex` and `CORA_edge`; pass the actual labels for your own data.
- DGL or PyTorch import failures: rerun `uv sync --extra ml` from the repository root and confirm that Python comes from the root `.venv`.
