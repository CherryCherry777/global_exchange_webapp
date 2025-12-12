Instalación
===========

Esta guía describe el proceso completo de instalación de Global Exchange Webapp en un entorno de desarrollo local.

Requisitos previos
------------------

**Software requerido:**

- **Python 3.12 o superior**: El proyecto utiliza características modernas de Python. Verificar versión con ``python --version``.
- **PostgreSQL 14+**: Base de datos principal del sistema. Alternativamente, SQLite para desarrollo rápido.
- **Git**: Para clonar el repositorio y control de versiones.
- **pip**: Gestor de paquetes de Python (incluido con Python).

**Requisitos de sistema:**

- Mínimo 4 GB de RAM disponible.
- 2 GB de espacio en disco para dependencias y base de datos.
- Conexión a Internet para descargar paquetes.

Pasos de instalación (entorno Windows)
--------------------------------------

**1. Clonar el repositorio:**

.. code-block:: powershell

   git clone <url-del-repositorio>
   cd global_exchange_webapp

**2. Crear y activar un entorno virtual:**

.. code-block:: powershell

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

El prompt del terminal mostrará ``(.venv)`` indicando que el entorno está activo.

**3. Instalar dependencias:**

.. code-block:: powershell

   pip install --upgrade pip
   pip install -r requirements.txt

**4. Configurar variables de entorno:**

Crear un archivo ``.env`` en la raíz del proyecto con las siguientes variables:

.. code-block:: text

   DEBUG=True
   SECRET_KEY=<clave-secreta-generada>
   DATABASE_URL=postgres://usuario:password@localhost:5432/global_exchange
   ALLOWED_HOSTS=localhost,127.0.0.1

**5. Configurar la base de datos:**

Crear la base de datos en PostgreSQL:

.. code-block:: powershell

   createdb global_exchange

**6. Aplicar migraciones:**

.. code-block:: powershell

   python manage.py migrate

Esto crea todas las tablas necesarias en la base de datos.

**7. Crear superusuario administrador:**

.. code-block:: powershell

   python manage.py createsuperuser

Seguir las instrucciones para definir usuario, email y contraseña.

**8. Recopilar archivos estáticos:**

.. code-block:: powershell

   python manage.py collectstatic --noinput

**9. Ejecutar servidor de desarrollo:**

.. code-block:: powershell

   python manage.py runserver

Acceder a ``http://localhost:8000/`` en el navegador.

Verificación de la instalación
------------------------------

Para verificar que la instalación es correcta:

1. Acceder a ``http://localhost:8000/admin/`` e iniciar sesión con el superusuario.
2. Ejecutar las pruebas del sistema: ``python manage.py test``.
3. Verificar que no hay errores con: ``python manage.py check``.

Notas para producción
---------------------

- Configurar ``DEBUG=False`` y definir ``ALLOWED_HOSTS`` apropiadamente.
- Usar un servidor WSGI como Gunicorn detrás de Nginx.
- Configurar HTTPS con certificados SSL válidos.
- Revisar la configuración de seguridad en ``settings.py``.
