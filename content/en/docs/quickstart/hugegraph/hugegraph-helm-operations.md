---
title: "Operate HugeGraph on Kubernetes"
linkTitle: "Operations on Kubernetes (Helm)"
weight: 5
search_keywords:
  - helm
  - kubernetes
  - operations
  - disaster recovery
  - networkpolicy
---

### 1 Scope

This page is for operating a HugeGraph cluster that the Helm chart already
deployed. Installing, upgrading, and uninstalling are on the
[deployment page](/docs/quickstart/hugegraph/hugegraph-helm/); the full
parameter reference stays in the
[chart README](https://github.com/apache/hugegraph/tree/master/helm/hugegraph#configuration).

Commands below assume the release is named `hugegraph` in namespace
`hugegraph`; substitute your own names. Two credentials come up repeatedly,
both read from chart-managed Secrets:

```bash
PASSWORD="$(kubectl get secret -n hugegraph hugegraph-admin \
  -o jsonpath='{.data.password}' | base64 --decode)"
PD_SECRET="$(kubectl get secret -n hugegraph hugegraph-pd-auth \
  -o jsonpath='{.data.secret-key}' | base64 --decode)"
```

### 2 Ports and health

| Component | Port | Purpose |
|------|-------------|---------|
| PD | `8686` | gRPC (Store and Server clients) |
| PD | `8620` | REST / health probes |
| PD | `8610` | Raft |
| Store | `8500` | gRPC |
| Store | `8510` | Raft |
| Store | `8520` | REST / health probes |
| Server | `8080` | Gremlin and REST API |

All ports are configurable through values; changing `server.port` updates the
listener, container port, and Service together. A stalled component (process
alive but frozen) is ended by its liveness probe: the default 20 s period and
3-failure threshold bound the blast radius of a stalled Store at roughly one
minute, and raft moves its partition leaders within seconds of the restart.

Reach the API through a port-forward:

```bash
kubectl port-forward -n hugegraph svc/hugegraph-server 8080:8080
curl --user "admin:${PASSWORD}" http://127.0.0.1:8080/versions
curl --user "admin:${PASSWORD}" http://127.0.0.1:8080/graphs
```

### 3 Scheduling

Every component (`pd`, `store`, `server`, `hubble`) exposes `nodeSelector`,
`tolerations`, `affinity`, `topologySpreadConstraints`, and
`priorityClassName`. Pinning Store to labeled nodes is just:

```yaml
store:
  nodeSelector:
    hugegraph/role: storage
```

`antiAffinity` (`required` | `preferred` | `disabled`) renders a hostname
pod-anti-affinity preset for `pd`, `store`, and `server`; Hubble is
single-replica by design and has no such key. Setting a raw `affinity`
replaces the preset entirely. All three default to `preferred`, so the chart
schedules on clusters with fewer nodes than replicas. The trade: under node
pressure the scheduler may co-locate replicas, and a single node failure can
then take more than one PD or Store replica with it. Production clusters with
enough nodes should pin `pd.antiAffinity` and `store.antiAffinity` to
`required`, as `values-cluster.yaml` does.

### 4 Partition sharding

A fresh install seeds PD with a partition shard count of 3 when
`store.replicas` is at least 3, and 1 otherwise; without the seed, the PD
image pins `partition.default-shard-count` to 1 and chart-deployed clusters
would run without store-level HA. The chart passes the value as
`-Dpartition.default-shard-count` in PD's `JAVA_OPTS`, so the image's JVM
auto-sizing is unaffected.

**The seed applies at first bootstrap only.** PD persists the shard count the
first time it starts with empty storage; from then on the stored value is
authoritative, and changing `pd.partition.defaultShardCount` or scaling
`store.replicas` later has no effect on an initialized cluster. To change
the shard count of a running cluster, use PD's own config API (odd values
only, at most the live store count), then trigger
`GET /v1/task/patrolPartitions` and expect shard-group reallocation.

The shard count also fixes the initial partition count:
`store.replicas x storeMaxShardCount / shardCount`, computed once at
bootstrap. With the image default `store-max-shard-count` of 12, a default
3-store install gets 12 partitions; raise
`pd.partition.storeMaxShardCount` (likewise seeded once) when more
partitions are wanted.

An explicit `pd.partition.defaultShardCount` must be odd and at most
`store.replicas`; the chart rejects other values at render time because PD
would otherwise clamp or refuse them silently.

