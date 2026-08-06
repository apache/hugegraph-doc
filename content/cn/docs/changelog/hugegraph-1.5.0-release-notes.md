---
title: "HugeGraph 1.5.0 Release Notes"
linkTitle: "Release-1.5.0"
weight: 3
---

> WIP: This doc is under construction, please wait for the final version (BETA) 

### 运行环境/版本说明

1. **1.5.0**版开始， `hugegraph` 相关组件仅支持 Java 11 编译/运行环境 

PS: 未来 HugeGraph 组件的版本会朝着 `Java 11 -> Java 17 -> Java 21` 演进

### hugegraph

> 本版本新增了大量功能并进行了多项优化，尤其是针对自控分布式版本新后端 HStore (Raft + RocksDB) 的实现支持，欢迎试用反馈

#### API Changes

- **BREAKING CHANGE**: Support "parent & child" `EdgeLabel` type [#2662](https://github.com/apache/hugegraph/pull/2662)

#### Feature Changes

- Integrate `pd-grpc`, `pd-common`, and `pd-client` [#2498](https://github.com/apache/hugegraph/pull/2498)
- Integrate `store-grpc`, `store-common`, and `store-client` [#2476](https://github.com/apache/hugegraph/pull/2476)
- Integrate `store-rocksdb` submodule [#2513](https://github.com/apache/hugegraph/pull/2513)
- Integrate `pd-core` into HugeGraph [#2478](https://github.com/apache/hugegraph/pull/2478)
- Integrate `pd-service` into HugeGraph [#2528](https://github.com/apache/hugegraph/pull/2528)
- Integrate `pd-dist` into HugeGraph and add core tests, client tests, and REST tests for PD [#2532](https://github.com/apache/hugegraph/pull/2532)
- Integrate `server-hstore` into HugeGraph [#2534](https://github.com/apache/hugegraph/pull/2534)
- Integrate `store-core` submodule [#2548](https://github.com/apache/hugegraph/pull/2548)
- Integrate `store-node` submodule [#2537](https://github.com/apache/hugegraph/pull/2537)
- Support new backend Hstore [#2560](https://github.com/apache/hugegraph/pull/2560)
- Support Docker deployment for PD and Store [#2573](https://github.com/apache/hugegraph/pull/2573)
- Add a tool method `encode` [#2647](https://github.com/apache/hugegraph/pull/2647)
- Add basic `MiniCluster` module for distributed system testing [#2615](https://github.com/apache/hugegraph/pull/2615)
- Support disabling RocksDB auto-compaction via configuration [#2586](https://github.com/apache/hugegraph/pull/2586)

#### Bug Fixes

- Switch RocksDB backend to memory when executing Gremlin examples [#2518](https://github.com/apache/hugegraph/pull/2518)
- Avoid overriding backend config in Gremlin example scripts [#2519](https://github.com/apache/hugegraph/pull/2519)
- Update resource references [#2522](https://github.com/apache/hugegraph/pull/2522)
- Randomly generate default values [#2568](https://github.com/apache/hugegraph/pull/2568)
- Update build artifact path for Docker deployment [#2590](https://github.com/apache/hugegraph/pull/2590)
- Ensure thread safety for range attributes in PD [#2641](https://github.com/apache/hugegraph/pull/2641)
- Correct server Docker copy source path [#2637](https://github.com/apache/hugegraph/pull/2637)
- Fix JRaft Timer Metrics bug in Hstore [#2602](https://github.com/apache/hugegraph/pull/2602)
- Enable JRaft MaxBodySize configuration [#2633](https://github.com/apache/hugegraph/pull/2633)

#### Option Changes

- Mark old raft configs as deprecated [#2661](https://github.com/apache/hugegraph/pull/2661)
- Enlarge bytes write limit and remove `big` parameter when encoding/decoding string ID length [#2622](https://github.com/apache/hugegraph/pull/2622)

#### Other Changes

- Add Swagger-UI LICENSE files [#2495](https://github.com/apache/hugegraph/pull/2495)
- Translate CJK comments and punctuations to English across multiple modules [#2536](https://github.com/apache/hugegraph/pull/2536), [#2623](https://github.com/apache/hugegraph/pull/2625), [#2645](https://github.com/apache/hugegraph/pull/2645)
- Introduce `install-dist` module in root [#2552](https://github.com/apache/hugegraph/pull/2552)
- Enable up-to-date checks for UI (CI) [#2609](https://github.com/apache/hugegraph/pull/2609)
- Minor improvements for POM properties [#2574](https://github.com/apache/hugegraph/pull/2574)
- Migrate HugeGraph Commons [#2628](https://github.com/apache/hugegraph/pull/2628)
- Tar source and binary packages for HugeGraph with PD-Store [#2594](https://github.com/apache/hugegraph/pull/2594)
- Refactor: Enhance cache invalidation of the partition → leader shard in `ClientCache` [#2588](https://github.com/apache/hugegraph/pull/2588)
- Refactor: Remove redundant properties in `LogMeta` and `PartitionMeta` [#2598](https://github.com/apache/hugegraph/pull/2598)

### hugegraph-toolchain

#### API Changes
- Support "parent & child" `EdgeLabel` type [#624](https://github.com/apache/hugegraph-toolchain/pull/624)

#### Feature Changes
- Support English interface & add a script/doc for it in Hubble [#631](https://github.com/apache/hugegraph-toolchain/pull/631)

#### Bug Fixes
- Serialize source and target label for non-father EdgeLabel [#628](https://github.com/apache/hugegraph-toolchain/pull/628)
- Encode/decode Chinese error after building Hubble package [#627](https://github.com/apache/hugegraph-toolchain/pull/627)
- Configure IPv4 to fix timeout of `yarn install` in Hubble [#636](https://github.com/apache/hugegraph-toolchain/pull/636)
- Remove debugging output to speed up the frontend construction in Hubble [#638](https://github.com/apache/hugegraph-toolchain/pull/638)

#### Other Changes
- Bump `express` from 4.18.2 to 4.19.2 in Hubble Frontend [#598](https://github.com/apache/hugegraph-toolchain/pull/598)
- Make IDEA support IssueNavigationLink [#600](https://github.com/apache/hugegraph-toolchain/pull/600)
- Update `yarn.lock` for Hubble [#605](https://github.com/apache/hugegraph-toolchain/pull/605)
- Introduce `editorconfig-maven-plugin` for verifying code style defined in `.editorconfig` [#614](https://github.com/apache/hugegraph-toolchain/pull/614)
- Upgrade distribution version to 1.5.0 [#639](https://github.com/apache/hugegraph-toolchain/pull/639)

#### Documentation Changes
- Clarify the contributing guidelines [#604](https://github.com/apache/hugegraph-toolchain/pull/604)
- Enhance the README file for Hubble [#613](https://github.com/apache/hugegraph-toolchain/pull/613)
- Update README style referring to the server's style [#615](https://github.com/apache/hugegraph-toolchain/pull/615)

### hugegraph-ai

#### API Changes

- Added local LLM API and version API. [#41](https://github.com/apache/hugegraph-ai/pull/41), [#44](https://github.com/apache/hugegraph-ai/pull/44)
- Implemented new API and optimized code structure. [#63](https://github.com/apache/hugegraph-ai/pull/63)
- Support for graphspace and refactored all APIs. [#67](https://github.com/apache/hugegraph-ai/pull/67)

#### Feature Changes

- Added openai's apibase configuration and asynchronous methods in RAG web demo. [#41](https://github.com/apache/hugegraph-ai/pull/41), [#58](https://github.com/apache/hugegraph-ai/pull/58)
- Support for multi reranker and enhanced UI. [#73](https://github.com/apache/hugegraph-ai/pull/73)
- Node embedding, node classify, and graph classify with models based on DGL. [#83](https://github.com/apache/hugegraph-ai/pull/83)
- Graph learning algorithm implementation (10+). [#102](https://github.com/apache/hugegraph-ai/pull/102)
- Support for any openai-style API (standard). [#95](https://github.com/apache/hugegraph-ai/pull/95)

#### Bug Fixes

- Fixed fusiform_similarity test in traverser for server 1.3.0. [#37](https://github.com/apache/hugegraph-ai/pull/37)
- Avoid generating config twice and corrected e_cache type. [#56](https://github.com/apache/hugegraph-ai/pull/56), [#117](https://github.com/apache/hugegraph-ai/pull/117)
- Fixed null value detection on vid attributes. [#115](https://github.com/apache/hugegraph-ai/pull/115)
- Handled profile regenerate error. [#98](https://github.com/apache/hugegraph-ai/pull/98)

#### Option Changes

- Added auth for fastapi and gradio. [#70](https://github.com/apache/hugegraph-ai/pull/70)
- Support for multiple property types and importing graph from the entire doc. [#84](https://github.com/apache/hugegraph-ai/pull/84)

#### Other Changes

- Reformatted documentation and updated README. [#36](https://github.com/apache/hugegraph-ai/pull/36), [#81](https://github.com/apache/hugegraph-ai/pull/81)
- Introduced a black for code format in GitHub actions. [#47](https://github.com/apache/hugegraph-ai/pull/47)
- Updated dependencies and environment preparations. [#45](https://github.com/apache/hugegraph-ai/pull/45), [#65](https://github.com/apache/hugegraph-ai/pull/65)
- Enhanced user-friendly README. [#82](https://github.com/apache/hugegraph-ai/pull/82)

### hugegraph-computer

#### Feature Changes

- Support Single Source Shortest Path Algorithm [#285](https://github.com/apache/hugegraph-computer/pull/285)
- Support Output Filter [#303](https://github.com/apache/hugegraph-computer/pull/303)

#### Bug Fixes

- Fix: base-ref/head-ref Missed in Dependency-Review on Schedule Push [#304](https://github.com/apache/hugegraph-computer/pull/304)

#### Option Changes

- Refactor(core): StringEncoding [#300](https://github.com/apache/hugegraph-computer/pull/300)

#### Other Changes

- Improve(algorithm): Random Walk Vertex Inactive [#301](https://github.com/apache/hugegraph-computer/pull/301)
- Upgrade Version to 1.3.0 [#305](https://github.com/apache/hugegraph-computer/pull/305)
- Doc(readme): Clarify the Contributing Guidelines [#306](https://github.com/apache/hugegraph-computer/pull/306)
- Doc(readme): Add Hyperlink to Apache 2.0 [#308](https://github.com/apache/hugegraph-computer/pull/308)
- Migrate Project to Computer Directory [#310](https://github.com/apache/hugegraph-computer/pull/310)
- Update for Release 1.5 [#317](https://github.com/apache/hugegraph-computer/pull/317)
- Fix Path When Exporting Source Package [#319](https://github.com/apache/hugegraph-computer/pull/319)

### 发布细节

Please check the release details/contributor in each repository:

- [Server Release Notes](https://github.com/apache/hugegraph/releases)
- [Toolchain Release Notes](https://github.com/apache/hugegraph-toolchain/releases)
- [Computer Release Notes](https://github.com/apache/hugegraph-computer/releases)
- [AI Release Notes](https://github.com/apache/hugegraph-ai/releases)
