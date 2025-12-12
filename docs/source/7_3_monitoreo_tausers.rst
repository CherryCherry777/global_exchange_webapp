7.3 Monitoreo de T-ausers
=========================

El monitoreo de terminales permite supervisar el estado operativo de todos los puntos de venta, detectar problemas y garantizar la continuidad del servicio.

Indicadores clave
-----------------

**Estado de conexión:**

- **Online**: Terminal conectado y operativo.
- **Offline**: Sin comunicación con el servidor.
- **Intermitente**: Conexión inestable con desconexiones frecuentes.
- **Mantenimiento**: Terminal en mantenimiento programado.
- **Deshabilitado**: Terminal bloqueado por seguridad o decisión administrativa.

**Métricas de actividad:**

- Última sincronización (timestamp y tiempo transcurrido).
- Número de transacciones procesadas (hoy, semana, mes).
- Volumen total operado.
- Tiempo promedio por transacción.

**Indicadores de salud:**

- Errores en las últimas 24 horas.
- Transacciones fallidas o rechazadas.
- Alertas de seguridad.

Dashboard de terminales
-----------------------

**Acceso:**

Menú → Terminales → Monitor

**Vista de lista:**

- Tabla con todos los terminales registrados.
- Indicador visual de estado (verde/amarillo/rojo).
- Filtros por sucursal, estado, ubicación.
- Ordenamiento por cualquier columna.

**Vista de mapa (si disponible):**

- Ubicación geográfica de cada terminal.
- Iconos con estado en tiempo real.
- Clic para ver detalles del terminal.

**Vista de detalle:**

- Información completa del terminal.
- Gráfico de actividad (transacciones por hora).
- Historial de conexión.
- Últimas transacciones procesadas.

Logs y trazas
-------------

**Tipos de registros:**

- **Conexión/desconexión**: Eventos de cambio de estado.
- **Transacciones**: Operaciones procesadas con resultado.
- **Errores**: Fallos con detalle técnico.
- **Seguridad**: Intentos de acceso, cambios de credenciales.

**Consulta de logs:**

1. Seleccionar el terminal.
2. Ir a la pestaña "Logs".
3. Filtrar por tipo de evento, rango de fechas, severidad.
4. Exportar a CSV si se requiere análisis detallado.

**Retención de logs:**

- Logs operativos: 30 días online, archivado posterior.
- Logs de seguridad: 1 año mínimo por cumplimiento.
- Logs de transacciones: indefinido (vinculados a transacciones).

Alertas y notificaciones
------------------------

**Configuración de alertas:**

- Terminal offline por más de X minutos.
- Errores repetidos (más de N en Y minutos).
- Transacciones atípicas (montos inusuales).
- Intentos de acceso no autorizados.

**Canales de notificación:**

- Email a administradores.
- SMS para alertas críticas (si configurado).
- Notificaciones push en la aplicación.
- Integración con sistemas de alerting (PagerDuty, Opsgenie).

**Escalamiento:**

- Nivel 1: Notificación al operador responsable.
- Nivel 2: Escalamiento a supervisor tras X minutos sin respuesta.
- Nivel 3: Alerta a administración central.

Acciones de gestión
-------------------

**Reinicio remoto:**

- Si el terminal soporta control remoto, enviar comando de reinicio.
- Registrar la acción y el usuario que la ejecutó.

**Bloqueo de terminal:**

- Deshabilitar terminal comprometido inmediatamente.
- Revocar credenciales (regenerar API key).
- Notificar al responsable del terminal.

**Modo mantenimiento:**

- Marcar terminal como "en mantenimiento".
- El terminal no procesa transacciones pero mantiene conexión.
- Útil para actualizaciones o revisiones.

Buenas prácticas
----------------

- Revisar el dashboard de terminales al inicio de cada jornada.
- Investigar cualquier terminal offline por más de 15 minutos.
- Mantener actualizados los datos de contacto de responsables.
- Realizar pruebas periódicas de conectividad y rendimiento.
- Documentar incidentes y acciones tomadas.
