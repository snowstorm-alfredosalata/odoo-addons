# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.


{
    'name': 'Kontrol - An Odoo MES',
    'version': '12.0',
    'author': 'Alfredo Salata',
    'summary': 'Advanced MES for Odoo.',
    'website': 'http://rdsmoulding.com',
    'category': 'Production',
    'description': """""",
    'depends': ['mrp_workorder'],
    'data': [
        'views/mrp_workorder_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/mrp_workcenter_productivity_views.xml',
        'views/mrp_andon_views.xml',
        'views/web_asset_backend_template.xml',
        
        'wizard/overproduce_confirm_wizard.xml',
        'wizard/next_workorder_wizard.xml',

        'report/productivity_timetable_templates.xml',

        'security/ir.model.access.csv',

        'data/mrp_data.xml',
    ],
    'qweb': ['static/src/xml/mrp.xml']
}
