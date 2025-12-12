Acceso al sistema
=================

Esta sección describe los diferentes métodos de acceso al sistema Global Exchange Webapp y las credenciales necesarias.

Tipos de acceso y credenciales
------------------------------

El sistema soporta diferentes tipos de usuarios con niveles de acceso específicos:

- **Superusuario/Administrador**: Acceso completo a todas las funcionalidades, incluyendo el panel de administración Django.
- **Supervisor**: Puede aprobar transacciones, gestionar operadores y generar reportes avanzados.
- **Operador**: Realiza operaciones de compra/venta y gestiona clientes asignados.
- **Usuario básico**: Acceso limitado a consultas y operaciones propias.

Los usuarios se crean mediante:

1. El panel de administración Django (``/admin/``) por un administrador.
2. El comando ``python manage.py createsuperuser`` para el primer administrador.
3. La interfaz de gestión de usuarios del sistema (si está habilitada).

Iniciar sesión
--------------

**Pasos para acceder al sistema:**

1. Abrir el navegador web y navegar a la URL del sistema (ejemplo: ``http://localhost:8000/``).
2. El sistema redirigirá automáticamente a la página de inicio de sesión si no hay una sesión activa.
3. Introducir el nombre de usuario en el campo correspondiente.
4. Introducir la contraseña asignada.
5. Hacer clic en el botón "Iniciar sesión".

**URLs de acceso importantes:**

- Página principal: ``/``
- Login directo: ``/accounts/login/``
- Panel de administración: ``/admin/``

**Notas sobre la sesión:**

- Las sesiones expiran después del tiempo configurado en ``SESSION_COOKIE_AGE``.
- Al cerrar el navegador, la sesión puede mantenerse activa según la configuración.
- El sistema registra la fecha y hora del último acceso de cada usuario.

Recuperación de contraseña
--------------------------

**Proceso de recuperación:**

1. En la pantalla de login, hacer clic en "¿Olvidaste tu contraseña?".
2. Introducir el correo electrónico asociado a la cuenta.
3. El sistema enviará un enlace de restablecimiento al correo.
4. Seguir el enlace y definir una nueva contraseña segura.

**Requisitos de contraseña:**

- Mínimo 8 caracteres.
- Debe incluir letras y números.
- No puede ser similar al nombre de usuario.
- No puede ser una contraseña común.

**En entornos de desarrollo:**

Si el backend de correo está configurado como ``console.EmailBackend``, el enlace de recuperación se mostrará en la consola del servidor.

Acceso al panel de administración
---------------------------------

El panel de administración Django proporciona acceso directo a todos los modelos del sistema:

- **URL**: ``/admin/``
- **Requisitos**: Usuario con permisos de staff (``is_staff=True``) o superusuario.

**Funcionalidades del panel admin:**

- Gestión completa de usuarios y grupos.
- Edición directa de registros en la base de datos.
- Visualización del historial de cambios.
- Exportación e importación de datos.

Buenas prácticas de seguridad
-----------------------------

- **Cuentas individuales**: Cada usuario debe tener su propia cuenta; no compartir credenciales.
- **Principio de menor privilegio**: Asignar solo los permisos necesarios para cada rol.
- **Cambio periódico de contraseñas**: Especialmente para cuentas con privilegios elevados.
- **Monitoreo de accesos**: Revisar periódicamente los registros de inicio de sesión.
- **Bloqueo por intentos fallidos**: El sistema puede configurarse para bloquear después de múltiples intentos fallidos.
- **Cerrar sesión al terminar**: Especialmente en equipos compartidos.
