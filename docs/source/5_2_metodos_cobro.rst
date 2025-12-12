5.2 Métodos de cobro globales
=============================

Tipos de métodos de cobro
-------------------------

- `MedioCobro`: cuenta bancaria, billetera de cobro, pasarela de pago para recibir fondos.
- `CuentaBancariaCobro`, `BilleteraCobro` y otras entidades que permiten recibir y reconciliar ingresos.

Configuración
--------------

- Registrar credenciales y detalles de conciliación en la UI (`CuentaBancariaCobro` o `BilleteraCobro`).
- Configurar webhooks y endpoints seguros para notificaciones de pago; validar firmas.

Operaciones
-----------

- Flujo típico: recibir notificación del proveedor → validar y conciliar → actualizar saldo interno y registros.
- Exponer vistas para ver el estado de cobros y exportar registros para contabilidad.
