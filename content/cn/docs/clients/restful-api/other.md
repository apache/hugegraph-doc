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
> **安全诊断要求**
> - **仅监听本地 Loopback**：Arthas 默认且仅允许监听 `127.0.0.1`。Server 拒绝非 loopback 地址（如 `0.0.0.0`），严禁通过反向代理或容器端口映射对外暴露。
> - **管理员权限限制**：HTTP API 激活要求 Server 已开启鉴权，且必须具备管理员权限；未开启鉴权时直接返回 `403`。
> - **免重启本地诊断**：推荐直接在主机上使用服务进程所属的 OS 用户运行 `bin/arthas.sh`，无需修改配置或重启 JVM。

| 部署方式 | 推荐激活方式 | 权限与访问说明 |
|----------|--------------|----------------|
| Server（已[开启认证](/cn/docs/config/config-authentication/)） | 管理员调用 `PUT /arthas` 或运行 `bin/arthas.sh` | 仅管理员账号可调用 HTTP 接口；本地脚本需服务 OS 用户权限 |
| Server（未开启认证） | 本地脚本 `bin/arthas.sh` | HTTP 接口直接返回 `403`（包括 loopback 与代理请求） |
| Store | 本地脚本 `bin/arthas.sh` | `GET /v1/arthasstart` 已禁用并返回 `403`（Store 无对应管理员鉴权机制） |

##### 激活与使用方式

```bash {tab="本地免重启诊断 (推荐)"}
# 1. 以运行服务进程的 OS 用户在安装根目录下执行（离线使用包内代理，无需下载或重启）
bin/arthas.sh

# 2. 同一主机运行多个实例时，可显式指定进程 PID 与端口
bin/arthas.sh --pid <PID> --telnet-port 3659

# 3. 退出诊断：终端内输入 quit 仅断开客户端连接；输入 stop 卸载诊断代理（不影响服务 JVM）
```

```bash {tab="管理员 HTTP API 激活"}
# 1. 调用 REST API 激活诊断（Server 需已开启认证，输入管理员密码）
curl --user admin -X PUT http://127.0.0.1:8080/arthas

# 2. 成功后返回生效的配置（默认端口 8562/8561，监听 127.0.0.1）
# 3. 使用本地脚本连接已有代理
bin/arthas.sh --telnet-port 8562
```

##### HTTP 响应体示例

成功激活后返回 HTTP `200` 及生效配置：

```json
{
    "arthas.telnetPort": "8562",
    "arthas.httpPort": "8561",
    "arthas.ip": "127.0.0.1",
    "arthas.disabledCommands": "jad"
}
```

> [!NOTE]
> [配置项](/cn/docs/config/config-option/) 采用规范的 snake_case 命名：`arthas.telnet_port`、`arthas.http_port`、`arthas.ip` 与 `arthas.disabled_commands`。
> 旧版 camelCase 命名仍作为兼容回退；显式配置的 snake_case 选项优先。响应内容保持 Arthas 代理的原始键名以便兼容现有客户端。
