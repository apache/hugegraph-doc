---
title: "HugeGraph 0.7 Release Notes"
linkTitle: "Release-0.7.4"
draft: true
weight: 21
---

### API & Java Client

#### 功能更新
- 支持异步删除元数据和重建索引（HugeGraph-889）
- 加入监控API，并与Gremlin的监控框架集成（HugeGraph-1273）
 
#### BUG修复
- EdgeAPI更新属性时会将属性值也置为属性键（HugeGraph-81）
- 当删除顶点或边时，如果id非法应该返回400错误而非404（HugeGraph-1337）

### Core

#### 功能更新
- 支持HBase后端存储（HugeGraph-1280）
- 增加异步API框架，耗时操作可通过调用异步API实现（HugeGraph-387）
- 支持对长属性列建立二级索引，取消目前索引列长度256字节的限制（HugeGraph-1314）
- 支持顶点属性的“创建或更新”操作（HugeGraph-1303）
- 支持全文检索功能（HugeGraph-1322）
- 支持数据库表的版本号检查（HugeGraph-1328）
- 删除顶点时，如果遇到超级点的时候报错"Batch too large"或“Batch 65535 statements”（HugeGraph-1354）
- 支持异步删除元数据和重建索引（HugeGraph-889）
- 支持异步长时间执行Gremlin任务（HugeGraph-889）

#### BUG修复
- 防止超级点访问时查询过多下一层顶点而阻塞服务（HugeGraph-1302）
- HBase初始化时报错连接已经关闭（HugeGraph-1318）
- 按照date属性过滤顶点报错String无法转为Date（HugeGraph-1319）
- 残留索引删除，对range索引的判断存在错误（HugeGraph-1291）
- 支持组合索引后，残留索引清理没有考虑索引组合的情况（HugeGraph-1311）
- 根据otherV的条件来删除边时，可能会因为边的顶点不存在导致错误（HugeGraph-1347）
- label索引对offset和limit结果错误（HugeGraph-1329）
- vertex label或者edge label没有开启label index，删除label会导致数据无法删除（HugeGraph-1355）
 
#### 内部修改
- hbase后端代码引入较新版本的Jackson-databind包，导致HugeGraphServer启动异常（HugeGraph-1306）
- Core和Client都自己持有一个shard类，而不是依赖于common模块（HugeGraph-1316）
- 去掉rebuild index和删除vertex label和edge label时的80w的capacity限制（HugeGraph-1297）
- 所有schema操作需要考虑同步问题（HugeGraph-1279）
- 拆分Cassandra的索引表，把element id每条一行，避免聚合高时，导入速度非常慢甚至卡住（HugeGraph-1304）
- 将hugegraph-test中关于common的测试用例移动到hugegraph-common中（HugeGraph-1297）
- 异步任务支持保存任务参数，以支持任务恢复（HugeGraph-1344）
- 支持通过脚本部署文档到GitHub（HugeGraph-1351）
- RocksDB和Hbase后端索引删除实现（HugeGraph-1317）
 
### Loader

#### 功能更新
- HugeLoader支持用户手动创建schema，以文件的方式传入（HugeGraph-1295）

#### BUG修复
- HugeLoader导数据时未区分输入文件的编码，导致可能产生乱码（HugeGraph-1288）
- HugeLoader打包的example目录的三个子目录下没有文件（HugeGraph-1288）
- 导入的CSV文件中如果数据列本身包含逗号会解析出错（HugeGraph-1320）
- 批量插入避免单条失败导致整个batch都无法插入（HugeGraph-1336）
- 异常信息作为模板打印异常（HugeGraph-1345）
- 导入边数据，当列数不对时导致程序退出（HugeGraph-1346）
- HugeLoader的自动创建schema失败（HugeGraph-1363）
- ID长度检查应该检查字节长度而非字符串长度（HugeGraph-1374）
 
#### 内部修改
- 添加测试用例（HugeGraph-1361）
 
### Tools
 
#### 功能更新
- backup/restore使用多线程加速，并增加retry机制（HugeGraph-1307）
- 一键部署支持传入路径以存放包（HugeGraph-1325）
- 实现dump图功能（内存构建顶点及关联边）（HugeGraph-1339）
- 增加backup-scheduler功能，支持定时备份且保留一定数目最新备份（HugeGraph-1326）
- 增加异步任务查询和异步执行Gremlin的功能（HugeGraph-1357）

#### BUG修复
- hugegraph-tools的backup和restore编码为UTF-8（HugeGraph-1321）
- hugegraph-tools设置默认JVM堆大小和发布版本号（HugeGraph-1340）
 
### Studio

#### BUG修复
- HugeStudio中顶点id包含换行符时g.V()会导致groovy解析出错（HugeGraph-1292）
- 限制返回的顶点及边的数量（HugeGraph-1333）
- 加载note出现消失或者卡住情况（HugeGraph-1353）
- HugeStudio打包时，编译失败但没有报错，导致发布包无法启动（HugeGraph-1368）