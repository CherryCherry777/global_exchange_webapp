7.4 Denominaciones
===================

Las denominaciones representan los valores físicos de billetes y monedas disponibles en cada terminal, permitiendo el control preciso del efectivo.

Modelo de datos
---------------

**Modelo:** ``CurrencyDenomination``

**Campos principales:**

- ``currency``: Moneda a la que pertenece la denominación.
- ``valor``: Valor nominal de la denominación (ej: 100000, 50000, 20000 para PYG).
- ``tipo``: Tipo de denominación (billete, moneda).
- ``activo``: Indica si la denominación está en circulación.
- ``imagen``: Imagen representativa (opcional).

**Modelo:** ``CajaDenominacion`` (inventario por terminal)

**Campos:**

- ``terminal``: Referencia al T-auser.
- ``denominacion``: Referencia a ``CurrencyDenomination``.
- ``cantidad``: Número de unidades disponibles.
- ``fecha_actualizacion``: Última modificación del inventario.

Cargar denominaciones
----------------------

**Configuración inicial de denominaciones:**

1. Acceder a Menú → Configuración → Denominaciones.
2. Para cada moneda operada, definir las denominaciones disponibles.
3. Ingresar el valor nominal de cada billete/moneda.
4. Marcar como activas las denominaciones en circulación.

**Ejemplo para PYG:**

- Billetes: 100.000, 50.000, 20.000, 10.000, 5.000, 2.000
- Monedas: 1.000, 500, 100, 50

**Ejemplo para USD:**

- Billetes: 100, 50, 20, 10, 5, 1
- Monedas: 0.25, 0.10, 0.05, 0.01 (generalmente no se manejan)

**Carga de inventario en terminal:**

1. Ir a Terminales → Seleccionar terminal → Denominaciones.
2. Para cada denominación, ingresar la cantidad disponible.
3. Confirmar el inventario inicial.
4. El sistema calcula automáticamente el total en caja.

Control de efectivo en terminales
---------------------------------

**Registro de movimientos:**

Cada transacción actualiza el inventario de denominaciones:

- **Entrada**: Efectivo recibido del cliente (se incrementa inventario).
- **Salida**: Efectivo entregado al cliente (se decrementa inventario).

**Contabilización:**

.. code-block:: text

   Saldo en caja = Σ (cantidad_denominacion × valor_denominacion)
   
   Ejemplo:
   - 10 billetes de 100.000 = 1.000.000
   - 20 billetes de 50.000 = 1.000.000
   - 50 billetes de 20.000 = 1.000.000
   - Total en caja: 3.000.000 PYG

**Alertas de inventario:**

- Denominación agotándose (menos de X unidades).
- Exceso de denominación (más de Y unidades).
- Desbalance detectado (diferencia entre calculado y reportado).

Arqueo de caja
--------------

**Propósito:**

El arqueo (o corte de caja) es el proceso de verificar que el efectivo físico coincide con el registrado en el sistema.

**Proceso de arqueo:**

1. El operador cuenta físicamente el efectivo por denominación.
2. Registra las cantidades en el formulario de arqueo.
3. El sistema compara con el inventario esperado.
4. Se generan reportes de diferencias si existen.
5. El supervisor aprueba y cierra el arqueo.

**Informe de arqueo:**

- Denominación | Cantidad Sistema | Cantidad Física | Diferencia
- Total esperado vs Total contado
- Observaciones del operador
- Firma/aprobación del supervisor

**Frecuencia recomendada:**

- Al inicio de cada turno.
- Al cierre de cada turno.
- Ante sospecha de discrepancia.

Buenas prácticas
----------------

- **Registro detallado**: Mantener registro de cada arqueo con responsable y timestamp.
- **Investigar discrepancias**: Cualquier diferencia debe investigarse y documentarse.
- **Controles cruzados**: Dos personas para arqueos de montos significativos.
- **Respaldo físico**: Conservar formularios de arqueo firmados.
- **Reposición oportuna**: Solicitar reposición antes de que se agoten denominaciones.
- **Seguridad**: Limitar acceso al módulo de denominaciones a personal autorizado.
