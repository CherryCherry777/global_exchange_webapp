Documentación de Vistas
========================

Este documento contiene la documentación de todas las vistas principales del sistema Global Exchange.

Autenticación
-------------

register
~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para el registro de nuevos usuarios en el sistema.  
**Funcionalidad:** 
- Muestra formulario de registro
- Valida datos del usuario
- Envía email de verificación
- Asigna rol por defecto "Usuario"

verify_email
~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para verificar el email del usuario mediante token.  
**Funcionalidad:**
- Valida token de verificación
- Activa cuenta del usuario
- Redirige a página de login

custom_logout
~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista personalizada para cerrar sesión del usuario.  
**Funcionalidad:**
- Cierra sesión del usuario
- Limpia datos de sesión
- Redirige a página pública

Usuarios
--------

manage_user_roles
~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para gestionar roles de usuarios del sistema.  
**Funcionalidad:**
- Lista todos los usuarios
- Permite asignar/remover roles
- Solo accesible para administradores

add_role_to_user
~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para agregar un rol específico a un usuario.  
**Funcionalidad:**
- Asigna rol a usuario
- Valida permisos del administrador
- Actualiza jerarquía de roles

remove_role_from_user
~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para remover un rol específico de un usuario.  
**Funcionalidad:**
- Remueve rol de usuario
- Valida que no sea rol protegido
- Actualiza permisos del usuario

manage_users
~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista principal para gestión de usuarios del sistema.  
**Funcionalidad:**
- Lista usuarios con filtros
- Permite activar/desactivar usuarios
- Gestión de permisos por usuario

Clientes
--------

manage_clientes
~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista principal para gestionar clientes del sistema.  
**Funcionalidad:**
- Lista todos los clientes
- Filtros por categoría y estado
- Estadísticas de clientes
- Búsqueda por nombre/documento

create_cliente
~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para crear nuevos clientes en el sistema.  
**Funcionalidad:**
- Muestra formulario de creación
- Valida datos del cliente
- Asigna categoría por defecto
- Guarda cliente en base de datos

create_client
~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista alternativa para crear clientes con formulario completo.  
**Funcionalidad:**
- Formulario extendido de cliente
- Campos adicionales (RUC, email, teléfono)
- Validación de documentos únicos
- Asignación automática de categoría

view_client
~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para ver detalles completos de un cliente.  
**Funcionalidad:**
- Muestra información del cliente
- Lista usuarios asignados
- Historial de transacciones
- Opciones de edición

modify_client
~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para modificar datos de un cliente existente.  
**Funcionalidad:**
- Formulario pre-poblado con datos actuales
- Validación de cambios
- Actualización en base de datos
- Mensajes de confirmación

delete_cliente
~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para eliminar un cliente del sistema.  
**Funcionalidad:**
- Confirmación de eliminación
- Verificación de dependencias
- Eliminación lógica o física
- Actualización de estadísticas

Monedas
-------

manage_currencies
~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para gestionar monedas del sistema.  
**Funcionalidad:**
- Lista monedas activas/inactivas
- Filtros por estado
- Estadísticas de monedas
- Acciones de activación/desactivación

create_currency
~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para crear nuevas monedas en el sistema.  
**Funcionalidad:**
- Formulario de creación de moneda
- Validación de códigos únicos
- Configuración de decimales
- Subida de banderas

modify_currency
~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para modificar datos de una moneda existente.  
**Funcionalidad:**
- Formulario pre-poblado
- Actualización de tasas
- Modificación de decimales
- Cambio de estado activo/inactivo

manage_quotes
~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para gestionar cotizaciones de monedas.  
**Funcionalidad:**
- Lista cotizaciones por moneda
- Configuración de precios base
- Ajuste de comisiones
- Estado activo/inactivo

modify_quote
~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para modificar cotizaciones específicas.  
**Funcionalidad:**
- Edición de precio base
- Ajuste de comisiones de compra/venta
- Validación de rangos
- Actualización en tiempo real

Medios de Pago
--------------

add_payment_method
~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para agregar medios de pago a clientes.  
**Funcionalidad:**
- Formularios por tipo de medio
- Validación de datos específicos
- Asociación con cliente
- Configuración de estado activo

manage_payment_methods
~~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para gestionar métodos de pago globales.  
**Funcionalidad:**
- Lista métodos de pago globales
- Configuración de comisiones
- Estado activo/inactivo
- Gestión centralizada

