Módulo: Roles
===============

Resumen
-------

El módulo **Roles** centraliza la creación, edición y eliminación de roles (grupos) y la asignación de permisos a dichos roles. Está construido sobre `django.contrib.auth.models.Group` y `Permission`.

Modelos relevantes
------------------

- `Role` (definido en `webapp.models`): relación uno-a-uno con `Group` para agregar metadatos (`is_active`).
- `django.contrib.auth.models.Group` y `Permission` se usan para gestionar permisos y miembros.

Vistas principales
-------------------

- `manage_roles`: lista roles, muestra estado y métricas.
- `create_role`: formulario para crear un `Group` y asignar permisos.
- `modify_role`: editar nombre, permisos o eliminar un rol (con protecciones para roles críticos como `Administrador`).
- `delete_role`, `confirm_delete_role`, `update_role_permissions`.

URLs (nombres)
--------------

- `manage_roles`, `create_role`, `modify_role`, `delete_role`, `confirm_delete_role`, `update_role_permissions`

Templates
---------

Plantillas en `templates/webapp/roles/` (p. ej. `manage_roles.html`, `create_role.html`, `modify_role.html`).

Reglas y seguridades
--------------------

- Sólo usuarios con rol `Administrador` pueden ejecutar la mayoría de acciones (ver `@role_required("Administrador")`).
- Los `PROTECTED_ROLES` (definidos en `webapp.views.constants`) impiden eliminar roles críticos como `Administrador`.

Ejemplos (Django shell)
-----------------------

Crear un rol y asignar permisos:

.. code-block:: python

   python manage.py shell
   >>> from django.contrib.auth.models import Group, Permission
   >>> r = Group.objects.create(name='Operador')
   >>> p = Permission.objects.get(codename='add_cliente')  # ejemplo
   >>> r.permissions.add(p)

Referencia automática
---------------------

.. automodule:: webapp.models
   :members:

.. automodule:: webapp.views.roles
   :members:

-------

.. code-block:: python

   # Pseudocódigo de ejemplo
   from webapp.roles import manager

   role = manager.create_role('operador')
   manager.assign_permission(role, 'can_create_exchange')

API / Referencia (cómo añadirla)
--------------------------------

Para incluir la referencia automática:

.. code-block:: rst

   .. automodule:: webapp.roles
      :members:

Mantén esta página y reemplaza el contenido con las descripciones reales cuando las proveas.
