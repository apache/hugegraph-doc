---
title: "Built-in User Authentication and Authorization Configuration and Usage in HugeGraph"
linkTitle: "Config Authentication"
weight: 3
search_keywords: [HugeGraph authentication, authorization, StandardAuthenticator]
search_boost: 1.7
---

### Overview
HugeGraph provides `StandardAuthenticator` for multi-user authentication and access control based on users, groups, operations, and resources.

Initialization creates the `admin` superuser. Administrators create users, groups, and resources, then grant or revoke permissions.
Users receive read, write, delete, and execute permissions through their groups.

A resource describes accessible data using `type`, `label`, and `properties`. Conditions within one resource are combined with AND; multiple resources are
combined with OR.

This relationship grants a user read access to data for Beijing.

```java
// Scenario: A user only has data read permission for the Beijing area
user(name=xx) -belong-> group(name=xx) -access(read)-> target(graph=graph1, resource={label: person, city: Beijing})
```

### Configure User Authentication

By default, HugeGraph does **not enable** user authentication, and it needs to be enabled by modifying the configuration file.

> [!WARNING]
> **Production requires authentication**
>
> HugeGraph disables user authentication by default. In production, enable authentication and authorization, set a strong non-default administrator password,
maintain the Server IP allowlist, and grant minimum permissions. Do not expose Gremlin, Cypher, or other query endpoints directly to the public network.
Standard Server configuration writes authentication-proxy audit records to `audit-*.log`; retain these files and restrict read access. `auth.audit_log_rate`
limits per-user output rather than serving as a dedicated audit-log on/off switch.

Use `StandardAuthenticator` for built-in access control, or implement `HugeAuthenticator` to connect an existing identity system.

