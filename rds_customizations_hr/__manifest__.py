# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': "RDS Customizations - HR", 
    'summary': "Reports and personalized views for RDS Moulding Technology S.p.A.",
    'description': """
                      This module is intended for sole use by RDS Moulding Technology S.p.A.
                      Its purpuse is to add custom reports/views to Odoo.
                    """,
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Integrations', 
    'version': '12.0',
    'depends': [
                'hr', 'hr_contract', 'hr_attendance'
               ], 
    'data': [
            'report/employee_badge.xml', 
            'views/hr_views.xml',
            'views/report_templates.xml',
            'views/web_asset_backend_template.xml'
    ],
    'application': False,
    'installable': True,
} 