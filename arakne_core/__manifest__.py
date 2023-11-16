# $$LICENSE_BRIEF$$

{
    'name': 'Arakne Core',
    'version': '1.0',
    'category': 'Manufacturing/IoT',
    'summary': """Advanced IoT Services.""",
    'depends': ['mrp'],
    'external_dependencies': {
        'python': ['paramiko']
    },
    'description': """ """,
    'data': [
        'views/arakne_views_menus.xml',
        'views/arakne_daemon_views.xml',
        'views/arakne_device_views.xml',
        'views/arakne_device_model_views.xml',

        'security/arakne_security.xml',
        'security/ir.model.access.csv'
    ],
    'author': 'MyCo s.r.l.',
    'license': 'Other proprietary'
}