HugeGraph uses [HTTP Basic Authentication](https://en.wikipedia.org/wiki/Basic_access_authentication). The value after
`Basic` is the Base64 encoding of `username:password`. With curl, pass the credentials directly through `-u`:

```bash
curl -u 'admin:<password>' \
  http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
```

> [!WARNING]
> **Protect Basic Authentication credentials**
>
> Basic Authentication only Base64-encodes `username:password`; it does not encrypt credentials. Use HTTPS for network transmission. See [HTTPS
configuration](config-https).

> [!WARNING]
> **JWT risks in older versions**
>
> HugeGraph-Server versions before 1.5.0 have JWT-related security risks in Auth mode. Upgrade affected versions or change the JWT `secretKey` according to that
version's requirements.

`auth.token_secret` is read from the authentication graph's configuration. The default graph is `hugegraph`, so its file is normally
`conf/graphs/hugegraph.properties`; if `auth.graph_store` changes, use that graph's properties file.
The core configuration defaults to 32 random bytes encoded as Base64 and does not write that default back to the file. Independently generated defaults cannot
remain consistent across restarts or Server nodes. To preserve existing tokens across restarts or validate the same token on multiple nodes, explicitly
configure the same strong random secret in each authentication graph configuration.

Server encodes this string as UTF-8 for JJWT's HS256 signer, which requires at least 32 bytes. This is a byte-length requirement; an arbitrary 32-character
string need not have sufficient randomness. The command below generates 32 random bytes and Base64-encodes them locally.

```properties
# Set the same value in every Server node's authentication graph configuration
auth.token_secret=<locally-generated-secret>
```

Generate the secret locally and transfer it securely into the authentication graph configuration. Do not commit the actual secret or expose it in public logs:

```bash
openssl rand -base64 32
```

Token lifetime is controlled by `auth.token_expire`, defaulting to 86400 seconds.

Both `auth.token_expire` and `auth.token_secret` belong to the authentication graph specified by `auth.graph_store`. Entries with the same names in
`rest-server.properties` do not override that graph configuration.

#### StandardAuthenticator Mode
`StandardAuthenticator` stores users and password hashes in the backend and checks access by role.
After updating these three configurations, [initialize authentication and restart Server](#switching-authentication-mode).

Set the authenticator and REST configuration path in `conf/gremlin-server.yaml`.

```yaml
authentication: {
  authenticator: org.apache.hugegraph.auth.StandardAuthenticator,
  authenticationHandler: org.apache.hugegraph.auth.WsAndHttpBasicAuthHandler,
  config: {tokens: conf/rest-server.properties}
}
```

Set the authenticator and authentication graph in `conf/rest-server.properties`.

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
`auth.graph_store` names the graph that stores authentication data. It must match a graph configuration in `conf/graphs/`.

Set `gremlin.graph` in `conf/graphs/<graph>.properties` for each protected graph.

```properties
gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy
```

For authorization API usage, see the [Authentication API](/docs/clients/restful-api/auth/) documentation.

### Custom User Authentication System

Implement `org.apache.hugegraph.auth.HugeAuthenticator` and point both `authenticator` configurations to that implementation to connect an existing identity
system.

### Switching authentication mode

Use this sequence for a local persistent backend such as RocksDB, after applying the configuration above.
HStore/PD deployments create the administrator through the PD startup path. Set `auth.admin_pa` for that deployment instead of using local interactive
initialization.

1. **Stop Server.**

   ```bash
   bin/stop-hugegraph.sh
   ```

1. **Initialize authentication data.**

   ```bash
   bin/init-store.sh
   ```

   Enter a strong password when prompted to create `admin`. Existing graph data is retained. If `admin` already exists, this command does not reset its
   password.
   Keep the existing storage directory.

1. **Start Server and check authentication.**

   ```bash
   bin/start-hugegraph.sh
   curl -u admin \
     http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
   ```

   curl prompts for the password. Correct credentials should return HTTP 200; missing or incorrect credentials should return HTTP 401.
   If startup fails, check the logs and authentication graph configuration before retrying.
{.steps}

### Enable authentication with Docker

For a new container, choose either Docker run or Docker Compose. For an existing container, see
[enabling authentication in existing containers](#3-enter-the-container-to-enable-authentication-mode).

When deploying with Docker, the official image supports enabling authentication
directly via environment variables (applicable to the official `/hugegraph-server` layout).
Replace the placeholder below with your image tag or digest:

```bash
export HUGEGRAPH_IMAGE='<image:tag-or-digest>'
read -r -s -p 'Admin password: ' PASSWORD
printf '\n'
export PASSWORD
```

Execute the command and enter a strong administrator password when prompted. Avoid committing plaintext passwords into shared Compose files.
Persist the JWT secret in the authentication graph configuration as described [above](#configure-user-authentication). Use the same value across all nodes.

#### Docker run {#1-use-docker-run}

Create a new container and publish its REST port only on the local host.

```bash
docker run -d --name server \
  -p 127.0.0.1:8080:8080 \
  -e PASSWORD \
  "$HUGEGRAPH_IMAGE"
unset PASSWORD
```

The entrypoint configures authentication, initializes the backend on first startup, and starts Server.
Continue with [checking authentication](#check-authentication).

#### Docker Compose {#2-use-docker-compose}

Save the following as `compose.yaml`. Compose rejects missing required variables to avoid starting an unauthenticated service by accident.
Start the service in the same terminal.

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

Set these variables again before recreating the container. Retain its data volumes and persist the configuration required by your deployment.
Continue with [checking authentication](#check-authentication).

#### Existing containers {#3-enter-the-container-to-enable-authentication-mode}

Use this path for an official Server container that ran without authentication and uses a local persistent backend.
Back up its data first. Confirm that the configuration, backend data, and `conf-bak` are all in mounted persistent volumes.
The official image declares `/hugegraph-server` as a volume; inspect the mounts of custom images first.
HStore/PD and external authentication services use their own administrator initialization paths.

1. **Stop the original container and open a maintenance container with the same image and volumes.**

   ```bash
   SERVER_IMAGE=$(docker inspect --format '{{.Image}}' server)
   docker stop server
   docker run --rm -it --volumes-from server \
     --entrypoint bash "$SERVER_IMAGE"
   ```

   Keep the original container stopped so two JVMs do not open the local database at once. `--entrypoint bash` opens a shell without starting Server.

1. **Configure authentication and initialize it inside the maintenance container.**

   ```bash
   cd /hugegraph-server
   bin/enable-auth.sh
   ```

   On its first run, `enable-auth.sh` saves the original configuration in `conf-bak` and updates authentication and the default `hugegraph` graph.
   If `conf-bak` already exists, the script skips its changes. Check all three configurations under [StandardAuthenticator mode](#standardauthenticator-mode).
   Configure other authentication graphs manually.
   Write a strong random JWT secret to the authentication graph configuration as described [above](#configure-user-authentication), then initialize it.

   ```bash
   bin/init-store.sh
   exit
   ```

   Enter the administrator password when prompted, then exit after initialization succeeds.

1. **Start the original container from the host.**

   ```bash
   docker start server
   ```

   Retain the `docker/init_complete` marker. Later changes to the `PASSWORD` environment variable do not change the stored administrator password.
{.steps}

#### Check authentication

Once Server is running, execute the following requests from the host to verify. `-u admin` prompts interactively for the password:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
curl -sS -o /dev/null -w '%{http_code}\n' -u admin \
  http://127.0.0.1:8080/graphspaces/DEFAULT/graphs/hugegraph/schema/vertexlabels
```

Requests without credentials should return `401 Unauthorized`, while requests with the correct password return `200 OK` (incorrect passwords also return `401`).
Note: Current master URLs include `/graphspaces/DEFAULT`; for 1.7.0 and older versions, omit the graphspace prefix (use `/graphs/hugegraph/...` directly).
If unauthenticated requests still return `200`, authentication is not active; inspect configuration and restart Server.
