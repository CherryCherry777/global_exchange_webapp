4.3 Límites de intercambio
==========================

Los límites de intercambio controlan los montos máximos y mínimos que los clientes pueden transaccionar, cumpliendo con políticas internas y regulaciones de prevención de lavado de dinero (AML).

Modelo de configuración
-----------------------

**Modelo:** ``LimiteIntercambioConfig``

**Campos principales:**

- ``moneda``: Moneda a la que aplica el límite.
- ``categoria``: Categoría de cliente (opcional; si no se especifica, aplica a todos).
- ``monto_min``: Monto mínimo por transacción.
- ``monto_max``: Monto máximo por transacción.
- ``limite_diario``: Monto máximo acumulado permitido en un día.
- ``limite_mensual``: Monto máximo acumulado permitido en un mes.
- ``activo``: Indica si la configuración está vigente.

Configurar límites mínimos y máximos
------------------------------------

**Acceso:**

Menú → Configuración → Límites de intercambio (formulario ``limite_edit``)

**Proceso de configuración:**

1. Seleccionar la moneda para la cual definir límites.
2. Opcionalmente, seleccionar una categoría de cliente específica.
3. Definir el monto mínimo por transacción (evita operaciones insignificantes).
4. Definir el monto máximo por transacción (control de riesgo).
5. Establecer límites acumulados diarios y mensuales.
6. Activar la configuración y guardar.

**Ejemplo de configuración:**

- USD - Estándar: Mín $50, Máx $5,000, Diario $10,000, Mensual $50,000.
- USD - VIP: Mín $100, Máx $50,000, Diario $100,000, Mensual $500,000.

Límites por moneda
-------------------

**Consideraciones por tipo de moneda:**

- **Monedas volátiles**: Límites más conservadores para reducir exposición al riesgo.
- **Monedas principales (USD, EUR)**: Límites más amplios por mayor liquidez.
- **Moneda local (PYG)**: Límites acordes a regulaciones locales.

**Validación en transacciones:**

Antes de crear una transacción, el sistema verifica:

1. Que el monto cumpla con el mínimo configurado.
2. Que el monto no exceda el máximo por transacción.
3. Que el acumulado diario del cliente no supere el límite.
4. Que el acumulado mensual del cliente no supere el límite.

Límites por categoría de cliente
--------------------------------

**Modelo:** ``LimiteIntercambioCliente``

Registra el consumo acumulado de límites por cliente:

- ``cliente``: Referencia al cliente.
- ``moneda``: Moneda del límite.
- ``consumido_diario``: Monto acumulado del día actual.
- ``consumido_mensual``: Monto acumulado del mes actual.
- ``fecha_ultimo_reset``: Fecha del último reinicio de contadores.

**Flujo de validación:**

1. Al procesar una transacción, se consulta ``LimiteIntercambioCliente``.
2. Se compara el consumo actual + monto nuevo contra ``LimiteIntercambioConfig``.
3. Si excede, la transacción es rechazada con mensaje informativo.
4. Si es válida, se actualiza el consumo y se registra en ``LimiteIntercambioLog``.

Tareas de reseteo
-----------------

**Modelo:** ``LimiteIntercambioScheduleConfig``

**Tarea programada:** ``check_and_reset_limites_intercambio``

**Funcionamiento:**

- **Reset diario**: A las 00:00 de cada día, se reinician los contadores diarios.
- **Reset mensual**: El primer día de cada mes, se reinician los contadores mensuales.
- El sistema mantiene historial de resets para auditoría.

Vistas de consulta
------------------

**Para administradores:**

- Listado de configuraciones de límites activos.
- Estadísticas de clientes cerca del límite.

**Para operadores:**

- Consulta de límite disponible por cliente antes de operar.
- Visualización del consumo actual (diario/mensual).

**Para clientes (si aplica):**

- Vista de sus límites asignados y consumo actual.
- Ventana temporal restante para reset.

Notas operativas
----------------

- Exponer en la UI el consumo actual por cliente para transparencia operativa.
- Configurar notificaciones cuando un cliente alcanza el 80% de su límite.
- Mantener logs de transacciones rechazadas por límite para análisis.
- Revisar periódicamente la configuración de límites según evolución del negocio.
