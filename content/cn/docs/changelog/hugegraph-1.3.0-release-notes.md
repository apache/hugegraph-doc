---
title: "HugeGraph 1.3.0 Release Notes"
linkTitle: "Release-1.3.0"
weight: 5
---

### 运行环境/版本说明

1. 优先在 `hugegraph/toolchain/commons`软件中使用 Java 11, 此次是这些模块最后一次主版本兼容 Java 8 了。(computer 则仅支持 Java11)
2. 另外相比 Java11, 使用 Java8 会失去一些**安全性**的保障，我们推荐生产或对外网暴露访问的环境使用 Java11 并开启 [Auth 权限认证](/cn/docs/config/config-authentication/)

**1.3.0** 是最后兼容 **Java 8** 的版本，在 1.5.0 开始就会全面使用 Java 11 (除`client`外).

PS: 未来 HugeGraph 组件的版本会朝着 `Java 11 -> Java 17 -> Java 21` 演进

### hugegraph

> 在此次版本中我们修复了一些 SEC 相关的问题，如果是线上或者对外服务请升级到最新版本 + 开启权限认证

#### API Changes

* feat(api): optimize adjacent-edges query ([#2408](https://github.com/apache/hugegraph/pull/2408))

#### Feature Changes

- feat: support docker use the auth when starting ([#2403](https://github.com/apache/hugegraph/pull/2403))
- feat: added the OpenTelemetry trace support ([#2477](https://github.com/apache/hugegraph/pull/2477))

#### Bug Fix

- fix(core): task restore interrupt problem on restart server ([#2401](https://github.com/apache/hugegraph/pull/2401))
- fix(server): reinitialize the progress to set up graph auth friendly ([#2411](https://github.com/apache/hugegraph/pull/2411))
- fix(chore): remove zgc in dockerfile for ARM env ([#2421](https://github.com/apache/hugegraph/pull/2421))
- fix(server): make CacheManager constructor private to satisfy the singleton pattern ([#2432](https://github.com/apache/hugegraph/pull/2432))
- fix(server): unify the license headers ([#2438](https://github.com/apache/hugegraph/pull/2438))
- fix: format and clean code in dist and example modules ([#2441](https://github.com/apache/hugegraph/pull/2441))
- fix: format and clean code in core module ([#2440](https://github.com/apache/hugegraph/pull/2440))
- fix: format and clean code in modules ([#2439](https://github.com/apache/hugegraph/pull/2439))
- fix(server): clean up the code ([#2456](https://github.com/apache/hugegraph/pull/2456))
- fix(server): remove extra blank lines ([#2459](https://github.com/apache/hugegraph/pull/2459))
- fix(server): add tip for gremlin api NPE with an empty query ([#2467](https://github.com/apache/hugegraph/pull/2467))
- fix(server): fix the metric name when promthus collects hugegraph metric, see issue ([#2462](https://github.com/apache/hugegraph/pull/2462))
- fix(server): `serverStarted` error when execute gremlin example ([#2473](https://github.com/apache/hugegraph/pull/2473))
- fix(auth): enhance the URL check ([#2422](https://github.com/apache/hugegraph/pull/2422))

#### Option Changes

* refact(server): enhance the storage path in RocksDB & clean code ([#2491](https://github.com/apache/hugegraph/pull/2491))

#### Other Changes

- chore: add a license link ([#2398](https://github.com/apache/hugegraph/pull/2398))
- doc: enhance NOTICE info to keep it clear ([#2409](https://github.com/apache/hugegraph/pull/2409))
- chore(server): update swagger info for default server profile ([#2423](https://github.com/apache/hugegraph/pull/2423))
- fix(server): unify license header for protobuf file ([#2448](https://github.com/apache/hugegraph/pull/2448))
- chore: improve license header checker confs and pre-check header when validating ([#2445](https://github.com/apache/hugegraph/pull/2445))
- chore: unify to call SchemaLabel.getLabelId() ([#2458](https://github.com/apache/hugegraph/pull/2458))
- chore: refine the hg-style.xml specification ([#2457](https://github.com/apache/hugegraph/pull/2457))
- chore: Add a newline formatting configuration and a comment for warning ([#2464](https://github.com/apache/hugegraph/pull/2464))
- chore(server): clear context after req done ([#2470](https://github.com/apache/hugegraph/pull/2470))

### hugegraph-toolchain

#### API Changes

#### Feature Changes

* fix(loader): update shade plugin for spark loader ([#566](https://github.com/apache/hugegraph-toolchain/pull/566))
* fix(hubble): yarn install timeout in arm64 ([#583](https://github.com/apache/hugegraph-toolchain/pull/583))
* fix(loader): support file name with prefix for hdfs source ([#571](https://github.com/apache/hugegraph-toolchain/pull/571))
* feat(hubble): warp the exception info in HugeClientUtil ([#589](https://github.com/apache/hugegraph-toolchain/pull/589))

#### Bug Fix

* fix: concurrency issue causing file overwrite due to identical filenames ([#572](https://github.com/apache/hugegraph-toolchain/pull/572))

#### Option Changes

* feat(client): support user defined OKHTTPClient configs ([#590](https://github.com/apache/hugegraph-toolchain/pull/590)) 

#### Other Changes

* doc: update copyright date(year) in NOTICE ([#567](https://github.com/apache/hugegraph-toolchain/pull/567))
* chore(deps): bump ip from 1.1.5 to 1.1.9 in /hugegraph-hubble/hubble-fe ([#580](https://github.com/apache/hugegraph-toolchain/pull/580))
* refactor(hubble): enhance maven front plugin ([#568](https://github.com/apache/hugegraph-toolchain/pull/568))
* chore(deps): bump es5-ext from 0.10.53 to 0.10.63 in /hugegraph-hubble/hubble-fe ([#582](https://github.com/apache/hugegraph-toolchain/pull/582))
* chore(hubble): Enhance code style in hubble ([#592](https://github.com/apache/hugegraph-toolchain/pull/592))
* chore: upgrade version to 1.3.0 ([#596](https://github.com/apache/hugegraph-toolchain/pull/596))
* chore(ci): update profile commit id for 1.3 ([#597](https://github.com/apache/hugegraph-toolchain/pull/597))

### hugegraph-commons

#### Feature Changes

* feat: support user defined RestClientConfig/HTTPClient params ([#140](https://github.com/apache/hugegraph-commons/pull/140))

#### Bug Fix

#### Other Changes

* chore: disable clean flatten for deploy ([#141](https://github.com/apache/hugegraph-commons/pull/141))

### hugegraph-ai

这是 hugegraph-ai 的第一个发布版本，包含了多种特性，其中包括初始化的 Python 客户端、通过 LLM 构建知识图谱的能力，
以及基于 HugeGraph 的 RAG（Retrieval-Augmented Generation）集成。此外，该版本还在 python 客户端方面增加了重要的功能，
如变量 API、认证（auth）、度量（metric）、遍历器（traverser）和任务 API，以及使用 Gradio 创建交互式和可视化的演示。

除了这些新功能外，该版本还解决了多个错误和问题，确保了更加稳定和无误的用户体验。维护任务，如依赖更新、项目结构改进以及基本持续集成（CI）的添加，
进一步增强了项目的健壮性和开发工作流程。

> 这个版本的发布凝聚了 HugeGraph 社区的协作努力，感谢各位贡献者的付出。

#### Feature Changes

* feat: initialize hugegraph python client ([#5](https://github.com/apache/hugegraph-ai/pull/5))
* feat(llm): knowledge graph construction by llm ([#7](https://github.com/apache/hugegraph-ai/pull/7))
* feat: initialize rag based on HugeGraph ([#20](https://github.com/apache/hugegraph-ai/pull/20))
* feat(client): add variables api and test ([#24](https://github.com/apache/hugegraph-ai/pull/24))
* feat: add llm wenxinyiyan & config util & spo_triple_extract ([#27](https://github.com/apache/hugegraph-ai/pull/27))
* feat: add auth&metric&traverser&task api and ut ([#28](https://github.com/apache/hugegraph-ai/pull/28))
* feat: refactor construct knowledge graph task ([#29](https://github.com/apache/hugegraph-ai/pull/29))
* feat: Introduce gradio for creating interactive and visual demo ([#30](https://github.com/apache/hugegraph-ai/pull/30))

#### Bug Fix

* fix: invalid GitHub label ([#3](https://github.com/apache/hugegraph-ai/pull/3))
* fix: import error ([#13](https://github.com/apache/hugegraph-ai/pull/13))
* fix: function getEdgeByPage(): the generated query url does not include the parameter page ([#15](https://github.com/apache/hugegraph-ai/pull/15))
* fix: issue template ([#23](https://github.com/apache/hugegraph-ai/pull/23))
* fix: base-ref/head-ref missed in dependency-check-ci on branch push ([#25](https://github.com/apache/hugegraph-ai/pull/25))

#### Other Changes

* chore: add asf.yaml and ISSUE_TEMPLATE ([#1](https://github.com/apache/hugegraph-ai/pull/1))
* Bump urllib3 from 2.0.3 to 2.0.7 in /hugegraph-python ([#8](https://github.com/apache/hugegraph-ai/pull/8))
* chore: create .gitignore file for py ([#9](https://github.com/apache/hugegraph-ai/pull/9))
* refact: improve project structure & add some basic CI ([#17](https://github.com/apache/hugegraph-ai/pull/17))
* chore: Update LICENSE and NOTICE ([#31](https://github.com/apache/hugegraph-ai/pull/31))
* chore: add release scripts ([#33](https://github.com/apache/hugegraph-ai/pull/33))
* chore: change file chmod 755 ([#34](https://github.com/apache/hugegraph-ai/pull/34))

### 发布细节

Please check the release details/contributor in each repository:

- [Server Release Notes](https://github.com/apache/hugegraph/releases)
- [Toolchain Release Notes](https://github.com/apache/hugegraph-toolchain/releases)
- [AI Release Notes](https://github.com/apache/hugegraph-ai/releases)
- [Commons Release Notes](https://github.com/apache/hugegraph-commons/releases)
