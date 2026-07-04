"""Generate Helm Deployment/Service/HPA/PDB templates for IPE services."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELM_DIR = ROOT / "helm" / "ipe" / "templates"

SERVICES = [
    "dpe-svc",
    "fea-svc",
    "cap-svc",
    "mat-svc",
    "connector",
    "res-svc",
    "nlp-svc",
    "demand-svc",
    "scenario-svc",
    "supply-svc",
    "order-svc",
    "equipment-svc",
    "material-svc",
    "procurement-svc",
    "alert-svc",
    "sustain-svc",
    "quality-svc",
    "scn-svc",
    "rec-svc",
    "ml-svc",
    "del-svc",
    "network-svc",
]


def deployment(svc: str) -> str:
    return f"""\
{{{{- if .Values.services.{svc}.enabled }}}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {svc}
  labels:
    app.kubernetes.io/name: {svc}
    app.kubernetes.io/instance: {{{{ .Release.Name }}}}
    app.kubernetes.io/part-of: ipe
    app.kubernetes.io/managed-by: {{{{ .Release.Service }}}}
spec:
  replicas: {{{{ .Values.services.{svc}.replicaCount }}}}
  selector:
    matchLabels:
      app.kubernetes.io/name: {svc}
      app.kubernetes.io/instance: {{{{ .Release.Name }}}}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {svc}
        app.kubernetes.io/instance: {{{{ .Release.Name }}}}
        app.kubernetes.io/part-of: ipe
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{{{{ .Values.services.{svc}.port }}}}"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: {{{{ include "ipe.serviceAccountName" . }}}}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: {svc}
          image: "{{{{ .Values.global.imageRegistry }}}}/{svc}:{{{{ .Values.global.imageTag }}}}"
          imagePullPolicy: {{{{ .Values.global.imagePullPolicy }}}}
          ports:
            - containerPort: {{{{ .Values.services.{svc}.port }}}}
              name: http
          env:
            - name: IPE_SERVICE_NAME
              value: "{svc}"
            - name: IPE_PORT
              value: "{{{{ .Values.services.{svc}.port }}}}"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: ipe-db-secret
                  key: url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: ipe-redis-secret
                  key: url
          resources:
            {{{{- toYaml .Values.services.{svc}.resources | nindent 12 }}}}
          livenessProbe:
            httpGet:
              path: {{{{ .Values.services.{svc}.healthCheck.path }}}}
              port: http
            initialDelaySeconds: {{{{ .Values.services.{svc}.healthCheck.initialDelaySeconds }}}}
            periodSeconds: {{{{ .Values.services.{svc}.healthCheck.periodSeconds }}}}
          readinessProbe:
            httpGet:
              path: {{{{ .Values.services.{svc}.healthCheck.path }}}}
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
          volumeMounts:
            - name: config
              mountPath: /app/config
              readOnly: true
      volumes:
        - name: config
          configMap:
            name: {{{{ include "ipe.fullname" . }}}}-config
{{{{- end }}}}
"""


def service(svc: str) -> str:
    return f"""\
{{{{- if .Values.services.{svc}.enabled }}}}
apiVersion: v1
kind: Service
metadata:
  name: {svc}
  labels:
    app.kubernetes.io/name: {svc}
    app.kubernetes.io/instance: {{{{ .Release.Name }}}}
    app.kubernetes.io/part-of: ipe
spec:
  type: ClusterIP
  ports:
    - port: {{{{ .Values.services.{svc}.port }}}}
      targetPort: http
      name: http
  selector:
    app.kubernetes.io/name: {svc}
    app.kubernetes.io/instance: {{{{ .Release.Name }}}}
{{{{- end }}}}
"""


def hpa(svc: str) -> str:
    return f"""\
{{{{- if and .Values.services.{svc}.enabled .Values.services.{svc}.hpa.enabled }}}}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {svc}
  labels:
    app.kubernetes.io/name: {svc}
    app.kubernetes.io/instance: {{{{ .Release.Name }}}}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {svc}
  minReplicas: {{{{ .Values.services.{svc}.hpa.minReplicas }}}}
  maxReplicas: {{{{ .Values.services.{svc}.hpa.maxReplicas }}}}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{{{ .Values.services.{svc}.hpa.targetCPUUtilization }}}}
{{{{- end }}}}
"""


def pdb(svc: str) -> str:
    return f"""\
{{{{- if and .Values.services.{svc}.enabled .Values.services.{svc}.pdb.enabled }}}}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {svc}
  labels:
    app.kubernetes.io/name: {svc}
    app.kubernetes.io/instance: {{{{ .Release.Name }}}}
spec:
  minAvailable: {{{{ .Values.services.{svc}.pdb.minAvailable }}}}
  selector:
    matchLabels:
      app.kubernetes.io/name: {svc}
      app.kubernetes.io/instance: {{{{ .Release.Name }}}}
{{{{- end }}}}
"""


def main() -> None:
    HELM_DIR.mkdir(parents=True, exist_ok=True)
    for svc in SERVICES:
        (HELM_DIR / f"deployment-{svc}.yaml").write_text(deployment(svc), encoding="utf-8")
        (HELM_DIR / f"service-{svc}.yaml").write_text(service(svc), encoding="utf-8")
        (HELM_DIR / f"hpa-{svc}.yaml").write_text(hpa(svc), encoding="utf-8")
        (HELM_DIR / f"pdb-{svc}.yaml").write_text(pdb(svc), encoding="utf-8")
    print(f"Generated {len(SERVICES) * 4} template files in {HELM_DIR}/")


if __name__ == "__main__":
    main()
