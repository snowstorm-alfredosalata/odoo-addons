# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.


{
    'name': 'Concurrent Production Orders',
    'version': '12.0',
    'author': 'Alfredo Salata',
    'summary': 'Allows managing different productive paradigms.',
    'website': 'http://rdsmoulding.com',
    'category': 'Production',
    'description': """""",
    'depends': ['mrp', 'mrp_bom_costing_no_batching', 'mrp_account_enterprise'],
    'data': [
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/cost_structure_report.xml'
    ],
    'qweb': []
}
