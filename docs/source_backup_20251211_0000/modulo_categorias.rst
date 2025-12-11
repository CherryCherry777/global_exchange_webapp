Módulo: Categorías de Clientes
==============================

Resumen
-------

Las `Categorías` agrupan clientes y permiten aplicar reglas o descuentos por categoría. Se usan en filtros y estadísticas dentro del módulo `Clientes`.

Modelo
------

- `Categoria` (en `webapp.models`): campos principales `nombre` (único) y `descuento` (Decimal entre 0 y 1). Meta: orden por `id`.

Vistas
------

- `manage_categories` — listado y gestión de categorías.
- `modify_category(category_id)` — editar categoría.
- `create_sample_categories_view` — helper para crear categorías de ejemplo (ver `webapp/urls.py`).

Uso
---

- En el formulario de creación/edición de `Cliente` se selecciona una `Categoria`.
- En `manage_clientes` hay filtros por categoría y se muestran `total_categorias`.

Ejemplo (shell)
---------------

.. code-block:: python

   from webapp.models import Categoria
   Categoria.objects.create(nombre='VIP', descuento=0.20)
   Categoria.objects.create(nombre='Standard', descuento=0.0)

Referencia automática
---------------------

.. automodule:: webapp.models
   :members:
