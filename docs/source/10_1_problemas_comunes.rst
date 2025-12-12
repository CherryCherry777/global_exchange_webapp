**10.1 Problemas comunes y soluciones**
=======================================

Esta página documenta los problemas más frecuentes con pasos detallados de diagnóstico y solución.

Problema: El servidor Django no arranca
---------------------------------------

**Síntomas:**

- El comando ``python manage.py runserver`` falla.
- Errores de importación (``ModuleNotFoundError``, ``ImportError``).
- ``django.core.exceptions.ImproperlyConfigured``.
- El servidor inicia pero falla inmediatamente.

**Diagnóstico paso a paso:**

1. **Verificar entorno virtual activo**:

   .. code-block:: powershell

      # Verificar que el prompt muestre (.venv)
      # Si no está activo:
      .\.venv\Scripts\Activate.ps1

2. **Verificar variable de entorno DJANGO_SETTINGS_MODULE**:

   .. code-block:: powershell

      echo $env:DJANGO_SETTINGS_MODULE
      # Debe mostrar: web_project.settings

3. **Verificar dependencias instaladas**:

   .. code-block:: powershell

      pip install -r requirements.txt

4. **Ejecutar verificación de Django**:

   .. code-block:: powershell

      python manage.py check

5. **Verificar archivo .env**:

   .. code-block:: powershell

      # Verificar que existe y tiene las variables requeridas
      Get-Content .env

**Soluciones según el error:**

- ``SECRET_KEY not set``: Agregar ``SECRET_KEY`` al archivo ``.env``.
- ``ModuleNotFoundError``: Ejecutar ``pip install -r requirements.txt``.
- ``ImproperlyConfigured``: Revisar ``settings.py`` y variables de entorno.

Problema: Error de conexión a base de datos
-------------------------------------------

**Síntomas:**

- ``django.db.utils.OperationalError: could not connect to server``.
- ``FATAL: password authentication failed``.
- ``FATAL: database "xxx" does not exist``.

**Diagnóstico:**

1. **Verificar que PostgreSQL esté ejecutándose**:

   .. code-block:: powershell

      Get-Service postgresql*

2. **Verificar credenciales en .env**:

   .. code-block:: text

      DATABASE_URL=postgres://usuario:password@localhost:5432/global_exchange

3. **Probar conexión manualmente**:

   .. code-block:: powershell

      psql -U usuario -h localhost -d global_exchange

**Soluciones:**

- Servicio detenido: Iniciar el servicio PostgreSQL.
- Credenciales incorrectas: Verificar usuario y contraseña.
- Base de datos no existe: Crear con ``createdb global_exchange``.

Problema: Migraciones fallidas
------------------------------

**Síntomas:**

- ``django.db.utils.ProgrammingError: relation "xxx" does not exist``.
- ``django.db.migrations.exceptions.InconsistentMigrationHistory``.
- Error al ejecutar ``python manage.py migrate``.

**Diagnóstico:**

1. **Verificar estado de migraciones**:

   .. code-block:: powershell

      python manage.py showmigrations

2. **Identificar migraciones pendientes**:

   .. code-block:: powershell

      python manage.py migrate --plan

**Soluciones:**

- Migraciones pendientes: Ejecutar ``python manage.py migrate``.
- Inconsistencia: Puede requerir ``python manage.py migrate --fake`` con cuidado.
- Conflictos: Revisar y resolver conflictos en archivos de migración.

Problema: Error al construir documentación Sphinx
-------------------------------------------------

**Síntomas:**

- ``make html`` o ``.\make.bat html`` produce errores.
- Advertencias de "duplicate object description".
- Errores de importación en ``conf.py``.

**Diagnóstico:**

1. **Ejecutar desde el directorio correcto**:

   .. code-block:: powershell

      cd docs
      .\make.bat html

2. **Revisar salida de errores**:

   - Errores marcados como ``ERROR`` son críticos.
   - Advertencias (``WARNING``) pueden ignorarse temporalmente.

**Soluciones comunes:**

- Duplicados: Agregar ``:noindex:`` en documentación repetida.
- Import error: Verificar ``sys.path`` en ``conf.py``.
- Módulo no encontrado: Verificar que Django esté configurado en ``conf.py``.

Problema: Archivos estáticos no se muestran
-------------------------------------------

**Síntomas:**

- CSS y JavaScript no cargan.
- Imágenes rotas.
- Errores 404 para archivos en ``/static/``.

**Solución:**

.. code-block:: powershell

   python manage.py collectstatic --noinput

Problema: Terminal (T-auser) no conecta
---------------------------------------

**Síntomas:**

- Terminal aparece offline en el dashboard.
- Transacciones no se procesan.
- Error de timeout en conexión.

**Diagnóstico:**

1. Verificar conectividad de red desde el terminal.
2. Verificar que la URL del servidor sea correcta.
3. Verificar que el API key sea válido.
4. Revisar logs del terminal.

**Soluciones:**

- Red: Verificar cable, WiFi, firewall.
- Credenciales: Regenerar API key si expiró.
- Servidor: Verificar que el servidor esté accesible.

Problema: Transacción rechazada por límite
------------------------------------------

**Síntomas:**

- Mensaje "Límite excedido".
- Cliente no puede operar.

**Solución:**

1. Verificar límite configurado para la categoría del cliente.
2. Verificar consumo actual del cliente.
3. Si es legítimo, solicitar aumento de límite al supervisor.
4. Considerar cambio de categoría del cliente.

Otros problemas comunes
-----------------------

**Sesión expira muy rápido:**

- Revisar ``SESSION_COOKIE_AGE`` en ``settings.py``.

**Emails no se envían:**

- Verificar configuración SMTP en ``settings.py``.
- En desarrollo, verificar consola si usa ``console.EmailBackend``.

**Cotización desactualizada:**

- Verificar tarea de sincronización automática.
- Actualizar manualmente desde el panel.
