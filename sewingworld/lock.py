from contextlib import contextmanager
from django.db import connection
from functools import wraps

from celery import Task
from celery.local import Proxy


class Lock:
    """
    PostgreSQL session-level advisory lock on hashtext(name), or on (hashtext(name), instance).

    It is taken on creation. With wait=True it blocks until it gets the lock, otherwise `locked` tells whether it got it.
    """
    def __init__(self, name: str, instance: int | None = None, wait=False):
        self.name = name

        # Only placeholders go into the SQL, the values are passed separately
        self.params = 'hashtext(%s)'
        self.values = [self.name]
        if instance is not None:
            self.params += ', %s'
            self.values.append(instance)

        if wait:
            lock_func = 'pg_advisory_lock'
        else:
            lock_func = 'pg_try_advisory_lock'

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT {lock_func}({self.params})', self.values)
            locked = cursor.fetchone()[0]
        # pg_advisory_lock() returns void (None) once it holds the lock
        self.locked = wait or locked

    def release(self):
        if self.locked:
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT pg_advisory_unlock({self.params})', self.values)
            self.locked = False


@contextmanager
def lock(name: str):
    cursor = connection.cursor()
    cursor.execute('SELECT pg_advisory_lock(hashtext(%s))', (name,))
    try:
        yield
    finally:
        cursor.execute('SELECT pg_advisory_unlock(hashtext(%s))', (name,))


def single_instance(func=None, *, wait=False):
    """
    Single instance run decorator for Celery tasks

    Goes below @shared_task, bound or not, with or without arguments:

        @shared_task(name='shop.tasks.import1c', bind=True)
        @single_instance(wait=True)
        def import1c(self, file):

    Celery names the task after the function it gets (module and __name__) unless the name is given,
    and celery beat finds the task by that name, so the wrapper has to look like the function it wraps.

    :param boolean wait: Wait until previous task instance finishes or drop current task
    """
    def decorator(func):
        # Proxy goes first: it matches shared_task's proxy by type, while the Task check would
        # read proxy.__class__, resolving the proxy and finalizing the app in the middle of imports
        if isinstance(func, (Proxy, Task)):
            raise TypeError('@single_instance goes below @shared_task, not above it')

        lock_key = f'{func.__module__}.{func.__qualname__}'

        # A bound task passes its self in args, so one wrapper serves both kinds
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock = Lock(lock_key, wait=wait)
            if not lock.locked:
                return

            try:
                return func(*args, **kwargs)
            finally:
                lock.release()

        return wrapper

    # Bare @single_instance gets the function itself. Returning `decorator` then would register
    # every such task as 'sewingworld.lock.decorator', a name beat can't tell them apart by.
    if func is not None:
        return decorator(func)
    return decorator
