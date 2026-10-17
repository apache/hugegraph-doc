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

Starting with HugeGraph 1.8.0, Server and Store bundle Arthas 4.1.5 (PD does not embed an Arthas agent).
You can attach it to a running JVM for live troubleshooting via the local script or the administrator HTTP endpoint.

> [!IMPORTANT]
> **Diagnostic Access**
> - **Local by Default**: Arthas defaults to `127.0.0.1`. Administrators may explicitly bind another valid address, including `0.0.0.0`.
> - **Native Authentication Recommended**: Enable Arthas native authentication, especially before exposing diagnostic ports beyond loopback.
>   HugeGraph administrator authentication protects activation only. For API credentials, set native `-Darthas.username=...` and `-Darthas.password=...`
>   on the Server JVM and restart; these are not REST configuration keys. Without native credentials, a specific non-loopback bind has no login.
>   Native defaults bypass authentication for clients from `127.0.0.1`, including other OS users or containers in the same Pod, even with credentials.
>   Set `-Darthas.localConnectionNonAuth=false` on the service JVM and restart to disable this bypass. Restrict host, Pod and port-forward access
>   to trusted operators. Limit firewall rules, port mappings and forwarding; wildcard listeners may accept IPv4 and IPv6 depending on OS/JVM settings.
>   The local helper stops Arthas when it exits; API-only activation still requires an explicit `stop`.
> - **Administrator Privilege**: HTTP API activation requires authentication to be enabled on Server with administrator privileges;
>   requests without authentication enabled return `403`.
> - **Offline Local Diagnostics**: For routine troubleshooting, run `bin/arthas.sh` on the host as the service OS user without restarting
>   the JVM or editing configuration.

| Deployment | Recommended Activation | Access & Permissions |
|------------|------------------------|----------------------|
| Server ([auth](/docs/config/config-authentication/)) | `PUT /arthas` or `bin/arthas.sh` | Admin HTTP access; helper requires service OS user |
| Server (auth disabled) | Local helper `bin/arthas.sh` | HTTP activation returns `403` |
| Store | Local helper `bin/arthas.sh` | `GET /v1/arthasstart` is disabled and returns `403` |

##### Activation & Diagnostics

```bash {tab="Local Diagnostics (Single Instance)"}
# Run on the host as the service OS user (uses bundled agent offline, no restart needed)
bin/arthas.sh
```

```bash {tab="Multi-Instance on Host"}
# Explicitly specify target JVM PID and a custom telnet port
bin/arthas.sh --pid <PID> --telnet-port 3659
```

```bash {tab="Administrator HTTP Activation"}
# 1. Invoke REST API to attach diagnostic agent (requires Server authentication; enter admin password)
curl --user admin -X PUT http://127.0.0.1:8080/arthas

# 2. On success, returns applied configuration (default ports 8562/8561 on 127.0.0.1)
# 3. Connect to the active agent using the local helper
bin/arthas.sh --telnet-port 8562
```

To exit diagnostics, enter `quit` or `stop`; the helper automatically stops Arthas when the session ends, while the service JVM keeps running.

The helper reads `bin/pid` by default and requires JDK 17. Both distributions include the agent files in `lib/arthas`, so no download,
runtime extraction, or persistent user cache is needed. For a newly activated agent, telnet defaults to `127.0.0.1:3658`; HTTP, MCP,
and tunnel connections are disabled. Interactive mode requires a terminal. For pipes, scripts, or `docker exec` without `-it`,
use `bin/arthas.sh --command version` instead.

The helper automatically stops Arthas when the client exits, including after `--command` completes or `quit`, and handles `INT`, `TERM`,
and `HUP` for cleanup. `SIGKILL` prevents cleanup; verify the agent is stopped after a forced termination. This does not change the
lifecycle of an agent activated only through the HTTP API.
Avoid concurrent helper sessions: exiting one stops the shared agent and all its diagnostic sessions. Connecting through the helper
also applies this cleanup to an agent previously activated through the API.

