---
title: "Built-in User Authentication and Authorization Configuration and Usage in HugeGraph"
linkTitle: "Config Authentication"
weight: 3
---

### Overview
To facilitate authentication usage in different user scenarios, HugeGraph currently provides built-in authorization `StandardAuthenticator` mode,
which supports multi-user authentication and fine-grained access control. It adopts a 4-layer design based on "User-UserGroup-Operation-Resource" to
flexibly control user roles and permissions (supports multiple GraphServers).

Some key designs of the `StandardAuthenticator` mode include:
- During initialization, a super administrator (`admin`) user is created. Subsequently, other users can be created by the super administrator. Once newly created users are assigned sufficient permissions, they can create or manage more users.
- It supports dynamic creation of users, user groups, and resources, as well as dynamic allocation or revocation of permissions.
- Users can belong to one or multiple user groups. Each user group can have permissions to operate on any number of resources. The types of operations include read, write, delete, execute, and others.
- "Resource" describes the data in the graph database, such as vertices that meet certain criteria. Each resource consists of three elements: `type`, `label`, and `properties`. There are 18 types in total, with the ability to combine any label and properties. The internal condition of a resource is an AND relationship, while the condition between multiple resources is an OR relationship.

Here is an example to illustrate:

```java
// Scenario: A user only has data read permission for the Beijing area
user(name=xx) -belong-> group(name=xx) -access(read)-> target(graph=graph1, resource={label: person, city: Beijing})
```

### Configure User Authentication

By default, HugeGraph does **not enable** user authentication, and it needs to be enabled by modifying the configuration file.

> ⚠️ **SEC Reminder: Security of Graph Query Languages (Gremlin/Cypher)**
>
> Due to potential system security risks brought about by the flexibility of graph query languages, **please avoid exposing any query-related endpoints directly to public/external network environments**. In actual production deployments, please use the **[Authentication System](/docs/config/config-authentication/)** outlined here combined with an **IP Whitelist** as a dual-security mechanism, and we recommend enabling Audit Logs to pinpoint the exact queries executed by users. Given the stateless nature of the Server, it is strongly recommended overall to use a **[Containerized Environment (Docker/K8s)](/docs/quickstart/hugegraph/hugegraph-server/#31-use-docker-container-convenient-for-testdev)** architecture to effectively isolate underlying system safety risks at a minimal cost.

You need to modify the configuration file to enable this feature. HugeGraph provides built-in authentication mode: `StandardAuthenticator`. This mode supports multi-user authentication and fine-grained permission control. Additionally, developers can implement their own `HugeAuthenticator` interface to integrate with their existing authentication systems.

HugeGraph authentication modes adopt [HTTP Basic Authentication](https://en.wikipedia.org/wiki/Basic_access_authentication). In simple terms, when sending an HTTP request, you need to set the `Authentication` header to `Basic` and provide the corresponding username and password. The corresponding HTTP plaintext format is as follows:

```http
GET http://localhost:8080/graphs/hugegraph/schema/vertexlabels
Authorization: Basic admin xxxx
```

**Warning**: Versions of HugeGraph-Server prior to 1.5.0 have a JWT-related security vulnerability in the Auth mode. 
Users are advised to update to a newer version or manually set the JWT token's secretKey. It can be set in the `rest-server.properties` file by setting the `auth.token_secret` information:

```properties
auth.token_secret=XXXX   # should be a 32-chars string, consist of A-Z, a-z and 0-9
```

You can also generate it with the following command:

```shell
RANDOM_STRING=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)
echo "auth.token_secret=${RANDOM_STRING}" >> rest-server.properties
```

#### StandardAuthenticator Mode
The `StandardAuthenticator` mode supports user authentication and permission control by storing user information in the database backend. This
implementation authenticates users based on their names and passwords (encrypted) stored in the database and controls user permissions based on their
roles. Below is the specific configuration process (requires service restart):

Configure the `authenticator` and its `rest-server` file path in the `gremlin-server.yaml` configuration file:

```yaml
authentication: {
  authenticator: org.apache.hugegraph.auth.StandardAuthenticator,
  authenticationHandler: org.apache.hugegraph.auth.WsAndHttpBasicAuthHandler,
  config: {tokens: conf/rest-server.properties}
}
```

Configure the `authenticator` and `graph_store` information in the `rest-server.properties` configuration file:

```properties
auth.authenticator=org.apache.hugegraph.auth.StandardAuthenticator
auth.graph_store=hugegraph

# Auth Client Config
# If GraphServer and AuthServer are deployed separately, you also need to specify the following configuration. Fill in the IP:RPC port of AuthServer.
# auth.remote_url=127.0.0.1:8899,127.0.0.1:8898,127.0.0.1:8897

```
In the above configuration, the `graph_store` option specifies which graph to use for storing user information. If there are multiple graphs, you can choose any of them.

In the `hugegraph{n}.properties` configuration file, configure the `gremlin.graph` information:

```properties
gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy
```

For detailed API calls and explanations regarding permissions, please refer to the [Authentication-API](/docs/clients/restful-api/auth) documentation.

### Custom User Authentication System

If you need to support a more flexible user system, you can customize the authenticator for extension.
Simply implement the `org.apache.hugegraph.auth.HugeAuthenticator` interface with your custom authenticator, 
and then modify the `authenticator` configuration item in the configuration file to point to your implementation.

### Switching authentication mode

After the authentication configuration completed, enter the **admin password** on the **command line** when executing `init store.sh` for the first time. (For non-Docker mode)

If deployed based on Docker image or if HugeGraph has already been initialized and needs to be converted to authentication mode, 
relevant graph data needs to be deleted and HugeGraph needs to be restarted. If there is already business data in the diagram, 
it is temporarily **not possible** to directly convert the authentication mode (version<=1.2.0)

> Improvements for this feature have been included in the latest release (available in the latest docker image), please refer to [PR 2411](https://github.com/apache/hugegraph/pull/2411). Seamless switching is now available.

```bash
# stop the hugeGraph firstly
bin/stop-hugegraph.sh

# delete the store data (here we use the default path for rocksdb)
# there is no need to delete in the latest version (fixed in https://github.com/apache/hugegraph/pull/2411)
rm -rf rocksdb-data/

# init store again
bin/init-store.sh

# start hugeGraph again
bin/start-hugegraph.sh

```

### Use docker to enable authentication mode

For versions of the hugegraph/hugegraph image equal to or greater than 1.2.0, you can enable authentication mode while starting the Docker image. 

The steps are as follows:

#### 1. Use docker run

To enable authentication mode, add the environment variable `PASSWORD=xxx` (you can freely set the password) in the `docker run` command:

```bash
docker run -itd -e PASSWORD=xxx --name=server -p 8080:8080 hugegraph/hugegraph:1.5.0
```

#### 2. Use docker-compose

Use `docker-compose` and set the environment variable `PASSWORD=xxx`:

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

#### 3. Enter the container to enable authentication mode

Enter the container first:

```bash
docker exec -it server bash
# Modify the config quickly, the modified file are save in the conf-bak folder
bin/enable-auth.sh
```

Then follow [Switching authentication mode](#switching-authentication-mode)
