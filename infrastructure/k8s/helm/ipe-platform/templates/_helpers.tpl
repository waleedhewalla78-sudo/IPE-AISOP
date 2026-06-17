{{- define "ipe.name" -}}
{{- default .Chart.Name .Values.global.environment | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "ipe.labels" -}}
app.kubernetes.io/name: {{ include "ipe.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: ipe-platform
{{- end }}

{{- define "ipe.image" -}}
{{ .Values.global.imageRegistry }}/{{ . }}:{{ .Values.global.imageTag }}
{{- end }}

{{- define "ipe.postgres-dsn" -}}
postgresql+asyncpg://ipe_app:{{ .Values.global.postgresPassword }}@postgres-headless:5432/ipe
{{- end }}
