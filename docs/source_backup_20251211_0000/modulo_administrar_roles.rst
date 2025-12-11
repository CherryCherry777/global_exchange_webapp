Módulo: Administrar Roles de Usuario
====================================

Resumen
-------

Este módulo contiene las vistas y utilidades para asignar y remover roles (grupos) a usuarios, validar reglas de negocio relacionadas con jerarquías de roles y mostrar métricas.

Vistas principales
-------------------

- `manage_user_roles`: interfaz para ver usuarios y roles, asignar o remover roles.
- `add_role_to_user(user_id)`: endpoint para asignar un rol por nombre a un usuario.
- `remove_role_from_user(user_id, role_name)`: remueve un rol del usuario, con comprobaciones de orden jerárquico.

URLs (nombres)
--------------

- `manage_user_roles`, `add_role_user`, `remove_role_user`

Reglas y validaciones
---------------------

- `ROLE_TIERS` (definido en `webapp.views.constants`) define la jerarquía de roles; los usuarios sólo pueden asignar/remover roles si su nivel lo permite.
- `PROTECTED_ROLES` evita operaciones sobre roles críticos.
- Se previene que un usuario elimine su propio rol de mayor nivel si eso dejaría su cuenta sin privilegios necesarios.

Templates
---------

Plantilla principal: `templates/webapp/roles_usuarios/manage_user_roles.html`.

Ejemplo (Django shell)
----------------------

Asignar un rol desde el shell:

.. code-block:: python

   python manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> from django.contrib.auth.models import Group
   >>> User = get_user_model()
   >>> u = User.objects.get(username='juan')
   >>> g = Group.objects.get(name='Empleado')
   >>> u.groups.add(g)

Referencia automática
---------------------

.. automodule:: webapp.views.roles_de_usuarios
   :members:

Notas
-----

Si quieres que las páginas de administración de roles por usuario incluyan auditoría (quién asignó/quién removió roles), puedo añadir un modelo `RoleAssignmentLog` y las plantillas correspondientes.
