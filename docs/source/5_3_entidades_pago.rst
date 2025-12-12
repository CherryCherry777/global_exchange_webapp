5.3 Entidades de pago/cobro
===========================

Las entidades representan a los proveedores externos (bancos, pasarelas de pago, billeteras) con los que el sistema interactúa para procesar transacciones financieras.

Modelo de datos
---------------

**Modelo:** ``Entidad``

**Campos principales:**

- ``nombre``: Nombre comercial de la entidad (ej: "Banco Continental", "Stripe", "Tigo Money").
- ``tipo``: Tipo de entidad (banco, PSP, billetera electrónica).
- ``codigo``: Código interno o identificador único.
- ``pais``: País de operación de la entidad.
- ``activo``: Indica si la entidad está habilitada en el sistema.
- ``logo``: Imagen del logo para identificación visual.

Registrar entidades
-------------------

**Acceso:**

Menú → Configuración → Entidades

**Proceso de registro:**

1. Crear nueva entidad.
2. Ingresar nombre comercial y tipo.
3. Asignar código identificador único.
4. Seleccionar país de operación.
5. Subir logo (opcional pero recomendado).
6. Guardar el registro.

**Tipos de entidades:**

- **Bancos**: Instituciones financieras tradicionales para transferencias.
- **PSP (Payment Service Providers)**: Proveedores de servicios de pago como Stripe, PayPal.
- **Billeteras**: Servicios de dinero electrónico como Tigo Money, Mercado Pago.
- **Corresponsales**: Agentes o puntos de cobro asociados.

Vincular entidades con métodos
------------------------------

**Asociación con MedioPago / MedioCobro:**

Cada método de pago o cobro debe estar vinculado a una entidad que lo procesa:

1. Al crear un método de pago, seleccionar la entidad responsable.
2. Configurar los parámetros específicos de la entidad:
   - ``provider_id``: Identificador en el sistema del proveedor.
   - ``api_key``: Clave de API para autenticación.
   - ``webhook_url``: URL para recibir notificaciones.
   - ``ambiente``: Sandbox o producción.

**Configuración de cuentas:**

- ``CuentaBancariaNegocio``: Cuenta propia del negocio en un banco.
- ``Billetera``: Billetera del negocio en un proveedor de dinero electrónico.

**Ejemplo de vinculación:**

- Entidad: "Banco Itaú" → Cuenta bancaria de cobro #12345.
- Entidad: "Stripe" → Método de pago "Tarjeta de crédito".

Gestión de credenciales
-----------------------

**Almacenamiento seguro:**

- Las credenciales de API deben almacenarse cifradas.
- Usar variables de entorno para claves sensibles en producción.
- No incluir credenciales en el código fuente ni en logs.

**Metadatos de configuración:**

- ``provider_id``: Identificador del comercio en el proveedor.
- ``api_key``: Clave para autenticación en API.
- ``secret_key``: Clave secreta para firmas y validaciones.
- ``webhook_secret``: Secreto para validar webhooks entrantes.

**Rotación de credenciales:**

- Establecer política de rotación periódica (ej: cada 90 días).
- Documentar el proceso de actualización de claves.
- Mantener período de coexistencia durante la transición.

Consideraciones de compliance
-----------------------------

**Seguridad de datos:**

- Cifrar IBAN, números de cuenta y claves en reposo.
- Usar TLS para todas las comunicaciones con proveedores.
- Implementar control de acceso basado en roles.

**Auditoría:**

- Registrar todos los cambios en configuración de entidades.
- Mantener historial de quién modificó credenciales y cuándo.
- Alertar sobre accesos inusuales a configuraciones sensibles.

**Permisos:**

- Solo administradores de nivel superior pueden crear/editar entidades.
- Separar permisos de visualización y edición.
- Requerir doble autorización para cambios críticos.

**Cumplimiento normativo:**

- Verificar que las entidades cumplan regulaciones locales (SIB, BCP, etc.).
- Mantener documentación de contratos y acuerdos.
- Revisar periódicamente el estado regulatorio de cada entidad.
