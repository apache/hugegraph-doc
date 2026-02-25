---
title: "HugeGraph 1.2.0 Release Notes"
linkTitle: "Release-1.2.0"
weight: 7
---

### Java version statement

> In the future, we will gradually upgrade the java version, **Java 11** -> **Java 17** -> **Java 21**.

1. Consider using Java 11 in hugegraph/hugegraph-toolchain/hugegraph-commons, also compatible with Java 8 now. 
2. hugegraph-computer required to use Java 11, **not compatible with Java 8 now!**

**v1.2.0 是倒数第二个兼容 Java8 的大版本**, 到 1.5.0 [PD/Store](https://github.com/apache/hugegraph/issues/2265) 正式合入 master 
后标志着 Java8 兼容的正式终结 (除 Client 外所有组件都将以 Java 11 作为基准，然后逐步迈向 Java17/21).

### hugegraph

#### API Changes

- feat(api&core): in oltp apis, add statistics info and support full info about vertices and edges ([#2262](https://github.com/apache/hugegraph/pull/2262))
- feat(api): support embedded arthas agent in hugegraph-server ([#2278](https://github.com/apache/hugegraph/pull/2278),[#2337](https://github.com/apache/hugegraph/pull/2337))
- feat(api): support metric API Prometheus format & add statistic metric api ([#2286](https://github.com/apache/hugegraph/pull/2286))
- feat(api-core): support label & property filtering for both edge and vertex & support kout dfs mode ([#2295](https://github.com/apache/hugegraph/pull/2295))
- feat(api): support recording slow query log ([#2327](https://github.com/apache/hugegraph/pull/2327))


#### Feature Changes

- feat: support task auto manage by server role state machine ([#2130](https://github.com/apache/hugegraph/pull/2130))
- feat: support parallel compress snapshot ([#2136](https://github.com/apache/hugegraph/pull/2136))
- feat: use an enhanced CypherAPI to refactor it ([#2143](https://github.com/apache/hugegraph/pull/2143))
- feat(perf): support JMH benchmark in HG-test module ([#2238](https://github.com/apache/hugegraph/pull/2238))
- feat: optimising adjacency edge queries ([#2242](https://github.com/apache/hugegraph/pull/2242))
- Feat: IP white list ([#2299](https://github.com/apache/hugegraph/pull/2299))
- feat(cassandra): adapt cassandra from 3.11.12 to 4.0.10 ([#2300](https://github.com/apache/hugegraph/pull/2300))
- feat: support Cassandra with docker-compose in server ([#2307](https://github.com/apache/hugegraph/pull/2307))
- feat(core): support batch+parallel edges traverse ([#2312](https://github.com/apache/hugegraph/pull/2312))
- feat: adapt Dockerfile for new project structur ([#2344](https://github.com/apache/hugegraph/pull/2344))
- feat(server):swagger support auth for standardAuth mode by ([#2360](https://github.com/apache/hugegraph/pull/2360))
- feat(core): add IntMapByDynamicHash V1 implement ([#2377](https://github.com/apache/hugegraph/pull/2377))

#### Bug Fix

- fix: transfer add_peer/remove_peer command to leader ([#2112](https://github.com/apache/hugegraph/pull/2112))
- fix query dirty edges of a vertex with cache ([#2166](https://github.com/apache/hugegraph/pull/2166))
- fix exception of vertex-drop with index ([#2181](https://github.com/apache/hugegraph/pull/2181))
- fix: remove dup 'From' in filterExpiredResultFromFromBackend ([#2207](https://github.com/apache/hugegraph/pull/2207))
- fix: jdbc ssl mode parameter redundant ([#2224](https://github.com/apache/hugegraph/pull/2224))
- fix: error when start gremlin-console with sample script ([#2231](https://github.com/apache/hugegraph/pull/2231))
- fix(core): support order by id ([#2233](https://github.com/apache/hugegraph/pull/2233))
- fix: update ssl_mode value ([#2235](https://github.com/apache/hugegraph/pull/2235))
- fix: optimizing ClassNotFoundException error message for MYSQL ([#2246](https://github.com/apache/hugegraph/pull/2246))
- fix: asf invalid notification scheme 'discussions_status' ([#2247](https://github.com/apache/hugegraph/pull/2247))
- fix: asf invalid notification scheme 'discussions_comment' ([#2250](https://github.com/apache/hugegraph/pull/2250))
- fix: incorrect use of 'NO_LIMIT' variable ([#2253](https://github.com/apache/hugegraph/pull/2253))
- fix(core): close flat mapper iterator after usage ([#2281](https://github.com/apache/hugegraph/pull/2281))
- fix(dist): avoid var PRELOAD cover environmnet vars ([#2302](https://github.com/apache/hugegraph/pull/2302))
- fix: base-ref/head-ref missed in dependency-review on master ([#2308](https://github.com/apache/hugegraph/pull/2308))
- fix(core): handle schema Cache expandCapacity concurrent problem ([#2332](https://github.com/apache/hugegraph/pull/2332))
- fix: in wait-storage.sh, always wait for storage with default rocksdb ([#2333](https://github.com/apache/hugegraph/pull/2333))
- fix(api): refactor/downgrade record logic for slow log ([#2347](https://github.com/apache/hugegraph/pull/2347))
- fix(api): clean some code for release ([#2348](https://github.com/apache/hugegraph/pull/2348))
- fix: remove redirect-to-master from synchronous Gremlin API ([#2356](https://github.com/apache/hugegraph/pull/2356))
- fix HBase PrefixFilter bug ([#2364](https://github.com/apache/hugegraph/pull/2364))
- chore: fix curl failed to request https urls ([#2378](https://github.com/apache/hugegraph/pull/2378))
- fix(api): correct the vertex id in the edge-existence api ([#2380](https://github.com/apache/hugegraph/pull/2380))
- fix: github action build docker image failed during the release 1.2 process ([#2386](https://github.com/apache/hugegraph/pull/2386))
- fix: TinkerPop unit test lack some lables ([#2387](https://github.com/apache/hugegraph/pull/2387))

#### Option Changes

- feat(dist): support pre-load test graph data in docker container ([#2241](https://github.com/apache/hugegraph/pull/2241))

#### Other Changes

- refact: use standard UTF-8 charset & enhance CI configs ([#2095](https://github.com/apache/hugegraph/pull/2095))
- move validate release to hugegraph-doc ([#2109](https://github.com/apache/hugegraph/pull/2109))
- refact: use a slim way to build docker image on latest code & support zgc ([#2118](https://github.com/apache/hugegraph/pull/2118))
- chore: remove stage-repo in pom due to release done & update mail rule ([#2128](https://github.com/apache/hugegraph/pull/2128))
- doc: update issue template & README file ([#2131](https://github.com/apache/hugegraph/pull/2131))
- chore: cmn algorithm optimization ([#2134](https://github.com/apache/hugegraph/pull/2134))
- add github token for license check comment ([#2139](https://github.com/apache/hugegraph/pull/2139))
- chore: disable PR up-to-date in branch ([#2150](https://github.com/apache/hugegraph/pull/2150))
- refact(core): remove lock of globalMasterInfo to optimize perf ([#2151](https://github.com/apache/hugegraph/pull/2151))
- chore: async remove left index shouldn't effect query ([#2199](https://github.com/apache/hugegraph/pull/2199))
- refact(rocksdb): clean & reformat some code ([#2200](https://github.com/apache/hugegraph/pull/2200))
- refact(core): optimized batch removal of remaining indices consumed by a single consumer ([#2203](https://github.com/apache/hugegraph/pull/2203))
- add com.janeluo.ikkanalyzer dependency to core model ([#2206](https://github.com/apache/hugegraph/pull/2206))
- refact(core): early stop unnecessary loops in edge cache ([#2211](https://github.com/apache/hugegraph/pull/2211))
- doc: update README & add QR code ([#2218](https://github.com/apache/hugegraph/pull/2218))
- chore: update .asf.yaml for mail rule ([#2221](https://github.com/apache/hugegraph/pull/2221))
- chore: improve the UI & content in README ([#2227](https://github.com/apache/hugegraph/pull/2227))
- chore: add pr template ([#2234](https://github.com/apache/hugegraph/pull/2234))
- doc: modify ASF and remove meaningless CLA ([#2237](https://github.com/apache/hugegraph/pull/2237))
- chore(dist): replace wget to curl to download swagger-ui ([#2277](https://github.com/apache/hugegraph/pull/2277))
- Update StandardStateMachineCallback.java ([#2290](https://github.com/apache/hugegraph/pull/2290))
- doc: update README about start server with example graph ([#2315](https://github.com/apache/hugegraph/pull/2315))
- README.md tiny improve ([#2320](https://github.com/apache/hugegraph/pull/2320))
- doc: README.md tiny improve ([#2331](https://github.com/apache/hugegraph/pull/2331))
- refact: adjust project structure for merge PD & Store[Breaking Change] ([#2338](https://github.com/apache/hugegraph/pull/2338))
- chore: disable raft test in normal PR due to timeout problem ([#2349](https://github.com/apache/hugegraph/pull/2349))
- chore(ci): add stage profile settings ([#2361](https://github.com/apache/hugegraph/pull/2361))
- refact(api): update common 1.2 & fix jersey client code problem ([#2365](https://github.com/apache/hugegraph/pull/2365))
- chore: move server info into GlobalMasterInfo ([#2370](https://github.com/apache/hugegraph/pull/2370))
- chore: reset hugegraph version to 1.2.0 ([#2382](https://github.com/apache/hugegraph/pull/2382))


### hugegraph-computer
#### Feature Changes
* feat: implement fast-failover for MessageRecvManager and DataClientManager ([#243](https://github.com/apache/hugegraph-computer/pull/243))
* feat: implement parallel send data in load graph step ([#248](https://github.com/apache/hugegraph-computer/pull/248))
* feat(k8s): init operator project & add webhook ([#259](https://github.com/apache/hugegraph-computer/pull/259), [#263](https://github.com/apache/hugegraph-computer/pull/263))
* feat(core): support load vertex/edge snapshot ([#269](https://github.com/apache/hugegraph-computer/pull/269))
* feat(k8s): Add MinIO as internal(default) storage ([#272](https://github.com/apache/hugegraph-computer/pull/272))
* feat(algorithm): support random walk in computer ([#274](https://github.com/apache/hugegraph-computer/pull/274), [#280](https://github.com/apache/hugegraph-computer/pull/280))
* feat: use 'foreground' delete policy to cancel k8s job ([#290](https://github.com/apache/hugegraph-computer/pull/290))

#### Bug Fix
* fix: superstep not take effect ([#237](https://github.com/apache/hugegraph-computer/pull/237))
* fix(k8s): modify inconsistent apiGroups ([#270](https://github.com/apache/hugegraph-computer/pull/270))
* fix(algorithm): record loop is not copied ([#276](https://github.com/apache/hugegraph-computer/pull/276))
* refact(core): adaptor for common 1.2 & fix a string of possible CI problem ([#286](https://github.com/apache/hugegraph-computer/pull/286))
* fix: remove okhttp1 due to conflicts risk ([#294](https://github.com/apache/hugegraph-computer/pull/294))
* fix(core): io.grpc.grpc-core dependency conflic ([#296](https://github.com/apache/hugegraph-computer/pull/296))

#### Option Changes
* feat(core): isolate namespace for different input data source ([#252](https://github.com/apache/hugegraph-computer/pull/252))
* refact(core): support auth config for computer task ([#265](https://github.com/apache/hugegraph-computer/pull/265))

#### Other Changes
* remove apache stage repo & update notification rule ([#232](https://github.com/apache/hugegraph-computer/pull/232))
* chore: fix empty license file ([#233](https://github.com/apache/hugegraph-computer/pull/233))
* chore: enhance mailbox settings & enable require ci ([#235](https://github.com/apache/hugegraph-computer/pull/235))
* fix: typo errors in start-computer.sh ([#238](https://github.com/apache/hugegraph-computer/pull/238))
* [Feature-241] Add PULL_REQUEST_TEMPLATE ([#242](https://github.com/apache/hugegraph-computer/pull/242), [#257](https://github.com/apache/hugegraph-computer/pull/257))
* chore: change etcd url only for ci ([#245](https://github.com/apache/hugegraph-computer/pull/245))
* doc: update readme & add QR code ([#249](https://github.com/apache/hugegraph-computer/pull/249))
* doc(k8s): add building note for missing classes ([#254](https://github.com/apache/hugegraph-computer/pull/254))
* chore: reduce mail to dev list ([#255](https://github.com/apache/hugegraph-computer/pull/255))
* add: dependency-review ([#266](https://github.com/apache/hugegraph-computer/pull/266))
* chore: correct incorrect comment ([#268](https://github.com/apache/hugegraph-computer/pull/268))
* refactor(api): ListValue.getFirst() replaces ListValue.get(0) ([#282](https://github.com/apache/hugegraph-computer/pull/282))
* Improve: Passing workerId to WorkerStat & Skip wait worker close if master executes failed ([#292](https://github.com/apache/hugegraph-computer/pull/292))
* chore: add check dependencies ([#293](https://github.com/apache/hugegraph-computer/pull/293))
* chore(license): update license for 1.2.0 ([#299](https://github.com/apache/hugegraph-computer/pull/299))

### hugegraph-toolchain

#### API Changes

- feat(client): support edgeExistence api ([#544](https://github.com/apache/hugegraph-toolchain/pull/544))
- refact(client): update tests for new OLTP traverser APIs ([#550](https://github.com/apache/hugegraph-toolchain/pull/550))


#### Feature Changes

- feat(spark): support spark-sink connector for loader ([#497](https://github.com/apache/hugegraph-toolchain/pull/497))
- feat(loader): support kafka as datasource ([#506](https://github.com/apache/hugegraph-toolchain/pull/506))
- feat(client): support go client for hugegraph ([#514](https://github.com/apache/hugegraph-toolchain/pull/514))
- feat(loader): support docker for loader ([#530](https://github.com/apache/hugegraph-toolchain/pull/530))
- feat: update common version and remove jersey code ([#538](https://github.com/apache/hugegraph-toolchain/pull/538))


#### Bug Fix

- fix: convert numbers to strings ([#465](https://github.com/apache/hugegraph-toolchain/pull/465))
- fix: hugegraph-spark-loader shell string length limit ([#469](https://github.com/apache/hugegraph-toolchain/pull/469))
- fix: spark loader meet Exception: Class is not registered ([#470](https://github.com/apache/hugegraph-toolchain/pull/470))
- fix: spark loader Task not serializable ([#471](https://github.com/apache/hugegraph-toolchain/pull/471))
- fix: spark with loader has dependency conflicts ([#480](https://github.com/apache/hugegraph-toolchain/pull/480))
- fix: spark-loader example schema and struct mismatch ([#504](https://github.com/apache/hugegraph-toolchain/pull/504))
- fix(loader): error log ([#499](https://github.com/apache/hugegraph-toolchain/pull/499))
- fix: checkstyle && add suppressions.xml ([#500](https://github.com/apache/hugegraph-toolchain/pull/500))
- fix(loader): resolve error in loader script ([#510](https://github.com/apache/hugegraph-toolchain/pull/510))
- fix: base-ref/head-ref missed in dependency-check-ci on branch push ([#516](https://github.com/apache/hugegraph-toolchain/pull/516), [#551](https://github.com/apache/hugegraph-toolchain/pull/551))
- fix yarn network connection on linux/arm64 arch ([#519](https://github.com/apache/hugegraph-toolchain/pull/519))
- fix(hubble): drop-down box could not display all options ([#535](https://github.com/apache/hugegraph-toolchain/pull/535))
- fix(hubble): build with node and yarn ([#543](https://github.com/apache/hugegraph-toolchain/pull/543))
- fix(loader): loader options ([#548](https://github.com/apache/hugegraph-toolchain/pull/548))
- fix(hubble): parent override children dep version ([#549](https://github.com/apache/hugegraph-toolchain/pull/549))
- fix: exclude okhttp1 which has different groupID with okhttp3 ([#555](https://github.com/apache/hugegraph-toolchain/pull/555))
- fix: github action build docker image failed ([#556](https://github.com/apache/hugegraph-toolchain/pull/556), [#557](https://github.com/apache/hugegraph-toolchain/pull/557))
- fix: build error with npm not exist & tiny improve ([#558](https://github.com/apache/hugegraph-toolchain/pull/558))


#### Option Changes

- set default data when create graph ([#447](https://github.com/apache/hugegraph-toolchain/pull/447))


#### Other Changes

- chore: remove apache stage repo & update mail rule ([#433](https://github.com/apache/hugegraph-toolchain/pull/433), [#474](https://github.com/apache/hugegraph-toolchain/pull/474), [#479](https://github.com/apache/hugegraph-toolchain/pull/479))
- refact: clean extra store file in all modules ([#434](https://github.com/apache/hugegraph-toolchain/pull/434))
- chore: use fixed node.js version 16 to avoid ci problem ([#437](https://github.com/apache/hugegraph-toolchain/pull/437), [#441](https://github.com/apache/hugegraph-toolchain/pull/441))
- chore(hubble): use latest code in Dockerfile ([#440](https://github.com/apache/hugegraph-toolchain/pull/440))
- chore: remove maven plugin for docker build ([#443](https://github.com/apache/hugegraph-toolchain/pull/443))
- chore: improve spark parallel ([#450](https://github.com/apache/hugegraph-toolchain/pull/450))
- doc: fix build status badge link ([#455](https://github.com/apache/hugegraph-toolchain/pull/455))
- chore: keep hadoop-hdfs-client and hadoop-common version consistent ([#457](https://github.com/apache/hugegraph-toolchain/pull/457))
- doc: add basic contact info & QR code in README ([#462](https://github.com/apache/hugegraph-toolchain/pull/462), [#475](https://github.com/apache/hugegraph-toolchain/pull/475))
- chore: disable PR up-to-date in branch ([#473](https://github.com/apache/hugegraph-toolchain/pull/473))
- chore: auto add pr auto label by path ([#466](https://github.com/apache/hugegraph-toolchain/pull/466), [#528](https://github.com/apache/hugegraph-toolchain/pull/528))
- chore: unify the dependencies versions of the entire project ([#478](https://github.com/apache/hugegraph-toolchain/pull/478))
- chore(deps): bump async, semver, word-wrap, browserify-sign in hubble-fe ([#484](https://github.com/apache/hugegraph-toolchain/pull/484), [#491](https://github.com/apache/hugegraph-toolchain/pull/491), [#494](https://github.com/apache/hugegraph-toolchain/pull/494), [#529](https://github.com/apache/hugegraph-toolchain/pull/529))
- chore: add pr template ([#498](https://github.com/apache/hugegraph-toolchain/pull/498))
- doc(hubble): add docker-compose to start with server ([#522](https://github.com/apache/hugegraph-toolchain/pull/522))
- chore(ci): add stage profile settings ([#536](https://github.com/apache/hugegraph-toolchain/pull/536))
- chore(client): increase the api num as the latest server commit + 10 ([#546](https://github.com/apache/hugegraph-toolchain/pull/546))
- chore(spark): install hugegraph from source ([#552](https://github.com/apache/hugegraph-toolchain/pull/552))
- doc: adjust docker related desc in readme ([#559](https://github.com/apache/hugegraph-toolchain/pull/559))
- chore(license): update license for 1.2 ([#560](https://github.com/apache/hugegraph-toolchain/pull/560), [#561](https://github.com/apache/hugegraph-toolchain/pull/561))



### hugegraph-commons

#### Feature Changes

- feat(common): replace jersey dependencies with OkHttp (Breaking Change) ([#133](https://github.com/apache/hugegraph-commons/pull/133))

#### Bug Fix

- fix(common): handle spring-boot2/jersey dependency conflicts ([#131](https://github.com/apache/hugegraph-commons/pull/131))
- fix: Assert.assertThrows() should check result of exceptionConsumer ([#135](https://github.com/apache/hugegraph-commons/pull/135))
- fix(common): json param convert ([#137](https://github.com/apache/hugegraph-commons/pull/137))

#### Other Changes

- refact(common): add more construction methods for convenient ([#132](https://github.com/apache/hugegraph-commons/pull/132))
- add: dependency-review ([#134](https://github.com/apache/hugegraph-commons/pull/134))
- refact(common): rename jsonutil to avoid conflicts with server ([#136](https://github.com/apache/hugegraph-commons/pull/136))
- doc: update README for release ([#138](https://github.com/apache/hugegraph-commons/pull/138))
- update licence ([#139](https://github.com/apache/hugegraph-commons/pull/139))

### Release Details

Please check the release details in each repository:

- [Server Release Notes](https://github.com/apache/hugegraph/releases)
- [Toolchain Release Notes](https://github.com/apache/hugegraph-toolchain/releases)
- [Computer Release Notes](https://github.com/apache/hugegraph-computer/releases)
- [Commons Release Notes](https://github.com/apache/hugegraph-commons/releases)