For [native Arthas authentication](https://arthas.aliyun.com/en/doc/auth.html), pass the agent's own credentials:

```bash
bin/arthas.sh --target-ip 0.0.0.0 \
    --username diagnostics --password '<arthas-password>'
```

Use single-line credentials; printable ASCII avoids the bundled Arthas 4.1.5 telnet client's Unicode limitation.
Password-only use defaults to username `arthas`. These credentials are separate from HugeGraph accounts.
The helper uses them for `--command` and exit cleanup automatically.
For interactive diagnosis, if prompted, enter `auth --username diagnostics <arthas-password>` in the Arthas console.
When reusing an existing agent, provide its existing credentials; the options do not change them.
Password arguments may appear in shell history and process listings; handle them on a trusted host.
With `--username` alone, native Arthas generates a password in the target JVM's Arthas log. Supply `--password` for authenticated batch commands and cleanup.
If cleanup fails, the helper returns nonzero and the agent may remain running; use the logged password with native `auth`, then `stop`, to close it.

Authentication is optional and follows Arthas defaults. `arthas.localConnectionNonAuth=true` permits connections from `127.0.0.1` to skip authentication.
The helper uses a private configuration, so editing `lib/arthas/arthas.properties` does not configure it; if needed, it honors the target JVM property
`-Darthas.localConnectionNonAuth=false` after restarting that JVM. When binding `0.0.0.0` or `::` without an explicit password, Arthas 4.1.5
creates a password and prints it in the target JVM output and Arthas log. Supplying credentials explicitly is more convenient for remote use and cleanup.
Authentication does not encrypt ordinary telnet or HTTP traffic; use a protected network or encrypted transport for remote access.

No commands are disabled by default. Administrators may optionally configure a comma-separated list such as `jad,mc`.
Before reusing an API-started agent, leave `session` and `stop` out of `arthas.disabled_commands` (or its legacy alias).
`session` verifies the target PID; `stop` closes Arthas without stopping the service JVM. Existing configurations remain accepted,
but failed PID verification or listener cleanup makes the helper print an error and exit nonzero; the agent may remain running.
To recover from an agent with `stop` disabled, remove that restriction and restart the service before activating Arthas again.
Newly attached local agents keep both commands available.

> [!TIP]
> Official Server (including HStore) and Store images bundle JDK 17. In container environments, you can run the same
> helper inside the container as the service OS user: `docker exec -it <container> bin/arthas.sh` without extra JDK
> installation or diagnostic port mappings.

An already active agent retains its listener settings. Connect on its current telnet port; the helper does not rebind it or disable an
existing HTTP listener. Supply the bind address with `--target-ip`, for example
`bin/arthas.sh --target-ip ::1 --telnet-port 8562 --command version` or `bin/arthas.sh --target-ip 0.0.0.0`.
The default remains `127.0.0.1`; `localhost` maps to `127.0.0.1`. For wildcard binds `0.0.0.0` and `::`, the helper connects and cleans up
through `127.0.0.1` for either wildcard. A wildcard listener may accept both IPv4 and IPv6 depending on OS/JVM settings; firewall both.
Remote clients use the host's actual reachable address. Existing agents retain their listener
and authentication settings; helper options cannot reconfigure them.
To switch from the Server API defaults to the local helper defaults, stop only Arthas and attach again:

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
    "arthas.disabledCommands": ""
}
```

> [!NOTE]
> [Configuration options](/docs/config/config-option/) use canonical snake_case names: `arthas.telnet_port`,
> `arthas.http_port`, `arthas.ip`, and `arthas.disabled_commands`. Legacy camelCase aliases remain supported
> for backward compatibility; explicit snake_case settings take precedence (see
> [upgrade note](/docs/config/config-guide/#3-rest-serverproperties)). The response preserves Arthas agent
> key names for client compatibility.
