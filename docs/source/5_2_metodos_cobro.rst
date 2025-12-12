5.2 Métodos de cobro globales
=============================

Los métodos de cobro definen las formas en que el negocio recibe fondos de los clientes y de operaciones de venta de divisas.

Modelo de datos
---------------

**Modelos principales:**

- ``MedioCobro``: Representa un canal para recibir fondos.
- ``CuentaBancariaCobro``: Cuenta bancaria configurada para recibir transferencias.
- ``BilleteraCobro``: Billetera electrónica para recepción de pagos digitales.

**Campos de CuentaBancariaCobro:**

- ``banco``: Nombre de la institución bancaria.
- ``numero_cuenta``: Número de cuenta bancaria.
- ``tipo_cuenta``: Tipo de cuenta (corriente, ahorro).
- ``titular``: Nombre del titular de la cuenta.
- ``moneda``: Moneda de la cuenta.
- ``activo``: Indica si está disponible para recibir fondos.

**Campos de BilleteraCobro:**

- ``proveedor``: Nombre del servicio de billetera.
- ``identificador``: Número de teléfono o ID de la billetera.
- ``webhook_url``: URL para recibir notificaciones de pago.
- ``api_key``: Credenciales de integración.

Tipos de métodos de cobro
-------------------------

**Cuenta bancaria:**

- Recepción de transferencias nacionales e internacionales.
- Conciliación manual o automática de depósitos.
- Soporte para múltiples cuentas por moneda.

**Billetera de cobro:**

- Recepción de pagos desde billeteras electrónicas.
- Notificaciones instantáneas mediante webhooks.
- Integración con APIs de proveedores locales.

**Pasarela de pago:**

- Recepción de pagos con tarjeta.
- Los fondos se depositan en cuenta bancaria asociada.
- Reportes de transacciones desde el panel del proveedor.

Configuración de métodos de cobro
---------------------------------

**Acceso:**

Menú → Configuración → Métodos de cobro

**Registrar cuenta bancaria:**

1. Crear nueva cuenta bancaria de cobro.
2. Ingresar datos bancarios completos (banco, número, tipo, titular).
3. Seleccionar la moneda de la cuenta.
4. Configurar parámetros de conciliación.
5. Activar y guardar.

**Registrar billetera:**

1. Crear nueva billetera de cobro.
2. Seleccionar el proveedor del servicio.
3. Ingresar identificador (teléfono o email).
4. Configurar credenciales de API y webhook.
5. Validar conexión mediante prueba.
6. Activar y guardar.

**Configuración de webhooks:**

- Registrar la URL del endpoint en el proveedor de pagos.
- Configurar el secreto para validación de firmas.
- Implementar lógica de reintentos para notificaciones fallidas.

Operaciones de conciliación
---------------------------

**Flujo de conciliación:**

1. El sistema recibe notificación del proveedor (webhook) o detecta depósito.
2. Se valida la autenticidad de la notificación (firma, origen).
3. Se identifica la transacción asociada.
4. Se actualiza el estado de la transacción a "pagada".
5. Se actualiza el saldo interno correspondiente.
6. Se genera registro para contabilidad.

**Vistas de gestión:**

- Listado de cobros pendientes de conciliación.
- Historial de cobros conciliados.
- Exportación de registros para contabilidad.

**Conciliación manual:**

- Para transferencias bancarias sin notificación automática.
- El operador verifica el depósito y lo vincula a la transacción.
- Se registra la fecha y hora de conciliación.

Buenas prácticas
----------------

- **Validar todas las notificaciones**: Verificar firmas antes de procesar.
- **Logs detallados**: Registrar cada interacción para diagnóstico.
- **Alertas**: Configurar notificaciones para conciliaciones pendientes.
- **Seguridad**: Cifrar datos sensibles (números de cuenta) en reposo.
- **Revisión diaria**: Verificar que no queden cobros sin conciliar.
