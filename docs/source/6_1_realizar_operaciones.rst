6.1 Realizar operaciones de compra/venta
=======================================

Introducción
------------

Esta sección documenta el flujo para crear operaciones de compra/venta (intercambios) en la plataforma.

Flujo típico
-----------

1. Selección de moneda origen y destino.
2. Introducir monto y denominación (si aplica).
3. Calcular cotización vigente (buy/sell) y comisiones.
4. Confirmar la operación y procesar la transacción.

Vistas y endpoints
------------------

- `create_exchange` / `compraventa` — vistas que inician y confirman operaciones.
- `api/calculate-quote/` — endpoint que devuelve montos según tasas actuales.

Validaciones
-----------

- Verificar límites del cliente (`LimiteIntercambioCliente`) antes de autorizar.
- Comprobar fondos y métodos de cobro/pago disponibles.
- Registrar `LimiteIntercambioLog` para evitar doble consumo de límite.

Errores comunes y manejo
-----------------------

- Moneda inactiva: rechazar y notificar.
- Límite excedido: informar al usuario y sugerir alternativas.
