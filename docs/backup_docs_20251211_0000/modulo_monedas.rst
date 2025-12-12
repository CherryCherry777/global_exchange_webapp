```restructuredtext
Monedas
=======

Descripción
-----------

Este módulo agrupa los modelos y utilidades relacionadas con las monedas soportadas por la plataforma: denominaciones, históricos y sincronizaciones.

Modelos importantes
-------------------

.. list-table:: Modelos relevantes
   :widths: 20 80
   :header-rows: 0

   * - `Currency` - Moneda principal (código, nombre, símbolo, decimales, banderas, flags para sincronización).
   * - `CurrencyDenomination` - Denominaciones o fracciones (p. ej. billetes y monedas físicas) asociadas a una moneda.
   * - `CurrencyHistory` - Registros históricos de cotización y/o cambios para una moneda.

Autodoc (clases)
-----------------

Las clases pueden ser documentadas con `autoclass` para mostrar campos y métodos:

.. autoclass:: webapp.models.Currency
   :members:
   :noindex:

.. autoclass:: webapp.models.CurrencyDenomination
   :members:
   :noindex:

.. autoclass:: webapp.models.CurrencyHistory
   :members:
   :noindex:

Vistas y uso
------------

- Administración: vistas CRUD para `Currency` en el panel interno (`manage_currencies`, `create_currency`, etc.).
- Sincronización: hay tareas y señales que sincronizan banderas/denominaciones y registran `CurrencyHistory`.

Ejemplo rápido (obtener moneda por código):

.. code-block:: python

   from webapp.models import Currency
   eur = Currency.objects.get(code='EUR')
   print(eur.symbol, eur.decimals)

Notas
-----

- Evita documentar `webapp.models` completo en múltiples páginas para no generar advertencias duplicadas de autodoc. Usa `:noindex:` o centraliza la documentación de modelos cuando sea posible.

```