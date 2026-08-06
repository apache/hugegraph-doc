---
title: "HugeGraph 1.7.0 Release Notes"
linkTitle: "Release-1.7.0"
weight: 1
---

> WIP: This doc is under construction, please wait for the final version (BETA)

### Operating Environment / Version Description

For **1.7.0** version `hugegraph`, related components only support Java11.

### hugegraph

#### API Changes

- **BREAKING CHANGE**: Disable legacy backends include MySQL/PG/c*(.etc) [#2746](https://github.com/apache/hugegraph/pull/2746)
- **BREAKING CHANGE**: Release version 1.7.0 [server + pd + store] [#2889](https://github.com/apache/hugegraph/pull/2889)

#### Feature Changes

- Support MemoryManagement for graph query framework [#2649](https://github.com/apache/hugegraph/pull/2649)
- LoginAPI support token_expire field [#2754](https://github.com/apache/hugegraph/pull/2754)
- Add option for task role election [#2843](https://github.com/apache/hugegraph/pull/2843)
- Optimize perf by avoid boxing long [#2861](https://github.com/apache/hugegraph/pull/2861)
- StringId hold bytes to avoid decode/encode [#2862](https://github.com/apache/hugegraph/pull/2862)
- Add PerfExample5 and PerfExample6 [#2860](https://github.com/apache/hugegraph/pull/2860)
- RocksDBStore remove redundant checkOpened() call [#2863](https://github.com/apache/hugegraph/pull/2863)
- Add path filter [#2898](https://github.com/apache/hugegraph/pull/2898)
- Init serena memory system & add memories [#2902](https://github.com/apache/hugegraph/pull/2902)

#### Bug Fixes

- Filter dynamice path(PUT/GET/DELETE) with params cause OOM [#2569](https://github.com/apache/hugegraph/pull/2569)
- JRaft Histogram Metrics Value NaN [#2631](https://github.com/apache/hugegraph/pull/2631)
- Update server image desc [#2702](https://github.com/apache/hugegraph/pull/2702)
- Kneigbor-api has unmatched edge type with server [#2699](https://github.com/apache/hugegraph/pull/2699)
- Add license for swagger-ui & reset use stage to false in ci yml [#2706](https://github.com/apache/hugegraph/pull/2706)
- Fix build pd-store arm image [#2744](https://github.com/apache/hugegraph/pull/2744)
- Fix graph server cache notifier mechanism [#2729](https://github.com/apache/hugegraph/pull/2729)
- Tx leak when stopping the graph server [#2791](https://github.com/apache/hugegraph/pull/2791)
- Ensure backend is initialized in gremlin script [#2824](https://github.com/apache/hugegraph/pull/2824)
- Fix some potential lock & type cast issues [#2895](https://github.com/apache/hugegraph/pull/2895)
- Fix npe in getVersion [#2897](https://github.com/apache/hugegraph/pull/2897)
- Fix the support for graphsapi in rocksdb and add testing for graphsapi [#2900](https://github.com/apache/hugegraph/pull/2900)
- Remove graph path in auth api path [#2899](https://github.com/apache/hugegraph/pull/2899)
- Migrate to LTS jdk11 in all Dockerfile [#2901](https://github.com/apache/hugegraph/pull/2901)
- Remove the judgment for java8 compatibility in the init-store [#2905](https://github.com/apache/hugegraph/pull/2905)
- Add missing license and remove binary license.txt & fix tinkerpop ci & remove duplicate module [#2910](https://github.com/apache/hugegraph/pull/2910)

#### Option Changes

- Remove some outdated configuration [#2678](https://github.com/apache/hugegraph/pull/2678)

#### Other Changes

- Update outdated docs for release 1.5.0 [#2690](https://github.com/apache/hugegraph/pull/2690)
- Fix licenses and remove empty files [#2692](https://github.com/apache/hugegraph/pull/2692)
- Update repo artifacts references [#2695](https://github.com/apache/hugegraph/pull/2695)
- Adjust release fury version [#2698](https://github.com/apache/hugegraph/pull/2698)
- Fix the JSON license issue [#2697](https://github.com/apache/hugegraph/pull/2697)
- Add debug info for tp test [#2688](https://github.com/apache/hugegraph/pull/2688)
- Enhance words in README [#2734](https://github.com/apache/hugegraph/pull/2734)
- Add collaborators in asf config [#2741](https://github.com/apache/hugegraph/pull/2741)
- Adjust the related filters of sofa-bolt [#2735](https://github.com/apache/hugegraph/pull/2735)
- Reopen discussion in .asf.yml config [#2751](https://github.com/apache/hugegraph/pull/2751)
- Fix typo in README [#2806](https://github.com/apache/hugegraph/pull/2806)
- Centralize version management in project [#2797](https://github.com/apache/hugegraph/pull/2797)
- Update notice year [#2826](https://github.com/apache/hugegraph/pull/2826)
- Improve maven Reproducible Builds → upgrade plugins [#2874](https://github.com/apache/hugegraph/pull/2874)
- Enhance docker instruction with auth opened graph [#2881](https://github.com/apache/hugegraph/pull/2881)
- Remove the package existing in java8 [#2792](https://github.com/apache/hugegraph/pull/2792)
- Revise Docker usage instructions in README [#2882](https://github.com/apache/hugegraph/pull/2882)
- Add DeepWiki badge to README [#2883](https://github.com/apache/hugegraph/pull/2883)
- Update guidance for store module [#2894](https://github.com/apache/hugegraph/pull/2894)
- Update test commands and improve documentation clarity [#2893](https://github.com/apache/hugegraph/pull/2893)
- Bump rocksdb version from 7.2.2 to 8.10.2 [#2896](https://github.com/apache/hugegraph/pull/2896)

### hugegraph-toolchain

#### API Changes

- Support graphspace [#633](https://github.com/apache/hugegraph-toolchain/pull/633)

#### Feature Changes

- Support jdbc date type & sync .editorconfig [#648](https://github.com/apache/hugegraph-toolchain/pull/648)
- Add a useSSL option for mysql [#650](https://github.com/apache/hugegraph-toolchain/pull/650)
- Patch for father sub edge [#654](https://github.com/apache/hugegraph-toolchain/pull/654)
- Improve user experience for user script [#666](https://github.com/apache/hugegraph-toolchain/pull/666)
- Support concurrent readers, short-id & Graphsrc [#683](https://github.com/apache/hugegraph-toolchain/pull/683)
- Init serena onboarding & project memory files [#692](https://github.com/apache/hugegraph-toolchain/pull/692)

#### Bug Fixes

- Typo word in display [#655](https://github.com/apache/hugegraph-toolchain/pull/655)
- Patch up missing classes and methods for hubble [#657](https://github.com/apache/hugegraph-toolchain/pull/657)
- Adjust Client to 1.7.0 server [#689](https://github.com/apache/hugegraph-toolchain/pull/689)
- Remove json license for release 1.7.0 [#698](https://github.com/apache/hugegraph-toolchain/pull/698)

#### Other Changes

- Update hugegraph source commit id [#640](https://github.com/apache/hugegraph-toolchain/pull/640)
- Add collaborators in asf config [#656](https://github.com/apache/hugegraph-toolchain/pull/656)
- Update pom for version-1.7.0 [#681](https://github.com/apache/hugegraph-toolchain/pull/681)
- Add DeepWiki badge to README [#684](https://github.com/apache/hugegraph-toolchain/pull/684)
- Adjust APIs to compatible with 1.7.0 server [#685](https://github.com/apache/hugegraph-toolchain/pull/685)
- Adjust LoadContext to 1.7.0 version [#687](https://github.com/apache/hugegraph-toolchain/pull/687)
- Migrate to LTS jdk11 in all Dockerfile [#691](https://github.com/apache/hugegraph-toolchain/pull/691)
- Update copyright year in NOTICE file [#697](https://github.com/apache/hugegraph-toolchain/pull/697)

### hugegraph-computer

#### Feature Changes

- Migration Vermeer to hugegraph-computer [#316](https://github.com/apache/hugegraph-computer/pull/316)
- Make startChan's size configurable [#328](https://github.com/apache/hugegraph-computer/pull/328)
- Assign WorkerGroup via worker configuration [#332](https://github.com/apache/hugegraph-computer/pull/332)
- Support task priority based scheduling [#336](https://github.com/apache/hugegraph-computer/pull/336)
- Avoid 800k [#340](https://github.com/apache/hugegraph-computer/pull/340)

#### Bug Fixes

- Fix docker file build [#341](https://github.com/apache/hugegraph-computer/pull/341)

#### Other Changes

- Update release version to 1.5.0 [#318](https://github.com/apache/hugegraph-computer/pull/318)
- Update go depends module & fix headers [#321](https://github.com/apache/hugegraph-computer/pull/321)
- Update go version to 1.23 [#322](https://github.com/apache/hugegraph-computer/pull/322)
- Add collaborator in .asf.yaml [#323](https://github.com/apache/hugegraph-computer/pull/323)
- Update the Go version in docker image [#333](https://github.com/apache/hugegraph-computer/pull/333)
- Add DeepWiki badge to README [#337](https://github.com/apache/hugegraph-computer/pull/337)
- Bump project version to 1.7.0 (RELEASE) [#338](https://github.com/apache/hugegraph-computer/pull/338)
- Update copyright year in NOTICE file [#342](https://github.com/apache/hugegraph-computer/pull/342)

### hugegraph-ai

#### API Changes

- Support choose template in api [#135](https://github.com/apache/hugegraph-ai/pull/135)
- Add post method for paths-api [#162](https://github.com/apache/hugegraph-ai/pull/162)
- Support switch graph in api & add some query configs [#184](https://github.com/apache/hugegraph-ai/pull/184)
- Text2gremlin api [#258](https://github.com/apache/hugegraph-ai/pull/258)
- Support switching prompt EN/CN [#269](https://github.com/apache/hugegraph-ai/pull/269)
- **BREAKING CHANGE**: Update keyword extraction method [#282](https://github.com/apache/hugegraph-ai/pull/282)

#### Feature Changes

- Added the process of text2gql in graphrag V1.0 [#105](https://github.com/apache/hugegraph-ai/pull/105)
- Use pydantic-settings for config management [#122](https://github.com/apache/hugegraph-ai/pull/122)
- Timely execute vid embedding & enhance some HTTP logic [#141](https://github.com/apache/hugegraph-ai/pull/141)
- Use retry from tenacity [#143](https://github.com/apache/hugegraph-ai/pull/143)
- Modify the summary info and enhance the request logic [#147](https://github.com/apache/hugegraph-ai/pull/147)
- Automatic backup graph data timely [#151](https://github.com/apache/hugegraph-ai/pull/151)
- Add a button to backup data & count together [#153](https://github.com/apache/hugegraph-ai/pull/153)
- Extract topk_per_keyword & topk_return_results to .env [#154](https://github.com/apache/hugegraph-ai/pull/154)
- Modify clear buttons [#156](https://github.com/apache/hugegraph-ai/pull/156)
- Support intent recognition V1 [#159](https://github.com/apache/hugegraph-ai/pull/159)
- Change vid embedding x:yy to yy & use multi-thread [#158](https://github.com/apache/hugegraph-ai/pull/158)
- Support mathjax in rag query block V1 [#157](https://github.com/apache/hugegraph-ai/pull/157)
- Use poetry to manage the dependencies [#149](https://github.com/apache/hugegraph-ai/pull/149)
- Return schema.groovy first when backup graph data [#161](https://github.com/apache/hugegraph-ai/pull/161)
- Merge all logs into one file [#171](https://github.com/apache/hugegraph-ai/pull/171)
- Use uv for the CI action [#175](https://github.com/apache/hugegraph-ai/pull/175)
- Use EN prompt for keywords extraction [#174](https://github.com/apache/hugegraph-ai/pull/174)
- Support litellm LLM provider [#178](https://github.com/apache/hugegraph-ai/pull/178)
- Improve graph extraction default prompt [#187](https://github.com/apache/hugegraph-ai/pull/187)
- Replace vid by full vertexes info [#189](https://github.com/apache/hugegraph-ai/pull/189)
- Support asynchronous streaming generation in rag block by using async_generator and asyncio.wait [#190](https://github.com/apache/hugegraph-ai/pull/190)
- Generalize the regex extraction func [#194](https://github.com/apache/hugegraph-ai/pull/194)
- Create quick_start.md [#196](https://github.com/apache/hugegraph-ai/pull/196)
- Support Docker & K8s deployment way [#195](https://github.com/apache/hugegraph-ai/pull/195)
- Multi-stage building in Dockerfile [#199](https://github.com/apache/hugegraph-ai/pull/199)
- Support graph checking before updating vid embedding [#205](https://github.com/apache/hugegraph-ai/pull/205)
- Disable text2gql by default [#216](https://github.com/apache/hugegraph-ai/pull/216)
- Use 4.1-mini and 0.01 temperature by default [#214](https://github.com/apache/hugegraph-ai/pull/214)
- Enhance the multi configs for LLM [#212](https://github.com/apache/hugegraph-ai/pull/212)
- Textbox to Code [#217](https://github.com/apache/hugegraph-ai/pull/223)
- Replace the IP + Port with URL [#209](https://github.com/apache/hugegraph-ai/pull/209)
- Update gradio's version [#235](https://github.com/apache/hugegraph-ai/pull/235)
- Use asyncio to get embeddings [#215](https://github.com/apache/hugegraph-ai/pull/215)
- Change QPS -> RPM for timer decorator [#241](https://github.com/apache/hugegraph-ai/pull/241)
- Support batch embedding [#238](https://github.com/apache/hugegraph-ai/pull/238)
- Using nuitka to provide a binary/perf way for the service [#242](https://github.com/apache/hugegraph-ai/pull/242)
- Use uv instead poetry [#226](https://github.com/apache/hugegraph-ai/pull/226)
- Basic compatible in text2gremlin generation [#261](https://github.com/apache/hugegraph-ai/pull/261)
- Enhance config path handling and add project root validation [#262](https://github.com/apache/hugegraph-ai/pull/262)
- Add vermeer python client for graph computing [#263](https://github.com/apache/hugegraph-ai/pull/263)
- Use uv in client & ml modules & adapter the CI [#257](https://github.com/apache/hugegraph-ai/pull/257)
- Use uv to manage pkgs & update README [#272](https://github.com/apache/hugegraph-ai/pull/272)
- Limit the deps version to handle critical init problems [#279](https://github.com/apache/hugegraph-ai/pull/279)
- Support semi-automated prompt generation [#281](https://github.com/apache/hugegraph-ai/pull/281)
- Support semi-automated generated graph schema [#274](https://github.com/apache/hugegraph-ai/pull/274)
- Unify all modules with uv [#287](https://github.com/apache/hugegraph-ai/pull/287)
- Add GitHub Actions for auto upstream sync and update SEALData subsample logic [#289](https://github.com/apache/hugegraph-ai/pull/289)
- Add a basic LLM/AI coding instruction file [#290](https://github.com/apache/hugegraph-ai/pull/290)
- Add rules for AI coding guideline - V1.0 [#293](https://github.com/apache/hugegraph-ai/pull/293)
- Replace QianFan by OpenAI-compatible format [#285](https://github.com/apache/hugegraph-ai/pull/285)
- Optimize vector index with asyncio embedding [#264](https://github.com/apache/hugegraph-ai/pull/264)
- Refactor embedding parallelization to preserve order [#295](https://github.com/apache/hugegraph-ai/pull/295)
- Support storing vector data for a graph instance by model type/name [#265](https://github.com/apache/hugegraph-ai/pull/265)
- Add AGENTS.md as new document standard [#299](https://github.com/apache/hugegraph-ai/pull/299)
- Add Fixed Workflow Execution Engine: Flow, Node, and Scheduler Architecture [#302](https://github.com/apache/hugegraph-ai/pull/302)
- Support vector db layer V1.0 [#304](https://github.com/apache/hugegraph-ai/pull/304)

#### Bug Fixes

- Limit the length of log & improve the format [#121](https://github.com/apache/hugegraph-ai/pull/121)
- Pylint in ml [#125](https://github.com/apache/hugegraph-ai/pull/125)
- Critical bug with pylint usage [#131](https://github.com/apache/hugegraph-ai/pull/131)
- Multi vid k-neighbor query only return the data of first vid [#132](https://github.com/apache/hugegraph-ai/pull/132)
- Replace getenv usage to settings [#133](https://github.com/apache/hugegraph-ai/pull/133)
- Correct header writing errors [#140](https://github.com/apache/hugegraph-ai/pull/140)
- Update prompt to fit prefix cache [#137](https://github.com/apache/hugegraph-ai/pull/137)
- Extract_graph_data use wrong method [#145](https://github.com/apache/hugegraph-ai/pull/145)
- Use empty str for llm config [#155](https://github.com/apache/hugegraph-ai/pull/155)
- Update gremlin generate prompt to apply fuzzy match [#163](https://github.com/apache/hugegraph-ai/pull/163)
- Enable fastapi auto reload function [#164](https://github.com/apache/hugegraph-ai/pull/164)
- Fix tiny bugs & optimize reranker layout [#202](https://github.com/apache/hugegraph-ai/pull/202)
- Enable tasks concurrency configs in Gradio [#188](https://github.com/apache/hugegraph-ai/pull/188)
- Align regex extraction of json to json format of prompt [#211](https://github.com/apache/hugegraph-ai/pull/211)
- Fix documentation sample code error [#219](https://github.com/apache/hugegraph-ai/pull/219)
- Failed to remove vectors when updating vid embedding [#243](https://github.com/apache/hugegraph-ai/pull/243)
- Skip empty chunk in LLM steaming mode [#245](https://github.com/apache/hugegraph-ai/pull/245)
- Ollama batch embedding bug [#250](https://github.com/apache/hugegraph-ai/pull/250)
- Fix Dockerfile to add pyproject.toml anchor file [#266](https://github.com/apache/hugegraph-ai/pull/266)
- Add missing 'properties' in gremlin prompt formatting [#298](https://github.com/apache/hugegraph-ai/pull/298)
- Fixed cgraph version [#305](https://github.com/apache/hugegraph-ai/pull/305)
- Ollama embedding API usage and config param [#306](https://github.com/apache/hugegraph-ai/pull/306)

#### Option Changes

- Remove enable_gql logic in api & rag block [#148](https://github.com/apache/hugegraph-ai/pull/148)

#### Other Changes

- Update README for python-client/SDK [#150](https://github.com/apache/hugegraph-ai/pull/150)
- Enable pip cache [#142](https://github.com/apache/hugegraph-ai/pull/142)
- Enable discussion & change merge way [#201](https://github.com/apache/hugegraph-ai/pull/201)
- Synchronization with official documentation [#273](https://github.com/apache/hugegraph-ai/pull/273)
- Fix grammar errors [#275](https://github.com/apache/hugegraph-ai/pull/275)
- Improve README clarity and deployment instructions [#276](https://github.com/apache/hugegraph-ai/pull/276)
- Add docker-compose deployment and improve container networking instructions [#280](https://github.com/apache/hugegraph-ai/pull/280)
- Update docker compose command [#283](https://github.com/apache/hugegraph-ai/pull/283)
- Reduce third-party library log output [#244](https://github.com/apache/hugegraph-ai/pull/284)
- Update README with improved setup instructions [#294](https://github.com/apache/hugegraph-ai/pull/294)
- Add collaborators in asf config [#182](https://github.com/apache/hugegraph-ai/pull/182)

### Release Details

Please check the release details/contributor in each repository:

- [Server Release Notes](https://github.com/apache/hugegraph/releases)
- [Toolchain Release Notes](https://github.com/apache/hugegraph-toolchain/releases)
- [Computer Release Notes](https://github.com/apache/hugegraph-computer/releases)
- [AI Release Notes](https://github.com/apache/hugegraph-ai/releases)
