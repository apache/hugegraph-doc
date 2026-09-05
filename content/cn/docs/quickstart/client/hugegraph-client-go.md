---
title: "HugeGraph Go 客户端快速入门"
linkTitle: "Go 客户端"
weight: 3
---

HugeGraph Go Client 是 Toolchain 仓库中的 Go SDK，目前提供版本查询、Schema（PropertyKey、VertexLabel、EdgeLabel）、顶点和 Gremlin API。边数据 API 尚未实现。

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

`NewCommonClient` 要求 `Host` 是 IP 地址，`Port` 在 1 到 65535 之间；客户端始终使用明文 HTTP 连接。未启用认证时，用户名和密码留空；只有两者都设置时才会发送 Basic Auth。

`GraphSpace` 只在 `Vertex` API（此时请求路径为 `/graphspaces/{space}/graphs/{graph}/...`）和 Gremlin 默认 aliases 中生效（空值按 `DEFAULT` 处理）。Schema 相关入口和 `Version()` 始终请求 `/graphs/{graph}/...` 和 `/versions`，与 `GraphSpace` 无关。默认图空间填写 `DEFAULT`；将 `GraphSpace` 留空时，`Vertex` API 会回退到旧版 Server 使用的 `/graphs/{graph}` 路径。

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

`Version()` 返回的 `Versions` 包含 HugeGraph Server、Core、Gremlin 和 REST API 版本。若使用源码提供的 `NewDefaultCommonClient()`，默认连接 `127.0.0.1:8080` 下的 `hugegraph` 图，使用 `admin`/`pa` 认证，并挂载一个打印全部请求和响应体的 `ColorLogger`；生产代码通常应显式传入配置。

## 配置项

`hugegraph.Config` 包含以下字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `Host` | `string` | HugeGraph Server 的 IP 地址，不支持主机名 |
| `Port` | `int` | HugeGraph Server 的 REST 端口，取值 1 到 65535 |
| `GraphSpace` | `string` | 图空间，仅 `Vertex` API 和 Gremlin 默认 aliases 使用；不需要时填空字符串 |
| `Graph` | `string` | Server 上配置的图名 |
| `Username` | `string` | Server 用户名，未启用认证时填空字符串 |
| `Password` | `string` | Server 密码，未启用认证时填空字符串 |
| `Transport` | `http.RoundTripper` | 自定义 HTTP transport，为 nil 时使用 `http.DefaultTransport` |
| `Logger` | `hgtransport.Logger` | 请求/响应日志，为 nil 时不记录日志 |

`hgtransport` 包提供四种 logger：`TextLogger`（纯文本）、`ColorLogger`（终端彩色）、`CurlLogger`（可执行的 curl 命令）和 `JSONLogger`（JSON 行）。它们的字段相同：`Output`（`io.Writer`）、`EnableRequestBody` 和 `EnableResponseBody`。

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

## 已实现的入口

`CommonClient` 当前公开以下入口：

| 入口 | 用途 |
|---|---|
| `Version()` | 查询服务端版本 |
| `Schema()` | 查询完整 Schema |
| `Propertykey` | `Create`、`GetAll`、`GetByName`、`UpdateUserdata`、`DeleteByName` |
| `VertexLabel` | `Create`、`GetAll`、`GetByName`、`UpdateUserdata`、`DeleteByName` |
| `EdgeLabel` | `Create`、`GetAll`、`DeleteByName` |
| `Vertex` | `Create`、`BatchCreate`、`UpdateProperties`（通过 `WithAction` 指定 `append` 或 `eliminate`） |
| `Gremlin` | `Get` 和 `Post`。`Post` 默认 `language` 为 `gremlin-groovy`，根据 `GraphSpace` 和 `Graph` 自动填充 `graph`/`g` aliases，并在 `Data` 中返回解析后的结果；`Get` 只返回状态码，并把原始响应打印到 stdout。 |

每个操作都通过挂在操作本身上的 `With...` 函数式选项传参，例如 `client.Gremlin.Post.WithGremlin(...)` 或 `client.Propertykey.GetByName.WithName(...)`。

```go
resp, err := client.Gremlin.Post(
	client.Gremlin.Post.WithGremlin("g.V().limit(3)"),
)
if err != nil {
	log.Fatal(err)
}
fmt.Println(resp.StatusCode, resp.Data.Status.Code, resp.Data.Result.Data)
```

> `Vertex` 相关操作的入参是 `internal/model` 包中的 `model.Vertex[any]`。Go 不允许从其他 module 导入 `internal` 包，因此目前 `Vertex` API 只能在客户端 module 内部调用；其测试文件也已全部注释。

完整调用方式可参考各 API 目录中的测试，例如 [`version_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/version_test.go)、[`gemlin_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/gremlin/gemlin_test.go) 和 [`vertexlabel_test.go`](https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go/api/v1/vertexlabel/vertexlabel_test.go)。
