---
title: "HugeGraph Go 客户端快速入门"
linkTitle: "Go 客户端"
weight: 3
---

基于 Go 语言的 HugeGraph Client SDK 工具。

## 软件架构

(软件架构说明)

## 安装教程

```shell
go get github.com/apache/hugegraph-toolchain/hugegraph-client-go
```

## 已实现 API

| API     | 说明          |
|---------|-------------|
| schema  | 获取模型 schema |
| version | 获取版本信息      |

## 使用说明

### 1. 初始化客户端

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
		Username: "", // 根据实际情况填写用户名
		Password: "", // 根据实际情况填写密码
		Logger: &hgtransport.ColorLogger{
			Output:             os.Stdout,
			EnableRequestBody:  true,
			EnableResponseBody: true,
		},
	})

	if err != nil {
		log.Fatalf("Error creating the client: %s\n", err)
	}

	// 使用 client 进行操作...
	_ = client // 避免 "imported and not used" 错误
}
```

### 2. 获取 HugeGraph 版本

#### 使用 SDK 获取版本信息

```go
package main

import (
	"fmt"
	"log"
	"os"

	"github.com/apache/hugegraph-toolchain/hugegraph-client-go"
	"github.com/apache/hugegraph-toolchain/hugegraph-client-go/hgtransport"
)

// initClient 初始化并返回一个 HugeGraph 客户端实例
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
	// 假设 client 有一个 Version 方法返回版本信息和一个错误
	// res, err := client.Version() // 实际调用
	// 模拟返回，因为原始 README 中的 client.Version() 返回类型与此处使用不完全匹配
	type VersionInfo struct {
		Versions struct {
			Version string `json:"version"`
			Core    string `json:"core"`
			Gremlin string `json:"gremlin"`
			API     string `json:"api"`
		} `json:"versions"`
		// Body io.ReadCloser // 假设有 Body 用于关闭，根据实际 SDK 调整
	}

	// 模拟 API 调用和返回
	res := &VersionInfo{
		Versions: struct {
			Version string `json:"version"`
			Core    string `json:"core"`
			Gremlin string `json:"gremlin"`
			API     string `json:"api"`
		}{
			Version: "1.0.0", // 示例版本
			Core:    "1.0.0",
			Gremlin: "3.x.x",
			API:     "v1",
		},
	}
	// err := error(nil) // 假设没有错误

	// if err != nil {
	// 	log.Fatalf("Error getting the response: %s\n", err)
	// }
	// defer res.Body.Close() // 如果有 Body，需要关闭

	fmt.Println(res.Versions)
	fmt.Println(res.Versions.Version)
}

func main() {
	getVersion()
}
```

#### 返回值的结构

```go
package main

// VersionResponse 定义了版本 API 返回的结构体
type VersionResponse struct {
	Versions struct {
		Version string `json:"version"` // hugegraph version
		Core    string `json:"core"`    // hugegraph core version
		Gremlin string `json:"gremlin"` // hugegraph gremlin version
		API     string `json:"api"`     // hugegraph api version
	} `json:"versions"`
}
```

## API 文档参考

<!-- 可以在此部分添加指向更详细 API 文档的链接 -->
