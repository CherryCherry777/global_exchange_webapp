4.1 Monedas
===========

Monedas disponibles
-------------------

- Modelo: `Currency` (ver `webapp.models`) contiene campos como `code`, `name`, `symbol`, `decimals`, `flag_image`, `is_active`.
- Listado de monedas: la interfaz de administración muestra todas las monedas con su estado (activo/inactivo) y opciones para editar.

Activar / desactivar monedas
----------------------------

- La acción de activar/desactivar controla si una moneda aparece en los formularios de transacción y en el frontend.
- Vistas: `manage_currencies`, `toggle_currency_active` o acciones equivalentes en admin.
- Buenas prácticas: desactivar una moneda no elimina su histórico; notificar a usuarios si una moneda deja de estar disponible.

Consideraciones
---------------

- Antes de desactivar una moneda, asegúrate de revisar transacciones pendientes o saldos asociados.
- Se recomienda mantener una documentación de cambios de políticas de monedas en la sección de cambios operativos.
