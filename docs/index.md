# IPE — Intelligent Planning Engine

AI-driven production planning platform. ERP-agnostic. Odoo-first.

## Architecture

- **7 AI microservices** (FastAPI + OR-Tools)
- **Canonical Data Model** on PostgreSQL 16 + TimescaleDB
- **Apache Kafka** event mesh
- **React 18** frontend with Tailwind CSS
- **Kubernetes** deployment with ArgoCD GitOps
