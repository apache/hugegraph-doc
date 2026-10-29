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
Enabled SeaTunnel adds its configured `apache/seatunnel` image. Enabled Vermeer uses `hugegraph/vermeer:helm-30b67d93e7d0`, pinned by digest
and reused by Master, Worker and token initialization. Official publishing runs
record the source and image digest; see the
[Vermeer deployment guide](https://github.com/apache/hugegraph/blob/e886e9a669cdfd47c9f83392f86fc47940167960/helm/hugegraph/docs/vermeer.md).
Custom image overrides must also update `vermeer.image.digest`, or explicitly clear it to select by tag; digest takes priority.
The base local-PV example omits Vermeer claims: standalone adds two,
while cluster adds one Master claim plus one per Worker (four additional claims by default).

## 2 Ports and health

PD listens on REST 8620, gRPC 8686 and Raft 8610; Store on REST 8520, gRPC 8500 and Raft 8510; Server HTTP on 8080; Hubble HTTP on 8088.
Client Services hide individual Pod addresses. NodePort is a separate allocated port on reachable nodes, not the application listener port.
PD `/v1/ready` requires a Raft leader; `/v1/health` only confirms the listener. Store startup waits for a majority of ready PD peers.
Server waits up to `server.storageWaitTimeoutSeconds` (default 300) before its application startup; adjust it for slow storage bootstrap.
No local Helm rendering verifies live cluster reachability, volumes or JVM capacity.

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
> - See the [Vermeer Guide](https://github.com/apache/hugegraph/blob/e886e9a669cdfd47c9f83392f86fc47940167960/helm/hugegraph/docs/vermeer.md) and
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

## 4 Partition sharding

At first bootstrap, the chart seeds three shard replicas when there are at least three Stores, and one otherwise.
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

Server replicas are routinely mutable; an HPA also needs CPU requests. Store growth is a coordinated storage/shard operation.
PD growth/shrink and Store shrink cannot be handled as ordinary replica changes, because persistent Raft/shard membership must be updated first.
Chart upgrade checks reject unsupported identity/membership changes on initialized StatefulSets; fresh installs do not query StatefulSets for upgrade checks.
Scale through the documented lifecycle procedure rather than `kubectl scale`, which can leave Hubble's Store metrics configuration stale.

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
