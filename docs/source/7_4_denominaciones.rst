7.4 Denominaciones
===================

Cargar denominaciones
----------------------

- Modelo: `CurrencyDenomination` almacena valores físicos (p. ej. billetes y monedas) por `Currency`.
- Flujo: en la configuración del terminal se cargan las denominaciones disponibles y la cantidad inicial de cada una.

Control de efectivo en terminales
-------------------------------

- Contabilizar entradas y salidas de efectivo por denominación para conciliar caja.
- Generar informes de arqueo (corte de caja) con resumen por denominación y totales.

Buenas prácticas
---------------

- Llevar registro de arqueos con firma o usuario responsable.
- Implementar controles para evitar manipulación y registrar discrepancias.
