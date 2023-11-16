# -*- coding: utf-8 -*-
# $$LICENSE_BRIEF$$
{
    'name': 'Better Workcenter Logs',
    'version': '1.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': """Extends Workcenter Productivity Logs.""",
    'depends': ['mrp'],
    'description': """Extends Workcenter Logs, allowing 2-Layers categorization, better graphing with fixed colors (requires better_graphs module), better menus and more.""",
    'data': [
        'views/mrp_workcenter_productivity_loss_views.xml',
        'views/mrp_workcenter_productivity_loss_type_views.xml',

        'data/mrp_workcenter_productivity_loss_data.xml',

        'security/ir.model.access.csv'
    ],
    'author': 'MyCo s.r.l.',
    'license': 'Other proprietary'
}
