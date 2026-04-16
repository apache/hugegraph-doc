---
title: "HugeGraph 内置用户权限与扩展权限配置及使用"
linkTitle: "权限配置"
weight: 3
---

### 概述

HugeGraph 为了方便不同用户场景下的鉴权使用，目前内置了完备的`StandardAuthenticator`权限模式，支持多用户认证、
以及细粒度的权限访问控制，采用基于“用户 - 用户组 - 操作 - 资源”的 4 层设计，灵活控制用户角色与权限 (支持多 GraphServer)

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
> 出于图查询语言的灵活性可能带来的潜在系统安全隐患，**请避免直接在公网/外网环境暴露任何查询相关接口**。在实际生产部署时，请以此处的 **[鉴权认证体系](/cn/docs/config/config-authentication/)** 结合 **IP 白名单** 为安全双重保障机制，同时建议开启 Audit Log (审计日志) 以精准定位用户执行的具体查询语句。鉴于 Server 的无状态特性，整体架构上强烈推荐采用 **[容器化环境 (Docker/K8s)](/cn/docs/quickstart/hugegraph/hugegraph-server/#31-使用-docker-容器-便于测试)** 部署，以极低成本有效隔离底层系统的安全风险。

目前已内置实现了`StandardAuthenticator`模式，该模式支持多用户认证与细粒度权限控制。此外，开发者可以自定义实现`HugeAuthenticator`接口来对接自身的权限系统。

用户认证方式均采用 [HTTP Basic Authentication](https://zh.wikipedia.org/wiki/HTTP%E5%9F%BA%E6%9C%AC%E8%AE%A4%E8%AF%81) ，简单说就是在发送 HTTP 请求时在 `Authentication` 设置选择 `Basic` 然后输入对应的用户名和密码，对应 HTTP 明文如下所示 :

```http
GET http://localhost:8080/graphs/hugegraph/schema/vertexlabels
Authorization: Basic admin xxxx
```

**警告**：在 1.5.0 之前版本的 HugeGraph-Server 在鉴权模式下存在 JWT 相关的安全隐患，请务必使用新版本或自行修改 JWT token 的 secretKey。

修改方式为在配置文件`rest-server.properties`中重写`auth.token_secret`信息：(1.5.0 后会默认生成随机值则无需配置)

```properties
auth.token_secret=XXXX   #这里为 32 位 String，由 a-z，A-Z 和 0-9 组成
```

也可以通过下面的命令实现：

```shell
RANDOM_STRING=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)
echo "auth.token_secret=${RANDOM_STRING}" >> rest-server.properties
```

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

在配置文件`rest-server.properties`中配置`authenticator`及其`graph_store`信息：

```properties
auth.authenticator=org.apache.hugegraph.auth.StandardAuthenticator
auth.graph_store=hugegraph

# auth client config
# 如果是分开部署 GraphServer 和 AuthServer，还需要指定下面的配置，地址填写 AuthServer 的 IP:RPC 端口
#auth.remote_url=127.0.0.1:8899,127.0.0.1:8898,127.0.0.1:8897
```

其中，`graph_store`配置项是指使用哪一个图来存储用户信息，如果存在多个图的话，选取任意一个均可。

在配置文件`hugegraph{n}.properties`中配置`gremlin.graph`信息：

```properties
gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy
```

然后详细的权限 API 调用和说明请参考 [Authentication-API](/docs/clients/restful-api/auth) 文档。

### 自定义用户认证系统

如果需要支持更加灵活的用户系统，可自定义 authenticator 进行扩展，自定义 authenticator 实现接口`org.apache.hugegraph.auth.HugeAuthenticator`即可，然后修改配置文件中`authenticator`配置项指向该实现。

### 基于鉴权模式启动

在鉴权配置完成后，需在首次执行 `init-store.sh` 时命令行中输入 `admin` 密码 (非 docker 部署模式下)

如果基于 docker 镜像部署或者已经初始化 HugeGraph 并需要转换为鉴权模式，需要删除相关图数据并重新启动 HugeGraph, 若图已有业务数据，暂时**无法直接转换**鉴权模式 (hugegraph 版本 <= 1.2.0) 
> 对于该功能的改进已经在最新版本发布 (Docker latest 可用)，可参考 [PR 2411](https://github.com/apache/hugegraph/pull/2411), 此时可无缝切换。 

```bash
# stop the hugeGraph firstly
bin/stop-hugegraph.sh

# delete the store data (here we use the default path for rocksdb)
# Note: no need to delete data in the latest code (fixed in https://github.com/apache/hugegraph/pull/2411)
rm -rf rocksdb-data/

# init store again
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
docker run -itd -e PASSWORD=xxx --name=server -p 8080:8080 hugegraph/hugegraph:1.5.0
```

#### 2. 采用 docker-compose

使用 `docker-compose` 在环境变量中设置 `PASSWORD=xxx`即可

```yaml
version: '3'
services:
  server:
    image: hugegraph/hugegraph:1.5.0
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
