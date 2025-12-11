Documentación de Módulos - Global Exchange Webapp
==================================================

Esta documentación describe los 23 módulos principales del sistema Global Exchange Webapp, incluyendo su funcionalidad, métodos principales y características técnicas.

.. contents::
   :depth: 2
   :local:

========================================
1. MÓDULO DE AUTENTICACIÓN
========================================

**Script Principal:** ``views.py``
**Métodos:** ``register``, ``verify_email``

Descripción
-----------
El módulo de autenticación maneja el registro de nuevos usuarios y la verificación de correos electrónicos para activar cuentas.

Funcionalidades Principales
----------------------------

**1.1 Registro de Usuarios (register)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py:57``

**Funcionalidad:**
- Procesa el formulario de registro de nuevos usuarios
- Valida datos únicos (username, email)
- Crea usuarios inactivos hasta verificación de email
- Envía email de activación automáticamente
- Asigna rol "Usuario" por defecto

**Flujo de Trabajo:**
1. Usuario completa formulario de registro
2. Sistema valida datos (username único, email único)
3. Usuario se crea con ``is_active=False``
4. Se envía email de verificación
5. Usuario recibe mensaje de confirmación

**Validaciones:**
- Username: solo letras, números, guiones y guiones bajos
- Email: formato válido y único en el sistema
- Password: cumplimiento de políticas de seguridad

**1.2 Verificación de Email (verify_email)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py:83``

**Funcionalidad:**
- Verifica tokens de activación de email
- Activa cuentas de usuario tras verificación exitosa
- Maneja tokens expirados o inválidos

**Parámetros:**
- ``uidb64``: ID del usuario codificado en base64
- ``token``: Token de verificación generado

**Flujo de Trabajo:**
1. Usuario hace clic en enlace de verificación
2. Sistema decodifica ID y valida token
3. Si válido: activa cuenta y redirige a login
4. Si inválido: muestra error y redirige a registro

========================================
2. MÓDULO DE USUARIOS
========================================

**Script Principal:** ``views.py``
**Método:** ``manage_user_roles``

Descripción
-----------
Gestiona la asignación y administración de roles para usuarios del sistema.

Funcionalidades Principales
----------------------------

**2.1 Gestión de Roles de Usuario (manage_user_roles)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py:137``

**Funcionalidad:**
- Lista todos los usuarios con sus roles asignados
- Permite agregar/quitar roles a usuarios específicos
- Controla jerarquía de roles (Administrador > Empleado > Usuario)
- Valida permisos de administración

**Características:**
- Vista restringida a administradores
- Interfaz moderna con estadísticas
- Gestión en tiempo real de roles
- Validación de jerarquía de permisos

========================================
3. MÓDULO DE CLIENTES
========================================

**Script Principal:** ``views.py``
**Métodos:** ``manage_clientes``, ``create_cliente``

Descripción
-----------
Administra el CRUD completo de clientes del sistema, incluyendo su información personal y categorización.

Funcionalidades Principales
----------------------------

**3.1 Gestión de Clientes (manage_clientes)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Lista todos los clientes registrados
- Filtros por estado (activo/inactivo)
- Búsqueda por nombre o documento
- Acciones: ver, editar, desactivar, eliminar

**Características:**
- Interfaz moderna con tema oscuro
- Estadísticas en tiempo real
- Paginación para grandes volúmenes
- Validación de permisos de administración

**3.2 Creación de Clientes (create_cliente)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Formulario de creación de nuevos clientes
- Validación de datos únicos (documento)
- Asignación automática de categoría
- Integración con sistema de roles

**Campos del Formulario:**
- Nombre completo
- Documento de identidad
- Tipo de cliente (Persona/Empresa)
- Categoría
- Estado (activo/inactivo)

========================================
4. MÓDULO DE MONEDAS
========================================

**Script Principal:** ``views.py``
**Método:** ``manage_currencies``

Descripción
-----------
Gestiona las divisas y tasas de cambio del sistema de intercambio.

Funcionalidades Principales
----------------------------

**4.1 Gestión de Monedas (manage_currencies)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Administra divisas disponibles en el sistema
- Configura tasas de compra y venta
- Controla decimales para cada moneda
- Activa/desactiva monedas

**Características:**
- Interfaz de administración moderna
- Validación de tasas de cambio
- Historial de actualizaciones
- Integración con página pública

========================================
5. MÓDULO DE MEDIOS DE PAGO
========================================

**Script Principal:** ``views.py``
**Método:** ``add_payment_method``

