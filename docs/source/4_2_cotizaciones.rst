4.2 Cotizaciones
=================

Actualizar tasas de cambio
--------------------------

- Fuentes: las tasas pueden provenir de sincronizadores externos, APIs o configuraciones manuales en el panel.
- Vistas y tareas: endpoints administrativos para actualizar tasas y tareas periódicas que sincronizan `CurrencyHistory`.

Historial de cotizaciones
-------------------------

- Modelo: `CurrencyHistory` almacena registros con `currency`, `rate_buy`, `rate_sell`, `timestamp`.
- Consultas: `api_currency_history` y vistas internas permiten consultar histórico por rango de fechas.

Cotizaciones por categoría de cliente
-------------------------------------

- Reglas: en algunos casos las cotizaciones pueden ajustarse por categoría de cliente (descuentos, comisiones).
- Implementación: aplicar multiplicadores o márgenes distintos en las funciones de cálculo según `Cliente.categoria`.

Buenas prácticas
---------------

- Registrar la fuente de la tasa (API, manual) en `CurrencyHistory` para trazabilidad.
- Probar actualizaciones en staging antes de aplicarlas en producción; avisar a usuarios cuando haya cambios relevantes.
