# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'ZPL Labels',
    'version': '1.0',
    'sequence': 200,
    'category': 'Inventory',
    'summary': 'Handle various ZPL Labeling formats.',
    'description': "",
    'depends': ['stock', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/zpl_views.xml',
        'wizard/zpl_wizard.xml',
    ],
    'installable': True,
    'application': True,
}
