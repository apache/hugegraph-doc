---
title: "Security Report"
linkTitle: "Security"
weight: 7
---

## Reporting New Security Problems with Apache HugeGraph

> [!WARNING]
> **Production security requirements**
>
> HugeGraph disables user authentication by default. In production, enable authentication and authorization, set `white_ip.status=enable`, maintain the IP allowlist, and grant minimum permissions. Do not expose Gremlin, Cypher, or other query endpoints directly to the public network. See the [IP allowlist API](/docs/clients/restful-api/other/). Isolate the Server process, for example with [Docker or Kubernetes](/docs/quickstart/hugegraph/hugegraph-server/#31-use-docker-container-convenient-for-testdev).
>
> Standard Server configuration writes authentication-proxy audit records to `audit-*.log`. Retain these files and restrict read access. `auth.audit_log_rate` controls the maximum per-user log output rate rather than serving as a dedicated audit-log on/off switch.

> [!WARNING]
> **Vulnerability reporting scope**
>
> The community has received many reports about the flexibility of graph query languages. Until the security architecture is refactored, known risks from DSL queries executed with **Auth disabled or deliberately skipped, outside an authorized session**, will **not be treated individually as new vulnerabilities**.
>
> Exploitation through **anonymous or unauthorized access despite Auth being enabled**, or **bypassing an IP allowlist or escaping a container** to cause serious privilege violations or system compromise, remains a high-risk security vulnerability. Please report these cases to the community.

Following ASF procedures, the HugeGraph community actively works to resolve security issues.

Report security issues privately to the dedicated security list first. See the [ASF security procedures](https://www.apache.org/security/committers.html) for details.

The security list handles **undisclosed** vulnerabilities and their resolution. Report ordinary software bugs through GitHub Issues/Discussions or the developer mailing list. Messages unrelated to security sent to the security list will be ignored.

Security mailing list: `security@hugegraph.apache.org`

The general vulnerability-handling process is:

- The reporter privately sends the HugeGraph security list the affected versions, description, reproduction steps, and impact.
- The project security team works privately with the reporter on a fix. A `CVE` identifier can be requested after initial confirmation.
- The project releases an updated version of the affected software containing the fix.
- At an appropriate time, the project discloses the general issue and how to apply the fix, following ASF rules and omitting sensitive reproduction details.
- CVE publication and related steps follow the ASF security procedures.

## Known Security Vulnerabilities (CVEs)

### [HugeGraph](https://github.com/apache/hugegraph) main repository (Server/PD/Store)

- [CVE-2024-27348](https://www.cve.org/CVERecord?id=CVE-2024-27348): HugeGraph-Server - Command execution in gremlin
- [CVE-2024-27349](https://www.cve.org/CVERecord?id=CVE-2024-27349): HugeGraph-Server - Bypass whitelist in Auth mode
- [CVE-2024-43441](https://www.cve.org/CVERecord?id=CVE-2024-43441): HugeGraph-Server - Fixed JWT Token (Secret)
- [CVE-2025-26866](https://www.cve.org/CVERecord?id=CVE-2025-26866): HugeGraph-Server - RAFT and deserialization vulnerability

### [HugeGraph-Toolchain](https://github.com/apache/hugegraph-toolchain) repository (Hubble/Loader/Client/Tools/..)

- [CVE-2024-27347](https://www.cve.org/CVERecord?id=CVE-2024-27347): HugeGraph-Hubble - SSRF in Hubble connection page
