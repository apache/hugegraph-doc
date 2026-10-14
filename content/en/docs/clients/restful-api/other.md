---
title: "Other API"
linkTitle: "Other"
weight: 18
description: "Other REST API: Provide auxiliary functions such as version query, API listing, exception trace switch, IP allowlist and the Arthas agent."
---

### 11.1 Other

#### 11.1.1 View Version Information of HugeGraph

##### Method & Url

```text
GET http://localhost:8080/versions
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "versions": {
        "version": "v1",
        "core": "1.7.0",
        "gremlin": "3.5.1",
        "api": "0.72.0.0"
    }
}
```

#### 11.1.2 View the profile of the server

Returns the service name, the core version, the documentation links and the API groups served by this node.

##### Method & Url

```text
GET http://localhost:8080/
```

##### Response Status

```json
200
```

##### Response Body

The `swagger_ui` value is derived from `restserver.url`, and `apis` lists the API groups registered on this node, sorted by name.

```json
{
    "service": "hugegraph",
    "version": "1.7.0",
    "doc": "https://hugegraph.apache.org/docs/",
    "api_doc": "https://hugegraph.apache.org/docs/clients/",
    "swagger_ui": "http://127.0.0.1:8080/swagger-ui/index.html",
    "apis": [
        "arthas",
        "auth",
        "cypher",
        "filter",
        "graph",
        "gremlin",
        "job",
        "metrics",
        "profile",
        "raft",
        "schema",
        "space",
        "traversers",
        "variables"
    ]
}
```

#### 11.1.3 List all APIs of the server

Lists every registered resource method, grouped by API group and resource class. Each entry carries the url, the HTTP method and the query parameters with their types and default values.

##### Method & Url

```text
GET http://localhost:8080/apis
```

##### Response Status

```json
200
```

##### Response Body

The response is long, the following fragment shows the shape:

```json
{
    "apis": {
        "schema": {
            "PropertyKeyAPI": [
                {
                    "url": "graphspaces/{graphspace}/graphs/{graph}/schema/propertykeys",
                    "method": "GET",
                    "parameters": [
                        {
                            "name": "names",
                            "type": "java.util.List<java.lang.String>",
                            "default_value": null
                        }
                    ]
                }
            ]
        }
    }
}
```

#### 11.1.4 View and switch the exception trace stack

Whether the error responses of the server carry the exception stack in the `exception` and `cause` fields is decided by the `exception.allow_trace` option (default `true`). The switch below is a node-wide runtime override: while it is on, the stack is always included, no matter what the option says. `GET` reports the state of that override, which starts as `false`.

##### Method & Url

```text
GET http://localhost:8080/exception/trace
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "trace": false
}
```

##### Method & Url

```text
PUT http://localhost:8080/exception/trace
```

##### Request Body

```json
true
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "trace": true
}
```

#### 11.1.5 Manage the IP allowlist, **this operation requires administrator privileges**

The allowlist is only enforced when it is switched on, see the `white_ip.status` option (default `disable`).

##### List the allowlist

##### Method & Url

```text
GET http://localhost:8080/whiteiplist
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "whiteIpList": [
        "127.0.0.1"
    ]
}
```

##### Add IPs to or remove IPs from the allowlist

##### Params

- ips: list of IPv4 addresses
- action: `load` to add, `remove` to delete

##### Method & Url

```text
POST http://localhost:8080/whiteiplist
```

##### Request Body

```json
{
    "ips": [
        "10.0.0.1",
        "10.0.0.2"
    ],
    "action": "load"
}
```

##### Response Status

```json
202
```

##### Response Body

`existed_ips` are the addresses already in the list, `added_ips` are the newly added ones, and `illegal_ips` is only returned when some addresses are not valid IPv4 addresses. For `action=remove` the response carries `removed_ips` and `non_existed_ips` instead.

```json
{
    "existed_ips": [],
    "added_ips": [
        "10.0.0.1",
        "10.0.0.2"
    ]
}
```

