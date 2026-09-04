---
title: "报告安全问题"
linkTitle: "安全公告"
weight: 7
---

## 报告 Apache HugeGraph 的安全问题

> ⚠️ **SEC 提醒：致漏洞研究人员关于图查询语言的说明**
>
> 生产环境应启用[鉴权](/cn/docs/config/config-authentication/)、IP 白名单和审计日志，并使用 [Docker 或 Kubernetes](/cn/docs/quickstart/hugegraph/hugegraph-server/#31-使用-docker-容器-便于测试) 隔离 Server 进程。
>
> 近期社区已收到较多关于图查询语言灵活性的安全反馈。在 HugeGraph 安全体系整体重构完成前，对于在**不启用或跳过 Auth 系统/避开授权身份**的前提下执行 DSL 查询的情况，此类已知风险将**不再单独视为新漏洞**进行处理。
>
> 如果开启 Auth 后仍可匿名或越权访问，或者可以绕过 IP 白名单、逃逸容器并破坏底层系统，请按高危安全漏洞报告。

请先通过项目的私有安全邮件列表报告安全问题。流程见 [ASF Security](https://www.apache.org/security/committers.html)。

请注意，安全邮件组适用于报告**未公开**的安全漏洞并跟进漏洞处理的过程。常规的软件 `Bug/Error` 报告应该使用 `Github Issue/Discussion` 
或是 `HugeGraph-Dev` 邮箱组。发送到安全邮件组但与安全问题无关的邮件将被忽略。

独立的安全邮件 (组) 地址为： `security@hugegraph.apache.org` 

安全漏洞处理大体流程如下：

- 报告人私下向 Apache HugeGraph SEC 邮件组报告漏洞 (尽可能包括复现的版本/相关说明/复现方式/影响范围等)
- HugeGraph 项目安全团队与报告人私下合作/商讨漏洞解决方案 (初步确认后可申请 `CVE` 编号予以登记)
- 项目创建一个新版本的受漏洞影响的软件包，以提供修复程序
- 合适的时间可公开漏洞的大体问题 & 描述如何应用修复程序 (遵循 ASF 规范，公告中不应携带复现细节等敏感信息)
- 正式的 CVE 发布及相关流程同 ASF-SEC 页面

## 已发现的安全漏洞 (CVEs)

### [HugeGraph](https://github.com/apache/hugegraph) 主仓库 (Server/PD/Store)

- [CVE-2024-27348](https://www.cve.org/CVERecord?id=CVE-2024-27348): HugeGraph-Server - Command execution in gremlin
- [CVE-2024-27349](https://www.cve.org/CVERecord?id=CVE-2024-27349): HugeGraph-Server - Bypass whitelist in Auth mode
- [CVE-2024-43441](https://www.cve.org/CVERecord?id=CVE-2024-43441): HugeGraph-Server - Fixed JWT Token (Secret)
- [CVE-2025-26866](https://www.cve.org/CVERecord?id=CVE-2025-26866): HugeGraph-Server - RAFT and deserialization vulnerability

### [HugeGraph-Toolchain](https://github.com/apache/hugegraph-toolchain) 仓库 (Hubble/Loader/Client/Tools/..)

- [CVE-2024-27347](https://www.cve.org/CVERecord?id=CVE-2024-27347): HugeGraph-Hubble - SSRF in Hubble connection page
