CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_BROKER_TRANSPORT_OPTIONS = {
    # 'sep': ':',
    # 'queue_order_strategy': 'priority',
    # Redis hands a task that no worker has acknowledged to another one after this long, so it has to outlast
    # the longest countdown or ETA: order mail waits up to seven days for a confirmed address, review requests a week.
    'visibility_timeout': 691200  # 8 days
}
# CELERY_SEND_EVENTS = True
# CELERY_TASK_SEND_SENT_EVENT = True
# CELERY_ACKS_LATE = True
# CELERY_TASK_DEFAULT_PRIORITY = 4
# CELERYD_PREFETCH_MULTIPLIER = 1

CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_EXPIRES = 691200  # 8 days
CELERY_RESULT_EXTENDED = True
