9.2 Cambio de cotización urgente
================================

Este procedimiento describe los pasos a seguir cuando es necesario actualizar una cotización de forma inmediata debido a un evento de mercado, error detectado o ajuste comercial.

Cuando aplicar este procedimiento
---------------------------------

**Situaciones que requieren cambio urgente:**

- Variación significativa en el mercado de divisas.
- Error detectado en cotización vigente.
- Directiva comercial de la gerencia.
- Falla en la sincronización automática de tasas.
- Evento económico o político que afecta el mercado.

**Indicadores de urgencia:**

- Diferencia mayor al 1% respecto al mercado.
- Múltiples clientes reportando cotización incorrecta.
- Alerta de fuentes de mercado sobre volatilidad.

Procedimiento paso a paso
-------------------------

**Paso 1: Validar la necesidad (5 minutos)**

1. Confirmar la variación con al menos dos fuentes:
   - API de cotizaciones del proveedor.
   - Sitio web de referencia (BCP, Bloomberg, Reuters).
   - Cotización de competidores.

2. Documentar la evidencia:
   - Captura de pantalla de las fuentes.
   - Hora exacta de la verificación.

3. Determinar el tipo de cambio:
   - Ajuste menor (< 0.5%): Procedimiento estándar.
   - Ajuste significativo (0.5% - 2%): Notificar a supervisor.
   - Ajuste mayor (> 2%): Requiere aprobación de gerencia.

**Paso 2: Notificar a stakeholders (2 minutos)**

1. Comunicar a:
   - Supervisor de operaciones.
   - Área de riesgo (si aplica).
   - Operadores de caja (para pausar operaciones temporalmente).

2. Método de notificación:
   - Mensaje interno del sistema.
   - Grupo de WhatsApp/Telegram operativo.
   - Llamada telefónica para casos críticos.

**Paso 3: Pausar operaciones (opcional)**

Para cambios mayores al 1%:

1. Activar modo "cotización en actualización" en el sistema.
2. Los operadores no procesan nuevas transacciones.
3. Transacciones en curso se completan con cotización anterior.

**Paso 4: Aplicar nueva cotización (3 minutos)**

1. Acceder a: Menú → Configuración → Cotizaciones.

2. Seleccionar la moneda a actualizar.

3. Ingresar los nuevos valores:
   - Tasa de compra (buy_rate).
   - Tasa de venta (sell_rate).
   - Verificar que el spread sea coherente.

4. Completar campos obligatorios:
   - Motivo del cambio (campo de texto).
   - Fuente de la cotización.

5. Confirmar y guardar.

**Paso 5: Verificar propagación (2 minutos)**

1. Confirmar registro en ``CurrencyHistory``:
   - Verificar timestamp.
   - Verificar que se registró el usuario.
   - Verificar el motivo.

2. Verificar en terminales:
   - Refrescar pantalla en un terminal de prueba.
   - Confirmar que muestra la nueva cotización.

3. Invalidar caches si es necesario:
   - Cache del frontend.
   - Cache de API.

**Paso 6: Comunicar y reanudar (2 minutos)**

1. Notificar a operadores que pueden reanudar.

2. Comunicar al frontend (si aplica):
   - Actualizar cotizaciones en pantallas públicas.
   - Publicar en canales de clientes.

3. Documentar el cambio:
   - Hora de aplicación.
   - Valores anterior y nuevo.
   - Personas notificadas.

Rollback y mitigación
---------------------

**Si la cotización fue errónea:**

1. Detectar el error lo antes posible.

2. Aplicar inmediatamente la cotización correcta.

3. Identificar transacciones afectadas:
   - Consultar transacciones en el periodo del error.
   - Calcular diferencia en cada transacción.

4. Evaluar impacto:
   - Número de transacciones afectadas.
   - Monto total de diferencia.
   - Determinar si requiere compensación.

5. Documentar incidente:
   - Causa del error.
   - Tiempo de exposición.
   - Acciones correctivas.
   - Medidas preventivas.

**Plan de rollback:**

.. code-block:: text

   1. Mantener cotización anterior como referencia.
   2. Si el cambio genera efectos adversos:
      a. Revertir a cotización anterior.
      b. Notificar a todos los operadores.
      c. Pausar operaciones hasta estabilizar.
   3. Investigar causa del problema.
   4. Aplicar corrección una vez validada.

Registro y auditoría
--------------------

**Información a registrar:**

- Fecha y hora exacta del cambio.
- Usuario que realizó el cambio.
- Cotización anterior.
- Cotización nueva.
- Motivo documentado.
- Fuente de la nueva cotización.
- Aprobaciones obtenidas.

**Retención:**

- Mantener historial indefinidamente para auditoría.
- Exportar periódicamente para respaldo externo.

Buenas prácticas
----------------

- Siempre validar con múltiples fuentes antes de cambiar.
- Nunca realizar cambios sin documentar el motivo.
- Probar en staging cuando sea posible (para cambios masivos).
- Mantener comunicación clara con todos los involucrados.
- Tener procedimiento de rollback preparado.
- Revisar cambios urgentes en la reunión de cierre del día.
