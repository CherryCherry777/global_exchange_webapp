4.3 Límites de intercambio
==========================

Configurar límites mínimos y máximos
-----------------------------------

- Modelo: `LimiteIntercambioConfig` contiene los límites por periodo (diario, mensual) y por moneda/categoría.
- Interfaz: formulario `limite_edit` para establecer `min`, `max`, y parámetros de frecuencia.

Límites por moneda
-------------------

- Definir topes específicos para cada `Currency` cuando corresponda (p. ej. monedas volátiles pueden tener límites más bajos).
- Asegurar que las validaciones de transacción consulten la configuración activa antes de crear una `Transaccion`.

Límites por categoría de cliente
--------------------------------

- La configuración puede incluir `categoria` como llave para aplicar límites diferentes a clientes VIP u otros segmentos.
- Implementación práctica: `LimiteIntercambioCliente` guarda saldos consumidos y se compara con la `LimiteIntercambioConfig` al procesar transacciones.

Notas operativas
----------------

- Exponer en la UI una vista de consumo actual por cliente y la ventana temporal (día/mes) para transparencia.
- Tener una tarea de reseteo (p. ej. `check_and_reset_limites_intercambio`) cuya configuración está en `LimiteIntercambioScheduleConfig`.
