# Helm integration refresh evidence

Checked on 2026-11-15 (Asia/Singapore). This record covers the bilingual Helm deployment and Kubernetes operations pages.
Screenshot provenance is recorded in [Hubble screenshots](fixtures/hubble-screenshots.json) and
[Vermeer/Helm screenshots](fixtures/vermeer-helm-screenshots.json); the Hubble and Vermeer guides have their own refresh records.

## Source baseline

- Chart and Store lifecycle contracts: [apache/hugegraph at 8828d8238ad578f0d8ac25010c3dd6d4b3ba0e07][server-source].
- Hubble native adapter, UI and operations: [apache/hugegraph-toolchain at 20807295eed25d8c135bb1d10ab456d4f4523ecb][hubble-source].
- Vermeer native engine: [apache/hugegraph-computer at cc990987d2932fe269948e197a82d73da6869494][vermeer-source].

The current Hubble adapter accepts 19 algorithm identifiers. Both translated algorithm catalogs were compared with the actual `Set.of(...)` in
`DirectVermeerService`; the upstream Helm prose's older nine-algorithm count is not the capability baseline.

[server-source]: https://github.com/apache/hugegraph/tree/8828d8238ad578f0d8ac25010c3dd6d4b3ba0e07/helm/hugegraph
[hubble-source]: https://github.com/apache/hugegraph-toolchain/tree/20807295eed25d8c135bb1d10ab456d4f4523ecb/hugegraph-hubble
[vermeer-source]: https://github.com/apache/hugegraph-computer/tree/cc990987d2932fe269948e197a82d73da6869494/vermeer

## Local render and browser checks

Helm 3.16.2 `helm lint --strict` passed. Fresh templates were rendered for:

1. `values-single.yaml` with standalone Vermeer.
2. `values-cluster.yaml` with cluster Vermeer and three Workers.
3. The single-node Vermeer case in strict mode.
4. `values-single.yaml` plus `values-rag.yaml`.
5. An offline upgrade with `--is-upgrade` and all three recorded bootstrap counts pinned to one.

YAML assertions verified the immutable bootstrap record, PD counts, Hubble's internal Master origin and token-file wiring,
standalone's separate Worker claim, the cluster Worker count, easy/strict HTTP Service types, and private internal Services.
They also checked the shared Hubble data-volume paths for H2 and `text2gql.shared.master_key_file`,
and RAG's single replica, Recreate strategy, 10 GiB claim, ClusterIP and disabled ServiceAccount token mount.
Six relevant existing chart test suites passed, totaling 50 tests: Text2GQL key storage, fresh/bootstrap records,
PD growth, PD shrink and practical access notes.

The strict Hugo build passed. At 1440 and 390 CSS pixels in both languages, Chromium verified the integrated Mermaid diagram,
five-step workflow, topology Tabs, table-reader Enter/Escape behavior and restored focus, no document-level horizontal overflow,
and the complete Markdown fallback. Both rendered file trees have 15 comments after adding `values-rag.yaml`;
the existing readability regression's expected count was updated accordingly.
The diagram uses a vertical flow after inspecting its narrow-screen rendering.

The Vermeer, Helm deployment and Kubernetes operations pairs now share 41, 19 and 18 native heading IDs respectively.
English heading IDs remain unchanged; changed Chinese IDs retain their old fragments in adjacent inert `span` aliases.
A fresh strict build and Chromium checks at 1440 and 390 CSS pixels confirmed matching Duo View heading sequences, enabled Sync Scroll,
mobile pane switching and no document overflow. Static comparison retained every pre-change DOM ID without duplicates;
no renderer, script or English prose changed for this alignment.

These local render and browser checks do not prove live Kubernetes scheduling, persistent-volume provisioning or computation.
The final combined checks must run against the fresh artifact after all screenshot files have been generated.

## Live minimal Helm deployment

