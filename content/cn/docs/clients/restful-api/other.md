---
title: "Other API"
linkTitle: "Other"
weight: 18
description: "Other（其他接口）REST 接口:提供版本查询、API 列表、异常堆栈开关、IP 白名单和 Arthas 诊断代理等辅助功能。"
---

### 11.1 Other

#### 11.1.1 查看HugeGraph的版本信息

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

#### 11.1.2 查看服务的概要信息

返回服务名、内核版本、文档地址以及当前节点注册的 API 分组。

##### Method & Url

```text
GET http://localhost:8080/
```

##### Response Status

```json
200
```

##### Response Body

`swagger_ui` 由 `restserver.url` 拼接得到，`apis` 是当前节点注册的 API 分组，按名称排序。

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

#### 11.1.3 列出服务的全部 API

按 API 分组和资源类列出所有已注册的接口方法，每条记录包含 url、HTTP 方法，以及查询参数的类型和默认值。

##### Method & Url

```text
GET http://localhost:8080/apis
```

##### Response Status

```json
200
```

##### Response Body

返回内容较长，下面的片段展示了它的结构：

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

#### 11.1.4 查看和切换异常堆栈开关

服务返回的错误信息中是否带上 `exception` 和 `cause` 等异常堆栈字段，由 `exception.allow_trace` 配置项（默认 `true`）决定。下面的接口是一个节点级别的运行期覆盖开关：打开时无论配置项取值如何都会带上堆栈。`GET` 返回的是该覆盖开关的状态，初始为 `false`。

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

#### 11.1.5 管理 IP 白名单，**该操作需要管理员权限**

白名单只在开关打开时生效，参见 `white_ip.status` 配置项（默认 `disable`）。

##### 查看白名单

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

##### 向白名单添加或删除 IP

##### Params

- ips: IPv4 地址列表
- action: `load` 表示添加，`remove` 表示删除

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

`existed_ips` 是已经在白名单中的地址，`added_ips` 是新增的地址，`illegal_ips` 只在存在非法 IPv4 地址时返回。`action=remove` 时返回的是 `removed_ips` 和 `non_existed_ips`。

```json
{
    "existed_ips": [],
    "added_ips": [
        "10.0.0.1",
        "10.0.0.2"
    ]
}
```

##### 启用或关闭白名单

##### Params

- status: `true` 表示启用，`false` 表示关闭

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

#### 11.1.6 启动 Arthas 诊断代理

以下行为面向包含 [Server PR #2945](https://github.com/apache/hugegraph/pull/2945) 的下一版本，旧版本的激活方式和监听默认值有所不同。

[Arthas](https://arthas.aliyun.com/) 可挂载到正在运行的 JVM 上进行诊断。Server 和 Store 统一内置 Arthas 4.1.5，PD 未内置 Arthas 代理。
根据部署方式选择入口：

| 部署方式 | 激活方式 |
|----------|----------|
| Server 已[开启认证](/cn/docs/config/config-authentication/) | 已认证的管理员可直接调用 `PUT /arthas`。 |
| Server 未开启认证 | 以服务进程所属的 OS 用户在主机上运行 `bin/arthas.sh`。HTTP 激活返回 `403`，loopback 或代理请求也不例外。 |
| Store | 使用相同的本地脚本。`GET /v1/arthasstart` 返回 `403`，Store 此接口没有管理员认证机制。 |

Arthas 仅监听 loopback。Server HTTP 激活时会拒绝非 loopback 地址，包括 `0.0.0.0`，并禁用 MCP。
不要通过反向代理或容器端口映射暴露诊断端口。远程排查时，通过 SSH 登录主机后运行本地脚本。

##### 管理员通过 HTTP 激活

Server 已配置认证时，无需额外开启 Arthas 开关或重启 JVM。使用管理员账号调用：

```bash
curl --user admin -X PUT http://127.0.0.1:8080/arthas
```

命令会提示输入密码。已认证的非管理员返回 `403`；缺少凭据或凭据无效时，按 Server 配置的认证机制处理。
Server 未开启认证时，此接口始终返回 `403`，不会挂载代理。

成功请求返回 HTTP `200` 和生效的 Arthas 配置：

```json
{
    "arthas.telnetPort": "8562",
    "arthas.httpPort": "8561",
    "arthas.ip": "127.0.0.1",
    "arthas.disabledCommands": "jad"
}
```

[配置项](/cn/docs/config/config-option/) 使用 `arthas.telnet_port`、`arthas.http_port`、`arthas.ip` 和 `arthas.disabled_commands`。
旧 camelCase 名称仍兼容；显式设置的 snake_case 值优先，两种名称的值冲突时会输出警告。响应保持 Arthas 代理的键名，以兼容已有客户端。
这些选项写在服务端配置中，不从请求体传入。

##### 无需重启的本地诊断

在 Server 或 Store 发行包目录下，使用 JDK 17 和服务进程所属的 OS 用户运行：

```bash
bin/arthas.sh
```

脚本读取 `bin/pid`，校验目标组件正在运行，并离线使用发行包内的代理，无需下载、修改配置或重启服务。
新激活代理时，脚本固定监听 loopback，telnet 端口默认为 `3658`，HTTP 和 MCP 均禁用。同一主机运行多个 JVM 时，可显式指定目标进程和空闲 telnet 端口：

```bash
bin/arthas.sh --pid 12345 --telnet-port 3659
bin/arthas.sh --pid 12345 --telnet-port 3659 --command version
```

已经激活的代理会保留现有监听配置，脚本无法重新绑定端口或关闭它已有的 HTTP 监听。
如果代理通过 Server API 激活，使用 `bin/arthas.sh --telnet-port 8562` 连接，或改为配置的 telnet 端口。
如需切换为本地脚本的默认配置，先在当前端口停止诊断代理，再重新挂载：

```bash
bin/arthas.sh --telnet-port 8562 --command stop
bin/arthas.sh
```

这只停止 Arthas，不会重启服务 JVM。

将 `12345` 替换为目标组件的 PID。需要可用的 JDK `java`、`jar` 和 `jcmd` 工具。`quit` 仅断开客户端，`stop` 停止诊断代理而不停止服务。
脚本会在用户私有缓存中保留 JVM 仍可能使用的代理文件。Arthas 可执行高权限 JVM 操作，服务账号的 OS 访问权限仍应按管理员权限管理。
