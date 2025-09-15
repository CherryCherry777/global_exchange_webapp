Documentación de Módulos - Global Exchange Webapp
==================================================

Esta documentación describe los 12 módulos principales del sistema Global Exchange Webapp, incluyendo su funcionalidad, métodos principales y características técnicas.

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
ARQUITECTURA TÉCNICA
========================================

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
