# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.


{
    'name': 'Kontrol - An Odoo MES',
    'version': '12.0',
    'author': 'Alfredo Salata',
    'summary': 'Advanced MES for Odoo. - HR Fields',
    'website': 'http://rdsmoulding.com',
    'category': 'Production',
    'description': """""",
    'depends': ['hr', 'odoo_kontrol'],
    'data': [
        'views/mrp_workorder_views.xml',
        'views/mrp_workcenter_productivity.xml',
    ],
}
