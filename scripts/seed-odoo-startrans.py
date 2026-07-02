#!/usr/bin/env python3
"""Seed Star Trans demo master data into local Odoo (17/19).

Creates: products, work centers, BOM (lines + routing), MOs, customer/SO, supplier/PO.

Usage:
  python scripts/seed-odoo-startrans.py
  python scripts/seed-odoo-startrans.py --url http://localhost:8069 --db starttrans1 --user admin --password YOUR_PASSWORD
"""

from __future__ import annotations

import argparse
import sys
import xmlrpc.client
from datetime import datetime, timedelta


MODULES = ["sale", "purchase", "stock", "mrp"]


def connect(url: str, db: str, user: str, password: str):
    common = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        raise SystemExit(f"Authentication failed for {user}@{db}. Check password.")
    models = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/object")
    return uid, models


def ensure_modules(db, uid, password, models):
    for name in MODULES:
        mod_ids = models.execute_kw(db, uid, password, "ir.module.module", "search", [[("name", "=", name)]])
        if not mod_ids:
            print(f"  WARN module {name} not found")
            continue
        state = models.execute_kw(db, uid, password, "ir.module.module", "read", [mod_ids], {"fields": ["state"]})[0]["state"]
        if state != "installed":
            print(f"  Installing {name}...")
            models.execute_kw(db, uid, password, "ir.module.module", "button_immediate_install", [mod_ids])


