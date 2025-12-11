6.3 Reporte de transacciones
=============================

Filtros de búsqueda
-------------------

- Filtrar por rango de fechas, cliente, categoría, moneda y estado.
- Paginación: devolver resultados paginados para grandes volúmenes.

Exportar reportes
-----------------

- La vista `reporte_transacciones` permite exportar CSV con `Content-Disposition: attachment`.
- Incluir columnas clave: `fecha`, `cliente`, `moneda`, `monto_origen`, `monto_destino`, `comision`, `estado`.

Análisis de datos
-----------------

- Sugerencia: exportar y analizar en herramientas externas (Excel, Pandas).
- Añadir dashboards internos para métricas periódicas (volumen diario, top clientes, ingresos por comisión).

Ejemplo (descarga CSV con Python)
--------------------------------

.. code-block:: python

   import requests
   r = requests.get('http://localhost:8000/reportes/', params={'from':'2025-01-01','to':'2025-01-31'})
   open('reporte_transacciones.csv','wb').write(r.content)
