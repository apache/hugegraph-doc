---
title: "HugeGraph-ML"
linkTitle: "HugeGraph-ML"
weight: 2
---

HugeGraph-ML integrates HugeGraph with popular graph learning libraries, enabling end-to-end machine learning workflows directly on graph data.

## Overview

`hugegraph-ml` provides a unified interface for applying graph neural networks and machine learning algorithms to data stored in HugeGraph. It eliminates the need for complex data export/import pipelines by seamlessly converting HugeGraph data to formats compatible with leading ML frameworks.

### Key Features

- **Direct HugeGraph Integration**: Query graph data directly from HugeGraph without manual exports
- **21 Implemented Algorithms**: Comprehensive coverage of node classification, graph classification, embedding, and link prediction
- **DGL Backend**: Leverages Deep Graph Library (DGL) for efficient training
- **End-to-End Workflows**: From data loading to model training and evaluation
- **Modular Tasks**: Reusable task abstractions for common ML scenarios

## Prerequisites

- **Python**: 3.9+ (standalone module)
- **HugeGraph Server**: 1.0+ (recommended: 1.5+)
- **UV Package Manager**: 0.7+ (for dependency management)

## Installation

### 1. Start HugeGraph Server

```bash
# Option 1: Docker (recommended)
docker run -itd --name=hugegraph -p 8080:8080 hugegraph/hugegraph

# Option 2: Binary packages
# See https://hugegraph.apache.org/docs/download/download/
```

### 2. Clone and Setup

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/hugegraph-ml
```

### 3. Install Dependencies

```bash
# uv sync automatically creates .venv and installs all dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### 4. Navigate to Source Directory

```bash
cd ./src
```

> [!NOTE]
> All examples assume you're in the activated virtual environment.

## Implemented Algorithms

HugeGraph-ML currently implements **21 graph machine learning algorithms** across multiple categories:

### Node Classification (11 algorithms)

Predict labels for graph nodes based on network structure and features.

