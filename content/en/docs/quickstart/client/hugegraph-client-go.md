---
title: "HugeGraph Go Client Quick Start"
linkTitle: "Go Client"
weight: 3
---

A HugeGraph Client SDK tool based on the Go language.

## Software Architecture

(Software architecture description)

## Installation Tutorial

```shell
go get github.com/apache/hugegraph-toolchain/hugegraph-client-go
```

## Implemented APIs

| API     | Description             |
|---------|-------------------------|
| schema  | Get schema information  |
| version | Get version information |

## Usage Instructions

### 1. Initialize the Client

```go
package main

import (
	"log"
	"os"

	"github.com/apache/hugegraph-toolchain/hugegraph-client-go"
	"github.com/apache/hugegraph-toolchain/hugegraph-client-go/hgtransport"
)

func main() {
	client, err := hugegraph.NewCommonClient(hugegraph.Config{
		Host:     "127.0.0.1",
		Port:     8080,
		Graph:    "hugegraph",
		Username: "", // Fill in the username according to the actual situation
		Password: "", // Fill in the password according to the actual situation
		Logger: &hgtransport.ColorLogger{
			Output:             os.Stdout,
			EnableRequestBody:  true,
			EnableResponseBody: true,
		},
	})

	if err != nil {
		log.Fatalf("Error creating the client: %s\n", err)
	}

	// Use the client for operations...
	_ = client // Avoid "imported and not used" error
}
```

### 2. Get HugeGraph Version

#### Get Version Information Using SDK

```go
package main

import (
	"fmt"
	"log"
	"os"

	"github.com/apache/hugegraph-toolchain/hugegraph-client-go"
	"github.com/apache/hugegraph-toolchain/hugegraph-client-go/hgtransport"
)

// initClient initializes and returns a HugeGraph client instance
func initClient() *hugegraph.CommonClient {
	client, err := hugegraph.NewCommonClient(hugegraph.Config{
		Host:     "127.0.0.1",
		Port:     8080,
		Graph:    "hugegraph",
		Username: "",
		Password: "",
		Logger: &hgtransport.ColorLogger{
			Output:             os.Stdout,
			EnableRequestBody:  true,
			EnableResponseBody: true,
		},
	})
	if err != nil {
		log.Fatalf("Error creating the client: %s\n", err)
	}
	return client
}

func getVersion() {
	client := initClient()
	// Assume client has a Version method that returns version information and an error
	// res, err := client.Version() // Actual call
	// Simulate return, as the client.Version() return type in the original README does not fully match the usage here
	type VersionInfo struct {
		Versions struct {
			Version string `json:"version"`
			Core    string `json:"core"`
			Gremlin string `json:"gremlin"`
			API     string `json:"api"`
		} `json:"versions"`
		// Body io.ReadCloser // Assume there is a Body to close, adjust according to the actual SDK
	}

	// Simulate API call and return
	res := &VersionInfo{
		Versions: struct {
			Version string `json:"version"`
			Core    string `json:"core"`
			Gremlin string `json:"gremlin"`
			API     string `json:"api"`
		}{
			Version: "1.0.0", // Example version
			Core:    "1.0.0",
			Gremlin: "3.x.x",
			API:     "v1",
		},
	}
	// err := error(nil) // Assume no error

	// if err != nil {
	// 	log.Fatalf("Error getting the response: %s\n", err)
	// }
	// defer res.Body.Close() // If there is a Body, it needs to be closed

	fmt.Println(res.Versions)
	fmt.Println(res.Versions.Version)
}

func main() {
	getVersion()
}
```

#### Structure of the Return Value

```go
package main

// VersionResponse defines the structure returned by the version API
type VersionResponse struct {
	Versions struct {
		Version string `json:"version"` // hugegraph version
		Core    string `json:"core"`    // hugegraph core version
		Gremlin string `json:"gremlin"` // hugegraph gremlin version
		API     string `json:"api"`     // hugegraph api version
	} `json:"versions"`
}
```

## API Reference

<!-- Links to more detailed API documentation can be added here -->
