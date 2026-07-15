# Implementation Plan: 024-phase3-ai-agents

**Date**: 2026-07-15  
**Sources**: Phase 3 Blueprint v2.0 + Technical Spec v2.0

## Approach

1. Migrations 051–059 (055 ALTER for existing supplier_score)
2. Core libraries + APIs in fea/cap/demand/mat/dpe/nlp/sop
3. New upload-svc (sop-svc scaffold)
4. Kong R2 + custom release2 compose
5. Web routes under Platform / Planning / Supply / AI hubs
6. Unit tests per core module; R2 smoke when stack up

## Deferred (documented)

- Full CDM row insert for every upload file type (validation + wizard first)
- Multi-tenant wizard persistence beyond in-memory / optional DB tables
