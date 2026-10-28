---
title: "Documentation site preview"
linkTitle: "Documentation site preview"
description: "Preview and check the Hugo documentation site with the pinned OINK module."
type: docs
weight: 20
outputs: [HTML, print, markdown]
---

## Check the local toolchain

Use the tool versions pinned in the repository's `go.mod` and CI configuration. From the documentation repository root, check the tools and theme:

```bash {wrap=true}
hugo version
go version
hugo mod graph
```

> [!DETAILS]- Optional: terminal player authoring example
>
> Use the copyable commands above to check versions. This optional example shows maintainers how the player works.
> Recordings are suitable for interactive operations, startup sequences and troubleshooting walkthroughs.
> Change `file`, `title` or `speed` in Markdown to adjust the file, title or speed; re-record the `.cast` when commands or output change.
> It was recorded on 2026-10-11 with Hugo 0.165 Extended, Go 1.27.1 and OINK 1.2.0.
> Playback runs at 0.1 times the recorded speed to make the short output easier to read. The cast is served locally with the site.
>
> <div class="hg-toolchain-recording">
>
> {{< asciinema file="/casts/oink-upgrade-check.cast" title="Recorded documentation toolchain and theme check" speed="0.1" >}}
>
> </div>
>
> [Download the original recording](/casts/oink-upgrade-check.cast).

## Preview and validate

1. Start the local preview from the repository root:

   ```bash
   scripts/hugo.sh server
   ```

2. Open [the local site](http://localhost:1313/) and inspect both language versions of the changed page.
3. Run the production build with CI's diagnostics:

   ```bash
   scripts/hugo.sh build
   ```
{.steps}

The wrapper generates version-navigation settings before starting Hugo. A different preview port can be passed with `-p`,
for example `scripts/hugo.sh server -p 8080`.

For the complete contribution checks and theme upgrade workflow, see the repository's
[contribution guide](https://github.com/apache/hugegraph-doc/blob/master/contribution.md) and
[OINK upgrade guide](https://github.com/apache/hugegraph-doc/blob/master/scripts/oink-upgrade.md).
