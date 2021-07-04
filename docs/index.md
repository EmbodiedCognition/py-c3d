{{ define "html" }}
{{ with .GetPage "/c3d" }}{{.Render}}{{end}}
{{ end }}
