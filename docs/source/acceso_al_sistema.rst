Acceso al sistema
=================

Credenciales y roles
--------------------

- Los usuarios se crean en el panel de administración o mediante el flujo de registro del frontend.
- Existen roles (p. ej. Administrador, Empleado, Usuario) que determinan permisos en el sistema.

Iniciar sesión
--------------

1. Abrir la URL de la aplicación en el navegador (p. ej. `http://localhost:8000/`).
2. Navegar a la pantalla de login (`/accounts/login/` o la ruta definida en `webapp/urls.py`).
3. Introducir usuario y contraseña.

Recuperación de contraseña
--------------------------

- Usa la opción '¿Olvidaste tu contraseña?' para iniciar el proceso de recuperación (correo de restablecimiento).
- En entornos locales, revisa la consola o el backend de emails configurado (SMTP local o `console.EmailBackend`).

Acceso al panel de administración
---------------------------------

- Accede a `/admin/` con un superusuario para gestionar modelos, usuarios y permisos.

Buenas prácticas
---------------

- No compartas cuentas de administrador.
- Revisa y asigna permisos mínimos necesarios por rol.
