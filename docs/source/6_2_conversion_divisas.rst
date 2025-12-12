6.2 Conversión de divisas
=========================

Esta sección describe el mecanismo de conversión de montos entre diferentes divisas, incluyendo el cálculo de tasas y el manejo de precisiones decimales.

Mecanismo de conversión
-----------------------

**Modelos involucrados:**

- ``Currency``: Define las propiedades de cada moneda (decimales, símbolo).
- ``CurrencyHistory``: Almacena el historial de cotizaciones.

**Fórmula de conversión:**

.. code-block:: text

   monto_destino = monto_origen * tasa_conversion
   
   Donde:
   - tasa_conversion = rate_sell (si el cliente compra divisa extranjera)
   - tasa_conversion = rate_buy (si el cliente vende divisa extranjera)

**Precisión y redondeo:**

- Los cálculos internos mantienen precisión completa (Decimal).
- El redondeo se aplica según los decimales configurados para cada moneda.
- El guaraní (PYG) usa 0 decimales; USD/EUR usan 2 decimales.

Función de conversión
---------------------

**Implementación en código:**

.. code-block:: python

   from decimal import Decimal, ROUND_HALF_UP
   from webapp.models import Currency, CurrencyHistory

   def convert(amount, from_code, to_code, operation_type='sell'):
       """
       Convierte un monto de una moneda a otra.
       
       Args:
           amount: Monto a convertir (Decimal o float).
           from_code: Código ISO de la moneda origen.
           to_code: Código ISO de la moneda destino.
           operation_type: 'buy' o 'sell' según el tipo de operación.
       
       Returns:
           Decimal: Monto convertido con redondeo aplicado.
       """
       from_cur = Currency.objects.get(code=from_code)
       to_cur = Currency.objects.get(code=to_code)
       
       # Obtener la última cotización vigente
       history = CurrencyHistory.objects.filter(
           currency=from_cur
       ).order_by('-timestamp').first()
       
       if operation_type == 'buy':
           rate = history.rate_buy
       else:
           rate = history.rate_sell
       
       result = Decimal(str(amount)) * rate
       
       # Aplicar redondeo según decimales de la moneda destino
       precision = Decimal(10) ** -to_cur.decimals
       return result.quantize(precision, rounding=ROUND_HALF_UP)

**Ejemplo de uso:**

.. code-block:: python

   # Convertir 100 USD a PYG (cliente vendiendo dólares)
   monto_pyg = convert(100, 'USD', 'PYG', 'buy')
   # Resultado: 730000 (según cotización de compra)
   
   # Convertir 500000 PYG a USD (cliente comprando dólares)
   monto_usd = convert(500000, 'PYG', 'USD', 'sell')
   # Resultado: 67.12 (según cotización de venta)

Consulta de cotizaciones históricas
-----------------------------------

**Endpoint:** ``api_currency_history``

**Parámetros de consulta:**

- ``currency``: Código de la moneda a consultar.
- ``from_date``: Fecha inicial del rango.
- ``to_date``: Fecha final del rango.
- ``limit``: Número máximo de registros a retornar.

**Respuesta:**

.. code-block:: json

   {
     "currency": "USD",
     "history": [
       {
         "timestamp": "2025-12-12T10:00:00Z",
         "rate_buy": 7300.00,
         "rate_sell": 7350.00,
         "source": "manual"
       },
       {
         "timestamp": "2025-12-11T10:00:00Z",
         "rate_buy": 7280.00,
         "rate_sell": 7330.00,
         "source": "api"
       }
     ]
   }

**Usos del historial:**

- Generación de gráficos de evolución de tasas.
- Verificación de la cotización aplicada en transacciones pasadas.
- Análisis de tendencias para toma de decisiones.
- Auditoría y cumplimiento regulatorio.

Ajustes por categoría de cliente
--------------------------------

**Aplicación de descuentos:**

Las categorías de cliente pueden modificar la tasa efectiva:

.. code-block:: python

   def get_effective_rate(base_rate, cliente, operation_type):
       """
       Calcula la tasa efectiva considerando descuentos de categoría.
       """
       descuento = cliente.categoria.descuento / 100
       
       if operation_type == 'buy':
           # Mejor precio para el cliente (tasa más alta)
           return base_rate * (1 + descuento)
       else:
           # Menor costo para el cliente (tasa más baja)
           return base_rate * (1 - descuento)

**Ejemplo:**

- Tasa base venta USD: 7350 PYG
- Cliente VIP (descuento 5%): 7350 * 0.95 = 6982.50 PYG
- El cliente VIP paga menos por cada dólar.

Consideraciones técnicas
------------------------

- **Usar Decimal**: Evitar float para cálculos financieros por imprecisión.
- **Registrar fuente**: Almacenar si la tasa provino de API o fue manual.
- **Cache de cotizaciones**: Considerar cache para reducir consultas a BD.
- **Timezone**: Almacenar timestamps en UTC para consistencia.