### 5 NetworkPolicy

`networkPolicy.enabled` renders one NetworkPolicy per component (PD, Store,
Server, and Hubble when enabled). Each policy isolates its own Pods in both
directions and lists the traffic they need, so apply order does not matter.
It is off in `values.yaml`, because the base values cannot know who your
clients are, and on in `values-cluster.yaml`.

It only works when the cluster's network plugin enforces NetworkPolicy (kind
v0.25 or later, k3s, Calico, Cilium); other plugins accept the objects and
enforce nothing. To check, run a Pod without chart labels in another
namespace and `curl` the PD client Service on the REST port: it must time
out.

With the policies on, the release admits only its own traffic:

| To | From, ports |
|---|---|
| PD | PD: raft, gRPC. Store, Server, and Hubble in `pd` mode: gRPC, REST |
| Store | Store: raft. Server: gRPC, REST. Hubble in `pd` mode: REST |
| Server | Hubble and the `helm test` Pod: `server.port` |
| Hubble | nothing (port-forward uses loopback and needs no rule) |

Every component may also resolve DNS on port 53. Nothing outside the release
is admitted unless it is listed in `networkPolicy.<component>.extraIngress`,
including the Ingress controller and the clients of a NodePort or
LoadBalancer Service. Exposing PD, Server or Hubble that way, or setting
`server.advertiseUrl`, with an empty `extraIngress` fails the render instead
of opening the port. The check sees only exposure the chart creates; a
Service, Gateway route or proxy you add yourself needs its own entry.

Two egress facts to plan around. PD, Store and Server reach nothing outside
the release except DNS, so features that call out do not work with the
policies on; the one default caller is the Store image, which downloads
`libjemalloc.so` from github.com on every start. With the policies on that
connection times out after about two minutes and the Store starts without
jemalloc (measured on kind: Ready after 151 s instead of 11 s); the same
happens on any cluster without internet access. And the `helm test` Pod is
selected by no chart policy, so under a namespace-wide default-deny policy
of your own you must allow it egress to `server.port` and DNS.

**Letting other workloads in.** Every rule must name its peers in `from`;
to admit any address, write an `ipBlock` such as `0.0.0.0/0` explicitly. A
`namespaceSelector` and a `podSelector` in the same peer must both match;
as two separate peers, either one is enough. What a NodePort or
LoadBalancer client looks like from the Pod depends on the network plugin,
`externalTrafficPolicy`, and the node the request arrives on. Measured with
a NodePort Server on two-node kind clusters:

- kindnet, and Cilium with kube-proxy replacement: a call to the Server's
  own node arrived with the client address; through the other node it
  arrived with that node's address.
- Calico: through the other node the call arrived from that node's tunnel
  address inside the Pod CIDR.
- Cilium with kube-proxy: no `ipBlock` rule admitted NodePort traffic,
  because Cilium identifies node addresses by its own node identities
  rather than by CIDR.

Test with the plugin you run and name the CIDR you see arriving. A worked
example admitting an Ingress controller, an application namespace, and
Prometheus:

```yaml
networkPolicy:
  server:
    extraIngress:
      - from:
          - namespaceSelector:
              matchLabels:
                kubernetes.io/metadata.name: ingress-nginx
            podSelector:
              matchLabels:
                app.kubernetes.io/name: ingress-nginx
        ports:
          - port: 8080
      - from:
          - namespaceSelector:
              matchLabels:
                kubernetes.io/metadata.name: apps
        ports:
          - port: 8080
  pd:
    extraIngress:
      - from:
          - namespaceSelector:
              matchLabels:
                kubernetes.io/metadata.name: monitoring
        ports:
          - port: 8620
```

### 6 Rolling Store images safely

Store rolling updates advance on a listener check, not on shard recovery,
so the controller can replace the next Store while the previous one is
still rejoining its shard groups. For a production image roll, set
`store.updateStrategy.type=OnDelete` and delete Store Pods one at a time,
checking between deletions.

`Up` in PD is not that check. PD marks a Store `Up` at registration, before
the Store has restored any partition, and a stopped Store stays `Up` in
every shard group until its keep-alive entry expires (300 s on current
images): a Pod deleted and back inside that window never leaves `Up` at
all. Start with the Pod instead:

