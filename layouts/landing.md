{{- .Store.Set "tdOutputFormat" "markdown" -}}
{{- partial "page-meta-lastmod.html" . }}
{{- $landing := partial "landing/data.html" . -}}
{{- $text := partial "landing/text.html" (dict "page" . "data" $landing) | strings.TrimSpace -}}
{{- if and (eq .Section "community") (eq (.Params.landing | default "") "community") -}}
  {{- $parts := split $text "\n\n" -}}
  {{- $ctaHeading := cond (eq .Language.Lang "cn") "## 了解项目运作方式" "## Learn how the project works" -}}
  {{- $roster := partial "community/members.md" (dict "page" .) | strings.TrimSpace -}}
  {{- $before := slice -}}{{- $after := slice -}}{{- $found := false -}}
  {{- range $parts -}}
    {{- if and (not $found) (strings.HasPrefix . $ctaHeading) }}{{ $found = true }}{{ end -}}
    {{- if $found }}{{ $after = $after | append . }}{{ else }}{{ $before = $before | append . }}{{ end -}}
  {{- end -}}
  {{- $text = delimit (slice (delimit $before "\n\n") $roster (delimit $after "\n\n")) "\n\n" -}}
{{- end -}}
{{- with $text }}
{{ . | safeHTML }}
{{- end }}
