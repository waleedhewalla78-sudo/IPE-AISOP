-- verify_audit_immutability.sql
--
-- Verifies that the ipe_app role lacks UPDATE and DELETE privileges
-- on cdm_audit_log, and that the RLS policy is active.
--
-- Run: psql -U ipe_app -d ipe -f scripts/validation/verify_audit_immutability.sql
--
-- Expected output:
--  has_update | has_delete | rls_enabled
-- ------------+------------+-------------
--  f          | f          | t

WITH privilege_check AS (
    SELECT
        EXISTS (
            SELECT 1
            FROM information_schema.table_privileges
            WHERE grantee = 'ipe_app'
              AND table_name = 'cdm_audit_log'
              AND table_schema = 'public'
              AND privilege_type = 'UPDATE'
        ) AS has_update,
        EXISTS (
            SELECT 1
            FROM information_schema.table_privileges
            WHERE grantee = 'ipe_app'
              AND table_name = 'cdm_audit_log'
              AND table_schema = 'public'
              AND privilege_type = 'DELETE'
        ) AS has_delete,
        EXISTS (
            SELECT 1
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'cdm_audit_log'
              AND n.nspname = 'public'
              AND c.relrowsecurity = true
        ) AS rls_enabled
)
SELECT
    has_update,
    has_delete,
    rls_enabled,
    CASE
        WHEN has_update = false AND has_delete = false AND rls_enabled = true
        THEN 'PASS: Audit log is append-only (UPDATE/DELETE revoked, RLS active)'
        ELSE 'FAIL: Audit log immutability is compromised'
    END AS result
FROM privilege_check;