Descripción
-----------
Administra los métodos de pago disponibles para cada cliente del sistema.

Funcionalidades Principales
----------------------------

**5.1 Agregar Medios de Pago (add_payment_method)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py:1005``

**Funcionalidad:**
- Crea nuevos medios de pago por cliente
- Soporta múltiples tipos: tarjeta, billetera, cuenta bancaria, cheque
- Validaciones específicas por tipo
- Integración con sistema de clientes

**Tipos de Medios de Pago:**
- **Tarjeta:** número tokenizado, banco, vencimiento, últimos 4 dígitos
- **Billetera:** número de celular, proveedor
- **Cuenta Bancaria:** número de cuenta, banco, alias/CBU
- **Cheque:** número de cheque, banco emisor, vencimiento, monto

**Características de Seguridad:**
- Números de tarjeta tokenizados
- Validación de formatos específicos
- Control de permisos por rol

========================================
6. MÓDULO DE ROLES
========================================

**Script Principal:** ``views.py``
**Método:** ``manage_roles``

Descripción
-----------
Administra los roles del sistema y sus permisos asociados.

Funcionalidades Principales
----------------------------

**6.1 Gestión de Roles (manage_roles)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py:232``

**Funcionalidad:**
- Crea, edita y elimina roles del sistema
- Asigna permisos específicos a cada rol
- Controla jerarquía de roles
- Valida roles protegidos del sistema

**Roles del Sistema:**
- **Administrador:** Acceso completo al sistema
- **Empleado:** Acceso a operaciones y clientes
- **Usuario:** Acceso básico y perfil personal

========================================
7. MÓDULO DE CATEGORÍAS
========================================

**Script Principal:** ``views.py``
**Método:** ``manage_categories``

Descripción
-----------
Gestiona las categorías de clientes para su clasificación y organización.

Funcionalidades Principales
----------------------------

**7.1 Gestión de Categorías (manage_categories)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Administra categorías de clientes
- CRUD completo de categorías
- Asignación automática a clientes
- Validación de categorías en uso

========================================
8. MÓDULO DE PERFIL
========================================

**Script Principal:** ``views.py``
**Método:** ``edit_profile``

Descripción
-----------
Permite a los usuarios gestionar su información personal y configuración de cuenta.

Funcionalidades Principales
----------------------------

**8.1 Edición de Perfil (edit_profile)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Actualización de información personal
- Cambio de contraseña
- Gestión de preferencias
- Validación de datos únicos

========================================
9. MÓDULO DE DASHBOARD
========================================

**Script Principal:** ``views.py``
**Método:** ``landing_page``

Descripción
-----------
Proporciona el panel principal de administración con acceso a todas las funcionalidades del sistema.

Funcionalidades Principales
----------------------------

**9.1 Página de Aterrizaje (landing_page)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Panel central de administración
- Acceso rápido a todos los módulos
- Estadísticas del sistema en tiempo real
- Navegación intuitiva por roles

**Características:**
- Diseño moderno con tema oscuro
- Métricas en tiempo real
- Acceso controlado por roles
- Interfaz responsiva

========================================
10. MÓDULO DE ASIGNACIONES
========================================

**Script Principal:** ``views.py``
**Método:** ``asignar_cliente_usuario``

Descripción
-----------
Gestiona la asignación de clientes a usuarios específicos para su atención y seguimiento.

Funcionalidades Principales
----------------------------

**10.1 Asignación de Clientes (asignar_cliente_usuario)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Asigna clientes a usuarios específicos
- Gestiona relaciones cliente-usuario
- Controla asignaciones existentes
- Validación de permisos de asignación

**Características:**
- Interfaz de gestión moderna
- Validación de asignaciones duplicadas
- Historial de asignaciones
- Control de permisos por rol

========================================
11. MÓDULO DE MÉTODOS DE COBRO
========================================

**Script Principal:** ``views.py``
**Métodos:** ``manage_cobro_methods``, ``modify_cobro_method``

Descripción
-----------
Administra los métodos de cobro disponibles en el sistema para procesar pagos de clientes.

Funcionalidades Principales
----------------------------

**11.1 Gestión de Métodos de Cobro (manage_cobro_methods)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Lista métodos de cobro del sistema
- Configuración de comisiones por método
- Estado activo/inactivo
- Gestión centralizada de configuración

**Características:**
- Interfaz administrativa moderna
- Configuración granular por moneda
- Estadísticas de uso por método
- Validación de configuración