| Algorithm | Paper | Description |
|-----------|-------|-------------|
| **GCN** | [Kipf & Welling, 2017](https://arxiv.org/abs/1609.02907) | Graph Convolutional Networks |
| **GAT** | [Veličković et al., 2018](https://arxiv.org/abs/1710.10903) | Graph Attention Networks |
| **GraphSAGE** | [Hamilton et al., 2017](https://arxiv.org/abs/1706.02216) | Inductive representation learning |
| **APPNP** | [Klicpera et al., 2019](https://arxiv.org/abs/1810.05997) | Personalized PageRank propagation |
| **AGNN** | [Thekumparampil et al., 2018](https://arxiv.org/abs/1803.03735) | Attention-based GNN |
| **ARMA** | [Bianchi et al., 2019](https://arxiv.org/abs/1901.01343) | Autoregressive moving average filters |
| **DAGNN** | [Liu et al., 2020](https://arxiv.org/abs/2007.09296) | Deep adaptive graph neural networks |
| **DeeperGCN** | [Li et al., 2020](https://arxiv.org/abs/2006.07739) | Very deep GCN architectures |
| **GRAND** | [Feng et al., 2020](https://arxiv.org/abs/2005.11079) | Graph random neural networks |
| **JKNet** | [Xu et al., 2018](https://arxiv.org/abs/1806.03536) | Jumping knowledge networks |
| **Cluster-GCN** | [Chiang et al., 2019](https://arxiv.org/abs/1905.07953) | Scalable GCN training via clustering |

### Graph Classification (2 algorithms)

Classify entire graphs based on their structure and node features.

| Algorithm | Paper | Description |
|-----------|-------|-------------|
| **DiffPool** | [Ying et al., 2018](https://arxiv.org/abs/1806.08804) | Differentiable graph pooling |
| **GIN** | [Xu et al., 2019](https://arxiv.org/abs/1810.00826) | Graph isomorphism networks |

### Graph Embedding (3 algorithms)

Learn unsupervised node representations for downstream tasks.

| Algorithm | Paper | Description |
|-----------|-------|-------------|
| **DGI** | [Veličković et al., 2019](https://arxiv.org/abs/1809.10341) | Deep graph infomax (contrastive learning) |
| **BGRL** | [Thakoor et al., 2021](https://arxiv.org/abs/2102.06514) | Bootstrapped graph representation learning |
| **GRACE** | [Zhu et al., 2020](https://arxiv.org/abs/2006.04131) | Graph contrastive learning |

### Link Prediction (3 algorithms)

Predict missing or future connections in graphs.

| Algorithm | Paper | Description |
|-----------|-------|-------------|
| **SEAL** | [Zhang & Chen, 2018](https://arxiv.org/abs/1802.09691) | Subgraph extraction and labeling |
| **P-GNN** | [You et al., 2019](http://proceedings.mlr.press/v97/you19b/you19b.pdf) | Position-aware GNN |
| **GATNE** | [Cen et al., 2019](https://arxiv.org/abs/1905.01669) | Attributed multiplex heterogeneous network embedding |

### Fraud Detection (2 algorithms)

Detect anomalous nodes in graphs (e.g., fraudulent accounts).

| Algorithm | Paper | Description |
|-----------|-------|-------------|
| **CARE-GNN** | [Dou et al., 2020](https://arxiv.org/abs/2008.08692) | Camouflage-resistant GNN |
| **BGNN** | [Zheng et al., 2021](https://arxiv.org/abs/2101.08543) | Bipartite graph neural network |

### Post-Processing (1 algorithm)

Improve predictions via label propagation.

| Algorithm | Paper | Description |
|-----------|-------|-------------|
| **C&S** | [Huang et al., 2020](https://arxiv.org/abs/2010.13993) | Correct & Smooth (prediction refinement) |

## Usage Examples

### Example 1: Node Embedding with DGI

Perform unsupervised node embedding on the Cora dataset using Deep Graph Infomax (DGI).

#### Step 1: Import Dataset (if needed)

```python
from hugegraph_ml.utils.dgl2hugegraph_utils import import_graph_from_dgl

# Import Cora dataset from DGL to HugeGraph
import_graph_from_dgl("cora")
```

#### Step 2: Convert Graph Data

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL

# Convert HugeGraph data to DGL format
hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(vertex_label="CORA_vertex", edge_label="CORA_edge")
```

#### Step 3: Initialize Model

```python
from hugegraph_ml.models.dgi import DGI

# Create DGI model
model = DGI(n_in_feats=graph.ndata["feat"].shape[1])
```

#### Step 4: Train and Generate Embeddings

```python
from hugegraph_ml.tasks.node_embed import NodeEmbed

# Train model and generate node embeddings
node_embed_task = NodeEmbed(graph=graph, model=model)
embedded_graph = node_embed_task.train_and_embed(
    add_self_loop=True,
    n_epochs=300,
    patience=30
)
```

#### Step 5: Downstream Task (Node Classification)

```python
from hugegraph_ml.models.mlp import MLPClassifier
from hugegraph_ml.tasks.node_classify import NodeClassify

# Use embeddings for node classification
model = MLPClassifier(
    n_in_feat=embedded_graph.ndata["feat"].shape[1],
    n_out_feat=embedded_graph.ndata["label"].unique().shape[0]
)
node_clf_task = NodeClassify(graph=embedded_graph, model=model)
node_clf_task.train(lr=1e-3, n_epochs=400, patience=40)
print(node_clf_task.evaluate())
```

**Expected Output:**
```python
{'accuracy': 0.82, 'loss': 0.5714246034622192}
```

**Full Example**: See [dgi_example.py](https://github.com/apache/hugegraph-ai/blob/main/hugegraph-ml/src/hugegraph_ml/examples/dgi_example.py)

### Example 2: Node Classification with GRAND

Directly classify nodes using the GRAND model (no separate embedding step needed).

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL
from hugegraph_ml.models.grand import GRAND
from hugegraph_ml.tasks.node_classify import NodeClassify

# Load graph
hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(vertex_label="CORA_vertex", edge_label="CORA_edge")

# Initialize GRAND model
model = GRAND(
    n_in_feats=graph.ndata["feat"].shape[1],
    n_out_feats=graph.ndata["label"].unique().shape[0]
)

# Train and evaluate
node_clf_task = NodeClassify(graph=graph, model=model)
node_clf_task.train(lr=1e-2, n_epochs=1500, patience=100)
print(node_clf_task.evaluate())
```

**Full Example**: See [grand_example.py](https://github.com/apache/hugegraph-ai/blob/main/hugegraph-ml/src/hugegraph_ml/examples/grand_example.py)

## Core Components

### HugeGraph2DGL Converter

Seamlessly converts HugeGraph data to DGL graph format:

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL

hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(
    vertex_label="person",      # Vertex label to extract
    edge_label="knows",         # Edge label to extract
    directed=False              # Graph directionality
)
```

### Task Abstractions

Reusable task objects for common ML workflows:

| Task | Class | Purpose |
|------|-------|---------|
| Node Embedding | `NodeEmbed` | Generate unsupervised node embeddings |
| Node Classification | `NodeClassify` | Predict node labels |
| Graph Classification | `GraphClassify` | Predict graph-level labels |
| Link Prediction | `LinkPredict` | Predict missing edges |

## Best Practices

1. **Start with Small Datasets**: Test your pipeline on small graphs (e.g., Cora, Citeseer) before scaling
2. **Use Early Stopping**: Set `patience` parameter to avoid overfitting
3. **Tune Hyperparameters**: Adjust learning rate, hidden dimensions, and epochs based on dataset size
4. **Monitor GPU Memory**: Large graphs may require batch training (e.g., Cluster-GCN)
5. **Validate Schema**: Ensure vertex/edge labels match your HugeGraph schema

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" to HugeGraph | Verify server is running on port 8080 |
| CUDA out of memory | Reduce batch size or use CPU-only mode |
| Model convergence issues | Try different learning rates (1e-2, 1e-3, 1e-4) |
| ImportError for DGL | Run `uv sync` to reinstall dependencies |

## Contributing

To add a new algorithm:

1. Create model file in `src/hugegraph_ml/models/your_model.py`
2. Inherit from base model class and implement `forward()` method
3. Add example script in `src/hugegraph_ml/examples/`
4. Update this documentation with algorithm details

## See Also

- [HugeGraph-AI Overview](../_index.md) - Full AI ecosystem
- [HugeGraph-LLM](./hugegraph-llm.md) - RAG and knowledge graph construction
- [GitHub Repository](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-ml) - Source code and examples
