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

The following behavior targets the next release with [server PR #2945](https://github.com/apache/hugegraph/pull/2945).
Earlier releases have different activation and bind defaults.

[Arthas](https://arthas.aliyun.com/en/) attaches to a running JVM for diagnosis. Server and Store bundle the same Arthas 4.1.5 version;
PD does not embed an Arthas agent. Choose an activation method that matches your deployment:

| Deployment | Activation |
|------------|------------|
| Server with [authentication enabled](/docs/config/config-authentication/) | An authenticated administrator can call `PUT /arthas` directly. |
| Server without authentication | Run `bin/arthas.sh` on the host as the service's OS user. HTTP activation returns `403`, including loopback/proxy requests. |
| Store | Run the same local helper. `GET /v1/arthasstart` returns `403`; Store has no administrator authentication for this endpoint. |

Arthas listens on loopback only. Non-loopback addresses, including `0.0.0.0`, are rejected during Server HTTP activation, and MCP is disabled.
Do not expose diagnostic ports through a reverse proxy or container port mapping. For remote diagnosis, log into the host over SSH and run the local helper.

##### Administrator HTTP activation

No additional Arthas enable switch or JVM restart is needed when Server authentication is already configured. Authenticate as the administrator:

```bash
curl --user admin -X PUT http://127.0.0.1:8080/arthas
```

The command prompts for the password. Authenticated non-administrators receive `403`; missing or invalid credentials follow the configured
Server authentication behavior. When authentication is disabled, this endpoint always returns `403` before attaching the agent.

A successful request returns HTTP `200` and the applied Arthas configuration:

```json
{
    "arthas.telnetPort": "8562",
    "arthas.httpPort": "8561",
    "arthas.ip": "127.0.0.1",
    "arthas.disabledCommands": "jad"
}
```

The [configuration options](/docs/config/config-option/) use `arthas.telnet_port`, `arthas.http_port`, `arthas.ip`, and `arthas.disabled_commands`.
Legacy camelCase aliases remain supported; explicit snake_case settings win and conflicting aliases produce a warning. The response keeps
Arthas agent key names for compatibility. These settings belong in the server configuration, not the request body.

##### Local diagnostics without a restart

From the Server or Store distribution directory, use JDK 17 and the OS account that owns the service process:

```bash
bin/arthas.sh
```

The helper reads `bin/pid`, verifies the running component, and uses the bundled agent offline. It needs no download, configuration edit,
or service restart. When attaching a new agent, it uses loopback telnet port `3658` with HTTP and MCP disabled. For multiple JVMs on one host,
select the process and an available telnet port explicitly:

```bash
bin/arthas.sh --pid 12345 --telnet-port 3659
bin/arthas.sh --pid 12345 --telnet-port 3659 --command version
```

An already active agent retains its existing listener settings; the helper cannot rebind it or disable its HTTP listener.
For an agent started through the Server API, connect with `bin/arthas.sh --telnet-port 8562` (or the configured telnet port).
To switch deliberately to the helper's defaults, stop the diagnostic agent on its current port, then attach again:

```bash
bin/arthas.sh --telnet-port 8562 --command stop
bin/arthas.sh
```

This stops only Arthas and does not restart the service JVM.

Replace `12345` with the target component's PID. The JDK's `java`, `jar`, and `jcmd` tools must be available. `quit` disconnects the client;
`stop` stops the diagnostic agent without stopping the service. The helper retains agent files in the user's private cache while the JVM may use them.
Arthas can execute powerful JVM operations; OS access to the service account remains a privileged operation.
