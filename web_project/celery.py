import os
from celery import Celery
from celery.schedules import crontab

# Configura el entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_project.settings")

app = Celery("web_project")

# Cargar configuración de settings.py con prefijo CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-descubrir tareas en todas las apps
app.autodiscover_tasks()
