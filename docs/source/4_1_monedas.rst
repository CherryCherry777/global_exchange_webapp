4.1 Monedas
===========

El módulo de Monedas gestiona todas las divisas disponibles en el sistema para operaciones de cambio, incluyendo su configuración, formato de visualización y estado operativo.

Modelo de datos
---------------

**Modelo:** ``Currency`` (ubicado en ``webapp/models.py``)

**Campos principales:**

- ``code``: Código ISO 4217 de la moneda (ej: USD, EUR, PYG). Campo único y obligatorio.
- ``name``: Nombre completo de la moneda (ej: "Dólar estadounidense", "Guaraní paraguayo").
- ``symbol``: Símbolo de la moneda para visualización (ej: $, €, ₲).
- ``decimals``: Número de decimales para cálculos y presentación (normalmente 2, pero 0 para PYG).
- ``decimales_cotizacion``: Decimales específicos para mostrar cotizaciones.
- ``flag_image``: Imagen de la bandera del país asociado (para interfaz gráfica).
- ``is_active``: Indica si la moneda está habilitada para transacciones.

Listado de monedas disponibles
------------------------------

**Acceso:**

Menú → Configuración → Monedas (vista ``manage_currencies``)

**Información mostrada:**

- Código y nombre de cada moneda.
- Símbolo y bandera.
- Estado actual (activa/inactiva).
- Fecha de última actualización de cotización.

**Funcionalidades del listado:**

- Búsqueda por código o nombre.
- Filtrado por estado (activas/inactivas).
- Ordenamiento por cualquier columna.

Activar / desactivar monedas
----------------------------

**Función:** ``toggle_currency_active``

**Efectos de desactivar una moneda:**

- La moneda no aparece en los formularios de transacción.
- No se puede seleccionar como origen o destino de operaciones.
- Las transacciones históricas permanecen intactas.
- Las cotizaciones pueden seguir actualizándose para referencia.

**Proceso para desactivar:**

1. Acceder al listado de monedas.
2. Localizar la moneda a desactivar.
3. Hacer clic en el botón de estado o seleccionar "Desactivar".
4. Confirmar la acción.

**Proceso para reactivar:**

1. En el listado, filtrar por monedas inactivas.
2. Seleccionar la moneda.
3. Hacer clic en "Activar".
4. Verificar que tenga cotización vigente antes de permitir transacciones.

Configurar una nueva moneda
---------------------------

**Pasos para agregar una moneda:**

1. Acceder a Monedas → Nueva moneda.
2. Ingresar el código ISO (verificar estándar ISO 4217).
3. Completar nombre, símbolo y configuración de decimales.
4. Subir la imagen de bandera (opcional pero recomendado).
5. Definir el estado inicial (activa/inactiva).
6. Guardar y configurar la cotización inicial.

Consideraciones importantes
---------------------------

**Antes de desactivar una moneda:**

- Verificar que no existan transacciones pendientes con esa moneda.
- Revisar saldos en billeteras y cuentas asociadas.
- Notificar a los operadores sobre el cambio.
- Considerar un período de transición para clientes frecuentes.

**Decimales y redondeo:**

- Los decimales afectan cómo se muestran los montos en pantalla.
- Los cálculos internos mantienen precisión completa.
- El redondeo se aplica solo en la presentación final.

**Buenas prácticas:**

- Mantener actualizada la imagen de bandera para facilitar identificación visual.
- Documentar cambios de políticas de monedas en el changelog operativo.
- Realizar pruebas en staging antes de activar nuevas monedas en producción.
- Monitorear el volumen de transacciones por moneda para decisiones de negocio.
