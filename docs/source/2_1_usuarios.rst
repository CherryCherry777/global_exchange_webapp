2.1 Usuarios
============

1. ¿QUÉ ES?
-----------

Breve descripción:

El módulo de Usuarios gestiona las cuentas de las personas que acceden al sistema (operadores, administradores y clientes internos). Centraliza creación, edición, desactivación y recuperación de credenciales.

¿Para qué sirve?

- Controlar identidades y credenciales.
- Asociar roles/permisos a cuentas.
- Mantener trazabilidad de cambios sobre usuarios.

2. ¿CÓMO ACCEDER?
------------------

Ruta desde el menú principal:

Menú → Configuración → Usuarios

También mediante la interfaz de administración Django (`/admin/`) si tienes permisos.

3. FUNCIONALIDADES PRINCIPALES
-----------------------------

A) Crear usuario
-----------------
Pasos:

1. Menú → Configuración → Usuarios → Nuevo usuario.
2. Completar datos obligatorios (`username`, `password`) y campos opcionales.
3. Asignar rol(es) en `Roles` si corresponde.
4. Guardar.

Campos importantes:

- `username`: Identificador único. Ejemplo: `jdoe`.
- `email`: Correo para notificaciones (si aplica). Ejemplo: `jdoe@empresa.com`.
- `password`: Contraseña inicial (se recomienda cambiar en primer acceso).
- `groups` / `roles`: Roles asignados. Ejemplo: `Operador`.

Resultado: se crea la cuenta; si está habilitado, se puede enviar un email de activación (opcional). El usuario podrá iniciar sesión con sus credenciales.

B) Editar usuario
------------------
Pasos:

1. Menú → Configuración → Usuarios → Seleccionar usuario → Editar.
2. Modificar campos necesarios (nombre, email, roles).
3. Guardar cambios.

Campos importantes:

- `first_name` / `last_name`: Nombre visible en la UI.
- `is_active`: Activa/desactiva el acceso sin borrar el registro.

Resultado: los cambios se aplican inmediatamente; si cambias la contraseña y quieres forzar logout, invalida sesiones activas.

C) Eliminar usuario
--------------------
Pasos:

1. Menú → Configuración → Usuarios → Seleccionar usuario → Eliminar.
2. Confirmar la acción.

Campos importantes:

- `is_active`: se recomienda usar `is_active=False` para deshabilitar en lugar de borrado.

Resultado: según la política, el usuario se marca como eliminado o se desactiva; registros históricos permanecen.

4. EJEMPLO PRÁCTICO
-------------------

Alta de un nuevo operador (paso a paso):

1. Menú → Configuración → Usuarios → Nuevo usuario.
2. `username`: `operador_mario`.
3. `password`: asignar contraseña segura temporal.
4. `groups`: seleccionar `Operador`.
5. Guardar.

Al finalizar, el operador podrá iniciar sesión y ver las opciones permitidas por su rol.

5. ERRORES COMUNES
------------------

- Error: "El email ya está en uso" — Solución: verificar usuarios duplicados; use `is_active=False` si debe reasignarse el email.
- Error: "Permiso denegado" al acceder a una vista — Solución: revisar asignación de roles/permisos y la jerarquía de permisos del usuario.
- Problema: Olvido de contraseña y correo no recibido — Solución: comprobar configuración SMTP o usar reset desde `admin`.

6. TIPS ÚTILES
---------------

- Usa desactivación (`is_active=False`) en lugar de borrar para mantener historial.
- Documenta cambios de roles en la auditoría; añade una nota con motivo cuando sea un cambio administrativo.
- Para pruebas, crea cuentas en entorno de staging con permisos limitados en vez de usar cuentas reales.

Comandos útiles (Django shell)
-----------------------------

.. code-block:: python

   from django.contrib.auth import get_user_model
   User = get_user_model()
   u = User.objects.create_user('ana', email='ana@example.com', password='secreto')

