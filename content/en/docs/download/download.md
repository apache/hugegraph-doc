---
title: "Download Apache HugeGraph"
linkTitle: "Download"
weight: 2
search_keywords: [HugeGraph download, release artifacts, SHA512]
search_boost: 3
---


> Instructions:
> 
> - Use published packages. Java 11 is recommended for Server 1.7.0; see the [Server startup guide](/docs/quickstart/hugegraph/hugegraph-server/#21-install-java-11-jdk-11) for other supported JDKs. Check each component's versioned quick start for Toolchain, AI, Vermeer, and other runtime requirements.
> - To verify downloads, use the corresponding hash (SHA512), signature, and [Project Signature Verification KEYS](https://downloads.apache.org/hugegraph/KEYS).
> - Instructions for checking hash (SHA512) and signatures are on the [Validate Release](/docs/contribution-guidelines/validate-release) page, and you can also refer to [ASF official instructions](https://www.apache.org/dyn/closer.cgi#verify).
> - Note: The version numbers of all components of HugeGraph have been kept consistent, and the version numbers of Maven repositories such as `client/loader/hubble/common` are the same. You can refer to these for dependency references [maven example](https://github.com/apache/hugegraph-toolchain#maven-dependencies).
> - Compatibility note: after HugeGraph graduated in January 2026, download paths moved from `/incubator/hugegraph` to `/hugegraph`. Historical release file names may still include `-incubating-`.
> - To build from source, refer to [build from source](/docs/quickstart/hugegraph/hugegraph-server).

The `src` suffix identifies a source archive that must be compiled according to the component guide; its directory cannot be used like a binary distribution to run startup scripts. Master may include unreleased configuration or APIs. When using release packages below or versioned container images, check the applicability notes in the documentation.

### Latest Version

{{< asf-downloads latest >}}

---

### Archived Versions

> Note: `1.3.0` is the last major version compatible with Java8, please switch to or migrate to Java11 as soon as possible (lower versions of Java have potentially more SEC risks and performance impacts). Starting from version `1.5.0`, a Java11 runtime environment is required.

{{< asf-downloads archived >}}
