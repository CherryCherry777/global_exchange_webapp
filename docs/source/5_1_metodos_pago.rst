5.1 Métodos de pago globales
=============================

Tipos de métodos de pago
------------------------

- `MedioPago` / `TipoPago` (ver `webapp.models`): tarjeta, transferencia bancaria, billetera, otros.
- Cada método puede tener parámetros de configuración (p. ej. provider, api_key, modo sandbox/producción).

Configuración
--------------

- Formularios: configurar credenciales y opciones en la UI de administración (`MedioPago` CRUD).
- Integraciones: tokens y webhooks están administrados por proveedores externos (p. ej. Stripe).
- Pruebas: usar modo `sandbox` cuando esté disponible; mantener logs de sincronización.

Buenas prácticas
---------------

- No almacenar datos sensibles (números de tarjeta) en texto claro — usar tokenización del PSP.
- Revisar permisos para quién puede habilitar/deshabilitar un `MedioPago`.
