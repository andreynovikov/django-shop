REST_FRAMEWORK = {
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer'
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication'
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'NUM_PROXIES': 0,  # nginx passes real client address in REMOTE_ADDR, do not trust X-Forwarded-For
    'DEFAULT_THROTTLE_RATES': {
        # SMS password request, per IP and per phone
        'check': '20/hour',
        'check_phone': '5/hour',
        # login with 4-digit SMS password, per IP and per phone
        'login': '10/min',
        'login_phone': '10/hour',
        'login_phone_day': '20/day',
    }
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Sewing World API',
    'COMPONENT_SPLIT_REQUEST': True,
    'SERVE_PERMISSIONS': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'SERVE_AUTHENTICATION': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

DRF_API_LOGGER_DATABASE = True
DRF_API_LOGGER_TIMEDELTA = 180
DRF_API_LOGGER_SLOW_API_ABOVE = 500
