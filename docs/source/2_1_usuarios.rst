2.1 Usuarios
============

Crear usuarios
--------------

- Vistas y formularios: `UserCreateView` / `user_form.html` (ver `webapp/views/usuarios.py` y `webapp/forms.py`).
- Campos importantes: `username`, `email` (único), `first_name`, `last_name`, `groups` (roles), `is_active`.

Pasos para crear desde el panel (admin o UI):

1. Ir a la sección Usuarios > Nuevo usuario.
2. Completar datos obligatorios y asignar roles si corresponde.
3. Guardar y, si corresponde, enviar email de bienvenida.

Editar y eliminar usuarios
--------------------------

- Editar: `UserUpdateView` — permite cambiar datos de perfil y roles (si el usuario tiene permisos).
- Eliminar: `UserDeleteView` — suele requerir confirmación y, por política, evitar borrar administradores críticos.

Buenas prácticas:

- Usar desactivación (`is_active=False`) en vez de borrado cuando se requiera mantener histórico.
- Verificar cambios de roles con auditoría cuando sean operaciones sensibles.

Gestión de credenciales
-----------------------

- Reset de contraseña: flujo estándar de Django (correo con token) o administración por `admin`.
- MFA/TOTP y tokens: si el proyecto incluye MFA, documentar la provisión y recuperación de códigos.
- Restauración de sesiones: invalidar sesiones activas al resetear contraseña si se desea mayor seguridad.

Ejemplos (Django shell)
-----------------------

.. code-block:: python

   from django.contrib.auth import get_user_model
   User = get_user_model()
   u = User.objects.create_user('ana', email='ana@example.com', password='secreto')
