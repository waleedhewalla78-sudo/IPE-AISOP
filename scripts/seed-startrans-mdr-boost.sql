-- Post-Odoo-sync MDR boost for Star Trans demo tenant (Release 1 Gate 11).
-- Restores inventory + lead-time coverage after live sync overwrites seed positions.

UPDATE cdm_product
SET lead_time_days = COALESCE(lead_time_days, 7)
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND lead_time_days IS NULL;

INSERT INTO cdm_inventory_position (time, tenant_id, product_id, location_id, qty_on_hand, qty_reserved, qty_in_transit)
SELECT NOW(), p.tenant_id, p.id, l.id, 100, 0, 0
FROM cdm_product p
JOIN cdm_location l ON l.tenant_id = p.tenant_id
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND NOT EXISTS (
    SELECT 1 FROM cdm_inventory_position ip
    WHERE ip.tenant_id = p.tenant_id AND ip.product_id = p.id
  )
LIMIT 200;
