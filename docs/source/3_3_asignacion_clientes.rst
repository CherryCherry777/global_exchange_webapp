3.3 Asignación de clientes a usuarios
=====================================

Este módulo permite vincular clientes específicos con operadores del sistema, estableciendo responsabilidades claras y facilitando el seguimiento de la relación comercial.

Modelo de relación
------------------

**Modelo:** ``ClienteUsuario``

Este modelo establece una relación muchos-a-muchos entre clientes y usuarios del sistema.

**Campos principales:**

- ``cliente``: Referencia al modelo ``Cliente``.
- ``usuario``: Referencia al modelo de usuario (``AUTH_USER_MODEL``).
- ``fecha_asignacion``: Fecha y hora en que se realizó la asignación.
- ``asignado_por``: Usuario que realizó la asignación (para auditoría).
- ``activo``: Indica si la asignación está vigente.

Vincular clientes con operadores
---------------------------------

**Acceso:**

Menú → Clientes → Asignaciones (vista ``assign_clients``)

**Proceso de asignación:**

1. Acceder a la vista de asignaciones.
2. Seleccionar el operador (usuario) que será responsable.
3. Elegir los clientes a asignar desde el listado disponible.
4. Confirmar la asignación.
5. El sistema registra la fecha, hora y usuario que realizó la operación.

**Casos de uso:**

- Asignar nuevos clientes al operador responsable de su zona geográfica.
- Redistribuir clientes cuando un operador está de vacaciones.
- Asignar clientes VIP a operadores especializados.
- Transferir cartera de clientes entre sucursales.

Gestionar asignaciones existentes
---------------------------------

**Visualización:**

- La vista ``assign_clients`` muestra todas las asignaciones activas.
- Se puede filtrar por operador o por cliente.
- Cada registro muestra: cliente, operador asignado, fecha de asignación.

**Desasignación:**

- Función: ``desasignar_cliente_usuario``
- Permite remover la relación entre un cliente y un operador.
- La desasignación no elimina el registro, sino que lo marca como inactivo para mantener historial.

**Acciones en masa:**

- Seleccionar múltiples asignaciones para desactivar o transferir.
- Útil para reorganizaciones de equipos o cambios de turno.

Permisos requeridos
-------------------

**Para asignar clientes:**

- ``add_clienteusuario``: Permiso para crear nuevas asignaciones.

**Para desasignar:**

- ``delete_clienteusuario``: Permiso para remover asignaciones.

**Para ver asignaciones:**

- ``view_clienteusuario``: Permiso para consultar asignaciones existentes.

Buenas prácticas
----------------

- **Auditoría completa**: Registrar quién realizó cada asignación y cuándo.
- **Evitar duplicados**: El sistema valida que no existan asignaciones duplicadas activas.
- **Historial**: No eliminar registros antiguos; marcar como inactivos para mantener trazabilidad.
- **Comunicación**: Notificar al operador cuando recibe nuevos clientes asignados.
- **Revisión periódica**: Auditar asignaciones para detectar desbalances de carga de trabajo.
- **Respaldo antes de cambios masivos**: Exportar asignaciones actuales antes de reorganizaciones.
