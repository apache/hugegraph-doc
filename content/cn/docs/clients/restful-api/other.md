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

自 HugeGraph 1.8.0 起，Server 和 Store 统一内置 Arthas 4.1.5（PD 未内置 Arthas 代理）。可通过本地脚本或管理员 HTTP 接口挂载到正在运行的 JVM 进行在线诊断。

> [!IMPORTANT]
> **诊断访问说明**
> - **默认本地监听**：Arthas 默认监听 `127.0.0.1`；管理员可显式配置其他有效地址，包括 `0.0.0.0`。
> - **推荐原生认证**：建议开启 Arthas 原生认证，尤其是在对外暴露诊断端口前。HugeGraph 管理员鉴权只保护激活入口。
>   未启用 Arthas 认证时，所有网络可达的客户端均可执行命令，包括其他 OS 用户或同 Pod 内的容器。
>   管理员负责防火墙、端口映射及转发访问控制。本地脚本退出时会停止 Arthas；仅通过 HTTP API 激活时，仍需显式执行 `stop`。
> - **管理员权限限制**：HTTP API 激活要求 Server 已开启鉴权，且必须具备管理员权限；未开启鉴权时直接返回 `403`。
> - **免重启本地诊断**：推荐直接在主机上使用服务进程所属的 OS 用户运行 `bin/arthas.sh`，无需修改配置或重启 JVM。

| 部署方式 | 推荐激活方式 | 权限与访问说明 |
|----------|--------------|----------------|
| Server（已[开启认证](/cn/docs/config/config-authentication/)） | 管理员调用 `PUT /arthas` 或运行 `bin/arthas.sh` | 仅管理员账号可调用 HTTP 接口；本地脚本需服务 OS 用户权限 |
| Server（未开启认证） | 本地脚本 `bin/arthas.sh` | HTTP 接口直接返回 `403`（包括 loopback 与代理请求） |
| Store | 本地脚本 `bin/arthas.sh` | `GET /v1/arthasstart` 已禁用并返回 `403`（Store 无对应管理员鉴权机制） |

##### 激活与使用方式

```bash {tab="本地免重启诊断 (单实例)"}
# 以服务进程所属的 OS 用户执行（离线使用包内代理，无需重启）
bin/arthas.sh
```

```bash {tab="同机多实例诊断"}
# 显式指定目标 JVM 进程 PID 及自定义 telnet 端口
bin/arthas.sh --pid <PID> --telnet-port 3659
```

```bash {tab="管理员 HTTP API 激活"}
# 1. 调用 REST API 挂载诊断代理（需已开启 Server 认证，输入管理员密码）
curl --user admin -X PUT http://127.0.0.1:8080/arthas

# 2. 成功后返回生效配置（默认端口 8562/8561，监听 127.0.0.1）
# 3. 使用本地脚本连接已有代理
bin/arthas.sh --telnet-port 8562
```

退出诊断：在终端输入 `quit` 或 `stop` 即可；脚本会在会话结束时自动清理并停止 Arthas 代理，服务 JVM 持续运行。

脚本默认读取 `bin/pid`，需要 JDK 17。两个发行包均在 `lib/arthas` 内提供代理文件，无需下载、运行时解压或持久化的用户缓存。
新挂载代理时，telnet 默认监听 `127.0.0.1:3658`，HTTP、MCP 和 tunnel 连接均禁用。
交互模式需要终端。在管道、脚本或未使用 `-it` 的 `docker exec` 中，请改用 `bin/arthas.sh --command version`。

本地脚本会在客户端退出时自动停止 Arthas，包括 `--command` 执行完成或输入 `quit`，并处理 `INT`、`TERM`、`HUP` 信号以完成清理。
`SIGKILL` 会阻止清理，强制终止后需确认代理已停止。仅通过 HTTP API 激活代理的生命周期不受此机制影响。
请勿并发运行多个脚本会话，退出任一会话都会停止共享代理及其全部诊断会话。脚本连接 API 已激活的代理后，也会在退出时停止该代理。

