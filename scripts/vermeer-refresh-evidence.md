# Vermeer guide source and verification

This records the evidence for the current English and Chinese
`quickstart/computing/hugegraph-vermeer.md` guides. It does not establish an ASF
release or production deployment acceptance.

## Source snapshots

- Native engine: `apache/hugegraph-computer@cc990987d2932fe269948e197a82d73da6869494`,
  especially `vermeer/apps/master/services/http_tasks.go`,
  `vermeer/apps/master/services/http_cluster.go`, `vermeer/algorithms/` and
  `vermeer/apps/options/option.go`.
- Hubble: `apache/hugegraph-toolchain@20807295eed25d8c135bb1d10ab456d4f4523ecb`,
  especially `DirectVermeerService.java`, `VermeerController.java`,
  `modules/asyncTasks/taskIdentity.js`, `modules/algorithm/olapTaskRegistry.js`
  and `modules/algorithm/GraphResult/OlapPreview/index.js`.
- Chart: `apache/hugegraph@8828d8238ad578f0d8ac25010c3dd6d4b3ba0e07`,
  `helm/hugegraph/values.yaml` and the Vermeer/Hubble templates.

The current native registry and Hubble adapter contain 19 distinct algorithm
identifiers. Historical `kout_all` is not registered. The old section heading
remains as a compatibility reference, but its unsupported request was removed.
The adapter rejects custom edge-weight/property-filter expressions because it
cannot verify their availability in the loaded snapshot.

## Native execution

The following check ran on 2026-11-15 (Asia/Singapore) using the native source
snapshot, without API interception:

1. Build with the module's Go 1.23.7 toolchain and `-tags=dev`. Separate Master
   and Worker processes used their own data directories and loopback HTTP/gRPC
   ports; authentication was disabled for this local trial.
2. Start one Worker in the common `$` pool. Worker availability returned true;
   the cluster snapshot reported one registered and one ready Worker.
3. Load a headerless UTF-8 CSV graph with vertices `1`, `2`, `3`, `4` and edges
   `1,2`, `2,3`, `3,4`, `4,1`. The guide's string-encoded host-to-path maps,
   delimiter, in-memory backend and one-thread load were used.
4. Submit PageRank with one thread, 20 steps, damping `0.85` and difference
   threshold `0.00001`; select local output plus `output.need_query=1`.
5. Verify successful completion and four `ID`/`Value` rows, each equal to `0.25`.
   With native `limit=2`, cursors were `2` then `4`; another request at `4`
   returned EOF. This is distinct from Hubble's look-ahead `has_more` wrapper.
6. Verify `POST /api/v1/tasks` returns HTTP 405. Native submission uses
   `POST /api/v1/tasks/create`.
7. Verify `POST /api/v1/graphs/docs_ring/preview-edges` returns HTTP 404.
   This snapshot does not implement Hubble's optional adjacency-enrichment
   contract. Hubble therefore preserves valid computation values and reports
   adjacency unavailable; the guide does not claim a connected result graph.
8. Take a later health snapshot: Master and Worker resource observations were
   AVAILABLE. Initial warming-up metrics did not change Worker readiness.

An initial Go 1.27.3 build failed in Sonic's `GoMapIterator` support. The module's
Go 1.23.7 build succeeded without dependency changes; the guide uses that
recorded toolchain rather than claiming compatibility with every newer compiler.
The `dev` build reads UI assets from disk; this check covered native APIs, not
UI acceptance or production distribution packaging.

A separate allocation check observed a registered/ready Worker in an unassigned
named group while the caller's `/workers/availability` remained false. Moving
the local Worker to the common pool made it available. Registration and scoped
allocation readiness must remain separate.

Native execution here does not cover HStore scans, Server authentication,
multiple Workers, cancellation, topology changes or restart recovery. Hubble
screenshots and Helm integration evidence are maintained with their respective
refreshes; they must not be inferred from this CSV smoke check.

## Production binary build

`GOTOOLCHAIN=go1.23.7 make` subsequently passed against the same source snapshot.
The default target downloaded the native UI dependencies, generated embedded
assets and compiled the ordinary binary without the development tag. This
proves binary/UI-asset compilation, not live native-UI acceptance or release
archive provenance.

`make init` failed during its optional protoc download because extraction met
existing protobuf include files and prompted for overwrite without stdin. The
ordinary executable does not need that additional initialization target; the
guide uses the verified default `make` target. No dependency or source patch was
used to obtain a successful build.
