Módulo: Asignación de Cliente a Usuario
=======================================

Resumen
-------

Describe la relación y el flujo para asignar clientes a usuarios mediante el modelo intermedio `ClienteUsuario` y las vistas para asignar y desasignar.

Modelo relevante
-----------------

- `ClienteUsuario` (en `webapp.models`): relación intermedia entre `Cliente` y el `AUTH_USER_MODEL` (campo `usuario`), con `fecha_asignacion` y restricción `unique_together` en (`cliente`, `usuario`).

Vistas y endpoints
-------------------

- `assign_clients` — interfaz principal (POST con `action=assign` o `action=unassign`). Muestra `clientes`, `usuarios` y `asignaciones`.
- `asignar_cliente_usuario` — formulario basado en `AsignarClienteForm` (permiso: `webapp.add_clienteusuario`, `webapp.view_clienteusuario`).
- `desasignar_cliente_usuario(asignacion_id)` — elimina la asignación (permiso: `webapp.delete_clienteusuario`).
- `view_client(client_id)` — ver detalles y usuarios asignados a un cliente.

URLs
----

- `assign_clients` (ruta administrativa), `asignar_cliente_usuario`, `desasignar_cliente_usuario`, `view_client`.

Templates
---------

Plantillas: `templates/webapp/asignar_clientes_a_usuarios/` — `assign_clients.html`, `asignar_cliente_usuario.html`, `view_client.html`.

Reglas
------

- Se verifica que no se creen duplicados usando `ClienteUsuario.objects.filter(...).exists()` y capturas de `IntegrityError` en el formulario antiguo.
- Acciones protegidas por `@role_required("Administrador")` o `@permitir_permisos` según la vista.

Ejemplo (POST assign)
---------------------

Payload típico (formulario):

```
action=assign
cliente_id=12
usuario_id=45
```

Ejemplo (shell)
---------------

.. code-block:: python

   from webapp.models import Cliente, ClienteUsuario
   from django.contrib.auth import get_user_model
   User = get_user_model()
   cliente = Cliente.objects.first()
   user = User.objects.filter(is_active=True).first()
   ClienteUsuario.objects.get_or_create(cliente=cliente, usuario=user)
