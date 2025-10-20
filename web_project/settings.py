from pathlib import Path
import environ
import os
from django.contrib import messages
from django.urls import reverse_lazy
from celery.schedules import crontab
#from .celery import app
from django.conf import settings

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))
else:
    print("⚠️ WARNING: .env file not found at", env_file)

#environ.Env.read_env(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


#print("DB_NAME", env("DB_NAME", default="not set"))

SITE_URL = env('SITE_URL', default='http://127.0.0.1:8000')

# Usuario custom
AUTH_USER_MODEL = 'webapp.CustomUser'

# Autenticación
LOGIN_URL = reverse_lazy('login')
LOGIN_REDIRECT_URL = '/landing/'
LOGOUT_REDIRECT_URL = "login"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="sandbox.smtp.mailtrap.io")
EMAIL_PORT = env.int("EMAIL_PORT", default=2525)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = "Global Exchange <noreply@mailtrap.io>"
SUPPORT_EMAIL = "soporte@tuempresa.com"


# Seguridad
SECRET_KEY = 'django-insecure-)p9*n*q!wuaxfx-f4lnm8($i^606cz*#29!6t5rb2wigihdq-t'
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'webapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'web_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'webapp.context_processors.admin_status',
                'webapp.context_processors.clientes_disponibles',
            ],
        },
    },
]

WSGI_APPLICATION = 'web_project.wsgi.application'

# Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalización
LANGUAGE_CODE = 'es'
#TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'webapp/static'),
]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

#Para activar/desactivar MFA en login
MFA_LOGIN = env.bool('MFA_LOGIN', default=True)

#Para activar/desactivar el envio de correo de tasas al hacer login
CORREO_TASAS_LOGIN = env.bool('CORREO_TASAS_LOGIN', default=True)

#Stripe
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

# Use timezone-aware datetimes
USE_TZ = True
TIME_ZONE = 'America/Asuncion'

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Asuncion'
CELERY_ENABLE_UTC = True  # recommended

CELERY_BEAT_SCHEDULE = {
    "check_exchange_email_schedule": {
        "task": "webapp.tasks.check_and_send_exchange_rates",
        "schedule": 60.0,  # cada 60 segundos
    },
    "cancelar_transacciones_vencidas_cbn": {
        "task": "webapp.tasks.cancelar_transacciones_vencidas_cbn",
        "schedule": crontab(minute="*/2"),  # cada 2 minutos
    },
    "cancelar_transacciones_vencidas_tauser": {
        "task": "webapp.tasks.cancelar_transacciones_vencidas_tauser",
        "schedule": crontab(minute="*/2"),  # cada 2 minutos
    },
    "limpiar_codigos_mfa_cada_hora": {
        "task": "webapp.tasks.cleanup_expired_mfa_codes",
        "schedule": crontab(minute=0, hour="*/1"),  # cada hora
    },
    "check_limite_intercambio_schedule": {
        "task": "webapp.tasks.check_and_reset_limites_intercambio",
        "schedule": 60.0,  # cada 60 segundos
    },
}

MESSAGE_TAGS = {
    messages.SUCCESS: 'success',
    messages.ERROR: 'error',
    messages.WARNING: 'warning',
    messages.INFO: 'info',
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}


"""
Nota: ejecutar estos comandos en la terminal de linux para  que funcionen los correos temporizados

sudo apt install redis-server <- este solo la primera vez, el resto todas las veces


sudo systemctl enable redis-server
sudo systemctl start redis-server

Y para empezar celery (el handler para tareas temporizadas)
#En una terminal separada de manage.py
celery -A web_project worker -l info 

#En OTRA terminal aparte de la del worker
celery -A web_project beat -l info 

todos los cambios en las configuraciones de django requieren matar los procesos celery y reiniciar
pkill -f 'celery'

"""