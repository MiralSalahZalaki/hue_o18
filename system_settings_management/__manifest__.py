{
    'name': 'System Settings Configuration',
    'version': "18.0.1.0.0",
    'depends': ['base', 'education_core', 'mail', 'mc_app', 'contacts', 'classroom_management'],
    'sequence': 1,
    'author': 'Mansoura College',
    'category': 'Industries',
    'data': [
        'security/ir.model.access.csv',
        'views/system_settings.xml',
    ],
    'assets': {
        'web.assets_backend': [

            'system_settings_management/static/src/js/system_settings_action_helper/system_settings_action_helper.xml',
            'system_settings_management/static/src/views/system_onboarding_list/system_onboarding_list_renderer.xml',
            'system_settings_management/static/src/js/system_settings_action_helper/system_settings_action_helper.js',
            'system_settings_management/static/src/views/system_onboarding_list/system_onboarding_list_renderer.js',
            'system_settings_management/static/src/views/system_onboarding_list/system_onboarding_list_view.js',
        ],
    },
    'installable': True,
    'application': True,
    "license": "LGPL-3",
    'icon': '/system_settings_management/static/description/system_settings_icon.png',
}