**11.2 Modificación de Métodos de Cobro (modify_cobro_method)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Edición de configuración de cobro
- Ajuste de comisiones y tarifas
- Cambio de parámetros operativos
- Validación de cambios

**Características:**
- Formulario pre-poblado con datos actuales
- Validación en tiempo real
- Registro de historial de cambios
- Notificación de impactos

========================================
12. MÓDULO DE PÁGINAS PÚBLICAS
========================================

**Script Principal:** ``views.py``
**Métodos:** ``public_home``, ``api_active_currencies``

Descripción
-----------
Gestiona las páginas públicas del sistema accesibles sin autenticación.

Funcionalidades Principales
----------------------------

**12.1 Página Principal Pública (public_home)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Muestra información general del servicio
- Lista monedas activas y cotizaciones actuales
- Acceso para usuarios no registrados
- Enlaces de navegación principales

**Características:**
- Diseño responsivo y moderno
- Información actualizada en tiempo real
- Integración con API de cotizaciones
- Optimización para SEO

**12.2 API de Monedas Activas (api_active_currencies)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Proporciona datos de monedas en formato JSON
- Filtros por estado y disponibilidad
- Cálculo automático de comisiones
- Cache para mejorar rendimiento

**Características:**
- Respuesta JSON estructurada
- Documentación automática con Swagger
- Control de rate limiting
- Seguridad de endpoints públicos

========================================
13. MÓDULO DE UTILIDADES
========================================

**Script Principal:** ``views.py``
**Métodos:** ``change_client``, ``set_cliente_seleccionado``

Descripción
-----------
Proporciona funciones utilitarias para mejorar la experiencia del usuario.

Funcionalidades Principales
----------------------------

**13.1 Cambio de Cliente (change_client)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Permite cambiar cliente seleccionado en sesión
- Lista clientes asignados al usuario
- Actualización de contexto de aplicación
- Redirección automática al dashboard apropiado

**Características:**
- Interfaz intuitiva de selección
- Validación de permisos de acceso
- Actualización automática de menú
- Preservación de estado de navegación

**13.2 Establecer Cliente Seleccionado (set_cliente_seleccionado)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Actualización vía AJAX del cliente seleccionado
- Validación de permisos de acceso
- Respuesta JSON inmediata
- Actualización de interfaz sin recarga

**Características:**
- Comunicación asíncrona eficiente
- Validación del lado del servidor
- Actualización en tiempo real
- Manejo de errores robusto

========================================
14. MÓDULO DE COMPRA Y VENTA
========================================

**Script Principal:** ``views.py``
**Métodos:** ``compraventa``, ``ingresar_pin``, ``historial_transacciones``

Descripción
-----------
Gestiona las operaciones de compra y venta de divisas, incluyendo la conversión entre diferentes monedas y el historial de transacciones.

Funcionalidades Principales
----------------------------

**14.1 Operaciones de Compra y Venta (compraventa)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Procesa operaciones de compra y venta de divisas
- Calcula tasas de cambio en tiempo real
- Valida límites de intercambio por cliente
- Gestiona diferentes métodos de pago y cobro
- Aplica comisiones según configuración

**Características:**
- Interfaz intuitiva para operaciones
- Cálculo automático de montos
- Validación de fondos disponibles
- Confirmación de operaciones
- Integración con Stripe para pagos

**Tipos de Operación:**
- **Compra:** Cliente compra divisas extranjeras
- **Venta:** Cliente vende divisas extranjeras
- **Conversión:** Cambio entre diferentes monedas

**14.2 Validación de PIN (ingresar_pin)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Valida PIN de seguridad para operaciones sensibles
- Protege transacciones de alto valor
- Limita intentos de PIN por seguridad
- Registra intentos fallidos

**Características:**
- Sistema de seguridad adicional
- Bloqueo temporal por intentos fallidos
- Registro de auditoría de validaciones
- Notificación de seguridad

**14.3 Historial de Transacciones (historial_transacciones)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Muestra historial completo de operaciones
- Filtros por fecha, tipo, moneda y estado
- Detalle completo de cada transacción
- Exportación de reportes

**Características:**
- Interfaz moderna con filtros avanzados
- Paginación para grandes volúmenes
- Búsqueda por número de operación
- Estados de transacción claros

**Estados de Transacción:**
- **Pendiente:** Operación iniciada pero no completada
- **Procesando:** Validación y procesamiento en curso
- **Completada:** Operación exitosa
- **Cancelada:** Operación cancelada por usuario o sistema
- **Fallida:** Error en el procesamiento

