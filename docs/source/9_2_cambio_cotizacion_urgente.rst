9.2 Cambio de cotización urgente
================================

Contexto
--------

Procedimiento cuando es necesario actualizar una cotización de forma inmediata (market event, ajuste manual).

Pasos rápidos
------------

1. Validar la necesidad: confirmar la fuente de la variación (API externa, error, evento de mercado).
2. Notificar stakeholders: operaciones y riesgo.
3. Aplicar la cotización: usar la interfaz administrativa o endpoint seguro para cambiar la tasa.
4. Registrar en `CurrencyHistory` la razón y el usuario que aplicó el cambio.
5. Comunicar al frontend y, si aplica, invalidar cachés/obtener nuevas tasas en el cliente.

Rollback y mitigación
---------------------

- Tener un plan de rollback si la cotización aplicada genera efectos indeseados.
- Probar en staging cuando sea posible antes de aplicar en producción.
