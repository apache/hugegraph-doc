{{- /*
  Community Markdown follows the landing data order. Native OINK sections use
  its text renderer unchanged; only the nested roster uses the site partial.
*/ -}}
{{- .Store.Set "tdOutputFormat" "markdown" -}}
# {{ .Title }}

{{- with .Description }}
> {{ . }}

{{- end }}

{{- $page := . -}}
{{- $landing := partial "landing/data.html" . -}}
{{- range $entry := ($landing.sections | default slice) -}}
  {{- $resolved := partial "landing/entry.html" (dict "home" $landing "entry" $entry) -}}
  {{- if and $resolved.enabled $resolved.data -}}
    {{- if eq $resolved.type "community-members" -}}
      {{- partial "community/members.md" (dict "page" $page) -}}
    {{- else -}}
      {{- $text := partial "landing/text.html" (dict "page" $page "data" (dict "sections" (slice $entry))) | strings.TrimSpace -}}
      {{- with $text }}
{{ . | safeHTML }}

      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
