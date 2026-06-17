{
    "name": "IPE Connector",
    "version": "1.0.0",
    "category": "Manufacturing",
    "summary": "Intelligent Planning Engine - Odoo Integration Connector",
    "description": """
        IPE Connector module for Odoo integration with the Intelligent Planning Engine.
        - Fires real-time events on sale order confirmation, purchase order changes, and MRP production status updates
        - Queues events for async delivery to the IPE Event Mesh
        - Receives and processes planning actions (confirm MO, reschedule, create RFQ)
    """,
    "author": "IPE Team",
    "website": "https://opencode.ai",
    "depends": ["sale", "purchase", "mrp", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/ipe_data.xml",
        "views/ipe_config_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
