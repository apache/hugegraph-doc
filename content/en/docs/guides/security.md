---
title: "Security Report"
linkTitle: "Security"
weight: 7
---

## Reporting New Security Problems with Apache HugeGraph

> ⚠️ **SEC Reminder: Notice to Vulnerability Researchers Regarding Graph Query Languages**
>
> Given the inherent parsing and execution flexibility of graph query languages (like Gremlin/Cypher), HugeGraph strongly recommends relying on the **"[Auth (Authentication)](/docs/config/config-authentication/) + IP Whitelist + Audit Log"** mechanism in production environments to adhere to the Principle of Least Privilege. Furthermore, since Server nodes are essentially stateless, **it is explicitly advised to use [Containerized Environments (Docker/K8s)](/docs/quickstart/hugegraph/hugegraph-server/#31-use-docker-container-convenient-for-testdev) for isolated deployments in all production environments**.
>
> Recently, the community has received numerous security reports concerning the flexibility of graph queries. Until the overall HugeGraph security architecture is fully refactored, known situations involving the execution of DSL queries with **Auth disabled or skipped, or by using an anonymous or unauthorized identity** will **no longer be treated individually as new vulnerabilities**.
>
> However, if a vulnerability can still be exploited in an environment where the **Auth system is enabled** by accessing it with an **anonymous or unauthorized identity**, or if one successfully **bypasses the IP whitelist / escapes the container** causing severe unauthorized access or underlying system destruction, we still consider this a high-risk security vulnerability and highly encourage you to report it to us at any time!

Adhering to the specifications of ASF, the HugeGraph community maintains a highly proactive and open attitude towards addressing security issues in the **remediation** projects.

We strongly recommend that users first report such issues to our dedicated security email list, with detailed procedures specified in the [ASF SEC](https://www.apache.org/security/committers.html) code of conduct.

Please note that the security email group is reserved for reporting **undisclosed** security vulnerabilities and following up on the vulnerability resolution process. 
Regular software `Bug/Error` reports should be directed to `Github Issue/Discussion` or the `HugeGraph-Dev` email group. Emails sent to the security list that are unrelated to security issues will be ignored.

The independent security email (group) address is: `security@hugegraph.apache.org`

The general process for handling security vulnerabilities is as follows:

- The reporter privately reports the vulnerability to the Apache HugeGraph SEC email group (including as much information as possible, such as reproducible versions, relevant descriptions, reproduction methods, and the scope of impact)
- The HugeGraph project security team collaborates privately with the reporter to discuss the vulnerability resolution (after preliminary confirmation, a `CVE` number can be requested for registration)
- The project creates a new version of the software package affected by the vulnerability to provide a fix
- At an appropriate time, a general description of the vulnerability and how to apply the fix will be publicly disclosed (in compliance with ASF standards, the announcement should not disclose sensitive information such as reproduction details)
- Official CVE release and related procedures follow the ASF-SEC page

## Known Security Vulnerabilities (CVEs)

### HugeGraph main project (Server/PD/Store)

- [CVE-2024-27348](https://www.cve.org/CVERecord?id=CVE-2024-27348): HugeGraph-Server - Command execution in gremlin
- [CVE-2024-27349](https://www.cve.org/CVERecord?id=CVE-2024-27349): HugeGraph-Server - Bypass whitelist in Auth mode
- [CVE-2024-43441](https://www.cve.org/CVERecord?id=CVE-2024-43441): HugeGraph-Server - Fixed JWT Token (Secret)
- [CVE-2025-26866](https://www.cve.org/CVERecord?id=CVE-2025-26866): HugeGraph-Server - RAFT and deserialization vulnerability

### HugeGraph-Toolchain project (Hubble/Loader/Client/Tools/..)

- [CVE-2024-27347](https://www.cve.org/CVERecord?id=CVE-2024-27347): HugeGraph-Hubble - SSRF in Hubble connection page
