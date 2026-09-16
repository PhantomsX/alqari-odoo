{
    "name": "Al-Qari Document AI",
    "version": "17.0.1.0.8",
    "category": "Productivity",
    "summary": "OCR, extract fields, classify, and validate documents via Al-Qari API",
    "description": """
Al-Qari Document AI for Odoo
============================

Thin Odoo connector for Al-Qari cloud API (Odoo 17). All OCR, extraction,
classification, validation, and review logic runs on Al-Qari servers.

Features
--------
* API key authentication to https://api.alqari.sa
* Upload PDFs and images → OCR → extract → classify → validate via API
* Optional human review queue (API-driven)
* Stores API responses in Odoo; no local document AI logic

Requires an Al-Qari account and API key (qari_...).
Documentation: see CUSTOMER_INSTALL.md in the module package.
    """,
    "author": "Al-Qari",
    "website": "https://alqari.sa",
    "support": "https://alqari.sa",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/alqari_security.xml",
        "security/ir.model.access.csv",
        "data/alqari_validation_rule_data.xml",
        "views/res_config_settings_views.xml",
        "views/alqari_validation_rule_views.xml",
        "views/alqari_document_views.xml",
        "wizard/alqari_process_wizard_views.xml",
        "views/menu.xml",
    ],
    "external_dependencies": {
        "python": ["requests"],
    },
    "images": ["static/description/banner.png", "static/description/icon.png"],
    "installable": True,
    "application": True,
}
