---
title: "HugeGraph 内置用户权限与扩展权限配置及使用"
linkTitle: "权限配置"
weight: 3
search_keywords: [HugeGraph 认证, 权限配置, StandardAuthenticator]
search_boost: 1.7
---

### 概述

HugeGraph 内置 `StandardAuthenticator`，支持多用户认证和基于“用户、用户组、操作、资源”的权限控制。

初始化会创建超级管理员 `admin`。管理员可创建用户、用户组及资源，并分配或撤销权限。用户通过所属组获得读、写、删除和执行等权限。

资源用 `type`、`label` 和 `properties` 描述可访问的数据。同一资源中的条件需同时满足，多个资源之间满足其一即可。

下面的关系表示用户仅可读取北京地区的数据。

```java
// 场景：某用户只有北京地区的数据读取权限
user(name=xx) -belong-> group(name=xx) -access(read)-> target(graph=graph1, resource={label: person, city: Beijing})
```

### 配置用户认证

HugeGraph 目前默认**未启用**用户认证功能，需通过修改配置文件来启用该功能。

> [!WARNING]
> **生产环境必须启用鉴权**
>
> HugeGraph 默认不启用用户认证。生产环境必须启用认证与授权、设置非默认强管理员密码、启用并维护 Server IP 白名单，并按最小权限为用户授权；不得将 Gremlin、Cypher 等查询接口直接暴露到公网。Server 标准配置会将鉴权代理记录写入
`audit-*.log`，部署时必须保留并限制这些日志的读取权限。`auth.audit_log_rate` 只限制每用户的日志输出速率，不是审计日志的启停开关。

`StandardAuthenticator` 支持多用户认证和细粒度权限控制。也可以实现 `HugeAuthenticator` 接口来接入已有的用户系统。

