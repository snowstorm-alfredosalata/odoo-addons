# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': "Commitment Date on Sales Order Report", 
    'summary': "",
    'description': """
                    """,
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Integrations', 
    'version': '12.0', 
    'depends': [
                'sale'
               ], 
    'data': [
        'reports/sale_order.xml'
    ],
    'application': False,
    'installable': True,
} 