---
title: "HugeGraph Go 客户端快速入门"
linkTitle: "Go 客户端"
weight: 3
---

HugeGraph Go Client 是 Toolchain 仓库中的 Go SDK，目前提供版本查询、Schema、顶点、边和 Gremlin API。

> 该模块仍在开发中。接口范围以 [`hugegraph-client-go/api/v1`](https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-client-go/api/v1) 下的源码为准。

## 环境要求

- Go 1.19 或更高版本
- 可访问的 HugeGraph Server，默认示例地址为 `http://127.0.0.1:8080`

## 安装

在 Go module 项目中执行：

```shell
go get github.com/apache/hugegraph-toolchain/hugegraph-client-go
```

## 初始化客户端

`NewCommonClient` 要求 `Host` 是 IP 地址；未启用认证时，用户名和密码留空。当前 Server 的图资源路径包含图空间，默认填写 `DEFAULT`。将 `GraphSpace` 留空只适用于仍使用 `/graphs/{graph}` 路径的旧版 Server。

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

`Version()` 返回的 `Versions` 包含 HugeGraph Server、Core、Gremlin 和 REST API 版本。若使用源码提供的 `NewDefaultCommonClient()`，默认连接 `127.0.0.1:8080` 下的 `hugegraph` 图，并使用 `admin`/`pa` 认证；生产代码通常应显式传入配置。

## 已实现的入口

`CommonClient` 当前公开以下入口：

| 入口 | 用途 |
|---|---|
| `Version()` | 查询服务端版本 |
| `Schema()` | 查询完整 Schema |
| `Propertykey` | 管理 PropertyKey |
| `VertexLabel` | 管理 VertexLabel |
| `EdgeLabel` | 管理 EdgeLabel |
| `Vertex` | 创建、批量创建和更新顶点属性 |
| `Gremlin` | 通过 GET 或 POST 执行 Gremlin |

完整调用方式可参考各 API 目录中的测试，例如 [`version_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/version_test.go) 和 [`vertexlabel_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/vertexlabel/vertexlabel_test.go)。
