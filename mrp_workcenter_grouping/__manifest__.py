# $$LICENSE_BRIEF$$

{
    'name': 'MRP Reports Grouping',
    'version': '1.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': """Adds grouping of workcenter, productivity logs and workorders by workstation, department and plant.""",
    'depends': ['mrp'],
    'description': """ """,
    'data': [
        'views/mrp_workcenter_views.xml',
        'views/mrp_workcenter_grouping_views.xml',

        'security/ir.model.access.csv'
    ],
    'author': 'MyCo s.r.l.',
    'license': 'Other proprietary'
}
