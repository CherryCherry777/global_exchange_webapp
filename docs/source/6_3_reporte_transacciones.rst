6.3 Reporte de transacciones
=============================

Los reportes de transacciones proporcionan visibilidad completa sobre las operaciones realizadas, permitiendo análisis, auditoría y conciliación contable.

Acceso a reportes
-----------------

**Ubicación:**

Menú → Reportes → Transacciones (vista ``reporte_transacciones``)

**Permisos requeridos:**

- ``view_transaccion``: Ver listado de transacciones.
- ``export_transaccion``: Exportar reportes a CSV/Excel.

Filtros de búsqueda
-------------------

**Filtros disponibles:**

- **Rango de fechas**: Selección de fecha inicio y fecha fin con calendario.
- **Cliente**: Búsqueda por nombre o documento del cliente.
- **Categoría**: Filtrar por categoría de cliente (VIP, Estándar, etc.).
- **Moneda**: Filtrar por moneda origen o destino de la operación.
- **Estado**: Filtrar por estado (completada, pendiente, cancelada, rechazada).
- **Operador**: Filtrar por el usuario que realizó la operación.
- **Terminal**: Filtrar por terminal/caja donde se procesó.

**Combinación de filtros:**

- Los filtros son acumulativos (AND lógico).
- Los resultados se actualizan en tiempo real al aplicar filtros.

**Paginación:**

- Resultados paginados para manejar grandes volúmenes.
- Configuración de items por página: 25, 50, 100.

Columnas del reporte
--------------------

**Información incluida:**

- ``fecha``: Fecha y hora de la transacción.
- ``codigo``: Código único de la transacción.
- ``cliente``: Nombre del cliente.
- ``documento``: Documento de identidad del cliente.
- ``moneda_origen``: Moneda entregada por el cliente.
- ``monto_origen``: Monto en moneda origen.
- ``moneda_destino``: Moneda recibida por el cliente.
- ``monto_destino``: Monto en moneda destino.
- ``tasa_aplicada``: Tipo de cambio utilizado.
- ``comision``: Monto de comisión cobrada.
- ``estado``: Estado actual de la transacción.
- ``operador``: Usuario que procesó la operación.
- ``terminal``: Identificador del punto de venta.

Exportar reportes
-----------------

**Formato CSV:**

1. Aplicar los filtros deseados.
2. Hacer clic en "Exportar CSV".
3. El archivo se descarga con cabecera ``Content-Disposition: attachment``.
4. Abre en Excel, Google Sheets u otra herramienta de análisis.

**Contenido del archivo:**

- Primera fila: encabezados de columnas.
- Codificación: UTF-8 con BOM para compatibilidad con Excel.
- Separador: coma (,).

**Ejemplo de exportación programática:**

.. code-block:: python

   import requests

   # Autenticación (ajustar según implementación)
   session = requests.Session()
   session.post('http://localhost:8000/accounts/login/', data={
       'username': 'operador',
       'password': 'password'
   })

   # Descargar reporte con filtros
   response = session.get('http://localhost:8000/reportes/transacciones/', params={
       'from': '2025-01-01',
       'to': '2025-01-31',
       'estado': 'completada',
       'format': 'csv'
   })

   # Guardar archivo
   with open('reporte_enero_2025.csv', 'wb') as f:
       f.write(response.content)

Análisis de datos
-----------------

**Métricas clave:**

- Volumen total de transacciones por periodo.
- Monto total operado por moneda.
- Ingresos por comisiones.
- Transacciones por categoría de cliente.
- Rendimiento por operador.
- Distribución horaria de operaciones.

**Herramientas recomendadas:**

- Microsoft Excel / Google Sheets para análisis básico.
- Python con Pandas para análisis avanzado.
- Power BI / Tableau para dashboards interactivos.

**Ejemplo con Pandas:**

.. code-block:: python

   import pandas as pd

   # Cargar reporte exportado
   df = pd.read_csv('reporte_transacciones.csv')

   # Volumen por moneda
   print(df.groupby('moneda_origen')['monto_origen'].sum())

   # Top 10 clientes por volumen
   print(df.groupby('cliente')['monto_origen'].sum().nlargest(10))

   # Transacciones por día
   df['fecha'] = pd.to_datetime(df['fecha'])
   print(df.groupby(df['fecha'].dt.date).size())

Dashboards internos
-------------------

**Widgets disponibles:**

- Gráfico de volumen diario.
- Top clientes del periodo.
- Distribución por moneda (pie chart).
- Ingresos por comisiones (tendencia).

**Actualización:**

- Los dashboards se actualizan en tiempo real.
- Posibilidad de configurar período de visualización.

Consideraciones
---------------

- Limitar el rango de fechas para consultas grandes (mejor rendimiento).
- Programar exportaciones de reportes periódicos mediante tareas automatizadas.
- Almacenar copias de reportes críticos para auditoría.
- Verificar permisos antes de compartir reportes con datos sensibles.