modify_payment_method
~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para modificar métodos de pago globales.  
**Funcionalidad:**
- Edición de comisiones
- Cambio de nombre
- Modificación de estado
- Validación de datos

Roles
-----

manage_roles
~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para gestionar roles del sistema.  
**Funcionalidad:**
- Lista todos los roles
- Creación de nuevos roles
- Asignación de permisos
- Jerarquía de roles

create_role
~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para crear nuevos roles en el sistema.  
**Funcionalidad:**
- Formulario de creación
- Asignación de permisos
- Configuración de jerarquía
- Validación de nombres únicos

delete_role
~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para eliminar roles del sistema.  
**Funcionalidad:**
- Verificación de uso del rol
- Confirmación de eliminación
- Actualización de usuarios afectados
- Protección de roles del sistema

Categorías
----------

manage_categories
~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para gestionar categorías de clientes.  
**Funcionalidad:**
- Lista categorías existentes
- Configuración de descuentos
- Estadísticas por categoría
- Gestión de estado activo

modify_category
~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para modificar categorías existentes.  
**Funcionalidad:**
- Edición de nombre y descuento
- Validación de rangos
- Actualización de clientes afectados
- Historial de cambios

Perfil
------

edit_profile
~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para editar perfil del usuario autenticado.  
**Funcionalidad:**
- Formulario de datos personales
- Cambio de contraseña
- Actualización de email
- Configuración de preferencias

profile
~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para mostrar perfil del usuario.  
**Funcionalidad:**
- Información personal
- Roles asignados
- Clientes asignados
- Historial de actividad

Dashboard
---------

landing_page
~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista principal del dashboard según rol del usuario.  
**Funcionalidad:**
- Redirección según rol
- Acceso a funciones específicas
- Estadísticas generales
- Navegación principal

admin_dash
~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Dashboard específico para administradores.  
**Funcionalidad:**
- Estadísticas del sistema
- Acceso a todas las funciones
- Gestión de usuarios y roles
- Monitoreo de actividad

employee_dash
~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Dashboard específico para empleados.  
**Funcionalidad:**
- Funciones limitadas por rol
- Gestión de clientes asignados
- Acceso a transacciones
- Herramientas de trabajo

Asignaciones
------------

asignar_cliente_usuario
~~~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para asignar clientes a usuarios del sistema.  
**Funcionalidad:**
- Formulario de asignación
- Validación de duplicados
- Asociación cliente-usuario
- Confirmación de asignación

assign_clients
~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista mejorada para gestión de asignaciones cliente-usuario.  
**Funcionalidad:**
- Lista asignaciones existentes
- Formulario de nueva asignación
- Búsqueda y filtros
- Desasignación de clientes

desasignar_cliente_usuario
~~~~~~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para desasignar clientes de usuarios.  
**Funcionalidad:**
- Confirmación de desasignación
- Verificación de permisos
- Actualización de relaciones
- Historial de cambios

Métodos de Cobro
----------------

manage_cobro_methods
~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para gestionar métodos de cobro globales.  
**Funcionalidad:**
- Lista métodos de cobro
- Configuración de comisiones
- Estado activo/inactivo
- Gestión centralizada

modify_cobro_method
~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para modificar métodos de cobro globales.  
**Funcionalidad:**
- Edición de comisiones
- Cambio de configuración
- Modificación de estado
- Validación de datos

Páginas Públicas
----------------

public_home
~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista de la página pública principal.  
**Funcionalidad:**
- Muestra monedas activas
- Información de cotizaciones
- Acceso para invitados
- Enlaces de registro/login

api_active_currencies
~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** API para obtener monedas activas en formato JSON.  
**Funcionalidad:**
- Retorna datos de monedas
- Formato JSON estructurado
- Filtros por estado
- Cálculos de comisiones

Utilidades
----------

change_client
~~~~~~~~~~~~~
**Ubicación:** views.py  
**Descripción:** Vista para cambiar cliente seleccionado en sesión.  
**Funcionalidad:**
- Lista clientes asignados
- Cambio de cliente activo
- Actualización de sesión
- Redirección a dashboard

set_cliente_seleccionado
~~~~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para establecer cliente seleccionado via AJAX.
**Funcionalidad:**
- Actualización via AJAX
- Validación de permisos
- Respuesta JSON
- Actualización de interfaz

Compra y Venta
--------------

