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
