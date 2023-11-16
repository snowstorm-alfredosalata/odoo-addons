# -*- coding: utf-8 -*-
{
    "name": "Cloud Sync for Enterprise Documents",
    "version": "13.0.1.0.6",
    "category": "Document Management",
    "author": "faOtools",
    "website": "https://faotools.com/apps/13.0/cloud-sync-for-enterprise-documents-431",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "cloud_base",
        "documents"
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/documents_document.xml"
    ],
    "qweb": [
        
    ],
    "js": [
        
    ],
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The technical extension to sync Odoo Enterprise Documents with cloud clients",
    "description": """
For the full details look at static/description/index.html

* Features * 
- The documents hierarchy is reflected within the folder 'Odoo / Odoo Docs'
- Each Odoo folder has a linked cloud folder
- All files are synced with the same logic as usual attachments



#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "44.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=81&ticket_version=13.0&ticket_license=enterpise&url_type_id=3",
}