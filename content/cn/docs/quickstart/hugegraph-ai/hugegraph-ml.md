---
title: "HugeGraph-ML"
linkTitle: "HugeGraph-ML"
weight: 2
---

HugeGraph-ML 将 HugeGraph 与流行的图学习库集成，支持直接在图数据上进行端到端的机器学习工作流。

## 概述

`hugegraph-ml` 提供了统一接口，用于将图神经网络和机器学习算法应用于存储在 HugeGraph 中的数据。它通过无缝转换 HugeGraph 数据到主流 ML 框架兼容格式，消除了复杂的数据导出/导入流程。

### 核心功能

- **直接 HugeGraph 集成**：无需手动导出即可直接从 HugeGraph 查询图数据
- **21 种算法实现**：全面覆盖节点分类、图分类、嵌入和链接预测
- **DGL 后端**：利用深度图库（DGL）进行高效训练
- **端到端工作流**：从数据加载到模型训练和评估
- **模块化任务**：可复用的常见 ML 场景任务抽象

## 环境要求

- **Python**：3.9+（独立模块）
- **HugeGraph Server**：1.0+（推荐：1.5+）
- **UV 包管理器**：0.7+（用于依赖管理）

## 安装

### 1. 启动 HugeGraph Server

```bash
# 方案一：Docker（推荐）
docker run -itd --name=hugegraph -p 8080:8080 hugegraph/hugegraph

# 方案二：二进制包
# 参见 https://hugegraph.apache.org/docs/download/download/
```

### 2. 克隆并设置

```bash
git clone https://github.com/apache/hugegraph-ai.git
cd hugegraph-ai/hugegraph-ml
```

### 3. 安装依赖

```bash
# uv sync 自动创建 .venv 并安装所有依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate
```

### 4. 导航到源代码目录

```bash
cd ./src
```

> [!NOTE]
> 所有示例均假定您在已激活的虚拟环境中。

## 已实现算法

HugeGraph-ML 目前实现了跨多个类别的 **21 种图机器学习算法**：

### 节点分类（11 种算法）

基于网络结构和特征预测图节点的标签。

