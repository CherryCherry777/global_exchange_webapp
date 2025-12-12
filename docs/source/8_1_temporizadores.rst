8.1 Temporizadores
===================

Los temporizadores controlan aspectos críticos relacionados con sesiones de usuario, expiración de tokens y ejecución de tareas programadas.

Configuración de sesiones
-------------------------

**Parámetros de sesión en Django:**

Los siguientes parámetros se configuran en ``settings.py``:

- ``SESSION_COOKIE_AGE``: Duración de la sesión en segundos.
  - Valor por defecto: 1209600 (2 semanas).
  - Valor recomendado para producción: 3600-28800 (1-8 horas).

- ``SESSION_EXPIRE_AT_BROWSER_CLOSE``: Si es ``True``, la sesión expira al cerrar el navegador.
  - Valor por defecto: ``False``.
  - Recomendado para entornos de alta seguridad: ``True``.

- ``SESSION_SAVE_EVERY_REQUEST``: Si es ``True``, actualiza la expiración en cada petición.
  - Valor por defecto: ``False``.
  - Recomendado para mantener sesión activa: ``True``.

**Ejemplo de configuración:**

.. code-block:: python

   # settings.py
   SESSION_COOKIE_AGE = 3600  # 1 hora
   SESSION_EXPIRE_AT_BROWSER_CLOSE = True
   SESSION_SAVE_EVERY_REQUEST = True
   SESSION_COOKIE_SECURE = True  # Solo HTTPS
   SESSION_COOKIE_HTTPONLY = True  # No accesible desde JavaScript

Timeout por inactividad
-----------------------

**Implementación de timeout:**

Para cerrar sesión después de un período de inactividad:

1. Middleware que registra la última actividad.
2. Comparación con el tiempo actual en cada petición.
3. Logout automático si supera el umbral.

**Configuración:**

- ``INACTIVITY_TIMEOUT``: Segundos de inactividad antes de logout.
- Valor típico: 900-1800 (15-30 minutos).

**Forzar logout al cambiar credenciales:**

Cuando se modifican contraseñas o permisos críticos:

1. Invalidar todas las sesiones activas del usuario.
2. Forzar nuevo inicio de sesión.

Expiración de tokens
--------------------

**Tokens de API:**

- Configurar tiempo de vida de tokens de autenticación.
- Implementar refresh tokens para renovación sin re-login.

**Tokens de recuperación de contraseña:**

- ``PASSWORD_RESET_TIMEOUT``: Segundos de validez del enlace.
- Valor por defecto Django: 259200 (3 días).
- Valor recomendado: 3600-86400 (1-24 horas).

Alertas automáticas
-------------------

**Tipos de alertas temporales:**

- Terminales offline por más de X minutos.
- Límites de intercambio cerca de agotarse.
- Cotizaciones no actualizadas en X horas.
- Transacciones pendientes de conciliación.
- Tareas programadas que no se ejecutaron.

**Configuración de alertas:**

Las alertas se configuran mediante tareas periódicas en ``webapp/tasks.py``:

.. code-block:: python

   from celery import shared_task
   from datetime import timedelta
   from django.utils import timezone

   @shared_task
   def check_offline_terminals():
       """
       Verifica terminales sin actividad y envía alertas.
       """
       threshold = timezone.now() - timedelta(minutes=15)
       offline_terminals = Tauser.objects.filter(
           ultima_sincronizacion__lt=threshold,
           estado='online'
       )
       for terminal in offline_terminals:
           send_alert(f"Terminal {terminal.tauser_id} offline")
           terminal.estado = 'offline'
           terminal.save()

**Herramientas de alerting:**

- **Email**: Configurar ``EMAIL_BACKEND`` y credenciales SMTP.
- **PagerDuty/Opsgenie**: Integración para incidentes críticos.
- **Slack/Teams**: Webhooks para notificaciones de equipo.

**Programación de tareas:**

Usar Celery Beat o cron para ejecutar verificaciones:

- Cada 5 minutos: verificar terminales offline.
- Cada hora: verificar cotizaciones desactualizadas.
- Diariamente: verificar límites próximos a reset.

Documentación de valores
------------------------

**Registro de configuración:**

Documentar todos los temporizadores en un archivo centralizado:

.. code-block:: text

   # Archivo: docs/TIMEOUTS.md
   
   ## Sesiones
   - SESSION_COOKIE_AGE: 3600 (1 hora)
   - INACTIVITY_TIMEOUT: 1800 (30 minutos)
   
   ## Tokens
   - PASSWORD_RESET_TIMEOUT: 86400 (24 horas)
   - API_TOKEN_LIFETIME: 3600 (1 hora)
   
   ## Alertas
   - TERMINAL_OFFLINE_THRESHOLD: 15 minutos
   - RATE_UPDATE_MAX_AGE: 4 horas

Buenas prácticas
----------------

- Definir valores diferentes por entorno (desarrollo, staging, producción).
- Probar cambios de timeout en staging antes de producción.
- Documentar el propósito de cada temporizador.
- Incluir pruebas automatizadas que validen comportamiento de expiración.
- Revisar periódicamente los valores según necesidades operativas.
