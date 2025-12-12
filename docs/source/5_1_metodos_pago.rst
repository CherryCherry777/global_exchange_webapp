5.1 Métodos de pago globales
=============================

Los métodos de pago definen las formas en que los clientes pueden realizar pagos al sistema durante operaciones de compra de divisas.

Modelo de datos
---------------

**Modelos principales:**

- ``MedioPago``: Representa un método de pago configurado en el sistema.
- ``TipoPago``: Clasifica los métodos de pago por tipo (tarjeta, transferencia, efectivo, etc.).

**Campos de MedioPago:**

- ``nombre``: Nombre descriptivo del método (ej: "Tarjeta Visa", "Transferencia Bancaria").
- ``tipo_pago``: Referencia al tipo de pago (``TipoPago``).
- ``moneda``: Moneda en la que opera el método.
- ``proveedor``: Identificador del proveedor de servicios de pago (PSP).
- ``activo``: Indica si el método está disponible para transacciones.
- ``modo``: Entorno de operación (sandbox/producción).

Tipos de métodos de pago
------------------------

**Tarjetas de crédito/débito:**

- Procesamiento mediante integración con pasarelas (Stripe, PayPal, etc.).
- Tokenización de datos para cumplimiento PCI-DSS.
- Soporte para pagos recurrentes y guardado de métodos.

**Transferencia bancaria:**

- Registro de cuentas destino para recibir fondos.
- Verificación manual o automática de depósitos.
- Tiempos de acreditación según el banco.

**Billeteras electrónicas:**

- Integración con servicios como mercado Pago, Tigo Money, etc.
- Notificaciones en tiempo real mediante webhooks.

**Efectivo:**

- Pago en punto de venta (terminal/caja).
- Control de denominaciones y arqueo.

Configuración de métodos de pago
--------------------------------

**Acceso:**

Menú → Configuración → Métodos de pago

**Proceso de configuración:**

1. Crear nuevo método de pago o editar existente.
2. Seleccionar el tipo de pago correspondiente.
3. Configurar credenciales del proveedor:
   - API Key (clave de API).
   - Secret Key (clave secreta).
   - Webhook URL (endpoint para notificaciones).
4. Definir moneda y límites aplicables.
5. Seleccionar modo (sandbox para pruebas, producción para operación real).
6. Activar el método y guardar.

**Integración con Stripe:**

- Configurar ``STRIPE_SECRET_KEY`` en variables de entorno.
- Registrar ``STRIPE_WEBHOOK_SECRET`` para validar eventos.
- Los tokens de tarjeta se gestionan directamente en Stripe, nunca en el sistema.

Pruebas y validación
--------------------

**Modo sandbox:**

- Usar credenciales de prueba del proveedor.
- Simular transacciones sin movimiento real de fondos.
- Verificar el flujo completo: autorización, captura, notificación.

**Logs de sincronización:**

- Mantener registro de todas las interacciones con el PSP.
- Almacenar respuestas para diagnóstico de problemas.
- Configurar alertas para errores repetidos.

Buenas prácticas de seguridad
-----------------------------

- **Nunca almacenar datos sensibles**: Números de tarjeta, CVV u otros datos deben tokenizarse en el PSP.
- **Cifrado de credenciales**: Las API keys deben almacenarse en variables de entorno, no en código.
- **Validación de webhooks**: Verificar firmas de los eventos recibidos.
- **Permisos restringidos**: Solo administradores pueden habilitar/deshabilitar métodos de pago.
- **Auditoría**: Registrar quién modifica la configuración de métodos de pago.
- **Rotación de claves**: Cambiar credenciales periódicamente según políticas de seguridad.
