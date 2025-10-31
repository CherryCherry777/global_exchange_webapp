Nuevos Módulos Implementados
============================

Este documento contiene la documentación de los nuevos módulos y funcionalidades implementados en el sistema Global Exchange.

Módulos de Facturación
-----------------------

.. automodule:: webapp.views.factura
   :members:
   :undoc-members:
   :show-inheritance:

El módulo de facturación proporciona las siguientes funcionalidades:

ver_factura
~~~~~~~~~~~
**Descripción:** Vista principal para mostrar facturas del sistema.
**Parámetros:**
- ``request``: Objeto HttpRequest de Django
- ``factura_id`` (opcional): ID de la factura a mostrar

**Retorna:** HttpResponse con el template de factura renderizado

factura_view
~~~~~~~~~~~~
**Descripción:** Vista específica para renderizar contenido de factura por ID.
**Parámetros:**
- ``request``: Objeto HttpRequest de Django
- ``factura_id``: ID específico de la factura

**Retorna:** HttpResponse con datos de factura específica

factura_pdf
~~~~~~~~~~~
**Descripción:** Vista para generar y descargar facturas en formato PDF.
**Parámetros:**
- ``request``: Objeto HttpRequest de Django
- ``factura_id``: ID de la factura a generar

**Retorna:** HttpResponse con PDF de la factura
**Dependencias:** weasyprint (para generación de PDF)

Módulos TAUser
--------------

.. automodule:: webapp.views.tauser
   :members:
   :undoc-members:
   :show-inheritance:

El módulo TAUser gestiona terceros autorizados para operaciones financieras:

tauser_login
~~~~~~~~~~~~
**Descripción:** Sistema de autenticación para TAUsers.
**Funcionalidades:**
- Validación de credenciales específicas para TAUsers
- Manejo de sesiones independientes
- Redirección a dashboard específico

tauser_home
~~~~~~~~~~~
**Descripción:** Dashboard principal para TAUsers autenticados.
**Funcionalidades:**
- Panel de control con transacciones pendientes
- Estadísticas de operaciones realizadas
- Acceso rápido a funciones de pago/cobro

tauser_pagar
~~~~~~~~~~~~
**Descripción:** Procesamiento de pagos por TAUsers.
**Parámetros:**
- ``request``: Objeto HttpRequest
- ``pk``: Primary key de la transacción

**Funcionalidades:**
- Validación de permisos TAUser
- Procesamiento de pagos
- Actualización de estados

tauser_cobrar
~~~~~~~~~~~~~
**Descripción:** Procesamiento de cobros por TAUsers.
**Parámetros:**
- ``request``: Objeto HttpRequest
- ``pk``: Primary key de la transacción

**Funcionalidades:**
- Validación de transferencias recibidas
- Confirmación de cobros
- Actualización automática de estados

Módulos de Límites de Intercambio
----------------------------------

.. automodule:: webapp.views.limites_de_intercambio
   :members:
   :undoc-members:
   :show-inheritance:

Gestión avanzada de límites de intercambio por categoría de cliente:

limites_intercambio_list
~~~~~~~~~~~~~~~~~~~~~~~~
**Descripción:** Vista principal para gestión de límites.
**Funcionalidades:**
- Lista límites por categoría de cliente
- Filtros por moneda y estado
- Estadísticas de uso

limites_intercambio_tabla_htmx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Descripción:** Actualización dinámica de tabla mediante HTMX.
**Funcionalidades:**
- Actualización parcial sin recarga completa
- Filtros en tiempo real
- Mejora de experiencia de usuario

limite_config_edit
~~~~~~~~~~~~~~~~~~~
**Descripción:** Edición de configuración de límites específicos.
**Parámetros:**
- ``config_id``: ID de la configuración de límite

**Funcionalidades:**
- Formulario de edición con validación
- Actualización en tiempo real
- Historial de cambios

Módulos de Cotizaciones Avanzadas
----------------------------------

.. automodule:: webapp.views.cotizaciones
   :members:
   :undoc-members:
   :show-inheritance:

Sistema avanzado de gestión de cotizaciones y precios:

api_currency_history
~~~~~~~~~~~~~~~~~~~~
**Descripción:** API REST para historial de cotizaciones.
**Retorna:** JSON con datos históricos
**Parámetros de Query:**
- ``currency``: Código de moneda
- ``start_date``: Fecha de inicio
- ``end_date``: Fecha de fin

**Ejemplo de respuesta:**

.. code-block:: json

   {
     "currency": "USD",
     "history": [
       {
         "date": "2025-10-31",
         "buy_rate": 7200.00,
         "sell_rate": 7300.00
       }
     ]
   }

prices_list
~~~~~~~~~~~
**Descripción:** Lista todos los precios configurados.
**Funcionalidades:**
- Vista tabular de precios por moneda
- Estado activo/inactivo
- Última actualización

edit_prices
~~~~~~~~~~~
**Descripción:** Edición masiva de precios.
**Funcionalidades:**
- Formulario múltiple de precios
- Validación de consistencia
- Actualización simultánea

historical_view
~~~~~~~~~~~~~~~
**Descripción:** Vista web con gráficos de historial.
**Funcionalidades:**
- Gráficos interactivos
- Filtros por periodo
- Exportación de datos

Funciones de Desuscripción
~~~~~~~~~~~~~~~~~~~~~~~~~~~

