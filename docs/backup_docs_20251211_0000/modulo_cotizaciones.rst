```restructuredtext
Cotizaciones
=============

Descripción
-----------

Contiene las vistas y utilidades para obtener cotizaciones históricas y actuales de las monedas soportadas por la plataforma. Incluye endpoints API usados por el frontend y funciones de conversión.

Endpoints y vistas relevantes
----------------------------

- `api_currency_history` : endpoint API que devuelve el histórico de cotizaciones para una moneda (usado por gráficos y widgets en el frontend).
- Vistas de cálculo y conversión (ej.: `convert_currency`, `get_sell_buy_rates`) que toman `Currency` y denominaciones y devuelven montos convertidos.

Autodoc (funciones y vistas)
----------------------------

.. automodule:: webapp.views.cotizaciones
   :members:
   :noindex:

Ejemplo de uso (API):

.. code-block:: http

   GET /api/currency-history/?currency=USD&days=30

Ejemplo de consumo en Python:

.. code-block:: python

   import requests
   resp = requests.get('http://localhost:8000/api/currency-history/', params={'currency':'USD','days':30})
   data = resp.json()

Consideraciones
---------------

- Asegúrate de que `webapp.models.Currency` tenga la configuración correcta de decimales antes de mostrar montos.
- Corrige docstrings con indentación incorrecta (p. ej. errores en `api_currency_history`) para evitar fallos en la compilación de Sphinx.

```