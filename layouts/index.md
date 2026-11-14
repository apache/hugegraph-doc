{{- /* Keep the homepage's semantic Markdown aligned with its bilingual data.
     LLMS discovery remains native: index.llms.txt links this output. */ -}}
{{- .Page.Store.Set "tdOutputFormat" "markdown" -}}
{{- $data := index hugo.Data.landing .Site.Language.Lang -}}
{{- $chunks := slice (printf "# %s" (.Title | strings.TrimSpace)) -}}
{{- with .Description | strings.TrimSpace -}}
  {{- $chunks = $chunks | append (printf "> %s" (replace . "\n" "\n> ")) -}}
{{- end -}}
{{- with .Site.Home.OutputFormats.Get "llms" -}}
  {{- $chunks = $chunks | append (printf "%s [%s](%s)"
      (T "markdown_llms_index") (path.Base .RelPermalink)
      (partial "content/markdown-url.html" .RelPermalink)) -}}
{{- end -}}

{{- /* Archived releases only own their versioned documentation. The current
     product catalogue contains components and routes absent from older releases;
     keep their Markdown home as a native documentation/LLMS index instead. */ -}}
{{- if not .Site.Params.archived_version -}}
{{- $chunks = $chunks | append (printf "## %s\n\n%s" $data.hero.title $data.hero.body) -}}
{{- range slice $data.hero.primary $data.hero.secondary -}}
  {{- $chunks = $chunks | append (printf "[%s](%s)"
      (partial "content/markdown-escape.html" .label)
      (partial "content/markdown-url.html" (.url | relURL))) -}}
{{- end -}}

{{- $chunks = $chunks | append (printf "## %s" $data.story.label) -}}
{{- range $id := slice "database" "toolchain" "computing" "ai" -}}
  {{- $layer := index $data.layers $id -}}
  {{- $beat := index $data.story.beats $id -}}
  {{- $chunks = $chunks | append (printf "### %s\n\n%s\n\n%s\n\n**%s**\n\n%s"
      $layer.name $layer.components $layer.description $beat.title $beat.body) -}}
  {{- if eq $id "database" -}}
    {{- $chunks = $chunks | append "```gremlin\ng.V().has('name', 'marko').out('knows')\n```" -}}
  {{- end -}}
  {{- $chunks = $chunks | append (printf "[%s](%s)"
      (partial "content/markdown-escape.html" $beat.link_label)
      (partial "content/markdown-url.html" ($beat.url | relURL))) -}}
{{- end -}}

{{- $chunks = $chunks | append (printf "## %s" $data.statement.body) -}}
{{- range $data.statement.figures -}}
  {{- $chunks = $chunks | append (printf "- **%s** — %s" .value .label) -}}
{{- end -}}

{{- $chunks = $chunks | append (printf "## %s" $data.capabilities.title) -}}
{{- range $data.capabilities.items -}}
  {{- $chunks = $chunks | append (printf "- [**%s**](%s) — %s"
      (partial "content/markdown-escape.html" .title)
      (partial "content/markdown-url.html" (.url | relURL)) .body) -}}
{{- end -}}

{{- $chunks = $chunks | append (printf "## %s\n\n%s" $data.platforms.title (delimit (collections.Apply hugo.Data.landing.platforms "index" "." "name") ", ")) -}}
{{- $chunks = $chunks | append (printf "## %s\n\n%s" $data.components.title $data.components.body) -}}
{{- range $data.components.groups -}}
  {{- $chunks = $chunks | append (printf "### %s" .title) -}}
  {{- range .items -}}
    {{- $label := .name -}}
    {{- if .first_use }}{{ $label = printf "%s (%s)" $label $data.components.first_use }}{{ end -}}
    {{- $chunks = $chunks | append (printf "- [**%s**](%s) — %s"
        (partial "content/markdown-escape.html" $label)
        (partial "content/markdown-url.html" (.url | relURL)) .body) -}}
  {{- end -}}
{{- end -}}

{{- $chunks = $chunks | append (printf "## %s\n\n%s\n\n```bash\n%s\n```\n\n%s\n\n```bash\n%s\n```"
    $data.quickstart.title $data.quickstart.body $data.quickstart.command
    $data.quickstart.verify $data.quickstart.verify_command) -}}
{{- range slice $data.quickstart.install $data.quickstart.next -}}
  {{- $chunks = $chunks | append (printf "[%s](%s)"
      (partial "content/markdown-escape.html" .label)
      (partial "content/markdown-url.html" (.url | relURL))) -}}
{{- end -}}

{{- $chunks = $chunks | append (printf "## %s\n\n%s" $data.community.title $data.community.body) -}}
{{- range $data.community.items -}}
  {{- $label := printf "**%s**" (partial "content/markdown-escape.html" .title) -}}
  {{- with .url -}}
    {{- $label = printf "[%s](%s)" $label (partial "content/markdown-url.html" (. | relURL)) -}}
  {{- end -}}
  {{- $chunks = $chunks | append (printf "- %s — %s" $label .body) -}}
{{- end -}}
{{- end -}}

{{- with .Pages -}}
  {{- $chunks = $chunks | append (printf "---\n\n%s" (T "markdown_section_pages")) -}}
  {{- range . -}}
    {{- $line := printf "- [%s](%s)" (.Title | strings.TrimSpace)
        (partial "content/markdown-url.html" .RelPermalink) -}}
    {{- with .Description | strings.TrimSpace }}{{ $line = printf "%s: %s" $line . }}{{ end -}}
    {{- $chunks = $chunks | append $line -}}
  {{- end -}}
{{- end -}}
{{ delimit $chunks "\n\n" }}
