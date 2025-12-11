3.3 Asignación de clientes a usuarios
=====================================

Vincular clientes con operadores
---------------------------------

- Modelo: `ClienteUsuario` — relación entre `Cliente` y `AUTH_USER_MODEL`.
- Flujo: desde `assign_clients` se elige cliente y operador (usuario) y se crea la asignación.

Gestionar asignaciones
----------------------

- Ver asignaciones actuales en la interfaz `assign_clients`.
- Desasignar mediante `desasignar_cliente_usuario` o acciones en masa.
- Reglas: evitar duplicados y respetar permisos (`add_clienteusuario`, `delete_clienteusuario`).

Buenas prácticas
----------------

- Registrar quién realizó la asignación y cuándo (auditoría).
- Proveer una vista de historial para revertir asignaciones si fuera necesario.
