{{- $page := .page -}}
{{- $data := hugo.Data.community.roster -}}
{{- $labels := dict
  "en" (dict "title" "Project members" "lead" "Current Apache HugeGraph PMC members and Committers, sourced from public ASF records." "chair" "Chair")
  "cn" (dict "title" "项目成员" "lead" "Apache HugeGraph 当前的 PMC 成员与 Committers，数据来自 ASF 公开记录。" "chair" "主席")
-}}
{{- $copy := index $labels $page.Language.Lang | default (index $labels "en") -}}
## {{ $copy.title }}

{{ $copy.lead }}

{{ range $role := slice "pmc" "committers" -}}
### {{ if eq $role "pmc" }}PMC{{ else }}Committers{{ end }}

{{ range (index $data.roles $role) -}}
- [{{ with .github }}@{{ .login }}{{ else }}{{ .asf_id }}{{ end }}]({{ .profile_url }}){{ if .chair }} — {{ $copy.chair }}{{ end }}
{{ end }}

{{ end -}}
