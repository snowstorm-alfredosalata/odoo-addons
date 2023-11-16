# -*- coding: utf-8 -*-

{ 
    'name': "Visitors", 
    'summary': "A module to manage visitors.", 
    'description': """This module allows the creation of visitor profiles, scheduling of visits, printing of visitor badges.""", 
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Visits', 
    'version': '12.0.1.0.0', 
    'depends': ['base'], 
    'data': [
        'security/visit_security.xml',
        'security/ir.model.access.csv',
        'views/visit_views.xml',
    ],
    'application': 'true',
    'installable': 'true',
} 