# -*- coding: utf-8 -*-
{
    'name': 'Bukh Lotto',
    'version': '1.0',
    'website': 'https://www.loto.mn',
    'category': 'Lotto',
    'summary': 'Bukh Lotto',
    'description': """
        Lotto events.
""",
    'depends': ['event', 'website', 'website_event_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/bukhloto_views.xml',
        'views/event_view.xml',
        'views/event_templates.xml',
        'views/check_lotto_templates.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
