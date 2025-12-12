**10.3 Contacto de soporte**
============================

Esta página describe los canales disponibles para obtener ayuda técnica y cómo reportar problemas efectivamente.

Canales de soporte
------------------

**Sistema de Issues en GitHub**

- **Uso**: Reportar bugs, solicitar funcionalidades, documentar problemas técnicos.
- **Acceso**: Sección "Issues" del repositorio.
- **Etiquetas disponibles**:
  - ``bug``: Problema o comportamiento incorrecto.
  - ``enhancement``: Solicitud de nueva funcionalidad.
  - ``documentation``: Problemas o mejoras de documentación.
  - ``question``: Consultas generales.
  - ``urgent``: Problemas que requieren atención inmediata.

**Comunicación interna del equipo**

- Para consultas rápidas entre miembros del equipo de desarrollo.
- Canales de Slack/Teams designados para el proyecto.

Información para reportar problemas
-----------------------------------

Para facilitar la resolución rápida de problemas, incluye la siguiente información:

**Información básica:**

- Título descriptivo del problema.
- Fecha y hora en que ocurrió.
- Usuario afectado (si aplica).
- Entorno: desarrollo, staging o producción.

**Descripción técnica:**

- Pasos exactos para reproducir el problema.
- Comportamiento esperado vs. comportamiento actual.
- Frecuencia: ¿ocurre siempre o intermitentemente?

**Evidencia:**

- Fragmentos de logs relevantes (errores, tracebacks).
- Capturas de pantalla si es un problema visual.
- Respuestas de API si es problema de integración.

**Contexto del código:**

- Versión del código (commit hash o nombre de branch).
- Últimos cambios realizados antes del problema.

**Plantilla de reporte:**

.. code-block:: text

   ## Descripción del problema
   [Descripción clara y concisa]

   ## Pasos para reproducir
   1. Ir a '...'
   2. Hacer clic en '...'
   3. Observar el error

   ## Comportamiento esperado
   [Qué debería pasar]

   ## Comportamiento actual
   [Qué está pasando]

   ## Entorno
   - Entorno: [desarrollo/staging/producción]
   - Branch/Commit: [hash o nombre]
   - Navegador (si aplica): [nombre y versión]

   ## Logs/Screenshots
   [Adjuntar evidencia relevante]

Niveles de prioridad
--------------------

**P0 - Crítico**

- Sistema completamente caído.
- Brecha de seguridad confirmada.
- Pérdida de datos.
- Transacciones no se procesan.

*Tiempo de respuesta objetivo: 1 hora*

**P1 - Alto**

- Funcionalidad principal degradada.
- Afecta a múltiples usuarios.
- Workaround difícil o no disponible.

*Tiempo de respuesta objetivo: 4 horas*

**P2 - Medio**

- Funcionalidad secundaria afectada.
- Existe workaround viable.
- Afecta a usuarios específicos.

*Tiempo de respuesta objetivo: 24 horas*

**P3 - Bajo**

- Problema menor o cosmético.
- No afecta operación.
- Mejoras de experiencia.

*Tiempo de respuesta objetivo: 1 semana*

Horario de atención
-------------------

**Horario regular:**

- Lunes a viernes: 9:00 - 18:00 (hora local).
- Respuestas a issues en horario laboral.

**Incidentes críticos (P0):**

- Para problemas críticos fuera de horario:
  - Marcar el issue con etiqueta ``P0`` y ``urgent``.
  - Contactar por el canal de emergencias designado.
  - Seguir el runbook de incidentes si existe.

Escalamiento
------------

Si no recibes respuesta en el tiempo esperado:

1. Verificar que el issue tenga toda la información necesaria.
2. Agregar comentario solicitando actualización.
3. Contactar directamente al líder técnico.
4. Para P0/P1, escalar a gerencia si no hay respuesta en 2x el tiempo objetivo.

Recursos de autoayuda
---------------------

Antes de contactar soporte, revisa:

1. Esta documentación (especialmente sección de Problemas Comunes).
2. Issues cerrados en el repositorio (puede haber sido resuelto antes).
3. Logs del sistema para identificar el error específico.
4. Configuración del entorno vs. requisitos documentados.
