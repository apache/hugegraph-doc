---
title: "HugeGraph 1.0.0 Release Notes"
linkTitle: "Release-1.0.0"
weight: 9
---

### OLTP API & Client Changes

#### API Changes

- feat(api): support hot set trace through /exception/trace API.
- feat(api): support query by Cypher language.
- feat(api): support swagger UI to viewing API.

#### Client Changes

- feat(client) support Cypher query API.
- refact(client): change 'limit' type from long to int.
- feat(client): server bypass for hbase writing (Beta).

### Core & Server

#### Feature Changes

- feat: support Java 11.
- feat(core): support adamic-adar & resource-allocation algorithms.
- feat(hbase): support hash rowkey & pre-init tables.
- feat(core): support query by Cypher language.
- feat(core): support automatic management and fail-over for cluster role.
- feat(core): support 16 OLAP algorithms, like: LPA, Louvain, PageRank, BetweennessCentrality, RingsDetect.
- feat: prepare for Apache release.

#### Bug Fix

- fix(core): can't query edges by multi labels + properties.
- fix(core): occasionally NoSuchMethodError Relations().
- fix(core): limit max depth for cycle detection.
- fix(core): traversal contains Tree step has different result.
- fix edge batch update error.
- fix unexpected task status.
- fix(core): edge cache not clear when update or delete associated vertex.
- fix(mysql): run g.V() is error when it's MySQL backend.
- fix: close exception and server-info EXPIRED_INTERVAL.
- fix: export ConditionP.
- fix: query by within + Text.contains.
- fix: schema label race condition of addIndexLabel/removeIndexLabel.
- fix: limit admin role can drop graph.
- fix: ProfileApi url check & add build package to ignore file.
- fix: can't shut down when starting with exception.
- fix: Traversal.graph is empty in StepStrategy.apply() with count().is(0).
- fix: possible extra comma before where statement in MySQL backend.
- fix: JNA UnsatisfiedLinkError for Apple M1.
- fix: start RpcServer NPE & args count of ACTION_CLEARED error & example error.
- fix: rpc server not start.
- fix: User-controlled data in numeric cast & remove word dependency.
- fix: closing iterators on errors for Cassandra & Mysql.

#### Option Changes

- move `raft.endpoint` option from graph scope to server scope.

#### Other Changes

- refact(core): enhance schema job module.
- refact(raft): improve raft module & test & install snapshot and add peer.
- refact(core): remove early cycle detection & limit max depth.
- cache: fix assert node.next==empty.
- fix apache license conflicts: jnr-posix and jboss-logging.
- chore: add logo in README & remove outdated log4j version.
- refact(core): improve CachedGraphTransaction perf.
- chore: update CI config & support ci robot & add codeQL SEC-check & graph option.
- refact: ignore security check api & fix some bugs & clean code.
- doc: enhance CONTRIBUTING.md & README.md.
- refact: add checkstyle plugin & clean/format the code.
- refact(core): improve decode string empty bytes & avoid array-construct columns in BackendEntry.
- refact(cassandra): translate ipv4 to ipv6 metrics & update cassandra dependency version.
- chore: use .asf.yaml for apache workflow & replace APPLICATION_JSON with TEXT_PLAIN.
- feat: add system schema store.
- refact(rocksdb): update rocksdb version to 6.22 & improve rocksdb code.
- refact: update mysql scope to test & clean protobuf style/configs.
- chore: upgrade Dockerfile server to 0.12.0 & add editorconfig & improve ci.
- chore: upgrade grpc version.
- feat: support updateIfPresent/updateIfAbsent operation.
- chore: modify abnormal logs & upgrade netty-all to 4.1.44.
- refact: upgrade dependencies & adopt new analyzer & clean code.
- chore: improve .gitignore & update ci configs & add RAT/flatten plugin.
- chore(license): add dependencies-check ci & 3rd-party dependency licenses.
- refact: Shutdown log when shutdown process & fix tx leak & enhance the file path.
- refact: rename package to apache & dependency in all modules (Breaking Change).
- chore: add license checker & update antrun plugin & fix building problem in windows.
- feat: support one-step script for apache release v1.0.0 release.

### Computer (OLAP)

#### Algorithm Changes

- feat: implement page-rank algorithm.
- feat: implement wcc algorithm.
- feat: implement degree centrality.
- feat: implement triangle_count algorithm.
- feat: implement rings-detection algorithm.
- feat: implement LPA algorithm.
- feat: implement kcore algorithm.
- feat: implement closeness centrality algorithm.
- feat: implement betweenness centrality algorithm.
- feat: implement cluster coefficient algorithm.

#### Platform Changes

- feat: init module computer-core & computer-algorithm & etcd dependency.
- feat: add Id as base type of vertex id.
- feat: init Vertex/Edge/Properties & JsonStructGraphOutput.
- feat: load data from hugegraph server.
- feat: init basic combiner, Bsp4Worker, Bsp4Master.
- feat: init sort & transport interface & basic FileInput/Output Stream.
- feat: init computation & ComputerOutput/Driver interface.
- feat: init Partitioner and HashPartitioner
- feat: init Master/WorkerService module.
- feat: init Heap/LoserTree sorting.
- feat: init rpc module.
- feat: init transport server, client, en/decode, flowControl, heartbeat.
- feat: init DataDirManager & PointerCombiner.
- feat: init aggregator module & add copy() and assign() methods to Value class.
- feat: add startAsync and finishAsync on client side, add onStarted and onFinished on server side.
- feat: init store/sort module.
- feat: link managers in worker sending end.
- feat: implement data receiver of worker.
- feat: implement StreamGraphInput and EntryInput.
- feat: add Sender and Receiver to process compute message.
- feat: add seqfile fromat.
- feat: add ComputeManager.
- feat: add computer-k8s and computer-k8s-operator.
- feat: add startup and make docker image code.
- feat: sort different type of message use different combiner.
- feat: add HDFS output format.
- feat: mount config-map and secret to container.
- feat: support java11.
- feat: support partition concurrent compute.
- refact: abstract computer-api from computer-core.
- refact: optimize data receiving.
- fix: release file descriptor after input and compute.
- doc: add operator deploy readme.
- feat: prepare for Apache release.

### Toolchain (loader, tools, hubble)

- feat(loader): support use SQL to construct graph.
- feat(loader): support Spark-Loader mode(include jdbc source).
- feat(loader): support Flink-CDC mode.
- fix(loader):  fix NPE when loading ORC data.
- fix(loader):  fix schema is not cached with Spark/Flink mode.
- fix(loader):  fix json deserialize error.
- fix(loader):  fix jackson conflicts & missing dependencies.
- feat(hubble): supplementary algorithms UI.
- feat(hubble): support highlighting and hints for Gremlin text.
- feat(hubble): add docker-file for hubble.
- feat(hubble): display packaging log output progress while building.
- fix(hubble):  fix port-input placeholder UI.
- feat: prepare for Apache release.

### Commons (common,rpc)

- feat: support assert-throws method returning Future.
- feat: add Cnm and Anm to CollectionUtil.
- feat: support custom content-type.
- feat: prepare for Apache release.

### Release Details

Please check the release details in each repository:

- [Server Release Notes](https://github.com/apache/hugegraph/releases/tag/1.0.0)
- [Toolchain Release Notes](https://github.com/apache/hugegraph-toolchain/releases/tag/1.0.0)
- [Computer Release Notes](https://github.com/apache/hugegraph-computer/releases/tag/1.0.0)
- [Commons Release Notes](https://github.com/apache/hugegraph-commons/releases/tag/1.0.0)
