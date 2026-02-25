---
title: Maturity
description: Apache HugeGraph maturity assessment
weight: 50
---

# Maturity Assessment for Apache HugeGraph

The goals of this maturity model are to describe how Apache projects operate in a concise and high-level way, and to provide a basic framework that projects may choose to use to evaluate themselves.

More details can be found [here](https://community.apache.org/apache-way/apache-project-maturity-model.html).

## Status of this assessment

Preliminary assessment completed.

## Maturity model assessment

The following table is filled according to the [Apache Maturity Model](https://community.apache.org/apache-way/apache-project-maturity-model.html). Mentors and community members are welcome to comment and modify it.

### CODE

| **ID**   | **Description** | **Status** |
| -------- | --------------- | ---------- |
| **CD10** | The project produces Open Source software for distribution to the public, at no charge.                                                                                                                                                                         | **YES** The project source code is licensed under the `Apache License 2.0`. |
| **CD20** | Anyone can easily discover and access the project's code.                                                                                                                                                                                                     | **YES** The [official website](https://hugegraph.apache.org/) includes a link to the [GitHub repository](https://github.com/apache/hugegraph). |
| **CD30** | Anyone using standard, widely-available tools, can build the code in a reproducible way.                                                                                                                                                                       | **YES**  Apache HugeGraph provides a [Quick Start](https://hugegraph.apache.org/docs/quickstart/hugegraph/hugegraph-server/) document that explains how to compile the source code. |
| **CD40** | The full history of the project's code is available via a source code control system, in a way that allows anyone to recreate any released version. | **YES** The project uses Git, and anyone can view the full history of the project via commit logs and tags for each release. |
| **CD50** | The source code control system establishes the provenance of each line of code in a reliable way, based on strong authentication of the committer. When third parties contribute code, commit messages provide reliable information about the code provenance. | **YES** The project uses GitHub managed by Apache Infra, ensuring provenance of each line of code to a committer. Third-party contributions are accepted via pull requests in accordance with the [Contribution Guidelines](https://hugegraph.apache.org/docs/contribution-guidelines/).|

### LICENSE

| **ID**   | **Description** | **Status** |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **LC10** | The Apache License, version 2.0, covers the released code.                                                                                                                                                                                                                     | **YES** The [LICENSE](https://github.com/apache/hugegraph/blob/master/LICENSE) file is present in the source repository. All source files contain the APLv2 header, which is checked by the Apache Rat plugin during builds. |
| **LC20** | Libraries that are mandatory dependencies of the project's code do not create more restrictions than the Apache License does.                                                                                                                                          | **YES** All dependencies have been checked and none of them create more restrictions than the Apache License does. |
| **LC30** | The libraries mentioned in LC20 are available as Open Source software.                                                                                                                                                                                      | **YES** Dependencies are available in public Maven repositories. |
| **LC40** | Committers are bound by an Individual Contributor Agreement (the "Apache iCLA") that defines which code they may commit and how they need to identify code that is not their own. | **YES** All committers have a signed iCLA on file with the ASF. |
| **LC50** | The project clearly defines and documents the copyright ownership of everything that the project produces.                                                                                                                                                                              | **YES** This is documented via copyright notices in the source files and the NOTICE file. |

### Releases

| **ID**   | **Description** | **Status** |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **RE10** | Releases consist of source code, distributed using standard and open archive formats that are expected to stay readable in the long term.                                                                                                                                       | **YES** Source releases are distributed via [dist.apache.org](https://dist.apache.org/repos/dist/release/hugegraph/) and linked from the website's [download page](https://hugegraph.apache.org/docs/download/download/). |
| **RE20** | The project's PMC (Project Management Committee, see CS10) approves each software release in order to make the release an act of the Foundation.                                                                                                                                                                          | **YES** All releases are voted on by the PMC on the dev@hugegraph.apache.org mailing list. |
| **RE30** | Releases are signed and/or distributed along with digests that anyone can reliably use to validate the downloaded archives.                                                                                                                                                       | **YES** All releases are signed by the release manager and distributed with checksums. The [KEYS](https://downloads.apache.org/hugegraph/KEYS) file is available for verification. |
| **RE40** | The project can distribute convenience binaries alongside source code, but they are not Apache Releases, they are provided with no guarantee. | **YES** The project provides convenience binaries, but only the source code archive is an official Apache release. |
| **RE50** | The project documents a repeatable release process so that someone new to the project can independently generate the complete set of artifacts required for a release. | **YES** The project documents its release process in the [How to Release](https://github.com/apache/hugegraph/wiki/ASF-Release-Guidance-V2.0) guide. |

### Quality

| **ID**   | **Description** | **Status** |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **QU10** | The project is open and honest about the quality of its code. Various levels of quality and maturity for various modules are natural and acceptable as long as they are clearly communicated. | **YES** Users are encouraged to [report issues](https://github.com/apache/hugegraph/issues) on GitHub, and all discussions are public. |
| **QU20** | The project puts a very high priority on producing secure software.                                                                                                                                                                                                            | **YES** All reported security issues are treated with high priority. |
| **QU30** | The project provides a well-documented, secure and private channel to report security issues, along with a documented way of responding to them. | **YES** The project website has a dedicated [security page](https://hugegraph.apache.org/docs/guides/security/) with instructions for reporting vulnerabilities. |
| **QU40** | The project puts a high priority on backwards compatibility and aims to document any incompatible changes and provide tools and documentation to help users transition to new features. | **YES** The project values backward compatibility and documents any breaking changes in release notes. |
| **QU50** | The project strives to respond to documented bug reports in a timely manner. | **YES** The community is active in addressing issues reported on GitHub and questions on the mailing list. |

### Community

| **ID**   | **Description** | **Status** |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **CO10** | The project has a well-known homepage that points to all the information required to operate according to this maturity model. | **YES** The [website](https://hugegraph.apache.org/) serves as the central point for project information. |
| **CO20** | The community welcomes contributions from anyone who acts in good faith and in a respectful manner, and who adds value to the project. | **YES** Apache HugeGraph has a [Contribution Guidelines](https://hugegraph.apache.org/docs/contribution-guidelines/) page and welcomes all valuable contributions. |
| **CO30** | Contributions include source code, documentation, constructive bug reports, constructive discussions, marketing and generally anything that adds value to the project. | **YES** The project values both code and non-code contributions. |
| **CO40** | The community strives to be meritocratic and gives more rights and responsibilities to contributors who, over time, add value to the project. | **YES** The community follows the Apache Way and has a history of promoting active contributors to committer and PMC roles. |
| **CO50** | The project documents how contributors can earn more rights such as commit access or decision power, and applies these principles consistently. | **YES** The process for becoming a committer is outlined in the [contribution guidelines](https://hugegraph.apache.org/docs/contribution-guidelines/committer-guidelines/). |
| **CO60** | The community operates based on consensus of its members (see CS10) who have decision power. Dictators, benevolent or not, are not welcome in Apache projects. | **YES** All major decisions are made through public discussion and consensus on the mailing list. |
| **CO70** | The project strives to answer user questions in a timely manner. | **YES** The community uses the dev@hugegraph.apache.org mailing list, [GitHub Issues](https://github.com/apache/hugegraph/issues), and [GitHub Discussions](https://github.com/apache/hugegraph/discussions) to provide support to users. |

### Consensus

| **ID**   | **Description** | **Status** |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **CS10** | The project maintains a public list of its contributors who have decision power. The project's PMC (Project Management Committee) consists of those contributors. | **YES** Project governance information is publicly available via ASF committee and roster pages, such as [committee info](https://projects.apache.org/committee.html?hugegraph). |
| **CS20** | Decisions require a consensus among PMC members and are documented on the project's main communications channel. The PMC takes community opinions into account, but the PMC has the final word. | **YES** All decisions are made by votes on the dev@hugegraph.apache.org mailing list, requiring at least three +1 votes from PMC members and no vetos. |
| **CS30** | The project uses documented voting rules to build consensus when discussion is not sufficient. | **YES** The project uses the standard ASF voting rules. |
| **CS40** | In Apache projects, vetoes are only valid for code commits. The person exercising the veto must justify it with a technical explanation, as per the Apache voting rules defined in CS30. | **YES** The HugeGraph community follows this principle. |
| **CS50** | All "important" discussions happen asynchronously in written form on the project's main communications channel. Offline, face-to-face or private discussions that affect the project are also documented on that channel. | **YES** All important discussions and decisions are documented on the public mailing list for transparency and accessibility. |

### Independence

| **ID**   | **Description** | **Status** |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **IN10** | The project is independent from any corporate or organizational influence. | **YES** The PMC members and committers of Apache HugeGraph are from 10+ different companies/college/institution, ensuring no single entity controls the project. |
| **IN20** | Contributors act as themselves, not as representatives of a corporation or organization. | **YES** Contributions are made by individuals on behalf of the project and community, not their employers. |
