---
title: "Built-in User Authentication and Authorization Configuration and Usage in HugeGraph"
linkTitle: "Config Authentication"
weight: 3
search_keywords: [HugeGraph authentication, authorization, StandardAuthenticator]
search_boost: 1.7
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

> [!WARNING]
> **Production requires authentication**
>
> HugeGraph disables user authentication by default. In production, enable authentication and authorization, set a strong non-default administrator password, maintain the Server IP allowlist, and grant minimum permissions. Do not expose Gremlin, Cypher, or other query endpoints directly to the public network. Standard Server configuration writes authentication-proxy audit records to `audit-*.log`; retain these files and restrict read access. `auth.audit_log_rate` limits per-user output rather than serving as a dedicated audit-log on/off switch.

You need to modify the configuration file to enable this feature. HugeGraph provides built-in authentication mode: `StandardAuthenticator`. This mode supports multi-user authentication and fine-grained permission control. Additionally, developers can implement their own `HugeAuthenticator` interface to integrate with their existing authentication systems.

HugeGraph uses [HTTP Basic Authentication](https://en.wikipedia.org/wiki/Basic_access_authentication). The value after
`Basic` is the Base64 encoding of `username:password`. With curl, pass the credentials directly through `-u`:

```bash
curl -u 'admin:<password>' \
  http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
```

> [!WARNING]
> **Protect Basic Authentication credentials**
>
> Basic Authentication only Base64-encodes `username:password`; it does not encrypt credentials. Use HTTPS for network transmission. See [HTTPS configuration](config-https).

> [!WARNING]
> **JWT risks in older versions**
>
> HugeGraph-Server versions before 1.5.0 have JWT-related security risks in Auth mode. Upgrade affected versions or change the JWT `secretKey` according to that version's requirements.

`auth.token_secret` is read from the authentication graph's configuration. The default graph is `hugegraph`, so its file is normally `conf/graphs/hugegraph.properties`; if `auth.graph_store` changes, use that graph's properties file.
The source-code default generates 32 random bytes encoded as Base64, but does not write the value back to the file. Independently generated defaults cannot remain consistent across restarts or Server nodes. To preserve existing tokens across restarts or validate the same token on multiple nodes, explicitly configure the same strong random secret in each authentication graph configuration.

Server encodes this string as UTF-8 for JJWT's HS256 signer, which requires at least 32 bytes. This is a byte-length requirement; an arbitrary 32-character string need not have sufficient randomness. The command below generates 32 random bytes and Base64-encodes them locally.

```properties
# Set the same value in every Server node's authentication graph configuration
auth.token_secret=<locally-generated-secret>
```

Generate the secret locally and transfer it securely into the authentication graph configuration. Do not commit the actual secret or expose it in public logs:

```bash
openssl rand -base64 32
```

Since the default is generated at every startup, explicitly configure it when tokens must survive restarts or be accepted by multiple nodes. Token lifetime is controlled by `auth.token_expire`, defaulting to 86400 seconds.

Both `auth.token_expire` and `auth.token_secret` belong to the authentication graph specified by `auth.graph_store`. Entries with the same names in `rest-server.properties` do not override that graph configuration.

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

Configure the authenticator and the graph that stores authorization data in `rest-server.properties`:

```properties
auth.authenticator=org.apache.hugegraph.auth.StandardAuthenticator
auth.graph_store=hugegraph
# Used when Server first creates admin; replace public default pa with a strong password in production
# For local persistent backends, init-store.sh prompts for a password when StandardAuthenticator is first initialized
#auth.admin_pa=<your-admin-password>

# Auth Client Config
# If GraphServer and AuthServer are deployed separately, you also need to specify the following configuration. Fill in the IP:RPC port of AuthServer.
# auth.remote_url=127.0.0.1:8899,127.0.0.1:8898,127.0.0.1:8897

```
In the above configuration, the `graph_store` option specifies which graph to use for storing user information. If there are multiple graphs, you can choose any of them.

In the `hugegraph{n}.properties` configuration file, configure the `gremlin.graph` information:

```properties
gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy
```

For authorization API usage, see the [Authentication API](/docs/clients/restful-api/auth/) documentation.

### Custom User Authentication System

If you need to support a more flexible user system, you can customize the authenticator for extension.
Simply implement the `org.apache.hugegraph.auth.HugeAuthenticator` interface with your custom authenticator, 
and then modify the `authenticator` configuration item in the configuration file to point to your implementation.

### Switching authentication mode

When `init-store.sh` is run for the first time and the `admin` user does not yet exist, the command prompts for the
administrator password. For an initialized persistent backend, `init-store.sh` adds the system metadata required for
authentication without deleting existing graph data.

```bash
# stop the hugeGraph firstly
bin/stop-hugegraph.sh

# Initialize authentication system metadata; existing backend data is preserved
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
docker run -itd -e PASSWORD=xxx --name=server -p 8080:8080 hugegraph/hugegraph:1.7.0
```

#### 2. Use docker-compose

Use `docker-compose` and set the environment variable `PASSWORD=xxx`:

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

#### 3. Enter the container to enable authentication mode

Enter the container first:

```bash
docker exec -it server bash
# Modify the config quickly, the modified file are save in the conf-bak folder
bin/enable-auth.sh
```

Then follow [Switching authentication mode](#switching-authentication-mode)
