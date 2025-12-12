```restructuredtext
Métodos de pago (globales)
==========================

Descripción
-----------

Documenta los métodos de pago soportados para pagar servicios o productos en la plataforma. Incluye configuraciones generales, modelos referenciados y cómo se exponen en la interfaz de administración.

Modelos y conceptos
--------------------

.. list-table:: Modelos y conceptos
   :widths: 25 75
   :header-rows: 0

   * - `MedioPago` - Representa un método de pago configurado (p. ej. tarjeta, transferencia, billetera).
   * - `TipoPago` - Categoría o subtipo (p. ej. "Tarjeta de crédito", "Tarjeta de débito").
   * - `CuentaBancariaNegocio` - Cuenta del negocio usada para conciliación cuando aplica.

Autodoc
-------

.. automodule:: webapp.models
   :members: MedioPago, TipoPago, CuentaBancariaNegocio
   :noindex:

Vistas y formularios
---------------------

- Formularios de configuración en `webapp/forms.py` y vistas CRUD en `webapp/views`.
- Integraciones externas (p. ej. Stripe, pasarelas) están referenciadas en funciones específicas de pago y sincronización.

Consideraciones de seguridad
---------------------------

- Nunca almacenar números de tarjeta en texto claro; usa tokenización provista por el PSP.
- Revisa permisos de administración para quién puede habilitar/deshabilitar `MedioPago`.

```