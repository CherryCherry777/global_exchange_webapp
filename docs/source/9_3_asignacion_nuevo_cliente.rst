9.3 Asignación de nuevo cliente
================================

Objetivo
--------

Describir el proceso para incorporar un nuevo cliente y asignarlo a un operador u equipo.

Flujo recomendado
-----------------

1. Crear cliente: completar `ClienteForm` con datos y categoría.
2. Validar información: verificar documento, correo y KYC si aplica.
3. Asignar operador: usar `assign_clients` o interfaz de asignación; registrar `ClienteUsuario`.
4. Comunicar al operador y actualizar estado de cliente.

Puntos de control
-----------------

- Validar límites y restricciones según categoría antes de habilitar transacciones.
- Registrar auditoría de quién asignó y cuándo.
