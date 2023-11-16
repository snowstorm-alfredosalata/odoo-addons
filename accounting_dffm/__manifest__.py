# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': "Payment Terms - Data fattura fine mese", 
    'summary': "Calcolo del pagamento a dffm secondo convenzioni italiane.",
    'description': """
                      This module is intended for sole use by RDS Moulding Technology S.p.A.
                    """,
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Integrations', 
    'version': '12.0', 
    'depends': [
                'account'
               ], 
    'data': [
        'views/account_views.xml',
    ],
    'application': False,
    'installable': True,
} 