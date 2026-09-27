import ast
import json
from importlib import import_module
from django.core.management.base import BaseCommand
from django_celery_results.models import TaskResult


def rerun_task_by_id(task_id):
    # 1. Fetch the logged task result from the database
    task_log = TaskResult.objects.get(task_id=task_id)

    # 2. Dynamically import the task function
    module_name, task_name = task_log.task_name.rsplit('.', 1)
    module = import_module(module_name)
    celery_task = getattr(module, task_name)

    # 3. Deserialize arguments (django-celery-results stores them as stringified JSON)
    # 3. Safely parse args (ensure it becomes a list)
    args = task_log.task_args or []
    if isinstance(args, str):
        args = json.loads(args)
        args = args.strip().replace('\n', '')
        if args.startswith('(') and args.endswith(')'):
            # ast.literal_eval safely parses Python literals like tuples without executing code
            args = ast.literal_eval(args)
        else:
            args = json.loads(args)

    # 4. Safely parse kwargs (ensure it becomes a dictionary)
    kwargs = task_log.task_kwargs or {}
    if isinstance(kwargs, str):
        kwargs = json.loads(kwargs)
        # Handle potential double-serialization (string inside a string)
        if isinstance(kwargs, str):
            kwargs = json.loads(kwargs)

    # 4. Trigger the task again
    new_task = celery_task.delay(*args, **kwargs)
    return new_task.id


class Command(BaseCommand):
    help = 'Rerun celery task'

    def add_arguments(self, parser):
        parser.add_argument('task', nargs='+', type=str)

    def handle(self, *args, **options):
        for task_id in options['task']:
            rerun_task_by_id(task_id)
            self.stdout.write('Successfully rerun task %s' % task_id)
