8.3 Respaldos y seguridad
=========================

Respaldos
---------

- Frecuencia: definir política (diaria/horaria) para respaldos de la base de datos y archivos críticos.
- Procedimiento: usar `pg_dump` o herramientas de backup compatibles con el motor que uses; mantener copias fuera del sitio (offsite) y con retención definida.

Seguridad
--------

- Cifrado: proteger datos sensibles en tránsito (TLS) y en reposo (discos, backups con cifrado).
- Rotación de claves: política para rotación periódica de API keys y secretos.
- Accesos: aplicar principio de menor privilegio y registrar accesos administrativos.

Pruebas y restauración
----------------------

- Probar restauraciones periódicas para validar que los backups son utilizables.
- Documentar el RTO/RPO esperado y procedimientos de emergencia.

Cumplimiento
-----------

- Mantener documentación de cumplimiento (si aplica) y un plan de respuesta a incidentes.
