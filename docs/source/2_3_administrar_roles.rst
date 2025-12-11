2.3 Administrar roles de usuario
================================

Asignar roles
-------------

- Interfaces: `manage_user_roles` y endpoints relacionados (`add_role_to_user`, `asignar_role_user`).
- Validaciones: comprobar jerarquía (`ROLE_TIERS`) para evitar que un usuario asigne roles por encima de su nivel.
- Auditoría: registrar quién asignó qué rol y cuándo (recomendado).

Modificar permisos
------------------

- Edición de permisos asociados a un `Group` (rol) mediante `modify_role` o la UI de `admin`.
- Cambios en permisos críticos deben revisarse y probarse en staging antes de aplicar en producción.

Flujo recomendado para cambios críticos
--------------------------------------

1. Proponer cambio en sistema de control de versiones (issue/PR con motivo).
2. Probar el cambio en entorno de staging con una cuenta no-administrador.
3. Aplicar y auditar en producción, registrando el rollback plan.
