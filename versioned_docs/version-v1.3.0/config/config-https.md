---
title: "Configuring HugeGraphServer to Use HTTPS Protocol"
linkTitle: "Config HTTPS"
weight: 4
---

### Overview

By default, HugeGraphServer uses the HTTP protocol. However, if you have security requirements for your requests, you can configure it to use HTTPS.

### Server Configuration

Modify the `conf/rest-server.properties` configuration file and change the schema part of `restserver.url` to `https`.

```ini
# Set the protocol to HTTPS
restserver.url=https://127.0.0.1:8080
# Server keystore file path. This default value is automatically effective when using HTTPS, and you can modify it as needed.
ssl.keystore_file=conf/hugegraph-server.keystore
# Server keystore file password. This default value is automatically effective when using HTTPS, and you can modify it as needed.
ssl.keystore_password=******
```

The server's `conf` directory already includes a keystore file named `hugegraph-server.keystore`, and the password for this file is `hugegraph`. These are the default values when enabling the HTTPS protocol. Users can generate their own keystore file and password, and then modify the values of `ssl.keystore_file` and `ssl.keystore_password`.

### Client Configuration

#### Using HTTPS in HugeGraph-Client

When constructing a HugeClient, pass the HTTPS-related configurations. Here's an example in Java:

```java
String url = "https://localhost:8080";
String graphName = "hugegraph";
HugeClientBuilder builder = HugeClient.builder(url, graphName);
// Client keystore file path
String trustStoreFilePath = "hugegraph.truststore";
// Client keystore password
String trustStorePassword = "******";
builder.configSSL(trustStoreFilePath, trustStorePassword);
HugeClient hugeClient = builder.build();
```

> Note: Before version 1.9.0, HugeGraph-Client was created directly using the `new` keyword and did not support the HTTPS protocol. Starting from version 1.9.0, it changed to use the builder pattern and supports configuring the HTTPS protocol.

#### Using HTTPS in HugeGraph-Loader

When starting an import task, add the following options in the command line:

```bash
# HTTPS
--protocol https
# Client certificate file path. When specifying --protocol as https, the default value conf/hugegraph.truststore is automatically used, and you can modify it as needed.
--trust-store-file {file}
# Client certificate file password. When specifying --protocol as https, the default value hugegraph is automatically used, and you can modify it as needed.
--trust-store-password {password}
```

Under the `conf` directory of hugegraph-loader, there is already a default client certificate file named `hugegraph.truststore`, and its password is `hugegraph`.

#### Using HTTPS in HugeGraph-Tools

When executing commands, add the following options in the command line:

```bash
# Client certificate file path. When using the HTTPS protocol in the URL, the default value conf/hugegraph.truststore is automatically used, and you can modify it as needed.
--trust-store-file {file}
# Client certificate file password. When using the HTTPS protocol in the URL, the default value hugegraph is automatically used, and you can modify it as needed.
--trust-store-password {password}
# When executing migration commands and using the --target-url with the HTTPS protocol, the default value conf/hugegraph.truststore is automatically used, and you can modify it as needed.
--target-trust-store-file {target-file}
# When executing migration commands and using the --target-url with the HTTPS protocol, the default value hugegraph is automatically used, and you can modify it as needed.
--target-trust-store-password {target-password}
```

Under the `conf` directory of hugegraph-tools, there is already a default client certificate file named `hugegraph.truststore`, and its password is `hugegraph`.

### How to Generate Certificate Files

This section provides an example of generating certificates. If the default certificate is sufficient or if you already know how to generate certificates, you can skip this section.

#### Server

1. Generate the server's private key and import it into the server's keystore file. The `server.keystore` is for the server's use and contains its private key.

```bash
keytool -genkey -alias serverkey -keyalg RSA -keystore server.keystore
```

During the process, fill in the description information according to your requirements. The description information for the default certificate is as follows:

```
First and Last Name: hugegraph
Organizational Unit Name: hugegraph
Organization Name: hugegraph
City or Locality Name: BJ
State or Province Name: BJ
Country Code: CN
```

2. Export the server certificate based on the server's private key.

```bash
keytool -export -alias serverkey -keystore server.keystore -file server.crt
```

`server.crt` is the server's certificate.

#### Client

```bash
keytool -import -alias serverkey -file server.crt -keystore client.truststore
```

`client.truststore` is for the client's use and contains the trusted certificate.