##### Enable or disable the allowlist

##### Params

- status: `true` to enable, `false` to disable

##### Method & Url

```text
PUT http://localhost:8080/whiteiplist?status=true
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "WhiteIpListOpen": true
}
```

#### 11.1.6 Start the Arthas agent

Starting with HugeGraph 1.8.0, Server and Store bundle Arthas 4.1.5 (PD does not embed an Arthas agent). You can attach it to a running JVM for live troubleshooting via the local script or the administrator HTTP endpoint.

> [!IMPORTANT]
> **Security Requirements for Diagnostics**
> - **Loopback Only**: Arthas defaults to `127.0.0.1` and accepts only loopback addresses. Non-loopback addresses (such as `0.0.0.0`) are rejected.
>   Diagnostic ports must not be exposed via reverse proxies or container port mappings.
> - **Administrator Privilege**: HTTP API activation requires authentication to be enabled on Server with administrator privileges;
>   requests without authentication enabled return `403`.
> - **Offline Local Diagnostics**: For routine troubleshooting, run `bin/arthas.sh` on the host as the service OS user without restarting
>   the JVM or editing configuration.

| Deployment | Recommended Activation | Access & Permissions |
|------------|------------------------|----------------------|
| Server ([authentication enabled](/docs/config/config-authentication/)) | Administrator `PUT /arthas` or `bin/arthas.sh` | Only administrator accounts can invoke the HTTP endpoint; helper script requires service OS user access |
| Server (authentication disabled) | Local helper `bin/arthas.sh` | HTTP activation returns `403` (including loopback and proxy requests) |
| Store | Local helper `bin/arthas.sh` | `GET /v1/arthasstart` is disabled and returns `403` (Store lacks administrator authentication for this endpoint) |

##### Activation & Diagnostics

```bash {tab="Local Diagnostics (Recommended)"}
# 1. Run on the host as the service OS user (uses bundled agent offline, no restart or download needed)
bin/arthas.sh

# 2. For multiple instances on one host, specify PID and port explicitly
bin/arthas.sh --pid <PID> --telnet-port 3659

# 3. Disconnect: enter 'quit' to exit client session; enter 'stop' to unload the agent (does not affect JVM)
```

```bash {tab="Administrator HTTP Activation"}
# 1. Invoke REST API to attach diagnostic agent (requires Server authentication; enter admin password)
curl --user admin -X PUT http://127.0.0.1:8080/arthas

# 2. On success, returns applied configuration (default ports 8562/8561 on 127.0.0.1)
# 3. Connect to the active agent using the local helper
bin/arthas.sh --telnet-port 8562
```

The helper reads `bin/pid` by default and requires JDK 17. Both distributions include the agent files in `lib/arthas`, so no download,
runtime extraction, or persistent user cache is needed. For a newly activated agent, telnet defaults to `127.0.0.1:3658`; HTTP, MCP,
and tunnel connections are disabled.

An already active agent retains its listener settings. Connect on its current telnet port; the helper does not rebind it or disable an
existing HTTP listener. To switch from the Server API defaults to the local helper defaults, stop only Arthas and attach again:

```bash
bin/arthas.sh --telnet-port 8562 --command stop
bin/arthas.sh
```

Use the configured telnet port if it differs from `8562`. The service JVM keeps running.

##### HTTP Response Body

A successful activation returns HTTP `200` and the applied configuration:

```json
{
    "arthas.telnetPort": "8562",
    "arthas.httpPort": "8561",
    "arthas.ip": "127.0.0.1",
    "arthas.disabledCommands": "jad"
}
```

> [!NOTE]
> [Configuration options](/docs/config/config-option/) use canonical snake_case names: `arthas.telnet_port`, `arthas.http_port`, `arthas.ip`, and `arthas.disabled_commands`.
> Legacy camelCase aliases remain supported for backward compatibility; explicit snake_case settings take precedence. The response preserves Arthas agent key names for client compatibility.
