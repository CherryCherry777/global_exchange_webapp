7.2 Configurar terminales
=========================

Esta sección describe el proceso completo para registrar y configurar un nuevo terminal (T-auser) en el sistema.

Requisitos previos
------------------

**Hardware:**

- Dispositivo compatible (PC, laptop, tablet) con navegador web moderno.
- Conexión de red estable (cableada preferiblemente para puntos fijos).
- Impresora térmica para comprobantes (opcional pero recomendado).
- Lector de código de barras/QR (opcional).

**Software:**

- Sistema operativo actualizado (Windows 10+, Linux, macOS).
- Navegador web Chrome, Firefox o Edge en versión reciente.
- Cliente de sincronización (si se requiere modo offline).

**Credenciales:**

- ``tauser_id``: Identificador único asignado por el administrador.
- ``api_key``: Clave de autenticación para el terminal.
- URL del servidor backend.

Pasos de configuración
----------------------

**1. Registrar terminal en el sistema:**

Desde el panel de administración:

1. Acceder a Menú → Configuración → Terminales.
2. Hacer clic en "Nuevo terminal".
3. Completar los datos:
   - ``tauser_id``: Identificador único (ej: "TERM-001").
   - ``nombre``: Nombre descriptivo (ej: "Caja Principal Centro").
   - ``ubicacion``: Dirección o descripción del lugar.
   - ``sucursal``: Seleccionar la sucursal correspondiente.
   - ``responsable``: Usuario encargado del terminal.
4. Guardar el registro.

**2. Generar credenciales:**

1. En la ficha del terminal, ir a "Seguridad".
2. Hacer clic en "Generar API Key".
3. Copiar la clave generada (solo se muestra una vez).
4. Opcionalmente, generar certificado para TLS mutuo.

**3. Configurar el dispositivo:**

1. En el dispositivo físico, acceder a la configuración del cliente.
2. Ingresar la URL del servidor: ``https://api.example.com/``.
3. Ingresar el ``tauser_id`` y ``api_key``.
4. Configurar la zona horaria del dispositivo (debe coincidir con el servidor).
5. Guardar y probar conexión.

**4. Verificar conectividad:**

1. El terminal debe aparecer como "Online" en el panel.
2. Verificar que la última sincronización sea reciente.
3. Realizar una transacción de prueba.

Configuración de caja inicial
-----------------------------

**Asignar fondo de caja:**

1. Ir a la ficha del terminal → "Denominaciones".
2. Ingresar la cantidad inicial de cada denominación.
3. Registrar el monto total como fondo de caja.
4. Confirmar con firma o aprobación del supervisor.

**Denominaciones típicas:**

- Billetes: 100.000, 50.000, 20.000, 10.000, 5.000, 2.000 (PYG).
- Monedas: 1.000, 500, 100, 50 (PYG).
- Divisas: Billetes USD, EUR según operación.

Opciones avanzadas
------------------

**Modo offline:**

- Habilitar almacenamiento local de transacciones.
- Configurar límite de transacciones en modo offline.
- Definir política de sincronización (automática al reconectar, manual).

**Límites por terminal:**

- Monto máximo por transacción.
- Monto máximo diario.
- Tipos de operaciones permitidas.

**Configuración de impresión:**

- Seleccionar impresora por defecto.
- Configurar formato de comprobante.
- Habilitar/deshabilitar impresión automática.

**Usuarios autorizados:**

- Asignar usuarios que pueden operar el terminal.
- Configurar permisos específicos por usuario/terminal.

Solución de problemas de conexión
---------------------------------

**Terminal no conecta:**

1. Verificar conectividad de red (ping al servidor).
2. Confirmar que la URL del servidor es correcta.
3. Verificar que el ``api_key`` no haya expirado.
4. Revisar firewall y puertos requeridos (443 para HTTPS).

**Error de sincronización de hora:**

1. Verificar configuración de zona horaria.
2. Sincronizar reloj del dispositivo con servidor NTP.
3. Diferencias mayores a 5 minutos pueden causar rechazos.
