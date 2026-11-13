---
title: 成熟度
description: Apache HugeGraph 成熟度评估
weight: 50
---

# Apache HugeGraph 成熟度评估

本成熟度模型的目标是以简洁、高层次的方式描述 Apache 项目如何运作，并提供一个基础框架，供项目自行评估时使用。

更多信息请参阅[此处](https://community.apache.org/apache-way/apache-project-maturity-model.html)。

## 本评估的状态

初步评估已完成。

## 成熟度模型评估

下表依据 [Apache 成熟度模型](https://community.apache.org/apache-way/apache-project-maturity-model.html)填写。欢迎导师和社区成员提出意见并进行修改。

### 代码（CODE）

| **ID** | **描述** | **状态** |
| -------- | --------------- | ---------- |
| **CD10** | 项目以免费方式向公众发布开源软件。 | **是** 项目源代码采用 `Apache License 2.0` 许可。 |
| **CD20** | 任何人都可以方便地发现并访问项目代码。 | **是** [官方网站](https://hugegraph.apache.org/)包含指向 [GitHub 仓库](https://github.com/apache/hugegraph)的链接。 |
| **CD30** | 任何人都可以使用标准且广泛可用的工具以可复现的方式构建代码。 | **是** Apache HugeGraph 提供了[快速上手](https://hugegraph.apache.org/docs/quickstart/hugegraph/hugegraph-server/)文档，说明如何编译源代码。 |
| **CD40** | 项目代码的完整历史可通过版本控制系统获取，任何人都能据此重建任意已发布的版本。 | **是** 项目使用 Git，任何人都可以通过每次发布的提交日志和标签查看项目的完整历史。 |
| **CD50** | 版本控制系统基于对提交者的强身份认证，以可靠的方式确定每一行代码的来源。当第三方贡献代码时，提交信息提供可靠的代码来源信息。 | **是** 项目使用由 Apache Infra 管理的 GitHub，确保每一行代码都能溯源到提交者。第三方贡献按照[贡献指南](https://hugegraph.apache.org/docs/contribution-guidelines/)通过拉取请求接收。 |

### 许可证（LICENSE）

| **ID** | **描述** | **状态** |
| -------- | --------------- | ---------- |
| **LC10** | Apache License 2.0 覆盖已发布的代码。 | **是** 源代码仓库中存在 [LICENSE](https://github.com/apache/hugegraph/blob/master/LICENSE) 文件。所有源文件都包含 APLv2 文件头，构建时由 Apache Rat 插件检查。 |
| **LC20** | 项目代码的必需依赖库不会带来比 Apache License 更多的限制。 | **是** 所有依赖均已检查，没有任何依赖带来比 Apache License 更多的限制。 |
| **LC30** | LC20 中提到的库以开源软件的形式提供。 | **是** 依赖均可在公共 Maven 仓库中获取。 |
| **LC40** | 提交者受个人贡献者协议（"Apache iCLA"）约束，该协议规定了他们可以提交哪些代码，以及如何标明非本人编写的代码。 | **是** 所有提交者都已在 ASF 备案签署的 iCLA。 |
| **LC50** | 项目清晰地定义并记录了其产出物的版权归属。 | **是** 通过源文件中的版权声明和 NOTICE 文件进行记录。 |

### 发布（Releases）

| **ID** | **描述** | **状态** |
| -------- | --------------- | ---------- |
| **RE10** | 发布内容由源代码组成，使用标准且开放的归档格式分发，以保证长期可读。 | **是** 源码发布通过 [dist.apache.org](https://dist.apache.org/repos/dist/release/hugegraph/) 分发，并在官网的[下载页面](https://hugegraph.apache.org/docs/download/download/)提供链接。 |
| **RE20** | 项目 PMC（项目管理委员会，见 CS10）批准每次软件发布，使发布成为基金会的行为。 | **是** 所有发布均由 PMC 在 dev@hugegraph.apache.org 邮件列表上投票通过。 |
| **RE30** | 发布内容附带签名和/或摘要，任何人都能可靠地用它验证下载的归档文件。 | **是** 所有发布均由发布经理签名并附带校验和。[KEYS](https://downloads.apache.org/hugegraph/KEYS) 文件可用于验证。 |
| **RE40** | 项目可以在源代码之外分发便利二进制包，但它们不是 Apache 发布版本，不提供任何保证。 | **是** 项目提供便利二进制包，但只有源码归档是官方 Apache 发布版本。 |
| **RE50** | 项目记录了可重复的发布流程，使新加入项目的人能够独立生成发布所需的完整产物集合。 | **是** 项目在[如何发布](https://github.com/apache/hugegraph/wiki/ASF-Release-Guidance-V2.0)指南中记录了发布流程。 |

### 质量（Quality）

| **ID** | **描述** | **状态** |
| -------- | --------------- | ---------- |
| **QU10** | 项目对其代码质量保持开放和诚实。各模块存在不同的质量和成熟度是自然且可接受的，只要清楚地告知用户。 | **是** 鼓励用户在 GitHub 上[报告问题](https://github.com/apache/hugegraph/issues)，所有讨论都是公开的。 |
| **QU20** | 项目高度重视产出安全的软件。 | **是** 所有报告的安全问题都会得到高优先级处理。 |
| **QU30** | 项目提供文档完备、安全且私密的渠道来报告安全问题，并记录了响应这些问题的方式。 | **是** 项目网站设有专门的[安全页面](https://hugegraph.apache.org/docs/guides/security/)，说明如何报告漏洞。 |
| **QU40** | 项目高度重视向后兼容性，力求记录所有不兼容的变更，并提供工具和文档帮助用户迁移到新功能。 | **是** 项目重视向后兼容性，并在发布说明中记录所有破坏性变更。 |
| **QU50** | 项目力求及时响应已记录的缺陷报告。 | **是** 社区积极处理 GitHub 上报告的问题和邮件列表中的提问。 |

### 社区（Community）

| **ID** | **描述** | **状态** |
| -------- | --------------- | ---------- |
| **CO10** | 项目拥有广为人知的主页，指向按照本成熟度模型运作所需的全部信息。 | **是** [网站](https://hugegraph.apache.org/)是项目信息的中心入口。 |
| **CO20** | 社区欢迎任何以善意和尊重的方式行事、并为项目增加价值的贡献者。 | **是** Apache HugeGraph 设有[贡献指南](https://hugegraph.apache.org/docs/contribution-guidelines/)页面，欢迎所有有价值的贡献。 |
| **CO30** | 贡献包括源代码、文档、建设性的缺陷报告、建设性的讨论、市场推广以及任何为项目增加价值的内容。 | **是** 项目同样重视代码和非代码贡献。 |
| **CO40** | 社区力求任人唯贤，随着时间推移为项目增加价值的贡献者将获得更多权利和责任。 | **是** 社区遵循 Apache Way，并有过将活跃贡献者提升为提交者和 PMC 成员的历史。 |
| **CO50** | 项目记录了贡献者如何获得更多权利（如提交权限或决策权），并始终如一地应用这些原则。 | **是** 成为提交者的流程在[贡献指南](https://hugegraph.apache.org/docs/contribution-guidelines/committer-guidelines/)中说明。 |
| **CO60** | 社区依据拥有决策权的成员（见 CS10）的共识运作。Apache 项目不欢迎独裁者，无论其是否善意。 | **是** 所有重大决策都通过邮件列表上的公开讨论和共识做出。 |
| **CO70** | 项目力求及时回答用户的问题。 | **是** 社区通过 dev@hugegraph.apache.org 邮件列表、[GitHub Issues](https://github.com/apache/hugegraph/issues) 和 [GitHub Discussions](https://github.com/apache/hugegraph/discussions) 为用户提供支持。 |

### 共识（Consensus）

| **ID** | **描述** | **状态** |
| -------- | --------------- | ---------- |
| **CS10** | 项目维护一份拥有决策权的贡献者公开名单。项目 PMC（项目管理委员会）由这些贡献者组成。 | **是** 项目治理信息可通过 ASF 委员会和名册页面公开获取，例如[委员会信息](https://projects.apache.org/committee.html?hugegraph)。 |
| **CS20** | 决策需要 PMC 成员达成共识，并记录在项目的主要沟通渠道上。PMC 会考虑社区意见，但 PMC 拥有最终决定权。 | **是** 所有决策都通过 dev@hugegraph.apache.org 邮件列表投票做出，要求至少三名 PMC 成员投 +1 票且无人否决。 |
| **CS30** | 当讨论不足以形成共识时，项目使用记录在案的投票规则来达成共识。 | **是** 项目使用标准的 ASF 投票规则。 |
| **CS40** | 在 Apache 项目中，否决仅对代码提交有效。行使否决权的人必须按照 CS30 中定义的 Apache 投票规则，以技术说明为其提供理由。 | **是** HugeGraph 社区遵循这一原则。 |
| **CS50** | 所有"重要"讨论都以书面形式异步发生在项目的主要沟通渠道上。影响项目的线下、面对面或私下讨论也会记录在该渠道上。 | **是** 所有重要讨论和决策都记录在公开邮件列表上，以保证透明和可访问。 |

### 独立性（Independence）

| **ID** | **描述** | **状态** |
| -------- | --------------- | ---------- |
| **IN10** | 项目独立于任何公司或组织的影响。 | **是** Apache HugeGraph 的 PMC 成员和提交者来自 10 多家不同公司/高校/机构，确保没有任何单一实体控制项目。 |
| **IN20** | 贡献者以个人身份行事，而非作为公司或组织的代表。 | **是** 贡献由个人以项目和社区的名义做出，而非其雇主。 |
