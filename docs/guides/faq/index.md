# FAQ

LLMS index: [llms.txt](/llms.txt)

---

- How to choose the back-end storage? RocksDB or distributed storage?

  HugeGraph supports multiple deployment modes. Choose based on your data scale and scenario:
  - **Standalone Mode**: Server + RocksDB, suitable for development/testing and small to medium-scale data (≤ 2 TB)
  - **Distributed Mode**: HugeGraph-PD + HugeGraph-Store (HStore), for deployments that require horizontal scaling and multiple replicas, supporting data scales up to 1 PB

  Version 1.7.0 supports RocksDB, HStore, HBase, and Memory. Legacy backends such as Cassandra, ScyllaDB, MySQL, and PostgreSQL require version 1.5.x or earlier.

- Prompt when starting the service: `xxx (core dumped) xxx`

  First confirm that the JDK version is Java 11 or later. HugeGraph 1.7.0 no longer supports Java 8.

- The service is started successfully, but there is a prompt similar to "Unable to connect to the backend or the connection is not open" when operating the graph

  Persistent local backends such as RocksDB and HBase must be initialized with `init-store` before their first startup. HStore is managed by PD and Store and does not use this script.
  
- Do all backends need to be executed before use init-store, and can the serialization options be filled in at will?

  Memory and HStore do not use `init-store`; persistent local backends such as RocksDB and HBase must be initialized before first use. The serializer must match the backend—for example, RocksDB uses `binary`.

- Execution `init-store` error: ```Exception in thread "main" java.lang.UnsatisfiedLinkError: /tmp/librocksdbjni3226083071221514754.so: /usr/lib64/libstdc++.so.6: version `GLIBCXX_3.4.10' not found (required by /tmp/librocksdbjni3226083071221514754.so)```

  RocksDB requires gcc 4.3.0 (GLIBCXX_3.4.10) and above

- The `bin` directory contains `start-hugegraph.sh`, `start-restserver.sh` and `start-gremlinserver.sh`.  These scripts seem to be related to startup.  Which one should be used?

  Current release packages retain only `start-hugegraph.sh` as the Server startup script. GremlinServer and the REST Server run in the same process.

- Two graphs are configured, the names are `hugegraph` and `hugegraph1`, and the command to start the service is `start-hugegraph.sh`. Is only the hugegraph graph opened?

  The script name is unrelated to the graph name. To load multiple local graphs from the `graphs` directory, set `graph.load_from_local_config=true` in `rest-server.properties`; its default value in the source code is `false`.

- After the service starts successfully, garbled characters are returned when using `curl` to query all vertices

  The batch vertices/edges returned by the server are compressed (gzip), and can be redirected to `gunzip` for decompression (`curl http://example | gunzip`), or can be sent with the `postman` of `Firefox` or the `restlet` plug-in of Chrome browser. request, the response data will be decompressed automatically.
  
- When using the vertex Id to query the vertex through the `RESTful API`, it returns empty, but the vertex does exist

  Check the type of the vertex ID. If it is a string type, the "id" part of the API URL needs to be enclosed in double quotes, while for numeric types, it is not necessary to enclose the ID in quotes.

- Vertex Id has been double quoted as required, but querying the vertex via the   RESTful API  still returns empty
  
  Check whether the vertex id contains `+`, `space`, `/`, `?`, `%`, `&`, and `=` reserved characters of these `URLs`.  If they exist, they need to be encoded. The following table gives the coded values:
  
  ```
  special character | encoded value
  ------------------| -------------
  +                 | %2B
  space             | %20
  /                 | %2F
  ?                 | %3F
  %                 | %25
  #                 | %23
  &                 | %26
  =                 | %3D
  ```
  
- Timeout when querying vertices or edges of a certain category (`query by label`)

  Since the amount of data belonging to a certain label may be relatively large, please add a limit limit.

- It is possible to operate the graph through the `RESTful API`, but when sending `Gremlin` statements, an error is reported: `Request Failed(500)`

  It may be that the configuration of `GremlinServer` is wrong, check whether the `host` and `port` of `gremlin-server.yaml` match the `gremlinserver.url` of `rest-server.properties`, if they do not match, modify them, and then Restart the service.

- When using `Loader` to import data, a `Socket Timeout` exception occurs, and then `Loader` is interrupted

  Continuously importing data will put too much pressure on the `Server`, which will cause some requests to time out. The pressure on `Server` can be appropriately relieved by adjusting the parameters of `Loader` (such as: number of retries, retry interval, error tolerance, etc.), and reduce the frequency of this problem.

- How to delete all data from a graph

  An administrator can call `DELETE /graphspaces/{graphspace}/graphs/{graph}/clear`. The request must include the `confirm_message` required by the source code; see the [Graph API](../clients/restful-api/graphs) for the exact format. This operation removes schemas, vertices, edges, and indexes.

- The database has been cleared and `init-store` has been executed, but when trying to add a schema, the prompt "xxx has existed" appeared.

  There is a cache in the `HugeGraphServer`, and it is necessary to restart the `Server` when the database is cleared, otherwise the residual cache will be inconsistent.

- An error is reported during the process of inserting vertices or edges: `Id max length is 128, but got xxx {yyy}` or `Big id max length is 32768, but got xxx`

  In order to ensure query performance, the current backend storage limits the length of the id column. The vertex id cannot exceed 128 bytes, the edge id cannot exceed 32768 bytes, and the index id cannot exceed 128 bytes.

- Is there support for nested attributes, and if not, are there any alternatives?

  Nested attributes are currently not supported. Alternative: Nested attributes can be taken out as individual vertices and connected with edges.

- Can an `EdgeLabel` connect multiple pairs of `VertexLabel`, such as "investment" relationship, which can be "individual" investing in "enterprise", or "enterprise" investing in "enterprise"?

  An `EdgeLabel` does not support connecting multiple pairs of `VertexLabels`, users need to split the `EdgeLabel` into finer details, such as: "personal investment", "enterprise investment".

- Prompt `HTTP 415 Unsupported Media Type` when sending a request through `RestAPI`

  `Content-Type: application/json` needs to be specified in the request header

Other issues can be searched in the issue area of the corresponding project, such as [Server-Issues](https://github.com/apache/hugegraph/issues) / [Loader Issues](https://github.com/apache/hugegraph-loader/issues)
