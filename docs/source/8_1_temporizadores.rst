8.1 Temporizadores
===================

Configurar tiempos de sesión
----------------------------

- Parámetros típicos: tiempo de inactividad antes de logout, duración de la sesión, tiempo de expiración de tokens.
- Ubicación de configuración: `settings.py` (variables como `SESSION_COOKIE_AGE`, `SESSION_EXPIRE_AT_BROWSER_CLOSE`) o en la UI operativa si está expuesto.

Implementación recomendada
---------------------------

- Definir valores por entorno (desarrollo, staging, producción).
- Forzar cierre de sesión al cambiar credenciales críticas o permisos.

Alertas automáticas
-------------------

- Configurar alertas y cron jobs para eventos importantes: conexiones fallidas repetidas, terminales offline, límites alcanzados.
- Herramientas: sistemas de alerting (PagerDuty, Opsgenie) o correo electrónico mediante tareas periódicas en `webapp/tasks.py`.

Buenas prácticas
---------------

- Documentar los valores por defecto y cómo ajustarlos en `README.md` o en un archivo de operaciones.
- Añadir pruebas que validen expiraciones y comportamiento esperado de sesión.
