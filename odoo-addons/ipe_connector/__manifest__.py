{
    "name": "IPE Connector",
    "version": "19.0.1.0.0",
    "category": "Manufacturing",
    "summary": "Intelligent Planning Engine - Odoo 19 Integration",
    "description": """
        Bidirectional IPE ↔ Odoo integration:
        - REST API (/ipe/api/v1/*) for IPE connector pull/push
        - Real-time event hooks (sale, purchase, MRP)
        - Write-back receiver (/ipe/action)
    """,
    "author": "Diligent / IPE Team",
    "depends": ["sale", "purchase", "mrp", "stock", "product"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "data/ipe_data.xml",
        "data/ir_cron.xml",
        "views/ipe_config_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
