# HugeGraph Go Client Quick Start

LLMS index: [llms.txt](/llms.txt)

---

HugeGraph Go Client is the Go SDK in the Toolchain repository. It currently provides APIs for version queries, schemas, vertices, edges, and Gremlin.

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

`NewCommonClient` requires `Host` to be an IP address. Leave the username and password empty when authentication is disabled. Current server graph resource paths include a graph space; use `DEFAULT` for the default space. Leaving `GraphSpace` empty applies only to older servers that still use the `/graphs/{graph}` path.

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

The `Versions` value returned by `Version()` includes the HugeGraph Server, Core, Gremlin, and REST API versions. The `NewDefaultCommonClient()` helper in the source connects to the `hugegraph` graph at `127.0.0.1:8080` with `admin`/`pa` authentication. Production code should normally pass an explicit configuration instead.

## Available Entry Points

`CommonClient` currently exposes the following entry points:

| Entry point | Purpose |
|---|---|
| `Version()` | Query the server version |
| `Schema()` | Query the complete schema |
| `Propertykey` | Manage property keys |
| `VertexLabel` | Manage vertex labels |
| `EdgeLabel` | Manage edge labels |
| `Vertex` | Create vertices in single or batch mode and update vertex properties |
| `Gremlin` | Execute Gremlin through GET or POST |

For complete usage, see the tests in each API directory, such as [`version_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/version_test.go) and [`vertexlabel_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/vertexlabel/vertexlabel_test.go).
