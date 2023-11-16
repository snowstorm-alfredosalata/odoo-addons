# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': 'Working Shifts',
    'category': 'Human Resources',
    'description': "Extends HR and Resource Calendar to manage shifts.",
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0',
    'depends': [
                'hr'
               ], 
    'data': [
        'security/ir.model.access.csv',
        'views/shift_views.xml',
        'cron/cron_rotate_shifts.xml',
    ],
    'application': False,
    'installable': True,
} 