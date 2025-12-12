7.1 ¿Qué son los T-ausers?
==========================

Los T-ausers (Terminal Users) son entidades que representan terminales físicas o puntos de venta conectados al sistema Global Exchange, utilizados para procesar operaciones de cambio de divisas en ubicaciones físicas.

Definición y propósito
----------------------

**¿Qué es un T-auser?**

Un T-auser es una representación lógica de:

- Un dispositivo físico (computadora, tablet, terminal POS) ubicado en un punto de atención.
- Una caja registradora virtual con control de efectivo y denominaciones.
- Un punto de operación que puede procesar transacciones de forma autónoma o conectada.

**Diferencia con usuarios regulares:**

- Los usuarios regulares son personas que inician sesión y realizan operaciones.
- Los T-ausers son dispositivos/terminales que procesan transacciones, operados por usuarios.
- Un usuario puede operar diferentes T-ausers según su turno o ubicación.

Casos de uso
------------

**1. Operaciones en punto de venta:**

- Procesar compra/venta de divisas en ventanilla.
- Registrar el efectivo recibido y entregado por denominación.
- Emitir comprobantes de transacción.

**2. Control de efectivo:**

- Mantener inventario de billetes y monedas por denominación.
- Registrar entradas y salidas de efectivo.
- Controlar el saldo de caja del terminal.

**3. Monitoreo de operaciones:**

- Seguimiento de transacciones por terminal.
- Análisis de productividad por punto de venta.
- Detección de anomalías o patrones inusuales.

**4. Soporte a modo offline:**

- Almacenar transacciones localmente cuando no hay conectividad.
- Sincronizar con el servidor central al recuperar conexión.
- Garantizar continuidad operativa.

Modelo y relaciones
-------------------

**Modelo principal:** ``Tauser`` / ``TauserTerminal`` (ubicado en ``webapp/models.py``)

**Campos principales:**

- ``tauser_id``: Identificador único del terminal (ej: "TERM-001", "CAJA-SUR-01").
- ``nombre``: Nombre descriptivo del terminal.
- ``ubicacion``: Dirección o descripción de la ubicación física.
- ``sucursal``: Sucursal a la que pertenece el terminal.
- ``estado``: Estado actual (online, offline, mantenimiento, deshabilitado).
- ``ultima_sincronizacion``: Timestamp de la última comunicación con el servidor.
- ``ip_address``: Dirección IP del dispositivo.
- ``version_software``: Versión del software instalado en el terminal.

**Relaciones:**

- ``Transaccion``: Cada transacción registra el T-auser donde se procesó.
- ``Billetera``: Cada T-auser tiene asociada una billetera para control de saldo.
- ``CajaDenominacion``: Registro de efectivo por denominación en el terminal.
- ``Usuario``: Usuarios autorizados a operar el terminal.

Seguridad y autenticación
-------------------------

**Métodos de autenticación:**

- **API Key**: Clave única asignada a cada terminal para autenticar peticiones.
- **Certificado**: Certificado digital para comunicación segura (TLS mutuo).
- **Token de sesión**: Tokens de corta duración renovables automáticamente.

**Registro de actividad:**

- Cada operación registra el T-auser y el usuario que la ejecutó.
- Se almacena la IP de origen y timestamp de cada acción.
- Los intentos de acceso fallidos generan alertas.

**Buenas prácticas:**

- Rotar API keys periódicamente.
- Restringir acceso por IP cuando sea posible.
- Monitorear intentos de acceso no autorizados.
- Deshabilitar inmediatamente terminales comprometidos.