========================================
15. MÓDULO DE VERIFICACIÓN DE IDENTIDAD
========================================

**Script Principal:** ``views.py``
**Métodos:** ``resend_verification_email``, ``custom_logout``

Descripción
-----------
Proporciona funcionalidades avanzadas de autenticación y gestión de sesiones.

Funcionalidades Principales
----------------------------

**15.1 Reenvío de Email de Verificación (resend_verification_email)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Reenvía email de verificación
- Genera nuevo token seguro
- Controla límites de reenvío
- Valida usuario existente

**Características:**
- Sistema de límites por seguridad
- Tokens únicos por solicitud
- Registro de reenvíos realizados
- Notificación clara al usuario

**15.2 Cierre de Sesión Personalizado (custom_logout)**

**Ubicación:** ``webapp/views.py``

**Funcionalidad:**
- Cierra sesión del usuario actual
- Limpia datos de sesión completamente
- Registra acción de logout
- Redirige a página pública

**Características:**
- Limpieza segura de sesión
- Registro de auditoría
- Protección contra ataques
- Experiencia de usuario mejorada

========================================
16. MÓDULO DE FACTURACIÓN
========================================

**Script Principal:** ``factura.py``
**Métodos:** ``ver_factura``, ``factura_view``, ``factura_pdf``

Descripción
-----------
Sistema completo de facturación con generación de documentos fiscales y gestión de comprobantes.

Funcionalidades Principales
----------------------------

**16.1 Vista Principal de Factura (ver_factura)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/factura.py``

**Funcionalidad:**
- Interfaz principal para visualización de facturas
- Renderizado con iframe para mejor presentación
- Botones de acción para PDF y operaciones
- Información completa de facturación
- Integración con sistema de impresión

**Características:**
- Diseño profesional para documentos fiscales
- Vista previa en tiempo real
- Opciones de personalización
- Compatibilidad con diferentes formatos
- Optimización para impresión

**16.2 Vista Específica de Factura (factura_view)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/factura.py``

**Funcionalidad:**
- Renderizado específico por ID de factura
- Obtención de datos completos de transacción
- Cálculos automáticos de impuestos y totales
- Preparación de datos para diferentes formatos
- Validación de permisos de acceso

**Características:**
- Cálculos precisos de impuestos
- Información detallada de productos/servicios
- Datos de cliente y empresa
- Validación de integridad de datos
- Seguridad en acceso a documentos

**16.3 Generación de PDF (factura_pdf)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/factura.py``

**Funcionalidad:**
- Generación de PDF usando weasyprint
- Diseño profesional para documentos fiscales
- Descarga automática o visualización en navegador
- Optimización para diferentes tamaños de papel
- Compatibilidad con estándares fiscales

**Características:**
- Calidad profesional de PDF
- Diseño responsive para PDF
- Optimización de tamaño de archivo
- Compatibilidad multiplataforma
- Metadatos completos de documento

========================================
17. MÓDULO DE TEMPORIZADORES
========================================

**Script Principal:** ``schedule_views.py``
**Métodos:** ``manage_schedule``, configuración automática de tareas

Descripción
-----------
Sistema de automatización y programación de tareas para operaciones del sistema.

Funcionalidades Principales
----------------------------

**17.1 Gestión de Temporizadores (manage_schedule)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Funcionalidad:**
- Configuración de envío automático de emails
- Programación de reseteo de límites de intercambio
- Configuración de expiración de transacciones
- Interface administrativa para temporizadores
- Validación de configuraciones de horarios

**Características:**
- Configuración flexible de frecuencias
- Validación de horarios y fechas
- Sistema de backup para tareas críticas
- Logs detallados de ejecución
- Notificaciones de estado de tareas

**Tipos de Temporizadores:**

**17.2 Email Schedule Config**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Envío automático de cotizaciones diarias
- Resúmenes semanales para usuarios
- Notificaciones personalizadas
- Configuración de horarios específicos

**17.3 Límite Intercambio Schedule Config**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Reseteo automático de límites diarios/mensuales
- Configuración por categoría de cliente
- Historial de ejecuciones
- Validación de límites activos

**17.4 Expiración Transacción Config**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Timeout automático de transacciones pendientes
- Configuración por tipo de medio de pago
- Notificaciones de expiración
- Limpieza automática de transacciones vencidas

============================================
18. MÓDULO DE TAUSER (TERCEROS AUTORIZADOS)
============================================

