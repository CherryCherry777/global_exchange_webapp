8.3 Respaldos y seguridad
=========================

Esta sección describe las políticas y procedimientos para respaldos de datos y medidas de seguridad del sistema.

Política de respaldos
---------------------

**Frecuencia de respaldos:**

- **Base de datos**:
  - Respaldo completo: diario (preferiblemente en horario de baja actividad).
  - Respaldo incremental: cada 4-6 horas.
  - Logs de transacciones: continuo (WAL en PostgreSQL).

- **Archivos del sistema**:
  - Configuraciones: con cada cambio y semanalmente.
  - Media/uploads: diariamente.
  - Código fuente: versionado en Git.

**Procedimiento de respaldo de base de datos:**

.. code-block:: powershell

   # Respaldo completo PostgreSQL
   $fecha = Get-Date -Format "yyyyMMdd_HHmmss"
   pg_dump -U usuario -h localhost global_exchange > "backup_$fecha.sql"
   
   # Comprimir el respaldo
   Compress-Archive -Path "backup_$fecha.sql" -DestinationPath "backup_$fecha.zip"
   
   # Mover a almacenamiento seguro
   Copy-Item "backup_$fecha.zip" "\\servidor-backup\global_exchange\"

**Almacenamiento de respaldos:**

- Mantener copias en ubicación local para recuperación rápida.
- Copias offsite (otro centro de datos o nube) para recuperación ante desastres.
- Cifrado de respaldos antes de transferir a ubicaciones remotas.

**Retención:**

- Respaldos diarios: últimos 30 días.
- Respaldos semanales: últimos 3 meses.
- Respaldos mensuales: último año.
- Respaldos anuales: indefinido (según regulaciones).

Pruebas de restauración
-----------------------

**Frecuencia de pruebas:**

- Mensualmente: restaurar respaldo en ambiente de prueba.
- Trimestralmente: simulacro completo de recuperación.
- Anualmente: prueba de recuperación ante desastres (DR).

**Procedimiento de restauración:**

.. code-block:: powershell

   # Restaurar desde respaldo PostgreSQL
   psql -U usuario -h localhost -d global_exchange_restore < backup_20251212.sql
   
   # Verificar integridad
   python manage.py check --database restore
   python manage.py migrate --check

**Documentación requerida:**

- RTO (Recovery Time Objective): Tiempo máximo aceptable para restaurar servicio.
  - Objetivo típico: 4 horas.
  
- RPO (Recovery Point Objective): Pérdida máxima de datos aceptable.
  - Objetivo típico: 1 hora (respaldos incrementales cada hora).

Medidas de seguridad
--------------------

**Cifrado en tránsito:**

- TLS 1.2+ obligatorio para todas las conexiones.
- Certificados SSL válidos (no autofirmados en producción).
- HSTS habilitado para forzar HTTPS.

**Cifrado en reposo:**

- Discos de base de datos con cifrado (LUKS, BitLocker).
- Respaldos cifrados antes de transferir (GPG, AES-256).
- Archivos sensibles cifrados en almacenamiento.

**Gestión de credenciales:**

- Variables de entorno para secretos, nunca en código.
- Rotación de claves API cada 90 días.
- Contraseñas de servicio con complejidad mínima.

Control de acceso
-----------------

**Principio de menor privilegio:**

- Cada usuario tiene solo los permisos necesarios.
- Revisiones periódicas de permisos asignados.
- Remover acceso inmediatamente al cesar funciones.

**Autenticación:**

- Contraseñas robustas (8+ caracteres, complejidad).
- Bloqueo tras intentos fallidos.
- MFA para cuentas administrativas (si disponible).

**Registro de accesos:**

- Logging de todos los inicios de sesión.
- Alertas por accesos desde ubicaciones inusuales.
- Historial de cambios en permisos.

Plan de respuesta a incidentes
------------------------------

**Clasificación de incidentes:**

- **P1 - Crítico**: Sistema no disponible, brecha de seguridad confirmada.
- **P2 - Alto**: Funcionalidad principal degradada, sospecha de brecha.
- **P3 - Medio**: Funcionalidad secundaria afectada.
- **P4 - Bajo**: Problemas menores sin impacto operativo.

**Procedimiento de respuesta:**

1. **Detección**: Identificar y clasificar el incidente.
2. **Contención**: Aislar sistemas afectados, preservar evidencia.
3. **Erradicación**: Eliminar causa raíz del incidente.
4. **Recuperación**: Restaurar servicios a operación normal.
5. **Lecciones aprendidas**: Documentar y mejorar procesos.

**Contactos de emergencia:**

- Documentar lista de contactos con teléfonos y roles.
- Actualizar lista mensualmente.
- Disponible offline (no depender solo del sistema).

Cumplimiento normativo
----------------------

**Regulaciones aplicables:**

- Ley de protección de datos personales del país.
- Regulaciones del Banco Central para casas de cambio.
- Estándares PCI-DSS si se procesan tarjetas.
- Regulaciones AML/KYC.

**Documentación requerida:**

- Políticas de seguridad documentadas y aprobadas.
- Registros de auditoría disponibles para inspección.
- Evidencia de pruebas de restauración.
- Plan de continuidad del negocio.

Buenas prácticas
----------------

- Automatizar respaldos y verificar su ejecución.
- Probar restauraciones regularmente, no solo durante emergencias.
- Mantener documentación actualizada de todos los procedimientos.
- Capacitar al personal en procedimientos de seguridad.
- Realizar auditorías de seguridad periódicas.
