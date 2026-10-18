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

Starting with HugeGraph 1.8.0, Server and Store bundle Arthas 4.1.5 (PD does not embed an Arthas agent). You can attach it to a running JVM for live
troubleshooting via the local script or the administrator HTTP endpoint.

> [!IMPORTANT]
> **Security & Access Control**
> - **Local by Default**: Arthas binds to `127.0.0.1` by default. If binding a wildcard address (such as `0.0.0.0`),
>   ensure firewall protection and enable authentication.
> - **Administrator Privilege**: HTTP API activation (`PUT /arthas`) requires Server authentication enabled with administrator privileges;
>   requests without authentication enabled return `403`.
> - **Store Endpoint Disabled**: Store's `GET /v1/arthasstart` is disabled and returns `403`. Use `bin/arthas.sh` instead.
> - **No Restart & Auto Cleanup**: We recommend running `bin/arthas.sh` on the host as the service OS user without restarting the JVM;
>   exiting the interactive session automatically unloads the agent.

| Deployment | Recommended Activation | Access & Permissions |
|------------|------------------------|----------------------|
| Server ([auth](/docs/config/config-authentication/)) | Admin `PUT /arthas` or `bin/arthas.sh` | Admin HTTP credentials; script requires service OS user |
| Server (auth disabled) | Local script `bin/arthas.sh` | HTTP activation returns `403` (including loopback and proxy requests) |
| Store | Local script `bin/arthas.sh` | `GET /v1/arthasstart` is disabled and returns `403` |

##### Activation & Diagnostics

```bash {tab="Local Diagnostics (Recommended)"}
# Run on the host as the service OS user (uses bundled agent offline, no restart needed)
bin/arthas.sh

# Container environments (official images bundle JDK 17)
docker exec -it <container> bin/arthas.sh
```

```bash {tab="Common Diagnostic Options"}
# Specify target JVM PID and custom telnet port (multi-instance on host)
bin/arthas.sh --pid <PID> --telnet-port 3659

# Specify remote bind address and native authentication credentials
bin/arthas.sh --target-ip 0.0.0.0 --username admin --password '<password>'

# Non-interactive single-command batch execution
bin/arthas.sh --command version
```

```bash {tab="Administrator HTTP Activation"}
# 1. Invoke REST API to attach diagnostic agent (requires Server auth; default ports 8562/8561 on 127.0.0.1)
curl -u admin:pa -X PUT http://127.0.0.1:8080/arthas

# 2. Connect to the active agent using the local script
bin/arthas.sh --telnet-port 8562
```

##### Operational Notes & Security Configuration

- **Session Exit & Cleanup**: The local script automatically stops Arthas and releases ports when exiting (via `quit`, `stop`, or `--command` completion),
  leaving the service JVM running. If activated via HTTP API only, execute `stop` in the console to unload the agent.
- **Authentication & Security**: Enable native authentication before exposing diagnostic ports beyond loopback. Supply credentials via `--username`/`--password`
  in the script or set JVM properties `-Darthas.username` and `-Darthas.password`. For full authentication behavior and options, see
  [Arthas Authentication Documentation](https://arthas.aliyun.com/en/doc/auth.html).
- **Disabling Dangerous Commands**: In `rest-server.properties`, configure `arthas.disabled_commands` with a comma-separated list (e.g., `jad,mc`).
  Keep `session` and `stop` enabled so tooling can manage the agent lifecycle. See [Arthas Commands](https://arthas.aliyun.com/en/doc/commands.html)
  for command usage.

##### HTTP Response Body

A successful activation returns HTTP `200` and the applied configuration:

```json
{
    "arthas.telnetPort": "8562",
    "arthas.httpPort": "8561",
    "arthas.ip": "127.0.0.1",
    "arthas.disabledCommands": ""
}
```

> [!NOTE]
> [Configuration options](/docs/config/config-option/) use canonical snake_case names: `arthas.telnet_port`, `arthas.http_port`, `arthas.ip`,
> and `arthas.disabled_commands`. Legacy camelCase aliases remain supported for backward compatibility; explicit snake_case settings take precedence (see
> [upgrade note](/docs/config/config-guide/#3-rest-serverproperties)). The response preserves Arthas agent key names for client compatibility.
