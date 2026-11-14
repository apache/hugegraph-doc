# Apache HugeGraph

> 覆盖 OLTP、OLAP 与图智能的全栈图数据库生态系统。

LLMS 索引： [llms.txt](/cn/llms.txt)

## 全栈图技术平台

实时查询数据关系，离线分析全图，用 Graph AI 构建 LLM 记忆和本体图谱

[快速开始](/cn/docs/quickstart/)

[GitHub](https://github.com/apache/hugegraph)

## HugeGraph，从一套技术栈到不同规模

### 图数据库

server/pd/store

Server 提供图查询，分布式部署使用 PD 管理分区、Store 存储副本

**从一个点开始**

沿着边，找到这个点的邻居。图数据库支持单机内嵌存储，也支持基于 Raft 的高可用分布式存储

```gremlin
g.V().has('name', 'marko').out('knows')
```

[查看图数据库部署指南](/cn/docs/quickstart/hugegraph/)

### 图工具链

loader/hubble/tools

用 Loader 批量导入顶点和边，在 Hubble 中查看关系，用 Tools 备份和迁移数据

**沿着边出发**

用 Loader 导入顶点和边，再用 Hubble 查看查询结果，沿着一条边找到下一个顶点

[查看图工具链指南](/cn/docs/quickstart/toolchain/)

### 图计算

vermeer/computer

在内存或 BSP 集群上对全图进行 OLAP 分析

**全图计算，挖掘社群**

图计算对整个数据集进行 OLAP 分析，Vermeer 在内存中运行，Computer 使用 BSP 集群

[探索图计算](/cn/docs/quickstart/computing/)

### 图 AI

llm/sdk/rag

结合大语言模型实现 GraphRAG 与本体图谱构建

**拥抱 AI，向图前行**

Graph AI 的图抽取 SDK、Memory 和本体平台都在快速迭代，欢迎大家参与共建

[探索图 AI](/cn/docs/quickstart/hugegraph-ai/)

## 从**图数据存储**和**实时查询**，到**离线分析**和**图 AI**，一套图系统贯穿全程

- **千亿级** — 顶点与边的规模

- **毫秒级** — 多跳查询延迟

- **30+** — 内置图算法

- **首个** — Apache 顶级图系统

## 核心特点

- [**高效**](/cn/docs/quickstart/toolchain/hugegraph-loader/) — 支持海量数据批量导入、毫秒级图检索，以及数千用户并发的在线操作

- [**智能化**](/cn/docs/quickstart/hugegraph-ai/) — 支持 GraphRAG、自动化知识图谱构建，并内置 20 多种图机器学习算法

- [**易用**](/cn/docs/quickstart/toolchain/) — 支持 Gremlin、Cypher 与 RESTful API，配备覆盖导入、可视化和运维的完整工具链

- [**通用**](/cn/docs/quickstart/computing/) — 基于 Apache TinkerPop 的属性图建模，覆盖 OLTP 与 OLAP，可集成 Hadoop 和 Spark

- [**可扩展**](/cn/docs/quickstart/hugegraph/hugegraph-hstore/) — 支持水平扩容和分布式部署，覆盖从单机到 PB 级集群的使用场景

- [**开放生态**](/cn/docs/clients/client/hugegraph-client/) — 遵循 TinkerPop 标准，提供多语言客户端，由活跃且持续演进的 Apache 社区支持

## 无缝衔接现有技术栈

Apache Spark, Apache Flink, Apache Hadoop, Docker, Kubernetes, Helm, RocksDB, Python, Go, OpenJDK

## ALL IN ONE

图数据库可单机或分布式部署。按需搭配图工具链、图计算和图 AI 组件

### 图数据库

- [**Server \(从这里开始\)**](/cn/docs/quickstart/hugegraph/hugegraph-server/) — 图数据库引擎，提供 REST API、Gremlin 与 Cypher

- [**PD**](/cn/docs/quickstart/hugegraph/hugegraph-pd/) — 管理元数据、分区和集群调度的 Placement Driver

- [**Store**](/cn/docs/quickstart/hugegraph/hugegraph-hstore/) — 基于 Raft 一致性协议的分布式存储

### 工具链

- [**Hubble**](/cn/docs/quickstart/toolchain/hugegraph-hubble/) — 用于图数据可视化的 Web 平台

- [**Loader**](/cn/docs/quickstart/toolchain/hugegraph-loader/) — 用于批量加载图数据的导入工具

- [**Tools**](/cn/docs/quickstart/toolchain/hugegraph-tools/) — 用于备份、恢复和迁移的命令行工具

### 图计算与 AI

- [**Vermeer**](/cn/docs/quickstart/computing/hugegraph-vermeer/) — 在内存中运行图算法，支持 PageRank 和社群发现

- [**AI**](/cn/docs/quickstart/hugegraph-ai/) — 结合大语言模型实现 GraphRAG 与知识图谱构建

## 快速开始

Docker 默认以单机模式启动 HugeGraph Server，监听本机 8080 端口。单机模式支持内存或磁盘存储

```bash
docker run -d -p 127.0.0.1:8080:8080 hugegraph/hugegraph
```

查看启动日志，再确认服务已就绪

```bash
curl -fsS http://127.0.0.1:8080/versions
```

[其他安装方式](/cn/docs/download/download/)

[验证服务并执行第一次查询](/cn/docs/quickstart/hugegraph/hugegraph-server/)

## 欢迎加入 HugeGraph 开源社区

欢迎新用户和贡献者一起交流、参与开发

- [**GitHub**](https://github.com/apache/hugegraph) — 通过 GitHub Pull Request 提交贡献

- [**微信公众号**](/cn/docs/introduction/#community) — 扫码关注「Apache HugeGraph」，获取社区动态

- [**工具链**](/cn/docs/quickstart/toolchain/) — 获取图数据导入、可视化、备份、恢复与迁移工具

- [**Discord**](https://discord.gg/bT7GtKEnJK) — 加入 HugeGraph 社区，交流使用经验

---

本节页面：

- [Documentation](/cn/docs/)

- [Search Results](/cn/search/)

- [关于 Apache HugeGraph](/cn/about/)

- [博客](/cn/blog/)

- [社区](/cn/community/)
