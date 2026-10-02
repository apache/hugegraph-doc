---
title: "Rust Modernization Roadmap"
linkTitle: "Rust Modernization"
weight: 7
description: "Status and contribution entry points for incremental Rust experiments across HugeGraph."
---

This page is the documentation entry point for proposed, incremental Rust modernization work across the HugeGraph ecosystem. It is a map of active proposals, not a commitment to rewrite existing components or evidence that a feature has shipped.

## Roadmap

| Area | Repository | Tracking issue | Current maturity | Owner |
| --- | --- | --- | --- | --- |
| Toolchain | `apache/hugegraph-toolchain` | [#748](https://github.com/apache/hugegraph-toolchain/issues/748) | Proposal tracking | To be assigned in the issue |
| Server, HStore, and PD | `apache/hugegraph` | [#3110](https://github.com/apache/hugegraph/issues/3110) | Proposal tracking | To be assigned in the issue |
| Graph computing | `apache/hugegraph-computer` | [#355](https://github.com/apache/hugegraph-computer/issues/355) | Proposal tracking | To be assigned in the issue |
| Documentation | `apache/hugegraph-doc` | [#462](https://github.com/apache/hugegraph-doc/issues/462) | Proposal tracking | To be assigned in the issue |

The linked issues are the source of truth for scope and status. A proposal must not be described as implemented until its code, tests, and documentation have been accepted.

## Shared maturity terms

- **Proposal tracking**: an issue exists, but no implementation has been accepted.
- **Experiment**: a proof of concept is available for evaluation. Its APIs, formats, and behavior may change without compatibility guarantees.
- **Preview**: the component has documented installation and validation paths and is suitable for opt-in evaluation, but is not yet recommended as a production default.
- **Production-ready**: maintainers have documented support scope, compatibility, upgrades, rollback, operational limits, and release availability.

Every Rust-related page should state its maturity, owning repository or issue, supported platforms, known limitations, and the release containing the documented behavior. Planned behavior should be labeled **proposed**.

## Delivery gates

Documentation evolves with implementation:

1. **RFC or proposal**: record goals, non-goals, ownership, compatibility risks, and acceptance criteria.
2. **Proof of concept**: document a reproducible build and test path plus known limitations.
3. **Preview**: add compatibility matrices, migration and rollback procedures, benchmarks, and troubleshooting.
4. **Production-ready**: document supported versions and platforms, upgrade guarantees, operational guidance, and release references.

## How to contribute

Choose one of the linked tracking issues and confirm that your intended work is not already claimed. Useful first contributions include:

- keeping the roadmap table synchronized with accepted work;
- proposing a Rust toolchain and workspace convention in the owning repository;
- adding compatibility, platform, or benchmark-report templates;
- documenting an accepted proof of concept with reproducible commands;
- maintaining equivalent English and Chinese content.

Do not publish benchmark claims without the source revision, hardware, dataset, configuration, commands, and repeated results needed to reproduce them.