**Script Principal:** ``tauser.py``
**Métodos:** ``tauser_login``, ``tauser_home``, ``tauser_pagar``, ``tauser_cobrar``

Descripción
-----------
Sistema especializado para gestión de terceros autorizados que procesan pagos y cobros del sistema.

Funcionalidades Principales
----------------------------

**18.1 Login de TAUser (tauser_login)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/tauser.py``

**Funcionalidad:**
- Sistema de autenticación independiente para TAUsers
- Validación de credenciales específicas
- Gestión de sesiones separadas del sistema principal
- Redirección a dashboard especializado
- Control de acceso basado en permisos TAUser

**Características:**
- Autenticación segura independiente
- Gestión de sesiones específicas
- Validación de permisos especializados
- Registro de actividad de TAUsers
- Integración con sistema de auditoría

**18.2 Dashboard TAUser (tauser_home)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/tauser.py``

**Funcionalidad:**
- Panel de control específico para TAUsers
- Lista de transacciones pendientes de procesamiento
- Estadísticas de operaciones realizadas
- Acceso directo a funciones de pago y cobro
- Información de estado del sistema

**Características:**
- Interfaz optimizada para operaciones rápidas
- Información en tiempo real
- Métricas de rendimiento personal
- Notificaciones de transacciones urgentes
- Tools especializadas para TAUsers

**18.3 Procesamiento de Pagos TAUser (tauser_pagar)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/tauser.py``

**Funcionalidad:**
- Procesamiento de pagos por parte de TAUsers
- Validación de transacciones pendientes
- Confirmación de pagos realizados
- Actualización automática de estados
- Registro detallado de operaciones

**Características:**
- Validación exhaustiva de transacciones
- Confirmación segura de pagos
- Actualización en tiempo real
- Prevención de duplicaciones
- Integración con sistemas bancarios

**18.4 Procesamiento de Cobros TAUser (tauser_cobrar)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/tauser.py``

**Funcionalidad:**
- Gestión de cobros por TAUsers
- Validación de transferencias recibidas
- Confirmación de recepción de fondos
- Actualización de estados de cobro
- Reconciliación automática

**Características:**
- Validación de transferencias bancarias
- Confirmación de montos recibidos
- Actualización automática de estados
- Prevención de errores de reconciliación
- Integración con sistemas bancarios

========================================
19. MÓDULO DE LÍMITES DE INTERCAMBIO
========================================

**Script Principal:** ``limites_de_intercambio.py``
**Métodos:** ``limites_intercambio_list``, ``limites_intercambio_tabla_htmx``, ``limite_config_edit``

Descripción
-----------
Gestión avanzada de límites de intercambio por categoría de cliente con tecnología HTMX para actualizaciones dinámicas.

Funcionalidades Principales
----------------------------

**19.1 Lista de Límites (limites_intercambio_list)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/limites_de_intercambio.py``

**Funcionalidad:**
- Vista principal para gestión de límites
- Lista todos los límites por categoría de cliente
- Filtros por moneda, estado y categoría
- Estadísticas de uso y disponibilidad
- Información de límites activos/inactivos

**Características:**
- Interfaz moderna con filtros avanzados
- Estadísticas en tiempo real
- Validación de límites por categoría
- Información detallada de uso
- Acciones rápidas de edición

**19.2 Tabla Dinámica HTMX (limites_intercambio_tabla_htmx)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/limites_de_intercambio.py``

**Funcionalidad:**
- Actualización dinámica de tabla sin recarga completa
- Tecnología HTMX para mejor experiencia de usuario
- Filtros en tiempo real con respuesta inmediata
- Optimización de rendimiento para grandes volúmenes
- Interactividad mejorada en frontend

**Características:**
- Actualizaciones parciales eficientes
- Respuesta inmediata a filtros
- Reducción de carga del servidor
- Experiencia de usuario mejorada
- Compatibilidad con JavaScript deshabilitado

**19.3 Edición de Configuración (limite_config_edit)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/limites_de_intercambio.py``

**Funcionalidad:**
- Formulario de edición de límites específicos
- Validación de rangos y montos permitidos
- Actualización en tiempo real de configuración
- Historial completo de cambios realizados
- Validación de impacto en clientes activos

**Características:**
- Formulario pre-poblado con datos actuales
- Validación en tiempo real
- Confirmación de cambios críticos
- Historial de modificaciones
- Notificación de impacto en clientes