compraventa
~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista principal para operaciones de compra y venta de divisas.
**Funcionalidad:**
- Procesa operaciones de compra/venta
- Calcula tasas de cambio en tiempo real
- Valida límites de intercambio
- Gestiona métodos de pago y cobro
- Aplica comisiones según configuración

ingresar_pin
~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para validar PIN de seguridad en operaciones sensibles.
**Funcionalidad:**
- Valida PIN para operaciones de alto valor
- Sistema de intentos limitados
- Bloqueo temporal por seguridad
- Registro de validaciones

historial_transacciones
~~~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para mostrar historial completo de transacciones.
**Funcionalidad:**
- Lista transacciones con filtros
- Detalle completo de operaciones
- Estados de transacciones
- Exportación de reportes

Nuevos Métodos Agregados
=========================

A continuación se documentan los métodos adicionales incorporados al sistema:

Métodos de Autenticación Adicionales
------------------------------------

resend_verification_email
~~~~~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para reenviar email de verificación al usuario.
**Funcionalidad:**
- Genera nuevo token de verificación
- Envía email con enlace de activación
- Validación de usuario existente
- Límites de reenvío por seguridad

Métodos de Usuarios Adicionales
-------------------------------

add_role_to_user
~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para asignar roles adicionales a usuarios existentes.
**Funcionalidad:**
- Lista roles disponibles
- Validación de jerarquía de permisos
- Asignación múltiple de roles
- Verificación de conflictos de permisos

remove_role_from_user
~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para remover roles específicos de usuarios.
**Funcionalidad:**
- Lista roles actuales del usuario
- Protección de roles del sistema
- Validación de usuario con múltiples roles
- Actualización de permisos en tiempo real

activate_user
~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista administrativa para activar usuarios manualmente.
**Funcionalidad:**
- Activación sin verificación de email
- Solo accesible para administradores
- Registro de auditoría de activación
- Notificación automática al usuario

deactivate_user
~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista administrativa para desactivar usuarios del sistema.
**Funcionalidad:**
- Desactivación temporal de cuentas
- Preservación de datos históricos
- Solo accesible para administradores
- Notificación automática al usuario

delete_user
~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista administrativa para eliminar usuarios permanentemente.
**Funcionalidad:**
- Eliminación completa de cuenta
- Verificación de dependencias
- Confirmación de administrador
- Registro de auditoría

modify_users
~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para modificación masiva de usuarios.
**Funcionalidad:**
- Edición múltiple de usuarios
- Actualización de datos comunes
- Validación masiva
- Reporte de cambios realizados

Métodos de Clientes Adicionales
-------------------------------

create_client
~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista alternativa para creación de clientes con formulario extendido.
**Funcionalidad:**
- Formulario completo de cliente
- Validación de documentos únicos
- Asignación automática de categoría
- Configuración inicial de límites

view_client
~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista detallada de información de cliente específico.
**Funcionalidad:**
- Información completa del cliente
- Lista de usuarios asignados
- Historial de transacciones
- Opciones de gestión

modify_client
~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para modificar información de clientes existentes.
**Funcionalidad:**
- Formulario pre-poblado
- Validación de cambios
- Actualización en tiempo real
- Registro de historial de cambios

delete_cliente
~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para eliminación de clientes del sistema.
**Funcionalidad:**
- Confirmación de eliminación
- Verificación de transacciones pendientes
- Eliminación lógica o física según configuración
- Actualización de estadísticas

inactivar_cliente
~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para desactivar temporalmente clientes.
**Funcionalidad:**
- Desactivación sin eliminación
- Preservación de historial
- Reactivación futura posible
- Notificación automática

activar_cliente
~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para reactivar clientes previamente desactivados.
**Funcionalidad:**
- Activación de clientes inactivos
- Restauración de permisos
- Notificación automática
- Validación de estado previo

Métodos de Monedas Adicionales
------------------------------

create_currency
~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para crear nuevas monedas en el sistema.
**Funcionalidad:**
- Formulario de creación de moneda
- Validación de códigos únicos (ISO 4217)
- Configuración de decimales
- Subida opcional de imagen de bandera

modify_currency
~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para modificar parámetros de monedas existentes.
**Funcionalidad:**
- Actualización de tasas de cambio
- Modificación de configuración de decimales
- Cambio de estado activo/inactivo
- Validación de impacto en transacciones

toggle_currency
~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para activar/desactivar monedas rápidamente.
**Funcionalidad:**
- Cambio rápido de estado
- Validación de monedas en uso
- Actualización automática de interfaces
- Registro de cambios