A separate task-owned Kind cluster ran Kubernetes 1.37.0 with the matching kubectl and its standard local-path StorageClass.
The installation used the unmodified current chart, the single-node preset, standalone Vermeer and a local resource overlay.
Authentication and persistence remained enabled. `helm install --wait` and `helm test --logs` passed.
All five claims bound: PD, Store, Hubble, Vermeer Master and standalone Worker. Local-path capacities are declarations, not preallocated storage.

Runtime image references were recorded by immutable digest:

| Component | Image digest |
| --- | --- |
| PD | `hugegraph/pd@sha256:5929dcfe9a45009a55ab871bd0370b500d3517b59d9dac62727bb2661ce84a54` |
| Store | `hugegraph/store@sha256:947237c603cf692e571db21267d1694bf4904ceb82ee3dd103d3eae0aec20750` |
| Server | `hugegraph/server@sha256:f0a792265d86f4f9b14421c742ebdcec76861d4bee9e1b9091ad0153f2e71a34` |
| Hubble | `hugegraph/hubble@sha256:40f020c3a629ec81127cdad90054283259eb3730ee2804598367bb370b3950b5` |
| Vermeer | `hugegraph/vermeer@sha256:80ccc46d2f4553ce383941ff5d5247ae18c99de4f6fa01a9817defec00ac722a` |

Hubble and Vermeer image revision labels match the source baselines above. PD/Store/Server images have no revision label;
their digests and observed behavior are recorded without claiming a source identity that their labels do not establish.
Server reported Core 1.8.0, Gremlin 3.8.1 and API 0.73.0.0. Helm's Server hook passed graph binding and visible index-state checks on the one Server;
business assertions were explicitly skipped because `server.testGremlin` was unset. The Vermeer hook verified its service token and allocated Worker availability.

Through the authenticated Hubble backend, the built-in sample loaded into Vermeer with 8 vertices and 6 edges.
Five compute tasks completed successfully: PageRank, PPR, SCC, clustering coefficient and Jaccard.
Each returned eight ID/value rows over four two-row pages; the last full page correctly returned `has_more:false`.
This validates the signed Hubble task-ID and pagination path for those tasks, not all 19 algorithms or production-scale behavior.
The result-preview adjacency request remained unavailable on this native image; retained values were still readable.

## Independent health signals observed

The live deployment retained its real diagnostic state in screenshots:

- Kubernetes reported the Store Pod Ready using the chart's `/v1/health` probes.
- `/-/lifecycle` reported `STARTED`, while the separate operator-controlled `/-/state` flag remained `STARTING`.
  Hubble consequently reported its service-readiness observation as `NOT_READY` even while sample graph queries and Vermeer scans succeeded.
- PD cluster statistics were available, while per-member system metrics reported `pd_metrics_unmapped`:
  the configured client Service origin differed from the advertised member's Pod FQDN.

The [Store lifecycle documentation][store-lifecycle] explicitly separates process startup from PD registration, partition recovery,
Raft catch-up, data readiness and the operator-controlled state flag. Hubble's
[operations diagnostics][hubble-diagnostics] separately describe endpoint/member mapping and source collection.
No management state was changed to make the dashboard appear healthy. No Service metric sample was reassigned to a member.

[store-lifecycle]: https://github.com/apache/hugegraph/blob/8828d8238ad578f0d8ac25010c3dd6d4b3ba0e07/hugegraph-store/docs/deployment-guide.md#step-3-deploy-store-cluster
[hubble-diagnostics]: https://github.com/apache/hugegraph-toolchain/blob/20807295eed25d8c135bb1d10ab456d4f4523ecb/hugegraph-hubble/docs/operations-diagnostics-20261023.md

Task-local artifacts are under `/var/tmp/hubble-helm-live/` (`images.json`, `helm-test.log`, `live-api-verification.json`)
and `/var/tmp/helm-docs-verification.json`. This was a single-node acceptance run, not an HA, failure-recovery, RF-migration or long-duration test.
RAG was rendered and checked locally; no live model connection or RAG inference is claimed by this record.
