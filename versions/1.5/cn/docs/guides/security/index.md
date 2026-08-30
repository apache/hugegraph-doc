# 报告安全问题

LLMS 索引： [llms.txt](/versions/1.5/cn/llms.txt)

---

## 报告 Apache HugeGraph 的安全问题

遵循 ASF 的规范，HugeGraph 社区对**解决修复**项目中的安全问题保持非常积极和开放的态度。

我们强烈建议用户首先向我们的独立安全邮件列表报告此类问题，相关详细的流程规范请参考 [ASF SEC](https://www.apache.org/security/committers.html) 守则。

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

### [HugeGraph-Toolchain](https://github.com/apache/hugegraph-toolchain) 仓库 (Hubble/Loader/Client/Tools/..)

- [CVE-2024-27347](https://www.cve.org/CVERecord?id=CVE-2024-27347): HugeGraph-Hubble - SSRF in Hubble connection page
