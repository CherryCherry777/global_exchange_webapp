2.2 Roles
=========

Tipos de roles
--------------

- `Administrador`: control total, puede gestionar usuarios, roles, configuración y límites.
- `Empleado` / `Operador`: acceso a operaciones diarias (gestión de clientes, transacciones), sin permisos críticos.
- `Usuario` / `Cliente`: nivel mínimo, acceso a interfaces de cliente y consultas.

Nota: Los nombres y niveles concretos están definidos en `webapp/views/constants.py` y en `webapp/models.py` (modelo `Role` si existe).

Permisos por rol
-----------------

- Los permisos se gestionan con `django.contrib.auth.models.Permission` y se asignan a `Group`.
- Ejemplos de permisos frecuentes:
  - `add_cliente`, `change_cliente`, `delete_cliente`, `view_cliente`
  - `add_transaccion`, `change_transaccion`, `view_transaccion`
  - `view_limiteintercambioconfig`, `change_limiteintercambioconfig`

Recomendaciones
---------------

- Mantener un rol `Administrador` protegido (`PROTECTED_ROLES`) para evitar eliminación accidental.
- Documentar la matriz de permisos y revisar periódicamente las asignaciones.
