6.2 Conversión de divisas
=========================

Actualizar y calcular conversiones
---------------------------------

- Uso de `Currency` y `CurrencyHistory` para obtener tasas actuales y pasadas.
- Funciones de cálculo: aplicar `rate_buy`/`rate_sell`, redondeo según `decimals` de la moneda.

Conversión en código
---------------------

.. code-block:: python

   from webapp.models import Currency
   def convert(amount, from_code, to_code):
       from_cur = Currency.objects.get(code=from_code)
       to_cur = Currency.objects.get(code=to_code)
       rate = get_rate(from_cur, to_cur)  # función interna
       return round(amount * rate, to_cur.decimals)

Cotizaciones históricas
------------------------

- `api_currency_history` proporciona series temporales para gráficos y auditoría.
- Asegúrate de consultar `CurrencyHistory` con filtros por rango de fechas.

Consideraciones
---------------

- Aplicar margen/comisión por categoría de cliente si corresponde.
- Registrar la fuente de la tasa (manual vs API) para trazabilidad.
