---
title: "HugeGraph 0.6 Release Notes"
linkTitle: "Release-0.6.1"
draft: true
weight: 23
---

### API & Java Client

#### 功能更新
- 增加RESTFul API paths和crosspoints，找出source到target顶点间多条路径或包含交叉点的路径（HugeGraph-1210）
- 在API层添加批量插入并发数的控制，避免出现全部的线程都用于写而无法查询的情况（HugeGraph-1228）
- 增加scan-API，允许客户端并发地获取顶点和边（HugeGraph-1197）
- Client支持传入用户名密码访问带权限控制的HugeGraph（HugeGraph-1256）
- 为顶点及边的list API添加offset参数（HugeGraph-1261）
- RESTful API的顶点/边的list不允许同时传入page 和 [label，属性]（HugeGraph-1262）
- k-out、K-neighbor、paths、shortestpath等API增加degree、capacity和limit（HugeGraph-1176）
- 增加restore status的set/get/clear接口（HugeGraph-1272）

#### BUG修复
- 使 RestClient的basic auth使用Preemptive模式（HugeGraph-1257）
- HugeGraph-Client中由ResultSet获取多次迭代器，除第一次外其他的无法迭代（HugeGraph-1278）

### Core

#### 功能更新
- RocksDB实现scan特性（HugeGraph-1198）
- Schema userdata 提供删除 key 功能（HugeGraph-1195）
- 支持date类型属性的范围查询（HugeGraph-1208）
- limit下沉到backend，尽可能不进行多余的索引读取（HugeGraph-1234）
- 增加 API 权限与访问控制（HugeGraph-1162）
- 禁止多个后端配置store为相同的值（HugeGraph-1269）

#### BUG修复
- RocksDB的Range查询时如果只指定上界或下界会查出其他IndexLabel的记录（HugeGraph-1211）
- RocksDB带limit查询时，graphTransaction查询返回的结果多一个（HugeGraph-1234）
- init-store在CentOS上依赖通用的io.netty有时会卡住，改为使用netty-transport-native-epoll（HugeGraph-1255）
- Cassandra后端in语句（按id查询）元素个数最大65535（HugeGraph-1239）
- 主键加索引(或普通属性)作为查询条件时报错（HugeGraph-1276）
- init-store.sh在Centos平台上初始化失败或者卡住（HugeGraph-1255）
 
### 测试
无

### 内部修改
- 将compareNumber方法搬移至common模块（HugeGraph-1208）
- 修复HugeGraphServer无法在Ubuntu机器上启动的Bug（HugeGraph-1154） 
- 修复init-store.sh无法在bin目录下执行的BUG（HugeGraph-1223）
- 修复HugeGraphServer启动过程中无法通过CTRL+C终止的BUG（HugeGraph-1223）
- HugeGraphServer启动前检查端口是否被占用（HugeGraph-1223） 
- HugeGraphServer启动前检查系统JDK是否安装以及版本是否为1.8（HugeGraph-1223）
- 给HugeConfig类增加getMap()方法（HugeGraph-1236）
- 修改默认配置项，后端使用RocksDB，注释重要的配置项（HugeGraph-1240）
- 重命名userData为userdata（HugeGraph-1249）
- centos 4.3系统HugeGraphServer进程使用jps命令查不到
- 增加配置项ALLOW_TRACE，允许设置是否返回exception stack trace（HugeGraph-81）

### Tools
 
#### 功能更新
- 增加自动化部署工具以安装所有组件（HugeGraph-1267）
- 增加clear的脚本，并拆分deploy和start-all（HugeGraph-1274）
- 对hugegraph服务进行监控以提高可用性（HugeGraph-1266）
- 增加backup/restore功能和命令（HugeGraph-1272）
- 增加graphs API对应的命令（HugeGraph-1272）
 
#### BUG修复 

### Loader

#### 功能更新
- 默认添加csv及json的示例（HugeGraph-1259）

#### BUG修复
