import os
from celery import Celery
from celery.schedules import crontab

# Configura el entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "simulador.settings")

app = Celery("simulador")

# Cargar configuración de settings.py con prefijo CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-descubrir tareas en todas las apps
app.autodiscover_tasks()

# Ejemplo de schedule si quieres un horario fijo
app.conf.beat_schedule = {
    "check-and-send-exchange-rates": {
        "task": "webapp.tasks.check_and_send_exchange_rates",
        "schedule": 60.0,  # cada minuto, revisa si toca enviar
    },
}