unsubscribe
^^^^^^^^^^^
**Descripción:** Procesamiento de desuscripción de emails.
**Parámetros:**
- ``uidb64``: Usuario codificado en base64
- ``token``: Token de verificación

unsubscribe_confirm
^^^^^^^^^^^^^^^^^^^
**Descripción:** Confirmación de desuscripción exitosa.

unsubscribe_error
^^^^^^^^^^^^^^^^^
**Descripción:** Manejo de errores en desuscripción.

Dashboards Especializados
--------------------------

.. automodule:: webapp.views.vistas_varias
   :members:
   :undoc-members:
   :show-inheritance:

analyst_dash
~~~~~~~~~~~~
**Descripción:** Dashboard específico para analistas.
**Funcionalidades:**
- Métricas avanzadas del sistema
- Herramientas de análisis de datos
- Reportes especializados
- Acceso a información histórica detallada

Nuevas Páginas Principales
---------------------------

.. automodule:: webapp.views.paginas_principales
   :members:
   :undoc-members:
   :show-inheritance:

administar_metodos_pago
~~~~~~~~~~~~~~~~~~~~~~~
**Descripción:** Nueva interfaz moderna para administración de métodos de pago.
**Características de diseño:**
- Cards interactivos con efectos hover
- Diseño responsive para móviles
- Iconografía moderna
- Navegación intuitiva

**Funcionalidades técnicas:**
- Gestión centralizada de métodos de pago
- Configuración de comisiones por método
- Estados activo/inactivo
- Validaciones en tiempo real

Transacciones Avanzadas
-----------------------

.. automodule:: webapp.views.compraventa_y_conversión
   :members:
   :undoc-members:
   :show-inheritance:

Funciones Utilitarias
~~~~~~~~~~~~~~~~~~~~~

guardar_transaccion
^^^^^^^^^^^^^^^^^^^
**Descripción:** Función para crear y guardar transacciones.
**Parámetros:**
- ``cliente``: Objeto Cliente
- ``usuario``: Usuario que realiza la operación
- ``data``: Dict con datos de la transacción
- ``estado``: Estado inicial de la transacción
- ``payment_intent_id`` (opcional): ID de Stripe

**Retorna:** Objeto Transaccion creado

monto_stripe
^^^^^^^^^^^^
**Descripción:** Conversión de montos para API de Stripe.
**Parámetros:**
- ``monto_origen``: Monto en Decimal
- ``moneda``: Código de moneda

**Retorna:** Entero en centavos para Stripe

Vistas de Transacciones
~~~~~~~~~~~~~~~~~~~~~~~

get_metodos_pago_cobro
^^^^^^^^^^^^^^^^^^^^^^
**Descripción:** API para obtener métodos disponibles.
**Retorna:** JSON con métodos de pago y cobro disponibles

transaccion_list
^^^^^^^^^^^^^^^^
**Descripción:** Lista paginada de transacciones.
**Funcionalidades:**
- Filtros avanzados por múltiples criterios
- Paginación optimizada
- Búsqueda textual
- Exportación de resultados

ingresar_idTransferencia
^^^^^^^^^^^^^^^^^^^^^^^^
**Descripción:** Ingreso de ID de transferencia.
**Parámetros:**
- ``transaccion_id``: ID de la transacción

**Funcionalidades:**
- Validación de formato de ID
- Actualización automática de estado
- Confirmación de operación

Suite de Testing
----------------

El sistema incluye una suite completa de tests que cubren:

Test de Modelos
~~~~~~~~~~~~~~~
- Validación de campos obligatorios
- Restricciones de integridad
- Métodos de modelo custom
- Relaciones entre modelos

Test de Vistas
~~~~~~~~~~~~~~
- Autenticación y autorización
- Respuestas HTTP correctas
- Contexto de templates
- Redirecciones apropiadas

Test de Integración
~~~~~~~~~~~~~~~~~~~
- Flujos completos de usuario
- Integración con APIs externas
- Procesamiento de pagos
- Notificaciones por email

Test de Rendimiento
~~~~~~~~~~~~~~~~~~~
- Tiempo de respuesta de vistas
- Optimización de consultas de base de datos
- Carga de archivos estáticos
- Cache de contenido

Configuración de Desarrollo
---------------------------

Para trabajar con estos nuevos módulos en desarrollo:

1. **Instalación de dependencias:**

.. code-block:: bash

   pip install -r requirements.txt

2. **Configuración de weasyprint (Linux/WSL):**

.. code-block:: bash

   sudo apt-get install python3-dev libcairo2-dev libpango1.0-dev
   pip install weasyprint

3. **Ejecutar tests:**

.. code-block:: bash

   # Tests individuales por módulo
   python manage.py test webapp.tests.test_schedule_config -v 2
   python manage.py test webapp.tests.test_landing_views -v 2
   
   # Todos los tests
   python manage.py test webapp.tests -v 2

4. **Generar documentación:**

.. code-block:: bash

   cd docs
   make html
   # En Windows:
   make.bat html

Consideraciones de Producción
-----------------------------

**weasyprint en Windows:**
- Requiere librerías del sistema (Cairo, Pango)
- Recomendado usar Docker o WSL2 para desarrollo
- En producción Linux funciona nativamente

**Rendimiento:**
- Cache activado para APIs de cotizaciones
- Paginación en listas de transacciones
- Optimización de consultas de base de datos

**Seguridad:**
- Validación de permisos en todas las vistas
- Tokens de verificación para operaciones sensibles
- Audit log para cambios críticos
- Rate limiting en APIs públicas