可通过脚本传递 [Arthas 原生认证](https://arthas.aliyun.com/doc/auth.html)凭据：

```bash
bin/arthas.sh --target-ip 0.0.0.0 \
    --username diagnostics --password '<arthas-password>'
```

凭据需为单行；建议使用可打印 ASCII，避免包内 Arthas 4.1.5 telnet 客户端的 Unicode 限制。仅传密码时用户名默认为 `arthas`。
这组凭据独立于 HugeGraph 账号，脚本会自动将其用于 `--command` 和退出清理。
交互诊断时若提示需要认证，请在 Arthas 控制台输入 `auth --username diagnostics <arthas-password>`。
复用已有代理时应提供其原有凭据，脚本参数不会修改它。密码参数可能出现在 shell 历史及进程列表中，请在可信主机上妥善处理。
仅提供 `--username` 时，原生 Arthas 会生成密码并记录于目标 JVM 的 Arthas 日志。建议提供 `--password`，方便认证批处理及自动清理。
清理失败时脚本返回非零，代理可能仍在运行；请使用日志中的密码通过原生 `auth` 认证，再执行 `stop` 关闭代理。

认证保持可选，并遵循 Arthas 默认行为。`arthas.localConnectionNonAuth=true` 允许来自 `127.0.0.1` 的连接免认证。
脚本使用独立配置，编辑 `lib/arthas/arthas.properties` 不会配置本脚本；如有需要，可在目标 JVM 设置 `-Darthas.localConnectionNonAuth=false`。
未显式提供密码且监听 `0.0.0.0` 时，Arthas 4.1.5 会生成密码并打印至目标 JVM 输出及 Arthas 日志；显式提供凭据更方便远程使用和清理。
认证不会加密普通 telnet 或 HTTP 流量；远程访问请使用受保护网络或加密传输。

默认不禁用任何命令，管理员可按需配置以逗号分隔的列表，例如 `jad,mc`。
复用 API 已激活的代理前，请勿在 `arthas.disabled_commands`（或旧别名）中禁用 `session` 和 `stop`。
`session` 用于确认目标 PID，`stop` 只关闭 Arthas，不会停止服务 JVM。已有配置继续兼容，但无法确认 PID 或关闭监听时，
脚本会打印错误并以非零状态退出，代理可能仍在运行。若已有代理禁用了 `stop`，请移除该限制并重启服务，再重新激活 Arthas。
本地脚本新激活的代理始终保留这两个命令。

> [!TIP]
> 官方 Server（包括 HStore）与 Store 镜像均内置 JDK 17。在容器环境中，可直接以服务 OS 用户运行同一脚本：
> `docker exec -it <container> bin/arthas.sh`，无需额外安装 JDK 或映射诊断端口。

已有代理保留当前监听配置。请使用原 telnet 端口连接，脚本不会重新绑定端口或关闭已有的 HTTP 监听。
通过 `--target-ip` 指定监听地址，例如 `bin/arthas.sh --target-ip ::1 --telnet-port 8562 --command version`，
或使用 `bin/arthas.sh --target-ip 0.0.0.0`。默认仍为 `127.0.0.1`，`localhost` 映射为 `127.0.0.1`。
使用通配监听地址 `0.0.0.0` 或 `::` 时，脚本分别通过 `127.0.0.1` 或 `::1` 连接及清理；远程客户端连接主机实际可达的地址。
已有代理保留当前监听和认证配置，脚本参数不会重新配置它。
如需从 Server API 默认配置切换为本地脚本默认配置，先只停止 Arthas，再重新挂载：

```bash
bin/arthas.sh --telnet-port 8562 --command stop
bin/arthas.sh
```

若配置了其他 telnet 端口，请将 `8562` 替换为实际值。服务 JVM 持续运行，无需重启。

##### HTTP 响应体示例

成功激活后返回 HTTP `200` 及生效配置：

```json
{
    "arthas.telnetPort": "8562",
    "arthas.httpPort": "8561",
    "arthas.ip": "127.0.0.1",
    "arthas.disabledCommands": ""
}
```

> [!NOTE]
> [配置项](/cn/docs/config/config-option/) 采用规范的 snake_case 命名：`arthas.telnet_port`、`arthas.http_port`、`arthas.ip` 与 `arthas.disabled_commands`。
> 旧版 camelCase 命名仍作为兼容回退；显式配置的 snake_case 选项优先（参见[配置指南升级说明](/cn/docs/config/config-guide/#3-rest-serverproperties)）。
> 响应内容保持 Arthas 代理的原始键名以便兼容现有客户端。
