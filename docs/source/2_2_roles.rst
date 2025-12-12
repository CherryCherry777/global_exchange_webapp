
2.2 Roles
=========

1. ¿QUÉ ES?
-----------

Breve descripción:

El módulo de Roles define conjuntos de permisos que se asignan a usuarios para controlar el acceso a funcionalidades del sistema.

¿Para qué sirve?

- Agrupar permisos relacionados y facilitar la administración.
- Aplicar políticas de acceso en la UI y en las APIs.

2. ¿CÓMO ACCEDER?
------------------

Ruta desde el menú principal:

Menú → Configuración → Roles

También se puede gestionar desde `admin` en `/admin/auth/group/` o mediante endpoints internos si existen.

3. FUNCIONALIDADES PRINCIPALES
-----------------------------

A) Crear rol
------------
Pasos:

1. Menú → Configuración → Roles → Nuevo rol.
2. Introducir nombre y descripción.
3. Seleccionar permisos asociados (listas de `Permission`).
4. Guardar.

Campos importantes:

- `name`: Nombre del rol. Ejemplo: `Operador`.
- `permissions`: Lista de permisos. Ejemplo: `add_transaccion`, `view_cliente`.

Resultado: se crea un grupo (`Group`) con los permisos seleccionados; los usuarios asignados al rol adquieren esos permisos.

B) Editar rol
-------------
Pasos:

1. Menú → Configuración → Roles → Seleccionar rol → Editar.
2. Modificar permisos o nombre.
3. Guardar y revisar usuarios afectados.

Campos importantes:

- `permissions`: cambios aquí impactan a todos los usuarios del rol.

Resultado: los usuarios del rol ven sus permisos actualizados de forma inmediata.

C) Eliminar rol
---------------
Pasos:

1. Menú → Configuración → Roles → Seleccionar rol → Eliminar.
2. Confirmar baneo o reasignar usuarios antes de la eliminación.

Resultado: si el rol se elimina, los usuarios lo perderán; es recomendable reasignar a un rol alternativo o advertir previamente.

4. EJEMPLO PRÁCTICO
-------------------

Crear un rol `Supervisor` con permisos de consulta y aprobación:

1. Menú → Configuración → Roles → Nuevo rol.
2. `name`: `Supervisor`.
3. Seleccionar permisos: `view_transaccion`, `change_transaccion` (si incluye aprobación), `view_cliente`.
4. Guardar.

5. ERRORES COMUNES
------------------

- Error: "Permisos insuficientes después de asignar rol" — Solución: comprobar que el permiso requerido está incluido en `permissions` y no sólo documentado.
- Problema: Usuarios quedan sin permisos tras editar rol — Solución: revisar si la edición eliminó permisos fundamentales y comunicar a los afectados.

6. TIPS ÚTILES
---------------

- Mantén roles simples y con un propósito único (ej: `Operador`, `Supervisor`, `Administrador`).
- Documenta la matriz `rol ↔ permiso` en un archivo central para auditoría.
- Prueba cambios en staging antes de aplicarlos en producción para evitar cortes de acceso.

Notas técnicas
--------------

Los permisos se gestionan con `django.contrib.auth.models.Permission` y se agrupan en `Group` (roles). Revisa `webapp/models.py` y `webapp/views/constants.py` para definiciones y constantes relacionadas.
