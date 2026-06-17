# Event Mesh

Apache Kafka topics follow the pattern `ipe.{entity}.{event}`.

## Core Topics

| Topic | Producer | Consumers |
|-------|----------|-----------|
| `ipe.demand.created` | Connector | dpe-svc, mat-svc |
| `ipe.demand.classified` | dpe-svc | fea-svc |
| `ipe.supply.updated` | Connector | mat-svc |
| `ipe.inventory.changed` | Connector | mat-svc, dpe-svc |
| `ipe.mo.feasibility_scored` | fea-svc | res-svc |
| `ipe.resolution.proposed` | res-svc | Frontend |

## Dead Letter Queues

Each service has a DLQ topic: `ipe.dlq.{service-name}` for failed event processing.
