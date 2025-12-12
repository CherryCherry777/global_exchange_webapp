```restructuredtext
Entidades de pago / cobro
=========================

Descripción
-----------

Documenta las entidades que participan en los flujos de pago y cobro: proveedores, cuentas bancarias, billeteras de negocios y configuraciones relacionadas para conciliación.

Modelos clave
------------

.. list-table:: Modelos clave
   :widths: 25 75
   :header-rows: 0

   * - `Entidad` - Proveedor o contraparte (p. ej. banco, PSP, conciliador).
   * - `CuentaBancariaNegocio` - Cuenta bancaria del negocio o de un tercero para recepción/envío de fondos.
   * - `Billetera` / `BilleteraCobro` - Representación de saldos internos asociados a la entidad.

Autodoc
-------

.. automodule:: webapp.models
   :members: Entidad, CuentaBancariaNegocio, Billetera, BilleteraCobro
   :noindex:

Integraciones y sincronización
------------------------------

- Señales (`webapp/signals.py`) mantienen coherencia entre `Entidad`, cuentas y `LimiteIntercambioConfig` cuando se crean o actualizan proveedores.
- Revisa `webapp/tasks.py` para procesos periódicos que reconcilián o sincronizan saldos.

Consideraciones
--------------

- Mantén registros de identificación (IBAN, CBU) cifrados o con acceso restringido.
- Documenta procedimientos de onboarding para nuevas `Entidad` y cómo configurarlas en la UI.

```