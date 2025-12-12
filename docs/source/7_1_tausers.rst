7.1 ¿Qué son los T-ausers?
=========================

Definición
----------

Los "T-ausers" son terminales/usuarios técnicos (terminal users) que representan dispositivos físicos o instancias de caja conectadas al sistema. Se usan para procesar operaciones en punto de venta y para controlar efectivo físico en terminales.

Casos de uso
-----------

- Registrar operaciones desde un terminal físico.
- Asociar denominaciones y controlar saldo físico por terminal.
- Monitorizar estado y conectividad de la terminal.

Modelo y relaciones
-------------------

- `Tauser` / `TauserTerminal` (ver `webapp.models`) suele incluir identificador único, ubicación, estado (online/offline) y metadatos.
- Relación con `Transaccion` y `Billetera` para rastrear movimientos.

Seguridad
--------

- Cada terminal debe autenticarse (API key o certificado) y registrar actividad para auditoría.
