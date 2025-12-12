Métodos de cobro (globales)
===========================

Descripción
-----------

Documenta los métodos que la plataforma utiliza para recibir pagos (cobros) de clientes o terceros: billeteras de cobro, cuentas bancarias, pasarelas de cobro integradas y sus formularios.

Modelos y componentes
---------------------

.. list-table:: Modelos y componentes
   :widths: 25 75
   :header-rows: 0

   * - `MedioCobro` - Medio por el cual se recibe dinero (p. ej. "Cuenta bancaria", "Billetera de cobro").
   * - `BilleteraCobro` - Entidad interna para manejar cobros por billetera.
   * - `CuentaBancariaCobro` - Cuentas usadas para cobros y conciliación.

Autodoc
-------

.. automodule:: webapp.models
   :members: MedioCobro, BilleteraCobro, CuentaBancariaCobro
   :noindex:

Flujos y vistas
----------------

- Formularios de registrar medios de cobro en `webapp/forms.py`.
- Vistas que muestran estados de cobro y registros en `webapp/views`.

Notas operativas
----------------

- Asegura que los endpoints de webhooks (si existen) validen firmas y origen.
- Define claramente la relación entre `MedioCobro` y entidades externas (proveedor, identificador de cuenta).
