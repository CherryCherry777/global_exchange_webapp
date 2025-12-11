Módulo: Usuarios
=================

Resumen
-------

El módulo **Usuarios** gestiona la creación, modificación, eliminación y administración de cuentas de usuario.
Incluye vistas basadas en clases para CRUD y vistas adicionales para administración (activar/desactivar, modificar roles, etc.).

Modelos relevantes
------------------

- `CustomUser` (definido en `webapp.models`): extiende `AbstractUser`, fuerza email único, añade campos como `receive_exchange_emails` y `unsubscribe_token`.
- `ClienteUsuario` (relación entre `Cliente` y usuario): tabla intermedia que vincula clientes con usuarios.

Vistas principales
-------------------

- `UserListView`, `UserCreateView`, `UserUpdateView`, `UserDeleteView` — vistas genéricas (templates en `webapp/usuarios/`).
- `manage_users`, `modify_users`, `activate_user`, `deactivate_user`, `confirm_delete_user` — vistas para administración y acciones en masa.

URLs (nombres)
--------------

- `user_list`, `user_create`, `user_update`, `user_delete`
- `manage_users`, `modify_users`, `activate_user`, `deactivate_user`, `confirm_delete_user`

Templates
---------

Las plantillas relacionadas están en `templates/webapp/usuarios/` (por ejemplo `manage_users.html`, `modify_users.html`, `user_form.html`).

Reglas y permisos
-----------------

- La mayoría de las vistas de administración requieren el decorador `@role_required("Administrador")` o `login_required`.
- Las validaciones: no se permite desactivar/eliminar administradores ni que un usuario desactive su propia cuenta.

Ejemplos rápidos (Django shell)
-------------------------------

Crear un usuario y asignarle un rol desde el shell:

.. code-block:: bash

   python manage.py shell
   >>> from django.contrib.auth.models import Group
   >>> from django.contrib.auth import get_user_model
   >>> User = get_user_model()
   >>> u = User.objects.create_user('maria', email='maria@example.com', password='secreto')
   >>> g = Group.objects.get_or_create(name='Empleado')[0]
   >>> u.groups.add(g)

Incluir referencia automática (opcional)
--------------------------------------

.. automodule:: webapp.models
   :members:
   :undoc-members:

.. automodule:: webapp.views.usuarios
   :members:
   :undoc-members:

Notas
-----

Cuando proveas la documentación específica de procesos (por ejemplo: flujo de registro, verificación de email, MFA), la agregaré como subsecciones o páginas separadas.