def get_or_create(db, uid, password, models, model: str, domain: list, vals: dict) -> int:
    ids = models.execute_kw(db, uid, password, model, "search", [domain], {"limit": 1})
    if ids:
        return ids[0]
    return models.execute_kw(db, uid, password, model, "create", [vals])


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8069")
    p.add_argument("--db", default="starttrans1", help="Odoo database (listed via xmlrpc /db list)")
    p.add_argument("--user", default="whewalla@gmail.com")
    p.add_argument("--password", default="admin")
    args = p.parse_args()

    print(f"Connecting to Odoo {args.url} db={args.db}...")
    uid, models = connect(args.url, args.db, args.user, args.password)
    print(f"  Authenticated uid={uid}")

    print("Ensuring modules (sale, purchase, stock, mrp)...")
    ensure_modules(args.db, uid, args.password, models)

    uom_unit = models.execute_kw(
        args.db, uid, args.password, "uom.uom", "search", [[("name", "=", "Units")]], {"limit": 1}
    )
    uom_id = uom_unit[0] if uom_unit else 1

    # --- Products ---
    print("Creating products...")
    products = {}
    product_defs = [
        ("TR-500", "Transformer 500 kVA", "consu"),
        ("TR-1000", "Transformer 1000 kVA", "consu"),
        ("COPPER-WIRE", "Copper Winding Wire", "consu"),
        ("CORE-SILICON", "Silicon Steel Core", "consu"),
        ("INSUL-OIL", "Insulating Oil", "consu"),
        ("TANK-STEEL", "Steel Tank", "consu"),
    ]
    for code, name, ptype in product_defs:
        pid = get_or_create(
            args.db, uid, args.password, models,
            "product.product",
            [("default_code", "=", code)],
            {"name": name, "default_code": code, "type": ptype, "uom_id": uom_id, "is_storable": True},
        )
        products[code] = pid
        print(f"  {code} -> id {pid}")

    # --- Work centers ---
    print("Creating work centers...")
    wcs = {}
    for code, name, cap in [
        ("WC-WIND", "Coil Winding", 8.0),
        ("WC-ASSY", "Core & Coil Assembly", 8.0),
        ("WC-TEST", "Vacuum Test Bay", 6.0),
        ("WC-PACK", "Pack & Ship", 8.0),
    ]:
        wc_id = get_or_create(
            args.db, uid, args.password, models,
            "mrp.workcenter",
            [("code", "=", code)],
            {"name": name, "code": code, "time_efficiency": 100},
        )
        wcs[code] = wc_id

    # --- Customer & supplier ---
    print("Creating customer and supplier...")
    cust_id = get_or_create(
        args.db, uid, args.password, models,
        "res.partner",
        [("name", "=", "Great Lakes Utility Co.")],
        {"name": "Great Lakes Utility Co.", "customer_rank": 1},
    )
    sup_id = get_or_create(
        args.db, uid, args.password, models,
        "res.partner",
        [("name", "=", "Nile Copper Supplies")],
        {"name": "Nile Copper Supplies", "supplier_rank": 1},
    )

    # --- BOM with lines + routing ---
    print("Creating BOM for TR-500...")
    tr500 = products["TR-500"]
    tr500_tmpl = models.execute_kw(
        args.db, uid, args.password, "product.product", "read", [[tr500]], {"fields": ["product_tmpl_id"]}
    )[0]["product_tmpl_id"][0]
    bom_ids = models.execute_kw(
        args.db, uid, args.password, "mrp.bom", "search",
        [[("product_tmpl_id", "=", tr500_tmpl)]], {"limit": 1},
    )
    if bom_ids:
        bom_id = bom_ids[0]
        print(f"  BOM exists id={bom_id}")
    else:
        bom_id = models.execute_kw(args.db, uid, args.password, "mrp.bom", "create", [{
            "product_tmpl_id": tr500_tmpl,
            "product_id": tr500,
            "product_qty": 1.0,
            "type": "normal",
            "bom_line_ids": [
                (0, 0, {"product_id": products["COPPER-WIRE"], "product_qty": 120.0}),
                (0, 0, {"product_id": products["CORE-SILICON"], "product_qty": 2.0}),
                (0, 0, {"product_id": products["INSUL-OIL"], "product_qty": 500.0}),
                (0, 0, {"product_id": products["TANK-STEEL"], "product_qty": 1.0}),
            ],
            "operation_ids": [
                (0, 0, {"name": "Wind Coils", "workcenter_id": wcs["WC-WIND"], "time_cycle_manual": 240, "sequence": 10}),
                (0, 0, {"name": "Assembly", "workcenter_id": wcs["WC-ASSY"], "time_cycle_manual": 180, "sequence": 20}),
                (0, 0, {"name": "Vacuum Test", "workcenter_id": wcs["WC-TEST"], "time_cycle_manual": 90, "sequence": 30}),
                (0, 0, {"name": "Pack", "workcenter_id": wcs["WC-PACK"], "time_cycle_manual": 60, "sequence": 40}),
            ],
        }])
        print(f"  Created BOM id={bom_id}")

    # --- BOM for TR-1000 ---
    print("Creating BOM for TR-1000...")
    tr1000 = products["TR-1000"]
    tr1000_tmpl = models.execute_kw(
        args.db, uid, args.password, "product.product", "read", [[tr1000]], {"fields": ["product_tmpl_id"]}
    )[0]["product_tmpl_id"][0]
    bom1000_ids = models.execute_kw(
        args.db, uid, args.password, "mrp.bom", "search",
        [[("product_tmpl_id", "=", tr1000_tmpl)]], {"limit": 1},
    )
    if bom1000_ids:
        bom1000_id = bom1000_ids[0]
        print(f"  BOM exists id={bom1000_id}")
    else:
        bom1000_id = models.execute_kw(args.db, uid, args.password, "mrp.bom", "create", [{
            "product_tmpl_id": tr1000_tmpl,
            "product_id": tr1000,
            "product_qty": 1.0,
            "type": "normal",
            "bom_line_ids": [
                (0, 0, {"product_id": products["COPPER-WIRE"], "product_qty": 220.0}),
                (0, 0, {"product_id": products["CORE-SILICON"], "product_qty": 4.0}),
                (0, 0, {"product_id": products["INSUL-OIL"], "product_qty": 900.0}),
                (0, 0, {"product_id": products["TANK-STEEL"], "product_qty": 1.0}),
            ],
            "operation_ids": [
                (0, 0, {"name": "Wind Coils", "workcenter_id": wcs["WC-WIND"], "time_cycle_manual": 360, "sequence": 10}),
                (0, 0, {"name": "Assembly", "workcenter_id": wcs["WC-ASSY"], "time_cycle_manual": 300, "sequence": 20}),
                (0, 0, {"name": "Vacuum Test", "workcenter_id": wcs["WC-TEST"], "time_cycle_manual": 120, "sequence": 30}),
                (0, 0, {"name": "Pack", "workcenter_id": wcs["WC-PACK"], "time_cycle_manual": 90, "sequence": 40}),
            ],
        }])
        print(f"  Created BOM id={bom1000_id}")

    # Link TR-1000 MO to its BOM if missing
    mo1000_ids = models.execute_kw(
        args.db, uid, args.password, "mrp.production", "search",
        [[("product_id", "=", tr1000), ("state", "in", ["draft", "confirmed", "progress"])]],
    )
    for mo_id in mo1000_ids:
        mo = models.execute_kw(
            args.db, uid, args.password, "mrp.production", "read", [[mo_id]], {"fields": ["bom_id"]}
        )[0]
        if not mo.get("bom_id"):
            models.execute_kw(
                args.db, uid, args.password, "mrp.production", "write",
                [[mo_id], {"bom_id": bom1000_id}],
            )
            print(f"  Linked MO id={mo_id} to BOM id={bom1000_id}")

    # --- Manufacturing orders ---
    print("Creating manufacturing orders...")
    start = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    mo_defs = [
        (tr500, 2.0, start, start + timedelta(days=5)),
        (products["TR-1000"], 1.0, start + timedelta(days=1), start + timedelta(days=8)),
    ]
    mo_ids = []
    for product_id, qty, ds, df in mo_defs:
        existing = models.execute_kw(
            args.db, uid, args.password, "mrp.production", "search",
            [[("product_id", "=", product_id), ("state", "in", ["draft", "confirmed", "progress"])]],
            {"limit": 1},
        )
        if existing:
            mo_ids.append(existing[0])
            continue
        mo_id = models.execute_kw(args.db, uid, args.password, "mrp.production", "create", [{
            "product_id": product_id,
            "product_qty": qty,
            "date_start": ds.strftime("%Y-%m-%d %H:%M:%S"),
            "date_finished": df.strftime("%Y-%m-%d %H:%M:%S"),
        }])
        models.execute_kw(args.db, uid, args.password, "mrp.production", "action_confirm", [[mo_id]])
        mo_ids.append(mo_id)
        print(f"  MO id={mo_id} product={product_id} qty={qty}")

    # --- Sale order ---
    print("Creating sale order...")
    so_ids = models.execute_kw(
        args.db, uid, args.password, "sale.order", "search",
        [[("partner_id", "=", cust_id), ("state", "in", ["draft", "sent", "sale"])]], {"limit": 1},
    )
    if not so_ids:
        so_id = models.execute_kw(args.db, uid, args.password, "sale.order", "create", [{
            "partner_id": cust_id,
            "order_line": [(0, 0, {
                "product_id": tr500,
                "product_uom_qty": 2,
            })],
        }])
        models.execute_kw(args.db, uid, args.password, "sale.order", "action_confirm", [[so_id]])
        print(f"  Sale order id={so_id}")
    else:
        print(f"  Sale order exists id={so_ids[0]}")

    # --- Purchase order ---
    print("Creating purchase order...")
    po_ids = models.execute_kw(
        args.db, uid, args.password, "purchase.order", "search",
        [[("partner_id", "=", sup_id), ("state", "in", ["draft", "sent", "purchase"])]], {"limit": 1},
    )
    if not po_ids:
        po_id = models.execute_kw(args.db, uid, args.password, "purchase.order", "create", [{
            "partner_id": sup_id,
            "order_line": [(0, 0, {
                "product_id": products["COPPER-WIRE"],
                "product_qty": 500,
                "price_unit": 12.5,
            })],
        }])
        models.execute_kw(args.db, uid, args.password, "purchase.order", "button_confirm", [[po_id]])
        print(f"  Purchase order id={po_id}")
    else:
        print(f"  Purchase order exists id={po_ids[0]}")

    print("\nDone. Star Trans Odoo seed complete.")
    print("Next: .\\scripts\\setup-odoo-integration.ps1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
