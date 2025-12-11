3.1 Clientes
============

Alta de clientes
----------------

- Vistas y formularios: `create_client` / `ClienteForm` (ver `webapp/views/clientes.py` y `webapp/forms.py`).
- Campos comunes: `nombre`, `documento`, `correo`, `telefono`, `direccion`, `categoria`, `estado`, `stripe_customer_id`.

Pasos para dar de alta un cliente:

1. Acceder a la sección Clientes > Nuevo cliente.
2. Completar los datos obligatorios y seleccionar la `Categoria` si aplica.
3. Guardar; en entornos configurados se sincroniza con Stripe y se genera `stripe_customer_id`.

Edición de datos
----------------

- `modify_client(client_id)` — permite actualizar los datos, sincronizar con Stripe y revisar historial.
- Buenas prácticas: conservar historial y usar auditoría en cambios sensibles (documentos, RUC).

Consulta de clientes
--------------------

- `manage_clientes` — listado con búsqueda por texto y filtros por categoría, estado y fecha.
- Exportación: usar funciones de exportar CSV desde la UI para análisis externo.

Ejemplo (Django shell)
----------------------

.. code-block:: python

   from webapp.models import Cliente
   Cliente.objects.filter(categoria__nombre='VIP').values('nombre','correo')
