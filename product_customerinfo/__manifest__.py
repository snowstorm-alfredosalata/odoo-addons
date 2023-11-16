# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': 'Customer-specific product info.',
    'category': 'Sale',
    'description': """
Extends product with additional tables for managing customer-specific product code, description and notes.
--------------------------------------------------------------
""",
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0',
    'depends': [
                'product', 'sale'
               ], 
    'data': [
            'security/ir.model.access.csv',
            'views/product_views.xml',
    ],
    'application': False,
    'installable': True,
} 