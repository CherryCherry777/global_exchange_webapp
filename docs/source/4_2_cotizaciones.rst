4.2 Cotizaciones
=================

Las cotizaciones definen los tipos de cambio entre monedas, fundamentales para calcular los montos en operaciones de compra y venta de divisas.

Conceptos básicos
-----------------

**Tasa de compra (buy_rate):**

Precio al que el sistema compra una moneda extranjera. Es el tipo de cambio aplicado cuando un cliente vende divisas.

**Tasa de venta (sell_rate):**

Precio al que el sistema vende una moneda extranjera. Es el tipo de cambio aplicado cuando un cliente compra divisas.

**Spread:**

Diferencia entre la tasa de venta y la tasa de compra. Representa el margen de ganancia en cada operación.

Actualizar tasas de cambio
--------------------------

**Fuentes de cotización:**

- **APIs externas**: Sincronización automática con proveedores de datos de mercado.
- **Configuración manual**: Ingreso directo de tasas por operadores autorizados.
- **Tareas programadas**: Actualización periódica mediante jobs del sistema.

**Vistas y endpoints:**

- Panel administrativo para edición manual de cotizaciones.
- Endpoints de API para integración con fuentes externas.
- Tareas periódicas que sincronizan ``CurrencyHistory`` automáticamente.

**Proceso de actualización manual:**

1. Acceder a Cotizaciones → Actualizar tasas.
2. Seleccionar la moneda a actualizar.
3. Ingresar nueva tasa de compra (buy_rate).
4. Ingresar nueva tasa de venta (sell_rate).
5. Verificar que el spread sea coherente con las políticas.
6. Confirmar y guardar; el sistema registra el cambio en el historial.

Historial de cotizaciones
-------------------------

**Modelo:** ``CurrencyHistory``

**Campos principales:**

- ``currency``: Referencia a la moneda.
- ``rate_buy``: Tasa de compra en ese momento.
- ``rate_sell``: Tasa de venta en ese momento.
- ``timestamp``: Fecha y hora del registro.
- ``source``: Origen de la cotización (manual, API, sistema).
- ``updated_by``: Usuario que realizó la actualización (si fue manual).

**Consulta del historial:**

- Endpoint: ``api_currency_history``
- Permite filtrar por moneda, rango de fechas y fuente.
- Útil para análisis de tendencias y auditoría.

**Uso del historial:**

- Generación de gráficos de evolución de tasas.
- Verificación de cotización aplicada en transacciones pasadas.
- Análisis de spread histórico.

Cotizaciones por categoría de cliente
-------------------------------------

**Personalización de tasas:**

El sistema permite aplicar condiciones especiales según la categoría del cliente:

- **Clientes VIP**: Pueden recibir tasas preferenciales con menor spread.
- **Corporativos**: Tasas negociadas según contrato.
- **Estándar**: Tasas públicas sin modificadores.

**Implementación:**

- Las funciones de cálculo consideran ``Cliente.categoria`` para aplicar multiplicadores.
- El descuento de la categoría puede afectar el spread efectivo.
- Los ajustes se aplican transparentemente en el cálculo de la transacción.

Buenas prácticas
----------------

- **Trazabilidad**: Registrar siempre la fuente de la tasa (API, manual) en el historial.
- **Pruebas previas**: Probar actualizaciones en staging antes de producción.
- **Comunicación**: Avisar a los operadores cuando hay cambios significativos.
- **Validación**: Verificar que las nuevas tasas sean coherentes (buy_rate < sell_rate).
- **Respaldo**: Exportar historial periódicamente para análisis offline.
- **Monitoreo**: Configurar alertas para variaciones atípicas en tasas de mercado.