edit_prices
~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para edición masiva de precios de monedas.
**Funcionalidad:**
- Actualización simultánea de múltiples monedas
- Validación de consistencia de tasas
- Registro de cambios históricos
- Notificación a usuarios afectados

Métodos de Pago y Cobro Adicionales
-----------------------------------

manage_payment_methods
~~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista administrativa para gestión global de métodos de pago.
**Funcionalidad:**
- Lista métodos de pago del sistema
- Configuración de comisiones globales
- Estado activo/inactivo por método
- Gestión centralizada de configuración

modify_payment_method
~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para modificar configuración de métodos de pago globales.
**Funcionalidad:**
- Edición de comisiones y tarifas
- Cambio de nombres y descripciones
- Modificación de estado operativo
- Validación de configuración

my_payment_methods
~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista personal para que usuarios gestionen sus métodos de pago.
**Funcionalidad:**
- Lista métodos de pago personales
- Agregar nuevos métodos de pago
- Editar métodos existentes
- Eliminar métodos no utilizados

manage_cobro_methods
~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista administrativa para gestión de métodos de cobro globales.
**Funcionalidad:**
- Configuración de métodos de cobro del sistema
- Gestión de comisiones de cobro
- Estado activo/inactivo
- Configuración por moneda

modify_cobro_method
~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para modificar métodos de cobro globales.
**Funcionalidad:**
- Edición de configuración de cobro
- Ajuste de comisiones
- Cambio de parámetros operativos
- Validación de cambios

Métodos de Páginas Públicas
---------------------------

public_home
~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Página pública principal del sistema Global Exchange.
**Funcionalidad:**
- Muestra monedas activas y cotizaciones
- Información general del servicio
- Acceso para usuarios no registrados
- Enlaces de registro y login

api_active_currencies
~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** API REST para obtener información de monedas activas.
**Funcionalidad:**
- Retorna datos en formato JSON
- Filtros por estado y disponibilidad
- Cálculo automático de comisiones
- Cache para mejorar rendimiento

Métodos de Utilidades Adicionales
---------------------------------

change_client
~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para cambiar el cliente seleccionado en la sesión del usuario.
**Funcionalidad:**
- Lista clientes asignados al usuario
- Cambio de cliente activo en sesión
- Actualización de contexto de aplicación
- Redirección automática al dashboard apropiado

Métodos de Roles Adicionales
----------------------------

create_role
~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para crear nuevos roles personalizados en el sistema.
**Funcionalidad:**
- Formulario de creación de roles
- Asignación granular de permisos
- Configuración de jerarquía
- Validación de nombres únicos

delete_role
~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para eliminar roles personalizados del sistema.
**Funcionalidad:**
- Verificación de uso del rol
- Reasignación automática de usuarios afectados
- Protección de roles del sistema
- Confirmación de eliminación

Métodos de Categorías Adicionales
---------------------------------

modify_category
~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para modificar categorías de clientes existentes.
**Funcionalidad:**
- Edición de nombre y configuración
- Ajuste de descuentos asociados
- Validación de impacto en clientes
- Historial de cambios realizados

Métodos de Dashboard Adicionales
--------------------------------

admin_dash
~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Dashboard específico para administradores del sistema.
**Funcionalidad:**
- Métricas generales del sistema
- Acceso rápido a funciones administrativas
- Gestión de usuarios y configuración
- Monitoreo de actividad del sistema

employee_dash
~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Dashboard específico para empleados del sistema.
**Funcionalidad:**
- Funciones limitadas según permisos
- Gestión de clientes asignados
- Acceso a herramientas de trabajo diarias
- Información relevante para operaciones

Métodos de Asignaciones Adicionales
-----------------------------------

assign_clients
~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista mejorada para gestión de asignaciones cliente-usuario.
**Funcionalidad:**
- Interfaz moderna para asignaciones
- Búsqueda y filtros avanzados
- Gestión masiva de asignaciones
- Desasignación de clientes

desasignar_cliente_usuario
~~~~~~~~~~~~~~~~~~~~~~~~~~
**Ubicación:** views.py
**Descripción:** Vista para remover asignaciones cliente-usuario específicas.
**Funcionalidad:**
- Confirmación de desasignación
- Verificación de permisos necesarios
- Actualización automática de relaciones
- Registro de historial de cambios
