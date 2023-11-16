# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'RDS Reports',
    'version': '1.1',
    'summary': 'Custom reports for RDS',
    'description': "",
    'website': '',
    'depends': ['mrp'],
    'category': 'Custom Reports',
    'sequence': 13,
    'data': [
        'report/reports.xml',

        'report/bom_cost_xml.xml',

    ],
}
