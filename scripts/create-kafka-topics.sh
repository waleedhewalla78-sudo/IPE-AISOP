#!/usr/bin/env bash
BOOTSTRAP="localhost:9092"

TOPICS=(
  "ipe.demand.created"
  "ipe.demand.classified"
  "ipe.supply.updated"
  "ipe.supply.delay_detected"
  "ipe.inventory.changed"
  "ipe.workcenter.status_changed"
  "ipe.mo.feasibility_scored"
  "ipe.mo.auto_confirmed"
  "ipe.resolution.proposed"
  "ipe.resolution.approved"
  "ipe.delay.logged"
  "ipe.reconciliation.completed"
  "ipe.operator.absence"
  "ipe.dlq.dpe-svc"
  "ipe.dlq.mat-svc"
  "ipe.dlq.cap-svc"
  "ipe.dlq.fea-svc"
  "ipe.dlq.res-svc"
  "ipe.dlq.del-svc"
  "ipe.dlq.nlp-svc"
)

for topic in "${TOPICS[@]}"; do
  kafka-topics --bootstrap-server "$BOOTSTRAP" \
    --create --if-not-exists \
    --topic "$topic" \
    --partitions 6 \
    --replication-factor 1 \
    --config retention.ms=604800000
  echo "Created topic: $topic"
done
