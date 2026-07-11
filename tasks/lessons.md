# Lessons Learned

- Existing Odoo Config v2 uses `cdm_odoo_config_version` + KMS encryption; Sprint 4 Wave 1 requires `cdm_erp_connection` + Fernet/`IPE_ENCRYPTION_KEY`. Keep both: versioning API stays, new `/erp/connections` is the self-service connection manager.
- `cdm_otd_snapshot` already exists in migration 039 — skip recreating; extend aggregator/API instead.
- Spec 017 W1 numbering differs slightly from Sprint 4 docs (Spec maps Odoo to W1-03–06 and OTD to W1-07–08). Mark Spec 017 items DONE against the completed capability, not the remapped Sprint 4 labels alone.
