8.2 Parámetros del sistema
==========================

Descripción
-----------

Esta página documenta los parámetros configurables que afectan el comportamiento de la aplicación: límites, timeouts, opciones de logging, modos de integración, etc.

Ejemplos de parámetros
----------------------

- `ROLE_TIERS`: jerarquía de roles y sus niveles.
- `PROTECTED_ROLES`: roles que no deben eliminarse.
- `SESSION_COOKIE_AGE`: duración de sesión en segundos.
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`: claves para integración con Stripe.

Dónde cambiar parámetros
------------------------

- Preferir variables de entorno y `settings.py` para valores sensibles.
- Para parámetros operativos no sensibles, considerar un modelo `SystemParameter` para edición desde UI.

Auditoría y despliegue
----------------------

- Mantener un historial de cambios en parámetros críticos y documentar el motivo en el changelog.
- Validar cambios en staging antes de aplicarlos en producción.