| 算法 | 论文 | 描述 |
|-----|------|------|
| **GCN** | [Kipf & Welling, 2017](https://arxiv.org/abs/1609.02907) | 图卷积网络 |
| **GAT** | [Veličković et al., 2018](https://arxiv.org/abs/1710.10903) | 图注意力网络 |
| **GraphSAGE** | [Hamilton et al., 2017](https://arxiv.org/abs/1706.02216) | 归纳式表示学习 |
| **APPNP** | [Klicpera et al., 2019](https://arxiv.org/abs/1810.05997) | 个性化 PageRank 传播 |
| **AGNN** | [Thekumparampil et al., 2018](https://arxiv.org/abs/1803.03735) | 基于注意力的 GNN |
| **ARMA** | [Bianchi et al., 2019](https://arxiv.org/abs/1901.01343) | 自回归移动平均滤波器 |
| **DAGNN** | [Liu et al., 2020](https://arxiv.org/abs/2007.09296) | 深度自适应图神经网络 |
| **DeeperGCN** | [Li et al., 2020](https://arxiv.org/abs/2006.07739) | 非常深的 GCN 架构 |
| **GRAND** | [Feng et al., 2020](https://arxiv.org/abs/2005.11079) | 图随机神经网络 |
| **JKNet** | [Xu et al., 2018](https://arxiv.org/abs/1806.03536) | 跳跃知识网络 |
| **Cluster-GCN** | [Chiang et al., 2019](https://arxiv.org/abs/1905.07953) | 通过聚类实现可扩展 GCN 训练 |

### 图分类（2 种算法）

基于结构和节点特征对整个图进行分类。

| 算法 | 论文 | 描述 |
|-----|------|------|
| **DiffPool** | [Ying et al., 2018](https://arxiv.org/abs/1806.08804) | 可微分图池化 |
| **GIN** | [Xu et al., 2019](https://arxiv.org/abs/1810.00826) | 图同构网络 |

### 图嵌入（3 种算法）

学习用于下游任务的无监督节点表示。

| 算法 | 论文 | 描述 |
|-----|------|------|
| **DGI** | [Veličković et al., 2019](https://arxiv.org/abs/1809.10341) | 深度图信息最大化（对比学习） |
| **BGRL** | [Thakoor et al., 2021](https://arxiv.org/abs/2102.06514) | 自举图表示学习 |
| **GRACE** | [Zhu et al., 2020](https://arxiv.org/abs/2006.04131) | 图对比学习 |

### 链接预测（3 种算法）

预测图中缺失或未来的连接。

| 算法 | 论文 | 描述 |
|-----|------|------|
| **SEAL** | [Zhang & Chen, 2018](https://arxiv.org/abs/1802.09691) | 子图提取和标注 |
| **P-GNN** | [You et al., 2019](http://proceedings.mlr.press/v97/you19b/you19b.pdf) | 位置感知 GNN |
| **GATNE** | [Cen et al., 2019](https://arxiv.org/abs/1905.01669) | 属性多元异构网络嵌入 |

### 欺诈检测（2 种算法）

检测图中的异常节点（例如欺诈账户）。

| 算法 | 论文 | 描述 |
|-----|------|------|
| **CARE-GNN** | [Dou et al., 2020](https://arxiv.org/abs/2008.08692) | 抗伪装 GNN |
| **BGNN** | [Zheng et al., 2021](https://arxiv.org/abs/2101.08543) | 二部图神经网络 |

### 后处理（1 种算法）

通过标签传播改进预测。

| 算法 | 论文 | 描述 |
|-----|------|------|
| **C&S** | [Huang et al., 2020](https://arxiv.org/abs/2010.13993) | 校正与平滑（预测优化） |

## 使用示例

### 示例 1：使用 DGI 进行节点嵌入

使用深度图信息最大化（DGI）在 Cora 数据集上进行无监督节点嵌入。

#### 步骤 1：导入数据集（如需）

```python
from hugegraph_ml.utils.dgl2hugegraph_utils import import_graph_from_dgl

# 从 DGL 导入 Cora 数据集到 HugeGraph
import_graph_from_dgl("cora")
```

#### 步骤 2：转换图数据

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL

# 将 HugeGraph 数据转换为 DGL 格式
hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(vertex_label="CORA_vertex", edge_label="CORA_edge")
```

#### 步骤 3：初始化模型

```python
from hugegraph_ml.models.dgi import DGI

# 创建 DGI 模型
model = DGI(n_in_feats=graph.ndata["feat"].shape[1])
```

#### 步骤 4：训练并生成嵌入

```python
from hugegraph_ml.tasks.node_embed import NodeEmbed

# 训练模型并生成节点嵌入
node_embed_task = NodeEmbed(graph=graph, model=model)
embedded_graph = node_embed_task.train_and_embed(
    add_self_loop=True,
    n_epochs=300,
    patience=30
)
```

#### 步骤 5：下游任务（节点分类）

```python
from hugegraph_ml.models.mlp import MLPClassifier
from hugegraph_ml.tasks.node_classify import NodeClassify

# 使用嵌入进行节点分类
model = MLPClassifier(
    n_in_feat=embedded_graph.ndata["feat"].shape[1],
    n_out_feat=embedded_graph.ndata["label"].unique().shape[0]
)
node_clf_task = NodeClassify(graph=embedded_graph, model=model)
node_clf_task.train(lr=1e-3, n_epochs=400, patience=40)
print(node_clf_task.evaluate())
```

**预期输出：**
```python
{'accuracy': 0.82, 'loss': 0.5714246034622192}
```

**完整示例**：参见 [dgi_example.py](https://github.com/apache/hugegraph-ai/blob/main/hugegraph-ml/src/hugegraph_ml/examples/dgi_example.py)

### 示例 2：使用 GRAND 进行节点分类

使用 GRAND 模型直接对节点进行分类（无需单独的嵌入步骤）。

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL
from hugegraph_ml.models.grand import GRAND
from hugegraph_ml.tasks.node_classify import NodeClassify

# 加载图
hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(vertex_label="CORA_vertex", edge_label="CORA_edge")

# 初始化 GRAND 模型
model = GRAND(
    n_in_feats=graph.ndata["feat"].shape[1],
    n_out_feats=graph.ndata["label"].unique().shape[0]
)

# 训练和评估
node_clf_task = NodeClassify(graph=graph, model=model)
node_clf_task.train(lr=1e-2, n_epochs=1500, patience=100)
print(node_clf_task.evaluate())
```

**完整示例**：参见 [grand_example.py](https://github.com/apache/hugegraph-ai/blob/main/hugegraph-ml/src/hugegraph_ml/examples/grand_example.py)

## 核心组件

### HugeGraph2DGL 转换器

无缝将 HugeGraph 数据转换为 DGL 图格式：

```python
from hugegraph_ml.data.hugegraph2dgl import HugeGraph2DGL

hg2d = HugeGraph2DGL()
graph = hg2d.convert_graph(
    vertex_label="person",      # 要提取的顶点标签
    edge_label="knows",         # 要提取的边标签
    directed=False              # 图的方向性
)
```

### 任务抽象

用于常见 ML 工作流的可复用任务对象：

| 任务 | 类 | 用途 |
|-----|-----|------|
| 节点嵌入 | `NodeEmbed` | 生成无监督节点嵌入 |
| 节点分类 | `NodeClassify` | 预测节点标签 |
| 图分类 | `GraphClassify` | 预测图级标签 |
| 链接预测 | `LinkPredict` | 预测缺失边 |

## 最佳实践

1. **从小数据集开始**：在扩展之前先在小图（例如 Cora、Citeseer）上测试您的流程
2. **使用早停**：设置 `patience` 参数以避免过拟合
3. **调整超参数**：根据数据集大小调整学习率、隐藏维度和周期数
4. **监控 GPU 内存**：大图可能需要批量训练（例如 Cluster-GCN）
5. **验证 Schema**：确保顶点/边标签与您的 HugeGraph schema 匹配

## 故障排除

| 问题 | 解决方案 |
|-----|---------|
| 连接 HugeGraph "Connection refused" | 验证服务器是否在 8080 端口运行 |
| CUDA 内存不足 | 减少批大小或使用仅 CPU 模式 |
| 模型收敛问题 | 尝试不同的学习率（1e-2、1e-3、1e-4） |
| DGL 的 ImportError | 运行 `uv sync` 重新安装依赖 |

## 贡献

添加新算法：

1. 在 `src/hugegraph_ml/models/your_model.py` 创建模型文件
2. 继承基础模型类并实现 `forward()` 方法
3. 在 `src/hugegraph_ml/examples/` 添加示例脚本
4. 更新此文档并添加算法详情

## 另见

- [HugeGraph-AI 概述](../_index.md) - 完整 AI 生态系统
- [HugeGraph-LLM](./hugegraph-llm.md) - RAG 和知识图谱构建
- [GitHub 仓库](https://github.com/apache/hugegraph-ai/tree/main/hugegraph-ml) - 源代码和示例
