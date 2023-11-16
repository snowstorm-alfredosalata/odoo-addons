# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "No Batching on Routing Costs in BOM Cost Report",
    'version': '0.1',
    'summary': "Computes BOM Costs without 'batching' routings",
    'description': "",
    'website': 'https://www.odoo.com/page/manufacturing',
    'category': 'Manufacturing/Manufacturing',
    'depends': ['mrp', 'mrp_account'],
    'data': [
        'views/mrp_bom_views.xml'
    ],
}