```bash
kubectl -n hugegraph wait --for=condition=Ready \
  pod/hugegraph-store-<ordinal> --timeout=10m
```

Then check shard membership and leadership per group, read from the PD
leader (see Disaster Recovery below for finding the leader):

```bash
curl -s -u "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/shardGroups | jq '
  .shardGroups[] | {id: (.id // 0),
                    shards: [.shards[] | {storeId, role}],
                    leaders: [.shards[] | select(.role=="Leader")] | length}'
```

Delete the next Store only when the replaced Pod is `Ready`, its Store id
shows a fresh `lastHeartBeat` in `/v1/stores`, and every group reports its
full shard count with exactly one `Leader`.

Know what this does not prove: the shard list is PD's membership record,
not a statement that the Store caught up on the raft log. No endpoint on
current images reports restoration-complete. For a closer look,
port-forward the replaced Store and read its own view of a group:
`GET :8520/v1/partition/<groupId>` returns the raft role, term, and
committed index that Store holds, and fails while the Store is down;
compare term and index with a peer Store rather than reading them alone.
The plural `GET :8520/v1/partitions` answers 500 on any Store that follows
a group on images built before
[apache/hugegraph#3232](https://github.com/apache/hugegraph/pull/3232)
(merged 2026-09-24); after it, it answers 200 on every Store, with `conf`
and `peers` null for followed groups. The per-group path works on both.

Leave a margin after the membership check, keep `store.pdb.minAvailable`
at `replicas - 1` so an accidental second eviction is refused, and treat a
group that is short a shard or has no leader as a stop. A real
restoration-complete signal is upstream work, tracked in
[apache/hugegraph#3229](https://github.com/apache/hugegraph/issues/3229).

### 7 Disaster recovery

What PD automates on current builds is narrow: a 60-second patrol only
marks Stores that stopped sending heartbeats as `Offline`. There is no
automatic re-replication; re-placing the replicas of a lost Store,
reconciling shard groups, and processing tombstoned Stores run only when a
partition patrol is triggered explicitly.

The task endpoints execute locally on the PD that receives them, and a
follower answers with an empty success while doing nothing.
Port-forwarding the client Service selects an arbitrary PD, so identify
the leader first, then port-forward that Pod (two terminals: the forward
runs in the foreground):

```bash
kubectl port-forward -n hugegraph svc/hugegraph-pd-client 8620:8620
# Read .data.pdLeader.raftUrl; its host names the leader Pod.
curl -su "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/members
# Stop the Service forward, then forward the leader Pod instead.
kubectl port-forward -n hugegraph pod/<leader-pod> 8620:8620
# Reconcile shard groups and process tombstoned Stores.
curl -u "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/task/patrolPartitions
# Spread Raft leaders, then partition data.
curl -u "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/task/balanceLeaders
curl -u "hg:${PD_SECRET}" http://127.0.0.1:8620/v1/task/balancePartitions
```

Read `/v1/members` again after the tasks: if leadership moved mid-sequence,
the later tasks ran on a follower and did nothing. Wait at least 180 s
before rerunning `balanceLeaders` after a `balancePartitions` call:
`balancePartitions` sets a balance-shard flag for 180 s even when it moves
nothing, and `balanceLeaders` inside that window is refused. On images
built before
[apache/hugegraph#3233](https://github.com/apache/hugegraph/pull/3233)
(merged 2026-09-24) the refusal is a bare HTTP 500 whose reason appears
only in the PD log; after it, the reason comes back in the body as
`{"status":1001,"error":"balance shard is processing, please try later!"}`.

Telling a real run from a no-op takes the PD leader's log, because the
responses do not: `patrolPartitions` answers the same empty success on the
leader and on a follower, whether or not it repaired anything (look for
`reallocShards`, `shardOffline` or `storeTurnoff` lines, or diff
`/v1/shardGroups` before and after), and `balancePartitions` answers `{}`
on the leader and an empty body on a follower. `balanceLeaders` is the one
call whose body carries the work. Distinguishable task responses are
upstream work, tracked in
[apache/hugegraph#3231](https://github.com/apache/hugegraph/issues/3231).

Run `patrolPartitions` after replacing a Store that is not coming back,
`balancePartitions` once the cluster is stable again, and `balanceLeaders`
after restarts that skewed leader placement.

**Losing a Store volume.** A Store rebuilt with an empty PVC recovers in
place on images carrying
[apache/hugegraph#3234](https://github.com/apache/hugegraph/pull/3234)
(merged 2026-09-24); on every earlier image, including all published
release images, it does not. In both cases the replacement registers under
a new Store ID while its Pod name, DNS name, and raft address are
unchanged, so `/v1/stores` lists two IDs at one address.

On post-#3234 images the retirement works: find the old ID in `/v1/stores`
(the row at the replaced Pod's address that is not the newly registered
one), `POST /v1/store/<oldId>` with `{"storeState":"Tombstone"}` on the PD
leader, run `GET /v1/task/patrolPartitions`, and wait; verify every shard
group is back to full shard count with one leader, no group names the old
ID, and the replaced Store's own `:8520/v1/partition/<groupId>` answers
200 for every group; then `DELETE /v1/store/<oldId>` to erase the retired
record. Measured on a 3+3+3 install with images built from `master` at
`dbb6663a`: the replacement was Ready in 156 s, all 12 groups converged
onto the new ID 1 s after the Tombstone and patrol (the empty Store caught
up by raft snapshot install), and a continuous writer lost 0 acknowledged
writes.

On images without #3234 the same retirement runs and does not repair the
groups: PD fires the configuration change, but the group leader sees the
address already in the group, so jraft has nothing to add and the group
keeps the old ID. Measured: 20 minutes and three patrols later, all 12
groups still listed the retired ID and the replacement Store held no
partitions. Nothing in the health surface shows the failure; `/v1/stores`,
cluster state, Hubble, and Pod readiness all read healthy while every
shard group runs on two live replicas. The one check that shows it is the
replaced Store's own `:8520/v1/partition/<groupId>`.

So the default remains: replace a Store Pod, keep its PVC (the Store id
lives in the data path, and the Pod comes back under the same id). Treat
the empty-PVC procedure as recovery for post-#3234 images only; on a
released image a genuinely lost volume leaves the cluster degraded, and
expect to rebuild rather than to recover in place.

Periodic leader balancing is tracked in
[apache/hugegraph#3135](https://github.com/apache/hugegraph/issues/3135);
disaster-recovery metrics in
[apache/hugegraph#3136](https://github.com/apache/hugegraph/issues/3136).

### 8 Scaling

PD and Store reserve the maximum StatefulSet ordinal in their resource
names, so scaling never renames a PersistentVolumeClaim or shifts a Pod
identity; both are capped at 99 replicas. Server scales freely through
`server.replicas` or `server.hpa` (with HPA on, the Deployment omits
`spec.replicas` so upgrades do not overwrite the autoscaler).

A staged rollout cannot be written in a values file (the schema requires
one replica per component); stage it with `kubectl scale statefulset
hugegraph-store --replicas=0` and scale back up when ready. The Servers
wait, not ready, until Stores register, and the next `helm upgrade`
restores the full topology from values.

Changing PD or Store replicas on a live release is not a values change:
raft and shard membership are persisted, and Pods alone do not reconfigure
them. The chart rejects both directions for PD and a shrink for Store by
reading the live StatefulSet, so fresh installs at any count are
unaffected.

**PD, either direction.** The rendered peer list reaches raft only as its
bootstrap configuration, which an initialized group ignores; a 3-to-5
upgrade leaves the voting configuration at three, and a 3-to-1 shrink
loses quorum outright. Membership changes go through the PD client API
(no REST route exposes them), which the chart cannot wrap. Change the
membership through PD, confirm it in `/v1/members`, scale the live
StatefulSet, then `helm upgrade` with the matching value; until that
sequence is verified on your own build, install the PD count you intend
to keep.

**Store, shrinking.** Draining is a state transition, not a balance:
neither `patrolPartitions` nor `balancePartitions` retires a healthy
Store. Retire the leaving Stores the way Disaster Recovery retires a
replaced one:

1. Check the remaining Stores still cover the persisted shard count
   (`pd.partition.defaultShardCount`; empty derives 3 when
   `store.replicas` is at least 3).
2. Map the ordinals the shrink will delete (the highest ones) to Store
   ids through `/v1/stores`, matching on the Pod address.
3. `POST /v1/store/<id>` with `{"storeState":"Tombstone"}` for each
   leaving id.
4. Wait until `/v1/shardGroups` no longer lists those ids and every group
   reports its full shard count with one leader.
5. Scale the live StatefulSet, then `helm upgrade` with the matching
   value.

Deleting the PVCs of the removed ordinals is separate and permanent; do it
only after step 4 reports the data moved.

### 9 Running Hubble outside the cluster

In-cluster Hubble (`hubble.enabled=true` plus a port-forward) is the
recommended path and is covered on the deployment page. Two paths exist
for a Hubble that must run outside the cluster.

**Direct Server URL** (graph, schema, data, and Gremlin; no PD
discovery): leave in-chart Hubble off, expose Server
(`server.service.type` NodePort/LoadBalancer, or Ingress), and run a
standalone Hubble image with:

```properties
pd.enabled=false
server.direct_url=https://<reachable-server-host>:<port>
```

Mount the file at `/hubble/conf/hugegraph-hubble.properties` (the image
workdir is `/hubble`). Use HTTPS or a trusted channel for
`server.direct_url`: login sends the Server credentials over that URL.

**PD discovery** (the outside Hubble asks PD for the Server address):
in-cluster names such as `*.svc` are not reachable from outside, so the
chart provides two knobs. Set `server.advertiseUrl` to the absolute
`http(s)://` URL the outside Hubble will use after discovery; the chart
registers it with PD in place of the in-cluster Service URL. And expose
the PD client Service (`pd.service.type` NodePort/LoadBalancer), which
requires `pd.service.allowInsecureExposure=true` because PD gRPC has no
authentication; restrict who can reach it first (with the chart's
NetworkPolicy on, the render refuses the exposure until its callers are
listed in `networkPolicy.pd.extraIngress`). Then run standalone Hubble
with:

```properties
pd.enabled=true
pd.peers=<reachable-pd-host>:<grpc-port>
pd.server=<reachable-pd-host>:<rest-port>
```

Trade-off: when `server.advertiseUrl` is set, every Server replica
registers that same logical URL and PD returns it to every discovery
client, including an in-cluster Hubble. Leave it empty for the default
in-cluster path, where each Server Pod registers its own IP.

Local quick test (cluster and Hubble on one machine): port-forward Server
`8080` and PD client `8620`/`8686`, set
`server.advertiseUrl=http://127.0.0.1:8080`, run standalone Hubble with
`--network host` and the properties above, then open Hubble on `8088`.

### 10 When Gremlin fails with "Could not rebind"

The error has two causes with different lifetimes.

**A convergence window after creating a graph.** The Server that handles
`CreateGraph` waits for its own Gremlin binding before returning HTTP 200
([#3138](https://github.com/apache/hugegraph/pull/3138)), so
create-then-query on the same Server is reliable. Other replicas converge
independently, and until they finish, a Gremlin query routed through the
load-balanced Service to a not-yet-converged replica can fail with a 400
such as `Could not rebind [g]`. Retry with backoff (the window normally
closes in seconds), use sticky routing or a port-forward for
create-then-verify flows, or poll `/graphs` on each replica before
opening query traffic. Cluster-wide readiness is tracked in
[#3137](https://github.com/apache/hugegraph/issues/3137).

**A Server Pod that started while PD was rolling.** Gremlin Server
instantiates the graph once at startup; if the PD client cannot connect
at that moment, the Pod passes readiness and serves REST while every
Gremlin request on it fails with `Could not rebind [graph]`, for the life
of the Pod. Its `hugegraph-server.log` names it:

```
Graph [DEFAULT-hugegraph] configured at [...] could not be instantiated and
will not be available in Gremlin Server
```

After any upgrade that rolled PD and Server together, check Gremlin on
each Server Pod (the image ships no curl, so port-forward each Pod):

```bash
kubectl port-forward -n hugegraph pod/<server-pod> 8080:8080
curl -s --compressed -u "admin:${PASSWORD}" -H 'Content-Type: application/json' \
  -X POST http://127.0.0.1:8080/gremlin \
  -d '{"gremlin":"graph.traversal().V().limit(1).count()","aliases":{"graph":"DEFAULT-hugegraph"}}'
```

A healthy Pod answers with `result.data`; delete a Pod that answers
`Could not rebind`. Its replacement binds normally once PD is stable
(measured: 4 of 12 Server starts that overlapped a PD roll hit this, and
every deletion recovered).
