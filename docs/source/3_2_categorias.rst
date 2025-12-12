3.2 Categorías de clientes
==========================

Las categorías permiten segmentar a los clientes según su perfil comercial, aplicando condiciones diferenciadas como descuentos, límites de transacción y comisiones especiales.

Modelo de datos
---------------

**Modelo:** ``Categoria`` (ubicado en ``webapp/models.py``)

**Campos principales:**

- ``nombre``: Identificador único de la categoría (ej: VIP, Estándar, Corporativo). Campo obligatorio y único.
- ``descripcion``: Descripción detallada de las condiciones y beneficios de la categoría.
- ``descuento``: Porcentaje de descuento aplicable en comisiones (valor decimal entre 0 y 100).
- ``activo``: Indica si la categoría está disponible para asignación a nuevos clientes.

Crear categorías
-----------------

**Acceso:**

Menú → Configuración → Categorías → Nueva categoría

**Proceso de creación:**

1. Hacer clic en "Nueva categoría".
2. Ingresar el nombre único de la categoría.
3. Definir el porcentaje de descuento aplicable (0% si no aplica).
4. Agregar una descripción que explique los criterios de la categoría.
5. Guardar el registro.

**Ejemplos de categorías comunes:**

- **VIP**: Clientes con alto volumen de transacciones. Descuento: 15%.
- **Estándar**: Clientes regulares sin beneficios especiales. Descuento: 0%.
- **Corporativo**: Empresas con contrato comercial. Descuento: 10%.
- **Nuevo**: Clientes recién registrados en período de evaluación. Descuento: 5%.

Asignar categorías a clientes
-----------------------------

**Durante la creación del cliente:**

- El campo ``categoria`` es obligatorio al crear un nuevo cliente.
- Seleccionar la categoría apropiada del listado desplegable.

**Modificación de categoría:**

- Desde la ficha del cliente, editar el campo ``categoria``.
- Los cambios de categoría afectan inmediatamente los límites y condiciones aplicables.
- Se recomienda documentar el motivo del cambio en el historial.

**Asignación en lote:**

- Existen vistas para migrar múltiples clientes entre categorías.
- Útil para promociones masivas o reclasificación por volumen de operaciones.

Consideraciones importantes
---------------------------

**Validaciones:**

- El ``nombre`` de la categoría debe ser único en el sistema.
- No se puede eliminar una categoría que tenga clientes asignados.
- Para desactivar una categoría, primero reasignar sus clientes.

**Impacto en el negocio:**

- Los límites de intercambio pueden configurarse por categoría.
- Las comisiones de transacción consideran el descuento de la categoría.
- Los reportes pueden segmentarse por categoría para análisis.

**Buenas prácticas:**

- Mantener un número manejable de categorías (4-6 recomendado).
- Definir criterios claros y documentados para cada categoría.
- Revisar periódicamente la asignación de clientes según su comportamiento.
- Comunicar a los clientes cuando cambia su categoría.
