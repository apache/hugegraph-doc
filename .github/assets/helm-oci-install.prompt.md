# Helm consumer quickstart illustration

Generated with the built-in image generation tool. Final asset: `static/images/helm-oci-install.png`.

## Prompt

```text
Use case: infographic-diagram
Asset type: user-facing HugeGraph documentation quickstart image, wide landscape around 3:1.
Primary request: Create a clean, simple three-stage guide showing how a user finds and installs a HugeGraph Helm chart. This is a consumer guide, with no CI or publication implementation details.
Style: white background, navy typography, restrained teal and blue accents, crisp minimal line icons, generous spacing, no shadows that obscure labels, readable at 1100px wide. No watermark.
Composition: three rounded cards from left to right. First card a search icon and a small catalog icon. Second card two registry destination pills at its left, BOTH with converging arrows into a single .tgz file icon at its right. Third card a Helm command/terminal icon alongside a Kubernetes cluster icon. Clear rightward main flow. The arrow from first to second means selecting a version, NOT downloading a chart from Artifact Hub.
Text (verbatim):
Overall title: "Install HugeGraph with Helm"
First card heading: "Find a chart version"
First card main label: "Artifact Hub"
First card subtext: "Search & documentation"
First-to-second connector label, small: "Choose version"
Second card heading: "Get the chart"
Second card registry pill 1: "GHCR (recommended)"
Second card registry pill 2: "Docker Hub"
Second card file label: ".tgz"
Second-to-third connector label, small: "Install"
Third card heading: "Install with Helm"
Third card subtext: "Kubernetes"
Bottom note, clearly separated from the three main cards: "Container images are downloaded separately"
Accuracy constraints: Artifact Hub indexes metadata and documentation; the actual chart .tgz is obtained from GHCR or Docker Hub. Chart and container images are different artifacts. Do not draw an archive-file arrow from Artifact Hub. Do not imply the .tgz contains container images. Optional: a tiny separate container-image icon with dotted arrow directly toward Kubernetes can support the bottom note, but omit if it clutters. No source, git, checks, workflow jobs, publisher locks, tests or release pipeline. No topology counts or high-availability guarantees. Keep text exactly as above and legible.
```

## Chinese localization prompt

Final asset: `static/images/helm-oci-install-cn.png`.

```text
Use case: text-localization
Edit target: the supplied HugeGraph Helm consumer installation diagram.
Create a Simplified Chinese version by changing ONLY the instructional text below. Preserve the same three-card composition, white background, navy/teal/blue colors, all icons, logos, registry-to-.tgz arrows and Helm-to-Kubernetes arrow, aspect ratio and spacing. Use clear, clean, correctly rendered Simplified Chinese sans-serif typography. Text must fit without clipping and remain legible.
Exact replacements:
"Install HugeGraph with Helm" → "使用 Helm 安装 HugeGraph"
"Find a chart version" → "选择 Chart 版本"
"Get the chart" → "下载 Chart"
"Install with Helm" → "用 Helm 安装"
"Search & documentation" → "搜索与使用说明"
"Choose version" → "选择版本"
"(recommended)" → "（推荐）"
"Install" (connector label) → "安装"
"Container images are downloaded separately" → "容器镜像需单独下载"
Keep these technical labels exactly as they currently appear: "Artifact Hub", "GHCR", "Docker Hub", ".tgz", "HELM", "Kubernetes".
Do not translate technical brand names, add other text, change the workflow, or alter graphics. No watermark.
```
