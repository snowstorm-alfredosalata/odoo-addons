# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2019 RDS Moulding Technology S.p.A.

{ 
    'name': "Workorder Replanner", 
    'summary': "A wizard to help planning the workorders",
    'description': """
                      This module is intended for sole use by RDS Moulding Technology S.p.A.
                      Its purpuse is to give access to more planning options on workorders.
                    """,
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Integrations', 
    'version': '12.0',
    'depends': [
                'mrp_workorder'
               ], 
    'data': [
        'wizard/wizard_planner.xml'
    ],
    'application': False,
    'installable': True,
} 