用户认证使用 [HTTP Basic Authentication](https://zh.wikipedia.org/wiki/HTTP%E5%9F%BA%E6%9C%AC%E8%AE%A4%E8%AF%81)。`Basic` 后面的值是 `用户名:密码` 的 Base64 编码。使用 curl 时可直接通过
`-u` 传入凭据。

```bash
curl -u 'admin:<password>' \
  http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
```

> [!WARNING]
> **保护 Basic Authentication 凭据**
>
> Basic Authentication 只对 `用户名:密码` 做 Base64 编码，不会加密凭据。通过网络发送时必须使用 HTTPS；相关设置见 [HTTPS 配置](config-https)。

> [!WARNING]
> **旧版本 JWT 风险**
>
> HugeGraph-Server 1.5.0 之前的版本在鉴权模式下存在 JWT 相关安全隐患。使用受影响版本时必须升级，或按该版本要求修改 JWT token 的 `secretKey`。

`auth.token_secret` 由认证数据图的配置读取。默认认证图名为 `hugegraph`，因此配置文件通常是 `conf/graphs/hugegraph.properties`；如果修改了 `auth.graph_store`，应改为对应图的 properties 文件。
核心配置默认会生成 32 个随机字节并以 Base64 编码，该默认值不会自行写回配置文件；重启后或多个 Server 节点之间无法依赖各自生成的默认值保持一致。若需要令已有 token 在重启后继续有效，或让多个节点验证同一 token，请为认证图显式配置同一个强随机密钥。

Server 将配置字符串按 UTF-8 编码后交给 JJWT 的 HS256 签名器，密钥至少需要 32 字节；这是字节长度要求，不代表任意 32 字符串都具有足够随机性。下面的命令在本机生成 32 个随机字节并以 Base64 编码。

```properties
# 在每个 Server 节点的认证图配置中填写同一个值
auth.token_secret=<本机生成的密钥>
```

可在本机终端生成密钥，再通过安全方式填入认证图配置；不要把实际密钥提交到代码库或公开日志。

```bash
openssl rand -base64 32
```

token 的有效期由 `auth.token_expire` 决定，默认为 86400 秒。

`auth.token_expire` 和 `auth.token_secret` 都属于 `auth.graph_store` 指定的认证数据图配置；`rest-server.properties` 中的同名项不会覆盖认证图配置。

#### StandardAuthenticator 模式
`StandardAuthenticator` 在后端存储用户及密码哈希，并按用户角色控制访问。修改以下三处配置后，按[启动顺序](#基于鉴权模式启动)初始化并重启服务。

在 `conf/gremlin-server.yaml` 中配置认证器及 REST 配置路径。

```yaml
authentication: {
  authenticator: org.apache.hugegraph.auth.StandardAuthenticator,
  authenticationHandler: org.apache.hugegraph.auth.WsAndHttpBasicAuthHandler,
  config: {tokens: conf/rest-server.properties}
}
```

在 `conf/rest-server.properties` 中配置认证器和权限数据存储图。

```properties
auth.authenticator=org.apache.hugegraph.auth.StandardAuthenticator
auth.graph_store=hugegraph
# Server 启动路径首次创建内置 admin 账号时使用，默认值为公开的 pa，生产部署前务必显式设置强密码
# 本地持久化后端首次启用 StandardAuthenticator 时，init-store.sh 会交互式读取密码
#auth.admin_pa=<your-admin-password>

# auth client config
# 如果是分开部署 GraphServer 和 AuthServer，还需要指定下面的配置，地址填写 AuthServer 的 IP:RPC 端口
#auth.remote_url=127.0.0.1:8899,127.0.0.1:8898,127.0.0.1:8897
```

`auth.graph_store` 指定保存认证数据的图，名称必须与 `conf/graphs/` 中的图配置对应。

在每个受保护图的配置文件 `conf/graphs/<graph>.properties` 中设置 `gremlin.graph`。

```properties
gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy
```

权限 API 的调用方式见 [Authentication API](/cn/docs/clients/restful-api/auth/) 文档。

### 自定义用户认证系统

实现 `org.apache.hugegraph.auth.HugeAuthenticator` 接口，再将两处 `authenticator` 配置指向该实现，即可接入已有用户系统。

### 基于鉴权模式启动

下面的顺序适用于本地持久化后端，例如 RocksDB。先完成上面的配置，再初始化认证数据。
HStore/PD 部署的管理员由 PD 启动路径创建，须按该部署的配置设置 `auth.admin_pa`，不要照搬本地后端的交互式初始化流程。

1. **停止 Server。**

   ```bash
   bin/stop-hugegraph.sh
   ```

1. **初始化认证数据。**

   ```bash
   bin/init-store.sh
   ```

   首次创建 `admin` 时，按提示输入强密码。已有图数据会保留；已有 `admin` 时不会重新设置其密码。
   此命令补充后端与认证系统信息，不需要删除原有存储目录。

1. **启动并检查认证。**

   ```bash
   bin/start-hugegraph.sh
   curl -u admin \
     http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
   ```

   curl 会提示输入密码。正确密码应返回 HTTP 200；不带凭据或使用错误密码应返回 HTTP 401。
   启动失败时先检查日志和认证图配置，不要通过清空数据来重试。
{.steps}

### 使用 Docker 时开启鉴权模式

新容器在 Docker run 和 Compose 中选择一种方式。已经运行过的容器直接阅读[既有容器](#3-进入容器后重新开启鉴权模式)。

使用 Docker 部署时，官方镜像支持通过环境变量直接开启鉴权模式（适用于官方 Server 镜像 `/hugegraph-server` 布局）。
将占位符替换为实际镜像标签或 digest：

```bash
export HUGEGRAPH_IMAGE='<image:tag-or-digest>'
read -r -s -p 'Admin password: ' PASSWORD
printf '\n'
export PASSWORD
```

提示输入管理员密码后执行启动命令。为保障凭据安全，请避免将密码以明文形式提交到共享 Compose 文件中。
JWT 密钥仍按[上面的配置](#配置用户认证)持久保存到认证图配置；多节点必须使用同一个值。

#### Docker run {#1-采用-docker-run}

创建一个新容器，并仅向本机开放 REST 端口。

```bash
docker run -d --name server \
  -p 127.0.0.1:8080:8080 \
  -e PASSWORD \
  "$HUGEGRAPH_IMAGE"
unset PASSWORD
```

入口脚本完成认证配置和首次初始化后启动 Server。接着阅读[检查认证结果](#检查认证结果)。

#### Docker Compose {#2-采用-docker-compose}

将下面的内容保存为 `compose.yaml`。必填变量缺失时，Compose 会报错，避免意外启动无认证服务。
在同一终端中启动服务。

```yaml
services:
  server:
    image: ${HUGEGRAPH_IMAGE:?Set HUGEGRAPH_IMAGE}
    container_name: server
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      PASSWORD: ${PASSWORD:?Set PASSWORD}
```

```bash
docker compose up -d
unset PASSWORD
```

以后重新创建容器前，需要重新设置这些变量。保留已有数据卷，并按部署要求持久保存配置。
接着阅读[检查认证结果](#检查认证结果)。

#### 既有容器 {#3-进入容器后重新开启鉴权模式}

此路径适用于原先未开启认证、使用本地持久化后端的官方 Server 容器。
先备份数据，并确认配置、后端数据及 `conf-bak` 均位于容器挂载的持久卷中。
官方镜像将 `/hugegraph-server` 声明为卷；自定义镜像应先检查挂载位置。
HStore/PD 或外部认证服务使用各自的管理员初始化流程。

1. **停止原容器，使用同一镜像和数据卷打开临时维护容器。**

   ```bash
   SERVER_IMAGE=$(docker inspect --format '{{.Image}}' server)
   docker stop server
   docker run --rm -it --volumes-from server \
     --entrypoint bash "$SERVER_IMAGE"
   ```

   原容器须保持停止，防止两个 JVM 同时打开本地数据库。`--entrypoint bash` 使维护容器只打开终端。

1. **在维护容器内修改配置并初始化。**

   ```bash
   cd /hugegraph-server
   bin/enable-auth.sh
   ```

   `enable-auth.sh` 首次运行时将原配置保存到 `conf-bak`，然后修改默认 `hugegraph` 图和认证配置。
   如果 `conf-bak` 已存在，脚本会跳过修改，须按[StandardAuthenticator 模式](#standardauthenticator-模式)检查三处配置。
   使用其他认证图时也应手动配置对应文件。
   按[上面的配置](#配置用户认证)将强随机 JWT 密钥写入认证图配置，再运行初始化命令。

   ```bash
   bin/init-store.sh
   exit
   ```

   按提示输入管理员密码，确认初始化成功后退出。

1. **在宿主机启动原容器。**

   ```bash
   docker start server
   ```

   不需要删除 `docker/init_complete` 标记。后续 `PASSWORD` 环境变量的变化不会修改已存储的管理员密码。
{.steps}

#### 检查认证结果

等待 Server 启动后，在宿主机执行以下请求验证。`-u admin` 会交互式提示输入密码：

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
curl -sS -o /dev/null -w '%{http_code}\n' -u admin \
  http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
```

未携带凭据的请求预期返回 `401 Unauthorized`，输入正确密码的请求返回 `200 OK`（若输入错误密码则同样返回 `401`）。
注：当前主线版本 URL 包含 `/graphspaces/DEFAULT`，1.7.0 等历史版本请省略 graphspace 前缀（直接使用 `/graphs/hugegraph/...`）。
若未提供凭据仍返回 `200`，说明鉴权未成功启用，请检查配置并重启 Server。
