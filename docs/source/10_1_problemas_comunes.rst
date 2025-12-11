**10.1 Problemas comunes y soluciones**
=====================================

Introducción
------------

Esta página lista problemas que suelen aparecer en el despliegue o la operación diaria, con pasos de diagnóstico y soluciones recomendadas.

Problema: El servidor Django no arranca
-------------------------------------

Síntomas:

- `python manage.py runserver` falla con errores de importación o `django.core.exceptions.ImproperlyConfigured`.

Diagnóstico y solución rápida:

1. Verifica variables de entorno: asegúrate de que `DJANGO_SETTINGS_MODULE` apunte al módulo correcto.
2. Revisa que las dependencias estén instaladas: ejecuta `pip install -r requirements.txt`.
3. Ejecuta `python manage.py check` para detectar configuraciones inválidas.
4. Si el error es de migraciones, corre `python manage.py migrate`.

Problema: Error al construir la documentación con Sphinx
------------------------------------------------------

Síntomas:

- `make html` o `.\make.bat html` produce errores o muchas advertencias.

Diagnóstico y solución rápida:

1. Ejecuta el comando en el directorio `docs`:

```
.\make.bat html
```

2. Revisa los errores marcados como `ERROR` (no las advertencias). Corrige docstrings o import paths que fallan.
3. Si aparecen advertencias de "duplicate object description", centraliza la documentación de modelos en un único archivo `models.rst` o añade `:noindex:` en entradas repetidas.
4. Para problemas con `django.setup()`, asegúrate de que `sys.path` incluye la ruta del proyecto en `docs/source/conf.py`.

Otros problemas comunes
----------------------

- Conexión a la base de datos: revisa `DATABASES` en `settings.py` y credenciales.
- Archivos estáticos: ejecutar `python manage.py collectstatic` en producción.
- Permisos de archivos y directorios en el servidor de producción.
