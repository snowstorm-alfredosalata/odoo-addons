# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': 'Budget Management - Partner',
    'category': 'Accounting',
    'description': """
Extends budgets to allow partner-based filtering.
--------------------------------------------------------------
""",
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0', 
    'depends': [
                'account', 'account_budget'
               ], 
    'data': [
        'views/account_budget_views.xml'
    ],
    'application': False,
    'installable': True,
} 