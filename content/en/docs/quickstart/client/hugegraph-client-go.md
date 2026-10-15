---
title: "HugeGraph Go Client Quick Start"
linkTitle: "Go Client"
weight: 3
---

HugeGraph Go Client is the Go SDK in the Toolchain repository. It currently provides APIs for version queries, schemas (property keys, vertex labels, and edge labels), vertices, and Gremlin. An edge data API is not implemented yet.

> This module is still under development. Refer to the source code under [`hugegraph-client-go/api/v1`](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-client-go/api/v1) for the currently available interfaces.

## Requirements

- Go 1.19 or later
- An accessible HugeGraph Server; examples use `http://127.0.0.1:8080`

## Installation

Run the following command in a Go module project:

```shell
go get github.com/apache/hugegraph-toolchain/hugegraph-client-go
```

## Initialize the Client

`NewCommonClient` requires `Host` to be an IP address and `Port` to be between 1 and 65535. The client always connects over plain HTTP. Leave the username and password empty when authentication is disabled; Basic Auth is sent only when both are set.

When `GraphSpace` is nonempty, the `Vertex` and schema APIs (`Schema()`, `Propertykey`, `VertexLabel`, and `EdgeLabel`) use
`/graphspaces/{space}/graphs/{graph}/...`; an empty value selects the legacy `/graphs/{graph}/...` paths. Use `DEFAULT` for the default space.
Gremlin default aliases also use `GraphSpace`, treating an empty value as `DEFAULT`. `Version()` calls `/versions` independently of graph space.

```go
package main

import (
	"fmt"
	"log"

	hugegraph "github.com/apache/hugegraph-toolchain/hugegraph-client-go"
)

func main() {
	client, err := hugegraph.NewCommonClient(hugegraph.Config{
		Host:       "127.0.0.1",
		Port:       8080,
		GraphSpace: "DEFAULT",
		Graph:      "hugegraph",
		Username:   "",
		Password:   "",
	})
	if err != nil {
		log.Fatal(err)
	}

	response, err := client.Version()
	if err != nil {
		log.Fatal(err)
	}
	defer response.Body.Close()

	fmt.Println(response.Versions.Version)
}
```

The `Versions` value returned by `Version()` includes the HugeGraph Server, Core, Gremlin, and REST API versions. The `NewDefaultCommonClient()` helper in the source connects to the `hugegraph` graph at `127.0.0.1:8080` with `admin`/`pa` authentication and a `ColorLogger` that prints every request and response body. Production code should normally pass an explicit configuration instead.

## Configuration Options

`hugegraph.Config` has the following fields:

| Field | Type | Description |
|---|---|---|
| `Host` | `string` | HugeGraph Server IP address. Host names are rejected. |
| `Port` | `int` | HugeGraph Server REST port, 1 to 65535 |
| `GraphSpace` | `string` | Graph space for the `Vertex` and schema APIs and default Gremlin aliases; use `DEFAULT` for the default space. |
| `Graph` | `string` | Graph name configured on the server |
| `Username` | `string` | Server username; empty string when authentication is disabled |
| `Password` | `string` | Server password; empty string when authentication is disabled |
| `Transport` | `http.RoundTripper` | Custom HTTP transport; `http.DefaultTransport` when nil |
| `Logger` | `hgtransport.Logger` | Request/response logger; no logging when nil |

The `hgtransport` package ships four loggers: `TextLogger` (plain text), `ColorLogger` (terminal colors), `CurlLogger` (runnable curl commands), and `JSONLogger` (JSON lines). Each has the same fields: `Output` (an `io.Writer`), `EnableRequestBody`, and `EnableResponseBody`.

```go
import (
	"os"

	hugegraph "github.com/apache/hugegraph-toolchain/hugegraph-client-go"
	"github.com/apache/hugegraph-toolchain/hugegraph-client-go/hgtransport"
)

client, err := hugegraph.NewCommonClient(hugegraph.Config{
	Host:  "127.0.0.1",
	Port:  8080,
	Graph: "hugegraph",
	Logger: &hgtransport.ColorLogger{
		Output:             os.Stdout,
		EnableRequestBody:  true,
		EnableResponseBody: true,
	},
})
```

## Available Entry Points

`CommonClient` currently exposes the following entry points:

| Entry point | Purpose |
|---|---|
| `Version()` | Query the server version |
| `Schema()` | Query the complete schema |
| `Propertykey` | `Create`, `GetAll`, `GetByName`, `UpdateUserdata`, `DeleteByName` |
| `VertexLabel` | `Create`, `GetAll`, `GetByName`, `UpdateUserdata`, `DeleteByName` |
| `EdgeLabel` | `Create`, `GetAll`, `DeleteByName` |
| `Vertex` | `Create`, `BatchCreate`, `UpdateProperties` (with `WithAction`: `append` or `eliminate`) |
| `Gremlin` | `Get` and `Post`. `Post` defaults `language` to `gremlin-groovy`, fills the `graph`/`g` aliases from `GraphSpace` and `Graph`, and returns the parsed result in `Data`. `Get` only returns the status code and prints the raw response to stdout. |

Each operation takes functional options named `With...` on the operation itself, for example `client.Gremlin.Post.WithGremlin(...)` or `client.Propertykey.GetByName.WithName(...)`.

`EdgeLabel.Create` accepts `Properties: nil` or an empty `[]string{}` in its request data to create an edge label without properties.

Typed APIs return `err` for request validation, transport, response reading, or JSON decoding failures.
An HTTP 4xx/5xx response can still return `err == nil`; for example, creating a vertex with a nonexistent label returns HTTP 400.
Check that `response.StatusCode` is in the 2xx range before reading result data. For `Gremlin.Post`, also check `response.Data.Status.Code`
for a successful Gremlin protocol status (2xx).

```go
resp, err := client.Gremlin.Post(
	client.Gremlin.Post.WithGremlin("g.V().limit(3)"),
)
if err != nil {
	log.Fatal(err)
}
defer resp.Body.Close()
if resp.StatusCode < 200 || resp.StatusCode >= 300 {
	log.Fatalf("HugeGraph returned HTTP %d", resp.StatusCode)
}
if resp.Data.Status.Code < 200 || resp.Data.Status.Code >= 300 {
	log.Fatalf("Gremlin returned status %d: %s", resp.Data.Status.Code, resp.Data.Status.Message)
}
fmt.Println(resp.Data.Result.Data)
```

> The `Vertex` operations take `model.Vertex[any]` values from the `internal/model` package. Go does not allow importing an `internal` package from another module, so at the moment the `Vertex` API can only be called from code inside the client module itself; its test file is also fully commented out.

For complete usage, see the tests in each API directory, such as [`version_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/version_test.go), [`gemlin_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/gremlin/gemlin_test.go), and [`vertexlabel_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/vertexlabel/vertexlabel_test.go).
