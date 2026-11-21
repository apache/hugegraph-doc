# Helm integration verification scope

This covers the bilingual deployment and Kubernetes operations guides. Exact source identities, runtime images and screenshot hashes live in
[Hubble fixtures](fixtures/hubble-screenshots.json) and [Vermeer/Helm fixtures](fixtures/vermeer-helm-screenshots.json).
Review contracts in the [chart](https://github.com/apache/hugegraph/tree/master/helm/hugegraph),
[Hubble adapter](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-hubble) and
[native engine](https://github.com/apache/hugegraph-computer/tree/master/vermeer).

## Coverage

- Local chart checks cover single-node/cluster Vermeer, strict access mode, RAG configuration and offline upgrade bootstrap records.
  Assertions inspect immutable bootstrap counts, private Services, token files, Worker claims and Hubble's persistent H2/Text2GQL key paths.
- The real deployment used a separate task-owned Kind cluster, the current chart, single-node preset and standalone Vermeer with a resource overlay.
  Authentication and persistence stayed enabled; install readiness and Helm hooks passed, and all component claims bound.
  Local-path claim capacities are declarations, not preallocated storage.
- The Server hook checked graph binding and visible index states; business assertions were skipped because `server.testGremlin` was unset.
  The Vermeer hook checked its service token and allocated Worker availability.
- Authenticated Hubble loaded the 8-vertex/6-edge sample into Vermeer. PageRank, PPR, SCC, clustering coefficient and Jaccard completed,
  with retained ID/value rows, signed task routing and final-page `has_more:false` verified.
  This covers those tasks, not every identifier in the adapter's 19-algorithm catalog.
- Hubble/Vermeer image revision labels match the fixture source identities. PD/Store/Server labels do not establish a source revision;
  their recorded digests identify the observed images without asserting a missing source label.

## Observed boundaries

- Store was Kubernetes Ready and lifecycle STARTED while its separate operator-controlled state remained STARTING.
  Hubble showed NOT_READY even though sample queries and Vermeer scans succeeded. No management flag was changed for the screenshots.
- PD statistics were readable, but per-member metrics showed `pd_metrics_unmapped` because the client Service origin differed from advertised Pod FQDNs.
  No Service metric sample was reassigned to a member.
- The native image lacks the optional preview-edges route; retained results stayed readable with adjacency unavailable.
- This was a minimal single-node run, not HA, failure-recovery, replica-factor migration or long-duration acceptance.
  RAG was checked by rendering configuration; no live model connection or RAG inference was exercised.

## Review entry points

- Lifecycle and diagnostics: [Store deployment](https://github.com/apache/hugegraph/blob/master/hugegraph-store/docs/deployment-guide.md)
  and [Hubble diagnostics](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-hubble/docs/operations-diagnostics-20261023.md).
- Native Duo View IDs preserve old Chinese fragments; review Mermaid, Steps, topology Tabs, technical tables and Markdown fallbacks on desktop/mobile.
- Runtime logs and API readbacks are verified against live clusters. The PageRank result summary, runtime image identities and screenshot hashes are recorded in [fixtures](fixtures/vermeer-helm-screenshots.json). Other algorithm, paging and Store/PD diagnostic assertions are not recorded in that file.
- Run source, build, link and browser gates against a frozen artifact using the [contribution guide](../contribution.md).
