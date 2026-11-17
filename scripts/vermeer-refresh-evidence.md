# Vermeer guide verification scope

This covers the current English and Chinese Vermeer guides. Exact source and image identities and screenshot hashes are recorded in
[Vermeer/Helm fixtures](fixtures/vermeer-helm-screenshots.json) and [Hubble fixtures](fixtures/hubble-screenshots.json).
Review the [native APIs and algorithms](https://github.com/apache/hugegraph-computer/tree/master/vermeer),
[Hubble adapter](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-hubble) and
[chart](https://github.com/apache/hugegraph/tree/master/helm/hugegraph).

## Source contracts

- Native names and Hubble's 19-identifier catalog are checked separately; historical `kout_all` is not registered.
  Its old heading remains for deep-link compatibility, without an unsupported request example.
- The adapter cannot verify loaded edge-weight/filter properties, so its custom weight/filter expressions remain restricted.
- Native submission, positive IDs and EOF pagination are distinct from Hubble's signed routing IDs and look-ahead `has_more` metadata.
  The native baseline lacks the optional preview-edges route; valid retained values remain readable without adjacency enrichment.

## Native execution

- A local source build used the module's Go 1.23.7 toolchain, separate Master/Worker data directories and loopback HTTP/gRPC ports.
  Authentication was disabled for this CSV trial; it is separate from the authenticated Helm deployment.
- One Worker in the common `$` pool loaded the documented four-vertex directed CSV ring. PageRank completed with four values of `0.25`.
  Two-row native pages advanced cursors, and a further request returned EOF. The unsupported submission path returned HTTP 405.
- Full-sample Closeness and Betweenness returned four finite values of `0.5`; Triangle and Clustering completed with three steps and returned zero.
  Both rejected a two-step budget. Boolean Cycle Detection returned `1` for every vertex. These checks did not migrate an existing writeback schema.
- Cluster snapshots showed registered/ready Workers and available resource observations. An unassigned named-group Worker could remain ready
  while unavailable to the caller's space; registration, metrics availability and scoped allocation readiness are separate signals.
- The development build exercised APIs with UI files read from disk. The ordinary `make` target also compiled embedded UI assets and the binary;
  successful compilation does not establish live native-UI acceptance or release archive provenance.

## Limits and review entry points

- This native CSV check does not establish HStore scans, Server authentication, multiple-Worker execution, cancellation,
  topology changes or restart recovery. It does not validate all 19 algorithms or production-scale behavior.
- The separate Helm run verifies selected Hubble-to-Vermeer tasks; see [Helm evidence](helm-refresh-evidence.md).
  Neither record establishes HA or real RAG inference acceptance.
- Review native API handling in `apps/master/services/http_tasks.go` and `http_cluster.go`, output contracts in `algorithms/`,
  and Hubble routing/preview behavior in `DirectVermeerService`, `AsyncTaskService` and the OLAP result components.
- Run source, build, link and browser gates against a frozen artifact using the [contribution guide](../contribution.md).
