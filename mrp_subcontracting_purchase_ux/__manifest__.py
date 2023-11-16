# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Purchase Subcontracting Ux Utilities",
    'version': '0.1',
    'summary': "View Subcontract on Purchase Order",
    'description': "",
    'website': 'https://www.odoo.com/page/manufacturing',
    'category': 'Manufacturing/Manufacturing',
    'depends': ['mrp_subcontracting', 'purchase_stock'],
    'data': [
        'views/purchase_views.xml',
    ],
}
