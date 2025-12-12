
2.3 Administrar roles de usuario
================================

1. ¿QUÉ ES?
-----------

Breve descripción:

Esta sección trata las operaciones para asignar, revocar y auditar roles a usuarios individuales. Es la capa operativa que aplica la política de roles al inventario de usuarios.

¿Para qué sirve?

- Permitir que los administradores asignen responsabilidades a cuentas.
- Controlar cambios en privilegios con trazabilidad.

2. ¿CÓMO ACCEDER?
------------------

Ruta desde el menú principal:

Menú → Configuración → Usuarios → Administrar Roles

También existen endpoints de API y vistas administrativas (`manage_user_roles`, `add_role_to_user`).

3. FUNCIONALIDADES PRINCIPALES
------------------------------

A) Asignar rol a usuario
------------------------
Pasos:

1. Menú → Configuración → Usuarios → Seleccionar usuario → Administrar Roles.
2. Seleccionar rol(s) para asignar.
3. Confirmar y guardar (registrar auditoría si aplica).

Campos importantes:

- `user`: el usuario objetivo. Ejemplo: `operador_mario`.
- `roles`: lista de roles a aplicar. Ejemplo: `Operador`.

Resultado: el usuario obtiene los permisos del rol; las sesiones activas podrán necesitar renovación para aplicar cambios.

B) Revocar rol
---------------
Pasos:

1. Menú → Configuración → Usuarios → Seleccionar usuario → Administrar Roles.
2. Desmarcar el rol que se desea revocar.
3. Guardar y, si corresponde, dejar nota en la auditoría.

Resultado: el usuario pierde los permisos asociados al rol.

C) Auditoría de asignaciones
----------------------------
Pasos:

1. Acceder al log de auditoría o a la tabla `role_assignment_log` si existe.
2. Filtrar por usuario, rol o rango de fechas.

Campos importantes:

- `actor`: quien realizó la asignación.
- `target_user`: usuario afectado.
- `role`: rol asignado/revocado.
- `timestamp`: momento de la acción.

Resultado: registro accesible para revisiones y cumplimiento.

4. EJEMPLO PRÁCTICO
-------------------

Asignar rol `Operador` a un nuevo empleado:

1. Menú → Configuración → Usuarios → Buscar `juan.p`.
2. Administrar Roles → seleccionar `Operador`.
3. Guardar.

Registrar en la auditoría: actor=`admin_ana`, target_user=`juan.p`, role=`Operador`, timestamp=2025-12-11T10:25:00Z.

5. ERRORES COMUNES
------------------

- Error: "No tienes permiso para asignar este rol" — Solución: comprobar la jerarquía (`ROLE_TIERS`) y los permisos del actor; usar una cuenta con privilegios adecuados o solicitar elevación.
- Problema: El usuario no recibe permisos tras asignar rol — Solución: comprobar caché/servicios de autenticación, forzar logout/login o invalidar sesiones.

6. TIPS ÚTILES
---------------

- Automatiza asignaciones repetitivas mediante scripts en staging y plantillas de roles.
- Añade un campo `motivo` obligatorio para cambios críticos en producción para facilitar auditoría.
- Revisa periódicamente asignaciones inactivas y depura roles no usados.

