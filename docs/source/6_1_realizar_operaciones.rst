6.1 Realizar operaciones de compra/venta
========================================

Esta sección documenta el flujo completo para crear y procesar operaciones de intercambio de divisas en la plataforma.

Conceptos fundamentales
-----------------------

**Operación de compra:**

El cliente vende divisas extranjeras y recibe moneda local. El sistema compra la divisa al ``buy_rate``.

**Operación de venta:**

El cliente compra divisas extranjeras pagando con moneda local. El sistema vende la divisa al ``sell_rate``.

**Comisión:**

Cargo adicional que se aplica a la operación, calculado como porcentaje o monto fijo según configuración.

Flujo de operación
------------------

**Paso 1: Selección de monedas**

- Seleccionar la moneda de origen (la que el cliente entrega).
- Seleccionar la moneda de destino (la que el cliente recibe).
- El sistema verifica que ambas monedas estén activas.

**Paso 2: Ingreso de monto**

- Ingresar el monto a intercambiar.
- Opcionalmente, especificar denominaciones si es efectivo.
- El sistema valida que el monto cumpla con los límites configurados.

**Paso 3: Cálculo de cotización**

- El sistema obtiene la cotización vigente para el par de monedas.
- Se aplica la tasa correspondiente (compra o venta).
- Se calculan las comisiones según la categoría del cliente.
- Se muestra el monto final que recibirá el cliente.

**Paso 4: Confirmación**

- El operador verifica los datos con el cliente.
- Se confirma la operación.
- El sistema crea el registro de transacción.

**Paso 5: Procesamiento**

- Se actualiza el consumo de límites del cliente.
- Se registra el movimiento en las billeteras/cajas correspondientes.
- Se genera comprobante de la operación.

Vistas y endpoints
------------------

**Vistas principales:**

- ``create_exchange``: Formulario para iniciar nueva operación.
- ``compraventa``: Vista alternativa para operaciones de compra/venta.
- ``confirm_transaction``: Confirmación final de la operación.

**Endpoints de API:**

- ``api/calculate-quote/``: Calcula cotización sin crear transacción.
  - Parámetros: ``from_currency``, ``to_currency``, ``amount``.
  - Respuesta: monto calculado, tasa aplicada, comisión, total.

- ``api/create-transaction/``: Crea y procesa la transacción.
  - Requiere autenticación y permisos de operador.

Validaciones del sistema
------------------------

**Validación de límites:**

Antes de autorizar una operación, el sistema verifica:

1. ``LimiteIntercambioCliente``: Consumo acumulado del cliente.
2. ``LimiteIntercambioConfig``: Configuración de límites aplicable.
3. Comparación del monto solicitado contra el límite disponible.

**Validación de fondos:**

- Para operaciones en efectivo: verificar disponibilidad en caja.
- Para operaciones con métodos de pago: verificar estado del método.

**Registro de auditoría:**

- ``LimiteIntercambioLog``: Registra cada consumo de límite para evitar doble conteo.

Manejo de errores
-----------------

**Moneda inactiva:**

- Mensaje: "La moneda seleccionada no está disponible actualmente."
- Acción: El operador debe seleccionar otra moneda o contactar administración.

**Límite excedido:**

- Mensaje: "El monto excede el límite disponible. Límite restante: X."
- Acción: Reducir el monto o solicitar ampliación de límite.

**Error de cotización:**

- Mensaje: "No hay cotización vigente para esta moneda."
- Acción: Verificar que la moneda tenga cotización actualizada.

**Fondos insuficientes:**

- Mensaje: "No hay fondos suficientes en caja para esta operación."
- Acción: Solicitar reposición de fondos o usar otro método.

Consideraciones operativas
--------------------------

- Verificar identidad del cliente antes de procesar operaciones significativas.
- Conservar documentación de respaldo para operaciones que superen umbrales.
- Imprimir comprobante y entregar al cliente.
- Revisar el arqueo de caja al finalizar el turno.
