---
title: "Operate HugeGraph on Kubernetes"
linkTitle: "Kubernetes Operations"
weight: 5
search_keywords: [HugeGraph Helm operations, local PV, NetworkPolicy, PD, Store]
---

This guide accompanies [Helm deployment](./hugegraph-helm.md). Detailed lifecycle checks and recovery notes are maintained in the
[operations reference](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md); all parameters are commented in `values.yaml`.
Commands assume release/namespace `hugegraph`; substitute the actual workload names if overridden.

## 1 Storage and private images

The base installation needs seven persistent volumes. Dynamic storage requires a working provisioner; static local storage requires prepared directories
and matching PVs on the named nodes. Use the [complete examples](https://github.com/apache/hugegraph/tree/master/helm/hugegraph/examples)
for all seven local PVs, `WaitForFirstConsumer`, registry mirrors and GitOps Secrets.
An initially Pending PVC with `WaitForFirstConsumer` can be normal; persistent Pending needs PVC/Pod events and PV matching checks.
A bound claim with a missing directory or permission mismatch can fail mounting. Do not replace failed PVCs with temporary data directories.

```bash
kubectl -n hugegraph get pvc,pods
kubectl -n hugegraph describe pvc <claim-name>
kubectl -n hugegraph describe pod <pod-name>
kubectl get pv,storageclass
```

For `ImagePullBackOff`, inspect Pod events and registry access/credentials. The default image inventory contains four component images;
Store wait and Helm test reuse existing component images with `curl` already installed. Explicit helper-image overrides must also be mirrored.
Enabled SeaTunnel adds its configured `apache/seatunnel` image. Vermeer uses `hugegraph/vermeer:latest` by default,
reused by Master, Worker and token initialization; pin a compatible digest or tag for reproducibility.
Enabled RAG adds the image digest in `values-rag.yaml`. See the
[Vermeer deployment guide](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/vermeer.md).
Custom image overrides must also update `vermeer.image.digest`, or explicitly clear it to select by tag; digest takes priority.
The base local-PV example omits Vermeer claims: standalone adds two,
while cluster adds one Master claim plus one per Worker (four additional claims by default).

### Preserve the Text2GQL encryption key {#text2gql-master-key}

The chart now sets `text2gql.shared.master_key_file=/hubble-data/text2gql-master.key`, alongside H2 on the Hubble data volume.
Back up and restore both together. With Hubble persistence disabled, replacing the Pod loses the `emptyDir` data and key.

When upgrading from the old container-local `/hubble/data/text2gql-master.key`, preserve that key at the new path or
**re-enter and save the model API key once after upgrading**. H2 may still indicate a saved API key while generation returns HTTP 503;
saving other settings does not repair a missing encryption key. A new key is created on API-key save, not during startup or decryption.
Keep the key's owner UID stable and its mode `0600` across replacements. A Secret-supplied `HUBBLE_TEXT2GQL_MASTER_KEY` takes precedence over the file;
preserve the same Secret value to decrypt existing data. See the
[full key recovery contract](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#hubble-text2gql-credentials).

## 2 Ports and health

PD listens on REST 8620, gRPC 8686 and Raft 8610; Store on REST 8520, gRPC 8500 and Raft 8510; Server HTTP on 8080; Hubble HTTP on 8088.
Client Services hide individual Pod addresses. NodePort is a separate allocated port on reachable nodes, not the application listener port.
PD `/v1/ready` requires a Raft leader; `/v1/health` only confirms the listener. Store startup waits for a majority of ready PD peers.
Server waits up to `server.storageWaitTimeoutSeconds` (default 300) before its application startup; adjust it for slow storage bootstrap.
No local Helm rendering verifies live cluster reachability, volumes or JVM capacity.

Store probes use `/v1/health`. On supported versions, `/-/lifecycle: STARTED` only confirms Spring readiness and a running gRPC listener;
`/-/state` is a separate operator-controlled flag and can still be `STARTING`. Kubernetes Ready and Hubble's `NOT_READY` observation can therefore
coexist. Check PD registration, partition recovery and actual graph queries separately; see the
[Store lifecycle contract](https://github.com/apache/hugegraph/blob/master/hugegraph-store/docs/deployment-guide.md#step-3-deploy-store-cluster).

PD cluster statistics and per-member metric collection are independent too. A Service origin that cannot be mapped to one advertised member can
report `pd_metrics_unmapped` while cluster statistics remain available. Hubble does not infer a member from a Service alias or assign that sample to
the leader. Inspect the configured/advertised origins and collection details; the
[operations diagnostics](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-hubble/docs/operations-diagnostics-20261023.md)
explain the trusted-origin boundary.

### Preserve the metadata namespace {#metadata-namespace}

`metadataCluster: hg-test` sets the PD metadata namespace prefix (injected into Server `HG_SERVER_CLUSTER` and Store `PD_CLUSTER`).
It is not a Raft group name; changing it will not automatically migrate existing metadata. **Never** arbitrarily change this prefix on an initialized cluster to enable Vermeer. If Server REST queries succeed but Vermeer scanning Store fails with `Schema missing` or `no such vertex label`, check that the namespace prefix matches across all components.

If a legacy environment used a custom prefix, record it explicitly on the Server Deployment before upgrading:

```bash
kubectl -n hugegraph annotate deployment hugegraph-server \
  hugegraph.apache.org/metadata-cluster='<verified-existing-namespace>'
```

and ensure `metadataCluster` matches this value in your values file. For Store nodes using `store.updateStrategy.type=OnDelete`, follow the [rolling upgrade procedure](#6-rolling-store-images-safely) to recreate Pods one by one so the new settings take effect.

> [!DETAILS]- Optional Engines Operations: Probes, Credentials, and Topology Switching
> - **Ports & Health**: SeaTunnel HTTP/UI runs on `8080`; Vermeer Master HTTP/gRPC listens on `6688/6689`, and Worker on `6788/6789`.
>   Native HTTP/UI defaults to NodePort in easy mode and ClusterIP in strict mode; both require login.
>   Internal RPC, Worker HTTP and SeaTunnel `5801` stay private.
>   With `service.type: null`, the mode default applies; explicit `ClusterIP` stays private, while explicit `NodePort` exposes authenticated HTTP/UI.
>   Use the assigned HTTP NodePort from Service `hugegraph-seatunnel` or `hugegraph-vermeer-master` with a reachable node IP.
>   See [native access commands](/docs/quickstart/hugegraph/hugegraph-helm/#optional-engines); ClusterIP access can use port-forwarding.
> - **Credentials & Sessions**: Generated admin passwords use 6 characters in easy mode or 16 in strict mode, retained across upgrades and mode changes.
>   In Vermeer native UI, enter the password from Secret `<release>-vermeer-admin` into **Admin credential**; Hubble internal service tokens are auto-wired.
> - **Topology Changes**: Ensure active computations and batch ingestion jobs are complete and in-memory graphs are unloaded before changing `seatunnel.mode`
>   or `vermeer.mode`. Standalone and cluster use separate PVC claims, so mode changes do not migrate local files.
> - See the [Vermeer Guide](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/vermeer.md) and
>   [SeaTunnel Guide](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/seatunnel.md) for full recovery and configuration details.

### Helm test coverage

`helm test` validates graph binding on every Server Pod (`DEFAULT-hugegraph` by default, or configured via `server.testGraphAlias`), and requires
currently visible associated indexes to be in `CREATED` state.
Run it after index creation/rebuild jobs finish, with no schema changes during the test.
On HStore, reading an unfinished index can cache its temporary status on other Pods; retries do not refresh that state.
Indexed queries on those Pods may keep failing after the job succeeds; replace affected Server Pods only after the jobs finish.
The hook does not fix cross-Server schema cache consistency. Its 150-second internal retry window allows transient elections to settle;
Helm's `--timeout` does not change that window.
It reads indexes by ID without refreshing the full index cache; it does not prove index query results or complete schema consistency.
For existing data, use `--set-file server.testGremlin=assertions.groovy` during Helm upgrade to add read-only business assertions on every Pod.
The script must use `assert` or throw on unexpected results; returning `false` alone does not fail the request.
See [business query assertions](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#business-query-assertions)
for an example and coverage limits. Without a script, business assertions are reported as skipped.
The default hook creates no schema or data. Custom scripts use the hook's Server credential (`admin` with auth enabled);
read-only execution is not enforced, so supply trusted, read-only assertions.

Server API responses negotiate compression through `Accept-Encoding`. Gzip-capable clients can request `gzip` or use `curl --compressed`;
`identity` or no compression request keeps the response uncompressed. Build a new Server image from the updated source to include this behavior;
updating the chart alone does not update an existing image.

### PD REST authentication

PD REST uses HTTP Basic auth: `hg`, `store`, `hubble` and `vermeer` share the PD REST Secret password.
Server's `admin` account is not a PD REST account and receives 401. For the default release/Secret and a reachable PD REST address:

```bash
PD_SECRET=$(kubectl -n hugegraph get secret hugegraph-pd-auth \
  -o jsonpath='{.data.secret-key}' | base64 --decode)
curl --user "hg:${PD_SECRET}" "http://<pd-rest-address>:8620/v1/stores"
```

The HTTP example assumes a trusted internal network. For other access paths, use an HTTPS gateway or optionally forward the PD Service:
`kubectl -n hugegraph port-forward service/hugegraph-pd-client 8620:8620`, then query `http://127.0.0.1:8620`.

With `pd.auth.existingSecret` or a custom `pd.auth.key`, read the actual Secret and key. Do not use the Server admin password.
Variables avoid literal passwords in shell history, but expanded credentials can briefly appear in process arguments.
On shared terminals, use `curl --user hg` to prompt for the password or a private curl config with permissions `600`;
the [credentials guide](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#credentials)
also covers password-update payloads. Keep credential files out of logs and version control.

## 3 Scheduling

The default `preferred` anti-affinity permits scheduling with fewer nodes than replicas. `values-cluster.yaml` sets required PD/Store anti-affinity,
so it needs at least three schedulable nodes. Explicit affinity takes priority over presets.
Local PV node affinity must match the workload's placement constraints; PV capacity declarations do not enforce filesystem quotas.
Do not change a persisted PD/Store Raft hostname or port as an ordinary upgrade: those addresses are recorded identities.

### Keep initialization history separate from live membership {#stable-bootstrap-topology}

The chart records initial PD peers, Store allowlist count and startup Store threshold in an immutable, retained
`<fullname>-bootstrap` ConfigMap. The Helm caller needs namespace ConfigMap-read and PVC-list permissions.
There is no `bootstrap.enabled` switch. Keep this record through upgrades, rollbacks and manual node changes;
it is initialization history, not the current PD voting set or the set of all admitted Stores.

| Value | Fresh installation | Initialized installation |
|---|---|---|
| `bootstrap.pdReplicas` | Empty uses requested PD replicas | Retain recorded initial count |
| `bootstrap.storeReplicas` | Empty uses requested Store replicas | Retain recorded initial allowlist count |
| `bootstrap.initialStoreCount` | Empty uses requested Store replicas | Retain recorded startup threshold |
| `pd.partition.defaultShardCount` | Explicit odd RF, or RF=1 below 3 initial Stores / RF=3 otherwise | PD-persisted replica policy remains authoritative |
{.wide .expand}

For example, growing one Store to three does not convert persisted RF=1 to RF=3. Five PD replicas require a PDB that preserves
three available voters (`pd.pdb.minAvailable=3`); the default two is insufficient. Use PD images implementing separate bootstrap admission
and runtime voting-quorum checks, and verify the capability of the selected image rather than inferring it from `latest`.

An older test installation without a record can be adopted only with unchanged, verified topology, RF, names, ports,
PVC bindings and Raft identities. Run the read-only `helm/check_bootstrap_adoption.py` from the matching Server source against PD and every Store,
retain its before report, then upgrade with reviewed values and compare with `--before` afterward. Follow the
[complete adoption procedure](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#adopting-same-topology-test-data);
it includes graph read/write checks. Do not delete a conflicting record or infer original membership from current replica counts.

Offline upgrades cannot discover retained history: use `helm template --is-upgrade` and explicitly pin all three recorded bootstrap counts.
Offline rendering cannot establish that existing PVCs are safe to reuse. Remove a legacy `bootstrap.enabled` value through reviewed
`--reset-values -f reviewed-values.yaml`; carrying it forward with `--reuse-values` is rejected.

## 4 Partition sharding

At first bootstrap, the chart seeds three shard replicas when the recorded initial Store count is at least three, and one otherwise.
PD persists the partition settings; changing chart values after initialization does not rewrite that metadata.
Use the PD configuration API and a coordinated partition patrol for an existing cluster. An explicit shard count must be odd and no greater than Store replicas.
See the [topology constraints](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#topology-and-scheduling)
before changing a live cluster; the chart does not migrate existing shard metadata.

## 5 NetworkPolicy

Easy mode and the ordinary cluster preset leave full base-service isolation disabled by default; strict enables it.
SeaTunnel and Vermeer always require login. Their native policies allow external HTTP only when the final Service type is NodePort,
while internal RPC, Worker HTTP and SeaTunnel member ports retain their release-caller restrictions, even with `networkPolicy.enabled=false`.
The cluster network plugin must enforce NetworkPolicy for these resources to have an effect.
The generated policies admit component traffic and DNS. For base services, external clients and Ingress controllers need suitable
`networkPolicy.<component>.extraIngress` rules; external discovery addresses may need matching `extraEgress`.
For base-service rules, an empty list can block outside traffic and native Kubernetes rules include `{}` to allow all;
there is no separate source-acknowledgement gate. Use your actual source addresses/selectors, considering NodePort SNAT and controller behavior.

```yaml
networkPolicy:
  enabled: true
  server:
    extraIngress:
      - from:
          - ipBlock:
              cidr: 10.20.0.0/16
        ports:
          - protocol: TCP
            port: 8080
  hubble:
    extraIngress:
      - from:
          - ipBlock:
              cidr: 10.20.0.0/16
        ports:
          - protocol: TCP
            port: 8088
```

Native-engine `extraIngress` accepts explicit internal Pod/namespace selectors only; IP blocks and unrestricted rules are rejected.
NodePort HTTP access is admitted by the generated policy without an `extraIngress` rule.
The base-service example above applies to Server. External data destinations can use engine `extraEgress`;
strict mode additionally enforces egress isolation.

## 6 Rolling Store images safely

Use `store.updateStrategy.type=OnDelete` for a controlled maintenance rollout, as the cluster preset does.
Delete one Store Pod at a time. Before replacing the next, verify the previous Pod is Ready, has a fresh Store heartbeat and each shard group has its
full membership and exactly one leader, read from the PD leader. PD's `Up` status alone does not prove completed shard recovery.
PDBs limit voluntary eviction, not StatefulSet controller disruption. Stop on missing members or leaders.
The [operations reference](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#rolling-store-updates-and-recovery)
summarizes these rollout conditions;
it does not provide a complete per-group diagnostic or disk-loss recovery procedure.

A single Store replacement can cause request errors or timeouts while Raft leadership and client routes converge, even with full replicas.
There is no zero-error guarantee. Observe application errors as well as shard recovery before continuing; do not blindly retry writes.

### PD patrol and leader balance

Partition patrol repairs shard membership; leader balance is a separate manual task and is not scheduled automatically.
Before either task, identify the PD leader through authenticated `/v1/members` (`data.pdLeader.restUrl`) and confirm its `/v1/ready` reports `isLeader: true`.
The GET tasks `/v1/task/patrolPartitions` and `/v1/task/balanceLeaders` change cluster state; target that confirmed leader with PD REST credentials.
Wait for membership recovery and split/move tasks to finish before balancing leaders; Stores must have fresh heartbeats and groups full, healthy membership.
A busy task returns body `status: 1001`. A follower may return empty success, and leader transfers are asynchronous:
HTTP 200 or a transfer plan does not prove completion. Recheck `/v1/partitions`, `/v1/stores` and application errors before further maintenance.
Follow the [task procedure](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#pd-patrol-and-leader-balance)
for the separate patrol and balance steps; do not loop task requests while maintenance is busy.

## 7 Disaster recovery

Preserve existing volumes, claim identities and PD membership. Do not delete RocksDB lock files to recover a deployment, or replace persisted membership
with freshly generated nodes. A new empty PVC does not restore the data from a lost Store disk.
Local disks cannot migrate their files automatically when a node fails. Take backups outside these PVs and test recovery separately.
The chart does not implement backup or automatic recovery. The
[recovery notes](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#rolling-store-updates-and-recovery)
describe constraints, not a complete recovery sequence.
Before destructive changes, establish and validate a recovery plan for the deployed version and remaining replicas or backups.

## 8 Scaling

Server replicas are routinely mutable; an HPA also needs CPU requests. PD and Store changes need database-level coordination before
reconciling Helm resources. Preserve the [bootstrap record](#stable-bootstrap-topology) throughout:

- **PD growth/shrink:** prepare and verify the actual Raft membership first. Desired replicas do not change that membership.
- **Store growth:** prepare storage, check capacity, and explicitly admit the new Pending Store identity.
- **Store shrink:** set the source to Exiting, wait for migration and recovery, verify that actual members exclude it and its local engines are empty,
  then reduce resources. Keep PVCs until retirement and data checks finish.
- **Vermeer Workers:** finish/cancel tasks and unload compute graphs before changing Worker count; recheck availability and reload afterward.

Historical PD seeds still govern Store startup. An initial one-PD cluster expanded to three still needs PD0 to start a new Store;
current PD quorum alone is not enough. Shrinking below the recorded seed majority is unsupported.
Before Store restarts/additions, check both the recorded seed majority and actual PD quorum. Follow the
[controlled node-change procedure][node-changes].

[node-changes]: https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/operations.md#controlled-node-changes-and-recovery-limits
Avoid direct `kubectl scale` as a substitute for the lifecycle procedure; it can also leave Hubble's trusted Store metric targets stale.

## 9 Running Hubble outside the cluster

Direct mode only needs an externally reachable Server URL. PD discovery also needs externally reachable PD gRPC, and Server addresses registered with PD
must be reachable from that external Hubble. Set `server.advertiseUrl` to a shared reachable Server URL when needed; it affects all discovery clients,
including in-cluster Hubble. In-chart Hubble already uses internal service discovery and needs no public PD entry point.
HTTP is supported directly; TLS termination remains optional. Hubble remains single-replica and its current login requires Server authentication.

## 10 When Gremlin fails with Could not rebind

A Server can become Ready and serve REST while Gremlin binding failed during a PD rollout. Run `helm test hugegraph -n hugegraph --logs --timeout 5m`;
the hook checks authenticated graph-bound Gremlin on every Server Pod. Once PD is stable, replace the failing Server Pod and verify again.
A test that only calls `/versions` does not prove graph binding; also check fresh Hubble login and a graph query.

For `ERROR: missing required env 'HG_PD_AUTH_SECRET_KEY'`, inspect the PD Pod's Secret reference and the corresponding key, not the Secret value in logs.
The chart normally injects this shared PD REST credential automatically. Custom containers/manifests must provide the same value to PD and its clients.
In GitOps, create the external Secret before workload reconciliation; with ordinary Helm, retain the chart-generated release Secret.

## 11 Vermeer and RAG recovery {#vermeer-and-rag-recovery}

Vermeer standalone adds two claims; cluster adds one Master claim and one per Worker. Master and Worker must never share a Pebble directory,
even when their containers share a Pod. Claims are retained when disabling/uninstalling Vermeer or reducing Workers.
Explicitly disabled storage uses `emptyDir`; a PVC failure does not fall back to it. Separate standalone and cluster claims are not migrated
when switching topology. Persistent metadata, Worker files and task history do not restore in-memory graphs, cached results or running tasks.
Stop submissions, complete/cancel tasks and unload graphs before topology changes; check Worker availability and reload afterward.

Application logs go to stdout, not the data volume. For the standalone Pod:

```bash
kubectl -n hugegraph logs hugegraph-vermeer-master-0 -c master
kubectl -n hugegraph logs hugegraph-vermeer-master-0 -c worker
```

In cluster mode, use the selected Worker Pod's name (for example, `hugegraph-vermeer-worker-0`) for the second command.
If graph loading fails, check PD discovery, Store gRPC reachability, metadata namespace and Worker Schema credentials;
Pod Ready or `/healthcheck` alone does not establish usable Worker allocation. See
[Vermeer load and compute verification](./hugegraph-helm.md#vermeer-workflow).

RAG uses one persistent resource tree and one replica with Recreate deployment. Saved `settings.yaml` connections override deployment defaults.
A Secret/file change needs a restart; it does not overwrite user-saved connection fields. Preserve the PVC and use the UI to update saved credentials.
A UI save validates and persists configuration without calling the model; **Test saved connection** performs that separate check.
See the [RAG configuration and recovery contract](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/rag.md).

### Check the complete workflow {#integrated-verification}

1. Run `helm test hugegraph -n hugegraph --logs --timeout 5m` and inspect workload/PVC state.
1. Sign in to Hubble afresh and read/write an isolated graph with known expected data.
1. Load that graph into Vermeer, run an algorithm, confirm task success and read result pages. Check the engine and graph context.
1. Open the Vermeer compute summary in Hubble Operations and inspect readiness plus observation timestamps.
1. If RAG is enabled, test saved Chat/Embedding connections and a small extraction/retrieval workflow separately.
{.steps}

Helm rendering checks configuration, `--wait` checks Kubernetes readiness, and the test hook checks its documented graph assertions.
None independently proves Vermeer calculations, RAG model availability, upgrade data preservation or recovery.
