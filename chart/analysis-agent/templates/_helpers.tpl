{{/*
Expand the name of the chart.
*/}}
{{- define "analysis-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "analysis-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "analysis-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "analysis-agent.labels" -}}
helm.sh/chart: {{ include "analysis-agent.chart" . }}
{{ include "analysis-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "analysis-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "analysis-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Webhook labels
*/}}
{{- define "analysis-agent.webhook.labels" -}}
{{ include "analysis-agent.labels" . }}
app: webhook-service
component: webhook
{{- end }}

{{/*
Notifier labels
*/}}
{{- define "analysis-agent.notifier.labels" -}}
{{ include "analysis-agent.labels" . }}
app: notifier-service
component: notifier
{{- end }}

{{/*
Agent labels
*/}}
{{- define "analysis-agent.agent.labels" -}}
{{ include "analysis-agent.labels" . }}
app: devops-rca
component: agent
{{- end }}

{{/*
Create the name of the webhook service account to use
*/}}
{{- define "analysis-agent.webhook.serviceAccountName" -}}
{{- if .Values.rbac.create }}
{{- default "webhook-sa" .Values.rbac.serviceAccounts.webhook.name }}
{{- else }}
{{- default "default" .Values.rbac.serviceAccounts.webhook.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the notifier service account to use
*/}}
{{- define "analysis-agent.notifier.serviceAccountName" -}}
{{- if .Values.rbac.create }}
{{- default "notifier-sa" .Values.rbac.serviceAccounts.notifier.name }}
{{- else }}
{{- default "default" .Values.rbac.serviceAccounts.notifier.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the agent service account to use
*/}}
{{- define "analysis-agent.agent.serviceAccountName" -}}
{{- if .Values.rbac.create }}
{{- default "agent-sa" .Values.rbac.serviceAccounts.agent.name }}
{{- else }}
{{- default "default" .Values.rbac.serviceAccounts.agent.name }}
{{- end }}
{{- end }}
