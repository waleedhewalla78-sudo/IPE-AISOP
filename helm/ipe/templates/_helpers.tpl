{{/*
Expand the name of the chart.
*/}}
{{- define "ipe.name" -}}
{{- default .Chart.Name .Values.global.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ipe.fullname" -}}
{{- if .Values.global.fullnameOverride }}
{{- .Values.global.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.global.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Service account name
*/}}
{{- define "ipe.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ipe.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Common labels — pass dict with root context and serviceName
*/}}
{{- define "ipe.labels" -}}
app.kubernetes.io/name: {{ .serviceName }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.global.imageTag | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: ipe
app.kubernetes.io/component: {{ .serviceName }}
{{- end }}

{{- define "ipe.selectorLabels" -}}
app.kubernetes.io/name: {{ .serviceName }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Container image for a service
*/}}
{{- define "ipe.image" -}}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .serviceName .Values.global.imageTag }}
{{- end }}

{{/*
Kafka bootstrap (placeholder for Bitnami/Strimzi wiring)
*/}}
{{- define "ipe.kafka.bootstrapServers" -}}
{{- printf "%s-controller-headless.%s.svc.cluster.local:9092" .Values.kafka.serviceName .Release.Namespace }}
{{- end }}
