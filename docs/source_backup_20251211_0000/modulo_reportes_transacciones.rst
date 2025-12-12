Reportes de transacciones
==========================

Descripción
-----------

Contiene las vistas y utilidades para generar reportes exportables de transacciones y ganancias. Soporta filtros y exportación a CSV.

Vistas relevantes
-----------------

.. automodule:: webapp.views.reportes_transacciones_ganancias
   :members:
   :noindex:

- `reporte_transacciones` : vista que genera un CSV con las transacciones filtradas por fechas, categoría, moneda y estado.

Uso (exportar CSV)
-------------------

1. Accede a la página de reportes en el panel: `reportes/`.
2. Aplica filtros y pulsa `Exportar CSV` (la vista responde con `Content-Disposition: attachment; filename="reporte_transacciones.csv"`).

Ejemplo en Python (descarga):

.. code-block:: python

   import requests
   r = requests.get('http://localhost:8000/reportes/', params={'from':'2025-01-01','to':'2025-01-31'})
   open('reporte_transacciones.csv','wb').write(r.content)

Notas
-----

- Revisa la paginación y permisos: la vista requiere permisos adecuados en el backend para evitar divulgación de datos.