========================================
20. MÓDULO DE COTIZACIONES AVANZADAS
========================================

**Script Principal:** ``cotizaciones.py``
**Métodos:** ``api_currency_history``, ``historical_view``, ``unsubscribe``, ``prices_list``, ``edit_prices``

Descripción
-----------
Sistema avanzado de gestión de cotizaciones con API REST, visualización histórica y gestión de suscripciones.

Funcionalidades Principales
----------------------------

**20.1 API de Historial de Monedas (api_currency_history)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/cotizaciones.py``

**Funcionalidad:**
- API REST para obtener historial de cotizaciones
- Datos en formato JSON optimizado para gráficos
- Filtros por moneda, fecha y rango temporal
- Cache inteligente para mejorar rendimiento
- Documentación automática con Swagger

**Características:**
- Respuesta JSON estructurada
- Filtros flexibles por parámetros
- Cache con invalidación inteligente
- Rate limiting para prevenir abuso
- Versionado de API

**Ejemplo de Respuesta:**

.. code-block:: json

   {
     "currency": "USD",
     "period": "30d",
     "data": [
       {
         "date": "2025-10-31",
         "buy_rate": 7200.00,
         "sell_rate": 7300.00,
         "volume": 15000.00
       }
     ]
   }
```

**20.2 Vista Histórica (historical_view)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/cotizaciones.py``

**Funcionalidad:**
- Interfaz web con gráficos interactivos
- Visualización de tendencias históricas
- Filtros por periodo y moneda específica
- Exportación de datos en múltiples formatos
- Análisis de volatilidad y tendencias

**Características:**
- Gráficos interactivos con Chart.js
- Filtros dinámicos sin recarga
- Exportación a Excel, PDF, CSV
- Análisis estadístico básico
- Responsive design para móviles

**20.3 Sistema de Desuscripción (unsubscribe)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/cotizaciones.py``

**Funcionalidad:**
- Procesamiento seguro de desuscripción de emails
- Validación de tokens de desuscripción
- Actualización de preferencias de usuario
- Confirmación de desuscripción exitosa
- Manejo de errores y casos edge

**Características:**
- Tokens seguros con expiración
- Validación de usuario y token
- Confirmación visual clara
- Opciones de reactivación
- Registro de actividad

**20.4 Lista de Precios (prices_list)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/cotizaciones.py``

**Funcionalidad:**
- Vista tabular de todos los precios del sistema
- Estado activo/inactivo por moneda
- Información de última actualización
- Acciones rápidas de edición masiva
- Estadísticas de volatilidad

**Características:**
- Tabla ordenable y filtrable
- Indicadores visuales de estado
- Acciones masivas disponibles
- Historial de cambios visible
- Alertas de precios obsoletos

**20.5 Edición de Precios (edit_prices)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Ubicación:** ``webapp/views/cotizaciones.py``

**Funcionalidad:**
- Formulario de edición múltiple de precios
- Validación de consistencia entre monedas
- Actualización simultánea de cotizaciones
- Confirmación de cambios masivos
- Previsualización de impacto

**Características:**
- Edición masiva eficiente
- Validación cruzada de tasas
- Confirmación de cambios críticos
- Rollback automático en errores
- Notificaciones a usuarios afectados

Tecnologías Utilizadas
----------------------
- **Framework:** Django 5.2.5
- **Base de Datos:** PostgreSQL
- **Frontend:** HTML5, CSS3, JavaScript
- **Autenticación:** Django Auth System
- **Email:** Django Mail System
- **Documentación:** Sphinx

Patrones de Diseño
------------------
- **MVC:** Modelo-Vista-Controlador
- **RBAC:** Role-Based Access Control
- **Decorators:** Para control de permisos
- **Forms:** Para validación de datos
- **Templates:** Para presentación

Seguridad
---------
- Autenticación por email
- Tokens de verificación seguros
- Control de roles y permisos
- Validación de formularios
- Protección CSRF
- Sanitización de datos

========================================
CONCLUSIONES
========================================

El sistema Global Exchange Webapp implementa un conjunto completo de módulos que cubren todas las funcionalidades necesarias para la gestión de un sistema de intercambio de divisas. Cada módulo está diseñado con principios de seguridad, escalabilidad y mantenibilidad, utilizando las mejores prácticas de Django y desarrollo web moderno.

La documentación automática generada por Sphinx permite mantener la documentación actualizada con los cambios en el código, facilitando el mantenimiento y la colaboración en el desarrollo del proyecto.
