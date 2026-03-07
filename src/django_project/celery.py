import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django_project.settings")

celery = Celery('django_project')

celery.config_from_object("django.conf:settings",namespace="CELERY")
celery.autodiscover_tasks()
