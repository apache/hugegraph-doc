---
title: "Other API"
linkTitle: "Other"
weight: 18
description: "Other REST API: Provide auxiliary functions such as version query, API listing, exception trace switch, IP allowlist and the Arthas agent."
---

### 11.1 Other

#### 11.1.1 View Version Information of HugeGraph

##### Method & Url

```
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

```
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

```
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

```
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

```
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

```
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

```
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

```
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

Attaches the [Arthas](https://arthas.aliyun.com/en/) agent to the running server process for diagnosis. The ports, the bind IP and the disabled commands are taken from the `arthas.telnetPort`, `arthas.httpPort`, `arthas.ip` and `arthas.disabledCommands` options, see [Config Options](/docs/config/config-option/).

##### Method & Url

```
PUT http://localhost:8080/arthas
```

##### Response Status

```json
200
```

##### Response Body

The applied Arthas configuration is returned:

```json
{
    "arthas.telnetPort": "8562",
    "arthas.httpPort": "8561",
    "arthas.ip": "0.0.0.0",
    "arthas.disabledCommands": "jad"
}
```
