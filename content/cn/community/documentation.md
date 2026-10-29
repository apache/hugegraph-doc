---
title: "文档站本地预览"
linkTitle: "文档站本地预览"
description: "使用固定的 OINK 模块版本预览和检查 Hugo 文档站。"
type: docs
weight: 20
outputs: [HTML, print, markdown]
---

## 检查本地工具链

使用仓库 `go.mod` 和 CI 配置指定的工具版本。在文档仓库根目录执行以下命令，检查工具链和主题版本：

```bash {wrap=true}
hugo version
go version
hugo mod graph
```

> [!DETAILS]- 可选：终端播放器用法示例
>
> 版本检查使用上方可复制的命令即可。此处仅供维护者了解播放器用法；交互操作、启动过程和排障演示才适合录制。
> 修改 Markdown 中的 `file`、`title`、`speed` 可以更换文件、标题和速度；命令或输出变化时应重新录制 `.cast`。
> 录像实际录制于 2026-10-11，使用 Hugo 0.165 Extended、Go 1.27.1 和 OINK 1.2.0。
> 播放速度为原速的 0.1 倍，便于阅读简短输出；录像文件由本站本地提供。
>
> <div class="hg-toolchain-recording">
>
> {{< asciinema file="/casts/oink-upgrade-check.cast" title="文档工具链与主题版本检查实录" speed="0.1" >}}
>
> </div>
>
> [下载原始录像](/casts/oink-upgrade-check.cast)。

## 预览与验证

1. 在仓库根目录启动本地预览：

   ```bash
   scripts/hugo.sh server
   ```

2. 打开[本地站点](http://localhost:1313/)，检查所改页面的中英文版本。
3. 执行与 CI 一致、保留诊断日志的生产构建：

   ```bash
   scripts/hugo.sh build
   ```
{.steps}

包装脚本会先生成版本导航配置，再启动 Hugo。可通过 `-p` 指定预览端口，例如 `scripts/hugo.sh server -p 8080`。

完整的贡献检查和主题升级流程见仓库中的
[贡献指南](https://github.com/apache/hugegraph-doc/blob/master/contribution.md)和
[OINK 升级指南](https://github.com/apache/hugegraph-doc/blob/master/scripts/oink-upgrade.md)。
