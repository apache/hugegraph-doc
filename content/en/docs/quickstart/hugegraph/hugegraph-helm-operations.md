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
Enabled SeaTunnel adds its configured `apache/seatunnel` image; enabled Vermeer adds a compatible `hugegraph/vermeer` build,
reused by Master, Worker and token initialization. The base local-PV example omits Vermeer claims: standalone adds two,
while cluster adds one Master claim plus one per Worker (four additional claims by default).

## 2 Ports and health

PD listens on REST 8620, gRPC 8686 and Raft 8610; Store on REST 8520, gRPC 8500 and Raft 8510; Server HTTP on 8080; Hubble HTTP on 8088.
Client Services hide individual Pod addresses. NodePort is a separate allocated port on reachable nodes, not the application listener port.
PD `/v1/ready` requires a Raft leader; `/v1/health` only confirms the listener. Store startup waits for a majority of ready PD peers.
Server waits up to `server.storageWaitTimeoutSeconds` (default 300) before its application startup; adjust it for slow storage bootstrap.
No local Helm rendering verifies live cluster reachability, volumes or JVM capacity.

### Preserve the metadata namespace {#metadata-namespace}

`metadataCluster: hg-test` keeps the legacy Server PD metadata prefix and configures both Server `HG_SERVER_CLUSTER` and Store `PD_CLUSTER`.
It is not a Raft name or a metadata-migration option. Do not switch an initialized deployment to `hg` merely to enable Vermeer.
If Vermeer Store scans report `Schema missing` or `no such vertex label` while Server REST queries work, first compare this shared value
with the existing Server metadata namespace and the environment of each running Store Pod.

Online upgrades reject a target value that conflicts with the recorded Server Deployment annotation or explicit `HG_SERVER_CLUSTER` value.
Standard legacy `hg-test` releases need no extra adoption action. If an older custom image used another prefix and the Chart cannot verify it,
inspect the existing Server logs/configuration first. Record that verified existing value on the Server Deployment, then set `metadataCluster`
to exactly the same value in the reviewed Helm values:

```bash
kubectl -n hugegraph annotate deployment hugegraph-server \
  hugegraph.apache.org/metadata-cluster='<verified-existing-namespace>'
```

Replace the placeholder only after verification. This records the namespace already in use; it does not copy or migrate PD keys.
Offline/GitOps rendering cannot inspect the running Deployment, so preserve the verified value explicitly.
With the cluster preset's `store.updateStrategy.type=OnDelete`, updating the StatefulSet template does not update running Pods.
Apply the existing [one-at-a-time Store procedure](#6-rolling-store-images-safely) before expecting the new environment to take effect.
Replacing a Pod backed by `emptyDir` discards its temporary data; such a rollout is not a lossless recovery or migration.

> [!DETAILS]- Optional engines: readiness, credentials and recovery
> SeaTunnel and Vermeer stay disabled in both HugeGraph presets; enabling either adds separate entry credentials and network rules.
> SeaTunnel HTTP/UI uses 8080 and Basic authentication. Its private HTTP/member ports admit only required internal callers in both modes.
> Its long-running hybrid process does not provide PVC-backed checkpoint recovery.
>
> Vermeer Master HTTP/gRPC uses 6688/6689, and Worker HTTP/gRPC uses 6788/6789. Its native UI/API also remains private behind ClusterIP.
> Standalone has one Pod with separate Master/Worker containers and data volumes; cluster has one Master plus three Worker Pods by default.
> Both engines always require native login. New administrator passwords are 16 characters and upgrades retain existing credentials.
> Optional administration uses authorized port-forwarding; Vermeer **Admin credential** accepts the password from `<release>-vermeer-admin`,
> key `password`, with no username required. Login creates a 24-hour versioned session cookie. SeaTunnel still uses username `admin`.
> Hubble service authentication is automatic and separate from human passwords; no token retrieval is needed.
> An external Vermeer administrator Secret change needs a Master restart only; internal service-factor rotation needs Master and Hubble, not Workers.
>
> Master/Worker listener health does not prove space-level compute readiness. Check `/api/v1/workers/availability` with the service credential,
> then verify loading and a known algorithm result through Hubble. The common Worker pool avoids manual allocation for new spaces.
> Persistent metadata does not restore in-memory graphs, result caches or running jobs automatically.
> Stop submissions, finish/cancel tasks and unload compute graphs before topology/Worker-count changes; inspect availability and reload afterward.
> Standalone and cluster use different Worker claims, so changing modes does not migrate local files.
>
> Follow the [Vermeer operations guide](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/vermeer.md)
> and [SeaTunnel operations guide](https://github.com/apache/hugegraph/blob/master/helm/hugegraph/docs/seatunnel.md)
> for administrator password retrieval, retained claims and exact upgrade commands. Raw service tokens are advanced internal integrations only.

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
SeaTunnel and Vermeer always keep private ClusterIP Services, login and native HTTP/RPC ingress restrictions, even with `networkPolicy.enabled=false`.
The cluster network plugin must enforce NetworkPolicy for these resources to have an effect.
The generated policies admit component traffic and DNS. External clients and Ingress controllers need suitable
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

Native engine ingress accepts explicit internal Pod/namespace selectors only; IP blocks and allow-all forms are rejected.
The base-service example above applies to Server, not native engine exposure. External data destinations can use engine `extraEgress`;
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
