3.1 Clientes
============

El módulo de Clientes es fundamental para la operación del sistema, ya que permite registrar y gestionar toda la información de las personas o empresas que realizan operaciones de cambio de divisas.

Alta de clientes
----------------

**Vista y formulario:**

- La creación de clientes se realiza a través de la vista ``create_client`` utilizando el formulario ``ClienteForm``.
- Ubicación del código: ``webapp/views/clientes.py`` y ``webapp/forms.py``.

**Campos del formulario:**

- ``nombre``: Nombre completo del cliente (persona) o razón social (empresa). Campo obligatorio.
- ``documento``: Número de documento de identidad (cédula, RUC, pasaporte). Campo obligatorio y único.
- ``correo``: Dirección de correo electrónico para notificaciones y comunicaciones.
- ``telefono``: Número de teléfono de contacto con código de país.
- ``direccion``: Dirección física del cliente.
- ``categoria``: Categoría asignada que determina descuentos y límites aplicables.
- ``estado``: Estado del cliente en el sistema (activo, inactivo, pendiente de verificación).
- ``stripe_customer_id``: Identificador de cliente en Stripe para procesamiento de pagos.

**Proceso de alta paso a paso:**

1. Acceder al menú: Clientes → Nuevo cliente.
2. Completar todos los campos obligatorios marcados con asterisco.
3. Seleccionar la categoría apropiada según el perfil del cliente.
4. Verificar que el documento no esté duplicado en el sistema.
5. Guardar el registro; el sistema asignará un ID único al cliente.

**Integración con Stripe:**

Si la integración con Stripe está configurada, al guardar un nuevo cliente se crea automáticamente un registro en Stripe y se almacena el ``stripe_customer_id`` para futuras transacciones.

Edición de datos
----------------

**Vista de modificación:**

- Función: ``modify_client(client_id)``
- Permite actualizar cualquier campo del cliente, incluyendo cambio de categoría.

**Campos sensibles:**

Los siguientes campos requieren atención especial al modificarse:

- ``documento``: Cambios deben validarse contra documentación física.
- ``categoria``: Cambios afectan límites y condiciones comerciales.
- ``estado``: Desactivar un cliente impide nuevas transacciones.

**Sincronización:**

- Los cambios en datos básicos (nombre, correo) se sincronizan con Stripe automáticamente.
- Se mantiene un historial de cambios para auditoría.

**Buenas prácticas:**

- Conservar el historial de cambios sin eliminar registros.
- Documentar el motivo de cambios significativos (categoría, estado).
- Usar auditoría para cambios en documentos o RUC.

Consulta de clientes
--------------------

**Vista de listado:**

- Función: ``manage_clientes``
- Muestra todos los clientes con paginación automática.

**Opciones de búsqueda:**

- Búsqueda por texto: nombre, documento, correo.
- Filtros por categoría: VIP, Estándar, etc.
- Filtros por estado: Activo, Inactivo, Pendiente.
- Filtros por fecha de registro o última actividad.

**Exportación de datos:**

- Botón "Exportar CSV" genera archivo descargable con los clientes filtrados.
- Incluye todas las columnas visibles en el listado.
- Útil para análisis externos en Excel o herramientas BI.

**Vista de detalle:**

- Clic en un cliente muestra su ficha completa.
- Incluye: datos personales, historial de transacciones, límites consumidos, métodos de pago asociados.

Ejemplo de consulta (Django shell)
----------------------------------

.. code-block:: python

   from webapp.models import Cliente
   
   # Obtener clientes VIP con sus datos básicos
   clientes_vip = Cliente.objects.filter(
       categoria__nombre='VIP',
       estado='activo'
   ).values('id', 'nombre', 'correo', 'documento')
   
   # Contar clientes por categoría
   from django.db.models import Count
   Cliente.objects.values('categoria__nombre').annotate(total=Count('id'))
