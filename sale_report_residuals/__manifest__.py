# Intended for sole use by RDS Moulding Technology SpA. See README file.

{ 
    'name': "Sale Report Residuals", 
    'summary': "Adds residuals and groupby delivery in sale_report.",
    'description': """""",
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'sale', 
    'version': '12.0', 
    'depends': [
                'sale_stock'
               ], 
    'data': [
        'report/sale_report_views.xml'
    ],
    'application': False,
    'installable': True,
} 