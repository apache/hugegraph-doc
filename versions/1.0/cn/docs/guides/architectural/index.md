# HugeGraph Architecture Overview

LLMS 索引： [llms.txt](/versions/1.0/cn/llms.txt)

---

### 1 概述

作为一款通用的图数据库产品，HugeGraph需具备图数据的基本功能，如下图所示。HugeGraph包括三个层次的功能，分别是存储层、计算层和用户接口层。 HugeGraph支持OLTP和OLAP两种图计算类型，其中OLTP实现了[Apache TinkerPop3](https://tinkerpop.apache.org)框架，并支持[Gremlin](https://tinkerpop.apache.org/gremlin.html)查询语言。 OLAP计算是基于SparkGraphX实现。

<center>
  <img src="/versions/1.0/docs/images/design/architectural-overview.png" alt="image">
</center>


### 2 组件

HugeGraph的主要功能分为HugeCore、ApiServer、HugeGraph-Client、HugeGraph-Loader和HugeGraph-Studio等组件构成，各组件之间的通信关系如下图所示。

<center>
  <img src="/versions/1.0/docs/images/design/architectural-component.png" alt="image">
</center>


- HugeCore ：HugeGraph的核心模块，TinkerPop的接口主要在该模块中实现。HugeCore的功能涵盖包括OLTP和OLAP两个部分。
- ApiServer ：提供RESTFul Api接口，对外提供Graph Api、Schema Api和Gremlin Api等接口服务。
- HugeGraph-Client：基于Java客户端驱动程序。HugeGraph-Client是Java版本客户端驱动程序，后续可根据需要提供Python、Go、C++等多语言支持。
- HugeGraph-Loader：数据导入模块。HugeGraph-Loader可以扫描并分析现有数据，自动生成Graph Schema创建语言，通过批量方式快速导入数据。
- HugeGraph-Studio：基于Web的可视化IDE环境。以Notebook方式记录Gremlin查询，可视化展示Graph的关联关系。HugeGraph-Studio也是本系统推荐的工具。
- HugeGraph-Computer：HugeGraph-Computer是一个分布式图处理系统 (OLAP)。
