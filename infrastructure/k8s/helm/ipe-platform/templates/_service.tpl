{{- define "ipe.service.deployment" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .name }}
  labels:
    {{- include "ipe.labels" .root | nindent 4 }}
    app.kubernetes.io/component: {{ .name }}
spec:
  replicas: {{ .config.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/instance: {{ .root.Release.Name }}
      app.kubernetes.io/component: {{ .name }}
  template:
    metadata:
      labels:
        app.kubernetes.io/instance: {{ .root.Release.Name }}
        app.kubernetes.io/component: {{ .name }}
    spec:
      containers:
        - name: {{ .name }}
          image: {{ include "ipe.image" (dict "root" .root "image" (printf "ipe-%s" (replace "_" "-" .name))) }}
          imagePullPolicy: {{ .root.Values.global.imagePullPolicy }}
          ports:
            - containerPort: {{ .config.port }}
              protocol: TCP
          env:
            - name: KAFKA_BOOTSTRAP_SERVERS
              value: {{ .root.Values.global.kafkaBootstrapServers }}
            - name: REDIS_URL
              value: {{ .root.Values.global.redisUrl }}
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: ipe-database-credentials
                  key: dsn
            - name: ENVIRONMENT
              value: {{ .root.Values.global.environment }}
           resources:
             requests:
               cpu: {{ .config.resources.requests.cpu }}
               memory: {{ .config.resources.requests.memory }}
             limits:
               cpu: {{ .config.resources.limits.cpu }}
               memory: {{ .config.resources.limits.memory }}
           livenessProbe:
             httpGet:
               path: /api/v1/health
               port: {{ .config.port }}
             initialDelaySeconds: 15
             periodSeconds: 30
             timeoutSeconds: 5
             failureThreshold: 3
           readinessProbe:
             httpGet:
               path: /api/v1/health
               port: {{ .config.port }}
             initialDelaySeconds: 5
             periodSeconds: 10
             timeoutSeconds: 3
             failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: {{ .name }}
  labels:
    {{- include "ipe.labels" .root | nindent 4 }}
    app.kubernetes.io/component: {{ .name }}
spec:
  selector:
    app.kubernetes.io/instance: {{ .root.Release.Name }}
    app.kubernetes.io/component: {{ .name }}
  ports:
    - port: {{ .config.port }}
      targetPort: {{ .config.port }}
      protocol: TCP
      name: http
{{- end -}}
