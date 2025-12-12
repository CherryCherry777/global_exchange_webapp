Instalación
===========

Requisitos previos
------------------

- Python 3.12+ (ver `requirements.txt` para dependencias exactas).
- PostgreSQL (o la base de datos que uses en `settings.py`).
- Entorno virtual recomendado (`venv` o `virtualenv`).

Pasos rápidos (entorno Windows)
-------------------------------

1. Crear y activar un entorno virtual:

.. code-block:: powershell

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Instalar dependencias:

.. code-block:: powershell

   pip install -r requirements.txt

3. Configurar variables de entorno (.env) según `README.md` y `settings.py`.

4. Migrar la base de datos:

.. code-block:: powershell

   python manage.py migrate

5. Crear superusuario (opcional):

.. code-block:: powershell

   python manage.py createsuperuser

6. Ejecutar servidor local:

.. code-block:: powershell

   python manage.py runserver

Notas
-----

- Para despliegues en producción, revisa `README.md` y los archivos de configuración del servidor.
- Si usas Docker, hay scripts y ejemplos en la raíz del proyecto (añadir si corresponde).
