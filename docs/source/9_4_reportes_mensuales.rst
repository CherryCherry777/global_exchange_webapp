9.4 Generación de reportes mensuales
====================================

Esta guía describe el proceso para generar, automatizar y distribuir reportes mensuales para finanzas, gerencia y cumplimiento regulatorio.

Tipos de reportes mensuales
---------------------------

**Reporte de operaciones:**

- Total de transacciones realizadas.
- Volumen por moneda (compras y ventas).
- Distribución por día de la semana.
- Comparativa con mes anterior.

**Reporte de ingresos:**

- Ingresos totales por comisiones.
- Desglose por tipo de operación.
- Desglose por categoría de cliente.
- Spread promedio por moneda.

**Reporte de clientes:**

- Nuevos clientes registrados.
- Clientes activos (con al menos una transacción).
- Top 10 clientes por volumen.
- Distribución por categoría.

**Reporte de operadores:**

- Transacciones por operador.
- Volumen procesado por operador.
- Tickets atendidos por operador.
- Incidencias por operador.

**Reporte de cumplimiento:**

- Transacciones sobre umbral regulatorio.
- Clientes con KYC pendiente.
- Alertas de AML generadas.
- Reportes enviados a entidades reguladoras.

Proceso de generación manual
----------------------------

**Paso 1: Definir parámetros**

1. Acceder a: Menú → Reportes → Reportes mensuales.

2. Seleccionar parámetros:
   - Período: Mes y año (ej: Noviembre 2025).
   - Tipo de reporte: Operaciones, Ingresos, Clientes, etc.
   - Filtros adicionales: Sucursal, categoría, moneda.

**Paso 2: Generar reporte**

1. Hacer clic en "Generar reporte".

2. El sistema procesa los datos (puede tomar varios minutos para volúmenes grandes).

3. Se muestra vista previa del reporte.

**Paso 3: Exportar**

1. Seleccionar formato de exportación:
   - **CSV**: Para análisis en Excel o herramientas BI.
   - **PDF**: Para presentaciones y archivo.
   - **Excel**: Con formato y gráficos.

2. Descargar el archivo.

3. Verificar contenido antes de distribuir.

**Paso 4: Archivar**

1. Guardar copia en carpeta de archivo mensual.

2. Nombrar con convención estándar:
   - ``reporte_operaciones_2025_11.csv``
   - ``reporte_ingresos_2025_11.pdf``

Automatización de reportes
--------------------------

**Configuración de tareas programadas:**

.. code-block:: python

   # webapp/tasks.py
   from celery import shared_task
   from datetime import datetime, timedelta

   @shared_task
   def generar_reportes_mensuales():
       """
       Genera reportes del mes anterior.
       Programar para ejecutarse el día 1 de cada mes.
       """
       # Calcular mes anterior
       hoy = datetime.now()
       primer_dia_mes_actual = hoy.replace(day=1)
       ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
       mes_reporte = ultimo_dia_mes_anterior.month
       anio_reporte = ultimo_dia_mes_anterior.year
       
       # Generar cada tipo de reporte
       reportes = [
           ('operaciones', generar_reporte_operaciones),
           ('ingresos', generar_reporte_ingresos),
           ('clientes', generar_reporte_clientes),
       ]
       
       for nombre, funcion in reportes:
           archivo = funcion(mes_reporte, anio_reporte)
           # Subir a storage seguro
           upload_to_storage(archivo, f'reportes/{anio_reporte}/{mes_reporte}/')
           # Enviar por email si configurado
           enviar_reporte_email(archivo, destinatarios)

**Programación con Celery Beat:**

.. code-block:: python

   # settings.py
   CELERY_BEAT_SCHEDULE = {
       'generar-reportes-mensuales': {
           'task': 'webapp.tasks.generar_reportes_mensuales',
           'schedule': crontab(day_of_month=1, hour=6, minute=0),
       },
   }

Análisis y distribución
-----------------------

**Destinatarios típicos:**

- **Gerencia**: Resumen ejecutivo con KPIs clave.
- **Finanzas**: Detalle de ingresos y conciliación.
- **Operaciones**: Métricas de productividad.
- **Cumplimiento**: Reportes regulatorios.

**Métodos de distribución:**

1. **Email automático**:
   - Configurar lista de destinatarios por tipo de reporte.
   - Adjuntar archivo y resumen en el cuerpo.

2. **Carpeta compartida**:
   - Subir a drive/sharepoint corporativo.
   - Notificar a interesados.

3. **Dashboard BI**:
   - Integrar datos con Power BI, Tableau, etc.
   - Actualización automática mensual.

**Integración con herramientas BI:**

.. code-block:: python

   # Ejemplo: Exportar a formato compatible con Power BI
   import pandas as pd

   def exportar_para_bi(mes, anio):
       transacciones = Transaccion.objects.filter(
           fecha__month=mes,
           fecha__year=anio
       ).values(
           'fecha', 'cliente__nombre', 'cliente__categoria__nombre',
           'moneda_origen__code', 'monto_origen',
           'moneda_destino__code', 'monto_destino',
           'comision', 'operador__username'
       )
       
       df = pd.DataFrame(transacciones)
       df.to_csv(f'data_bi_{anio}_{mes}.csv', index=False)

Archivo y retención
-------------------

**Política de retención:**

- Reportes mensuales: Conservar mínimo 5 años.
- Reportes regulatorios: Según normativa aplicable (generalmente 10 años).
- Datos fuente: Indefinido en base de datos.

**Organización de archivos:**

.. code-block:: text

   /reportes/
   ├── 2025/
   │   ├── 01/
   │   │   ├── reporte_operaciones_2025_01.csv
   │   │   ├── reporte_ingresos_2025_01.pdf
   │   │   └── reporte_clientes_2025_01.xlsx
   │   ├── 02/
   │   └── ...
   └── 2024/
       └── ...

Buenas prácticas
----------------

- Verificar datos antes de distribuir reportes.
- Mantener consistencia en formato y nomenclatura.
- Documentar cualquier ajuste o corrección aplicada.
- Automatizar todo lo posible para reducir errores manuales.
- Revisar periódicamente que la automatización funciona correctamente.
