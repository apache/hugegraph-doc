---
title: "Manage an HStore Cluster with Hubble"
description: "Connect HStore and PD to Hubble and understand GraphSpaces, Schema templates, cluster topology, and node metrics."
linkTitle: "Hubble with HStore"
weight: 2
search_keywords: [HugeGraph Hubble, HStore, PD, GraphSpace, cluster management]
---

This guide covers the differences between HStore + PD and standalone RocksDB.
For modeling, importing data, and querying, see the [Hubble standalone guide](/docs/quickstart/toolchain/hugegraph-hubble/).
The configuration and features below were checked against Toolchain `master`; they have not been verified in a running distributed environment.

## Connect to a distributed cluster

Hubble still manages graph data through the **Server graph API**. In distributed mode, it discovers Servers through PD
and collects cluster information from PD and Store. Hubble does not read or write graph data directly in Store.

Follow the [PD deployment guide](/docs/quickstart/hugegraph/hugegraph-pd/) and
[HStore deployment guide](/docs/quickstart/hugegraph/hugegraph-hstore/) to start matching versions of PD, Store, and Server.
Confirm that Server is registered and Store is ready, then edit Hubble's `conf/hugegraph-hubble.properties`.
These hostnames illustrate a minimal topology on one container network; replace them with addresses reachable from the Hubble backend:

```properties
pd.enabled=true
cluster=hg
pd.peers=pd:8686
pd.server=pd:8620
```

| Setting | Purpose | Bundled value |
|---|---|---|
| `pd.enabled` | Explicitly enable PD mode; `server.direct_url` is not used in this mode. | `false` |
| `cluster` | Cluster name used for Server discovery; it must match the registration. | `hg` |
| `pd.peers` | PD **gRPC** addresses, separated by commas. | `127.0.0.1:8686` |
| `pd.server` | PD **REST** address for cluster operations, not a list of gRPC peers. | `127.0.0.1:8620` |

Do not interchange ports `8686` and `8620`, or retain `127.0.0.1` for connections between containers.
The bundled file explicitly sets `pd.enabled=false`, while the Java fallback for a missing key is `true`; set it explicitly in either deployment.
Restart Hubble after changing the configuration. You do not enter a Server host and port for each graph in the UI.

## Select a GraphSpace before a graph

A GraphSpace groups graphs and their access permissions. In PD mode, select an accessible GraphSpace in the graph overview,
then open a graph for modeling, importing, or querying. Check the current graph after switching spaces, especially when spaces contain identically named graphs.

When Server authentication is enabled, the GraphSpace list reflects the account's permissions.
For Servers that support GraphSpace permission presets, use Hubble account management to assign access.
Enabling `pd.enabled` does not grant administrative permissions. See [Server authentication and authorization](/docs/config/config-authentication/).

**User-defined Schema templates require PD mode**. Templates store reusable Groovy Schema within a GraphSpace and can be applied when creating a graph.
Creating a template requires write access to that space; updating or deleting it also requires ownership or the corresponding administrative permission.
These templates are separate from the built-in sample data in the standalone guide. Standalone mode does not provide user template management.

## Inspect the cluster and its nodes

The cluster overview presents Server, PD, and Store in one topology, with node status and available cluster facts such as partition counts.
Filter the node list and open a node's details to inspect JVM, CPU, memory, backend, or partition metrics supplied by that component.
Metric availability varies by component and version. Missing, stale, and failed collections are labeled separately; an empty value does not mean zero.

With Server authentication enabled, cluster operations require the `ADMIN` level; GraphSpace write permission is insufficient.
Operations information is also readable in anonymous Server mode, so restrict network access to Hubble and upstream ports.

### Configure operations access

Hubble's **backend** uses the PD/Store operations credentials, separately from the Server account used to log in through the browser.
Put deployment-specific credentials in the actual configuration file. Do not include passwords in documentation, screenshots, or committed configuration:

| Setting | Bundled default | Configuration |
|---|---|---|
| `operations.pd.username` / `operations.pd.password` | Username `hubble`, empty password | Match PD operations REST authentication. |
| `operations.store.username` / `operations.store.password` | Username `hubble`, empty password | Set the service account when upstream Store REST authentication is enabled. |
| `operations.store.allowed_targets` | `[http://127.0.0.1:8520,http://[::1]:8520]` | List trusted Store metric origins. |

For example, when a containerized Store advertises `store:8520`, set:

```properties
operations.store.allowed_targets=[http://store:8520]
```

For multiple nodes, list each trusted origin. Every entry must use `http` or `https` with an explicit port and no path, credentials, or wildcard,
and must match the Store metric target returned by PD. Adding an origin to this list does not register or discover a node.

If topology is available but metrics are incomplete, check backend connectivity and authentication to PD REST, the Store REST/metric targets returned by PD,
and their match with the allowlist. A partially available overview means some sources could not be collected;
it does not imply that all graph APIs are unavailable.
