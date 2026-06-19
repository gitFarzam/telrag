import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django_project.settings")

celery = Celery('django_project')

celery.config_from_object("django.conf:settings",namespace="CELERY")
# celery.autodiscover_tasks()

# Configure Celery to survive disconnects
celery.conf.update(
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=None,
)

# log
celery.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(task_name)s: %(message)s',
)