# HugeGraph 内置用户权限与扩展权限配置及使用

LLMS index: [llms.txt](/versions/1.0/llms.txt)

---

### 概述
HugeGraph 为了方便不同用户场景下的鉴权使用，目前内置了两套权限模式：
1. 简单的`ConfigAuthenticator`模式，通过本地配置文件存储用户名和密码 (仅支持单 GraphServer)
2. 完备的`StandardAuthenticator`模式，支持多用户认证、以及细粒度的权限访问控制，采用基于 “用户-用户组-操作-资源” 的 4 层设计，灵活控制用户角色与权限 (支持多 GraphServer)

其中 `StandardAuthenticator` 模式的几个核心设计：
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

HugeGraph 默认**不启用**用户认证功能，需通过修改配置文件来启用该功能。内置实现了`StandardAuthenticator`和`ConfigAuthenticator`两种模式，`StandardAuthenticator`模式支持多用户认证与细粒度权限控制，`ConfigAuthenticator`模式支持简单的用户权限认证。此外，开发者可以自定义实现`HugeAuthenticator`接口来对接自身的权限系统。

用户认证方式均采用 [HTTP Basic Authentication](https://zh.wikipedia.org/wiki/HTTP%E5%9F%BA%E6%9C%AC%E8%AE%A4%E8%AF%81) ，简单说就是在发送 HTTP 请求时在 `Authentication` 设置选择 `Basic` 然后输入对应的用户名和密码，对应 HTTP 明文如下所示 :

```http
GET http://localhost:8080/graphs/hugegraph/schema/vertexlabels
Authorization: Basic admin xxxx
```

#### StandardAuthenticator模式
`StandardAuthenticator`模式是通过在数据库后端存储用户信息来支持用户认证和权限控制，该实现基于数据库存储的用户的名称与密码进行认证（密码已被加密），基于用户的角色来细粒度控制用户权限。下面是具体的配置流程（重启服务生效）：

在配置文件`gremlin-server.yaml`中配置`authenticator`及其`rest-server`文件路径：

```yaml
authentication: {
  authenticator: com.baidu.hugegraph.auth.StandardAuthenticator,
  authenticationHandler: com.baidu.hugegraph.auth.WsAndHttpBasicAuthHandler,
  config: {tokens: conf/rest-server.properties}
}
```

在配置文件`rest-server.properties`中配置`authenticator`及其`graph_store`信息：

```properties
auth.authenticator=com.baidu.hugegraph.auth.StandardAuthenticator
auth.graph_store=hugegraph

# auth client config
# 如果是分开部署 GraphServer 和 AuthServer, 还需要指定下面的配置, 地址填写 AuthServer 的 IP:RPC 端口
#auth.remote_url=127.0.0.1:8899,127.0.0.1:8898,127.0.0.1:8897
```
其中，`graph_store`配置项是指使用哪一个图来存储用户信息，如果存在多个图的话，选取任意一个均可。

在配置文件`hugegraph{n}.properties`中配置`gremlin.graph`信息：

```properties
gremlin.graph=com.baidu.hugegraph.auth.HugeFactoryAuthProxy
```

然后详细的权限 API 调用和说明请参考 [Authentication-API](/versions/1.0/docs/clients/restful-api/auth) 文档 

#### ConfigAuthenticator模式

`ConfigAuthenticator`模式是通过预先在配置文件中设置用户信息来支持用户认证，该实现是基于配置好的静态`tokens`来验证用户是否合法。下面是具体的配置流程（重启服务生效）：

在配置文件`gremlin-server.yaml`中配置`authenticator`及其`rest-server`文件路径：

```yaml
authentication: {
  authenticator: com.baidu.hugegraph.auth.ConfigAuthenticator,
  authenticationHandler: com.baidu.hugegraph.auth.WsAndHttpBasicAuthHandler,
  config: {tokens: conf/rest-server.properties}
}
```

在配置文件`rest-server.properties`中配置`authenticator`及其`tokens`信息：

```properties
auth.authenticator=com.baidu.hugegraph.auth.ConfigAuthenticator
auth.admin_token=token-value-a
auth.user_tokens=[hugegraph1:token-value-1, hugegraph2:token-value-2]
```

在配置文件`hugegraph{n}.properties`中配置`gremlin.graph`信息：

```properties
gremlin.graph=com.baidu.hugegraph.auth.HugeFactoryAuthProxy
```

### 自定义用户认证系统

如果需要支持更加灵活的用户系统，可自定义authenticator进行扩展，自定义authenticator实现接口`com.baidu.hugegraph.auth.HugeAuthenticator`即可，然后修改配置文件中`authenticator`配置项指向该实现。
