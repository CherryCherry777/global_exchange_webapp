Módulo: Clientes
=================

Resumen
-------

El módulo **Clientes** gestiona la entidad `Cliente` que representa clientes (personas o empresas) que utilizan los servicios. Provee vistas para listar, crear, editar, activar/inactivar y eliminar clientes.

Modelo principal
----------------

- `Cliente` (definido en `webapp.models`): campos principales: `nombre`, `razonSocial`, `documento`, `ruc`, `correo`, `telefono`, `direccion`, `categoria`, `estado`, `stripe_customer_id`, `fechaRegistro`.

Vistas principales
-------------------

- `manage_clientes` — listado y filtros (search, categoría, estado).  
- `create_client` — formulario de creación y sincronización con Stripe.  
- `modify_client(client_id)` — edición y sincronización con Stripe.  
- `delete_cliente(cliente_id)` — eliminar cliente (confirmación).  
- `inactivar_cliente(pk)` / `activar_cliente(pk)` — toggles de estado.

URLs (nombres relevantes)
-------------------------

- `manage_clientes`, `create_client`, `modify_client`, `delete_cliente`, `inactivar_cliente`, `activar_cliente`

Templates
---------

Plantillas relacionadas: `templates/webapp/clientes/` — `manage_clients.html`, `create_client.html`, `modify_client.html`, `confirm_delete_cliente.html`.

Reglas y validaciones
---------------------

- Verificaciones de unicidad para `documento` y `correo` en `create_client`.
- Uso de `@role_required("Administrador")` para acciones administrativas.  
- Integración con Stripe: `stripe.Customer.create` y `stripe.Customer.modify` usan `settings.STRIPE_SECRET_KEY`.

Ejemplo — crear cliente (shell)
-------------------------------

.. code-block:: python

   python manage.py shell
   >>> from webapp.models import Cliente, Categoria
   >>> c = Categoria.objects.first()
   >>> Cliente.objects.create(nombre='ACME S.A.', documento='1234567', correo='contacto@acme.test', telefono='+59599123456', direccion='Av. Principal 123', tipoCliente='persona_juridica', categoria=c, estado=True)

Referencia automática (opcional)
--------------------------------

.. automodule:: webapp.models
   :members:

Notas
-----

Si deseas añadir diagramas del flujo (por ejemplo, creación → sincronización Stripe → confirmación por email), pégalos y los incorporo en esta página.
