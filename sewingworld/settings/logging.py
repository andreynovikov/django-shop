LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': 'logs/django_error.log',
            'formatter': 'verbose',
        },
        'beru_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': 'logs/beru.log',
            'formatter': 'verbose',
        },
        'kassa_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': 'logs/kassa.log',
            'formatter': 'verbose',
        },
        'sber_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': 'logs/sber.log',
            'formatter': 'verbose',
        },
        'ozon_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': 'logs/ozon.log',
            'formatter': 'verbose',
        },
        'wb_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': 'logs/wb.log',
            'formatter': 'verbose',
        },
        'rarus_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': 'logs/rarus.log',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'shop': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'INFO',
        },
        'sewingworld': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'INFO',
        },
        'django': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'beru': {
            'handlers': ['beru_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'yandex_kassa': {
            'handlers': ['kassa_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'sber': {
            'handlers': ['sber_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ozon': {
            'handlers': ['ozon_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'wb': {
            'handlers': ['wb_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'rarus': {
            'handlers': ['rarus_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'two_factor': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    }
}
