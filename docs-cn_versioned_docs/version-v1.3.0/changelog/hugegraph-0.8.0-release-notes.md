---
title: "HugeGraph 0.8 Release Notes"
linkTitle: "Release-0.8.0"
draft: true
weight: 19
---

### API & Client

#### 功能更新

- 服务端增加 rays 和 rings 的 RESTful API（hugegraph #45）
- 使创建 IndexLabel 返回异步任务（hugegraph #95，hugegraph-client #9）
- 客户端增加恢复模式相关的 API（hugegraph-client #10）
- 让 task-list API 不返回 task_input 和 task_result（hugegraph #143）
- 增加取消异步任务的API（hugegraph #167，hugegraph-client #15）
- 增加获取后端 metrics 的 API（hugegraph #155）

#### BUG修复

- 分页获取时最后一页的 page 应该为 null 而非 "null"（hugegraph #168）
- 分页迭代获取服务端已经没有下一页了应该停止获取（hugegraph-client #16）
- 添加顶点使用自定义 Number Id 时报类型无法转换（hugegraph-client #21）

#### 内部修改

- 增加持续集成测试（hugegraph-client #19）

### Core

#### 功能更新

- 取消异步任务通过 label 查询时 80w 的限制（hugegraph #93）
- 允许 cardinality 为 set 时传入 Json List 形式的属性值（hugegraph #109）
- 支持在恢复模式和合并模式来恢复图（hugegraph #114）
- RocksDB 后端支持多个图指定为同一个存储目录（hugegraph #123）
- 支持用户自定义权限认证器（hugegraph-loader #133）
- 当服务重启后重新开始未完成的任务（hugegraph #188）
- 当顶点的 Id 策略为自定义时，检查是否已存在相同 Id 的顶点（hugegraph #189）

#### BUG修复

- 增加对 HasContainer 的 predicate 不为 null 的检查（hugegraph #16）
- RocksDB 后端由于数据目录和日志目录错误导致 init-store 失败（hugegraph #25）
- 启动 hugegraph 时由于 logs 目录不存在导致提示超时但实际可访问（hugegraph #38）
- ScyllaDB 后端遗漏注册顶点表（hugegraph #47）
- 使用 hasLabel 查询传入多个 label 时失败（hugegraph #50）
- Memory 后端未初始化 task 相关的 schema（hugegraph #100）
- 当使用 hasLabel 查询时，如果元素数量超过 80w，即使加上 limit 也会报错（hugegraph #104）
- 任务的在运行之后没有保存过状态（hugegraph #113）
- 检查后端版本信息时直接强转 HugeGraphAuthProxy 为 HugeGraph（hugegraph #127）
- 配置项 batch.max_vertices_per_batch 未生效（hugegraph #130）
- 配置文件 rest-server.properties 有错误时 HugeGraphServer 启动不报错，但是无法访问（hugegraph #131）
- MySQL 后端某个线程的提交对其他线程不可见（hugegraph #163）
- 使用 union(branch) + has(date) 查询时提示 String 无法转换为 Date（hugegraph #181）
- 使用 RocksDB 后端带 limit 查询顶点时会返回不完整的结果（hugegraph #197）
- 提示其他线程无法操作 tx（hugegraph #204）

#### 内部修改

- 拆分 graph.cache_xx 配置项为 vertex.cache_xx 和 edge.cache_xx 两类（hugegraph #56）
- 去除 hugegraph-dist 对 hugegraph-api 的依赖（hugegraph #61）
- 优化集合取交集和取差集的操作（hugegraph #85）
- 优化 transaction 的缓存处理和索引及 Id 查询（hugegraph #105）
- 给各线程池的线程命名（hugegraph #124）
- 增加并优化了一些 metrics 统计（hugegraph #138）
- 增加了对未完成任务的 metrics 记录（hugegraph #141）
- 让索引更新以分批方式提交，而不是全量提交（hugegraph #150）
- 在添加顶点/边时一直持有 schema 的读锁，直到提交/回滚完成（hugegraph #180）
- 加速 Tinkerpop 测试（hugegraph #19）
- 修复 Tinkerpop 测试在 resource 目录下找不到 filter 文件的 BUG（hugegraph #26）
- 开启 Tinkerpop 测试中 supportCustomIds 特性（hugegraph #69）
- 持续集成中添加 HBase 后端的测试（hugegraph #41）
- 避免持续集成的 deploy 脚本运行多次（hugegraph #170）
- 修复 cache 单元测试跑不过的问题（hugegraph #177）
- 持续集成中修改部分后端的存储为 tmpfs 以加快测试速度（hugegraph #206）

#### 其它

- 增加 issue 模版（hugegraph #42）
- 增加 CONTRIBUTING 文件（hugegraph #59）

### Loader

#### 功能更新

- 支持忽略源文件某些特定列（hugegraph-loader #2）
- 支持导入 cardinality 为 Set 的属性数据（hugegraph-loader #10）
- 单条插入也使用多个线程执行，解决了错误多时最后单条导入慢的问题（hugegraph-loader #12）

#### BUG修复

- 导入过程可能统计出错（hugegraph-loader #4）
- 顶点使用自定义 Number Id 导入出错（hugegraph-loader #6）
- 顶点使用联合主键时导入出错（hugegraph-loader #18）

#### 内部修改

- 增加持续集成测试（hugegraph-loader #8）
- 优化检测到文件不存在时的提示信息（hugegraph-loader #16）

### Tools

#### 功能更新

- 增加 KgDumper （hugegraph-tools #6）
- 支持在恢复模式和合并模式中恢复图（hugegraph-tools #9）

#### BUG修复

- 脚本中的工具函数 get_ip 在系统未安装 ifconfig 时报错（hugegraph-tools #13）
