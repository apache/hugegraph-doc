---
title: "HugeGraph 内置用户权限与扩展权限配置及使用"
linkTitle: "权限配置"
weight: 3
search_keywords: [HugeGraph 认证, 权限配置, StandardAuthenticator]
search_boost: 1.7
---

### 概述

HugeGraph 内置 `StandardAuthenticator`，支持多用户认证和基于“用户、用户组、操作、资源”的权限控制。

`StandardAuthenticator` 模式的几个核心设计：
- 初始化时创建超级管理员 (`admin`) 用户，后续通过超级管理员创建其它用户，新创建的用户被分配足够权限后，可以创建或管理更多的用户
- 支持动态创建用户、用户组、资源，支持动态分配或取消权限
- 用户可以属于一个或多个用户组，每个用户组可以拥有对任意个资源的操作权限，操作类型包括：读、写、删除、执行等种类
- "资源" 描述了图数据库中的数据，比如符合某一类条件的顶点，每一个资源包括 `type`、`label`、`properties`三个要素，共有 18 种类型、任意 label、任意 properties 可组合形成的资源，一个资源的内部条件是且关系，多个资源之间的条件是或关系

举例说明：

```java
// 场景：某用户只有北京地区的数据读取权限
user(name=xx) -belong-> group(name=xx) -access(read)-> target(graph=graph1, resource={label: person, city: Beijing})
```

### 配置用户认证

HugeGraph 目前默认**未启用**用户认证功能，需通过修改配置文件来启用该功能。

> ⚠️ **SEC 提醒：图查询语言 (Gremlin/Cypher) 的安全性**
>
> 鉴于图查询语言的灵活性可能带来的潜在系统安全隐患，不要把 Gremlin、Cypher 等查询接口直接暴露到公网。生产环境应同时启用[鉴权](/cn/docs/config/config-authentication/)、IP 白名单和审计日志，并通过 [Docker 或 Kubernetes](/cn/docs/quickstart/hugegraph/hugegraph-server/#31-使用-docker-容器-便于测试) 隔离 Server 进程。

`StandardAuthenticator` 支持多用户认证和细粒度权限控制。也可以实现 `HugeAuthenticator` 接口来接入已有的用户系统。

用户认证使用 [HTTP Basic Authentication](https://zh.wikipedia.org/wiki/HTTP%E5%9F%BA%E6%9C%AC%E8%AE%A4%E8%AF%81)。`Basic` 后面的值是 `用户名:密码` 的 Base64 编码。使用 curl 时可直接通过 `-u` 传入凭据：

```bash
curl -u 'admin:<password>' \
  http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
```

Basic Authentication 只对 `用户名:密码` 做 Base64 编码，不会加密凭据。通过 HTTP 发送时应使用 HTTPS；相关设置见 [HTTPS 配置](config-https)。

**警告**：在 1.5.0 之前版本的 HugeGraph-Server 在鉴权模式下存在 JWT 相关的安全隐患，请务必使用新版本或自行修改 JWT token 的 secretKey。

`auth.token_secret` 由认证数据图的配置读取。默认认证图名为 `hugegraph`，因此配置文件通常是
`conf/graphs/hugegraph.properties`；如果修改了 `auth.graph_store`，应改为对应图的 properties 文件。
源码默认会生成 32 个随机字节并以 Base64 编码，但该值不会写回配置文件；重启后或多个 Server 节点之间
无法依赖各自生成的默认值保持一致。若需要令已有 token 在重启后继续有效，或让多个节点验证同一 token，
请为认证图显式配置同一个强随机密钥：

Server 将配置字符串按 UTF-8 编码后交给 JJWT 的 HS256 签名器，密钥至少需要 32 字节；这是字节长度要求，不代表任意 32 字符串都具有足够随机性。下面的命令在本机生成 32 个随机字节并以 Base64 编码。

```properties
# 在每个 Server 节点的认证图配置中填写同一个值
auth.token_secret=<本机生成的密钥>
```

可在本机终端生成密钥，再通过安全方式填入认证图配置；不要把实际密钥提交到代码库或公开日志：

```bash
openssl rand -base64 32
```

由于默认值在每次启动时随机生成，当 token 需要在重启后继续有效、或者需要被多个服务节点接受时，必须显式配置该项。token 的有效期由
`auth.token_expire` 决定，默认为 86400 秒。

`auth.token_expire` 和 `auth.token_secret` 都属于 `auth.graph_store` 指定的认证数据图配置；`rest-server.properties` 中的同名项不会覆盖认证图配置。

#### StandardAuthenticator 模式
`StandardAuthenticator`模式是通过在数据库后端存储用户信息来支持用户认证和权限控制，该实现基于数据库存储的用户的名称与密码进行认证（密码已被加密），基于用户的角色来细粒度控制用户权限。下面是具体的配置流程（重启服务生效）：

在配置文件`gremlin-server.yaml`中配置`authenticator`及其`rest-server`文件路径：

```yaml
authentication: {
  authenticator: org.apache.hugegraph.auth.StandardAuthenticator,
  authenticationHandler: org.apache.hugegraph.auth.WsAndHttpBasicAuthHandler,
  config: {tokens: conf/rest-server.properties}
}
```

在 `rest-server.properties` 中配置认证器和权限数据存储图：

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

其中，`graph_store`配置项是指使用哪一个图来存储用户信息，如果存在多个图的话，选取任意一个均可。

在配置文件`hugegraph{n}.properties`中配置`gremlin.graph`信息：

```properties
gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy
```

权限 API 的调用方式见 [Authentication API](/cn/docs/clients/restful-api/auth/) 文档。

### 自定义用户认证系统

如果需要支持更加灵活的用户系统，可自定义 authenticator 进行扩展，自定义 authenticator 实现接口`org.apache.hugegraph.auth.HugeAuthenticator`即可，然后修改配置文件中`authenticator`配置项指向该实现。

### 基于鉴权模式启动

首次执行 `init-store.sh` 时，如果尚未创建 `admin` 用户，命令会要求输入管理员密码。对于已经初始化的持久化后端，`init-store.sh` 会补充认证所需的系统信息，无需删除原有图数据。

```bash
# stop the hugeGraph firstly
bin/stop-hugegraph.sh

# 初始化认证系统信息；已有后端数据会被保留
bin/init-store.sh

# start hugeGraph again
bin/start-hugegraph.sh

```

### 使用 Docker 时开启鉴权模式

对于镜像 `hugegraph/hugegraph` 大于等于 `1.2.0` 的版本，我们可以在启动 `docker` 镜像的同时开启鉴权模式

具体做法如下：

#### 1. 采用 docker run

在 `docker run` 中添加环境变量 `PASSWORD=xxx`（密码可以自由设置）即可开启鉴权模式：：

```bash
docker run -itd -e PASSWORD=xxx --name=server -p 8080:8080 hugegraph/hugegraph:1.7.0
```

#### 2. 采用 docker-compose

使用 `docker-compose` 在环境变量中设置 `PASSWORD=xxx`即可

```yaml
version: '3'
services:
  server:
    image: hugegraph/hugegraph:1.7.0
    container_name: server
    ports:
      - 8080:8080
    environment:
      - PASSWORD=xxx
```

#### 3. 进入容器后重新开启鉴权模式

首先进入容器：

```bash
docker exec -it server bash
# 用于快速修改配置, 修改前的文件被保存在conf-bak文件夹下
bin/enable-auth.sh
```

之后参照 [基于鉴权模式启动](#基于鉴权模式启动) 即可
