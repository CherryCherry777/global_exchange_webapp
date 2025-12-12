```restructuredtext
Límites de intercambio
======================

Descripción
-----------

Documenta la configuración de límites por moneda y categoría de cliente, los saldos por cliente y la lógica que evita exceder los topes durante transacciones.

Modelos y objetos clave
-----------------------

.. list-table:: Modelos
   :widths: 20 80
   :header-rows: 0

   * - `LimiteIntercambioConfig` - Configuración por `categoria` + `moneda` con montos máximos por periodo.
   * - `LimiteIntercambioCliente` - Saldo actual (consumido) por cliente para una configuración determinada.
   * - `LimiteIntercambioLog` - Log de consumos y reversos para evitar dobles descuentos.
   * - `LimiteIntercambioScheduleConfig` - Configuración de reseteo (diaria, mensual) para límites.

Autodoc
-------

.. autoclass:: webapp.models.LimiteIntercambioConfig
   :members:
   :noindex:

.. autoclass:: webapp.models.LimiteIntercambioCliente
   :members:
   :noindex:

Vistas y formularios
---------------------

- `limites_intercambio_list` : lista y panel principal de configuración (requiere permiso `view_limiteintercambioconfig`).
- `limites_intercambio_tabla_htmx` : carga la tabla parcial (htmx) usada en la UI.
- `limite_edit` : formulario para crear/editar una configuración.

Lógicas importantes
-------------------

- Las señales y los `LimiteIntercambioLog` protegen contra dobles descuentos y garantizan que las transacciones actualicen los saldos con `select_for_update`.
- Existe una tarea periódica `check_and_reset_limites_intercambio` que resetea saldos según la `LimiteIntercambioScheduleConfig`.

Ejemplo (carga de tabla HTMX):

.. code-block:: http

   GET /limites/cargar-tabla/  (authenticated, with permissions)

```