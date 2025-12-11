3.2 Categorías de clientes
==========================

Crear categorías
-----------------

- Modelo: `Categoria` (ver `webapp.models`) con campos `nombre` y `descuento`.
- Pasos: ir a Categorías > Nueva categoría, completar `nombre` y valores asociados.

Asignar categorías
------------------

- En la creación o edición de un `Cliente` se selecciona la `Categoria` correspondiente.
- También existen vistas para asignar categorías en lote o migrar clientes entre categorías.

Consideraciones
---------------

- Validar unicidad de `nombre` y revisar reglas de negocio al aplicar descuentos.
- Documentar el impacto de las categorías en límites de intercambio o comisiones.
